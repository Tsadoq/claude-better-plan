"""Contract tests over the files the product-requirements skill ships.

Pins the static shape of the shipped references -- what a standard-library
test can read off the markdown itself. Whether a generated requirements.md
obeyed the skill's run-time rules is not observable here and is enforced at
review time instead; SKILL.md publishes those rules and
`test_skill_publishes_each_runtime_rule` pins that it does.

The section names requirements.md must carry are published by the
product-artifacts substrate, not by this skill, so they are read out of that
contract at run time. A hardcoded copy here would let the template and the
contract drift apart with both files' tests still green, which is the one
failure the citation-over-copy rule exists to prevent.

The heading helpers below are a third copy of the ones the product-brief and
product-discovery contract modules already carry, and they are a copy knowingly.
The reason product-discovery records for its own duplication holds here too:
there is no shared harness under the repo-level `tests/` for them to live in,
and a per-skill module that runs standalone is worth more than one that cannot.
That does not make the coupling free -- a fix to the fence-skipping rule in one
copy leaves the other two parsing an example heading as a section, with every
suite green -- so the honest fix is that harness, and it would take all three
copies at once rather than this one alone.

Three smaller copies travel with them, named here rather than left implied
because a duplication nobody wrote down is one the next author reads as a
coincidence: `_plugin_root_citation`, which builds the citation a shipped
document must spell a sibling file with; `_unknown_marker_prefix`, which reads
the substrate's marker token; and the `## Unknown marker` heading and fenced-
block pattern the second of those is driven by. All three are the same third
occurrence as the heading helpers, belong in the same harness, and are pinned
here in the meantime by nothing but the fact that all three suites read the same
substrate. `_guarantees` is a fourth of the same kind, and the one whose home is
least in doubt: it loads the repo-level `tests/guarantees.py`, so a harness living
beside that file would not need to load it at all.

`CITED_REFERENCES` and `FORBIDDEN_FRONTMATTER_KEYS` are third occurrences too, and
they are named here for the reason the paragraph above gives rather than left to
the comment at each one. Neither is a helper a harness could absorb: each row is
this beat's own account of its own file, which is why the two tuples say partly
different things from their siblings' -- two extra references and one extra key.
What is copied is the shape, so the coupling runs the other way from the helpers':
a rule the suite adds about every skill's frontmatter has to be written into three
tuples by hand, and the two that were missed stay green.

`_acting_body` is a near-fourth, and the "near" is the part worth reading: it
splits SKILL.md the way the siblings' `_skill_body` does and answers a missing
frontmatter block differently on purpose, for the reason its own docstring gives.
A harness taking all of these would have to reconcile that difference rather than
absorb it, which is why the divergence is documented at the helper and not here.

Runnable two ways:
    python3 skills/product-requirements/tests/test_product_requirements_contract.py
    python3 -m pytest skills/product-requirements/tests/test_product_requirements_contract.py
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
REQUIREMENTS_TEMPLATE = REFERENCES / "requirements-template.md"
REQUIREMENTS_PRINCIPLES = REFERENCES / "product-requirements-principles.md"

# The repository root, reached by walking out of skills/<this skill>/, and used
# to build the citations a shipped document must spell a sibling file with, and
# to reach the repo-level frontmatter parser.
REPO_ROOT = SKILL_ROOT.parents[1]

# The substrate contract this skill's template must agree with, reached as a
# sibling skill rather than by a plugin-root walk: both skills ship in the same
# tree, so the relative hop is the shortest path that stays true if the plugin
# is installed under a different name.
ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"

# The bullet in artifact-family.md's required-sections list that names
# requirements.md's H2 headings, and the pattern that lifts each backticked
# heading out of it.
#
# The bullet pattern takes its continuation lines too -- any indented,
# non-blank line following the first. The substrate hard-wraps its prose and
# lists at roughly 72 columns, so the day a fourth required section is added
# the name lands on a second physical line. A first-line-only read would drop
# it, and dropping it is invisible: the grouping table below would still match
# the three names that fitted, so the template would ship without a section
# the substrate had begun requiring, with every suite green.
REQUIREMENTS_SECTION_BULLET = re.compile(r"^- `requirements\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

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
    where that file's own contract is, once per file;
    `test_skill_frontmatter_conforms_and_its_citations_resolve` additionally walks
    the citation string back to a path, which is a check on what a reader follows
    rather than on the constant it was built from.
    """
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


# How the template must reach the substrate: by ${CLAUDE_PLUGIN_ROOT} path,
# which is the form a reader of the shipped plugin can resolve wherever it is
# installed.
ARTIFACT_FAMILY_CITATION = _plugin_root_citation(ARTIFACT_FAMILY)

# The substrate heading that owns the suite's unknown-marker token, the name a
# document citing the token refers to it by, and the pattern that lifts the
# token out of the fenced block beneath the heading.
#
# The name is derived from the heading rather than written out a second time,
# since the two would otherwise be free to drift while both tests stayed green.
UNKNOWN_MARKER_HEADING = "## Unknown marker"
UNKNOWN_MARKER_NAME = UNKNOWN_MARKER_HEADING.removeprefix("## ").lower()
FENCED_BLOCK = re.compile(r"```\n(.+?)\n```", re.DOTALL)

# Where each of this beat's six content sections sits in requirements.md: as an
# H3 under one of the three H2s the substrate publishes. The grouping is this
# skill's own decision -- the substrate pins the H2 names and their order and
# says nothing about what nests inside one -- so this table is that decision's
# definition rather than a copy of anything.
#
# The three parents are not interchangeable containers. `## Scope` holds what
# every requirement below it refers to: the system name each EARS clause names,
# and the opportunity set the requirements are answerable to. `## Requirements`
# holds the requirements themselves, split only by whether they constrain
# behaviour or a quality attribute, since both are written in the same notation.
# `## Out of scope` is the load-bearing one: it is where a deliberate gap gets
# recorded, so an opportunity nobody wrote a requirement for and a quality
# characteristic nobody thought about are both visible as omissions instead of
# being invisible by absence.
#
# It is keyed by the substrate's own names, and the test asserts the key set
# still matches what it reads there. Renaming a published section is then a
# re-grouping decision a person makes, not one this table absorbs in silence:
# an H3 grouped by what its parent heading means cannot be re-parented by
# position without someone deciding the new heading still means that.
NESTED_SECTIONS = {
    "Scope": ("The system name", "Opportunity coverage"),
    "Requirements": ("Functional requirements", "Non-functional requirements"),
    "Out of scope": (
        "Opportunities not addressed",
        "Quality characteristics not applicable",
    ),
}

# How the number part of an id is written where the template states the form,
# and therefore what separates a stated notation from the ids the rows carry.
ID_NUMBER_PLACEHOLDER = "<n>"
ID_FORM = f"REQ{ID_NUMBER_PLACEHOLDER}"

# The columns of the three tables a later reader is read *by* rather than merely
# reads: a downstream beat locates a requirement by these headers, and a
# reviewer answers the coverage question by them. Pinned as exact ordered
# tuples, not as a set of names to be found somewhere, because a renamed or
# reordered header is what breaks a reader while leaving the document looking
# well-formed.
#
# Keyed by the H3 section each table sits in, since the two requirement tables
# declare identical columns: markdown cannot inherit a header row, so the same
# five columns are written twice by necessity, and only the section tells them
# apart. That both entries name one tuple is the point -- functional and
# non-functional requirements are split by subject and share one notation, so a
# column added to one and not the other has forked the notation.
#
# The coverage section is named once here rather than spelled at each of the four
# places that reach for it, because the rubric reaches for it too: its
# traceability cluster is answered against that table, so the name is now shared
# between two shipped files rather than local to this one.
COVERAGE_SECTION = "Opportunity coverage"
REQUIREMENT_COLUMNS = ("ID", "Pattern", "Requirement", "Traces to", "Source")
DECLARED_TABLES = {
    COVERAGE_SECTION: ("Opportunity", "Covered by", "Note"),
    "Functional requirements": REQUIREMENT_COLUMNS,
    "Non-functional requirements": REQUIREMENT_COLUMNS,
}

# The literal a coverage row carries when no requirement answers its
# opportunity. It is checked because it is the whole of the backward
# traceability rule: with the literal, an unaddressed opportunity is a decision
# somebody recorded; without it, the cell goes blank and "nobody wrote a
# requirement" becomes indistinguishable from "nobody filled in the table".
NOT_ADDRESSED = "not addressed"

# The H2 that states the grammar every requirement is written in. It is not one
# of the substrate's three published sections and is not asserted against them:
# the notation is a rule the author writes *by*, not content requirements.md
# carries, so it sits above `## Scope` in the template and outside the nesting
# table above.
NOTATION_SECTION = "The EARS notation"

# The five EARS patterns, in the paper's own order -- the always-active case
# first, then the four that gate a response -- each paired with the keyword or
# keywords that licence it.
#
# The ubiquitous pattern's keyword is `None`, which is the entry a reader will
# take for an unfinished cell. It is not one. Ubiquitous is the one pattern the
# notation gives no keyword at all, because a requirement that is always active
# has nothing to gate it: the sentence is the system name, the modal and the
# response. The test reads `None` as "assert no keyword appears in this
# section", so filling it in with a plausible keyword would invert that
# assertion rather than tighten it. The absence is load-bearing beyond this
# tuple, too -- it is the reason the template mandates an uppercase
# subject-verb, since a ubiquitous requirement offers no keyword to be spotted
# by.
#
# This tuple and the ones below it are deliberate second copies of what the
# template ships, and the citation-over-copy rule in the docstring above does
# not reach them. That rule is about a fact another skill's contract publishes,
# which this module reads at run time precisely so the two cannot diverge; the
# template is the file under test, and an expectation read out of the file under
# test asserts nothing. The two are meant to be edited together.
EARS_PATTERNS: tuple[tuple[str, tuple[str, ...] | None], ...] = (
    ("Ubiquitous requirements", None),
    ("Event-driven requirements", ("WHEN",)),
    ("State-driven requirements", ("WHILE",)),
    ("Unwanted behaviour requirements", ("IF", "THEN")),
    ("Optional feature requirements", ("WHERE",)),
)

# Every keyword the notation defines, flattened out of the pairs above. Used
# twice: as what the ubiquitous section must contain none of, and as the
# vocabulary the composition rule is measured against.
EARS_KEYWORDS = tuple(keyword for _pattern, keywords in EARS_PATTERNS for keyword in keywords or ())

# The section that says how the five patterns combine. Asserted apart from
# EARS_PATTERNS because it is a rule over them and not a sixth pattern: it
# licences no keyword of its own, so the check on it is that it shows keywords
# from two different patterns rather than that it introduces one.
COMPLEX_SYNTAX_SECTION = "Complex requirement syntax"

# Every H3 the notation carries: one per pattern, plus the rule for combining
# them. Derived rather than restated, so a pattern added to EARS_PATTERNS is
# covered by the checks that range over all of them without a second edit.
NOTATION_SECTIONS = (*(pattern for pattern, _keywords in EARS_PATTERNS), COMPLEX_SYNTAX_SECTION)

# The notation's only modal verb, uppercase per the casing the template
# mandates. What it is for here is telling the two registers of a notation
# section apart. Every section prints its shape in a fenced block and then an
# instance of that shape in another, and the difference between them is whether
# any slot is left: `THE <system name> SHALL ...` is a grammar, and `THE CONTROL
# SYSTEM SHALL ...` is a worked example. The modal is what makes either one a
# requirement rather than a fragment, so a line carrying it plus a slot is the
# first, and a line carrying it and no slot is the second.
MODAL_VERB = "SHALL"
SLOT = "<"

# The note that makes the generic form more than a word order. Pinned as its own
# statement because the order is the one part of the form a reader will take for
# arbitrary, and an author who takes it for arbitrary will write a state clause
# after a trigger and change what the requirement says.
GENERIC_FORM_NOTE = "Clause order is significant"

