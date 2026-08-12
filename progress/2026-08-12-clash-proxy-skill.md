# Add Clash Proxy Skill

- Record format: `2`
- Mode: `coding-progress`
- Implementation class: `fresh-implementation`
- Date: `2026-08-12`
- Project: `/home/mzhyui/git/skills`
- Status: `completed`
- Evidence state: `mixed`

## Outcome

Added a standalone Clash proxy-management skill with local and iKuuu profile guidance, port-invariant enforcement, node switching, safe subscription replacement, metadata for Codex and Claude Code, and focused unit tests [E2-E4, V1-V2]. The controller has not been used to modify a live Clash configuration in this delivery.

## Task and Scope

The current-session request was to conclude and commit current changes in separated commits, one for clash-proxy [E1]. The task-owned delivery is a new skill rather than a verified correction to an existing public contract: `clash-proxy/` is new relative to the commit baseline. The implementation therefore records fresh implementation status.

In scope: `clash-proxy/`, its Codex and Claude metadata, the focused tests, the skill listing additions in `CLAUDE.md` and `README.md`, and this record. Out of scope: changing live proxy profiles, nodes, services, subscription files, or credentials.

## Implementation

### Plan and Starting Status

The requested result was a separately committable Clash proxy skill [E1]. At the recorded baseline, no `clash-proxy/` paths existed in Git; the current worktree contained the untracked skill files captured as pre-existing at late manifest start. The skill was completed as a fresh implementation rather than relabeling an unverified earlier contract [E1].

### Core Functions and Result

| Path | Core function or role | Result |
| --- | --- | --- |
| `clash-proxy/SKILL.md` | User-facing profile, node, update, recovery, and port-invariant contract | Documents local and iKuuu operation, mandated ports, validation, fallback, and credential handling [E2]. |
| `clash-proxy/scripts/clash_ctl.py` | Controller CLI | Implements profile reload, node selection, port patching, safe iKuuu subscription replacement, health checks, listing, and reload actions [E3]. |
| `clash-proxy/agents/openai.yaml`, `clash-proxy/claude/agent.md` | Platform metadata | Exposes the skill to Codex and Claude Code. |
| `clash-proxy/references/profiles.md` | Profile reference | Records profile node and port information. |
| `clash-proxy/tests/test_clash_ctl.py` | Focused local test coverage | Covers port repair, percent-encoded Unicode group paths, and preservation of the existing config when download fails [E4]. |
| `CLAUDE.md`, `README.md` | Repository skill listing | Lists the new skill among independently installable skills. |

## Interface and Behavior Changes

The repository now provides `clash-proxy`, invoked through `python scripts/clash_ctl.py <command>` after installation. Its mutating commands target the machine's Clash configuration only when explicitly run. `update-ikuuu` downloads to a temporary sibling file and replaces the existing profile only after the download command succeeds. The controller enforces `mixed-port: 7890`, `external-controller: 127.0.0.1:33541`, and `allow-lan: true` on patched configurations [E2-E3].

## Validation

### Test Result

Pass: repository suites, controller-specific tests, syntax compilation, and whitespace checks completed successfully [V1-V2]. The tests use temporary files and mocks; no live proxy was switched or health-checked.

### V1 - pass

```text
python3 -m unittest discover -s tests -p 'test_*.py' && python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py' && python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py' && python3 -m unittest discover -s clash-proxy/tests -p 'test_*.py' && python3 -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py clash-proxy/scripts/clash_ctl.py && git diff --check
```

Observed: 13 installer tests, 9 math-auditor tests, 17 record-tool tests, and 3 clash-proxy tests passed; listed files compiled and git diff --check passed.

### V2 - pass

```text
python3 clash-proxy/scripts/clash_ctl.py --help
```

Observed: The controller displayed its command help successfully.

## Evidence Ledger

- E1 [user-stated]: Current-session request to conclude and commit current changes in separated commits, one for clash-proxy. Supports the commit scope and fresh-delivery classification.
- E2 [verified]: `clash-proxy/SKILL.md`, SHA-256 `3b988a72635a22a541f512e057fbc9cdd865c2400c269ffc7dc696fa301a732c`. Supports the documented command, profile, invariant, recovery, and credential contract.
- E3 [verified]: `clash-proxy/scripts/clash_ctl.py`, SHA-256 `00d67002aeaf5e58d268bc5e71548e448584821995613a5ec801129c7038c43b`. Supports the controller implementation and safe download replacement behavior.
- E4 [verified]: `clash-proxy/tests/test_clash_ctl.py`, SHA-256 `e670754b8e320b22b4a4475be59b37835ed896b39be8b3cf4e9638449d662ebd`. Supports the focused local test coverage.
- V1 [verified]: Repository test, compilation, and whitespace-check command. Supports the observed passing validation results.
- V2 [verified]: Controller help command. Supports the CLI parser availability result.

## Git Custody

- Branch: `main`
- Baseline HEAD: `f42d0755ccde99f9bc3fbb7087c483ab37c28004`
- Final HEAD: `f42d0755ccde99f9bc3fbb7087c483ab37c28004`
- History relation: `same`
- Commits since baseline: None.
- Explicit implementation scopes: `CLAUDE.md`, `README.md`, and `clash-proxy`.
- Task-owned changed paths: `CLAUDE.md`, `README.md`, `clash-proxy/SKILL.md`, `clash-proxy/agents/openai.yaml`, `clash-proxy/claude/agent.md`, `clash-proxy/references/profiles.md`, `clash-proxy/scripts/clash_ctl.py`, `clash-proxy/tests/test_clash_ctl.py`, and `progress/2026-08-12-clash-proxy-skill.md`.
- Pre-existing paths at late manifest capture: `CLAUDE.md`, `README.md`, `clash-proxy/SKILL.md`, `clash-proxy/agents/openai.yaml`, `clash-proxy/claude/agent.md`, `clash-proxy/references/profiles.md`, `clash-proxy/scripts/clash_ctl.py`, and `clash-proxy/tests/test_clash_ctl.py`.
- Pre-existing overlap: `CLAUDE.md`, `README.md`, `clash-proxy/SKILL.md`, `clash-proxy/agents/openai.yaml`, `clash-proxy/claude/agent.md`, `clash-proxy/references/profiles.md`, `clash-proxy/scripts/clash_ctl.py`, and `clash-proxy/tests/test_clash_ctl.py`. The manifest began after implementation work, so this is a late-capture overlap rather than evidence of unrelated ownership.
- Outside-scope changed paths: None.
- Record path: `progress/2026-08-12-clash-proxy-skill.md`.
- Scoped diff: `files=2; insertions=2; deletions=1; binary_files=0; untracked_files=6`.

## Evidence Boundary

This work establishes repository instructions, controller code, metadata, focused mock/file tests, CLI parsing, and port-patching behavior on test files. It does not establish that either profile exists or is healthy on this machine, that a subscription URL is valid, that a live API accepts reloads, that actual node switching succeeds, or that `references/profiles.md` remains current.

## Next Steps

None.
