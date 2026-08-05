
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO = SKILL_ROOT.parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
REFERENCES = SKILL_ROOT / "references"
SCRIPTS = SKILL_ROOT / "scripts"
STORY_MAP_TEMPLATE = REFERENCES / "story-map-template.md"
ISSUES_PRINCIPLES = REFERENCES / "product-issues-principles.md"

ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"
INVEST_GATE = SKILL_ROOT.parent / "product-requirements" / "references" / "requirements-template.md"

PLUGIN_MANIFEST = REPO / ".claude-plugin" / "plugin.json"

PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"
PLUGIN_ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")

BARE_PLUGIN_PATH = re.compile(r"(?<!\$\{CLAUDE_PLUGIN_ROOT\}/)skills/")

STAMPED_VERSION = r"/\d+\.\d+\.\d+"

RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

CLUSTER_LEVEL = 3
MINIMUM_RED_FLAG_CLUSTERS = 4

RERUN_SECTION = "Re-run behaviour"

REQUIRED_KEYS_SECTION = "Required keys"
UNKNOWN_MARKER_SECTION = "Unknown marker"

MARKER_TOKEN = re.compile(r"\[([A-Z][A-Z ]{2,}):")

INVEST_CRITERIA = ("Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable")
INVEST_CRITERIA_CEILING = 1


