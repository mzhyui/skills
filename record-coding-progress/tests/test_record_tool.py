from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "record_tool.py"


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
- Date: `2026-07-29`
- Project: {repo}
- Status: `completed`
- Evidence state: `verified`

## Outcome

Implemented the task [E1].

## Task and Scope

Task scope: task.txt. Outside scope: preexisting.txt and outside.txt.

## Implementation

Changed task.txt.

## Validation

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

    def test_validator_rejects_false_check_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            manifest = root / "manifest.json"
            run_tool(
                "start",
                "--mode",
                "coding-progress",
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
                "--repo",
                str(repo),
                "--output",
                str(manifest),
            )
            overwrite = run_tool(
                "start",
                "--mode",
                "coding-progress",
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


if __name__ == "__main__":
    unittest.main()
