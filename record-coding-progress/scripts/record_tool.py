#!/usr/bin/env python3
"""Collect and validate evidence for record-coding-progress notes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from uuid import uuid4


SUPPORTED_SCHEMA_VERSIONS = (2, 3)
MODES = ("coding-progress", "session-documentation")
IMPLEMENTATION_KINDS = ("function-fix", "fresh-implementation")
CHECK_RESULTS = ("pass", "fail", "partial", "not-run")
SOURCE_KINDS = ("user", "repository", "artifact", "web")
EVIDENCE_CLASSES = ("verified", "user-stated", "inferred", "proposed")
V2_CODING_STATUSES = ("completed", "partial", "blocked")
V2_SESSION_STATUSES = ("concluded", "proposed", "partial", "blocked")
CODING_TASK_TYPES = (
    "bug",
    "feature",
    "refactor",
    "maintenance",
    "migration",
    "evaluation",
    "experiment",
    "tooling",
)
SESSION_TASK_TYPES = (
    "research",
    "design",
    "diagnosis",
    "decision",
    "experiment-plan",
    "review",
    "documentation",
)
TASK_TYPES = tuple(dict.fromkeys((*CODING_TASK_TYPES, *SESSION_TASK_TYPES)))
PRIORITIES = ("critical", "high", "normal", "low", "unspecified")
V3_STATUSES = ("proposed", "in-progress", "validating", "blocked", "done", "canceled")
STATUS_CATEGORIES = {
    "proposed": "to-do",
    "in-progress": "in-progress",
    "validating": "in-progress",
    "blocked": "in-progress",
    "done": "done",
    "canceled": "done",
}
TERMINAL_STATUSES = ("done", "canceled")
RESOLUTIONS = ("completed", "partial-handoff", "superseded", "duplicate", "wont-do", "canceled")
DONE_RESOLUTIONS = ("completed", "partial-handoff", "superseded", "duplicate", "wont-do")
CANCELED_RESOLUTIONS = ("canceled", "superseded", "duplicate", "wont-do")
LINK_TYPES = ("parent", "blocks", "blocked-by", "relates-to", "supersedes", "duplicates")
ALLOWED_TRANSITIONS = {
    "proposed": ("in-progress", "canceled"),
    "in-progress": ("validating", "blocked", "done", "canceled"),
    "validating": ("in-progress", "blocked", "done", "canceled"),
    "blocked": ("in-progress", "canceled"),
    "done": (),
    "canceled": (),
}
COMMON_HEADINGS = (
    "Outcome",
    "Evidence Ledger",
    "Evidence Boundary",
    "Next Steps",
)
CODING_HEADINGS = ("Task and Scope", "Implementation", "Validation", "Git Custody")
SESSION_HEADINGS = ("Context and Scope", "Findings and Decisions")
SESSION_FORBIDDEN_HEADINGS = (
    "Implementation",
    "Interface and Behavior Changes",
    "Validation",
    "Git Custody",
    "Core Code and Functions",
    "Git Information",
)
V3_COMMON_HEADINGS = (*COMMON_HEADINGS, "Lifecycle")


class RecordError(Exception):
    """A user-facing manifest or repository error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_rfc3339(value: str) -> str:
    candidate = value.strip()
    if candidate == "unavailable":
        return candidate
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordError(f"timestamp must use RFC 3339 with a timezone: {value}") from exc
    if parsed.tzinfo is None:
        raise RecordError(f"timestamp must include a timezone: {value}")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parsed_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validated_date(value: str, label: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise RecordError(f"{label} must use YYYY-MM-DD: {value}") from exc
    if parsed.strftime("%Y-%m-%d") != value:
        raise RecordError(f"{label} must use YYYY-MM-DD: {value}")
    return value


def unique_values(values: list[str] | None) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in (values or []) if item.strip()))


def require_text(value: str | None, flag: str) -> str:
    if not value or not value.strip():
        raise RecordError(f"{flag} must be non-empty")
    return value.strip()


def task_types_for_mode(mode: str) -> tuple[str, ...]:
    return CODING_TASK_TYPES if mode == "coding-progress" else SESSION_TASK_TYPES


def validation_state(manifest: dict[str, Any]) -> str:
    if manifest["mode"] == "session-documentation":
        return "not-applicable"
    results = [item["result"] for item in manifest.get("checks", [])]
    if "fail" in results:
        return "fail"
    if "partial" in results:
        return "partial"
    if "pass" in results:
        return "pass"
    return "not-run"


def compatible_resolution(status: str, resolution: str | None) -> bool:
    if status == "done":
        return resolution in DONE_RESOLUTIONS
    if status == "canceled":
        return resolution in CANCELED_RESOLUTIONS
    return resolution in (None, "unresolved")


def next_lifecycle_id(manifest: dict[str, Any]) -> str:
    return f"L{len(manifest.get('lifecycle', [])) + 1}"


def append_lifecycle_event(
    manifest: dict[str, Any],
    *,
    at: str,
    actor: str,
    reason: str,
    from_status: str,
    to_status: str,
    action: str,
) -> None:
    manifest.setdefault("lifecycle", []).append(
        {
            "id": next_lifecycle_id(manifest),
            "at": at,
            "actor": actor,
            "reason": reason,
            "from": from_status,
            "to": to_status,
            "action": action,
        }
    )


def checked_event_time(manifest: dict[str, Any], value: str | None = None) -> str:
    at = normalize_rfc3339(value) if value else utc_now()
    if at == "unavailable":
        raise RecordError("lifecycle event time cannot be unavailable")
    previous = manifest.get("updated_at") or manifest["created_at"]
    if parsed_timestamp(at) < parsed_timestamp(previous):
        raise RecordError(f"lifecycle event time precedes the last update: {at} < {previous}")
    return at


def monotonic_update_time(manifest: dict[str, Any]) -> str:
    now = utc_now()
    previous = manifest.get("updated_at") or manifest["created_at"]
    return previous if parsed_timestamp(now) < parsed_timestamp(previous) else now


