# Readable progress records

## Outcome

Progress records now lead with a readable account of the work: the result, meaningful changes, validation findings, limits, and next steps. Exact commands, evidence IDs, hashes, full metadata, lifecycle events, and Git custody move to a folded appendix at the end. Failures and qualifications remain visible in the body.

## Task and Scope

The user identified the RTX 3080 to A6000 migration note as difficult to read, especially its ten numbered validation subsections and duplicated evidence ledger. The confirmed request was to redesign the record-coding-progress skill's structure around a human-friendly body. The prior templates required numbered check headings and rigid implementation subheadings; v3 also placed lifecycle history among the main sections.

## Implementation

### A narrative body and an evidence appendix

The [writing guide](../record-coding-progress/references/readable-records.md) defines the new layout and includes a migration-results example. Writers explain changes by topic, summarize validation by what it establishes, and group routine checks. Descriptive links lead to the detailed receipts when needed. Fixed implementation and test-result subheadings are no longer required; the substantive content requirements remain in the instructions.

Coding and session-documentation references for v2 and v3 now follow this layout. The Codex default prompt and Claude agent instructions use the same convention. Session records retain their design content and omit checks and Git custody.

### Check receipts remain tied to their evidence

The [record tool](../record-coding-progress/scripts/record_tool.py) accepts named appendix entries containing a check ID, result, evidence classification, exact command, observed summary, and captured artifact hash. Each new receipt is checked against its own manifest entry, so another check's text cannot satisfy a missing command or outcome. Duplicate and unknown check IDs are rejected. A check recorded here no longer needs a second copy in Evidence Ledger.

## Interface and Behavior Changes

This adds a Markdown presentation option to formats 2 and 3. Existing numbered check layouts remain valid, and the manifest schemas, CLI arguments, lifecycle vocabulary, and format dispatch remain unchanged. Session records reject the new Check Details section, consistent with their existing prohibition on command validation.

## Validation

All 60 repository tests passed: 29 record-tool tests, 13 installer tests, nine math-auditor tests, and nine scientific-figure tests. The new cases cover folded records, discovery, v2/v3 compatibility, and rejection of false results or receipts borrowed from another check. Existing lifecycle and custody tests continue to pass.

