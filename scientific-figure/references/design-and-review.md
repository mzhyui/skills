# Design and review

## Illustrated scientific style

- Establish one reading direction and a few large rounded stage panels. Keep the output visually identifiable; stage boundaries should express the method's organization.
- Use small scientific abstractions: stacked tokens, a matrix with a few cells, graph nodes and edges, a miniature image stack, or a predictor block. These are schematic illustrations, not invented results or data distributions.
- Apply a consistent outline weight and corner radius. Mild irregularity can make nonsemantic icons look drawn; keep label baselines, arrow endpoints, and mathematical geometry precise. Shadows are optional and should survive print without obscuring boundaries.
- When appropriate, use orange for text, blue for images, purple for screening, and yellow for decisions. For other methods choose colors that represent their actual roles. A stage color and a modality color should not conflict. Reinforce roles with names, shapes, or line patterns.
- Use sans-serif labels, short action phrases, and explicitly numbered stages. Prefer additional height or selective detail removal to shrinking labels. Keep mathematics in a conventional math font. Reserve any informal lettering for optional titles.
- Route arrows between named ports; avoid crossing text, cutting through unrelated boxes, or letting an arrowhead disappear under a panel. Branches and feedback require explicit labels where their meaning could be confused. Use a legend if line styles carry distinct meanings.
- Keep meaningful labels in the vector layer even when an illustration is raster. A raster-only workflow is insufficient when the requested deliverable is editable SVG.

## Scientific review

Review the final SVG against the source, not just against the scene graph (both could share the same mistake):

1. Every operation, scientific icon, and arrow corresponds to a source-supported entity or relationship.
2. Order, dimensions where known, training/inference boundaries, and modalities are consistent. No unlabeled combination implies an unsupported fusion operation.
3. Equations preserve equality/approximation signs, indices, superscripts, subscripts, operator order, and symbols. Check the rendered glyphs as well as the source strings.
4. Decision conditions are present; loop return points and source-provided termination semantics remain correct. A layout loop must not imply algorithmic iteration.
5. The output and any scope limitations are represented faithfully. Illustrative matrices, curves, and scores are not presented as experimental results.

## Render review

Open the PNG in an image viewer; inspect both the high-resolution export and the nominal 96 dpi size preview. The latter approximates on-screen manuscript size; physical display density/zoom can vary, so also verify the PDF page size and intended manuscript scale.

Check:

- Readable stage titles, body labels, subscripts, and legends at the intended width. Check longer multilingual labels and fallback glyphs when applicable.
- No clipping, unintended text overlap, crowding, or confusing arrow crossings. Check arrowheads at both ends of loops. Automated text-box overlap warnings need interpretation; deliberate multiline math may overlap bounding boxes without touching ink.
- Consistent edge weights, panel spacing, alignment, icon style, and color semantics. Check a grayscale view when colors encode meaning; differentiate critical paths by more than hue.
- Adequate contrast on the chosen background and a practical transparent-background appearance. Check on white for publication even if an editor uses a dark canvas.
- PDF and PNG agree, page dimensions match the brief, and raster assets have adequate effective resolution. Check equations in the PDF because its text/font treatment can differ from PNG.

Example PDF inspection with Poppler, when available:

```bash
pdfinfo exports/figure.pdf
pdftoppm -singlefile -scale-to 1600 -png exports/figure.pdf exports/pdf-preview
```

Open the generated `pdf-preview.png`. Rendering a preview does not constitute inspecting it.

## Record outcomes without overstating them

In `validation.md`, identify the specific files and widths inspected, source comparison performed, repairs made, and unresolved issues. Use `passed`, `issues found`, or `not performed` per check. Distinguish mechanical pass, visual judgment, and source fidelity. If a required renderer or image viewer is unavailable, keep the unperformed check explicit and deliver a draft. Reinspect after changing geometry, labels, fonts, output size, or math.
