"""Unit tests for github_destination.py: the calls that create and link a slice set.

`fixtures/issue_25.json` is the load-bearing artefact here, and the property
that matters is that its two integers disagree: `id` is 5046900288 while
`number` is 25. The sub-issue and dependency endpoints take the database id and
every other endpoint in this beat takes the number, so a fixture whose id
happened to equal its number would let an adapter reaching for the wrong integer
pass every assertion below. Anyone re-capturing it against another issue is not
refreshing a sample, they are deleting the only evidence that the distinction
was ever checked, and must keep the two values apart.

No call leaves this process and no `gh` is invoked. The adapter runs for real
against a fake `Transport` -- the same port production holds -- which records
every invocation in arrival order and answers from the captured payload. Order
is half of what this module is responsible for: a label that does not exist when
a create names it, or a link sent before the issue it points at, are failures no
single-call assertion would catch. The last test swaps the fake for the real
`DryRunTransport`, because a dry run is the one caller that must reach the end
of the sequence while knowing nothing about the repository.

Two payloads here are not captured. A second issue is the captured one with its
number and id moved, because one `gh api` capture cannot describe a two-slice
batch, and the milestone answers are shaped from the REST reference. Both are
named below so a reader knows which bytes came off a real invocation.

Runnable two ways:
    python3 -m pytest skills/product-issues/tests/test_github_destination.py
    uv run --no-project pytest skills/product-issues/tests/test_github_destination.py
"""

from __future__ import annotations

import importlib.util
import json
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
    # Registered before it is executed, and under its plain name: `@dataclass`
    # resolves the string annotations `from __future__ import annotations`
    # produces through `sys.modules[cls.__module__]`, and the adapter's own
    # imports of its siblings must find these instances rather than loading
    # second copies whose `Invocation` would be a different class.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


issue_transport = _load("issue_transport")
gh_capability = _load("gh_capability")
slice_file = _load("slice_file")
github_destination = _load("github_destination")

# The repository the fixtures were captured against.
REPO = "Tsadoq/claude-better-plan"

# The captured issue. Its `id` and `number` are read from the file rather than
# written out here, so a re-capture moves every assertion with it.
ISSUE_25 = json.loads((FIXTURES / "issue_25.json").read_text(encoding="utf-8"))

# The issue the batch is filed under. Not arbitrary: issue 25 really is one of
# issue 14's sub-issues in the captured set, so the parent-and-child pair these
# tests file is the pair GitHub actually holds.
PARENT = 14

# A second issue for the batch tests: the captured payload with its two integers
# moved, which is as close to captured as a second create can get from a single
# `gh api` capture. Its number and id disagree for the same reason the real
# one's do.
ISSUE_26 = {
    **ISSUE_25,
    "number": 26,
    "id": 5046900301,
    "html_url": "https://github.com/Tsadoq/claude-better-plan/issues/26",
}

# The two capabilities the adapter is asked to spell calls for. Neither machine
# has the 2.94.0 link flags; that direction changes nothing here, because every
# link this module sends goes to the REST endpoints on both paths.
GH_INSTALLED = gh_capability.Capability(usable=True, version=(2, 82, 0), supports_link_flags=False)
NO_GH = gh_capability.Capability(usable=False, version=None, supports_link_flags=False)


