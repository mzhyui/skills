# Session documentation template

Use every heading below for session-documentation mode. This template records a research, design, analysis, or decision discussion that did not produce a material code change. Do not add code, Git, diff, commit, worktree, command-validation, or implementation-asset sections.

~~~
# <Concise session topic>

- Date: <YYYY-MM-DD>
- Project: <repository, project, or Not applicable>
- Status: <concluded | proposed | partial | blocked>

## Purpose

- Request: <What the user asked to preserve.>
- Decision or objective: <The durable conclusion, design objective, or question addressed.>

## Context and Scope

- Starting context: <Grounded starting point from the discussion or source artifacts.>
- Constraints: <Resource, research, compatibility, or user constraints.>
- In scope: <What the documentation covers.>
- Out of scope: <Explicit exclusions.>

## Findings and Decisions

<Organize verified findings, decisions, alternatives, and rationale by topic. State which items are proposals when not yet implemented or tested.>

## Technical Design or Experimental Plan

<Preserve necessary algorithms, equations, data contracts, interfaces, reward definitions, evaluation procedures, milestones, and acceptance gates. Use concise pseudocode or schemas only when necessary.>

## Evaluation and Evidence Boundary

- Evaluation plan: <Metrics, baselines, statistical methods, or review criteria.>
- Current evidence: <What was inspected, verified, or demonstrated.>
- Not yet established: <Claims that require implementation, experiments, external validation, or a future decision.>

## Next Steps

1. <First actionable next step.>
2. <Second actionable next step.>
3. <Optional gate or dependency.>

## Sources Used

- <User-provided document, repository artifact, verified source, or None.>
~~~

Keep the document self-contained and skimmable. Preserve durable design content, but do not include a transcript, hidden reasoning, tool traces, code-change assets, or Git boilerplate.
