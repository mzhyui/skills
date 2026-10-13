"""Behavioral checks for export, diagnosis, and preservation of existing files."""
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/render_check.py"
SPEC = importlib.util.spec_from_file_location("render_check", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def svg(contents):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 400">{contents}</svg>'


class InspectionTests(unittest.TestCase):
    def inspect(self, contents, width=7):
        return MODULE.inspect_svg(ET.fromstring(svg(contents)), width, 8)

    def test_duplicate_and_missing_references(self):
        result = self.inspect('<rect id="a"/><rect id="a"/><use href="#missing"/>')
        self.assertTrue(any("Duplicate IDs" in s for s in result[4]))
        self.assertTrue(any("Unresolved local reference" in s for s in result[4]))

    def test_external_dependencies_are_rejected(self):
        for contents in ['<image href="https://example.com/figure.png"/>', '<style>@import "remote.css";</style>', '<path fill="url(https://example.com/fill)"/>']:
            with self.subTest(contents=contents):
                self.assertTrue(self.inspect(contents)[4])

    def test_font_size_tracks_physical_width(self):
        contents = '<g font-size="20"><text id="label" x="30" y="80">Label</text></g>'
        full = self.inspect(contents)
        reduced = self.inspect(contents, width=3.5)
        self.assertAlmostEqual(full[3][0]["size_pt"], 10.08)
        self.assertAlmostEqual(reduced[3][0]["size_pt"], 5.04)
        self.assertFalse(full[5])
        self.assertTrue(any("Small text" in s for s in reduced[5]))

    def test_uncertain_typography_is_not_reported_as_checked(self):
        for contents in ['<g transform="scale(.5)"><text font-size="20">Label</text></g>', '<style>text {font-size: 5px}</style><text>Label</text>']:
            with self.subTest(contents=contents):
                result = self.inspect(contents)
                self.assertEqual(result[3], [])
                self.assertTrue(result[5])

    def test_inline_font_style_overrides_presentation_attribute(self):
        result = self.inspect('<text font-size="8" style="font-size: 24px">Label</text>')
        self.assertAlmostEqual(result[3][0]["size_pt"], 12.096)


class CommandTests(unittest.TestCase):
    def invoke(self, source, out, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), str(source), "--out-dir", str(out), *extra], capture_output=True, text=True, timeout=60)

    def test_invalid_svg_writes_failure_report(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "input.svg"
            source.write_text(svg('<use href="#missing"/>'))
            result = self.invoke(source, base / "out")
            self.assertEqual(result.returncode, 2)
            report = json.loads((base / "out/render-report.json").read_text())
            self.assertEqual(report["status"], "invalid_input")
            self.assertFalse((base / "out/figure.pdf").exists())

    def test_existing_output_and_source_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "input.svg"
            source.write_text(svg('<text font-size="20">Label</text>'))
            out = base / "out"
            out.mkdir()
            sentinel = out / "figure.pdf"
            sentinel.write_bytes(b"existing output")
            self.assertEqual(self.invoke(source, out).returncode, 2)
            self.assertEqual(sentinel.read_bytes(), b"existing output")
            same = base / "figure.svg"
            same.write_bytes(source.read_bytes())
            self.assertEqual(self.invoke(same, base, "--overwrite").returncode, 2)
            self.assertEqual(same.read_bytes(), source.read_bytes())

    @unittest.skipUnless(shutil.which("inkscape"), "Inkscape not installed")
    def test_real_export_detects_overlap_and_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "input.svg"
            source.write_text(svg('<text id="a" x="30" y="80" font-size="22">OVERLAP</text><text id="b" x="30" y="80" font-size="22">OVERLAP</text><rect id="offpage" x="980" y="200" width="100" height="30"/>'))
            before = source.read_bytes()
            out = base / "out"
            result = self.invoke(source, out)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((out / "render-report.json").read_text())
            self.assertEqual(report["status"], "rendered_with_warnings")
            self.assertTrue(any("text overlap" in w for w in report["warnings"]))
            self.assertTrue(any("canvas overflow" in w for w in report["warnings"]))
            self.assertEqual(report["scientific_review"], "not_performed")
            self.assertEqual(report["visual_review"], "not_performed")
            self.assertEqual(source.read_bytes(), before)
            self.assertTrue((out / "figure.pdf").read_bytes().startswith(b"%PDF"))
            png = (out / "figure.png").read_bytes()
            self.assertEqual(struct.unpack(">II", png[16:24]), (2100, 840))


if __name__ == "__main__":
    unittest.main()
