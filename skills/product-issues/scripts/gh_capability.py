#!/usr/bin/env python3
"""Which GitHub path this machine can take, read from what it advertises.

"`gh` is installed" is not one capability but two. `gh issue create` gained
`--parent`, `--blocked-by` and `--blocking` in 2.94.0 (2026-06-10); every
release before that files issues perfectly well and its create carries no links
at all. Which of those two `gh` this is has to be found out, not guessed.

Nothing routes on that answer today, and this says so rather than leaving a
reader to hunt for a create that does not exist. Links go to the REST endpoints
on every path -- github_destination.py's "**Links go through the REST endpoints
on every path**" holds the reason, which is the shape of the transport port's
create rather than anything about the CLI -- so `supports_link_flags` is
detected and reported without being read: `file_issues.py`'s preview names it,
which is how somebody sees which `gh` this machine has. It is kept rather than
deleted because it costs one invocation that names no repository and reaches no
network, and because it is the fact a create carrying its own links would have
to branch on, which is `issue_transport.py`'s question to reopen. Until then no
code here passes a link flag to anything, and that is a settled decision rather
than an unfinished one.

That question is answered by asking `gh` rather than by comparing version
strings. `detect` reads `gh issue create --help` and looks for the flags in its
FLAGS block, so a release that adds them is believed the day it is installed and no
version table here has to be kept in step with upstream. The parsed version is
carried alongside because a message that says which `gh` was found is worth far
more than one that says a flag was missing, but nothing branches on it.

The second question this module answers is which host to talk to. `gh` resolves
that from `GH_HOST` or from its own config file, and the config file is the part
a stdlib path cannot read: the format is `gh`'s, it is not documented as an
interface, and a hosts entry there is the only record that this checkout belongs
to an Enterprise appliance. `rest_base_url` therefore takes `GH_HOST` as the
answer when it is set, and when it is not, treats a non-github.com git remote as
proof that github.com is the *wrong* answer rather than as the right one. It
refuses. Filing a team's roadmap into a stranger's github.com repository is not
a failure anybody can take back, and an appliance can serve its API from a host
its git remotes do not name, so a plausible guess is worse here than a stop.

Standard library only, like every script in this suite, and `gh` is reached
through the same `Transport` port everything else uses: reading `gh --version`
is an ordinary invocation, and a second way to shell out would be a seam with
one caller and no production reason to exist.
"""

from __future__ import annotations

import os
import re
import sys
import urllib.parse
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

# The transport port is the file next to this one. These scripts are not a
# package -- they run as plain `python3` subprocesses as well as under the
# harness, so there is no parent to import through -- and a sibling is reached
# by putting their shared directory on the path, anchored on `__file__` so the
# working directory does not matter. Same bootstrap as lib/artifact_common.py's
# consumers, one directory closer.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from issue_transport import GITHUB_API_BASE, Invocation, Transport, TransportError  # noqa: E402

# The one host whose REST API is not served from the host itself.
GITHUB_DOT_COM = "github.com"

# Where an Enterprise Server appliance mounts the REST API on its own host.
ENTERPRISE_API_PATH = "/api/v3"

# The two linking flags, spelled here once so that "which flags" is one fact
# rather than a string retyped wherever the question comes up. No create sends
# them, per the module docstring, so today they are read by `_advertises` below
# and by the test that splices them into a captured help; a create that one day
# carries links takes its argv from these names rather than writing them again.
PARENT_FLAG = "--parent"
BLOCKED_BY_FLAG = "--blocked-by"

# The whole set that has to be present before `supports_link_flags` is true.
# `--parent` is the marker the plan names; `--blocked-by` is checked alongside
# it because a create carrying links would have to send both, so a `gh` with one
# and not the other does not have the capability this field is named for. They
# shipped in the same release, so on every `gh` that exists today the two
# answers agree.
LINK_FLAGS: tuple[str, ...] = (PARENT_FLAG, BLOCKED_BY_FLAG)

# `gh --version` opens `gh version 2.82.0 (2025-10-15)`. The first dotted triple
# in that output is the version; the release URL on the next line repeats it.
_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")

# One line of a `gh` help FLAGS block: indented, optionally opening with a short
# flag, then the long name. Matching the line's shape rather than searching the
# text is what keeps a flag named in an EXAMPLES line from counting as a flag
# the CLI accepts.
_FLAG_LINE = re.compile(r"^\s+(?:-\w, )?(--[a-z0-9][a-z0-9-]*)")


class EnterpriseHostUnknown(RuntimeError):
    """The REST path cannot tell which GitHub it is meant to be talking to.

    Raised rather than defaulting, because both of the answers available here
    are irreversible in different directions: filing into the wrong github.com
    repository cannot be undone, and refusing costs one environment variable.
    """