class _FakeGitHub:
    """A GitHub that answers from the fixtures and remembers what it was asked.

    `invocations` holds every call in arrival order, including creates: a create
    is an ordinary `POST repos/{owner}/{repo}/issues` on the REST path, so
    recording it as one is what lets an ordering assertion read a single list.
    """

    def __init__(
        self,
        *,
        issues: tuple[dict[str, Any], ...] = (ISSUE_25,),
        milestones: tuple[dict[str, Any], ...] = (),
        existing_labels: tuple[str, ...] = (),
    ) -> None:
        self.invocations: list[Any] = []
        self.created: list[tuple[str, str, str]] = []
        self._issues = list(issues)
        self._milestones = [dict(one) for one in milestones]
        self._existing_labels = set(existing_labels)

    def run(self, invocation: Any) -> Any:
        self.invocations.append(invocation)
        if invocation.argv:
            return issue_transport.Result(status=0, stdout="")

        body = invocation.body or {}
        if invocation.method == "GET" and invocation.url.startswith(f"repos/{REPO}/milestones"):
            return issue_transport.Result(status=200, json=list(self._milestones))
        if invocation.method == "POST" and invocation.url == f"repos/{REPO}/labels":
            if body.get("name") in self._existing_labels:
                # What the REST path gets for a label whose name is taken, and
                # the shape `RestTransport` raises it in.
                raise issue_transport.CallFailed(invocation.summary, 422, "already_exists")
            return issue_transport.Result(status=201, json=dict(body))
        if invocation.method == "POST" and invocation.url == f"repos/{REPO}/milestones":
            created = {"title": body["title"], "number": len(self._milestones) + 1}
            self._milestones.append(created)
            return issue_transport.Result(status=201, json=created)
        return issue_transport.Result(status=200, json={})

    def create_issue(self, repo: str, title: str, body: str) -> Any:
        assert self._issues, "the adapter created more issues than this test seeded payloads for"
        payload = self._issues.pop(0)
        self.created.append((repo, title, body))
        self.invocations.append(
            issue_transport.Invocation(
                summary=f"create issue in {repo}: {title}",
                method="POST",
                url=f"repos/{repo}/issues",
                body={"title": title, "body": body},
            )
        )
        return issue_transport.Filed(number=payload["number"], id=payload["id"], url=payload["html_url"])

    def sent(self, url: str) -> Any:
        """The one invocation aimed at `url`, or a failure naming what was sent
        instead -- a missing call and a duplicated one are different bugs."""
        matching = [one for one in self.invocations if one.url == url]
        sent = [one.url or one.argv for one in self.invocations]
        assert len(matching) == 1, f"expected exactly one call to {url}, got {sent}"
        return matching[0]


def _write_slice(
    tmp_path: Path,
    name: str,
    *,
    slice_id: str,
    title: str,
    labels: str = "[]",
    milestone: str | None = None,
    filed: dict[str, Any] | None = None,
) -> Any:
    """A real slice file, read back through the real parser.

    Written and re-read rather than constructed, so these tests file what
    `read_slice` actually produces rather than what a hand-built `Slice` would.
    `labels` is the raw frontmatter text, so a test can write a malformed value
    the way somebody's editor would.
    """
    lines = [
        "---",
        f"slice: {slice_id}",
        f"title: {title}",
        "activity: Review a cohort",
        "roadmap_item: ITEM2",
        f"labels: {labels}",
    ]
    if milestone is not None:
        lines.append(f"milestone: {milestone}")
    if filed is not None:
        lines.append(f"filed_github: {json.dumps(filed)}")
    lines += ["---", "", "## Context", "", "Somebody wrote this.", ""]

    path = tmp_path / name
    path.write_text("\n".join(lines), encoding="utf-8")
    return slice_file.read_slice(path)


def test_link_child_sends_database_id_not_issue_number(tmp_path: Path) -> None:
    transport = _FakeGitHub()
    one = _write_slice(tmp_path, "slice-01.md", slice_id="SLICE-01", title="Narrow the roster")

    filed = [
        record
        for _, record in github_destination.file_slices(
            transport, REPO, [one], capability=NO_GH, parent=PARENT
        )
    ]

    assert [record.number for record in filed] == [ISSUE_25["number"]], (
        "the batch reported an issue other than the one the transport filed"
    )
    link = transport.sent(f"repos/{REPO}/issues/{PARENT}/sub_issues")
    assert link.body == {"sub_issue_id": ISSUE_25["id"]}, (
        "the sub-issue call must carry the child's database id. GitHub reads this field as an id, so "
        "sending the issue number instead either attaches an unrelated issue or fails, and neither "
        "outcome says which"
    )
    assert str(ISSUE_25["number"]) not in json.dumps(link.body), (
        f"the issue number {ISSUE_25['number']} reached the sub-issue body, which is the one integer "
        "that endpoint must never see"
    )


