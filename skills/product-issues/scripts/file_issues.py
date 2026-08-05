#!/usr/bin/env python3
"""Stage 2 as one command: read the slices stage 1 wrote, and file them.

Usage:
    file_issues.py --slug <slug> --product-dir <dir> --destination markdown
    file_issues.py --slug <slug> --product-dir <dir> --destination github
                   --repo <owner/name> [--parent <n>] [--file]

Every other module in this beat does one thing to one subject: parse a slice,
detect a `gh`, spell a call, refuse a batch. None of them decides whether
anything happens. That decision is this module's whole subject, and it is made
in three places:

**Nothing is filed unless `--file` is passed.** Without it the run builds a
`DryRunTransport`, walks the identical sequence, prints what it would have sent,
and writes no ledger entry -- because the issue numbers that transport hands
back are placeholders, and a slice recording one would tell the next run that a
create nobody made had succeeded. `record_nothing` and `record_in_slice` are the
pair that expresses this: the transport decides whether a call goes out, and the
recorder decides whether a file is written, and neither of them is a flag read
somewhere below.

"No call" means no call to GitHub. The run still asks the local `gh` what
version it is and which flags it takes, because the sequence a dry run describes
is only the sequence filing would send if it knows which of the two spellings
that `gh` accepts, and a preview of the other path is exactly the drift the
transport port exists to prevent. Asking a binary on this machine to identify
itself reaches no network and touches nobody's repository.

**`--destination markdown` returns before a transport exists.** Stage 1 already
wrote the slice files, so this destination has nothing left to do and reports
what is there. Reaching for a tracker to answer it would make markdown a fourth
adapter rather than the substrate the tracker destinations are built on.

**A slice already carrying a `filed_github` entry is skipped and counted.** That
is what makes a second run file the remainder rather than a duplicate set. The
adapter refuses such a slice outright, which is the guard behind this one; the
count is what tells a reader that a short run was a resumed run.

JSON on stdout, like every script in this suite, and exactly one object of it.
The dry run's description of the sequence therefore goes to stderr, so a caller
can pipe stdout to a parser while a person reads the sequence.

One reading this module owns and no sibling can. `preflight.Parent` is a value
somebody read, because pre-flight holds no transport; this is where it is read,
every page of the sub-issues list and a walk up `parent_issue_url` for the
depth. A dry run cannot read it -- reading is a call -- so it reports the
ceilings as unread rather than passing a fabricated parent that would refuse
nothing while looking like a check.

Standard library only, like every script in this suite.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

# Siblings are reached the way every script in this suite reaches one: their
# shared directory on the path, anchored on `__file__`. See gh_capability.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh_capability  # noqa: E402
import github_destination  # noqa: E402
import preflight  # noqa: E402
import slice_file  # noqa: E402
from issue_transport import (  # noqa: E402
    DRY_RUN_URL_SCHEME,
    DryRunTransport,
    Filed,
    GhTransport,
    Invocation,
    RestTransport,
    Transport,
    TransportError,
)

# The two answers `--destination` takes. `GITHUB` is the adapter's own name for
# itself, which is also what composes the ledger key, so the word a user types
# and the key a run writes are one fact rather than two that can drift.
MARKDOWN = "markdown"
GITHUB = github_destination.DESTINATION
DESTINATIONS: tuple[str, ...] = (MARKDOWN, GITHUB)

# Stage 1's output folder and the chain member every slice traces back to, both
# under `<product-dir>/<slug>/`. Spelled here rather than imported from
# `product-artifacts`, whose `artifact-family.md` publishes the chain: reaching
# into another skill's scripts would be this suite's first cross-skill code
# import, for two path segments.
ISSUES_DIRNAME = "issues"
ROADMAP = "roadmap.md"

# The remote consulted when the REST path has to work out which GitHub this is.
DEFAULT_REMOTE = "origin"

# One page of the sub-issues list, at the largest page GitHub's list endpoints
# will return. Asking for fewer would only mean more round trips: the ceiling
# this count feeds is `preflight.MAX_SUB_ISSUES`, which is under a page, so a
# parent within the limit is answered in one call.
SUB_ISSUE_PAGE = 100

# Where paging stops regardless. By then the count is many times
# `preflight.MAX_SUB_ISSUES` and the batch will be refused whatever the exact
# number is, so the bound costs no decision and is what keeps a list endpoint
# that never shortens from looping forever.
MAX_SUB_ISSUE_PAGES = 10

# What the report says about GitHub's two sub-issue ceilings, which are the one
# thing here that cannot be checked without reading live state.
CEILINGS_CHECKED = "checked against the parent's current children and depth"
CEILINGS_NO_PARENT = "not applicable: this batch is filed at the top level, under no parent"
CEILINGS_UNREAD = (
    "not read: a dry run makes no call to GitHub, so the parent's current children and depth are "
    "unknown here. Pass --file to have them read before anything is created"
)

# The parent passed to pre-flight when nothing was read about one, which is both
# the top-level case and the dry run. Neither ceiling can be breached against it,
# and that is the point: `preflight.check` takes a `Parent` whether or not one
# was read, so a run that read nothing passes a value that visibly refuses
# nothing and says so in `ceilings`, rather than one that looks like a reading.
UNREAD_PARENT = preflight.Parent(number=0, children=0, depth=0)

# What a recorder hands back: the ledger entry it wrote, or None when it wrote
# none. `filed` in the report counts these, so a run that created nothing counts
# nothing without anybody consulting a flag.
Recorder = Callable[[slice_file.Slice, Filed], "dict[str, Any] | None"]


def read_slices(issues_dir: Path) -> list[slice_file.Slice]:
    """Every slice file in `issues_dir`, in filename order.

    Filename order is filing order, and it is the order stage 1's own numbering
    puts them in. A batch has to be filed in *some* order and this is the only
    one a reader can predict from the folder listing.
    """
    if not issues_dir.is_dir():
        raise FileNotFoundError(
            f"{issues_dir} does not exist, so this slug has no slices to file. Run the slicing stage "
            "before this one"
        )
    paths = sorted(issues_dir.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"{issues_dir} holds no slice files, so there is nothing to file")
    return [slice_file.read_slice(path) for path in paths]


def markdown_report(slug: str, issues_dir: Path, slices: Sequence[slice_file.Slice]) -> dict[str, Any]:
    """What stage 1 wrote, which is the whole of the markdown destination.

    No transport is built to answer this and none is needed: the slices are on
    disk, reviewable as a diff and revertible with `git checkout`, which is the
    property that makes markdown the substrate rather than a fourth adapter.
    """
    return {
        "slug": slug,
        "destination": MARKDOWN,
        "issues_dir": str(issues_dir),
        "count": len(slices),
        "slices": [
            {
                "slice": one.frontmatter["slice"],
                "title": one.frontmatter["title"],
                "path": str(one.path),
            }
            for one in slices
        ],
    }


def record_in_slice(one: slice_file.Slice, issue: Filed) -> dict[str, Any]:
    """Write `issue` into `one`'s frontmatter and report what was written.

    All three of `number`, `id` and `url` are recorded, and the first two are
    not the same value said twice: `number` is what a person reads and `id` is
    the internal database id, unrelated integers (25 against 5046900288 on a
    captured issue). Nothing here reads `id`, but the sub-issue and dependency
    endpoints accept nothing else, so a ledger that recorded only the number
    could not be used to link the issue it names.

    Refuses a placeholder rather than writing it. `DryRunTransport` hands back
    negative numbers under a scheme nothing can resolve precisely so that one
    reaching a file is unmistakable, and a slice recording a placeholder would
    both name an issue that does not exist and make every later run skip the
    slice, which is the one failure this ledger exists to prevent.
    """
    if issue.url.startswith(f"{DRY_RUN_URL_SCHEME}:"):
        raise RuntimeError(
            f"{one.path} was about to record {issue.url}, which is the placeholder a dry run hands "
            "back rather than an issue. A dry run must be paired with `record_nothing`"
        )
    entry = {"number": issue.number, "id": issue.id, "url": issue.url}
    slice_file.write_filed_entry(one.path, GITHUB, entry)
    return {"slice": one.frontmatter["slice"], "path": str(one.path), **entry}


def record_nothing(one: slice_file.Slice, issue: Filed) -> None:
    """Record nothing, which is what a dry run has to record.

    No issue was created, so there is nothing true to write into a slice and
    nothing to report as filed. This is the whole of what `--file` changes below
    the command line.
    """
    return None


def file_batch(
    transport: Transport,
    repo: str,
    slices: Sequence[slice_file.Slice],
    *,
    capability: gh_capability.Capability,
    parent: int | None,
    record: Recorder,
) -> Iterator[dict[str, Any]]:
    """File `slices` into `repo`, recording each issue the moment it exists.

    A generator, and for the same reason `github_destination.file_slices` is
    one: `record` is called between two of its yields, so "the ledger entry is
    written before the next create starts" is structural rather than a promise.
    A run killed mid-batch therefore leaves a record that is true of every slice
    that got through and of no other, and a caller consuming this lazily keeps
    the entries written so far even when a later create fails.
    """
    for one, issue in github_destination.file_slices(
        transport, repo, slices, capability=capability, parent=parent
    ):
        entry = record(one, issue)
        if entry is not None:
            yield entry


def read_parent(transport: Transport, repo: str, number: int) -> preflight.Parent:
    """Issue `number` as the two ceilings see it, read from `repo`.

    Both values are reads, which is why this is here rather than in `preflight`:
    that module holds no transport so that "nothing was called" is a property of
    its code rather than a promise in its docstring.
    """
    return preflight.Parent.from_sub_issues(
        number, _sub_issues(transport, repo, number), depth=_depth(transport, repo, number)
    )


def _sub_issues(transport: Transport, repo: str, number: int) -> list[Any]:
    """Every sub-issue of `repo#number`, across every page.

    Every page and not the first: the endpoint pages at 30 by default while the
    ceiling it feeds is 100, so a caller reading one page undercounts by up to 70
    children and gets a refusal that never fires. `Parent.from_sub_issues` cannot
    detect a truncated list, so completeness is this function's job.
    """
    found: list[Any] = []
    for page in range(1, MAX_SUB_ISSUE_PAGES + 1):
        answered = transport.run(
            Invocation(
                summary=f"read page {page} of {repo}#{number}'s sub-issues",
                method="GET",
                url=f"repos/{repo}/issues/{number}/sub_issues?per_page={SUB_ISSUE_PAGE}&page={page}",
            )
        ).json
        # A transport that describes rather than performs answers no body, and
        # knows nothing about the repository, so it reports no children.
        if not isinstance(answered, list):
            break
        found.extend(answered)
        if len(answered) < SUB_ISSUE_PAGE:
            break
    return found


def _depth(transport: Transport, repo: str, number: int) -> int:
    """How deep `repo#number` sits in the sub-issue tree, top level being 1.

    Walked rather than read: nothing in an issue payload says how deep it sits,
    only whether it has a parent, so the answer is one read per level up. The
    walk stops at the nesting ceiling because a parent that deep already has no
    room for children, and remembers where it has been because a cycle GitHub
    should not permit is still not worth hanging on.
    """
    seen = {number}
    at = number
    for depth in range(1, preflight.MAX_NESTING_DEPTH + 1):
        answered = transport.run(
            Invocation(
                summary=f"read {repo}#{at} to see whether it is itself a sub-issue",
                method="GET",
                url=f"repos/{repo}/issues/{at}",
            )
        ).json
        above = _parent_number(answered)
        if above is None or above in seen:
            return depth
        seen.add(above)
        at = above
    return preflight.MAX_NESTING_DEPTH


def _parent_number(payload: Any) -> int | None:
    """The issue number of the parent an issue payload names, or None when it
    names none and so sits at the top level.

    `parent_issue_url` is an absolute API URL, and only its trailing number is
    used: an `Invocation` carries a path relative to the REST base, so that the
    same call runs through `gh api` and through `urllib` alike.
    """
    if not isinstance(payload, dict):
        return None
    url = payload.get("parent_issue_url")
    if not isinstance(url, str) or not url:
        return None
    try:
        return int(url.rstrip("/").rsplit("/", 1)[-1])
    except ValueError:
        return None


def _filing_transport(shell: Transport, capability: gh_capability.Capability) -> Transport:
    """The transport a run that files should use.

    `gh` when there is one, because it owns the credential and no token is
    placed on a command line; the stdlib REST path otherwise. The REST path has
    to be told which GitHub this is, and the git remote is the evidence
    `gh_capability` weighs -- it refuses rather than defaulting when the remote
    names an appliance, since filing into the wrong github.com repository cannot
    be taken back.
    """
    if capability.usable:
        return shell
    return RestTransport(gh_capability.rest_base_url(remote_url=_remote_url(shell)))


def _remote_url(shell: Transport) -> str | None:
    """This checkout's `origin` URL, or None when there is no remote to read.

    Read through the transport port rather than through `subprocess` directly,
    because a second way to shell out would be a seam with one caller. A missing
    remote is an absence rather than a failure: it leaves the github.com default
    in place, which is what `rest_base_url` does with it.
    """
    try:
        return (
            shell.run(
                Invocation(
                    summary=f"read this checkout's {DEFAULT_REMOTE} remote",
                    argv=("git", "remote", "get-url", DEFAULT_REMOTE),
                )
            ).stdout.strip()
            or None
        )
    except TransportError:
        return None


def _described(invocation: Invocation) -> dict[str, Any]:
    """One intended call as the two things a reader of a preview needs: what it
    does to their repository, and what would actually go out."""
    spelled = " ".join(invocation.argv) if invocation.argv else f"{invocation.method} {invocation.url}"
    return {"summary": invocation.summary, "call": spelled}


def _reported(capability: gh_capability.Capability) -> dict[str, Any]:
    """The local `gh` as the report names it. `version` is a string because it
    is for a person to read; nothing branches on it."""
    return {
        "usable": capability.usable,
        "version": None if capability.version is None else ".".join(str(n) for n in capability.version),
        "link_flags": capability.supports_link_flags,
    }


def _fail(report: dict[str, Any], message: str) -> int:
    """Print `report` carrying `message` and answer the exit status for it.

    The report is printed rather than replaced by the error, because a failure
    part-way through a batch is the case this beat is built around: what got
    filed before it is in `issues`, and a caller that got only an error message
    would have to go and look.
    """
    report["error"] = message
    print(json.dumps(report, indent=2))
    return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="File a slug's slices to a destination")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--product-dir", required=True)
    parser.add_argument("--destination", required=True, choices=DESTINATIONS)
    # Meaningful only to --destination github, so it is checked there rather
    # than here: a markdown run must not be asked for a repository it never uses.
    parser.add_argument("--repo", help="owner/name of the repository to file into")
    parser.add_argument("--parent", type=int, help="issue number to file this batch under")
    parser.add_argument(
        "--file",
        action="store_true",
        help="actually file. Without it the run describes what it would do and creates nothing",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    folder = Path(args.product_dir).expanduser().resolve() / args.slug
    issues_dir = folder / ISSUES_DIRNAME

    report: dict[str, Any] = {"slug": args.slug, "destination": args.destination}
    try:
        slices = read_slices(issues_dir)
    except (OSError, slice_file.SliceFormatError) as err:
        return _fail(report, str(err))

    if args.destination == MARKDOWN:
        print(json.dumps(markdown_report(args.slug, issues_dir, slices), indent=2))
        return 0

    if not args.repo:
        return _fail(report, "--repo is required for --destination github, as owner/name")

    # One `gh` for the whole run: it identifies the local install, it is the
    # filing transport when there is a usable one, and its create pacing is per
    # instance, so a second one would pace nothing.
    shell = GhTransport()
    capability = gh_capability.detect(shell)

    to_file = [one for one in slices if one.filed(GITHUB) is None]
    written: list[dict[str, Any]] = []
    report.update(
        {
            "issues_dir": str(issues_dir),
            "repo": args.repo,
            "parent": args.parent,
            "dry_run": not args.file,
            "gh": _reported(capability),
            # Null until the run has got as far as deciding it, which is what a
            # failure before that leaves behind.
            "ceilings": None,
            "skipped": len(slices) - len(to_file),
            "planned": len(to_file),
            "filed": 0,
            "issues": written,
            "calls": [],
        }
    )

    # Built before the parent is read, because on a dry run it is what makes
    # that read impossible: describing a call is not making one.
    preview = None if args.file else DryRunTransport(stream=sys.stderr)
    failure: str | None = None
    try:
        transport = preview if preview is not None else _filing_transport(shell, capability)

        if args.parent is None:
            parent, report["ceilings"] = UNREAD_PARENT, CEILINGS_NO_PARENT
        elif preview is not None:
            parent, report["ceilings"] = UNREAD_PARENT, CEILINGS_UNREAD
        else:
            parent, report["ceilings"] = read_parent(transport, args.repo, args.parent), CEILINGS_CHECKED

        preflight.check(to_file, capability, parent, roadmap=folder / ROADMAP)
        for entry in file_batch(
            transport,
            args.repo,
            to_file,
            capability=capability,
            parent=args.parent,
            record=record_nothing if preview is not None else record_in_slice,
        ):
            written.append(entry)
    except (
        gh_capability.EnterpriseHostUnknown,
        github_destination.SliceNotFilable,
        preflight.PreflightRefusal,
        slice_file.SliceFormatError,
        TransportError,
    ) as err:
        failure = str(err)

    report["filed"] = len(written)
    if preview is not None:
        report["calls"] = [_described(one) for one in preview.invocations]

    if failure is not None:
        return _fail(report, failure)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
