#!/usr/bin/env python3
"""One slice file's frontmatter, read and amended without disturbing its body.

A slice is a single unit of work cut from a roadmap item and written as one
markdown file under `docs/product/<slug>/issues/`. Its opening `---` block is a
flat sequence of `key: value` lines whose structured values are JSON:

    ---
    slice: SLICE-03
    title: Narrow the roster to one cohort
    activity: Review a cohort
    roadmap_item: ITEM2
    labels: ["product-issues", "size/S"]
    filed_github: {"number": 42, "id": 5046900288, "url": "https://..."}
    ---

Flat rather than nested, because every script in this suite is standard library
only: there is no YAML parser to reach for, while `json.loads` and `json.dumps`
are both there and round-trip exactly. That is also why an indented line is a
refusal here rather than something to skip. A format that merely looks like YAML
would otherwise start being written as YAML, and the first nested block would be
read as half a slice by code that reported no problem.

The second half of this module is the ledger. Once a slice has been filed, its
`filed_<destination>` key records the issue that now exists, and a later run
reads that key to know it has nothing left to do for this slice. That key's name
is composed from the destination rather than fixed, and `Slice.filed` and
`write_filed_entry` are the pair that compose it, so a caller names a
destination and never a key. `write_filed_entry` is held to a narrow
contract in return: it adds or replaces exactly that one key, leaves the other
keys in the order the file already had, and leaves the body bytes alone. The
body is editorial text a person wrote and a person approved, and nothing in this
beat is entitled to reformat it.

`REQUIRED_KEYS` is this code's copy of a schema published in
`references/story-map-template.md`, which is that schema's single home; a
contract test pins the two together rather than trusting them to stay in step.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# The line that opens and closes the frontmatter block.
FENCE = "---"

# Every ledger key is this prefix followed by a destination name. It sits here
# because `write_filed_entry` and `Slice.filed` compose the key between them,
# and a caller that named one itself would be spelling this module's format.
FILED_PREFIX = "filed_"

# The keys every slice carries, in the order a slice states them. This is the
# code's copy of the schema published in `references/story-map-template.md`:
#
#   slice         the slice's own id, stable across runs and never renumbered
#   title         the one-line title the issue is filed under
#   activity      the story map backbone activity this slice sits under
#   roadmap_item  the `ITEM` id in roadmap.md that this slice was cut from
#   labels        a JSON list of label names to apply at the destination
#
# A `milestone` and any `filed_<destination>` entry are optional and so are
# absent from this tuple: a slice is complete before anything has been filed.
REQUIRED_KEYS: tuple[str, ...] = ("slice", "title", "activity", "roadmap_item", "labels")


class SliceFormatError(ValueError):
    """A slice file this module will not read, named down to the line.

    Whoever sees this message is usually about to open the file and fix it by
    hand, so the file and the offending line are carried as fields as well as
    being written into the message. `line` is None for a fault the file has as a
    whole -- an unclosed block, a missing key -- which has no one line to blame.
    """

    def __init__(self, path: Path, line: int | None, detail: str) -> None:
        self.path = path
        self.line = line
        self.detail = detail
        where = f":{line}" if line is not None else ""
        super().__init__(f"{path}{where}: {detail}")


@dataclass(frozen=True)
class Slice:
    """One slice file, split into the part this module owns and the part it does not.

    `frontmatter` maps every key to its value in the order the file states them,
    with JSON values decoded and every other value left the string it was. The
    keys a person wrote -- `title`, `labels`, `roadmap_item` -- are read straight
    out of it. A `filed_` entry is the exception, because its key is composed
    from a destination rather than fixed: ask `filed` for one, so that only this
    module ever spells the ledger key.

    `body` is the file's text from just past the closing fence to its end, held
    unparsed: it is what becomes the issue body, and this module's only duty
    towards it is to hand it back unchanged.
    """

    path: Path
    frontmatter: dict[str, Any]
    body: str

    def filed(self, destination: str) -> dict[str, Any] | None:
        """What a previous run recorded when it filed this slice to
        `destination`, or None when no run has. A record in hand means the issue
        already exists there and this run must skip the slice rather than create
        a second one."""
        return self.frontmatter.get(_filed_key(destination))


def read_slice(path: Path) -> Slice:
    """`path` parsed into its frontmatter and its body.

    Raises `SliceFormatError` for everything this format does not accept: a
    missing or unclosed fence, a line that is not one `key: value` pair, an
    indented line, a repeated key, a JSON value that does not parse, and a
    missing required key. A returned `Slice` therefore already carries every key
    in `REQUIRED_KEYS`, and every `filed_` entry in it is a JSON object, which is
    what spares callers from checking either.
    """
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as err:
        raise SliceFormatError(path, None, f"is not valid UTF-8: {err}") from err

    # A carriage return is dropped at each comparison below rather than out of
    # `lines` here, because the body is rejoined from this same list: normalising
    # it once would be normalising somebody's file on their behalf.
    lines = text.split("\n")
    if lines[0].rstrip("\r") != FENCE:
        raise SliceFormatError(path, 1, f"does not open with a {FENCE!r} fence, so it carries no frontmatter")
    closing = _closing_fence(path, lines)

    frontmatter: dict[str, Any] = {}
    for offset, raw in enumerate(lines[1:closing]):
        line = offset + 2  # past the opening fence, counting from 1
        key, value = _pair(path, line, raw.rstrip("\r"))
        if key in frontmatter:
            raise SliceFormatError(path, line, f"repeats {key!r}, so one of the two values would be lost")
        frontmatter[key] = value

    missing = [key for key in REQUIRED_KEYS if key not in frontmatter]
    if missing:
        raise SliceFormatError(path, None, f"is missing {', '.join(missing)}, which every slice must carry")

    # `split` and `join` on the same separator are exact inverses, so this is
    # the file's own text after the closing fence rather than a rebuild of it.
    return Slice(path=path, frontmatter=frontmatter, body="\n".join(lines[closing + 1 :]))


def write_filed_entry(path: Path, destination: str, record: Mapping[str, Any]) -> None:
    """Record in `path` that this slice now exists at `destination`.

    Adds `filed_<destination>` carrying `record`, or replaces it in place when a
    previous run left one, and touches nothing else: the other keys keep the
    order the file had them in, and the body keeps its bytes.

    Every value in `record` must be JSON-serialisable, since the entry is written
    as a JSON object and read back as one; anything else raises `TypeError` from
    the encoder rather than a `SliceFormatError`, because it is a fault in the
    calling code and not in the file.

    Called the moment a create succeeds rather than once a batch is done. A run
    that dies halfway is the case this record exists for, so what it leaves
    behind has to be true of every slice it got through and of no other.
    """
    current = read_slice(path)
    frontmatter = dict(current.frontmatter)
    # Assignment leaves an existing key where it was and appends a new one,
    # which is exactly the ordering rule this function promises.
    frontmatter[_filed_key(destination)] = dict(record)

    rendered = "".join(f"{key}: {_rendered(value)}\n" for key, value in frontmatter.items())
    _overwrite(path, f"{FENCE}\n{rendered}{FENCE}\n{current.body}")


def _filed_key(destination: str) -> str:
    """The ledger key for `destination`, spelled once so that what one run writes
    and what the next run looks for cannot drift apart."""
    return f"{FILED_PREFIX}{destination}"


def _closing_fence(path: Path, lines: list[str]) -> int:
    """The index of the line closing the frontmatter block."""
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r") == FENCE:
            return index
    raise SliceFormatError(path, None, f"frontmatter block is never closed by a {FENCE!r} line")


def _pair(path: Path, line: int, text: str) -> tuple[str, Any]:
    """One frontmatter line as its key and its decoded value."""
    if not text.strip():
        raise SliceFormatError(path, line, "is blank; every line between the fences is one `key: value` pair")
    if text[0].isspace():
        raise SliceFormatError(
            path,
            line,
            "is indented, and this frontmatter is flat. Nested blocks are refused rather than skipped, so "
            "that a file written as if it were YAML is never quietly read as half of one",
        )

    key, separator, value = text.partition(":")
    key = key.rstrip()
    if not separator or not key or key.split() != [key]:
        raise SliceFormatError(path, line, f"is not one `key: value` pair: {text!r}")
    return key, _decoded(path, line, key, value.strip())


def _decoded(path: Path, line: int, key: str, text: str) -> Any:
    """`text` as JSON when it opens as an object or an array, and as the string
    it already is otherwise.

    Only those two openings count as structure, so a title holding a number, a
    colon or a bracket mid-sentence stays the sentence somebody wrote. A value
    that opens as JSON and then fails to parse is an error rather than a string:
    a truncated ledger entry that quietly became text would report the slice as
    filed while saying nothing about where.
    """
    value: Any = text
    if text[:1] in ("{", "["):
        try:
            value = json.loads(text)
        except json.JSONDecodeError as err:
            detail = f"{key!r} opens as JSON and does not parse: {err.msg}"
            raise SliceFormatError(path, line, detail) from err

    if key.startswith(FILED_PREFIX) and not isinstance(value, dict):
        raise SliceFormatError(path, line, f"{key!r} must be a JSON object recording the filed issue")
    return value


def _rendered(value: Any) -> str:
    """A value written the way `read_slice` will read it back: a string as
    itself, anything structured as JSON. `ensure_ascii` is off because the file
    is UTF-8 and a label in somebody's own alphabet should stay readable in it."""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _overwrite(path: Path, text: str) -> None:
    """Replace `path`'s contents in one step.

    A slice must never be observable half-written. This is the file that answers
    whether an issue was already created, and a truncated one read by the next
    run is worse than no record at all, so a neighbouring temporary file is
    renamed over the original: an atomic operation within one filesystem, which
    the two paths necessarily share.

    `newline=""` stops the text's line endings being translated on the way out,
    so the body leaves as the bytes that arrived.
    """
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    try:
        os.replace(temporary, path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