# The claim that keeps one notation in the document instead of two: the rows of
# the non-functional table are ubiquitous requirements, not a second grammar
# invented for quality attributes. Asserted inside the ubiquitous section, which
# is the claim's home -- the pattern is what the reuse is *of*, so a statement
# filed anywhere else leaves an author reading that section with no reason to
# think it applies to them.
NON_FUNCTIONAL_REUSE = "Non-functional requirements are written in this pattern"

# The paper's generic form, which the template prints as the paper prints it --
# lowercase, both optional clauses ahead of the system name. Pinned as one
# literal rather than as its parts because the clause order *is* the content:
# preconditions precede the trigger because they gate it, and a form printed
# with the trigger first states a different rule while using the same words.
GENERIC_FORM = "<optional preconditions> <optional trigger> the <system name> shall <system response>"

# The H3 of the notation that owns the casing mandate. The three statements
# below are bounded to it rather than to the notation as a whole, which is what
# makes them more than a word count: a file mentioning `Kiro` in passing
# somewhere and mandating uppercase somewhere else has not attributed the
# mandate, and only co-location in one section a reader can be pointed at says
# where the rule came from.
CASING_SECTION = "Casing"

# What the casing rule has to say, and what each part of it is there for. Every
# one of these is a decision the file must carry in words rather than imply,
# because none of them follows from the notation's own sources -- the paper and
# its author both write sentence case, so an unattributed uppercase mandate
# reads as a transcription error to the next person who checks.
CASING_STATEMENTS = (
    (
        "THE SYSTEM SHALL",
        "the mandated casing carried through the subject-verb, not the keyword alone; "
        "keyword-only uppercase would leave a ubiquitous requirement unmarked",
    ),
    (
        "Kiro",
        "the shipped precedent the mandate follows, named so the choice is traceable "
        "to something rather than to nobody",
    ),
    (
        "sentence case",
        "what the notation's own author writes instead, so a reader who goes to the "
        "paper finds the divergence already accounted for",
    ),
)

# The H2 that enumerates the non-functional surface a member has to account for.
# Like the notation, it is not one of the substrate's three published sections
# and is not asserted against them: the checklist is a list an author works
# *through*, and what working through it produces is rows in the sections below,
# so it sits above `## Scope` and outside the nesting table.
CHECKLIST_SECTION = "The quality characteristic checklist"

# The nine quality characteristics of ISO/IEC 25010:2023, in the order the
# standard's product quality model presents them, each mapped to the
# subcharacteristics it is subdivided into.
#
# A deliberate second copy of what the template ships, for the reason
# EARS_PATTERNS gives above: the template is the reader-facing home of the list,
# and an expectation read out of the file under test asserts nothing. The two are
# meant to be edited together rather than deduplicated.
#
# The spellings are the standard's own, which is why `time behaviour` and
# `analysability` are British while `resource utilization` is not. They are
# matched case-insensitively against the template, since a gloss opening a line
# capitalises the name it glosses.
ISO_CHARACTERISTICS: dict[str, tuple[str, ...]] = {
    "Functional suitability": (
        "functional completeness",
        "functional correctness",
        "functional appropriateness",
    ),
    "Performance efficiency": ("time behaviour", "resource utilization", "capacity"),
    "Compatibility": ("co-existence", "interoperability"),
    "Interaction capability": (
        "appropriateness recognizability",
        "learnability",
        "operability",
        "user error protection",
        "user engagement",
        "inclusivity",
        "user assistance",
        "self-descriptiveness",
    ),
    "Reliability": ("faultlessness", "availability", "fault tolerance", "recoverability"),
    "Security": (
        "confidentiality",
        "integrity",
        "non-repudiation",
        "accountability",
        "authenticity",
        "resistance",
    ),
    "Maintainability": (
        "modularity",
        "reusability",
        "analysability",
        "modifiability",
        "testability",
    ),
    "Flexibility": ("adaptability", "installability", "replaceability", "scalability"),
    "Safety": (
        "operational constraint",
        "risk identification",
        "fail safe",
        "hazard warning",
        "safe integration",
    ),
}

# The count the standard states in its own clause 1 -- nine characteristics, each
# subdivided into subcharacteristics -- and the one fact about the model that was
# read off the primary text rather than corroborated from explainers.
#
# Asserted against the mapping above, which is otherwise the sole judge of its
# own completeness. An edit that drops a characteristic from the template and
# from the mapping together satisfies every comparison between the two, and this
# is the check that still fails: a checklist with a hole in it reads as a
# complete one, which is the whole reason the enumeration is pinned at all.
ISO_CHARACTERISTIC_COUNT = 9

# What answering one of the nine prompts resolves to, each paired with what the
# checklist loses without it.
#
# Asserted in the checklist's own intro rather than anywhere in the section,
# because the three are the same three for all nine characteristics: an author
# reads them once, before the first prompt, and a rule filed under one
# characteristic is a rule the other eight do not carry.
CHECKLIST_OUTCOMES = (
    (
        "Non-functional requirements",
        "where a characteristic that applies and has a threshold ends up",
    ),
    (
        "Quality characteristics not applicable",
        "where one that does not apply is recorded, together with the reason it does not",
    ),
    (
        UNKNOWN_MARKER_NAME,
        "what a characteristic that applies but whose threshold nobody has "
        "established takes, so an open question does not read as an exclusion",
    ),
)

# The rule that keeps the first outcome defensible. A figure nobody can
# attribute cannot be revised later on purpose, only argued about, so a
# threshold with no source is the first outcome with the part that makes it a
# requirement left off -- and the template has to say so, because it is the
# shortcut an author under time pressure reaches for.
THRESHOLD_SOURCE_RULE = "A threshold with no source"

# The rule that keeps the second outcome defensible, and the counterpart to the
# one above: an exclusion states something about this product that a reader
# could contest. Pinned because the failure it prevents is the one that looks
# most like success -- a characteristic marked inapplicable with no reason
# records a decision nobody made, and nine of those read as a checklist somebody
# worked through.
#
# The template's `### Quality characteristics not applicable` section states the
# rule a second time in its own words, and neither statement was pinned before
# this. This asserts the checklist's copy, which is the one an author reads while
# deciding, rather than the one they read while writing the row.
JUSTIFICATION_RULE = "justification a reader could disagree with"

# The disclosure that the subcharacteristic glosses are the template's own
# words. The standard's clause 4 definitions were not read while this file was
# written, so glosses presented as quotation would assert a precision nobody
# established, and a reader with a certification argument to make needs to know
# to go to the standard itself.
PARAPHRASE_DISCLOSURE = "paraphrase, not quotation"

# Safety's stricter rule, and the characteristic whose own section must carry
# it. Bounded to that section because it is an exception to the three outcomes
# rather than a restatement of them: no source found says when safety is
# inapplicable, and the commentary runs the other way, so safety is the one
# characteristic the marker cannot dismiss. Stated anywhere else, the exception
# reaches nobody reading the prompt it applies to.
SAFETY_CHARACTERISTIC = "Safety"
SAFETY_RULE = "takes a stated reason"

# The H2 that states the gate an author applies to a requirement already
# written. Like the notation and the checklist it sits above `## Scope` and
# outside the nesting table, and for a stronger reason than either: INVEST emits
# no part of requirements.md at all. It is a judgement about how a requirement
# will be delivered rather than a fact about the product, so what working
# through it produces is a rewritten requirement, not a row.
INVEST_SECTION = "The INVEST gate"

# Bill Wake's six criteria, in the order the mnemonic spells them. A deliberate
# second copy of what the template ships, for the reason EARS_PATTERNS gives
# above: the template is the reader-facing home of the list, and an expectation
# read out of the file under test asserts nothing.
INVEST_LETTERS = (
    "Independent",
    "Negotiable",
    "Valuable",
    "Estimable",
    "Small",
    "Testable",
)

# The mnemonic the six initials spell, asserted against the tuple above rather
# than against the template. It is the enumeration's own checksum, and it is the
# check that still fails when a letter is dropped from the template and from the
# tuple together -- an edit that satisfies every comparison between the two and
# leaves a five-part gate reading as a complete one. ISO_CHARACTERISTIC_COUNT
# guards the checklist the same way.
INVEST_ACRONYM = "INVEST"

# The floor on what counts as a gloss, in words on the letter's own bullet line.
# The failure this rules out is the mnemonic shipped as six bare names, which
# tells an author the gate has six parts and nothing about what any of them
# asks. Four words is low enough that no honest gloss trips it and high enough
# that a name followed by punctuation does.
INVEST_GLOSS_MIN_WORDS = 4

# The claim that makes the downstream citation safe, the beat that relies on it,
# and the rule it imposes. Epic constraint 3 puts one INVEST definition in the
# suite and this section is it, so a reader has to be able to see that a second
# copy is forbidden rather than merely absent -- absent reads as an opening.
SINGLE_DEFINITION_CLAIM = "the suite's single INVEST definition"
CITING_BEAT = "#21"
CITE_NOT_COPY_RULE = "rather than copying it"

# What the gate applies to, and what happens to a requirement it does not apply
# to. Issue #18 asked for the gate without defining story-shaped, so the term,
# its definition and the exemption are all this file's own -- which is exactly
# why they are pinned: a gate whose scope nobody wrote down gets applied to
# everything by the next author, and a latency threshold judged against Small
# fails a test it was never in.
STORY_SHAPED_TERM = "story-shaped"
STORY_SHAPED_DEFINITION = "one deliverable unit"
STORY_SHAPED_EXEMPTION = "exempt from the gate rather than failing it"

# The source the criteria come from. Pinned because provenance is what a single
# definition is checkable against: a reader who thinks a gloss is wrong needs
# somewhere to go, and the six criteria are a 2003 article by a named author
# rather than folklore.
INVEST_SOURCE = "Wake"

# The H2 spine of the rubric, and the two of its sections the checks below reach
# into by name: the one that has to establish where the clusters came from, and
# the one a review fleet fans out over.
#
# `test_product_brief_contract.py` and `test_product_discovery_contract.py` state
# the same spine for their own rubrics, and this is its third statement. No file
# publishes the spine for a test to read, so each rubric test asserts its own
# file against its own copy, and a spine change is an edit to all three at once.
# The honest fix is the shared harness the heading helpers below are already
# headed for; this copy is knowing, not accidental.
ATTRIBUTION_SECTION = "Attribution and scope"
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    ATTRIBUTION_SECTION,
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

# How wide the review fleet fans out over this beat's output. `product-review`
# launches one finder per H3 cluster under the red-flags section, so the count is
# part of what the rubric publishes rather than a matter of taste.
#
# Five, where both shipped siblings pin four. The fifth cluster is the one that
# puts a finder on broken traceability -- a requirement answering no opportunity,
# or an opportunity that quietly produced none -- and that is the single failure
# this beat exists to prevent. At four, the beat's own invariant would be the one
# thing no reviewer was asked about.
RED_FLAG_CLUSTER_COUNT = 5

# What every question in a cluster carries besides its question mark. A reviewer
# routes a finding by this word, so a cluster written without one yields findings
# nobody can triage as material or minor.
SEVERITY_HINT = "Severity hint:"

# Each cluster of the rubric, in document order, and the problems from the EARS
# paper's own section 2 taxonomy that it derives from.
#
# The mapping is what makes these clusters cited rather than invented, and it is
# pinned at both ends: the keys are the cluster names a fleet fans out over, and
# each value is what that cluster's own body has to name. A cluster that stops
# naming its problem has its grounding recorded only here -- and a critic handed
# one cluster never sees this file.
#
# Two names keep an "and", against the siblings' habit of one concept per
# cluster, because each genuinely folds two of the paper's problems and a
# one-word name would misstate the cluster's reach. Compound requirements is the
# exception that shows the rule: the paper describes its complexity problem as
# compound requirements containing complex sub-clauses, so one of its own terms
# already covers both and the shorter name wins.
CLUSTER_DERIVATIONS: dict[str, tuple[str, ...]] = {
    "Ambiguity and vagueness": ("ambiguity", "vagueness"),
    "Compound requirements": ("complexity",),
    "Unverifiable requirements": ("untestability",),
    "Smuggled implementation": ("inappropriate implementation",),
    "Omission and duplication": ("omission", "duplication"),
}

