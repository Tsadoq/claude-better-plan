"""Contract tests over the files the product-discovery skill ships.

Pins the static shape of the shipped references -- what a standard-library
test can read off the markdown itself. Whether a generated discovery.md obeyed
the skill's run-time rules is not observable here and is enforced at review
time instead; SKILL.md publishes those rules and a later test pins that it does.

The section names discovery.md must carry are published by the product-artifacts
substrate, not by this skill, so they are read out of that contract at run time.
A hardcoded copy here would let the template and the contract drift apart with
both files' tests still green, which is the one failure the citation-over-copy
rule exists to prevent.

Runnable two ways:
    python3 skills/product-discovery/tests/test_product_discovery_contract.py
    python3 -m pytest skills/product-discovery/tests/test_product_discovery_contract.py
"""

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

# The repository root, reached by walking out of skills/<this skill>/, and used
# to build the citations a shipped document must spell a sibling file with, and
# to reach the repo-level frontmatter parser.
REPO_ROOT = SKILL_ROOT.parents[1]

# The substrate contract this skill's template must agree with, reached as a
# sibling skill rather than by a plugin-root walk: both skills ship in the same
# tree, so the relative hop is the shortest path that stays true if the plugin
# is installed under a different name.
ARTIFACT_FAMILY = (
    SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"
)

# The bullet in artifact-family.md's required-sections list that names
# discovery.md's H2 headings, and the pattern that lifts each backticked
# heading out of it.
#
# The bullet pattern takes its continuation lines too -- any indented,
# non-blank line following the first. The substrate hard-wraps its prose and
# lists at roughly 72 columns, so the day a fourth required section is added
# the name lands on a second physical line. A first-line-only read would drop
# it, and dropping it is invisible: the grouping table below would still match
# the three names that fitted, so the template would ship without a section
# the substrate had begun requiring, with every suite green.
DISCOVERY_SECTION_BULLET = re.compile(
    r"^- `discovery\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE
)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

UNKNOWN_MARKER_HEADING = "## Unknown marker"
FENCED_BLOCK = re.compile(r"```\n(.+?)\n```", re.DOTALL)

# The variable a shipped document must spell a sibling file's path with. It is
# what resolves at run time wherever the plugin is installed; a path relative to
# a checkout is a path only this checkout has.
PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


# Defined among the constants, against this module's constants-then-helpers
# layout, because the citation below is built from it rather than written out.
def _plugin_root_citation(path: Path) -> str:
    """How a shipped document must cite `path` for a reader to reach it.

    Built from the path constant rather than written as a literal, so a citation
    can never pass this module's checks while pointing at a file the repository
    does not ship at that location. Whether the file itself exists is asserted
    where that file's own contract is, once per file.
    """
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


# How the template must reach the section list and the marker definition: by
# ${CLAUDE_PLUGIN_ROOT} path, which is the form a skill body can resolve at run
# time.
ARTIFACT_FAMILY_CITATION = _plugin_root_citation(ARTIFACT_FAMILY)

# The section holding the tree's four node tables. Named once here because both
# the grouping table below and the table checks refer to it.
TREE_SECTION = "The tree"

# Where each of the five framework sections sits in discovery.md: as an H3
# under one of the three H2s the substrate publishes. The grouping is this
# skill's own decision -- the substrate pins the H2 names and their order and
# says nothing about what nests inside one -- so this table is that decision's
# definition rather than a copy of anything.
#
# It is keyed by the substrate's own names, and the test asserts the key set
# still matches what it reads there. Renaming a published section is then a
# re-grouping decision a person makes, not one this table absorbs in silence:
# an H3 grouped by what its parent heading means cannot be re-parented by
# position without someone deciding the new heading still means that.
NESTED_SECTIONS = {
    "Signals": (TREE_SECTION, "Market sizing"),
    "Constraints": ("Assumption mapping",),
    "Open questions": ("Riskiest assumption tests", "JTBD switch-interview structure"),
}

# The header cells a node table declares besides its id.
PARENT_COLUMN = "Parent"
EVIDENCE_COLUMN = "Evidence"

# How the rules write the number part of an id, and therefore what separates a
# stated id form from the prefix its rows actually carry.
ID_NUMBER_PLACEHOLDER = "<n>"

