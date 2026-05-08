#!/usr/bin/env python3
"""Phase 0 bootstrap and state mutation for /deep-plan.

Two modes:

1. Bootstrap (initial call):
       setup_session.py --harness-plan-path <PATH> --session-id <ID>
   Resolves project root via `git rev-parse --show-toplevel` (falls back to
   cwd with `no_git=true` sentinel), reads
   $XDG_STATE_HOME/deep-plan/projects.json (default
   ~/.local/state/deep-plan/projects.json) to find the project's plans_dir
   (returns `prompt_for_plans_dir=true` sentinel and four candidate options
   if first time), writes the per-session state file, and creates the
   /tmp/deep-plan-<session_id>/ sandbox.

2. Update (subsequent calls):
       setup_session.py --update key=value --session-id <ID>
   Mutates the state file in place. Permitted keys: plans_dir,
   custom_plan_path, phase, decisions (JSON-encoded list).

Both modes print a JSON blob to stdout describing the resulting state.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HOME = Path.home()


def _runtime_dir() -> Path:
    raw = os.environ.get("XDG_STATE_HOME")
    base = Path(raw) if raw else HOME / ".local" / "state"
    return base / "deep-plan"


RUNTIME_DIR = _runtime_dir()
STATE_DIR = RUNTIME_DIR / "state"
PROJECTS_JSON = RUNTIME_DIR / "projects.json"
HOOK_ERROR_LOG = RUNTIME_DIR / "hook-errors.log"
LEGACY_RUNTIME_DIR = HOME / ".claude" / "deep-plan"


def ensure_runtime_dirs() -> None:
    """Self-bootstrap runtime layout. Replaces the old install.py step.

    Also performs a one-shot migration from ~/.claude/deep-plan/ to the new
    XDG location if the new dir is empty and the legacy dir has content.
    """
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not PROJECTS_JSON.exists():
        PROJECTS_JSON.write_text("{}\n")
    if not HOOK_ERROR_LOG.exists():
        HOOK_ERROR_LOG.touch()
    _maybe_migrate_legacy()


def _maybe_migrate_legacy() -> None:
    if not LEGACY_RUNTIME_DIR.exists() or LEGACY_RUNTIME_DIR == RUNTIME_DIR:
        return
    breadcrumb = RUNTIME_DIR / "MIGRATED.txt"
    if breadcrumb.exists():
        return
    try:
        legacy_projects = LEGACY_RUNTIME_DIR / "projects.json"
        if legacy_projects.exists() and PROJECTS_JSON.read_text().strip() in ("", "{}"):
            PROJECTS_JSON.write_text(legacy_projects.read_text())
        legacy_state = LEGACY_RUNTIME_DIR / "state"
        if legacy_state.is_dir():
            for f in legacy_state.glob("*.json"):
                target = STATE_DIR / f.name
                if not target.exists():
                    target.write_text(f.read_text())
        breadcrumb.write_text(
            f"Migrated from {LEGACY_RUNTIME_DIR} on {utcnow()}.\n"
            "Legacy dir left intact; safe to delete manually.\n"
        )
    except Exception:
        pass

PERMITTED_UPDATE_KEYS = {
    "plans_dir",
    "custom_plan_path",
    "harness_plan_path",
    "phase",
    "decisions",
}


def utcnow() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_project_root(cwd: Path) -> tuple[Path, bool]:
    """Return (project_root, no_git)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            top = result.stdout.strip()
            if top:
                return Path(top).resolve(), False
    except Exception:
        pass
    return cwd.resolve(), True