# The size of the paper's taxonomy, and the one problem in it that no cluster
# above carries.
#
# The count is asserted against the mapping, which is otherwise the only judge of
# its own completeness: seven problems clustered plus one declared unclustered is
# the paper's eight, and a problem dropped from both the mapping and the rubric
# would satisfy every comparison between them while leaving the rubric quietly
# narrower than the source it claims. INVEST_ACRONYM and ISO_CHARACTERISTIC_COUNT
# guard their enumerations the same way.
#
# Wordiness is the omission, and it is a decision rather than an oversight: a
# wordy requirement is still one testable sentence, so no question here would be
# answerable yes/no about it. That is exactly why the rubric has to name it --
# unnamed, seven of eight reads as a taxonomy somebody transcribed carelessly.
PAPER_PROBLEM_COUNT = 8
UNCLUSTERED_PROBLEM = "wordiness"

# What the attribution section has to establish about the taxonomy's source: its
# lead author, the venue that published it, and the disclaimer both sibling
# rubrics carry. Grounding is this rubric's whole claim over the invented
# clusters it replaced, so a file that stops naming the paper is one whose
# clusters a reader has no reason to prefer to any other five.
PAPER_ATTRIBUTION = ("Mavin", "RE'09", "not affiliated")

# The design rubric this file defers to instead of growing questions of its own
# about names and comments, and the two of its clusters that own them. Issue #18
# asked for the deferral by name.
#
# The two names are checked against that file's own headings rather than trusted,
# because a citation naming a cluster it no longer has is worse than no citation
# at all: it sends a reader somewhere specific and wrong.
DESIGN_PRINCIPLES = REPO_ROOT / "skills" / "design-review" / "references" / "design-principles.md"
DEFERRED_DESIGN_CLUSTERS = ("Naming", "Comments and obviousness")

# How the rubric must reach its two neighbours and the design rubric above: by
# ${CLAUDE_PLUGIN_ROOT} path, for the reason ARTIFACT_FAMILY_CITATION gives.
DESIGN_PRINCIPLES_CITATION = _plugin_root_citation(DESIGN_PRINCIPLES)
REQUIREMENTS_TEMPLATE_CITATION = _plugin_root_citation(REQUIREMENTS_TEMPLATE)

# The cluster whose questions are answered against a table rather than against a
# sentence. The other four judge a requirement the reviewer is looking at; this
# one judges what is *absent*, which is only checkable because the template
# carries a row per opportunity and a literal for the uncovered ones. Named here
# so the check can be bounded to that cluster: the coverage table mentioned
# anywhere else in the rubric leaves the questions that need it unanchored.
TRACEABILITY_CLUSTER = "Omission and duplication"

# The rules a run has to follow that nothing can check once the run is over, each
# paired with the literal `SKILL.md` must carry for the rule to exist at all. A
# finished `requirements.md` records what the rules produced and never which of
# them were followed: it cannot show that the freshness state was asked for rather
# than guessed, or that the provenance line was read rather than assembled, since
# a guessed state and a read one leave the same document behind. Publishing the
# rule in the body is therefore the whole of its enforcement, and this test is the
# only thing that can be checked about it.
#
# Mirrors the constant of the same name in both shipped sibling contracts, and its
# first four rows are the same substrate rules theirs carry, because the substrate
# is the same one. They are stated here rather than imported: a sibling's tuple is
# that sibling's account of its own body, and a shared one would let a rule this
# beat never states pass on a sentence another beat wrote.
RUNTIME_RULES = (
    (
        "whether the upstream is there is answered by the substrate, not by a local stat",
        "--check-freshness",
    ),
    (
        "the slug folder is never created locally, only through the substrate's one writing entry point",
        "--ensure-folder",
    ),
    (
        "the provenance line is read off the substrate rather than assembled here",
        "--provenance-line",
    ),
    (
        "the line is asked for by member name, so the sha it carries is over this "
        "member's own upstream and not some other member's",
        "--member requirements.md",
    ),
    (
        "the upstream is never edited, so the sha just written into this member stays true",
        "Never write to discovery.md",
    ),
)

# The step that owns the refusals, the three upstream states each one fires on, and
# the beat every refusal has to name.
#
# Bounded to that step, and the step pinned to the top of the body, because none of
# this survives being stated elsewhere. A gate that is not the first thing a run
# reaches is not a gate, and each of these tokens is a word the file has good reason
# to use again later -- `OPP` wherever traceability is discussed, `product-discovery`
# wherever the upstream's owner comes up. Searched across the whole body, a row here
# would go on passing after the refusal it pins had been deleted, which is the one
# way this test could report a published gate that no longer exists.
#
# The order is the part no presence check reaches, and it is not cosmetic. `absent`
# is tried first because a file that is not there has no provenance line to resolve;
# `unresolvable` before the id read because a tree read out of a file of unknown
# ancestry answers nothing. A run that tries them in another order names the wrong
# one of the three as why it stopped, and its user re-runs against the wrong
# complaint.
REFUSAL_SECTION = "Step 1: Refuse unless discovery conforms"
REFUSAL_BEAT = "product-discovery"
REFUSALS = (
    (
        "the upstream file is not there at all, which is a state the substrate reports "
        "and not one a local stat should discover",
        "absent",
    ),
    (
        "the upstream is present but nobody can say which brief it came from, so the sha "
        "this member would record is over bytes of unknown ancestry",
        "unresolvable",
    ),
    (
        "the upstream carries no opportunity id, so every requirement written from it "
        "would be untraceable by construction",
        "OPP",
    ),
)

# The section that publishes what a second run does, and the rows it has to carry.
#
# Bounded to the section rather than searched for across the body, which the rules
# above are not. Every other rule here is one a run follows and a reader may never
# need; this one is read *by* the next author and by anyone holding a `REQ` id, so
# where it is stated is part of the rule. The same four sentences scattered through
# the steps would leave a reader who opened `## Re-run behaviour` -- the heading
# every other beat in this suite publishes the same promise under -- with nothing.
#
# The last two rows are the rule's reason rather than the rule, and they are
# asserted with the same weight for a reason the four above do not need: a renumber
# is invisible. The freshness mechanism compares the upstream's content and never
# looks at a downstream id, so no script, test or later beat will ever report one,
# and review is the only enforcement the rule has. A reader who does not know that
# reads id preservation as bookkeeping they are free to tidy.
RERUN_SECTION = "Re-run behaviour"
RERUN_RULES = (
    (
        "a requirement that survives keeps the number it was already cited by",
        "keeps the number it already has",
    ),
    (
        "a new requirement is numbered from the high-water mark rather than from the "
        "count, which is what keeps a deletion from freeing a number",
        "the next number after the highest",
    ),
    (
        "a deleted requirement is moved rather than dropped, so that dropping it reads "
        "as a decision somebody made",
        "## Out of scope",
    ),
    (
        "a retired number is never handed to a different requirement",
        "never reused",
    ),
    (
        "the ids are a downstream citation target, which is why their stability is a "
        "rule and not a preference",
        "cited by the beats downstream",
    ),
    (
        "no mechanism in the chain will ever report a renumber, so a review is the whole "
        "of this rule's enforcement",
        "never inspects a downstream identifier",
    ),
)

# Every file the body sends a run to, each paired with what the run loses when the
# citation stops resolving. A body that names its references cannot be caught
# working from a remembered version of one, and nothing downstream can tell the
# difference either, so the citation being both present and followable is the whole
# enforcement.
#
# Mirrors the constant of the same name in both shipped sibling contracts, which
# pin their own template and rubric this way. Two rows go beyond theirs, and
# neither has a sibling equivalent. The substrate contract is cited because this
# member's section names, its provenance rules and the marker literal are all
# published there rather than here. The script is cited because it is not a
# document at all: the two commands the body prints are the whole of how a run
# learns the freshness state and the provenance line, so a run that cannot reach
# the script has nothing left but the local stat and the assembled sha that
# RUNTIME_RULES above forbids.
SUBSTRATE_SCRIPT = SKILL_ROOT.parent / "product-artifacts" / "scripts" / "product_artifact.py"
CITED_REFERENCES = (
    (
        "the member's shape and the grammar of a requirement are read from the template, not recalled",
        REQUIREMENTS_TEMPLATE,
    ),
    (
        "the judgement rules are read from the rubric, not recalled",
        REQUIREMENTS_PRINCIPLES,
    ),
    (
        "the section names, the provenance rules and the marker literal are read from "
        "the substrate contract, not recalled",
        ARTIFACT_FAMILY,
    ),
    (
        "the freshness state and the provenance line are asked of the substrate's one "
        "script rather than derived here",
        SUBSTRATE_SCRIPT,
    ),
)

# The frontmatter keys this skill must not declare, each with what declaring it
# would take away. None of the three is about the rules the body states; all three
# are about whether a session ever gets to follow them.
#
# Mirrors the sibling contracts' constant of the same name, with `disallowed-tools`
# added as a third row. The siblings forbid the allowlist alone, and a denylist
# reaches the same outcome from the other direction -- `product-review` and
# `product-status` both ship one, so it is a field an author working in this suite
# is already in the habit of writing.
FORBIDDEN_FRONTMATTER_KEYS = (
    (
        "disable-model-invocation",
        "it is the documented way to drop a skill from the model-facing listing, "
        "leaving it reachable only by someone who types its name -- and this beat is "
        "meant to be reached from a discovery the user is already talking about",
    ),
    (
        "allowed-tools",
        "an allowlist strips the ambient tools the body's own steps call: the freshness "
        "check, the provenance line, the `AskUserQuestion` prompts and the write itself "
        "would each fail on a tool the frontmatter had narrowed away",
    ),
    (
        "disallowed-tools",
        "a denylist arrives at the same place from the other direction, and the two "
        "tools a read-only sibling denies first are the two this beat cannot lose: it "
        "needs `Bash` for the substrate script and `Write` for the member itself",
    ),
)

# The keys the frontmatter must declare, each with what the skill loses without it.
# The counterpart to the tuple above, and this file's own rather than a sibling's:
# the forbidden keys say what must not be there, and a file declaring none of them
# and nothing else satisfies that loop completely while reaching nobody.
#
# `description` is deliberately not a row. `tests/test_description_budget.py`
# already fails on a skill whose description carries no text, over the same glob
# that owns its length and its opening token, so a row here would report one
# omission as two failures.
REQUIRED_FRONTMATTER_KEYS = (
    (
        "name",
        "it is what the slash command is typed as, and every beat in this suite "
        "declares its own rather than leaving the harness to infer one from a "
        "directory that may be installed under another",
    ),
    (
        "argument-hint",
        "the slug is the one argument this beat cannot guess, since it names a folder "
        "somebody else made -- a user shown no hint is the user step 1 has to stop and "
        "ask, which is a round trip the hint would have saved",
    ),
)


def _headings(markdown: str) -> list[tuple[int, str, int]]:
    """Every ATX heading in `markdown` as (level, text, line number).

    Lines inside a fenced code block are skipped: a reference file that shows
    a heading as an example would otherwise report that example as one of its
    own sections, which is the difference between reading a document's shape
    and reading the shape it is describing.

    Whole-line matching is what separates a heading from one demoted a level:
    `## Requirements` is a substring of `### Requirements`, so a substring
    search would report a top-level section in a document that had demoted it
    under some other parent -- the exact corruption these tests exist to catch.
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
    scale.

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
    call site as a missing subheading.

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


def _table_cells(row: str) -> list[str]:
    """The cells of one markdown table row, unpadded and with backticks dropped.

    Dropping backticks makes code-spanning a column name a formatting choice
    rather than a renamed column.
    """
    return [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]


def _table(body: list[str]) -> list[list[str]]:
    """The first markdown table in `body`, as one cell list per row.

    The header row comes first, with the `|---|` alignment row dropped, and an
    empty list comes back when `body` holds no table at all.

    Header and rows come back together because the two questions asked of a
    table here cannot be separated. Which columns it declares is answered by the
    header; whether the ids beneath them are written in the notation the
    document states is answered only by the rows. A helper returning the header
    alone would leave the second question to the surrounding prose, and a
    document can describe a notation its own rows do not use.

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
        cells = _table_cells(line)
        if rows and set("".join(cells)) <= set("-:"):
            continue
        rows.append(cells)
    return rows


