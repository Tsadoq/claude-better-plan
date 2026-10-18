from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

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
