# Scientific-figure editable PowerPoint delivery

- Record format: `2`
- Mode: `coding-progress`
- Implementation class: `fresh-implementation`
- Date: `2026-11-03`
- Project: `/home/mzhyui/git/skills`
- Status: `completed`
- Evidence state: `mixed`

## Outcome

Added an optional native editable PPTX workflow, a runnable single-slide example,
a standard-library structural inventory, and behavioral tests. The example and
its PPTX-derived previews are retained under `scientific-figure/examples/editable-pptx/`.
Native object structure, programmatic edit persistence, and LibreOffice rendering
are verified (V5, V8–V10). Microsoft PowerPoint interaction is untested.

## Task and Scope

The user asked whether scientific-figure can also provide a PPTX artifact that
is friendly to later editing (E1). Interpreted this as adding an optional
PowerPoint companion to the repository skill. The implementation uses native
objects and disclosed image/route limitations, without changing default SVG/PDF
delivery, rewriting archival figures, or installing globally. Existing icon
work from earlier conversation turns remains outside this task.

## Implementation

### Plan and Starting Status

The task plan follows E1: add native-editability guidance, demonstrate it in a
runnable example, inventory actual OOXML objects, and verify editing and rendering.
The baseline skill delivered SVG/PDF/PNG but had no PPTX contract or example (E2).
The current update adds this capability; it is not a lossless general SVG converter.

### Core Functions and Result

| Core paths | Function and result |
| --- | --- |
| `scientific-figure/SKILL.md`, `README.md`, `references/artifact-contract.md` | Route optional PPTX requests and define companion deliverables and evidence limits. |
| `scientific-figure/references/editable-powerpoint.md` | Specify native text/shapes/connectors, object naming, editability disclosure, source authority, and actual PPTX render review. |
| `scientific-figure/agents/openai.yaml`, `claude/agent.md` | Align Codex and Claude discovery and behavior. |
| `scientific-figure/assets/example-editable-pptx.py` | `build_presentation()` generates named native objects, grouped icons, attached forward connectors, and an explicit freeform feedback route; CLI preserves existing outputs. |
| `scientific-figure/scripts/pptx_check.py` | `inspect_pptx()` follows slide order, recursively inventories native objects, checks IDs and connection targets, and discloses picture-only or unsupported evidence. |
| `scientific-figure/tests/test_pptx.py` | Seven focused tests cover object inspection, invalid input, preservation, and edit/save/reopen behavior. |
| `scientific-figure/examples/editable-pptx/`, `examples/README.md` | Retain an actual editable PPTX, structural report, editability notes, rendered PDF/PNGs, hashes, and visual-review record; index the new example separately from archives. |

## Interface and Behavior Changes

PPTX becomes an optional deliverable when requested. The native generator requires
`python-pptx`; the checker needs only the standard library. Both CLIs expose
`--help` and reject replacing existing output files. Inventory status is
`inspected` or `invalid`, never a visual/scientific approval. Programmatic node
movement does not prove interactive auto-routing in a presentation application.

## Validation

### Test Result

Across the four required suites, 72 tests pass when the scientific-figure suite
runs in the dependency-equipped environment (V1–V3, V5). The system-Python run
explicitly skips two native-generation tests (V4). Compilation and skill checks
pass (V6). The sandbox renderer failure and successful authorized retry are
recorded separately (V7–V8). The enlarged and nominal-size previews were inspected
(V10); no actual Microsoft PowerPoint application session was available.

### V1 - pass

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
```

13 installer tests passed.

### V2 - pass

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py'
```

9 math-auditor tests passed.

### V3 - pass

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py'
```

29 progress-record tests passed.

### V4 - partial

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scientific-figure/tests -p 'test_*.py'
```

21 discovered: 19 passed, 2 native-generation tests skipped because system Python lacks python-pptx; V5 exercises all 21.

### V5 - pass

```text
PYTHONDONTWRITEBYTECODE=1 /home/mzhyui/git/emogame/.venv/bin/python -m unittest discover -s scientific-figure/tests -p 'test_*.py'
```

All 21 passed, including 7 new PowerPoint tests and label/node save-reopen persistence with connector target IDs retained.

### V6 - pass

```text
python3 -m py_compile scientific-figure/scripts/pptx_check.py scientific-figure/assets/example-editable-pptx.py scientific-figure/tests/test_pptx.py && python3 /home/mzhyui/.codex/skills/.system/skill-creator/scripts/quick_validate.py scientific-figure && git diff --check
```

Compilation, skill validation, and tracked diff whitespace checks passed. Updated skill guidance local links resolve.

### V7 - fail

```text
libreoffice -env:UserInstallation=file:///tmp/scientific-pptx-render/lo-profile --headless --convert-to pdf --outdir /tmp/scientific-pptx-render scientific-figure/examples/editable-pptx/figure.pptx
```

Initial sandboxed renderer exited 1 without PDF; a memory-settings retry also exited 1. Authorized rendering outside the sandbox succeeded in V8.

### V8 - pass

```text
GSETTINGS_BACKEND=memory libreoffice -env:UserInstallation=file:///tmp/scientific-pptx-clean/lo-profile --headless --convert-to pdf --outdir /tmp/scientific-pptx-clean /tmp/scientific-pptx-clean/figure.pptx
```

LibreOffice 24.2.7.2 rendered the final shadow-free PPTX; final PDF retained as examples/editable-pptx/pptx-render.pdf.

### V9 - pass

```text
python3 scientific-figure/scripts/pptx_check.py /tmp/scientific-pptx-clean/figure.pptx --output /tmp/scientific-pptx-clean/pptx-report.json
```

