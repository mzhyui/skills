# Batman figure reconstruction

- `figure.svg`: self-contained editable master, 2011 × 1021 viewBox, assumed 14-inch width.
- `exports/figure.pdf`: PDF with embedded fonts.
- `exports/figure.png`: 300 dpi PNG (4200 pixels wide).
- `preview.png`: convenient original-resolution preview.
- `reference-comparison.png`: original/rebuilt side-by-side.
- `generate_figure.py`: editable generator (Python 3 + Pillow).
- `assets/`: nine cropped source-image details; all diagrams and surrounding text are vector.
- `diagram-spec.md`, `style-profile.md`, `scene-graph.json`, `validation.md`, `manifest.json`: provenance, geometry, reconstruction limits and checks.

Rebuild from the repository root (requires the original `figures/图片.png`, Python with Pillow, and Inkscape):

```bash
python3 figures/batman-rebuilt/generate_figure.py
python3 skills/scientific-figure/scripts/render_check.py figures/batman-rebuilt/figure.svg --out-dir figures/batman-rebuilt/exports --width-in 14 --dpi 300 --min-font-pt 8 --overwrite
```

The generator refreshes the master, crops, spec, profile and scene graph; the helper refreshes primary exports and its report. Comparison/review records reflect this delivery and need review after subsequent edits. Fonts: Liberation Serif, Comic Neue, TeX Gyre Termes. The SVG includes its raster assets, so it can be moved independently; the PDF embeds its fonts. The original image is untouched.
