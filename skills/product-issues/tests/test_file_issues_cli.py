
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import urllib.request
from collections.abc import Sequence
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
slice_file = _load("slice_file")
github_destination = _load("github_destination")
preflight = _load("preflight")
file_issues = _load("file_issues")

REPO = "Tsadoq/claude-better-plan"

SLUG = "cohort-review"

ISSUE_25 = json.loads((FIXTURES / "issue_25.json").read_text(encoding="utf-8"))

ISSUE_26 = {
    **ISSUE_25,
    "number": 26,
    "id": 5046900301,
    "html_url": "https://github.com/Tsadoq/claude-better-plan/issues/26",
}

PARENT = 25
GRANDPARENT = 14

SUB_ISSUES = json.loads((FIXTURES / "sub_issues_populated.json").read_text(encoding="utf-8"))

NO_GH = gh_capability.Capability(usable=False, version=None, supports_link_flags=False)


def _no_network(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    shelled: list[list[str]] = []
    real_run = subprocess.run

    def recording_run(argv: Any, *args: Any, **kwargs: Any) -> Any:
        shelled.append(list(argv))
        return real_run(argv, *args, **kwargs)

    def refuse_to_connect(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError(
            "the run opened an HTTP connection. Nothing in this suite may reach the network, and a "
            "default run may not reach GitHub at all"
        )

    monkeypatch.setattr(subprocess, "run", recording_run)
    monkeypatch.setattr(urllib.request.OpenerDirector, "open", refuse_to_connect)
    return shelled


def _slug_folder(tmp_path: Path, *, filed: dict[str, Any] | None = None) -> Path:
    product_dir = tmp_path / "product"
    folder = product_dir / SLUG
    issues = folder / "issues"
    issues.mkdir(parents=True)

    (folder / "roadmap.md").write_text(
        "# Roadmap\n\n| Item | Name |\n|---|---|\n| ITEM2 | Review a cohort |\n",
        encoding="utf-8",
    )
    for number, title in ((1, "Narrow the roster"), (2, "Show one cohort")):
        lines = [
            "---",
            f"slice: SLICE-0{number}",
            f"title: {title}",
            "activity: Review a cohort",
            "roadmap_item: ITEM2",
            "labels: []",
        ]
        if filed is not None and number == 1:
            lines.append(f"filed_github: {json.dumps(filed)}")
        lines += ["---", "", "## Context", "", "Somebody wrote this.", ""]
        (issues / f"slice-0{number}.md").write_text("\n".join(lines), encoding="utf-8")
    return product_dir


def _slices(product_dir: Path) -> list[Any]:
    return [slice_file.read_slice(path) for path in sorted((product_dir / SLUG / "issues").glob("*.md"))]


def _github_argv(product_dir: Path, *extra: str) -> list[str]:
    return [
        "--slug",
        SLUG,
        "--product-dir",
        str(product_dir),
        "--destination",
        "github",
        "--repo",
        REPO,
        *extra,
    ]


def test_default_run_is_a_dry_run_that_makes_no_call(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    product_dir = _slug_folder(tmp_path)
    shelled = _no_network(monkeypatch)

    status = file_issues.main(_github_argv(product_dir))

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert status == 0, f"a dry run must succeed, and this one reported {payload.get('error')!r}"
    assert (payload["planned"], payload["filed"], payload["skipped"]) == (2, 0, 0), (
        "the default must plan both slices and file neither: `filed` counts ledger entries written, and "
        "a run that wrote one without `--file` has created an issue nobody asked it to"
    )

    creates = [one for one in payload["calls"] if one["call"] == f"POST repos/{REPO}/issues"]
    assert len(creates) == 2, (
        f"the dry run must describe one create per planned slice, and described {payload['calls']}. An "
        "empty or short sequence is a preview of something other than what filing does"
    )
    assert all(one["summary"] in captured.err for one in creates), (
        "the intended sequence must be printed for a person to read, and to stderr rather than stdout, "
        "which carries one JSON object and nothing else"
    )

    assert [one.filed("github") for one in _slices(product_dir)] == [None, None], (
        "a dry run wrote a ledger entry. The issue numbers its transport hands back are placeholders, so "
        "a slice recording one would tell the next run that a create nobody made had succeeded"
    )
    assert set(map(tuple, shelled)) <= {("gh", "--version"), ("gh", "issue", "create", "--help")}, (
        f"a default run shelled out to {shelled}. The only thing it may run is the local gh identifying "
        "itself; every one of those names no repository and reaches no network"
    )
    assert shelled, (
        "the dry run asked the local gh nothing, so the spelling it previewed is a guess. Which calls "
        "filing sends depends on what this gh accepts, and a preview of the other path is drift"
    )


def test_markdown_destination_reports_the_slices_and_builds_no_transport(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    product_dir = _slug_folder(tmp_path)
    shelled = _no_network(monkeypatch)

    status = file_issues.main(
        ["--slug", SLUG, "--product-dir", str(product_dir), "--destination", "markdown"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert status == 0, f"the markdown destination reported {payload.get('error')!r}"
    assert [one["slice"] for one in payload["slices"]] == ["SLICE-01", "SLICE-02"], (
        "the markdown destination reports what stage 1 wrote, in the order stage 2 would file it"
    )
    assert shelled == [], (
        "the markdown run reached for a tracker. Stage 1 already wrote these files, so markdown is the "
        "substrate the tracker destinations are built on rather than a fourth adapter, and it must "
        "return before any transport exists"
    )


def test_a_slice_already_filed_is_skipped_and_only_the_rest_are_planned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    already = {"number": ISSUE_25["number"], "id": ISSUE_25["id"], "url": ISSUE_25["html_url"]}
    product_dir = _slug_folder(tmp_path, filed=already)
    _no_network(monkeypatch)

    status = file_issues.main(_github_argv(product_dir))

    payload = json.loads(capsys.readouterr().out)
    assert status == 0, f"the resumed run reported {payload.get('error')!r}"
    assert (payload["planned"], payload["skipped"]) == (1, 1), (
        "a slice already recording an issue must be skipped and counted, so a resumed run files the "
        "remainder rather than refusing the batch or creating a second issue for it"
    )
    assert [one["call"] for one in payload["calls"]] == [f"POST repos/{REPO}/issues"], (
        "the skipped slice must reach no call at all; filing is the one act here that cannot be undone"
    )


def test_each_ledger_entry_is_written_before_the_next_issue_is_created(tmp_path: Path) -> None:
    product_dir = _slug_folder(tmp_path)
    slices = _slices(product_dir)
    transport = _FakeGitHub((ISSUE_25, ISSUE_26), [one.path for one in slices])

    written = list(
        file_issues.file_batch(
            transport,
            REPO,
            slices,
            capability=NO_GH,
            parent=None,
            record=file_issues.record_in_slice,
        )
    )

    assert transport.recorded_at_each_create == [[False, False], [True, False]], (
        "each slice's ledger entry must be on disk before the next create starts. Batching the writes "
        "to the end means a run killed mid-batch leaves issues that no slice file names, and filing is "
        "the one act here that cannot be undone"
    )
    assert [one.filed("github") for one in _slices(product_dir)] == [
        {"number": 25, "id": ISSUE_25["id"], "url": ISSUE_25["html_url"]},
        {"number": 26, "id": ISSUE_26["id"], "url": ISSUE_26["html_url"]},
    ], (
        "each entry must record the issue's database id as well as its number. They are unrelated "
        "values, and the id is the only one the sub-issue endpoints accept"
    )
    assert [one["slice"] for one in written] == ["SLICE-01", "SLICE-02"], (
        "the batch must hand back an entry per slice it recorded, since that list is what the report "
        "counts as filed and what a caller reads to see what a killed run got through"
    )


def test_the_parent_is_counted_across_every_page_of_its_sub_issues(tmp_path: Path) -> None:
    padding = [dict(one) for one in (SUB_ISSUES * 10)[:100]]
    transport = _FakeGitHub(pages=(padding, SUB_ISSUES), payloads={GRANDPARENT: {}})

    parent = file_issues.read_parent(transport, REPO, GRANDPARENT)

    assert parent.children == len(padding) + len(SUB_ISSUES), (
        "the sub-issue count must span every page. GitHub pages this endpoint while the ceiling it "
        "feeds is 100, so a count that stops at the first page undercounts and the refusal that exists "
        "to stop a half-filed batch never fires"
    )


def test_a_parent_that_is_itself_a_sub_issue_is_read_as_one_level_deeper(tmp_path: Path) -> None:
    transport = _FakeGitHub(
        pages=([],), payloads={PARENT: ISSUE_25, GRANDPARENT: {"number": GRANDPARENT}}
    )

    parent = file_issues.read_parent(transport, REPO, PARENT)

    assert parent.depth == 2, (
        f"issue {PARENT} sits under issue {GRANDPARENT} -- its captured payload says so in "
        "`parent_issue_url` -- so it is one level below the top and a batch under it nests one deeper "
        "again. Nothing in an issue payload states a depth, so an unwalked parent reports 1 and the "
        "nesting ceiling goes unenforced"
    )


def test_a_placeholder_issue_is_refused_rather_than_written_into_a_slice(tmp_path: Path) -> None:
    product_dir = _slug_folder(tmp_path)
    one = _slices(product_dir)[0]
    placeholder = issue_transport.DryRunTransport(stream=_Sink()).create_issue(REPO, "Narrow", "body")

    with pytest.raises(RuntimeError, match=issue_transport.DRY_RUN_URL_SCHEME):
        file_issues.record_in_slice(one, placeholder)

    assert slice_file.read_slice(one.path).filed("github") is None, (
        "a placeholder reached a slice file, which would report an issue that does not exist and make "
        "the next run skip the slice forever"
    )


class _FakeGitHub:

    def __init__(
        self,
        creates: tuple[dict[str, Any], ...] = (),
        watching: Sequence[Path] = (),
        *,
        pages: Sequence[list[Any]] = (),
        payloads: dict[int, dict[str, Any]] | None = None,
    ) -> None:
        self.invocations: list[Any] = []
        self.recorded_at_each_create: list[list[bool]] = []
        self._creates = list(creates)
        self._watching = list(watching)
        self._pages = list(pages)
        self._payloads = payloads or {}

    def run(self, invocation: Any) -> Any:
        self.invocations.append(invocation)
        if invocation.url.split("?")[0].endswith("/sub_issues"):
            return issue_transport.Result(status=200, json=self._pages.pop(0) if self._pages else [])
        return issue_transport.Result(status=200, json=self._payloads.get(_trailing(invocation.url), {}))

    def create_issue(self, repo: str, title: str, body: str) -> Any:
        assert self._creates, "the batch created more issues than this test seeded payloads for"
        self.recorded_at_each_create.append(
            [slice_file.read_slice(path).filed("github") is not None for path in self._watching]
        )
        payload = self._creates.pop(0)
        return issue_transport.Filed(
            number=payload["number"], id=payload["id"], url=payload["html_url"]
        )


def _trailing(url: str) -> int:
    try:
        return int(url.rstrip("/").rsplit("/", 1)[-1])
    except ValueError:
        return 0


class _Sink:

    def write(self, text: str) -> int:
        return len(text)
