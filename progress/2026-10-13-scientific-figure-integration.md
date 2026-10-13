# Scientific Figure integration

- Record format: `3`
- Record ID: `RCP-20261013T043933Z-09556860`
- Mode: `coding-progress`
- Task type: `migration`
- Task slug: `scientific-figure-integration`
- Date: `2026-10-13`
- Project: `/home/mzhyui/git/skills`
- Priority: `unspecified`
- Owner: `Unassigned`
- Components: `None`
- Labels: `None`
- Status category: `done`
- Status: `done`
- Resolution: `completed`
- Created at: `2026-10-13T04:39:33Z`
- Started at: `unavailable`
- Updated at: `2026-10-13T05:01:26Z`
- Completed at: `2026-10-13T05:01:26Z`
- Due date: `Not applicable`
- Evidence state: `verified`
- Validation state: `pass`
- Implementation class: `fresh-implementation`

## Outcome

Integrated a self-contained scientific-figure skill for Codex and Claude Code, including all five archived example bundles. All 58 unit tests passed; two self-contained examples generated and rendered successfully. Three missing-reference rebuilds remain intentionally archival (V10). The closeout rerun passed all 58 tests and verified 93 archival files and 30 active links (V11-V13). The staged whitespace gate has two documented archive exceptions (V14).

## Task and Scope

The user approved integrating the plot project into ./scientific-figure, including examples, and selected archival preservation for missing-input generators (E1). The original integration left the source project unchanged and performed no global installation, commit, or push. The subsequent closeout request (E5) authorizes a local commit of all visible changes, including the pre-existing README TODO.

## Lifecycle

Current blocker: None

| ID | At | Action | From | To | Actor | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | 2026-10-13T04:39:33Z | created | none | in-progress | record-tool | record created |
| L2 | 2026-10-13T04:46:29Z | transition | in-progress | done | codex | Integrated the scientific-figure skill and all archival examples; validation and isolated runnable smoke checks passed. |
| L3 | 2026-10-13T04:47:09Z | resume | done | in-progress | codex | Finalize exact validation commands and visual inspection evidence in the handoff. |
| L4 | 2026-10-13T04:47:09Z | transition | in-progress | done | codex | Integration, archival preservation, installation, and bounded rendering validation complete. |

| L5 | 2026-10-13T05:01:26Z | resume | done | in-progress | codex | User requested closeout and local commit of all current changes, including the pre-existing README TODO. |
| L6 | 2026-10-13T05:01:26Z | transition | in-progress | done | codex | Full visible snapshot validated for the requested local commit; archival whitespace exceptions recorded. |

Relationships: None

## Implementation

### Plan and Starting Status

The approved plan imported an existing skill, renderer, references, workflow generator, renderer tests, and five examples. The hub previously lacked scientific-figure. Inspection found three absent PNG references and an existing README TODO. The evidence manifest was started after initial copying; its baseline worktree includes early task edits, so recorded overlap is not evidence that these files predated the task.

### Core Functions and Result

| Path | Result |
| --- | --- |
| scientific-figure/SKILL.md | Existing modes preserved; linked new portable usage guide and archive index. |
| scientific-figure/agents/openai.yaml | Original Codex metadata and implicit discovery behavior preserved. |
| scientific-figure/claude/agent.md | Added Claude skill agent following hub conventions. |
| scientific-figure/scripts/render_check.py | Renderer imported without behavior changes. |
| scientific-figure/tests | Relocated eight renderer tests and added actual installation resource-preservation regression. |
| scientific-figure/examples | All 93 source files preserved byte-for-byte; added a separate index. |
| AGENTS.md and README.md | Added skill entry, test commands, and documentation links. |

## Interface and Behavior Changes

New independently installable scientific-figure package and Claude agent. Renderer CLI, artifact formats, and all archived generators are unchanged. Current documentation distinguishes historical paths from executable commands and missing originals from reproducible inputs.

## Validation

### Test Result

Aggregate: `pass`. 58 unit tests passed (9 scientific-figure, 13 installer, 9 math auditor, 27 record tool). Workflow and FU-framework smoke renders passed mechanical checks. Integration preview inspection was bounded to the three listed previews; no new scientific validation is claimed.

### V1 - pass

```text
python3 -m unittest discover -s scientific-figure/tests -p 'test_*.py' -v
```

