"""Guards the plan-file template and a golden plan against finalize drift.

If a future edit desyncs `plan-file-template.md` or the golden example from
`finalize_plan.py`, these tests fail. This is the regression guard for the
original bug (validator required a section the template never mentioned).

Runnable two ways:
    python3 skills/deep-plan/tests/test_template_contract.py
    python3 -m pytest skills/deep-plan/tests/test_template_contract.py
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # skills/deep-plan
SCRIPTS = ROOT / "scripts"
TEMPLATE = ROOT / "references" / "plan-file-template.md"
GOLDEN = Path(__file__).resolve().parent / "golden" / "example-plan.md"

REQUIRED = [
    "## Context",
    "## Decisions made",
    "## Architecture",
    "## Tasks",
    "## References",
    "## Open questions",
]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


finalize = _load("finalize_plan")


def _extract_skeleton(text: str) -> str:
    m = re.search(r"````markdown\n(.*?)\n````", text, re.DOTALL)
    assert m, "skeleton code fence not found in plan-file-template.md"
    return m.group(1)


def test_template_skeleton_normalizes_to_valid() -> None:
    skeleton = _extract_skeleton(TEMPLATE.read_text())
    repaired, report = finalize.repair(skeleton)
    for sec in REQUIRED:
        assert sec in repaired, f"required section {sec} missing after repair"
    assert "—" not in repaired and "–" not in repaired, "em/en-dash survived repair"
    for line in repaired.splitlines():
        if line.startswith("### Task"):
            assert re.match(r"^### Task \d+: ", line), f"non-colon task header: {line!r}"
    again, _ = finalize.repair(repaired)
    assert again == repaired, "repair must be idempotent"


def test_template_declares_overview_markers_and_summary_rule() -> None:
    text = TEMPLATE.read_text()
    skeleton = _extract_skeleton(text)

    # Markers come from finalize_plan constants (never re-hardcoded here) and
    # appear exactly once each, wrapping the Task overview heading between
    # Architecture and Tasks in the skeleton.
    assert text.count(finalize.OVERVIEW_BEGIN) == 1
    assert text.count(finalize.OVERVIEW_END) == 1
    arch = skeleton.index("## Architecture")
    begin = skeleton.index(finalize.OVERVIEW_BEGIN)
    heading = skeleton.index("## Task overview")
    end = skeleton.index(finalize.OVERVIEW_END)
    tasks = skeleton.index("## Tasks")
    assert arch < begin < heading < end < tasks, (
        "Task overview region must sit between ## Architecture and ## Tasks"
    )

    # Formatting rules name the opening summary-sentence rule and the
    # folder member set.
    assert "plain-English summary sentence" in text
    for member in ("plan.md", "research.md", "probes.md", "design.md"):
        assert member in text, f"folder member {member} not named in template"

    # The dotted-sibling naming is gone.
    assert "<slug>.probes.md" not in text
    assert "<slug>.research.md" not in text


def test_golden_plan_has_no_fixes_or_warnings() -> None:
    repaired, report = finalize.repair(GOLDEN.read_text())
    assert report["ok"] is True
    assert report["fixes"] == [], f"golden plan should need no fixes, got {report['fixes']}"
    assert report["warnings"] == [], f"golden plan should have no warnings, got {report['warnings']}"


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
    sys.exit(1 if failed else 0)