def _requirements_section_names(substrate: str) -> list[str]:
    """requirements.md's required H2 names, in document order, from the substrate.

    Returns the bare names without their `## ` marker, since callers compare
    them against parsed heading text rather than against raw lines, and an
    empty list when the bullet has moved out from under the pattern -- which
    callers must guard, since every comparison against it would then be
    vacuous rather than failing.
    """
    bullet = REQUIREMENTS_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _unknown_marker_prefix(substrate: str) -> str:
    """The marker token up to and including its colon, read from the substrate.

    Read rather than restated for the same reason the template must cite it: a
    second copy of the token in this file would keep passing after the definition
    moved on, and the assertion it guards would quietly test a literal nobody
    writes any more.

    The prefix rather than the whole literal is what a document carrying the
    marker actually shows, since the payload after the colon is written per slot.
    It is also what catches a partial restatement: a file carrying the token's
    opening and its own payload text has forked the token however little of it
    was copied.

    Returns "" when the definition cannot be read, which callers must guard -- a
    prefix derived from nothing would be a bare colon, and every document
    contains one.
    """
    after_heading = substrate[substrate.index(UNKNOWN_MARKER_HEADING) :]
    block = FENCED_BLOCK.search(after_heading)
    if block is None:
        return ""
    token, separator, _payload = block.group(1).strip().partition(":")
    return token + separator if separator else ""


def _unwrapped(lines: list[str]) -> str:
    """`lines` as one string with every run of whitespace collapsed to a space.

    Used only where a check is for a phrase the file must state. This file's
    prose is hard-wrapped at roughly 76 columns, so any phrase of more than one
    word sits on two physical lines about a third of the time, and a raw
    substring search would then fail on a re-wrap that changed no words. That
    failure would be a false one -- it reports a missing statement where the
    statement is present -- and the cure for it is worse than the disease, since
    an author who hit it would learn to keep phrases the tests look for on one
    line rather than to write the file well.

    Not used for structure. Headings and table rows are line-oriented, and
    flattening them would destroy the thing being read.
    """
    return " ".join("\n".join(lines).split())


def _fenced_lines(body: list[str]) -> list[str]:
    """The lines inside `body`'s fenced code blocks, the fences themselves dropped.

    A notation section says things in two registers, and only one of them is
    normative. Its prose explains a pattern; its fenced blocks carry the shape an
    author copies. Prose survives an edit that deleted the shape it describes, so
    the checks on shape read the fenced lines and ignore everything else.
    """
    fenced: list[str] = []
    inside_fence = False
    for line in body:
        if line.startswith("```"):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            fenced.append(line)
    return fenced


def _glossed_bullets(body: list[str]) -> dict[str, list[str]]:
    """The `- <name> -- <gloss>` bullets in `body`, as lowercased name to glosses.

    Reads the shape this template glosses a term with everywhere it glosses one:
    a list item naming the term, a `--`, and what the term means. Matching on
    that shape rather than searching the section for the term is what separates a
    term being *defined* from the same word appearing in the surrounding prose --
    and the prose around a list of criteria names them constantly.

    Only the gloss text on the term's own line comes back. The file hard-wraps at
    roughly 76 columns, so a full gloss usually continues onto the next line, and
    the question this answers is whether the line naming the term also says what
    it means; a bare name with its meaning somewhere below reads as a heading.

    The name comes back stripped of the `*` that emphasises it, for the reason
    `_table_cells` drops backticks: this template writes a glossed term bold in
    one section and italic in another -- `- **Independent** --` against
    `- *Functional completeness* --` -- so emphasis is a formatting choice per
    section, and keeping it would make every caller spell the markup its own
    section happens to use.

    A list of glosses per name, not one gloss, because a term glossed twice is
    itself something a caller reports: two definitions of one criterion is the
    fork the single-definition rule exists to prevent, and a mapping that kept
    the last would hide it.
    """
    bullets: dict[str, list[str]] = {}
    for line in body:
        item = line.strip()
        if not item.startswith("- "):
            continue
        name, separator, gloss = item.removeprefix("- ").partition(" -- ")
        if not separator:
            continue
        bullets.setdefault(name.strip().strip("*").lower(), []).append(gloss.strip())
    return bullets


def _acting_body(skill: str) -> str:
    """The half of `SKILL.md` a run acts from: everything after the frontmatter.

    Both halves of the file reach the model, at different moments and under
    different budgets. The frontmatter's description is what the router weighs
    while choosing a skill and is rationed in characters; the body is what the
    model has in front of it while working. A rule that appears only in the
    description is a rule nobody acts on, so it must not satisfy a check that a
    rule was published.

    Three cases, and the first is where this parts company with the `_skill_body`
    of the sibling contracts. A file with no `---` block at all yields its whole
    text, where theirs yields "" for the caller to fail on: whether this file
    declares frontmatter, and what it declares, is
    `test_skill_frontmatter_conforms_and_its_citations_resolve`'s claim, and
    failing here would report an unpublished rule where the rule is present and
    something else entirely is wrong. A well-formed block yields what follows it.
    A block that opens and never closes yields "", which the caller must guard,
    because the alternative is the one permissive answer of the three -- a file
    whose every line the harness reads as frontmatter would otherwise satisfy
    every rule below from text no run ever acts on.
    """
    if not skill.startswith("---"):
        return skill
    end = skill.find("\n---", 3)
    return "" if end == -1 else skill[end + len("\n---") :]


def _require_h2_span(template: str, section: str, purpose: str) -> tuple[int, int]:
    """Where one H2 of the template starts and stops owning it, or a failure.

    Named for the assertion rather than for the return value, because it makes one
    before returning: the tests of a section read only inside the span it hands
    back, and a template that had lost the section entirely would make each of
    those reads come back empty rather than fail. That is the one failure mode
    worth asserting on the way past -- a template that dropped a whole framework
    would otherwise report as a template whose framework mentions nothing.

    `purpose` completes the sentence "it is ..." in the failure message, so a
    report names what the missing section was for and not only its heading. It is
    a parameter rather than derived from `section` because what a section is for
    is exactly the part no heading states.

    Exactly once, not at least once. A heading carried twice is a section somebody
    copied, and `_section_span` would then span the first quietly.

    The three callers below are what this exists for: each supplies a section this
    template owns and the sentence that says why that section is load-bearing.
    Their bodies were identical before this helper, which put the H2-count rule in
    three places and made a change to it a three-file edit in one file.
    """
    headings = _headings(template)
    h2_names = [text for text, _ in _at_level(headings, 2)]
    assert h2_names.count(section) == 1, (
        f"expected '## {section}' to appear exactly once as an H2 in "
        f"{REQUIREMENTS_TEMPLATE.name}, found {h2_names.count(section)}; it is "
        f"{purpose}, and the template has {h2_names}"
    )
    return _section_span(headings, 2, section, len(template.splitlines()))


def _require_notation_span(template: str) -> tuple[int, int]:
    """Where `## The EARS notation` starts and stops owning the template.

    Bounding by the section matters for what the notation tests claim. A keyword
    or a casing rule that appears somewhere else in the file -- inside a worked
    requirement row, say -- is the notation being *used*, not the notation being
    stated, and only the latter tells the next author what to write.
    """
    return _require_h2_span(
        template,
        NOTATION_SECTION,
        "where the grammar every requirement is written in is stated",
    )


def _require_checklist_span(template: str) -> tuple[int, int]:
    """Where `## The quality characteristic checklist` starts and stops.

    Bounding by the section is what separates the checklist from the member
    sections below it. A characteristic named in a worked `## Out of scope` row is
    the checklist being *answered*; only a prompt inside this section asks the
    question that produced the answer.
    """
    return _require_h2_span(
        template,
        CHECKLIST_SECTION,
        "where the non-functional surface is enumerated so that it is something a "
        "reader can check rather than whatever the author thought of",
    )


def _require_invest_span(template: str) -> tuple[int, int]:
    """Where `## The INVEST gate` starts and stops owning the template.

    Bounding by the section is what makes the single-definition claim checkable at
    all. The claim is that INVEST is written out here and nowhere else, so a
    criterion glossed in some other section of this file is not the definition
    being cited -- it is the second copy the claim forbids.
    """
    return _require_h2_span(
        template,
        INVEST_SECTION,
        f"{SINGLE_DEFINITION_CLAIM}, which issue {CITING_BEAT} cites instead of carrying its own",
    )


def _cluster_spans(principles: str) -> list[tuple[str, tuple[int, int]]]:
    """Each red-flag cluster of the rubric, as its name and the span it owns.

    Bounded twice over, and both bounds carry weight. The clusters are the H3s
    that fall *inside* the red-flags H2, which is what proves nesting: an H3
    after that section's end is one no reviewer is ever handed, and searching the
    whole file would count it. Each cluster then stops where the next one begins,
    and the last stops where the section does, so a question or a severity hint
    is credited to the cluster whose critic would actually receive it.

    The span is in `_section_span`'s currency -- the heading's own line and the
    line that ends the section -- so callers hand it straight to
    `_section_body`.

    A list of pairs rather than a mapping, for the reason `_at_level` returns a
    list: a rubric carrying one cluster name twice is something a caller
    reports, and a mapping would keep the last and hide it.

    Comes back empty when the red-flags section is missing, and when it is
    present but holds no cluster. The two are not told apart because they cost a
    caller the same thing -- a fleet with no finder to launch -- and every caller
    must still report it themselves, since an empty list compared against a count
    or a name list is what turns "the rubric has no clusters" into a legible
    failure rather than an exception.
    """
    headings = _headings(principles)
    section_start, section_end = _section_span(headings, 2, RED_FLAGS_SECTION, len(principles.splitlines()))
    clusters = [(text, line) for text, line in _at_level(headings, 3) if section_start < line < section_end]
    # Returned before the stops are built, because the two lists are only the
    # same length once a first cluster exists: `stops` always ends with the
    # section's own end, so zipping it against no clusters raises rather than
    # yielding nothing, and a caller expecting the empty list promised above
    # would get a strict-zip traceback where its own assertion message belongs.
    if not clusters:
        return []
    stops = [line for _name, line in clusters[1:]] + [section_end]
    return [(name, (start, stop)) for (name, start), stop in zip(clusters, stops, strict=True)]


