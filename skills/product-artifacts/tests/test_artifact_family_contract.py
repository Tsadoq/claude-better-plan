"""Contract test: artifact-family.md's published member chain and provenance literal.

Pins what a substring elsewhere cannot express: that
skills/product-artifacts/references/artifact-family.md names all five chain
members in chain order and carries the provenance literal exactly once, so the
document five downstream skills will cite cannot drift from what
product_artifact.py implements. Runtime state classification (fresh, stale,
unresolvable, absent) is owned by the later freshness tests, not here.

Runnable two ways:
    python3 skills/product-artifacts/tests/test_artifact_family_contract.py
    python3 -m pytest skills/product-artifacts/tests/test_artifact_family_contract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ARTIFACT_FAMILY = (
    Path(__file__).resolve().parent.parent / "references" / "artifact-family.md"
)

# The closed five-member chain, in chain order.
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

# brief.md's required H2 names, in the order the PR-FAQ format reads them.
BRIEF_SECTIONS = (
    "## Press release",
    "## External FAQ",
    "## Internal FAQ",
)

# A placeholder from brief.md's pre-PR-FAQ section set. Its absence is what
# distinguishes a replaced list from one the PR-FAQ names were appended to.
SUPERSEDED_BRIEF_SECTION = "## Success criteria"

UNKNOWN_MARKER_LITERAL = "[UNKNOWN: <what is missing> -- <who would know>]"

UNKNOWN_MARKER_HEADING = "## Unknown marker"

# Each payload field is documented on its own bullet, so a beat learns what to
# put in it rather than inferring the field from the literal's placeholder.
UNKNOWN_MARKER_FIELD_BULLETS = (
    "- `<what is missing>`",
    "- `<who would know>`",
)

# The rule that makes the payload load-bearing: a marker missing half its
# payload must read as broken, not merely terse, or beats will emit one-field
# markers and the routing the second field exists for is silently lost.
UNKNOWN_MARKER_RULE_TERMS = ("mandatory", "malformed")


def _section_body(text: str, heading: str) -> str:
    """Return the text under `heading`, stopping at the next H2 or end of file.

    Scoping a search to one section is what separates "the document mentions
    this somewhere" from "the section a reader consults actually says it".
    """
    after_heading = text[text.index(heading) + len(heading) :]
    next_h2 = after_heading.find("\n## ")
    return after_heading if next_h2 == -1 else after_heading[:next_h2]


def test_artifact_family_pins_member_chain_and_provenance_literal() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    # Chain order: each member's first occurrence must come after the previous
    # member's first occurrence, so the prose cannot silently reorder the chain.
    positions = [text.find(member) for member in MEMBERS_IN_CHAIN_ORDER]
    for member, pos in zip(MEMBERS_IN_CHAIN_ORDER, positions, strict=True):
        assert pos != -1, f"artifact-family.md is missing chain member {member!r}"
    assert positions == sorted(positions), (
        f"artifact-family.md must name the five members in chain order "
        f"{MEMBERS_IN_CHAIN_ORDER}; found at positions {positions}"
    )

    # The literal five downstream skills cite must appear exactly once: zero
    # means it was never published, and more than once invites two copies to
    # drift apart from each other.
    occurrences = text.count(PROVENANCE_LITERAL)
    assert occurrences == 1, (
        f"expected the provenance literal {PROVENANCE_LITERAL!r} to appear exactly "
        f"once, found {occurrences}"
    )

    for heading in REQUIRED_HEADINGS:
        assert heading in text, f"artifact-family.md is missing heading {heading!r}"


def test_artifact_family_pins_brief_sections_and_unknown_marker() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    # Document order: the PR-FAQ's three sections are a sequence, not a set --
    # an internal FAQ published ahead of the press release would describe a
    # different format -- so first occurrences must ascend.
    positions = [text.find(section) for section in BRIEF_SECTIONS]
    for section, pos in zip(BRIEF_SECTIONS, positions, strict=True):
        assert pos != -1, f"artifact-family.md is missing brief.md section {section!r}"
    assert positions == sorted(positions), (
        f"artifact-family.md must name brief.md's sections in document order "
        f"{BRIEF_SECTIONS}; found at positions {positions}"
    )

    # Appending the PR-FAQ names to the old placeholder set would leave both
    # readings defensible, so the superseded name must be gone, not merely
    # outranked.
    assert SUPERSEDED_BRIEF_SECTION not in text, (
        f"artifact-family.md still names the superseded brief.md section "
        f"{SUPERSEDED_BRIEF_SECTION!r}; the PR-FAQ sections replace that set "
        f"rather than extend it"
    )

    # One definition, cited everywhere else: a second copy is a token that can
    # drift, and zero copies is a marker no beat can write.
    occurrences = text.count(UNKNOWN_MARKER_LITERAL)
    assert occurrences == 1, (
        f"expected the unknown-marker literal {UNKNOWN_MARKER_LITERAL!r} to appear "
        f"exactly once, found {occurrences}"
    )

    # The payload rule must live under the marker's own heading: a beat about
    # to write a marker reads that one section, so a rule stated anywhere else
    # in the document is a rule it will never see.
    marker_section = _section_body(text, UNKNOWN_MARKER_HEADING)
    for bullet in UNKNOWN_MARKER_FIELD_BULLETS:
        assert bullet in marker_section, (
            f"{UNKNOWN_MARKER_HEADING!r} does not document the payload field "
            f"{bullet!r} on its own bullet"
        )
    for term in UNKNOWN_MARKER_RULE_TERMS:
        assert term in marker_section, (
            f"{UNKNOWN_MARKER_HEADING!r} must state that both payload fields are "
            f"mandatory and that a marker with an empty field is malformed; the "
            f"word {term!r} is missing from the section"
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
