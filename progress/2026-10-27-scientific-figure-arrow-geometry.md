# Correct scientific-figure arrowhead bumps

- Record format: `2`
- Mode: `coding-progress`
- Implementation class: `fresh-implementation`
- Date: `2026-10-27`
- Project: `/home/mzhyui/git/skills`
- Status: `completed`
- Evidence state: `verified`

## Outcome

Corrected arrow shaft/head overlap in the skill and the user's Qwen figure.
Added a standard-library geometry helper, composition/review instructions, an
updated example generator, and five regression tests. All 65 repository tests
passed; fresh Qwen and workflow exports have zero mechanical warnings/errors.
PNG/PDF visual review found clean arrow tapers in inspected samples (V1–V8).

## Task and Scope

E1 is the user's request to remove the shaft-width bump at triangular arrowheads,
with the Qwen3.5-2B SVG supplied as the example. The initial SVG (E2) used round
shafts ending at tip-anchored triangles; changing the cap alone would still
expose shaft corners beside the taper. The confirmed implementation intent was
to correct the geometry, preserve the intended tips, and prevent recurrence.

The skill initially had no reusable arrow geometry helper. Because this adds a
new helper API, the delivery is classified as fresh-implementation even though
its purpose is a defect correction. Seven repository source/resource paths are
in scope. The original figure's generator, scene graph, master and exports were
also synchronized after rendering and reviewing staged copies. Thirteen prior
files were hash-checked and backed up before applying sixteen reviewed files;
that external artifact delivery is verified by V7 and is outside this checkout's
Git accounting. No installed skill copy was changed.

## Implementation

### Plan and Starting Status

Use the supplied SVG to identify the faulty join; encode a safe overlap and
shortened shaft while retaining the intended tip; use this geometry in the
active example; add focused analytic and rendered regression checks (E1–E3).
Archived figure bundles remain byte-preserved (V9).

### Core Functions and Result

| Path | Core function or role | Result |
| --- | --- | --- |
| `scientific-figure/scripts/arrow_geometry.py` | `arrow_geometry`, `add_arrow` | Shorten the shaft inside a solid unstroked head, retain tips/bends, reject invalid dimensions and heads that cannot fit the final segment |
| `scientific-figure/tests/test_arrow_geometry.py` | Five regression tests | Check containment, six directions, multiple widths, inherited styles, dash handling, invalid routes, and rendered taper/overshoot |
| `scientific-figure/assets/example-workflow.py` | Example generator | Apply the helper to semantic and icon arrows; retain intended routes in the scene graph |
| `scientific-figure/SKILL.md` | Composition instructions | Require geometry that keeps the shaft out of the taper |
| `scientific-figure/references/arrow-construction.md` | Formula and authoring guide | Explain marker placement, overlap, tip preservation, single-outline alternatives, and curve limits |
| `scientific-figure/references/design-and-review.md` | Visual review checklist | Inspect PNG and PDF head taper, shoulders, tips, and connections |
| `scientific-figure/README.md` | Usage/dependencies | Document the helper and optional rendered-test dependencies |

For head length $L$, head width $W$, shaft width $w$, choose
$o=\min(w/2,L(1-w/W)/2)$ and trim the shaft by $L-o$. The shaft endpoint
corners lie inside the broad part of the triangle, while the actual tip stays
at its specified port. Use an explicit color, butt shaft cap, and unstroked head.

The helper intentionally rejects heads that reach a bend. During staging, the temporary
Qwen adaptation exposed a 36-unit head on a 35-unit final segment; the
figure generator now explicitly chooses min(3 × stroke, 90% of terminal length).
The corrected delivery changes all 20 arrows (12 semantic, 4 icon, 4 legend),
with all labels, non-arrow primitives, nodes and semantic routes preserved (V7).
Original files are retained in
`/home/mzhyui/git/Signal_and_nn/docs/figures/qwen35-2b-architecture/revisions/2026-10-27-arrow-fix-before/`.
See `arrow-fix-revision.md` in the figure directory for the focused revision record.

## Interface and Behavior Changes

Added the importable `arrow_geometry(points, stroke_width, head_length, head_width)`
and `add_arrow(parent, defs, identifier, points, *, color, stroke_width=3,
head_length=None, head_width=None, dash=None)` helpers. Defaults use three shaft
widths for head length/width. Routes must have finite nondegenerate 2D segments,
and the head must fit strictly within the last segment. Curve trimming and start
markers are outside this helper's API. Existing render CLI/schema is unchanged.