@dataclass(frozen=True)
class Capability:
    """What the local `gh` answered, in the terms the rest of the beat asks in.

    `usable` is true of a `gh` that ran and identified itself. The only use for
    it is deciding whether to route calls through `gh`, so a `gh` that is on
    PATH and cannot be run counts as not usable: there is nothing a caller could
    do with the distinction except route around it either way.

    `version` is a comparable triple, or None when `gh` is unusable or printed
    something this could not parse. Nothing here branches on it -- it exists so
    a message can name the `gh` that was found -- so an unparsed version costs a
    detail in a report and never a decision.

    `supports_link_flags` covers the whole of `LINK_FLAGS`, and nothing branches
    on it: it is reported rather than routed on, for the reason the module
    docstring gives. False remains the answer every ambiguity resolves to, which
    costs nothing to be wrong about while no create sends the flags, and is
    already what the REST linking path does on every machine.
    """

    usable: bool
    version: tuple[int, int, int] | None
    supports_link_flags: bool


def detect(transport: Transport) -> Capability:
    """What the `gh` behind `transport` can do, asked rather than assumed.

    Two invocations: `gh --version` for the identification, and
    `gh issue create --help` for the flags. A failure of either is read as an
    absence rather than raised, because every caller of this function is about
    to choose a path and none of them has a better answer to give a raised
    error than the fallback path this returns.
    """
    version_text = _answered(transport, ("gh", "--version"), "read gh's version")
    if version_text is None:
        return Capability(usable=False, version=None, supports_link_flags=False)

    help_text = _answered(transport, ("gh", "issue", "create", "--help"), "read what gh issue create accepts")
    return Capability(
        usable=True,
        version=_version(version_text),
        supports_link_flags=help_text is not None and _advertises(help_text, LINK_FLAGS),
    )


def rest_base_url(env: Mapping[str, str] | None = None, *, remote_url: str | None = None) -> str:
    """The REST base URL the stdlib path should call, or a refusal to guess it.

    `env` defaults to the process environment; `remote_url` is whatever
    `git remote get-url` printed for the remote this run files against, and None
    when there is no remote to read. The two are not weighed evenly, and the
    asymmetry is the point: `GH_HOST` is somebody stating the answer, while a
    remote is only evidence, good enough to prove github.com wrong and not good
    enough to name what is right.

    Raises `EnterpriseHostUnknown` when the remote names a host other than
    github.com and `GH_HOST` is unset. This is the REST path's function, called
    only when `gh` is absent; a run with `gh` installed never reaches here
    because `gh` reads its own config and resolves the host itself.
    """
    declared = _host(os.environ if env is None else env)
    if declared is not None:
        return GITHUB_API_BASE if declared == GITHUB_DOT_COM else f"https://{declared}{ENTERPRISE_API_PATH}"

    remote = _remote_host(remote_url)
    if remote is not None and remote != GITHUB_DOT_COM:
        raise EnterpriseHostUnknown(
            f"the remote points at {remote}, not {GITHUB_DOT_COM}, and GH_HOST is unset, so there is "
            f"no way to tell which API to call without reading gh's own config. Set GH_HOST={remote} "
            "if that host serves the API, or install gh and let it resolve the host itself"
        )
    return GITHUB_API_BASE


def _answered(transport: Transport, argv: tuple[str, ...], summary: str) -> str | None:
    """What `argv` printed, or None when it could not be run at all."""
    try:
        return transport.run(Invocation(summary=summary, argv=argv)).stdout
    except TransportError:
        return None


def _version(text: str) -> tuple[int, int, int] | None:
    """The version triple `gh --version` printed, or None when its output did
    not carry one."""
    found = _VERSION.search(text)
    if found is None:
        return None
    major, minor, patch = found.groups()
    return int(major), int(minor), int(patch)


def _advertises(help_text: str, flags: Iterable[str]) -> bool:
    """True when `help_text` lists every one of `flags` as a flag of its own.

    Every flag rather than any: the name of the capability is plural, and a
    `gh` advertising one flag and not the other does not have what a create
    carrying links would need.
    """
    listed = {found.group(1) for found in map(_FLAG_LINE.match, help_text.splitlines()) if found}
    return all(flag in listed for flag in flags)


def _host(env: Mapping[str, str]) -> str | None:
    """The host `GH_HOST` names, lowercased, or None when it is unset or blank."""
    return env.get("GH_HOST", "").strip().lower() or None


def _remote_host(url: str | None) -> str | None:
    """The host a git remote URL points at, or None when it names no host.

    Handles both spellings git uses: a real URL (`https://host/owner/name.git`,
    `ssh://git@host/owner/name.git`) and the scp-like form
    (`git@host:owner/name.git`), which is not a URL and so is not something
    `urlsplit` can read. A remote that is a local path carries no host and
    returns None, which leaves the github.com default in place rather than
    refusing over a filesystem path.
    """
    text = (url or "").strip()
    if not text:
        return None

    netloc = urllib.parse.urlsplit(text).netloc if "://" in text else text.partition(":")[0]
    host = netloc.rpartition("@")[2].partition(":")[0].lower()
    return None if not host or "/" in host else host
