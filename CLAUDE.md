# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A collection of **independently usable skills for both Codex and Claude Code**, each a self-contained directory. There is no application, no build, and no shared runtime — each skill is a standalone prompt/instruction package that agents load by name.

Skills: `anchor-plans`, `edit-paper-with-history`, `paper-math-auditor`, `maintain-server-task-status`, `record-coding-progress`, `clash-proxy`.

`AGENTS.md` at the repo root is the authoritative style/process contract — read it and follow it for any skill work.

## Dual-platform layout

Every skill is self-contained and installed "by skill scope" (never the whole repo as a plugin). Two platforms read the same skill:

- **Codex** reads `SKILL.md` + `agents/openai.yaml`. Built-in `$skill-installer install https://github.com/mzhyui/skills/tree/main/<name>` installs it directly — no repo changes needed.
- **Claude Code** reads `SKILL.md` plus the per-skill `claude/agent.md` (its subagent). The `/name` slash command is auto-exposed by the installed skill, so no command file is needed. `scripts/install_skill.py` places both into `~/.claude/`:
  ```bash
  python3 scripts/install_skill.py anchor-plans
  python3 scripts/install_skill.py https://github.com/mzhyui/skills/tree/main/anchor-plans
  ```
  Installer flags: `--dest <dir>`, `--force`, `--dry-run`. It installs to `~/.claude/skills/<name>/` and `~/.claude/agents/<name>.md`, excluding the Codex-only `agents/` and the installer-source `claude/` dirs.

## Common skill layout

Every skill keeps its main contract in `SKILL.md` (frontmatter `name` / `description` + imperative instructions). Per-skill extras, kept inside that skill's directory:

- `agents/openai.yaml` — Codex display name, short description, default prompt, `allow_implicit_invocation` policy.
- `claude/agent.md` — Claude subagent definition (frontmatter; preloads the skill via `skills:`).
- `scripts/*.py` — helper tooling (audit, ledger, probe, record utilities).
- `references/*.md` — templates, schemas, protocols the `SKILL.md` points at.
- `tests/test_*.py` — `unittest` suites (only `paper-math-auditor` and `record-coding-progress` have them).
- `assets/` — non-code templates.

Keep all new skill-specific code, references, tests, and assets inside the owning skill's directory. The only repo-root code is the cross-cutting `scripts/install_skill.py` and its `tests/`.

## Commands

No compilation or packaging step.

```bash
# Run all test suites
python3 -m unittest discover -s tests -p 'test_*.py'          # installer
python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py'
python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py'

# Syntax-check the helper scripts
python3 -m py_compile \
  paper-math-auditor/scripts/sympy_audit.py \
  maintain-server-task-status/scripts/status_ledger.py \
  maintain-server-task-status/scripts/status_probe.py \
  record-coding-progress/scripts/record_tool.py

# Run one test method (tests dirs have no __init__.py, so run from inside the dir)
cd paper-math-auditor/tests && python3 -m unittest test_sympy_audit.SympyAuditTests.test_derivative_is_checked_independently

# Inspect a script's interface before invoking it
python3 <script> --help
```

Run both `unittest` discovery commands before submitting changes. Keep dependencies from the surrounding environment; do not vendor caches or virtual environments.

## Architecture notes

- Scripts are standalone Python 3 CLIs (type-hinted, small functions, concise docstrings). The three status scripts (`status_ledger.py`, `status_probe.py`) coordinate: `status_ledger.py` reads/writes the repository status ledger; `status_probe.py` aggregates distributed status probes. `sympy_audit.py` is a restricted symbolic-audit tool. `record_tool.py` writes progress notes.
- Skills intentionally share vocabulary. Preserve existing JSON schemas and the established status/verdict terminology — do not rename across skills.
- Status/progress skills are **read-only by default**; mutations require explicit authorization. The math auditor uses a restricted parser — never replace it with `eval` or an unrestricted expression parser.
- Do not commit credentials, host secrets, generated logs, caches, or sensitive status artifacts (note the `__pycache__/` dirs already present under some skills).
