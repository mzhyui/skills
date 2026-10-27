"""Build editable polyline arrows whose shafts stay inside their arrowheads.

Import ``add_arrow`` from a figure generator. Coordinates describe the intended
route through the arrow tip; only the rendered shaft endpoint is shortened.
Python standard library only. Curves and start markers need separate geometry.
"""
import math
from collections.abc import Sequence
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
Point = tuple[float, float]


def arrow_geometry(
    points: Sequence[Sequence[float]],
    stroke_width: float,
    head_length: float,
    head_width: float,
) -> tuple[list[Point], float]:
    """Return shortened shaft points and the marker's safe base overlap.

    Require the head to fit the last segment so its orientation stays correct.
    Reject degenerate geometry rather than silently moving a bend or the tip.
    """
    dimensions = (stroke_width, head_length, head_width)
    if not all(math.isfinite(v) and v > 0 for v in dimensions):
        raise ValueError("Arrow dimensions must be finite and positive")
    if head_width <= stroke_width:
        raise ValueError("Head width must exceed shaft width")
    route = [tuple(map(float, point)) for point in points]
    if len(route) < 2 or any(len(p) != 2 or not all(map(math.isfinite, p)) for p in route):
        raise ValueError("Arrow route needs at least two finite 2D points")
    if any(a == b for a, b in zip(route, route[1:])):
        raise ValueError("Arrow route has a zero-length segment")
    # At x=overlap the triangle is still wider than the entire shaft. A small
    # overlap prevents an antialiasing seam without entering the narrow taper.
    overlap = min(stroke_width / 2, head_length * (1 - stroke_width / head_width) / 2)
    dx, dy = (route[-1][i] - route[-2][i] for i in range(2))
    terminal_length = math.hypot(dx, dy)
    if terminal_length <= head_length:
        raise ValueError("Head must fit inside the final segment; reduce it or reroute the arrow")
    trim = head_length - overlap
    x, y = route[-1]
    route[-1] = (x - trim * dx / terminal_length, y - trim * dy / terminal_length)
    return route, overlap


def add_arrow(
    parent: ET.Element,
    defs: ET.Element,
    identifier: str,
    points: Sequence[Sequence[float]],
    *,
    color: str,
    stroke_width: float = 3,
    head_length: float | None = None,
    head_width: float | None = None,
    dash: str | None = None,
) -> ET.Element:
    """Append a butt-capped shaft and a solid, unstroked, named end marker.

    Use a unique identifier per arrow and pass the root SVG's defs element.
    Head dimensions use canvas units, independent of inherited stroke styles.
    """
    length = 3 * stroke_width if head_length is None else head_length
    width = 3 * stroke_width if head_width is None else head_width
    shaft, overlap = arrow_geometry(points, stroke_width, length, width)
    marker_id = f"{identifier}-head"
    marker = ET.SubElement(defs, f"{{{SVG}}}marker", {
        "id": marker_id, "viewBox": f"0 0 {length:g} {width:g}",
        "markerWidth": f"{length:g}", "markerHeight": f"{width:g}",
        "markerUnits": "userSpaceOnUse", "refX": f"{overlap:g}",
        "refY": f"{width / 2:g}", "orient": "auto", "overflow": "visible",
    })
    ET.SubElement(marker, f"{{{SVG}}}path", {
        "d": f"M 0 0 L {length:g} {width / 2:g} L 0 {width:g} Z",
        "fill": color, "stroke": "none", "stroke-dasharray": "none",
    })
    attributes = {
        "id": identifier, "d": "M " + " L ".join(f"{x:.12g} {y:.12g}" for x, y in shaft),
        "fill": "none", "stroke": color, "stroke-width": f"{stroke_width:g}",
        "stroke-linecap": "butt", "stroke-linejoin": "round",
        "marker-end": f"url(#{marker_id})", "stroke-dasharray": dash or "none",
    }
    return ET.SubElement(parent, f"{{{SVG}}}path", attributes)