9 scientific-figure integration and renderer tests passed

### V2 - pass

```text
python3 -m unittest discover -s tests -p 'test_*.py' && python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py' && python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py'
```

13 installer, 9 math-auditor, and 27 record-progress tests passed

### V3 - pass

```text
python3 /home/mzhyui/.codex/skills/.system/skill-creator/scripts/quick_validate.py scientific-figure && python3 -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py scientific-figure/scripts/render_check.py scientific-figure/assets/example-workflow.py scientific-figure/examples/*/generate_figure.py && git diff --check
```

Skill metadata validation, Python compilation, and whitespace checks passed

### V4 - pass

```text
python3 /tmp/verify-scientific-figure-integration.py
```

All 93 source example files matched destination hashes with no missing or changed files

### V5 - pass

```text
python3 scientific-figure/assets/example-workflow.py --out-dir /tmp/scientific-figure-demo-check && python3 scientific-figure/scripts/render_check.py /tmp/scientific-figure-demo-check/figure.svg --out-dir /tmp/scientific-figure-demo-check/exports --width-in 7 --dpi 300
```

Workflow example generated and rendered with mechanical_checks_passed; scientific and visual review remained not_performed

### V6 - pass

```text
python3 /tmp/scientific-figure-fu-check/fu-framework-rebuilt/generate_figure.py && python3 scientific-figure/scripts/render_check.py /tmp/scientific-figure-fu-check/fu-framework-rebuilt/figure.svg --out-dir /tmp/scientific-figure-fu-check/exports --width-in 13.3333333333 --dpi 300
```

FU-framework generator produced 67 labels and 21 arrows; render check returned mechanical_checks_passed

### V7 - pass

```text
python3 -m unittest discover -s scientific-figure/tests -p 'test_*.py' -v
```

Installed skill resources and extracted Claude agent; excluded agents and claude source directories from skill payload

### V8 - pass

```text
python3 /tmp/verify-scientific-figure-integration.py
```

32 active documentation links resolved; archival documents intentionally excluded

### V9 - pass

```text
view_image: /tmp/scientific-figure-demo-check/exports/figure-size-preview.png; /tmp/scientific-figure-demo-check/pdf-preview.png; /tmp/scientific-figure-fu-check/pdf-preview.png
```

Codex inspected the three previews: readable labels, visible arrows, and no observed clipping. This is a bounded rendering smoke review, not scientific validation.

### V10 - not-run

```text
Archived Batman, federated-unlearning, and GBHINDER generator rebuilds
```

Original reference PNGs are missing; preserved archival generators were intentionally not rerun, as selected by the user.

The temporary verification script compared SHA-256 values for every original archive file against its destination and resolved 32 relative links in active documentation; archive-internal historical links were excluded. Smoke generators ran in temporary directories; their reports retain scientific_review and visual_review as not_performed because those fields are machine-owned. PDF previews were rendered with pdftoppm at maximum dimension 1600 pixels before separate inspection.

### V11 - pass

```text
python3 -m unittest discover -s tests -p 'test_*.py' && python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py' && python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py' && python3 -m unittest discover -s scientific-figure/tests -p 'test_*.py'
```

All 58 tests passed in the closeout run: 13 installer, 9 math-auditor, 27 record-progress, 9 scientific-figure; no skips.

### V12 - pass

```text
python3 -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py scientific-figure/scripts/render_check.py scientific-figure/assets/example-workflow.py scientific-figure/examples/*/generate_figure.py && git diff --check && python3 /home/mzhyui/.codex/skills/.system/skill-creator/scripts/quick_validate.py scientific-figure
```

Python compilation, tracked-diff whitespace check, and skill metadata validation passed at closeout.

### V13 - pass

```text
python3 /tmp/verify-scientific-figure-integration.py
```

All 93 archival files match source hashes; 30 active documentation links resolve. This supersedes the earlier reported count of 32 in V8.

### V14 - pass

```text
git diff --cached --check -- . ':(exclude)scientific-figure/examples/federated-unlearning-rebuilt/figure.svg' ':(exclude)scientific-figure/examples/federated-unlearning-rebuilt/exports/figure.svg'
```

Staged whitespace gate passed with two explicit archive exceptions. The unfiltered git diff --cached --check exited 2 with 70 trailing-whitespace lines across those two SVGs. V13 verifies their byte-for-byte source equality; preserve them under the archival contract.