def run_git(repo: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise RecordError(f"git {' '.join(args)} failed: {detail}")
    return result


def git_root(repo: Path) -> Path | None:
    result = run_git(repo, ["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def git_branch(root: Path) -> str:
    result = run_git(root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else "detached"


def git_head(root: Path) -> str | None:
    result = run_git(root, ["rev-parse", "--verify", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def git_status(root: Path) -> list[str]:
    output = run_git(root, ["status", "--short", "--untracked-files=all"]).stdout
    return [line for line in output.splitlines() if line]


def working_tree_paths(root: Path) -> list[str]:
    paths: set[str] = set()
    unstaged = run_git(root, ["diff", "--name-only", "-z", "--"])
    paths.update(item for item in unstaged.stdout.split("\0") if item)
    staged = run_git(root, ["diff", "--cached", "--name-only", "-z", "--"])
    paths.update(item for item in staged.stdout.split("\0") if item)
    untracked = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    paths.update(item for item in untracked.stdout.split("\0") if item)
    return sorted(paths)


def verify_commit(root: Path, value: str) -> str:
    result = run_git(root, ["rev-parse", "--verify", f"{value}^{{commit}}"], check=False)
    if result.returncode != 0:
        raise RecordError(f"baseline commit is not valid in {root}: {value}")
    return result.stdout.strip()


def coding_snapshot(
    root: Path,
    baseline_head: str | None = None,
    *,
    baseline_unavailable: bool = False,
) -> dict[str, Any]:
    current_head = git_head(root)
    if baseline_unavailable:
        resolved_baseline = None
        baseline_source = "unavailable"
    elif baseline_head:
        resolved_baseline = verify_commit(root, baseline_head)
        baseline_source = "explicit"
    elif current_head:
        resolved_baseline = current_head
        baseline_source = "current-at-start"
    else:
        resolved_baseline = None
        baseline_source = "unborn-repository"
    status = git_status(root)
    return {
        "root": str(root),
        "branch": git_branch(root),
        "head": current_head,
        "status": status,
        "status_paths": working_tree_paths(root),
        "baseline_head": resolved_baseline,
        "baseline_source": baseline_source,
    }


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RecordError(f"manifest does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RecordError(f"manifest is not valid JSON: {exc}") from exc
    if manifest.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        raise RecordError(f"unsupported manifest schema: {manifest.get('schema_version')!r}")
    if manifest.get("mode") not in MODES:
        raise RecordError(f"unsupported manifest mode: {manifest.get('mode')!r}")
    return manifest


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_scope(root: Path, value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(root)
        except ValueError as exc:
            raise RecordError(f"task path is outside repository: {value}") from exc
    normalized = PurePosixPath(candidate.as_posix())
    if normalized.is_absolute() or ".." in normalized.parts:
        raise RecordError(f"task path must stay inside repository: {value}")
    text = normalized.as_posix().rstrip("/")
    if text in ("", "."):
        raise RecordError("repository root cannot be used as a task path; list explicit scopes")
    return text


def scope_matches(path: str, scopes: Iterable[str]) -> bool:
    return any(path == scope or path.startswith(f"{scope}/") for scope in scopes)


def changed_paths_since(root: Path, baseline: str | None) -> list[str]:
    paths = set(working_tree_paths(root))
    if baseline:
        result = run_git(root, ["diff", "--name-only", "-z", baseline, "--"])
        paths.update(item for item in result.stdout.split("\0") if item)
    untracked = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    paths.update(item for item in untracked.stdout.split("\0") if item)
    return sorted(paths)


def diff_summary(root: Path, baseline: str | None, scopes: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "files": 0,
        "insertions": 0,
        "deletions": 0,
        "binary_files": 0,
        "untracked_files": 0,
    }
    if not scopes:
        return summary
    if baseline:
        result = run_git(root, ["diff", "--numstat", baseline, "--", *scopes])
        for line in result.stdout.splitlines():
            fields = line.split("\t", 2)
            if len(fields) < 3:
                continue
            added, deleted, _ = fields
            summary["files"] += 1
            if added == "-" or deleted == "-":
                summary["binary_files"] += 1
            else:
                summary["insertions"] += int(added)
                summary["deletions"] += int(deleted)
    untracked = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    summary["untracked_files"] = sum(
        1
        for item in untracked.stdout.split("\0")
        if item and scope_matches(item, scopes)
    )
    return summary


def history_relation(root: Path, baseline: str | None, final_head: str | None) -> str:
    if not baseline or not final_head:
        return "unavailable"
    if baseline == final_head:
        return "same"
    result = run_git(root, ["merge-base", "--is-ancestor", baseline, final_head], check=False)
    return "ancestor" if result.returncode == 0 else "diverged"


def commits_since_baseline(
    root: Path,
    baseline: str | None,
    final_head: str | None,
) -> list[dict[str, str]]:
    if history_relation(root, baseline, final_head) != "ancestor":
        return []
    result = run_git(root, ["log", "--format=%H%x09%s", f"{baseline}..{final_head}"])
    commits: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        commit_hash, separator, subject = line.partition("\t")
        if separator:
            commits.append({"hash": commit_hash, "subject": subject})
    return commits


def command_start(args: argparse.Namespace) -> None:
    output = Path(args.output).resolve()
    if output.exists():
        raise RecordError(f"refusing to overwrite existing manifest: {output}")
    repository = Path(args.repo).resolve()
    if not repository.exists():
        raise RecordError(f"repository or project path does not exist: {repository}")

    created_at = utc_now()
    manifest: dict[str, Any] = {
        "schema_version": args.record_format,
        "mode": args.mode,
        "repository": str(repository),
        "created_at": created_at,
        "sources": [],
        "checks": [],
        "finalized_at": None,
    }
    if args.record_format == 3:
        task_type = require_text(args.task_type, "--task-type")
        if task_type not in task_types_for_mode(args.mode):
            allowed = ", ".join(task_types_for_mode(args.mode))
            raise RecordError(f"task type {task_type!r} is not valid for {args.mode}; use one of: {allowed}")
        task_slug = require_text(args.task_slug, "--task-slug")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", task_slug):
            raise RecordError("--task-slug must contain lowercase letters, digits, and single hyphens")
        record_date = validated_date(require_text(args.record_date, "--record-date"), "record date")
        due_date = validated_date(args.due_date, "due date") if args.due_date else None
        started_at = normalize_rfc3339(args.started_at) if args.started_at else created_at
        initial_status = args.initial_status
        manifest.update(
            {
                "record_id": f"RCP-{created_at.replace('-', '').replace(':', '')}-{uuid4().hex[:8]}",
                "task_type": task_type,
                "task_slug": task_slug,
                "record_date": record_date,
                "priority": args.priority,
                "owner": args.owner.strip() if args.owner and args.owner.strip() else "Unassigned",
                "components": unique_values(args.component),
                "labels": unique_values(args.label),
                "status": initial_status,
                "status_category": STATUS_CATEGORIES[initial_status],
                "resolution": "unresolved",
                "started_at": started_at,
                "updated_at": created_at,
                "completed_at": None,
                "due_date": due_date,
                "evidence_state": None,
                "validation_state": None,
                "links": [],
                "lifecycle": [],
            }
        )
        append_lifecycle_event(
            manifest,
            at=created_at,
            actor="record-tool",
            reason="record created",
            from_status="none",
            to_status=initial_status,
            action="created",
        )
    elif any(
        value
        for value in (
            args.task_type,
            args.task_slug,
            args.record_date,
            args.started_at,
            args.due_date,
            args.owner,
            args.component,
            args.label,
        )
    ) or args.initial_status != "in-progress" or args.priority != "unspecified":
        raise RecordError("v3 lifecycle options require --record-format 3")
    if args.mode == "coding-progress":
        if not args.implementation_kind:
            raise RecordError("--implementation-kind is required in coding-progress mode")
        manifest["implementation_kind"] = args.implementation_kind
        if args.baseline_head and args.baseline_unavailable:
            raise RecordError("--baseline-head and --baseline-unavailable are mutually exclusive")
        root = git_root(repository)
        if root is None:
            manifest["git"] = {
                "available": False,
                "reason": "not a Git checkout",
                "baseline": None,
                "final": None,
            }
            if args.baseline_head:
                raise RecordError("--baseline-head requires a Git checkout")
            if args.baseline_unavailable:
                raise RecordError("--baseline-unavailable is unnecessary outside a Git checkout")
        else:
            manifest["repository"] = str(root)
            manifest["git"] = {
                "available": True,
                "baseline": coding_snapshot(
                    root,
                    args.baseline_head,
                    baseline_unavailable=args.baseline_unavailable,
                ),
                "final": None,
            }
    elif args.baseline_head or args.baseline_unavailable or args.implementation_kind:
        raise RecordError(
            "baseline and implementation-kind options are valid only in coding-progress mode"
        )

    save_manifest(output, manifest)
    git_data = manifest.get("git", {})
    if git_data.get("available"):
        baseline = git_data["baseline"]
        baseline_value = baseline["baseline_head"] or "unavailable"
        print(
        f"created {output}; format={args.record_format}; mode={args.mode}; "
            f"implementation_kind={manifest['implementation_kind']}; baseline={baseline_value}; "
            f"dirty_paths={len(baseline['status_paths'])}"
        )
    else:
        suffix = f"; implementation_kind={manifest['implementation_kind']}" if (
            manifest["mode"] == "coding-progress"
        ) else ""
        print(f"created {output}; format={args.record_format}; mode={args.mode}{suffix}; git=not-recorded")


def command_add_source(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["finalized_at"]:
        raise RecordError("cannot add a source after manifest finalization")
    if manifest["schema_version"] == 3 and manifest["status"] in TERMINAL_STATUSES:
        raise RecordError("cannot add a source in a terminal status; resume the record first")
    sha = args.sha256
    if sha and not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
        raise RecordError("--sha256 must contain exactly 64 hexadecimal characters")
    source_file = None
    if args.file:
        file_path = Path(args.file).resolve()
        if not file_path.is_file():
            raise RecordError(f"source file is not a file: {file_path}")
        computed_sha = sha256_file(file_path)
        if sha and sha.lower() != computed_sha:
            raise RecordError(
                f"provided SHA-256 does not match source file: {sha.lower()} != {computed_sha}"
            )
        sha = computed_sha
        source_file = {"path": str(file_path), "size": file_path.stat().st_size}
    source_id = f"E{len(manifest['sources']) + 1}"
    manifest["sources"].append(
        {
            "id": source_id,
            "kind": args.kind,
            "locator": args.locator,
            "sha256": sha.lower() if sha else None,
            "file": source_file,
        }
    )
    if manifest["schema_version"] == 3:
        manifest["updated_at"] = monotonic_update_time(manifest)
    save_manifest(path, manifest)
    print(f"added {source_id}; kind={args.kind}")


def command_add_check(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["finalized_at"]:
        raise RecordError("cannot add a check after manifest finalization")
    if manifest["schema_version"] == 3 and manifest["status"] in TERMINAL_STATUSES:
        raise RecordError("cannot add a check in a terminal status; resume the record first")
    if manifest["mode"] != "coding-progress":
        raise RecordError("checks are forbidden in session-documentation mode")
    artifact = None
    if args.artifact:
        artifact_path = Path(args.artifact).resolve()
        if not artifact_path.is_file():
            raise RecordError(f"check artifact is not a file: {artifact_path}")
        artifact = {
            "path": str(artifact_path),
            "size": artifact_path.stat().st_size,
            "sha256": sha256_file(artifact_path),
        }
    check_id = f"V{len(manifest['checks']) + 1}"
    manifest["checks"].append(
        {
            "id": check_id,
            "command": args.command,
            "result": args.result,
            "summary": args.summary,
            "artifact": artifact,
        }
    )
    if manifest["schema_version"] == 3:
        manifest["updated_at"] = monotonic_update_time(manifest)
    save_manifest(path, manifest)
    print(f"added {check_id}; result={args.result}")


def apply_transition(
    manifest: dict[str, Any],
    *,
    target: str,
    actor: str,
    reason: str,
    resolution: str | None,
    at: str | None = None,
) -> None:
    current = manifest["status"]
    if target == current:
        raise RecordError(f"status is already {target}; use finish to finalize the current status")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise RecordError(f"transition is not allowed: {current} -> {target}")
    actor = require_text(actor, "--actor")
    reason = require_text(reason, "--reason")
    if target == "blocked" and not reason:
        raise RecordError("a blocked transition requires a blocker reason")
    if not compatible_resolution(target, resolution):
        if target == "done":
            allowed = ", ".join(DONE_RESOLUTIONS)
        elif target == "canceled":
            allowed = ", ".join(CANCELED_RESOLUTIONS)
        else:
            allowed = "unresolved"
        raise RecordError(f"resolution is not valid for status {target}; use: {allowed}")
    event_at = checked_event_time(manifest, at)
    manifest["status"] = target
    manifest["status_category"] = STATUS_CATEGORIES[target]
    manifest["resolution"] = resolution if target in TERMINAL_STATUSES else "unresolved"
    manifest["completed_at"] = event_at if target in TERMINAL_STATUSES else None
    manifest["blocked_reason"] = reason if target == "blocked" else None
    manifest["updated_at"] = event_at
    append_lifecycle_event(
        manifest,
        at=event_at,
        actor=actor,
        reason=reason,
        from_status=current,
        to_status=target,
        action="transition",
    )


def command_transition(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["schema_version"] != 3:
        raise RecordError("transition is available only for record format 3")
    if manifest["finalized_at"]:
        raise RecordError("cannot transition a finalized manifest; use resume")
    apply_transition(
        manifest,
        target=args.to,
        actor=args.actor,
        reason=args.reason,
        resolution=args.resolution,
        at=args.at,
    )
    save_manifest(path, manifest)
    print(f"transitioned {path}; status={manifest['status']}; resolution={manifest['resolution']}")


def command_add_link(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["schema_version"] != 3:
        raise RecordError("add-link is available only for record format 3")
    if manifest["finalized_at"]:
        raise RecordError("cannot add a link after manifest finalization")
    if manifest["status"] in TERMINAL_STATUSES:
        raise RecordError("cannot add a link in a terminal status; resume the record first")
    target = require_text(args.target, "--target")
    if target == manifest["record_id"]:
        raise RecordError("a record cannot link to itself")
    links = manifest["links"]
    if any(item["type"] == args.type and item["target"] == target for item in links):
        raise RecordError(f"duplicate link: {args.type} {target}")
    if args.type == "parent" and any(item["type"] == "parent" for item in links):
        raise RecordError("a record can have only one parent link")
    links.append({"id": f"R{len(links) + 1}", "type": args.type, "target": target})
    manifest["updated_at"] = monotonic_update_time(manifest)
    save_manifest(path, manifest)
    print(f"added R{len(links)}; type={args.type}; target={target}")


def command_resume(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["schema_version"] != 3:
        raise RecordError("resume is available only for record format 3")
    if not manifest["finalized_at"] and manifest["status"] not in TERMINAL_STATUSES:
        raise RecordError("record is already active")
    event_at = checked_event_time(manifest, args.at)
    actor = require_text(args.actor, "--actor")
    reason = require_text(args.reason, "--reason")
    current = manifest["status"]
    manifest["status"] = "in-progress"
    manifest["status_category"] = "in-progress"
    manifest["resolution"] = "unresolved"
    manifest["completed_at"] = None
    manifest["blocked_reason"] = None
    manifest["evidence_state"] = None
    manifest["validation_state"] = None
    manifest["finalized_at"] = None
    if manifest.get("git"):
        manifest["git"]["final"] = None
    manifest["updated_at"] = event_at
    append_lifecycle_event(
        manifest,
        at=event_at,
        actor=actor,
        reason=reason,
        from_status=current,
        to_status="in-progress",
        action="resume",
    )
    save_manifest(path, manifest)
    print(f"resumed {path}; status=in-progress")


def capture_final_git(
    manifest: dict[str, Any], task_paths: list[str], record_path_arg: str | None
) -> tuple[int, int, int] | None:
    if manifest["mode"] == "session-documentation":
        if task_paths or record_path_arg:
            raise RecordError("task and record paths are forbidden in session-documentation mode")
        return None
    git_data = manifest["git"]
    if not git_data["available"]:
        if task_paths or record_path_arg:
            raise RecordError("task and record paths require a Git checkout")
        git_data["final"] = None
        return None
    root = Path(git_data["baseline"]["root"])
    scopes = sorted(set(normalized_scope(root, item) for item in task_paths))
    record_path = normalized_scope(root, record_path_arg) if record_path_arg else None
    if record_path and scope_matches(record_path, scopes):
        raise RecordError("--record-path must not be nested in a --task-path scope")
    custody_scopes = [*scopes, *([record_path] if record_path else [])]
    final_status = git_status(root)
    final_head = git_head(root)
    baseline_head = git_data["baseline"].get("baseline_head")
    changed = changed_paths_since(root, baseline_head)
    preexisting = set(git_data["baseline"]["status_paths"])
    owned = sorted(item for item in changed if scope_matches(item, custody_scopes))
    outside = sorted(item for item in changed if not scope_matches(item, custody_scopes))
    overlap = sorted(set(owned) & preexisting)
    git_data["final"] = {
        "root": str(root),
        "branch": git_branch(root),
        "head": final_head,
        "status": final_status,
        "status_paths": working_tree_paths(root),
        "task_paths": scopes,
        "record_path": record_path,
        "changed_paths": changed,
        "task_owned_changed_paths": owned,
        "preexisting_paths": sorted(preexisting),
        "preexisting_overlap": overlap,
        "outside_scope_changed_paths": outside,
        "scoped_diff": diff_summary(root, baseline_head, scopes),
        "history_relation": history_relation(root, baseline_head, final_head),
        "commits_since_baseline": commits_since_baseline(root, baseline_head, final_head),
    }
    return len(owned), len(overlap), len(outside)


def command_finish(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["schema_version"] == 2:
        if any((args.status, args.evidence_state, args.actor, args.reason, args.resolution, args.at)):
            raise RecordError("v3 lifecycle options require a record format 3 manifest")
        if manifest["finalized_at"] and not args.refresh:
            raise RecordError("manifest is already finalized; pass --refresh to recapture final state")
        counts = capture_final_git(manifest, args.task_path or [], args.record_path)
        manifest["finalized_at"] = utc_now()
        save_manifest(path, manifest)
        if counts is None:
            suffix = (
                "git=unavailable"
                if manifest["mode"] == "coding-progress"
                else f"sources={len(manifest['sources'])}"
            )
            print(f"finalized {path}; {suffix}")
        else:
            owned, overlap, outside = counts
            print(
                f"finalized {path}; owned={owned}; overlap={overlap}; "
                f"outside_scope={outside}; checks={len(manifest['checks'])}"
            )
        return

    if args.refresh:
        if not manifest["finalized_at"]:
            raise RecordError("cannot refresh a manifest before finalization")
        if any((args.status, args.evidence_state, args.actor, args.reason, args.resolution, args.at)):
            raise RecordError("--refresh preserves lifecycle fields; omit v3 lifecycle options")
        counts = capture_final_git(manifest, args.task_path or [], args.record_path)
        save_manifest(path, manifest)
        if counts is None:
            print(f"refreshed {path}; lifecycle=preserved")
        else:
            owned, overlap, outside = counts
            print(f"refreshed {path}; owned={owned}; overlap={overlap}; outside_scope={outside}; lifecycle=preserved")
        return
    if manifest["finalized_at"]:
        raise RecordError("manifest is already finalized; pass --refresh or resume it")
    target = require_text(args.status, "--status")
    evidence_state = require_text(args.evidence_state, "--evidence-state")
    if target != manifest["status"]:
        apply_transition(
            manifest,
            target=target,
            actor=args.actor,
            reason=args.reason,
            resolution=args.resolution,
            at=args.at,
        )
        finalized_at = manifest["updated_at"]
    else:
        actor = require_text(args.actor, "--actor")
        reason = require_text(args.reason, "--reason")
        if not compatible_resolution(target, args.resolution):
            raise RecordError(f"resolution is not valid for status {target}")
        if target in TERMINAL_STATUSES:
            if manifest["resolution"] == "unresolved":
                manifest["resolution"] = args.resolution
            elif args.resolution != manifest["resolution"]:
                raise RecordError("finish resolution must match the terminal transition resolution")
        event_at = checked_event_time(manifest, args.at)
        manifest["updated_at"] = event_at
        append_lifecycle_event(
            manifest,
            at=event_at,
            actor=actor,
            reason=reason,
            from_status=target,
            to_status=target,
            action="finalized",
        )
        finalized_at = event_at
    manifest["evidence_state"] = evidence_state
    manifest["validation_state"] = validation_state(manifest)
    counts = capture_final_git(manifest, args.task_path or [], args.record_path)
    manifest["finalized_at"] = finalized_at
    save_manifest(path, manifest)
    if counts is None:
        suffix = "git=unavailable" if manifest["mode"] == "coding-progress" else f"sources={len(manifest['sources'])}"
        print(f"finalized {path}; status={target}; resolution={manifest['resolution']}; {suffix}")
    else:
        owned, overlap, outside = counts
        print(
            f"finalized {path}; status={target}; resolution={manifest['resolution']}; "
            f"owned={owned}; overlap={overlap}; outside_scope={outside}; checks={len(manifest['checks'])}"
        )


def metadata_value(text: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip("`")


def headings(text: str) -> set[str]:
    return set(re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE))


def normalized_whitespace(value: str) -> str:
    return " ".join(value.split())


def section_text(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else ""


def has_level_three_heading(text: str, heading: str) -> bool:
    return bool(re.search(rf"^###\s+{re.escape(heading)}\s*$", text, re.MULTILINE))


def evidence_id_has_class(text: str, evidence_id: str) -> bool:
    for line in text.splitlines():
        if re.search(rf"\b{re.escape(evidence_id)}\b", line) and any(
            evidence_class in line.lower() for evidence_class in EVIDENCE_CLASSES
        ):
            return True
    return False


def diff_summary_token(summary: dict[str, Any]) -> str:
    return (
        f"files={summary['files']}; insertions={summary['insertions']}; "
        f"deletions={summary['deletions']}; binary_files={summary['binary_files']}; "
        f"untracked_files={summary.get('untracked_files', 0)}"
    )


def validate_note_v2(manifest: dict[str, Any], note: Path) -> list[str]:
    try:
        text = note.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"note does not exist: {note}"]

    errors: list[str] = []
    if metadata_value(text, "Record format") != "2":
        errors.append("metadata Record format must be `2`")
    if metadata_value(text, "Mode") != manifest["mode"]:
        errors.append(f"metadata Mode must be `{manifest['mode']}`")
    date = metadata_value(text, "Date")
    if not date or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        errors.append("metadata Date must use YYYY-MM-DD")
    evidence_state = metadata_value(text, "Evidence state")
    if evidence_state not in ("verified", "mixed", "unverified"):
        errors.append("metadata Evidence state must be verified, mixed, or unverified")
    status = metadata_value(text, "Status")
    allowed_statuses = V2_CODING_STATUSES if manifest["mode"] == "coding-progress" else V2_SESSION_STATUSES
    if status not in allowed_statuses:
        errors.append(f"metadata Status must be one of: {', '.join(allowed_statuses)}")
    if not metadata_value(text, "Project"):
        errors.append("metadata Project is required")
    if re.search(r"<(?:Title|repository|project|task|path|temporary|YYYY)", text):
        errors.append("unresolved template placeholder found")

    note_headings = headings(text)
    mode_headings = CODING_HEADINGS if manifest["mode"] == "coding-progress" else SESSION_HEADINGS
    for heading in (*COMMON_HEADINGS, *mode_headings):
        if heading not in note_headings:
            errors.append(f"missing required heading: ## {heading}")

    evidence_ledger = section_text(text, "Evidence Ledger")
    for source in manifest["sources"]:
        if source["id"] not in text:
            errors.append(f"source {source['id']} is absent from the note")
        elif not evidence_id_has_class(evidence_ledger, source["id"]):
            errors.append(
                f"source {source['id']} must be classified in the Evidence Ledger as one of: "
                f"{', '.join(EVIDENCE_CLASSES)}"
            )
        if normalized_whitespace(source["locator"]) not in normalized_whitespace(text):
            errors.append(f"source locator for {source['id']} is absent from the note")
        if source.get("sha256") and source["sha256"] not in text:
            errors.append(f"source hash for {source['id']} is absent from the note")

    if not manifest.get("finalized_at"):
        errors.append("manifest must be finalized before note validation")
    if manifest["mode"] == "session-documentation":
        if not manifest["sources"]:
            errors.append("session-documentation requires at least one recorded source")
        for forbidden in SESSION_FORBIDDEN_HEADINGS:
            if forbidden in note_headings:
                errors.append(f"session-documentation forbids heading: ## {forbidden}")
        if manifest.get("checks"):
            errors.append("session-documentation manifest must not contain checks")
        if "git" in manifest:
            errors.append("session-documentation manifest must not contain Git evidence")
        return errors

    implementation_kind = manifest.get("implementation_kind")
    if implementation_kind is not None:
        if implementation_kind not in IMPLEMENTATION_KINDS:
            errors.append("manifest implementation_kind is unsupported")
        elif metadata_value(text, "Implementation class") != implementation_kind:
            errors.append(
                "metadata Implementation class must match manifest implementation_kind: "
                f"{implementation_kind}"
            )
        else:
            implementation = section_text(text, "Implementation")
            required_implementation_headings = (
                ("Preserved Contract", "Corrective Change")
                if implementation_kind == "function-fix"
                else ("Plan and Starting Status", "Core Functions and Result")
            )
            for heading in required_implementation_headings:
                if not has_level_three_heading(implementation, heading):
                    errors.append(
                        f"{implementation_kind} records require implementation heading: "
                        f"### {heading}"
                    )
            validation = section_text(text, "Validation")
            if not has_level_three_heading(validation, "Test Result"):
                errors.append(
                    "coding records with implementation_kind require validation heading: "
                    "### Test Result"
                )

    for check in manifest["checks"]:
        if check["id"] not in text:
            errors.append(f"check {check['id']} is absent from the note")
        elif not evidence_id_has_class(evidence_ledger, check["id"]):
            errors.append(
                f"check {check['id']} must be classified as verified in the Evidence Ledger"
            )
        expected_heading = rf"^###\s+{re.escape(check['id'])}\s+-\s+{re.escape(check['result'])}\s*$"
        if not re.search(expected_heading, text, re.MULTILINE):
            errors.append(f"check {check['id']} must report result `{check['result']}` in its heading")
        if check["command"] not in text:
            errors.append(f"exact command for {check['id']} is absent from the note")
        if normalized_whitespace(check["summary"]) not in normalized_whitespace(text):
            errors.append(f"observed summary for {check['id']} is absent from the note")
        artifact = check.get("artifact")
        if artifact and artifact["sha256"] not in text:
            errors.append(f"artifact hash for {check['id']} is absent from the note")

    git_data = manifest.get("git", {})
    if git_data.get("available"):
        baseline = git_data["baseline"]
        final = git_data.get("final")
        if final is None:
            errors.append("Git evidence has not been finalized")
        else:
            exact_values = {
                "final branch": final["branch"],
            }
            if final["head"]:
                exact_values["final HEAD"] = final["head"]
            elif not re.search(r"final\s+head[^\n]*unavailable", text, re.IGNORECASE):
                errors.append("note must state that final HEAD is unavailable")
            if baseline["baseline_head"]:
                exact_values["baseline HEAD"] = baseline["baseline_head"]
            elif not re.search(
                r"baseline\s+head[^\n]*unavailable",
                text,
                re.IGNORECASE,
            ):
                errors.append("note must state that baseline HEAD is unavailable")
            for label, value in exact_values.items():
                if value not in text:
                    errors.append(f"{label} is absent from the note: {value}")
            path_fields = (
                "task_paths",
                "task_owned_changed_paths",
                "preexisting_paths",
                "preexisting_overlap",
                "outside_scope_changed_paths",
            )
            for field in path_fields:
                for value in final[field]:
                    if value not in text:
                        errors.append(f"Git {field} path is absent from the note: {value}")
            if final.get("record_path") and final["record_path"] not in text:
                errors.append(f"Git record path is absent from the note: {final['record_path']}")
            relation = final.get("history_relation", "unavailable")
            if not re.search(
                rf"history\s+relation[^\n]*{re.escape(relation)}",
                text,
                re.IGNORECASE,
            ):
                errors.append(f"Git history relation is absent from the note: {relation}")
            commits = final.get("commits_since_baseline", final.get("task_commits", []))
            for commit in commits:
                if commit["hash"] not in text or commit["subject"] not in text:
                    errors.append(
                        f"commit since baseline is absent or incomplete in the note: "
                        f"{commit['hash']} {commit['subject']}"
                    )
            summary_token = diff_summary_token(final["scoped_diff"])
            if normalized_whitespace(summary_token) not in normalized_whitespace(text):
                errors.append(f"scoped diff summary is absent from the note: {summary_token}")
    elif "unavailable" not in text.lower():
        errors.append("note must state that Git evidence is unavailable")
    return errors


def rendered_list(values: list[str]) -> str:
    return ", ".join(values) if values else "None"


def expected_v3_metadata(manifest: dict[str, Any]) -> dict[str, str]:
    expected = {
        "Record format": "3",
        "Record ID": manifest["record_id"],
        "Mode": manifest["mode"],
        "Task type": manifest["task_type"],
        "Task slug": manifest["task_slug"],
        "Date": manifest["record_date"],
        "Project": manifest["repository"],
        "Priority": manifest["priority"],
        "Owner": manifest["owner"],
        "Components": rendered_list(manifest["components"]),
        "Labels": rendered_list(manifest["labels"]),
        "Status category": manifest["status_category"],
        "Status": manifest["status"],
        "Resolution": manifest["resolution"],
        "Created at": manifest["created_at"],
        "Started at": manifest["started_at"],
        "Updated at": manifest["updated_at"],
        "Completed at": manifest["completed_at"] or "Not applicable",
        "Due date": manifest["due_date"] or "Not applicable",
        "Evidence state": manifest["evidence_state"],
        "Validation state": manifest["validation_state"],
    }
    if manifest["mode"] == "coding-progress":
        expected["Implementation class"] = manifest["implementation_kind"]
    return expected


def validate_v3_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    record_id = manifest.get("record_id", "")
    if not re.fullmatch(r"RCP-\d{8}T\d{6}Z-[0-9a-f]{8}", record_id):
        errors.append(f"manifest record ID is invalid: {record_id!r}")
    task_type = manifest.get("task_type")
    if task_type not in task_types_for_mode(manifest["mode"]):
        errors.append(f"manifest task type is invalid for {manifest['mode']}: {task_type!r}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", manifest.get("task_slug", "")):
        errors.append("manifest task slug is invalid")
    try:
        validated_date(manifest.get("record_date", ""), "record date")
        if manifest.get("due_date"):
            validated_date(manifest["due_date"], "due date")
    except RecordError as exc:
        errors.append(str(exc))
    if manifest.get("priority") not in PRIORITIES:
        errors.append(f"manifest priority is invalid: {manifest.get('priority')!r}")
    status = manifest.get("status")
    if status not in V3_STATUSES:
        errors.append(f"manifest status is invalid: {status!r}")
    elif manifest.get("status_category") != STATUS_CATEGORIES[status]:
        errors.append("manifest status category does not match status")
    resolution = manifest.get("resolution")
    if status in V3_STATUSES and not compatible_resolution(status, resolution):
        errors.append(f"manifest resolution is invalid for status {status}: {resolution!r}")
    completed_at = manifest.get("completed_at")
    if status in TERMINAL_STATUSES and not completed_at:
        errors.append("terminal manifest status requires completed_at")
    if status not in TERMINAL_STATUSES and completed_at:
        errors.append("nonterminal manifest status must not have completed_at")
    if status == "blocked" and not manifest.get("blocked_reason"):
        errors.append("blocked manifest requires a blocker reason")
    if manifest.get("evidence_state") not in ("verified", "mixed", "unverified"):
        errors.append("manifest evidence_state must be verified, mixed, or unverified")
    expected_validation = validation_state(manifest)
    if manifest.get("validation_state") != expected_validation:
        errors.append(
            f"manifest validation_state must be {expected_validation}: "
            f"{manifest.get('validation_state')!r}"
        )
    if not manifest.get("finalized_at"):
        errors.append("manifest must be finalized before note validation")
    timestamp_fields = ("created_at", "updated_at", "finalized_at")
    parsed: dict[str, datetime] = {}
    for field in timestamp_fields:
        value = manifest.get(field)
        if not value:
            continue
        try:
            normalized = normalize_rfc3339(value)
            if normalized != value:
                errors.append(f"manifest {field} must be normalized UTC RFC 3339")
            parsed[field] = parsed_timestamp(normalized)
        except RecordError as exc:
            errors.append(str(exc))
    if "created_at" in parsed and "updated_at" in parsed and parsed["updated_at"] < parsed["created_at"]:
        errors.append("manifest updated_at precedes created_at")
    if "updated_at" in parsed and "finalized_at" in parsed and parsed["finalized_at"] < parsed["updated_at"]:
        errors.append("manifest finalized_at precedes updated_at")
    for field in ("started_at", "completed_at"):
        value = manifest.get(field)
        if not value or value == "unavailable":
            continue
        try:
            if normalize_rfc3339(value) != value:
                errors.append(f"manifest {field} must be normalized UTC RFC 3339")
        except RecordError as exc:
            errors.append(str(exc))
    if completed_at and "created_at" in parsed and "finalized_at" in parsed:
        try:
            completed_time = parsed_timestamp(normalize_rfc3339(completed_at))
            if completed_time < parsed["created_at"]:
                errors.append("manifest completed_at precedes created_at")
            if completed_time > parsed["finalized_at"]:
                errors.append("manifest completed_at follows finalized_at")
        except RecordError:
            pass
    lifecycle = manifest.get("lifecycle", [])
    if not lifecycle:
        errors.append("manifest lifecycle must contain at least the creation event")
    previous_time: datetime | None = None
    previous_status: str | None = None
    for index, event in enumerate(lifecycle, start=1):
        if event.get("id") != f"L{index}":
            errors.append(f"manifest lifecycle ID must be L{index}")
        try:
            event_time = parsed_timestamp(normalize_rfc3339(event.get("at", "")))
            if previous_time and event_time < previous_time:
                errors.append(f"manifest lifecycle event L{index} is out of time order")
            previous_time = event_time
        except RecordError as exc:
            errors.append(str(exc))
        for field in ("actor", "reason", "from", "to", "action"):
            if not event.get(field):
                errors.append(f"manifest lifecycle event L{index} lacks {field}")
        action = event.get("action")
        from_status = event.get("from")
        to_status = event.get("to")
        if index == 1:
            if action != "created" or from_status != "none" or to_status not in ("proposed", "in-progress"):
                errors.append("manifest lifecycle L1 must be the creation event")
            if event.get("at") != manifest.get("created_at"):
                errors.append("manifest lifecycle L1 time must equal created_at")
        else:
            if from_status != previous_status:
                errors.append(f"manifest lifecycle event L{index} does not continue the status chain")
            if action == "transition":
                if from_status not in ALLOWED_TRANSITIONS or to_status not in ALLOWED_TRANSITIONS[from_status]:
                    errors.append(f"manifest lifecycle event L{index} contains a forbidden transition")
            elif action == "finalized":
                if from_status != to_status:
                    errors.append(f"manifest lifecycle event L{index} has an invalid finalization loop")
            elif action == "resume":
                if to_status != "in-progress":
                    errors.append(f"manifest lifecycle event L{index} has an invalid resume target")
            else:
                errors.append(f"manifest lifecycle event L{index} has an unsupported action")
        previous_status = to_status
    if lifecycle and lifecycle[-1].get("to") != status:
        errors.append("manifest status does not match the last lifecycle event")
    links = manifest.get("links", [])
    parent_count = 0
    seen_links: set[tuple[str, str]] = set()
    for index, link in enumerate(links, start=1):
        if link.get("id") != f"R{index}":
            errors.append(f"manifest link ID must be R{index}")
        link_type = link.get("type")
        target = link.get("target")
        if link_type not in LINK_TYPES or not target:
            errors.append(f"manifest link R{index} is invalid")
            continue
        if target == record_id:
            errors.append(f"manifest link R{index} is a self-link")
        key = (link_type, target)
        if key in seen_links:
            errors.append(f"manifest link R{index} duplicates {link_type} {target}")
        seen_links.add(key)
        if link_type == "parent":
            parent_count += 1
    if parent_count > 1:
        errors.append("manifest has more than one parent link")
    return errors


def validate_v3_sources(manifest: dict[str, Any], text: str, errors: list[str]) -> None:
    evidence_ledger = section_text(text, "Evidence Ledger")
    for source in manifest["sources"]:
        if source["id"] not in text:
            errors.append(f"source {source['id']} is absent from the note")
        elif not evidence_id_has_class(evidence_ledger, source["id"]):
            errors.append(
                f"source {source['id']} must be classified in the Evidence Ledger as one of: "
                f"{', '.join(EVIDENCE_CLASSES)}"
            )
        if normalized_whitespace(source["locator"]) not in normalized_whitespace(text):
            errors.append(f"source locator for {source['id']} is absent from the note")
        if source.get("sha256") and source["sha256"] not in text:
            errors.append(f"source hash for {source['id']} is absent from the note")


def validate_v3_checks(manifest: dict[str, Any], text: str, errors: list[str]) -> None:
    evidence_ledger = section_text(text, "Evidence Ledger")
    for check in manifest["checks"]:
        if check["id"] not in text:
            errors.append(f"check {check['id']} is absent from the note")
        elif not evidence_id_has_class(evidence_ledger, check["id"]):
            errors.append(f"check {check['id']} must be classified as verified in the Evidence Ledger")
        expected_heading = rf"^###\s+{re.escape(check['id'])}\s+-\s+{re.escape(check['result'])}\s*$"
        if not re.search(expected_heading, text, re.MULTILINE):
            errors.append(f"check {check['id']} must report result `{check['result']}` in its heading")
        if check["command"] not in text:
            errors.append(f"exact command for {check['id']} is absent from the note")
        if normalized_whitespace(check["summary"]) not in normalized_whitespace(text):
            errors.append(f"observed summary for {check['id']} is absent from the note")
        artifact = check.get("artifact")
        if artifact and artifact["sha256"] not in text:
            errors.append(f"artifact hash for {check['id']} is absent from the note")


def validate_v3_git(manifest: dict[str, Any], text: str, errors: list[str]) -> None:
    git_data = manifest.get("git", {})
    if not git_data.get("available"):
        if manifest["mode"] == "coding-progress" and "unavailable" not in text.lower():
            errors.append("note must state that Git evidence is unavailable")
        return
    baseline = git_data["baseline"]
    final = git_data.get("final")
    if final is None:
        errors.append("Git evidence has not been finalized")
        return
    exact_values = {"final branch": final["branch"]}
    if final["head"]:
        exact_values["final HEAD"] = final["head"]
    elif not re.search(r"final\s+head[^\n]*unavailable", text, re.IGNORECASE):
        errors.append("note must state that final HEAD is unavailable")
    if baseline["baseline_head"]:
        exact_values["baseline HEAD"] = baseline["baseline_head"]
    elif not re.search(r"baseline\s+head[^\n]*unavailable", text, re.IGNORECASE):
        errors.append("note must state that baseline HEAD is unavailable")
    for label, value in exact_values.items():
        if value not in text:
            errors.append(f"{label} is absent from the note: {value}")
    for field in (
        "task_paths",
        "task_owned_changed_paths",
        "preexisting_paths",
        "preexisting_overlap",
        "outside_scope_changed_paths",
    ):
        for value in final[field]:
            if value not in text:
                errors.append(f"Git {field} path is absent from the note: {value}")
    if final.get("record_path") and final["record_path"] not in text:
        errors.append(f"Git record path is absent from the note: {final['record_path']}")
    relation = final.get("history_relation", "unavailable")
    if not re.search(rf"history\s+relation[^\n]*{re.escape(relation)}", text, re.IGNORECASE):
        errors.append(f"Git history relation is absent from the note: {relation}")
    for commit in final.get("commits_since_baseline", final.get("task_commits", [])):
        if commit["hash"] not in text or commit["subject"] not in text:
            errors.append(
                f"commit since baseline is absent or incomplete in the note: "
                f"{commit['hash']} {commit['subject']}"
            )
    summary_token = diff_summary_token(final["scoped_diff"])
    if normalized_whitespace(summary_token) not in normalized_whitespace(text):
        errors.append(f"scoped diff summary is absent from the note: {summary_token}")


def validate_note_v3(manifest: dict[str, Any], note: Path) -> list[str]:
    try:
        text = note.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"note does not exist: {note}"]
    errors = validate_v3_manifest(manifest)
    for label, value in expected_v3_metadata(manifest).items():
        if metadata_value(text, label) != value:
            errors.append(f"metadata {label} must match manifest: {value}")
    if re.search(r"<(?:Title|repository|project|task|path|temporary|YYYY)", text):
        errors.append("unresolved template placeholder found")
    note_headings = headings(text)
    mode_headings = CODING_HEADINGS if manifest["mode"] == "coding-progress" else SESSION_HEADINGS
    for heading in (*V3_COMMON_HEADINGS, *mode_headings):
        if heading not in note_headings:
            errors.append(f"missing required heading: ## {heading}")
    lifecycle_text = section_text(text, "Lifecycle")
    for event in manifest.get("lifecycle", []):
        event_values = (
            event["id"],
            event["at"],
            event["action"],
            event["from"],
            event["to"],
            event["actor"],
            event["reason"],
        )
        if not any(
            all(normalized_whitespace(value) in normalized_whitespace(line) for value in event_values)
            for line in lifecycle_text.splitlines()
        ):
            errors.append(f"lifecycle event {event['id']} is absent or incomplete in the note")
    for link in manifest.get("links", []):
        if not any(
            all(value in line for value in (link["id"], link["type"], link["target"]))
            for line in lifecycle_text.splitlines()
        ):
            errors.append(f"record link {link['id']} is absent or incomplete in the note")
    if (
        manifest.get("blocked_reason")
        and normalized_whitespace(manifest["blocked_reason"])
        not in normalized_whitespace(lifecycle_text)
    ):
        errors.append("current blocker reason is absent from the Lifecycle section")
    if not manifest.get("blocked_reason") and not re.search(
        r"current\s+blocker\s*:\s*`?None`?", lifecycle_text, re.IGNORECASE
    ):
        errors.append("Lifecycle must state Current blocker: None")
    validate_v3_sources(manifest, text, errors)
    if manifest["mode"] == "session-documentation":
        if metadata_value(text, "Implementation class") is not None:
            errors.append("session-documentation must omit Implementation class metadata")
        if not manifest["sources"]:
            errors.append("session-documentation requires at least one recorded source")
        for forbidden in SESSION_FORBIDDEN_HEADINGS:
            if forbidden in note_headings:
                errors.append(f"session-documentation forbids heading: ## {forbidden}")
        if manifest.get("checks"):
            errors.append("session-documentation manifest must not contain checks")
        if "git" in manifest:
            errors.append("session-documentation manifest must not contain Git evidence")
        return errors
    implementation = section_text(text, "Implementation")
    required_implementation_headings = (
        ("Preserved Contract", "Corrective Change")
        if manifest["implementation_kind"] == "function-fix"
        else ("Plan and Starting Status", "Core Functions and Result")
    )
    for heading in required_implementation_headings:
        if not has_level_three_heading(implementation, heading):
            errors.append(
                f"{manifest['implementation_kind']} records require implementation heading: ### {heading}"
            )
    validation = section_text(text, "Validation")
    if not has_level_three_heading(validation, "Test Result"):
        errors.append("coding records require validation heading: ### Test Result")
    validate_v3_checks(manifest, text, errors)
    validate_v3_git(manifest, text, errors)
    return errors


def command_validate(args: argparse.Namespace) -> None:
    manifest = load_manifest(Path(args.manifest).resolve())
    validator = validate_note_v3 if manifest["schema_version"] == 3 else validate_note_v2
    errors = validator(manifest, Path(args.note).resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(
        f"valid record v{manifest['schema_version']}; mode={manifest['mode']}; "
        f"implementation_kind={manifest.get('implementation_kind', 'legacy')}; "
        f"sources={len(manifest['sources'])}; checks={len(manifest['checks'])}"
    )


def split_metadata_list(value: str | None) -> list[str]:
    if not value or value in ("None", "unavailable"):
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def note_index_entry(path: Path, root: Path) -> dict[str, Any] | None:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    record_format = metadata_value(content, "Record format") or "1"
    date = metadata_value(content, "Date")
    status = metadata_value(content, "Status")
    project = metadata_value(content, "Project") or metadata_value(content, "Repository")
    if not date or not status or (not project and record_format == "1"):
        return None
    return {
        "path": path.relative_to(root).as_posix(),
        "record_format": record_format,
        "record_id": metadata_value(content, "Record ID") or "unavailable",
        "mode": metadata_value(content, "Mode") or "unavailable",
        "task_type": metadata_value(content, "Task type") or "unavailable",
        "status": status,
        "resolution": metadata_value(content, "Resolution") or "unavailable",
        "priority": metadata_value(content, "Priority") or "unavailable",
        "date": date,
        "project": project or "unavailable",
        "components": split_metadata_list(metadata_value(content, "Components")),
        "labels": split_metadata_list(metadata_value(content, "Labels")),
    }


def command_list(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise RecordError(f"list root is not a directory: {root}")
    since = validated_date(args.since, "since date") if args.since else None
    until = validated_date(args.until, "until date") if args.until else None
    if since and until and since > until:
        raise RecordError("--since must not be after --until")
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        entry = note_index_entry(path, root)
        if entry is None:
            continue
        scalar_filters = {
            "mode": args.mode,
            "task_type": args.task_type,
            "status": args.status,
            "resolution": args.resolution,
            "priority": args.priority,
        }
        if any(value and entry[field] != value for field, value in scalar_filters.items()):
            continue
        if args.component and args.component not in entry["components"]:
            continue
        if args.label and args.label not in entry["labels"]:
            continue
        if since and entry["date"] < since:
            continue
        if until and entry["date"] > until:
            continue
        entries.append(entry)
    if args.json:
        print(json.dumps(entries, indent=2, ensure_ascii=True, sort_keys=True))
        return
    columns = (
        ("DATE", "date"),
        ("FORMAT", "record_format"),
        ("RECORD ID", "record_id"),
        ("MODE", "mode"),
        ("TASK TYPE", "task_type"),
        ("STATUS", "status"),
        ("RESOLUTION", "resolution"),
        ("PRIORITY", "priority"),
        ("PATH", "path"),
    )
    widths = {
        key: max(len(header), *(len(str(entry[key])) for entry in entries))
        if entries
        else len(header)
        for header, key in columns
    }
    print("  ".join(header.ljust(widths[key]) for header, key in columns))
    for entry in entries:
        print("  ".join(str(entry[key]).ljust(widths[key]) for _, key in columns))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    start = subparsers.add_parser("start", help="create a temporary evidence manifest")
    start.add_argument(
        "--record-format",
        type=int,
        choices=SUPPORTED_SCHEMA_VERSIONS,
        default=2,
        help="manifest format (default: 2 for legacy CLI compatibility; new skill records use 3)",
    )
    start.add_argument("--mode", choices=MODES, required=True)
    start.add_argument("--implementation-kind", choices=IMPLEMENTATION_KINDS)
    start.add_argument("--task-type", choices=TASK_TYPES)
    start.add_argument("--task-slug")
    start.add_argument("--record-date")
    start.add_argument("--initial-status", choices=("proposed", "in-progress"), default="in-progress")
    start.add_argument("--priority", choices=PRIORITIES, default="unspecified")
    start.add_argument("--owner")
    start.add_argument("--component", action="append")
    start.add_argument("--label", action="append")
    start.add_argument("--started-at")
    start.add_argument("--due-date")
    start.add_argument("--repo", required=True)
    start.add_argument("--output", required=True)
    start.add_argument("--baseline-head")
    start.add_argument("--baseline-unavailable", action="store_true")
    start.set_defaults(func=command_start)

    source = subparsers.add_parser("add-source", help="add a material evidence source")
    source.add_argument("--manifest", required=True)
    source.add_argument("--kind", choices=SOURCE_KINDS, required=True)
    source.add_argument("--locator", required=True)
    source.add_argument("--sha256")
    source.add_argument("--file")
    source.set_defaults(func=command_add_source)

    check = subparsers.add_parser("add-check", help="record an observed validation check")
    check.add_argument("--manifest", required=True)
    check.add_argument("--command", required=True)
    check.add_argument("--result", choices=CHECK_RESULTS, required=True)
    check.add_argument("--summary", required=True)
    check.add_argument("--artifact")
    check.set_defaults(func=command_add_check)

    transition = subparsers.add_parser("transition", help="move a v3 record through its lifecycle")
    transition.add_argument("--manifest", required=True)
    transition.add_argument("--to", choices=V3_STATUSES, required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--reason", required=True)
    transition.add_argument("--resolution", choices=RESOLUTIONS)
    transition.add_argument("--at")
    transition.set_defaults(func=command_transition)

    link = subparsers.add_parser("add-link", help="add a local relationship to a v3 record")
    link.add_argument("--manifest", required=True)
    link.add_argument("--type", choices=LINK_TYPES, required=True)
    link.add_argument("--target", required=True)
    link.set_defaults(func=command_add_link)

    resume = subparsers.add_parser("resume", help="resume a terminal or finalized v3 record")
    resume.add_argument("--manifest", required=True)
    resume.add_argument("--actor", required=True)
    resume.add_argument("--reason", required=True)
    resume.add_argument("--at")
    resume.set_defaults(func=command_resume)

    finish = subparsers.add_parser("finish", help="capture final evidence")
    finish.add_argument("--manifest", required=True)
    finish.add_argument("--task-path", action="append")
    finish.add_argument("--record-path")
    finish.add_argument("--status", choices=V3_STATUSES)
    finish.add_argument("--evidence-state", choices=("verified", "mixed", "unverified"))
    finish.add_argument("--actor")
    finish.add_argument("--reason")
    finish.add_argument("--resolution", choices=RESOLUTIONS)
    finish.add_argument("--at")
    finish.add_argument(
        "--refresh",
        action="store_true",
        help="recapture final state while preserving the original baseline and evidence",
    )
    finish.set_defaults(func=command_finish)

    validate = subparsers.add_parser("validate", help="validate a v2 or v3 Markdown note")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--note", required=True)
    validate.set_defaults(func=command_validate)

    list_records = subparsers.add_parser("list", help="list local progress records")
    list_records.add_argument("--root", required=True)
    list_records.add_argument("--mode", choices=MODES)
    list_records.add_argument("--task-type", choices=TASK_TYPES)
    list_records.add_argument("--status")
    list_records.add_argument("--resolution")
    list_records.add_argument("--priority", choices=PRIORITIES)
    list_records.add_argument("--component")
    list_records.add_argument("--label")
    list_records.add_argument("--since")
    list_records.add_argument("--until")
    list_records.add_argument("--json", action="store_true")
    list_records.set_defaults(func=command_list)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except RecordError as exc:
        parser.exit(2, f"record_tool: error: {exc}\n")


if __name__ == "__main__":
    main()
