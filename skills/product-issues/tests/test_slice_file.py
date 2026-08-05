"""Unit tests for slice_file.py, the slice frontmatter reader and writer.

A slice file is the beat's record of what was decided and, once filed, of where
that decision went. The write that records a filing therefore has to be
surgical. `test_write_filed_entry_round_trips_and_preserves_body` pins the three
things that makes it: the record decodes back as JSON with its integers still
integers, the body bytes are the ones that went in, and the keys that were
already there keep their order with exactly one appended. The body assertion
compares raw bytes and computes the expected body by splitting the source text
itself, never by asking `slice_file` where the body starts -- the module's own
idea of that boundary is the thing under test.

The second test pins the refusals, one file per shape the format rejects, each
checked against the line its message has to name. The nested case is the one the
design singles out: an indented line is an error rather than something to skip
past, because silently ignoring a nested block is how a format that merely looks
like YAML starts being written as YAML.

Real files under `tmp_path` throughout, and nothing is patched.

Runnable two ways:
    python3 -m pytest skills/product-issues/tests/test_slice_file.py
    uv run --no-project pytest skills/product-issues/tests/test_slice_file.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Registered before it is executed, for the reason test_issue_transport.py's
    # loader gives: `@dataclass` resolves the string annotations that
    # `from __future__ import annotations` produces through
    # `sys.modules[cls.__module__]`, and an unregistered module makes that
    # lookup return None mid-decoration.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


slice_file = _load("slice_file")

# A slice as the beat writes one: every required key, a JSON list among them so
# the structured half of the format is exercised, and a body of two sections.
SLICE_TEXT = """\
---
slice: SLICE-03
title: Narrow the roster to one cohort
activity: Review a cohort
roadmap_item: ITEM2
labels: ["product-issues", "size/S"]
---

## Context

The roster lists every learner at once, so a coach scrolls past four cohorts to
reach their own.

## Acceptance criteria

- picking a cohort leaves only that cohort's learners on the page
"""

# The keys above, in the order the file states them.
SLICE_KEYS = ["slice", "title", "activity", "roadmap_item", "labels"]

# Everything after the closing fence, cut out of SLICE_TEXT rather than restated
# below it, so that editing the slice above cannot leave the expectation behind.
EXPECTED_BODY = SLICE_TEXT.split("---\n", 2)[2]

# A filed record in its real shape. The id is the one captured from a real issue
# of this repository and is nine orders of magnitude away from any issue number,
# so a write that turned it into text, or that stored the number under `id`,
# fails here rather than at the first attempt to link a sub-issue.
FILED_GITHUB = {
    "number": 42,
    "id": 5046900288,
    "url": "https://github.com/Tsadoq/claude-better-plan/issues/42",
}

# A markdown file that is not a slice at all, which is what a stray note left in
# the issues folder looks like to the reader.
UNFENCED_TEXT = """\
# Slice 04

No frontmatter block, so there is nothing here to file.
"""

# The same slice written by somebody who assumed the block was YAML. Line 6
# opens `labels:` and line 7 continues it as a nested list item.
NESTED_TEXT = """\
---
slice: SLICE-05
title: Narrow the roster to one cohort
activity: Review a cohort
roadmap_item: ITEM2
labels:
  - product-issues
---

## Context

Written as if the frontmatter were YAML, which it is not.
"""

# Prose smuggled into the block: line 7 is a sentence rather than a pair.
UNPAIRED_TEXT = """\
---
slice: SLICE-06
title: Narrow the roster to one cohort
activity: Review a cohort
roadmap_item: ITEM2
labels: []
blocked by SLICE-05
---

## Context

Ordering belongs in the body, not in the frontmatter.
"""

# Every shape this format refuses, with the line each refusal has to name.
REFUSED = [
    ("no frontmatter fence", UNFENCED_TEXT, 1),
    ("a nested key", NESTED_TEXT, 7),
    ("a line that is not a pair", UNPAIRED_TEXT, 7),
]


def test_write_filed_entry_round_trips_and_preserves_body(tmp_path: Path) -> None:
    path = tmp_path / "slice-03.md"
    path.write_bytes(SLICE_TEXT.encode("utf-8"))

    slice_file.write_filed_entry(path, "github", FILED_GITHUB)

    frontmatter = slice_file.read_slice(path).frontmatter
    assert list(frontmatter) == [*SLICE_KEYS, "filed_github"], (
        f"the write was meant to append exactly one key and leave the rest in order, "
        f"and instead left {list(frontmatter)}"
    )
    assert frontmatter["filed_github"]["id"] == 5046900288, (
        f"the database id did not survive the write as the integer it was: "
        f"{frontmatter['filed_github']['id']!r}"
    )
    assert frontmatter["filed_github"] == FILED_GITHUB, (
        f"the filed record came back changed, so a later run would read a different issue "
        f"than the one that was created: {frontmatter['filed_github']!r}"
    )
    assert path.read_bytes().split(b"---\n", 2)[2] == EXPECTED_BODY.encode("utf-8"), (
        "the body bytes changed; recording a filing may touch the frontmatter and nothing else"
    )


@pytest.mark.parametrize(("fault", "text", "line"), REFUSED, ids=[case[0] for case in REFUSED])
def test_a_file_this_format_cannot_read_is_refused_at_its_offending_line(
    fault: str, text: str, line: int, tmp_path: Path
) -> None:
    path = tmp_path / "slice-xx.md"
    path.write_bytes(text.encode("utf-8"))

    with pytest.raises(slice_file.SliceFormatError) as caught:
        slice_file.read_slice(path)

    assert caught.value.line == line, (
        f"a slice with {fault} was refused at line {caught.value.line} rather than line {line}, "
        f"so the message sends the reader to the wrong place in the file"
    )
    assert str(path) in str(caught.value), (
        f"the refusal does not say which file it was reading: {caught.value}"
    )
