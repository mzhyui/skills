---
name: record-coding-progress
description: Record durable, repository-adaptive progress notes with explicit task type, lifecycle status, resolution, timestamps, local relationships, and evidence state. Use for substantial coding handoffs or when the user asks to record, conclude, summarize, or preserve current-session research, design, diagnosis, or decisions. Coding records classify function fixes versus fresh implementations and capture validation and Git custody; documentation records omit code-change boilerplate. Commit only when explicitly requested with this skill.
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

Resolve the destination in this order: explicit user path, repository-designated location, existing `progress/`, then `<repository-root>/progress/`. Use `YYYY-MM-DD-<task-slug>.md`.

Never upgrade an existing record implicitly:

- If the same-task same-day note is v3 and its original manifest is available, resume or update it with that manifest.
- If the v3 manifest is unavailable, create a uniquely suffixed successor note and add a `supersedes` link; do not reconstruct evidence or overwrite history.
- If the note is v2, continue it with record format 2 and [references/coding-progress-v2.md](references/coding-progress-v2.md) or [references/session-documentation-v2.md](references/session-documentation-v2.md).
- If it lacks `Record format: 2` or `Record format: 3`, continue it as v1 using the applicable legacy template:

  - coding: [references/progress-template.md](references/progress-template.md)
  - documentation: [references/session-documentation-template.md](references/session-documentation-template.md)

Do not convert or bulk-migrate legacy notes.

## Capture v3 evidence

For a new record, read the shared lifecycle reference and only the selected mode reference:

- shared lifecycle: [references/lifecycle-v3.md](references/lifecycle-v3.md)
- coding: [references/coding-progress-v3.md](references/coding-progress-v3.md)
- documentation: [references/session-documentation-v3.md](references/session-documentation-v3.md)

Automatically select a mode-compatible task type from the lifecycle reference. Task type describes the work; mode describes the record; coding implementation class describes contract continuity. Keep these dimensions separate.

Use `scripts/record_tool.py` to keep deterministic evidence outside model context:

1. Run `start --record-format 3` before implementation when coding mode applies, passing the task type, task slug, record date, and automatically selected `--implementation-kind function-fix` or `--implementation-kind fresh-implementation`. If invoked late, pass a verified `--baseline-head`; otherwise record the baseline as unavailable rather than inferring it. Pass `--started-at unavailable` when the actual task start is unknown.
2. Add every material source with `add-source --manifest <path> --kind <kind> --locator <locator>`. The `--locator` is required and must identify the source (file path, URL, or description). Classify conclusions as `verified`, `user-stated`, `inferred`, or `proposed`.
3. Add each observed check with `add-check --manifest <path> --command <command> --result <pass|fail|partial|not-run> --summary <summary>`. All three flags are required. The tool assigns check IDs automatically (V1, V2, ...) in the order added; do not supply `--id`. The `--summary` must state the observed outcome (e.g., "17/17 tests pass", "build fails with error X"). The tool records commands as data and never executes them.
4. Use `transition` and `add-link` when lifecycle state or local relationships change. A blocked state requires its concrete reason. Do not edit lifecycle IDs manually.
5. Run `finish` with the actual status, evidence state, actor, reason, conditional resolution, and every coding task path. Write the Markdown record from the finalized manifest, including exact commands and observed summaries for every check.
6. Rerun `finish --refresh` with the same coding paths plus `--record-path <note-path>`. Refresh recaptures custody without changing lifecycle timestamps or adding an event. Update the note's custody fields, then run `validate --manifest <path> --note <note-path>` and fix every error.

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
- Never fabricate or supply check IDs manually; they are assigned by `add-check` in insertion order. Never omit a required flag (`--locator` on `add-source`; `--command`, `--result`, `--summary` on `add-check`). If a check was not actually run, record it as `--result not-run` with an honest summary rather than inventing an outcome.
- Keep lifecycle status, terminal resolution, evidence state, and validation state independent. A failed check can be verified evidence. Continuing partial work is `in-progress` and `unresolved`; `partial-handoff` is only for intentionally closed scope.

## Preserve explicitly supplied Markdown documents

When the user supplies a substantive Markdown-style design, protocol, analysis, or decision document in the conversation and explicitly asks to record it "as is", include its complete text in the record under `## Verbatim User-Supplied Document`. Preserve its original wording, ordering, headings, tables, equations, delimiters, and line breaks; do not normalize notation, repair Markdown, condense it, or replace it with a summary. You may add only the applicable metadata, required record sections, an evidence ledger, and an evidence-boundary statement around the verbatim document.

Classify the supplied document as a `user-stated` source unless its individual claims were separately inspected. Its presence is a durable design record, not verification of cited files, literature, implementation status, experiment status, or scientific claims. Do not let an embedded "verification status" upgrade the record's own evidence state.

## Optional commit mode

Read [references/commit-mode.md](references/commit-mode.md) only when the user explicitly invokes this skill with `commit`, `commit changes`, or equivalent wording. Commit mode is forbidden for implicit invocation and session-documentation mode. Never push unless separately requested.
