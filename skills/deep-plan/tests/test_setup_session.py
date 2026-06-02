"""Tests for setup_session.py state shape after the write-guard removal.

Runnable two ways:
    python3 skills/deep-plan/tests/test_setup_session.py
    python3 -m pytest skills/deep-plan/tests/test_setup_session.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import tempfile
import types
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

# Point runtime state at a throwaway dir BEFORE importing the module (it reads
# XDG_STATE_HOME at import time).
_TMP = tempfile.mkdtemp(prefix="deep-plan-test-state-")
os.environ["XDG_STATE_HOME"] = _TMP


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


setup = _load("setup_session")


def test_bootstrap_state_has_archive_field_and_no_custom_path() -> None:
    sid = "pytest-archive-field"
    ns = types.SimpleNamespace(session_id=sid, harness_plan_path="/tmp/harness-plan.md")
    try:
        result = setup.cmd_bootstrap(ns)
        assert "archive_plan_path" in result
        assert result["archive_plan_path"] is None
        assert "custom_plan_path" not in result
        assert result["harness_plan_path"].endswith("harness-plan.md")

        state_file = Path(_TMP) / "deep-plan" / "state" / f"{sid}.json"
        on_disk = json.loads(state_file.read_text())
        assert "archive_plan_path" in on_disk
        assert "custom_plan_path" not in on_disk
    finally:
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_archive_plan_path_is_a_permitted_update_key() -> None:
    assert "archive_plan_path" in setup.PERMITTED_UPDATE_KEYS
    assert "custom_plan_path" not in setup.PERMITTED_UPDATE_KEYS


def test_update_plans_dir_persists_and_creates_dir() -> None:
    sid = "pytest-update-plansdir"
    boot = types.SimpleNamespace(session_id=sid, harness_plan_path="/tmp/h.md")
    try:
        setup.cmd_bootstrap(boot)
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "chosen-plans"
            ns = types.SimpleNamespace(session_id=sid, update=[f"plans_dir={target}"])
            result = setup.cmd_update(ns)
            assert result["ok"] is True
            assert result["plans_dir"] == str(target.resolve())
            assert target.exists(), "plans_dir should be created on update"

            projects = json.loads((Path(_TMP) / "deep-plan" / "projects.json").read_text())
            root = result["project_root"]
            assert projects[root]["plans_dir"] == str(target.resolve())
    finally:
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_unknown_update_key_rejected() -> None:
    sid = "pytest-bad-update-key"
    boot = types.SimpleNamespace(session_id=sid, harness_plan_path="/tmp/h.md")
    try:
        setup.cmd_bootstrap(boot)
        ns = types.SimpleNamespace(session_id=sid, update=["bogus_key=1"])
        result = setup.cmd_update(ns)
        assert result["ok"] is False
        assert "not permitted" in result["error"]
    finally:
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_legacy_migration_copies_once() -> None:
    saved = (
        setup.RUNTIME_DIR,
        setup.STATE_DIR,
        setup.PROJECTS_JSON,
        setup.HOOK_ERROR_LOG,
        setup.LEGACY_RUNTIME_DIR,
    )
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        new_runtime = base / "new"
        legacy = base / "legacy"
        (legacy / "state").mkdir(parents=True)
        (legacy / "projects.json").write_text('{"/proj": {"plans_dir": "/proj/.claude/plans"}}\n')
        (legacy / "state" / "old-session.json").write_text('{"session_id": "old-session"}')

        setup.RUNTIME_DIR = new_runtime
        setup.STATE_DIR = new_runtime / "state"
        setup.PROJECTS_JSON = new_runtime / "projects.json"
        setup.HOOK_ERROR_LOG = new_runtime / "hook-errors.log"
        setup.LEGACY_RUNTIME_DIR = legacy
        try:
            setup.ensure_runtime_dirs()
            migrated = json.loads(setup.PROJECTS_JSON.read_text())
            assert migrated == {"/proj": {"plans_dir": "/proj/.claude/plans"}}
            assert (setup.STATE_DIR / "old-session.json").exists()
            assert (new_runtime / "MIGRATED.txt").exists()

            # Second run must NOT re-migrate: the breadcrumb guards it.
            (legacy / "projects.json").write_text('{"/proj2": {}}\n')
            setup.ensure_runtime_dirs()
            again = json.loads(setup.PROJECTS_JSON.read_text())
            assert again == {"/proj": {"plans_dir": "/proj/.claude/plans"}}, "must not re-migrate"
        finally:
            (
                setup.RUNTIME_DIR,
                setup.STATE_DIR,
                setup.PROJECTS_JSON,
                setup.HOOK_ERROR_LOG,
                setup.LEGACY_RUNTIME_DIR,
            ) = saved


if __name__ == "__main__":
    import sys
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
    shutil.rmtree(_TMP, ignore_errors=True)
    sys.exit(1 if failed else 0)
