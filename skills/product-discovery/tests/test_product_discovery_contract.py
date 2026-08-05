
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"
SKILL_MD = SKILL_ROOT / "SKILL.md"
OST_TEMPLATE = REFERENCES / "opportunity-solution-tree-template.md"
DISCOVERY_PRINCIPLES = REFERENCES / "product-discovery-principles.md"

REPO_ROOT = SKILL_ROOT.parents[1]

ARTIFACT_FAMILY = (
    SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"
)

DISCOVERY_SECTION_BULLET = re.compile(
    r"^- `discovery\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE
)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

UNKNOWN_MARKER_HEADING = "## Unknown marker"
FENCED_BLOCK = re.compile(r"```\n(.+?)\n```", re.DOTALL)

PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


def _plugin_root_citation(path: Path) -> str:
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


ARTIFACT_FAMILY_CITATION = _plugin_root_citation(ARTIFACT_FAMILY)

TREE_SECTION = "The tree"

NESTED_SECTIONS = {
    "Signals": (TREE_SECTION, "Market sizing"),
    "Constraints": ("Assumption mapping",),
    "Open questions": ("Riskiest assumption tests", "JTBD switch-interview structure"),
}

PARENT_COLUMN = "Parent"
EVIDENCE_COLUMN = "Evidence"

ID_NUMBER_PLACEHOLDER = "<n>"

RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

RED_FLAG_CLUSTER_COUNT = 4

SEVERITY_HINT = "Severity hint:"


class NodeLayer(NamedTuple):

    id_column: str
    id_form: str
    names_a_parent: bool
    carries_evidence: bool

    @property
    def id_prefix(self) -> str:
        return self.id_form.removesuffix(ID_NUMBER_PLACEHOLDER)


NODE_LAYERS = (
    NodeLayer("Outcome id", "OUT<n>", names_a_parent=False, carries_evidence=False),
    NodeLayer("Opportunity id", "OPP<n>", names_a_parent=True, carries_evidence=True),
    NodeLayer("Solution id", "SOL<n>", names_a_parent=True, carries_evidence=False),
    NodeLayer("Assumption test id", "AT<n>", names_a_parent=True, carries_evidence=False),
)


RUNTIME_RULES = (
    (
        "whether the upstream is there is answered by the substrate, not by a local stat",
        "--check-freshness",
    ),
    (
        "the provenance line is read off the substrate rather than assembled here",
        "--provenance-line",
    ),
    (
        "the market-sizing sweep names the agent it launches",
        "deep-plan:dp-research-shallow",
    ),
    (
        "every refusal names the beat that would fix it",
        "product-brief",
    ),
    (
        "a second run replaces the member rather than refusing or merging into it",
        "replaces discovery.md",
    ),
)

UNKNOWN_MARKER_RULE = "an unestablished slot takes the unknown marker"

CITED_REFERENCES = (
    ("the document's shape is read from the template, not recalled", OST_TEMPLATE),
    ("the judgement rules are read from the rubric, not recalled", DISCOVERY_PRINCIPLES),
)

FORBIDDEN_FRONTMATTER_KEYS = (
    (
        "disable-model-invocation",
        "it is the documented way to drop a skill from the model-facing listing, "
        "leaving it reachable only by someone who types its name -- and this beat is "
        "meant to be reached from a brief the user is talking about",
    ),
    (
        "allowed-tools",
        "an allowlist strips the ambient tools the body's own steps call: the freshness "
        "check, the provenance line, the background sizing sweep and the evidence "
        "interview would each fail on a tool the frontmatter had narrowed away",
    ),
)


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


def _at_level(headings: list[tuple[int, str, int]], level: int) -> list[tuple[str, int]]:
    return [(text, lineno) for depth, text, lineno in headings if depth == level]


def _section_span(
    headings: list[tuple[int, str, int]], level: int, name: str, last_line: int
) -> tuple[int, int]:
    start = next(
        (line for depth, text, line in headings if depth == level and text == name),
        None,
    )
    if start is None:
        return last_line + 1, last_line + 1
    end = next(
        (line for depth, _text, line in headings if line > start and depth <= level),
        last_line + 1,
    )
    return start, end


