#!/usr/bin/env python3
"""Stop hook for the deep-plan skill.

Removes the per-session state file and sandbox directory. Also runs a
defensive sweep of any /tmp/deep-plan-* dirs older than 7 days.

Never blocks session end. All exceptions are swallowed silently.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "deep-plan" / "state"
TMP = Path("/tmp")
SANDBOX_PREFIX = "deep-plan-"
TTL_SECONDS = 7 * 86400


def main() -> None:
    try:
        try:
            payload = json.load(sys.stdin)
        except Exception:
            payload = {}

        session_id = str(payload.get("session_id", ""))
        if session_id:
            state_file = STATE_DIR / f"{session_id}.json"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                except Exception:
                    state = {}
                sandbox_raw = state.get("sandbox_dir", "")
                if sandbox_raw:
                    sandbox = Path(sandbox_raw)
                    if sandbox.is_dir() and sandbox.name.startswith(SANDBOX_PREFIX):
                        shutil.rmtree(sandbox, ignore_errors=True)
                state_file.unlink(missing_ok=True)

        cutoff = time.time() - TTL_SECONDS
        for d in TMP.glob(f"{SANDBOX_PREFIX}*"):
            if d.is_dir():
                try:
                    if d.stat().st_mtime < cutoff:
                        shutil.rmtree(d, ignore_errors=True)
                except Exception:
                    pass
    except Exception:
        pass


if __name__ == "__main__":
    main()