## Validation

### Test Result

65/65 repository tests passed: 14 scientific-figure, 13 installer, 9 math-auditor,
29 record-coding-progress. Python compilation and skill validation passed.
The initial temporary-adaptation failure was resolved before the final V6/V7 checks.

### V1 - pass

```text
python3 -m unittest discover -s scientific-figure/tests -p 'test_*.py' -v
```

14/14 tests pass, including Inkscape/Pillow silhouette checks at four shaft widths and analytic endpoint/containment checks in six directions.

### V2 - pass

```text
python3 -m unittest discover -s tests -p 'test_*.py' && python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py' && python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py'
```

13 installer, 9 math-auditor, and 29 progress tests pass (51 total).

### V3 - pass

```text
python3 -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py scientific-figure/scripts/render_check.py scientific-figure/scripts/arrow_geometry.py scientific-figure/assets/example-workflow.py scientific-figure/examples/*/generate_figure.py
```

All listed Python files compile.

### V4 - pass

```text
python3 /home/mzhyui/.codex/skills/.system/skill-creator/scripts/quick_validate.py scientific-figure
```

Skill is valid.

### V5 - pass

```text
python3 scientific-figure/scripts/render_check.py /tmp/scientific-arrow-review/workflow/figure.svg --out-dir /tmp/scientific-arrow-review/workflow/exports --width-in 7 --dpi 300
```

Updated workflow exports pass with zero mechanical warnings/errors.

### V6 - pass

```text
python3 scientific-figure/scripts/render_check.py /tmp/scientific-arrow-review/qwen35-2b-architecture/figure.svg --out-dir /tmp/scientific-arrow-review/qwen35-2b-architecture/reviewed-exports --width-in 10 --dpi 300
```

Corrected Qwen exports pass with zero mechanical warnings/errors; reviewed bytes subsequently copied into the original directory.

### V7 - pass

```text
python3 /tmp/scientific-arrow-review/verify_delivery.py
```

20 arrows corrected; 12 nodes/routes and all non-arrow objects preserved; delivered/source/export/backup hashes verified.

### V8 - pass

```text
view_image /tmp/scientific-arrow-review/arrow-before-after.png; view_image /tmp/scientific-arrow-review/qwen35-2b-architecture/reviewed-exports/figure-size-preview.png; view_image /tmp/scientific-arrow-review/workflow/exports/pdf-preview.png
```

Codex inspected enlarged original/corrected PNG/PDF arrow crops, the Qwen nominal-size figure, and the workflow PDF preview. Sampled heads have clean tapers with no shaft bumps; view_image is a tool call, not a shell command.

### V9 - pass

```text
git diff --check -- scientific-figure && git status --short -- scientific-figure && git diff --numstat -- scientific-figure/examples
```

Whitespace check passes; only the seven task source/resource paths changed under scientific-figure, and no archived example changed.

## Evidence Ledger

| ID | Class | Locator and supported conclusion |
| --- | --- | --- |
| E1 | user-stated | Current request: correct scientific-figure arrowhead bumps, illustrated by the Qwen3.5-2B SVG |
| E2 | verified | /home/mzhyui/git/Signal_and_nn/docs/figures/qwen35-2b-architecture/revisions/2026-10-27-arrow-fix-before/figure.svg; SHA-256 `02298615f2f27878c49b3d6433c40fd69666998132dce8502737edc2eddc1384` |
| E3 | verified | scientific-figure/scripts/arrow_geometry.py; SHA-256 `08c0162bc90eeafbfc0bb5c6b161e3db15f282cc73acc345625456ce05b35737` |
| V1 | verified | Observed command/tool outcome recorded above: pass |
| V2 | verified | Observed command/tool outcome recorded above: pass |
| V3 | verified | Observed command/tool outcome recorded above: pass |
| V4 | verified | Observed command/tool outcome recorded above: pass |
| V5 | verified | Observed command/tool outcome recorded above: pass |
| V6 | verified | Observed command/tool outcome recorded above: pass |
| V7 | verified | Observed command/tool outcome recorded above: pass |
| V8 | verified | Observed command/tool outcome recorded above: pass |
| V9 | verified | Observed command/tool outcome recorded above: pass |

