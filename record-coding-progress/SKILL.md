---
name: record-coding-progress
description: Record durable, repository-adaptive progress notes for material coding work, or transform a current-session research, design, analysis, or decision discussion into organized project documentation. Use for substantial implementation handoffs or when the user asks to record, conclude, summarize, or preserve session findings. Coding records capture scoped implementation, validation, and Git custody; documentation records preserve decisions, designs, evidence boundaries, and next steps without code-change boilerplate. Commit only when explicitly requested with this skill.
---

# Record Coding Progress

Create a precise, self-contained handoff. Follow repository instructions and local Markdown conventions. Never record hidden reasoning, credentials, environment variables, tokens, or unsupported claims.

## Route the record

Choose exactly one mode:

- **coding-progress**: material runtime, interface, schema, protocol, evaluation, reproducibility, bug-fix, or multi-file implementation work.
- **session-documentation**: a requested research, design, diagnosis, decision, or experiment-plan record with no material code change.

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

1. Run `start` before implementation when coding mode applies. If invoked late, pass a verified `--baseline-head`; otherwise record the baseline as unavailable rather than inferring it.
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
- In documentation mode, never imply code changes, experiments, or inspections that did not occur.

## Optional commit mode

Read [references/commit-mode.md](references/commit-mode.md) only when the user explicitly invokes this skill with `commit`, `commit changes`, or equivalent wording. Commit mode is forbidden for implicit invocation and session-documentation mode. Never push unless separately requested.
