# Reconstruction validation

Reviewed by Codex against `../图片4.png` on 2026-10-13. This checks the supplied illustration, not the underlying GBHINDER algorithm.

## Source fidelity

The three major enclosures, local graph collection, model aggregation, malicious-update/download/upload legend, historical channel attention regularization, CE Loss, Topological Consistency, and adaptive momentum information update are retained. Inspected the current/history weight notation, feature subscripts and adversarial superscripts, δ and π terms, channel operator and ℝ^N, layer indices and figure caption. Arrow directions and the two converging CE comparison heads follow the visible reference. Internal schematic graphs, color bars and vector cartoons are approximate reconstructions; their fine positions and contours are not recovered scientific source data. No paper-level correctness claim is made.

## Automated checks

Command (from repository root):

```bash
python3 skills/scientific-figure/scripts/render_check.py figures/gbhinder-rebuilt/figure.svg --out-dir figures/gbhinder-rebuilt/exports --width-in 14 --dpi 300 --overwrite
```

Renderer: Inkscape 1.2.2. No errors, duplicate IDs, missing references, reported text intersections or out-of-canvas objects. 53 editable text objects, no raster image elements. The remaining warning requests a manual font-size check on rotated `pre-pooling-label`: its 27-unit type at 14 inches / 2065 units is 13.18 pt; rotation does not change scale. All automatically audited text meets the 8 pt threshold at the supplied size. The renderer reported nonfatal GtkRecentManager initialization messages. Machine report intentionally leaves scientific and visual review as not_performed; the human-readable review is recorded here separately. Artifact hashes are in `artifact-hashes.json`.

PDF: one page, 1008 × 417.356 points, corresponding to 14 × 5.797 inches. PNG: 300 dpi. Font substitutions affect editing on systems without the supplied fonts; Tinos is used for body text and STIXGeneral for calligraphic math runs.

## Visual review

Inspected the enlarged PNG, final `exports/pdf-preview.png`, final `exports/figure-size-preview.png`, `reference-comparison.png`, and a grayscale preview before the final block-arrow refinement. Final PDF and size-preview checks show legible labels at the assumed 14-inch width, no observed clipped text or accidental text intersections. PDF agrees with the PNG composition. Superscript collisions and excessive marker sizes found in the first render were repaired; thick flow arrows now use explicit polygons. Dashed panel boundaries, legend, downward cyan updates, upward perturbation arrow, and opposing orange feature-comparison arrows remain visible. Color-bar identities retain the reference's dependence on color; grayscale does not distinguish all feature values.

## Reference match

- Layout: matched in overall aspect ratio, enclosure positions, panel hierarchy, title and legend placement; small coordinates estimated.
- Overall design: matched pastel palette and model perspective; tiny raster shadows omitted.
- Fonts: adapted to Tinos and STIXGeneral; exact original font unknown. Superscripts remain editable tspans.
- Line styles: matched dashed containers, colored arrows and dotted comparisons; arrowhead contours estimated.
- Icons: graph/model/feature geometry reconstructed; devil cartoons and layer-channel internal graph details adapted as vectors.

Use the 14-inch export for review. Reducing the complete dense diagram to 7 inches also halves its physical text size; the result is not certified for a particular manuscript or venue.
