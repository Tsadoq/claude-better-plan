
from __future__ import annotations

import os
import re
import sys
import urllib.parse
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from issue_transport import GITHUB_API_BASE, Invocation, Transport, TransportError  # noqa: E402

GITHUB_DOT_COM = "github.com"

ENTERPRISE_API_PATH = "/api/v3"

PARENT_FLAG = "--parent"
BLOCKED_BY_FLAG = "--blocked-by"

LINK_FLAGS: tuple[str, ...] = (PARENT_FLAG, BLOCKED_BY_FLAG)

_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")

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
