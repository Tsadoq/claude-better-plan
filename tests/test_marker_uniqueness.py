
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SKILLS = REPO / "skills"

DIALECT_DEFINITION = SKILLS / "product-artifacts" / "references" / "artifact-family.md"
DIALECT_HEADING = "## Unknown marker"

MARKER_TOKEN = re.compile(r"\[([A-Z][A-Z ]{2,}):")


def _published_dialect(definition: Path) -> str:
    text = definition.read_text()
    start = text.find(DIALECT_HEADING)
    if start == -1:
        return ""
    section = text[start:]
    end = section.find("\n## ", len(DIALECT_HEADING))
    match = MARKER_TOKEN.search(section if end == -1 else section[:end])
    return "" if match is None else match.group(1)


def _scan_marker_tokens(root: Path) -> dict[str, tuple[Path, int]]:
    first_seen: dict[str, tuple[Path, int]] = {}
    for markdown in sorted(root.rglob("*.md")):
        for lineno, line in enumerate(markdown.read_text().splitlines(), start=1):
            for match in MARKER_TOKEN.finditer(line):
                first_seen.setdefault(match.group(1), (markdown, lineno))
    return first_seen


def _describe(found: dict[str, tuple[Path, int]], expected: str) -> str:
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
