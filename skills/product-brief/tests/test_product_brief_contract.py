
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"
SKILL_MD = SKILL_ROOT / "SKILL.md"
PR_FAQ_TEMPLATE = REFERENCES / "pr-faq-template.md"
PRODUCT_BRIEF_PRINCIPLES = REFERENCES / "product-brief-principles.md"

REPO_ROOT = SKILL_ROOT.parents[1]

ARTIFACT_FAMILY = (
    SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"
)

BRIEF_SECTION_BULLET = re.compile(r"^- `brief\.md`:(.*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

UNKNOWN_MARKER_HEADING = "## Unknown marker"
FENCED_BLOCK = re.compile(r"```\n(.+?)\n```", re.DOTALL)

PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


def _plugin_root_citation(path: Path) -> str:
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


ARTIFACT_FAMILY_CITATION = _plugin_root_citation(ARTIFACT_FAMILY)

PRESS_RELEASE_PARTS = (
    "Heading",
    "Subheading",
    "Summary paragraph",
    "Problem paragraph",
    "Solution paragraphs",
    "Spokesperson quote",
    "Customer quote",
    "Getting started",
)

RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

RED_FLAG_CLUSTER_COUNT = 4

SEVERITY_HINT = "Severity hint:"

RUNTIME_RULES = (
    (
        "the slug folder is created by the substrate script and never locally",
        "--ensure-folder",
    ),
    (
        "the research sweep names the agent it launches",
        "deep-plan:dp-research-shallow",
    ),
    (
        "a second run replaces the member rather than refusing or merging into it",
        "replaces brief.md",
    ),
    (
        "brief.md heads the chain and so records no upstream",
        "carries no provenance line",
    ),
)

UNKNOWN_MARKER_RULE = "an unestablished slot takes the unknown marker"

CITED_REFERENCES = (
    ("the brief's shape is read from the template, not recalled", PR_FAQ_TEMPLATE),
    ("the judgement rules are read from the rubric, not recalled", PRODUCT_BRIEF_PRINCIPLES),
)

FORBIDDEN_FRONTMATTER_KEYS = (
    (
        "disable-model-invocation",
        "it is the documented way to drop a skill from the model-facing listing, "
        "leaving it reachable only by someone who types its name -- and this skill "
        "is meant to be reached from a raw product idea a user describes",
    ),
    (
        "allowed-tools",
        "an allowlist strips the ambient tools the body's own steps call: the folder "
        "script, the background research agent and the interview would each fail on a "
        "tool the frontmatter had narrowed away",
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


def _brief_section_names(substrate: str) -> list[str]:
    bullet = BRIEF_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _unknown_marker_literal(substrate: str) -> str:
    after_heading = substrate[substrate.index(UNKNOWN_MARKER_HEADING) :]
    block = FENCED_BLOCK.search(after_heading)
    return "" if block is None else block.group(1).strip()


def _unknown_marker_prefix(substrate: str) -> str:
    literal = _unknown_marker_literal(substrate)
    return literal.split(":", 1)[0] + ":" if literal else ""


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


def test_pr_faq_template_keeps_the_two_faqs_separate() -> None:
    assert PR_FAQ_TEMPLATE.exists(), f"missing shipped template: {PR_FAQ_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = PR_FAQ_TEMPLATE.read_text()

    required_sections = _brief_section_names(substrate)
    assert len(required_sections) >= 3, (
        f"could not read brief.md's required H2 names out of {ARTIFACT_FAMILY.name}; "
        f"{BRIEF_SECTION_BULLET.pattern!r} yielded {required_sections}, so the "
        f"template's drift check has nothing to compare against"
    )

    headings = _headings(template)
    h2 = _at_level(headings, 2)
    h2_names = [text for text, _ in h2]
    h2_line = dict(h2)

    for name in required_sections:
        assert name in h2_names, (
            f"pr-faq-template.md is missing the H2 section '## {name}'; "
            f"{ARTIFACT_FAMILY.name} requires it of brief.md, and the template "
            f"has {h2_names}"
        )

    ordered = [h2_line[name] for name in required_sections]
    assert ordered == sorted(ordered), (
        f"pr-faq-template.md must carry brief.md's sections in the order "
        f"{ARTIFACT_FAMILY.name} publishes {required_sections}; found them at "
        f"lines {ordered}"
    )

    for name in [n for n in required_sections if n.endswith("FAQ")]:
        occurrences = h2_names.count(name)
        assert occurrences == 1, (
            f"expected '## {name}' to appear exactly once as an H2 in "
            f"pr-faq-template.md, found {occurrences}; the external and internal "
            f"FAQs address different audiences and stay separate top-level sections"
        )

    press_release, next_section = required_sections[0], required_sections[1]
    press_release_line, next_section_line = h2_line[press_release], h2_line[next_section]
    h3_line = dict(_at_level(headings, 3))
    for part in PRESS_RELEASE_PARTS:
        assert part in h3_line, (
            f"pr-faq-template.md is missing the press-release part '### {part}'; "
            f"its H3 headings are {sorted(h3_line)}"
        )
        assert press_release_line < h3_line[part] < next_section_line, (
            f"press-release part '### {part}' sits at line {h3_line[part]}, outside "
            f"'## {press_release}' (line {press_release_line}) and the section that "
            f"follows it, '## {next_section}' (line {next_section_line}); the eight "
            f"parts nest under the press release"
        )

    marker_prefix = _unknown_marker_prefix(substrate)
    assert marker_prefix, (
        f"could not read the unknown-marker literal out of {ARTIFACT_FAMILY.name}; "
        f"expected a fenced block under {UNKNOWN_MARKER_HEADING!r}"
    )
    assert marker_prefix not in template, (
        f"pr-faq-template.md restates the unknown marker ({marker_prefix!r}); it must "
        f"cite {ARTIFACT_FAMILY_CITATION} for the token instead of carrying a "
        f"copy that can drift from the definition"
    )
    assert ARTIFACT_FAMILY_CITATION in template, (
        f"pr-faq-template.md must cite {ARTIFACT_FAMILY_CITATION} so a reader "
        f"filling an unestablished slot can reach the marker's definition"
    )


def test_principles_expose_four_red_flag_clusters() -> None:
    assert PRODUCT_BRIEF_PRINCIPLES.exists(), (
        f"missing shipped rubric: {PRODUCT_BRIEF_PRINCIPLES}"
    )

    principles = PRODUCT_BRIEF_PRINCIPLES.read_text()
    lines = principles.splitlines()
    headings = _headings(principles)

    h2 = _at_level(headings, 2)
    h2_names = [text for text, _ in h2]
    h2_line = dict(h2)
    for section in PRINCIPLES_SPINE:
        assert section in h2_names, (
            f"product-brief-principles.md is missing the H2 section '## {section}'; "
            f"it shares its heading spine with the plugin's other rubric files so "
            f"that an orchestrator can quote one section by name, and it has "
            f"{h2_names}"
        )

    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"product-brief-principles.md must carry its spine sections in the order "
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
        f"'## {RED_FLAGS_SECTION}' in product-brief-principles.md, found "
        f"{len(clusters)}: {cluster_names}; a review launches one finder per "
        f"cluster, so the count is part of what this file publishes"
    )

    cluster_ends = [line for _, line in clusters[1:]] + [section_end]
    for (name, start), stop in zip(clusters, cluster_ends, strict=True):
        body = _section_body(lines, (start, stop))
        assert any(line.rstrip().endswith("?") for line in body), (
            f"cluster '### {name}' of product-brief-principles.md carries no line "
            f"ending in a question mark; every cluster is a set of questions a "
            f"reviewer answers yes or no against a written brief, and prose "
            f"cannot be answered. The four clusters are {cluster_names}"
        )
        assert any(SEVERITY_HINT in line for line in body), (
            f"cluster '### {name}' of product-brief-principles.md carries no "
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
        f"{SKILL_MD.name} carries no `---` frontmatter block for its body to follow, so "
        f"the harness has no description to route on and the rules below would be "
        f"searched for in a file whose shape is already wrong"
    )
    assert not re.search(r"^description:", body, re.MULTILINE), (
        f"{SKILL_MD.name}'s frontmatter survived into what `_skill_body` returned as its "
        f"body, so this module and tests/guarantees.py no longer agree on where the "
        f"block ends. Every rule below would pass on a rule stated only in the "
        f"description, which is text the model routes on and never acts from"
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
            f"brief.md against this rule after the fact, so the body stating it is the "
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
