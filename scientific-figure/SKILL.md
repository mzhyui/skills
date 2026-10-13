---
name: scientific-figure
description: Create scientific framework figures from methodology, match the layout, design style, fonts, line styles, and icons of a reference SVG/PNG/PDF, or revise an existing SVG/PNG/PDF from written instructions. Use for scientific workflows and model architectures requiring editable SVG and reviewed publication exports; use ordinary plotting tools for data charts.
---

# Scientific Figure

Turn a scientific method into an accurate, legible, editable figure. Work in three stages: **Scientific abstraction → Graphical composition → Render and validate**. Save intermediate artifacts so revisions can change the design without silently changing the science.

## Select the mode

| User intent | Mode | Required guidance |
| --- | --- | --- |
| Draw a framework from Methods, pseudocode, or code | **Create** | The three stages below |
| Use an SVG, PNG, or PDF as a layout/style reference for a similar figure | **Reference-guided creation** | Read [reference matching](references/reference-matching.md), then apply the three stages |
| Change an existing SVG, PNG, or PDF according to literal written requirements | **Revise** | Read [figure revision](references/figure-revision.md); apply the stages to the requested changes |

Infer the mode from the request. “Use A's style for my method” makes A the visual reference; “change these labels in A” makes A the edit target. When both apply, preserve the edit target's content and apply the requested reference styling. Ask only if the file's role or a consequential requested change is ambiguous. A new methodology is not required for a cosmetic edit of an existing figure.

## Establish the brief

Read the supplied methodology and any repository figure conventions. Locate the actual source before drawing. Treat reference images as visual guidance; their operations, equations, and claims do not transfer to the user's method. If a linked reference cannot be viewed, disclose that and work from the supplied description.

Use known constraints; ask only for missing information that changes scientific meaning or the required delivery. For creation with new scientific content, if no method was supplied, ask for it and prepare the reference profile or layout skeleton while waiting. For revision or faithful reconstruction, the existing figure and written requirements can supply the content; verify ambiguous text or scientific changes as needed. Label any requested demonstration as illustrative. Do not invent an algorithm to fill a panel.

For creation without a visual reference, default to a landscape, two-column figure approximately 7 inches wide, white or transparent background, editable SVG plus PDF, and PNG previews. For reference matching, preserve the reference's aspect ratio and visual language unless content or explicit constraints require adaptation. For revision, preserve the target's page/canvas size, background, and established typography unless instructed otherwise; do not silently resize or restyle it to these defaults. Record assumed print sizes as assumptions. Aim for at least 8 pt text at final size; flag conflicts with a requested exact match and make any deviation explicit. A venue's actual requirements override the default. A requested TikZ workflow remains valid; retain its `.tex` source and render it with the manuscript's engine.

Use a new figure-specific output directory and preserve the supplied original. Preserve source manuscript files unless their editing or integration is requested. Load [the artifact contract](references/artifact-contract.md) when writing the specification and scene graph; update existing records or use focused change records for a small revision.

## 1. Scientific abstraction

For a new figure, write `diagram-spec.md` before construction. For revision, document the current relevant content and requested semantic changes in the revision record instead of requiring a new full Methods specification:

- Bind the source: document path, section/equation or code anchor, and a hash where possible. Give user-provided text a saved, stable source ID.
- Extract inputs, operations, intermediate representations, outputs, decisions, and iterations. Give each a stable ID and source anchor. Preserve exact symbols, index ranges, conditions, and training/inference boundaries.
- Describe each arrow's meaning and direction. Distinguish data flow, control flow, gradients, and optional paths. Include a feedback loop only if the method contains one; specify its return point and stopping rule if given.
- Group operations into roughly 3–5 numbered stages when that fits the method. Use another count when scientifically clearer. Mark omissions made for readability and retain the full source meaning in the specification.
- Separate supported facts, graphical choices, and unresolved scientific questions. Missing dimensions, equations, or branch conditions remain unresolved; never manufacture them for symmetry.

Check the extraction against the source. Continue autonomously when meaning is clear. If an unresolved fact changes topology or claims, ask a focused question and keep the affected region visibly provisional; unaffected layout work may proceed. An intermediate draft does not require a routine approval gate.

## 2. Graphical composition

