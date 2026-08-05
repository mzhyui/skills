---
name: maintain-server-task-status
description: Capture and maintain fresh, durable, evidence-bound server and task status for local machines, server 223, AutoDL, and other compute hosts. Use for server, worker, job, queue, task-cell, assignment, dispatch, recovery, resume, shutdown, or distributed-progress requests. Probe current evidence, distinguish liveness from completion, use shared-storage fallback only with verified custody, and update the repository status ledger.
---

# Maintain Server Task Status

Keep status requests read-only unless the user authorizes a mutation.

## Fast path

1. Resolve the exact requested scope and decisive workflow gate. For matrix
   completion, list assigned task IDs first; do not start with a fleet scan.
2. Read only the matching prior summary:

   ```bash
   python <skill-dir>/scripts/status_ledger.py latest --format compact \
     --repo-root <repo> --machine-id <machine> --scope-id <scope>
   ```

3. Run each distinct official status command once, in parallel where safe. For
   distributed selective V11, pass every status JSON and assigned task ID to
   one aggregate probe:

   ```bash
   python <skill-dir>/scripts/status_probe.py selective-v11 \
     --status-json <cell-a-status.json> \
     --status-json <cell-b-status.json> \
     --task-id <assigned-task-a> --task-id <assigned-task-b>
   ```

   Default `--audit-mode auto` evaluates the workflow gate first. If any
   assigned task is absent, nonterminal, unretained, opened, or bound, it
   returns the blocker without hashing retained assets.
4. Probe only endpoints whose live state can change the verdict, such as a
   nonterminal or unknown task. Use the bounded host helper; do not probe every
   configured host for an artifact-completion question:

   ```bash
   python <skill-dir>/scripts/status_probe.py host \
     --machine-id <machine> --target <local-or-ssh-target> \
     --checkout <checkout> --python <python> --process-pattern <pattern>
   ```

5. When every selective V11 task is structurally ready, rerun the aggregate
   probe with each assigned `--task-root`. Auto mode then performs the required
   full size/SHA-256 audit. Use `--audit-mode metadata` only for a quick
   existence/size check; it never proves completion. Use `--audit-mode full`
   for pre-open, shutdown, suspected drift, or an explicit integrity audit.
6. Decide from the strongest evidence: validated terminal artifacts, final
   manifests, progress, liveness, then history. Without a valid terminal
   contract, report `running`, `blocked`, or `unknown`, never `complete`.
7. Record one schema-v2 snapshot for the requested aggregate scope unless
   machine-specific states materially differ, then verify the new chain tip:

   ```bash
   python <skill-dir>/scripts/status_ledger.py record \
     --repo-root <repo> --input <snapshot.json>
   python <skill-dir>/scripts/status_ledger.py verify \
     --mode tail --repo-root <repo>
   ```

8. Report verdict, decisive gate, observation time and timezone, direct versus
   fallback evidence, evidence boundary, snapshot path, and SHA-256.

## Conditional guidance

- Read [references/status-probes.md](references/status-probes.md) only when
  choosing or interpreting routine probes.
- Read [references/fallback-recovery.md](references/fallback-recovery.md) only
  for unavailable endpoints, shared-storage fallback, recovery, or shutdown.
- Read [references/assignment-dispatch.md](references/assignment-dispatch.md)
  only for assignment, reassignment, dispatch, or resume.
- Read [references/snapshot-schema.md](references/snapshot-schema.md) only when
  manually constructing or debugging a snapshot.

## Invariants

- Processes, sessions, GPUs, logs, partial checkpoints, and connection refusal
  never prove completion.
- Fallback proves artifact state only; it never proves unavailable-host
  liveness.
- Generic `running` requires fresh direct liveness plus progress. Fallback-only
  nonterminal artifacts are `unknown` unless a registered workflow contract
  authoritatively defines a running state.
- Selective V11 completion requires every assigned task to be
  `ready_to_bind`, retained, and independently size/SHA-256 audited. Keep
  `labels_opened` and `matrix_bound` separate and false for pre-open readiness.
- Do not rehash ready tasks after another assigned task already makes the
  requested matrix gate impossible. Auto mode must report the blocker and
  `audit_performed=skipped_blocked_gate`; prior audits remain historical
  custody evidence, not a fresh full audit.
- Metadata-only validation must report `ready_pending_full_audit` and cannot
  set completion evidence or `retained_assets_verified=true`.
- Preserve frozen task identities, seeds, evidence roots, scientific gates,
  histories, and unrelated worktree changes.
- Exclude credentials and secret-bearing commands from probes and records.
- Run `verify --mode full` for audits, suspected drift, index repair, or before
  relying on historical integrity; routine checks use `--mode tail`.
