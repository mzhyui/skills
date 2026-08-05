#!/usr/bin/env python3
"""Install a single skill from the mzhyui/skills repo into Claude Code.

This is the Claude-side counterpart of Codex's built-in `$skill-installer`. It
fetches ONE self-contained skill directory (the "skill scope"), validates that
it contains `SKILL.md`, and installs it at the Claude user level so Claude Code
picks it up. A skill exposes a `/name` slash command automatically, so the only
extra piece is the subagent:

  ~/.claude/skills/<name>/   the skill contract (SKILL.md + scripts/references)
  ~/.claude/agents/<name>.md the skill's subagent definition (from claude/agent.md)

Sources accepted:
  https://github.com/mzhyui/skills/tree/main/anchor-plans
  anchor-plans                       (defaults to github.com/mzhyui/skills @ main)
  mzhyui/skills/anchor-plans
  /absolute/or/relative/path/to/anchor-plans   (install straight from a local dir)

The `agents/` (Codex-only) and `claude/` (installer source) folders are not
copied into the installed skill; everything else ships as-is.

Stdlib only. Install under ~/.claude by default.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.request import urlopen

DEFAULT_REPO = "mzhyui/skills"
DEFAULT_REF = "main"

# Directories that belong to a sibling platform or to the installer itself and
# must not be copied into the installed Claude skill.
EXCLUDE_DIRS = ("agents", "claude", "__pycache__")

_GITHUB_HTTPS_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?"
    r"(?:/tree/(?P<ref>[^/]+))?(?:/(?P<path>.*))?$"
)
_GITHUB_SSH_RE = re.compile(
    r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?"
    r"(?:/tree/(?P<ref>[^/]+))?(?:/(?P<path>.*))?$"
)


@dataclasses.dataclass(frozen=True)
class SkillSource:
    """A parsed reference to a skill directory inside a GitHub repo."""

    owner: str
    repo: str
    ref: str
    path: str
    name: str

    def clone_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}.git"


@dataclasses.dataclass(frozen=True)
class InstallPlan:
    """Where each piece of a skill lands under a destination home."""

    skill_dir: Path
    agent_file: Optional[Path]

    def paths(self) -> Tuple[Path, ...]:
        return tuple(p for p in (self.skill_dir, self.agent_file) if p is not None)


def parse_source(
    source: str,
    default_repo: str = DEFAULT_REPO,
    default_ref: str = DEFAULT_REF,
) -> SkillSource:
    """Parse a URL or bare skill name into a SkillSource.

    Raises ValueError when the source has no resolvable skill path.
    """
    s = source.strip().strip("/")
    for regex in (_GITHUB_HTTPS_RE, _GITHUB_SSH_RE):
        match = regex.match(s)
        if match:
            path = (match.group("path") or "").strip("/")
            if not path:
                raise ValueError(f"no skill path in source: {source!r}")
            return SkillSource(
                owner=match.group("owner"),
                repo=match.group("repo"),
                ref=match.group("ref") or default_ref,
                path=path,
                name=Path(path).name,
            )
    if "/" in s:
        parts = s.split("/")
        if len(parts) < 3:
            raise ValueError(
                f"{source!r} is neither a GitHub URL nor a bare skill name; "
                "use URL form https://github.com/<owner>/<repo>/tree/<ref>/<path>"
            )
        owner, repo = parts[0], parts[1]
        path = "/".join(parts[2:])
        return SkillSource(owner, repo, default_ref, path, Path(path).name)
    owner, repo = default_repo.split("/", 1)
    return SkillSource(owner, repo, default_ref, s, s)


def _fetch_via_git(src: SkillSource, workdir: Path) -> Path:
    clone = workdir / "clone"
    _run(
        ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
         "--branch", src.ref, src.clone_url(), str(clone)]
    )
    _run(["git", "-C", str(clone), "sparse-checkout", "set", src.path])
    return clone / src.path


def _fetch_via_api(src: SkillSource, workdir: Path) -> Path:
    """Fallback: download the skill directory through the GitHub REST API."""
    url = f"https://api.github.com/repos/{src.owner}/{src.repo}/git/trees/{src.ref}?recursive=1"
    with urlopen(url) as resp:
        tree = json.load(resp)
    dest_root = workdir / "tree"
    prefix = src.path + "/"
    for entry in tree.get("tree", []):
        path = entry.get("path", "")
        if not path.startswith(prefix):
            continue
        if entry.get("type") != "blob":
            continue
        raw = f"https://raw.githubusercontent.com/{src.owner}/{src.repo}/{src.ref}/{path}"
        target = dest_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(raw) as resp:
            target.write_bytes(resp.read())
    return dest_root / src.path


def fetch_skill(src: SkillSource, workdir: Path) -> Path:
    """Fetch the skill directory for a source into a fresh working directory."""
    skill_dir = _fetch_via_git(src, workdir)
    if not (skill_dir / "SKILL.md").is_file():
        skill_dir = _fetch_via_api(src, workdir)
    _require_skill(skill_dir, src.name)
    return skill_dir


def plan_install(
    name: str, skill_dir: Path, dest: Path, force: bool = False
) -> InstallPlan:
    """Compute where a skill would be installed under `dest`. Never writes."""
    _require_skill(skill_dir, name)
    skill_target = dest / "skills" / name
    agent_source = skill_dir / "claude" / "agent.md"
    if skill_target.exists() and not force:
        raise FileExistsError(
            f"skill already installed at {skill_target} (use --force to overwrite)"
        )
    return InstallPlan(
        skill_dir=skill_target,
        agent_file=(dest / "agents" / f"{name}.md") if agent_source.is_file() else None,
    )


def install_from_dir(
    name: str, skill_dir: Path, dest: Path, force: bool = False
) -> InstallPlan:
    """Copy a local skill dir into the Claude layout under `dest`."""
    plan = plan_install(name, skill_dir, dest, force=force)
    plan.skill_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        skill_dir,
        plan.skill_dir,
        ignore=shutil.ignore_patterns(*EXCLUDE_DIRS),
        dirs_exist_ok=force,
    )
    _copy_component(skill_dir / "claude" / "agent.md", plan.agent_file)
    return plan


def _copy_component(source: Path, target: Optional[Path]) -> None:
    if source is None or target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _require_skill(skill_dir: Path, name: str) -> None:
    if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
        raise FileNotFoundError(
            f"no skill found at {skill_dir!s} (expected a directory with SKILL.md)"
        )
    if not name:
        raise ValueError("skill name must not be empty")


def _run(argv: List[str]) -> None:
    import subprocess

    subprocess.run(argv, check=True)


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install a single skill from mzhyui/skills into Claude Code.",
    )
    parser.add_argument(
        "source",
        help="skill to install: a GitHub URL, a bare skill name, or a local skill dir",
    )
    parser.add_argument(
        "--ref", default=None, help="git ref to fetch (default: main, or from URL)"
    )
    parser.add_argument(
        "--dest",
        default="~/.claude",
        help="Claude home to install into (default: ~/.claude)",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"owner/repo used for bare skill names (default: {DEFAULT_REPO})",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing install")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    dest = Path(args.dest).expanduser()
    source = args.source

    # A local directory is installed directly, no network fetch needed.
    if Path(source).exists():
        skill_dir = Path(source)
        name = skill_dir.name
        workdir: Optional[Path] = None
    else:
        src = parse_source(source, default_repo=args.repo)
        if args.ref:
            src = SkillSource(src.owner, src.repo, args.ref, src.path, src.name)
        # The fetched skill lives inside `workdir`; keep that alive until the
        # install (from worker function to dest) has copied it out.
        workdir = Path(tempfile.mkdtemp(prefix="install-skill-"))
        skill_dir = fetch_skill(src, workdir)
        name = src.name

    try:
        if args.dry_run:
            plan = plan_install(name, skill_dir, dest, force=args.force)
            print("Dry run — would install:")
            for path in plan.paths():
                print(f"  {path}")
            return 0

        plan = install_from_dir(name, skill_dir, dest, force=args.force)
        print(f"Installed skill '{name}':")
        for path in plan.paths():
            print(f"  {path}")
        print("Restart Claude Code (or start a new session) to pick up the skill.")
        return 0
    finally:
        if workdir is not None:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
