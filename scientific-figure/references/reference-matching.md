# Reference-guided creation

Use when the user provides a target SVG, PNG, or PDF and asks for a similar figure using its layout, design style, font, line style, or icons. The input supplies the visual reference; the user's method supplies scientific content. Faithful reconstruction of the same figure is also valid when requested.

## Inspect the actual reference

Record file name, SHA-256, format, canvas dimensions/aspect ratio, and selected page or crop in `style-profile.md`. Open a rendered preview before describing the style. For a multipage PDF, use the figure/page identified by the user; inspect thumbnails to find a unique candidate, and ask only if selection remains ambiguous. Preserve the full figure including its labels and legend when making a crop.

Inspect recoverable structure as well as pixels:

| Input | Inspect | Recovery limits |
| --- | --- | --- |
| SVG | `viewBox`, physical dimensions, groups, transforms, CSS/inherited styles, text/tspan attributes, strokes, markers, paths, symbols/use references, embedded images; also render it | An SVG can contain flattened images or outlined text; the extension alone does not establish editability |
| PNG | Pixel size, transparency, available DPI metadata, overall preview and crops of labels/arrows/icons | Positions and styles can be measured visually, but exact font identity and original vector objects are usually unrecoverable |
| PDF | Page size, selected figure bounding box, embedded font names, text extraction, images, and vector content; render the page/figure | A PDF can be vector, scanned, or mixed. Extracted text order and imported vectors may differ from the visible figure |

Use available tools such as an XML parser for SVG, Pillow for PNG, and `pdfinfo`, `pdffonts`, `pdftotext`, `pdfimages -list`, and `pdftoppm` for PDF. These are options, not mandatory dependencies. Example PDF preview:

```bash
pdfinfo reference.pdf
pdffonts reference.pdf
pdftoppm -f 2 -l 2 -singlefile -r 180 -png reference.pdf reference-page-2
```

Render a copied SVG with Inkscape or an available SVG renderer. For style inspection, retain its original aspect ratio; only normalize physical size for a known publication target. If a dependency or font is missing, record the observed rendering difference. Never claim an unseen file has been matched.

## Extract a concrete style profile

For each property, record the **observation/value**, **evidence location**, **confidence** (`extracted`, `estimated`, or `unknown`), and **implementation choice**. Include all five requested dimensions:

1. **Layout:** aspect ratio, reading order, rows/columns, stage proportions, alignment, gutters, padding, grouping, title/legend placement, arrow routing corridors, and distribution of whitespace. Use coordinates normalized to the selected figure bounds, so a layout can transfer across resolutions.
2. **Overall design:** palette and its semantic roles, background, panel fills, corner radii, outline treatment, shadows, texture, and illustration density. Distinguish a deliberate hand-drawn appearance from raster compression or antialiasing.
3. **Fonts:** families when identifiable, fallback families, font sizes and their hierarchy, weight, slant, line height, alignment, math style, and script support. SVG/PDF metadata can identify a font; appearance alone supports an estimate. Check availability locally, e.g. `fc-match`, and disclose substitutions and their effect on wrapping. Do not promise exact font matching from pixels.
4. **Line styles:** thickness relative to panel/text size, solid/dashed/dotted patterns, dash spacing, line caps/joins, arrowhead geometry/scale, edge curvature, connector ports, and distinctions between data/control/feedback paths.
5. **Icons:** inventory, scientific meaning, silhouette, level of detail, perspective, stroke/fill treatment, palette, size relative to labels, and whether the source is native vector or bitmap. Prefer reusable vector symbols/paths or faithfully redrawn vector icons. New concepts need new icons in the same visual grammar; do not transplant an icon with a different scientific meaning.

Record the user's priorities, such as “keep the four-column layout exactly” or “match icons and linework but use my journal's font”. User requirements override the reference and generic styling defaults. If no priority is given, aim to match all five dimensions and record necessary adaptations. A generic pastel flowchart is not sufficient when a reference's distinguishing features are available.

## Map the new content to the reference

Write the source-grounded diagram specification and map its entities into the observed layout. Carry reusable style tokens into `scene-graph.json`, with a `style_profile` path and the reference's file/page identity. Exact coordinates may change to fit new labels or a different number of stages; retain hierarchy, proportions, spacing logic, and icon treatment where possible.

For a style-only reference, do not transfer scientific operations, labels, equations, or causal links. For faithful reconstruction, use the visible figure as the content source, check text against higher-quality/vector sources where available, and mark unreadable labels unresolved. OCR is a draft transcript and requires visual checking, especially for minus signs, Greek letters, subscripts, and arrows.

Retain editable text and native shapes in the new master. Embedding the reference PNG as a single image inside an SVG is a reference layer, not a reconstructed editable figure. If an icon remains raster, identify it and its effective resolution; keep surrounding labels and connections editable.

## Compare and refine

Render the new figure and build a side-by-side `reference-comparison.png` with both figures shown at the same displayed width and aspect ratios preserved. Inspect label, arrowhead, and icon crops at a larger scale when they carry the distinctive style. Do not distort either image to make their bounding boxes match.

In `validation.md`, review each of the five dimensions separately as `matched`, `adapted`, or `unresolved`, with specific evidence and reasons. Recheck the scientific content independently. No single image-similarity score establishes style or scientific correctness; the helper's checks do not assess reference similarity.

Revise observed mismatches and rerender until the requested similarity and publication readability are met, or clearly identify the missing font, unreadable detail, or other limitation. Deliver `style-profile.md`, the comparison preview, and the ordinary figure bundle. State which reference characteristics were retained and which were deliberately adapted.
