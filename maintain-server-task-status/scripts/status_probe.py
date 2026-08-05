#!/usr/bin/env python3
"""Collect bounded read-only host and selective-V11 status evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ProbeError(ValueError):
    """Raised when probe inputs or artifacts violate their contract."""


AUDIT_MODES = ("auto", "metadata", "full")


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ProbeError(f"{label} must be a JSON object: {path}")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bounded(value: str, max_lines: int = 32, max_chars: int = 4096) -> str:
    lines = value.splitlines()[:max_lines]
    return "\n".join(lines)[:max_chars]


def host_script(args: argparse.Namespace) -> str:
    repo = shlex.quote(args.checkout)
    python = shlex.quote(args.python)
    raw_pattern = args.process_pattern
    guarded_pattern = (
        f"[{raw_pattern[0]}]{raw_pattern[1:]}" if raw_pattern else "$^"
    )
    pattern = shlex.quote(guarded_pattern)
    return f"""set +e
printf 'OBSERVED_AT\\t'; date -Is 2>&1 | head -1
printf 'HOSTNAME\\t'; hostname 2>&1 | head -1
printf 'UPTIME\\t'; uptime -p 2>&1 | head -1
printf 'REVISION\\t'; git -C {repo} rev-parse HEAD 2>&1 | head -1
printf 'PYTHON\\t'; {python} -c 'import sys; print(sys.executable)' 2>&1 | head -1
printf 'CUDA\\t'; PYTHONWARNINGS=ignore {python} -c 'import json; import torch; print(json.dumps({{"available": torch.cuda.is_available(), "count": torch.cuda.device_count()}}))' 2>&1 | tail -1
printf 'GPU_BEGIN\\n'; nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader,nounits 2>&1 | head -32
printf 'GPU_END\\n'
printf 'PROCESS_BEGIN\\n'; pgrep -af -- {pattern} 2>&1 | head -32
printf 'PROCESS_END\\n'
printf 'SPACE\\t'; df -Pk {repo} 2>&1 | tail -1
printf 'INODES\\t'; df -Pi {repo} 2>&1 | tail -1
"""


def parse_host_output(stdout: str) -> dict[str, Any]:
    single: dict[str, str] = {}
    sections: dict[str, list[str]] = {"GPU": [], "PROCESS": []}
    section: str | None = None
    for line in stdout.splitlines():
        if line in {"GPU_BEGIN", "PROCESS_BEGIN"}:
            section = line.removesuffix("_BEGIN")
            continue
        if line in {"GPU_END", "PROCESS_END"}:
            section = None
            continue
        if section:
            sections[section].append(line[:512])
            continue
        key, separator, value = line.partition("\t")
        if separator:
            single[key] = value
    processes = [
        line
        for line in sections["PROCESS"]
        if "status_probe.py" not in line
        and "codex-linux-sandbox" not in line
        and " bwrap --new-session" not in line
    ]
    return {
        "cuda": single.get("CUDA"),
        "gpu_inventory": sections["GPU"],
        "hostname": single.get("HOSTNAME"),
        "inodes": single.get("INODES"),
        "interpreter": single.get("PYTHON"),
        "observed_at": single.get("OBSERVED_AT"),
        "processes": processes,
        "repository_revision": single.get("REVISION"),
        "storage": single.get("SPACE"),
        "uptime": single.get("UPTIME"),
    }


def command_host(args: argparse.Namespace) -> dict[str, Any]:
    script = host_script(args)
    if args.target == "local":
        command = ["bash", "-s"]
    else:
        command = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={args.timeout}",
            args.target,
            "bash",
            "-s",
        ]
    result = subprocess.run(
        command,
        input=script,
        check=False,
        capture_output=True,
        text=True,
        timeout=args.timeout + 10,
    )
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if result.returncode:
        error = bounded(result.stderr or result.stdout, max_lines=4, max_chars=1024)
        return {
            "adapter": "generic",
            "evidence": [
                {
                    "authority": "context",
                    "channel": "direct",
                    "kind": "reachability",
                    "observed_at": now,
                    "source": f"bounded direct probe: {args.machine_id}",
                    "summary": error or f"probe exited with code {result.returncode}",
                }
            ],
            "machine": {
                "hostname": None,
                "machine_id": args.machine_id,
                "reachability": "unreachable",
            },
            "observation": {},
        }
    observation = parse_host_output(result.stdout)
    observed_at = observation.get("observed_at") or now
    process_count = len(observation["processes"])
    return {
        "adapter": "generic",
        "evidence": [
            {
                "authority": "context",
                "channel": "direct",
                "kind": "host_probe",
                "observed_at": observed_at,
                "source": f"bounded direct probe: {args.machine_id}",
                "summary": "Host identity, revision, interpreter, GPU, and storage were observed.",
            },
            {
                "authority": "liveness",
                "channel": "direct",
                "kind": "process",
                "observed_at": observed_at,
                "source": f"pgrep pattern: {args.process_pattern}",
                "summary": f"{process_count} bounded process matches were observed.",
            },
        ],
        "machine": {
            "hostname": observation["hostname"],
            "machine_id": args.machine_id,
            "reachability": "reachable",
        },
        "observation": observation,
    }


def verify_asset_row(
    row: Any,
    label: str,
    *,
    verify_hashes: bool,
) -> None:
    if not isinstance(row, dict):
        raise ProbeError(f"{label} must be an object")
    path_value = row.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ProbeError(f"{label}.path is missing")
    path = Path(path_value)
    if not path.is_file():
        raise ProbeError(f"{label} is missing: {path}")
    size = row.get("size_bytes")
    if not isinstance(size, int) or path.stat().st_size != size:
        raise ProbeError(f"{label} size mismatch: {path}")
    digest = row.get("sha256")
    if not isinstance(digest, str) or not digest:
        raise ProbeError(f"{label} SHA-256 is missing: {path}")
    if verify_hashes and file_sha256(path) != digest:
        raise ProbeError(f"{label} SHA-256 mismatch: {path}")


def audit_retained_manifest(
    task_root: Path,
    *,
    verify_hashes: bool = True,
) -> tuple[str, int]:
    manifest_path = task_root / "retained_assets.json"
    manifest = load_object(manifest_path, "retained-assets manifest")
    task_id = manifest.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise ProbeError(f"retained-assets manifest has no task_id: {manifest_path}")
    if manifest.get("status") != "ready_to_bind_assets_retained":
        raise ProbeError(f"retained-assets status is not terminal: {manifest_path}")
    if manifest.get("labels_opened") is not False:
        raise ProbeError(f"retained-assets manifest opened labels: {manifest_path}")
    rows = []
    field_rows = {}
    for field in ("assets", "evidence_files"):
        value = manifest.get(field)
        if not isinstance(value, list):
            raise ProbeError(f"{manifest_path}:{field} must be a list")
        for index, row in enumerate(value):
            verify_asset_row(
                row,
                f"{manifest_path}:{field}[{index}]",
                verify_hashes=verify_hashes,
            )
        rows.extend(value)
        field_rows[field] = value
    declared_counts = {
        "asset_count": len(field_rows["assets"]),
        "evidence_file_count": len(field_rows["evidence_files"]),
    }
    for field, expected in declared_counts.items():
        if manifest.get(field) != expected:
            raise ProbeError(f"{manifest_path}:{field} mismatch")
    expected_asset_bytes = sum(
        int(row["size_bytes"]) for row in field_rows["assets"]
    )
    if manifest.get("asset_bytes") != expected_asset_bytes:
        raise ProbeError(f"{manifest_path}:asset_bytes mismatch")
    return task_id, len(rows)


def load_official_statuses(
    paths: list[Path],
) -> list[tuple[Path, dict[str, Any], dict[str, dict[str, Any]]]]:
    statuses = []
    for path in paths:
        official = load_object(path, "official V11 status")
        if official.get("schema") != "weight-spectrometry-v11-attack-status/v1":
            raise ProbeError(f"official V11 status schema is unsupported: {path}")
        task_rows = official.get("tasks")
        if not isinstance(task_rows, list):
            raise ProbeError(f"official V11 status tasks must be a list: {path}")
        tasks: dict[str, dict[str, Any]] = {}
        for row in task_rows:
            if not isinstance(row, dict) or not isinstance(row.get("task_id"), str):
                continue
            task_id = row["task_id"]
            if task_id in tasks:
                raise ProbeError(f"duplicate official task {task_id}: {path}")
            tasks[task_id] = row
        statuses.append((path, official, tasks))
    return statuses


def retained_manifest_task_id(task_root: Path) -> str:
    manifest_path = task_root / "retained_assets.json"
    manifest = load_object(manifest_path, "retained-assets manifest")
    task_id = manifest.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise ProbeError(f"retained-assets manifest has no task_id: {manifest_path}")
    return task_id


def resolve_official_task(
    task_id: str,
    statuses: list[tuple[Path, dict[str, Any], dict[str, dict[str, Any]]]],
) -> tuple[Path, dict[str, Any]] | None:
    matches = [
        (path, tasks[task_id])
        for path, _, tasks in statuses
        if task_id in tasks
    ]
    if not matches:
        return None
    active = [
        match for match in matches if match[1].get("status") != "blocked_on_source"
    ]
    if len(active) > 1:
        sources = ", ".join(str(path) for path, _ in active)
        raise ProbeError(
            f"task has multiple active official statuses: {task_id}: {sources}"
        )
    return active[0] if active else matches[0]


def command_selective_v11(args: argparse.Namespace) -> dict[str, Any]:
    status_paths = list(dict.fromkeys(Path(path) for path in args.status_json))
    statuses = load_official_statuses(status_paths)
    task_roots = list(dict.fromkeys(Path(path) for path in args.task_root))
    requested = set(args.task_id)
    if not requested:
        for task_root in task_roots:
            requested.add(retained_manifest_task_id(task_root))
    if not requested:
        raise ProbeError("selective-v11 requires --task-id or --task-root")

    errors = []
    workflow_counts: dict[str, int] = {}
    for task_id in sorted(requested):
        try:
            resolved = resolve_official_task(task_id, statuses)
        except ProbeError as exc:
            errors.append(str(exc))
            workflow_counts["ambiguous"] = workflow_counts.get("ambiguous", 0) + 1
            continue
        if resolved is None:
            errors.append(f"task is absent from official status: {task_id}")
            workflow_counts["absent"] = workflow_counts.get("absent", 0) + 1
            continue
        _, row = resolved
        state = str(row.get("status", "unknown"))
        workflow_counts[state] = workflow_counts.get(state, 0) + 1
        if state != "ready_to_bind":
            errors.append(f"task is not ready_to_bind: {task_id}: {state}")
        elif row.get("assets_retained") is not True:
            errors.append(f"task lacks retained-assets marker: {task_id}")

    for path, official, _ in statuses:
        if official.get("labels_opened") is not False:
            errors.append(f"official status reports labels_opened=true: {path}")
        if official.get("matrix_bound") is not False:
            errors.append(f"official status reports matrix_bound=true: {path}")

    gate_blocked = bool(errors)
    audited: dict[str, int] = {}
    audit_performed = "none"
    should_audit = args.audit_mode == "full" or (
        args.audit_mode in {"auto", "metadata"} and not gate_blocked
    )
    verify_hashes = args.audit_mode != "metadata"
    if should_audit:
        audit_performed = "full" if verify_hashes else "metadata"
        for task_root in task_roots:
            try:
                task_id, rows = audit_retained_manifest(
                    task_root,
                    verify_hashes=verify_hashes,
                )
                if task_id not in requested:
                    raise ProbeError(f"unexpected retained task: {task_id}")
                if task_id in audited:
                    raise ProbeError(f"duplicate retained task root: {task_id}")
                audited[task_id] = rows
            except ProbeError as exc:
                errors.append(str(exc))
        for task_id in sorted(requested):
            if task_id not in audited:
                errors.append(
                    f"task retained-assets manifest was not audited: {task_id}"
                )
    elif gate_blocked:
        audit_performed = "skipped_blocked_gate"

    full_audit = audit_performed == "full"
    complete = bool(requested) and not errors and full_audit
    metadata_ready = (
        bool(requested)
        and not errors
        and audit_performed == "metadata"
    )
    verdict = "complete" if complete else ("unknown" if metadata_ready else "blocked")
    authority = "completion" if complete else "progress"
    if complete:
        summary = (
            f"{len(requested)} selective V11 tasks are ready and retained; "
            f"{sum(audited.values())} manifest rows passed size and SHA-256 checks."
        )
    elif metadata_ready:
        summary = (
            f"{len(requested)} selective V11 tasks passed metadata checks across "
            f"{sum(audited.values())} manifest rows; a full SHA-256 audit is "
            "still required for completion."
        )
    elif audit_performed == "skipped_blocked_gate":
        ready = workflow_counts.get("ready_to_bind", 0)
        summary = (
            f"{ready}/{len(requested)} requested selective V11 tasks are "
            f"ready_to_bind; {len(errors)} blocking issue(s) make completion "
            "impossible, so retained-asset hashing was skipped."
        )
    else:
        summary = f"Selective V11 audit found {len(errors)} blocking issue(s)."
    labels_opened = any(
        official.get("labels_opened") is True for _, official, _ in statuses
    )
    matrix_bound = any(
        official.get("matrix_bound") is True for _, official, _ in statuses
    )
    return {
        "adapter": "selective-v11",
        "audit_mode": args.audit_mode,
        "audit_performed": audit_performed,
        "counts": {
            "manifest_rows": sum(audited.values()),
            "requested": len(requested),
            "workflow_states": dict(sorted(workflow_counts.items())),
        },
        "errors": errors,
        "evidence": [
            {
                "authority": authority,
                "channel": "artifact",
                "kind": "workflow_status",
                "source": f"{len(status_paths)} official V11 status file(s)",
                "summary": summary,
            }
        ],
        "status_files": [str(path) for path in status_paths],
        "status_patch": {
            "assets_retained": complete or metadata_ready,
            "completion_evidence": complete,
            "labels_opened": labels_opened,
            "matrix_bound": matrix_bound,
            "retained_assets_verified": complete,
            "summary": summary,
            "verdict": verdict,
            "workflow_adapter": "selective-v11",
            "workflow_state": (
                "ready_to_bind"
                if complete
                else ("ready_pending_full_audit" if metadata_ready else "blocked")
            ),
        },
        "task_ids": sorted(requested),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect bounded, read-only server/task evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    host = subparsers.add_parser("host", help="Run one bounded local or SSH probe.")
    host.add_argument("--machine-id", required=True)
    host.add_argument("--target", required=True, help="'local' or an SSH target")
    host.add_argument("--checkout", required=True)
    host.add_argument("--python", default="python3")
    host.add_argument("--process-pattern", default="scripts/ws.py")
    host.add_argument("--timeout", type=int, default=10)
    host.set_defaults(handler=command_host)

    selective = subparsers.add_parser(
        "selective-v11", help="Audit official status and retained assets."
    )
    selective.add_argument(
        "--status-json",
        action="append",
        default=[],
        required=True,
        help="Official status JSON; repeat for distributed matrix roots.",
    )
    selective.add_argument("--task-root", action="append", default=[])
    selective.add_argument("--task-id", action="append", default=[])
    selective.add_argument(
        "--audit-mode",
        choices=AUDIT_MODES,
        default="auto",
        help=(
            "auto skips hashes when the workflow gate is already blocked; "
            "metadata checks existence and size only; full always hashes."
        ),
    )
    selective.set_defaults(handler=command_selective_v11)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = args.handler(args)
    except (ProbeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
