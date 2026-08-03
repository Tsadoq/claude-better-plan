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
