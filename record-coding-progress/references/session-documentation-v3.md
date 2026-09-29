# Session-documentation record v3

Use this mode to preserve research, analysis, design, diagnosis, a decision, a review, or an experiment plan without a material code change. First read [lifecycle-v3.md](lifecycle-v3.md), then apply this session-specific contract.

## Start and capture

Create a temporary manifest with the appropriate session task type:

```text
python3 <skill-path>/scripts/record_tool.py start --record-format 3 --mode session-documentation --task-type <type> --task-slug <slug> --record-date <YYYY-MM-DD> --repo <project-path> --output <temporary-manifest>
```

Add only sources actually used. For a local artifact, use `add-source --file <path>` to bind its SHA-256. Session mode rejects checks, task paths, record paths, and Git evidence.

Finalize with the status of the documented work, not a vague description of the prose:

```text
python3 <skill-path>/scripts/record_tool.py finish --manifest <temporary-manifest> --status <status> --evidence-state <state> --actor <actor> --reason <reason> [--resolution <resolution>]
```

Session validation state is always `not-applicable`.

## Required record shape

In addition to the v3 lifecycle metadata and `## Lifecycle`, use:

1. `## Outcome`
2. `## Context and Scope`
3. `## Lifecycle`
4. `## Findings and Decisions`
5. `## Evidence Ledger`
6. `## Evidence Boundary`
7. `## Next Steps`

Add `## Technical Design or Experimental Plan` only when algorithms, equations, interfaces, schemas, protocols, milestones, metrics, or gates are central.

Lead with the durable conclusion or decision. Organize findings by topic, classify every material item as `verified`, `user-stated`, `inferred`, or `proposed`, and cite its `E*` source. Do not imply code changes, experiments, or inspections that did not occur. Omit implementation inventories, command-validation sections, diffs, commits, branches, and worktree state.

Run:

```text
python3 <skill-path>/scripts/record_tool.py validate --manifest <temporary-manifest> --note <note-path>
```

Fix every validation error before reporting completion. Commit mode never applies to this mode.
