"""Tests for load_tasks.py: parse a finalized plan into structured tasks.

Runnable two ways:
    python3 skills/deep-plan/tests/test_load_tasks.py
    python3 -m pytest skills/deep-plan/tests/test_load_tasks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
GOLDEN = Path(__file__).resolve().parent / "golden" / "example-plan.md"

# load_tasks imports finalize_plan as a sibling; put scripts/ on the path so
# both resolve when the test runner's cwd is elsewhere.
sys.path.insert(0, str(SCRIPTS))

import load_tasks  # noqa: E402


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