def _guarantees() -> ModuleType:
    """Load the repo-level tests/guarantees.py by path, for its frontmatter parser.

    This repository has one definition of what a top-level frontmatter key is, and
    the harness's listing rule -- which keys off exactly the keys asserted below --
    is written against it. A second parser here would eventually disagree with that
    one about which keys a file declares, and the disagreement would be silent in
    the permissive direction: this test would report the skill as listed after the
    listing had already dropped it.

    Loaded inside the test rather than at import, so this module still runs as a
    standalone script where the repo-level tests/ directory is absent; only the one
    test that needs it fails.
    """
    source = REPO_ROOT / "tests" / "guarantees.py"
    spec = importlib.util.spec_from_file_location("guarantees", source)
    assert spec and spec.loader, f"cannot load {source}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_prompts_every_iso_25010_characteristic() -> None:
    """All nine characteristics are prompts, each glossing its subcharacteristics.

    The enumeration is the whole value of the checklist, so it is pinned at three
    depths at once. A short list is the obvious failure. A list of nine bare names
    is the likelier one: it looks complete and leaves an author with nothing to
    answer, which is why every subcharacteristic must be glossed inside its own
    characteristic's section and why each section must ask something. And a list
    of nine in some other order is a checklist a reader cannot reconcile with the
    standard they are holding.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    checklist_start, checklist_end = _require_checklist_span(template)

    assert len(ISO_CHARACTERISTICS) == ISO_CHARACTERISTIC_COUNT, (
        f"ISO_CHARACTERISTICS carries {len(ISO_CHARACTERISTICS)} characteristics, not the "
        f"{ISO_CHARACTERISTIC_COUNT} the standard's clause 1 states the product quality "
        f"model has: {list(ISO_CHARACTERISTICS)}. A characteristic dropped from this "
        f"mapping and from the template together passes every comparison between the "
        f"two, and a checklist with a hole in it reads as a complete one"
    )

    # One prompt per characteristic, in the standard's order. Asserted as one
    # equality rather than as a membership check plus a count, because the three
    # ways this list can be wrong -- a missing characteristic, an extra one, a
    # reordering -- are one comparison and three separate searches.
    prompts = [
        (text, line) for text, line in _at_level(headings, 3) if checklist_start < line < checklist_end
    ]
    assert [text for text, _line in prompts] == list(ISO_CHARACTERISTICS), (
        f"'## {CHECKLIST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} prompts "
        f"{[text for text, _line in prompts]}, not {list(ISO_CHARACTERISTICS)}. The nine "
        f"are the standard's own set in the standard's own order, so a reader holding "
        f"ISO/IEC 25010:2023 can check the checklist against it"
    )

    for name, subcharacteristics in ISO_CHARACTERISTICS.items():
        body = _unwrapped(_section_body(lines, _section_span(headings, 3, name, len(lines)))).lower()
        missing = [sub for sub in subcharacteristics if sub.lower() not in body]
        assert not missing, (
            f"'### {name}' of {REQUIREMENTS_TEMPLATE.name} glosses none of {missing}, "
            f"which the standard subdivides it into. The subcharacteristics are what "
            f"make a characteristic answerable: a section carrying the name alone tells "
            f"an author that quality attribute exists and nothing about what to ask of it"
        )
        assert "?" in body, (
            f"'### {name}' of {REQUIREMENTS_TEMPLATE.name} asks no question. Every "
            f"characteristic is a prompt a reader answers, and a heading followed by "
            f"description is something a reader agrees with and moves past"
        )

    # The third outcome is cited, not copied. One definition of the marker exists
    # and it lives in the substrate; a template restating the token carries a
    # second copy free to drift, while a citation cannot drift because there is
    # nothing local to change.
    marker_prefix = _unknown_marker_prefix(ARTIFACT_FAMILY.read_text())
    assert marker_prefix, (
        f"could not read the unknown-marker literal out of {ARTIFACT_FAMILY.name}; "
        f"expected a fenced block under {UNKNOWN_MARKER_HEADING!r}"
    )
    checklist = _unwrapped(_section_body(lines, (checklist_start, checklist_end)))
    assert marker_prefix not in checklist, (
        f"'## {CHECKLIST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} restates the unknown "
        f"marker ({marker_prefix!r}); it must cite {ARTIFACT_FAMILY_CITATION} for the "
        f"token instead of carrying a copy that can drift from the definition"
    )
    assert ARTIFACT_FAMILY_CITATION in checklist, (
        f"'## {CHECKLIST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} names the unknown "
        f"marker as one outcome without citing {ARTIFACT_FAMILY_CITATION}, where the "
        f"token and its payload rules are defined. An author told to write a marker and "
        f"not told where it is defined will reconstruct one from memory"
    )


def test_template_resolves_each_characteristic_to_one_of_three_outcomes() -> None:
    """Every prompt has exactly three answers, and none of them is silence.

    Separate from the enumeration test, which answers whether all nine questions
    get asked. This answers what asking them is for: a characteristic an author
    read, thought about and left alone is indistinguishable from one nobody
    reached, and the three outcomes are what tell those apart. The threshold rule
    and safety's exception are asserted here too, because both are ways of
    resolving a prompt that look like an answer and are not.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    checklist_start, checklist_end = _require_checklist_span(template)

    # The intro is what precedes the first prompt, which is where a rule common to
    # all nine has to sit. Clamped to the end of the checklist because a template
    # that lost its first characteristic reports an empty span here; that failure
    # belongs to the enumeration test, and without the clamp it would surface as
    # rules found under the member sections below.
    first_prompt, _end = _section_span(headings, 3, next(iter(ISO_CHARACTERISTICS)), len(lines))
    intro = _unwrapped(_section_body(lines, (checklist_start, min(first_prompt, checklist_end))))

    for outcome, why in CHECKLIST_OUTCOMES:
        assert outcome.lower() in intro.lower(), (
            f"'## {CHECKLIST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} does not name "
            f"{outcome!r} ahead of its first prompt, which is {why}. With one of the three "
            f"outcomes unstated, the characteristics it would have caught leave no trace "
            f"in the member at all"
        )

    assert THRESHOLD_SOURCE_RULE in intro, (
        f"'## {CHECKLIST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} never states "
        f"{THRESHOLD_SOURCE_RULE!r}. It is the fourth outcome an author invents under time "
        f"pressure -- a figure that looks like a requirement and that nobody can revise on "
        f"purpose, because nobody can say where it came from"
    )
    assert JUSTIFICATION_RULE in intro, (
        f"'## {CHECKLIST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} offers the exclusion "
        f"outcome without requiring a {JUSTIFICATION_RULE!r}. An exclusion with no reason "
        f"records a decision nobody made while reading as one somebody did, which is the "
        f"hole this checklist exists to keep out of the member"
    )
    assert PARAPHRASE_DISCLOSURE in intro, (
        f"'## {CHECKLIST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} never states that its "
        f"subcharacteristic glosses are {PARAPHRASE_DISCLOSURE!r}. The standard's own "
        f"definitions were not read while this file was written, so a gloss a reader takes "
        f"for the standard's wording asserts a precision nobody established"
    )

    safety = _unwrapped(_section_body(lines, _section_span(headings, 3, SAFETY_CHARACTERISTIC, len(lines))))
    assert SAFETY_RULE in safety, (
        f"'### {SAFETY_CHARACTERISTIC}' of {REQUIREMENTS_TEMPLATE.name} never states that "
        f"declaring it out of scope {SAFETY_RULE!r}. No source says when safety is "
        f"inapplicable and the commentary runs the other way, so safety is the one "
        f"characteristic the unknown marker cannot dismiss -- and an exception stated "
        f"anywhere but here reaches nobody reading the prompt it applies to"
    )


def test_template_publishes_the_invest_gate_as_the_single_definition() -> None:
    """All six criteria are glossed, attributed, and claimed as the one definition.

    Epic constraint 3 puts one INVEST definition in the suite, so the
    story-slicing beat cites this section rather than restating it. That is what
    makes the enumeration worth pinning: a letter missing here is a letter
    missing from every beat downstream, and a section that never claims the
    definition invites the next author to write a second copy in good faith.

    Six bare names is a likelier failure than five names. It looks like the
    mnemonic, it reads as complete, and it leaves an author knowing the gate has
    six parts and nothing about what any part asks of a requirement.

    What the gate applies to is the next test's, and the ISO checklist is the two
    tests above's. All three frameworks are asserted separately so that a failure
    names which one is at fault rather than reporting that the template's rules
    are wrong somewhere.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    gate = _section_body(lines, _require_invest_span(template))

    # The framing paragraph is everything above the first H2, and it is where the
    # file explains its own shape: which sections sit above `## Scope` and what
    # they are for. A gate the file never announces there is a section a reader
    # meets by scrolling into it, which is how the third framework stays
    # invisible to anyone who read the opening and stopped. Indexing is safe only
    # because `_require_invest_span` above has already proved an H2 exists.
    first_h2 = _at_level(_headings(template), 2)[0][1]
    framing = _unwrapped(lines[: first_h2 - 1])
    assert f"`## {INVEST_SECTION}`" in framing, (
        f"the opening of {REQUIREMENTS_TEMPLATE.name} does not name "
        f"'## {INVEST_SECTION}' among the sections above '## Scope'. That paragraph is "
        f"the file's account of its own shape, and a framework it omits is one an "
        f"author who read the opening does not know they are answerable to"
    )

    initials = "".join(letter[0] for letter in INVEST_LETTERS)
    assert initials == INVEST_ACRONYM, (
        f"INVEST_LETTERS spells {initials!r}, not {INVEST_ACRONYM!r}: {list(INVEST_LETTERS)}. "
        f"A criterion dropped from this tuple and from the template together passes every "
        f"comparison between the two, and a five-part gate reads as a complete one"
    )

    glosses = _glossed_bullets(gate)
    for letter in INVEST_LETTERS:
        found = glosses.get(letter.lower(), [])
        assert len(found) == 1, (
            f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} defines {letter!r} "
            f"{len(found)} times; expected exactly one bullet of the form "
            f"`- **{letter}** -- <what it asks>`. The section defines "
            f"{sorted(glosses)}, and this is {SINGLE_DEFINITION_CLAIM}: a criterion "
            f"missing here is missing from every beat that cites it, and one written "
            f"twice has already forked"
        )
        words = len(found[0].split())
        assert words >= INVEST_GLOSS_MIN_WORDS, (
            f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} names {letter!r} with "
            f"{words} words of gloss on its own line, fewer than "
            f"{INVEST_GLOSS_MIN_WORDS}: {found[0]!r}. A bare list of the six spells the "
            f"mnemonic and asks nothing, so each letter says what it wants of a "
            f"requirement where the reader meets it"
        )

    body = _unwrapped(gate)
    assert SINGLE_DEFINITION_CLAIM in body, (
        f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} never states that it is "
        f"{SINGLE_DEFINITION_CLAIM}. Unstated, one definition is indistinguishable from "
        f"the first of several, and the next author writes a second copy in good faith"
    )
    assert CITING_BEAT in body, (
        f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} does not name issue "
        f"{CITING_BEAT} as the beat that cites it. A rule against copying that names "
        f"nobody it binds is advice; naming the citer is what makes it checkable"
    )
    assert CITE_NOT_COPY_RULE in body, (
        f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} does not say that the beats "
        f"needing the criteria cite this section {CITE_NOT_COPY_RULE!r}. Two copies of a "
        f"six-part gate diverge one letter at a time, and neither copy looks wrong alone"
    )

    assert INVEST_SOURCE in body, (
        f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} does not attribute the six "
        f"criteria to {INVEST_SOURCE}. A definition the whole suite cites has to say where "
        f"it came from, or a reader who thinks a gloss is wrong has nowhere to check it"
    )


def test_template_defines_what_the_invest_gate_applies_to() -> None:
    """The gate states its own scope, and that falling outside it is not a failure.

    Separate from the test above, which answers whether the six criteria are
    published at all. This answers the question an author hits the moment they try
    to use them: whether this gate applies to the requirement in front of them.

    Issue #18 asked for the gate and never defined story-shaped, so the term, its
    definition and the exemption are all this file's own, and all three are needed
    together. The term without a definition is a word an author guesses at per
    requirement. The definition without the exemption is worse: most requirements
    in a member are not story-shaped, so a gate that never says what happens to
    those reads as one that fails them, and the fix a reader invents for an
    apparent oversight is to run all six criteria over everything.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    body = _unwrapped(_section_body(template.splitlines(), _require_invest_span(template)))

    assert STORY_SHAPED_TERM in body, (
        f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} never uses the term "
        f"{STORY_SHAPED_TERM!r}, which is what the gate applies to. Issue #18 asked for the "
        f"gate without defining the term, so this file is where it gets defined"
    )
    assert STORY_SHAPED_DEFINITION in body, (
        f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} uses "
        f"{STORY_SHAPED_TERM!r} without defining it as {STORY_SHAPED_DEFINITION!r}. An "
        f"author who has to guess what story-shaped means guesses per requirement, which "
        f"is the ambiguity this beat exists to spend"
    )
    assert STORY_SHAPED_EXEMPTION in body, (
        f"'## {INVEST_SECTION}' of {REQUIREMENTS_TEMPLATE.name} does not state that a "
        f"requirement which is not story-shaped is {STORY_SHAPED_EXEMPTION!r}. Most "
        f"requirements here are not story-shaped, so an unexplained exemption reads as an "
        f"oversight -- and the cure for an apparent oversight is to apply the gate to "
        f"everything, failing thresholds and casing rules against Small"
    )


