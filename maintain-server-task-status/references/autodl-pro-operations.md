# AutoDL Pro instance-operation SOP

Use this procedure for authorized AutoDL Pro creation and shutdown, or its
read-only steps for account, image, and instance checks. Preserve the requested
region, GPU quantity/specification, image, and post-create action. Authorization
for an earlier test is not permission to create additional instances later.

Official references, checked on 2026-10-23:
- [Common API](https://www.autodl.com/docs/common_api/)
- [Container instance Pro API](https://www.autodl.com/docs/instance_pro_api/)

## 1. Establish connectivity and authentication

The API origin is `https://api.autodl.com`. A successful origin GET establishes
connectivity only. Authenticate with the raw developer token in `Authorization`,
without a `Bearer` prefix. Load it from `AUTODL_TOKEN`, or from
`AUTODL_TOKEN_FILE` (default `~/.config/autodl/token`, mode 0600).
Keep the token outside skills, repositories, command arguments, and records.

Use the bundled helper; no third-party dependencies are needed:

```bash
python <skill-dir>/scripts/autodl_api.py balance
```

Require both HTTP 200 and `response.code == "Success"`. HTTP 200 alone can
contain an API rejection. The common API's balance fields use thousandths of a
yuan. An authenticated balance response does not establish Pro eligibility.
`TORealName` means the account needs personal or company identity verification.
After the user reports verification, reconcile inventory before retrying a
previously rejected creation.

The helper makes one request per invocation, refuses redirects, and redacts
passwords, tokens, secret-bearing commands, and JWT strings. Exit codes are
0 for success, 2 for API rejection, and 3 for local/transport failure.
`--execute` is a mutation guard, not a substitute for user authorization.

## 2. Resolve the image and capture inventory

These are independent read-only calls and may run in parallel:

```bash
python <skill-dir>/scripts/autodl_api.py images
python <skill-dir>/scripts/autodl_api.py instances
```

Both lists are paginated. Inspect `max_page`/`result_total` and use `--page`
before concluding that a name is absent or unique. Match the exact private
image name with `status=finished`; resolve ambiguity before creating anything.
Do not substitute a public image or an unfinished image. Capture existing
instance UUIDs and choose a unique name so an uncertain create result can be
reconciled without duplicate allocation.

Image UUIDs are account-specific. Re-resolve the image for each new operation
rather than reusing a UUID from an earlier lookup.

## 3. Prepare and submit one create request

For the requested 4080(S)-32G 性能型, the documented spec is `v-32g-p`.
Creation is pay-as-you-go. The following tested request uses one GPU, no extra
system-disk expansion, and only `westDC3`. Replace the example image UUID with
the freshly resolved UUID and use a unique instance name.

```json
{
  "data_center_list": ["westDC3"],
  "req_gpu_amount": 1,
  "expand_system_disk_by_gb": 0,
  "gpu_spec_uuid": "v-32g-p",
  "image_uuid": "<resolved-image-uuid>",
  "cuda_v_from": 113,
  "instance_name": "<image-name>-westDC3-test-<unique-timestamp>"
}
```

`cuda_v_from=113` constrains host-driver support to CUDA >= 11.3; it does not
describe the image's installed CUDA version. Choose the workload's required
minimum. Zero disk expansion still includes the default system disk. Omitting
`data_center_list` allows automatic region selection; include only the requested
region when locality matters. Do not add fallback regions after a capacity error
without authorization.

```bash
python <skill-dir>/scripts/autodl_api.py create --request-file <reviewed-request.json> --execute
```

Save the sanitized request, response, observation time, request ID, and returned
instance UUID. A `Success` create receipt proves acceptance, not boot or GPU
readiness. If the response is lost or times out, inspect inventory by unique
name and pre-create UUID set before any retry. Do not automatically repeat
create calls or create a second instance to work around slow image preparation.

## 4. Apply the requested shutdown timing

### Immediate shutdown after creation

When the user asks to create and then shut down, call `power_off` on the newly
returned UUID immediately after create success. Do not add a boot/GPU gate to
this request. Immediate power-off while the instance was still being prepared
worked in the verified westDC3 test; treat future acceptance/state as evidence,
not a universal guarantee that every transitional state permits power-off.

```bash
python <skill-dir>/scripts/autodl_api.py power-off --instance <new-instance-uuid> --execute
python <skill-dir>/scripts/autodl_api.py status --instance <new-instance-uuid>
python <skill-dir>/scripts/autodl_api.py instances
```

Require a confirmed stopped state (`shutdown` in the observed API) and the same
UUID in inventory. A successful power-off POST alone is not shutdown proof.
Retain the instance unless release was separately requested. Retained storage
may remain chargeable.

### Shutdown after boot or GPU verification

Use this path only when runtime verification is requested. Poll status until
`running`, optionally perform the authorized read-only GPU check, then power
off and confirm shutdown. Creating/image-download progress is not boot proof;
even a high progress percentage may persist for many minutes.

```bash
python <skill-dir>/scripts/autodl_api.py status --instance <new-instance-uuid>
python <skill-dir>/scripts/autodl_api.py snapshot --instance <new-instance-uuid>
```

The helper sends GET `instance_uuid` as a URL query parameter. The official
documentation's GET JSON-body example returned `RequestParameterIsWrong` in
live testing. Snapshot responses contain SSH passwords and Jupyter tokens;
the helper redacts them. A runtime SSH probe must obtain credentials privately
in memory and never persist a raw snapshot.

For a long wait, run a persistent watcher under detached `screen` or a service
manager. Use the user's requested polling cadence rather than assuming a
universal interval. A watcher must:

- Bind to one authorized UUID, use a singleton lock, and preserve prior
  observations when replacing another watcher. Process visibility can differ
  across sandbox boundaries; an empty sandbox process listing is insufficient
  evidence that the old watcher exited.
- Write timestamped, redacted status/events and the next scheduled check. Verify
  its detached process, held lock, and first successful provider query before
  reporting it as running independently of the conversation.
- Reconcile current provider state before retrying any uncertain power-off.
  Use a retry cooldown and finite mutation-attempt limit; record failures.
- Keep GPU-check failure distinct from shutdown success. When shutdown after a
  bounded test is authorized, a failed probe must not leave compute running
  indefinitely. Verify the final state and retain the instance.
- Record terminal evidence and exit when stopped. `screen` survives conversation
  termination, but does not restart after the local machine reboots.

Do not use host `shutdown` commands, including `shutdown --help`, as probes.
Use the documented Pro `power_off` API for the explicitly authorized UUID.

## 5. Record the result and its limits

Keep creation acceptance, actual region, boot, GPU availability, power-off
acceptance, confirmed shutdown, and retention separate. Use the assigned region
from snapshot/inventory, not the request alone. Capture direct observation time
and timezone, sanitized receipts, instance UUID, request IDs, and evidence hashes.

Use the skill's schema-v2 status ledger and verify its new tail. Preserve its
existing verdict vocabulary: provider `shutdown` can be recorded as an additional
provider-state field. Do not label a generic scientific workload `complete`
because an infrastructure smoke test passed. If ledger verification fails,
preserve its history and report the mismatch; use a clearly named separate
ledger for this operation rather than silently repairing or bypassing integrity.

## Verified example and boundaries

On 2026-10-23, a request restricted to `westDC3` created a Pro instance with
one `v-32g-p` GPU and a private image. AutoDL assigned
`west-E` / 西北B区. Immediate power-off returned `Success`; both the status
endpoint and inventory confirmed `shutdown`, with the instance retained.

This proves that create-and-immediate-shutdown path for that observed request.
It does not prove boot, GPU runtime, performance, future capacity, or an immutable
mapping from scheduling region to assigned zone. An earlier auto-region request
selected `bj-B1` and remained in image preparation during subsequent checks;
do not turn that observation into a claimed westDC3 boot-speed advantage.
