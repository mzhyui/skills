# Add delivery classification to Record Coding Progress

- Record format: `2`
- Mode: `coding-progress`
- Implementation class: `fresh-implementation`
- Date: `2026-08-10`
- Project: `/home/mzhyui/git/skills`
- Status: `completed`
- Evidence state: `mixed`

## Outcome

Implemented automatic coding-record classification and synchronized the active installed skill. Each coding-progress manifest now declares either `function-fix` or `fresh-implementation`; the validator requires the matching record shape. The result is bounded to the skill workflow and its tests [E1, E3-E5, V1-V2].

## Task and Scope

The request was to distinguish function fixes from fresh implementations, preserve the current contract for fixes, require plan and starting-status detail for fresh implementations, and update the installed skill [E1].

Plan source: the current user request [E1]. The pre-task coding-progress route had one general implementation handoff and no delivery classification [E2]. Original status: no implementation class was captured in a coding manifest, and no conditional record shape was validated.

In scope: the Record Coding Progress instructions, Codex metadata, Claude agent prompt, v2 coding reference, evidence tool, focused tests, and this progress note. The task did not alter session-documentation mode, commit-mode behavior, the manifest schema version, or existing unclassified v2 manifests.

## Implementation

### Plan and Starting Status

The implementation adds an automatic, evidence-bound classification within coding-progress mode. A current-contract defect correction is `function-fix`; a new, planned, initial, contract-changing, or contract-uncertain delivery is `fresh-implementation`. The skill directs the agent to infer this from the task without asking the user, and to conservatively use `fresh-implementation` when a preserved contract cannot be verified [E1, E3].

### Core Functions and Result

| Path | Core function or role | Result |
| --- | --- | --- |
| `record-coding-progress/SKILL.md` | Routing and evidence-bound classification rules | Adds automatic classification, a conservative ambiguity rule, and the plan-source requirement for fresh work [E3]. |
| `record-coding-progress/references/coding-progress-v2.md` | v2 coding-record shape | Adds `Implementation class`, conditional implementation subsections, and `### Test Result` [E3]. |
| `record-coding-progress/scripts/record_tool.py` | `start` and `validate` | Requires `--implementation-kind` for new coding manifests, persists it, and validates matching metadata, implementation headings, and test-result heading [E4]. |
| `record-coding-progress/tests/test_record_tool.py` | Record-tool coverage | Updates coding starts and covers a valid fresh record, missing classification rejection, and missing fresh-implementation heading rejection [E5]. |
| `record-coding-progress/agents/openai.yaml`, `record-coding-progress/claude/agent.md` | Invocation prompts | Reflect the automatic classification behavior. |

The updated repository copies of `SKILL.md`, `agents/openai.yaml`, `references/coding-progress-v2.md`, and `scripts/record_tool.py` were copied to `/home/mzhyui/.codex/skills/record-coding-progress/` [V2]. The installed directory intentionally does not receive repository-only tests or the Claude installer source directory.

## Validation

### Test Result

Pass: all repository test suites, the focused record-tool suite, syntax compilation, diff whitespace check, and installed-file parity check completed successfully [V1-V2].

### V1 - pass

```text
python3 -m unittest discover -s tests -p 'test_*.py' && python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py' && python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py' && python3 -m unittest discover -s clash-proxy/tests -p 'test_*.py' && python3 -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py clash-proxy/scripts/clash_ctl.py && git diff --check
```

Observed: 13 installer tests, 9 math-auditor tests, 17 record-tool tests, and 3 clash-proxy tests passed; listed files compiled and git diff --check passed.

### V2 - pass

```text
cmp -s record-coding-progress/SKILL.md /home/mzhyui/.codex/skills/record-coding-progress/SKILL.md && cmp -s record-coding-progress/agents/openai.yaml /home/mzhyui/.codex/skills/record-coding-progress/agents/openai.yaml && cmp -s record-coding-progress/references/coding-progress-v2.md /home/mzhyui/.codex/skills/record-coding-progress/references/coding-progress-v2.md && cmp -s record-coding-progress/scripts/record_tool.py /home/mzhyui/.codex/skills/record-coding-progress/scripts/record_tool.py && python3 /home/mzhyui/.codex/skills/record-coding-progress/scripts/record_tool.py start --help >/dev/null
```

Observed: Installed SKILL.md, Codex metadata, coding reference, and record tool match the repository copies; the installed tool accepted --help.

