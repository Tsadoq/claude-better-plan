"""Contract test: the readability-guidance content.

Pins the structure of skills/deep-plan/references/readability-principles.md
(the single source of truth for narrative-artifact readability) so callers
that quote its sections by heading never silently break. Stdlib only, so CI
does not need pyyaml.

Runnable two ways:
    python3 skills/deep-plan/tests/test_readability_contract.py
    python3 -m pytest skills/deep-plan/tests/test_readability_contract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
READABILITY = ROOT / "skills" / "deep-plan" / "references" / "readability-principles.md"

PRINCIPLES_H2 = (
    "## Plan-time authoring rules",
    "## Review-time red flags",
    "## How to update these guidelines",
)


def _section(text: str, heading: str) -> str:
    """Return the body of an H2 section (from its heading to the next H2)."""
    start = text.find(heading)
    if start == -1:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _clusters(section: str) -> list[str]:
    """Split an H2 section body into its H3 cluster bodies."""
    parts = section.split("\n### ")
    return ["### " + part for part in parts[1:]]


def test_readability_principles_structure() -> None:
    assert READABILITY.exists(), f"missing guideline file: {READABILITY}"
    text = READABILITY.read_text()

    positions: list[int] = []
    for heading in PRINCIPLES_H2:
        assert heading in text, f"readability-principles.md missing section {heading!r}"
        positions.append(text.index(heading))
    assert positions == sorted(positions), (
        f"H2 sections out of order; expected {PRINCIPLES_H2}"
    )

    red_flags = _section(text, "## Review-time red flags")
    clusters = _clusters(red_flags)
    assert len(clusters) == 1, (
        f"expected exactly 1 H3 red-flag cluster, found {len(clusters)}"
    )
    questions = [ln for ln in clusters[0].splitlines() if ln.rstrip().endswith("?")]
    assert len(questions) >= 5, (
        f"the red-flag cluster must carry at least five checkable yes/no "
        f"questions (lines ending in '?'), found {len(questions)}"
    )

    update = _section(text, "## How to update these guidelines")
    assert "test_readability_contract.py" in update, (
        "the update section must name its pinning test test_readability_contract.py"
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
