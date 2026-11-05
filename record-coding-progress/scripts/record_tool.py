#!/usr/bin/env python3
"""Capture Git custody, validate, and list record-coding-progress notes (format 4)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


RECORD_FORMAT = "4"
SNAPSHOT_VERSION = 1
KINDS = ("implementation", "evaluation", "session")
STATUSES = ("done", "partial", "blocked")
CHANGE_TYPES = ("fix", "new")
CHECK_RESULT = re.compile(r"`(pass|fail|partial|not-run)`")
# Body sections in reading order; a leading "?" marks an optional section.
BODY_SECTIONS = {
    "implementation": ("Outcome", "Change", "?Interface changes", "Checks", "Open items"),
    "evaluation": ("Readout", "Setup", "?Detailed results", "Correctness checks", "Open items"),
    "session": ("Takeaways", "Method", "Discussion", "Decisions", "?Design or plan", "Open items"),
}
APPENDIX_SECTIONS = {
    "implementation": ("Record details", "Commands", "Git"),
    "evaluation": ("Record details", "Commands", "Git"),
    "session": ("Record details", "Sources"),
}
HEADLINE_SECTIONS = ("Readout", "Takeaways", "Outcome")
HTML_TAGS = frozenset(
    "a abbr b br code details div em hr i img kbd li ol p pre s span strong sub summary sup "
    "table tbody td th thead tr u ul".split()
)


class RecordError(Exception):
    """A user-facing input, repository, or note error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validated_date(value: str, label: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise RecordError(f"{label} must be YYYY-MM-DD: {value}") from exc
    return value


# --- Git -------------------------------------------------------------------


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


def require_git_root(repo: Path) -> Path:
    root = git_root(repo)
    if root is None:
        raise RecordError(f"not a Git repository: {repo}; write `Git: not applicable` instead")
    return root


def git_branch(root: Path) -> str:
    result = run_git(root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else "detached"


def git_head(root: Path) -> str | None:
    result = run_git(root, ["rev-parse", "--verify", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def nul_paths(root: Path, args: list[str]) -> set[str]:
    return {item for item in run_git(root, args).stdout.split("\0") if item}


def untracked_paths(root: Path) -> set[str]:
    return nul_paths(root, ["ls-files", "--others", "--exclude-standard", "-z"])


def working_tree_paths(root: Path) -> list[str]:
    paths = nul_paths(root, ["diff", "--name-only", "-z", "--"])
    paths |= nul_paths(root, ["diff", "--cached", "--name-only", "-z", "--"])
    return sorted(paths | untracked_paths(root))


def changed_paths_since(root: Path, baseline: str | None) -> list[str]:
    paths = set(working_tree_paths(root))
    if baseline:
        paths |= nul_paths(root, ["diff", "--name-only", "-z", baseline, "--"])
    return sorted(paths)


def verify_commit(root: Path, value: str) -> str:
    result = run_git(root, ["rev-parse", "--verify", f"{value}^{{commit}}"], check=False)
    if result.returncode != 0:
        raise RecordError(f"baseline commit is not valid in {root}: {value}")
    return result.stdout.strip()


def normalized_scope(root: Path, value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(root)
        except ValueError as exc:
            raise RecordError(f"task path is outside the repository: {value}") from exc
    normalized = PurePosixPath(candidate.as_posix())
    if normalized.is_absolute() or ".." in normalized.parts:
        raise RecordError(f"task path must stay inside the repository: {value}")
    text = normalized.as_posix().rstrip("/")
    if text in ("", "."):
        raise RecordError("the repository root cannot be a task path; list the changed paths")
    return text


def scope_matches(path: str, scopes: Iterable[str]) -> bool:
    return any(path == scope or path.startswith(f"{scope}/") for scope in scopes)


def diff_summary(root: Path, baseline: str | None, scopes: list[str]) -> dict[str, Any]:
    """Count changed lines inside the task scopes and say what they were compared with."""
    if baseline:
        args, basis = ["diff", "--numstat", baseline, "--"], "baseline to working tree"
    elif git_head(root):
        args, basis = ["diff", "--numstat", "HEAD", "--"], "uncommitted changes only; no baseline"
    else:
        args, basis = ["diff", "--cached", "--numstat", "--"], "staged changes; no commits yet"
    summary: dict[str, Any] = {
        "files": 0,
        "insertions": 0,
        "deletions": 0,
        "binary_files": 0,
        "untracked_files": 0,
        "basis": basis,
    }
    for line in run_git(root, [*args, *scopes]).stdout.splitlines():
        fields = line.split("\t", 2)
        if len(fields) < 3:
            continue
        summary["files"] += 1
        if fields[0] == "-" or fields[1] == "-":
            summary["binary_files"] += 1
        else:
            summary["insertions"] += int(fields[0])
            summary["deletions"] += int(fields[1])
    summary["untracked_files"] = sum(1 for path in untracked_paths(root) if scope_matches(path, scopes))
    return summary


def history_relation(root: Path, baseline: str | None, final_head: str | None) -> str:
    if not baseline or not final_head:
        return "unavailable"
    if baseline == final_head:
        return "same"
    result = run_git(root, ["merge-base", "--is-ancestor", baseline, final_head], check=False)
    return "ancestor" if result.returncode == 0 else "diverged"


def commits_since_baseline(root: Path, baseline: str | None, final_head: str | None) -> list[dict[str, str]]:
    if history_relation(root, baseline, final_head) != "ancestor":
        return []
    result = run_git(root, ["log", "--format=%H%x09%s", f"{baseline}..{final_head}"])
    commits: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        commit_hash, separator, subject = line.partition("\t")
        if separator:
            commits.append({"hash": commit_hash, "subject": subject})
    return commits


# --- start / custody -------------------------------------------------------


def command_start(args: argparse.Namespace) -> None:
    root = require_git_root(Path(args.repo).resolve())
    output = Path(args.output).resolve()
    if output.exists():
        raise RecordError(f"snapshot already exists: {output}")
    if root in output.parents:
        raise RecordError("keep the snapshot outside the repository, for example under /tmp")
    snapshot = {
        "snapshot_version": SNAPSHOT_VERSION,
        "root": str(root),
        "branch": git_branch(root),
        "head": git_head(root),
        "dirty_paths": working_tree_paths(root),
        "taken_at": utc_now(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"snapshot: {output}; baseline={snapshot['head'] or 'none (no commits yet)'}; "
        f"pre-existing changed paths={len(snapshot['dirty_paths'])}"
    )


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RecordError(f"snapshot does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RecordError(f"snapshot is not valid JSON: {exc}") from exc
    if snapshot.get("snapshot_version") != SNAPSHOT_VERSION:
        raise RecordError(f"unsupported snapshot: {path}")
    return snapshot


def custody_data(
    root: Path,
    baseline: str | None,
    baseline_source: str,
    preexisting: list[str] | None,
    scopes: list[str],
) -> dict[str, Any]:
    head = git_head(root)
    changed = changed_paths_since(root, baseline)
    task_changes = [path for path in changed if scope_matches(path, scopes)]
    return {
        "branch": git_branch(root),
        "baseline_head": baseline,
        "baseline_source": baseline_source,
        "final_head": head,
        "history": history_relation(root, baseline, head),
        "commits": commits_since_baseline(root, baseline, head),
        "task_paths": scopes,
        "task_changes": task_changes,
        "diff": diff_summary(root, baseline, scopes),
        "preexisting_in_task_paths": (
            None if preexisting is None else sorted(p for p in preexisting if scope_matches(p, scopes))
        ),
        "outside_change_count": len(changed) - len(task_changes),
    }


def code_list(items: list[str]) -> str:
    return ", ".join(f"`{item}`" for item in items) if items else "None"


def render_custody(data: dict[str, Any]) -> str:
    baseline = data["baseline_head"]
    baseline_text = f"`{baseline}` ({data['baseline_source']})" if baseline else f"unavailable ({data['baseline_source']})"
    final_text = f"`{data['final_head']}`" if data["final_head"] else "none (no commits yet)"
    history = data["history"]
    if data["commits"]:
        commits = "; ".join(f"`{c['hash'][:12]}` {c['subject']}" for c in data["commits"])
    elif history == "same":
        commits = "None"
    elif history == "diverged":
        commits = "None attributed (history diverged from the baseline)"
    else:
        commits = "unavailable"
    preexisting = data["preexisting_in_task_paths"]
    preexisting_text = "unavailable (no start snapshot)" if preexisting is None else code_list(preexisting)
    diff = data["diff"]
    token = "; ".join(
        f"{key}={diff[key]}" for key in ("files", "insertions", "deletions", "binary_files", "untracked_files")
    )
    return "\n".join(
        (
            f"- Branch: `{data['branch']}`",
            f"- Baseline HEAD: {baseline_text}",
            f"- Final HEAD: {final_text}; history: {history}",
            f"- Commits since baseline: {commits}",
            f"- Task paths: {code_list(data['task_paths'])}",
            f"- Task changes: {code_list(data['task_changes'])}",
            f"- Diff in task paths: `{token}` ({diff['basis']})",
            f"- Pre-existing changes in task paths: {preexisting_text}",
            f"- Changes outside task paths: {data['outside_change_count']} paths (not listed)",
        )
    )


def command_custody(args: argparse.Namespace) -> None:
    if args.snapshot:
        snapshot = load_snapshot(Path(args.snapshot).resolve())
        root = require_git_root(Path(snapshot["root"]))
        if args.repo and require_git_root(Path(args.repo).resolve()) != root:
            raise RecordError("--repo does not match the snapshot's repository")
        baseline = snapshot["head"]
        source = "start snapshot" if baseline else "no commits at start"
        preexisting: list[str] | None = snapshot["dirty_paths"]
    else:
        root = require_git_root(Path(args.repo or ".").resolve())
        preexisting = None
        if args.baseline == "unavailable":
            baseline, source = None, "baseline unavailable"
        else:
            baseline, source = verify_commit(root, args.baseline), "explicit"
    scopes = list(dict.fromkeys(normalized_scope(root, path) for path in args.path))
    data = custody_data(root, baseline, source, preexisting, scopes)
    print(json.dumps(data, indent=2, sort_keys=True) if args.json else render_custody(data))


# --- note parsing ----------------------------------------------------------


def metadata_value(text: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip().strip("`") if match else None


def strip_fences(text: str) -> str:
    return re.sub(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", "", text, flags=re.MULTILINE | re.DOTALL)


def sections(text: str) -> list[tuple[str, str]]:
    """Return level-two sections outside fenced code, in order."""
    body = strip_fences(text)
    matches = list(re.finditer(r"^##[ \t]+(.+?)[ \t]*$", body, re.MULTILINE))
    return [
        (match.group(1), body[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(body)])
        for index, match in enumerate(matches)
    ]


def has_table(content: str) -> bool:
    return bool(re.search(r"^[ \t]*\|.*\|[ \t]*\n[ \t]*\|[ \t:]*-{3,}", content, re.MULTILINE))


def bullets(content: str) -> list[str]:
    return re.findall(r"^[ \t]*(?:[-*]|\d+\.)[ \t]+(.+)$", content, re.MULTILINE)


def placeholders(text: str) -> list[str]:
    prose = re.sub(r"`[^`\n]*`|\$[^$\n]+\$", "", strip_fences(text))
    found = []
    for match in re.finditer(r"<([A-Za-z/][^<>\n]*)>", prose):
        inner = match.group(1)
        name = re.match(r"/?([A-Za-z][\w-]*)", inner)
        if "://" in inner or "@" in inner or (name and name.group(1).lower() in HTML_TAGS):
            continue
        found.append(match.group(0))
    return found


# --- validate --------------------------------------------------------------


def validate_metadata(details: str, errors: list[str]) -> str | None:
    kind = metadata_value(details, "Kind")
    if kind not in KINDS:
        errors.append(f"Kind must be one of: {', '.join(KINDS)}")
        return None
    if metadata_value(details, "Status") not in STATUSES:
        errors.append(f"Status must be one of: {', '.join(STATUSES)}")
    date = metadata_value(details, "Date") or ""
    try:
        validated_date(date, "Date")
    except RecordError as exc:
        errors.append(str(exc))
    if not metadata_value(details, "Project"):
        errors.append("Project is required")
    change = metadata_value(details, "Change type")
    if kind == "implementation" and change not in CHANGE_TYPES:
        errors.append("implementation records need Change type `fix` or `new`")
    if kind != "implementation" and change:
        errors.append("Change type applies to implementation records only")
    return kind


def validate_note(text: str) -> list[str]:
    record_format = metadata_value(text, "Record format") or "1"
    if record_format != RECORD_FORMAT:
        return [f"format {record_format} notes are frozen; validate checks format {RECORD_FORMAT} only"]
    found = sections(text)
    content = dict(found)
    names = [name for name, _ in found]
    if "Record details" not in content:
        return ["missing appendix section: ## Record details"]
    errors: list[str] = []
    kind = validate_metadata(content["Record details"], errors)
    if kind is None:
        return errors
    if not re.search(r"^<details>", text, re.MULTILINE):
        errors.append("fold the appendix in <details> … </details>")

    appendix_start = names.index("Record details")
    order = [entry.lstrip("?") for entry in BODY_SECTIONS[kind]]
    positions = []
    for entry in BODY_SECTIONS[kind]:
        name, required = entry.lstrip("?"), not entry.startswith("?")
        if name not in content:
            if required:
                errors.append(f"missing section: ## {name}")
            continue
        if names.index(name) > appendix_start:
            errors.append(f"## {name} belongs in the body, before the appendix")
        if required and not content[name].strip():
            errors.append(f"## {name} is empty")
        positions.append(names.index(name))
    if positions != sorted(positions):
        errors.append(f"body sections must appear in this order: {' → '.join(order)}")
    for name in APPENDIX_SECTIONS[kind]:
        if name not in content:
            errors.append(f"missing appendix section: ## {name}")
        elif not content[name].strip():
            errors.append(f"## {name} is empty")

    if kind == "evaluation" and not has_table(content.get("Readout", "")):
        errors.append("## Readout needs a results table (Measure | Result | Compared with | Meaning)")
    if kind == "session":
        if not bullets(content.get("Takeaways", "")):
            errors.append("## Takeaways needs bullet points")
        if not has_table(content.get("Decisions", "")):
            errors.append("## Decisions needs a table (Item | Status | Reason)")
        if not bullets(content.get("Sources", "")):
            errors.append("## Sources needs at least one bullet")
    if "Commands" in content:
        entries = bullets(content["Commands"])
        if kind != "session" and not entries:
            errors.append("## Commands needs one bullet per check")
        for entry in entries:
            if not CHECK_RESULT.search(entry):
                errors.append(f"Commands entry lacks `pass`, `fail`, `partial`, or `not-run`: {entry[:60]}")
    if metadata_value(content["Record details"], "Status") == "blocked":
        if "block" not in content.get("Open items", "").lower():
            errors.append("a blocked record must name the blocker under ## Open items")
    for placeholder in dict.fromkeys(placeholders(text)):
        errors.append(f"unresolved template placeholder: {placeholder}")
    return errors


def command_validate(args: argparse.Namespace) -> None:
    note = Path(args.note).resolve()
    try:
        text = note.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read note: {exc}") from exc
    errors = validate_note(text)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    details = dict(sections(text))["Record details"]
    print(f"valid format-{RECORD_FORMAT} {metadata_value(details, 'Kind')} record: {note}")


# --- list ------------------------------------------------------------------


def plain(line: str) -> str:
    line = re.sub(r"^[ \t]*(?:[-*>]|\d+\.)[ \t]+", "", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
    return line.replace("**", "").replace("`", "").strip()


def first_paragraph(content: str) -> str:
    lines: list[str] = []
    for item in content.splitlines():
        stripped = item.strip()
        skip = not stripped or stripped.startswith(("|", "#", "<"))
        if lines and (skip or re.match(r"(?:[-*]|\d+\.)\s", stripped)):
            break
        if not skip:
            lines.append(stripped)
    return " ".join(lines)


def headline(text: str) -> str:
    """Return the first sentence of the answer-bearing section."""
    found = sections(text)
    content = next((body for name, body in found if name in HEADLINE_SECTIONS), found[0][1] if found else "")
    answer = re.search(r"\*\*Answer\.?\*\*\.?[ \t]*", content)
    paragraph = first_paragraph(content[answer.end() :] if answer else content)
    return re.split(r"(?<=[.!?])\s", plain(paragraph), maxsplit=1)[0]


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
        "kind": metadata_value(content, "Kind") or metadata_value(content, "Mode") or "unavailable",
        "status": status,
        "date": date,
        "project": project or "unavailable",
        "headline": headline(content),
    }


def command_list(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise RecordError(f"list root is not a directory: {root}")
    since = validated_date(args.since, "--since") if args.since else None
    until = validated_date(args.until, "--until") if args.until else None
    entries = []
    for path in sorted(root.rglob("*.md")):
        entry = note_index_entry(path, root)
        if entry is None:
            continue
        if (args.kind and entry["kind"] != args.kind) or (args.status and entry["status"] != args.status):
            continue
        if (since and entry["date"] < since) or (until and entry["date"] > until):
            continue
        entries.append(entry)
    if args.json:
        print(json.dumps(entries, indent=2, ensure_ascii=False, sort_keys=True))
        return
    columns = (("DATE", "date"), ("FORMAT", "record_format"), ("KIND", "kind"), ("STATUS", "status"), ("PATH", "path"))
    widths = {key: max([len(header)] + [len(entry[key]) for entry in entries]) for header, key in columns}
    print("  ".join(header.ljust(widths[key]) for header, key in columns) + "  HEADLINE")
    for entry in entries:
        text = entry["headline"]
        short = text if len(text) <= args.width else text[: args.width - 1] + "…"
        print("  ".join(entry[key].ljust(widths[key]) for _, key in columns) + f"  {short}")


# --- CLI -------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    start = subparsers.add_parser("start", help="snapshot the baseline HEAD and pre-existing changes")
    start.add_argument("--repo", default=".", help="repository path (default: current directory)")
    start.add_argument("--output", required=True, help="snapshot JSON path outside the repository")
    start.set_defaults(func=command_start)

    custody = subparsers.add_parser("custody", help="print the Git block for a record's appendix")
    baseline = custody.add_mutually_exclusive_group(required=True)
    baseline.add_argument("--snapshot", help="snapshot written by start")
    baseline.add_argument("--baseline", help="verified baseline commit, or 'unavailable' for a late start")
    custody.add_argument("--repo", help="repository path (default: snapshot repository or current directory)")
    custody.add_argument("--path", action="append", required=True, help="file or directory the task changed")
    custody.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    custody.set_defaults(func=command_custody)

    validate = subparsers.add_parser("validate", help="check a format-4 note's structure")
    validate.add_argument("--note", required=True)
    validate.set_defaults(func=command_validate)

    list_records = subparsers.add_parser("list", help="list records of every format with their headlines")
    list_records.add_argument("--root", required=True, help="progress directory to scan")
    list_records.add_argument("--kind", help="kind (format 4) or mode (older formats)")
    list_records.add_argument("--status")
    list_records.add_argument("--since", help="earliest date, YYYY-MM-DD")
    list_records.add_argument("--until", help="latest date, YYYY-MM-DD")
    list_records.add_argument("--width", type=int, default=100, help="headline width in table output")
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
