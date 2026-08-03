"""Contract tests over the files the product-brief skill ships.

Pins the static shape of the shipped references -- what a standard-library
test can read off the markdown itself. Whether a generated brief.md obeyed the
skill's run-time rules is not observable here and is enforced at review time
instead; SKILL.md publishes those rules and a later test pins that it does.

The section names brief.md must carry are published by the product-artifacts
substrate, not by this skill, so they are read out of that contract at run
time. A hardcoded copy here would let the template and the contract drift
apart with both files' tests still green, which is the one failure the
citation-over-copy rule exists to prevent.

Runnable two ways:
    python3 skills/product-brief/tests/test_product_brief_contract.py
    python3 -m pytest skills/product-brief/tests/test_product_brief_contract.py
"""

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

# The repository root, reached by walking out of skills/<this skill>/, and used
# only to load the repo-level frontmatter parser below.
REPO_ROOT = SKILL_ROOT.parents[1]

# The substrate contract this skill's template must agree with, reached as a
# sibling skill rather than by a plugin-root walk: both skills ship in the same
# tree, so the relative hop is the shortest path that stays true if the plugin
# is installed under a different name.
ARTIFACT_FAMILY = (
    SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"
)

# The bullet in artifact-family.md's required-sections list that names brief.md's
# H2 headings, and the pattern that lifts each backticked heading out of it.
BRIEF_SECTION_BULLET = re.compile(r"^- `brief\.md`:(.*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

UNKNOWN_MARKER_HEADING = "## Unknown marker"
FENCED_BLOCK = re.compile(r"```\n(.+?)\n```", re.DOTALL)

# The variable a shipped document must spell a sibling file's path with. It is
# what resolves at run time wherever the plugin is installed; a path relative to
# a checkout is a path only this checkout has.
PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


# Defined among the constants, against this module's constants-then-helpers
# layout, because the citations below are built from it rather than written out.
def _plugin_root_citation(path: Path) -> str:
    """How a shipped document must cite `path` for a reader to reach it.

    Built from the path constant rather than written as a literal, so a citation
    can never pass this module's checks while pointing at a file the repository
    does not ship at that location. Whether the file itself exists is asserted
    where that file's own contract is, once per file.
    """
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


# How the template must reach the marker definition: by ${CLAUDE_PLUGIN_ROOT}
# path, which is the form a skill body can resolve at run time.
ARTIFACT_FAMILY_CITATION = _plugin_root_citation(ARTIFACT_FAMILY)

# The press release's parts, in the order the Working Backwards resource lists
# them. Unlike the H2 section names these are the template's own vocabulary --
# the substrate pins a member's sections and says nothing about what goes
# inside one -- so this tuple is their definition, not a copy of one.
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

# The heading spine the plugin's rubric files share, and the one of them whose
# H3 children a review fleet quotes. Unlike brief.md's section names, which the
# substrate publishes and this module reads back, the spine is published
# nowhere: it is the shape an orchestrator expects of a rubric, so this tuple is
# its definition rather than a copy of one.
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

# One cluster per documented PR-FAQ failure mode, and the number of finders a
# review launches over a brief. The count is part of the file's interface, not a
# stylistic preference: a fifth cluster changes what the reviewing skill does.
RED_FLAG_CLUSTER_COUNT = 4

# What every bullet in a cluster carries besides its question. A reviewer routes
# a finding by this word, so a cluster written without one produces findings
# nobody can triage -- which is why it is pinned here and not left to style.
SEVERITY_HINT = "Severity hint:"

# The run-time rules SKILL.md publishes, one row per rule. Each names something
# no later reader can check: a written brief.md does not record which folder
# call created it, whether a sweep was launched, or what the previous run held.
# Publishing the rule in the body is the whole of its enforcement, and these
# rows pin only that it was published.
#
# Each row carries a fixed literal rather than a set of words to co-occur,
# because a body that mentions folders and research somewhere near each other
# has told the acting model nothing it can follow. The trade is that rewording
# a rule is a test change, and it is why the table is short: rules a reviewer
# can already catch in a finished brief -- that a researched figure carries its
# citation, that a quote reads as authored -- are questions in
# product-brief-principles.md instead, and pinning their wording here as well
# would freeze prose twice over for one rule.
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

# The fifth rule, whose literal is not this file's to state: the marker token is
# defined once in the substrate and read back from it, the same way
# `test_pr_faq_template_keeps_the_two_faqs_separate` reads it. Only the rule's
# name is fixed here, and the row is assembled where the substrate is read.
UNKNOWN_MARKER_RULE = "an unestablished slot takes the unknown marker"

# Two more rules of the same kind, about what the body reads rather than what it
# writes. A body that names its references cannot be caught working from a
# remembered version of one, and nothing downstream can tell the difference
# either, so the citation being present is again the whole enforcement.
CITED_REFERENCES = (
    ("the brief's shape is read from the template, not recalled", PR_FAQ_TEMPLATE),
    ("the judgement rules are read from the rubric, not recalled", PRODUCT_BRIEF_PRINCIPLES),
)

# The frontmatter keys this skill must not declare, each with what declaring it
# would take away. Neither is about the rules the body states; both are about
# whether a session ever gets to follow them.
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
    """Every ATX heading in `markdown` as (level, text, line number).

    Lines inside a fenced code block are skipped: a reference file that shows
    a heading as an example would otherwise report that example as one of its
    own sections, which is the difference between reading a document's shape
    and reading the shape it is describing.

    Whole-line matching is what separates a heading from one demoted a level:
    `## External FAQ` is a substring of `### External FAQ`, so a substring
    search would report a top-level FAQ section in a document that had folded
    both FAQs under one merged parent -- the exact corruption these tests
    exist to catch.
    """
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
    """The (text, line number) of each heading at `level`, in document order.

    A list rather than a mapping, because a heading that appears twice is
    itself something these tests report; collapsing to a mapping first would
    hide the repetition that proves two sections were merged or copied.
    """
    return [(text, lineno) for depth, text, lineno in headings if depth == level]


def _section_span(
    headings: list[tuple[int, str, int]], level: int, name: str, last_line: int
) -> tuple[int, int]:
    """Where one section starts and stops owning the document, as line numbers.

    Every line number here is 1-based, matching what `_headings` reports and what
    an editor shows; `last_line` is the document's own final line on that same
    scale. Converting a span to a list index is `_section_body`'s job, so that
    the base is stated once and compensated for once.

    Returns the section heading's own line and the line of the next heading at
    the same or a higher level -- the point where the section stops -- or
    `last_line + 1` when nothing follows it. The body is the lines strictly
    between the two.

    Bounding by the successor heading rather than by the end of the file is what
    lets a caller ask whether a subheading sits *inside* a section; measuring to
    the end instead would count every later subheading in the document as one of
    this section's own.

    Spans the first heading of that level and name. A document carrying the
    section twice reports only the first one's contents, which surfaces at the
    call site as a subheading count that does not match -- the same way a
    document that split its subheadings across two copies would.

    Returns an empty span when no such heading exists, so a caller that has not
    already asserted the heading's presence sees an empty section rather than an
    exception.
    """
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
    """The lines a section contains, given the span that bounds it.

    `_section_span` speaks in 1-based line numbers naming two headings, which is
    the currency a caller needs to ask whether something *nests* inside a
    section. Asking what a section *says* is the commoner question, and this
    turns one into the other so that no caller re-derives the conversion:
    `lines[start]` is the line after the opening heading, and `lines[stop - 2]`
    is the line before the heading that ends the section.

    Takes the span as the pair `_section_span` returns rather than as two loose
    integers, so a caller cannot pair the start of one section with the end of
    another.
    """
    start, stop = span
    return lines[start : stop - 1]


def _brief_section_names(substrate: str) -> list[str]:
    """brief.md's required H2 names, in document order, read from the substrate.

    Returns the bare names without their `## ` marker, since callers compare
    them against parsed heading text rather than against raw lines, and an
    empty list when the bullet has moved out from under the pattern -- which
    callers must guard, since every comparison against it would then be
    vacuous rather than failing.
    """
    bullet = BRIEF_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _unknown_marker_literal(substrate: str) -> str:
    """The unknown-marker token, read from the substrate's fenced definition.

    Read rather than restated for the same reason the template must cite it:
    a second copy of the token in this file would keep passing after the
    definition moved on, and the assertion it guards would quietly test a
    literal nobody writes any more. Returns an empty string when no fenced
    block follows the heading, which callers must guard for the same reason.
    """
    after_heading = substrate[substrate.index(UNKNOWN_MARKER_HEADING) :]
    block = FENCED_BLOCK.search(after_heading)
    return "" if block is None else block.group(1).strip()


def _unknown_marker_prefix(substrate: str) -> str:
    """The marker token up to and including its colon, read from the substrate.

    The prefix rather than the whole literal is what a document carrying the
    marker actually shows, since the payload after the colon is written per
    slot. It is also what catches a partial restatement: a file carrying the
    token's opening and its own payload text has forked the token however
    little of it was copied.

    Returns "" when the definition cannot be read, which callers must guard for
    the same reason `_unknown_marker_literal` gives -- a prefix derived from
    nothing would be a bare colon, and every document contains one.
    """
    literal = _unknown_marker_literal(substrate)
    return literal.split(":", 1)[0] + ":" if literal else ""


def _skill_body(text: str) -> str:
    """SKILL.md without its frontmatter block, or "" if it has no such block.

    The complement of what `guarantees.frontmatter_value` reads, split on the
    same two markers: a leading `---` and the next line-initial `---`. The
    split is what makes a rule check mean something. Both halves reach the
    model, but at different moments and under different budgets -- the
    description is what the router weighs before the skill is chosen and is
    rationed in characters, while the body is what the model has in front of it
    while acting -- so a rule that appears only in the description is a rule the
    acting model never reads.

    Returns "" rather than the whole text on a malformed block, so a caller that
    guards the empty case fails loudly instead of quietly finding its literals
    in frontmatter that is not frontmatter.
    """
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return "" if end == -1 else text[end + len("\n---") :]


def _guarantees() -> ModuleType:
    """Load the repo-level tests/guarantees.py by path, for its frontmatter parser.

    This repository has one definition of what a top-level frontmatter key is,
    and the harness's listing rule -- which keys off exactly the key asserted
    below -- is written against it. A second parser here would eventually
    disagree with that one about which keys a file declares, and the failure
    would be silent in the permissive direction: this test would report the
    skill as listed after the listing had already dropped it.

    Loaded inside the test rather than at import, so this module still runs as a
    standalone script where the repo-level tests/ directory is absent; only the
    one test that needs it fails.
    """
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
    # Three is the fewest names the checks below can be run on at all: they
    # need a first section and a successor to bound the press-release parts,
    # and two FAQs to compare against each other. A shorter list means the
    # bullet moved out from under the pattern, and every assertion after this
    # one would pass by having nothing to compare rather than by agreeing.
    assert len(required_sections) >= 3, (
        f"could not read brief.md's required H2 names out of {ARTIFACT_FAMILY.name}; "
        f"{BRIEF_SECTION_BULLET.pattern!r} yielded {required_sections}, so the "
        f"template's drift check has nothing to compare against"
    )

    headings = _headings(template)
    h2 = _at_level(headings, 2)
    h2_names = [text for text, _ in h2]
    # Mapping a repeated heading to its last line is harmless here: the only
    # repetition that would change a verdict is a duplicated FAQ section, and
    # the count check below reports that rather than resolving it.
    h2_line = dict(h2)

    for name in required_sections:
        assert name in h2_names, (
            f"pr-faq-template.md is missing the H2 section '## {name}'; "
            f"{ARTIFACT_FAMILY.name} requires it of brief.md, and the template "
            f"has {h2_names}"
        )

    # Document order is part of the published schema: a template that emits the
    # sections in another sequence shapes a different document.
    ordered = [h2_line[name] for name in required_sections]
    assert ordered == sorted(ordered), (
        f"pr-faq-template.md must carry brief.md's sections in the order "
        f"{ARTIFACT_FAMILY.name} publishes {required_sections}; found them at "
        f"lines {ordered}"
    )

    # The two audience-specific FAQs are the format's defining feature: the
    # external one answers a customer, the internal one a stakeholder. Either
    # merging them into one section or demoting them under a shared parent
    # loses that split, and both show up here as a count other than one.
    for name in [n for n in required_sections if n.endswith("FAQ")]:
        occurrences = h2_names.count(name)
        assert occurrences == 1, (
            f"expected '## {name}' to appear exactly once as an H2 in "
            f"pr-faq-template.md, found {occurrences}; the external and internal "
            f"FAQs address different audiences and stay separate top-level sections"
        )

    # The press release's parts are subsections of it, not siblings. Bounding
    # them by the section that follows proves the nesting rather than merely
    # proving the eight names appear somewhere in the file.
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

    # One definition, cited everywhere else. The template restating the token
    # would be a second copy free to drift; citing the path that defines it
    # cannot drift, because there is nothing local to change.
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

    # The spine's order is part of it. These files are read top to bottom by a
    # maintainer and quoted section by section by an orchestrator, and the
    # sequence is the reading path: who wrote this and what it covers, then how
    # to author, then how to review, then how to change the file itself. A rubric
    # that resequences them is a different document wearing the same headings.
    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"product-brief-principles.md must carry its spine sections in the order "
        f"{list(PRINCIPLES_SPINE)}, the order its sibling rubric files use; found "
        f"them at lines {spine_lines}"
    )

    # A cluster is what nests under the red-flag section, not merely what appears
    # somewhere later in the file. Bounding the search proves the nesting: an H3
    # past the section's end is one no reviewer would ever be handed.
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

    # Each cluster stops where the next one begins, and the last stops where the
    # red-flag section does.
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
    # `_skill_body` finds the frontmatter boundary itself, because guarantees.py
    # exposes the keys inside the block and not the remainder. That makes it a
    # second reader of one boundary, so the two are pinned to each other here
    # rather than trusted to stay in step: were this split to stop consuming the
    # block, the description would still be sitting in what the rules below call
    # the body, and every one of them could be satisfied by frontmatter.
    assert not re.search(r"^description:", body, re.MULTILINE), (
        f"{SKILL_MD.name}'s frontmatter survived into what `_skill_body` returned as its "
        f"body, so this module and tests/guarantees.py no longer agree on where the "
        f"block ends. Every rule below would pass on a rule stated only in the "
        f"description, which is text the model routes on and never acts from"
    )

    # Backticks are dropped before matching so that code-spanning a rule's nouns
    # is a formatting choice rather than a deleted rule. The words and their
    # order still have to be exactly right, which is what the row asserts.
    published = body.replace("`", "")

    marker_prefix = _unknown_marker_prefix(ARTIFACT_FAMILY.read_text())
    assert marker_prefix, (
        f"could not read the unknown-marker literal out of {ARTIFACT_FAMILY.name}; "
        f"expected a fenced block under {UNKNOWN_MARKER_HEADING!r}"
    )

    # The table is completed here rather than at module level because two of its
    # rows are not this file's to state: the marker token belongs to the
    # substrate, and a reference's citation is derived from the path constant
    # that locates it, so neither can drift from its definition into a stale
    # literal that keeps passing. The four fixed rows are SKILL.md's own wording.
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
    """Neither key that would keep a session from following the rules above.

    Separate from the rules themselves, which fail for an unrelated reason: one
    test answers whether the body states a rule, this one whether anything gets
    to act on it. Bundling them would report a stripped tool allowlist under a
    name about unpublished prose.
    """
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    # Read through guarantees.py rather than matched here, so that "declares a
    # key" means the same thing to this test as to the listing rule that acts on
    # one. A second parser would eventually disagree with it about folded
    # scalars, and this test would report a reachable skill after the harness
    # had already dropped it.
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