def _shipped_files() -> list[Path]:
    return [SKILL_MD, *sorted(REFERENCES.glob("*.md")), *sorted(SCRIPTS.glob("*.py"))]


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader, f"could not load {name} from {SCRIPTS}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _headings(markdown: str) -> list[tuple[int, str, int]]:
    headings = []
    inside_fence = False
    for lineno, line in enumerate(markdown.splitlines(), start=1):
        if line.startswith("```"):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue
        match = re.match(r"^(#{1,6}) (.+?)\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2), lineno))
    return headings


def _section_body(markdown: str, name: str) -> list[str]:
    lines = markdown.splitlines()
    headings = _headings(markdown)
    found = next(((depth, line) for depth, text, line in headings if text == name), None)
    if found is None:
        return []
    depth, start = found
    stop = next(
        (line for other, _text, line in headings if line > start and other <= depth),
        len(lines) + 1,
    )
    return lines[start : stop - 1]


def _first_table(body: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body:
        if not line.lstrip().startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if rows and set("".join(cells)) <= set("-:"):
            continue
        rows.append(cells)
    return rows


def _plugin_directory_name() -> str:
    return json.loads(PLUGIN_MANIFEST.read_text()).get("name", "")


def _invest_criteria_named(path: Path) -> list[str]:
    text = path.read_text()
    return sorted(criterion for criterion in INVEST_CRITERIA if re.search(rf"\b{criterion}\b", text))


def _published_marker_token() -> str:
    match = MARKER_TOKEN.search("\n".join(_section_body(ARTIFACT_FAMILY.read_text(), UNKNOWN_MARKER_SECTION)))
    return match.group(1) if match else ""


def test_skill_cites_plugin_root_and_never_a_stamped_path() -> None:
    assert SKILL_MD.is_file(), f"missing shipped skill body: {SKILL_MD}"
    assert PLUGIN_MANIFEST.is_file(), (
        f"missing plugin manifest: {PLUGIN_MANIFEST}. The stamped-path scan is built from "
        f"the directory name it declares, so nothing below is a check on anything without it"
    )

    skill = SKILL_MD.read_text()

    cited = PLUGIN_ROOT_PATH.findall(skill)
    assert cited, (
        f"{SKILL_MD.name} spells no {PLUGIN_ROOT_VARIABLE} path at all. This beat restates "
        f"none of its three reference files and reaches the substrate by script, so a body "
        f"citing nothing is one working from memory on every rule it does not carry"
    )

    for relative in cited:
        assert (REPO / relative).is_file(), (
            f"{SKILL_MD.name} cites {PLUGIN_ROOT_VARIABLE}/{relative}, which this repository "
            f"does not ship. A run following it reads nothing and carries on from memory, "
            f"which is the one failure a redirect was supposed to prevent"
        )

    sample = REFERENCES.relative_to(REPO).as_posix()
    assert BARE_PLUGIN_PATH.search(sample), (
        f"the unprefixed-path scanner no longer matches {sample!r}, so a clean sweep of "
        f"{SKILL_MD.name} would prove nothing about how its paths are spelled"
    )
    assert not BARE_PLUGIN_PATH.search(f"{PLUGIN_ROOT_VARIABLE}/{sample}"), (
        f"the unprefixed-path scanner matches the correctly prefixed {sample!r}, so it "
        f"reports every well-spelled citation in {SKILL_MD.name} as a defect"
    )

    bare = [
        (lineno, line)
        for lineno, line in enumerate(skill.splitlines(), start=1)
        if BARE_PLUGIN_PATH.search(line)
    ]
    assert not bare, (
        f"{SKILL_MD.name} names a path into the plugin tree without the "
        f"{PLUGIN_ROOT_VARIABLE} prefix, at {[lineno for lineno, _line in bare]}: "
        f"{[line.strip() for _lineno, line in bare]}. Unprefixed, it resolves against the "
        f"user's own repository, where nothing this plugin ships exists"
    )

    directory = _plugin_directory_name()
    assert directory, (
        f"{PLUGIN_MANIFEST.relative_to(REPO)} declares no 'name', so there is no plugin "
        f"directory to recognise a stamped path by and the scan below proves nothing"
    )

    stamped = re.compile(rf"/{re.escape(directory)}{STAMPED_VERSION}")
    installed = f"/home/someone/.claude/plugins/cache/a-repo/{directory}/9.9.9/{sample}"
    assert stamped.search(installed), (
        f"the stamped-path scanner {stamped.pattern!r} no longer matches {installed!r}, a "
        f"path out of an installed plugin cache, so the sweep below would report every "
        f"shipped file clean whatever they carried"
    )

    for path in _shipped_files():
        hits = stamped.findall(path.read_text())
        assert not hits, (
            f"{path.relative_to(REPO)} carries the version-stamped plugin path(s) {hits}. "
            f"That is a path copied out of an installed cache: it resolves in the session it "
            f"was copied from and in no session after the next release, so use "
            f"{PLUGIN_ROOT_VARIABLE} instead"
        )


def test_skill_publishes_the_re_run_section_a_second_run_reads() -> None:
    assert SKILL_MD.is_file(), f"missing shipped skill body: {SKILL_MD}"

    skill = SKILL_MD.read_text()
    occurrences = [text for _depth, text, _line in _headings(skill)].count(RERUN_SECTION)
    assert occurrences == 1, (
        f"expected '## {RERUN_SECTION}' exactly once in {SKILL_MD.name}, found "
        f"{occurrences}. Every beat in this suite publishes its second-run promise under "
        f"that heading, and a reader holding the previous version opens it by name"
    )

    body = "\n".join(_section_body(skill, RERUN_SECTION)).strip()
    assert body, (
        f"'## {RERUN_SECTION}' of {SKILL_MD.name} is empty. Nothing in this suite checks a "
        f"slice after it is written, so an empty section is a rule with no enforcement at "
        f"all rather than one enforced somewhere else"
    )


def test_principles_expose_the_clusters_a_review_fans_over() -> None:
    assert ISSUES_PRINCIPLES.is_file(), f"missing shipped rubric: {ISSUES_PRINCIPLES}"

    principles = ISSUES_PRINCIPLES.read_text()
    h2 = [(text, line) for depth, text, line in _headings(principles) if depth == 2]
    h2_names = [text for text, _line in h2]

    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' exactly once as an H2 in {ISSUES_PRINCIPLES.name}, "
            f"found {occurrences}; the file shares its heading spine with this suite's other "
            f"rubrics so an orchestrator can quote one section by name, and it carries "
            f"{h2_names}"
        )

    h2_line = dict(h2)
    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"{ISSUES_PRINCIPLES.name} must carry its spine sections in the order "
        f"{list(PRINCIPLES_SPINE)}, the order its sibling rubrics use; found them at lines "
        f"{spine_lines}"
    )

    red_flags = _section_body(principles, RED_FLAGS_SECTION)
    assert red_flags, (
        f"'## {RED_FLAGS_SECTION}' of {ISSUES_PRINCIPLES.name} has no body, so there is "
        f"nothing for the cluster count below to read. A review fans out over this section "
        f"alone, and an empty one launches no critics at all"
    )

    clusters = [text for depth, text, _line in _headings("\n".join(red_flags)) if depth == CLUSTER_LEVEL]
    assert len(clusters) >= MINIMUM_RED_FLAG_CLUSTERS, (
        f"expected at least {MINIMUM_RED_FLAG_CLUSTERS} H{CLUSTER_LEVEL} clusters under "
        f"'## {RED_FLAGS_SECTION}' in {ISSUES_PRINCIPLES.name}, found {len(clusters)}: "
        f"{clusters}. A review launches one finder per cluster, so a cluster dissolved into "
        f"prose is a question nobody asks of a slice set again"
    )


