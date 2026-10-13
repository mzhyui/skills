"""Verify installation carries the complete scientific-figure resource tree."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT.parent / "scripts/install_skill.py"


@unittest.skipUnless(INSTALLER.is_file(), "requires the skill hub installer")
class InstallationTests(unittest.TestCase):
    def test_install_preserves_resources_and_extracts_claude_agent(self):
        spec = importlib.util.spec_from_file_location("scientific_figure_installer", INSTALLER)
        installer = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = installer
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            plan = installer.install_from_dir("scientific-figure", ROOT, dest)
            for source in ROOT.rglob("*"):
                relative = source.relative_to(ROOT)
                if not source.is_file() or any(part in installer.EXCLUDE_DIRS for part in relative.parts):
                    continue
                with self.subTest(path=str(relative)):
                    self.assertEqual((plan.skill_dir / relative).read_bytes(), source.read_bytes())
            self.assertEqual(plan.agent_file.read_bytes(), (ROOT / "claude/agent.md").read_bytes())
            self.assertFalse((plan.skill_dir / "agents").exists())
            self.assertFalse((plan.skill_dir / "claude").exists())


if __name__ == "__main__":
    unittest.main()
