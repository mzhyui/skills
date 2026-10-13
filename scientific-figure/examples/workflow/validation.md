# Worked-example validation

Reviewed by Codex on 2026-10-13 (Asia/Shanghai). This is an illustrative figure-making workflow, not a validation of a research algorithm or experimental result.

## Scientific fidelity: passed for the supplied process

Compared the specification and final diagram with `method-source.md`, the saved excerpt of the user's process. The three stages preserve scientific abstraction, graphical composition, and render/validate order. Two forward arrows carry specification and vector-design information. The labeled feedback path represents the source's request to correct visual issues and repeat rendering until the figure works at manuscript size.

No equations, tensor dimensions, scientific screening decisions, or empirical scores were introduced. The source's operations are summarized in short action labels. The output includes editable SVG and PNG as requested, plus PDF as the chosen publication export. Orange/blue/purple identify numbered stages; the specification explicitly distinguishes this from modality colors. Icons are schematic representations of documents, a scene, and a checked preview. No linked reference image was inspected; style follows the user's written description.

## Automated checks: passed within the helper's scope

Final command, from the repository root:

```bash
python3 skills/scientific-figure/scripts/render_check.py examples/workflow/figure.svg \
  --out-dir examples/workflow/exports --width-in 7 --dpi 300 --min-font-pt 8 --overwrite
```

`--overwrite` was used only to regenerate this task's own example exports after a visual repair. The source SVG remained separate from normalized exports.

- Renderer: Inkscape 1.2.2 (b0a8486541, 2022-12-01).
- Result: `mechanical_checks_passed`; no structural, supported-font-size, canvas-overflow, or text-intersection warnings.
- Editable text elements: 17; font sizes at the target width: 8.4 and 9.1 pt.
- SVG target: 7 × 3.013888889 inches. `pdfinfo` reports one page, 504 × 217 pt, matching this size.
- PNG: 2100 × 904 pixels at 300 dpi, rounded to whole pixels. Size preview: 672 × 289 pixels at nominal 96 dpi.
- `pdffonts` reports embedded, subsetted DejaVu Sans regular and bold fonts.
- Source SVG SHA-256: `3abd94b436bb7b30409575bc6c4d8b243f3a20c26c53f13a1f8439080be31e39`. All primary export hashes and actual commands are in `exports/render-report.json`.

Inkscape emitted GTK recent-manager initialization warnings; commands exited successfully and the resulting files were inspected. Those messages are retained in the render report. The report deliberately leaves `scientific_review` and `visual_review` as `not_performed`, since the helper cannot perform them; this document records the subsequent agent review.

Skill metadata validation passed using the bundled `skill-creator/scripts/quick_validate.py`. Eight behavioral tests passed with `python3 -m unittest discover -s tests -v`, covering invalid references and duplicate IDs, external dependencies, physical font scaling, unsupported typography, inline-style precedence, failure reports, preservation of existing outputs/input, and real Inkscape exports with intentionally overlapping/off-page content.

## Visual review: passed for this example and width

Opened and inspected the high-resolution first PNG, then the corrected `exports/figure-size-preview.png`, `exports/pdf-preview.png`, and `exports/grayscale-preview.png`. The PDF preview was rendered with Poppler at a maximum dimension of 1600 pixels. The grayscale preview was converted from the final size preview with Pillow.

The first render revealed that “Source anchors + exact notation” extended past its inner card even though automated checks passed. The generator and scene graph were corrected to “Sources + exact notation”, and exports were regenerated. This preserved the scientific meaning while removing the overflow.

The final previews show readable titles and labels, no observed clipping or text collisions, visible forward arrowheads, and a clear labeled return loop. Numbering, titles, and line patterns retain meaning in grayscale. Native vector shapes and editable text constitute the entire figure; there are no embedded bitmap illustrations. PDF and PNG appearance agree in the inspected previews.

## Limits

This review covers one straightforward example at 7 inches wide, not general certification of generated figures. The helper does not detect text containment within every card, arrow semantics, all possible overlaps, or scientific mistakes. The worked example has no mathematical equations; complex LaTeX rendering, dense research-method layouts, and TikZ export have not been exercised. Venue-specific compliance and physical print inspection were not performed. Recheck readability if the manuscript scales the figure to another width.