def test_template_cites_the_invest_gate_without_restating_it() -> None:
    assert STORY_MAP_TEMPLATE.is_file(), f"missing shipped template: {STORY_MAP_TEMPLATE}"
    assert INVEST_GATE.is_file(), (
        f"missing the gate's published home: {INVEST_GATE}. The citation below is built "
        f"from that path, so a citation could otherwise pass while naming nothing"
    )

    citation = f"{PLUGIN_ROOT_VARIABLE}/{INVEST_GATE.relative_to(REPO).as_posix()}"
    assert citation in STORY_MAP_TEMPLATE.read_text(), (
        f"{STORY_MAP_TEMPLATE.name} does not cite {citation}. Every slice passes the INVEST "
        f"gate before its file is written, and this template is the file a run reads while "
        f"cutting, so a missing citation is a gate applied from memory"
    )

    defining = _invest_criteria_named(INVEST_GATE)
    assert len(defining) > INVEST_CRITERIA_CEILING, (
        f"{INVEST_GATE.relative_to(REPO)} names only {defining} of the six INVEST criteria, "
        f"so either the gate has moved out of that file or this scan no longer recognises a "
        f"criterion where one is written out. Until it does, the ban below proves nothing"
    )

    for path in _shipped_files():
        named = _invest_criteria_named(path)
        assert len(named) <= INVEST_CRITERIA_CEILING, (
            f"{path.relative_to(REPO)} names {named} -- {len(named)} of Wake's six INVEST "
            f"criteria. One can be an ordinary word in a sentence; more than one is the gate "
            f"being restated, and its single definition lives at "
            f"{INVEST_GATE.relative_to(REPO)} under '## The INVEST gate'"
        )


def test_shipped_files_introduce_no_second_unknown_marker() -> None:
    assert ARTIFACT_FAMILY.is_file(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    published = _published_marker_token()
    assert published, (
        f"no marker token could be read from '## {UNKNOWN_MARKER_SECTION}' in "
        f"{ARTIFACT_FAMILY.relative_to(REPO)}, so there is no published dialect to hold "
        f"this skill to. Whether that file is still well formed belongs to its own contract "
        f"test; this one needs it only to know what to compare against"
    )

    for path in _shipped_files():
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            for token in MARKER_TOKEN.findall(line):
                assert token == published, (
                    f"{path.relative_to(REPO)}:{lineno} introduces the marker dialect "
                    f"`[{token}: ...]`, but this suite publishes `[{published}: ...]` in "
                    f"{ARTIFACT_FAMILY.relative_to(REPO)}. Pre-flight refuses a batch by "
                    f"searching for the published token, so a slice written with this one "
                    f"gets filed with its open question still in it"
                )


def test_template_publishes_the_frontmatter_schema_slice_file_requires() -> None:
    assert STORY_MAP_TEMPLATE.is_file(), f"missing shipped template: {STORY_MAP_TEMPLATE}"

    body = _section_body(STORY_MAP_TEMPLATE.read_text(), REQUIRED_KEYS_SECTION)
    assert body, (
        f"{STORY_MAP_TEMPLATE.name} carries no '### {REQUIRED_KEYS_SECTION}' section. That "
        f"heading is where the frontmatter schema is published, so a rename here is read "
        f"below as a template publishing no keys at all"
    )

    rows = _first_table(body)
    assert len(rows) > 1, (
        f"'### {REQUIRED_KEYS_SECTION}' of {STORY_MAP_TEMPLATE.name} carries no table with "
        f"rows; the schema is published as one row per key, so a header alone declares "
        f"columns without saying what a slice must carry"
    )

    published = tuple(row[0] for row in rows[1:])
    required = _load("slice_file").REQUIRED_KEYS
    assert published == required, (
        f"{STORY_MAP_TEMPLATE.name} publishes the required keys {published}, but "
        f"slice_file.REQUIRED_KEYS is {required}. The template is the schema's single home "
        f"and the tuple is the code's copy of it, so whichever moved, the other moves with "
        f"it in the same commit -- a key in one alone is either a slice nothing will accept "
        f"or a refusal nobody was warned about"
    )


if __name__ == "__main__":
    import traceback

    failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception:  # noqa: BLE001
                failed += 1
                print(f"FAIL {_name}")
                traceback.print_exc()
    sys.exit(1 if failed else 0)