def _section_body(lines: list[str], span: tuple[int, int]) -> list[str]:
    start, stop = span
    return lines[start : stop - 1]


def _discovery_section_names(substrate: str) -> list[str]:
    bullet = DISCOVERY_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _unknown_marker_prefix(substrate: str) -> str:
    after_heading = substrate[substrate.index(UNKNOWN_MARKER_HEADING) :]
    block = FENCED_BLOCK.search(after_heading)
    if block is None:
        return ""
    token, separator, _payload = block.group(1).strip().partition(":")
    return token + separator if separator else ""


def _table_cells(row: str) -> list[str]:
    return [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]


def _node_table(body: list[str], id_column: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body:
        if not line.lstrip().startswith("|"):
            if rows:
                break
            continue
        cells = _table_cells(line)
        if not rows:
            if cells and cells[0] == id_column:
                rows.append(cells)
            continue
        if set("".join(cells)) <= set("-:"):
            continue
        rows.append(cells)
    return rows


def _skill_body(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return "" if end == -1 else text[end + len("\n---") :]


def _guarantees() -> ModuleType:
    source = REPO_ROOT / "tests" / "guarantees.py"
    spec = importlib.util.spec_from_file_location("guarantees", source)
    assert spec and spec.loader, f"cannot load {source}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tree_template_nests_the_five_sections_under_the_published_headings() -> None:
    assert OST_TEMPLATE.exists(), f"missing shipped template: {OST_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = OST_TEMPLATE.read_text()

    required_sections = _discovery_section_names(substrate)
    assert sorted(required_sections) == sorted(NESTED_SECTIONS), (
        f"NESTED_SECTIONS groups the template's H3 sections under "
        f"{sorted(NESTED_SECTIONS)}, but {ARTIFACT_FAMILY.name} publishes "
        f"{required_sections} for discovery.md. Each H3 is grouped by what its "
        f"parent heading means, so a renamed section needs re-grouping by hand "
        f"rather than silently keeping its old children"
    )

    lines = template.splitlines()
    headings = _headings(template)
    h2 = _at_level(headings, 2)
    h2_names = [text for text, _ in h2]

    for name in required_sections:
        occurrences = h2_names.count(name)
        assert occurrences == 1, (
            f"expected '## {name}' to appear exactly once as an H2 in "
            f"{OST_TEMPLATE.name}, found {occurrences}; {ARTIFACT_FAMILY.name} "
            f"requires the section of discovery.md, and the template has {h2_names}"
        )

    h2_line = dict(h2)
    ordered = [h2_line[name] for name in required_sections]
    assert ordered == sorted(ordered), (
        f"{OST_TEMPLATE.name} must carry discovery.md's sections in the order "
        f"{ARTIFACT_FAMILY.name} publishes {required_sections}; found them at "
        f"lines {ordered}"
    )

    h3_lines: dict[str, list[int]] = {}
    for text, line in _at_level(headings, 3):
        h3_lines.setdefault(text, []).append(line)

    for parent in required_sections:
        parent_start, parent_end = _section_span(headings, 2, parent, len(lines))
        for child in NESTED_SECTIONS[parent]:
            found = h3_lines.get(child, [])
            assert len(found) == 1, (
                f"expected '### {child}' to appear exactly once as an H3 in "
                f"{OST_TEMPLATE.name}, found it at lines {found}; its H3 headings "
                f"are {sorted(h3_lines)}"
            )
            assert parent_start < found[0] < parent_end, (
                f"'### {child}' sits at line {found[0]}, outside '## {parent}' "
                f"(line {parent_start}) and the section that follows it (line "
                f"{parent_end}); the five framework sections nest inside the three "
                f"H2s {ARTIFACT_FAMILY.name} publishes"
            )

    tree_body = _section_body(
        lines, _section_span(headings, 3, TREE_SECTION, len(lines))
    )
    tree_text = "\n".join(tree_body)
    for layer in NODE_LAYERS:
        rows = _node_table(tree_body, layer.id_column)
        assert rows, (
            f"'### {TREE_SECTION}' of {OST_TEMPLATE.name} has no table whose header "
            f"row opens on '{layer.id_column}'; each of the four layers carries its "
            f"own table so that only the layers needing a column declare one"
        )
        header, *node_rows = rows
        assert layer.id_form in tree_text, (
            f"'### {TREE_SECTION}' of {OST_TEMPLATE.name} never states the id form "
            f"'{layer.id_form}'. The layer prefix is what makes a mis-parented node "
            f"wrong on sight in the parent cell; a single unprefixed sequence would "
            f"read the same whatever it was parented to"
        )

        assert node_rows, (
            f"the '{layer.id_column}' table of {OST_TEMPLATE.name} has a header row "
            f"and no rows under it; the id notation is only observable in a row, so "
            f"a header-only table leaves this layer's prefix unpinned"
        )
        for cells in node_rows:
            assert re.fullmatch(rf"{re.escape(layer.id_prefix)}\d+", cells[0]), (
                f"the '{layer.id_column}' table of {OST_TEMPLATE.name} has a row "
                f"whose id reads {cells[0]!r}, which is not of the form "
                f"'{layer.id_form}' the rules state. The layer prefix is what makes "
                f"a mis-parented node wrong on sight in the parent cell, and a row "
                f"that drops it takes that property with it"
            )

        assert (PARENT_COLUMN in header) == layer.names_a_parent, (
            f"the '{layer.id_column}' table of {OST_TEMPLATE.name} "
            f"{'must' if layer.names_a_parent else 'must not'} declare a "
            f"'{PARENT_COLUMN}' column; its header row is {header}. The outcome is "
            f"the root and has nothing to name, and every other layer names exactly "
            f"one parent by id"
        )
        assert (EVIDENCE_COLUMN in header) == layer.carries_evidence, (
            f"the '{layer.id_column}' table of {OST_TEMPLATE.name} "
            f"{'must' if layer.carries_evidence else 'must not'} declare an "
            f"'{EVIDENCE_COLUMN}' column; its header row is {header}. Opportunities "
            f"carry evidence because an unevidenced one is a guess, and a layer that "
            f"carried the column only to leave it blank would make a blank cell and "
            f"a guess look alike"
        )

    marker_prefix = _unknown_marker_prefix(substrate)
    assert marker_prefix, (
        f"could not read the unknown-marker literal out of {ARTIFACT_FAMILY.name}; "
        f"expected a fenced block under {UNKNOWN_MARKER_HEADING!r}"
    )
    assert marker_prefix not in template, (
        f"{OST_TEMPLATE.name} restates the unknown marker ({marker_prefix!r}); it must "
        f"cite {ARTIFACT_FAMILY_CITATION} for the token instead of carrying a copy "
        f"that can drift from the definition"
    )
    assert ARTIFACT_FAMILY_CITATION in template, (
        f"{OST_TEMPLATE.name} must cite {ARTIFACT_FAMILY_CITATION}, which is where "
        f"both the section names it renders and the marker an unestablished slot "
        f"takes are defined"
    )


def test_principles_expose_four_red_flag_clusters() -> None:
    assert DISCOVERY_PRINCIPLES.exists(), f"missing shipped rubric: {DISCOVERY_PRINCIPLES}"

    principles = DISCOVERY_PRINCIPLES.read_text()
    lines = principles.splitlines()
    headings = _headings(principles)

    h2 = _at_level(headings, 2)
    h2_names = [text for text, _ in h2]

    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{DISCOVERY_PRINCIPLES.name}, found {occurrences}; it shares its heading "
            f"spine with the plugin's other rubric files so that an orchestrator can "
            f"quote one section by name, and it has {h2_names}"
        )

    h2_line = dict(h2)

    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"{DISCOVERY_PRINCIPLES.name} must carry its spine sections in the order "
        f"{list(PRINCIPLES_SPINE)}, the order its sibling rubric files use; found "
        f"them at lines {spine_lines}"
    )

    section_start, section_end = _section_span(
        headings, 2, RED_FLAGS_SECTION, len(lines)
    )
    clusters = [
        (text, line)
        for text, line in _at_level(headings, 3)
        if section_start < line < section_end
    ]
    cluster_names = [text for text, _ in clusters]
    assert len(clusters) == RED_FLAG_CLUSTER_COUNT, (
        f"expected exactly {RED_FLAG_CLUSTER_COUNT} H3 clusters under "
        f"'## {RED_FLAGS_SECTION}' in {DISCOVERY_PRINCIPLES.name}, found {len(clusters)}: "
        f"{cluster_names}; a review launches one finder per cluster, so the count "
        f"is part of what this file publishes"
    )

    cluster_ends = [line for _, line in clusters[1:]] + [section_end]
    for (name, start), stop in zip(clusters, cluster_ends, strict=True):
        body = _section_body(lines, (start, stop))
        assert any(line.rstrip().endswith("?") for line in body), (
            f"cluster '### {name}' of {DISCOVERY_PRINCIPLES.name} carries no line ending in a "
            f"question mark; every cluster is a set of questions a reviewer answers "
            f"yes or no against a written discovery.md, and prose cannot be "
            f"answered. The four clusters are {cluster_names}"
        )
        assert any(SEVERITY_HINT in line for line in body), (
            f"cluster '### {name}' of {DISCOVERY_PRINCIPLES.name} carries no "
            f"{SEVERITY_HINT!r} line; a question without one yields a finding a "
            f"reviewer cannot route as material or minor. The four clusters are "
            f"{cluster_names}"
        )


