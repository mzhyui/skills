#!/usr/bin/env python3
"""Record, summarize, and verify durable server/task status snapshots."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SNAPSHOT_SCHEMA_VERSION = 2
SUPPORTED_SNAPSHOT_SCHEMAS = {1, 2}
RECORD_SCHEMA_VERSION = 1
LATEST_SCHEMA_VERSION = 2
EVENT_TYPES = {
    "status_check",
    "assignment",
    "reassignment",
    "dispatch",
    "recovery",
    "shutdown",
}
VERDICTS = {
    "assigned",
    "blocked",
    "complete",
    "dispatched",
    "failed",
    "queued",
    "running",
    "unknown",
}
REACHABILITY = {"reachable", "unreachable", "partial", "unknown"}
DIRECT_CHECK = {"fresh", "stale", "unavailable", "unknown"}
AUTHORITIES = {"completion", "progress", "liveness", "context"}
EVIDENCE_CHANNELS = {"direct", "fallback", "artifact", "history"}
PREFLIGHT_VERDICTS = {"passed", "blocked", "failed", "unknown"}
DISPATCH_STATES = {"not_started", "queued", "running", "complete", "failed"}
ASSIGNMENT_ACTIONS = {"assign", "reassign", "dispatch"}
COMPLETION_ADAPTERS = {"legacy-v1", "selective-v11"}
FORBIDDEN_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "cookie",
    "cookies",
    "password",
    "passwd",
    "private_key",
    "refresh_token",
    "secret",
    "ssh_private_key",
    "token",
}


class LedgerError(ValueError):
    """Raised when a snapshot or ledger violates its contract."""


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise LedgerError(f"{field} must be a non-empty ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LedgerError(f"{field} is not a valid ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LedgerError(f"{field} must include a timezone")
    return parsed


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LedgerError(f"{field} must be an object")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LedgerError(f"{field} must be a non-empty string")
    return value.strip()


def require_enum(value: Any, field: str, allowed: set[str]) -> str:
    result = require_string(value, field)
    if result not in allowed:
        raise LedgerError(f"unsupported {field}: {result}")
    return result


def require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise LedgerError(f"{field} must be a list of non-empty strings")
    return value


def scan_for_secrets(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            forbidden_suffixes = (
                "_api_key",
                "_password",
                "_private_key",
                "_secret",
                "_token",
            )
            if normalized in FORBIDDEN_KEYS or normalized.endswith(
                forbidden_suffixes
            ):
                raise LedgerError(f"secret-bearing field is forbidden: {path}.{key}")
            scan_for_secrets(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_for_secrets(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if "-----BEGIN" in value and "PRIVATE KEY-----" in value:
            raise LedgerError(f"private-key material is forbidden: {path}")
        if re.search(r"://[^/@:\s]+:[^/@\s]+@", value):
            raise LedgerError(f"credential-bearing URL is forbidden: {path}")
        if re.search(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", value, re.IGNORECASE):
            raise LedgerError(f"bearer credential is forbidden: {path}")


def validate_assignment(root: dict[str, Any], event_type: str, strict: bool) -> None:
    if event_type not in {"assignment", "reassignment", "dispatch"}:
        return
    assignment = require_mapping(root.get("assignment"), "assignment")
    if strict:
        action = require_enum(
            assignment.get("action"), "assignment.action", ASSIGNMENT_ACTIONS
        )
        expected = {
            "assignment": "assign",
            "reassignment": "reassign",
            "dispatch": "dispatch",
        }[event_type]
        if action != expected:
            raise LedgerError(
                f"assignment.action must be {expected!r} for {event_type}"
            )
        preflight = require_enum(
            assignment.get("preflight_verdict"),
            "assignment.preflight_verdict",
            PREFLIGHT_VERDICTS,
        )
        dispatch_state = require_enum(
            assignment.get("dispatch_state"),
            "assignment.dispatch_state",
            DISPATCH_STATES,
        )
        if event_type == "dispatch" and preflight != "passed":
            raise LedgerError("dispatch requires assignment.preflight_verdict=passed")
        if event_type != "dispatch" and dispatch_state != "not_started":
            raise LedgerError(
                f"{event_type} requires assignment.dispatch_state=not_started"
            )
        for field in ("cell_ids", "task_ids", "constraints"):
            require_string_list(
                assignment.get(field, []), f"assignment.{field}"
            )
        resources = require_mapping(
            assignment.get("resources", {}), "assignment.resources"
        )
        gpu_ids = resources.get("gpu_ids", [])
        if not isinstance(gpu_ids, list) or not all(
            isinstance(item, int) and item >= 0 for item in gpu_ids
        ):
            raise LedgerError(
                "assignment.resources.gpu_ids must be non-negative integers"
            )
    else:
        require_string(assignment.get("action"), "assignment.action")
        require_string(
            assignment.get("preflight_verdict"), "assignment.preflight_verdict"
        )
        require_string(
            assignment.get("dispatch_state"), "assignment.dispatch_state"
        )
    require_string(
        assignment.get("target_machine_id"), "assignment.target_machine_id"
    )


def validate_snapshot(snapshot: Any) -> dict[str, Any]:
    root = require_mapping(snapshot, "snapshot")
    scan_for_secrets(root)
    schema_version = root.get("schema_version")
    if schema_version not in SUPPORTED_SNAPSHOT_SCHEMAS:
        raise LedgerError(
            "schema_version must be one of "
            f"{sorted(SUPPORTED_SNAPSHOT_SCHEMAS)}"
        )
    strict = schema_version == SNAPSHOT_SCHEMA_VERSION

    event_type = require_enum(root.get("event_type"), "event_type", EVENT_TYPES)
    parse_timestamp(root.get("observed_at"), "observed_at")

    machine = require_mapping(root.get("machine"), "machine")
    machine_id = require_string(machine.get("machine_id"), "machine.machine_id")
    require_string(machine.get("kind"), "machine.kind")
    reachability = require_enum(
        machine.get("reachability"), "machine.reachability", REACHABILITY
    )

    scope = require_mapping(root.get("scope"), "scope")
    require_string(scope.get("scope_id"), "scope.scope_id")
    for field in ("cell_ids", "task_ids"):
        require_string_list(scope.get(field, []), f"scope.{field}")

    freshness = require_mapping(root.get("freshness"), "freshness")
    require_enum(
        freshness.get("direct_check"), "freshness.direct_check", DIRECT_CHECK
    )
    if not isinstance(freshness.get("fallback_used"), bool):
        raise LedgerError("freshness.fallback_used must be Boolean")
    fallback_used = freshness["fallback_used"]
    if fallback_used:
        fallback_machine_id = require_string(
            freshness.get("fallback_machine_id"),
            "freshness.fallback_machine_id",
        )
        if fallback_machine_id == machine_id:
            raise LedgerError("fallback machine must differ from requested machine")
        if strict and not freshness.get("shared_custody_verified") is True:
            raise LedgerError(
                "fallback requires freshness.shared_custody_verified=true"
            )

    status = require_mapping(root.get("status"), "status")
    verdict = require_string(status.get("verdict"), "status.verdict")
    if strict and verdict not in VERDICTS:
        raise LedgerError(f"unsupported status.verdict: {verdict}")
    require_string(status.get("summary"), "status.summary")
    if not isinstance(status.get("completion_evidence"), bool):
        raise LedgerError("status.completion_evidence must be Boolean")
    completion_evidence = status["completion_evidence"]
    adapter = status.get("workflow_adapter")
    if strict:
        adapter = require_string(adapter, "status.workflow_adapter")
        require_string(root.get("evidence_boundary"), "evidence_boundary")

    evidence = root.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise LedgerError("evidence must be a non-empty list")
    has_completion = False
    has_progress = False
    has_direct_liveness = False
    for index, row_value in enumerate(evidence):
        row = require_mapping(row_value, f"evidence[{index}]")
        require_string(row.get("kind"), f"evidence[{index}].kind")
        require_string(row.get("source"), f"evidence[{index}].source")
        require_string(row.get("summary"), f"evidence[{index}].summary")
        authority = require_enum(
            row.get("authority"), f"evidence[{index}].authority", AUTHORITIES
        )
        has_completion = has_completion or authority == "completion"
        has_progress = has_progress or authority == "progress"
        if row.get("observed_at") is not None:
            parse_timestamp(row["observed_at"], f"evidence[{index}].observed_at")
        if strict:
            channel = require_enum(
                row.get("channel"),
                f"evidence[{index}].channel",
                EVIDENCE_CHANNELS,
            )
            has_direct_liveness = has_direct_liveness or (
                authority == "liveness" and channel == "direct"
            )
            if (
                fallback_used
                and reachability == "unreachable"
                and channel == "fallback"
                and authority == "liveness"
            ):
                raise LedgerError(
                    "fallback evidence cannot establish unavailable-host liveness"
                )

    if completion_evidence and not has_completion:
        raise LedgerError(
            "completion_evidence=true requires completion-authority evidence"
        )
    if strict and verdict == "complete":
        if not completion_evidence:
            raise LedgerError("complete verdict requires completion_evidence=true")
        if adapter not in COMPLETION_ADAPTERS:
            raise LedgerError(
                "complete verdict requires a completion-capable workflow adapter"
            )
    if strict and verdict == "running" and adapter != "legacy-v1":
        if reachability != "reachable" or not has_direct_liveness or not has_progress:
            raise LedgerError(
                "generic running verdict requires reachable direct liveness "
                "and progress evidence"
            )
    if strict and adapter == "selective-v11" and verdict == "complete":
        required = {
            "workflow_state": "ready_to_bind",
            "assets_retained": True,
            "retained_assets_verified": True,
            "labels_opened": False,
            "matrix_bound": False,
        }
        for field, expected in required.items():
            if status.get(field) != expected:
                raise LedgerError(
                    f"selective-v11 completion requires status.{field}="
                    f"{expected!r}"
                )

    for field in ("related_records", "notes"):
        values = root.get(field, [])
        if not isinstance(values, list) or not all(
            isinstance(item, str) for item in values
        ):
            raise LedgerError(f"{field} must be a list of strings")

    validate_assignment(root, event_type, strict)
    return root


def normalize_snapshot_v2(snapshot: Any) -> dict[str, Any]:
    source = validate_snapshot(snapshot)
    if source["schema_version"] == SNAPSHOT_SCHEMA_VERSION:
        return source
    normalized = json.loads(json.dumps(source))
    normalized["schema_version"] = SNAPSHOT_SCHEMA_VERSION
    normalized.setdefault(
        "evidence_boundary",
        "Only the cited evidence at the recorded observation time is established.",
    )
    freshness = normalized["freshness"]
    if freshness["fallback_used"]:
        freshness.setdefault("shared_custody_verified", True)
    status = normalized["status"]
    status.setdefault("workflow_adapter", "legacy-v1")
    for row in normalized["evidence"]:
        if "channel" not in row:
            if row["authority"] == "context":
                row["channel"] = "history"
            elif freshness["fallback_used"] and row["authority"] != "liveness":
                row["channel"] = "fallback"
            elif row["authority"] == "completion":
                row["channel"] = "artifact"
            else:
                row["channel"] = "direct"
    assignment = normalized.get("assignment")
    if assignment is not None:
        action_by_event = {
            "assignment": "assign",
            "reassignment": "reassign",
            "dispatch": "dispatch",
        }
        assignment["action"] = action_by_event[normalized["event_type"]]
        assignment.setdefault("cell_ids", normalized["scope"].get("cell_ids", []))
        assignment.setdefault("task_ids", normalized["scope"].get("task_ids", []))
        assignment.setdefault("constraints", [])
        assignment.setdefault("resources", {"gpu_ids": []})
        if normalized["event_type"] != "dispatch":
            assignment["dispatch_state"] = "not_started"
    return validate_snapshot(normalized)


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized[:80] or "unknown"


def repository_head(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None
    return result.stdout.strip() or None


def resolve_ledger_root(repo_root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise LedgerError("ledger root must remain inside the repository") from exc
    return resolved


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerError(f"cannot read valid JSON from {path}") from exc


def read_history(history_path: Path) -> list[dict[str, Any]]:
    if not history_path.exists():
        return []
    entries = []
    for line_number, line in enumerate(
        history_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            raise LedgerError(f"blank history line at {line_number}")
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerError(f"invalid history JSON at line {line_number}") from exc
        if not isinstance(entry, dict):
            raise LedgerError(f"history line {line_number} is not an object")
        entries.append(entry)
    return entries


def read_last_history_entry(history_path: Path) -> dict[str, Any] | None:
    if not history_path.exists() or history_path.stat().st_size == 0:
        return None
    with history_path.open("rb") as handle:
        position = handle.seek(0, os.SEEK_END)
        buffer = bytearray()
        while position:
            position -= 1
            handle.seek(position)
            value = handle.read(1)
            if value == b"\n" and buffer:
                break
            if value != b"\n":
                buffer.extend(value)
    try:
        result = json.loads(bytes(reversed(buffer)).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LedgerError("invalid final history entry") from exc
    if not isinstance(result, dict):
        raise LedgerError("final history entry is not an object")
    return result


def validate_history_entry(entry: dict[str, Any], sequence: int | None = None) -> None:
    if sequence is not None and entry.get("sequence") != sequence:
        raise LedgerError(f"history sequence mismatch at {sequence}")
    stored = entry.get("entry_sha256")
    if not isinstance(stored, str):
        raise LedgerError("history entry hash is missing")
    base = dict(entry)
    del base["entry_sha256"]
    if stored != sha256_bytes(canonical_bytes(base)):
        raise LedgerError(
            f"history hash mismatch at {entry.get('sequence', 'unknown')}"
        )


def validate_history_chain(entries: list[dict[str, Any]]) -> None:
    previous = None
    for expected_sequence, entry in enumerate(entries, start=1):
        validate_history_entry(entry, expected_sequence)
        if entry.get("previous_entry_sha256") != previous:
            raise LedgerError(f"history predecessor mismatch at {expected_sequence}")
        previous = entry["entry_sha256"]


def append_history(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical_bytes(entry))
        handle.flush()
        os.fsync(handle.fileno())


def scope_summary(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_type": entry["event_type"],
        "machine_id": entry["machine_id"],
        "observed_at": entry["observed_at"],
        "scope_id": entry["scope_id"],
        "snapshot_file_sha256": entry["snapshot_file_sha256"],
        "snapshot_path": entry["snapshot_path"],
        "snapshot_sha256": entry["snapshot_sha256"],
        "verdict": entry["verdict"],
    }


def latest_scopes_from_history(entries: list[dict[str, Any]]) -> dict[str, Any]:
    scopes = {}
    for entry in entries:
        scopes[f"{entry['machine_id']}|{entry['scope_id']}"] = scope_summary(entry)
    return scopes


def latest_document(
    entries: list[dict[str, Any]],
    scopes: dict[str, Any] | None = None,
    full_verified_at: str | None = None,
) -> dict[str, Any]:
    tip = entries[-1] if entries else None
    return {
        "schema_version": LATEST_SCHEMA_VERSION,
        "full_verification": {
            "entry_sha256": tip["entry_sha256"] if tip else None,
            "sequence": tip["sequence"] if tip else 0,
            "verified_at": full_verified_at,
        },
        "history": {
            "entries": tip["sequence"] if tip else 0,
            "tip_entry_sha256": tip["entry_sha256"] if tip else None,
        },
        "scopes": scopes if scopes is not None else latest_scopes_from_history(entries),
        "updated_at": tip["recorded_at"] if tip else None,
    }


def write_latest(
    ledger_root: Path,
    entries: list[dict[str, Any]],
    scopes: dict[str, Any] | None = None,
    full_verified_at: str | None = None,
) -> None:
    if not entries and not (ledger_root / "latest.json").exists():
        return
    atomic_write(
        ledger_root / "latest.json",
        canonical_bytes(
            latest_document(entries, scopes, full_verified_at=full_verified_at)
        ),
    )


def verify_snapshot_entry(repo_root: Path, entry: dict[str, Any]) -> None:
    relative = Path(entry["snapshot_path"])
    snapshot_path = repo_root / relative
    if not snapshot_path.is_file():
        raise LedgerError(f"snapshot file is missing: {relative}")
    if sha256_file(snapshot_path) != entry["snapshot_file_sha256"]:
        raise LedgerError(f"snapshot file hash mismatch: {relative}")
    envelope = load_json(snapshot_path)
    if envelope.get("record_schema_version") != RECORD_SCHEMA_VERSION:
        raise LedgerError(f"snapshot record schema mismatch: {relative}")
    snapshot = validate_snapshot(envelope.get("snapshot"))
    calculated_payload = sha256_bytes(canonical_bytes(snapshot))
    if calculated_payload != envelope.get("snapshot_sha256"):
        raise LedgerError(f"snapshot payload hash mismatch: {relative}")
    if calculated_payload != entry["snapshot_sha256"]:
        raise LedgerError(f"history payload hash mismatch: {relative}")


def verify_full(repo_root: Path, ledger_root: Path, refresh_index: bool) -> dict[str, Any]:
    history_path = ledger_root / "history.jsonl"
    entries = read_history(history_path)
    validate_history_chain(entries)
    paths_seen = set()
    for entry in entries:
        relative = Path(entry["snapshot_path"])
        if relative in paths_seen:
            raise LedgerError(f"duplicate snapshot path in history: {relative}")
        paths_seen.add(relative)
        verify_snapshot_entry(repo_root, entry)

    expected = latest_scopes_from_history(entries)
    latest_path = ledger_root / "latest.json"
    if latest_path.exists():
        current = load_json(latest_path)
        if current.get("schema_version") not in {1, LATEST_SCHEMA_VERSION}:
            raise LedgerError("latest.json schema mismatch")
        if current.get("scopes") != expected:
            raise LedgerError("latest.json does not match history")
    elif entries:
        raise LedgerError("latest.json is missing")

    verified_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if refresh_index:
        write_latest(
            ledger_root,
            entries,
            scopes=expected,
            full_verified_at=verified_at,
        )
    return {
        "entries": len(entries),
        "latest_scopes": len(expected),
        "ledger_root": str(ledger_root.relative_to(repo_root)),
        "mode": "full",
        "verified": True,
    }


def verify_tail(repo_root: Path, ledger_root: Path) -> dict[str, Any]:
    latest_path = ledger_root / "latest.json"
    history_path = ledger_root / "history.jsonl"
    if not latest_path.exists():
        if history_path.exists() and history_path.stat().st_size:
            raise LedgerError("latest index is missing; run verify --mode full")
        return {
            "entries": 0,
            "latest_scopes": 0,
            "ledger_root": str(ledger_root.relative_to(repo_root)),
            "mode": "tail",
            "verified": True,
        }
    latest = load_json(latest_path)
    if latest.get("schema_version") != LATEST_SCHEMA_VERSION:
        raise LedgerError("tail verification requires a v2 latest index")
    last = read_last_history_entry(history_path)
    history = require_mapping(latest.get("history"), "latest.history")
    if last is None:
        if history.get("entries") != 0 or latest.get("scopes") != {}:
            raise LedgerError("latest index is non-empty without history")
        entries = 0
    else:
        validate_history_entry(last)
        if history.get("entries") != last["sequence"]:
            raise LedgerError("latest history count does not match chain tip")
        if history.get("tip_entry_sha256") != last["entry_sha256"]:
            raise LedgerError("latest history tip does not match chain tip")
        key = f"{last['machine_id']}|{last['scope_id']}"
        if latest.get("scopes", {}).get(key) != scope_summary(last):
            raise LedgerError("latest scope does not match chain tip")
        verify_snapshot_entry(repo_root, last)
        entries = last["sequence"]
    checkpoint = require_mapping(
        latest.get("full_verification"), "latest.full_verification"
    )
    checkpoint_sequence = checkpoint.get("sequence")
    if not isinstance(checkpoint_sequence, int) or not 0 <= checkpoint_sequence <= entries:
        raise LedgerError("invalid full-verification checkpoint")
    if checkpoint_sequence and not isinstance(checkpoint.get("entry_sha256"), str):
        raise LedgerError("full-verification checkpoint hash is missing")
    return {
        "entries": entries,
        "latest_scopes": len(latest.get("scopes", {})),
        "ledger_root": str(ledger_root.relative_to(repo_root)),
        "mode": "tail",
        "verified": True,
    }


def record_snapshot(
    repo_root: Path, ledger_root: Path, snapshot: dict[str, Any]
) -> dict[str, Any]:
    snapshot_sha = sha256_bytes(canonical_bytes(snapshot))
    observed = parse_timestamp(snapshot["observed_at"], "observed_at")
    timestamp_slug = observed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    machine_id = snapshot["machine"]["machine_id"]
    scope_id = snapshot["scope"]["scope_id"]
    event_type = snapshot["event_type"]
    filename = (
        f"{timestamp_slug}--{slug(machine_id)}--{slug(scope_id)}--"
        f"{slug(event_type)}--{snapshot_sha[:12]}.json"
    )
    relative = Path(ledger_root.relative_to(repo_root)) / "snapshots" / filename
    snapshot_path = repo_root / relative
    recorded_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    envelope = {
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "repository_head": repository_head(repo_root),
        "repository_root": str(repo_root),
        "snapshot": snapshot,
        "snapshot_sha256": snapshot_sha,
    }
    content = canonical_bytes(envelope)
    history_path = ledger_root / "history.jsonl"
    latest_path = ledger_root / "latest.json"

    if latest_path.exists() and load_json(latest_path).get(
        "schema_version"
    ) == LATEST_SCHEMA_VERSION:
        verify_tail(repo_root, ledger_root)
        latest = load_json(latest_path)
        last = read_last_history_entry(history_path)
        entries_count = last["sequence"] if last else 0
        scopes = dict(latest.get("scopes", {}))
        full_verification = latest.get("full_verification", {})
    else:
        verify_full(repo_root, ledger_root, refresh_index=True)
        latest = load_json(latest_path) if latest_path.exists() else latest_document([])
        last = read_last_history_entry(history_path)
        entries_count = last["sequence"] if last else 0
        scopes = dict(latest.get("scopes", {}))
        full_verification = latest.get("full_verification", {})

    if snapshot_path.exists():
        existing = load_json(snapshot_path)
        if existing.get("record_schema_version") != RECORD_SCHEMA_VERSION:
            raise LedgerError(f"untracked snapshot schema mismatch: {relative}")
        existing_snapshot = validate_snapshot(existing.get("snapshot"))
        if sha256_bytes(canonical_bytes(existing_snapshot)) != snapshot_sha:
            raise LedgerError(f"conflicting existing snapshot: {relative}")
        for entry in read_history(history_path):
            if entry["snapshot_path"] == str(relative):
                if entry["snapshot_sha256"] != snapshot_sha:
                    raise LedgerError(f"conflicting history snapshot: {relative}")
                verify_snapshot_entry(repo_root, entry)
                return {
                    "history_sequence": entry["sequence"],
                    "idempotent": True,
                    "schema_version": snapshot["schema_version"],
                    "snapshot_file_sha256": entry["snapshot_file_sha256"],
                    "snapshot_path": str(relative),
                    "snapshot_sha256": snapshot_sha,
                }
        recorded_at = require_string(existing.get("recorded_at"), "recorded_at")
        parse_timestamp(recorded_at, "recorded_at")
    else:
        atomic_write(snapshot_path, content)
    file_sha = sha256_file(snapshot_path)
    entry_base = {
        "event_type": event_type,
        "machine_id": machine_id,
        "observed_at": snapshot["observed_at"],
        "previous_entry_sha256": last["entry_sha256"] if last else None,
        "recorded_at": recorded_at,
        "scope_id": scope_id,
        "sequence": entries_count + 1,
        "snapshot_file_sha256": file_sha,
        "snapshot_path": str(relative),
        "snapshot_sha256": snapshot_sha,
        "verdict": snapshot["status"]["verdict"],
    }
    entry = dict(entry_base)
    entry["entry_sha256"] = sha256_bytes(canonical_bytes(entry_base))
    append_history(history_path, entry)
    scopes[f"{machine_id}|{scope_id}"] = scope_summary(entry)
    current_entries = [entry]
    document = latest_document(
        current_entries,
        scopes=scopes,
        full_verified_at=full_verification.get("verified_at"),
    )
    document["full_verification"] = full_verification
    document["history"] = {
        "entries": entry["sequence"],
        "tip_entry_sha256": entry["entry_sha256"],
    }
    atomic_write(latest_path, canonical_bytes(document))
    verify_tail(repo_root, ledger_root)
    return {
        "history_sequence": entry["sequence"],
        "idempotent": False,
        "schema_version": snapshot["schema_version"],
        "snapshot_file_sha256": file_sha,
        "snapshot_path": str(relative),
        "snapshot_sha256": snapshot_sha,
    }


def compact_envelope(envelope: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    snapshot = envelope["snapshot"]
    status = snapshot["status"]
    return {
        "completion_evidence": status["completion_evidence"],
        "evidence_boundary": snapshot.get(
            "evidence_boundary",
            "Legacy v1 snapshot; only cited evidence at its observation time applies.",
        ),
        "event_type": snapshot["event_type"],
        "fallback_used": snapshot["freshness"]["fallback_used"],
        "machine_id": snapshot["machine"]["machine_id"],
        "observed_at": snapshot["observed_at"],
        "schema_version": snapshot["schema_version"],
        "scope_id": snapshot["scope"]["scope_id"],
        "snapshot_path": summary["snapshot_path"],
        "snapshot_sha256": summary["snapshot_sha256"],
        "summary": status["summary"],
        "verdict": status["verdict"],
        "workflow_adapter": status.get("workflow_adapter", "legacy-v1"),
        "workflow_state": status.get("workflow_state"),
    }


def lock_path_for(repo_root: Path) -> Path:
    key = hashlib.sha256(str(repo_root).encode("utf-8")).hexdigest()[:16]
    return Path("/tmp") / f"server-task-status-{key}.lock"


def command_record(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        raise LedgerError(f"repository does not exist: {repo_root}")
    ledger_root = resolve_ledger_root(repo_root, args.ledger_root)
    snapshot = normalize_snapshot_v2(load_json(Path(args.input)))
    lock_path = lock_path_for(repo_root)
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        return record_snapshot(repo_root, ledger_root, snapshot)


def command_verify(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    ledger_root = resolve_ledger_root(repo_root, args.ledger_root)
    lock_path = lock_path_for(repo_root)
    lock_mode = fcntl.LOCK_EX if args.mode == "full" else fcntl.LOCK_SH
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), lock_mode)
        if args.mode == "full":
            return verify_full(repo_root, ledger_root, refresh_index=True)
        return verify_tail(repo_root, ledger_root)


def command_latest(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    ledger_root = resolve_ledger_root(repo_root, args.ledger_root)
    latest_path = ledger_root / "latest.json"
    if not latest_path.exists():
        return {"matches": [], "message": "no status snapshots recorded"}
    if args.format == "compact":
        verify_tail(repo_root, ledger_root)
    else:
        verify_full(repo_root, ledger_root, refresh_index=False)
    latest = load_json(latest_path)
    matches = []
    for value in latest.get("scopes", {}).values():
        if args.machine_id and value["machine_id"] != args.machine_id:
            continue
        if args.scope_id and value["scope_id"] != args.scope_id:
            continue
        envelope = load_json(repo_root / value["snapshot_path"])
        matches.append(
            compact_envelope(envelope, value)
            if args.format == "compact"
            else envelope
        )
    if args.format == "compact":
        matches.sort(key=lambda item: (item["machine_id"], item["scope_id"]))
    else:
        matches.sort(
            key=lambda item: (
                item["snapshot"]["machine"]["machine_id"],
                item["snapshot"]["scope"]["scope_id"],
            )
        )
    return {"format": args.format, "matches": matches}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Maintain a hash-chained server/task status ledger."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--repo-root", required=True)
        subparser.add_argument(
            "--ledger-root", default="progress/server-task-status"
        )

    record = subparsers.add_parser("record", help="Record one v2 status snapshot.")
    add_common(record)
    record.add_argument("--input", required=True)
    record.set_defaults(handler=command_record)

    verify = subparsers.add_parser("verify", help="Verify the status ledger.")
    add_common(verify)
    verify.add_argument("--mode", choices=("tail", "full"), default="full")
    verify.set_defaults(handler=command_verify)

    latest = subparsers.add_parser("latest", help="Read latest snapshots.")
    add_common(latest)
    latest.add_argument("--machine-id")
    latest.add_argument("--scope-id")
    latest.add_argument("--format", choices=("compact", "full"), default="full")
    latest.set_defaults(handler=command_latest)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
    except LedgerError as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
