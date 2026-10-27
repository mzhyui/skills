# Coding-progress record v2

Use this mode for a material implementation result. Keep the record complete but non-repetitive: put each fact in its most specific section and link to descriptively named details where useful.

## Start and finish evidence capture

Create a temporary manifest before editing:

```text
python3 <skill-path>/scripts/record_tool.py start --mode coding-progress --implementation-kind <function-fix|fresh-implementation> --repo <repository> --output <temporary-manifest>
```

If recording begins late, use `--baseline-head <verified-hash>` only when the baseline is known; otherwise pass `--baseline-unavailable`. Never substitute the current `HEAD` for an unknown baseline. Add sources and observed checks during the task, then finalize with repeated explicit scopes:

```text
python3 <skill-path>/scripts/record_tool.py finish --manifest <temporary-manifest> --task-path <path> --record-path <record-path>
```

After writing the note, rerun `finish` with the same paths plus `--refresh`, update its custody fields, then validate. Keep the record outside every `--task-path` scope: `--record-path` makes it task-owned but excludes it from numeric implementation-diff counts, avoiding self-reference. For a local source artifact, use `add-source --file <path>` to compute its SHA-256.

## Required record shape

Use these metadata lines exactly, preferably in the final appendix described in [readable-records.md](readable-records.md):

```markdown
# <Title>

- Record format: `2`
- Mode: `coding-progress`
- Implementation class: `function-fix` or `fresh-implementation`
- Date: `YYYY-MM-DD`
- Project: <repository>
- Status: `completed`, `partial`, or `blocked`
- Evidence state: `verified`, `mixed`, or `unverified`
```

Use these required headings; order the body and appendix as described below:

1. `## Outcome`
2. `## Task and Scope`
3. `## Implementation`
4. `## Validation`
5. `## Evidence Ledger`
6. `## Git Custody`
7. `## Evidence Boundary`
8. `## Next Steps`

Add `## Interface and Behavior Changes` only when an API, CLI, schema, protocol, file format, default, validation rule, output, or compatibility behavior changed.

## Content contract

Apply [readable-records.md](readable-records.md): Outcome → Task and Scope → Implementation → optional Interface and Behavior Changes → Validation → Evidence Boundary → Next Steps. Put metadata, Check Details, Evidence Ledger, and Git Custody in the final folded appendix. No fixed level-three body headings are required.

- **Outcome:** direct verdict and the limitation that determines its scope.
- **Task and Scope:** request, target, starting state, and material constraints or exclusions.
- **Implementation:** explain changes by topic and identify core paths/functions where useful. For `function-fix`, identify the evidence-backed pre-existing contract, defect boundary, and corrective change. For `fresh-implementation`, identify the confirmed plan source and applicable detail, original implementation status, core functions, and result.
- **Validation:** summarize outcomes and their implications by validation area. Group routine checks. Explain failures, partial results, skips, and not-run checks; do not paste commands or use check IDs as headings in the body.
- **Check Details:** one descriptively named entry per manifest check, with tool-assigned `Check`, exact `Result`, `Evidence: verified`, exact command, observed summary, and artifact hash when captured. Record not-run reasons. Existing numbered headings with check classifications in Evidence Ledger remain valid.
- **Evidence Ledger:** map every source ID to its class (`verified`, `user-stated`, `inferred`, or `proposed`), locator, captured hash, and supported conclusion. Check entries in Check Details need not be repeated here.
- **Git Custody:** branch, baseline/final HEAD, history relation, commits since baseline, explicit scopes, task-owned changes, pre-existing changes, overlaps, outside-scope changes, ownership caveats, record path, and the manifest's exact scoped-diff token (`files=N; insertions=N; deletions=N; binary_files=N; untracked_files=N`). Do not call a commit task-owned without separate evidence. Use `unavailable` rather than inference; unborn repositories have no HEAD.
- **Evidence Boundary:** substantive limits, without repeating conclusions already explained.
- **Next Steps:** unresolved work, dependencies, or `None`.

Run:

```text
python3 <skill-path>/scripts/record_tool.py validate --manifest <temporary-manifest> --note <record-path>
```

Report the record path and validation outcome. Do not commit unless explicit commit mode is active.
