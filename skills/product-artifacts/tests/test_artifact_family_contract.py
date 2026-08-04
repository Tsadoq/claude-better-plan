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

ARTIFACT_FAMILY = Path(__file__).resolve().parent.parent / "references" / "artifact-family.md"

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

# spec.md's required H2 names, in the order the member reads them.
SPEC_SECTIONS = (
    "## Problem and opportunity",
    "## Requirements in scope",
    "## Non-goals",
)

# spec.md's pre-existing placeholder section set. All three are technology-shaped
# names the self-contained spec deliberately drops, and their absence is what
# distinguishes a replaced list from one the new names were appended to.
SUPERSEDED_SPEC_SECTIONS = (
    "## Interfaces",
    "## Behavior",
    "## Edge cases",
)

# roadmap.md's required H2 names, in the order the member reads them.
ROADMAP_SECTIONS = (
    "## Scored items",
    "## Sequence",
    "## Risks",
)

# roadmap.md's pre-existing placeholder names, both of them date-shaped terms the
# scored roadmap drops. `## Risks` is absent from this tuple because the new set
# retains it rather than replacing it. `## Sequencing` also has to be gone for
# `## Scored items`, `## Sequence` to mean what it says: `## Sequence` matches
# inside `## Sequencing`, so an unreplaced placeholder would satisfy the order
# assertion on its own.
SUPERSEDED_ROADMAP_SECTIONS = (
    "## Milestones",
    "## Sequencing",
)

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


def _assert_names_in_pinned_order(text: str, names: tuple[str, ...], what: str) -> None:
    """Assert `text` names every entry of `names`, in the order `names` gives.

    Order is judged on first occurrences, which is what order means for a list
    whose entries each appear once: a name that has moved ahead of its
    predecessor has changed the sequence a reader consults, even though the set
    of names is untouched. `what` is the singular label for one entry ("chain
    member", "spec.md section"), so a failure says which published list drifted
    rather than only that some order was wrong.
    """
    positions = [text.find(name) for name in names]
    for name, pos in zip(names, positions, strict=True):
        assert pos != -1, f"artifact-family.md is missing {what} {name!r}"
    assert positions == sorted(positions), (
        f"artifact-family.md must name every {what} in the pinned order "
        f"{names}; found at positions {positions}"
    )


def _assert_superseded_names_absent(text: str, names: tuple[str, ...], what: str) -> None:
    """Assert `text` names no entry of `names` anywhere in the document.

    The companion to `_assert_names_in_pinned_order`, and the half that makes it
    mean something: a replaced list and a list the new names were appended to
    both satisfy a pinned order, so only the superseded names' absence
    distinguishes them. Absence is judged over the whole document rather than
    the member's own row, because a placeholder that survived anywhere is a
    second answer to a question this file exists to answer once. `what` is the
    singular label for one entry ("spec.md section"), matching the order helper.
    """
    for name in names:
        assert name not in text, (
            f"artifact-family.md still names the superseded {what} {name!r}; "
            f"the pinned names replace that set rather than extend it"
        )


def test_artifact_family_pins_member_chain_and_provenance_literal() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    # The chain is an order, not a set: prose naming roadmap.md ahead of
    # brief.md would describe a chain that derives members from their own
    # descendants.
    _assert_names_in_pinned_order(text, MEMBERS_IN_CHAIN_ORDER, "chain member")

    # The literal five downstream skills cite must appear exactly once: zero
    # means it was never published, and more than once invites two copies to
    # drift apart from each other.
    occurrences = text.count(PROVENANCE_LITERAL)
    assert occurrences == 1, (
        f"expected the provenance literal {PROVENANCE_LITERAL!r} to appear exactly once, found {occurrences}"
    )

    for heading in REQUIRED_HEADINGS:
        assert heading in text, f"artifact-family.md is missing heading {heading!r}"


def test_artifact_family_pins_brief_sections_and_unknown_marker() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    # The PR-FAQ's three sections are a sequence, not a set: an internal FAQ
    # published ahead of the press release would describe a different format.
    _assert_names_in_pinned_order(text, BRIEF_SECTIONS, "brief.md section")

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

    # The three sections are a sequence, not a set: a spec that ruled scope out
    # before naming the problem would argue backwards.
    _assert_names_in_pinned_order(text, SPEC_SECTIONS, "spec.md section")

    # The self-contained sections replace the technology-shaped placeholder set
    # rather than extend it, so each superseded name must be gone.
    _assert_superseded_names_absent(text, SUPERSEDED_SPEC_SECTIONS, "spec.md section")


def test_artifact_family_pins_roadmap_sections() -> None:
    assert ARTIFACT_FAMILY.exists(), f"missing published contract: {ARTIFACT_FAMILY}"
    text = ARTIFACT_FAMILY.read_text()

    # The three sections are a sequence, not a set: a roadmap that ordered the
    # work before scoring it would have sequenced items it had not yet ranked.
    _assert_names_in_pinned_order(text, ROADMAP_SECTIONS, "roadmap.md section")

    # The scored sections replace the date-shaped placeholder pair rather than
    # extend it, so each superseded name must be gone.
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