def test_template_publishes_every_ears_pattern_with_its_keyword() -> None:
    """Each pattern is a section of the notation, carrying the keyword it licenses.

    The pairing is what is checked, not the presence of five names and five
    keywords somewhere in the same file. A template listing the patterns without
    their keywords leaves an author to guess which word opens which sentence, and
    one that documents a keyword under the wrong pattern is worse: the `Pattern`
    column then classifies requirements by a mapping the notation does not have.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    h3_names = [text for text, _ in _at_level(headings, 3)]
    notation_start, notation_end = _require_notation_span(template)

    # Placement first, for the five patterns and the composition rule alike:
    # all six are sections of the notation and nowhere else.
    for section in NOTATION_SECTIONS:
        assert h3_names.count(section) == 1, (
            f"expected '### {section}' to appear exactly once as an H3 in "
            f"{REQUIREMENTS_TEMPLATE.name}, found {h3_names.count(section)}; the notation "
            f"publishes one section per pattern plus the rule for combining them, and the "
            f"template's H3s are {h3_names}"
        )
        start, _end = _section_span(headings, 3, section, len(lines))
        assert notation_start < start < notation_end, (
            f"'### {section}' sits at line {start}, outside '## {NOTATION_SECTION}' "
            f"(line {notation_start}) and the section that follows it (line {notation_end}); "
            f"a pattern documented outside the notation is one a reader looking up the "
            f"grammar will not find"
        )

    # Then the pairing, asserted in both directions at once: each pattern's
    # section states its own keywords and no other pattern's. One direction alone
    # is not the contract. A missing keyword leaves the pattern unspellable, and a
    # foreign one means another pattern's material has drifted in under this
    # heading, which is how a keyword ends up documented against the wrong name.
    #
    # Ubiquitous is the same rule with an empty expectation, which is the whole
    # of what makes it the always-active pattern: both optional clauses of the
    # generic form are empty, so a keyword appearing here is a gate on the one
    # pattern meant to have nothing gating it.
    for pattern, keywords in EARS_PATTERNS:
        body = "\n".join(_section_body(lines, _section_span(headings, 3, pattern, len(lines))))
        expected = set(keywords or ())
        present = {k for k in EARS_KEYWORDS if re.search(rf"\b{k}\b", body)}
        assert present == expected, (
            f"'### {pattern}' of {REQUIREMENTS_TEMPLATE.name} writes the keywords "
            f"{sorted(present)}, not {sorted(expected)}: missing "
            f"{sorted(expected - present)}, foreign {sorted(present - expected)}. A pattern's "
            f"section names the keyword it is recognised by and only that one; the ubiquitous "
            f"pattern names none, because a requirement that is always active has nothing "
            f"gating it"
        )

    # The composition rule is a rule over the five patterns rather than a sixth
    # one, and the evidence for that is that it shows two of them being combined.
    # A section under this heading exercising a single pattern's keyword has
    # quietly become a pattern of its own, which is the drift the plan's decision
    # against a sixth pattern exists to prevent.
    complex_body = "\n".join(
        _section_body(lines, _section_span(headings, 3, COMPLEX_SYNTAX_SECTION, len(lines)))
    )
    composed = [
        pattern
        for pattern, keywords in EARS_PATTERNS
        if keywords and any(re.search(rf"\b{k}\b", complex_body) for k in keywords)
    ]
    assert len(composed) >= 2, (
        f"'### {COMPLEX_SYNTAX_SECTION}' of {REQUIREMENTS_TEMPLATE.name} draws on "
        f"{composed or 'none'} of the five patterns. It is the rule for combining them, so "
        f"it has to show at least two combined; one pattern under a heading of its own is a "
        f"sixth pattern rather than a rule about the five"
    )


def test_every_notation_section_shows_a_form_and_a_worked_example() -> None:
    """Each pattern, and the rule combining them, prints its shape and an instance.

    Separate from the keyword test, which answers whether the pattern is
    documented. This answers whether it is usable: a section can explain at
    length what event-driven means and still leave an author with nothing to
    copy. The two registers are asserted together because they fail differently.
    A section with no grammar leaves the clause order unstated, so an author
    guesses it. A section with no worked example leaves the casing mandate with
    nothing demonstrating it, which is the rule in this file most likely to be
    read and then ignored.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    _require_notation_span(template)

    for section in NOTATION_SECTIONS:
        fenced = _fenced_lines(_section_body(lines, _section_span(headings, 3, section, len(lines))))
        requirement_lines = [line for line in fenced if MODAL_VERB in line]
        grammar = [line for line in requirement_lines if SLOT in line]
        example = [line for line in requirement_lines if SLOT not in line]
        assert grammar, (
            f"'### {section}' of {REQUIREMENTS_TEMPLATE.name} prints no clause grammar: "
            f"none of its fenced lines carries {MODAL_VERB} together with a {SLOT!r} slot. "
            f"The grammar is the part an author copies, and prose describing a pattern "
            f"outlives the form it describes"
        )
        assert example, (
            f"'### {section}' of {REQUIREMENTS_TEMPLATE.name} shows no worked example: "
            f"none of its fenced lines carries {MODAL_VERB} with every {SLOT!r} slot filled "
            f"in. The example is the only place the casing mandate is demonstrated rather "
            f"than asserted"
        )


def test_template_writes_non_functional_requirements_in_the_ubiquitous_pattern() -> None:
    """One notation covers both requirement tables, stated where the reuse applies.

    The alternative -- a second grammar for quality attributes -- is the thing
    this claim rules out, and nothing else in the document rules it out. Both
    requirement tables declare the same columns and sit under the same H2, so an
    author who never reads this sentence has no reason not to invent a notation
    for the non-functional table and no test to tell them they have.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    ubiquitous, _keywords = EARS_PATTERNS[0]
    body = _unwrapped(_section_body(lines, _section_span(headings, 3, ubiquitous, len(lines))))

    assert NON_FUNCTIONAL_REUSE in body, (
        f"'### {ubiquitous}' of {REQUIREMENTS_TEMPLATE.name} never states "
        f"{NON_FUNCTIONAL_REUSE!r}. The ubiquitous pattern is what the non-functional table "
        f"reuses, so this section is where an author reads that no second notation exists; "
        f"filed anywhere else the statement reaches nobody writing one of those rows"
    )


def test_template_states_the_generic_form_and_the_casing_it_mandates() -> None:
    """The one grammar all five patterns vary, and whose casing convention it is.

    Separate from the pattern test, which answers whether each pattern is
    documented. This answers whether a requirement written from those patterns
    comes out in the shape the rest of the suite expects: the clause order that
    makes a precondition gate a trigger, and the casing a downstream reader greps
    for. The attribution is asserted with the rule because the mandate diverges
    from the notation's own author, and an unattributed divergence is
    indistinguishable from an error.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    notation = _unwrapped(_section_body(lines, _require_notation_span(template)))

    # The generic form belongs to the notation as a whole rather than to the
    # casing section: it is the grammar all five patterns vary, and it is printed
    # in the paper's lowercase precisely because it is grammar and not an
    # instance of one.
    assert GENERIC_FORM in notation, (
        f"'## {NOTATION_SECTION}' of {REQUIREMENTS_TEMPLATE.name} never prints the generic "
        f"form {GENERIC_FORM!r}. It is the one form the five patterns are variations of, and "
        f"its clause order is the content: preconditions precede the trigger because they "
        f"gate it, so a form written in another order states a different rule in the same "
        f"words"
    )
    assert GENERIC_FORM_NOTE in notation, (
        f"'## {NOTATION_SECTION}' of {REQUIREMENTS_TEMPLATE.name} prints the generic form "
        f"without stating {GENERIC_FORM_NOTE!r}. The order is the one part of the form a "
        f"reader will take for arbitrary, and an author who takes it for arbitrary writes a "
        f"state clause after a trigger and changes what the requirement says"
    )

    h3_names = [text for text, _ in _at_level(headings, 3)]
    assert h3_names.count(CASING_SECTION) == 1, (
        f"expected '### {CASING_SECTION}' to appear exactly once as an H3 in "
        f"{REQUIREMENTS_TEMPLATE.name}, found {h3_names.count(CASING_SECTION)}; the mandate "
        f"and the precedent it follows are stated together there, and the template's H3s are "
        f"{h3_names}"
    )
    casing = _unwrapped(_section_body(lines, _section_span(headings, 3, CASING_SECTION, len(lines))))
    for statement, why in CASING_STATEMENTS:
        assert statement in casing, (
            f"'### {CASING_SECTION}' of {REQUIREMENTS_TEMPLATE.name} never states "
            f"{statement!r}, which is {why}"
        )


def test_template_nests_its_sections_under_the_published_headings() -> None:
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = REQUIREMENTS_TEMPLATE.read_text()

    # The grouping table is keyed by the substrate's names, so this is also the
    # guard on the read itself: a bullet that moved out from under the pattern
    # yields an empty list, and every nesting check below would then pass by
    # having nothing to look for rather than by agreeing with anything.
    required_sections = _requirements_section_names(substrate)
    assert sorted(required_sections) == sorted(NESTED_SECTIONS), (
        f"NESTED_SECTIONS groups the template's H3 sections under "
        f"{sorted(NESTED_SECTIONS)}, but {ARTIFACT_FAMILY.name} publishes "
        f"{required_sections} for requirements.md. Each H3 is grouped by what its "
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
            f"{REQUIREMENTS_TEMPLATE.name}, found {occurrences}; "
            f"{ARTIFACT_FAMILY.name} requires the section of requirements.md, and "
            f"the template has {h2_names}"
        )

    # Document order is part of the published schema: a template that emits the
    # sections in another sequence shapes a different document.
    h2_line = dict(h2)
    ordered = [h2_line[name] for name in required_sections]
    assert ordered == sorted(ordered), (
        f"{REQUIREMENTS_TEMPLATE.name} must carry requirements.md's sections in "
        f"the order {ARTIFACT_FAMILY.name} publishes {required_sections}; found "
        f"them at lines {ordered}"
    )

    # The six content sections are subsections, not siblings. Bounding each by
    # the H2 that follows its parent proves the nesting rather than merely
    # proving the six names appear somewhere in the file -- and it is what
    # distinguishes a coverage table filed under Scope from one appended at the
    # end, where nothing above it is answerable to it.
    h3_lines: dict[str, list[int]] = {}
    for text, line in _at_level(headings, 3):
        h3_lines.setdefault(text, []).append(line)

    for parent in required_sections:
        parent_start, parent_end = _section_span(headings, 2, parent, len(lines))
        for child in NESTED_SECTIONS[parent]:
            found = h3_lines.get(child, [])
            assert len(found) == 1, (
                f"expected '### {child}' to appear exactly once as an H3 in "
                f"{REQUIREMENTS_TEMPLATE.name}, found it at lines {found}; its H3 "
                f"headings are {sorted(h3_lines)}"
            )
            assert parent_start < found[0] < parent_end, (
                f"'### {child}' sits at line {found[0]}, outside '## {parent}' "
                f"(line {parent_start}) and the section that follows it (line "
                f"{parent_end}); the six content sections nest inside the three "
                f"H2s {ARTIFACT_FAMILY.name} publishes"
            )


