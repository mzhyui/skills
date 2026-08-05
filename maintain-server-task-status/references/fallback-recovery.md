# Fallback, recovery, and shutdown

## Shared-storage fallback

Use a fallback host only when:

1. The assigned endpoint is unavailable or stale.
2. Current configuration or a live mount check proves shared custody.
3. The fallback resolves the exact assigned artifact root.
4. The workflow validator can inspect it without rewriting.

One verified shared mount may inspect multiple exact roots in one aggregate
probe. Do not reconnect to each unavailable endpoint or repeat identical
shared-storage scans when endpoint liveness cannot change the completion gate.

Record the direct error, fallback host and time, custody evidence, task root,
artifact timestamps, and unavailable-host process state as `unknown`.

## Recovery and shutdown

- Resolve the exact target and immutable evidence boundary before mutation.
- Preserve complete checkpoint families and retained assets; verify existence,
  size, and SHA-256 before shutdown or removal.
- Do not treat refusal, shutdown, or an interrupted queue as completion.
- Do not resume a terminal, opened, bound, or structurally incompatible root.
- Record recovery or shutdown as its own event, then collect a fresh
  post-action status.
- Never open labels, bind matrices, delete evidence, or relax frozen gates as
  part of a status check.
