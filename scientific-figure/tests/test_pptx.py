"""Check native edit persistence, picture detection, and file preservation."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = load_module("pptx_check", ROOT / "scripts/pptx_check.py")
EXAMPLE = load_module("pptx_example", ROOT / "assets/example-editable-pptx.py")
HAS_PPTX = importlib.util.find_spec("pptx") is not None
P = CHECKER.NS["p"]
A = CHECKER.NS["a"]
R = CHECKER.NS["r"]


def write_fixture(path: Path, objects: str) -> None:
    """Minimal OOXML fixture for the inventory, not an application-ready deck."""
    with ZipFile(path, "w") as archive:
        archive.writestr("ppt/presentation.xml", f'''<p:presentation xmlns:p="{P}" xmlns:r="{R}">
          <p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>
          <p:sldSz cx="6400800" cy="3108960"/></p:presentation>''')
        archive.writestr("ppt/_rels/presentation.xml.rels", '''<Relationships
          xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          <Relationship Id="rId1" Target="slides/slide7.xml"/></Relationships>''')
        archive.writestr("ppt/slides/slide7.xml", f'''<p:sld xmlns:p="{P}" xmlns:a="{A}">
          <p:cSld><p:spTree>{objects}</p:spTree></p:cSld></p:sld>''')


class InventoryTests(unittest.TestCase):
    def test_picture_only_slide_does_not_imply_editable_diagram(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "picture.pptx"
            write_fixture(source, '<p:pic><p:nvPicPr><p:cNvPr id="2" name="whole-figure"/></p:nvPicPr></p:pic>')
            result = CHECKER.inspect_pptx(source)
            self.assertEqual(result["slides"][0]["part"], "ppt/slides/slide7.xml")
            self.assertEqual(result["slides"][0]["counts"]["picture"], 1)
            self.assertEqual(result["slides"][0]["counts"]["editable_text_objects"], 0)
            self.assertTrue(any("no native diagram geometry" in w for w in result["warnings"]))
            self.assertEqual(result["visual_review"], "not_performed")

    def test_group_text_and_broken_connection_are_reported(self):
        objects = '''<p:grpSp><p:nvGrpSpPr><p:cNvPr id="2" name="panel"/></p:nvGrpSpPr>
          <p:sp><p:nvSpPr><p:cNvPr id="3" name="label"/><p:cNvSpPr txBox="1"/></p:nvSpPr>
          <p:txBody><a:p><a:r><a:t>Input</a:t></a:r><a:br/><a:r><a:t>x</a:t></a:r></a:p></p:txBody></p:sp>
          </p:grpSp><p:cxnSp><p:nvCxnSpPr><p:cNvPr id="4" name="edge"/>
          <p:cNvCxnSpPr><a:stCxn id="3" idx="0"/><a:endCxn id="99" idx="1"/>
          </p:cNvCxnSpPr></p:nvCxnSpPr></p:cxnSp>'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "group.pptx"
            write_fixture(source, objects)
            report = CHECKER.inspect_pptx(source)
            self.assertEqual(report["status"], "invalid")
            self.assertIn("missing connection target 99", report["errors"][0])
            label = next(o for o in report["slides"][0]["objects"] if o["name"] == "label")
            self.assertEqual(label["text"], "Input\nx")
            self.assertEqual(label["parent_group"], "2")
            self.assertEqual(label["kind"], "text_box")

    def test_duplicate_ids_are_invalid(self):
        shape = '<p:sp><p:nvSpPr><p:cNvPr id="2" name="box"/></p:nvSpPr></p:sp>'
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "duplicate.pptx"
            write_fixture(source, shape + shape)
            report = CHECKER.inspect_pptx(source)
            self.assertEqual(report["status"], "invalid")
            self.assertTrue(any("duplicate object ID" in e for e in report["errors"]))

    def test_cli_preserves_source_and_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pptx"
            output = Path(directory) / "report.json"
            write_fixture(source, "")
            before = source.read_bytes()
            command = [sys.executable, str(ROOT / "scripts/pptx_check.py"), str(source), "--output"]
            first = subprocess.run(command + [str(output)], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            report_before = output.read_bytes()
            for path in (output, source):
                result = subprocess.run(command + [str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(output.read_bytes(), report_before)
            self.assertTrue(json.loads(report_before)["warnings"])

    def test_cli_rejects_malformed_input_without_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.pptx"
            output = Path(directory) / "report.json"
            source.write_text("not a zip")
            result = subprocess.run([sys.executable, str(ROOT / "scripts/pptx_check.py"),
                                     str(source), "--output", str(output)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())


@unittest.skipUnless(HAS_PPTX, "python-pptx is required for native generation/edit tests")
class NativeExampleTests(unittest.TestCase):
    def test_label_and_node_edits_survive_save_reopen_with_attachments(self):
        from pptx import Presentation
        from pptx.util import Inches

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "figure.pptx"
            edited = Path(directory) / "edited.pptx"
            EXAMPLE.build_presentation().save(source)
            original_bytes = source.read_bytes()
            report = CHECKER.inspect_pptx(source)
            self.assertFalse(report["errors"])
            counts = report["slides"][0]["counts"]
            self.assertEqual(counts.get("picture", 0), 0)
            self.assertGreater(counts["editable_text_objects"], 10)
            self.assertEqual(counts["attached_connectors"], 2)
            self.assertEqual(counts["group"], 3)
            deck = Presentation(source)
            shapes = {s.name: s for s in deck.slides[0].shapes}
            node = shapes["node-abstraction"]
            new_left = node.left + Inches(.1)
            node.left = new_left
            node.text_frame.paragraphs[0].runs[0].text = "Revised source"
            original_targets = {o["name"]: o["connections"] for o in report["slides"][0]["objects"]
                                if o.get("connections")}
            deck.save(edited)
            reopened = Presentation(edited)
            new_node = next(s for s in reopened.slides[0].shapes if s.name == node.name)
            self.assertEqual(new_node.left, new_left)
            self.assertEqual(new_node.text, "Revised source")
            updated = CHECKER.inspect_pptx(edited)
            for obj in updated["slides"][0]["objects"]:
                if obj["name"] in original_targets:
                    self.assertEqual(obj["connections"], original_targets[obj["name"]])
            self.assertEqual(source.read_bytes(), original_bytes)

    def test_generator_refuses_existing_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(ROOT / "assets/example-editable-pptx.py"), "--out-dir", directory]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            source = Path(directory) / "figure.pptx"
            before = source.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
