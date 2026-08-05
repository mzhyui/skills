# Assignment and dispatch

Before placement, refresh every candidate that could change the decision.
Verify:

- GPU type, count, free memory, and conflicting workers;
- storage bytes and inodes;
- dataset, checkpoint, report, and persistent-root access;
- intended interpreter, checkout compatibility, packages, and caches;
- existing assignment, completion, immutable binding, and resume semantics;
- task identity, placement constraints, retention, and shutdown guards.

Record a blocked assignment when any required preflight fails. Otherwise record
the assignment before dispatch with target, task and cell IDs, GPU IDs,
constraints, previous target, and `preflight_verdict=passed`.

Dispatch only when requested. Require a passed preflight, then immediately
record post-dispatch evidence. A launch is `queued`, `dispatched`, or `running`,
never `complete`.
