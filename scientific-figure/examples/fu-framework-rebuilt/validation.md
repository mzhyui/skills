# Validation — 2026-10-13

Reviewer: Codex. Scope: faithful visual restyling of the supplied SVG; this is not a review of the underlying algorithm or diagnostic validity.

## Source fidelity

Passed: parsed readback confirms all 67 text IDs and exact Unicode text strings, including tspan content; all 21 directed connector IDs remain. The 1280 × 460 canvas is preserved. Reviewed each arrow against the source: four local training paths through randomization and the optional shuffler, shuffler to history, withdrawal through recomputation/replay/recovery, two independent evaluation rows, and diagnostic yes/no branches. No new scientific directed connector was added. The source does not define the acceptance criteria; they remain unspecified.

## Automated checks

```bash
python3 figures/fu-framework-rebuilt/generate_figure.py
python3 skills/scientific-figure/scripts/render_check.py figures/fu-framework-rebuilt/figure.svg --out-dir figures/fu-framework-rebuilt/exports --width-in 13.3333333333 --dpi 300 --min-font-pt 8 --overwrite
pdftoppm -singlefile -scale-to 1600 -png figures/fu-framework-rebuilt/exports/figure.pdf figures/fu-framework-rebuilt/exports/pdf-preview
```

Inkscape 1.2.2: `mechanical_checks_passed`, zero errors and zero warnings. No duplicate IDs, missing references, text intersections, or out-of-canvas objects reported. 67 editable text objects, zero raster image elements. Smallest audited script is 8.25 pt at the preserved 13.333-inch width; body captions start at 9 pt. Nonfatal GtkRecentManager messages appeared in renderer stderr. The machine report leaves scientific/visual reviews `not_performed` by design; the actual manual review is documented separately here.

PDF: one page, 960 × 345 points (13.333 × 4.792 inches). `pdffonts` confirms embedded/subset Tinos regular, bold, and bold italic, with Unicode maps. PNG exported at 300 dpi. Artifact hashes are recorded in `artifact-hashes.json`.

## Visual review

Inspected enlarged PNG/PDF preview, final nominal 96 dpi size preview, before/after comparison, and reference comparison. Inspected grayscale before the final branch-label-only adjustment; the final adjustment moves yes/no text away from arrows. The final PDF and size preview show readable math/scripts, clear arrowheads, no observed clipped labels, and no branch arrows crossing text. Refined two initial text collisions and the diagnostic diamond. The final outputs agree in composition. All meaningful labels and icons are editable vectors; Tinos must be available when editing the SVG to preserve typography.

## Reference matching

- Layout: adapted. Preserve the target's three columns and aspect ratio; reuse dashed enclosure hierarchy and compact operations.
- Overall design: matched visual vocabulary: white ground, cyan bands, lavender/neutral operations, pastel perspective models.
- Fonts: matched the actual rebuilt reference's Tinos family and bold italic headings. No inferred identity claim about the original raster's font.
- Line styles: matched dark dashed grouping and colored arrow family; flow colors adapted to source semantics.
- Icons: adapted GBHINDER model slabs and the neighboring figure's storage/sample conventions; no unrelated method icons or claims transferred.

This delivery retains the source size. Scaling the whole figure to 7 inches would shrink the smallest type to about 4.3 pt; a 7-inch manuscript version would require a separate layout revision.
