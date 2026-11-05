from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "record_tool.py"
FORMATS = SKILL / "references" / "record-formats.md"


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


def make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("start\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "initial")
    return repo


def custody(*args: str) -> dict:
    return json.loads(run_tool("custody", "--json", *args).stdout)


def appendix(kind: str, *, status: str = "done", change: str | None = "fix") -> str:
    lines = ["<details>", "<summary>Record details</summary>", "", "## Record details", ""]
    lines += ["- Record format: `4`", f"- Kind: `{kind}`"]
    if change:
        lines.append(f"- Change type: `{change}`")
    lines += ["- Date: `2026-11-05`", f"- Status: `{status}`", "- Project: demo", ""]
    if kind == "session":
        lines += ["## Sources", "", "- Current conversation — the user's question (user-stated).", ""]
    else:
        lines += [
            "## Commands",
            "",
            "- Unit tests — `pass` — `python3 -m unittest` — 3 tests passed.",
            "",
            "## Git",
            "",
            "Git: not applicable",
            "",
        ]
    return "\n".join([*lines, "</details>", ""])


IMPLEMENTATION_BODY = """# Retry the upload client

## Outcome

Uploads now retry transient 503 responses three times; permanent errors still fail fast.

## Change

The client gave up on the first 503. The public `upload()` contract is unchanged.

## Checks

Unit tests cover retry, back-off, and the permanent-error path; all pass.

## Open items

None.

"""

EVALUATION_BODY = """# Detector evaluation on the development roster

## Readout

**Question.** Does the detector separate attacked from clean models?

**Answer.** Yes on this roster: it ranks every attack above every clean model.
The roster is small.

| Measure | Result | Compared with | Meaning |
| --- | --- | --- | --- |
| AUROC (0.5 = chance) | 1.00 on 9 models | 0.71 for the previous method | Perfect ranking here |

**Decision.** Keep it as the default baseline.

## Setup

Nine VGG9 checkpoints, four attacked.

## Correctness checks

Unit tests and the independent verifier passed.

## Open items

None.

"""

SESSION_BODY = """# Scoring mechanism review

## Takeaways

- The stated mechanism does not drive the score.
- The score measures distance from the parent model (inferred).

## Method

The score projects each layer onto a reference subspace and measures the residual.

| Term | Meaning |
| --- | --- |
| C | Concentration of the residual across layers |

## Discussion

The projected-update term is 0.14–1.3% of residual energy.

## Decisions

| Item | Status | Reason |
| --- | --- | --- |
| Rewrite the mechanism prose now | rejected | The statistic is not fixed yet |

## Open items

Run the scale-separated decomposition.

"""


def note(kind: str, body: str | None = None, **appendix_options: object) -> str:
    bodies = {"implementation": IMPLEMENTATION_BODY, "evaluation": EVALUATION_BODY, "session": SESSION_BODY}
    if kind != "implementation":
        appendix_options.setdefault("change", None)
    return (body if body is not None else bodies[kind]) + appendix(kind, **appendix_options)  # type: ignore[arg-type]


class CustodyTests(unittest.TestCase):
    def test_snapshot_separates_task_preexisting_and_outside_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = make_repo(root)
            (repo / "src").mkdir()
            (repo / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
            git(repo, "add", "src/a.py")
            git(repo, "commit", "-q", "-m", "add a")
            (repo / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")
            (repo / "notes.txt").write_text("someone else's work\n", encoding="utf-8")
            snapshot = root / "snapshot.json"
            run_tool("start", "--repo", str(repo), "--output", str(snapshot))

            (repo / "src" / "a.py").write_text("a = 3\nb = 4\n", encoding="utf-8")
            (repo / "src" / "new.py").write_text("c = 5\n", encoding="utf-8")
            (repo / "README.md").write_text("changed outside scope\n", encoding="utf-8")
            data = custody("--snapshot", str(snapshot), "--path", "src")

            self.assertEqual(data["task_changes"], ["src/a.py", "src/new.py"])
            self.assertEqual(data["preexisting_in_task_paths"], ["src/a.py"])
            self.assertEqual(data["outside_change_count"], 2)
            self.assertEqual(data["history"], "same")
            self.assertEqual(data["commits"], [])
            self.assertEqual(data["diff"]["files"], 1)
            self.assertEqual(data["diff"]["untracked_files"], 1)
            self.assertEqual(data["diff"]["basis"], "baseline to working tree")

            markdown = run_tool("custody", "--snapshot", str(snapshot), "--path", "src").stdout
            self.assertIn("- Pre-existing changes in task paths: `src/a.py`", markdown)
            self.assertIn("files=1; insertions=2; deletions=1; binary_files=0; untracked_files=1", markdown)
            self.assertIn("- Changes outside task paths: 2 paths (not listed)", markdown)
            self.assertNotIn("notes.txt", markdown)

    def test_start_rejects_overwrite_snapshot_inside_repo_and_non_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = make_repo(root)
            snapshot = root / "snapshot.json"
            run_tool("start", "--repo", str(repo), "--output", str(snapshot))
            self.assertIn("already exists", run_tool("start", "--repo", str(repo), "--output", str(snapshot), expect=2).stderr)
            inside = run_tool("start", "--repo", str(repo), "--output", str(repo / "s.json"), expect=2)
            self.assertIn("outside the repository", inside.stderr)
            plain = root / "plain"
            plain.mkdir()
            result = run_tool("start", "--repo", str(plain), "--output", str(root / "p.json"), expect=2)
            self.assertIn("Git: not applicable", result.stderr)

    def test_custody_rejects_root_and_escaping_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = make_repo(Path(temporary))
            for path in (".", "../elsewhere", "/"):
                run_tool("custody", "--repo", str(repo), "--baseline", "unavailable", "--path", path, expect=2)
            run_tool("custody", "--repo", str(repo), "--baseline", "not-a-commit", "--path", "src", expect=2)

    def test_late_start_with_unavailable_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = make_repo(Path(temporary))
            (repo / "task.txt").write_text("late change\n", encoding="utf-8")
            (repo / "README.md").write_text("edited\n", encoding="utf-8")
            data = custody("--repo", str(repo), "--baseline", "unavailable", "--path", "task.txt", "--path", "README.md")
            self.assertIsNone(data["baseline_head"])
            self.assertIsNone(data["preexisting_in_task_paths"])
            self.assertEqual(data["history"], "unavailable")
            self.assertEqual(data["diff"]["basis"], "uncommitted changes only; no baseline")
            self.assertEqual(data["diff"]["files"], 1)
            markdown = run_tool("custody", "--repo", str(repo), "--baseline", "unavailable", "--path", "task.txt").stdout
            self.assertIn("unavailable (no start snapshot)", markdown)
            self.assertIn("- Commits since baseline: unavailable", markdown)

    def test_explicit_baseline_captures_commits_and_detached_head(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = make_repo(Path(temporary))
            baseline = git(repo, "rev-parse", "HEAD")
            (repo / "task.txt").write_text("committed change\n", encoding="utf-8")
            git(repo, "add", "task.txt")
            git(repo, "commit", "-q", "-m", "change task")
            final_head = git(repo, "rev-parse", "HEAD")
            git(repo, "checkout", "-q", "--detach", final_head)
            data = custody("--repo", str(repo), "--baseline", baseline, "--path", "task.txt")
            self.assertEqual(data["branch"], "detached")
            self.assertEqual(data["task_changes"], ["task.txt"])
            self.assertEqual(data["history"], "ancestor")
            self.assertEqual(data["commits"], [{"hash": final_head, "subject": "change task"}])

    def test_diverged_history_does_not_attribute_commits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = make_repo(Path(temporary))
            common = git(repo, "rev-parse", "HEAD")
            (repo / "baseline-only.txt").write_text("baseline branch\n", encoding="utf-8")
            git(repo, "add", "baseline-only.txt")
            git(repo, "commit", "-q", "-m", "baseline branch commit")
            baseline = git(repo, "rev-parse", "HEAD")
            git(repo, "checkout", "-q", "-b", "other", common)
            (repo / "task.txt").write_text("other branch\n", encoding="utf-8")
            git(repo, "add", "task.txt")
            git(repo, "commit", "-q", "-m", "other branch commit")
            data = custody("--repo", str(repo), "--baseline", baseline, "--path", "task.txt")
            self.assertEqual(data["history"], "diverged")
            self.assertEqual(data["commits"], [])
            markdown = run_tool("custody", "--repo", str(repo), "--baseline", baseline, "--path", "task.txt").stdout
            self.assertIn("None attributed (history diverged", markdown)

    def test_paths_with_spaces_rename_delete_and_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = make_repo(root)
            spaced = repo / "space dir"
            spaced.mkdir()
            (spaced / "old name.txt").write_text("old\n", encoding="utf-8")
            (spaced / "delete me.txt").write_text("delete\n", encoding="utf-8")
            git(repo, "add", "space dir")
            git(repo, "commit", "-q", "-m", "add spaced files")
            snapshot = root / "snapshot.json"
            run_tool("start", "--repo", str(repo), "--output", str(snapshot))
            git(repo, "mv", "space dir/old name.txt", "space dir/new name.txt")
            git(repo, "rm", "-q", "space dir/delete me.txt")
            (spaced / "new untracked.txt").write_text("new\n", encoding="utf-8")
            data = custody("--snapshot", str(snapshot), "--path", "space dir")
            for path in ("space dir/new name.txt", "space dir/delete me.txt", "space dir/new untracked.txt"):
                self.assertIn(path, data["task_changes"])
            self.assertEqual(data["preexisting_in_task_paths"], [])
            self.assertEqual(data["diff"]["untracked_files"], 1)

    def test_unborn_repository_reports_staged_and_untracked_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "unborn"
            repo.mkdir()
            git(repo, "init", "-q")
            snapshot = root / "snapshot.json"
            run_tool("start", "--repo", str(repo), "--output", str(snapshot))
            (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
            git(repo, "add", "staged.txt")
            data = custody("--snapshot", str(snapshot), "--path", "staged.txt", "--path", "untracked.txt")
            self.assertIsNone(data["baseline_head"])
            self.assertIsNone(data["final_head"])
            self.assertEqual(data["task_changes"], ["staged.txt", "untracked.txt"])
            self.assertEqual(data["diff"]["basis"], "staged changes; no commits yet")
            self.assertEqual((data["diff"]["files"], data["diff"]["untracked_files"]), (1, 1))


class ValidateTests(unittest.TestCase):
    def validate(self, text: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-11-05-note.md"
            path.write_text(text, encoding="utf-8")
            return run_tool("validate", "--note", str(path), expect=expect)

    def assert_rejected(self, text: str, message: str) -> None:
        self.assertIn(message, self.validate(text, expect=1).stderr)

    def test_valid_records_of_each_kind_pass(self) -> None:
        for kind in ("implementation", "evaluation", "session"):
            with self.subTest(kind=kind):
                self.assertIn(f"valid format-4 {kind} record", self.validate(note(kind)).stdout)
        self.validate(note("implementation", change="new"))
        self.validate(note("evaluation", EVALUATION_BODY.replace("## Correctness", "## Detailed results\n\nPer-dataset tables.\n\n## Correctness")))

    def test_reference_templates_match_the_validator(self) -> None:
        reference = FORMATS.read_text(encoding="utf-8")
        for kind, heading in (("implementation", "Implementation"), ("evaluation", "Evaluation"), ("session", "Session")):
            with self.subTest(kind=kind):
                section = reference.split(f"\n## {heading}\n", 1)[1]
                template = re.search(r"~~~markdown\n(.*?)\n~~~", section, re.DOTALL).group(1)
                self.assert_rejected(note(kind, template + "\n\n"), "unresolved template placeholder")
                filled = re.sub(r"<[^<>\n]+>", "Filled in", template)
                self.validate(note(kind, filled + "\n\n"))

    def test_evaluation_readout_requires_results_table(self) -> None:
        body = re.sub(r"\| Measure.*?\n\n", "", EVALUATION_BODY, flags=re.DOTALL)
        self.assert_rejected(note("evaluation", body), "## Readout needs a results table")

    def test_session_requires_method_takeaway_bullets_and_decisions_table(self) -> None:
        no_method = re.sub(r"## Method\n.*?(?=## Discussion)", "", SESSION_BODY, flags=re.DOTALL)
        self.assert_rejected(note("session", no_method), "missing section: ## Method")
        no_table = SESSION_BODY.replace("| Rewrite the mechanism prose now | rejected | The statistic is not fixed yet |", "")
        no_table = re.sub(r"\| Item.*?\n\| ---.*?\n", "Decided nothing.\n", no_table)
        self.assert_rejected(note("session", no_table), "## Decisions needs a table")
        prose = SESSION_BODY.replace("- The stated", "The stated").replace("- The score", "The score")
        self.assert_rejected(note("session", prose), "## Takeaways needs bullet points")

    def test_change_type_is_required_for_implementation_only(self) -> None:
        self.assert_rejected(note("implementation", change=None), "Change type `fix` or `new`")
        self.assert_rejected(note("evaluation", change="fix"), "implementation records only")

    def test_metadata_values_are_checked(self) -> None:
        self.assert_rejected(note("implementation").replace("`done`", "`completed`"), "Status must be one of")
        self.assert_rejected(note("implementation").replace("2026-11-05", "Nov 5"), "Date must be YYYY-MM-DD")
        self.assert_rejected(note("implementation").replace("`implementation`", "`coding-progress`"), "Kind must be one of")

    def test_section_order_and_body_placement(self) -> None:
        swapped = IMPLEMENTATION_BODY.replace("## Outcome", "## TEMP").replace("## Change", "## Outcome").replace("## TEMP", "## Change")
        self.assert_rejected(note("implementation", swapped), "must appear in this order")
        missing = IMPLEMENTATION_BODY.replace("## Checks\n\nUnit tests cover retry, back-off, and the permanent-error path; all pass.\n\n", "")
        self.assert_rejected(note("implementation", missing), "missing section: ## Checks")

    def test_commands_need_results_and_git_section(self) -> None:
        text = note("implementation").replace("— `pass` — ", "— ")
        self.assert_rejected(text, "Commands entry lacks")
        self.assert_rejected(note("evaluation").replace("## Git\n\nGit: not applicable\n", ""), "missing appendix section: ## Git")

    def test_blocked_record_names_its_blocker(self) -> None:
        self.assert_rejected(note("implementation", status="blocked"), "must name the blocker")
        blocked = IMPLEMENTATION_BODY.replace("## Open items\n\nNone.", "## Open items\n\nBlocked: staging credentials expired.")
        self.validate(note("implementation", blocked, status="blocked"))

    def test_placeholders_ignore_html_links_code_and_math(self) -> None:
        allowed = IMPLEMENTATION_BODY.replace(
            "None.",
            "See <https://example.com/x>, `--path <task path>`, $a<b>c$, and <br> tags.\n\n```text\nrun <skill-path>\n```",
        )
        self.validate(note("implementation", allowed))
        self.assert_rejected(note("implementation", IMPLEMENTATION_BODY.replace("None.", "<next step>")), "<next step>")

    def test_appendix_must_be_folded(self) -> None:
        text = note("session").replace("<details>\n<summary>Record details</summary>\n", "").replace("</details>\n", "")
        self.assert_rejected(text, "fold the appendix")

    def test_fenced_headings_do_not_count_as_sections(self) -> None:
        fenced = SESSION_BODY.replace(
            "## Discussion\n", "## Discussion\n\n~~~markdown\n## Decisions\n\n| A | B |\n| --- | --- |\n~~~\n\n"
        )
        self.validate(note("session", fenced))

    def test_legacy_notes_are_frozen(self) -> None:
        legacy = "# Old\n\n## Outcome\n\nDone.\n\n- Record format: `3`\n- Date: `2026-10-01`\n"
        self.assert_rejected(legacy, "format 3 notes are frozen")


class ListTests(unittest.TestCase):
    def test_list_reads_every_format_with_headlines_without_writing(self) -> None:
        notes = {
            "2026-08-01-v1.md": "# V1\n\n- Date: `2026-08-01`\n- Repository: `demo`\n- Status: `completed`\n\n"
            "## Outcome\n\n- Result: Shipped the parser.\n",
            "2026-09-01-v2.md": "# V2\n\n## Outcome\n\nThe migration finished on all\nhosts. Extra.\n\n"
            "- Record format: `2`\n- Mode: `coding-progress`\n- Date: `2026-09-01`\n- Project: demo\n- Status: `completed`\n",
            "nested/2026-10-01-v3.md": "# V3\n\n## Outcome\n\n**Done:** reviewed the design.\n\n"
            "- Record format: `3`\n- Mode: `session-documentation`\n- Date: `2026-10-01`\n- Project: demo\n- Status: `done`\n",
            "2026-11-05-v4.md": note("evaluation"),
            "README.md": "# Progress\n\nNot a record.\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, text in notes.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(text, encoding="utf-8")
            before = {path: path.read_bytes() for path in root.rglob("*")  if path.is_file()}

            entries = json.loads(run_tool("list", "--root", str(root), "--json").stdout)
            by_format = {entry["record_format"]: entry for entry in entries}
            self.assertEqual(sorted(by_format), ["1", "2", "3", "4"])
            self.assertEqual(by_format["1"]["headline"], "Result: Shipped the parser.")
            self.assertEqual(by_format["2"]["headline"], "The migration finished on all hosts.")
            self.assertEqual(by_format["3"]["headline"], "Done: reviewed the design.")
            self.assertEqual(by_format["4"]["headline"], "Yes on this roster: it ranks every attack above every clean model.")
            self.assertEqual(by_format["4"]["kind"], "evaluation")
            self.assertEqual(by_format["3"]["path"], "nested/2026-10-01-v3.md")

            filtered = json.loads(run_tool("list", "--root", str(root), "--json", "--kind", "evaluation").stdout)
            self.assertEqual([entry["record_format"] for entry in filtered], ["4"])
            dated = json.loads(run_tool("list", "--root", str(root), "--json", "--since", "2026-09-15").stdout)
            self.assertEqual(sorted(entry["record_format"] for entry in dated), ["3", "4"])
            table = run_tool("list", "--root", str(root), "--width", "20").stdout
            self.assertIn("HEADLINE", table.splitlines()[0])
            self.assertIn("…", table)
            run_tool("list", "--root", str(root), "--since", "yesterday", expect=2)
            self.assertEqual(before, {path: path.read_bytes() for path in root.rglob("*") if path.is_file()})


if __name__ == "__main__":
    unittest.main()