## Git Custody

Branch: `main`. Baseline and final HEAD:
`3c10718e02d42500b1cb3f0d0ec32c0535921486`. History relation: `same`;
commits since baseline: none. No commit or push was requested or performed.

Explicit implementation scopes and task-owned paths are the seven paths in the
core-functions table. Record: `progress/2026-10-27-scientific-figure-arrow-geometry.md`.
This progress note is task-owned via `--record-path` and
excluded from implementation-diff totals. There are no pre-existing overlaps.

Scoped diff: `files=4; insertions=29; deletions=11; binary_files=0; untracked_files=3`.
Untracked source contents are counted separately from tracked diff lines.

The 18 pre-existing/outside-scope paths are retained:

- `maintain-server-task-status/SKILL.md`
- `maintain-server-task-status/references/autodl-pro-operations.md`
- `maintain-server-task-status/scripts/autodl_api.py`
- `maintain-server-task-status/tests/test_autodl_api.py`
- `progress/2026-10-21-readable-progress-records.md`
- `progress/2026-10-21-update-installed-record-coding-progress.md`
- `progress/2026-10-23-autodl-pro-operation-sop.md`
- `record-coding-progress/SKILL.md`
- `record-coding-progress/agents/openai.yaml`
- `record-coding-progress/claude/agent.md`
- `record-coding-progress/references/coding-progress-v2.md`
- `record-coding-progress/references/coding-progress-v3.md`
- `record-coding-progress/references/lifecycle-v3.md`
- `record-coding-progress/references/readable-records.md`
- `record-coding-progress/references/session-documentation-v2.md`
- `record-coding-progress/references/session-documentation-v3.md`
- `record-coding-progress/scripts/record_tool.py`
- `record-coding-progress/tests/test_record_tool.py`

The scientific-figure task did not edit those files; the broader checks exercised
the visible worktree. The original figure directory is outside this repository;
V7 verifies its file hashes, backup custody, and equality with staged exports.
The temporary evidence manifest is `/tmp/scientific-arrow-progress.json` and is
not a committed artifact.

## Evidence Boundary

Geometry tests and inspected PNG/PDF samples support this arrow correction, not
general SVG correctness or scientific validity of the Qwen architecture. Curves,
start markers, and arbitrary inherited CSS need separately authored geometry or
review. Inkscape emitted GtkRecentManager notices while exports completed;
mechanical reports contain no errors/warnings. The report's automatic scientific
and visual review fields remain `not_performed`; V8 records the separate actual
image inspection. Global installed copies were not modified.

## Next Steps

None for the requested repository fix and supplied figure correction.

## Follow-up: Installed Skill Update

After the initial delivery above, the user explicitly requested updating the
installed skill. Synchronized the seven changed files from
`/home/mzhyui/git/skills/scientific-figure` into
`/home/mzhyui/.codex/skills/scientific-figure`. All 109 non-cache installed files
match the repository by SHA-256; the previous 106 files were preserved and their
backup hashes verified. Backup: `/home/mzhyui/.codex/skill-backups/scientific-figure-20261027T150724Z`.
The prior statements that no installed copy was changed describe the initial
repository-fix delivery; this follow-up records its subsequently authorized update.

Installed-copy verification:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s /home/mzhyui/.codex/skills/scientific-figure/tests -p 'test_*.py' -v
python3 /home/mzhyui/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/mzhyui/.codex/skills/scientific-figure
PYTHONDONTWRITEBYTECODE=1 python3 /home/mzhyui/.codex/skills/scientific-figure/assets/example-workflow.py --out-dir /tmp/scientific-figure-installed-arrow-check
python3 /home/mzhyui/.codex/skills/scientific-figure/scripts/render_check.py /tmp/scientific-figure-installed-arrow-check/figure.svg --out-dir /tmp/scientific-figure-installed-arrow-check/exports --width-in 7 --dpi 300
```

Observed: 13 installed tests passed; the hub-installer integration test was
explicitly skipped because the standalone skill lacks the repository installer.
Skill validation passed. Installed example generation and export passed with zero
mechanical warnings/errors. No additional visual-review claim is made for this
identical-source installation check. The file/hash manifest is
`/tmp/scientific-figure-install-manifest.json`. No commit or push was performed.
