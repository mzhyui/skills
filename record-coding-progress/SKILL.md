---
name: record-coding-progress
description: Write a clear, durable progress record: an implementation handoff (a fix or a new capability), an evaluation readout (what an evaluation, benchmark, ablation, or experiment found and what it means), or a session record of research, design, diagnosis, or decisions (what method was discussed and what was decided). Use for substantial coding handoffs, finished evaluations, or when the user asks to record, conclude, summarize, or preserve session findings. Commit only when explicitly requested with this skill.
---

# Record Coding Progress

Write a record a teammate can act on after reading only its first section. Read [references/record-formats.md](references/record-formats.md) before writing: it holds the writing rules, a template for each kind, and examples.

## Choose the kind

Pick the kind yourself; don't ask the user.

- **evaluation**: the main deliverable is a new measurement, such as an evaluation, benchmark, ablation, experiment run, or method comparison. Use it even when code was written to run the measurement; describe that code under Setup.
- **implementation**: the main deliverable is code. Set `Change type`:
  - `fix`: corrects a defect while a verified, pre-existing contract (interface, schema, protocol, intended behavior) stays the same. Name that contract.
  - `new`: adds a capability, implements a plan, or changes a contract. Also use `new` when you can't verify that the contract existed before. Name the plan source (a file or the conversation).

  The evidence decides, not the user's wording: a requested "fix" that changes behavior is `new`.
- **session**: no material code change and no new runs. Covers research, design, diagnosis, decisions, reviews, experiment plans, and analysis of existing outputs.

Skip recording minor, formatting-only, or unfinished work unless the user asks. Record requested partial or blocked work honestly.

## Where it goes

Use the user's explicit path; else a location the repository designates; else an existing `progress/`; else `<repository-root>/progress/`. Name the file `YYYY-MM-DD-<task-slug>.md`.

If a format-4 note for the same task and day exists, update it in place. Notes in older formats (no `Record format: 4`) are frozen. Never rewrite or convert them; write a new note with `- Follows: <old note path>` instead.

## Capture Git facts

For implementation and evaluation records, keep the snapshot outside the repository:

1. Before changing anything: `python3 <skill-path>/scripts/record_tool.py start --repo <repo> --output /tmp/<slug>-snapshot.json`
2. When done: `python3 <skill-path>/scripts/record_tool.py custody --snapshot /tmp/<slug>-snapshot.json --path <task path> [--path ...]`. Paste the output under `## Git` in the appendix.

Pass each file or directory the task changed as `--path`, never the repository root. If recording starts late, replace `--snapshot` with `--repo <repo>` plus `--baseline <verified commit>` or `--baseline unavailable`. Never take the current HEAD as an unknown baseline. Outside a Git repository, write `Git: not applicable`.

## Write it

Follow the template for the kind, then:

- List each check you actually ran under the appendix's `## Commands`: name, result (`pass`, `fail`, `partial`, or `not-run`), exact command, observed outcome. List an expected but skipped check as `not-run` with the reason.
- Keep tests and verifiers apart from findings. A method that ran correctly and performed badly is a finding.
- Keep this task's changes apart from changes already in the worktree. The `custody` output separates them.
- In a session record, never imply code changes, runs, or inspections that didn't happen.
- Never record secrets, credentials, environment-variable values, or hidden reasoning.

Validate, fix every error, then report the record path and the result:

```text
python3 <skill-path>/scripts/record_tool.py validate --note <note-path>
```

`record_tool.py list --root <progress-dir>` lists existing records of every format with their one-line headlines. It never writes.

## Preserve supplied documents

When the user supplies a substantive Markdown design, protocol, analysis, or decision document and asks to record it "as is", include its full text under `## Verbatim user-supplied document`. Keep its wording, order, headings, tables, equations, and line breaks unchanged. Treat it as `(user-stated)`: including it does not verify the files, results, or claims it mentions.

## Commit mode

Read [references/commit-mode.md](references/commit-mode.md) only when the user explicitly invokes this skill with `commit` or equivalent wording, for an implementation or evaluation record. Never commit otherwise or for session records. Never push unless asked separately.
