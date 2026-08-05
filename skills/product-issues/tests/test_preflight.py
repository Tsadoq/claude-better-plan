
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

RICE_TEMPLATE = HERE.parents[1] / "product-roadmap" / "references" / "rice-template.md"


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
preflight = _load("preflight")

CAPTURED_VERSION = (FIXTURES / "gh_version.txt").read_text(encoding="utf-8")
CAPTURED_HELP = (FIXTURES / "gh_issue_create_help.txt").read_text(encoding="utf-8")

NO_CHILDREN = json.loads((FIXTURES / "sub_issues_empty.json").read_text(encoding="utf-8"))
ELEVEN_CHILDREN = json.loads((FIXTURES / "sub_issues_populated.json").read_text(encoding="utf-8"))

MARKER_PREFIX = "[UNKNOWN:"

MARKER = f"{MARKER_PREFIX} the acceptance threshold -- the support lead]"

PARENT_NUMBER = 25
TOP_LEVEL = 1


class _RecordingGh:

    def __init__(self) -> None:
        self.argvs: list[tuple[str, ...]] = []
        self._answers: dict[tuple[str, ...], str] = {
            ("gh", "--version"): CAPTURED_VERSION,
            ("gh", "issue", "create", "--help"): CAPTURED_HELP,
        }

    def run(self, invocation: Any) -> Any:
        self.argvs.append(invocation.argv)
        assert invocation.argv in self._answers, f"an unexpected command was run: {invocation.argv}"
        return issue_transport.Result(status=0, stdout=self._answers[invocation.argv])

    def create_issue(self, repo: str, title: str, body: str) -> Any:
        raise AssertionError("checking whether a batch may be filed must never create an issue")


def _write_slice(
    folder: Path,
    filename: str,
    *,
    slice_id: str,
    title: str = "Narrow the roster to one cohort",
    roadmap_item: str = "ITEM1",
    body: str = "## Acceptance criteria\n\n- the roster shows one cohort\n",
) -> Any:
    path = folder / filename
    path.write_text(
        "---\n"
        f"slice: {slice_id}\n"
        f"title: {title}\n"
        "activity: Review a cohort\n"
        f"roadmap_item: {roadmap_item}\n"
        'labels: ["product-issues", "size/S"]\n'
        "---\n"
        f"\n{body}",
        encoding="utf-8",
    )
    return slice_file.read_slice(path)


def _write_roadmap(folder: Path, *items: str) -> Path:
    row = "| `{item}` | `do the thing` | `REQ1` | 12 | 2 | 80% | 1 | 19.2 | 2 weeks |\n"
    rows = "".join(row.format(item=item) for item in items)
    path = folder / "roadmap.md"
    path.write_text(
        "# Roadmap\n\n## Items\n\n"
        "| ID | Item | Requirements | Reach | Impact | Confidence | Effort | RICE | Appetite |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n" + rows,
        encoding="utf-8",
    )
    return path


def _three_slices(folder: Path, *, marked: str | None = None, in_title: bool = False) -> list[Any]:
    second: dict[str, str] = {}
    if marked is not None and in_title:
        second["title"] = f"Narrow the roster to {marked}"
    elif marked is not None:
        second["body"] = f"## Acceptance criteria\n\n- the roster shows {marked}\n"

    return [
        _write_slice(folder, "01-list-the-roster.md", slice_id="SLICE-01", roadmap_item="ITEM1"),
        _write_slice(folder, "02-narrow-the-roster.md", slice_id="SLICE-02", roadmap_item="ITEM2", **second),
        _write_slice(folder, "03-export-the-roster.md", slice_id="SLICE-03", roadmap_item="ITEM3"),
    ]


def _bytes_of(slices: list[Any]) -> dict[Path, bytes]:
    return {one.path: one.path.read_bytes() for one in slices}


