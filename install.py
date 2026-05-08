#!/usr/bin/env python3
"""Installer for the deep-plan skill.

Creates symlinks under ~/.claude/ that point at the source-of-truth
artifacts in ~/gits/plan-modes/deep-plan/. Ensures runtime directories
exist. Idempotent: safe to re-run any time the source files change.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"

SKILL_SRC = SOURCE_ROOT / "skills" / "deep-plan"
SKILL_LINK = CLAUDE_DIR / "skills" / "deep-plan"

AGENT_SRC_DIR = SOURCE_ROOT / "agents"
AGENT_LINK_DIR = CLAUDE_DIR / "agents"

RUNTIME_DIR = CLAUDE_DIR / "deep-plan"
STATE_DIR = RUNTIME_DIR / "state"
PROJECTS_JSON = RUNTIME_DIR / "projects.json"
HOOK_ERROR_LOG = RUNTIME_DIR / "hook-errors.log"

EXEC_PATHS = [
    SKILL_SRC / "hooks" / "guard_writes.py",
    SKILL_SRC / "hooks" / "cleanup.py",
    SKILL_SRC / "scripts" / "setup_session.py",
    SKILL_SRC / "scripts" / "resolve_slug.py",
    SKILL_SRC / "scripts" / "finalize_plan.py",
]


def info(msg: str) -> None:
    print(f"[deep-plan/install] {msg}")


def ensure_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        info(f"created {path}")
    else:
        info(f"exists  {path}")


def ensure_file(path: Path, content: str = "") -> None:
    if not path.exists():
        path.write_text(content)
        info(f"created {path}")


def ensure_symlink(link: Path, target: Path) -> None:
    if not target.exists():
        info(f"ERROR: source missing: {target}")
        sys.exit(1)
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        current = Path(os.readlink(link))
        if current == target:
            info(f"ok      {link} -> {target}")
            return
        link.unlink()
        info(f"replace {link} (was {current} -> now {target})")
    elif link.exists():
        info(f"ERROR: {link} exists and is not a symlink, refusing to replace")
        sys.exit(1)
    link.symlink_to(target)
    info(f"linked  {link} -> {target}")


def ensure_executable(path: Path) -> None:
    if not path.exists():
        info(f"ERROR: missing executable {path}")
        sys.exit(1)
    mode = path.stat().st_mode
    needed = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    if mode != needed:
        path.chmod(needed)
        info(f"chmod   {path}")
    else:
        info(f"exec    {path}")


def main() -> None:
    info(f"source: {SOURCE_ROOT}")
    info(f"target: {CLAUDE_DIR}")

    ensure_dir(RUNTIME_DIR)
    ensure_dir(STATE_DIR)
    ensure_file(PROJECTS_JSON, "{}\n")
    ensure_file(HOOK_ERROR_LOG, "")

    for p in EXEC_PATHS:
        ensure_executable(p)

    ensure_symlink(SKILL_LINK, SKILL_SRC)

    for agent_file in sorted(AGENT_SRC_DIR.glob("dp-*.md")):
        ensure_symlink(AGENT_LINK_DIR / agent_file.name, agent_file)

    info("done. restart Claude Code to pick up the new skill and agents.")


if __name__ == "__main__":
    main()
