"""Tests for load_tasks.py: parse a finalized plan into structured tasks.

Runnable two ways:
    python3 skills/deep-plan/tests/test_load_tasks.py
    python3 -m pytest skills/deep-plan/tests/test_load_tasks.py
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
GOLDEN = Path(__file__).resolve().parent / "golden" / "example-plan.md"
LEGACY = Path(__file__).resolve().parent / "golden" / "legacy-plan.md"

# load_tasks imports finalize_plan as a sibling; put scripts/ on the path so
# both resolve when the test runner's cwd is elsewhere.
sys.path.insert(0, str(SCRIPTS))

import finalize_plan  # noqa: E402
import load_tasks  # noqa: E402


def _run_main(argv: list[str]) -> tuple[int, dict[str, Any]]:
    old_argv = sys.argv
    sys.argv = ["load_tasks", *argv]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = load_tasks.main()
    finally:
        sys.argv = old_argv
    return code, json.loads(buf.getvalue())


def test_load_tasks_accepts_folder_path() -> None:
    with tempfile.TemporaryDirectory() as d:
        folder = Path(d) / "rate-limiter"
        folder.mkdir()
        (folder / "plan.md").write_text(GOLDEN.read_text())

        code_dir, from_dir = _run_main(["--plan", str(folder)])
        code_file, from_file = _run_main(["--plan", str(folder / "plan.md")])
        assert code_dir == 0 and code_file == 0
        assert from_dir["tasks"] == from_file["tasks"]

        empty = Path(d) / "empty"
        empty.mkdir()
        code, err = _run_main(["--plan", str(empty)])
        assert code != 0
        assert "plan.md" in err["error"], "error must name the expected plan.md member"


def test_parses_golden_plan_tasks_and_deps() -> None:
    parsed = load_tasks.parse_plan(GOLDEN.read_text())
    tasks = parsed["tasks"]
    assert len(tasks) == 2, f"expected 2 tasks, got {len(tasks)}"

    t1, t2 = tasks
    assert t1["n"] == 1 and t2["n"] == 2
    assert t1["depends_on"] == [], f"task 1 should depend on nothing, got {t1['depends_on']}"
    assert t2["depends_on"] == [1], f"task 2 should depend on [1], got {t2['depends_on']}"

    for t in tasks:
        assert t["subject"].strip(), f"task {t['n']} has empty subject"
        assert t["change"].strip(), f"task {t['n']} has empty change"

    # Golden has a code task (with Tests block) and a docs task (without one).
    assert t1["tests"], "task 1 (code) should carry a Tests block"
    assert not t2["tests"], "task 2 (docs) should have no Tests block"


def test_malformed_depends_on_degrades_to_empty() -> None:
    assert load_tasks.parse_depends_on("none") == []
    assert load_tasks.parse_depends_on("1") == [1]
    assert load_tasks.parse_depends_on("1, 2,3") == [1, 2, 3]
    # Garbage must not raise; it degrades to an empty list.
    assert load_tasks.parse_depends_on("see task above") == []
    assert load_tasks.parse_depends_on("") == []


def test_legacy_plan_parses_and_repairs_clean() -> None:
    # legacy-plan.md is a byte-frozen copy of the v0.7 golden: plans authored
    # under the old format must keep parsing and repairing clean forever.
    legacy = LEGACY.read_text()

    parsed = load_tasks.parse_plan(legacy)
    tasks = parsed["tasks"]
    assert len(tasks) == 2, f"legacy fixture must keep its 2 tasks, got {len(tasks)}"
    t1, t2 = tasks
    assert t1["n"] == 1 and t1["depends_on"] == [], (
        f"legacy task 1 must parse with no deps, got {t1['depends_on']}"
    )
    assert t2["n"] == 2 and t2["depends_on"] == [1], (
        f"legacy task 2 must keep depending on task 1, got {t2['depends_on']}"
    )
    assert parsed["decisions"][0]["chosen"] == "Redis", (
        "legacy decision row 1 must keep parsing into its five cells"
    )

    _, report = finalize_plan.repair(legacy)
    assert report["ok"] is True
    assert report["fixes"] == [], f"legacy plan must repair with zero fixes, got {report['fixes']}"
    assert report["warnings"] == [], (
        f"legacy plan must repair with zero warnings, got {report['warnings']}"
    )


def test_decisions_and_open_questions_surface() -> None:
    parsed = load_tasks.parse_plan(GOLDEN.read_text())
    assert len(parsed["decisions"]) == 2, "golden has two decision rows"
    assert parsed["decisions"][0]["chosen"] == "Redis"
    assert parsed["open_questions"].strip().lower() in ("none", "- none")


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
