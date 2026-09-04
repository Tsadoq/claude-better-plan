"""Baseline snapshot and scope audit for one task of a deep-plan plan.

The baseline is a commit object built through a throwaway index, never `git stash
create`: stash has to merge worktree state and so refuses whenever the real index
disagrees with disk (an intent-to-add entry, a stale stat cache), which is exactly
the state an unattended job leaves behind. The commit is unreachable, the real
index and the working tree are untouched, and the tree it records is the working
tree as it stood before the task started. It is authored under a fixed identity
because a repository with no `user.email` configured would otherwise get no
baseline at all.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

BASELINE_MESSAGE = "deep-plan baseline"
IDENTITY = ("-c", "user.name=deep-plan", "-c", "user.email=deep-plan@localhost")


class ScopeAuditError(RuntimeError):
    pass


def _git(root: Path, *args: str, index: Path | None = None) -> str:
    env = None if index is None else {**os.environ, "GIT_INDEX_FILE": str(index)}
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ScopeAuditError(f"git {' '.join(args)} failed in {root}: {result.stderr.strip()}")
    return result.stdout


def _head(root: Path) -> str:
    try:
        return _git(root, "rev-parse", "--verify", "HEAD").strip()
    except ScopeAuditError as exc:
        raise ScopeAuditError(f"{root} has no HEAD commit to take a baseline from") from exc


def _stage_worktree(root: Path, tree_ish: str, index: Path) -> None:
    _git(root, "read-tree", tree_ish, index=index)
    _git(root, "add", "-A", index=index)


def untracked(root: Path) -> list[str]:
    out = _git(root, "ls-files", "--others", "--exclude-standard", "--full-name")
    return sorted(line for line in out.splitlines() if line)


def snapshot(root: Path) -> dict[str, Any]:
    """Record the working tree as an unreachable commit and return its sha."""
    head = _head(root)
    with tempfile.TemporaryDirectory(prefix="deep-plan-index-") as tmp:
        index = Path(tmp) / "index"
        _stage_worktree(root, head, index)
        tree = _git(root, "write-tree", index=index).strip()
        commit = _git(
            root,
            *IDENTITY,
            "commit-tree",
            tree,
            "-p",
            head,
            "-m",
            BASELINE_MESSAGE,
            index=index,
        ).strip()
    return {"baseline": commit, "untracked": untracked(root)}


def changed(root: Path, snap: dict[str, Any]) -> list[str]:
    """Paths the working tree now differs from the baseline in, renames under the new path.

    Staged through a throwaway index too, so a file that was already untracked when
    the baseline was taken reads as unchanged rather than as a deletion.
    """
    baseline = str(snap["baseline"])
    with tempfile.TemporaryDirectory(prefix="deep-plan-index-") as tmp:
        index = Path(tmp) / "index"
        _stage_worktree(root, baseline, index)
        out = _git(root, "diff", "--name-only", "-M", "--cached", baseline, index=index)
    return sorted({line for line in out.splitlines() if line})


def _relative(root: Path, path: str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    try:
        return candidate.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def audit(
    root: Path,
    snap: dict[str, Any],
    targets: Iterable[str],
    allow: Iterable[str] = (),
) -> list[str]:
    """Changed paths the task was not permitted to touch. Absolute targets are relativised."""
    permitted = {_relative(root, path) for path in (*targets, *allow)}
    return [path for path in changed(root, snap) if path not in permitted]


def _split(values: Sequence[str]) -> list[str]:
    return [item.strip() for value in values for item in value.split(",") if item.strip()]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="deep-plan task baseline and scope audit")
    parser.add_argument("verb", choices=("snapshot", "changed", "audit"))
    parser.add_argument("--root", default=".", help="repository root (default: cwd)")
    parser.add_argument("--snapshot", help="the JSON the snapshot verb printed; changed and audit need it")
    parser.add_argument("--targets", action="append", default=[], help="comma-separated paths the task owns")
    parser.add_argument("--allow", action="append", default=[], help="comma-separated extra permitted paths")
    args = parser.parse_args(argv)
    if args.verb in ("changed", "audit") and not args.snapshot:
        parser.error(f"--snapshot is required by the {args.verb} verb")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    try:
        if args.verb == "snapshot":
            print(json.dumps(snapshot(root), indent=2, sort_keys=True))
            return 0
        taken: dict[str, Any] = json.loads(args.snapshot)
        if args.verb == "changed":
            print(json.dumps(changed(root, taken), indent=2))
            return 0
        unexpected = audit(root, taken, _split(args.targets), _split(args.allow))
        print(json.dumps({"ok": not unexpected, "unexpected": unexpected}, indent=2))
        return 1 if unexpected else 0
    except (ScopeAuditError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