One 7 x 3.4 inch slide; 12 text-bearing objects, 10 native shapes, 3 groups, 11 connectors including 2 attached forward arrows; zero pictures, errors, or warnings. Report copied with final PPTX.

### V10 - pass

```text
view_image(path='/home/mzhyui/git/skills/scientific-figure/examples/editable-pptx/pptx-preview.png'); view_image(path='/home/mzhyui/git/skills/scientific-figure/examples/editable-pptx/pptx-size-preview.png')
```

Assistant inspected actual PPTX-derived previews at 1800 px and nominal 7 inch/96 dpi size. No observed clipping, text collisions, or missing arrows; final theme shadows removed. Not a Microsoft PowerPoint interaction test.

## Evidence Ledger

| ID | Class | Locator and supported conclusion |
| --- | --- | --- |
| E1 | user-stated | Current conversation: add a post-editing-friendly PPTX artifact option to scientific-figure; native editable objects, runnable example, structural and rendered validation. The workflow detail is the implementation interpretation. |
| E2 | verified | Baseline `scientific-figure/SKILL.md`, SHA-256 `d71e5890faf78ab34bc0ffe060a12ca44395c9888811f928e3b700d938f36d89`: SVG/PDF/PNG workflow existed; PPTX delivery was absent. |
| V1 | verified | Exact command and observed pass outcome in Validation. |
| V2 | verified | Exact command and observed pass outcome in Validation. |
| V3 | verified | Exact command and observed pass outcome in Validation. |
| V4 | verified | Exact command and observed partial outcome in Validation. |
| V5 | verified | Exact command and observed pass outcome in Validation. |
| V6 | verified | Exact command and observed pass outcome in Validation. |
| V7 | verified | Exact command and observed fail outcome in Validation. |
| V8 | verified | Exact command and observed pass outcome in Validation. |
| V9 | verified | Exact command and observed pass outcome in Validation. |
| V10 | verified | Exact command and observed pass outcome in Validation. |

## Git Custody

Branch: `main`. Baseline and final HEAD: `44a08610290041296793cf5ee6b0b188f9335c31`.
History relation: `same`; commits since baseline: none. No commit or push.

Task scopes (the record is separately task-owned):

- `scientific-figure/README.md`
- `scientific-figure/SKILL.md`
- `scientific-figure/agents/openai.yaml`
- `scientific-figure/assets/example-editable-pptx.py`
- `scientific-figure/claude/agent.md`
- `scientific-figure/examples/README.md`
- `scientific-figure/examples/editable-pptx`
- `scientific-figure/references/artifact-contract.md`
- `scientific-figure/references/editable-powerpoint.md`
- `scientific-figure/scripts/pptx_check.py`
- `scientific-figure/tests/test_pptx.py`

Task-owned changed paths:

- `progress/2026-11-03-scientific-figure-editable-pptx.md`
- `scientific-figure/README.md`
- `scientific-figure/SKILL.md`
- `scientific-figure/agents/openai.yaml`
- `scientific-figure/assets/example-editable-pptx.py`
- `scientific-figure/claude/agent.md`
- `scientific-figure/examples/README.md`
- `scientific-figure/examples/editable-pptx/figure.pptx`
- `scientific-figure/examples/editable-pptx/pptx-editability.md`
- `scientific-figure/examples/editable-pptx/pptx-preview.png`
- `scientific-figure/examples/editable-pptx/pptx-render.pdf`
- `scientific-figure/examples/editable-pptx/pptx-report.json`
- `scientific-figure/examples/editable-pptx/pptx-size-preview.png`
- `scientific-figure/examples/editable-pptx/validation.md`
- `scientific-figure/references/artifact-contract.md`
- `scientific-figure/references/editable-powerpoint.md`
- `scientific-figure/scripts/pptx_check.py`
- `scientific-figure/tests/test_pptx.py`

Pre-existing and outside-scope paths (unchanged by this task):

- `scientific-figure/examples/icons/README.md`
- `scientific-figure/examples/icons/azure.svg`
- `scientific-figure/examples/icons/cloud-server-sketch.svg`
- `scientific-figure/examples/icons/curved-arrow.svg`
- `scientific-figure/examples/icons/elastic-cloud-server.svg`
- `scientific-figure/examples/icons/hacker-avatar-sketch.svg`
- `scientific-figure/examples/icons/huggingface-outline.svg`
- `scientific-figure/examples/icons/neural-network-sketch.svg`
- `scientific-figure/examples/icons/neural-network-weights-hand-drawn.svg`

Pre-existing overlap: none. No other outside-scope changes remain. A tracked
bytecode file modified by the required compilation check was restored to its
verified clean baseline bytes. File ownership describes this turn, not authorship
of the baseline repository or earlier icon work.

Scoped diff: `files=6; insertions=55; deletions=4; binary_files=0; untracked_files=11`.
Untracked artifacts are counted separately by the record tool; its tracked
binary-file count does not mean the new example has no binary artifacts.

## Evidence Boundary

This is a repository skill update and illustrative native-object example, not a
scientific result, a conversion of the user's research diagram, or a claim of
SVG/PPTX pixel parity. LibreOffice rendering and python-pptx edit persistence do
not establish Microsoft PowerPoint rendering or interactive connector behavior.
Complex artwork and equations may require disclosed picture/outline regions in
future figures; this particular sample contains no pictures. Manual PowerPoint
edits do not synchronize back into SVG/PDF or the generator automatically.

## Next Steps

None for this scoped capability update. Microsoft PowerPoint interaction remains
an explicit validation limitation; apply the native workflow to a supplied
scientific figure when one is requested.