## Evidence Ledger

- E1 [user-stated]: Current-session request to distinguish function fixes from fresh implementations and update the installed skill. Supports the requested feature and installation scope.
- E2 [verified]: record-coding-progress/SKILL.md before this task, inspected in the current session. Supports the original one-shape coding-record status.
- E3 [verified]: `record-coding-progress/SKILL.md`, SHA-256 `6d8523677c532bb244b45d0da9b8553461c1a4ae1e95d202ef642d8ea1f199fe`. Supports the final routing and record-content contract.
- E4 [verified]: `record-coding-progress/scripts/record_tool.py`, SHA-256 `a662651235499ecff38a3453944bbc78ac577fee64064eb66a8f1271b64aa10f`. Supports the manifest and validator behavior.
- E5 [verified]: `record-coding-progress/tests/test_record_tool.py`, SHA-256 `8830c468f0f90d21df9bb9488ac7c26b1c109fe0d2d9352011ad5dbdf43428e6`. Supports the focused coverage added for the new behavior.
- V1 [verified]: repository test, compilation, and whitespace-check command. Supports the observed passing validation results.
- V2 [verified]: installed-file parity and help command. Supports the installation synchronization result.

## Git Custody

- Branch: `main`
- Baseline HEAD: `b649a0ebfe2f8edb000ea2ed3de622cf01d42a80`
- Final HEAD: `b649a0ebfe2f8edb000ea2ed3de622cf01d42a80`
- History relation: `same`
- Commits since baseline: None.
- Explicit implementation scope: `record-coding-progress`.
- Task-owned changed paths: `record-coding-progress/SKILL.md`, `record-coding-progress/agents/openai.yaml`, `record-coding-progress/claude/agent.md`, `record-coding-progress/references/coding-progress-v2.md`, `record-coding-progress/scripts/__pycache__/record_tool.cpython-312.pyc`, `record-coding-progress/scripts/record_tool.py`, `record-coding-progress/tests/test_record_tool.py`, and `progress/2026-08-10-record-coding-progress-delivery-classification.md`.
- Pre-existing paths at late manifest capture: `CLAUDE.md`, `README.md`, `clash-proxy/SKILL.md`, `clash-proxy/agents/openai.yaml`, `clash-proxy/claude/agent.md`, `clash-proxy/references/profiles.md`, `clash-proxy/scripts/clash_ctl.py`, `clash-proxy/tests/test_clash_ctl.py`, `progress/2026-08-10-record-coding-progress-delivery-classification.md`, `record-coding-progress/SKILL.md`, `record-coding-progress/agents/openai.yaml`, `record-coding-progress/claude/agent.md`, `record-coding-progress/references/coding-progress-v2.md`, `record-coding-progress/scripts/__pycache__/record_tool.cpython-312.pyc`, `record-coding-progress/scripts/record_tool.py`, and `record-coding-progress/tests/test_record_tool.py`.
- Pre-existing overlap: `progress/2026-08-10-record-coding-progress-delivery-classification.md`, `record-coding-progress/SKILL.md`, `record-coding-progress/agents/openai.yaml`, `record-coding-progress/claude/agent.md`, `record-coding-progress/references/coding-progress-v2.md`, `record-coding-progress/scripts/__pycache__/record_tool.cpython-312.pyc`, `record-coding-progress/scripts/record_tool.py`, and `record-coding-progress/tests/test_record_tool.py`. The manifest began after implementation work, so this is a late-capture overlap rather than evidence of unrelated ownership.
- Outside-scope changed paths: `CLAUDE.md`, `README.md`, `clash-proxy/SKILL.md`, `clash-proxy/agents/openai.yaml`, `clash-proxy/claude/agent.md`, `clash-proxy/references/profiles.md`, `clash-proxy/scripts/clash_ctl.py`, and `clash-proxy/tests/test_clash_ctl.py`.
- Record path: `progress/2026-08-10-record-coding-progress-delivery-classification.md`.
- Scoped diff: `files=7; insertions=238; deletions=12; binary_files=1; untracked_files=0`.

## Evidence Boundary

This work establishes the updated workflow instructions, CLI capture, validator shape checks, focused automated coverage, parity of the copied installed files, and removal of the tracked generated record-tool bytecode cache. It does not prove that every future agent will classify a semantically ambiguous task correctly or that a user-stated plan is independently verified.

## Next Steps

None.
