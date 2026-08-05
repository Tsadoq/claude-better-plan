
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

_TMP = tempfile.mkdtemp(prefix="deep-plan-test-state-")
os.environ["XDG_STATE_HOME"] = _TMP


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


setup = _load("setup_session")


def test_bootstrap_state_drops_dead_fields_and_uses_plan_path() -> None:
    sid = "pytest-minimal-state"
    ns = types.SimpleNamespace(session_id=sid)
    dead_fields = (
        "harness_plan_path",
        "phase",
        "decisions",
        "archive_plan_path",
        "custom_plan_path",
    )
    try:
        result = setup.cmd_bootstrap(ns)
        assert "plan_path" in result
        assert result["plan_path"] is None
        for dead in dead_fields:
            assert dead not in result, f"dead field {dead!r} still in bootstrap result"

        state_file = Path(_TMP) / "deep-plan" / "state" / f"{sid}.json"
        on_disk = json.loads(state_file.read_text())
        assert on_disk["plan_path"] is None
        for dead in dead_fields:
            assert dead not in on_disk, f"dead field {dead!r} still in on-disk state"

        assert setup.PERMITTED_UPDATE_KEYS == {"plans_dir", "plan_path", "last_plan_path"}
    finally:
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_docs_plans_recommended_and_protected_sentinel() -> None:
    candidates = setup.candidate_plans_dirs(Path("/proj"))
    assert candidates[0]["path"].endswith("/docs/plans")
    assert candidates[0]["recommended"] == "true"
    claude_entries = [c for c in candidates if c["path"].endswith("/.claude/plans")]
    assert len(claude_entries) == 1
    assert claude_entries[0].get("warn"), ".claude/plans entry must carry a non-empty warn"

    sid = "pytest-protected-sentinel"
    root = setup.detect_project_root(Path.cwd())[0]
    projects_file = Path(_TMP) / "deep-plan" / "projects.json"
    saved = projects_file.read_text() if projects_file.exists() else None
    try:
        protected_dir = root / ".claude" / "plans"
        setup.save_projects({str(root): {"plans_dir": str(protected_dir)}})
        result = setup.cmd_bootstrap(types.SimpleNamespace(session_id=sid))
        assert result["sentinels"]["plans_dir_under_protected_path"] == str(protected_dir)

        setup.save_projects({str(root): {"plans_dir": str(root / "docs" / "plans")}})
        result = setup.cmd_bootstrap(types.SimpleNamespace(session_id=sid))
        assert not result["sentinels"]["plans_dir_under_protected_path"]
    finally:
        if saved is not None:
            projects_file.write_text(saved)
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_update_plans_dir_persists_and_creates_dir() -> None:
    sid = "pytest-update-plansdir"
    boot = types.SimpleNamespace(session_id=sid)
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


def test_last_plan_path_roundtrip_gated_on_approval() -> None:
    sid = "pytest-last-plan-memo"
    projects_file = Path(_TMP) / "deep-plan" / "projects.json"
    saved = projects_file.read_text() if projects_file.exists() else None
    try:
        setup.cmd_bootstrap(types.SimpleNamespace(session_id=sid))
        with tempfile.TemporaryDirectory() as d:
            plan = Path(d) / "plan.md"
            plan.write_text("# Some plan\n\n**Status**: approved\n")
            recorded = setup.cmd_update(
                types.SimpleNamespace(session_id=sid, update=[f"last_plan_path={plan}"])
            )
            assert recorded["ok"] is True

            found = setup.cmd_lookup(types.SimpleNamespace())
            assert found["last_plan_path"] == str(plan), (
                "lookup must return the memoized path while the plan is approved"
            )

            plan.write_text("# Some plan\n\n**Status**: draft\n")
            unapproved = setup.cmd_lookup(types.SimpleNamespace())
            assert unapproved["ok"] is True and unapproved["last_plan_path"] is None, (
                "a memo whose plan lost its approved Status must resolve to null, not error"
            )

            plan.unlink()
            missing = setup.cmd_lookup(types.SimpleNamespace())
            assert missing["ok"] is True and missing["last_plan_path"] is None, (
                "a memo pointing at a deleted plan must resolve to null, not error"
            )
    finally:
        if saved is not None:
            projects_file.write_text(saved)
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_lookup_cli_runs_without_session_id() -> None:
    script = SCRIPTS / "setup_session.py"
    looked_up = subprocess.run(
        [sys.executable, str(script), "--lookup"], capture_output=True, text=True
    )
    assert looked_up.returncode == 0, (
        f"--lookup must not require --session-id: {looked_up.stderr}"
    )
    out = json.loads(looked_up.stdout)
    assert out["ok"] is True
    assert set(out) == {"ok", "project_root", "plans_dir", "last_plan_path"}, (
        "lookup output must carry exactly the documented keys"
    )

    bootstrap = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert bootstrap.returncode != 0, "bootstrap without --session-id must be rejected"
    assert "--session-id is required" in bootstrap.stderr


