---
name: edit-paper-with-history
description: Edit or revise academic-paper prose while preserving a scope-confirmed, timestamped, human-readable editing history. Use for manuscript editing, rewriting, shortening, polishing, restructuring, or terminology changes in LaTeX, Markdown, or other text paper sources when Codex must first confirm exact target sections or ranges, summarize the original text and its core idea, and record every completed addition, deletion, and replacement as exact before-and-after passages.
---

# Edit Paper With History

Use a confirmation gate and a current-text baseline to keep paper edits bounded and auditable. Treat the target repository's existing content, including uncommitted changes, as user-owned.

## 1. Declare and confirm scope

Inspect the requested source files, then present a scope declaration containing:

- repository-relative target paths;
- one or more exact locators per file: section or subsection title, heading-to-heading interval, line interval, or quoted start and end anchors;
- the editing objective;
- explicit exclusions, including adjacent sections that must remain unchanged.

Use section titles or quoted boundary anchors whenever line numbers may drift. Do not edit yet. Wait for explicit user confirmation of the declaration even when the initial request appears precise.

If the user expands or changes the scope later, issue a revised declaration and obtain confirmation again. Do not silently include synchronized copies, bibliography files, appendices, or nearby prose.

## 2. Capture the current baseline

After confirmation and immediately before editing:

1. Record a timezone-aware start timestamp.
2. Capture the current contents of every target file or confirmed passage in a uniquely named temporary directory outside the repository.
3. Read the captured passage and write a concise original-text summary and core idea or argument.
4. Note important qualifications, evidence boundaries, terminology, citations, or notation that the edit must preserve.

Use this capture—not Git `HEAD`, a commit, or a hash—as the session baseline. Never attribute pre-existing worktree changes to the current edit.

Keep the capture temporary. Do not add snapshots, manifests, or draft history records to the repository. If the session is aborted or produces no text change, remove or abandon the temporary capture and create no editing-history record.

## 3. Edit only the confirmed passage

Make the requested paper edit without crossing a confirmed boundary. Preserve user changes outside the captured scope and follow repository-specific manuscript instructions.

Write revised manuscript prose in an academic-paper register. State the research question, method, evidence, interpretation, or limitation directly; do not frame prose as a software interface, validation log, or technical report. In titles, headings, captions, tables, and narrative, avoid schema-like field names and process-status wording such as `is_valid`, `input_requirement`, `pass_status`, `status: passed`, or checklist-style verdicts unless quoting or defining an indispensable artifact exactly. Translate the underlying idea into reader-facing prose (for example, "the setting satisfies the stated assumptions" or "the result meets the pre-specified criterion").

Prefer language that explains what the paper establishes in its stated setting over language that advertises a system, release, interface, or workflow. Retain precise implementation terms when needed for reproducibility, but introduce and explain them as scientific objects rather than product features.

For a multi-file session, edit only the confirmed scope in each listed file. A conceptual need for synchronization does not authorize editing an unlisted source.

If an out-of-scope or concurrent modification appears:

- stop the session;
- preserve user work;
- do not overwrite or broadly revert the file;
- report the conflict and request direction;
- do not emit a completed history record.

## 4. Account for every completed change

Compare the temporary baseline directly with the final current text. Review both a line-oriented diff and, when useful for dense prose, a word-oriented diff.

Group adjacent edits only when they form one coherent replacement. Record every session-owned:

- addition;
- deletion;
- replacement;
- movement of text, represented as a deletion plus an addition unless exact before-and-after blocks make the move unambiguous.

For each entry, provide:

- repository-relative path;
- confirmed scope;
- change type;
- original and final line locators when available;
- exact `Before` passage;
- exact `After` passage;
- a concise factual reason.

Use `(empty)` for the missing side of a pure addition or deletion. Do not use vague statements such as "polished wording" in place of exact passages. Do not claim unchanged words or lines were changed.

## 5. Write the completed history

Create `editing_history/` at the target repository root only after the edit is complete and non-empty. Copy [assets/editing-history-template.md](assets/editing-history-template.md) and fill every applicable field.

Name the record:

`YYYY-MM-DDTHH-MM-SS+HH-MM--short-scope.md`

Use a filesystem-safe, timezone-aware completion timestamp and a short lowercase hyphenated scope slug. Keep paths repository-relative. One record may cover multiple files only if their scopes were confirmed together.

Before finishing, verify:

- the record says `completed`;
- start and completion timestamps include timezones;
- every target path and confirmed locator appears;
- each scope has an original summary and core idea;
- the exact before-and-after entries reproduce the complete session diff within the confirmed scope;
- no session-owned change falls outside the confirmed scope;
- no hash, Git custody claim, commit, or push was added unless separately requested.

Report the edited paths and the new history-record path to the user.
