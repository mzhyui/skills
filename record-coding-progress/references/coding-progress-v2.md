# Coding-progress record v2

Use this mode for a material implementation result. Keep the record complete but non-repetitive: put each fact in its most specific section and cite its evidence ID elsewhere.

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

Use these metadata lines exactly:

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

Use these required headings:

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

- **Outcome:** direct verdict, deliverables, limitations.
- **Task and Scope:** request, target, starting state, constraints, decisions, assumptions, exclusions. For a `function-fix`, identify the evidence-backed pre-existing contract and the defect boundary. For a `fresh-implementation`, identify the confirmed plan source (a file source or relevant current context), the applicable plan detail, and the original implementation status.
- **Implementation:** concise execution sequence plus a table of repository-relative core paths, symbols, behavioral changes, and roles. A `function-fix` must use `### Preserved Contract` and `### Corrective Change`; state the contract kept and focus on the changes made. A `fresh-implementation` must use `### Plan and Starting Status` and `### Core Functions and Result`; state what was planned, what existed before, the core functions, and the implementation result.
- **Validation:** begin with `### Test Result`, stating the observed test outcome or `Not run: <reason>`. Then use one subsection per manifest check. Use `### <ID> - <result>`, reproduce the exact command in a `text` code fence, and state the observed summary. Record `not-run` reasons.
- **Evidence Ledger:** map every `E*` and `V*` ID used by a material claim to one class (`verified`, `user-stated`, `inferred`, or `proposed`), its locator/check, and the supported conclusion. Validation observations are `verified` even when their result is not a pass.
- **Git Custody:** branch, baseline/final HEAD, history relation, commits since baseline, explicit scopes, task-owned changes, pre-existing changes, overlaps, outside-scope changes, ownership caveats, and the manifest's exact scoped-diff token (`files=N; insertions=N; deletions=N; binary_files=N; untracked_files=N`). Do not call a commit task-owned without separate evidence. Use `unavailable` rather than inference; unborn repositories have no HEAD.
- **Evidence Boundary:** what the work establishes and does not establish.
- **Next Steps:** only unresolved work, dependencies, or `None`.

Run:

```text
python3 <skill-path>/scripts/record_tool.py validate --manifest <temporary-manifest> --note <record-path>
```

Report the record path and validation outcome. Do not commit unless explicit commit mode is active.
