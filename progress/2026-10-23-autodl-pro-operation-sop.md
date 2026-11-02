# AutoDL Pro operation SOP

## Outcome

The source `maintain-server-task-status` skill now includes an AutoDL Pro instance-operation SOP, a credential-aware API helper, and nine offline helper tests. All 69 tests across the required suites passed. The update is in the requested skills repository; no live instances were created or changed during this documentation update.

## Task and Scope

The user requested that the verified AutoDL Pro workflow from the conversation become an SOP in `~/git/skills`. The source skill previously had general server/task-status guidance but no AutoDL API reference or helper. Existing unrelated coding-progress changes were preserved. The supplied token remains outside the repository.

## Implementation

`maintain-server-task-status/references/autodl-pro-operations.md` covers connectivity versus authentication, exact private-image lookup, regional creation, error handling, immediate shutdown, optional runtime verification, persistent watchers, and status evidence. The entrypoint links this reference only for matching AutoDL work. `scripts/autodl_api.py` brings the previously exercised helper into the source skill, with type annotations; it implements raw Authorization, query-encoded GETs, credential redaction, redirect refusal, and explicit mutation guards.

The SOP preserves the distinction between creating and immediately shutting down, which was observed to work in a single requested region, and waiting for boot/GPU verification when requested. It records the observed zone assignment as a dated example rather than a permanent region mapping or performance result. Its watcher procedure preserves the chosen polling cadence and requires durable state, a singleton lock, provider reconciliation, and confirmed shutdown. It does not depend on a personal checkout's watcher implementation.

## Validation

The nine new offline tests cover credentials, encoding, exact region retention, mutation guards, API rejection, uncertain outcomes, and response redaction. The repository's existing installer, math-auditor, coding-progress, and scientific-figure suites passed, for 69 tests total. Skill validation, syntax compilation, whitespace checks, example JSON parsing, and a scan for the supplied credential also passed.

## Evidence Boundary

Live create-and-immediate-shutdown behavior was established earlier in this conversation on 2026-10-23; this update used those saved observations and performed only offline tests. It does not establish boot/GPU performance, future regional capacity, or a shutdown result for a separate earlier instance. Only the requested source skill was updated; the globally installed skill was not resynchronized in this step.

## Next Steps

None for the requested source SOP update. Future operators should resolve images and current provider state again before authorized mutations.

<details>
<summary>Record details — checks, sources, and history</summary>

## Record Metadata

- Record format: `3`
- Record ID: `RCP-20261022T191455Z-86018ce3`
- Mode: `coding-progress`
- Task type: `tooling`
- Task slug: `autodl-pro-operation-sop`
- Date: `2026-10-23`
- Project: `skills` repository
- Priority: `unspecified`
- Owner: `Unassigned`
- Components: `None`
- Labels: `None`
- Status category: `done`
- Status: `done`
- Resolution: `completed`
- Created at: `2026-10-22T19:14:55Z`
- Started at: `2026-10-22T19:14:55Z`
- Updated at: `2026-10-22T19:16:29Z`
- Completed at: `2026-10-22T19:16:29Z`
- Due date: `Not applicable`
- Evidence state: `verified`
- Validation state: `pass`
- Implementation class: `fresh-implementation`

## Check Details

### AutoDL helper behavior

- Check: `V1`
- Result: `pass`
- Evidence: verified

```text
PYTHONPYCACHEPREFIX=/tmp/autodl-sop-pycache python -m unittest discover -s maintain-server-task-status/tests -p 'test_*.py'
```

9 offline AutoDL helper tests passed: query parameters, raw Authorization, exact region/body preservation, nested redaction, credential permissions, mutation guards, API rejection, uncertain outcomes without retry, and non-JSON omission.

### Skill and SOP checks

- Check: `V2`
- Result: `pass`
- Evidence: verified

```text
quick_validate.py maintain-server-task-status; git diff --check -- maintain-server-task-status; parse SOP JSON and scan four changed files for the supplied credential
```

