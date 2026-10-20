# Paper editing discipline

- Record format: `3`
- Record ID: `RCP-20261020T082407Z-15f35b7b`
- Mode: `session-documentation`
- Task type: `documentation`
- Task slug: `paper-editing-discipline`
- Date: `2026-10-20`
- Project: /home/mzhyui/git/skills
- Priority: `unspecified`
- Owner: Unassigned
- Components: edit-paper-with-history
- Labels: None
- Status category: `done`
- Status: `done`
- Resolution: `completed`
- Created at: `2026-10-20T08:24:07Z`
- Started at: `unavailable`
- Updated at: `2026-10-20T08:24:07Z`
- Completed at: `2026-10-20T08:24:07Z`
- Due date: Not applicable
- Evidence state: `verified`
- Validation state: `not-applicable`

## Outcome

Verified: the paper-editing skill defines mandatory wording discipline, and its history template and Claude guidance support the same requirements (E1–E3).

## Context and Scope

This record documents the existing instruction changes in `edit-paper-with-history`. Their original authoring start time is unavailable. The review covers the skill contract, wording-exception fields, and Claude guidance; it does not evaluate an actual manuscript edit.

## Lifecycle

Current blocker: None.

| ID | At | Action | From | To | Actor | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | 2026-10-20T08:24:07Z | created | none | in-progress | record-tool | record created |
| L2 | 2026-10-20T08:24:07Z | transition | in-progress | done | Codex | Reviewed the editing-discipline instructions and synchronized history template and Claude guidance. |

Relationships: None.

## Findings and Decisions

- Verified: the skill excludes specified dismissive expressions from edited main text, including abstracts. A necessary exception requires exact wording, justification, a standalone Limitations location, and explicit user acknowledgement; scope expansion remains subject to scope confirmation (E1).
- Verified: the instructions require accurate transitions, explicit evidence-supported benefits and conditions, and neutral treatment of unfavorable results. Numerical comparisons, uncertainty, and substantive qualifications must be preserved; unsupported explanations and benefits are prohibited (E1).
- Verified: these rules apply only within the confirmed editing scope. Baselines and exact history retain original wording (E1).
- Verified: the history template captures wording, justification, location, acknowledgement, and scope expansion, and its checklist includes the discipline (E2). Claude guidance explicitly invokes the same requirement (E3).

## Evidence Ledger

| ID | Classification | Source | SHA-256 |
| --- | --- | --- | --- |
| E1 | verified | `edit-paper-with-history/SKILL.md` | `ecda3f8b689b64c37669965169c7ca9798bac7fd1d27360f8d8f9600796454e7` |
| E2 | verified | `edit-paper-with-history/assets/editing-history-template.md` | `1f633ca4c9505916391b3707e1b448692b1d20c384e0bc98c0a8deff57cf06b1` |
| E3 | verified | `edit-paper-with-history/claude/agent.md` | `bd7f2533a6b4fcbbc0a8e9cdbce40e9baf417d4f9b8c9e305db17d0c6874fc95` |

## Evidence Boundary

Verification establishes the content and consistency of the instructions. It does not establish agent compliance, manuscript quality, or scientific validity. No manuscript edits or experiments were performed for this documentation review.

## Next Steps

None required for the documentation closeout. Future manuscript use can assess compliance with these instructions.
