# Session-documentation record v2

Use this mode when preserving research, analysis, design, diagnosis, a decision, or an experiment plan without a material code change.

## Capture sources

Create a temporary manifest:

```text
python3 <skill-path>/scripts/record_tool.py start --mode session-documentation --repo <project-path> --output <temporary-manifest>
```

Add only sources actually used:

```text
python3 <skill-path>/scripts/record_tool.py add-source --manifest <temporary-manifest> --kind <user|repository|artifact|web> --locator <source>
```

Do not inspect or record Git state merely because the destination is a repository.
For a local source artifact, pass `--file <path>` so the tool computes and binds its SHA-256.

## Required record shape

Use these metadata lines exactly:

```markdown
# <Title>

- Record format: `2`
- Mode: `session-documentation`
- Date: `YYYY-MM-DD`
- Project: <project or `Not applicable`>
- Status: `concluded`, `proposed`, `partial`, or `blocked`
- Evidence state: `verified`, `mixed`, or `unverified`
```

Use these required headings:

1. `## Outcome`
2. `## Context and Scope`
3. `## Findings and Decisions`
4. `## Evidence Ledger`
5. `## Evidence Boundary`
6. `## Next Steps`

Add `## Technical Design or Experimental Plan` only when algorithms, equations, interfaces, schemas, protocols, milestones, metrics, or gates are central.

## Content contract

- Lead with the durable conclusion or decision, not a chat recap.
- Organize findings by topic. Mark each material item `verified`, `user-stated`, `inferred`, or `proposed`, and cite an `E*` source ID.
- Preserve necessary equations, data contracts, alternatives, and rationale without hidden reasoning or large code blocks.
- In the evidence ledger, map each source ID to one class (`verified`, `user-stated`, `inferred`, or `proposed`), its kind, locator, optional hash, and supported conclusion. Record the current user statement as a `user` source when no external artifact was used.
- State what was inspected or demonstrated separately from what remains unimplemented, unrun, or unestablished.
- Omit implementation inventories, diffs, commits, branches, worktree state, and command-validation sections.

Run:

```text
python3 <skill-path>/scripts/record_tool.py validate --manifest <temporary-manifest> --note <record-path>
```

Report the record path and validation outcome. Commit mode never applies to this mode.