Skill validation and whitespace check passed. SOP JSON preserves single-region selection and the GPU spec; no supplied credential appears in any changed file.

### Repository regression suites

- Check: `V3`
- Result: `pass`
- Evidence: verified

```text
PYTHONPYCACHEPREFIX=/tmp/autodl-sop-pycache python -m unittest discover -s tests -p 'test_*.py'
PYTHONPYCACHEPREFIX=/tmp/autodl-sop-pycache python -m unittest discover -s paper-math-auditor/tests -p 'test_*.py'
PYTHONPYCACHEPREFIX=/tmp/autodl-sop-pycache python -m unittest discover -s record-coding-progress/tests -p 'test_*.py'
PYTHONPYCACHEPREFIX=/tmp/autodl-sop-pycache python -m unittest discover -s scientific-figure/tests -p 'test_*.py'
```

All repository-prescribed suites passed: installer 13, math auditor 9, coding-progress 29, scientific-figure 9; 60 existing tests plus 9 new helper tests = 69 passed.

### Python syntax checks

- Check: `V4`
- Result: `pass`
- Evidence: verified

```text
PYTHONPYCACHEPREFIX=/tmp/autodl-sop-pycache python -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py maintain-server-task-status/scripts/autodl_api.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py scientific-figure/scripts/render_check.py scientific-figure/assets/example-workflow.py scientific-figure/examples/*/generate_figure.py
```

All prescribed Python syntax checks and the new AutoDL helper compiled successfully; caches redirected to /tmp.

## Evidence Ledger

- E1 (user-stated): Current conversation: update ~/git/skills server-task skill with AutoDL Pro instance-operation SOP; preserve the verified private-image, single-region create-and-shutdown procedure. Defines the requested scope.

## Git Custody

- Branch: `main`
- Baseline HEAD: `3c10718e02d42500b1cb3f0d0ec32c0535921486`
- Final HEAD: `3c10718e02d42500b1cb3f0d0ec32c0535921486`
- History relation: `same`
- Commits since baseline: None; no commit or push requested.
- Record path: `progress/2026-10-23-autodl-pro-operation-sop.md`
- Scoped diff: files=1; insertions=5; deletions=0; binary_files=0; untracked_files=3

| Path | Custody categories |
| --- | --- |
| `maintain-server-task-status/SKILL.md` | task_paths, task_owned_changed_paths |
| `maintain-server-task-status/references/autodl-pro-operations.md` | task_paths, task_owned_changed_paths |
| `maintain-server-task-status/scripts/autodl_api.py` | task_paths, task_owned_changed_paths |
| `maintain-server-task-status/tests/test_autodl_api.py` | task_paths, task_owned_changed_paths |
| `progress/2026-10-21-readable-progress-records.md` | preexisting_paths, outside_scope_changed_paths |
| `progress/2026-10-21-update-installed-record-coding-progress.md` | preexisting_paths, outside_scope_changed_paths |
| `progress/2026-10-23-autodl-pro-operation-sop.md` | task_owned_changed_paths |
| `record-coding-progress/SKILL.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/agents/openai.yaml` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/claude/agent.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/references/coding-progress-v2.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/references/coding-progress-v3.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/references/lifecycle-v3.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/references/readable-records.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/references/session-documentation-v2.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/references/session-documentation-v3.md` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/scripts/record_tool.py` | preexisting_paths, outside_scope_changed_paths |
| `record-coding-progress/tests/test_record_tool.py` | preexisting_paths, outside_scope_changed_paths |

Pre-existing overlap: None. Unrelated pre-existing work was preserved.

## Lifecycle

Current blocker: None

| ID | At | Action | From | To | Actor | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | 2026-10-22T19:14:55Z | created | none | in-progress | record-tool | record created |
| L2 | 2026-10-22T19:16:29Z | transition | in-progress | done | codex | Source skill now includes the verified AutoDL Pro operation SOP, secure API helper, and offline tests; all checks passed |

Local relationships: None.

</details>
