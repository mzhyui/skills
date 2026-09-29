# Record lifecycle v3

Read this reference for every new record-format-3 note. The temporary manifest is the lifecycle authority; the Markdown note is its durable, self-contained rendering.

## Classification and metadata

Use one task type appropriate to the selected mode:

- Coding: `bug`, `feature`, `refactor`, `maintenance`, `migration`, `evaluation`, `experiment`, or `tooling`.
- Session documentation: `research`, `design`, `diagnosis`, `decision`, `experiment-plan`, `review`, or `documentation`.

Task type describes the work. Mode describes the record shape. For coding, implementation class independently states whether the verified public contract was preserved.

Every v3 note uses these metadata lines. Use the manifest values exactly and render absent optional values as shown:

```markdown
- Record format: `3`
- Record ID: `<generated RCP ID>`
- Mode: `<coding-progress or session-documentation>`
- Task type: `<mode-compatible task type>`
- Task slug: `<lowercase-hyphenated slug>`
- Implementation class: `<function-fix or fresh-implementation>`
- Date: `<YYYY-MM-DD>`
- Project: <repository or project>
- Priority: `<critical, high, normal, low, or unspecified>`
- Owner: <owner or Unassigned>
- Components: <comma-separated values or None>
- Labels: <comma-separated values or None>
- Status category: `<to-do, in-progress, or done>`
- Status: `<proposed, in-progress, validating, blocked, done, or canceled>`
- Resolution: `<resolution or unresolved>`
- Created at: `<UTC RFC 3339 timestamp>`
- Started at: `<UTC RFC 3339 timestamp or unavailable>`
- Updated at: `<UTC RFC 3339 timestamp>`
- Completed at: `<UTC RFC 3339 timestamp or Not applicable>`
- Due date: `<YYYY-MM-DD or Not applicable>`
- Evidence state: `<verified, mixed, or unverified>`
- Validation state: `<pass, partial, fail, not-run, or not-applicable>`
```

Omit `Implementation class` in session-documentation mode. All other lines are required.

The tool generates `RCP-<UTC timestamp>-<8 lowercase hex>` record IDs. It records creation and update times automatically. Pass `--started-at unavailable` for a late capture whose actual start is unknown; never substitute the record creation time for an unknown historical start.

## Status and resolution

The status categories are derived:

- `proposed` is `to-do`.
- `in-progress`, `validating`, and `blocked` are `in-progress`.
- `done` and `canceled` are `done`.

Allowed transitions are:

```text
proposed -> in-progress | canceled
in-progress -> validating | blocked | done | canceled
validating -> in-progress | blocked | done | canceled
blocked -> in-progress | canceled
```

Nonterminal statuses use `unresolved`. A `done` record requires `completed`, `partial-handoff`, `superseded`, `duplicate`, or `wont-do`. A `canceled` record requires `canceled`, `superseded`, `duplicate`, or `wont-do`.

Use `blocked` only with a concrete blocker reason. Use `in-progress` plus `unresolved` for continuing partial work; use `done` plus `partial-handoff` only when the current scope is intentionally closed incomplete.

## Lifecycle and relationships

The note must include `## Lifecycle`, state the current blocker or `None`, and reproduce each manifest event on one table row:

```markdown
| ID | At | Action | From | To | Actor | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | <timestamp> | created | none | in-progress | record-tool | record created |
```

Do not invent lifecycle IDs. The tool assigns `L1`, `L2`, and so on. Reproduce each local relationship in the same section:

```markdown
| ID | Type | Target |
| --- | --- | --- |
| R1 | blocked-by | <record ID or repository-local path> |
```

Supported relationship types are `parent`, `blocks`, `blocked-by`, `relates-to`, `supersedes`, and `duplicates`. Targets are locators, not verified proof that another record exists.

Use:

```text
python3 <skill-path>/scripts/record_tool.py transition --manifest <manifest> --to <status> --actor <actor> --reason <reason> [--resolution <resolution>]
python3 <skill-path>/scripts/record_tool.py add-link --manifest <manifest> --type <type> --target <record-id-or-path>
```

`finish` may perform the final transition. After finalization, use `resume --manifest <manifest> --actor <actor> --reason <reason>` before adding evidence or changing lifecycle state. Resume preserves prior events, returns the record to `in-progress`, clears terminal fields and final Git evidence, and requires a fresh finish and validation.

`finish --refresh` recaptures custody only. It deliberately preserves lifecycle timestamps and does not add another event.

## Local discovery

List records without changing them:

```text
python3 <skill-path>/scripts/record_tool.py list --root <progress-directory> [--mode <mode>] [--task-type <type>] [--status <status>] [--resolution <resolution>] [--priority <priority>] [--component <component>] [--label <label>] [--since <YYYY-MM-DD>] [--until <YYYY-MM-DD>] [--json]
```

Legacy notes remain visible with unavailable values for fields their format did not define.
