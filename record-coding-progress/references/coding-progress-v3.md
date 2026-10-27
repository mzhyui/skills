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

## Record content and presentation

Use the body and folded appendix in [readable-records.md](readable-records.md). The visible body uses `## Outcome`, `## Task and Scope`, `## Implementation`, `## Validation`, `## Evidence Boundary`, and `## Next Steps`, in that order. Add `## Interface and Behavior Changes` only when a contract or behavior changed. Use descriptive topic subheadings where useful; no fixed level-three headings are required.

For `function-fix`, explain the verified preserved contract and corrective change. For `fresh-implementation`, explain the plan source, starting status, core functions, and implementation result.

Summarize validation by what was established, keeping failed, partial, and not-run checks visible with their consequences. The aggregate metadata state is `fail` if any check failed, `partial` if none failed but one is partial, `pass` if at least one passed and all others passed or were not run, and `not-run` otherwise. A `pass` aggregate does not mean every check ran; disclose material omissions in the body.

Put full v3 metadata, `## Check Details`, `## Evidence Ledger`, `## Git Custody`, and `## Lifecycle` in the final appendix. Use descriptive check headings with `Check`, `Result`, and `Evidence` fields, followed by the exact command and observed summary. Keep check receipts once, in Check Details; Evidence Ledger holds sources. Preserve hashes, source classifications, all Git ownership distinctions, the exact scoped-diff token, lifecycle events, and relationships. Use `unavailable` instead of inference. Legacy numbered check sections remain accepted.

Run:

```text
python3 <skill-path>/scripts/record_tool.py validate --manifest <temporary-manifest> --note <note-path>
```

Fix every validation error before reporting completion. Do not commit unless explicit commit mode is active.
