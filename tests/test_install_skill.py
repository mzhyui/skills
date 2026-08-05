"""Unit tests for scripts/install_skill.py (pure logic, no network)."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from install_skill import (  # noqa: E402
    InstallPlan,
    parse_source,
    plan_install,
    install_from_dir,
)


class ParseSourceTests(unittest.TestCase):
    def test_https_url_with_branch_and_path(self) -> None:
        src = parse_source("https://github.com/mzhyui/skills/tree/main/anchor-plans")
        self.assertEqual(
            (src.owner, src.repo, src.ref, src.path, src.name),
            ("mzhyui", "skills", "main", "anchor-plans", "anchor-plans"),
        )

    def test_https_url_with_trailing_slash_and_deep_path(self) -> None:
        src = parse_source("https://github.com/mzhyui/skills/tree/v1/x/nested-skill/")
        self.assertEqual(
            (src.owner, src.repo, src.ref, src.path, src.name),
            ("mzhyui", "skills", "v1", "x/nested-skill", "nested-skill"),
        )

    def test_ssh_url(self) -> None:
        src = parse_source("git@github.com:mzhyui/skills.git/tree/dev/record-coding-progress")
        self.assertEqual(
            (src.repo, src.ref, src.name),
            ("skills", "dev", "record-coding-progress"),
        )

    def test_bare_name_defaults_to_default_repo(self) -> None:
        src = parse_source("anchor-plans")
        self.assertEqual(
            (src.owner, src.repo, src.ref, src.name),
            ("mzhyui", "skills", "main", "anchor-plans"),
        )

    def test_owner_repo_path_form(self) -> None:
        src = parse_source("mzhyui/skills/edit-paper-with-history")
        self.assertEqual(
            (src.owner, src.repo, src.name),
            ("mzhyui", "skills", "edit-paper-with-history"),
        )

    def test_missing_skill_path_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_source("https://github.com/mzhyui/skills")
        with self.assertRaises(ValueError):
            parse_source("mzhyui/skills")

    def test_clone_url(self) -> None:
        src = parse_source("anchor-plans")
        self.assertEqual(src.clone_url(), "https://github.com/mzhyui/skills.git")


class _SkillFixture:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="skill-fixture-"))
        self.skill = self.root / "demo-skill"
        (self.skill / "scripts").mkdir(parents=True)
        (self.skill / "agents").mkdir()
        (self.skill / "claude").mkdir()
        (self.skill / "SKILL.md").write_text("---\nname: demo-skill\n---\nbody\n")
        (self.skill / "scripts" / "tool.py").write_text("print('hi')\n")
        (self.skill / "agents" / "openai.yaml").write_text("agent: codex\n")
        (self.skill / "claude" / "agent.md").write_text("---\nname: demo-skill\n---\nagent\n")

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class InstallLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = _SkillFixture()
        self.addCleanup(self.fx.cleanup)

    def test_plan_paths_under_dest(self) -> None:
        dest = Path(tempfile.mkdtemp(prefix="dest-"))
        self.addCleanup(lambda: shutil.rmtree(dest, ignore_errors=True))
        plan = plan_install("demo-skill", self.fx.skill, dest)
        self.assertIsInstance(plan, InstallPlan)
        self.assertEqual(plan.skill_dir, dest / "skills" / "demo-skill")
        self.assertEqual(plan.agent_file, dest / "agents" / "demo-skill.md")
        self.assertFalse(hasattr(plan, "command_file"))

    def test_install_copies_skill_and_components(self) -> None:
        dest = Path(tempfile.mkdtemp(prefix="dest-"))
        self.addCleanup(lambda: shutil.rmtree(dest, ignore_errors=True))
        plan = install_from_dir("demo-skill", self.fx.skill, dest)
        self.assertTrue((plan.skill_dir / "SKILL.md").is_file())
        self.assertTrue((plan.skill_dir / "scripts" / "tool.py").is_file())
        self.assertTrue(plan.agent_file.is_file())

    def test_install_excludes_codex_and_claude_dirs(self) -> None:
        dest = Path(tempfile.mkdtemp(prefix="dest-"))
        self.addCleanup(lambda: shutil.rmtree(dest, ignore_errors=True))
        plan = install_from_dir("demo-skill", self.fx.skill, dest)
        self.assertFalse((plan.skill_dir / "agents").exists())
        self.assertFalse((plan.skill_dir / "claude").exists())

    def test_existing_dest_refuses_without_force(self) -> None:
        dest = Path(tempfile.mkdtemp(prefix="dest-"))
        self.addCleanup(lambda: shutil.rmtree(dest, ignore_errors=True))
        install_from_dir("demo-skill", self.fx.skill, dest)
        with self.assertRaises(FileExistsError):
            plan_install("demo-skill", self.fx.skill, dest)

    def test_force_overwrites_existing_install(self) -> None:
        dest = Path(tempfile.mkdtemp(prefix="dest-"))
        self.addCleanup(lambda: shutil.rmtree(dest, ignore_errors=True))
        install_from_dir("demo-skill", self.fx.skill, dest)
        plan = plan_install("demo-skill", self.fx.skill, dest, force=True)
        self.assertEqual(plan.skill_dir, dest / "skills" / "demo-skill")

    def test_missing_skill_dir_raises(self) -> None:
        dest = Path(tempfile.mkdtemp(prefix="dest-"))
        self.addCleanup(lambda: shutil.rmtree(dest, ignore_errors=True))
        missing = self.fx.root / "nope"
        with self.assertRaises(FileNotFoundError):
            plan_install("nope", missing, dest)


if __name__ == "__main__":
    unittest.main()
