# Progress record template

Use every heading below. Replace angle-bracket placeholders and remove instructional comments. Preserve `None`, `Not applicable`, or `Not run: <reason>` when that is the truthful value.

```markdown
# <Concise task title>

- Date: `<YYYY-MM-DD>`
- Repository: `<repository-root or name>`
- Status: `<completed | partial | blocked>`

## Task and Target

- Task: <What the user requested.>
- Target: <The intended behavior, artifact, component, or acceptance condition.>

## Task Context

- Starting state: <Relevant behavior or implementation before this task.>
- Constraints: <Repository rules, compatibility requirements, user constraints, and safety boundaries.>
- Decisions and assumptions: <Material task-level choices and assumptions.>
- Out of scope: <Explicit exclusions.>

## Implementation Guidelines

<Summarize the design rules and repository conventions that governed the implementation.>

## Execution Process

1. <Factual implementation step.>
2. <Factual implementation step.>
3. <Factual verification or integration step.>

## Core Code and Functions

| Path | Symbol or section | Change | Role in the result |
|---|---|---|---|
| `<relative/path.py>` | `<function_or_class>` | <Concise behavioral change.> | <Why this is core.> |

Do not paste a large diff. Use a short code excerpt only when the contract cannot be described precisely without it.

## Input and Output Constraint Shifts

| Surface | Before | After | Compatibility or failure behavior |
|---|---|---|---|
| <CLI/API/schema/file/runtime surface> | <Previous constraint.> | <New constraint.> | <Compatibility, validation, fallback, or error behavior.> |

If no user-visible or machine-readable contract changed, state: `No input or output contract changed.`

## Outcome

- Result: <Direct outcome or verdict.>
- Deliverables: <Created or changed artifacts.>
- Limitations or unresolved items: <Remaining gaps, or None.>
- Evidence boundary: <What the work proves and what it does not prove.>

## Validation

| Command or check | Result | Interpretation |
|---|---|---|
| `<exact command>` | `<passed, failed, partial, or not run>` | <Counts, relevant failure, and scope.> |

## Git Information

- Branch: `<branch or unavailable>`
- Baseline HEAD: `<full or short hash, or unavailable>`
- Final HEAD: `<full or short hash, or unavailable>`
- Task commits: `<hash and subject, None, or unavailable>`
- Task-owned paths: `<paths or best-supported scoped list>`
- Scoped diff summary: `<diff stat or concise summary>`
- Pre-existing worktree changes: `<paths, None, or unavailable>`
- Remaining worktree status: `<clean, concise status, or unavailable>`
- Ownership caveats: `<overlap or uncertainty, or None>`
```

Keep the note concise enough to scan while preserving exact operational and validation facts needed for handoff.
