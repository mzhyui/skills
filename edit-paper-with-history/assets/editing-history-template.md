# Paper Editing History

- Status: completed
- Started at: `<YYYY-MM-DDTHH:MM:SS+HH:MM>`
- Completed at: `<YYYY-MM-DDTHH:MM:SS+HH:MM>`
- Editing objective: `<concise objective>`
- History record: `editing_history/<timestamp>--<scope>.md`

## Confirmed scope

| Source path | Confirmed locator | Original lines | Final lines | Explicit exclusions |
| --- | --- | ---: | ---: | --- |
| `<repository-relative path>` | `<section title, heading interval, line interval, or quoted anchors>` | `<start-end>` | `<start-end>` | `<excluded adjacent content>` |

## Original text record

### `<source path>` — `<confirmed locator>`

- Summary: `<concise abstract of the original passage>`
- Core idea: `<central claim, argument, or purpose>`
- Preserved constraints: `<qualifications, evidence boundaries, terminology, citations, or notation>`

## Acknowledged wording exceptions

Write `None` if no exception was used. Otherwise, record each exception:

- Exact wording: `<approved wording>`
- Justification: `<why this wording is necessary>`
- Location: `<repository-relative path and standalone Limitations section locator>`
- User acknowledgement: `<exact acknowledgement and conversation locator or timestamp, if available>`
- Scope expansion: `<revised confirmed scope and user confirmation, or not applicable>`

## Exact changes

### Change 1 — `<short factual label>`

- Source path: `<repository-relative path>`
- Confirmed scope: `<locator>`
- Change type: `<addition | deletion | replacement | move>`
- Original lines: `<start-end or not applicable>`
- Final lines: `<start-end or not applicable>`
- Reason: `<concise factual reason>`

Before:

```text
<exact original passage, or (empty)>
```

After:

```text
<exact final passage, or (empty)>
```

## Verification

- [ ] The record covers every session-owned change in the confirmed scope.
- [ ] Exact before-and-after passages agree with the baseline-to-final diff.
- [ ] No session-owned change falls outside the confirmed scope.
- [ ] The edited prose follows the skill's mandatory editing discipline, and any acknowledged wording exceptions are recorded above.
- [ ] All paths are repository-relative.
- [ ] Both timestamps include timezones.
- [ ] No hashes or Git custody claims are included.
