"""Shared primitives for the plugin's artifact-family scripts.

This module holds every rule two (or more) artifact families -- `docs/plans/`
today, `docs/product/` next -- have in common: slug normalisation and
validation, the generated-region marker convention, and the folder-collision
/ auto-increment check. It carries no knowledge of either family: no member
names, no chain order, no family-specific defaults beyond what a caller
passes in explicitly (see `extra_suffixes` below).

Cross-directory reach contract: this file lives at the plugin root, not next
to any one family's scripts, so every consumer is in a different directory.
A consumer makes this importable by inserting its own `lib/` onto
`sys.path` before importing, anchored on `__file__` so it works regardless of
current working directory:

    sys.path.insert(0, str(Path(__file__).resolve().parents[N] / "lib"))
    import artifact_common

`N` is however many parents separate the consumer script from the plugin
root. Do not rely on the `CLAUDE_PLUGIN_ROOT` environment variable for this:
it is set by the Claude Code harness for skill/agent invocations, but these
scripts also run as plain `python3` subprocesses (from tests, from each
other, from a shell), where that variable is not exported.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

# --------------------------------------------------------------------------
# Slugs
# --------------------------------------------------------------------------

# Kept short so a slug is always a reasonable filename/folder-name component;
# not tied to any filesystem limit, just a sanity bound on user input.
MAX_SLUG_LEN = 60
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalise_slug(raw: str) -> str:
    """Lowercase, collapse non-alphanumerics to single hyphens, trim, and
    cap at `MAX_SLUG_LEN`.

    The post-truncation `rstrip("-")` matters: slicing at `MAX_SLUG_LEN` can
    land mid-hyphen-run, and a trailing hyphen would otherwise make the
    result fail `SLUG_RE`/`is_valid_slug`.
    """
    s = raw.strip().lower()
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    if len(s) > MAX_SLUG_LEN:
        s = s[:MAX_SLUG_LEN].rstrip("-")
    return s


def is_valid_slug(s: str) -> bool:
    """Whether `s` is already normalised: non-empty, at most `MAX_SLUG_LEN`
    chars, and matching `SLUG_RE` (lowercase alphanumerics, single hyphens,
    no leading/trailing hyphen)."""
    if not s or len(s) > MAX_SLUG_LEN:
        return False
    return bool(SLUG_RE.match(s))


# --------------------------------------------------------------------------
# Generated regions
# --------------------------------------------------------------------------


class Markers(NamedTuple):
    begin: str
    end: str


def markers(name: str) -> Markers:
    """The begin/end marker pair for a generated region named `name`.

    Markers are HTML comments so they render invisibly in the rendered
    markdown: `<!-- {name}-index:begin generated: do not edit -->` and
    `<!-- {name}-index:end -->`.
    """
    return Markers(
        begin=f"<!-- {name}-index:begin generated: do not edit -->",
        end=f"<!-- {name}-index:end -->",
    )


def build_table_region(markers: Markers, columns: Sequence[str], rows: Sequence[str]) -> str:
    """A marker-delimited table region: begin marker, header, dash
    separator, the given rows, end marker, one per line."""
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    return "\n".join([markers.begin, header, separator, *rows, markers.end])


def splice_region(text: str, markers: Markers, region: str) -> str:
    """Replace the region between `markers` in `text` with `region`.

    When either marker is absent, `region` is appended after an `rstrip`
    plus a blank line, matching `regenerate_index`'s current fallback.
    """
    begin = text.find(markers.begin)
    end = text.find(markers.end)
    if begin != -1 and end != -1 and end > begin:
        return text[:begin] + region + text[end + len(markers.end) :]
    return text.rstrip() + "\n\n" + region + "\n"


# --------------------------------------------------------------------------
# Folder collisions
# --------------------------------------------------------------------------


def slug_taken(directory: Path, slug: str, extra_suffixes: Sequence[str] = ()) -> bool:
    """Whether `slug` collides with an existing folder or, per
    `extra_suffixes`, a legacy flat-file form (e.g. `.md`) in `directory`.
    """
    if (directory / slug).exists():
        return True
    return any((directory / f"{slug}{suffix}").exists() for suffix in extra_suffixes)


def next_v_suffix(directory: Path, slug: str, extra_suffixes: Sequence[str] = ()) -> str:
    """The first `slug` or `slug-vN` not taken in `directory`."""
    candidate = slug
    n = 2
    while slug_taken(directory, candidate, extra_suffixes):
        candidate = f"{slug}-v{n}"
        n += 1
        if n > 999:
            return f"{slug}-v{n}"
    return candidate
