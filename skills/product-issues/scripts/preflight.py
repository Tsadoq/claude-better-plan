#!/usr/bin/env python3
"""Every condition that should stop a batch, checked before the first call.

Filing is the one thing this beat does that cannot be undone, and a batch is
filed one issue at a time. That combination is what this module exists for: a
condition noticed on the seventh slice has already put six issues into a tracker
other people are looking at, with no way back except closing them by hand. So
every question that can be asked without making a call is asked here, together,
before anything is created.

`check` therefore raises rather than reporting. A caller has exactly one decision
to make -- file the batch or do not -- and a returned list of findings is a
decision the caller could get wrong, whereas a raised refusal is one it cannot.
Each check names *every* slice that fails it rather than the first, because the
alternative is a fix-and-rerun loop that reveals the next offender one run at a
time.

What is checked, and why each one is worth a whole batch:

- The unknown marker. A slice carrying it is a slice somebody has not finished
  deciding. Filing the rest and skipping that one is the worst available outcome,
  because the set then looks complete while the piece with the unestablished
  acceptance condition is missing.
- The two GitHub ceilings, 100 sub-issues under one parent and 8 levels of
  nesting. Both are enforced by the server on the call that breaches them, which
  means being discovered mid-batch.
- A slice whose `roadmap_item` names nothing in roadmap.md. The whole chain's
  claim is that every piece of work traces to something upstream, and a slice
  that traces to an id nobody wrote is a slice that entered the set some other
  way.

The marker token itself is read from `artifact-family.md`, which publishes it, and
is deliberately not spelled here: a second copy would keep matching after the
published token moved on, and this check would then pass every document in the
suite.

Standard library only, like every script in this suite. This module holds no
transport and takes none: what it knows about the tracker arrives as data the
caller already read, which is what makes "nothing was called" a property of the
code rather than a promise in a comment.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Siblings are reached the way every script in this suite reaches one: their
# shared directory on the path, anchored on `__file__`. See gh_capability.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gh_capability import Capability  # noqa: E402
from slice_file import Slice  # noqa: E402

# Where the suite publishes the unknown-value marker. Two directories up from
# `scripts/` is `skills/`, the same anchoring product_artifact.py uses to reach
# the plugin root.
ARTIFACT_FAMILY = (
    Path(__file__).resolve().parents[2] / "product-artifacts" / "references" / "artifact-family.md"
)

# The heading in that file whose fenced block is the marker's definition.
MARKER_HEADING = "## Unknown marker"

# GitHub's documented sub-issue limits: 100 children under one parent, and 8
# levels of nesting. The error returned when either is breached is not
# documented, which is the second reason to check rather than to attempt and
# interpret -- there is no status code to branch on afterwards.
MAX_SUB_ISSUES = 100
MAX_NESTING_DEPTH = 8

# What breaching either ceiling mid-batch would have left behind. One sentence
# rather than a branch on `Capability`, because the links are a call of their
# own after the create on every machine there is -- that decision and its
# reasons are github_destination.py's "**Links go through the REST endpoints on
# every path**". A refusal spends a sentence on this because an issue that
# exists and is attached to nothing is what somebody would otherwise have to go
# and find by hand.
BREACH_COST = (
    "Links here are a call made after each create, so the first slice past it would have been filed "
    "and then left unattached"
)

# The id form every roadmap item carries. This is this code's copy of a
# convention published in `skills/product-roadmap/references/rice-template.md`,
# which is that convention's single home; a test pins the two together rather
# than trusting them to stay in step. The marker below is read from its contract
# at run time instead, which is the stronger treatment, and is only possible
# because that contract publishes a literal token rather than a shape.
ROADMAP_ITEM_FORM = "ITEM<n>"

# `ROADMAP_ITEM_FORM` as something to find in a file: `ITEM1`, `ITEM12`. Bounded
# at both ends so `ITEM1` does not match inside `ITEM12`.
_ITEM_ID = re.compile(r"\bITEM\d+\b")

# A fenced block's contents, opening fence to closing fence, both line-initial.
_FENCED = re.compile(r"^```[^\n]*\n(.*?)^```", re.DOTALL | re.MULTILINE)


class PreflightRefusal(RuntimeError):
    """Base for every refusal here, so a caller can catch the family without
    naming each member. Catching it means one thing and nothing else: the batch
    was not filed, and no call was made."""


class UnknownMarkerPresent(PreflightRefusal):
    """A slice still carries the unknown-value marker."""


class SubIssueCeiling(PreflightRefusal):
    """The batch would take the parent past its sub-issue limit."""


class NestingCeiling(PreflightRefusal):
    """The parent already sits as deep as sub-issues may be nested."""


class SliceWithoutUpstream(PreflightRefusal):
    """A slice names a roadmap item that roadmap.md does not carry."""


class MarkerContractUnreadable(PreflightRefusal):
    """The marker could not be read from the file that publishes it.

    A fault in this installation rather than in anybody's slices, and still a
    refusal: a marker check that cannot read the marker would pass every batch,
    including the ones it exists to stop.
    """


@dataclass(frozen=True)
class Parent:
    """The issue a batch would be filed under, as the two ceilings see it.

    `children` is how many sub-issues it already has and `depth` is its own level
    in the sub-issue tree, counting a top-level issue as 1. Both are values the
    caller read from the tracker before planning anything, rather than something
    this module fetches: pre-flight holds no transport, and the dry-run transport
    a planning run holds cannot answer a read at all.
    """

    number: int
    children: int
    depth: int

    @classmethod
    def from_sub_issues(cls, number: int, sub_issues: Sequence[Any], *, depth: int) -> Parent:
        """A parent whose child count is read from what
        `GET /repos/{owner}/{repo}/issues/{number}/sub_issues` returned.

        The count is the length of that list and never `sub_issues_summary.total`
        from the issue payload. The summary is a counter kept alongside the
        issue, and a batch is refused or allowed on the strength of this number,
        so it comes from the collection itself.

        `sub_issues` must be *every* page of that response. The endpoint pages
        like every GitHub list endpoint, at 30 per page by default, while the
        ceiling it feeds is 100: a caller that passes the first page alone
        undercounts by up to 70 children and gets a refusal that never fires,
        which is the exact failure this check exists to prevent. Nothing here can
        detect a truncated list, so the whole of it is the caller's contract.

        `depth` has no default. Nothing in the sub-issues response says how deep
        the parent already sits -- that is a walk up `parent_issue_url`, which
        the caller does -- and a default would leave the nesting ceiling
        unenforced for every caller that forgot to pass one, which is the single
        failure a refusal must not have.
        """
        return cls(number=number, children=len(sub_issues), depth=depth)


def check(slices: Sequence[Slice], capability: Capability, parent: Parent, *, roadmap: Path) -> None:
    """Refuse the batch if anything about it should stop it, or return silently.

    `slices` are the slice files as `slice_file.read_slice` returned them, in the
    order they would be filed; `parent` is the issue they would be filed under;
    `roadmap` is the path to the roadmap.md they were cut from.

    `capability` is read by nothing here, and is named so that a reader stops
    looking for the branch. No refusal depends on it: GitHub enforces both
    ceilings whichever path the call takes, and `BREACH_COST` gives the reason
    the cost is one sentence rather than a branch on this argument. It is kept
    because a create that carried its own links would give it something to
    decide again. Callers pass what they detected and nothing is detected here,
    which is how this module goes on making no calls of its own.

    Raises one of the `PreflightRefusal` family, each naming every slice that
    failed that check. The slice-level checks come first because they name a file
    somebody can open and fix; the ceilings are a property of the destination and
    are the same fault whatever the slices say.
    """
    _refuse_unknown_markers(slices)
    _refuse_slices_without_upstream(slices, roadmap)
    _refuse_ceilings(slices, parent)


def unknown_marker_prefix(contract: Path = ARTIFACT_FAMILY) -> str:
    """The unknown-value marker's opening, read from the file that publishes it.

    The opening -- the token up to and including its colon -- rather than the
    whole literal, because the published literal carries placeholder payload
    (`<what is missing>`) while a document carrying a marker writes its own. The
    opening is the part every real marker shares, and it is also what catches a
    partial copy: a slot carrying the token and its own text has the marker in it
    however little of the definition was pasted.

    Raises `MarkerContractUnreadable` when the file, the heading, the fenced
    block or the colon is missing, rather than returning something empty that
    would match every document ever written.
    """
    try:
        text = contract.read_text(encoding="utf-8")
    except OSError as err:
        raise MarkerContractUnreadable(
            f"{contract} could not be read, and it is where the marker is published: {err}"
        ) from err

    heading = text.find(MARKER_HEADING)
    if heading < 0:
        raise MarkerContractUnreadable(
            f"{contract} has no {MARKER_HEADING!r} heading to read the marker from"
        )

    block = _FENCED.search(text, heading)
    if block is None:
        raise MarkerContractUnreadable(
            f"{contract}'s {MARKER_HEADING!r} section has no fenced block defining the marker"
        )

    opening, colon, _ = block.group(1).strip().partition(":")
    if not opening or not colon:
        raise MarkerContractUnreadable(
            f"the marker {block.group(1).strip()!r} published in {contract} carries no colon, so there is "
            "no opening to look for in a document"
        )
    return opening + colon


def _refuse_unknown_markers(slices: Sequence[Slice]) -> None:
    """Stop the batch when any slice still carries the marker."""
    prefix = unknown_marker_prefix()
    carrying = []
    for one in slices:
        site = _marker_site(one, prefix)
        if site is not None:
            carrying.append(f"{_named(one)} in {site}")

    if carrying:
        raise UnknownMarkerPresent(
            f"the unknown marker {prefix!r} is still in {', '.join(carrying)}, so nothing was filed. "
            "Filing the rest and leaving those behind is worse than filing none: the set would look "
            "complete, and the slices nobody finished deciding are the ones that went missing"
        )


def _refuse_slices_without_upstream(slices: Sequence[Slice], roadmap: Path) -> None:
    """Stop the batch when any slice names an item roadmap.md does not carry."""
    try:
        items = frozenset(_ITEM_ID.findall(roadmap.read_text(encoding="utf-8")))
    except OSError as err:
        raise SliceWithoutUpstream(
            f"no slice can be traced upstream, because {roadmap} could not be read: {err}"
        ) from err

    # `roadmap_item` is in `REQUIRED_KEYS`, so `read_slice` has already refused
    # any slice that lacks it and this lookup cannot fail.
    unmoored = [
        f"{_named(one)} names {one.frontmatter['roadmap_item']}"
        for one in slices
        if one.frontmatter["roadmap_item"] not in items
    ]
    if unmoored:
        raise SliceWithoutUpstream(
            f"{roadmap} carries no such item as {', '.join(unmoored)}. Every slice is cut from an item "
            "there, so an id that file does not carry means either the slice or the roadmap has moved on "
            "without the other"
        )


def _refuse_ceilings(slices: Sequence[Slice], parent: Parent) -> None:
    """Stop the batch when it would breach either GitHub sub-issue limit."""
    if parent.children + len(slices) > MAX_SUB_ISSUES:
        raise SubIssueCeiling(
            f"issue {parent.number} already has {parent.children} sub-issues and this batch adds "
            f"{len(slices)}, past GitHub's ceiling of {MAX_SUB_ISSUES}. {BREACH_COST}. "
            "Split the batch across more than one parent"
        )

    if parent.depth >= MAX_NESTING_DEPTH:
        raise NestingCeiling(
            f"issue {parent.number} already sits at depth {parent.depth}, and GitHub nests sub-issues "
            f"{MAX_NESTING_DEPTH} levels deep, so it can have no children at all. "
            f"{BREACH_COST}. File this batch under a shallower parent"
        )


def _marker_site(one: Slice, prefix: str) -> str | None:
    """Where in `one` the marker first appears, in words, or None when it does
    not. Frontmatter before body, so the answer names a key when it can."""
    for key, value in one.frontmatter.items():
        if prefix in _searchable(value):
            return f"its {key}"
    return "its body" if prefix in one.body else None


def _searchable(value: Any) -> str:
    """A frontmatter value as text to search, spelled the way the file spells
    it: a string as itself, anything structured as the JSON it was written as."""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _named(one: Slice) -> str:
    """One slice as both the things a reader needs: its id, and the file to open."""
    return f"{one.frontmatter['slice']} ({one.path})"
