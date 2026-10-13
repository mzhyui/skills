# Reconstruction validation

Reviewed 2026-10-13 by Codex against the supplied PNG. This is a reference reconstruction, not validation of the scientific method depicted.

## Scientific fidelity — visual transcription reviewed
The full reference and rebuilt PNG/PDF were compared. The attacker/data column, malicious SVD decomposition and its two components, benign/local/global parameter diagrams, before/after alignment plots, null-space inset, federated communication strip, four legend entries, and equation references (3)–(6) are retained. W_g^(t−1), W_g^t, x_1, x_n, Δ, ΔP, and Ũ_0 Ũ_0^T = P were checked visually. No numeric measurements were inferred from the schematic bars/regions. The source PNG is unchanged. No manuscript was available to verify mathematical or experimental claims.

## Automated checks — passed with disclosed raster warning
Command, from repository root:

```bash
python3 skills/scientific-figure/scripts/render_check.py figures/batman-rebuilt/figure.svg --out-dir figures/batman-rebuilt/exports --width-in 14 --dpi 300 --min-font-pt 8 --overwrite
pdftoppm -singlefile -scale-to 2011 -png figures/batman-rebuilt/exports/figure.pdf figures/batman-rebuilt/exports/pdf-preview
pdfinfo figures/batman-rebuilt/exports/figure.pdf
pdffonts figures/batman-rebuilt/exports/figure.pdf
```

Renderer: Inkscape 1.2.2; export succeeded. 69 editable text objects. No duplicate-ID, missing-reference, text-overlap, font-size, or canvas-overflow warnings. The sole warning is: “Raster image present; check effective resolution and disclose mixed vector/raster content.” Nine raster crop assets appear in 14 placements. Nominal effective resolution is approximately 144 ppi at the largest original-scale placements; detail is limited by the supplied PNG. All recorded scene object IDs and the four explicitly recorded inter-panel edge endpoint IDs resolve in the SVG. This is not a general scene-graph correctness test.

PDF: one page, 1008 × 511.769 pt (14 × 7.1079 in). All fonts reported by pdffonts are embedded subsets. Primary families are Liberation Serif, Comic Neue, and TeX Gyre Termes; symbol fallbacks include Noto Sans, FreeSerif, and Noto Serif CJK JP. Original font identity is unknown.

## Visual review — reviewed with known reconstruction differences
Inspected `preview.png` (2011 × 1021), `exports/figure-size-preview.png` (nominal 96 dpi), `exports/pdf-preview.png`, `reference-comparison.png` (same-width side-by-side comparison), and `exports/grayscale-preview.png`.

No observed clipping or accidental label intersections. The PDF and PNG agree on layout, labels, arrow directions, and math. Crop-border fragments were removed from the knowledge icons; stacked superscripts/subscripts and gray arrowhead scale were refined after the first render. Intentional overlaps are the header icons crossing panel borders, the Null Space title covering its inset border, and the plane vectors meeting at a point.

The 14-inch width is an assumption, chosen to preserve a readable large-format master. Small native labels are approximately 10 pt; smaller subscripts remain readable in the reviewed previews. At 7-inch manuscript width these labels would be about 5 pt and would require layout revision. Pale annotations and teal/gray connections retain the reference's relatively low contrast. Grayscale preserves labels and topology but reduces color distinctions, particularly between projection/parameter flows; this is a faithful-color reconstruction, not an accessibility redesign.

## Reference matching
| Dimension | Result | Evidence / limitation |
|---|---|---|
| Layout | Matched approximately | Same canvas aspect, panel coordinates, reading order, diagram positions and bottom strip |
| Overall design | Matched approximately | Blue/ivory fields, rounded borders, dashed grouping, illustrated book/photo treatment, purple/gold/blue semantics |
| Fonts | Adapted | Installed substitutes; different handwritten letter shapes and widths; original family unrecoverable |
| Line styles | Matched approximately | Native dashed borders, solid axes, block flow arrows, curved projection arrows, hatch fills; geometry estimated |
| Icons | Retained/adapted | Nine original raster crops; native network nodes/edges and simplified dashed ghost book; repeated book crops reuse the header illustration |

Fine grain textures, gradients, icon shapes, and some arrow geometry differ. This is an editable reconstruction with disclosed raster assets, not a pixel-identical recovery of the unavailable original vector source. See `manifest.json` and `exports/render-report.json` for hashes and mechanical evidence.