def load_projects() -> dict[str, dict[str, Any]]:
    if not PROJECTS_JSON.exists():
        return {}
    try:
        data = json.loads(PROJECTS_JSON.read_text() or "{}")
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_projects(data: dict[str, dict[str, Any]]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def candidate_plans_dirs(project_root: Path) -> list[dict[str, str]]:
    name = project_root.name or "project"
    return [
        {
            "label": f"{project_root}/.claude/plans/",
            "path": str(project_root / ".claude" / "plans"),
            "recommended": "true",
        },
        {
            "label": f"{project_root}/plans/",
            "path": str(project_root / "plans"),
            "recommended": "false",
        },
        {
            "label": f"{project_root}/docs/plans/",
            "path": str(project_root / "docs" / "plans"),
            "recommended": "false",
        },
        {
            "label": f"{project_root.parent}/{name}-plans/",
            "path": str(project_root.parent / f"{name}-plans"),
            "recommended": "false",
        },
    ]


def state_file_for(session_id: str) -> Path:
    return STATE_DIR / f"{session_id}.json"


def read_state(session_id: str) -> dict[str, Any]:
    sf = state_file_for(session_id)
    if not sf.exists():
        return {}
    try:
        data = json.loads(sf.read_text())
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def write_state(session_id: str, state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file_for(session_id).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def ensure_sandbox(session_id: str) -> Path:
    sandbox = Path("/tmp") / f"deep-plan-{session_id}"
    sandbox.mkdir(mode=0o700, exist_ok=True)
    try:
        os.chmod(sandbox, 0o700)
    except Exception:
        pass
    return sandbox


def cmd_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    ensure_runtime_dirs()
    cwd = Path.cwd()
    project_root, no_git = detect_project_root(cwd)
    projects = load_projects()
    project_key = str(project_root)

    plans_dir: str | None = None
    prompt_for_plans_dir = True
    record = projects.get(project_key)
    if record and record.get("plans_dir"):
        plans_dir = str(record["plans_dir"])
        prompt_for_plans_dir = False
        record["last_used_at"] = utcnow()
        projects[project_key] = record
        save_projects(projects)

    sandbox = ensure_sandbox(args.session_id)

    state: dict[str, Any] = {
        "session_id": args.session_id,
        "started_at": utcnow(),
        "project_root": project_key,
        "plans_dir": plans_dir,
        "harness_plan_path": str(Path(args.harness_plan_path).resolve()),
        "custom_plan_path": None,
        "sandbox_dir": str(sandbox),
        "phase": "Phase 0",
        "decisions": [],
    }
    write_state(args.session_id, state)

    return {
        **state,
        "sentinels": {
            "no_git": no_git,
            "prompt_for_plans_dir": prompt_for_plans_dir,
        },
        "candidate_plans_dirs": candidate_plans_dirs(project_root),
    }


def cmd_update(args: argparse.Namespace) -> dict[str, Any]:
    ensure_runtime_dirs()
    state = read_state(args.session_id)
    if not state:
        return {"ok": False, "error": f"no state for session_id={args.session_id}"}

    updates: dict[str, Any] = {}
    for kv in args.update:
        if "=" not in kv:
            return {"ok": False, "error": f"malformed update {kv!r}, expected key=value"}
        key, raw_value = kv.split("=", 1)
        if key not in PERMITTED_UPDATE_KEYS:
            return {
                "ok": False,
                "error": f"key {key!r} not permitted; allowed: {sorted(PERMITTED_UPDATE_KEYS)}",
            }
        value: Any = raw_value
        if key == "decisions":
            try:
                value = json.loads(raw_value)
            except Exception as exc:
                return {"ok": False, "error": f"decisions must be JSON: {exc!r}"}
        updates[key] = value

    state.update(updates)
    if "plans_dir" in updates and isinstance(updates["plans_dir"], str):
        plans_dir_path = Path(updates["plans_dir"]).resolve()
        plans_dir_path.mkdir(parents=True, exist_ok=True)
        state["plans_dir"] = str(plans_dir_path)
        projects = load_projects()
        project_key = str(state["project_root"])
        record = projects.get(project_key, {})
        record["plans_dir"] = str(plans_dir_path)
        record["last_used_at"] = utcnow()
        projects[project_key] = record
        save_projects(projects)

    write_state(args.session_id, state)
    return {"ok": True, **state}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="deep-plan session bootstrap and state mutation")
    p.add_argument("--session-id", required=True)
    p.add_argument("--harness-plan-path")
    p.add_argument(
        "--update",
        nargs="*",
        default=[],
        help="key=value pairs (repeatable). Mutually exclusive with --harness-plan-path bootstrap.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.update:
        result = cmd_update(args)
    elif args.harness_plan_path:
        result = cmd_bootstrap(args)
    else:
        print(json.dumps({"ok": False, "error": "provide --harness-plan-path or --update"}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
