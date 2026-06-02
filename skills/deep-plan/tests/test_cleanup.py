"""Tests for the cleanup.py Stop hook: per-session teardown + 7-day TTL sweep.

Everything is redirected into throwaway tmp dirs; the real /tmp and the real
state dir are never touched.

Runnable two ways:
    python3 skills/deep-plan/tests/test_cleanup.py
    python3 -m pytest skills/deep-plan/tests/test_cleanup.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HOOKS = Path(__file__).resolve().parent.parent / "hooks"


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, HOOKS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cleanup = _load("cleanup")


def _run_main(payload: dict[str, Any]) -> None:
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cleanup.main()
    finally:
        sys.stdin = old_stdin


def test_session_teardown_and_ttl_sweep() -> None:
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        tmp = base / "tmp"
        state_dir = base / "state"
        tmp.mkdir()
        state_dir.mkdir()

        sid = "cleanuptest"
        sandbox = tmp / f"deep-plan-{sid}"
        sandbox.mkdir()
        (sandbox / "scratch.txt").write_text("x")
        state_file = state_dir / f"{sid}.json"
        state_file.write_text(json.dumps({"sandbox_dir": str(sandbox)}))

        old_dir = tmp / "deep-plan-old"
        fresh_dir = tmp / "deep-plan-fresh"
        old_dir.mkdir()
        fresh_dir.mkdir()
        eight_days_ago = time.time() - 8 * 86400
        os.utime(old_dir, (eight_days_ago, eight_days_ago))

        # Point the module's module-level paths at the sandbox.
        orig_state, orig_tmp = cleanup.STATE_DIR, cleanup.TMP
        cleanup.STATE_DIR = state_dir
        cleanup.TMP = tmp
        try:
            _run_main({"session_id": sid})
        finally:
            cleanup.STATE_DIR, cleanup.TMP = orig_state, orig_tmp

        assert not state_file.exists(), "session state file should be removed"
        assert not sandbox.exists(), "session sandbox should be removed"
        assert not old_dir.exists(), "stale (>7d) sandbox should be swept"
        assert fresh_dir.exists(), "fresh (<7d) sandbox should be spared"


def test_missing_session_is_harmless() -> None:
    # No session_id, empty payload: must not raise.
    orig_state, orig_tmp = cleanup.STATE_DIR, cleanup.TMP
    with tempfile.TemporaryDirectory() as d:
        cleanup.STATE_DIR = Path(d) / "state"
        cleanup.TMP = Path(d) / "tmp"
        cleanup.TMP.mkdir()
        try:
            _run_main({})
        finally:
            cleanup.STATE_DIR, cleanup.TMP = orig_state, orig_tmp


if __name__ == "__main__":
    import traceback

    failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception:  # noqa: BLE001
                failed += 1
                print(f"FAIL {_name}")
                traceback.print_exc()
    sys.exit(1 if failed else 0)
