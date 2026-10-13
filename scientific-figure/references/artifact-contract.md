# Artifact contract

Use this contract for a full framework figure. For an existing figure's small revision, update the relevant records rather than reconstructing unrelated material. These artifacts support reasoning and traceability; they are not claims of independent scientific verification.

## `diagram-spec.md`

Include:

- **Brief:** audience, intended width/height, format, background, stylistic reference, assumptions.
- **Sources:** stable source IDs, paths or supplied text, hashes when available, exact section/equation/line anchors. Save pasted methodology as `method-source.md` when it is the only source; keep it distinct from interpretation.
- **Stages:** IDs, titles, input/output contracts, and operation membership.
- **Nodes:** ID, stage, kind (input / operation / representation / decision / output), exact label/math, source anchors, scientific meaning. Record dimensions only when supported.
- **Edges:** ID, source and destination IDs/ports, direction, type (data / control / gradient / feedback), label/condition, source anchors. A decision's outgoing edges carry the actual conditions. When the source omits a loop's stopping condition, record that omission instead of inventing convergence.
- **Notation:** each symbol, original equation, definition, rendering form, and source anchor. Do not normalize distinct symbols into one for visual consistency.
- **Abstraction choices:** grouped/omitted details and why they preserve meaning; distinction between illustration and measured evidence.
- **Open questions:** missing facts and whether they affect topology or claims. Mark resolved questions with the evidence that resolved them.

## `scene-graph.json`

Use SVG user coordinates with origin at the top left. Coordinates are explicit so the scene can be implemented in SVG, TikZ, or another vector editor. This is an agent-facing interchange convention, not a universal renderer schema. The supplied export helper accepts SVG and does not validate this JSON.

Example structure (a deliberately partial illustration):

```json
{
  "schema_version": 1,
  "canvas": {"view_box": [0, 0, 1200, 520], "width_in": 7, "background": "white"},
  "typography": {"family": "DejaVu Sans", "min_font_pt": 8},
  "palette": {"input": "#E6F0FA", "operation": "#F1E8FA", "ink": "#203044"},
  "panels": [
    {"id": "stage-1", "title": "1. Representation", "box": [24, 40, 480, 400]}
  ],
  "nodes": [
    {"id": "input-x", "spec_id": "input-x", "panel": "stage-1",
     "kind": "input", "box": [60, 180, 150, 76], "label": "Input x",
     "font_size": 20, "role": "input", "ports": {"out": [210, 218]}},
    {"id": "encode", "spec_id": "encode", "panel": "stage-1",
     "kind": "operation", "box": [290, 180, 170, 76], "label": "Encoder",
     "font_size": 20, "role": "operation", "ports": {"in": [290, 218]}}
  ],
  "edges": [
    {"id": "x-to-encoder", "spec_id": "x-to-encoder", "from": "input-x",
     "to": "encode", "from_port": "out", "to_port": "in", "type": "data",
     "points": [[210, 218], [290, 218]], "label": "", "marker_end": "arrow-data"}
  ],
  "decorations": [],
  "equations": []
}
```

For icons, decorations, and equations, record their ID, parent, bounding box, source asset or drawing primitive, and role. A scientific icon maps to a `spec_id`; a decorative icon states `decorative: true`. Equation entries include exact LaTeX/text, source anchor, and rendering method. Every visible label includes its text, position/box, font size, and alignment; record panel titles, edge labels, badges, and legends as explicitly as node labels. Extra properties are welcome when needed for curves, multilines, or math.

Before rendering, reconcile IDs and counts, ensure edge endpoints exist, inspect containment and routing, and check target font sizes. Do not treat JSON syntax validity as evidence that the scene matches the methodology. For an isotropically scaled SVG:

`font_pt = font_size_in_user_units × 72 × target_width_in / view_box_width`

Thus a 20-unit font in a 1200-unit figure printed at 7 inches is 8.4 pt. Increasing export DPI adds pixels, not physical text size. If the manuscript scales the figure to another width, recheck at that width.

## Delivery bundle

Typical contents:

```text
diagram-spec.md
scene-graph.json
figure.svg
generate_figure.py          # when generated through code
equations/                 # only when separate math assets are used
exports/figure.svg         # normalized physical width, editable text retained
exports/figure.pdf
exports/figure.png
exports/figure-size-preview.png
exports/render-report.json
validation.md
```

Names may follow repository conventions. Keep relative paths portable. Record font families and any fallback/substitution observed; SVG text depends on available fonts in an editor. PDF may embed or subset fonts; verify the exported result. Do not convert all text to paths in the sole editable master. Do not overwrite unrelated exports; use a distinct directory or the helper's deliberate `--overwrite` option for an authorized revision.

## Mode-specific records

For reference-guided creation, also save `style-profile.md` with the reference identity/page/crop, layout/design/font/line/icon observations, evidence and confidence, and implementation choices. Link it from the scene graph using `style_profile`. Save `reference-comparison.png` and record matched, adapted, or unresolved aspects in validation. Follow [reference matching](reference-matching.md).

For revision, save `revision-record.md` with original-file identity/hash, literal user requirements, target objects/regions, exact before/after changes, necessary dependent edits, retained invariants, and per-requirement verification. Save `before-after.png`. A small edit can use this focused record without creating a full new specification or scene graph; synchronize any existing source records and generator. Follow [figure revision](figure-revision.md).
