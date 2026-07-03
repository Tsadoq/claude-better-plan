#!/usr/bin/env python3
"""SessionEnd hook for the deep-plan skill.

Removes the ending session's state file and sandbox directory. Also runs a
defensive sweep of any /tmp/deep-plan-* dirs and state-dir JSONs older than
7 days (crash-killed sessions never fire SessionEnd, so aged leftovers are
pruned here).

Never blocks session end. All exceptions are swallowed silently.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path


def _runtime_dir() -> Path:
    raw = os.environ.get("XDG_STATE_HOME")
    base = Path(raw) if raw else Path.home() / ".local" / "state"
    return base / "deep-plan"


STATE_DIR = _runtime_dir() / "state"
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

        for f in STATE_DIR.glob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass


if __name__ == "__main__":
    main()
