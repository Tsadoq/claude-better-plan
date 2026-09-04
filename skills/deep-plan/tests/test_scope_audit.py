from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scope = _load("scope_audit")


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr.strip()}"
    return result.stdout


def _repo(tmp_path: Path) -> Path:
    """A repo in the shape the dispatcher meets: one commit, a stale index entry, a dirty file."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", ".")
    _git(root, "config", "user.email", "deep-plan@example.invalid")
    _git(root, "config", "user.name", "deep-plan tests")
    (root / "a.py").write_text("original\n")
    (root / "tracked.txt").write_text("one\ntwo\nthree\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    (root / "a.py").write_text("original\nedited by somebody else\n")
    (root / "pending.py").write_text("half written\n")
    _git(root, "add", "-N", "pending.py")
    return root


def test_snapshot_succeeds_with_an_intent_to_add_entry(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    stash = subprocess.run(["git", "stash", "create"], cwd=root, capture_output=True, text=True, check=False)
    assert stash.returncode != 0, "repo no longer reproduces the stash failure this snapshot replaces"

    snap = scope.snapshot(root)

    assert re.fullmatch(r"[0-9a-f]{40}", snap["baseline"]), f"not a commit sha: {snap['baseline']!r}"
    diff = subprocess.run(["git", "diff", "--quiet", snap["baseline"]], cwd=root, check=False)
    assert diff.returncode == 0, "baseline tree differs from the working tree"


def test_snapshot_leaves_the_real_index_alone(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    before = _git(root, "ls-files", "-s").splitlines()

    scope.snapshot(root)

    after = _git(root, "ls-files", "-s").splitlines()
    for was, now in zip(before, after, strict=False):
        assert was == now, f"index entry changed: {was}"
    assert len(before) == len(after), f"index holds {len(after)} entries, held {len(before)}"


def test_snapshot_does_not_degrade_to_head_on_a_dirty_tree(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD").strip()

    snap = scope.snapshot(root)

    assert snap["baseline"] != head, "baseline fell back to HEAD, blaming the task for a dirty tree"
    assert scope.changed(root, snap) == [], "pre-existing edits attributed to the task"


def test_snapshot_refuses_a_repository_with_no_head(tmp_path: Path) -> None:
    root = tmp_path / "fresh"
    root.mkdir()
    _git(root, "init", "-q", ".")

    with pytest.raises(scope.ScopeAuditError) as caught:
        scope.snapshot(root)

    assert "HEAD" in str(caught.value), f"refusal does not name the missing HEAD: {caught.value}"


def test_changed_excludes_untracked_files_that_predate_the_snapshot(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "stray.log").write_text("left behind by an earlier run\n")

    snap = scope.snapshot(root)

    assert "stray.log" in snap["untracked"]
    assert scope.changed(root, snap) == [], "an untracked file older than the snapshot was reported"


def test_changed_includes_a_file_the_task_created(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    snap = scope.snapshot(root)

    (root / "created.py").write_text("task work\n")
    (root / "a.py").write_text("original\nedited by somebody else\nand now by the task\n")

    assert scope.changed(root, snap) == ["a.py", "created.py"]


def test_a_rename_is_reported_once_under_its_new_path(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    snap = scope.snapshot(root)

    (root / "renamed.txt").write_text((root / "tracked.txt").read_text())
    (root / "tracked.txt").unlink()

    assert scope.changed(root, snap) == ["renamed.txt"]


def test_audit_lists_only_paths_outside_targets_and_allow(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    snap = scope.snapshot(root)

    (root / "a.py").write_text("original\nedited by somebody else\nand now by the task\n")
    (root / "b.py").write_text("outside the task\n")
    (root / "design.md").write_text("## Implementation notes\n")

    unexpected = scope.audit(root, snap, targets=[str(root / "a.py")], allow=["design.md"])

    assert unexpected == ["b.py"], f"unexpected paths: {unexpected}"


def test_cli_audit_exits_one_and_names_the_offenders(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    script = str(SCRIPTS / "scope_audit.py")

    taken = subprocess.run(
        [sys.executable, script, "snapshot", "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert taken.returncode == 0, taken.stderr
    snap = json.loads(taken.stdout)

    (root / "b.py").write_text("outside the task\n")
    audited = subprocess.run(
        [
            sys.executable,
            script,
            "audit",
            "--root",
            str(root),
            "--snapshot",
            json.dumps(snap),
            "--targets",
            "a.py",
            "--allow",
            "design.md",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert audited.returncode == 1, f"audit passed with an offender present: {audited.stdout}"
    assert json.loads(audited.stdout)["unexpected"] == ["b.py"]