def test_labels_are_created_with_the_spelling_the_local_gh_supports() -> None:
    names = ["product-issues", "size/S"]

    with_gh = _FakeGitHub()
    github_destination.ensure_labels(with_gh, REPO, names, capability=GH_INSTALLED)
    assert [one.argv for one in with_gh.invocations] == [
        ("gh", "label", "create", name, "--repo", REPO, "--force") for name in names
    ], (
        "a machine with gh must go through `gh label create --force`, which updates in place and so "
        "needs no prior existence check"
    )

    without_gh = _FakeGitHub(existing_labels=("product-issues",))
    github_destination.ensure_labels(without_gh, REPO, names, capability=NO_GH)
    assert [(one.method, one.url, one.body) for one in without_gh.invocations] == [
        ("POST", f"repos/{REPO}/labels", {"name": name}) for name in names
    ], (
        "the REST path must POST each label, and must read the 422 for the label that already exists "
        "as the state it wanted rather than as a failure that stops the batch"
    )


def test_every_label_the_batch_names_exists_before_the_first_issue_names_one(tmp_path: Path) -> None:
    transport = _FakeGitHub(issues=(ISSUE_25, ISSUE_26))
    first = _write_slice(
        tmp_path,
        "slice-01.md",
        slice_id="SLICE-01",
        title="Narrow the roster",
        labels='["product-issues", "size/S"]',
    )
    second = _write_slice(
        tmp_path, "slice-02.md", slice_id="SLICE-02", title="Show one cohort", labels='["product-issues"]'
    )

    list(github_destination.file_slices(transport, REPO, [first, second], capability=NO_GH, parent=PARENT))

    urls = [one.url for one in transport.invocations]
    before_first_create = urls[: urls.index(f"repos/{REPO}/issues")]
    assert before_first_create == [f"repos/{REPO}/labels"] * 2, (
        "every label the batch names must exist before an issue names one, and a label two slices "
        "share must be ensured once rather than once per slice"
    )


def test_each_issue_is_yielded_before_the_next_one_is_created(tmp_path: Path) -> None:
    transport = _FakeGitHub(issues=(ISSUE_25, ISSUE_26))
    slices = [
        _write_slice(tmp_path, "slice-01.md", slice_id="SLICE-01", title="Narrow the roster"),
        _write_slice(tmp_path, "slice-02.md", slice_id="SLICE-02", title="Show one cohort"),
    ]

    # The create count at each yield is what the caller's ledger write depends
    # on: it writes between two yields, so a later create having already
    # happened would mean a killed run could leave an issue no ledger records.
    at_each_yield = [
        (one.frontmatter["slice"], record.number, len(transport.created))
        for one, record in github_destination.file_slices(
            transport, REPO, slices, capability=NO_GH, parent=PARENT
        )
    ]

    assert at_each_yield == [("SLICE-01", 25, 1), ("SLICE-02", 26, 2)], (
        "each slice must be handed back paired with its own issue and before the next create, so the "
        "ledger a killed run leaves behind is true of every slice that got through and of no other"
    )


def test_a_milestone_the_repository_already_carries_is_reused_rather_than_recreated(
    tmp_path: Path,
) -> None:
    # Number 3 rather than 1: a milestone number is its own sequence, and one
    # that matched an issue number would hide a mix-up between them.
    transport = _FakeGitHub(milestones=({"title": "Release 1", "number": 3},))
    one = _write_slice(
        tmp_path,
        "slice-01.md",
        slice_id="SLICE-01",
        title="Narrow the roster",
        labels='["size/S"]',
        milestone="Release 1",
    )

    list(github_destination.file_slices(transport, REPO, [one], capability=NO_GH, parent=None))

    posted = [call.url for call in transport.invocations if call.method == "POST"]
    assert f"repos/{REPO}/milestones" not in posted, (
        "an existing milestone was created again, and GitHub answers that with a 422 that stops the batch"
    )
    assert transport.sent(f"repos/{REPO}/issues/{ISSUE_25['number']}").body == {
        "labels": ["size/S"],
        "milestone": 3,
    }, "the issue must carry the labels its slice names and the number of the milestone it belongs to"