def test_skill_publishes_each_runtime_rule() -> None:
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    skill = SKILL_MD.read_text()
    body = _skill_body(skill)
    assert body, (
        f"{SKILL_MD.name} carries no `---` frontmatter block for its body to follow, so the "
        f"harness has no description to route on and the rules below would be searched for "
        f"in a file whose shape is already wrong"
    )
    assert not re.search(r"^description:", body, re.MULTILINE), (
        f"{SKILL_MD.name}'s frontmatter survived into what `_skill_body` returned as its "
        f"body, so this module and tests/guarantees.py no longer agree on where the block "
        f"ends. Every rule below would pass on a rule stated only in the description, which "
        f"is text the model routes on and never acts from"
    )

    published = body.replace("`", "")

    marker_prefix = _unknown_marker_prefix(ARTIFACT_FAMILY.read_text())
    assert marker_prefix, (
        f"could not read the unknown-marker literal out of {ARTIFACT_FAMILY.name}; "
        f"expected a fenced block under {UNKNOWN_MARKER_HEADING!r}"
    )

    rules = (
        *RUNTIME_RULES,
        (UNKNOWN_MARKER_RULE, marker_prefix),
        *((rule, _plugin_root_citation(path)) for rule, path in CITED_REFERENCES),
    )
    for rule, literal in rules:
        assert literal in published, (
            f"{SKILL_MD.name} does not publish the rule that {rule}: the literal "
            f"{literal!r} appears nowhere in its body. Nothing can check a generated "
            f"discovery.md against this rule after the fact, so the body stating it is the "
            f"only place the rule exists at all"
        )


def test_skill_frontmatter_omits_the_keys_that_would_disable_it() -> None:
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    frontmatter_value = _guarantees().frontmatter_value
    skill = SKILL_MD.read_text()

    for key, consequence in FORBIDDEN_FRONTMATTER_KEYS:
        declared = frontmatter_value(skill, key)
        assert declared is None, (
            f"{SKILL_MD.name} declares {key!r} (value {declared!r}), and {consequence}. "
            f"Removing the key is the fix; keeping it means the run-time rules the body "
            f"publishes are rules nothing will reach"
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
