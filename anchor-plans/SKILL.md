---
name: anchor-plans
description: Enforce a scope-anchoring interview before finalizing a non-trivial execution plan. Use in Plan Mode or when the user requests a roadmap, strategy, workflow, implementation plan, research or experiment plan, project or migration plan, execution schedule, resource allocation, milestones, or a plan with multiple viable technical paths. Do not use for simple explanations, direct factual answers, translations, small local fixes whose scope is obvious, or open-ended brainstorming that does not request an execution plan.
---

# Anchor Plans

Do not immediately produce a final plan for a complex or materially ambiguous task. Lock the objective, constraints, and execution contract first, then produce an execution-ready plan.

## Build a scope ledger

Extract relevant facts from the user's request, conversation, applicable instructions, and available project context before asking questions. Inspect discoverable repository or environment facts with read-only tools when practical.

Track each decision as `locked`, `unknown`, or `conflicting`:

- Objective: desired outcome, success criteria, minimum acceptable result, and dominant priority.
- Constraints: deadline, resources, existing environment, compatibility, forbidden approaches, budget, and other hard limits.
- Execution: executor, plan granularity, methodology preference, deliverables, and risk tolerance.

Treat an explicit statement that a constraint or preference does not exist as locked. Do not ask the user for facts that can be discovered safely. Do not silently infer a choice that could materially change scope, architecture, cost, claims, sequencing, or acceptance criteria.

## Run the interview state machine

Use this state sequence:

`PLAN_REQUEST -> CONTEXT_SCAN -> OBJECTIVE_LOCKED -> CONSTRAINTS_LOCKED -> EXECUTION_LOCKED -> PLAN_GENERATION`

For a complex request where all three dimensions begin unresolved, conduct at least three interaction rounds. Focus each round on one dimension:

1. Objective round: resolve the primary outcome, measurable success, minimum acceptable result, and priority among competing outcomes.
2. Constraints round: resolve the hard limits that bound feasible solutions, especially time, resources, environment, compatibility, prohibited approaches, and budget.
3. Execution round: resolve who will execute, the needed granularity, preferred methodology, required deliverables, and acceptable risk.

Count a dimension already locked by the request or verified context as satisfied and skip its round. Never invent redundant questions merely to reach three interactions. If one answer locks several dimensions, update all of them. If material ambiguity or conflict remains after the three dimensions have been covered, continue with narrowly targeted follow-ups.

Use the Plan Mode question tool when available. Otherwise ask one concise question at a time. Keep each round decision-oriented:

- Ask only questions whose answers can change the plan.
- Prefer one primary decision per question.
- Offer concrete, mutually exclusive choices when the decision space is known.
- Recommend an option when evidence supports one and state its consequence briefly.
- Avoid generic prompts such as "Anything else?" or exhaustive questionnaires.

## Decide when planning is anchored

Generate the final plan only when all of the following are true:

- State the primary outcome in one sentence.
- Make success and the minimum acceptable result verifiable.
- Identify in-scope and out-of-scope boundaries.
- Identify hard constraints, dependencies, and prohibited approaches, or record that none apply.
- Identify the executor, required detail level, deliverables, and acceptable risk.
- Resolve every open choice that could materially change the plan's architecture, order, resources, or validation.

Record harmless or reversible uncertainties as explicit assumptions instead of prolonging the interview. Continue questioning when an unresolved answer would produce a meaningfully different plan.

If the user supplies a complete brief, generate the plan without a redundant interview. If the user explicitly requests a best-effort plan without questions, honor that instruction, make conservative assumptions visible, and identify the decisions that could require replanning.

## Produce the final plan

Use these sections in this order:

1. Objective
2. Success criteria
3. Assumptions
4. Scope
5. Out of scope
6. Architecture / methodology
7. Milestones and implementation steps
8. Required resources and dependencies
9. Risks and mitigations
10. Validation criteria
11. Next actions

Keep each section proportional to the task. Make milestones ordered, assign ownership when known, state dependencies, and attach a verification or exit condition to each milestone. Distinguish confirmed facts from assumptions. Do not present unresolved material decisions as settled.