@pytest.mark.parametrize("in_title", [False, True], ids=["in the body", "in a frontmatter value"])
def test_unknown_marker_in_one_slice_refuses_whole_batch(tmp_path: Path, in_title: bool) -> None:
    assert preflight.unknown_marker_prefix() == MARKER_PREFIX, (
        "production no longer reads the marker artifact-family.md publishes, so every slice carrying "
        "an unestablished value would be filed as though it were settled"
    )

    slices = _three_slices(tmp_path, marked=MARKER, in_title=in_title)
    first, marked, last = slices
    untouched = _bytes_of(slices)
    recorder = _RecordingGh()
    capability = gh_capability.detect(recorder)
    asked_during_detection = list(recorder.argvs)
    parent = preflight.Parent.from_sub_issues(PARENT_NUMBER, NO_CHILDREN, depth=TOP_LEVEL)
    roadmap = _write_roadmap(tmp_path, "ITEM1", "ITEM2", "ITEM3")

    with pytest.raises(preflight.UnknownMarkerPresent) as refused:
        preflight.check(slices, capability, parent, roadmap=roadmap)

    message = str(refused.value)
    assert marked.path.name in message, (
        "the refusal does not name the file to open, so the fix starts with a search"
    )
    assert marked.frontmatter["slice"] in message, (
        "the refusal does not name the slice carrying the marker"
    )
    assert first.frontmatter["slice"] not in message and last.frontmatter["slice"] not in message, (
        "the refusal names slices that carry no marker, so the reader cannot tell which one to fix"
    )

    assert recorder.argvs == asked_during_detection, (
        "pre-flight ran a command of its own; a batch that is about to be refused must have made no call"
    )
    assert _bytes_of(slices) == untouched, (
        "a slice file changed during a refused batch, so a run that files nothing still left a mark"
    )


def test_sub_issue_ceiling_counts_the_batch_against_the_parents_existing_children(tmp_path: Path) -> None:
    slices = _three_slices(tmp_path)
    roadmap = _write_roadmap(tmp_path, "ITEM1", "ITEM2", "ITEM3")
    capability = gh_capability.detect(_RecordingGh())

    assert preflight.Parent.from_sub_issues(14, ELEVEN_CHILDREN, depth=TOP_LEVEL).children == 11, (
        "the child count is not the length of what the sub_issues endpoint returned"
    )

    room = preflight.MAX_SUB_ISSUES - len(slices)
    exactly_full = preflight.Parent(PARENT_NUMBER, room, TOP_LEVEL)
    one_too_many = preflight.Parent(PARENT_NUMBER, room + 1, TOP_LEVEL)

    preflight.check(slices, capability, exactly_full, roadmap=roadmap)

    with pytest.raises(preflight.SubIssueCeiling) as refused:
        preflight.check(slices, capability, one_too_many, roadmap=roadmap)
    message = str(refused.value)
    assert str(preflight.MAX_SUB_ISSUES) in message, "the refusal does not name the ceiling it hit"
    assert str(room + 1) in message and str(len(slices)) in message, (
        "the refusal names neither what is already there nor what this batch would add, which are the "
        "two numbers somebody needs to decide how to split the batch"
    )


def test_nesting_ceiling_refuses_a_parent_already_at_the_deepest_level(tmp_path: Path) -> None:
    slices = _three_slices(tmp_path)
    roadmap = _write_roadmap(tmp_path, "ITEM1", "ITEM2", "ITEM3")
    capability = gh_capability.detect(_RecordingGh())
    deepest = preflight.MAX_NESTING_DEPTH

    preflight.check(slices, capability, preflight.Parent(PARENT_NUMBER, 0, deepest - 1), roadmap=roadmap)

    with pytest.raises(preflight.NestingCeiling) as refused:
        preflight.check(slices, capability, preflight.Parent(PARENT_NUMBER, 0, deepest), roadmap=roadmap)
    assert str(deepest) in str(refused.value), "the refusal does not name the depth limit it hit"


def test_slice_naming_an_item_absent_from_the_roadmap_refuses_the_batch(tmp_path: Path) -> None:
    slices = _three_slices(tmp_path)
    first, unmoored, last = slices
    capability = gh_capability.detect(_RecordingGh())
    parent = preflight.Parent.from_sub_issues(PARENT_NUMBER, NO_CHILDREN, depth=TOP_LEVEL)
    roadmap = _write_roadmap(tmp_path, first.frontmatter["roadmap_item"], last.frontmatter["roadmap_item"])

    with pytest.raises(preflight.SliceWithoutUpstream) as refused:
        preflight.check(slices, capability, parent, roadmap=roadmap)

    message = str(refused.value)
    assert unmoored.frontmatter["slice"] in message, "the refusal does not name the slice to fix"
    assert unmoored.frontmatter["roadmap_item"] in message, (
        "the refusal does not name the item the slice claims to come from, which is the id to look for"
    )
    assert first.frontmatter["slice"] not in message and last.frontmatter["slice"] not in message, (
        "slices whose item is in the roadmap were reported as unmoored"
    )


