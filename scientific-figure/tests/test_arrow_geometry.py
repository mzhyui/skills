"""Check arrow silhouettes, attachment positions, and invalid-route rejection."""
import importlib.util
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

try:
    from PIL import Image
except ImportError:
    Image = None

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/arrow_geometry.py"
SPEC = importlib.util.spec_from_file_location("arrow_geometry", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SVG = MODULE.SVG


class GeometryTests(unittest.TestCase):
    def test_tip_and_bends_preserved_in_all_directions_and_widths(self):
        for direction in [(1, 0), (-1, 0), (0, 1), (0, -1), (0.6, 0.8), (-0.6, -0.8)]:
            for width in (1, 4, 12, 24):
                with self.subTest(direction=direction, width=width):
                    dx, dy = direction
                    points = [(-20, -20), (0, 0), (100 * dx, 100 * dy)]
                    original = list(points)
                    length, head_width = 3 * width, 3 * width
                    shaft, overlap = MODULE.arrow_geometry(points, width, length, head_width)
                    self.assertEqual(points, original)
                    self.assertEqual(shaft[:-1], points[:-1])
                    for i, delta in enumerate((dx, dy)):
                        self.assertAlmostEqual(shaft[-1][i] + (length - overlap) * delta, points[-1][i])
                    # Both butt-cap corners lie strictly inside the triangle.
                    self.assertLess(width, head_width * (1 - overlap / length))

    def test_bad_dimensions_rejected(self):
        for dims in [(0, 12, 12), (-1, 12, 12), (4, 0, 12), (4, 12, 4),
                     (4, 12, 3), (math.nan, 12, 12), (4, math.inf, 12)]:
            with self.subTest(dimensions=dims), self.assertRaises(ValueError):
                MODULE.arrow_geometry([(0, 0), (100, 0)], *dims)

    def test_invalid_or_too_short_routes_rejected_without_crossing_bend(self):
        for route in [[], [(0, 0)], [(0, 0), (0, 0)], [(0, 0), (12, 0)],
                      [(0, 0), (100, 0), (100, 5)], [(0, 0), (math.inf, 0)],
                      [(0, 0), (1, 2, 3)]]:
            with self.subTest(route=route), self.assertRaises(ValueError):
                MODULE.arrow_geometry(route, 4, 12, 12)

    def test_dashed_arrow_head_overrides_inherited_stroke_and_dash(self):
        root = ET.Element(f"{{{SVG}}}svg", {"stroke": "red", "stroke-width": "50", "stroke-dasharray": "1 2"})
        defs = ET.SubElement(root, f"{{{SVG}}}defs")
        path = MODULE.add_arrow(root, defs, "feedback", [(0, 0), (100, 0)],
                                color="blue", stroke_width=4, dash="9 7")
        marker = defs[0]
        self.assertEqual(path.get("stroke-linecap"), "butt")
        self.assertEqual(path.get("stroke-dasharray"), "9 7")
        self.assertEqual(marker.get("markerUnits"), "userSpaceOnUse")
        self.assertEqual(marker[0].get("stroke"), "none")
        self.assertEqual(marker[0].get("stroke-dasharray"), "none")
        self.assertEqual(marker[0].get("fill"), path.get("stroke"))
        self.assertEqual(path.get("marker-end"), f"url(#{marker.get('id')})")

    @unittest.skipUnless(shutil.which("inkscape") and Image, "requires Inkscape and Pillow")
    def test_rendered_heads_have_taper_without_shaft_shoulders_or_tip_bumps(self):
        root = ET.Element(f"{{{SVG}}}svg", {"viewBox": "0 0 200 180", "width": "200", "height": "180"})
        defs = ET.SubElement(root, f"{{{SVG}}}defs")
        for index, width in enumerate((2, 6, 12, 24)):
            y = 20 + index * 40
            MODULE.add_arrow(root, defs, f"w{width}", [(10, y), (170, y)], color="black", stroke_width=width)
        with tempfile.TemporaryDirectory() as directory:
            source, png = Path(directory) / "source.svg", Path(directory) / "render.png"
            ET.ElementTree(root).write(source)
            result = subprocess.run(["inkscape", str(source), "--export-area-page", "--export-width=800",
                                     "--export-background=white", "--export-background-opacity=1",
                                     f"--export-filename={png}"], capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(png) as rendered:
                rendered = rendered.convert("RGB")
                for index, width in enumerate((2, 6, 12, 24)):
                    y = 20 + index * 40
                    with self.subTest(width=width):
                        # One unit before the tip, only a narrow triangle remains.
                        # A full-width shaft ending at the tip colors this pixel.
                        self.assertEqual(rendered.getpixel((169 * 4, int((y + width * 0.45) * 4))), (255, 255, 255))
                        # A round-capped shaft at the tip extends into this region.
                        self.assertEqual(rendered.getpixel((171 * 4, y * 4)), (255, 255, 255))
                        self.assertLess(rendered.getpixel((166 * 4, y * 4))[0], 64)


if __name__ == "__main__":
    unittest.main()
