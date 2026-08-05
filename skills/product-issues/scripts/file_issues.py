
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

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

MARKDOWN = "markdown"
GITHUB = github_destination.DESTINATION
DESTINATIONS: tuple[str, ...] = (MARKDOWN, GITHUB)

ISSUES_DIRNAME = "issues"
ROADMAP = "roadmap.md"

DEFAULT_REMOTE = "origin"

SUB_ISSUE_PAGE = 100

MAX_SUB_ISSUE_PAGES = 10

CEILINGS_CHECKED = "checked against the parent's current children and depth"
CEILINGS_NO_PARENT = "not applicable: this batch is filed at the top level, under no parent"
CEILINGS_UNREAD = (
    "not read: a dry run makes no call to GitHub, so the parent's current children and depth are "
    "unknown here. Pass --file to have them read before anything is created"
)

UNREAD_PARENT = preflight.Parent(number=0, children=0, depth=0)

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
            "ceilings": None,
            "skipped": len(slices) - len(to_file),
            "planned": len(to_file),
            "filed": 0,
            "issues": written,
            "calls": [],
        }
    )

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
