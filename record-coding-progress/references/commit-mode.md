# Commit mode

Apply only when the user explicitly invokes `record-coding-progress` with a commit request, for an implementation or evaluation record.

1. Finish the record and pass `validate`.
2. Inspect `git status`, the diff of the task paths, and the staged diff.
3. Stage only the task's own changes (the `custody` "Task changes") and the record. Leave out anything also listed under "Pre-existing changes in task paths", unless you can separate the task's part.
4. Stop without committing if ownership is unclear, conflicts exist, or a required check failed. Say why.
5. Run `git diff --cached --check` and review `git diff --cached --stat`.
6. Create one local commit: an imperative subject of at most 72 characters and, when useful, up to three short body bullets, including validation.
7. Report the commit hash and subject. Never push without a separate request.

A record committed with its own change cannot contain that commit's hash. Say that the hash is in the Git history, and report it in your final response.
