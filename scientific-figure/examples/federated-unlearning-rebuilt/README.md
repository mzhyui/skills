# Federated unlearning figure reconstruction

Rebuilt from `../图片2.png`, preserving its aspect ratio, layout, labels and equations.

- `figure.svg`: editable vector master, 2043 × 783 viewBox; assumed width 14 inches.
- `exports/figure.pdf`: vector PDF with embedded text fonts.
- `exports/figure.png`: 300 dpi PNG, 4200 pixels wide.
- `preview.png`: original-resolution preview.
- `reference-comparison.png`: reference and reconstruction at equal scale.
- `generate_figure.py`: vector generator and editable LaTeX equation strings.
- `diagram-spec.md`, `scene-graph.json`, `style-profile.md`, `validation.md`, `manifest.json`: source, geometry and review records.

All diagrams are native vectors; 48 ordinary text objects remain text. The 35 mathematical objects use outlined STIX glyphs, editable through their LaTeX strings in the generator. Tinos approximates the reference serif font. The source spelling “Gaussion Noise” is preserved. This is a reconstruction, not an exact pixel match.

Run from the repository root with Python 3, Matplotlib and Inkscape installed:

```bash
python3 figures/federated-unlearning-rebuilt/generate_figure.py
python3 skills/scientific-figure/scripts/render_check.py figures/federated-unlearning-rebuilt/figure.svg --out-dir figures/federated-unlearning-rebuilt/exports --width-in 14 --dpi 300 --min-font-pt 8 --overwrite
pdftoppm -singlefile -scale-to 2043 -png figures/federated-unlearning-rebuilt/exports/figure.pdf figures/federated-unlearning-rebuilt/exports/pdf-preview
```

Comparison images, hashes and visual-review notes describe this delivery and must be refreshed following changes. The generator regenerates the specification, style profile, scene graph and SVG. Original input is preserved.
