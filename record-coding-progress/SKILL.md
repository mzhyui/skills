---
name: record-coding-progress
description: Record durable, repository-adaptive progress notes for material coding work, classifying coding records as current-contract function fixes or fresh implementations, or transform a current-session research, design, analysis, or decision discussion into organized project documentation. Use for substantial implementation handoffs or when the user asks to record, conclude, summarize, or preserve session findings. Coding records capture scoped implementation, validation, and Git custody; documentation records preserve decisions, designs, evidence boundaries, and next steps without code-change boilerplate. Commit only when explicitly requested with this skill.
---

# Record Coding Progress

Create a precise, self-contained handoff. Follow repository instructions and local Markdown conventions. Never record hidden reasoning, credentials, environment variables, tokens, or unsupported claims.

## Route the record

Choose exactly one mode:

- **coding-progress**: material runtime, interface, schema, protocol, evaluation, reproducibility, bug-fix, or multi-file implementation work.
- **session-documentation**: a requested research, design, diagnosis, decision, or experiment-plan record with no material code change.

For each `coding-progress` record, automatically classify the delivery; do not ask the user to choose it:

- **function-fix**: a defect correction whose verified, pre-existing public contract (interface, schema, protocol, and intended behavior) remains unchanged. Record the preserved contract and focus the handoff on the defect boundary and corrective changes.
- **fresh-implementation**: a new capability, a newly implemented confirmed plan, an initial implementation, or any task whose contract changes or cannot be verified as pre-existing. Record the plan source and relevant plan detail, original status, core functions, implementation result, and test result.

Use the evidence available in the current task to classify. A user calling something a “fix” is not enough: if the contract changes or its pre-task behavior is not verified, use `fresh-implementation`. When the classification is genuinely ambiguous, use `fresh-implementation` and state the uncertainty rather than claiming a preserved contract.

Skip automatic recording for minor, formatting-only, diagnosis-only, or unfinished work unless the user explicitly asks to preserve it. Record requested partial or blocked outcomes honestly.

Resolve the destination in this order: explicit user path, repository-designated location, existing `progress/`, then `<repository-root>/progress/`. Use `YYYY-MM-DD-<task-slug>.md`. Update a same-task same-day note; never overwrite an unrelated note.

If that note already exists and lacks `Record format: 2`, continue it as v1 using the applicable legacy template:

- coding: [references/progress-template.md](references/progress-template.md)
- documentation: [references/session-documentation-template.md](references/session-documentation-template.md)

Do not convert or bulk-migrate v1 notes implicitly.

## Capture v2 evidence

For a new v2 record, read only the selected mode reference:

- coding: [references/coding-progress-v2.md](references/coding-progress-v2.md)
- documentation: [references/session-documentation-v2.md](references/session-documentation-v2.md)

Use `scripts/record_tool.py` to keep deterministic evidence outside model context:

1. Run `start` before implementation when coding mode applies, passing the automatically selected `--implementation-kind function-fix` or `--implementation-kind fresh-implementation`. If invoked late, pass a verified `--baseline-head`; otherwise record the baseline as unavailable rather than inferring it.
2. Add every material source with `add-source`. Classify conclusions as `verified`, `user-stated`, `inferred`, or `proposed`.
3. Add each observed check with `add-check`. The tool records commands as data and never executes them.
4. Run `finish`; in coding mode pass every task-owned path explicitly.
5. Write the Markdown record from the compact manifest and selected reference.
6. Run `validate`. Fix every error before reporting completion.

Keep the JSON manifest under `/tmp`; do not add it to the repository. The Markdown record must remain understandable without the manifest.

## Preserve evidence boundaries

- State the outcome first and each material fact once.
- Tie conclusions to evidence IDs instead of repeating source detail.
- Distinguish implementation readiness from experimental, production, held-out, or scientific validation.
- Never turn a skipped, partial, blocked, or failed check into a pass.
- In coding mode, separate task-owned, pre-existing, overlapping, and out-of-scope changes.
- In a function-fix record, do not relabel a behavioral or interface change as contract preservation.
- In a fresh-implementation record, bind a source plan file with `add-source --file` when one exists; otherwise add the relevant current-plan conversation as a `user` source. Do not invent a plan, original status, core function, or test result.
- In documentation mode, never imply code changes, experiments, or inspections that did not occur.

## Preserve explicitly supplied Markdown documents

When the user supplies a substantive Markdown-style design, protocol, analysis, or decision document in the conversation and explicitly asks to record it "as is", include its complete text in the record under `## Verbatim User-Supplied Document`. Preserve its original wording, ordering, headings, tables, equations, delimiters, and line breaks; do not normalize notation, repair Markdown, condense it, or replace it with a summary. You may add only the v2 metadata, required record sections, an evidence ledger, and an evidence-boundary statement around the verbatim document.

Classify the supplied document as a `user-stated` source unless its individual claims were separately inspected. Its presence is a durable design record, not verification of cited files, literature, implementation status, experiment status, or scientific claims. Do not let an embedded "verification status" upgrade the record's own evidence state.

## Optional commit mode

Read [references/commit-mode.md](references/commit-mode.md) only when the user explicitly invokes this skill with `commit`, `commit changes`, or equivalent wording. Commit mode is forbidden for implicit invocation and session-documentation mode. Never push unless separately requested.
