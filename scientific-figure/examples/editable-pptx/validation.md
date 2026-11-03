# Editable PowerPoint example validation

Date: 2026-11-03. This is an illustrative figure-making workflow, not a research
result. The source is `../../assets/example-editable-pptx.py`; this standalone
native-object demonstration is not a pixel-identical conversion of the archived
SVG workflow example. No SVG/PPTX parity claim is made for this sample.

## Native objects and edit test

`pptx_check.py` reopened the generated OOXML package and reported one 7 × 3.4 inch
slide, 9 text boxes, 10 native shapes (including the feedback freeform), 3 groups,
and 11 connectors (9 decorative icon lines plus 2 attached forward arrows).
There are 12 text-bearing objects and zero pictures. No structural errors or
warnings were reported. The raw inventory is `pptx-report.json`.

The native-generation test changed a node label and its horizontal position in a
temporary copy, saved, and reopened the file. Both changes and the two forward
connector target IDs survived; the original bytes were unchanged. This is a
programmatic edit-persistence test using python-pptx 1.0.2, not an interactive
Microsoft PowerPoint test. The feedback route is an editable freeform that needs
manual adjustment when panels move. See `pptx-editability.md`.

## Rendering and visual review

LibreOffice 24.2.7.2 rendered the PPTX to `pptx-render.pdf`; Poppler produced
`pptx-preview.png`. DejaVu Sans and DejaVu Sans Bold are embedded/subset in the
PDF. The generator explicitly clears inherited and theme-reference shadows.
The Java-helper warning did not prevent conversion. Two initial sandboxed
LibreOffice attempts exited without a PDF; an authorized run outside the sandbox
with an isolated temporary profile produced the inspected result.

The assistant inspected the final enlarged PNG and nominal 96 dpi preview at
7 inches wide. The three panels, labels, document icons, two forward arrows,
and dashed feedback route are visible, with no observed clipping or label
collisions. Labels use 8.5–14 pt text. This visual review does not establish
identical rendering or interactive connector rerouting in Microsoft PowerPoint.

## Reproduce

From the skill directory, choose an interpreter with python-pptx and a fresh
output directory:

```bash
figure_pptx_dir=$(mktemp -d /tmp/scientific-figure-pptx.XXXXXX)
python assets/example-editable-pptx.py --out-dir "$figure_pptx_dir"
python scripts/pptx_check.py "$figure_pptx_dir/figure.pptx" --output "$figure_pptx_dir/pptx-report.json"
mkdir -p "$figure_pptx_dir/rendered"
GSETTINGS_BACKEND=memory libreoffice -env:UserInstallation="file://$figure_pptx_dir/lo-profile" --headless --convert-to pdf --outdir "$figure_pptx_dir/rendered" "$figure_pptx_dir/figure.pptx"
pdftoppm -singlefile -scale-to 1800 -png "$figure_pptx_dir/rendered/figure.pdf" "$figure_pptx_dir/pptx-preview"
python -m unittest discover -s tests -p 'test_pptx.py' -v
```

## Artifact hashes

Hashes identify this reviewed build; regenerated ZIP/PDF metadata may differ.

| Artifact | SHA-256 |
| --- | --- |
| `figure.pptx` | `87bc30286da060f32f487a1350395173385b224508b83b4e4a31ecc01f54741e` |
| `pptx-render.pdf` | `a66a01d0924a2446075b558a77cabc97aaf6425049a37365ee9d0844e6ec3fc8` |
| `pptx-preview.png` | `a5e8a9e7954408c34d06edcb0dff0e34d5efad5d79dcd99be6db12a83e2dfbf9` |
| `pptx-size-preview.png` | `640f984b61631ff293ddfc89891ea3df33dd9986c5aad237f006a3a3efc6e5a5` |
