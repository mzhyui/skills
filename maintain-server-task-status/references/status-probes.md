# Routine status probes

Use a timezone-aware observation time. Treat reachability, processes, sessions,
GPUs, storage, and host inventory as instantaneous.

## Direct observation

Prefer one bounded probe containing:

- `date -Is`, hostname, uptime, checkout revision, and intended interpreter;
- lightweight CUDA and GPU inventory;
- narrowly matched processes or sessions;
- checkout filesystem byte and inode headroom;
- the workflow's official status command;
- exact final indexes, manifests, hashes, and artifact timestamps.

Use `scripts/status_probe.py host` for the generic host packet. Avoid broad
process dumps, environment output, unbounded searches, and commands that change
access state. A blocked `nvidia-smi` is one observation, not proof that no GPU
exists.

## Probe budget

- Start with the artifact or workflow gate that can decide the request.
- Run independent status commands once and in parallel where safe.
- Probe liveness only for nonterminal or unknown assignments whose live state
  affects the answer. GPU and process checks add no completion authority to a
  retained terminal task.
- For shared storage, use one currently verified fallback mount to inspect all
  exact roots it holds. Do not repeat equivalent fallback reads per unavailable
  endpoint.
- Record one aggregate snapshot for one aggregate question. Add a separate
  machine snapshot only when its live state is independently material.

## Selective V11 audit modes

`status_probe.py selective-v11` accepts repeated `--status-json`, `--task-id`,
and `--task-root` arguments.

- `auto` is the routine default. It merges the official statuses, fails closed
  on duplicate active task states, and evaluates all requested task gates
  before reading retained assets. A blocked gate skips hashing. If every task
  is ready, auto performs a full audit and may establish completion.
- `metadata` checks retained-manifest structure plus listed file existence and
  exact size. It reports `ready_pending_full_audit`, never completion.
- `full` reads and SHA-256-verifies every listed asset even when another gate is
  blocked. Reserve it for explicit integrity audits, pre-open, suspected drift,
  and shutdown or cleanup gates.

When a task is absent from every supplied official status, treat it as a
completion blocker. The 84-task placeholder rows in separate selective roots
must not be summed; pass only the exact assigned task IDs.

## Verdict vocabulary

- `running`: fresh progress plus relevant direct live-worker evidence, or a
  registered adapter's authoritative running state.
- `queued`: assignment exists but execution has not started.
- `blocked`: a named gate or dependency prevents progress.
- `failed`: terminal workflow evidence records failure.
- `complete`: a registered workflow adapter validates its final contract.
- `unknown`: current evidence establishes none of the above.

Evidence authority is ordered as `completion`, `progress`, `liveness`,
`context`. Qualify pre-open and non-claim-bearing states explicitly.
When the assigned endpoint is unavailable, fallback-only nonterminal progress
is `unknown`; fallback process visibility cannot supply the missing liveness.
