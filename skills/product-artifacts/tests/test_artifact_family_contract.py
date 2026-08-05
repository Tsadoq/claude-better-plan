
from __future__ import annotations

import sys
from pathlib import Path

ARTIFACT_FAMILY = Path(__file__).resolve().parent.parent / "references" / "artifact-family.md"

MEMBERS_IN_CHAIN_ORDER = (
    "brief.md",
    "discovery.md",
    "requirements.md",
    "spec.md",
    "roadmap.md",
)

PROVENANCE_LITERAL = "**Derived from**: <upstream member> (<git blob sha>)"

REQUIRED_HEADINGS = (
    "## Members",
    "## Provenance",
    "## Staleness",
    "## Re-run behaviour",
    "## Unknown marker",
)

BRIEF_SECTIONS = (
    "## Press release",
    "## External FAQ",
    "## Internal FAQ",
)

SUPERSEDED_BRIEF_SECTION = "## Success criteria"

SPEC_SECTIONS = (
    "## Problem and opportunity",
    "## Requirements in scope",
    "## Non-goals",
)

SUPERSEDED_SPEC_SECTIONS = (
    "## Interfaces",
    "## Behavior",
    "## Edge cases",
)

ROADMAP_SECTIONS = (
    "## Scored items",
    "## Sequence",
    "## Risks",
)

SUPERSEDED_ROADMAP_SECTIONS = (
    "## Milestones",
    "## Sequencing",
)

UNKNOWN_MARKER_LITERAL = "[UNKNOWN: <what is missing> -- <who would know>]"

UNKNOWN_MARKER_HEADING = "## Unknown marker"

UNKNOWN_MARKER_FIELD_BULLETS = (
    "- `<what is missing>`",
    "- `<who would know>`",
)

UNKNOWN_MARKER_RULE_TERMS = ("mandatory", "malformed")


def _section_body(text: str, heading: str) -> str:
    after_heading = text[text.index(heading) + len(heading) :]
    next_h2 = after_heading.find("\n## ")
    return after_heading if next_h2 == -1 else after_heading[:next_h2]


def _assert_names_in_pinned_order(text: str, names: tuple[str, ...], what: str) -> None:
    positions = [text.find(name) for name in names]
    for name, pos in zip(names, positions, strict=True):
        assert pos != -1, f"artifact-family.md is missing {what} {name!r}"
    assert positions == sorted(positions), (
        f"artifact-family.md must name every {what} in the pinned order "
        f"{names}; found at positions {positions}"
    )


def _assert_superseded_names_absent(text: str, names: tuple[str, ...], what: str) -> None:
    for name in names:
        assert name not in text, (
            f"artifact-family.md still names the superseded {what} {name!r}; "
            f"the pinned names replace that set rather than extend it"
        )


def test_artifact_family_pins_member_chain_and_provenance_literal() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    _assert_names_in_pinned_order(text, MEMBERS_IN_CHAIN_ORDER, "chain member")

    occurrences = text.count(PROVENANCE_LITERAL)
    assert occurrences == 1, (
        f"expected the provenance literal {PROVENANCE_LITERAL!r} to appear exactly once, found {occurrences}"
    )

    for heading in REQUIRED_HEADINGS:
        assert heading in text, f"artifact-family.md is missing heading {heading!r}"


def test_artifact_family_pins_brief_sections_and_unknown_marker() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    _assert_names_in_pinned_order(text, BRIEF_SECTIONS, "brief.md section")

    assert SUPERSEDED_BRIEF_SECTION not in text, (
        f"artifact-family.md still names the superseded brief.md section "
        f"{SUPERSEDED_BRIEF_SECTION!r}; the PR-FAQ sections replace that set "
        f"rather than extend it"
    )

    occurrences = text.count(UNKNOWN_MARKER_LITERAL)
    assert occurrences == 1, (
        f"expected the unknown-marker literal {UNKNOWN_MARKER_LITERAL!r} to appear "
        f"exactly once, found {occurrences}"
    )

    marker_section = _section_body(text, UNKNOWN_MARKER_HEADING)
    for bullet in UNKNOWN_MARKER_FIELD_BULLETS:
        assert bullet in marker_section, (
            f"{UNKNOWN_MARKER_HEADING!r} does not document the payload field {bullet!r} on its own bullet"
        )
    for term in UNKNOWN_MARKER_RULE_TERMS:
        assert term in marker_section, (
            f"{UNKNOWN_MARKER_HEADING!r} must state that both payload fields are "
            f"mandatory and that a marker with an empty field is malformed; the "
            f"word {term!r} is missing from the section"
        )


def test_artifact_family_pins_spec_sections() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    _assert_names_in_pinned_order(text, SPEC_SECTIONS, "spec.md section")

    _assert_superseded_names_absent(text, SUPERSEDED_SPEC_SECTIONS, "spec.md section")


def test_artifact_family_pins_roadmap_sections() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    _assert_names_in_pinned_order(text, ROADMAP_SECTIONS, "roadmap.md section")

    _assert_superseded_names_absent(text, SUPERSEDED_ROADMAP_SECTIONS, "roadmap.md section")


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
