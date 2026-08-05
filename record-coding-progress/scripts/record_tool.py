#!/usr/bin/env python3
"""Collect and validate evidence for record-coding-progress v2 notes."""

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


SCHEMA_VERSION = 2
MODES = ("coding-progress", "session-documentation")
CHECK_RESULTS = ("pass", "fail", "partial", "not-run")
SOURCE_KINDS = ("user", "repository", "artifact", "web")
EVIDENCE_CLASSES = ("verified", "user-stated", "inferred", "proposed")
CODING_STATUSES = ("completed", "partial", "blocked")
SESSION_STATUSES = ("concluded", "proposed", "partial", "blocked")
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


class RecordError(Exception):
    """A user-facing manifest or repository error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
    if manifest.get("schema_version") != SCHEMA_VERSION:
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

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mode": args.mode,
        "repository": str(repository),
        "created_at": utc_now(),
        "sources": [],
        "checks": [],
        "finalized_at": None,
    }
    if args.mode == "coding-progress":
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
    elif args.baseline_head or args.baseline_unavailable:
        raise RecordError("baseline options are valid only in coding-progress mode")

    save_manifest(output, manifest)
    git_data = manifest.get("git", {})
    if git_data.get("available"):
        baseline = git_data["baseline"]
        baseline_value = baseline["baseline_head"] or "unavailable"
        print(
            f"created {output}; mode={args.mode}; baseline={baseline_value}; "
            f"dirty_paths={len(baseline['status_paths'])}"
        )
    else:
        print(f"created {output}; mode={args.mode}; git=not-recorded")


def command_add_source(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["finalized_at"]:
        raise RecordError("cannot add a source after manifest finalization")
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
    save_manifest(path, manifest)
    print(f"added {source_id}; kind={args.kind}")


def command_add_check(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["finalized_at"]:
        raise RecordError("cannot add a check after manifest finalization")
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
    save_manifest(path, manifest)
    print(f"added {check_id}; result={args.result}")


def command_finish(args: argparse.Namespace) -> None:
    path = Path(args.manifest).resolve()
    manifest = load_manifest(path)
    if manifest["finalized_at"] and not args.refresh:
        raise RecordError("manifest is already finalized; pass --refresh to recapture final state")
    task_paths = args.task_path or []
    if manifest["mode"] == "session-documentation":
        if task_paths or args.record_path:
            raise RecordError("task and record paths are forbidden in session-documentation mode")
        manifest["finalized_at"] = utc_now()
        save_manifest(path, manifest)
        print(f"finalized {path}; sources={len(manifest['sources'])}")
        return

    git_data = manifest["git"]
    if not git_data["available"]:
        if task_paths or args.record_path:
            raise RecordError("task and record paths require a Git checkout")
        git_data["final"] = None
        manifest["finalized_at"] = utc_now()
        save_manifest(path, manifest)
        print(f"finalized {path}; git=unavailable; checks={len(manifest['checks'])}")
        return

    root = Path(git_data["baseline"]["root"])
    scopes = sorted(set(normalized_scope(root, item) for item in task_paths))
    record_path = normalized_scope(root, args.record_path) if args.record_path else None
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
    manifest["finalized_at"] = utc_now()
    save_manifest(path, manifest)
    print(
        f"finalized {path}; owned={len(owned)}; overlap={len(overlap)}; "
        f"outside_scope={len(outside)}; checks={len(manifest['checks'])}"
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


def validate_note(manifest: dict[str, Any], note: Path) -> list[str]:
    try:
        text = note.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"note does not exist: {note}"]

    errors: list[str] = []
    if metadata_value(text, "Record format") != str(SCHEMA_VERSION):
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
    allowed_statuses = CODING_STATUSES if manifest["mode"] == "coding-progress" else SESSION_STATUSES
    if status not in allowed_statuses:
        errors.append(f"metadata Status must be one of: {', '.join(allowed_statuses)}")
    if not metadata_value(text, "Project"):
        errors.append("metadata Project is required")
    if re.search(r"<(?:Title|repository|project|task|path|temporary|YYYY)", text):
        errors.append("unresolved template placeholder found")

    note_headings = headings(text)
    for heading in (*COMMON_HEADINGS, *(CODING_HEADINGS if manifest["mode"] == "coding-progress" else SESSION_HEADINGS)):
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


def command_validate(args: argparse.Namespace) -> None:
    manifest = load_manifest(Path(args.manifest).resolve())
    errors = validate_note(manifest, Path(args.note).resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(
        f"valid record v{SCHEMA_VERSION}; mode={manifest['mode']}; "
        f"sources={len(manifest['sources'])}; checks={len(manifest['checks'])}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    start = subparsers.add_parser("start", help="create a temporary evidence manifest")
    start.add_argument("--mode", choices=MODES, required=True)
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

    finish = subparsers.add_parser("finish", help="capture final evidence")
    finish.add_argument("--manifest", required=True)
    finish.add_argument("--task-path", action="append")
    finish.add_argument("--record-path")
    finish.add_argument(
        "--refresh",
        action="store_true",
        help="recapture final state while preserving the original baseline and evidence",
    )
    finish.set_defaults(func=command_finish)

    validate = subparsers.add_parser("validate", help="validate a v2 Markdown note")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--note", required=True)
    validate.set_defaults(func=command_validate)
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