For new or reconstructed figures, write `scene-graph.json` before final SVG generation. It records canvas size, positions, containment, labels, exact notation, semantics, arrow routes, and illustration roles using the artifact contract. Map every scientific node and edge back to the specification; decorative objects are explicitly marked. For a local edit to an existing vector source, retain its geometry/groups and record only changed objects and necessary dependent edits; synchronize an existing scene graph or generator if one is present.

Read [the design and review guide](references/design-and-review.md) for illustrated styling, math, and layout checks. In reference mode, the extracted style profile controls layout, typography, linework, and icons; in revision mode, the user's requested changes and retained source styling control them. Otherwise use a clear reading direction, stage hierarchy, adequate whitespace, and a stable visual grammar. Select colors by scientific role; the user's example palette is an option, not a rule for unrelated modalities. Reinforce colors with labels or shapes.

Generate `figure.svg` with native vector geometry and editable text, semantic group IDs, and named arrow markers. Save the generator when using code; direct SVG authoring is also reproducible source. Implement illustrations as compact vectors where practical. Optional AI-generated bitmap illustrations may help depict physical objects, but keep scientific labels, arrows, equations, and decisions in the vector layer. Identify embedded raster assets in delivery.

For complex math, use locally rendered LaTeX or another reliable math renderer. Keep equation source and its mapping to vector paths; outlined math is visually editable but is no longer editable text. Never simplify notation merely because a renderer struggles with it. Prefer supported text or SVG `tspan` subscripts for simple notation.

The worked [example generator](assets/example-workflow.py) illustrates this three-stage figure-making process, not a research algorithm. Use it only as a style and implementation example; it is not a fixed layout for all methods.

For bundled artwork, dependencies, and portable usage commands, read the [usage guide](README.md) and [archival example index](examples/README.md). Choose only the examples relevant to the current figure. Archived review records describe their original runs; three reconstruction examples lack the original reference PNGs and cannot be rebuilt from this bundle alone.

## 3. Render and validate

For SVG, run the helper using the skill's actual directory and a separate, fresh export directory:

```bash
python /path/to/scientific-figure/scripts/render_check.py figure.svg \
  --out-dir exports --width-in 7 --dpi 300 --min-font-pt 8
```

Set `--width-in` to the actual intended width; the example's 7 inches must not silently resize a revision. The helper requires Python 3 and Inkscape. It accepts an SVG master, including one reconstructed from PNG or imported from PDF; it does not ingest those formats directly. It creates a physically sized editable SVG, PDF, a 300 dpi PNG, a nominal 96 dpi size preview, and `render-report.json`. It checks local references, duplicate IDs, supported font sizes, rendered bounds, and text bounding-box intersections. It does not establish scientific correctness or certify visual quality. Read warnings and the limitations in its report. If Inkscape is absent, use a locally available SVG renderer and PDF exporter, recording differences and omitted checks. Do not claim unperformed checks passed.

Then inspect the rendered image with the available image viewer, both enlarged and at target manuscript width. Inspect the PDF or an image rendered from it as well. Follow the checklist in the design and review guide. Repair errors in the source SVG or generator, synchronize the specification/scene graph when meaning or geometry changes, and rerender. Repeat until observed issues are resolved; if tools or unresolved source questions prevent completion, deliver an explicitly marked draft with the exact limitation.

Write `validation.md` with separate results for:

1. **Scientific fidelity:** source-to-node and source-to-arrow reconciliation, notation, conditions, omissions, outstanding questions.
2. **Automated checks:** exact command, renderer version, source/export hashes, errors and warnings. Rendering success alone is insufficient.
3. **Visual review:** the actual previews inspected, final physical size, readable labels, arrows/loops, clipping, crossings, contrast, and math appearance. Record reviewer and remaining issues; automated checks never fill this section as passed.
4. **Mode-specific review:** reference matching across layout, overall design, fonts, line styles, and icons; or requirement-by-requirement before/after verification and review of unchanged regions for revision.

Deliver the applicable specification/scene graph or focused revision record, SVG, PDF, previews, validation record, and any generator or equation assets needed to reproduce them. Include the style profile and comparison preview for reference matching, or the change record and before/after preview for revision. Link the main figure and editable source in the response, identify the target size, and state material limitations such as font substitutions, reconstructed content, unreviewed math, or raster elements. Do not claim venue compliance without checking that venue's requirements.
