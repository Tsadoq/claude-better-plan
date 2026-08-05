
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
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


issue_transport = _load("issue_transport")
gh_capability = _load("gh_capability")

CAPTURED_VERSION = (FIXTURES / "gh_version.txt").read_text(encoding="utf-8")
CAPTURED_HELP = (FIXTURES / "gh_issue_create_help.txt").read_text(encoding="utf-8")

LAST_FLAG = "  -w, --web              Open the browser to create an issue\n"
LAST_EXAMPLE = '  $ gh issue create --template "Bug Report"\n'

PARENT_FLAG_LINE = f"      {gh_capability.PARENT_FLAG} number    Parent issue number or URL\n"
BLOCKED_BY_FLAG_LINE = (
    f"      {gh_capability.BLOCKED_BY_FLAG} numbers   Issue numbers or URLs this issue is blocked by\n"
)

VERSION_2_94 = "gh version 2.94.0 (2026-06-10)\nhttps://github.com/cli/cli/releases/tag/v2.94.0\n"


class _FakeGh:

    def __init__(
        self, *, version_text: str = CAPTURED_VERSION, help_text: str | None = CAPTURED_HELP
    ) -> None:
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

    def run(self, invocation: Any) -> Any:
        raise issue_transport.CallFailed(invocation.summary, None, "gh is not on PATH")

    def create_issue(self, repo: str, title: str, body: str) -> Any:
        raise AssertionError("an absent gh cannot create anything")


def _help_listing(*extra_flags: str) -> str:
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
