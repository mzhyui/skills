# Validation — 2026-10-13

## Source fidelity

Reviewed by Codex against the actual `../图片2.png`, then against the equal-scale comparison. The three client cards, departure badge, central server, local-training inset, legend, learning and unlearning panels are reconstructed. The source's learning/unlearning arrow directions, model/update accents, selection labels λ/γ, remaining-client notation, direction vectors, cosine equation and calibrated-update equation are retained. “Gaussion Noise” is transcribed literally. Schematic icon details are approximated. This checks image transcription, not the mathematical validity or implementation of an underlying method.

## Automated checks

Command: `python3 skills/scientific-figure/scripts/render_check.py figures/federated-unlearning-rebuilt/figure.svg --out-dir figures/federated-unlearning-rebuilt/exports --width-in 14 --dpi 300 --min-font-pt 8 --overwrite`.

Inkscape 1.2.2. Final report: `mechanical_checks_passed`, zero errors and zero warnings. The report's scientific/visual review fields remain `not_performed` because that helper does not perform those reviews; human-readable agent review is recorded here. All 64 scene objects, 29 arrows and 35 mathematical objects resolve to SVG IDs. No raster images are embedded. There are 48 editable text objects. Outlined math is outside the helper's font-size audit.

PDF: one page, 1008 × 386.326 pt (14 × approximately 5.366 inches). `pdffonts` confirmed embedded Tinos regular/bold and Noto Serif Ethiopic (fallback vertical-ellipsis glyph). PNG is 4200 pixels wide at 300 dpi. Matplotlib math uses STIX outlines with LaTeX retained in the generator. Hashes are in `manifest.json` and `exports/render-report.json`.

## Visual review

Inspected the first full-resolution PNG, then final `exports/pdf-preview.png`, `exports/figure-size-preview.png`, `reference-comparison.png` and `exports/grayscale-preview.png`. Repaired oversized arrowheads, removed white backgrounds from equation assets, and used display-style fractions to improve correspondence and readability. Final PDF preview agrees with the PNG appearance; no observed clipped labels, equation collisions, or broken glyphs. The original's coincident client-1 update routes are retained.

At the assumed 14-inch size, the minimum ordinary text is approximately 10.36 pt. Equation scripts are smaller; dense notation should be inspected at the actual publication size. A 7-inch reduction is not certified readable. Grayscale retains shapes and labels but loses reliable color separation between learning and unlearning arrows, as in the source; color delivery is preferred for this faithful reconstruction.

## Reference comparison

- Layout: matched — source canvas ratio, panel boundaries and reading order retained.
- Design: matched with approximate colors — white background, pale borders, rounded client boxes and dotted subregions.
- Typography: adapted — Tinos/STIX substitutes; source math weight and metrics differ slightly.
- Line styles: matched with approximate geometry — dotted client outlines, colored exchange arrows, black stage arrows and dashed calibration vectors.
- Icons: adapted — fully vector redraws; database silhouettes, graph networks, shield and server retained; noise hatch strokes approximate the source.

Original PNG and unrelated workspace files were not modified.
