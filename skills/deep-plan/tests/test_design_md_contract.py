"""Guards the design.md reference template's required shape.

The template is the single contract both /deep-plan (seeding at Phase 4.4)
and /deep-plan:deep-plan-execute (per-task Implementation notes) write
against; if its headings drift, both skills drift with it.

Runnable two ways:
    python3 skills/deep-plan/tests/test_design_md_contract.py
    python3 -m pytest skills/deep-plan/tests/test_design_md_contract.py
"""

from __future__ import annotations

from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "design-md-template.md"


def test_design_template_required_sections() -> None:
    assert TEMPLATE.exists(), f"missing template: {TEMPLATE}"
    text = TEMPLATE.read_text()
    # The narrative skeleton, in order: title, Background prose, one
    # question-shaped section per decision (whose body opens with the decision
    # in its first sentence), and the execute-skill append target last.
    needles = [
        "# Design:",
        "## Background",
        "## {plain-language question",
        "first sentence",
        "## Implementation notes",
    ]
    pos = -1
    for needle in needles:
        found = text.find(needle, pos + 1)
        assert found > pos, f"{needle!r} missing or out of order in design-md-template.md"
        pos = found

    assert "readability-principles.md" in text, (
        "the template must point authors at readability-principles.md's "
        "Plan-time authoring rules instead of restating them"
    )
    assert "punctuation other than hyphens and underscores" in text, (
        "the template must state the anchor-slug rule plan.md decision rows "
        "link with (quoted from readability-principles.md)"
    )
    assert "**Chosen**" not in text, (
        "the retired Chosen/Rejected/Why field-block shape must not resurface"
    )


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