## Evidence Ledger

| ID | Classification | Source or observation |
| --- | --- | --- |
| E1 | user-stated | User-approved implementation plan in current conversation |
| E2 | verified | /home/mzhyui/git/plot/skills/scientific-figure |
| E3 | verified | /home/mzhyui/git/plot/examples |
| E4 | verified | AGENTS.md and existing hub README.md |
| V1 | verified | 9 scientific-figure integration and renderer tests passed |
| V2 | verified | 13 installer, 9 math-auditor, and 27 record-progress tests passed |
| V3 | verified | Skill metadata validation, Python compilation, and whitespace checks passed |
| V4 | verified | All 93 source example files matched destination hashes with no missing or changed files |
| V5 | verified | Workflow example generated and rendered with mechanical_checks_passed; scientific and visual review remained not_performed |
| V6 | verified | FU-framework generator produced 67 labels and 21 arrows; render check returned mechanical_checks_passed |
| V7 | verified | Installed skill resources and extracted Claude agent; excluded agents and claude source directories from skill payload |
| V8 | verified | 32 active documentation links resolved; archival documents intentionally excluded |
| V9 | verified | Codex inspected the three previews: readable labels, visible arrows, and no observed clipping. This is a bounded rendering smoke review, not scientific validation. |
| V10 | verified | Original reference PNGs are missing; preserved archival generators were intentionally not rerun, as selected by the user. |

| E5 | user-stated | Current user request: conclude all current changes and commit; includes existing README TODO and entire visible worktree |
| V11 | verified | All 58 tests passed in the closeout run: 13 installer, 9 math-auditor, 27 record-progress, 9 scientific-figure; no skips. |
| V12 | verified | Python compilation, tracked-diff whitespace check, and skill metadata validation passed at closeout. |
| V13 | verified | All 93 archival files match source hashes; 30 active documentation links resolve. This supersedes the earlier reported count of 32 in V8. |
| V14 | verified | Staged whitespace gate passed with two explicit archive exceptions. The unfiltered git diff --cached --check exited 2 with 70 trailing-whitespace lines across those two SVGs. V13 verifies their byte-for-byte source equality; preserve them under the archival contract. |

## Git Custody

- Branch: `main`
- Baseline HEAD: `345713f98a0a80e7910485bc10c8de3dc3ca2cba`
- Final HEAD: `345713f98a0a80e7910485bc10c8de3dc3ca2cba`
- History relation: `same`
- Commits since baseline at pre-commit capture: None. This note accompanies the requested local commit; its hash is available from Git history. No push is authorized or performed.
- Task scopes: AGENTS.md, README.md, scientific-figure
- Record path: progress/2026-10-13-scientific-figure-integration.md
- Original integration pre-task observation: only README.md was dirty, containing an unrelated TODO; that text remains unchanged. The all-current-changes closeout includes it explicitly (E5).
- The manifest was captured late: its preexisting/overlap flags below include initial task changes. They describe capture time, not original ownership.
- Scoped diff: `files=108; insertions=39640; deletions=1; binary_files=44; untracked_files=0`
- Outside-scope changes: None

