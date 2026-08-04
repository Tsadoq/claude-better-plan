"""Contract tests over the files the product-roadmap skill ships.

Pins the static shape of the shipped references -- what a standard-library test
can read off the markdown itself. Whether a written `roadmap.md` obeyed this
beat's run-time rules is not observable here: a finished roadmap records what
the rules produced and never which of them were followed, since a score somebody
reasoned to and a score somebody worked backwards from leave the same table
behind. That is enforced two ways instead -- at review time by the critic fleet
`product-review` fans over this skill's rubric, and before that by `SKILL.md`
publishing each rule where a run will read it.
`test_skill_publishes_each_runtime_rule` pins that it does, which is the only
check available.

The first two tests below split on who owns what, and that split is what a
failure has to be read against. The substrate publishes `roadmap.md`'s section
names and their order, so `test_template_renders_the_substrate_section_schema` reads them
out of that contract at run time rather than copying them: a hardcoded copy would
let the template and the contract drift apart with both files' suites green,
which is the one failure the citation-over-copy rule exists to prevent. Which
three names the substrate *ought* to publish is a question
`test_artifact_family_pins_roadmap_sections` owns over in the substrate's own
suite, and this module never re-asks it -- it asks only whether the template
renders whatever the substrate publishes.

The two tables inside `## Scored items` are this beat's own decision and nothing
else pins them, so `test_template_declares_the_columns_its_tables_are_read_by`
does. Keeping them out of the first test is deliberate: a reader who saw one test
fail could not otherwise tell a substrate disagreement from a renamed column, and
the two land in different files' fix loops. A reader who takes the columns for
substrate rules will go looking for them in the wrong file entirely.

The last two tests leave the template and take up the rubric beside it, and they
split on the same principle as the first two: a launchable review and a honest
one fail for unrelated reasons and are fixed in different places.
`test_principles_expose_five_red_flag_clusters` owns the launch.
`product-review` fans one critic per H3 cluster under `## Review-time red
flags`, so that count is not a matter of taste -- it is how wide a review of a
written `roadmap.md` goes -- and a cluster emptied into prose is a finder
launched with nothing to answer. It pins the count at five, the H2 spine at four
names in order, and each bullet as a question with a severity hint beneath it.

`test_principles_attribution_stays_checkable` owns what the launched questions
rest on. Most of that rubric reaches past its sources and three of its five
clusters have no source at all, so the attribution is where a reviewer finds out
which questions carry borrowed authority and which do not. It pins the citation
tokens, the non-affiliation sentence, the `${CLAUDE_PLUGIN_ROOT}` redirects
attached to the rules the rubric refuses to restate, and the one token the
rubric may not spell. Its two derived expectations -- the redirects, built from
the paths the cited files occupy, and the marker token, read out of the
substrate -- are derived rather than written down for the reason the first test
reads the substrate's section names at run time: a copy is a place for two files
to disagree while both suites stay green.

The last two tests leave the shipped references altogether and read `SKILL.md`,
the file that publishes the run-time rules to the run itself. They split the way
the siblings' pair does, on what fails a run rather than on subject:
`test_skill_gates_on_the_refusal_triad` asks whether the gate deciding there is
an upstream at all is still there, and `test_skill_publishes_each_runtime_rule`
asks whether the run that got past it is told the rules it works under. A
missing gate and an unpublished rule are fixed in different paragraphs of a
different kind.

Inside those two, the rule tables split again on scope, and that is how a
failure is read: `RUNTIME_RULES` is swept over the whole body because a run may
obey those rules in any step, while `REFUSAL_STEP_RULES`, `STEP_OBLIGATIONS` and
`RERUN_RULES` are bounded to the section that owns them. Bounding is not
fussiness -- every token in those three is a word the body has honest reason to
use again elsewhere, so a whole-body search would go on passing after the step
itself had been deleted, which is the one way this module could report a
published gate that no longer exists.

Two blocks here are copied from the sibling contract modules, and both copies are
knowing ones. The first is `_headings`, which product-brief, product-discovery,
product-requirements and product-spec all already carry. The second is larger and
worth naming in full, because a reader who thinks only the helper was copied will
under-estimate what a substrate change costs: `ARTIFACT_FAMILY` and its
sibling-reach comment, `BACKTICKED_H2`, `ROADMAP_SECTION_BULLET` with its
continuation-line comment, and `_roadmap_section_names` are product-spec's
equivalents with one member name changed. That is one piece of design knowledge --
how the substrate formats the bullet list a member's sections are published in --
now living in four or five modules at once, so a change to that format is an edit
to all of them, and this module is not the place it will be noticed first. The
rubric constants below -- `PRINCIPLES_SPINE`, `CLUSTER_LEVEL`,
`RED_FLAG_CLUSTER_COUNT` and `SEVERITY_HINT` -- are a third knowing copy on the
same terms: the same four modules already restate them, no file publishes the
spine for a test to read, and changing it is a five-module edit.

The reason those siblings record for their own duplication holds here too: there
is no shared harness under the repo-level `tests/` for any of it to live in, and a
per-skill module that runs standalone is worth more than one that cannot. The
honest fix is that harness, and it grows more expensive with each module that
copies the block rather than less -- which is the argument for building it before
the next beat lands, not an argument that this copy was free.

`_section_body`, `_tables` and `_clusters` are this module's own. The
siblings' `_section_span` plus `_section_body` pair is not copied. A span is the
currency for asking whether something *nests* inside a section, and the only
question here that needs nesting is which H3s belong to the red-flags cluster
list -- which `_clusters` answers by being handed that section's body
instead of the whole file, so an H3 outside it is not in the input rather than
being excluded by an arithmetic comparison of line numbers. Every other caller
below asks only what a section says.

Five more helpers arrive with the `SKILL.md` checks, and four are further copies
on the same terms. `_plugin_root_citation`, `_frontmatter_and_body`,
`_frontmatter_keys` and `_prose` are product-spec's, and `_invocations` is too;
each belongs in the same absent harness as the blocks above, and this module now
carries the largest share of that debt. `_section_prose` is this module's own,
and exists because `_section_body` here returns lines while every caller of it
below wants normalised prose -- spelling that two-step chain at each of the three
call sites is how a fix to one of them silently misses the others.

`_tables` differs from the siblings' `_table` in the way this member needs -- it
returns every table in a body rather than the first, because `## Scored items`
carries two and checking only the first is exactly how the coverage table's own
header would go unpinned.

Runnable two ways:
    python3 skills/product-roadmap/tests/test_product_roadmap_contract.py
    python3 -m pytest skills/product-roadmap/tests/test_product_roadmap_contract.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"
RICE_TEMPLATE = REFERENCES / "rice-template.md"
ROADMAP_PRINCIPLES = REFERENCES / "product-roadmap-principles.md"

# The shipped skill body, and the script its invocations must stay inside the
# vocabulary of. Both are read off disk rather than described here: a flag the
# body passes is checked against the parser that would receive it, so a flag the
# substrate renames fails here instead of failing at run time in a user's session.
SKILL_MD = SKILL_ROOT / "SKILL.md"
SUBSTRATE_SCRIPT = SKILL_ROOT.parent / "product-artifacts" / "scripts" / "product_artifact.py"

# The substrate contract this skill's template must agree with, reached as a
# sibling skill rather than by a plugin-root walk: both skills ship in the same
# tree, so the relative hop is the shortest path that stays true if the plugin is
# installed under a different name.
ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"

# The bullet in artifact-family.md's required-sections list that names roadmap.md's
# H2 headings, and the pattern that lifts each backticked heading out of it.
#
# The bullet pattern takes its continuation lines too -- any indented, non-blank
# line following the first. The substrate hard-wraps its prose and lists at roughly
# 72 columns, so the day a fourth required section is added the name lands on a
# second physical line. A first-line-only read would drop it, and dropping it is
# invisible in the wrong direction: the template would still carry the three names
# that fitted and the equality below would fail against a truncated expectation,
# reporting a template that had drifted when what had actually happened is that
# this pattern stopped reading the whole bullet.
ROADMAP_SECTION_BULLET = re.compile(r"^- `roadmap\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

# The member section both tables sit in. This restates one of the substrate's
# published names, and the restatement is guarded rather than trusted: the test
# below asserts it is still a name the substrate publishes before reading a
# section by it. Without that guard, a renamed section would leave the table
# lookups spanning nothing and failing with "carries no table", which points at
# the template when the template is the one file that was right.
SCORED_ITEMS_SECTION = "Scored items"

# The columns of the table the whole member is built around, as an exact ordered
# tuple rather than a set of names to be found somewhere. A reader locates a cell
# by its header, so a renamed or reordered column breaks that reader while leaving
# the document looking perfectly well-formed -- and four of the nine are inputs to
# one formula, where an order nobody can rely on is an invitation to read the
# wrong number into it.
SCORE_TABLE_COLUMNS = (
    "ID",
    "Item",
    "Traces to",
    "Reach",
    "Impact",
    "Confidence",
    "Effort",
    "Score",
    "Appetite",
)

# The columns of the second table, which is the check on the first: one row per
# requirement the upstream put in scope, so a specified requirement that no item
# covers is visible rather than merely absent.
COVERAGE_TABLE_COLUMNS = ("Requirement", "Covered by")

# Both tables of `## Scored items`, in the order the section carries them, each
# with the label a failure names it by.
#
# Ordered rather than keyed by section, which is how the sibling modules do it,
# because both of these sit under one heading and a key would not tell them
# apart. The order is itself part of what is pinned: the scored table is the
# evidence and the coverage table is the check on it, so a member that led with
# the check would be arguing from a conclusion. Two three-and-nine-column tables
# are also not recognisable by shape alone, which is why position is what
# identifies them here.
DECLARED_TABLES = (
    ("the scored-items table", SCORE_TABLE_COLUMNS),
    ("the requirement-coverage table", COVERAGE_TABLE_COLUMNS),
)

# The literal a `Covered by` cell carries when no item covers a requirement, and
# this beat's own decision rather than the substrate's.
#
# Pinned because the alternative to it is a blank cell, and a blank cell means
# either that no item covers the requirement or that nobody filled the table in.
# Telling those two apart is the whole reason the second table exists, so a
# template that stops showing the literal has removed the only thing that
# distinguishes a checked roadmap from an unfinished one. Asserted inside the
# coverage table's own rows rather than anywhere in the section: an author copies
# what a cell shows, and the same words sitting in a paragraph nearby would
# satisfy a looser search while leaving the cell itself blank.
NOT_COVERED_LITERAL = "not covered"

# The rubric's H2 spine, in the order a maintainer reads it top to bottom: where
# the questions came from, how to author, how to review, how to change the file.
# `product-review` quotes one of these sections -- or one H3 cluster inside the
# third -- into an agent prompt, so a renamed section leaves a caller quoting
# nothing.
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

# The heading level a red-flag cluster sits at, and how many of them this rubric
# publishes. The count is the load-bearing number: `product-review` launches one
# finder per cluster, so five is the width of the fan-out rather than a matter of
# taste, and a sixth is a change to what a review costs and what goes unasked.
CLUSTER_LEVEL = 3
RED_FLAG_CLUSTER_COUNT = 5

# What a cluster carries besides its questions. Without it a critic returns
# findings with no severity to route them by, so the fleet is launched and its
# output cannot be triaged -- a failure that looks like a working review.
SEVERITY_HINT = "Severity hint:"

# The section whose claims nothing else in the repository checks, and the tokens
# that make each of its citations checkable by the next reader.
#
# Each token is the one thing research settled about its source, chosen so that a
# citation cannot keep the token while losing what was verified: `1.2-chapter-03`
# because appetite is defined in chapter 3 and the chapter first guessed at was
# wrong; `framework.scaledagile.com` because the older `scaledagileframework.com`
# URL now redirects; `agilebusiness.org` because that body owns DSDM and is the
# only first-party source for MoSCoW's categories; and the Kano paper's exact
# title because its bibliography, not its method, is what could be confirmed. The
# Intercom path is the post every input's unit comes from.
ATTRIBUTION_SECTION = "Attribution and scope"
ATTRIBUTION_CITATIONS = (
    "intercom.com/blog/rice-simple-prioritization-for-product-managers/",
    "basecamp.com/shapeup/1.2-chapter-03",
    "framework.scaledagile.com/wsjf/",
    "agilebusiness.org/dsdm-project-framework/moscow-prioritisation.html",
    "Attractive Quality and Must-Be Quality",
    "prodpad.com/blog/invented-now-next-later-roadmap/",
)

# The disclaimer every rubric in this suite carries. Six named third parties are
# cited for framings this file then extends, so the sentence saying none of them
# endorsed the extension is part of the attribution rather than boilerplate.
NON_AFFILIATION = "not affiliated"

REPO = SKILL_ROOT.parent.parent

# The variable a shipped document spells a plugin path with. It resolves wherever
# the plugin is installed, which a repository-relative path does not.
PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


# Defined among the constants, against this module's constants-then-helpers
# layout, because the mapping below is built from it rather than written out.
def _plugin_root_citation(path: Path) -> str:
    """How a shipped document must cite `path` for a reader to reach it.

    Built from the path constant rather than written as a literal, so a citation
    can never pass a check here while pointing at a file the repository does not
    ship at that location -- the failure a hand-typed expectation invites, since a
    reader following a citation to nowhere is worse served than one following none
    at all. Each caller separately asserts that the cited file exists, which is a
    check on what a reader follows rather than on the constant it was built from.
    """
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO).as_posix()}"


# The three files this rubric forbids itself from restating, each of which it
# must therefore point at. The expectation is built from the path a file actually
# occupies rather than written out, so a citation cannot pass while naming a file
# the plugin does not ship -- a ban whose redirect has rotted tells a reviewer a
# rule exists somewhere unnamed, which is worse than no ban at all.
CITED_REFERENCES = (
    RICE_TEMPLATE,
    ARTIFACT_FAMILY,
    SKILL_ROOT.parent / "product-spec" / "references" / "product-spec-principles.md",
)

# The three files `SKILL.md` sends a run to instead of restating them, and the
# form it must spell each one in.
#
# A different three from the rubric's above, and the difference is the point: the
# rubric redirects a reviewer to the spec rubric, while the body redirects a run
# to its own rubric -- the judgement it writes under. The overlap is the template
# and the substrate contract, which both files defer to. Pinned because the body's
# whole claim to be short is that it restates none of the three: a citation
# deleted leaves a run working from a remembered version of the file, and nothing
# downstream can tell the difference.
SKILL_CITATIONS = {
    path: _plugin_root_citation(path)
    for path in (RICE_TEMPLATE, ROADMAP_PRINCIPLES, ARTIFACT_FAMILY)
}

# Where the substrate defines the suite's unknown marker, and the shape of a
# marker token, so the ban on spelling it here is checked against the real token
# rather than a copy of it.
#
# The pattern is `tests/test_marker_uniqueness.py`'s, and this is the repository's
# second copy of it. That module asks whether the tree uses one dialect; it cannot
# ask whether a particular file abstains, because a file spelling the marker
# correctly is exactly what it is looking for. The copy buys the only question it
# cannot answer, and the alternative -- restating the token here -- would put a
# third spelling of it in the tree, which is the thing that module exists to stop.
UNKNOWN_MARKER_SECTION = "Unknown marker"
MARKER_TOKEN = re.compile(r"\[([A-Z][A-Z ]{2,}):")

# The fence a frontmatter block opens and closes with, named so a failure can say
# what it was looking for rather than showing three dashes in a message.
FRONT_MATTER_FENCE = "---"

# The frontmatter key whose absence costs a round trip, and what that costs.
# `name` is not a row: it is checked by value against the directory rather than
# merely for presence, and `description` belongs to
# `tests/test_description_budget.py`.
REQUIRED_FRONTMATTER_KEYS = (
    (
        "argument-hint",
        "the slug is the one argument this beat cannot guess, since it names a folder "
        "somebody else made -- a user shown no hint is the user step 1 has to stop and "
        "ask, which is a round trip the hint would have saved",
    ),
)

# The key that would take this beat out of the model-facing skill listing, and the
# reason it must stay absent.
#
# It is the cheapest way under the listing budget and the one every sibling
# declined: the six shipped `product-*` beats are all reachable by the model, and a
# beat unreachable for a budget reason is routing decided by a self-imposed number
# rather than by what the beat is for. Pinned here because the budget is where the
# pressure to add it comes from, and a key added quietly changes how this beat is
# reached without changing a line a reader would think to check.
FORBIDDEN_FRONTMATTER_KEY = "disable-model-invocation"

# The rules a run has to follow that nothing can check once the run is over, each
# paired with the literal `SKILL.md` must carry for the rule to exist at all.
# Publishing the rule in the body is the whole of its enforcement, for the reason
# the module docstring gives, and this is the only thing about it that can be
# checked.
#
# These are the body-wide ones: a run may obey them in any step, so they are
# searched across the whole body. The rules that belong to one step are in
# `STEP_OBLIGATIONS` and `REFUSAL_STEP_RULES` below, bounded to the step that owns
# them, because a rule stated in some other step is one the run working this step
# never reads.
#
# The first five mirror the sibling beats' constants of the same name, because the
# substrate is the same one. They are stated here rather than imported: a sibling's
# tuple is that sibling's account of its own body, and a shared one would let a
# rule this beat never states pass on a sentence another beat wrote.
RUNTIME_RULES = (
    (
        "whether the upstream is there is answered by the substrate, not by a local stat",
        "--check-freshness",
    ),
    (
        "no state is derived locally from the files, so every beat in the chain reads one "
        "answer instead of each computing its own",
        "Derive no state of your own",
    ),
    (
        "the provenance line is read off the substrate rather than assembled here",
        "--provenance-line",
    ),
    (
        "naming the entry point is not enough: an author not told the line is copied will "
        "work the sha out by hand, and an assembled provenance line reports freshness "
        "nobody checked",
        "do not assemble a line",
    ),
    (
        "the sha in particular is never computed here, which is the half of the rule above "
        "that a run under time pressure would talk itself out of",
        "do not compute a sha",
    ),
    (
        "the line is asked for by member name, so the sha it carries is over this member's "
        "own upstream and not some other member's",
        "--member roadmap.md",
    ),
    (
        "the upstream is never edited, so the sha just written into this member stays true "
        "and a defect in the spec is routed to the beat that owns it",
        "Never write to spec.md",
    ),
)

# What each step beyond the first must say, keyed by the step that owns it.
#
# Bounded per step rather than searched across the body, for the reason
# `REFUSAL_STEP_RULES` records: every token here is a word the body has honest
# reason to use elsewhere, so a whole-body search would go on passing after the
# step itself had been deleted -- and deleting a whole step is exactly the
# regression this table exists to catch.
#
# The steps that only route a run to the template have no rows, which is the point:
# a step with nothing of its own to say should not be padded until it has some.
STEP_OBLIGATIONS = {
    "Step 2: Score every item, and score nothing you have to invent": (
        (
            "no input is ever supplied by the run itself, which is the failure the whole "
            "table is exposed to: an invented figure arrives with decimals and outranks a "
            "well-sourced item on a table nobody re-derives",
            "Never invent an input",
        ),
        (
            "an item whose input carries the marker gets no score at all, so the cost of "
            "an unknown is the ranking rather than the row",
            "has no Score",
        ),
    ),
    "Step 3: Derive the sequence, and record what beat the score": (
        (
            "the sequence is a decision rather than a view of the table above, and a "
            "sorted copy leaves a reader nothing to disagree with",
            "derived, not sorted",
        ),
        (
            "a departure from score order names which of the two things beat the score, "
            "which is what keeps it a decision rather than a mistake somebody will quietly "
            "correct",
            "outrank",
        ),
        (
            "the ordering that was rejected is written down while somebody still remembers "
            "why, since a year on the chosen order and the first order anybody typed look "
            "identical on the page",
            "rejected ordering",
        ),
    ),
    "Step 4: Get the provenance line, then write": (
        (
            "a null line means the upstream is still missing, and the only move left is "
            "back to step 1 -- a line filled in by hand reports an ancestry nobody checked",
            "inventing a line",
        ),
    ),
    "Step 5: Report": (
        (
            "the run says where it wrote, which is the one fact a user needs to check "
            "anything else the report claims",
            "path written",
        ),
        (
            "the counts are reported, so a roadmap whose items are half unscored and one "
            "whose items are all scored do not report identically",
            "how many",
        ),
    ),
}

# The step that owns the refusals, the beat every refusal has to name, and what
# that step must say beyond routing them.
#
# Bounded to that step, because none of this survives being stated elsewhere: each
# token is a word the file has good reason to use again later -- `REQ` wherever a
# traced row is discussed, `product-spec` wherever the upstream's owner comes up.
# Searched across the whole body, a row here would go on passing after the gate it
# pins had been deleted, which is the one way this test could report a published
# gate that no longer exists.
REFUSAL_SECTION = "Step 1: Refuse unless the spec conforms"
REFUSAL_BEAT = "product-spec"
REFUSAL_STEP_RULES = (
    (
        "the first refusal fires on an upstream that is not there at all, which the "
        "substrate reports as this state",
        "absent",
    ),
    (
        "the second fires on an upstream whose own ancestry cannot be established, since "
        "ordering work off it would put a sha over bytes of unknown ancestry into the "
        "member a reader ranks by",
        "unresolvable",
    ),
    (
        "the third is the one no script can make: a spec with no requirement id leaves "
        "every `Traces to` cell with nothing to name and the coverage table with no rows",
        "REQ",
    ),
    (
        "a stale upstream is not a fourth refusal -- refusing over it would have this beat "
        "re-decide something product-spec owns",
        "stale is not",
    ),
    (
        "only the immediate upstream is inspected, so a run does not gate on a state "
        "somebody further up the chain already decided to live with",
        "immediate upstream",
    ),
    (
        "the substrate's one writing entry point is never reached for: this beat refuses "
        "unless spec.md exists, and a spec.md that exists sits in a folder somebody else "
        "already made",
        "--ensure-folder",
    ),
    (
        "the third refusal is not routed around by supplying the id it refused over, which "
        "is the one move that would satisfy the gate while defeating it: an invented id "
        "traces an item to a requirement nobody wrote",
        "Never invent a requirement id",
    ),
)

# The section that publishes what a second run does, what its body has to say, and
# the one promise it may not make.
#
# Bounded to the section rather than searched across the body. Every other rule
# here is one a run follows and a reader may never need; this one is read *by*
# whoever holds the previous version, so where it is stated is part of the rule --
# `## Re-run behaviour` is the heading every beat in this suite publishes the same
# promise under, and a reader who opens it must not find it empty.
#
# The forbidden token is what makes the required ones mean something. product-brief
# and product-spec replace their members wholesale and say so under this same
# heading, so an author working across the beats is one edit away from promising
# the same here -- and a roadmap replaced wholesale renumbers rows that are cited
# from outside this folder, where no freshness check will ever report the move.
RERUN_SECTION = "Re-run behaviour"
RERUN_RULES = (
    (
        "a second run revises the member rather than replacing it, which is what lets an "
        "untouched item's row stay exactly as it was",
        "in place",
    ),
    (
        "a surviving item keeps the id it already has, however much its wording or its "
        "score changed",
        "keeps the number",
    ),
    (
        "a new item is numbered from the highest ever used rather than from the count of "
        "live ones, so a retirement cannot free a number for something else",
        "highest ever used",
    ),
    (
        "a dropped item is retired by leaving the sequence rather than by deletion, since "
        "a deleted row leaves every citation to its id pointing at nothing",
        "absence from ## Sequence",
    ),
    (
        "a re-scored item's previous score is gone, so the member never carries two "
        "numbers with no rule for choosing between them",
        "previous score is not",
    ),
    (
        "the version being revised cannot be got back, which is the fact that makes the "
        "ids in the file the only record of what they were",
        "gitignored",
    ),
)
RERUN_FORBIDDEN = "wholesale"

# How a flag is written wherever one appears, and how the substrate declares the
# ones it accepts. Reading the parser rather than keeping a list here is what makes
# every flag check below a check against the script that would receive it.
FLAG = re.compile(r"--[a-z][a-z-]*")
DECLARED_FLAG = re.compile(r"""add_argument\(\s*["'](--[a-z][a-z-]*)["']""")


def _headings(markdown: str) -> list[tuple[int, str, int]]:
    """Every ATX heading in `markdown` as (level, text, line number).

    Line numbers are **1-based**, matching what an editor shows and what the
    sibling modules' `_section_span` reports. That is the whole contract a caller
    slicing a section body depends on, since `str.splitlines()` is 0-based: a
    heading reported at `n` sits at `lines[n - 1]`, so `lines[n]` is already the
    first line under it. Stated here rather than at the call site because it is
    this function's promise to make, and a caller that has to infer the base from
    the `enumerate` below is reading the implementation to use the interface.

    Lines inside a fenced code block are skipped: a reference file that shows a
    heading as an example would otherwise report that example as one of its own
    sections, which is the difference between reading a document's shape and
    reading the shape it is describing.

    Whole-line matching is what separates a heading from one demoted a level:
    `## Sequence` is a substring of `### Sequence`, so a substring search would
    report a top-level section in a document that had demoted it under some other
    parent -- the exact corruption these tests exist to catch.
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


def _section_body(markdown: str, name: str) -> list[str]:
    """The lines the H2 called `name` contains, as raw lines.

    Bounded by the next heading at H2 or above, never by the end of the file.
    Measuring to the end instead would let a later section's tables answer for
    this one's, which is the failure that matters here: the member's three
    sections all carry markdown, and the first of them is the only one whose
    tables are pinned.

    The two bounds are asymmetric because `_headings` counts from 1 while
    `str.splitlines()` counts from 0. The start needs no adjustment -- `lines[n]`
    is already the line after a heading reported at `n` -- and the stop subtracts
    one to leave out the heading that ends the section. Both ends therefore
    exclude a heading, which is what makes this a body rather than a span.

    Spans the first heading of that name. A document carrying the section twice
    reports only the first one's contents, which surfaces at the call site as a
    missing or wrong-columned table.

    Comes back empty for a name no H2 carries, so a caller that has not already
    asserted the heading's presence sees an empty section rather than an
    exception. Every caller below asserts on what it finds in the body, so an
    absent section is reported as a missing table rather than passing quietly.
    """
    lines = markdown.splitlines()
    headings = _headings(markdown)
    start = next(
        (line for depth, text, line in headings if depth == 2 and text == name),
        None,
    )
    if start is None:
        return []
    stop = next(
        (line for depth, _text, line in headings if line > start and depth <= 2),
        len(lines) + 1,
    )
    return lines[start : stop - 1]


def _tables(body: list[str]) -> list[list[list[str]]]:
    """Every markdown table in `body`, each as one cell list per row.

    A table is a run of consecutive lines starting with `|`; anything else ends
    the run, so two tables separated by prose come back separately. Header rows
    come first within each table, with the `|---|` alignment row dropped.

    Every table rather than the first, which is where this parts company with the
    siblings' `_table`. `## Scored items` carries two, and a helper that returned
    only the first would leave the coverage table's own header unpinned while
    looking like it had checked the section -- the caller would be asserting
    against the scored table twice and could not tell.

    Header and rows come back together because the two questions asked of a table
    here cannot be separated. Which columns it declares is answered by the header;
    whether anything was said about what they hold is answered only by the rows. A
    helper returning headers alone would pass a template that declared eleven
    columns across two tables and showed none of them filled in.

    Backticks are stripped from every cell, so code-spanning a column name stays a
    formatting choice rather than becoming a renamed column.
    """
    tables: list[list[list[str]]] = []
    current: list[list[str]] | None = None
    for line in body:
        if not line.lstrip().startswith("|"):
            current = None
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if current is None:
            current = []
            tables.append(current)
        # An alignment row separates the header from the body and is not a row of
        # either. Checked only once a header is in hand, so a table whose first
        # line happens to be dashes still reports that first line as its header
        # rather than silently discarding it and promoting a data row.
        if current and set("".join(cells)) <= set("-:"):
            continue
        current.append(cells)
    return tables


def _roadmap_section_names(substrate: str) -> list[str]:
    """roadmap.md's required H2 names, in document order, from the substrate.

    Returns the bare names without their `## ` marker, since callers compare them
    against parsed heading text rather than against raw lines, and an empty list
    when the bullet has moved out from under the pattern -- which callers must
    guard, since a template's heading list would then be compared against nothing
    and reported as wrong for carrying any sections at all.
    """
    bullet = ROADMAP_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _clusters(body: list[str]) -> list[tuple[str, list[str]]]:
    """Each H3 nested in an H2's body, as its name and the lines beneath it.

    Takes the section body rather than the whole document, and that is what
    makes the nesting structural instead of asserted: `_section_body` has
    already cut the file at the next H2, so an H3 sitting *after*
    `## Review-time red flags` ends is not in `body` and cannot be counted. A
    whole-file scan would count it as a cluster, and no critic is ever handed
    it.

    Each cluster spans from its own heading to the next H3's, and the last one
    to the end of `body`, so a question or a severity hint is credited to the
    critic that would receive it rather than to whichever cluster happens to
    precede it in the file.

    Line numbers stay inside this function. `_headings` reports 1-based lines
    against the text it is given, which here is `body` rejoined, so `lines[n]`
    is already the first line under a heading at `n` and `stop - 1` is the
    index of the heading that ends a cluster. The caller gets names and lines
    and never sees the conversion.

    Comes back empty for a body carrying no H3 at all, which the caller reports
    as a cluster count of zero rather than meeting as an exception. That case
    returns early rather than falling through: `stops` below always ends with
    the body's own last line, so an empty `starts` would pair nothing with one
    stop and `strict=True` would raise instead -- turning "this rubric has no
    clusters", the single most important failure this module reports, into a
    `zip()` traceback naming neither the file nor the heading.
    """
    starts = [
        (text, line) for depth, text, line in _headings("\n".join(body)) if depth == CLUSTER_LEVEL
    ]
    if not starts:
        return []
    stops = [line for _text, line in starts[1:]] + [len(body) + 1]
    return [
        (text, body[start : stop - 1]) for (text, start), stop in zip(starts, stops, strict=True)
    ]


def _published_marker_token(substrate: str) -> str:
    """The unknown marker's bare token, read from the substrate's own definition.

    Returns "" when the definition cannot be read, which the caller must guard:
    an expectation derived from nothing would search this rubric for an empty
    string and report a clean abstention on a file that had spelled the marker
    on every other line.
    """
    match = MARKER_TOKEN.search("\n".join(_section_body(substrate, UNKNOWN_MARKER_SECTION)))
    return match.group(1) if match else ""


def _frontmatter_and_body(skill: str) -> tuple[str, str]:
    """`SKILL.md` split into the block a harness parses and the half a run acts from.

    Both halves reach the model, at different moments and under different budgets.
    The frontmatter's description is what the router weighs while choosing a skill
    and is rationed in characters; the body is what the model has in front of it
    while working. A rule that appears only in the description is a rule nobody
    acts on, so it must not satisfy a check that a rule was published.

    Returned together rather than one at a time, because the checks below ask one
    question of each half and two parses of the same `---` block could disagree
    about where it ends -- which would credit a frontmatter line to the body or the
    other way about.

    Three cases. A file with no `---` block at all yields no frontmatter and its
    whole text as the body, rather than nothing: whether this file declares
    frontmatter is a claim of its own, and answering the body's checks with "" would
    report unpublished rules where the rules are present and something else entirely
    is wrong. A well-formed block yields its two halves. A block that opens and never
    closes yields "" for both, which callers must guard, because that is the one
    permissive answer of the three -- a file whose every line the harness reads as
    frontmatter would otherwise satisfy every rule below from text no run acts on.
    """
    if not skill.startswith(FRONT_MATTER_FENCE):
        return "", skill
    end = skill.find(f"\n{FRONT_MATTER_FENCE}", len(FRONT_MATTER_FENCE))
    if end == -1:
        return "", ""
    return skill[len(FRONT_MATTER_FENCE) : end], skill[end + len(FRONT_MATTER_FENCE) + 1 :]


def _frontmatter_keys(frontmatter: str) -> dict[str, str]:
    """The top-level `key: value` pairs of a frontmatter block, values unquoted.

    This module's own small reader, so the suite's standard-library-only rule holds
    without a YAML dependency for the three things read here: whether a key is
    declared, whether one is absent, and what `name` is set to.

    Top-level means column zero, matching `tests/guarantees.py`'s own parser rather
    than merely resembling it. A looser `key.strip()` test would accept an indented
    look-alike, so a `name` nested under another key -- or sitting inside the folded
    `description` block -- would satisfy the directory-agreement check while the
    harness, reading only column zero, saw no `name` at all and inferred one from the
    directory. That is the exact failure that check exists to report.

    Values come back raw apart from surrounding quotes, which is enough for the keys
    read here and deliberately not enough for a folded one: `description: |` yields
    the bare block-scalar indicator, not the description. Measuring `description`
    belongs to `tests/test_description_budget.py`, which reads it through
    `tests/guarantees.py`'s `scalar_text` -- the one reader that strips that
    indicator -- and a second parser reaching for the same field is how two budgets
    come to disagree about what they are measuring.
    """
    keys: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line or line[0].isspace():
            continue
        key, separator, value = line.partition(":")
        if separator:
            keys.setdefault(key, value.strip().strip("\"'"))
    return keys


def _prose(text: str) -> str:
    """`text` as one line, with code spans and line wrapping taken out.

    The one normalisation every token check below runs through, so that "the body
    states this rule" means the same thing at each of them.

    Backticks go because code-spanning a rule's nouns is a formatting choice rather
    than a deleted rule -- the convention every sibling beat's contract follows. Runs
    of whitespace collapse because `SKILL.md` hard-wraps at roughly 76 columns, so any
    pinned phrase of more than three or four words sits on two physical lines about a
    third of the time. Matching against the wrapped text instead makes every
    multi-word expectation depend on where the wrap happens to fall, and the failure
    it produces is a false one: it reports a rule as unpublished when the rule is
    present and a word was added to an earlier sentence.

    Not used for structure. Headings are line-oriented, and flattening them would
    destroy the thing being read, so `_section_body` is always called on the raw text
    and `_prose` on what it returns.
    """
    return " ".join(text.replace("`", "").split())


def _section_prose(markdown: str, name: str) -> str:
    """What the H2 called `name` says, normalised, or "" when the section is absent.

    The one place the read-to-a-section chain is written -- body, then rejoin, then
    normalise. Three groups of checks below ask the same question of a different
    heading, and spelling the chain at each of them is how a fix to one step of it
    silently misses the others.

    An absent heading and an empty one both come back "", which every caller guards
    before reading anything out of it: without that guard a renamed step would report
    each of its obligations as separately unpublished, rather than as the one missing
    step it is.
    """
    return _prose("\n".join(_section_body(markdown, name)))


def _invocations(body: str) -> list[str]:
    """The fenced blocks of `body` that run the substrate script, as whole strings.

    Bounded to fenced blocks naming the script, which is what separates a command
    from prose about one. A run copies what the fence shows, so a flag misspelled
    there fails in a user's session, while the same token in a sentence is a
    documentation defect of a different kind and a different fix. That distinction is
    the whole reason this exists beside the body-wide token sweep: `_prose` flattens
    the fences into the body it searches, so a body carrying the right flag in prose
    and a typo in the fence satisfies every rule in `RUNTIME_RULES`.

    Comes back empty for a body that invokes the script nowhere, which callers must
    guard: a flag check over no invocations passes, and a beat that never calls the
    substrate is exactly the failure those runtime rules exist to prevent.
    """
    blocks: list[str] = []
    current: list[str] | None = None
    for line in body.splitlines():
        if line.startswith("```"):
            if current is None:
                current = []
            else:
                blocks.append("\n".join(current))
                current = None
            continue
        if current is not None:
            current.append(line)
    return [block for block in blocks if SUBSTRATE_SCRIPT.name in block]


def test_template_renders_the_substrate_section_schema() -> None:
    """The template carries exactly the member sections the substrate publishes.

    One property with one owner. The names and their order are the substrate's,
    so a failure here is always the same instruction: change the template, not
    the bullet. What the sections *contain* is this beat's own and is checked
    separately, because a reader who saw the two bundled could not tell a
    substrate disagreement from a renamed column of this skill's own.

    The template's preamble is deliberately outside the equality. What sits above
    the first member heading is scoring grammar an author writes *by*, not a
    section anybody copies into the member, so its H2s are the template's own
    business and this test starts reading at the first published name.
    """
    assert RICE_TEMPLATE.exists(), f"missing shipped template: {RICE_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = RICE_TEMPLATE.read_text()

    # Guard on the read itself before anything is compared against it: a bullet
    # that has moved out from under the pattern yields an empty list, and the
    # equality below would then report a template that carries sections as the
    # thing that had gone wrong.
    published = _roadmap_section_names(substrate)
    assert published, (
        f"no roadmap.md section bullet found in {ARTIFACT_FAMILY.name} under "
        f"{ROADMAP_SECTION_BULLET.pattern!r}; the template's headings are checked against "
        f"that bullet, so nothing below is a check on anything until it parses"
    )

    h2_names = [text for depth, text, _line in _headings(template) if depth == 2]

    assert published[0] in h2_names, (
        f"{RICE_TEMPLATE.name} carries no '## {published[0]}' heading, the first section "
        f"{ARTIFACT_FAMILY.name} publishes for roadmap.md. The template's H2s are "
        f"{h2_names}; everything from the first published name onward is the member, and "
        f"without that heading there is no member in this file at all"
    )

    # Equality from the first member heading onward, not containment, and in file
    # order. Containment would let the template grow a fourth member section of
    # its own, which is the shape this member cannot have: the substrate pins
    # membership as well as order, so a section it does not publish is one no
    # other reader in the chain knows about.
    member_h2 = h2_names[h2_names.index(published[0]) :]
    assert member_h2 == published, (
        f"{RICE_TEMPLATE.name} carries the member sections {member_h2}, but "
        f"{ARTIFACT_FAMILY.name} publishes {published} for roadmap.md, in that order. The "
        f"substrate owns these names -- the template renders them and never decides them "
        f"-- so this is the template to change, not the bullet"
    )


def test_template_declares_the_columns_its_tables_are_read_by() -> None:
    """Both tables of `## Scored items` declare the columns they are read by.

    This beat's own decisions, and nothing else pins them. The scored table is
    what a reader locates a score and its basis by; the coverage table is what
    makes a specified requirement that no item covers visible instead of merely
    absent. A rename or a reshuffle in either breaks that reader while leaving the
    document looking perfectly well-formed, which is why the headers are pinned as
    exact ordered tuples rather than as names to be found somewhere.

    Separate from the section-schema test above, which answers whether the section
    exists at all. This answers whether the section a reader reached is one they
    can use.
    """
    assert RICE_TEMPLATE.exists(), f"missing shipped template: {RICE_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    # The section name is a restatement of one the substrate publishes, so it is
    # guarded before it is used. Without this, a renamed section would leave the
    # body empty and every check below failing with "carries no table" -- pointing
    # at the template when the template is the one file that was right.
    published = _roadmap_section_names(ARTIFACT_FAMILY.read_text())
    assert SCORED_ITEMS_SECTION in published, (
        f"this module reads both tables out of '## {SCORED_ITEMS_SECTION}', but "
        f"{ARTIFACT_FAMILY.name} publishes {published} for roadmap.md. Which section a "
        f"table belongs in is this skill's decision, so a renamed section needs re-keying "
        f"by hand rather than silently keeping its tables"
    )

    body = _section_body(RICE_TEMPLATE.read_text(), SCORED_ITEMS_SECTION)
    tables = _tables(body)
    assert len(tables) == len(DECLARED_TABLES), (
        f"'## {SCORED_ITEMS_SECTION}' of {RICE_TEMPLATE.name} carries {len(tables)} "
        f"tables, not {len(DECLARED_TABLES)}: it declares "
        f"{[label for label, _columns in DECLARED_TABLES]}, in that order. The second is "
        f"the check on the first, so a section carrying one of them is either missing the "
        f"evidence or missing the thing that makes it complete"
    )

    for (label, columns), rows in zip(DECLARED_TABLES, tables, strict=True):
        header, *body_rows = rows
        assert tuple(header) == columns, (
            f"{label} in '## {SCORED_ITEMS_SECTION}' of {RICE_TEMPLATE.name} declares "
            f"columns {header}, not {list(columns)}. The names and their order are what a "
            f"reader locates a cell by, so a rename or a reshuffle leaves them reading the "
            f"wrong cell while the document still looks well-formed"
        )
        assert body_rows, (
            f"{label} in '## {SCORED_ITEMS_SECTION}' of {RICE_TEMPLATE.name} has a header "
            f"row and nothing under it; what belongs in each cell is only shown by a row, "
            f"so a header-only table declares columns without saying what they hold"
        )

    # In the coverage table's own cells, not merely somewhere in the section. An
    # author fills in what a cell shows them, so the literal has to be visible
    # where the blank it prevents would otherwise sit.
    coverage_cells = [cell for row in tables[1][1:] for cell in row]
    assert any(NOT_COVERED_LITERAL in cell for cell in coverage_cells), (
        f"no cell of the requirement-coverage table in {RICE_TEMPLATE.name} shows the "
        f"literal {NOT_COVERED_LITERAL!r}; its cells are {coverage_cells}. Without it the "
        f"only way to say no item covers a requirement is an empty cell, which is also "
        f"what an unfilled table looks like -- and telling those two apart is the whole "
        f"reason that table exists"
    )


def test_principles_expose_five_red_flag_clusters() -> None:
    """The rubric publishes a fleet `product-review` can actually launch.

    Two properties under one name, because a review needs both and neither is
    worth shipping alone. The spine is what an orchestrator quotes a section out
    of. The clusters are what it fans out over -- one finder each, so the count
    is how wide a review of a `roadmap.md` goes and what it leaves unasked.

    The count is the load-bearing assertion. Adding or removing a cluster
    changes what a review costs and which failures nobody looks for, which is a
    decision rather than an edit, so it lands here with every caller in the same
    commit.

    Three things are deliberately not asserted, and a maintainer relying on this
    test should know which. The five clusters are counted and not named, so
    replacing all five with five others of the same shape passes; the names are
    prose a reader judges. Nothing here reads `## Attribution and scope` at all,
    so a deleted citation or a dropped caveat is invisible to the suite -- a gap
    the rubric's own closing section records. And which composed path
    `product-review` selects this file by is that skill's test, not this one.
    """
    assert ROADMAP_PRINCIPLES.exists(), f"missing shipped rubric: {ROADMAP_PRINCIPLES}"

    principles = ROADMAP_PRINCIPLES.read_text()
    h2 = [(text, line) for depth, text, line in _headings(principles) if depth == 2]
    h2_names = [text for text, _line in h2]

    # Exactly once, not merely present: an orchestrator quoting a section by name
    # gets one of them, and a rubric carrying the heading twice has split a
    # section nobody can quote whole. It is also what makes the mapping below
    # safe, since collapsing to a dict keeps only the last of a repeated name.
    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{ROADMAP_PRINCIPLES.name}, found {occurrences}; the file shares its heading "
            f"spine with the suite's other rubrics so that an orchestrator can quote one "
            f"section by name, and it carries {h2_names}"
        )

    # The spine's order is part of it. A maintainer reads the file top to bottom,
    # and the sequence is the reading path: who this is borrowed from and what it
    # covers, then how to author, then how to review, then how to change the file.
    h2_line = dict(h2)
    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"{ROADMAP_PRINCIPLES.name} must carry its spine sections in the order "
        f"{list(PRINCIPLES_SPINE)}, the order its sibling rubrics use; found them at "
        f"lines {spine_lines}"
    )

    clusters = _clusters(_section_body(principles, RED_FLAGS_SECTION))
    cluster_names = [name for name, _body in clusters]
    assert len(clusters) == RED_FLAG_CLUSTER_COUNT, (
        f"expected exactly {RED_FLAG_CLUSTER_COUNT} H{CLUSTER_LEVEL} clusters nested "
        f"under '## {RED_FLAGS_SECTION}' in {ROADMAP_PRINCIPLES.name}, found "
        f"{len(clusters)}: {cluster_names}. A review launches one finder per cluster, so "
        f"this count is how wide the fleet fans out -- changing it changes what a review "
        f"costs and what goes unasked, and every caller quoting these clusters changes "
        f"with it"
    )

    for name, body in clusters:
        hints = [index for index, line in enumerate(body) if SEVERITY_HINT in line]
        assert hints, (
            f"cluster '### {name}' of {ROADMAP_PRINCIPLES.name} carries no "
            f"{SEVERITY_HINT!r} line, so nothing in it is both a question and routable: its "
            f"findings would come back with no severity to triage them by. The clusters are "
            f"{cluster_names}"
        )
        # Per hint rather than once per cluster. A cluster is a list of bullets,
        # each a question with its own hint beneath it, and checking only that
        # the two kinds of line both occur somewhere would pass a cluster of
        # seven statements carrying one stray question mark -- which is a critic
        # handed prose it cannot answer and a reviewer handed findings it cannot
        # route, reported as a healthy cluster.
        for index in hints:
            question = body[index - 1] if index else ""
            assert question.rstrip().endswith("?"), (
                f"the {SEVERITY_HINT!r} line at line {index + 1} of cluster '### {name}' in "
                f"{ROADMAP_PRINCIPLES.name} does not sit beneath a question: the line above "
                f"it is {question!r}. Every bullet is one question a critic answers yes or "
                f"no and one hint the answer is routed by, so a hint under anything else "
                f"belongs to no question"
            )


def test_principles_attribution_stays_checkable() -> None:
    """The rubric keeps saying where its questions came from, and where they did not.

    Separate from the fan-out test above because the two fail for unrelated
    reasons and land in different fix loops. That one asks whether a review can
    be launched at all; this one asks whether the launched questions still admit
    what they rest on. Most of this file's questions reach past their sources --
    three of the five clusters have no source at all -- so the attribution is not
    a courtesy at the top of the file, it is the part that stops a reviewer
    defending an extension on borrowed authority.

    Three properties, each of which fails silently without a test. The citations
    keep the tokens research settled, so the next reader can check them. The
    non-affiliation sentence survives, none of the six named parties having
    endorsed what is built on them here. And the two absences hold: this file
    cites the neighbours it refuses to restate, by paths that still name shipped
    files, and nowhere spells the marker token whose only home is the substrate.

    What stays unasserted is the prose itself -- the seven recorded extensions,
    the guidance on when WSJF, MoSCoW or Kano fit instead, and the reason ICE is
    dropped. A token is checkable; an argument is not, and pinning sentences
    would freeze wording that ought to improve.
    """
    assert ROADMAP_PRINCIPLES.exists(), f"missing shipped rubric: {ROADMAP_PRINCIPLES}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    principles = ROADMAP_PRINCIPLES.read_text()
    attribution = "\n".join(_section_body(principles, ATTRIBUTION_SECTION))
    assert attribution, (
        f"{ROADMAP_PRINCIPLES.name} carries no '## {ATTRIBUTION_SECTION}' section with a "
        f"body; every check below reads that section, so an empty one would report each "
        f"citation as deleted when the heading is what moved"
    )

    for citation in ATTRIBUTION_CITATIONS:
        assert citation in attribution, (
            f"'## {ATTRIBUTION_SECTION}' of {ROADMAP_PRINCIPLES.name} does not name "
            f"{citation!r}. Each token is the one thing research settled about its source, "
            f"and a citation that loses it stops being checkable by the next reader -- "
            f"which is the whole of what an attribution is for"
        )

    assert NON_AFFILIATION in attribution, (
        f"'## {ATTRIBUTION_SECTION}' of {ROADMAP_PRINCIPLES.name} carries no "
        f"{NON_AFFILIATION!r} sentence. Six third parties are cited here for framings this "
        f"file then extends, so saying that none of them endorsed the extension is part of "
        f"the attribution and not boilerplate"
    )

    # Over the whole file, not the attribution alone: a ban is stated in one
    # section and relied on by every question below it.
    for reference in CITED_REFERENCES:
        citation = _plugin_root_citation(reference)
        assert reference.is_file(), (
            f"{ROADMAP_PRINCIPLES.name} cites {citation}, but the plugin ships no file "
            f"there. Each citation is the redirect attached to a rule this rubric refuses "
            f"to restate, so a moved file leaves a reviewer told that a rule exists "
            f"somewhere unnamed"
        )
        assert citation in principles, (
            f"{ROADMAP_PRINCIPLES.name} does not cite {citation}. That file owns rules this "
            f"rubric forbids itself from restating, and a ban with its redirect deleted "
            f"forbids something while saying nowhere to look it up"
        )

    # Derived from the substrate rather than restated, so this cannot become the
    # third spelling of a token the suite publishes exactly once.
    token = _published_marker_token(ARTIFACT_FAMILY.read_text())
    assert token, (
        f"no marker token found under '## {UNKNOWN_MARKER_SECTION}' in "
        f"{ARTIFACT_FAMILY.name} using {MARKER_TOKEN.pattern!r}; the ban below is checked "
        f"against that token, so nothing here is a check on anything until it parses"
    )
    assert token not in principles, (
        f"{ROADMAP_PRINCIPLES.name} spells the unknown marker's token {token!r}. The "
        f"substrate is its only home and this file names it in words instead, so that one "
        f"definition cannot acquire a second copy that drifts from it while both files "
        f"read as correct"
    )


def test_skill_publishes_each_runtime_rule() -> None:
    """Every rule a run must obey is stated where a test can read the statement.

    Everything here is one property, which is why it is one test: the body is the
    whole of the enforcement. Nothing observable afterwards distinguishes a run that
    read its freshness state from one that guessed it, or a Reach counted off a
    ticket queue from one that sounded about right, so a rule missing from the body
    is a rule that does not exist -- and the `roadmap.md` it produces looks exactly
    like the one a compliant run produces. The body-wide sweep covers the rules a run
    may obey in any step; the per-step and per-section groups are bounded to the step
    or section that owns them, because a rule the body states somewhere else is one
    the run working that step never reads.

    The rules are checked as tokens rather than as structure, following the sibling
    beats' own `RUNTIME_RULES`, because what is being checked is that the statement is
    *present*. Whether it is stated persuasively is not decidable here and is left to
    the reader of the file. Every token is matched through `_prose`, so a re-wrap that
    changed no words cannot fail one.

    Four things are deliberately not asserted. The refusal gate is
    `test_skill_gates_on_the_refusal_triad`'s, split out because a missing gate and an
    unpublished rule are fixed in different places. The description's word count, its
    character cost and its leading noun belong to `tests/test_description_budget.py`,
    which owns them by glob and picks this file up automatically, so asserting any of
    them here would report one omission as two failures. How wide a review of this
    beat's output fans out is `test_principles_expose_five_red_flag_clusters`'s. And
    the order the steps appear in is not pinned -- only that each one exists and says
    what no reference file says for it.

    What is left still bundles more subjects than the name states -- the frontmatter
    contract, the body-wide rules, the per-step obligations, the re-run promise, the
    three citations and the substrate's flag vocabulary -- and that is a known cost
    rather than an oversight. They are one property under this name because they share
    one enforcement story: each is a claim the shipped body makes to the run reading it,
    and none of them is observable in what the run leaves behind. A failure is read off
    its message, each of which names the file, the token and what the omission costs.
    """
    assert SKILL_MD.exists(), (
        f"missing shipped skill body: {SKILL_MD}. Without it the beat is a folder of "
        f"references nothing invokes, and every rule below is unpublished"
    )
    assert SUBSTRATE_SCRIPT.exists(), (
        f"missing substrate script: {SUBSTRATE_SCRIPT}. The body's invocations are checked "
        f"against the flags this file declares, so its absence would make that check one "
        f"against an empty vocabulary -- which every invocation fails, for the wrong reason"
    )

    skill = SKILL_MD.read_text()
    frontmatter, body = _frontmatter_and_body(skill)

    # Guarded before anything is read out of it: an unclosed `---` block yields no
    # body, and every presence check below would then fail while reporting missing
    # rules rather than the malformed block that hid them.
    assert body.strip(), (
        f"{SKILL_MD.name} yielded no body to read. Either the file is empty or it opens a "
        f"{FRONT_MATTER_FENCE!r} frontmatter block and never closes it, which leaves the "
        f"harness reading the whole file as frontmatter and a run with no instructions at "
        f"all"
    )

    # Pins this module's split against the one tests/guarantees.py performs, which reads
    # the keys inside the block rather than the remainder and so cannot be asked for the
    # body directly. Were the two to stop agreeing on where the block ends, the
    # description would sit in what this module calls the body, and every rule below
    # could be satisfied by text the router weighs and the model never acts from.
    assert not re.search(r"^description:", body, re.MULTILINE), (
        f"{SKILL_MD.name}'s frontmatter survived into what `_frontmatter_and_body` "
        f"returned as its body, so this module and tests/guarantees.py no longer agree on "
        f"where the block ends"
    )

    # The directory name is not cosmetic: it is the token the description budget's
    # `product-*` rule looks for, and the path a `product-review` run composes this
    # beat's rubric from, so a `name` that disagrees with it splits one beat's identity
    # in two.
    frontmatter_keys = _frontmatter_keys(frontmatter)
    declared_name = frontmatter_keys.get("name", "")
    assert declared_name == SKILL_ROOT.name, (
        f"{SKILL_MD.name} declares frontmatter `name: {declared_name}` but sits in "
        f"{SKILL_ROOT.name}/. Every beat in this suite declares its own name rather than "
        f"leaving the harness to infer one from a directory that may be installed under "
        f"another, and the two must agree: the directory is what the rest of the suite "
        f"identifies this beat by"
    )
    for key, what_it_costs_to_omit in REQUIRED_FRONTMATTER_KEYS:
        assert key in frontmatter_keys, (
            f"{SKILL_MD.name} declares no top-level `{key}` in its frontmatter, and "
            f"{what_it_costs_to_omit}. Its keys are {sorted(frontmatter_keys)}"
        )
    assert FORBIDDEN_FRONTMATTER_KEY not in frontmatter_keys, (
        f"{SKILL_MD.name} declares `{FORBIDDEN_FRONTMATTER_KEY}`, which takes this beat out "
        f"of the model-facing skill listing entirely. It is the cheapest way under the "
        f"listing budget and the one every sibling declined: the shipped product-* beats "
        f"are all reachable by the model, and making the newest one unreachable is routing "
        f"decided by a self-imposed number rather than by what the beat is for. Its keys "
        f"are {sorted(frontmatter_keys)}"
    )

    body_prose = _prose(body)

    for why_the_rule_exists, token in RUNTIME_RULES:
        assert token in body_prose, (
            f"{SKILL_MD.name} never states {token!r} in its body, so the rule it stands for "
            f"is unpublished: {why_the_rule_exists}. Nothing downstream can find this out -- "
            f"a run that broke the rule leaves the same roadmap.md behind as one that kept "
            f"it -- so the statement in the body is the rule's only enforcement. Stating it "
            f"in the frontmatter description instead does not count: the description is what "
            f"the router weighs while choosing a skill, not what the model has in front of "
            f"it while working"
        )

    for section, obligations in STEP_OBLIGATIONS.items():
        step = _section_prose(body, section)
        assert step, (
            f"{SKILL_MD.name} carries no '## {section}' section with anything under it, so "
            f"the obligations below would each be checked against an empty string and "
            f"reported as separate omissions rather than as the one missing step. Its H2s "
            f"are {[text for depth, text, _line in _headings(body) if depth == 2]}"
        )
        for why_the_step_says_it, token in obligations:
            assert token in step, (
                f"'## {section}' of {SKILL_MD.name} never says {token!r}, so the obligation "
                f"it stands for is unpublished: {why_the_step_says_it}. Said in some other "
                f"step it reaches nobody -- a run works this step and then moves on, and no "
                f"reference file states this for it"
            )

    rerun = _section_prose(body, RERUN_SECTION)
    assert rerun, (
        f"{SKILL_MD.name} carries no '## {RERUN_SECTION}' section with anything under it. "
        f"Every beat in this suite publishes what a second run does under that exact "
        f"heading, and this member's ids are cited from outside the folder -- a reader "
        f"holding a filed issue needs to know whether re-running keeps the number it names"
    )
    for why_the_section_says_it, token in RERUN_RULES:
        assert token in rerun, (
            f"'## {RERUN_SECTION}' of {SKILL_MD.name} never says {token!r}: "
            f"{why_the_section_says_it}. This heading is where every beat in the suite "
            f"publishes the same promise, so a reader who opens it and finds the answer "
            f"half-stated will assume the sibling behaviour"
        )
    assert RERUN_FORBIDDEN not in rerun, (
        f"'## {RERUN_SECTION}' of {SKILL_MD.name} says {RERUN_FORBIDDEN!r}. That is "
        f"product-brief's and product-spec's promise, not this beat's, and it is the one an "
        f"author working across the beats will copy: a roadmap replaced whole renumbers rows "
        f"that issues filed elsewhere cite by id, and no freshness check in this chain "
        f"inspects a downstream identifier, so nothing will ever report the move"
    )

    for owner, citation in SKILL_CITATIONS.items():
        assert owner.exists(), (
            f"{SKILL_MD.name} is checked for citing {owner.name}, but that file is not at "
            f"{owner}; the expected citation is built from this path, so a moved file makes "
            f"the check below one on a citation nobody could follow"
        )
        assert citation in body, (
            f"{SKILL_MD.name} never cites {citation}. The body restates nothing "
            f"{owner.name} owns, and that is only half of the arrangement -- the other half "
            f"is sending the run to the file that owns the rule. A missing citation leaves a "
            f"run working from a remembered version of it, which nothing downstream can "
            f"detect. Cite it by {PLUGIN_ROOT_VARIABLE} path, which is what resolves "
            f"wherever the plugin is installed"
        )

    declared = set(DECLARED_FLAG.findall(SUBSTRATE_SCRIPT.read_text()))
    assert declared, (
        f"no flags parsed out of {SUBSTRATE_SCRIPT.name} under {DECLARED_FLAG.pattern!r}; "
        f"every flag check below is against that set, so nothing here is a check on "
        f"anything until it parses"
    )

    # Every flag any rule table in this module names has to be one the substrate accepts,
    # not only the ones the fences pass. Without this a substrate rename leaves a row
    # checking that the body publishes a flag nothing accepts -- so a body obeying it
    # instructs a run to fail, and this module reports that arrangement as healthy.
    #
    # All four tables, including the two this test does not itself read: the property is
    # of the module's pinned literals rather than of either test's subject, and an
    # exhaustive sweep is the only kind whose passing means anything. Splitting it to
    # follow the tables would leave the next table added guarded by nobody. The failure
    # message names the offending literal, so a reader is routed to the table that
    # carries it regardless of which test reported it.
    pinned = (
        *RUNTIME_RULES,
        *REFUSAL_STEP_RULES,
        *RERUN_RULES,
        *(rule for rules in STEP_OBLIGATIONS.values() for rule in rules),
    )
    for _why_the_rule_exists, token in pinned:
        for flag in FLAG.findall(token):
            assert flag in declared, (
                f"this module pins the rule {token!r}, whose flag {flag!r} "
                f"{SUBSTRATE_SCRIPT.name} does not declare -- it accepts {sorted(declared)}. "
                f"The row is checking that the body publishes a flag nothing accepts, so a "
                f"body obeying it instructs a run to fail"
            )

    invocations = _invocations(body)
    assert invocations, (
        f"{SKILL_MD.name} has no fenced block invoking {SUBSTRATE_SCRIPT.name}. The two "
        f"commands it prints are the whole of how a run learns the freshness state and the "
        f"provenance line; a body without them leaves a run with the local stat and the "
        f"hand-assembled sha the rules above exist to forbid"
    )
    for invocation in invocations:
        for flag in FLAG.findall(invocation):
            assert flag in declared, (
                f"an invocation in {SKILL_MD.name} passes {flag!r}, which "
                f"{SUBSTRATE_SCRIPT.name} does not declare -- it accepts {sorted(declared)}. "
                f"A run copies this fence verbatim, so the command fails in a user's session "
                f"with an argparse error and no state at all. The invocation is:\n{invocation}"
            )


def test_skill_gates_on_the_refusal_triad() -> None:
    """The refusal step names all three upstream states, and the beat that fixes them.

    Split from the test above because the two fail for unrelated reasons and are fixed
    in different places. That one asks whether the body published the rules a run works
    under; this one asks whether the run gets as far as working under them at all. A
    gate that is not there is not a weaker version of an unpublished rule -- it is the
    step whose whole job is deciding there is an upstream worth deriving from, and a run
    that skipped it writes a member whose provenance sha is over bytes nothing vouches
    for.

    Bounded to the step that owns the refusals rather than searched across the body, for
    the reason `REFUSAL_STEP_RULES` records: every token here is a word the file has
    good reason to use again later -- `REQ` wherever a traced row is discussed,
    `product-spec` wherever the upstream's owner comes up -- so a whole-body search
    would go on passing after the gate itself had been deleted.

    The file is read and split again rather than shared with the test above, which is
    how the sibling beats' pair of skill tests is arranged too. A module-level cache
    would couple two tests that are meant to fail independently, and the read is one
    call.

    What is not asserted here: that the three refusals appear in the stated order, and
    that `stale` is excluded in every sentence that names it. The first is prose a
    reader judges -- the ordering matters to a user meeting two states at once, and no
    token pins which paragraph came first -- and the second is the sibling
    product-spec's stricter check, left out because this beat's flag literals and its
    per-step obligations already outrun that sibling elsewhere and a reader comparing
    the two should meet the difference here rather than guess at it.
    """
    assert SKILL_MD.exists(), (
        f"missing shipped skill body: {SKILL_MD}. Without it there is no gate to check, "
        f"and no beat either"
    )

    frontmatter, body = _frontmatter_and_body(SKILL_MD.read_text())

    # Guarded before the section is read: an unclosed `---` block yields no body at all,
    # and the section below would then come back empty and report every refusal as
    # missing from a file whose refusal step is intact.
    assert body.strip(), (
        f"{SKILL_MD.name} yielded no body to read -- it is empty, or it opens a "
        f"{FRONT_MATTER_FENCE!r} frontmatter block and never closes it. Nothing below is a "
        f"check on the refusal step until that is fixed. Its frontmatter parsed as "
        f"{len(frontmatter)} characters"
    )

    refusal = _section_prose(body, REFUSAL_SECTION)
    assert refusal, (
        f"{SKILL_MD.name} carries no '## {REFUSAL_SECTION}' section with anything under it, "
        f"so every check below would read an empty string and report six missing rules "
        f"instead of the one missing gate. A gate that is not the first thing a run reaches "
        f"is not a gate: this beat's whole first act is deciding whether there is an "
        f"upstream worth ordering. Its H2s are "
        f"{[text for depth, text, _line in _headings(body) if depth == 2]}"
    )

    assert REFUSAL_BEAT in refusal, (
        f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} never names {REFUSAL_BEAT!r}. A refusal "
        f"that does not say which beat to run leaves the user with a stop and no next move, "
        f"and the next move is the only thing that makes a refusal better than a roadmap "
        f"built on nothing"
    )

    for why_the_gate_says_it, token in REFUSAL_STEP_RULES:
        assert token in refusal, (
            f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} never says {token!r}: "
            f"{why_the_gate_says_it}. Said in some other step it reaches nobody -- a run "
            f"reads this step before it has read anything else -- and said nowhere it is a "
            f"gate that does not exist, which looks identical afterwards to one that passed"
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