# The heading spine the plugin's rubric files share, and the one of them whose H3
# children a review fleet quotes. Unlike discovery.md's section names, which the
# substrate publishes and this module reads back, the spine is published nowhere
# -- it is the shape an orchestrator expects of a rubric -- so this tuple states
# it rather than reading it off anything.
#
# `test_product_brief_contract.py` states the same three constants for its own
# rubric, and a third rubric skill would state them again. That is the copy this
# module accepts knowingly: there is no published spine to read, so every rubric
# test asserts its own file against its own statement of the shape. The honest
# fix is one shared harness under the repo-level `tests/`, which is where the
# duplicated heading helpers above are already headed; until it exists, a spine
# change means editing every rubric skill's test, not just this one.
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

# One cluster per documented discovery failure mode, and the number of finders a
# review launches over a discovery.md. The count is part of the file's interface,
# not a stylistic preference: a fifth cluster changes what the reviewing skill
# does.
RED_FLAG_CLUSTER_COUNT = 4

# What every bullet in a cluster carries besides its question. A reviewer routes
# a finding by this word, so a cluster written without one produces findings
# nobody can triage -- which is why it is pinned here and not left to style.
SEVERITY_HINT = "Severity hint:"


class NodeLayer(NamedTuple):
    """One layer of the tree, and what its own table must declare.

    `id_column` is the header cell that identifies the layer's table, so that a
    check can find the right table among four without depending on their order
    in the section. `id_form` is the id shape the rules state for the layer.
    """

    id_column: str
    id_form: str
    names_a_parent: bool
    carries_evidence: bool

    @property
    def id_prefix(self) -> str:
        """The prefix an id of this layer starts with, before its number.

        Derived from the form the rules state rather than carried as a second
        field, so that a row cannot declare one notation for the prose and
        another for the ids the tables are checked against.
        """
        return self.id_form.removesuffix(ID_NUMBER_PLACEHOLDER)


# The four layers, outcome first. Per-layer tables rather than one flat table
# are what let `Evidence` be mandatory on opportunities and absent everywhere
# else, so the two flags are the point of the notation and not incidental: a
# uniform column set would make a blank evidence cell and an author's guess
# look alike on three layers out of four, which is the confusion the field
# exists to prevent.
#
# The id form is pinned because the layer prefix is what makes a solution
# parented to the outcome wrong on sight, in the parent cell, with nothing to
# cross-reference. Prose explaining that does not survive a later author who
# finds the prefixes noisy and collapses them into one sequence; this row does.
NODE_LAYERS = (
    NodeLayer("Outcome id", "OUT<n>", names_a_parent=False, carries_evidence=False),
    NodeLayer("Opportunity id", "OPP<n>", names_a_parent=True, carries_evidence=True),
    NodeLayer("Solution id", "SOL<n>", names_a_parent=True, carries_evidence=False),
    NodeLayer("Assumption test id", "AT<n>", names_a_parent=True, carries_evidence=False),
)


# The run-time rules SKILL.md publishes, one row per rule. Each names something
# no later reader can check off a written discovery.md: it does not record which
# script answered whether its upstream was there, whether a sizing sweep was
# launched, or what the previous run held. Publishing the rule in the body is the
# whole of its enforcement, and these rows pin only that it was published.
#
# Each row carries a fixed literal rather than a set of words to co-occur,
# because a body that mentions freshness and research somewhere near each other
# has told the acting model nothing it can follow. The trade is that rewording a
# rule is a test change, and it is why the table is short: rules a reviewer can
# already answer against a finished discovery.md -- that an assumption could be
# refuted, that the test order fell out of the mapping -- are questions in
# product-discovery-principles.md instead, and pinning their wording here as well
# would freeze prose twice over for one rule.
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

# The sixth rule, whose literal is not this file's to state: the marker token is
# defined once in the substrate and read back from it, the same way
# `test_tree_template_nests_the_five_sections_under_the_published_headings` reads
# it. Only the rule's name is fixed here, and the row is assembled where the
# substrate is read.
#
# Note which direction each file is checked in. The template must *not* restate
# the marker, because a template is copied from; the body must name it, because a
# body is acted on and a slot nobody filled is the failure the token exists for.
UNKNOWN_MARKER_RULE = "an unestablished slot takes the unknown marker"

# Two more rules of the same kind, about what the body reads rather than what it
# writes. A body that names its references cannot be caught working from a
# remembered version of one, and nothing downstream can tell the difference
# either, so the citation being present is again the whole enforcement.
CITED_REFERENCES = (
    ("the document's shape is read from the template, not recalled", OST_TEMPLATE),
    ("the judgement rules are read from the rubric, not recalled", DISCOVERY_PRINCIPLES),
)

