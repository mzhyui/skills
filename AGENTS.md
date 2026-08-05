# Repository Guidelines

## Project Structure & Module Organization

This repository contains independently usable skills for both **Codex and Claude Code**:

- `anchor-plans/` — scope-anchoring workflow for complex plans.
- `edit-paper-with-history/` — scoped paper-editing workflow and templates.
- `paper-math-auditor/` — mathematical-audit instructions, scripts, references, and tests.
- `maintain-server-task-status/` — server/task-status instructions, probes, and schemas.
- `record-coding-progress/` — durable progress documentation workflow, tool, references, and tests.

Each skill keeps its main contract in `SKILL.md`, Codex metadata in `agents/openai.yaml`, and its Claude Code subagent definition in `claude/agent.md` (the installed skill auto-exposes the `/name` slash command). Keep new skill-specific code, references, tests, and assets inside that skill directory. The only repo-root code is the cross-cutting `scripts/install_skill.py` installer and its `tests/`.

## Build, Test, and Development Commands

There is no compilation or packaging step. From the repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'          # installer
python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py'
python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py'
python3 -m py_compile paper-math-auditor/scripts/sympy_audit.py maintain-server-task-status/scripts/status_ledger.py maintain-server-task-status/scripts/status_probe.py record-coding-progress/scripts/record_tool.py scripts/install_skill.py
```

The `unittest` commands run the test suites; `py_compile` catches syntax errors. Use `python3 <script> --help` to inspect an interface before invoking it. Keep dependencies in the surrounding environment; do not vendor caches or virtual environments.

Installing a skill into Claude Code: `python3 scripts/install_skill.py <name-or-url> [--dest DIR] [--force] [--dry-run]` (see `README.md`).

## Coding Style & Naming Conventions

Use Python 3, four-space indentation, type hints, small functions, and concise docstrings. Follow `snake_case` for Python files, functions, and variables; use `CamelCase` for classes. Skill directories use lowercase kebab-case, and entrypoints remain exactly `SKILL.md`. Preserve existing JSON schemas and status/verdict vocabulary. Markdown should use clear imperative instructions and `$...$` for inline mathematical notation.

## Testing Guidelines

Add focused `unittest` cases under the relevant skill’s `tests/` directory, with filenames matching `test_*.py` and descriptive `test_<behavior>` methods. Cover accepted inputs, rejection paths, boundary conditions, and safety-sensitive behavior. Run both discovery commands before submitting changes.

## Commit & Pull Request Guidelines

This checkout has no accessible commit history, so no local convention can be inferred. Use short, imperative subjects such as `Add domain-boundary audit tests`; keep each commit focused. Pull requests should explain the affected skill and behavior, list validation commands and results, note schema or instruction changes, and link an issue when one exists. Include screenshots only when documenting a user-visible rendering change.

## Security & Configuration

The math auditor intentionally uses a restricted parser; never replace it with `eval` or an unrestricted expression parser. Treat server-status tooling as read-only unless explicitly authorized. Do not commit credentials, host secrets, generated logs, caches, or sensitive status artifacts.