The required Python compilation checks, skill validation, and whitespace check also passed. [Exact commands and outcomes](#check-details) are retained below.

## Evidence Boundary

The migration example rephrases the supplied historical record; its experiments were not rerun. Parser tests establish compatibility and receipt matching, while prose quality still requires editorial judgment. Folding depends on the Markdown renderer; the same content can remain an ordinary final appendix where folding is unsupported. Changes are in this repository; installed skill copies and the original migration note were not changed.

## Next Steps

None for the repository redesign.

<details>
<summary>Record details — checks, sources, and history</summary>

## Record Metadata

- Record format: `3`
- Record ID: `RCP-20261020T192730Z-11d189c7`
- Mode: `coding-progress`
- Task type: `tooling`
- Task slug: `readable-progress-records`
- Date: `2026-10-21`
- Project: `/home/mzhyui/git/skills`
- Priority: `unspecified`
- Owner: `Unassigned`
- Components: `None`
- Labels: `None`
- Status category: `done`
- Status: `done`
- Resolution: `completed`
- Created at: `2026-10-20T19:27:30Z`
- Started at: `unavailable`
- Updated at: `2026-10-20T19:31:28Z`
- Completed at: `2026-10-20T19:31:28Z`
- Due date: `Not applicable`
- Evidence state: `mixed`
- Validation state: `pass`
- Implementation class: `fresh-implementation`

## Check Details

### Record validation and compatibility

- Check: `V1`
- Result: `pass`
- Evidence: `verified`

```text
python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py'
```

29 tests passed, including named check receipt binding, folded v2/v3 validation, discovery, and legacy compatibility.

### Repository regression suites

- Check: `V2`
- Result: `pass`
- Evidence: `verified`

```text
python3 -m unittest discover -s tests -p 'test_*.py' && python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py' && python3 -m unittest discover -s scientific-figure/tests -p 'test_*.py'
```

Installer: 13 tests passed; math auditor: 9 tests passed; scientific figure: 9 tests passed.

### Python compilation

- Check: `V3`
- Result: `pass`
- Evidence: `verified`

```text
python3 -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py && python3 -m py_compile scientific-figure/scripts/render_check.py scientific-figure/assets/example-workflow.py scientific-figure/examples/*/generate_figure.py
```

All repository-prescribed Python compilation checks passed.

### Skill structure

- Check: `V4`
- Result: `pass`
- Evidence: `verified`

```text
python3 /home/mzhyui/.codex/skills/.system/skill-creator/scripts/quick_validate.py record-coding-progress
```

Skill is valid.

### Whitespace

- Check: `V5`
- Result: `pass`
- Evidence: `verified`

```text
git diff --check
```

No whitespace errors.

## Evidence Ledger

- E1 (user-stated): Current conversation: redesign record-coding-progress around a human-friendly body, using the RTX 3080 to A6000 migration note as the motivating example..
- E2 (verified): record-coding-progress/SKILL.md. SHA-256: `0d580b6af09d333007ea9e292a14a5d5dcb32fbc1663a03603bdf50fa680cb53`.
- E3 (verified): record-coding-progress/references/readable-records.md. SHA-256: `295271400e19ca620bea7ea44f9c00ffc34c70f64b12d1824ae13ded3c41e8d0`.
- E4 (verified): record-coding-progress/scripts/record_tool.py. SHA-256: `0d669587343e5d99df095c4bd7605e235fb2f1398526a262d50b2ddb68e99626`.
- E5 (verified): record-coding-progress/tests/test_record_tool.py. SHA-256: `4d1eb5526d958ca43269389053168eae2ace82ce71e8e29d291bdc107680ce62`.
- E6 (verified): /home/mzhyui/git/llm_acceleration/progress/2026-10-21-rtx3080-a6000-migration.md. SHA-256: `e25ebe6db51e4759c9ea1ca7749d513d41260959f1bc1091516ca3011ab56ba1`.

## Git Custody

- Branch: `main`
- Baseline HEAD: `3c10718e02d42500b1cb3f0d0ec32c0535921486`
- Final HEAD: `3c10718e02d42500b1cb3f0d0ec32c0535921486`
- History relation: `same`
- Commits since baseline: None. No commit or push performed.
- Implementation scope: `record-coding-progress`.
- Task-owned paths: `progress/2026-10-21-readable-progress-records.md`, `record-coding-progress/SKILL.md`, `record-coding-progress/agents/openai.yaml`, `record-coding-progress/claude/agent.md`, `record-coding-progress/references/coding-progress-v2.md`, `record-coding-progress/references/coding-progress-v3.md`, `record-coding-progress/references/lifecycle-v3.md`, `record-coding-progress/references/readable-records.md`, `record-coding-progress/references/session-documentation-v2.md`, `record-coding-progress/references/session-documentation-v3.md`, `record-coding-progress/scripts/record_tool.py`, `record-coding-progress/tests/test_record_tool.py`.
- Pre-existing changes: None.
- Overlap: None.
- Outside-scope changes: None.
- Record path: `progress/2026-10-21-readable-progress-records.md`
- Scoped diff: `files=10; insertions=167; deletions=123; binary_files=0; untracked_files=1`
- Ownership caveats: None. The record is excluded from implementation diff counts.

## Lifecycle

Current blocker: None

| ID | At | Action | From | To | Actor | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | 2026-10-20T19:27:30Z | created | none | in-progress | record-tool | record created |
| L2 | 2026-10-20T19:31:28Z | transition | in-progress | done | codex | Completed readable record presentation and compatibility validation. |

Local relationships: None.

</details>
