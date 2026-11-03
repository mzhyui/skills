# Editable PowerPoint companion

Read this when the user selects PPTX or PowerPoint editing during the pre-plot
confirmation. Deliver `figure.pptx` with any other selected formats; retain an
editable working source without requiring SVG/PDF as final deliverables.
Preserve the figure aspect ratio; one figure per
slide is the default, not a mandatory 16:9 slide. Generate both representations
from the same specification and geometry, and record any intentional differences.

## What must remain editable

Use native PowerPoint text boxes for labels, native shapes for panels and simple
icons, and native connectors for relationships. Give objects stable semantic
names in the Selection Pane, matching scene-graph IDs. Group parts that should
move together, while retaining separately editable labels and shapes. Keep text
as text, with explicit font family, size, margins, and wrapping settings.

Connect straight/elbow connectors to shapes when appropriate so moving a node can
retain its attachment. Explicitly routed freeform arrows remain editable geometry
but do not automatically follow nodes; identify those routes in the editability
notes. Preserve arrow direction, port meaning, and dashed/solid semantics.

| Content | Preferred PowerPoint representation | Disclose when used |
| --- | --- | --- |
| Labels and simple notation | Text runs; superscript/subscript where supported | Font substitution or layout changes |
| Panels, nodes, decisions | Native shapes | Reconstructed geometry |
| Edges | Attached connectors or editable freeform routes | Routes requiring manual adjustment |
| Simple icons | Grouped native shapes/freeforms | Approximation of source paths |
| Complex logos/artwork | Native freeforms if practical; otherwise a separate SVG or bitmap object | Picture objects are movable/resizable, not native component geometry |
| Equations | Native Office Math when the toolchain supports it; otherwise an isolated vector asset with retained LaTeX | Outlined math is not editable equation text |

A PNG, SVG, or PDF placed as one picture on a slide does not satisfy a request for
an editable diagram. Do not promise an arbitrary SVG-to-PPTX conversion preserves
text, paths, masks, gradients, fonts, or connector behavior. When only a flattened
source exists, reconstruct the requested editable elements and disclose the
remaining picture regions. Ask about a tradeoff only when it materially changes
the requested content or appearance.

## Implementation

Use an available native presentation toolchain; `python-pptx` is one option.
The [runnable example](../assets/example-editable-pptx.py) demonstrates named
native objects, a grouped icon, text frames, attached connectors, and a manually
routed feedback arrow. It is an illustrative layout template, not a generic SVG
converter or a replacement for the user's methodology. Adapt the figure's own
generator to emit PowerPoint objects using its scene graph.

`python-pptx` is optional and is needed only for this example/native generation.
The structural checker uses Python's standard library. Install dependencies into
a suitable environment rather than vendoring them inside the skill.

From the skill directory, with a Python interpreter containing `python-pptx`:

```bash
figure_pptx_dir=$(mktemp -d /tmp/scientific-figure-pptx.XXXXXX)
python assets/example-editable-pptx.py --out-dir "$figure_pptx_dir"
python scripts/pptx_check.py "$figure_pptx_dir/figure.pptx" \
  --output "$figure_pptx_dir/pptx-report.json"
```

The example refuses to replace existing outputs. It also writes
`pptx-editability.md` with the object mapping and editing limitations.

## Verify the actual PPTX

1. Reopen the exported file. Run `pptx_check.py` to inventory native shapes,
   editable text, connectors, pictures, groups, and graphic frames. Inspect
   names, connection targets, label strings, and picture-only slides. The checker
   does not validate font metrics, attachment behavior in the application,
   equation editability, or scientific correctness; counts are not a certificate.
2. Make a temporary copy, edit a label, move a node, save, and reopen it. Verify
   the changes and connector relationships survive. Programmatic readback checks
   object persistence; only an application check establishes actual interaction.
3. Render the PPTX itself using PowerPoint or LibreOffice. For example:

   ```bash
   libreoffice -env:UserInstallation="file://$figure_pptx_dir/lo-profile" \
     --headless --convert-to pdf --outdir "$figure_pptx_dir/rendered" \
     "$figure_pptx_dir/figure.pptx"
   pdftoppm -singlefile -scale-to 1800 -png \
     "$figure_pptx_dir/rendered/figure.pdf" "$figure_pptx_dir/pptx-preview"
   ```

   Create the `rendered` directory first. Keep this PDF separate from the
   publication PDF exported from SVG. Inspect text wrapping, fonts, arrowheads,
   grouping placement, clipping, and visual parity with the SVG. A successful
   SVG preview does not validate the PPTX. Record renderer/version; a LibreOffice
   render is not proof of identical rendering in Microsoft PowerPoint.
4. Include results in `validation.md`, with native-object counts, label/geometry
   reconciliation, actual render reviewed, edit test, and remaining limitations.
   If rendering or application testing is unavailable, state which checks were
   performed and which remain unverified.

## Deliver and maintain

Include `figure.pptx`, `pptx-report.json`, `pptx-preview.png`,
`pptx-editability.md`, and its generator in the figure bundle. The editability
note maps semantic IDs to Selection Pane names and identifies images, outlined
equations, font dependencies, manually routed edges, and approximated geometry.
Link the PPTX directly in the final response.

PowerPoint edits do not automatically update SVG, PDF, or the scene graph. State
which source is authoritative. On a subsequent revision, inspect and preserve
the user's latest PPTX edits before regenerating it; reconcile the formats
deliberately rather than overwriting those edits with an older generator.