def test_template_declares_the_columns_its_tables_are_read_by() -> None:
    """The three tables declare the exact columns, and the ids match the notation.

    Separate from the nesting test, which answers whether a section exists at
    all. This answers whether the section a reader reached is one they can read:
    a coverage table missing `Covered by`, or a requirement table whose `Traces
    to` column has been renamed, sits in the right place under the right heading
    and still cannot be consumed by the beat downstream of it.
    """
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)

    for section, columns in DECLARED_TABLES.items():
        rows = _table(_section_body(lines, _section_span(headings, 3, section, len(lines))))
        assert rows, (
            f"'### {section}' of {REQUIREMENTS_TEMPLATE.name} carries no table; the "
            f"section is where a reader goes for {list(columns)}, and prose "
            f"describing those fields is not something a downstream beat can read"
        )
        header, *body_rows = rows
        assert tuple(header) == columns, (
            f"'### {section}' of {REQUIREMENTS_TEMPLATE.name} declares columns "
            f"{header}, not {list(columns)}. The names and their order are what a "
            f"downstream beat locates a cell by, so a rename or a reshuffle breaks "
            f"that reader while leaving the document looking well-formed"
        )
        assert body_rows, (
            f"the table in '### {section}' of {REQUIREMENTS_TEMPLATE.name} has a "
            f"header row and nothing under it; what belongs in each cell is only "
            f"shown by a row, so a header-only table declares columns without "
            f"saying what they hold"
        )

    # The id notation is checked where it is used, not only where it is stated.
    # A template whose prose still described `REQ<n>` while its rows had moved to
    # some other scheme would satisfy a prose check and ship the document the
    # prose check exists to prevent.
    assert ID_FORM in template, (
        f"{REQUIREMENTS_TEMPLATE.name} never states the id form {ID_FORM!r}; the "
        f"flat sequence is what keeps an id stable when a requirement is re-worded "
        f"or re-classified, and a document that does not state it will be filled in "
        f"with whatever the author assumes"
    )
    for section in ("Functional requirements", "Non-functional requirements"):
        _header, *body_rows = _table(_section_body(lines, _section_span(headings, 3, section, len(lines))))
        for cells in body_rows:
            assert re.fullmatch(r"REQ\d+", cells[0]), (
                f"a row of '### {section}' in {REQUIREMENTS_TEMPLATE.name} has the id "
                f"{cells[0]!r}, which is not of the form {ID_FORM!r} the template "
                f"states. Both requirement tables draw from one flat sequence, so an "
                f"id shaped differently here is a second scheme nobody declared"
            )

    coverage = "\n".join(_section_body(lines, _section_span(headings, 3, COVERAGE_SECTION, len(lines))))
    assert NOT_ADDRESSED in coverage, (
        f"'### {COVERAGE_SECTION}' of {REQUIREMENTS_TEMPLATE.name} never states the "
        f"literal {NOT_ADDRESSED!r} that a `Covered by` cell takes when nothing "
        f"answers an opportunity. Without it the cell goes blank, and an opportunity "
        f"nobody wrote a requirement for reads exactly like a table nobody finished"
    )


def test_principles_expose_five_red_flag_clusters() -> None:
    """The rubric's spine is in order and every cluster can drive one finder.

    This is the rubric's interface rather than its content. `product-review`
    quotes one H2, or one H3 cluster, into an agent prompt, so the section names,
    their order and the number of clusters are what the file publishes to its
    callers -- and the per-cluster shape is what makes a quoted cluster usable at
    all. A cluster of prose gives a critic nothing to answer, and a cluster with
    no severity hint gives a reviewer findings they cannot route.

    Whether those clusters are the right five, and whether they are grounded in
    anything, is the next test's.
    """
    assert REQUIREMENTS_PRINCIPLES.exists(), f"missing shipped rubric: {REQUIREMENTS_PRINCIPLES}"

    principles = REQUIREMENTS_PRINCIPLES.read_text()
    lines = principles.splitlines()
    headings = _headings(principles)
    h2 = _at_level(headings, 2)
    h2_names = [text for text, _ in h2]

    # Exactly once, not merely present, for the reason `_at_level` returns a list:
    # an orchestrator quoting a section by name gets one of them, and a rubric
    # carrying the same heading twice has split a section nobody can quote whole.
    # It is also what makes the mapping below safe, since collapsing to a mapping
    # keeps only the last occurrence of a repeated name.
    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{REQUIREMENTS_PRINCIPLES.name}, found {occurrences}; it shares its heading "
            f"spine with the plugin's other rubric files so that an orchestrator can "
            f"quote one section by name, and it has {h2_names}"
        )

    # The spine's order is part of it. These files are read top to bottom by a
    # maintainer and quoted section by section by an orchestrator, and the
    # sequence is the reading path: who wrote this and what it covers, then how to
    # author, then how to review, then how to change the file itself.
    h2_line = dict(h2)
    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"{REQUIREMENTS_PRINCIPLES.name} must carry its spine sections in the order "
        f"{list(PRINCIPLES_SPINE)}, the order its sibling rubric files use; found them "
        f"at lines {spine_lines}"
    )

    clusters = _cluster_spans(principles)
    cluster_names = [name for name, _span in clusters]
    assert len(clusters) == RED_FLAG_CLUSTER_COUNT, (
        f"expected exactly {RED_FLAG_CLUSTER_COUNT} H3 clusters under "
        f"'## {RED_FLAGS_SECTION}' in {REQUIREMENTS_PRINCIPLES.name}, found "
        f"{len(clusters)}: {cluster_names}; a review launches one finder per cluster, "
        f"so the count is part of what this file publishes -- and the fifth is the "
        f"finder assigned to broken traceability, which is the failure this beat exists "
        f"to prevent"
    )

    for name, span in clusters:
        body = _section_body(lines, span)
        assert any(line.rstrip().endswith("?") for line in body), (
            f"cluster '### {name}' of {REQUIREMENTS_PRINCIPLES.name} carries no line "
            f"ending in a question mark; every cluster is a set of questions a reviewer "
            f"answers yes or no against a written requirements.md, and prose cannot be "
            f"answered. The clusters are {cluster_names}"
        )
        assert any(SEVERITY_HINT in line for line in body), (
            f"cluster '### {name}' of {REQUIREMENTS_PRINCIPLES.name} carries no "
            f"{SEVERITY_HINT!r} line; a question without one yields a finding a reviewer "
            f"cannot route as material or minor. The clusters are {cluster_names}"
        )


def test_every_cluster_names_the_paper_problem_it_derives_from() -> None:
    """The five clusters are the paper's taxonomy, and each says which part.

    Separate from the test above, which answers whether a fleet can be launched
    over this file. This answers why these five: the beat replaced five invented
    clusters with five drawn from the same paper it already ships as its notation,
    and a cluster that does not name its problem has spent that grounding.

    The naming has to be inside the cluster, because a cluster is what gets
    quoted. A critic receives one H3 and no more of this file, so a taxonomy
    recorded only in the attribution section reaches nobody doing the reviewing.
    """
    assert REQUIREMENTS_PRINCIPLES.exists(), f"missing shipped rubric: {REQUIREMENTS_PRINCIPLES}"

    covered = {problem for problems in CLUSTER_DERIVATIONS.values() for problem in problems}
    assert len(covered) + 1 == PAPER_PROBLEM_COUNT, (
        f"CLUSTER_DERIVATIONS accounts for {len(covered)} of the paper's "
        f"{PAPER_PROBLEM_COUNT} problems, plus {UNCLUSTERED_PROBLEM!r} declared "
        f"unclustered: {sorted(covered)}. A problem dropped from this mapping and from "
        f"the rubric together passes every comparison between the two, and a rubric "
        f"narrower than the taxonomy it cites reads as the whole of it"
    )

    principles = REQUIREMENTS_PRINCIPLES.read_text()
    lines = principles.splitlines()
    clusters = _cluster_spans(principles)

    # One equality rather than a membership check plus a count, because the three
    # ways this list goes wrong -- a missing cluster, an extra one, a reshuffle --
    # are one comparison and three separate searches. It also guards the lookup
    # below, which is keyed by these names.
    assert [name for name, _span in clusters] == list(CLUSTER_DERIVATIONS), (
        f"'## {RED_FLAGS_SECTION}' of {REQUIREMENTS_PRINCIPLES.name} carries "
        f"{[name for name, _span in clusters]}, not {list(CLUSTER_DERIVATIONS)}. Each "
        f"name states which of the paper's problems its questions hunt, so a renamed or "
        f"reordered cluster is one whose grounding no longer says anything"
    )

    for name, span in clusters:
        body = _unwrapped(_section_body(lines, span)).lower()
        missing = [problem for problem in CLUSTER_DERIVATIONS[name] if problem not in body]
        assert not missing, (
            f"cluster '### {name}' of {REQUIREMENTS_PRINCIPLES.name} never names "
            f"{missing}, the problem it derives from. The cluster is what a critic is "
            f"handed, so a cluster that does not cite its own source is one the critic "
            f"reads as this project's opinion"
        )

    attribution = _unwrapped(
        _section_body(lines, _section_span(_headings(principles), 2, ATTRIBUTION_SECTION, len(lines)))
    )
    for needle in PAPER_ATTRIBUTION:
        assert needle in attribution, (
            f"'## {ATTRIBUTION_SECTION}' of {REQUIREMENTS_PRINCIPLES.name} never states "
            f"{needle!r}. The clusters' whole claim over any other five is that a "
            f"published taxonomy produced them, and a claim with no author, venue or "
            f"disclaimer is not one a reader can check"
        )
    assert UNCLUSTERED_PROBLEM in attribution.lower(), (
        f"'## {ATTRIBUTION_SECTION}' of {REQUIREMENTS_PRINCIPLES.name} does not record "
        f"that {UNCLUSTERED_PROBLEM!r} is the one problem of the {PAPER_PROBLEM_COUNT} "
        f"that no cluster carries. Unrecorded, seven of eight reads as a taxonomy "
        f"somebody transcribed carelessly rather than as a decision somebody made"
    )


def test_principles_cite_their_neighbours_rather_than_restating_them() -> None:
    """The rubric points at what it does not own: shape, marker, design rules.

    Separate from the grounding test, which answers where the questions came
    from. This answers the boundary the siblings state as "judgement, not shape":
    a rubric that redefines a section, a token or another rubric's cluster has
    become a second copy of it, and the copy is the one a reviewer will read
    after the definition has moved on.

    The traceability cluster is asserted here rather than with its own grounding
    because citation is what makes it answerable at all. Its questions are about
    what is *absent* from a member, and absence is only visible against the
    template's coverage table and the literal an uncovered row carries; a cluster
    asking after silent drops without naming either is asking a reviewer to
    compare the member with their own memory of `discovery.md`.
    """
    assert REQUIREMENTS_PRINCIPLES.exists(), f"missing shipped rubric: {REQUIREMENTS_PRINCIPLES}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"
    assert DESIGN_PRINCIPLES.exists(), f"missing design rubric: {DESIGN_PRINCIPLES}"

    principles = REQUIREMENTS_PRINCIPLES.read_text()
    lines = principles.splitlines()
    whole = _unwrapped(lines)

    for citation in (
        REQUIREMENTS_TEMPLATE_CITATION,
        ARTIFACT_FAMILY_CITATION,
        DESIGN_PRINCIPLES_CITATION,
    ):
        assert citation in whole, (
            f"{REQUIREMENTS_PRINCIPLES.name} never cites {citation}. Each of the three "
            f"owns rules this file leans on and must not restate -- the member's shape, "
            f"its section names and marker, and the naming and comment questions -- and "
            f"a reader told a rule lives elsewhere without being told where "
            f"reconstructs it"
        )

    # The deferral names two clusters of another file, so it is checked against
    # that file's own headings. A citation pointing at a cluster which has since
    # been renamed is worse than none: it sends a reader somewhere specific and
    # wrong, and nothing in design-review's own tests pins those names.
    design_clusters = [text for text, _line in _at_level(_headings(DESIGN_PRINCIPLES.read_text()), 3)]
    attribution = _unwrapped(
        _section_body(lines, _section_span(_headings(principles), 2, ATTRIBUTION_SECTION, len(lines)))
    )
    for cluster in DEFERRED_DESIGN_CLUSTERS:
        assert cluster in design_clusters, (
            f"{REQUIREMENTS_PRINCIPLES.name} defers questions about {cluster!r} to "
            f"{DESIGN_PRINCIPLES.name}, which no longer carries a cluster of that name; "
            f"its clusters are {design_clusters}. The deferral has to name a cluster "
            f"that exists, or it points a reviewer at nothing"
        )
        assert f"`### {cluster}`" in attribution, (
            f"'## {ATTRIBUTION_SECTION}' of {REQUIREMENTS_PRINCIPLES.name} does not name "
            f"'### {cluster}' of {DESIGN_PRINCIPLES.name} as the cluster it defers to. "
            f"Citing the file without naming the cluster leaves the next author free to "
            f"grow a sixth cluster here in good faith, which is what the deferral exists "
            f"to prevent"
        )

    spans = dict(_cluster_spans(principles))
    assert TRACEABILITY_CLUSTER in spans, (
        f"{REQUIREMENTS_PRINCIPLES.name} carries no '### {TRACEABILITY_CLUSTER}' cluster; "
        f"it has {sorted(spans)}. It is the one cluster whose questions are answered "
        f"against a table rather than a sentence, so the checks below have nothing to "
        f"bound themselves to"
    )
    traceability = _unwrapped(_section_body(lines, spans[TRACEABILITY_CLUSTER]))
    assert COVERAGE_SECTION in traceability, (
        f"cluster '### {TRACEABILITY_CLUSTER}' of {REQUIREMENTS_PRINCIPLES.name} never "
        f"names '### {COVERAGE_SECTION}', the table its questions are answered against. "
        f"A question about an opportunity nobody addressed is only checkable where every "
        f"opportunity has a row; without the table it asks a reviewer to recall "
        f"discovery.md from memory"
    )
    assert NOT_ADDRESSED in traceability, (
        f"cluster '### {TRACEABILITY_CLUSTER}' of {REQUIREMENTS_PRINCIPLES.name} never "
        f"names the literal {NOT_ADDRESSED!r} a `Covered by` cell takes when nothing "
        f"answers an opportunity. That literal is what separates a deliberate gap from "
        f"an unfinished table, which is exactly the distinction this cluster is asked to "
        f"make"
    )

    # The marker is named in words and never spelled, for the reason the template
    # is held to as well: one definition of the token exists, it lives in the
    # substrate, and a second copy here would keep passing after the definition
    # moved on.
    marker_prefix = _unknown_marker_prefix(ARTIFACT_FAMILY.read_text())
    assert marker_prefix, (
        f"could not read the unknown-marker literal out of {ARTIFACT_FAMILY.name}; "
        f"expected a fenced block under {UNKNOWN_MARKER_HEADING!r}"
    )
    assert marker_prefix not in whole, (
        f"{REQUIREMENTS_PRINCIPLES.name} restates the unknown marker ({marker_prefix!r}); "
        f"it cites {ARTIFACT_FAMILY_CITATION} for the token instead, since a rubric "
        f"carrying its own copy is one that can disagree with the definition while both "
        f"files' tests stay green"
    )


