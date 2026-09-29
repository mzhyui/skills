# Coding-progress record v3

Use this mode for a material implementation result. First read [lifecycle-v3.md](lifecycle-v3.md), then apply this coding-specific contract.

## Start and capture

Start before implementation and keep the manifest under `/tmp`:

```text
python3 <skill-path>/scripts/record_tool.py start --record-format 3 --mode coding-progress --task-type <type> --task-slug <slug> --record-date <YYYY-MM-DD> --implementation-kind <function-fix|fresh-implementation> --repo <repository> --output <temporary-manifest>
```

Add `--baseline-head <verified-hash>` for a verified late baseline or `--baseline-unavailable` when the baseline cannot be established. Do not substitute current `HEAD` for an unknown baseline. Add optional priority, owner, component, label, start-time, and due-date fields only when grounded; explicit empty defaults are valid.

Add material sources and observed checks with the existing `add-source` and `add-check` commands. Commands are recorded as data and never executed by the record tool. Check IDs remain tool-assigned in insertion order.

## Finish and refresh

Finalize with the actual work status and evidence state:

```text
python3 <skill-path>/scripts/record_tool.py finish --manifest <temporary-manifest> --status <status> --evidence-state <state> --actor <actor> --reason <reason> [--resolution <resolution>] --task-path <path> [--task-path <path> ...] [--record-path <note-path>]
```

Write the note from the finalized manifest. Then rerun `finish` with the same paths, `--record-path`, and `--refresh`; update custody content if needed and validate. Keep the record outside every `--task-path` scope so `--record-path` can include it in custody without making implementation diff counts self-referential.

## Required record shape

In addition to the v3 lifecycle metadata and `## Lifecycle`, use:

1. `## Outcome`
2. `## Task and Scope`
3. `## Lifecycle`
4. `## Implementation`
5. `## Validation`
6. `## Evidence Ledger`
7. `## Git Custody`
8. `## Evidence Boundary`
9. `## Next Steps`

Add `## Interface and Behavior Changes` only when an API, CLI, schema, protocol, file format, default, validation rule, output, or compatibility behavior changed.

For `function-fix`, include `### Preserved Contract` and `### Corrective Change`. For `fresh-implementation`, include `### Plan and Starting Status` and `### Core Functions and Result`.

Begin validation with `### Test Result`, reporting the aggregate manifest state. Then use `### <ID> - <result>` for every check, reproduce its exact command in a `text` fence, and state the observed summary. The aggregate is `fail` if any check failed, `partial` if none failed but one is partial, `pass` if at least one passed and all others passed or were not run, and `not-run` otherwise.

Preserve the v2 evidence-ledger and Git-custody contracts: classify every `E*` and `V*` item, bind hashes when available, separate task-owned and pre-existing changes, reproduce the exact scoped-diff token, and use `unavailable` instead of inference.

Run:

```text
python3 <skill-path>/scripts/record_tool.py validate --manifest <temporary-manifest> --note <note-path>
```

Fix every validation error before reporting completion. Do not commit unless explicit commit mode is active.
