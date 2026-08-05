#!/usr/bin/env python3
"""A slice set turned into the ordered GitHub calls that create and link it.

Filing a batch is not a loop over creates. Labels have to exist before an issue
names one, a milestone has to be looked up before an issue can be filed against
it, and a link can only be sent once the issue it points at exists. That
ordering is this module's subject, and it is why the batch is one function
rather than a set of steps a caller sequences: a caller that got the order wrong
would find out from GitHub, halfway through a set of issues that cannot be
un-filed.

Every call goes through the `Transport` port, so the same code files, previews
under `DryRunTransport`, and runs offline in the tests. Two consequences of that
are worth stating because they are what keep the three paths honest:

- Creating an issue is delegated to `transport.create_issue`, which hands back a
  normalised `Filed`. Nothing here learns that `RestTransport` reads `id` and
  `number` off the 201 while `GhTransport` parses the number out of the URL that
  `gh issue create` prints and then fetches the id, `gh issue create` having no
  `--json` flag. That is also the only paced call in the beat -- GitHub's
  secondary limit caps content creation at 80 a minute -- which is why creates
  are never spelled here as a `run`.
- What a call is *spelled* as depends on `Capability`, not on which transport is
  in hand. `ensure_labels` is the one place the two spellings differ, and it
  reads the capability the caller detected, so a dry run describes the calls the
  real path would make rather than the calls its own transport could make.

**Links go through the REST endpoints on every path.** `gh` 2.94.0 added
`--parent` and `--blocked-by` to `gh issue create`, which take issue numbers and
so need no database id, and the plan intended those flags to replace the two
linking calls on a new-enough CLI. They cannot be reached from here: the port's
`create_issue` carries a title and a body and nothing else, so passing them
would mean spelling `gh issue create` as an argv invocation in this module,
which would duplicate that transport's URL-to-number-to-id normalisation and,
worse, step around the create pacing that lives behind `create_issue`. The
REST endpoints work identically on both paths -- `gh api` reaches them on a
2.82.0 -- so the flags are an optimisation of two calls per issue, not a
capability this beat would otherwise lack. Giving `create_issue` the links
belongs to `issue_transport.py`.

The two linking endpoints look alike and are not. Sub-issues take
`{"sub_issue_id": <id>}` and dependencies take `{"issue_id": <id>}`; both mean
the internal database id and neither means the issue number, while the issue in
the URL path is always a number. Getting either wrong is silent -- GitHub
ignores an unknown field -- which is why the two are separate named functions
rather than one parameterised call.

Standard library only, like every script in this suite.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Siblings are reached the way every script in this suite reaches one: their
# shared directory on the path, anchored on `__file__`. See gh_capability.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gh_capability import Capability  # noqa: E402
from issue_transport import CallFailed, Filed, Invocation, Transport  # noqa: E402
from slice_file import Slice  # noqa: E402

# The destination this module files to. It is also what composes the ledger key
# in a slice's frontmatter, so a caller passes this to `Slice.filed` and to
# `slice_file.write_filed_entry` rather than spelling `filed_github` anywhere.
DESTINATION = "github"

# GitHub's answer to creating something whose name is taken. For a label that is
# the state this module wanted, so it is read as success rather than as failure.
ALREADY_EXISTS = 422

# One page of milestones is 30 by default and 100 at most. A repository with
# more than this many is the one case where an existing milestone can go unseen
# here; the create that follows then fails with GitHub's own already-exists
# message, which is a stop rather than an issue filed against the wrong one.
MILESTONE_PAGE = 100

# The milestone number carried when the transport described the call instead of
# making it, which is the dry run: it answers no body, so no number exists to
# read. Negative for the same reason `DryRunTransport`'s placeholder issue
# numbers are -- nothing real is ever numbered this way, so a placeholder that
# reached a report is unmistakable there.
UNRESOLVED_MILESTONE = -1


class SliceNotFilable(ValueError):
    """A slice this module will not turn into an issue.

    Two things trigger it. A frontmatter value that is not the shape the
    published schema gives it -- `labels` that is not a list of strings, a
    `milestone` that is not a title -- because guessing at one would file
    something nobody wrote. And a slice that already carries a
    `filed_github` entry, because filing is the one action here that cannot be
    undone and a second create would leave two issues where the ledger names
    one. Callers skip already-filed slices; this refuses the ones that get
    through anyway.
    """


def ensure_labels(
    transport: Transport, repo: str, names: Iterable[str], *, capability: Capability
) -> None:
    """Make sure `repo` carries a label for every name in `names`.

    Once for the whole batch and before the first create: a repository label is
    shared by every issue that names it, so ensuring it per slice would be one
    wasted call per slice per label.

    The two paths differ in more than spelling. `gh label create --force`
    creates or updates and reports success either way, so the CLI path needs no
    existence check. The REST path has no equivalent and answers a name already
    taken with a 422, which is read here as the label existing -- the outcome
    asked for -- while every other failure is left to raise.
    """
    for name in dict.fromkeys(names):
        if capability.usable:
            transport.run(
                Invocation(
                    summary=f"create or update the label {name!r} in {repo}",
                    argv=("gh", "label", "create", name, "--repo", repo, "--force"),
                )
            )
            continue

        try:
            transport.run(
                Invocation(
                    summary=f"create the label {name!r} in {repo}",
                    method="POST",
                    url=f"repos/{repo}/labels",
                    # Name only. Colour is what `--force` exists to update on
                    # the other path, and inventing one here would repaint a
                    # label somebody chose a colour for.
                    body={"name": name},
                )
            )
        except CallFailed as err:
            if err.status != ALREADY_EXISTS:
                raise


def ensure_milestone(transport: Transport, repo: str, title: str) -> int:
    """The number of `repo`'s milestone called `title`, created if it has none.

    Reads before writing, unlike `ensure_labels`, and not out of caution: an
    issue is filed against a milestone's *number*, so the number has to be
    learned whether or not the create happens. There is no `gh milestone`
    command, so both paths take the same REST call.
    """
    existing = _milestone_numbers(transport, repo)
    if title in existing:
        return existing[title]

    created = transport.run(
        Invocation(
            summary=f"create the milestone {title!r} in {repo}",
            method="POST",
            url=f"repos/{repo}/milestones",
            body={"title": title},
        )
    )
    return _number(created.json)


def link_child(transport: Transport, repo: str, parent: int, child_id: int) -> None:
    """Make the issue whose database id is `child_id` a sub-issue of issue
    number `parent`.

    The two integers are different kinds and are not interchangeable: the URL
    names the parent by the number a person reads, and the body names the child
    by the internal id, which is the only thing this endpoint accepts.
    """
    transport.run(
        Invocation(
            summary=f"add the issue with database id {child_id} as a sub-issue of {repo}#{parent}",
            method="POST",
            url=f"repos/{repo}/issues/{parent}/sub_issues",
            body={"sub_issue_id": child_id},
        )
    )


def link_blocked_by(transport: Transport, repo: str, issue: int, blocker_id: int) -> None:
    """Record issue number `issue` as blocked by the issue whose database id is
    `blocker_id`.

    Issue dependencies are a mechanism of their own, not a flavour of
    sub-issues: a separate endpoint, and a body key of its own (`issue_id`, not
    `sub_issue_id`) for the same database id. `file_slices` does not call this,
    because the published slice schema carries no blocker key -- ordering lives
    in a slice body's `## Blocked by` section -- so it is here for the caller
    that has resolved blockers to ids and wants them recorded as links.
    """
    transport.run(
        Invocation(
            summary=f"record {repo}#{issue} as blocked by the issue with database id {blocker_id}",
            method="POST",
            url=f"repos/{repo}/issues/{issue}/dependencies/blocked_by",
            body={"issue_id": blocker_id},
        )
    )


def file_slices(
    transport: Transport,
    repo: str,
    slices: Sequence[Slice],
    *,
    capability: Capability,
    parent: int | None = None,
) -> Iterator[tuple[Slice, Filed]]:
    """File every slice into `repo` in the order given, under issue number
    `parent` when there is one.

    A generator, and that is the interface rather than an implementation
    detail: each slice is yielded the moment its issue exists and before the
    next create begins, so a caller writing its ledger entry on each iteration
    is writing a record that is true of every slice that got through and of no
    other. A run killed mid-batch leaves exactly that. The corollary is that
    nothing is filed until the caller iterates.

    Every slice is read and checked before the first call goes out, so a batch
    this module will not file is refused while the repository is still
    untouched. Already-filed slices are refused rather than skipped -- see
    `SliceNotFilable`. Deciding which slices a run should file is the caller's,
    since only it knows whether a ledger entry means "done" or "do again"; this
    only refuses to be the place a duplicate is created.
    """
    batch = [_checked(one) for one in slices]
    ensure_labels(
        transport, repo, [name for entry in batch for name in entry.labels], capability=capability
    )

    milestones: dict[str, int] = {}
    for entry in batch:
        title = entry.milestone
        if title is not None and title not in milestones:
            milestones[title] = ensure_milestone(transport, repo, title)
        yield entry.slice, _file(
            transport,
            repo,
            entry,
            parent=parent,
            milestone=None if title is None else milestones[title],
        )


@dataclass(frozen=True)
class _Checked:
    """One slice that this module has agreed to file, with the two frontmatter
    values a create needs already read out of it.

    Reading them into a value up front is what lets the whole batch be refused
    before anything is created: a slice whose `labels` are unusable is found
    while the repository is still untouched, rather than after the labels of the
    slices before it have been made.
    """

    slice: Slice
    labels: list[str]
    milestone: str | None


def _checked(one: Slice) -> _Checked:
    """`one` read into the terms filing needs, or a refusal to file it."""
    if one.filed(DESTINATION) is not None:
        raise SliceNotFilable(
            f"{_named(one)} already records a {DESTINATION} issue, so filing it would create a "
            "second one that no ledger entry names. Drop it from the batch, or clear its "
            f"{DESTINATION} entry if the issue it names is gone"
        )
    return _Checked(slice=one, labels=_labels(one), milestone=_milestone(one))


def _file(
    transport: Transport, repo: str, entry: _Checked, *, parent: int | None, milestone: int | None
) -> Filed:
    """One slice's create, then everything that has to happen after it."""
    one = entry.slice
    filed = transport.create_issue(repo, str(one.frontmatter["title"]), one.body)

    attributes = _attributes(entry.labels, milestone)
    if attributes:
        # A single edit rather than a call per attribute, and after the create
        # rather than on it: the port's create carries a title and a body, and
        # labels and milestones are the same call on both paths.
        transport.run(
            Invocation(
                summary=f"set {' and '.join(attributes)} on {repo}#{filed.number}",
                method="PATCH",
                url=f"repos/{repo}/issues/{filed.number}",
                body=attributes,
            )
        )

    if parent is not None:
        link_child(transport, repo, parent, filed.id)
    return filed