| Path | Task-owned change | Present at late baseline | Overlap |
| --- | --- | --- | --- |
| AGENTS.md | yes | yes | yes |
| README.md | yes | yes | yes |
| progress/2026-10-13-scientific-figure-integration.md | yes | no | no |
| scientific-figure/README.md | yes | yes | yes |
| scientific-figure/SKILL.md | yes | yes | yes |
| scientific-figure/agents/openai.yaml | yes | yes | yes |
| scientific-figure/assets/example-workflow.py | yes | yes | yes |
| scientific-figure/claude/agent.md | yes | yes | yes |
| scientific-figure/examples/README.md | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/README.md | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/aggregate.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/batman.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/benign-book.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/clean-photos.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/distribute.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/malicious-book.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/poisoned-photos.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/sleeping.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/assets/working.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/diagram-spec.md | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/exports/figure-size-preview.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/exports/figure.pdf | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/exports/figure.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/exports/figure.svg | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/exports/grayscale-preview.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/exports/pdf-preview.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/exports/render-report.json | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/figure.svg | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/generate_figure.py | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/manifest.json | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/preview.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/reference-comparison.png | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/scene-graph.json | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/style-profile.md | yes | yes | yes |
| scientific-figure/examples/batman-rebuilt/validation.md | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/README.md | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/diagram-spec.md | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/exports/figure-size-preview.png | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/exports/figure.pdf | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/exports/figure.png | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/exports/figure.svg | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/exports/grayscale-preview.png | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/exports/pdf-preview.png | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/exports/render-report.json | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/figure.svg | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/generate_figure.py | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/manifest.json | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/preview.png | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/reference-comparison.png | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/scene-graph.json | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/style-profile.md | yes | yes | yes |
| scientific-figure/examples/federated-unlearning-rebuilt/validation.md | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/README.md | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/artifact-hashes.json | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/before-after.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/diagram-spec.md | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/exports/figure-size-preview.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/exports/figure.pdf | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/exports/figure.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/exports/figure.svg | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/exports/grayscale-preview.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/exports/pdf-preview.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/exports/render-report.json | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/figure.svg | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/generate_figure.py | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/preview.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/reference-comparison.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/revision-record.md | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/scene-graph.json | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/source/fu_framework.svg | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/source/preview.png | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/style-profile.md | yes | yes | yes |
| scientific-figure/examples/fu-framework-rebuilt/validation.md | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/README.md | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/artifact-hashes.json | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/diagram-spec.md | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/exports/figure-size-preview.png | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/exports/figure.pdf | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/exports/figure.png | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/exports/figure.svg | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/exports/grayscale-preview.png | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/exports/pdf-preview.png | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/exports/render-report.json | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/figure.svg | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/generate_figure.py | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/preview.png | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/reference-comparison.png | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/scene-graph.json | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/style-profile.md | yes | yes | yes |
| scientific-figure/examples/gbhinder-rebuilt/validation.md | yes | yes | yes |
| scientific-figure/examples/workflow/diagram-spec.md | yes | yes | yes |
| scientific-figure/examples/workflow/exports/figure-size-preview.png | yes | yes | yes |
| scientific-figure/examples/workflow/exports/figure.pdf | yes | yes | yes |
| scientific-figure/examples/workflow/exports/figure.png | yes | yes | yes |
| scientific-figure/examples/workflow/exports/figure.svg | yes | yes | yes |
| scientific-figure/examples/workflow/exports/grayscale-preview.png | yes | yes | yes |
| scientific-figure/examples/workflow/exports/pdf-preview.png | yes | yes | yes |
| scientific-figure/examples/workflow/exports/render-report.json | yes | yes | yes |
| scientific-figure/examples/workflow/figure.svg | yes | yes | yes |
| scientific-figure/examples/workflow/method-source.md | yes | yes | yes |
| scientific-figure/examples/workflow/scene-graph.json | yes | yes | yes |
| scientific-figure/examples/workflow/validation.md | yes | yes | yes |
| scientific-figure/references/artifact-contract.md | yes | yes | yes |
| scientific-figure/references/design-and-review.md | yes | yes | yes |
| scientific-figure/references/figure-revision.md | yes | yes | yes |
| scientific-figure/references/reference-matching.md | yes | yes | yes |
| scientific-figure/scripts/render_check.py | yes | yes | yes |
| scientific-figure/tests/test_integration.py | yes | no | no |
| scientific-figure/tests/test_render_check.py | yes | yes | yes |

## Evidence Boundary

The earlier V8 entry reported 32 links; the current rerun establishes 30 (V13), and its correction is retained explicitly. Earlier smoke-render and visual-review results (V5, V6, V9) are preserved historical evidence; this closeout reran the automated suites, metadata/compilation, archive equality, and link checks. The unrestricted staged whitespace check reports 70 pre-existing trailing-space lines in the two SVGs named by V14; they are accepted archive-preservation exceptions, not cleaned artifacts.

Hash equality establishes archive preservation, not scientific acceptance or original-input availability. Historical validation records and paths remain unchanged. The three absent reference PNGs were not fabricated or recovered. Global discovery requires a separate installation; the tested installation used a temporary Claude home. Python caches produced by checks are ignored and excluded from the installed Claude resource tree.

## Next Steps

None within the approved integration scope. The three original reference PNGs would be needed only for future generator rebuilds of those archival examples.
