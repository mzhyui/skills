# skills

Independently usable Codex **and** Claude Code skills. Each skill is a
self-contained directory installed "by skill scope" — not the whole repo.

| Skill | Purpose |
|---|---|
| `anchor-plans` | Scope-anchoring interview before finalizing a complex plan |
| `edit-paper-with-history` | Scoped paper edits with an auditable, exact change history |
| `paper-math-auditor` | Read-only adversarial audit of paper mathematics |
| `maintain-server-task-status` | Fresh, evidence-bound server/task status |
| `record-coding-progress` | Durable progress / session documentation |
| `clash-proxy` | Manage Clash proxy profiles, nodes, and port invariants |
| `scientific-figure` | Create, reference-match, and revise scientific figures |

## Install a single skill

**Codex** (built-in installer, no extra tooling):

```
$skill-installer install https://github.com/mzhyui/skills/tree/main/anchor-plans
```

**Claude Code** (via this repo's installer script):

```bash
# from a clone of this repo
python3 scripts/install_skill.py anchor-plans

# or directly from a GitHub URL
python3 scripts/install_skill.py https://github.com/mzhyui/skills/tree/main/anchor-plans
```

Each skill installs into `~/.claude/` as a user-level skill
(`skills/<name>/`, which auto-exposes the `/name` slash command) plus its
subagent (`agents/<name>.md`). Add `--dest <dir>` to target a different Claude
home, `--force` to overwrite, and `--dry-run` to preview. Restart Claude Code
after installing.

## Develop

```bash
python3 -m unittest discover -s tests -p 'test_*.py'                 # installer
python3 -m unittest discover -s paper-math-auditor/tests -p 'test_*.py'
python3 -m unittest discover -s record-coding-progress/tests -p 'test_*.py'
python3 -m unittest discover -s scientific-figure/tests -p 'test_*.py'
```

Each skill's Claude subagent definition lives in `claude/agent.md`; Codex
metadata stays in `agents/openai.yaml`. The `/name` slash command is provided
automatically by the installed skill. See `AGENTS.md` for the full
conventions.

## TODO
- TODO 2026-10-10 git.V.34571: record-coding-progress should a progress reader to catch the important information