# The frontmatter keys this skill must not declare, each with what declaring it
# would take away. Neither is about the rules the body states; both are about
# whether a session ever gets to follow them.
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
    """Every ATX heading in `markdown` as (level, text, line number).

    Lines inside a fenced code block are skipped: a reference file that shows
    a heading as an example would otherwise report that example as one of its
    own sections, which is the difference between reading a document's shape
    and reading the shape it is describing.

    Whole-line matching is what separates a heading from one demoted a level:
    `## Signals` is a substring of `### Signals`, so a substring search would
    report a top-level section in a document that had demoted it under some
    other parent -- the exact corruption these tests exist to catch.
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
    call site as a missing subheading or a missing table row.

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


def _discovery_section_names(substrate: str) -> list[str]:
    """discovery.md's required H2 names, in document order, read from the substrate.

    Returns the bare names without their `## ` marker, since callers compare
    them against parsed heading text rather than against raw lines, and an
    empty list when the bullet has moved out from under the pattern -- which
    callers must guard, since every comparison against it would then be
    vacuous rather than failing.
    """
    bullet = DISCOVERY_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _unknown_marker_prefix(substrate: str) -> str:
    """The marker token up to and including its colon, read from the substrate.

    Read rather than restated for the same reason the template must cite it: a
    second copy of the token in this file would keep passing after the
    definition moved on, and the assertion it guards would quietly test a
    literal nobody writes any more.

    The prefix rather than the whole literal is what a document carrying the
    marker actually shows, since the payload after the colon is written per
    slot. It is also what catches a partial restatement: a file carrying the
    token's opening and its own payload text has forked the token however
    little of it was copied.

    Returns "" when the definition cannot be read, which callers must guard --
    a prefix derived from nothing would be a bare colon, and every document
    contains one.

    "Cannot be read" covers a literal with no colon in it, and not only a
    missing fenced block. That the token ends at a colon is this function's own
    reading of the marker, not something the substrate states, so the day the
    marker takes another delimiter this returns "" and the caller's guard fires.
    Splitting regardless would hand back the whole literal with a colon stuck on
    the end -- a string no document will ever contain, which would turn the
    caller's "the template does not restate the marker" check into one that
    passes on a template restating it in full.
    """
    after_heading = substrate[substrate.index(UNKNOWN_MARKER_HEADING) :]
    block = FENCED_BLOCK.search(after_heading)
    if block is None:
        return ""
    token, separator, _payload = block.group(1).strip().partition(":")
    return token + separator if separator else ""


def _table_cells(row: str) -> list[str]:
    """The cells of one markdown table row, unpadded and with backticks dropped.

    Dropping backticks makes code-spanning a column name a formatting choice
    rather than a renamed column.
    """
    return [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]


def _node_table(body: list[str], id_column: str) -> list[list[str]]:
    """The rows of the table in `body` whose first header cell is `id_column`.

    One cell list per row, the header first, with the `|---|` alignment row
    dropped. Returns an empty list when no table in `body` opens on that cell.

    Finding a table by its leading header cell is what lets the four node
    tables be checked independently of the order the section stacks them in,
    and it is why each layer's id column is named for its layer: a section of
    four tables all opening on a bare `Id` would be four tables no check could
    tell apart.

    Header and body rows come back together because the two questions asked of a
    node table cannot be separated. Which columns it declares is answered by the
    header; whether the ids beneath them carry their layer's prefix is answered
    only by the rows. A helper returning the header alone would leave the second
    question to be answered against the section's prose, where the rules
    describing the notation sit -- and a document can describe a notation it
    does not use.
    """
    rows: list[list[str]] = []
    for line in body:
        if not line.lstrip().startswith("|"):
            # A non-table line before the table is one of the section's own
            # paragraphs; after it, it is where the table stopped.
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
    """SKILL.md without its frontmatter block, or "" if it has no such block.

    The complement of what `guarantees.frontmatter_value` reads, split on the
    same two markers: a leading `---` and the next line-initial `---`. The split
    is what makes a rule check mean something. Both halves reach the model, but
    at different moments and under different budgets -- the description is what
    the router weighs before the skill is chosen and is rationed in characters,
    while the body is what the model has in front of it while acting -- so a rule
    that appears only in the description is a rule the acting model never reads.

    Returns "" rather than the whole text on a malformed block, so a caller that
    guards the empty case fails loudly instead of quietly finding its literals in
    frontmatter that is not frontmatter.
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
    would be silent in the permissive direction: this test would report the skill
    as listed after the listing had already dropped it.

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


