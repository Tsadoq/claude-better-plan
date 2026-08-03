"""Pins the plugin to a single unknown-marker dialect across every skill.

Epic constraint 9 says the plugin publishes one literal for "nobody has
established this value yet". That constraint spans skills, so no per-skill
contract test can own it: `product-artifacts` cannot notice that
`product-brief` forked a second token, and vice versa. This module is the
cross-skill half of that split.

Two things are deliberately left to their owners. Occurrence counts belong to
`skills/product-artifacts/tests/test_artifact_family_contract.py`, which owns
"the literal appears exactly once in artifact-family.md"; this module asserts
only that the *set* of dialects in use has one member. The token's spelling
belongs to that same test, so the expectation here is read out of the
substrate rather than restated -- a third copy of `UNKNOWN` in the repo would
only add somewhere for the definition and its guard to drift apart while both
stayed green.

Runnable two ways:
    python3 -m pytest tests/test_marker_uniqueness.py
    uvx pytest tests/test_marker_uniqueness.py -q
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Scoped to this plugin's own tree rather than the working directory: the
# skill runs inside user repositories, and one of them adopting spec-kit --
# whose marker is `[NEEDS CLARIFICATION: ...]` -- must not turn this suite red
# over files the plugin does not ship.
SKILLS = REPO / "skills"

# The substrate is the canonical home of the marker token, so it is also what
# says which dialect the rest of the tree must match.
DIALECT_DEFINITION = SKILLS / "product-artifacts" / "references" / "artifact-family.md"
DIALECT_HEADING = "## Unknown marker"

# The shape every marker dialect shares: an opening bracket, an all-caps token
# that may span words, then a colon introducing the payload. Requiring the
# colon and at least three characters is what keeps prose out -- an ordinary
# sentence containing "[A]" or a citation like "[RFC 2119]" cannot match.
MARKER_TOKEN = re.compile(r"\[([A-Z][A-Z ]{2,}):")


def _published_dialect(definition: Path) -> str:
    """The marker token the substrate publishes, read from its own definition.

    Returns "" when the definition cannot be read, which the caller must
    guard: an expectation derived from nothing would compare the tree against
    an empty token and pass on a tree that had forked in every file.
    """
    text = definition.read_text()
    start = text.find(DIALECT_HEADING)
    if start == -1:
        return ""
    section = text[start:]
    # Bounded at the next H2 so a token introduced by some later section
    # cannot be mistaken for the published one.
    end = section.find("\n## ", len(DIALECT_HEADING))
    match = MARKER_TOKEN.search(section if end == -1 else section[:end])
    return "" if match is None else match.group(1)


def _scan_marker_tokens(root: Path) -> dict[str, tuple[Path, int]]:
    """Map every marker token under `root` to where it was first introduced.

    Insertion order follows a sorted walk, so the reported location for a
    token is stable across runs and machines rather than filesystem-dependent.
    """
    first_seen: dict[str, tuple[Path, int]] = {}
    for markdown in sorted(root.rglob("*.md")):
        for lineno, line in enumerate(markdown.read_text().splitlines(), start=1):
            for match in MARKER_TOKEN.finditer(line):
                first_seen.setdefault(match.group(1), (markdown, lineno))
    return first_seen


def _describe(found: dict[str, tuple[Path, int]], expected: str) -> str:
    """Explain a failed scan, naming the file and line that broke it.

    Also owns the case where `expected` came back empty. An unreadable
    definition cannot match any real token, so the comparison fails on its
    own; this only replaces the bewildering message that would otherwise
    report every shipped marker as unexpected against a token of "".
    """
    if not expected:
        return (
            f"no marker token could be read from {DIALECT_HEADING!r} in "
            f"{DIALECT_DEFINITION.relative_to(REPO)}, so there is no published "
            "dialect to hold the rest of the tree to. Whether that file is "
            "still well formed belongs to its own contract test; this one "
            "needs it only to know what to compare against."
        )
    if not found:
        return (
            f"no marker token matched anywhere under {SKILLS.relative_to(REPO)}/, "
            f"though {DIALECT_DEFINITION.relative_to(REPO)} publishes "
            f"`[{expected}: ...]`. Either the skills stopped carrying the marker "
            "or this scan is pointed at the wrong tree."
        )
    lines = []
    for token, (path, lineno) in sorted(found.items()):
        role = "published" if token == expected else "UNEXPECTED"
        lines.append(f"  [{token}:  {role}, first seen at {path.relative_to(REPO)}:{lineno}")
    return (
        f"the plugin must use exactly one unknown-marker dialect, the "
        f"`[{expected}: ...]` published by {DIALECT_DEFINITION.relative_to(REPO)}, "
        f"but the shipped skills use {len(found)}:\n" + "\n".join(lines)
    )


def test_marker_scanner_matches_a_rival_dialect() -> None:
    """The scan below is only as good as the pattern driving it.

    A pattern that silently matched nothing would report a clean tree
    forever, so its ability to see a competing dialect is pinned separately:
    a failure here means the scan proves nothing, not that a fork shipped.
    """
    rival = "[NEEDS CLARIFICATION: which pricing tier -- ask the PM]"

    matches = MARKER_TOKEN.findall(rival)

    assert matches == ["NEEDS CLARIFICATION"], (
        f"the marker scanner failed to match {rival!r}, so a clean scan of the "
        "skills tree would prove nothing about which dialects are in use"
    )


def test_only_one_unknown_marker_dialect_exists() -> None:
    expected = _published_dialect(DIALECT_DEFINITION)

    found = _scan_marker_tokens(SKILLS)

    assert set(found) == {expected}, _describe(found, expected)
