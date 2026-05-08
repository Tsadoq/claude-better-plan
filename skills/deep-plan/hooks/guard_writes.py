#!/usr/bin/env python3
"""PreToolUse hook for the deep-plan skill.

Blocks Write/Edit/NotebookEdit calls outside the four allowed paths
(custom plan file, harness plan file, sandbox dir, session state dir),
and matches Bash commands against a regex of write side-effect patterns
unless the command literal contains the sandbox path.

Fail-open on any internal error: the hook prints nothing, exits 0, and
appends the exception to ~/.claude/deep-plan/hook-errors.log. Read the
log to debug; an empty log means the hook is healthy.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import NoReturn

STATE_DIR = Path.home() / ".claude" / "deep-plan" / "state"
ALLOWED_STATE_PATH_PREFIX = STATE_DIR
ERROR_LOG = Path.home() / ".claude" / "deep-plan" / "hook-errors.log"

WRITEY_BASH = re.compile(
    r"(>>?[^&]|"
    r"\btee\b|"
    r"\bmkdir\b|\btouch\b|\brm\b|"
    r"\bcp\b|\bmv\b|"
    r"\bsed\s+-i\b|"
    r"python[0-9.]*\s+-c\s+.*open\([^)]*['\"]w['\"]|"
    r"\bgit\s+(add|commit|push|reset|checkout\s+--))"
)


def deny(reason: str) -> NoReturn:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def allow() -> NoReturn:
    sys.exit(0)


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        log_error(exc)
        allow()

    try:
        session_id = str(payload.get("session_id", ""))
        tool = str(payload.get("tool_name", ""))
        args = payload.get("tool_input", {}) or {}

        state_file = STATE_DIR / f"{session_id}.json"
        if not state_file.exists():
            allow()

        state = json.loads(state_file.read_text())
        plan_paths: set[str] = set()
        for key in ("harness_plan_path", "custom_plan_path"):
            value = state.get(key)
            if value:
                plan_paths.add(str(Path(value).resolve()))

        sandbox_raw = state.get("sandbox_dir")
        sandbox = Path(sandbox_raw).resolve() if sandbox_raw else None

        if tool in ("Write", "Edit", "NotebookEdit"):
            file_path_str = args.get("file_path", "")
            if not file_path_str:
                allow()
            target = Path(file_path_str).resolve()
            if str(target) in plan_paths:
                allow()
            if sandbox is not None and (target == sandbox or is_under(target, sandbox)):
                allow()
            if is_under(target, ALLOWED_STATE_PATH_PREFIX):
                allow()
            deny(
                "deep-plan: writes only allowed to the canonical plan file, the "
                "harness plan mirror, the per-session sandbox, or the session "
                f"state dir. Got {target}. Move the write into the sandbox or "
                "skip the verification."
            )

        if tool == "Bash":
            cmd = str(args.get("command", ""))
            if sandbox is not None and str(sandbox) in cmd:
                allow()
            if WRITEY_BASH.search(cmd):
                deny(
                    "deep-plan: Bash side-effect patterns (>, >>, tee, mkdir, "
                    "rm, cp, mv, sed -i, python -c '...open(\"...\", \"w\")', "
                    "git add/commit/push/reset, git checkout --) are blocked "
                    f"outside the sandbox ({sandbox}). Move the side effect "
                    "into the sandbox or use Edit on the plan file."
                )
            allow()

        allow()
    except SystemExit:
        raise
    except Exception as exc:
        log_error(exc)
        allow()


def log_error(exc: BaseException) -> None:
    try:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a") as f:
            f.write(json.dumps({"error": repr(exc)}) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
