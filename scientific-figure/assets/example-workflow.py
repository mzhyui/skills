#!/usr/bin/env python3
"""Generate a self-contained vector example of the figure-making workflow.

Usage: python example-workflow.py --out-dir /tmp/figure-example
This illustrates the user's three-stage process, not a research algorithm.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
INK = "#26364A"
SOURCE = """# Source: user-provided figure-making workflow (excerpt)

## 1. Scientific abstraction
Give the AI your Methods section and request a stage-by-stage visual specification. Ask it to identify the inputs, transformations, computations, decisions, iterations, and outputs.
This prevents the model from inventing algorithmic operations merely to improve visual balance.

## 2. Graphical composition
Ask the AI to turn that specification into a detailed scene graph: every box, icon, arrow, label, equation, and color has a defined role and position.
For complex figures, use the image generator to explore illustrative styles and SVG generation to establish accurate geometry and text.

## 3. Render and validate
Generate the SVG, render it to PNG, inspect it visually, and ask the AI to fix overlapping annotations, weak visual hierarchy, inaccurate equations, and inconsistent colors. Repeat until it works at final manuscript size.

## Requested output from the supplied prompt
First create a precise diagram specification, then generate editable SVG. Check text, arrows, layout, and publication-size readability.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    names = ["method-source.md", "diagram-spec.md", "scene-graph.json", "figure.svg"]
    if any((out / name).exists() for name in names):
        parser.error("choose a directory without existing example artifacts")
    (out / "method-source.md").write_text(SOURCE, encoding="utf-8")
    source_hash = hashlib.sha256(SOURCE.encode()).hexdigest()
    spec = f"""# Diagram specification: scientific figure generation

Illustrative process diagram based on the supplied workflow, not experimental evidence.

## Brief and source
Landscape, 7 inches wide, 1440 × 620 user units, white background; editable text and native vectors. Minimum body font 24 units = 8.4 pt. Rounded panels and restrained illustrated icons use orange, blue, and purple as stage identifiers, reinforced by titles and numbers. These colors do not denote modalities in this example.

Source S1: `method-source.md`, SHA-256 `{source_hash}`. Section headings are stable anchors for the excerpt. PNG preview and editable SVG are source-requested; PDF is an additional publication export chosen in this implementation.

## Stages and nodes
| ID | Operation | Input | Output | Anchor |
| --- | --- | --- | --- | --- |
| abstraction | Identify entities and relations | Methods and exact notation | Diagram specification | S1 §1 |
| composition | Position panels, icons, labels, and arrows | Diagram specification | Scene graph and vector geometry | S1 §2 |
| validation | Render, inspect, and correct | Vector source | Editable figure and inspected previews | S1 §3; requested output |

## Edges
| ID | From → to | Meaning | Anchor |
| --- | --- | --- | --- |
| specify-to-compose | abstraction → composition | Specification informs composition | S1 §1–2 |
| compose-to-validate | composition → validation | Vector geometry goes to rendering/review | S1 §2–3 |
| revise-layout | validation → composition | If visual issues remain, revise layout and render again | S1 §3 |

The feedback arrow denotes visual revision, with stopping condition: the figure works at final manuscript size (S1 §3). It does not represent a learning algorithm. Scientific source problems would require revisiting abstraction; this compact example shows the explicitly described layout-revision loop only.

## Notation, icons, and abstraction choices
No mathematical equations, tensor dimensions, empirical scores, or scientific decision blocks occur in this source. None are added. Document, scene, and preview icons are schematic visual summaries of the three operations. Text lines inside icons are decorative strokes, not illegible scientific labels. Exact node wording is shortened for figure readability; the source excerpt preserves the full text.

## Open questions
None for this illustrative workflow. No inaccessible linked reference image was inspected; styling follows the user's written description.
"""
    (out / "diagram-spec.md").write_text(spec, encoding="utf-8")
    scene = {
        "schema_version": 1,
        "canvas": {"view_box": [0, 0, 1440, 620], "width_in": 7, "background": "white"},
        "typography": {"family": "DejaVu Sans", "min_font_pt": 8},
        "palette": {"ink": INK, "abstraction": "#B86B2C", "composition": "#377DA1", "validation": "#8061A7"},
        "panels": [], "nodes": [], "edges": [], "labels": [], "decorations": [], "equations": []}
    primitive_groups = {}

    def primitive(parent, kind, **attrs):
        primitive_groups.setdefault(parent, []).append({"tag": kind, "attrs": attrs})

    def label(identifier, parent, text, x, y, size=24, anchor="middle", weight="normal", fill=INK):
        scene["labels"].append({"id": identifier, "parent": parent, "text": text, "position": [x, y], "font_size": size, "anchor": anchor, "weight": weight, "fill": fill})

    stages = [
        ("abstraction", "Scientific abstraction", "#FFF5E9", "#B86B2C", "Extract entities and relations", "Diagram specification", "Sources + exact notation"),
        ("composition", "Graphical composition", "#EEF7FC", "#377DA1", "Arrange the scientific story", "Positioned scene graph", "Panels + icons + arrow routes"),
        ("validation", "Render and validate", "#F5F0FC", "#8061A7", "Inspect at manuscript size", "SVG + PDF + previews", "Science + layout review")]
    for i, (sid, title, fill, accent, action, output, detail) in enumerate(stages):
        x = 20 + i * 480
        panel = f"panel-{sid}"
        scene["panels"].append({"id": panel, "spec_id": sid, "box": [x, 20, 440, 490], "fill": fill, "stroke": accent})
        scene["nodes"].append({"id": sid, "spec_id": sid, "panel": panel, "kind": "operation", "box": [x, 20, 440, 490], "ports": {"in": [x, 308], "out": [x + 440, 308], "feedback": [x + 220, 510]}})
        label(f"title-{sid}", panel, title, x + 70, 80, 26, "start", "bold")
        primitive(panel, "circle", cx=x + 36, cy=70, r=22, fill=accent, stroke="none")
        label(f"number-{sid}", panel, str(i + 1), x + 36, 79, 26, weight="bold", fill="white")
        label(f"action-{sid}", panel, action, x + 220, 310)
        primitive(panel, "rect", x=x + 32, y=350, width=376, height=108, rx=17, fill="white", stroke=accent)
        label(f"output-{sid}", panel, output, x + 220, 391, 26, weight="bold")
        label(f"detail-{sid}", panel, detail, x + 220, 430, 24)
        icon = f"icon-{sid}"
        scene["decorations"].append({"id": icon, "spec_id": sid, "parent": panel, "box": [x + 110, 125, 220, 140], "role": "schematic operation illustration", "primitives": []})
        if i == 0:
            primitive(icon, "rect", x=x + 176, y=135, width=106, height=122, rx=10, fill="#F9DAB4", stroke=accent)
            primitive(icon, "rect", x=x + 157, y=124, width=106, height=122, rx=10, fill="white", stroke=accent)
            for j, length in enumerate([64, 52, 67, 43]):
                primitive(icon, "path", d=f"M {x+176} {154+j*21} h {length}", fill="none", stroke=accent)
        elif i == 1:
            for xx, yy, ww, hh in [(x+120, 142, 70, 44), (x+250, 142, 70, 44), (x+184, 222, 70, 44)]:
                primitive(icon, "rect", x=xx, y=yy, width=ww, height=hh, rx=10, fill="white", stroke=accent)
            for d in [f"M {x+190} 164 H {x+244}", f"M {x+285} 186 V 205 H {x+219} V 216"]:
                primitive(icon, "path", d=d, fill="none", stroke=accent, **{"marker-end": "url(#arrow)"})
        else:
            primitive(icon, "rect", x=x+130, y=133, width=180, height=128, rx=12, fill="white", stroke=accent)
            primitive(icon, "path", d=f"M {x+130} 163 H {x+310}", fill="none", stroke=accent)
            for j in range(3):
                primitive(icon, "circle", cx=x+146+j*15, cy=148, r=3, fill=accent, stroke="none")
            primitive(icon, "path", d=f"M {x+180} 213 L {x+209} 237 L {x+262} 188", fill="none", stroke=accent, **{"stroke-width": 7})
    for i, (eid, origin, dest) in enumerate([("specify-to-compose", "abstraction", "composition"), ("compose-to-validate", "composition", "validation")]):
        x = 460 + i*480
        scene["edges"].append({"id": eid, "spec_id": eid, "from": origin, "to": dest, "from_port": "out", "to_port": "in", "type": "data", "points": [[x+4, 308], [x+34, 308]], "marker_end": "arrow"})
    scene["edges"].append({"id": "revise-layout", "spec_id": "revise-layout", "from": "validation", "to": "composition", "from_port": "feedback", "to_port": "feedback", "type": "feedback", "points": [[1200, 514], [1200, 557], [720, 557], [720, 516]], "marker_end": "arrow", "dash": "9 7"})
    label("revision-label", None, "Visual issues? Revise and render again", 965, 601, 24)
    label("illustrative-label", None, "Illustrative figure-making workflow", 20, 601, 24, "start")
    # Persist every illustrative primitive before generating the SVG.
    for item in scene["decorations"]:
        item["primitives"] = primitive_groups.get(item["id"], [])
    scene["panel_primitives"] = {k: v for k, v in primitive_groups.items() if k.startswith("panel-")}
    (out / "scene-graph.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def element(parent, kind, **attrs):
        return ET.SubElement(parent, f"{{{SVG}}}{kind}", {k: str(v) for k, v in attrs.items()})

    root = ET.Element(f"{{{SVG}}}svg", {"viewBox": "0 0 1440 620", "width": "7in", "height": f"{7*620/1440}in", "font-family": "DejaVu Sans", "stroke-width": "2.6", "stroke-linecap": "round", "stroke-linejoin": "round"})
    element(root, "title").text = "Scientific figure generation: abstraction, composition, and validation"
    element(root, "desc").text = "Illustrative workflow with a visual-revision feedback loop. All content uses editable SVG text and native vector primitives."
    defs = element(root, "defs")
    marker = element(defs, "marker", id="arrow", markerWidth=8, markerHeight=8, refX=7, refY=4, orient="auto", markerUnits="userSpaceOnUse")
    element(marker, "path", d="M 0 0 L 8 4 L 0 8 Z", fill=INK, stroke="none")
    element(root, "rect", id="background", x=0, y=0, width=1440, height=620, fill="white", stroke="none")
    groups = {None: root}
    for panel in scene["panels"]:
        group = element(root, "g", id=panel["id"])
        groups[panel["id"]] = group
        x, y, w, h = panel["box"]
        element(group, "rect", x=x, y=y, width=w, height=h, rx=24, fill=panel["fill"], stroke=panel["stroke"])
        for p in scene["panel_primitives"].get(panel["id"], []):
            element(group, p["tag"], **p["attrs"])
    for icon in scene["decorations"]:
        group = element(groups[icon["parent"]], "g", id=icon["id"])
        for p in icon["primitives"]:
            element(group, p["tag"], **p["attrs"])
    for edge in scene["edges"]:
        points = " ".join(f"{x},{y}" for x, y in edge["points"])
        element(root, "polyline", id=edge["id"], points=points, fill="none", stroke=INK, **{"marker-end": f"url(#{edge['marker_end']})", "stroke-dasharray": edge.get("dash", "none")})
    for item in scene["labels"]:
        x, y = item["position"]
        element(groups[item["parent"]], "text", id=item["id"], x=x, y=y, fill=item["fill"], **{"font-size": item["font_size"], "text-anchor": item["anchor"], "font-weight": item["weight"]}).text = item["text"]
    ET.ElementTree(root).write(out / "figure.svg", encoding="utf-8", xml_declaration=True)
    print(out / "figure.svg")


if __name__ == "__main__":
    main()