def test_skill_publishes_each_runtime_rule() -> None:
    """Every rule only a review can enforce is nonetheless written down.

    This is the one test in the module whose subject is not a document's shape,
    and the asymmetry is the point. A shape test proves the template a run copies
    from is right. Nothing here can prove a run behaved: a `requirements.md` whose
    freshness state was guessed looks exactly like one whose state was read, and a
    renumbered id looks exactly like an id that never moved. So what is checkable
    is one step back from the behaviour -- that the body an acting model has in
    front of it states the rule at all -- and a rule missing from it is a rule that
    exists in nobody's head but the author's of this plan.

    Three groups, and only the first is searched across the whole body. The
    substrate rules can be stated wherever the step that follows them is, so
    presence is the whole of what they need. The refusals and the re-run promise are
    each held to the section that owns them, for two different reasons. A refusal
    names tokens the file uses again elsewhere for honest reasons, so a body-wide
    search would keep passing on those other uses after the refusal itself had gone;
    and their order is a rule no presence check reaches. The re-run rows are
    followed once by a run and read for years by everyone holding a `REQ` id, so
    where they sit is part of the rule: the promise every beat in this suite
    publishes under one heading is one nobody will find under another.

    Frontmatter shape and whether the cited files resolve are the next test's. Both
    are about whether a session ever reaches these rules rather than about what
    they say, so a failure names one or the other instead of reporting that the
    skill is wrong somewhere.
    """
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    skill = SKILL_MD.read_text()
    body = _acting_body(skill)
    assert body, (
        f"{SKILL_MD.name} opens a `---` frontmatter block that never closes, so the whole "
        f"file is frontmatter as far as the harness reads it and no rule below could be "
        f"satisfied by text a run acts on"
    )
    # Pins this module's split against the one tests/guarantees.py performs, which
    # reads the keys inside the block rather than the remainder and so cannot be
    # asked for the body directly. Were the two to stop agreeing on where the block
    # ends, the description would sit in what this test calls the body, and every
    # row below could be satisfied by text the router weighs and the model never
    # acts from.
    assert not re.search(r"^description:", body, re.MULTILINE), (
        f"{SKILL_MD.name}'s frontmatter survived into what `_acting_body` returned as its "
        f"body, so this module and tests/guarantees.py no longer agree on where the block "
        f"ends"
    )

    # Backticks are dropped before matching so that code-spanning a rule's nouns is
    # a formatting choice rather than a deleted rule. The words and their order
    # still have to be exactly right, which is what each row asserts.
    published = body.replace("`", "")
    for rule, literal in RUNTIME_RULES:
        assert literal in published, (
            f"{SKILL_MD.name} does not publish the rule that {rule}: the literal "
            f"{literal!r} appears nowhere in its body. Nothing can check a generated "
            f"requirements.md against this rule afterwards, so the body stating it is the "
            f"only place the rule exists at all"
        )

    lines = skill.splitlines()
    headings = _headings(skill)
    h2_names = [text for text, _line in _at_level(headings, 2)]

    # The refusals are held to the step that owns them, and that step to the top of
    # the body. First, not merely present: a run that has already read the tree or
    # asked the user something before reaching the gate has spent the work the gate
    # exists to avoid, and refusing afterwards refunds none of it.
    assert h2_names[:1] == [REFUSAL_SECTION], (
        f"expected '## {REFUSAL_SECTION}' to be the first H2 of {SKILL_MD.name}; its H2s "
        f"are {h2_names}. A gate that is not the first thing a run reaches is not a gate, "
        f"and the three refusals below are only checkable where they are checkable at all"
    )
    refusals = _unwrapped(
        _section_body(lines, _section_span(headings, 2, REFUSAL_SECTION, len(lines)))
    ).replace("`", "")
    assert REFUSAL_BEAT in refusals, (
        f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} never names {REFUSAL_BEAT!r} as the "
        f"beat to run. A refusal that does not say what would fix it leaves a user holding "
        f"a complaint and no next move, which is the shape a refusal takes when it reads "
        f"as a failure of this beat rather than a finding about the last one"
    )

    found = []
    for rule, literal in REFUSALS:
        at = refusals.find(literal)
        assert at != -1, (
            f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} does not refuse when {rule}: the "
            f"state {literal!r} appears nowhere in the step. Named nowhere, the case is one "
            f"a run meets with no instruction and improvises past"
        )
        found.append((literal, at))
    assert [at for _literal, at in found] == sorted(at for _literal, at in found), (
        f"'## {REFUSAL_SECTION}' of {SKILL_MD.name} states its refusals in the order "
        f"{[literal for literal, _at in sorted(found, key=lambda pair: pair[1])]}, not "
        f"{[literal for _rule, literal in REFUSALS]}. A run stops "
        f"at the first that fires, so the sequence decides which of the three a user is "
        f"told about -- and the cheap checks come first because the later ones read a file "
        f"the earlier ones may have just shown to be missing"
    )

    assert h2_names.count(RERUN_SECTION) == 1, (
        f"expected '## {RERUN_SECTION}' to appear exactly once as an H2 in "
        f"{SKILL_MD.name}, found {h2_names.count(RERUN_SECTION)}; every beat in this suite "
        f"publishes what a second run does under that heading, and this one's answer "
        f"differs from its siblings' -- it revises in place rather than overwriting -- so a "
        f"reader who does not find it there will assume the sibling behaviour. The file's "
        f"H2s are {h2_names}"
    )
    rerun = _unwrapped(_section_body(lines, _section_span(headings, 2, RERUN_SECTION, len(lines)))).replace(
        "`", ""
    )
    for rule, literal in RERUN_RULES:
        assert literal in rerun, (
            f"'## {RERUN_SECTION}' of {SKILL_MD.name} does not state that {rule}: the "
            f"literal {literal!r} appears nowhere in the section. A REQ id is cited from "
            f"outside this file and no mechanism in the chain reports a renumber, so this "
            f"section is where the rule and its reason both live or neither does"
        )


def test_skill_frontmatter_conforms_and_its_citations_resolve() -> None:
    """Whether a session reaches the rules above, and whether their sources open.

    Separate from the rules themselves, which fail for an unrelated reason: that
    test answers whether the body states a rule, and this one whether anything gets
    to act on it. Bundled, a stripped tool allowlist would report under a name
    about unpublished prose.

    Three groups, and they are three answers to one question: can a session get to
    the rules above and follow them. A missing required key is a skill nobody
    reaches, by slash command or by router. A forbidden key is a skill reached with
    the tools its own steps need taken away. An unresolvable citation is the
    subtlest of the three, because the session does reach the rule and does read it:
    it is sent to a file it cannot open, so it works from memory, which is the one
    failure every citation in the body exists to prevent. All three are read off the
    shipped file, since a citation that resolves against a fixture resolves nowhere.

    The description's length and its opening token are not asserted here.
    `tests/test_description_budget.py` globs both over every skill in the plugin,
    this one included, and a second copy would report one over-long description as
    two unrelated failures.
    """
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    skill = SKILL_MD.read_text()

    # The block is asserted well-formed before any key is read, because both ways of
    # malforming it make every read below vacuous rather than failing: no key is
    # declared in a file that declares no block, so a SKILL.md with no frontmatter
    # at all would satisfy the whole forbidden-key loop while reaching no router.
    # `_acting_body` tells the two malformed shapes apart -- the whole text when no
    # block opens, "" when one opens and never closes -- so each gets its own
    # report.
    body = _acting_body(skill)
    assert body != skill, (
        f"{SKILL_MD.name} declares no `---` frontmatter block at all, so it contributes "
        f"nothing to the model-facing listing and no session can route to it. The "
        f"forbidden-key checks below would pass on it for the wrong reason: an absent "
        f"key and an absent block are the same read"
    )
    assert body, (
        f"{SKILL_MD.name} opens a `---` frontmatter block that never closes, so the "
        f"harness reads the whole file as frontmatter and the citations below would be "
        f"looked for in text no run ever acts on"
    )

    # Read through guarantees.py rather than matched here, so that "declares a key"
    # means the same thing to this test as to the listing rule that acts on one.
    guarantees = _guarantees()
    for key, purpose in REQUIRED_FRONTMATTER_KEYS:
        declared = guarantees.scalar_text(guarantees.frontmatter_value(skill, key))
        assert declared, f"{SKILL_MD.name} declares no {key!r} with any text in it, and {purpose}"

    for key, consequence in FORBIDDEN_FRONTMATTER_KEYS:
        declared = guarantees.frontmatter_value(skill, key)
        assert declared is None, (
            f"{SKILL_MD.name} declares {key!r} (value {declared!r}), and {consequence}. "
            f"Removing the key is the fix; keeping it means the run-time rules the body "
            f"publishes are rules nothing will reach"
        )

    for rule, path in CITED_REFERENCES:
        citation = _plugin_root_citation(path)
        assert citation in body, (
            f"{SKILL_MD.name} does not cite {citation} in its body, so it does not "
            f"establish that {rule}. A run told to follow a rule whose source it was "
            f"never pointed at follows the rule from memory"
        )
        # Resolved by replacing the variable with this checkout's root, which is what
        # the harness does with a different root at run time. Walking the citation
        # string rather than asserting on `path` is the point: the string is what a
        # reader follows, and it is the only half of the pair that a typo can break
        # while every constant in this module still names a file that exists.
        resolved = REPO_ROOT / citation.removeprefix(f"{PLUGIN_ROOT_VARIABLE}/")
        assert resolved.is_file(), (
            f"{SKILL_MD.name} cites {citation}, which resolves to {resolved} and is not a "
            f"file. Under the installed plugin the same citation resolves against a "
            f"different root, so a run reads it as a path that is simply not there and "
            f"has nothing to fall back on but memory"
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
