"""Contract tests over the files the product-spec skill ships.

Pins the static shape of the shipped references -- what a standard-library test
can read off the markdown itself. Whether a written `spec.md` obeyed this beat's
run-time rules is not observable here and is enforced two ways instead: at review
time by the critic fleet `product-review` fans over this skill's rubric, and
before that by `SKILL.md` publishing each rule where a run will read it.
`test_skill_publishes_each_runtime_rule` pins that it does, which is the only
check available -- a finished `spec.md` records what the rules produced and never
which of them were followed, since a guessed freshness state and an asked-for one
leave the same document behind.

The rubric that fleet reads is itself one of the shipped references, so its
*interface* is pinned here too: the H2 spine an orchestrator quotes a section out
of, the cluster count that decides how many finders launch, and the parts of its
attribution that record where a shipped question outruns the source it credits.
Whether a cluster's questions are the right questions is not decidable by a test
and is left to the reader of the file.

The section names `spec.md` must carry are published by the product-artifacts
substrate, not by this skill, so they are read out of that contract at run time.
A hardcoded copy here would let the template and the contract drift apart with
both files' tests still green, which is the one failure the citation-over-copy
rule exists to prevent. Which three names the substrate *ought* to publish is a
question the substrate's own contract test owns, and this module never asks it.

Not everything checked here is the substrate's, though, and the split is what a
failure has to be read against. The substrate owns the section names, their order,
and the entry point a provenance line is read off. This beat owns the two tables'
columns and the three things the member deliberately does not carry -- they are
pinned here because nothing else pins them, and a reader who takes them for
substrate rules will go looking for them in the wrong file.

`_headings`, `_section_span`, `_section_body` and `_table` are a fourth copy of
helpers the product-brief, product-discovery and product-requirements contract
modules already carry, and the copy is a knowing one. The reason those three
record for their own duplication holds here too: there is no shared harness under
the repo-level `tests/` for them to live in, and a per-skill module that runs
standalone is worth more than one that cannot. That does not make the coupling
free -- a fix to the fence-skipping rule in one copy leaves the other three
parsing an example heading as a section, with every suite green -- so the honest
fix is that harness, and it would now take four copies at once rather than this
one alone. Three of the siblings' helpers are deliberately not copied. `_table_cells`
and `_cluster_spans` have one call site each and are written at it; `_at_level` now
has two, both one-line comprehensions over `_headings`, and stays uncopied because
naming the level in a comprehension is shorter than the call would be. `_paragraphs`
is this module's own, and answers a question no sibling asks: not what a section
says, but which of its statements sit close enough together to be read as one claim.

Four more helpers arrive with the `SKILL.md` checks. `_plugin_root_citation` is a
second copy of product-requirements' helper of that name and belongs in the same
harness. `_frontmatter_and_body` is a near-copy of that module's `_acting_body`,
returning both halves rather than the body alone because the checks below ask two
questions of one file -- what the frontmatter declares and what a run acts from --
and two parses of the same block could disagree about where it ends; `_prose` is
that module's `_unwrapped` with backtick-stripping folded in, since every token
check here wants both and wants them identically. `_frontmatter_keys`,
`_named_section` and `_sentences` are this module's own, each for the reason its
own docstring gives.

Runnable two ways:
    python3 skills/product-spec/tests/test_product_spec_contract.py
    python3 -m pytest skills/product-spec/tests/test_product_spec_contract.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent.parent
REFERENCES = SKILL_ROOT / "references"
SPEC_TEMPLATE = REFERENCES / "spec-template.md"

# The shipped skill body, and the script its invocations must stay inside the
# vocabulary of. Both are read off disk rather than described here: a flag the
# body passes is checked against the parser that would receive it, so a flag the
# substrate renames fails here instead of failing at run time in a user's session.
SKILL_MD = SKILL_ROOT / "SKILL.md"
SUBSTRATE_SCRIPT = SKILL_ROOT.parent / "product-artifacts" / "scripts" / "product_artifact.py"

# The rubric a `product-review` fleet fans out over. Its filename is not this
# module's to choose -- `product-review` composes the path from the member's owning
# beat -- so this constant restates that composition's output, and the two halves of
# a rename are caught in different places. A rename that stays inside the rubric
# glob (`product-*-principles.md`) but stops matching the composed path fails
# `test_rubric_template_derives_every_shipped_principles_file` over there. A rename
# out of the glob entirely makes the file invisible to that test and is caught here,
# by the existence assertion, which is the only thing standing between a renamed
# rubric and a review that launches no finders and reports a clean member.
SPEC_PRINCIPLES = REFERENCES / "product-spec-principles.md"

# The substrate contract this skill's template must agree with, reached as a
# sibling skill rather than by a plugin-root walk: both skills ship in the same
# tree, so the relative hop is the shortest path that stays true if the plugin
# is installed under a different name.
ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"

# The bullet in artifact-family.md's required-sections list that names spec.md's
# H2 headings, and the pattern that lifts each backticked heading out of it.
#
# The bullet pattern takes its continuation lines too -- any indented, non-blank
# line following the first. The substrate hard-wraps its prose and lists at
# roughly 72 columns, so the day a fourth required section is added the name
# lands on a second physical line. A first-line-only read would drop it, and
# dropping it is invisible in the wrong direction: the template would still
# carry the three names that fitted and the equality below would fail against a
# truncated expectation, reporting a template that had drifted when what had
# actually happened is that this pattern stopped reading the whole bullet.
SPEC_SECTION_BULLET = re.compile(r"^- `spec\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

# The substrate entry point a beat reads its finished provenance line off. Named
# here so the template can be checked for routing an author to it, and asserted
# present in the substrate as well as in the template: the flag is the substrate's
# to rename, and a rename that left this constant behind would leave the template
# check passing against a flag nothing accepts any more.
PROVENANCE_ENTRY_POINT = "--provenance-line"

# The rule that entry point exists to enforce, as the two statements a template
# silent on the subject would leave an author to guess at. Tokens rather than
# structure, following the sibling beats' own `RUNTIME_RULES` shape, because what
# is checked is that the statement is *present*: an author who is not told to copy
# the line will work the sha out by hand, and a member whose provenance was
# assembled rather than read is one whose freshness reporting is fiction while
# every document involved still looks well-formed.
PROVENANCE_STATEMENTS = ("do not assemble", "do not compute a sha")

# The columns of the two tables a reader is read *by* rather than merely reads:
# `/deep-plan` locates a carried requirement and its condition by these headers,
# and a reviewer answers the cost-of-exclusion question by those. Pinned as
# exact ordered tuples, not as name sets to be found somewhere, because a
# renamed or reordered header is what breaks that reader while leaving the
# document looking well-formed.
#
# Keyed by the section each table sits in, so a table pasted under the wrong
# heading is a failure rather than a pass: the two are three-column tables of
# short cells and neither is recognisable by shape alone. The keys are two of
# the substrate's own published names, which is a restatement the test guards
# rather than trusts -- it asserts the keys are still names the substrate
# publishes, so a renamed section is a re-keying decision somebody makes instead
# of one that quietly leaves both table checks looking for nothing.
DECLARED_TABLES = {
    "Requirements in scope": ("ID", "Acceptance condition", "Traces to"),
    "Non-goals": ("Non-goal", "Origin", "Cost of excluding it"),
}

# The opening fence of a YAML front-matter block. Checked on the first line
# only, which is the only place the convention puts one: a spec is read by
# people and by one consumer that treats the file as an opaque path, so a header
# of parseable key-value pairs would be a second, machine-readable copy of what
# the sections say, free to disagree with them.
FRONT_MATTER_FENCE = "---"

# Conventions from spec-kit's own template that this member does not carry, each
# paired with why carrying it would cost something.
#
# They are checked as substrings of the whole file rather than as structures,
# because the failure being prevented is a template that *describes* them: an
# author reading a template that shows a marker convention will use it, and the
# ban has to reach the prose as much as the shape. Which means the template
# cannot state either ban by naming its literal, and has to say what it excludes
# in its own words -- a constraint worth knowing before editing the template.
EXCLUDED_CONVENTIONS = (
    (
        "NEEDS CLARIFICATION",
        "the suite has exactly one unknown-value token and the substrate owns it, so a "
        "second marker convention invented here would compete with it",
    ),
    (
        "Feature Branch",
        "a branch-name metadata line couples the member to a numbered-folder workflow "
        "this chain does not have, and the slug in the path is the only identifier it needs",
    ),
)


# The rubric's H2 spine, and the two of its sections reached into by name below:
# the one that has to say where its questions came from, and the one a fleet fans
# out over.
#
# `product-review`'s own test spells the red-flags heading `"## Review-time red
# flags"` and a cluster heading's opener `"### "`. These are the same literals
# with the level markers taken off, because `_headings` has already stripped them
# by the time anything here compares a name. The three sibling rubric tests state
# this spine too, and no file publishes it for a test to read, so a spine change
# is an edit to four modules at once -- the same knowing duplication the heading
# helpers carry, and headed for the same shared harness. `SEVERITY_HINT`,
# `RED_FLAG_CLUSTER_COUNT` and `NON_AFFILIATION` below are restated across those
# same four modules on the same terms, and re-spelling any of them is the same
# four-file edit; they are not called out again at each one.
ATTRIBUTION_SECTION = "Attribution and scope"
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    ATTRIBUTION_SECTION,
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

# The heading level a red-flag cluster sits at, and how many of them the rubric
# publishes. The count is the load-bearing number in this file: `product-review`
# launches one finder per cluster, so five is the width of the fan-out rather than
# a matter of taste, and a sixth cluster is a change to what a review costs.
CLUSTER_LEVEL = 3
RED_FLAG_CLUSTER_COUNT = 5

# What a cluster carries besides its questions. Without it a critic returns
# findings a reviewer cannot triage, so the fleet is launched and its output is
# unroutable -- a failure that looks like a working review.
SEVERITY_HINT = "Severity hint:"

# The three sources the attribution has to name, each as the token that pins the
# one thing research actually established about it. `1.5-chapter-06` because the
# chapter guessed at first (`1.5-chapter-05`) does not define a no-go;
# `Is This Architecture?` because that is chapter 8's confirmed title; and
# `docs.bmad-method.org` because the path issue #19 cites is a 404 and this is
# where the claim was verified. A citation that loses its token has stopped being
# checkable by the next reader, which is the whole point of recording it.
SHAPE_UP_SOURCE = "1.5-chapter-06"
HOHPE_SOURCE = "Is This Architecture?"
BMAD_SOURCE = "docs.bmad-method.org"
ATTRIBUTION_CITATIONS = (SHAPE_UP_SOURCE, HOHPE_SOURCE, BMAD_SOURCE)

# The disclaimer every rubric in this suite carries. Three named third parties are
# cited here for framings this file then extends, so the sentence saying none of
# them endorsed the extension is part of the attribution rather than boilerplate.
NON_AFFILIATION = "not affiliated"

# The one word that keeps the BMAD citation honest, and the reason it is checked
# per paragraph rather than per file. BMAD's artifact is self-contained only up to
# a point -- the implementation agent still has PRD, architecture and epic context
# prepared for it -- so an uncaveated citation would claim a precedent for
# zero-ancestor independence that nobody has. A caveat two paragraphs away from
# the citation is a caveat a reader quoting the citation will not carry, which is
# why proximity is what gets asserted.
BMAD_CAVEAT = "partial"

# The sub-claim the consulted source did not support. Hohpe's accessible precursor
# essay carries this phrase in its title; the book chapter the attribution cites is
# not openly readable, and nothing available established that it contains a section
# of this name. Pinned absent because it is the most quotable thing about the
# citation and therefore the thing most likely to be added back by someone tidying
# up, at the cost of turning a careful attribution into an invented one.
UNSUPPORTED_SUB_CLAIM = "Look for Decisions!"

# The three files the rubric redirects a reader to instead of restating them, and
# the form it must spell each one in.
#
# `${CLAUDE_PLUGIN_ROOT}` is what resolves at run time wherever the plugin is
# installed; a path relative to a checkout is a path only this checkout has. Each
# expected citation is *built* from the path constant rather than written out as a
# literal, so a citation cannot pass this check while naming a file the repository
# does not ship at that location -- the failure a hand-typed expectation invites,
# since a reader following a citation to nowhere is worse served than one following
# none at all.
#
# Pinned because they are the other half of what this file bans. The rubric may not
# restate the section names, the two tables' columns, the unknown marker, or any
# judgement about a carried sentence, and every one of those bans is a redirect: the
# reader is sent to the file that owns the rule. A redirect nothing pins can be
# deleted with the bans still passing, which leaves a rubric that forbids restating
# four things and names nowhere to find them.
PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"
REQUIREMENTS_PRINCIPLES = (
    SKILL_ROOT.parent / "product-requirements" / "references" / "product-requirements-principles.md"
)


# Defined among the constants, against this module's constants-then-helpers
# layout, because the two mappings below are built from it rather than written out.
def _plugin_root_citation(path: Path) -> str:
    """How a shipped document must cite `path` for a reader to reach it.

    Built from the path constant rather than written as a literal, so a citation
    can never pass a check here while pointing at a file the repository does not
    ship at that location -- the failure a hand-typed expectation invites, since a
    reader following a citation to nowhere is worse served than one following none
    at all. Each caller separately asserts that the cited file exists, which is a
    check on what a reader follows rather than on the constant it was built from.
    """
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


NEIGHBOUR_CITATIONS = {
    path: _plugin_root_citation(path)
    for path in (SPEC_TEMPLATE, ARTIFACT_FAMILY, REQUIREMENTS_PRINCIPLES)
}

# The three files `SKILL.md` sends a run to instead of restating them, and the form
# it must spell each one in.
#
# A different three from the rubric's above, and the difference is the point: the
# rubric redirects a reviewer to the requirements rubric, while the body redirects a
# run to its own rubric -- the judgement it writes under. The overlap is the template
# and the substrate contract, which both files defer to. Pinned because the body's
# whole claim to be short is that it restates none of the three: a citation deleted
# leaves a run working from a remembered version of the file, and nothing downstream
# can tell the difference.
SKILL_CITATIONS = {
    path: _plugin_root_citation(path) for path in (SPEC_TEMPLATE, SPEC_PRINCIPLES, ARTIFACT_FAMILY)
}

# The opening of the suite's unknown-value marker, up to and including its colon.
# The prefix rather than the whole published form, which carries placeholders a
# document filling the marker in replaces; the prefix is the part every use of it
# shows.
#
# The rubric may not spell it: the marker has one home, the substrate contract, and
# a rubric that spells it has become a second definition free to drift. Checked
# against the substrate as well as against the rubric, for the reason
# `PROVENANCE_ENTRY_POINT` is -- the token is the substrate's to re-spell, and a
# re-spelling that left this constant behind would turn the ban below into a ban on
# a token nothing uses, passing over a rubric that had copied the live one.
UNKNOWN_MARKER_PREFIX = "[UNKNOWN:"

# The rules a run has to follow that nothing can check once the run is over, each
# paired with the literal `SKILL.md` must carry for the rule to exist at all.
# Publishing the rule in the body is the whole of its enforcement, for the reason the
# module docstring gives, and this is the only thing about it that can be checked.
#
# Mirrors product-requirements' constant of the same name, and its first three rows
# are the same substrate rules that one carries, because the substrate is the same
# one. They are stated here rather than imported: a sibling's tuple is that sibling's
# account of its own body, and a shared one would let a rule this beat never states
# pass on a sentence another beat wrote.
#
# The last three rows are this beat's own and have no sibling equivalent. Two of them
# guard the same failure from opposite ends -- the carried sentence drifting from the
# upstream's, and the upstream drifting from the carried sentence -- and the third is
# the only mitigation the replacement risk has at all.
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
        "the line is asked for by member name, so the sha it carries is over this "
        "member's own upstream and not some other member's",
        "--member spec.md",
    ),
    (
        "every carried requirement is the upstream's own sentence, so the copy this "
        "member is built on cannot quietly become a paraphrase",
        "byte-for-byte",
    ),
    (
        "a plan written from the version this run replaces is never revisited, which is "
        "the whole mitigation for a risk no freshness check can detect",
        "already been consumed by a plan",
    ),
    (
        "the upstream is never edited, so the sha just written into this member stays true",
        "Never write to requirements.md",
    ),
)

# The substrate's one writing entry point, which this beat must never reach for.
#
# Asserted absent from the whole file rather than from the body alone, where every
# rule above is asserted present in the body alone. The asymmetry is deliberate:
# publishing a rule only in the description would publish it where no run acts on it,
# so presence has to be proved in the body, while a flag named anywhere in a file is
# a flag its author was thinking of passing. Named in prose the ban would still read
# as an option, which is why the body states the no-folder rule in its own words and
# never spells this.
#
# Checked against the substrate's own declared flags before being banned, the way
# `PROVENANCE_ENTRY_POINT` and `UNKNOWN_MARKER_PREFIX` above are: the flag is the
# substrate's to rename, and a rename that left this literal behind would turn the ban
# into a ban on a token nothing accepts -- passing forever, including over a body that
# had begun passing the live write flag under its new name.
FORBIDDEN_ENTRY_POINT = "--ensure-folder"

# How a flag is written wherever one appears, and how the substrate declares the ones
# it accepts. Reading the parser rather than keeping a list here is what makes every
# flag check below a check against the script that would receive it.
FLAG = re.compile(r"--[a-z][a-z-]*")
DECLARED_FLAG = re.compile(r"""add_argument\(\s*["'](--[a-z][a-z-]*)["']""")

# The section that publishes what a second run does, what its body has to say, and the
# one promise it may not make.
#
# Bounded to the section rather than searched for across the body. Every other rule
# here is one a run follows and a reader may never need; this one is read *by*
# whoever holds the previous version, so where it is stated is part of the rule --
# `## Re-run behaviour` is the heading every beat in this suite publishes the same
# promise under, and a reader who opens it must not find it empty.
#
# The forbidden token is what makes the required ones mean something. `product-
# requirements` revises its member in place and says so under this same heading, so
# an author working across the two beats is one edit away from promising the same
# here, and a spec revised in place would keep requirement rows nothing upstream
# still says while reporting as fresh.
RERUN_SECTION = "Re-run behaviour"
RERUN_RULES = (
    (
        "a second run overwrites the member rather than revising it",
        "replace",
    ),
    (
        "the version being overwritten cannot be got back, which is the fact that makes "
        "the overwrite worth announcing at all -- there is no VCS history to fall back on",
        "gitignored",
    ),
    (
        "the overwrite is announced as a statement rather than put to the user as a "
        "prompt, so a run cannot turn the promise into a negotiation",
        "not a confirmation prompt",
    ),
)
RERUN_FORBIDDEN = "in place"

# Where this beat sits in the chain, each paired with what a reader loses when the body
# stops saying it. The input beat is not a row: `REFUSAL_BEAT` below pins it inside the
# step that names it, which is the only place a run acts on it.
#
# Pinned because the consumer is the premise of the whole member. A body that stops
# saying `/deep-plan` reads this file and nothing upstream of it is a body whose
# self-containment rule looks like fussiness, and the next author relaxes it.
CHAIN_POSITIONS = (
    (
        "the beat that sequences the specs this one produces, so a reader knows this "
        "member is not the last word on ordering",
        "product-roadmap",
    ),
    (
        "the consumer that opens this file and nothing upstream of it, which is the "
        "premise every other rule in the body rests on",
        "/deep-plan",
    ),
)

# The frontmatter key whose absence costs a round trip, and what that costs.
# `name` is not a row: it is checked by value against the directory rather than merely
# for presence, and `description` belongs to `tests/test_description_budget.py`.
REQUIRED_FRONTMATTER_KEYS = (
    (
        "argument-hint",
        "the slug is the one argument this beat cannot guess, since it names a folder "
        "somebody else made -- a user shown no hint is the user step 1 has to stop and "
        "ask, which is a round trip the hint would have saved",
    ),
)

# What each step beyond the first must say, keyed by the step that owns it.
#
# Bounded per step rather than searched across the body, for the reason `REFUSALS`
# records: `REQ` and `origins` are words the body has honest reasons to use elsewhere,
# so a whole-body search would go on passing after the step itself had been deleted --
# and deleting a whole step is exactly the regression this table exists to catch.
#
# One table rather than a constant per step, because every row is the same kind of
# claim: an obligation this beat carries that no reference file states for it. The
# steps that only route a run to the template have no rows here, which is the point --
# a step with nothing of its own to say should not be padded until it has some.
STEP_OBLIGATIONS = {
    "Step 2: Select the requirement set and read out what it answers": (
        (
            "the selected requirements are traceable to a validated opportunity, and the "
            "id is what a carried row traces to",
            "OPP",
        ),
        (
            "the problem is read out here and written into the member, since a planner "
            "who cannot see it has no way to judge whether the spec is worth building",
            "problem",
        ),
    ),
    "Step 4: Write the non-goals, each with what it costs": (
        (
            "a non-goal comes from one of two permitted origins and there is no third, "
            "which is what keeps this section from collecting things nobody assumed",
            "no third",
        ),
        (
            "each exclusion carries what it costs, which is the cell that makes the "
            "section worth reading rather than worth counting",
            "costs",
        ),
    ),
    "Step 6: Report": (
        (
            "the run says where it wrote, which is the one fact a user needs to check "
            "anything else the report claims",
            "path written",
        ),
        (
            "the counts are reported, so a spec carrying one requirement and a spec "
            "carrying twenty do not report identically",
            "how many",
        ),
    ),
}

# The step that owns the refusals, the three upstream states each one fires on, and
# the beat every refusal has to name.
#
# Bounded to that step, because none of this survives being stated elsewhere: each
# of these tokens is a word the file has good reason to use again later -- `REQ`
# wherever a carried row is discussed, `product-requirements` wherever the upstream's
# owner comes up. Searched across the whole body, a row here would go on passing
# after the refusal it pins had been deleted, which is the one way this test could
# report a published gate that no longer exists.
REFUSAL_SECTION = "Step 1: Refuse unless requirements conform"
REFUSAL_BEAT = "product-requirements"

# How a run is told to behave when more than one refusal would fire. Pinned as its own
# statement rather than inferred from the numbered list, because a list of three states
# says nothing about what to do when two of them hold: a run that reports all three
# tells its user to fix a provenance line in a file that is not there, and a run that
# reports none tells them only that something was wrong.
STOP_AT_FIRST = "Stop at the first one that fires"

REFUSALS = (
    (
        "the upstream file is not there at all, which is a state the substrate reports "
        "and not one a local stat should discover",
        "absent",
    ),
    (
        "the upstream is present but nobody can say which discovery it came from, so the "
        "sha this member would record is over bytes of unknown ancestry",
        "unresolvable",
    ),
    (
        "the upstream carries no requirement id, so the table this member exists to "
        "carry would have nothing to put in its first column",
        "REQ",
    ),
)

# The fourth state the substrate reports, which this beat records and carries on from
# rather than refusing over, and the phrase that has to sit in the same sentence as
# every mention of it.
#
# Checked per sentence rather than per section, and that granularity is the check. A
# stale upstream is the one state an author under time pressure would promote to a
# fourth refusal, and promoting it looks exactly like a sentence naming `stale` with
# no exclusion beside it. Asserted in both directions: the token has to be there, so
# the beat cannot go silent on a state a run will meet, and every sentence carrying it
# has to carry the exclusion too.
NOT_A_REFUSAL_STATE = "stale"
NOT_A_REFUSAL_PHRASE = "not one of the three"


def _headings(markdown: str) -> list[tuple[int, str, int]]:
    """Every ATX heading in `markdown` as (level, text, line number).

    Lines inside a fenced code block are skipped: a reference file that shows a
    heading as an example would otherwise report that example as one of its own
    sections, which is the difference between reading a document's shape and
    reading the shape it is describing.

    Whole-line matching is what separates a heading from one demoted a level:
    `## Non-goals` is a substring of `### Non-goals`, so a substring search would
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


def _section_span(
    headings: list[tuple[int, str, int]], level: int, name: str, last_line: int
) -> tuple[int, int]:
    """Where one section starts and stops owning the document, as line numbers.

    Every line number here is 1-based, matching what `_headings` reports and what
    an editor shows; `last_line` is the document's own final line on that same
    scale.

    Returns the section heading's own line and the line of the next heading at
    the same or a higher level -- the point where the section stops -- or
    `last_line + 1` when nothing follows it. The body is the lines strictly
    between the two.

    Bounding by the successor heading rather than by the end of the file is what
    keeps a later section's table out of an earlier section's body; measuring to
    the end instead would let the first table in the document answer for every
    section that follows it.

    Spans the first heading of that level and name. A document carrying the
    section twice reports only the first one's contents, which surfaces at the
    call site as a missing or wrong-columned table.

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


def _table(body: list[str]) -> list[list[str]]:
    """The first markdown table in `body`, as one cell list per row.

    The header row comes first, with the `|---|` alignment row dropped, and an
    empty list comes back when `body` holds no table at all.

    Header and rows come back together because the two questions asked of a table
    here cannot be separated. Which columns it declares is answered by the header;
    whether anything was said about what they hold is answered only by the rows. A
    helper returning the header alone would pass a table that declared three
    columns and showed none of them filled in.

    The *first* table, because each section this is called on carries one. A
    section that grows a second table is not served by silently checking its
    first: the caller's expected columns are keyed by section, so the honest fix
    then is a key per table rather than a scan that guesses which one was meant.
    """
    rows: list[list[str]] = []
    for line in body:
        if not line.lstrip().startswith("|"):
            # A non-table line before the table is one of the section's own
            # paragraphs; after it, it is where the table stopped.
            if rows:
                break
            continue
        # Dropping backticks makes code-spanning a column name a formatting
        # choice rather than a renamed column.
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if rows and set("".join(cells)) <= set("-:"):
            continue
        rows.append(cells)
    return rows


def _paragraphs(body: list[str]) -> list[str]:
    """`body` split into single-claim blocks, each rejoined into one string.

    A block is what a reader takes as one claim: a paragraph of prose, or one
    top-level bullet with its continuation lines. Two things end a block -- a blank
    line, and the start of the next unindented bullet -- and the second is not
    optional. A markdown list is conventionally written without blank lines between
    its items, so splitting on blank lines alone returns the whole list as a single
    block, and a caller asking whether a statement and its caveat arrived together
    would be answered yes for a caveat several bullets away. That is the exact
    failure this helper exists to detect, so the helper has to see list items apart.

    An indented bullet is a continuation and does not start a block: a sub-list
    elaborates the item above it rather than making a separate claim.

    Comes back empty for a body with no non-blank line, so a caller looking for a
    block containing something finds none rather than finding an empty one that
    contains nothing.
    """
    blocks: list[list[str]] = []
    for line in body:
        if not line.strip():
            if blocks and blocks[-1]:
                blocks.append([])
            continue
        starts_item = line.startswith(("- ", "* ", "+ "))
        if not blocks or not blocks[-1] or starts_item:
            blocks.append([])
        blocks[-1].append(line)
    return ["\n".join(block) for block in blocks if block]


def _spec_section_names(substrate: str) -> list[str]:
    """spec.md's required H2 names, in document order, from the substrate.

    Returns the bare names without their `## ` marker, since callers compare them
    against parsed heading text rather than against raw lines, and an empty list
    when the bullet has moved out from under the pattern -- which callers must
    guard, since a template's heading list would then be compared against nothing
    and reported as wrong for carrying any sections at all.
    """
    bullet = SPEC_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _frontmatter_and_body(skill: str) -> tuple[str, str]:
    """`SKILL.md` split into the block a harness parses and the half a run acts from.

    Both halves reach the model, at different moments and under different budgets.
    The frontmatter's description is what the router weighs while choosing a skill
    and is rationed in characters; the body is what the model has in front of it
    while working. A rule that appears only in the description is a rule nobody acts
    on, so it must not satisfy a check that a rule was published.

    Returned together, where the sibling `_acting_body` returns the body alone,
    because the checks here ask one question of each half and two parses of the same
    `---` block could disagree about where it ends -- which would credit a
    frontmatter line to the body or the other way about.

    Three cases. A file with no `---` block at all yields no frontmatter and its
    whole text as the body, rather than nothing: whether this file declares
    frontmatter is a claim of its own, and answering the body's checks with "" would
    report unpublished rules where the rules are present and something else entirely
    is wrong. A well-formed block yields its two halves. A block that opens and never
    closes yields "" for both, which callers must guard, because that is the one
    permissive answer of the three -- a file whose every line the harness reads as
    frontmatter would otherwise satisfy every rule below from text no run acts on.
    """
    if not skill.startswith("---"):
        return "", skill
    end = skill.find("\n---", 3)
    if end == -1:
        return "", ""
    return skill[3:end], skill[end + len("\n---") :]


def _frontmatter_keys(frontmatter: str) -> dict[str, str]:
    """The top-level `key: value` pairs of a frontmatter block, values unquoted.

    This module's own small reader, so the suite's standard-library-only rule holds
    without a YAML dependency for the two things read here: whether a key is declared,
    and what `name` is set to.

    Top-level means column zero, matching `tests/guarantees.py`'s own parser rather
    than merely resembling it. The looser `key.strip()` test this replaced accepted an
    indented look-alike, so a `name` nested under another key -- or sitting inside the
    folded `description` block -- satisfied the directory-agreement check while the
    harness, reading only column zero, saw no `name` at all and inferred one from the
    directory. That is the exact failure that check exists to report, and the loose
    read would have hidden it.

    Values come back raw apart from surrounding quotes, which is enough for the keys
    read here and deliberately not enough for a folded one: `description: |` yields the
    bare block-scalar indicator, not the description. Measuring `description` belongs
    to `tests/test_description_budget.py`, which reads it through
    `tests/guarantees.py`'s `scalar_text` -- the one reader that strips that indicator
    -- and a second parser reaching for the same field is how two budgets come to
    disagree about what they are measuring.
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
    third of the time. Matching against the unwrapped text instead makes every
    multi-word expectation depend on where the wrap happens to fall, and the failure it
    produces is a false one: it reports a rule as unpublished when the rule is present
    and a word was added to an earlier sentence. The cure would be worse than the
    disease, since an author who hit it would learn to keep the phrases tests look for
    on one line rather than to write the file well.

    Not used for structure. Headings are line-oriented, and flattening them would
    destroy the thing being read.
    """
    return " ".join(text.replace("`", "").split())


def _invocations(body: str) -> list[str]:
    """The fenced blocks of `body` that run the substrate script, as whole strings.

    Bounded to fenced blocks naming the script, which is what separates a command
    from prose about one. A run copies what the fence shows, so a flag misspelled
    there fails in a user's session, while the same token in a sentence is a
    documentation defect of a different kind and a different fix.

    Comes back empty for a body that invokes the script nowhere, which callers must
    guard: a flag check over no invocations passes, and a beat that never calls the
    substrate is exactly the failure the runtime rules above exist to prevent.
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


def _named_section(markdown: str, name: str) -> str:
    """What the H2 called `name` says in `markdown`, as raw lines, or "" when absent.

    The one place the read-to-a-section chain is written -- span, then body, then
    rejoin. Every caller below asks the same question of a different heading, and
    before this the chain was spelled at each of them and had already begun to diverge
    in its last step, so a fix to how a section is bounded would have landed at one
    call site and silently not the others.

    Raw rather than normalised, because the two questions asked of a section need
    different shapes: whether it states a phrase wants `_prose`, and whether a phrase
    travels with its qualifier wants sentences. Normalising here would force the second
    caller to undo it.
    """
    lines = markdown.splitlines()
    headings = _headings(markdown)
    return "\n".join(_section_body(lines, _section_span(headings, 2, name, len(lines))))


def _sentences(text: str) -> list[str]:
    """`text` as the sentences a reader reads it in, each collapsed to one line.

    Split after `.`, `!` or `?` followed by whitespace, which is the same rule the
    repo's description budget reads a first sentence by, so `requirements.md` and
    `spec.md` do not end a sentence mid-word.

    A sentence rather than a paragraph is the unit here because `_paragraphs` answers
    a different question -- whether two claims arrived together -- and the one asked
    below is the opposite: whether a token and its qualifier are in the *same* claim,
    which a paragraph is too coarse to tell.

    A numbered list marker splits off as a fragment of its own, since `1.` is a
    period followed by a space. Harmless for the checks below, which ask what a
    sentence contains rather than counting them, and cheaper than a rule that would
    have to know a list marker from an abbreviation.
    """
    return re.split(r"(?<=[.!?])\s+", _prose(text))


def test_spec_template_follows_the_published_member_shape() -> None:
    """The template describes the member `spec.md` is contracted to be.

    Five checks under one name because they are one property, and the property has
    two owners rather than one. The substrate publishes the section names, their
    order, and the entry point the provenance line is read off; this beat decides
    the two tables' columns and the three things the member deliberately does not
    carry. A failure in any of the five means the same thing to whoever reads it:
    the file an author writes a spec from no longer describes the member the chain
    agreed on. Which side of that split a given check came from is in the module
    docstring, since it decides which file a fix belongs in.
    """
    assert SPEC_TEMPLATE.exists(), f"missing shipped template: {SPEC_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = SPEC_TEMPLATE.read_text()

    # Guard on the read itself before anything is compared against it: a bullet
    # that has moved out from under the pattern yields an empty list, and the
    # equality below would then report a template that carries sections as the
    # thing that had gone wrong.
    published = _spec_section_names(substrate)
    assert published, (
        f"no spec.md section bullet found in {ARTIFACT_FAMILY.name} under "
        f"{SPEC_SECTION_BULLET.pattern!r}; the template's headings are checked against "
        f"that bullet, so nothing below is a check on anything until it parses"
    )

    lines = template.splitlines()
    headings = _headings(template)
    h2_names = [text for depth, text, _line in headings if depth == 2]

    # Equality, not containment, and in file order. Containment would let the
    # template grow a fourth section of its own, which is the shape this member
    # cannot have: it is the one member something outside the chain reads, and a
    # section the substrate does not publish is one no other reader knows about.
    assert h2_names == published, (
        f"{SPEC_TEMPLATE.name} carries the H2 sections {h2_names}, but "
        f"{ARTIFACT_FAMILY.name} publishes {published} for spec.md, in that order. The "
        f"substrate owns these names -- the template renders them and never decides them "
        f"-- so this is the template to change, not the bullet"
    )

    # The provenance line is the other half of what the substrate publishes about
    # this member, and the half the template can only get wrong by omission: it
    # routes an author to the entry point that emits the line, and says the line is
    # copied rather than worked out. Checked against the substrate first for the
    # same reason the section names are -- the flag is the substrate's to rename.
    assert PROVENANCE_ENTRY_POINT in substrate, (
        f"{ARTIFACT_FAMILY.name} no longer names {PROVENANCE_ENTRY_POINT!r}; the template "
        f"is checked for routing an author to that entry point, so the substrate having "
        f"renamed it makes this a check against a flag nothing accepts. Read the "
        f"substrate's provenance section for the flag it publishes now"
    )
    assert PROVENANCE_ENTRY_POINT in template, (
        f"{SPEC_TEMPLATE.name} never names {PROVENANCE_ENTRY_POINT!r}, the entry point "
        f"{ARTIFACT_FAMILY.name} publishes as where a finished provenance line comes from. "
        f"An author who is not sent there has to invent the line, and the member's whole "
        f"freshness story rests on it"
    )
    for statement in PROVENANCE_STATEMENTS:
        assert statement in template, (
            f"{SPEC_TEMPLATE.name} never states {statement!r}. Naming the entry point is "
            f"not enough on its own: a template that shows where the line comes from "
            f"without saying the line is copied leaves hand-assembling it as the reading "
            f"an author under time pressure will take, and a member whose provenance was "
            f"assembled reports freshness it never checked"
        )

    assert lines and lines[0].strip() != FRONT_MATTER_FENCE, (
        f"{SPEC_TEMPLATE.name} opens with a {FRONT_MATTER_FENCE!r} front-matter fence. "
        f"The member is plain prose: a header of parseable key-value pairs is a second, "
        f"machine-readable copy of what the sections below already say, free to disagree "
        f"with them and read in preference to them"
    )

    for literal, why_it_is_excluded in EXCLUDED_CONVENTIONS:
        assert literal not in template, (
            f"{SPEC_TEMPLATE.name} contains {literal!r}, a convention this member does "
            f"not carry: {why_it_is_excluded}. An author writes what the template shows, "
            f"so the ban has to hold in the template's own prose too -- state what is "
            f"excluded in this member's own words rather than by naming the literal"
        )

    # The keys restate two published names, so they are checked against the
    # substrate rather than trusted. Without this, a renamed section leaves both
    # table lookups spanning nothing and failing with "carries no table", which
    # points at the template when the template is the one file that was right.
    assert set(DECLARED_TABLES) <= set(published), (
        f"DECLARED_TABLES keys the template's tables by the sections "
        f"{sorted(DECLARED_TABLES)}, but {ARTIFACT_FAMILY.name} publishes {published} for "
        f"spec.md. Which section a table belongs in is this skill's decision, so a "
        f"renamed section needs re-keying by hand rather than silently keeping its table"
    )

    for section, columns in DECLARED_TABLES.items():
        rows = _table(_section_body(lines, _section_span(headings, 2, section, len(lines))))
        assert rows, (
            f"'## {section}' of {SPEC_TEMPLATE.name} carries no table; the section is "
            f"where a reader goes for {list(columns)}, and a missing field is only "
            f"visible as an empty cell -- prose describing the same fields hides the "
            f"omission this member's rubric exists to find"
        )
        header, *body_rows = rows
        assert tuple(header) == columns, (
            f"'## {section}' of {SPEC_TEMPLATE.name} declares columns {header}, not "
            f"{list(columns)}. The names and their order are what a reader locates a "
            f"cell by, so a rename or a reshuffle breaks that reader while leaving the "
            f"document looking well-formed"
        )
        assert body_rows, (
            f"the table in '## {section}' of {SPEC_TEMPLATE.name} has a header row and "
            f"nothing under it; what belongs in each cell is only shown by a row, so a "
            f"header-only table declares columns without saying what they hold"
        )


def test_principles_expose_the_fleet_fan_out_shape() -> None:
    """The rubric publishes a launchable fleet and an attribution that holds up.

    Three properties under one name, because a `product-review` run needs all
    three and none is worth shipping alone. The first is mechanical: the H2 spine
    an orchestrator quotes a section out of, and five clusters each carrying
    questions a critic can answer and hints a reviewer can route a finding by. The
    second is the attribution, checked at exactly the three points where research
    found the shipped claims reaching past their sources -- so the file keeps
    saying which parts are borrowed and which are this project's own. The third is
    that its four bans still come with their redirects: this rubric forbids
    restating what three neighbours own, and a ban whose citation has been deleted
    tells a reviewer a rule exists somewhere unnamed.

    The cluster count is the load-bearing assertion. It is how wide a review fans
    out, so changing it changes what a review costs and what it covers, and that
    is a decision rather than an edit.

    Three things are deliberately not asserted, and a maintainer relying on this
    test should know which. The five clusters are counted and not named, so
    replacing all five with five others of the same shape passes here; the names
    are prose a reader judges. Whether any question is a good question is not
    decidable at all. And which composed path `product-review` selects this file
    by is that skill's own test -- see the note on `SPEC_PRINCIPLES` for how a
    rename splits between the two modules.
    """
    assert SPEC_PRINCIPLES.exists(), f"missing shipped rubric: {SPEC_PRINCIPLES}"

    principles = SPEC_PRINCIPLES.read_text()
    lines = principles.splitlines()
    headings = _headings(principles)
    h2 = [(text, line) for depth, text, line in headings if depth == 2]
    h2_names = [text for text, _line in h2]

    # Exactly once, not merely present: an orchestrator quoting a section by name
    # gets one of them, and a rubric carrying the heading twice has split a section
    # nobody can quote whole. It is also what makes the mapping below safe, since
    # collapsing to a dict keeps only the last occurrence of a repeated name.
    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{SPEC_PRINCIPLES.name}, found {occurrences}; the file shares its heading "
            f"spine with the suite's other rubrics so that an orchestrator can quote one "
            f"section by name, and it carries {h2_names}"
        )

    # The spine's order is part of it. A maintainer reads the file top to bottom,
    # and the sequence is the reading path: who this is borrowed from and what it
    # covers, then how to author, then how to review, then how to change the file.
    h2_line = dict(h2)
    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"{SPEC_PRINCIPLES.name} must carry its spine sections in the order "
        f"{list(PRINCIPLES_SPINE)}, the order its sibling rubrics use; found them at "
        f"lines {spine_lines}"
    )

    # Clusters are the H3s falling *inside* the red-flags section, which is what
    # proves nesting: an H3 after that section's end is one no critic is ever
    # handed, and scanning the whole file would count it as a finder.
    red_flags_start, red_flags_end = _section_span(headings, 2, RED_FLAGS_SECTION, len(lines))
    clusters = [
        (text, line)
        for depth, text, line in headings
        if depth == CLUSTER_LEVEL and red_flags_start < line < red_flags_end
    ]
    cluster_names = [name for name, _line in clusters]
    assert len(clusters) == RED_FLAG_CLUSTER_COUNT, (
        f"expected exactly {RED_FLAG_CLUSTER_COUNT} H{CLUSTER_LEVEL} clusters nested "
        f"under '## {RED_FLAGS_SECTION}' in {SPEC_PRINCIPLES.name}, found "
        f"{len(clusters)}: {cluster_names}. A review launches one finder per cluster, so "
        f"this count is how wide the fleet fans out -- changing it changes what a review "
        f"costs and what goes unasked, and every caller quoting these clusters changes "
        f"with it"
    )

    # Each cluster stops where the next begins, and the last where the section
    # does, so a question or a hint is credited to the critic that would receive it
    # rather than to whichever cluster happens to precede it in the file.
    stops = [line for _name, line in clusters[1:]] + [red_flags_end]
    for (name, start), stop in zip(clusters, stops, strict=True):
        body = _section_body(lines, (start, stop))
        assert any(line.rstrip().endswith("?") for line in body), (
            f"cluster '### {name}' of {SPEC_PRINCIPLES.name} carries no line ending in a "
            f"question mark. Every cluster is a set of questions answered yes or no "
            f"against a written spec.md, and a critic handed prose has nothing to answer. "
            f"The clusters are {cluster_names}"
        )
        assert any(SEVERITY_HINT in line for line in body), (
            f"cluster '### {name}' of {SPEC_PRINCIPLES.name} carries no {SEVERITY_HINT!r} "
            f"line, so its findings come back with no severity to route them by and the "
            f"fleet's output cannot be triaged. The clusters are {cluster_names}"
        )

    attribution = _section_body(lines, _section_span(headings, 2, ATTRIBUTION_SECTION, len(lines)))
    attribution_text = "\n".join(attribution)

    for citation in ATTRIBUTION_CITATIONS:
        assert citation in attribution_text, (
            f"'## {ATTRIBUTION_SECTION}' of {SPEC_PRINCIPLES.name} does not name "
            f"{citation!r}. Each token is the one thing research settled about its source, "
            f"and a citation that loses it stops being checkable by the next reader -- "
            f"which is what an attribution is for"
        )

    assert NON_AFFILIATION in attribution_text, (
        f"'## {ATTRIBUTION_SECTION}' of {SPEC_PRINCIPLES.name} carries no "
        f"{NON_AFFILIATION!r} sentence. Three third parties are cited here for framings "
        f"this file then extends, so saying none of them endorsed the extension is part "
        f"of the attribution and not boilerplate"
    )

    # Per paragraph, not per section. The caveat's job is to travel with the
    # citation: a reader who quotes the BMAD sentence and leaves the caveat two
    # paragraphs behind has claimed a precedent for zero-ancestor independence that
    # BMAD does not supply, and every paragraph naming the source has to carry it.
    citing_bmad = [block for block in _paragraphs(attribution) if BMAD_SOURCE in block]
    assert citing_bmad, (
        f"'## {ATTRIBUTION_SECTION}' of {SPEC_PRINCIPLES.name} has no paragraph naming "
        f"{BMAD_SOURCE!r}, so the caveat check below has nothing to check; the citation "
        f"and its caveat are shipped together or not at all"
    )
    for block in citing_bmad:
        assert BMAD_CAVEAT in block, (
            f"a paragraph of '## {ATTRIBUTION_SECTION}' in {SPEC_PRINCIPLES.name} cites "
            f"{BMAD_SOURCE!r} without the word {BMAD_CAVEAT!r} beside it. BMAD's handoff "
            f"artifact is self-contained only up to a point -- the implementation agent "
            f"still has PRD, architecture and epic context prepared for it -- so an "
            f"uncaveated citation overstates the precedent this member rests on. The "
            f"paragraph is: {block!r}"
        )

    # Checked over the whole file rather than the attribution alone. The claim is
    # unsupported wherever it is made, and a cluster body is the likelier place for
    # it to reappear, since that is where a critic would find it persuasive.
    assert UNSUPPORTED_SUB_CLAIM not in principles, (
        f"{SPEC_PRINCIPLES.name} names {UNSUPPORTED_SUB_CLAIM!r}. The book chapter cited "
        f"in '## {ATTRIBUTION_SECTION}' is not openly readable and nothing consulted "
        f"established that it carries a section of that name -- the phrase belongs to an "
        f"accessible precursor essay, and lifting it into the book's citation turns a "
        f"careful attribution into an invented one"
    )

    # Asserted immediately before the bans they exist to serve, because that is the
    # pairing: this file forbids restating four rules and points at the files that
    # own them, and a ban whose redirect has been deleted still passes.
    for owner, citation in NEIGHBOUR_CITATIONS.items():
        assert owner.exists(), (
            f"{SPEC_PRINCIPLES.name} is checked for citing {owner.name}, but that file is "
            f"not at {owner}; the expected citation is built from this path, so a moved "
            f"file makes the check below one on a citation nobody could follow"
        )
        assert citation in principles, (
            f"{SPEC_PRINCIPLES.name} never cites {citation}. This file forbids restating "
            f"what {owner.name} owns, and the ban is only half of that: the other half is "
            f"telling a reviewer where the rule actually lives. Cite it by "
            f"{PLUGIN_ROOT_VARIABLE} path, which is what resolves wherever the plugin is "
            f"installed"
        )

    # Guarded against the substrate before being banned in the rubric: a token the
    # substrate no longer uses is one no rubric would copy, so the ban would hold
    # forever over a rubric free to spell whatever the marker had become.
    assert UNKNOWN_MARKER_PREFIX in ARTIFACT_FAMILY.read_text(), (
        f"{ARTIFACT_FAMILY.name} no longer spells {UNKNOWN_MARKER_PREFIX!r}, so the ban "
        f"below is a ban on a token nothing uses and would pass over a rubric that had "
        f"copied the marker's new spelling. Read the substrate's unknown-marker section "
        f"for the token it publishes now"
    )
    assert UNKNOWN_MARKER_PREFIX not in principles, (
        f"{SPEC_PRINCIPLES.name} spells the unknown-value marker {UNKNOWN_MARKER_PREFIX!r}. "
        f"The marker has exactly one home in this plugin and it is the artifact-family "
        f"contract; a rubric that spells it is a second definition free to drift from "
        f"the first. Name the marker, cite the contract, and do not reproduce the token"
    )


def test_skill_publishes_each_runtime_rule() -> None:
    """Every rule a run must obey is stated where a test can read the statement.

    Everything here is one property, which is why it is one test: the body is the
    whole of the enforcement. Nothing observable afterwards distinguishes a run that
    read its freshness state from one that guessed it, or a requirement carried across
    from one gently improved on the way, so a rule missing from the body is a rule that
    does not exist -- and the member it produces looks exactly like the member a
    compliant run produces. A body-wide sweep covers the rules a run may obey in any
    step; the per-step and per-section groups below are bounded to the step or section
    that owns them, because a rule the body states somewhere else is one the run
    working that step never reads.

    The rules are checked as tokens rather than as structure, following the sibling
    beats' own `RUNTIME_RULES`, because what is being checked is that the statement is
    *present*. Whether it is stated persuasively is not decidable here and is left to
    the reader of the file. Every token is matched through `_prose`, so a re-wrap that
    changed no words cannot fail one.

    Three things are deliberately not asserted. The description's length, its
    character cost and its leading noun belong to `tests/test_description_budget.py`,
    which owns them by glob and picks this file up automatically, so asserting any of
    them here would report one omission as two failures. How wide a review of this
    beat's output fans out is `test_principles_expose_the_fleet_fan_out_shape`'s. And
    the order the steps appear in is not pinned -- only that the refusal step exists
    and says the right things, which is
    `test_skill_gates_on_the_refusal_triad`'s question.

    It bundles more subjects than its name states, and that is a known cost rather
    than an oversight: the plan this beat was built from calls for two test functions
    split by *what fails a run* -- the gate, and everything the body must publish --
    rather than one per assertion. A failure is read off its message, each of which
    names the file, the token and what the omission costs.
    """
    assert SKILL_MD.exists(), (
        f"missing shipped skill body: {SKILL_MD}. Without it the beat is a folder of "
        f"references nothing invokes, and every rule below is unpublished"
    )
    assert SUBSTRATE_SCRIPT.exists(), (
        f"missing substrate script: {SUBSTRATE_SCRIPT}. The body's invocations are "
        f"checked against the flags this file declares, so its absence would make that "
        f"check one against an empty vocabulary -- which every invocation fails, for the "
        f"wrong reason"
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

    body_prose = _prose(body)

    for why_the_rule_exists, token in RUNTIME_RULES:
        assert token in body_prose, (
            f"{SKILL_MD.name} never states {token!r} in its body, so the rule it stands "
            f"for is unpublished: {why_the_rule_exists}. Nothing downstream can find this "
            f"out -- a run that broke the rule leaves the same spec.md behind as one that "
            f"kept it -- so the statement in the body is the rule's only enforcement. "
            f"Stating it in the frontmatter description instead does not count: the "
            f"description is what the router weighs while choosing a skill, not what the "
            f"model has in front of it while working"
        )

    declared = set(DECLARED_FLAG.findall(SUBSTRATE_SCRIPT.read_text()))
    assert declared, (
        f"no flags parsed out of {SUBSTRATE_SCRIPT.name} under {DECLARED_FLAG.pattern!r}; "
        f"every flag check below is against that set, so nothing here is a check on "
        f"anything until it parses"
    )

    # The ban is guarded against its owner before being made, the way the two other
    # substrate literals in this module are: a flag the substrate no longer accepts is a
    # flag no body would pass, so the ban would hold forever while a body reaching for
    # the write entry point under its new name sailed through.
    assert FORBIDDEN_ENTRY_POINT in declared, (
        f"{SUBSTRATE_SCRIPT.name} no longer declares {FORBIDDEN_ENTRY_POINT!r} -- it "
        f"accepts {sorted(declared)}. The ban below is therefore a ban on a token nothing "
        f"accepts and would pass over a body that had begun passing the substrate's write "
        f"entry point under its current name. Read the script's parser for the flag it "
        f"declares now"
    )
    assert FORBIDDEN_ENTRY_POINT not in skill, (
        f"{SKILL_MD.name} names {FORBIDDEN_ENTRY_POINT!r}. That is the substrate's one "
        f"writing entry point, and this beat never reaches for it: it refuses unless "
        f"requirements.md is already there, and a requirements.md that exists sits in a "
        f"folder with an index row somebody else already made. Naming the flag even to "
        f"forbid it leaves it reading as an option, so state the no-folder rule in the "
        f"body's own words"
    )

    # Every flag a pinned rule names has to be one the substrate accepts too, not only
    # the ones the fences pass. Without this a substrate rename leaves the body free to
    # keep the dead flag in the prose a run reads while its fence carries the live one.
    for _why_the_rule_exists, token in RUNTIME_RULES:
        for flag in FLAG.findall(token):
            assert flag in declared, (
                f"RUNTIME_RULES pins the rule {token!r}, whose flag {flag!r} "
                f"{SUBSTRATE_SCRIPT.name} does not declare -- it accepts {sorted(declared)}. "
                f"The row is checking that the body publishes a flag nothing accepts, so a "
                f"body obeying it instructs a run to fail"
            )

    invocations = _invocations(body)
    assert invocations, (
        f"{SKILL_MD.name} has no fenced block invoking {SUBSTRATE_SCRIPT.name}. The two "
        f"commands it prints are the whole of how a run learns the freshness state and the "
        f"provenance line; a body without them leaves a run with the local stat and the "
        f"hand-assembled sha that RUNTIME_RULES exists to forbid"
    )
    for invocation in invocations:
        for flag in FLAG.findall(invocation):
            assert flag in declared, (
                f"an invocation in {SKILL_MD.name} passes {flag!r}, which "
                f"{SUBSTRATE_SCRIPT.name} does not declare -- it accepts "
                f"{sorted(declared)}. A run copies this fence verbatim, so the command "
                f"fails in a user's session with an argparse error and no state at all. "
                f"The invocation is:\n{invocation}"
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

    for why_it_matters, token in CHAIN_POSITIONS:
        assert token in body_prose, (
            f"{SKILL_MD.name} never names {token!r} in its body: {why_it_matters}. A beat "
            f"that does not say where it sits reads as the end of the chain, and the next "
            f"author relaxes the rules that only make sense because it is not"
        )

    for section, obligations in STEP_OBLIGATIONS.items():
        step = _prose(_named_section(body, section))
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

    rerun = _prose(_named_section(body, RERUN_SECTION))
    assert rerun, (
        f"{SKILL_MD.name} carries no '## {RERUN_SECTION}' section with anything under it. "
        f"Every beat in this suite publishes what a second run does under that exact "
        f"heading, and this member is the one a plan is written from -- a reader holding a "
        f"spec needs to know whether re-running keeps it"
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
        f"product-requirements' promise, not this beat's, and it is the one an author "
        f"working across the two will copy: a spec revised in place keeps rows whose "
        f"upstream sentences have moved on, and reports fresh while doing it"
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
            f"is sending the run to the file that owns the rule. A missing citation leaves "
            f"a run working from a remembered version of it, which nothing downstream can "
            f"detect. Cite it by {PLUGIN_ROOT_VARIABLE} path, which is what resolves "
            f"wherever the plugin is installed"
        )


def test_skill_gates_on_the_refusal_triad() -> None:
    """The refusal step names all three upstream states, and the beat that fixes them.

    Bounded to the step that owns the refusals rather than searched across the body,
    for the reason `REFUSALS` records: every token here is a word the file has good
    reason to use again later, so a whole-body search would go on passing after the
    gate itself had been deleted.

    The fourth state is asserted differently from the three, and the difference is the
    test. `stale` must be named -- a beat silent on a state the substrate reports
    leaves a run to invent a response -- and every sentence naming it must also
    exclude it, because a stale upstream is the state an author would most plausibly
    promote to a fourth refusal, and this beat refusing over it would re-decide
    something product-requirements owns.

    That only one of the three is reported *is* asserted, via `STOP_AT_FIRST`. Which
    order they are tried in is not, though the file states it and it matters: a file
    that is not there has no provenance line to resolve, and a table read out of a file
    of unknown ancestry answers nothing. Pinning the order from token positions in
    prose would fail on a rewrite that changed no rule, so that one check is left to a
    reader.
    """
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    _frontmatter, body = _frontmatter_and_body(SKILL_MD.read_text())

    # Guarded here as well as in the sibling test, rather than left to it: an unclosed
    # `---` block yields no body at all, and the section read below would then come back
    # empty and report a missing refusal step in a file whose refusal step is intact.
    assert body.strip(), (
        f"{SKILL_MD.name} yielded no body to read -- it is empty, or it opens a "
        f"{FRONT_MATTER_FENCE!r} frontmatter block and never closes it. Nothing below is a "
        f"check on the refusal step until that is fixed"
    )

    section = _named_section(body, REFUSAL_SECTION)
    assert section.strip(), (
        f"{SKILL_MD.name} carries no '## {REFUSAL_SECTION}' section with anything under "
        f"it, so every check below reads an empty body and would report three missing "
        f"refusals instead of the one missing gate. A gate that is not the first thing a "
        f"run reaches is not a gate: this beat's whole first act is deciding whether there "
        f"is an upstream worth deriving from"
    )
    text = _prose(section)

    for what_it_fires_on, token in REFUSALS:
        assert token in text, (
            f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} never names {token!r}, so the "
            f"refusal it stands for is not published: {what_it_fires_on}. Named somewhere "
            f"else in the body it reaches nobody -- a run reads this step before it has "
            f"read anything else, and proceeding past a state that should have stopped it "
            f"puts a sha over bytes nothing vouches for into the one member a planner reads"
        )

    assert REFUSAL_BEAT in text, (
        f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} never names {REFUSAL_BEAT!r}. A "
        f"refusal that does not say which beat to run leaves the user with a stop and no "
        f"next move, and the next move is the only thing that makes a refusal better than "
        f"a bad spec"
    )

    assert STOP_AT_FIRST in text, (
        f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} never says {STOP_AT_FIRST!r}. The three "
        f"refusals can hold at once, and a step that does not say which one to report "
        f"leaves a run either naming all three -- sending its user to fix a provenance line "
        f"in a file that is not there -- or naming none"
    )

    assert NOT_A_REFUSAL_STATE in text, (
        f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} never names "
        f"{NOT_A_REFUSAL_STATE!r}. The substrate reports that state and a run will meet "
        f"it, so a step silent on it leaves the run to decide for itself whether it is a "
        f"refusal -- and the safe-looking decision is to stop, which would have this beat "
        f"re-decide something {REFUSAL_BEAT} owns"
    )
    sentences_naming_it = [
        sentence for sentence in _sentences(section) if NOT_A_REFUSAL_STATE in sentence
    ]
    for sentence in sentences_naming_it:
        assert NOT_A_REFUSAL_PHRASE in sentence, (
            f"a sentence of '## {REFUSAL_SECTION}' in {SKILL_MD.name} names "
            f"{NOT_A_REFUSAL_STATE!r} without {NOT_A_REFUSAL_PHRASE!r} beside it. That "
            f"state is reported and carried on from, never refused over, and this step is "
            f"where a fourth refusal would be added: the exclusion has to travel in the "
            f"same sentence, because a reader who stops at this one has the whole rule. "
            f"The sentence is: {sentence!r}"
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
