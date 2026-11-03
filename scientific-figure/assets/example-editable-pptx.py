#!/usr/bin/env python3
"""Create an illustrative, natively editable one-slide figure (python-pptx)."""

import argparse
from pathlib import Path


def build_presentation():
    """Build native objects; imports stay local so --help needs no dependency."""
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.dml import MSO_LINE_DASH_STYLE
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml.xmlchemy import OxmlElement
    from pptx.util import Inches, Pt

    presentation = Presentation()
    presentation.slide_width = Inches(7)
    presentation.slide_height = Inches(3.4)
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
    ink = "26364A"

    def no_shadow(shape) -> None:
        shape.shadow.inherit = False
        # Also clear the theme effect reference for LibreOffice compatibility.
        for effect in shape._element.xpath("./p:style/a:effectRef"):
            effect.set("idx", "0")

    def text(shape, value: str, size: float, bold: bool = False,
             color: str = ink) -> None:
        frame = shape.text_frame
        frame.clear()
        frame.word_wrap = False
        frame.margin_left = frame.margin_right = Inches(0.04)
        frame.margin_top = frame.margin_bottom = 0
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        paragraph = frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.space_before = paragraph.space_after = Pt(0)
        run = paragraph.add_run()
        run.text = value
        run.font.name = "DejaVu Sans"
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor.from_string(color)

    def label(name: str, value: str, x: float, y: float, w: float,
              h: float, size: float = 10, bold: bool = False):
        shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        shape.name = name
        text(shape, value, size, bold)
        return shape

    def box(shapes, name: str, x: float, y: float, w: float, h: float,
            fill: str, stroke: str, kind=MSO_SHAPE.ROUNDED_RECTANGLE):
        shape = shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.name = name
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill)
        shape.line.color.rgb = RGBColor.from_string(stroke)
        shape.line.width = Pt(1)
        no_shadow(shape)
        return shape

    def arrowhead(shape) -> None:
        line = shape._element.spPr.get_or_add_ln()
        head = OxmlElement("a:tailEnd")
        head.set("type", "triangle")
        head.set("w", "med")
        head.set("len", "med")
        line.append(head)

    label("figure-title", "From scientific source to editable figure", .2, .12, 6.6, .35, 14, True)
    nodes = []
    stages = [
        ("abstraction", "1  Scientific abstraction", "Read the source", "Diagram specification", "FFF5E9", "B86B2C"),
        ("composition", "2  Graphical composition", "Arrange the figure", "Positioned scene graph", "EEF7FC", "377DA1"),
        ("validation", "3  Render and validate", "Inspect and revise", "SVG / PDF / PPTX", "F5F0FC", "8061A7"),
    ]
    for index, (name, title, action, output, fill, accent) in enumerate(stages):
        x = .2 + 2.3 * index
        box(slide.shapes, f"panel-{name}", x, .65, 2, 1.95, fill, accent)
        label(f"title-{name}", title, x + .05, .74, 1.9, .3, 9.2, True)
        # One grouped, native document icon per stage demonstrates group editing.
        group = slide.shapes.add_group_shape()
        group.name = f"icon-{name}"
        box(group.shapes, f"icon-{name}-page", x + .83, 1.13, .34, .4,
            "FFFFFF", accent, MSO_SHAPE.RECTANGLE)
        for row in range(3):
            line = group.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT, Inches(x + .89), Inches(1.23 + row * .08),
                Inches(x + 1.11), Inches(1.23 + row * .08))
            line.name = f"icon-{name}-line-{row}"
            line.line.color.rgb = RGBColor.from_string(accent)
            line.line.width = Pt(.8)
            no_shadow(line)
        node = box(slide.shapes, f"node-{name}", x + .12, 1.71, 1.76, .38, "FFFFFF", accent)
        text(node, action, 10, True)
        nodes.append(node)
        label(f"output-{name}", output, x + .08, 2.22, 1.84, .25, 9)

    for index in range(2):
        source, target = nodes[index:index + 2]
        edge = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, source.left + source.width,
            source.top + source.height // 2, target.left,
            target.top + target.height // 2)
        edge.name = ("specify-to-compose", "compose-to-validate")[index]
        edge.begin_connect(source, 3)  # right connection site
        edge.end_connect(target, 1)  # left connection site
        edge.line.color.rgb = RGBColor.from_string(ink)
        edge.line.width = Pt(1.2)
        no_shadow(edge)
        arrowhead(edge)

    # A native freeform preserves this explicit route, but does not auto-attach.
    route = slide.shapes.build_freeform(580, 262, scale=Inches(.01))
    route.add_line_segments([(580, 287), (350, 287), (350, 262)], close=False)
    feedback = route.convert_to_shape()
    feedback.name = "revise-layout-manual-route"
    feedback.fill.background()
    feedback.line.color.rgb = RGBColor.from_string("8061A7")
    feedback.line.width = Pt(1)
    no_shadow(feedback)
    feedback.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    arrowhead(feedback)
    label("feedback-label", "Visual issues? Revise and render again", 3.15, 2.98, 3.6, .23, 8.5)
    label("illustrative-label", "Illustrative figure-making workflow", .2, 2.98, 2.8, .23, 8.5)
    slide.notes_slide.notes_text_frame.text = (
        "Illustrative figure-making workflow, not a research result. "
        "Named native text and shapes are editable. The two forward arrows are "
        "attached connectors; the feedback freeform needs manual rerouting after "
        "moving panels. Font: DejaVu Sans. PowerPoint edits do not update SVG/PDF."
    )
    return presentation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.out_dir / "figure.pptx", args.out_dir / "pptx-editability.md"]
    if any(path.exists() for path in paths):
        parser.error("choose a directory without existing example outputs")
    try:
        presentation = build_presentation()
    except ImportError as exc:
        parser.error(f"native generation requires python-pptx: {exc}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    presentation.save(paths[0])
    paths[1].write_text(
        "# PowerPoint editability\n\n"
        "Illustrative workflow, 7 × 3.4 inches. Font: DejaVu Sans.\n\n"
        "| Selection Pane name | Editing behavior |\n"
        "| --- | --- |\n"
        "| `panel-*` | Native rounded rectangles; resize/recolor |\n"
        "| `title-*`, `output-*`, `*-label`, `figure-title` | Native editable text |\n"
        "| `node-*` | Native shapes with editable text |\n"
        "| `icon-*` | Groups of native rectangles and lines; ungroup to edit parts |\n"
        "| `specify-to-compose`, `compose-to-validate` | Connectors attached to nodes |\n"
        "| `revise-layout-manual-route` | Native freeform; manually reroute after moving panels |\n\n"
        "No pictures or outlined text are used. Programmatic attachment metadata "
        "does not establish interactive behavior in every presentation editor.\n\n"
        "This generator is the initial source. Preserve subsequent manual PPTX "
        "edits before regeneration; SVG/PDF companions are not updated automatically.\n",
        encoding="utf-8",
    )
    print(paths[0])


if __name__ == "__main__":
    main()
