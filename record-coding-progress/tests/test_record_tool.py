from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "record_tool.py"
sys.path.insert(0, str(SCRIPT.parent))
import record_tool as record_module  # noqa: E402


def run_tool(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


class RecordToolTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Record Test")
        git(repo, "config", "user.email", "record@example.invalid")
        (repo / "task.txt").write_text("before\n", encoding="utf-8")
        (repo / "preexisting.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "task.txt", "preexisting.txt")
        git(repo, "commit", "-q", "-m", "initial")
        return repo

    def start_v3(
        self,
        root: Path,
        repo: Path,
        *,
        mode: str = "coding-progress",
        task_type: str = "feature",
        initial_status: str = "in-progress",
        implementation_kind: str = "fresh-implementation",
        extra: tuple[str, ...] = (),
    ) -> Path:
        manifest = root / f"{mode}-{task_type}-{len(list(root.glob('*.json')))}.json"
        args = [
            "start",
            "--record-format",
            "3",
            "--mode",
            mode,
            "--task-type",
            task_type,
            "--task-slug",
            "v3-test",
            "--record-date",
            "2026-09-03",
            "--initial-status",
            initial_status,
            "--repo",
            str(repo),
            "--output",
            str(manifest),
        ]
        if mode == "coding-progress":
            args.extend(("--implementation-kind", implementation_kind))
        args.extend(extra)
        run_tool(*args)
        return manifest

    def write_v3_note(self, manifest_path: Path, note: Path) -> None:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        components = ", ".join(data["components"]) or "None"
        labels = ", ".join(data["labels"]) or "None"
        metadata = [
            "# V3 test record",
            "",
            "- Record format: `3`",
            f"- Record ID: `{data['record_id']}`",
            f"- Mode: `{data['mode']}`",
            f"- Task type: `{data['task_type']}`",
            f"- Task slug: `{data['task_slug']}`",
        ]
        if data["mode"] == "coding-progress":
            metadata.append(f"- Implementation class: `{data['implementation_kind']}`")
        metadata.extend(
            [
                f"- Date: `{data['record_date']}`",
                f"- Project: {data['repository']}",
                f"- Priority: `{data['priority']}`",
                f"- Owner: {data['owner']}",
                f"- Components: {components}",
                f"- Labels: {labels}",
                f"- Status category: `{data['status_category']}`",
                f"- Status: `{data['status']}`",
                f"- Resolution: `{data['resolution']}`",
                f"- Created at: `{data['created_at']}`",
                f"- Started at: `{data['started_at']}`",
                f"- Updated at: `{data['updated_at']}`",
                f"- Completed at: `{data['completed_at'] or 'Not applicable'}`",
                f"- Due date: `{data['due_date'] or 'Not applicable'}`",
                f"- Evidence state: `{data['evidence_state']}`",
                f"- Validation state: `{data['validation_state']}`",
                "",
                "## Outcome",
                "",
                "Recorded outcome [E1]." if data["sources"] else "Recorded outcome.",
                "",
            ]
        )
        lifecycle = [
            "## Lifecycle",
            "",
            f"Current blocker: {data.get('blocked_reason') or 'None'}",
            "",
            "| ID | At | Action | From | To | Actor | Reason |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        lifecycle.extend(
            f"| {event['id']} | {event['at']} | {event['action']} | {event['from']} | "
            f"{event['to']} | {event['actor']} | {event['reason']} |"
            for event in data["lifecycle"]
        )
        lifecycle.extend(
            [
                "",
                "| ID | Type | Target |",
                "| --- | --- | --- |",
                *(f"| {link['id']} | {link['type']} | {link['target']} |" for link in data["links"]),
            ]
        )
        if not data["links"]:
            lifecycle.append("| None | None | None |")
        body = [*metadata, *lifecycle, ""]
        if data["mode"] == "coding-progress":
            body.extend(["## Task and Scope", "", "Bounded v3 test scope.", "", "## Implementation", ""])
            if data["implementation_kind"] == "function-fix":
                body.extend(
                    [
                        "### Preserved Contract",
                        "",
                        "Contract preserved.",
                        "",
                        "### Corrective Change",
                        "",
                        "Correction applied.",
                        "",
                    ]
                )
            else:
                body.extend(
                    [
                        "### Plan and Starting Status",
                        "",
                        "Plan source and starting status recorded.",
                        "",
                        "### Core Functions and Result",
                        "",
                        "Core result recorded.",
                        "",
                    ]
                )
            body.extend(["## Validation", "", "### Test Result", "", f"Aggregate: {data['validation_state']}.", ""])
            for check in data["checks"]:
                body.extend(
                    [
                        f"### {check['id']} - {check['result']}",
                        "",
                        "```text",
                        check["command"],
                        "```",
                        "",
                        f"Observed: {check['summary']}.",
                        "",
                    ]
                )
        else:
            body.extend(
                [
                    "## Context and Scope",
                    "",
                    "Bounded session scope.",
                    "",
                    "## Findings and Decisions",
                    "",
                    "Finding recorded [E1].",
                    "",
                ]
            )
        body.extend(["## Evidence Ledger", ""])
        for source in data["sources"]:
            body.append(f"- {source['id']} [verified]: {source['locator']}")
        for check in data["checks"]:
            body.append(f"- {check['id']} [verified]: {check['summary']}")
        if not data["sources"] and not data["checks"]:
            body.append("None.")
        body.append("")
        if data["mode"] == "coding-progress":
            body.extend(["## Git Custody", ""])
            git_data = data["git"]
            if not git_data["available"]:
                body.extend(["Git evidence is unavailable.", ""])
            else:
                baseline = git_data["baseline"]
                final = git_data["final"]
                summary = final["scoped_diff"]
                body.extend(
                    [
                        f"- Branch: {final['branch']}",
                        f"- Baseline HEAD: {baseline['baseline_head'] or 'unavailable'}",
                        f"- Final HEAD: {final['head'] or 'unavailable'}",
                        f"- History relation: {final['history_relation']}",
                        f"- Task paths: {', '.join(final['task_paths']) or 'None'}",
                        f"- Task-owned paths: {', '.join(final['task_owned_changed_paths']) or 'None'}",
                        f"- Pre-existing paths: {', '.join(final['preexisting_paths']) or 'None'}",
                        f"- Pre-existing overlap: {', '.join(final['preexisting_overlap']) or 'None'}",
                        f"- Outside-scope paths: {', '.join(final['outside_scope_changed_paths']) or 'None'}",
                        f"- Record path: {final['record_path'] or 'None'}",
                        "- Scoped diff: "
                        f"files={summary['files']}; insertions={summary['insertions']}; "
                        f"deletions={summary['deletions']}; binary_files={summary['binary_files']}; "
                        f"untracked_files={summary['untracked_files']}",
                        "",
                    ]
                )
                for commit in final["commits_since_baseline"]:
                    body.append(f"- Commit: {commit['hash']} {commit['subject']}")
        body.extend(
            [
                "## Evidence Boundary",
                "",
                "Establishes only the recorded evidence.",
                "",
                "## Next Steps",
                "",
                "None.",
                "",
            ]
        )
        note.write_text("\n".join(body), encoding="utf-8")

    def test_coding_manifest_classifies_scope_and_validates_note(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            (repo / "preexisting.txt").write_text("dirty before\n", encoding="utf-8")
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            baseline = json.loads(manifest.read_text(encoding="utf-8"))["git"]["baseline"]
            (repo / "task.txt").write_text("after\n", encoding="utf-8")
            (repo / "outside.txt").write_text("unrelated\n", encoding="utf-8")
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "repository",
                "--locator",
                "task.txt",
            )
            run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                "python -m unittest",
                "--result",
                "pass",
                "--summary",
                "1 test passed",
            )
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--task-path",
                "task.txt",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            final = data["git"]["final"]
            self.assertEqual(final["task_owned_changed_paths"], ["task.txt"])
            self.assertIn("preexisting.txt", final["outside_scope_changed_paths"])
            self.assertIn("outside.txt", final["outside_scope_changed_paths"])
            self.assertEqual(final["preexisting_overlap"], [])

            note = root / "note.md"
            diff_token = (
                f"files={final['scoped_diff']['files']}; "
                f"insertions={final['scoped_diff']['insertions']}; "
                f"deletions={final['scoped_diff']['deletions']}; "
                f"binary_files={final['scoped_diff']['binary_files']}; "
                f"untracked_files={final['scoped_diff']['untracked_files']}"
            )
            note.write_text(
                f"""# Test record

- Record format: `2`
- Mode: `coding-progress`
- Implementation class: `function-fix`
- Date: `2026-07-29`
- Project: {repo}
- Status: `completed`
- Evidence state: `verified`

## Outcome

Implemented the task [E1].

## Task and Scope

Task scope: task.txt. Outside scope: preexisting.txt and outside.txt.

## Implementation

### Preserved Contract

The task.txt input and output contract remains unchanged [E1].

### Corrective Change

Changed task.txt.

## Validation

### Test Result

Pass: the recorded unit test passed.

### V1 - pass

```text
python -m unittest
```

Observed: 1 test passed.

## Evidence Ledger

- E1 [verified]: repository source task.txt.
- V1 [verified]: validation.

## Git Custody

- Branch: {final["branch"]}
- Baseline HEAD: {baseline["baseline_head"]}
- Final HEAD: {final["head"]}
- History relation: {final["history_relation"]}
- Explicit scope: task.txt
- Outside scope: preexisting.txt, outside.txt
- Scoped diff: {diff_token}

## Evidence Boundary

Establishes the tested implementation only.

## Next Steps

None.
""",
                encoding="utf-8",
            )
            run_tool("validate", "--manifest", str(manifest), "--note", str(note))

    def test_fresh_implementation_requires_plan_status_core_result_and_test_headings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "fresh-implementation",
                "--repo",
                str(root),
                "--output",
                str(manifest),
            )
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "user",
                "--locator",
                "confirmed plan in current conversation",
            )
            run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                "python -m unittest",
                "--result",
                "pass",
                "--summary",
                "1 test passed",
            )
            run_tool("finish", "--manifest", str(manifest))
            note = root / "note.md"
            note.write_text(
                f"""# Fresh implementation record

- Record format: `2`
- Mode: `coding-progress`
- Implementation class: `fresh-implementation`
- Date: `2026-08-10`
- Project: {root}
- Status: `completed`
- Evidence state: `mixed`

## Outcome

Implemented the planned capability [E1].

## Task and Scope

Plan source: confirmed plan in current conversation [E1]. Original status: unimplemented.

## Implementation

### Plan and Starting Status

The confirmed plan was to add the capability; it was unimplemented before this work [E1].

### Core Functions and Result

The core record function now implements the capability.

## Validation

### Test Result

Pass: the unit test completed successfully.

### V1 - pass

```text
python -m unittest
```

Observed: 1 test passed.

## Evidence Ledger

- E1 [user-stated]: confirmed plan in current conversation.
- V1 [verified]: validation.

## Git Custody

Git evidence is unavailable because the project is not a Git checkout.

## Evidence Boundary

Establishes the recorded implementation and test only.

## Next Steps

None.
""",
                encoding="utf-8",
            )
            run_tool("validate", "--manifest", str(manifest), "--note", str(note))
            note.write_text(
                note.read_text(encoding="utf-8").replace(
                    "### Core Functions and Result",
                    "### Implementation Result",
                ),
                encoding="utf-8",
            )
            result = run_tool(
                "validate",
                "--manifest",
                str(manifest),
                "--note",
                str(note),
                expect=1,
            )
            self.assertIn(
                "fresh-implementation records require implementation heading: "
                "### Core Functions and Result",
                result.stderr,
            )

    def test_coding_start_requires_implementation_kind(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--repo",
                str(root),
                "--output",
                str(root / "manifest.json"),
                expect=2,
            )
            self.assertIn("--implementation-kind is required", result.stderr)

    def test_validator_rejects_false_check_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                "pytest",
                "--result",
                "fail",
                "--summary",
                "one failure",
            )
            run_tool("finish", "--manifest", str(manifest), "--task-path", "task.txt")
            note = root / "bad.md"
            note.write_text(
                """# Bad

- Record format: `2`
- Mode: `coding-progress`
- Date: `2026-07-29`
- Project: repo
- Status: `completed`
- Evidence state: `verified`

## Outcome
Bad.
## Task and Scope
Bad.
## Implementation
Bad.
## Validation
### V1 - pass
pytest
## Evidence Ledger
V1 [verified]
## Git Custody
Unavailable.
## Evidence Boundary
Bad.
## Next Steps
None.
""",
                encoding="utf-8",
            )
            result = run_tool(
                "validate",
                "--manifest",
                str(manifest),
                "--note",
                str(note),
                expect=1,
            )
            self.assertIn("must report result `fail`", result.stderr)

    def test_session_mode_omits_git_and_rejects_forbidden_heading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            manifest = root / "session.json"
            run_tool(
                "start",
                "--mode",
                "session-documentation",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "user",
                "--locator",
                "current conversation",
            )
            run_tool("finish", "--manifest", str(manifest))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertNotIn("git", data)
            note = root / "session.md"
            note.write_text(
                """# Session

- Record format: `2`
- Mode: `session-documentation`
- Date: `2026-07-29`
- Project: test
- Status: `concluded`
- Evidence state: `mixed`

## Outcome
Decision [E1].
## Context and Scope
Bounded scope.
## Findings and Decisions
User-stated decision [E1].
## Evidence Ledger
E1 [user-stated]: current conversation.
## Git Custody
None.
## Evidence Boundary
No implementation.
## Next Steps
One next step.
""",
                encoding="utf-8",
            )
            result = run_tool(
                "validate",
                "--manifest",
                str(manifest),
                "--note",
                str(note),
                expect=1,
            )
            self.assertIn("forbids heading: ## Git Custody", result.stderr)

    def test_session_requires_finalization_and_exact_source_locator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "session.json"
            run_tool(
                "start",
                "--mode",
                "session-documentation",
                "--repo",
                str(root),
                "--output",
                str(manifest),
            )
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "user",
                "--locator",
                "design discussion",
            )
            note = root / "session.md"
            note.write_text(
                """# Session

- Record format: `2`
- Mode: `session-documentation`
- Date: `2026-07-29`
- Project: test
- Status: `concluded`
- Evidence state: `mixed`

## Outcome
Decision [E1].
## Context and Scope
Bounded scope.
## Findings and Decisions
Decision [E1].
## Evidence Ledger
E1 is present without its locator.
## Evidence Boundary
No implementation.
## Next Steps
None.
""",
                encoding="utf-8",
            )
            result = run_tool(
                "validate",
                "--manifest",
                str(manifest),
                "--note",
                str(note),
                expect=1,
            )
            self.assertIn("manifest must be finalized", result.stderr)
            self.assertIn("source locator for E1", result.stderr)
            run_tool("finish", "--manifest", str(manifest))
            locked = run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "user",
                "--locator",
                "late source",
                expect=2,
            )
            self.assertIn("after manifest finalization", locked.stderr)

    def test_classification_must_be_inside_evidence_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "session.json"
            run_tool(
                "start",
                "--mode",
                "session-documentation",
                "--repo",
                str(root),
                "--output",
                str(manifest),
            )
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "user",
                "--locator",
                "current user statement",
            )
            run_tool("finish", "--manifest", str(manifest))
            note = root / "session.md"
            note.write_text(
                """# Session

- Record format: `2`
- Mode: `session-documentation`
- Date: `2026-07-29`
- Project: test
- Status: `proposed`
- Evidence state: `unverified`

## Outcome
Proposed conclusion [E1, proposed].
## Context and Scope
Current user statement.
## Findings and Decisions
Proposed conclusion [E1].
## Evidence Ledger
| ID | Kind | Locator |
| --- | --- | --- |
| E1 | user | current user statement |
## Evidence Boundary
No implementation.
## Next Steps
None.
""",
                encoding="utf-8",
            )
            result = run_tool(
                "validate",
                "--manifest",
                str(manifest),
                "--note",
                str(note),
                expect=1,
            )
            self.assertIn("classified in the Evidence Ledger", result.stderr)

    def test_non_git_and_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(root),
                "--output",
                str(manifest),
            )
            artifact = root / "result.json"
            artifact.write_text('{"ok": true}\n', encoding="utf-8")
            run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                "verify result.json",
                "--result",
                "partial",
                "--summary",
                "artifact inspected",
                "--artifact",
                str(artifact),
            )
            run_tool("finish", "--manifest", str(manifest))
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertFalse(data["git"]["available"])
            expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
            self.assertEqual(data["checks"][0]["artifact"]["sha256"], expected)

    def test_rejects_root_scope_and_manifest_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            overwrite = run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
                expect=2,
            )
            self.assertIn("refusing to overwrite", overwrite.stderr)
            root_scope = run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--task-path",
                ".",
                expect=2,
            )
            self.assertIn("repository root cannot be used", root_scope.stderr)

    def test_finish_refresh_preserves_baseline_and_recaptures_final_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            baseline = json.loads(manifest.read_text(encoding="utf-8"))["git"]["baseline"]
            (repo / "task.txt").write_text("first\n", encoding="utf-8")
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--task-path",
                "task.txt",
                "--record-path",
                "progress/record.md",
            )
            first = json.loads(manifest.read_text(encoding="utf-8"))["git"]["final"]
            (repo / "progress").mkdir()
            (repo / "progress" / "record.md").write_text("first note\n", encoding="utf-8")
            (repo / "later.txt").write_text("later\n", encoding="utf-8")
            blocked = run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--task-path",
                "task.txt",
                "--record-path",
                "progress/record.md",
                expect=2,
            )
            self.assertIn("pass --refresh", blocked.stderr)
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--task-path",
                "task.txt",
                "--record-path",
                "progress/record.md",
                "--refresh",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["git"]["baseline"], baseline)
            self.assertEqual(
                data["git"]["final"]["task_owned_changed_paths"],
                ["progress/record.md", "task.txt"],
            )
            self.assertEqual(data["git"]["final"]["scoped_diff"], first["scoped_diff"])
            self.assertEqual(data["git"]["final"]["record_path"], "progress/record.md")
            self.assertIn("later.txt", data["git"]["final"]["outside_scope_changed_paths"])

    def test_late_start_can_mark_baseline_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            (repo / "task.txt").write_text("late change\n", encoding="utf-8")
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
                "--baseline-unavailable",
            )
            run_tool("finish", "--manifest", str(manifest), "--task-path", "task.txt")
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertIsNone(data["git"]["baseline"]["baseline_head"])
            self.assertEqual(data["git"]["baseline"]["baseline_source"], "unavailable")

    def test_explicit_baseline_captures_commits_and_detached_head(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            baseline = git(repo, "rev-parse", "HEAD")
            (repo / "task.txt").write_text("committed change\n", encoding="utf-8")
            git(repo, "add", "task.txt")
            git(repo, "commit", "-q", "-m", "change task")
            final_head = git(repo, "rev-parse", "HEAD")
            git(repo, "checkout", "-q", "--detach", final_head)
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
                "--baseline-head",
                baseline,
            )
            run_tool("finish", "--manifest", str(manifest), "--task-path", "task.txt")
            data = json.loads(manifest.read_text(encoding="utf-8"))
            final = data["git"]["final"]
            self.assertEqual(final["branch"], "detached")
            self.assertEqual(final["task_owned_changed_paths"], ["task.txt"])
            self.assertEqual(final["history_relation"], "ancestor")
            self.assertEqual(final["commits_since_baseline"][0]["hash"], final_head)
            self.assertEqual(final["commits_since_baseline"][0]["subject"], "change task")

    def test_diverged_history_does_not_attribute_commits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            common = git(repo, "rev-parse", "HEAD")
            (repo / "baseline-only.txt").write_text("baseline branch\n", encoding="utf-8")
            git(repo, "add", "baseline-only.txt")
            git(repo, "commit", "-q", "-m", "baseline branch commit")
            explicit_baseline = git(repo, "rev-parse", "HEAD")
            git(repo, "checkout", "-q", "-b", "other", common)
            (repo / "task.txt").write_text("other branch\n", encoding="utf-8")
            git(repo, "add", "task.txt")
            git(repo, "commit", "-q", "-m", "other branch commit")
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
                "--baseline-head",
                explicit_baseline,
            )
            run_tool("finish", "--manifest", str(manifest), "--task-path", "task.txt")
            final = json.loads(manifest.read_text(encoding="utf-8"))["git"]["final"]
            self.assertEqual(final["history_relation"], "diverged")
            self.assertEqual(final["commits_since_baseline"], [])

    def test_paths_with_spaces_rename_delete_and_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            spaced = repo / "space dir"
            spaced.mkdir()
            (spaced / "old name.txt").write_text("old\n", encoding="utf-8")
            (spaced / "delete me.txt").write_text("delete\n", encoding="utf-8")
            git(repo, "add", "space dir")
            git(repo, "commit", "-q", "-m", "add spaced files")
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            git(repo, "mv", "space dir/old name.txt", "space dir/new name.txt")
            git(repo, "rm", "-q", "space dir/delete me.txt")
            (spaced / "new untracked.txt").write_text("new\n", encoding="utf-8")
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--task-path",
                "space dir",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            owned = data["git"]["final"]["task_owned_changed_paths"]
            self.assertIn("space dir/new name.txt", owned)
            self.assertIn("space dir/delete me.txt", owned)
            self.assertIn("space dir/new untracked.txt", owned)

    def test_check_command_is_recorded_as_data_and_artifact_hash_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            marker = root / "must-not-exist"
            artifact = root / "artifact.txt"
            artifact.write_text("evidence\n", encoding="utf-8")
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            command = f"touch {marker} | false"
            run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                command,
                "--result",
                "not-run",
                "--summary",
                "unsafe command intentionally not run",
                "--artifact",
                str(artifact),
            )
            self.assertFalse(marker.exists())
            run_tool("finish", "--manifest", str(manifest), "--task-path", "task.txt")
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["checks"][0]["command"], command)
            self.assertEqual(data["checks"][0]["result"], "not-run")
            locked = run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                "late",
                "--result",
                "pass",
                "--summary",
                "late",
                expect=2,
            )
            self.assertIn("after manifest finalization", locked.stderr)

    def test_source_file_hash_is_computed_and_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.txt"
            source.write_text("source evidence\n", encoding="utf-8")
            manifest = root / "session.json"
            run_tool(
                "start",
                "--mode",
                "session-documentation",
                "--repo",
                str(root),
                "--output",
                str(manifest),
            )
            mismatch = run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "artifact",
                "--locator",
                "source.txt",
                "--file",
                str(source),
                "--sha256",
                "0" * 64,
                expect=2,
            )
            self.assertIn("does not match source file", mismatch.stderr)
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "artifact",
                "--locator",
                "source.txt",
                "--file",
                str(source),
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            expected = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(data["sources"][0]["sha256"], expected)
            self.assertEqual(data["sources"][0]["file"]["size"], source.stat().st_size)

    def test_unborn_repository_records_unavailable_heads_and_staged_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "unborn"
            repo.mkdir()
            git(repo, "init", "-q")
            (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
            git(repo, "add", "staged.txt")
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
                "--implementation-kind",
                "function-fix",
                "--repo",
                str(repo),
                "--output",
                str(manifest),
                "--baseline-unavailable",
            )
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--task-path",
                "staged.txt",
                "--task-path",
                "untracked.txt",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertIsNone(data["git"]["baseline"]["head"])
            self.assertIsNone(data["git"]["baseline"]["baseline_head"])
            self.assertIsNone(data["git"]["final"]["head"])
            self.assertEqual(
                data["git"]["final"]["task_owned_changed_paths"],
                ["staged.txt", "untracked.txt"],
            )
            self.assertEqual(data["git"]["final"]["scoped_diff"]["untracked_files"], 1)

    def test_v3_coding_lifecycle_links_and_note_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            manifest = self.start_v3(
                root,
                repo,
                task_type="bug",
                implementation_kind="function-fix",
                extra=(
                    "--priority",
                    "high",
                    "--owner",
                    "Codex",
                    "--component",
                    "workflow",
                    "--component",
                    "workflow",
                    "--label",
                    "v3",
                    "--due-date",
                    "2026-09-10",
                ),
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertRegex(data["record_id"], r"^RCP-\d{8}T\d{6}Z-[0-9a-f]{8}$")
            self.assertEqual(data["components"], ["workflow"])
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "repository",
                "--locator",
                "task.txt",
            )
            run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                "python3 -m unittest",
                "--result",
                "pass",
                "--summary",
                "18 tests passed",
            )
            run_tool(
                "add-check",
                "--manifest",
                str(manifest),
                "--command",
                "ruff check",
                "--result",
                "not-run",
                "--summary",
                "ruff unavailable",
            )
            run_tool(
                "add-link",
                "--manifest",
                str(manifest),
                "--type",
                "parent",
                "--target",
                "RCP-20260901T000000Z-00000000",
            )
            run_tool(
                "transition",
                "--manifest",
                str(manifest),
                "--to",
                "validating",
                "--actor",
                "Codex",
                "--reason",
                "implementation complete",
            )
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--status",
                "done",
                "--resolution",
                "completed",
                "--evidence-state",
                "verified",
                "--actor",
                "Codex",
                "--reason",
                "validation complete",
                "--task-path",
                "task.txt",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["status_category"], "done")
            self.assertEqual(data["validation_state"], "pass")
            self.assertEqual(data["completed_at"], data["finalized_at"])
            note = root / "v3.md"
            self.write_v3_note(manifest, note)
            run_tool("validate", "--manifest", str(manifest), "--note", str(note))

    def test_v3_session_documentation_validates_without_git_or_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self.start_v3(
                root,
                root,
                mode="session-documentation",
                task_type="research",
                initial_status="proposed",
                extra=("--started-at", "unavailable"),
            )
            run_tool(
                "add-source",
                "--manifest",
                str(manifest),
                "--kind",
                "user",
                "--locator",
                "current research discussion",
            )
            run_tool(
                "transition",
                "--manifest",
                str(manifest),
                "--to",
                "in-progress",
                "--actor",
                "Codex",
                "--reason",
                "research started",
            )
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--status",
                "done",
                "--resolution",
                "completed",
                "--evidence-state",
                "mixed",
                "--actor",
                "Codex",
                "--reason",
                "documentation concluded",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["validation_state"], "not-applicable")
            self.assertNotIn("git", data)
            note = root / "session-v3.md"
            self.write_v3_note(manifest, note)
            run_tool("validate", "--manifest", str(manifest), "--note", str(note))

    def test_v3_rejects_wrong_task_type_slug_date_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for flag, value, expected in (
                ("--task-type", "research", "not valid for coding-progress"),
                ("--task-slug", "Bad Slug", "--task-slug"),
                ("--record-date", "2026-02-30", "record date"),
                ("--started-at", "2026-09-03T10:00:00", "timezone"),
            ):
                args = [
                    "start",
                    "--record-format",
                    "3",
                    "--mode",
                    "coding-progress",
                    "--task-type",
                    "feature",
                    "--task-slug",
                    "valid-slug",
                    "--record-date",
                    "2026-09-03",
                    "--implementation-kind",
                    "fresh-implementation",
                    "--repo",
                    str(root),
                    "--output",
                    str(root / f"{flag[2:]}.json"),
                ]
                index = args.index(flag) if flag in args else -1
                if index >= 0:
                    args[index + 1] = value
                else:
                    args.extend((flag, value))
                result = run_tool(*args, expect=2)
                self.assertIn(expected, result.stderr)

    def test_every_v3_transition_pair_matches_the_transition_table(self) -> None:
        base_time = "2026-09-03T00:00:00Z"
        for current in record_module.V3_STATUSES:
            for target in record_module.V3_STATUSES:
                manifest = {
                    "schema_version": 3,
                    "status": current,
                    "status_category": record_module.STATUS_CATEGORIES[current],
                    "resolution": "unresolved",
                    "completed_at": None,
                    "blocked_reason": "blocked" if current == "blocked" else None,
                    "created_at": base_time,
                    "updated_at": base_time,
                    "lifecycle": [],
                }
                resolution = "completed" if target == "done" else "canceled" if target == "canceled" else None
                allowed = target in record_module.ALLOWED_TRANSITIONS[current]
                if allowed:
                    record_module.apply_transition(
                        manifest,
                        target=target,
                        actor="test",
                        reason="matrix test",
                        resolution=resolution,
                        at=base_time,
                    )
                    self.assertEqual(manifest["status"], target)
                else:
                    with self.assertRaises(record_module.RecordError):
                        record_module.apply_transition(
                            manifest,
                            target=target,
                            actor="test",
                            reason="matrix test",
                            resolution=resolution,
                            at=base_time,
                        )

    def test_v3_requires_compatible_terminal_resolution_and_blocker_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self.start_v3(root, root)
            missing_resolution = run_tool(
                "transition",
                "--manifest",
                str(manifest),
                "--to",
                "done",
                "--actor",
                "Codex",
                "--reason",
                "done",
                expect=2,
            )
            self.assertIn("resolution is not valid", missing_resolution.stderr)
            blank_blocker = run_tool(
                "transition",
                "--manifest",
                str(manifest),
                "--to",
                "blocked",
                "--actor",
                "Codex",
                "--reason",
                " ",
                expect=2,
            )
            self.assertIn("--reason must be non-empty", blank_blocker.stderr)
            wrong_cancel = run_tool(
                "transition",
                "--manifest",
                str(manifest),
                "--to",
                "canceled",
                "--actor",
                "Codex",
                "--reason",
                "cancel",
                "--resolution",
                "completed",
                expect=2,
            )
            self.assertIn("resolution is not valid", wrong_cancel.stderr)
            out_of_order = run_tool(
                "transition",
                "--manifest",
                str(manifest),
                "--to",
                "validating",
                "--actor",
                "Codex",
                "--reason",
                "backdated transition",
                "--at",
                "2000-01-01T00:00:00Z",
                expect=2,
            )
            self.assertIn("precedes the last update", out_of_order.stderr)

    def test_v3_resume_and_refresh_preserve_history_and_lifecycle_times(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            manifest = self.start_v3(root, repo)
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--status",
                "blocked",
                "--evidence-state",
                "verified",
                "--actor",
                "Codex",
                "--reason",
                "dependency unavailable",
                "--task-path",
                "task.txt",
            )
            before = json.loads(manifest.read_text(encoding="utf-8"))
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--refresh",
                "--task-path",
                "task.txt",
            )
            refreshed = json.loads(manifest.read_text(encoding="utf-8"))
            for field in ("created_at", "updated_at", "finalized_at", "completed_at", "lifecycle"):
                self.assertEqual(refreshed[field], before[field])
            run_tool(
                "resume",
                "--manifest",
                str(manifest),
                "--actor",
                "Codex",
                "--reason",
                "dependency restored",
            )
            resumed = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(resumed["status"], "in-progress")
            self.assertEqual(resumed["resolution"], "unresolved")
            self.assertIsNone(resumed["finalized_at"])
            self.assertIsNone(resumed["git"]["final"])
            self.assertEqual(len(resumed["lifecycle"]), len(before["lifecycle"]) + 1)

    def test_v3_link_rejects_duplicate_self_and_second_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self.start_v3(root, root)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self_link = run_tool(
                "add-link",
                "--manifest",
                str(manifest),
                "--type",
                "relates-to",
                "--target",
                data["record_id"],
                expect=2,
            )
            self.assertIn("cannot link to itself", self_link.stderr)
            run_tool("add-link", "--manifest", str(manifest), "--type", "parent", "--target", "parent-a")
            duplicate = run_tool(
                "add-link",
                "--manifest",
                str(manifest),
                "--type",
                "parent",
                "--target",
                "parent-a",
                expect=2,
            )
            self.assertIn("duplicate link", duplicate.stderr)
            second_parent = run_tool(
                "add-link",
                "--manifest",
                str(manifest),
                "--type",
                "parent",
                "--target",
                "parent-b",
                expect=2,
            )
            self.assertIn("only one parent", second_parent.stderr)

    def test_v3_validation_states_are_derived(self) -> None:
        base = {"mode": "coding-progress", "checks": []}
        self.assertEqual(record_module.validation_state(base), "not-run")
        base["checks"] = [{"result": "not-run"}]
        self.assertEqual(record_module.validation_state(base), "not-run")
        base["checks"] = [{"result": "pass"}, {"result": "not-run"}]
        self.assertEqual(record_module.validation_state(base), "pass")
        base["checks"] = [{"result": "pass"}, {"result": "partial"}]
        self.assertEqual(record_module.validation_state(base), "partial")
        base["checks"] = [{"result": "partial"}, {"result": "fail"}]
        self.assertEqual(record_module.validation_state(base), "fail")
        self.assertEqual(
            record_module.validation_state({"mode": "session-documentation", "checks": []}),
            "not-applicable",
        )

    def test_v3_validator_rejects_metadata_and_lifecycle_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self.start_v3(root, root)
            run_tool(
                "finish",
                "--manifest",
                str(manifest),
                "--status",
                "done",
                "--resolution",
                "completed",
                "--evidence-state",
                "unverified",
                "--actor",
                "Codex",
                "--reason",
                "record complete",
            )
            note = root / "valid.md"
            self.write_v3_note(manifest, note)
            content = note.read_text(encoding="utf-8")
            note.write_text(content.replace("- Status: `done`", "- Status: `blocked`"), encoding="utf-8")
            result = run_tool("validate", "--manifest", str(manifest), "--note", str(note), expect=1)
            self.assertIn("metadata Status must match manifest", result.stderr)
            note.write_text(content.replace("record-tool", "tampered-actor", 1), encoding="utf-8")
            result = run_tool("validate", "--manifest", str(manifest), "--note", str(note), expect=1)
            self.assertIn("lifecycle event L1", result.stderr)
            tampered_manifest = root / "tampered.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["lifecycle"][-1]["from"] = "proposed"
            tampered_manifest.write_text(json.dumps(data), encoding="utf-8")
            note.write_text(content, encoding="utf-8")
            result = run_tool(
                "validate",
                "--manifest",
                str(tampered_manifest),
                "--note",
                str(note),
                expect=1,
            )
            self.assertIn("does not continue the status chain", result.stderr)

    def test_list_filters_mixed_record_versions_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "v1.md").write_text(
                "# Legacy\n\n- Date: `2026-08-01`\n- Repository: demo\n- Status: `partial`\n",
                encoding="utf-8",
            )
            (root / "v2.md").write_text(
                "# V2\n\n- Record format: `2`\n- Mode: `coding-progress`\n- Date: `2026-08-02`\n"
                "- Project: demo\n- Status: `completed`\n",
                encoding="utf-8",
            )
            (root / "v3.md").write_text(
                "# V3\n\n- Record format: `3`\n- Record ID: `RCP-20260903T000000Z-12345678`\n"
                "- Mode: `coding-progress`\n- Task type: `feature`\n- Date: `2026-09-03`\n"
                "- Project: demo\n- Priority: `high`\n- Components: workflow, cli\n- Labels: v3\n"
                "- Status: `done`\n- Resolution: `completed`\n",
                encoding="utf-8",
            )
            result = run_tool("list", "--root", str(root), "--json")
            rows = json.loads(result.stdout)
            self.assertEqual([row["record_format"] for row in rows], ["1", "2", "3"])
            self.assertEqual(rows[0]["task_type"], "unavailable")
            filtered = run_tool(
                "list",
                "--root",
                str(root),
                "--task-type",
                "feature",
                "--component",
                "workflow",
                "--since",
                "2026-09-01",
                "--json",
            )
            selected = json.loads(filtered.stdout)
            self.assertEqual([row["path"] for row in selected], ["v3.md"])
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["v1.md", "v2.md", "v3.md"])


if __name__ == "__main__":
    unittest.main()