def test_unknown_update_key_rejected() -> None:
    sid = "pytest-bad-update-key"
    boot = types.SimpleNamespace(session_id=sid)
    try:
        setup.cmd_bootstrap(boot)
        ns = types.SimpleNamespace(session_id=sid, update=["bogus_key=1"])
        result = setup.cmd_update(ns)
        assert result["ok"] is False
        assert "not permitted" in result["error"]
    finally:
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_v03_state_and_projects_forward_compat() -> None:
    sid = "pytest-v03-compat"
    root = setup.detect_project_root(Path.cwd())[0]
    projects_file = Path(_TMP) / "deep-plan" / "projects.json"
    saved = projects_file.read_text() if projects_file.exists() else None
    try:
        remembered = root / "docs" / "plans"
        setup.save_projects(
            {
                str(root): {
                    "plans_dir": str(remembered),
                    "last_used_at": "2026-01-01T00:00:00Z",
                    "stray_legacy_key": "ignored",
                }
            }
        )
        result = setup.cmd_bootstrap(types.SimpleNamespace(session_id=sid))
        assert result["plans_dir"] == str(remembered)

        setup.write_state(
            sid,
            {
                "session_id": sid,
                "project_root": str(root),
                "plans_dir": str(remembered),
                "harness_plan_path": "/tmp/legacy-harness.md",
                "archive_plan_path": None,
                "sandbox_dir": f"/tmp/deep-plan-{sid}",
                "phase": "Phase 0",
                "decisions": [],
            },
        )
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "new-plans"
            updated = setup.cmd_update(
                types.SimpleNamespace(session_id=sid, update=[f"plans_dir={target}"])
            )
            assert updated["ok"] is True

        rejected = setup.cmd_update(
            types.SimpleNamespace(session_id=sid, update=["harness_plan_path=x"])
        )
        assert rejected["ok"] is False
        assert "not permitted" in rejected["error"]
    finally:
        if saved is not None:
            projects_file.write_text(saved)
        shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


def test_bootstrap_ignores_legacy_state_dir() -> None:
    marker = "/marker/legacy-plans-dir-must-not-be-read"
    script = SCRIPTS / "setup_session.py"
    sid = "pytest-legacy-ignored"
    with tempfile.TemporaryDirectory() as d:
        home = Path(d).resolve()
        legacy = home / ".claude" / "deep-plan"
        (legacy / "state").mkdir(parents=True)
        (legacy / "projects.json").write_text(
            json.dumps({str(home): {"plans_dir": marker}}) + "\n"
        )
        (legacy / "state" / "old-session.json").write_text('{"session_id": "old-session"}')
        before = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}

        env = {**os.environ, "HOME": str(home), "XDG_STATE_HOME": str(home / "xdg-state")}
        try:
            proc = subprocess.run(
                [sys.executable, str(script), "--session-id", sid],
                cwd=home,
                env=env,
                capture_output=True,
                text=True,
            )
            assert proc.returncode == 0, f"bootstrap failed: {proc.stderr}"
            out = json.loads(proc.stdout)
            assert out["project_root"] == str(home), (
                "test setup is wrong: legacy record is keyed on a different project root, "
                f"so the migration path would not have been exercised (got {out['project_root']})"
            )
            assert out["plans_dir"] is None, (
                f"bootstrap resolved plans_dir from the legacy dir: {out['plans_dir']!r}"
            )
            assert out["sentinels"]["prompt_for_plans_dir"] is True
            assert marker not in proc.stdout, "legacy marker leaked into bootstrap output"

            xdg = home / "xdg-state" / "deep-plan"
            assert marker not in (xdg / "projects.json").read_text(), (
                "legacy projects.json was copied into the XDG state dir"
            )
            assert not (xdg / "state" / "old-session.json").exists(), (
                "legacy session state was resurrected into the XDG state dir"
            )

            after = {
                p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()
            }
            assert after == before, "legacy dir must be left untouched"
        finally:
            shutil.rmtree(Path("/tmp") / f"deep-plan-{sid}", ignore_errors=True)


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
    shutil.rmtree(_TMP, ignore_errors=True)
    sys.exit(1 if failed else 0)
