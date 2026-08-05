# Explicit coding-progress commit mode

Apply only when the user explicitly invokes `record-coding-progress` with a commit request.

1. Finish and validate the coding record.
2. Inspect current status, scoped diff, and staged diff.
3. Stage only explicit task-owned paths and the record. Exclude pre-existing or uncertain changes.
4. Stop without committing if ownership is ambiguous, conflicts exist, or required validation failed.
5. Run `git diff --cached --check` and inspect `git diff --cached --stat`.
6. Create one local commit with an imperative subject no longer than 72 characters and, when useful, up to three short body bullets including validation.
7. Report the commit hash and subject. Never push without a separate request.

A record committed with its implementation cannot contain that commit's own hash. State that the hash is available from Git history and report it in the final response.
