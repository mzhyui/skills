# Status snapshot schema v2

`status_ledger.py record` accepts v1 input for compatibility, normalizes it,
and writes a v2 snapshot. Existing v1 files remain immutable and readable.

## Required shape

```json
{
  "schema_version": 2,
  "event_type": "status_check",
  "observed_at": "2026-07-29T10:00:00+08:00",
  "machine": {
    "machine_id": "example",
    "kind": "autodl",
    "endpoint": "configured endpoint",
    "reachability": "reachable",
    "hostname": "worker"
  },
  "scope": {
    "scope_id": "task-scope",
    "cell_ids": [],
    "task_ids": ["task-1"]
  },
  "freshness": {
    "direct_check": "fresh",
    "fallback_used": false
  },
  "status": {
    "verdict": "running",
    "summary": "The worker is live; no terminal artifact exists.",
    "completion_evidence": false,
    "workflow_adapter": "generic"
  },
  "evidence_boundary": "Liveness only; completion is not established.",
  "evidence": [{
    "kind": "process",
    "source": "bounded direct probe",
    "observed_at": "2026-07-29T10:00:00+08:00",
    "authority": "liveness",
    "channel": "direct",
    "summary": "One relevant worker is active."
  }],
  "related_records": [],
  "notes": []
}
```

Enums are enforced for event, verdict, reachability, direct-check state,
authority, channel, assignment action, preflight verdict, and dispatch state.
Fallback requires a distinct machine and `shared_custody_verified=true`.

`complete` requires completion evidence and a completion-capable adapter.
Generic `running` requires a reachable endpoint plus direct-liveness and
progress evidence; fallback-only nonterminal evidence is `unknown`.
Selective V11 additionally requires `workflow_state=ready_to_bind`,
`assets_retained=true`, `retained_assets_verified=true`,
`labels_opened=false`, and `matrix_bound=false`.

Assignment, reassignment, and dispatch events also require `assignment` with
the matching action, target, task/cell IDs, resources, constraints, preflight
verdict, and dispatch state.

Use `latest --format compact` for routine context, `verify --mode tail` after
recording, and `verify --mode full` for complete historical integrity audits.
