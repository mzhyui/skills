# Scientific Figure

A self-contained Codex and Claude Code skill for creating scientific framework figures, matching reference artwork, and revising existing figures. Start with [SKILL.md](SKILL.md). Data charts should use ordinary plotting tools.

## Use and install

From this hub, ask your agent to read `scientific-figure/SKILL.md` and apply it to your Methods section, reference SVG/PNG/PDF, or written revision requirements. After installation, invoke `$scientific-figure` in Codex or `/scientific-figure` in Claude Code.

Install this directory with Codex's skill installer, or use the hub's Claude installer from the repository root:

```bash
python3 scripts/install_skill.py ./scientific-figure
```

The Claude installer includes the examples and resources and installs the companion agent. No global installation occurs merely by adding this directory to the hub.

## Modes and evidence

- **Create:** extract source-grounded entities, notation, and arrows into a specification, compose editable vector geometry with a scene graph, then render and review.
- **Reference-guided creation:** match layout, typography, line styles, and icons from an SVG, PNG, or PDF, recording recovered values versus estimates in a style profile and reference comparison.
- **Revise:** map written requirements to figure objects, preserve unaffected content, and deliver a revision record and before/after comparison. Flattened inputs may require reconstruction with disclosed limits.

For example: “Use page 2 of `reference.pdf` as the design reference for my Methods section. Deliver editable SVG and PDF with a reference comparison.” Or: “Revise `framework.svg`: rename Encoder to Feature encoder and make only feedback arrows dashed.”

The renderer accepts an SVG master, including one reconstructed from PNG or imported from PDF. Intake, style matching, and revision are agent workflows, not automatic CLI conversion. Rendering checks, visual review, and scientific fidelity remain separate; an export success is not scientific acceptance.

## Dependencies

The helper and workflow generator use Python 3's standard library. Rendering requires Inkscape. Poppler (`pdftoppm`, `pdfinfo`, `pdffonts`) supports PDF preview and inspection. Use fonts specified by the selected example or record substitutions. No image-generation API is required.

The FU-framework example uses Tinos for its intended appearance. The archived federated-unlearning generator additionally uses Matplotlib; Batman uses Pillow. Those two generators and GBHINDER require missing original reference PNGs; see the [example index](examples/README.md).

## Generate and render safely

These commands run from the skill directory, whether in this hub or installed elsewhere. Choose a fresh temporary directory for each run:

```bash
figure_demo_dir=$(mktemp -d /tmp/scientific-figure-demo.XXXXXX)
python3 assets/example-workflow.py --out-dir "$figure_demo_dir/workflow"
python3 scripts/render_check.py "$figure_demo_dir/workflow/figure.svg" \
  --out-dir "$figure_demo_dir/workflow/exports" --width-in 7 --dpi 300
pdftoppm -singlefile -scale-to 1600 -png \
  "$figure_demo_dir/workflow/exports/figure.pdf" "$figure_demo_dir/workflow/pdf-preview"
```

For the self-contained FU-framework rebuild, copy the archive before running its generator, which writes beside itself:

```bash
figure_rebuild_dir=$(mktemp -d /tmp/scientific-figure-rebuild.XXXXXX)
cp -R examples/fu-framework-rebuilt "$figure_rebuild_dir/fu-framework-rebuilt"
python3 "$figure_rebuild_dir/fu-framework-rebuilt/generate_figure.py"
python3 scripts/render_check.py "$figure_rebuild_dir/fu-framework-rebuilt/figure.svg" \
  --out-dir "$figure_rebuild_dir/fresh-exports" --width-in 13.3333333333 --dpi 300
```

The helper creates a physically sized editable SVG, PDF, high-resolution PNG, size preview, and render report. It refuses to overwrite named exports without `--overwrite` and preserves the input SVG. It reports mechanical limitations and leaves scientific/visual review as `not_performed`; inspect PNG and PDF previews and record those reviews separately. Use the actual intended figure width rather than silently applying the workflow example's 7 inches to another figure.

## Examples and tests

The [five archived bundles](examples/README.md) include editable figures, exports, specifications, scene graphs, comparisons, review records, and generators where available. Keep the archives unchanged and perform experiments in copies. The workflow depicts figure creation itself; the reconstructed research diagrams do not validate the methods they depict.

From this directory:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The real-export test needs Inkscape and skips explicitly when it is absent. The remaining tests exercise input validation, diagnostic boundaries, physical font scaling, and preservation of existing files.