def _attributes(labels: Sequence[str], milestone: int | None) -> dict[str, Any]:
    """What the edit after a create has to set, leaving out what the slice did
    not ask for. An absent key is untouched; a null one would clear what is
    there, which is why neither is sent as an empty value."""
    attributes: dict[str, Any] = {}
    if labels:
        attributes["labels"] = list(labels)
    if milestone is not None:
        attributes["milestone"] = milestone
    return attributes


def _labels(one: Slice) -> list[str]:
    """The label names `one` asks for.

    Refused rather than coerced when the value is not the JSON list the schema
    publishes: a plain string there would iterate as its own characters and file
    a label per letter into somebody's repository.
    """
    names = one.frontmatter["labels"]
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise SliceNotFilable(
            f"{_named(one)} has labels {names!r}, and labels is a JSON list of names"
        )
    return names


def _milestone(one: Slice) -> str | None:
    """The milestone title `one` asks for, or None when it asks for none."""
    title = one.frontmatter.get("milestone")
    if title is None:
        return None
    if not isinstance(title, str) or not title.strip():
        raise SliceNotFilable(
            f"{_named(one)} has milestone {title!r}, and a milestone is the title of one"
        )
    return title


def _milestone_numbers(transport: Transport, repo: str) -> dict[str, int]:
    """Every milestone `repo` has, by title.

    Open and closed both: a title is unique across both states, so reading only
    the open ones would try to create one that exists. An answer that is not a
    list is a transport that describes rather than performs, and it knows
    nothing about the repository, so it reports none.
    """
    answered = transport.run(
        Invocation(
            summary=f"read the milestones {repo} already has",
            method="GET",
            url=f"repos/{repo}/milestones?state=all&per_page={MILESTONE_PAGE}",
        )
    ).json
    if not isinstance(answered, list):
        return {}
    return {one["title"]: int(one["number"]) for one in answered if isinstance(one, dict)}


def _number(payload: Any) -> int:
    """The `number` a create answered with, or the placeholder for a transport
    that answered nothing because it made no call."""
    if isinstance(payload, dict) and "number" in payload:
        return int(payload["number"])
    return UNRESOLVED_MILESTONE


def _named(one: Slice) -> str:
    """One slice as both the things a reader needs: its id, and the file to open."""
    return f"{one.frontmatter['slice']} ({one.path})"
