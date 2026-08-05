
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN_INTEGRITY = ROOT / "skills" / "deep-plan" / "references" / "plan-integrity-principles.md"

PRINCIPLES_H2 = (
    "## Scope",
    "## Review-time red flags",
    "## How to update these guidelines",
)

REQUIRED_CHECKS = ("schedule", "depends on", "decision", "tests (tdd)", "claim")


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _clusters(section: str) -> list[str]:
    parts = section.split("\n### ")
    return ["### " + part for part in parts[1:]]


def test_plan_integrity_principles_structure() -> None:
    assert PLAN_INTEGRITY.exists(), f"missing guideline file: {PLAN_INTEGRITY}"
    text = PLAN_INTEGRITY.read_text()

    found = [ln.rstrip() for ln in text.splitlines() if ln.startswith("## ")]
    assert tuple(found) == PRINCIPLES_H2, (
        f"H2 headings must be exactly {PRINCIPLES_H2} in that order, found {tuple(found)}"
    )

    red_flags = _section(text, "## Review-time red flags")
    clusters = _clusters(red_flags)
    assert len(clusters) == 1, f"expected exactly 1 H3 red-flag cluster, found {len(clusters)}"
    assert clusters[0].startswith("### Plan integrity"), (
        f"the single cluster must be titled '### Plan integrity', found {clusters[0].splitlines()[0]!r}"
    )

    questions = [ln for ln in clusters[0].splitlines() if ln.rstrip().endswith("?")]
    assert len(questions) >= 5, (
        f"the cluster must carry at least five checkable yes/no questions "
        f"(lines ending in '?'), found {len(questions)}"
    )

    haystack = "\n".join(questions).lower()
    uncovered = [check for check in REQUIRED_CHECKS if check not in haystack]
    assert not uncovered, f"no question covers the retired plan-critic checks {uncovered}"

    update = _section(text, "## How to update these guidelines")
    assert "test_plan_integrity_contract.py" in update, (
        "the update section must name its pinning test test_plan_integrity_contract.py"
    )


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