def test_the_item_id_form_matched_here_is_the_one_the_roadmap_template_publishes(tmp_path: Path) -> None:
    assert preflight.ROADMAP_ITEM_FORM in RICE_TEMPLATE.read_text(encoding="utf-8"), (
        f"{RICE_TEMPLATE.name} no longer publishes item ids of the form "
        f"{preflight.ROADMAP_ITEM_FORM!r}, so preflight is matching a shape no roadmap writes any more "
        "and would call every slice in every batch unmoored"
    )

    other_shape = "TASK1"
    slices = [_write_slice(tmp_path, "01-list-the-roster.md", slice_id="SLICE-01", roadmap_item=other_shape)]
    roadmap = tmp_path / "roadmap.md"
    roadmap.write_text(f"# Roadmap\n\n| `{other_shape}` | `do the thing` |\n", encoding="utf-8")

    with pytest.raises(preflight.SliceWithoutUpstream):
        preflight.check(
            slices,
            gh_capability.detect(_RecordingGh()),
            preflight.Parent.from_sub_issues(PARENT_NUMBER, NO_CHILDREN, depth=TOP_LEVEL),
            roadmap=roadmap,
        )


def test_a_roadmap_that_cannot_be_read_refuses_the_batch_naming_the_file(tmp_path: Path) -> None:
    slices = _three_slices(tmp_path)
    capability = gh_capability.detect(_RecordingGh())
    parent = preflight.Parent.from_sub_issues(PARENT_NUMBER, NO_CHILDREN, depth=TOP_LEVEL)
    absent = tmp_path / "nowhere" / "roadmap.md"

    with pytest.raises(preflight.SliceWithoutUpstream) as refused:
        preflight.check(slices, capability, parent, roadmap=absent)

    assert str(absent) in str(refused.value), (
        "a roadmap that is not there must be named as the reason. Reporting it as three slices with "
        "bad ids sends somebody to edit three files that are correct"
    )


def test_a_marker_that_cannot_be_read_refuses_rather_than_matching_nothing(tmp_path: Path) -> None:
    with pytest.raises(preflight.MarkerContractUnreadable):
        preflight.unknown_marker_prefix(tmp_path / "nowhere" / "artifact-family.md")

    hollow = tmp_path / "artifact-family.md"
    hollow.write_text(f"# Contract\n\n{preflight.MARKER_HEADING}\n\nno fenced block here\n", encoding="utf-8")
    with pytest.raises(preflight.MarkerContractUnreadable):
        preflight.unknown_marker_prefix(hollow)


ADVERTISES_LINK_FLAGS = gh_capability.Capability(usable=True, version=(2, 94, 0), supports_link_flags=True)
ADVERTISES_NEITHER = gh_capability.Capability(usable=True, version=(2, 82, 0), supports_link_flags=False)


@pytest.mark.parametrize(
    ("parent", "refusal"),
    [
        (preflight.Parent(PARENT_NUMBER, preflight.MAX_SUB_ISSUES, TOP_LEVEL), preflight.SubIssueCeiling),
        (preflight.Parent(PARENT_NUMBER, 0, preflight.MAX_NESTING_DEPTH), preflight.NestingCeiling),
    ],
    ids=["sub-issue ceiling", "nesting ceiling"],
)
def test_a_ceiling_refusal_says_a_breach_would_have_left_an_issue_filed_and_unattached(
    tmp_path: Path, parent: Any, refusal: type[Exception]
) -> None:
    slices = _three_slices(tmp_path)
    roadmap = _write_roadmap(tmp_path, "ITEM1", "ITEM2", "ITEM3")

    told = []
    for capability in (ADVERTISES_LINK_FLAGS, ADVERTISES_NEITHER):
        with pytest.raises(refusal) as refused:
            preflight.check(slices, capability, parent, roadmap=roadmap)
        told.append(str(refused.value))

    for message in told:
        assert "would have been filed" in message and "unattached" in message, (
            "the refusal does not say what the breach would have left behind -- an issue created and "
            f"then attached to nothing -- so nobody knows to go and clean it up: {message}"
        )
        assert "on the create itself" not in message, (
            "the refusal claims this gh sends the links on the create. Nothing does: the links are REST "
            "calls made after every create, so this promises a create that was refused when the issue "
            f"is really there and unattached: {message}"
        )

    assert told[0] == told[1], (
        "the two `gh` were told different things about what a breach would have cost, but the linking "
        "calls are the same on both, so the cost is the same too"
    )