def test_a_milestone_the_repository_lacks_is_created_and_its_number_used(tmp_path: Path) -> None:
    transport = _FakeGitHub(issues=(ISSUE_25, ISSUE_26))
    slices = [
        _write_slice(
            tmp_path, f"slice-0{n}.md", slice_id=f"SLICE-0{n}", title=f"Slice {n}", milestone="Release 2"
        )
        for n in (1, 2)
    ]

    list(github_destination.file_slices(transport, REPO, slices, capability=NO_GH, parent=None))

    created = [call for call in transport.invocations if call.url == f"repos/{REPO}/milestones"]
    assert [(call.method, call.body) for call in created] == [("POST", {"title": "Release 2"})], (
        "a milestone two slices share must be created once, from the title their frontmatter names"
    )
    assert transport.sent(f"repos/{REPO}/issues/{ISSUE_26['number']}").body["milestone"] == 1, (
        "the second issue must be filed against the milestone the first one created, read from that "
        "create's own response rather than assumed"
    )


def test_blocked_by_is_a_separate_endpoint_from_sub_issues_with_its_own_body_key() -> None:
    transport = _FakeGitHub()

    github_destination.link_blocked_by(transport, REPO, ISSUE_26["number"], ISSUE_25["id"])

    blocked = transport.sent(f"repos/{REPO}/issues/{ISSUE_26['number']}/dependencies/blocked_by")
    assert blocked.body == {"issue_id": ISSUE_25["id"]}, (
        "dependencies spell the database id as `issue_id` while sub-issues spell it `sub_issue_id`; "
        "GitHub ignores an unknown field, so borrowing the other endpoint's key sends a call that "
        "succeeds and links nothing"
    )


@pytest.mark.parametrize(
    ("extra", "why"),
    [
        (
            {"filed": {"number": 25, "id": ISSUE_25["id"], "url": ISSUE_25["html_url"]}},
            "a slice that already records an issue would be filed twice, and neither issue could be "
            "un-filed afterwards",
        ),
        (
            {"labels": "product-issues"},
            "labels that are one string rather than a list would iterate as their own characters and "
            "file a label per letter",
        ),
        ({"milestone": ""}, "a blank milestone title would create an unnamed milestone"),
    ],
)
def test_a_slice_this_module_will_not_file_stops_the_batch_before_any_call(
    tmp_path: Path, extra: dict[str, Any], why: str
) -> None:
    one = _write_slice(
        tmp_path, "slice-01.md", slice_id="SLICE-01", title="Narrow the roster", **extra
    )
    transport = _FakeGitHub()

    with pytest.raises(github_destination.SliceNotFilable) as refused:
        list(github_destination.file_slices(transport, REPO, [one], capability=NO_GH, parent=PARENT))

    assert "SLICE-01" in str(refused.value), "the refusal must name the slice, since somebody has to open it"
    assert transport.invocations == [], f"the batch reached GitHub before refusing, and {why}"


def test_a_dry_run_describes_the_whole_sequence_without_making_a_call(tmp_path: Path) -> None:
    described: list[str] = []
    transport = issue_transport.DryRunTransport(stream=_Sink(described))
    one = _write_slice(
        tmp_path,
        "slice-01.md",
        slice_id="SLICE-01",
        title="Narrow the roster",
        labels='["size/S"]',
        milestone="Release 1",
    )

    filed = list(
        github_destination.file_slices(transport, REPO, [one], capability=NO_GH, parent=PARENT)
    )

    assert len(filed) == 1, "the dry run did not reach the end of the sequence it exists to preview"
    urls = [call.url for call in transport.invocations]
    assert urls == [
        f"repos/{REPO}/labels",
        f"repos/{REPO}/milestones?state=all&per_page=100",
        f"repos/{REPO}/milestones",
        f"repos/{REPO}/issues",
        f"repos/{REPO}/issues/-1",
        f"repos/{REPO}/issues/{PARENT}/sub_issues",
    ], (
        "a dry run must describe the create *and* the linking that follows it; a preview that stops at "
        "the create is not a preview of what filing does. It can answer no read, so it plans the "
        "milestone it cannot see and carries the placeholder issue number the transport handed back"
    )
    assert len(described) == len(urls), "every described call must have been printed exactly once"


class _Sink:
    """Somewhere for the dry run's own printing to go, so the test's output is
    the invocation list rather than six lines of console noise."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def write(self, text: str) -> int:
        if text.strip():
            self._lines.append(text.strip())
        return len(text)
