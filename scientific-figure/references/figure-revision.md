# Revise an existing figure from written requirements

Use when the user supplies an SVG, PNG, or PDF and literal instructions such as “replace label X with Y”, “move the legend to the lower right”, “make only feedback arrows dashed”, or “replace this icon while retaining the layout”. Act on explicit requirements without introducing a routine confirmation gate.

## Bind the original and the requested changes

Preserve the supplied file and render a baseline before modifying a working copy. Record its name, SHA-256, page/crop, dimensions, and any known generator/scene graph. For PDF page selection and format inspection, use the intake table in [reference matching](reference-matching.md); load the rest of that guide only if style matching is also requested.

Write a compact `revision-record.md` containing the user's requirements verbatim, then map each to an actionable row:

| Requirement ID | Literal instruction | Target object/region | Before → after | Dependent edits | Verification |
| --- | --- | --- | --- | --- | --- |
| R1 | Replace “Encoder” with “Feature encoder” | SVG `encoder-label`, or identified image region | Exact old/new text | Resize that label's box only if needed for fit | Text readback and rendered fit |
| R2 | Make feedback arrows dashed | Listed feedback edges | Existing stroke → specified dash pattern | Legend sample, if present and used for this meaning | Inspect every feedback edge and its arrowhead |

Use the actual user's instructions in the real record; the rows above are examples. Preserve the user's spelling, capitalization, symbols, punctuation, and specified counts/coordinates. Do not silently copyedit replacement text. If an instruction is descriptive, such as “make the arrow thicker”, choose a proportional change using the existing design and record the chosen value. Ask only when the target is ambiguous or instructions conflict in a way that changes meaning. Continue unambiguous edits while that question is pending.

Record retained invariants relevant to the edit: untouched labels/equations, node count, topology, canvas size, background, palette, line styles, or icon treatment. A global restyle naturally changes many visual properties; a label replacement does not authorize a global redesign. An added/removed scientific node may require explicit edge changes; do not invent their scientific meaning.

## Choose the least disruptive editing route

### Editable SVG

Edit native groups/text/paths/markers/styles in place on a working copy. Resolve inherited styles and transforms before changing coordinates. Scope shared CSS or marker changes to the requested objects; a shared arrow marker can alter unrelated edges. Keep stable IDs and preserve unaffected elements. If a generator is the source of truth, modify it and regenerate; synchronize an existing scene graph. Do not rewrite the whole drawing to make a local change.

An SVG with outlined labels may require replacing only the affected outlined group with editable text or newly rendered math. An SVG containing a raster figure follows the PNG reconstruction route for that content. State what was actually editable.

### PDF

Inspect the selected page/figure and determine whether its content is vector, raster, or mixed. Prefer the original vector source/generator if it is available. Otherwise import the relevant page into a vector editor or convert a working copy to SVG using available tools. Compare the import to the original preview before editing; watch for font substitutions, clipped groups, split glyphs, lost transparency, changed equations, and shifted connectors.

Keep the selected figure's bounds unless the request changes them. Treat imported paths as editable geometry, not automatically recoverable semantic objects. If conversion changes unrelated content, repair the affected regions or use a faithful reconstruction with that limitation disclosed. A scanned PDF follows the PNG route after extracting/rendering the selected region. Export a revised standalone figure by default; replacing a page inside a manuscript PDF is a separate operation only when requested.

### PNG or flattened content

Inspect at native pixel scale and in readable crops. Recover the visible content and layout, retaining uncertain text as unresolved. Prefer an editable reconstruction of the figure (or the affected region within a clearly disclosed mixed-content master). Preserve untouched content's appearance and avoid creating scientific details from blur. Rebuild labels, boxes, arrows, and symbols as separate editable objects when feasible.

For a small raster-only change explicitly requested by the user, a local raster edit is valid. For an editable delivery, a raster background plus editable replacement objects is a **partially editable composite**; identify which regions remain flattened. Do not describe it as a fully editable reconstruction. Covering old labels with opaque patches can damage arrows or textured backgrounds; verify the actual surroundings and repair the underlying region when necessary.

Raster input may lack a trustworthy physical print size. Preserve pixel dimensions/aspect ratio for the baseline comparison and record any assumed publication width separately. Report known font substitutions and reconstruction approximations. Do not claim lossless recovery of original vector structure from pixels.

## Apply, render, and check the literal requirements

Keep the baseline and revised rendering at equal scale. Generate `before-after.png`; optionally create an aligned difference/overlay view for small edits. Register the figures using stable geometry before interpreting pixel differences. Antialiasing, font rendering, and PDF import can change pixels without changing content; inspect unexpected differences instead of treating every pixel as a semantic edit.

For every requirement, record the exact completed change, relevant object IDs or regions, and verification result. Read back replacements from editable text where possible and inspect rendered labels. Review moved connectors, attached arrowheads, nearby labels, and legends for dependent effects. Inspect the whole figure for unintended changes to the retained invariants. Validate scientific changes against the user's supplied content; cosmetic revisions do not require inventing or requesting a full Methods section.

Run the SVG helper on the resulting editable master at the preserved/intended width, then perform the normal scientific and visual checks. The helper cannot verify the user's literal requirements automatically. Update the existing validation record or create one and link it from the revision record.

Deliver the revised figure in the requested format plus the editable master when applicable, matching PDF/PNG exports, `before-after.png`, and `revision-record.md`. For small edits the focused record can replace a new complete specification/scene graph; retain and update existing ones if present. Report each requirement as completed, partial, or blocked, and explain partial editability or unavoidable reconstruction changes. Preserve the supplied original unless the user explicitly requests its replacement.