def test_tree_template_nests_the_five_sections_under_the_published_headings() -> None:
    assert OST_TEMPLATE.exists(), f"missing shipped template: {OST_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = OST_TEMPLATE.read_text()

    # The grouping table is keyed by the substrate's names, so this is also the
    # guard on the read itself: a bullet that moved out from under the pattern
    # yields an empty list, and every nesting check below would then pass by
    # having nothing to look for rather than by agreeing with anything.
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

    # Document order is part of the published schema: a template that emits the
    # sections in another sequence shapes a different document.
    h2_line = dict(h2)
    ordered = [h2_line[name] for name in required_sections]
    assert ordered == sorted(ordered), (
        f"{OST_TEMPLATE.name} must carry discovery.md's sections in the order "
        f"{ARTIFACT_FAMILY.name} publishes {required_sections}; found them at "
        f"lines {ordered}"
    )

    # The five framework sections are subsections, not siblings. Bounding each
    # by the H2 that follows its parent proves the nesting rather than merely
    # proving the five names appear somewhere in the file -- and it is what
    # distinguishes a tree filed under Signals from a tree appended at the end.
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

    # Every node lives in one section, which is what makes the connection rules
    # checkable at all: "this solution's parent is the outcome" is a claim a
    # reader assembles from two places the moment the layers are split up.
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

        # The rules stating the notation and the tables using it are two
        # different properties, and only the second one is the property. A
        # template whose rules paragraph still described `SOL<n>` while every
        # table had been collapsed onto one unprefixed sequence would satisfy
        # the check above and ship exactly the document that check exists to
        # prevent, so the ids are read out of the rows as well.
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

    # One definition, cited everywhere else. The template restating the token
    # would be a second copy free to drift; citing the path that defines it
    # cannot drift, because there is nothing local to change.
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

    # Exactly once, not merely present, for the reason `_at_level` returns a list
    # in the first place: an orchestrator quoting a section by name gets one of
    # them, and a rubric carrying the same heading twice has split a section
    # nobody can quote whole. It is also what makes the mapping below safe, since
    # collapsing to a mapping keeps only the last occurrence of a repeated name.
    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{DISCOVERY_PRINCIPLES.name}, found {occurrences}; it shares its heading "
            f"spine with the plugin's other rubric files so that an orchestrator can "
            f"quote one section by name, and it has {h2_names}"
        )

    h2_line = dict(h2)

    # The spine's order is part of it. These files are read top to bottom by a
    # maintainer and quoted section by section by an orchestrator, and the
    # sequence is the reading path: who wrote this and what it covers, then how
    # to author, then how to review, then how to change the file itself. A rubric
    # that resequences them is a different document wearing the same headings.
    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"{DISCOVERY_PRINCIPLES.name} must carry its spine sections in the order "
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
        f"'## {RED_FLAGS_SECTION}' in {DISCOVERY_PRINCIPLES.name}, found {len(clusters)}: "
        f"{cluster_names}; a review launches one finder per cluster, so the count "
        f"is part of what this file publishes"
    )

    # Each cluster stops where the next one begins, and the last stops where the
    # red-flag section does.
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
    # `_skill_body` finds the frontmatter boundary itself, because guarantees.py
    # exposes the keys inside the block and not the remainder. That makes it a
    # second reader of one boundary, so the two are pinned to each other here
    # rather than trusted to stay in step: were this split to stop consuming the
    # block, the description would still be sitting in what the rules below call
    # the body, and every one of them could be satisfied by frontmatter.
    assert not re.search(r"^description:", body, re.MULTILINE), (
        f"{SKILL_MD.name}'s frontmatter survived into what `_skill_body` returned as its "
        f"body, so this module and tests/guarantees.py no longer agree on where the block "
        f"ends. Every rule below would pass on a rule stated only in the description, which "
        f"is text the model routes on and never acts from"
    )

    # Backticks are dropped before matching so that code-spanning a rule's nouns
    # is a formatting choice rather than a deleted rule. The words and their order
    # still have to be exactly right, which is what the row asserts.
    published = body.replace("`", "")

    marker_prefix = _unknown_marker_prefix(ARTIFACT_FAMILY.read_text())
    assert marker_prefix, (
        f"could not read the unknown-marker literal out of {ARTIFACT_FAMILY.name}; "
        f"expected a fenced block under {UNKNOWN_MARKER_HEADING!r}"
    )

    # The table is completed here rather than at module level because three of its
    # rows are not this file's to state: the marker token belongs to the substrate,
    # and a reference's citation is derived from the path constant that locates it,
    # so neither can drift from its definition into a stale literal that keeps
    # passing. The five fixed rows are SKILL.md's own wording.
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
    # scalars, and this test would report a reachable skill after the harness had
    # already dropped it.
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
