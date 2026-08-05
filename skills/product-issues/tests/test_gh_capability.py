"""Unit tests for gh_capability.py: what the local `gh` says it can do.

The linking flags `--parent` and `--blocked-by` landed in `gh` 2.94.0, and
everything before it creates issues perfectly well while its create carries no
links at all. What is under test is the *reading* of that difference and only
that: no code sends a link flag, because links go to the REST endpoints on every
path, so `supports_link_flags` is a fact reported in a preview rather than a
branch anything takes. gh_capability.py's own docstring says why it is detected
anyway. These tests hold it to being a read of what `gh` printed, since a
constant would report every machine as the same machine.

`fixtures/gh_issue_create_help.txt` is the load-bearing artefact here: it
is the verbatim `gh issue create --help` of the 2.82.0 on the machine this was
written against, and the property that matters is what it does *not* contain --
its FLAGS block lists no `--parent`, `--blocked-by` or `--blocking`. Anyone
re-capturing that fixture against a newer `gh` is not refreshing a sample, they
are deleting the only evidence the old path was ever exercised, and both
assertions in the first test below will fail rather than quietly invert.

No `gh` is invoked. Reading the real one would make the suite report whatever
this machine happens to have installed, which is the opposite of a test, so the
injected `Transport` is a fake replaying the captured stdout. Everything
gh_capability owns -- the version parse and the help-text parse -- runs for real
against those bytes.

The second test needs a `gh` that *does* advertise the flags, and no 2.94.0 was
reachable to capture one from. Its two flag lines and its version line are
therefore invented in their wording while copying the shape of the captured
files -- the `--recover string` line and the `gh version 2.82.0 (2025-10-15)`
line respectively -- and the flag lines are spliced into the real FLAGS block
rather than standing alone, so the parser is still read against genuine
surrounding text. That is as close to captured as this direction gets, and it
is worth having: without it, `supports_link_flags` could be the constant False
and `version` the constant `(2, 82, 0)`, and every other assertion here would
still pass.

Runnable two ways:
    python3 -m pytest skills/product-issues/tests/test_gh_capability.py
    uv run --no-project pytest skills/product-issues/tests/test_gh_capability.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FIXTURES = HERE / "fixtures"


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Registered before it is executed: `@dataclass` resolves the string
    # annotations that `from __future__ import annotations` produces through
    # `sys.modules[cls.__module__]`, and an unregistered module makes that
    # lookup return None mid-decoration. Registering `issue_transport` under
    # its plain name is also what lets gh_capability's own import of it find
    # this instance rather than loading a second copy whose `Invocation` would
    # be a different class.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


issue_transport = _load("issue_transport")
gh_capability = _load("gh_capability")

CAPTURED_VERSION = (FIXTURES / "gh_version.txt").read_text(encoding="utf-8")
CAPTURED_HELP = (FIXTURES / "gh_issue_create_help.txt").read_text(encoding="utf-8")

# The last line of the captured FLAGS block and the last line of its EXAMPLES
# block. Splicing after a line that is really there keeps the invented lines
# below inside genuine structure; a `replace` that matched nothing would
# silently test the unmodified file, so both are asserted present.
LAST_FLAG = "  -w, --web              Open the browser to create an issue\n"
LAST_EXAMPLE = '  $ gh issue create --template "Bug Report"\n'

# Invented wording, real shape: the indent the captured `--recover string` line
# uses for a flag with no short form, and a type word after the name as every
# captured flag line has. The names themselves are production's, taken from the
# constants rather than typed again, so a rename there fails this test instead
# of quietly leaving it testing a flag nobody probes for.
PARENT_FLAG_LINE = f"      {gh_capability.PARENT_FLAG} number    Parent issue number or URL\n"
BLOCKED_BY_FLAG_LINE = (
    f"      {gh_capability.BLOCKED_BY_FLAG} numbers   Issue numbers or URLs this issue is blocked by\n"
)

# A 2.94.0 `gh --version`, invented in the same way and for the same reason: the
# release that added the flags could not be reached to capture one from. Its
# shape is the captured 2.82.0 line's.
VERSION_2_94 = "gh version 2.94.0 (2026-06-10)\nhttps://github.com/cli/cli/releases/tag/v2.94.0\n"


class _FakeGh:
    """A `gh` that answers the two questions `detect` asks it and nothing else.

    An unexpected command fails the test rather than returning something
    plausible: `detect`'s whole job is to ask the environment, and a fake that
    answered anything would let it ask the wrong thing and still pass.
    """

    def __init__(
        self, *, version_text: str = CAPTURED_VERSION, help_text: str | None = CAPTURED_HELP
    ) -> None:
        # A None answer is a command that fails the way `GhTransport` fails one,
        # which is how the `gh` that runs but cannot print its own help is
        # written down.
        self._answers: dict[tuple[str, ...], str | None] = {
            ("gh", "--version"): version_text,
            ("gh", "issue", "create", "--help"): help_text,
        }

    def run(self, invocation: Any) -> Any:
        assert invocation.argv in self._answers, f"detect ran an unexpected command: {invocation.argv}"
        answer = self._answers[invocation.argv]
        if answer is None:
            raise issue_transport.CallFailed(invocation.summary, 1, "unknown command")
        return issue_transport.Result(status=0, stdout=answer)

    def create_issue(self, repo: str, title: str, body: str) -> Any:
        raise AssertionError("asking what gh can do must never create an issue")


class _AbsentGh:
    """A `gh` that is not on PATH, which is how `GhTransport` reports one: a
    `CallFailed` carrying no status, raised out of `FileNotFoundError`."""

    def run(self, invocation: Any) -> Any:
        raise issue_transport.CallFailed(invocation.summary, None, "gh is not on PATH")

    def create_issue(self, repo: str, title: str, body: str) -> Any:
        raise AssertionError("an absent gh cannot create anything")


def _help_listing(*extra_flags: str) -> str:
    """The captured help with `extra_flags` spliced into the end of its real
    FLAGS block."""
    assert LAST_FLAG in CAPTURED_HELP, "the captured help no longer ends its FLAGS block with --web"
    return CAPTURED_HELP.replace(LAST_FLAG, LAST_FLAG + "".join(extra_flags))


def test_detects_no_link_flags_on_captured_2_82_help() -> None:
    capability = gh_capability.detect(_FakeGh())

    assert capability.version == (2, 82, 0), (
        "the captured `gh version 2.82.0 (2025-10-15)` line did not parse into a comparable version"
    )
    assert capability.usable is True, "a gh that answered --version was reported unusable"
    assert capability.supports_link_flags is False, (
        "2.82.0's help lists no --parent, so claiming the link flags reports a machine that is not "
        "this one -- and is the answer a create carrying links would go on the day one exists"
    )


def test_link_flags_are_believed_only_when_every_one_is_listed_as_a_flag() -> None:
    both = gh_capability.detect(
        _FakeGh(version_text=VERSION_2_94, help_text=_help_listing(PARENT_FLAG_LINE, BLOCKED_BY_FLAG_LINE))
    )
    assert both.supports_link_flags is True, (
        "a gh advertising both link flags was not believed, so this reports False for every machine "
        "there is and is a constant wearing the shape of a detection"
    )
    assert both.version == (2, 94, 0), (
        "a second version parsed to the same triple as the captured 2.82.0 one, so the parse is a "
        "constant rather than a read of what gh printed"
    )

    parent_only = gh_capability.detect(_FakeGh(help_text=_help_listing(PARENT_FLAG_LINE)))
    assert parent_only.supports_link_flags is False, (
        "the pair was claimed on the strength of --parent alone. The capability is named for both "
        "flags, and a gh with half of them cannot carry the links a create would need"
    )

    assert LAST_EXAMPLE in CAPTURED_HELP, "the captured help no longer ends its EXAMPLES block as expected"
    mentioned = gh_capability.detect(
        _FakeGh(
            help_text=CAPTURED_HELP.replace(
                LAST_EXAMPLE, LAST_EXAMPLE + "  $ gh issue create --parent 25 --blocked-by 24\n"
            )
        )
    )
    assert mentioned.supports_link_flags is False, (
        "a flag named in an EXAMPLES line was counted as a flag the CLI accepts"
    )


def test_a_gh_that_cannot_be_asked_is_reported_as_unusable_rather_than_raising() -> None:
    absent = gh_capability.detect(_AbsentGh())
    assert absent.usable is False, "a gh that is not on PATH was reported usable"
    assert absent.version is None, "a version was reported for a gh that never ran"
    assert absent.supports_link_flags is False, "link flags were claimed for a gh that never answered"

    # A `gh` old enough that `issue create` refuses `--help` is hypothetical, but
    # the branch is not: this pins that a question which went unanswered is
    # written down as an absence rather than as a capability.
    mute = gh_capability.detect(_FakeGh(help_text=None))
    assert mute.usable is True, "a gh that printed its version was reported unusable over a failed --help"
    assert mute.supports_link_flags is False, "link flags were claimed from a help text that never arrived"


def test_rest_base_url_answers_github_and_refuses_to_guess_an_enterprise_host() -> None:
    github_remote = "git@github.com:Tsadoq/claude-better-plan.git"
    assert gh_capability.rest_base_url({}, remote_url=github_remote) == "https://api.github.com"
    assert gh_capability.rest_base_url({}) == "https://api.github.com"
    assert gh_capability.rest_base_url({}, remote_url="/srv/git/mirror.git") == "https://api.github.com", (
        "a remote that is a local path names no host, and refusing over one would stop a run that "
        "has said nothing at all about an appliance"
    )
    assert gh_capability.rest_base_url({"GH_HOST": "github.com"}) == "https://api.github.com"
    assert gh_capability.rest_base_url({"GH_HOST": "github.acme.com"}) == "https://github.acme.com/api/v3"

    with pytest.raises(gh_capability.EnterpriseHostUnknown) as refused:
        gh_capability.rest_base_url({}, remote_url="https://github.acme.com/acme/tooling.git")
    assert "github.acme.com" in str(refused.value), (
        "the refusal must name the host it saw, since the fix is to set GH_HOST to it"
    )
    assert "GH_HOST" in str(refused.value), "the refusal must name the variable that resolves it"
