# Federated-unlearning framework — GBHINDER style

The requested `../fu_framework.svg` and `figure.svg` are identical, fully editable SVGs. The original remains in `source/fu_framework.svg`. Canvas: 1280 × 460 (13.333 × 4.792 inches at standard SVG scale).

- `preview.png`: final preview
- `exports/figure.pdf`: vector PDF, embedded Tinos fonts
- `exports/figure.png`: 300 dpi PNG
- `before-after.png`: original/rebuilt comparison
- `reference-comparison.png`: GBHINDER/rebuilt comparison
- `generate_figure.py`: reproducible generator using the preserved text source
- `diagram-spec.md`, `scene-graph.json`, `style-profile.md`, `revision-record.md`, `validation.md`: source mapping and review

Run from the repository root (Python 3, Tinos, and Inkscape required):

```bash
python3 figures/fu-framework-rebuilt/generate_figure.py
python3 skills/scientific-figure/scripts/render_check.py figures/fu-framework-rebuilt/figure.svg --out-dir figures/fu-framework-rebuilt/exports --width-in 13.3333333333 --dpi 300 --overwrite
```

The generator rebuilds the bundle master only; after reviewing a later revision, copy `figure.svg` to `../fu_framework.svg` to update the requested path. Comparisons are review artifacts of this revision. The source figure's text, notation, and scientific topology are retained; perspective model illustrations do not prescribe an architecture.
