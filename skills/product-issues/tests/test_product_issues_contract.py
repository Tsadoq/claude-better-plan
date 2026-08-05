"""Contract tests over the files the product-issues skill ships.

Pins the static properties of the shipped markdown -- the ones no run-time test
can observe. Whether a written slice set obeyed this beat's rules is not
checkable here and mostly not checkable at all: no freshness check in this suite
reads a slice, so a folder cut down architectural layers and one cut across a
backbone leave the same bytes behind. That half is enforced by the critic fleet
`product-review` fans over this skill's rubric, and the only thing a test can add
is that the fleet is launchable and that every file a run is sent to can be
reached. Those two are what this module owns.

The six tests split on where a failure is fixed, which is how each one should be
read.

`test_skill_cites_plugin_root_and_never_a_stamped_path` owns reachability. Every
path `SKILL.md` sends a run to is spelled with `${CLAUDE_PLUGIN_ROOT}`, resolves
to a file this repository actually ships, and carries no version-stamped plugin
directory. The stamp is the failure worth naming: a path copied out of an
installed plugin cache -- `.../deep-plan/0.19.0/skills/...` -- works perfectly in
the session it was copied from and breaks for every user on the next release,
which is a defect that cannot be reproduced by the person who wrote it. The
existence check is what stops a citation rotting into a redirect to nothing, and
it is derived from the cited text rather than from a list kept here, since a list
is somewhere for the citation and its guard to disagree.

`test_skill_publishes_the_re_run_section_a_second_run_reads` owns the one rule
whose enforcement is entirely that it is written down. Slice ids are cited from
outside this folder and no check in this suite reaches them, so a re-run that
renumbers leaves every member reporting `fresh` while every citation points at
different work. Publishing the section is the whole of the guard.

`test_principles_expose_the_clusters_a_review_fans_over` owns the launch.
`product-review` quotes an H2 by name and fans one critic per H3 cluster under
`## Review-time red flags`, so the spine's names and the cluster count are not
matters of taste -- they are what a review can quote and how wide it goes. The
floor is a minimum rather than an equality, which is this module's one departure
from the sibling rubrics' contracts: those pin an exact count because their
rubrics were sized in the same commit as their callers, while `product-review`
fans over whatever this file publishes, so a fifth cluster here is a wider review
and not a broken caller.

`test_template_cites_the_invest_gate_without_restating_it` and
`test_shipped_files_introduce_no_second_unknown_marker` own the two things this
skill deliberately does not say. Both are bans, and a ban is only checkable in
the negative: the gate has one home in `product-requirements` and the marker has
one home in `product-artifacts`, and a second copy of either diverges one letter
at a time with neither copy looking wrong on its own.

The marker ban overlaps `tests/test_marker_uniqueness.py` and does not duplicate
it. That module globs `*.md` under `skills/`, so it can see a fork in this
skill's markdown but not in `scripts/preflight.py` -- which reads the token out
of `artifact-family.md` at run time precisely so the code holds no copy, and
whose obvious "simplification" is a hardcoded literal that the repo-level scan
would never look at. This module scans the scripts too.

`test_template_publishes_the_frontmatter_schema_slice_file_requires` owns the
seam between a schema and its reader. `story-map-template.md` is the schema's
single published home and `slice_file.REQUIRED_KEYS` is the code's copy, so the
keys are parsed back out of the template rather than written down here -- the way
`skills/product-artifacts/tests/test_product_artifact_queries.py` reads the chain
members out of the contract it checks `MEMBERS` against. An expectation written
here would be a third copy, and a third copy is where a green suite starts
meaning nothing.

Three things are deliberately unpinned, and a maintainer trusting a green run
should know which. The cluster *names* are prose a reader judges, so replacing
all four with four others of the same shape passes. The rubric's arguments and
its attribution section are unread here, so a deleted caveat is invisible.
`description` is unmeasured, because `tests/test_description_budget.py` owns the
frontmatter budget and a second reader of that field is how two budgets come to
disagree about what they are measuring.

`_headings`, `_section_body` and `_load` are copies of the sibling contract
modules' helpers, and the copies are knowing ones on the terms those modules
already record: there is no shared harness under the repo-level `tests/` for them
to live in, and a per-skill module that runs standalone is worth more than one
that cannot. `_section_body` here finds a heading at any level and bounds at the
next heading of that level or above, which the siblings' H2-only version does
not, because the frontmatter schema this module reads is published under an H3.
The honest fix is still that harness, and it gets more expensive with each module
that copies rather than less.

Runnable two ways:
    python3 skills/product-issues/tests/test_product_issues_contract.py
    uvx pytest skills/product-issues/tests/test_product_issues_contract.py
"""

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

# The two sibling skills this one refuses to restate, reached by a relative hop
# rather than a plugin-root walk: both ship in this same tree, so the hop stays
# true if the plugin is installed under a different name.
ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"
INVEST_GATE = SKILL_ROOT.parent / "product-requirements" / "references" / "requirements-template.md"

# Where the plugin declares its own directory name. Read rather than restated so
# that renaming the plugin cannot quietly turn the stamped-path scan below into a
# search for a string nothing will ever contain again.
PLUGIN_MANIFEST = REPO / ".claude-plugin" / "plugin.json"

# The variable a shipped document spells a plugin path with. It resolves wherever
# the plugin is installed, which neither a repository-relative path nor a path
# out of somebody's plugin cache does.
PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"
PLUGIN_ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")

# A path into the plugin's own tree that is *not* spelled with the variable. The
# lookbehind is what makes this a check rather than a search: `skills/` is the
# first segment of every plugin-root path too, so the pattern has to exclude the
# correct spelling instead of looking for an incorrect one, there being no shape
# a wrong prefix reliably has.
#
# Scoped to `skills/` and nothing else. `docs/product/<slug>/` paths in the same
# file are the user's repository and are bare on purpose; a rule that caught them
# would be a rule against writing down where the output goes.
BARE_PLUGIN_PATH = re.compile(r"(?<!\$\{CLAUDE_PLUGIN_ROOT\}/)skills/")

# The version segment of an installed plugin path, as a semver directory. This
# is what separates a stamp from a mention: `/deep-plan` on its own is the beat
# talking about its neighbour, while `/deep-plan/0.19.0/` is a path somebody
# copied out of a cache that will not exist after the next release.
STAMPED_VERSION = r"/\d+\.\d+\.\d+"

# The rubric's H2 spine, in the order a maintainer reads it: where the questions
# came from, how to author, how to review, how to change the file. It is the
# spine every rubric in this suite publishes, and `product-review` quotes one of
# these names into an agent prompt, so a renamed section leaves a caller quoting
# nothing.
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

# The heading level a red-flag cluster sits at, and the fewest this rubric may
# publish. A floor rather than an exact count: `product-review` launches one
# finder per cluster it finds, so a fifth cluster widens a review rather than
# breaking a caller, while a fourth removed is a question nobody asks again.
CLUSTER_LEVEL = 3
MINIMUM_RED_FLAG_CLUSTERS = 4

# The section a second run is read before it touches an existing folder, and the
# only enforcement the re-run rule has. Named here because where the rule is
# stated is part of the rule: `## Re-run behaviour` is the heading every beat in
# this suite publishes the same promise under, and a reader who opens it must not
# find it empty.
RERUN_SECTION = "Re-run behaviour"

# The H3 the slice frontmatter schema is published under, and the section of the
# substrate that defines the suite's unknown-value marker.
REQUIRED_KEYS_SECTION = "Required keys"
UNKNOWN_MARKER_SECTION = "Unknown marker"

# The shape every unknown-marker dialect shares: a bracket, an all-caps token
# that may span words, then a colon introducing the payload. Requiring the colon
# and at least three characters keeps ordinary prose out -- a sentence containing
# "[A]" or a citation like "[RFC 2119]" cannot match.
#
# This is `tests/test_marker_uniqueness.py`'s pattern, and the repository's third
# copy of it. The copy buys the one question neither of the others asks: that
# module and product-roadmap's contract both scan markdown, while the file that
# could fork the dialect invisibly is `scripts/preflight.py`.
#
# Re-typed rather than imported, which is the part worth defending. The copy it
# would be imported from is a pytest module at the repository root and not a
# package, so reaching it means loading `test_marker_uniqueness` by path and
# registering it in `sys.modules` under the name pytest collects that same file
# by -- a duplicate-module collision in any run that collects both. Nothing
# compares the three copies, so a change to the shape ships from whichever file
# is edited last: the pattern belongs in the shared harness the sibling contracts
# keep naming as the honest fix, and until that exists three copies with the
# reason written down beats a suite that cannot be run whole.
MARKER_TOKEN = re.compile(r"\[([A-Z][A-Z ]{2,}):")

# Wake's six criteria, whose single definition is `## The INVEST gate` in
# `requirements-template.md`, and the most of them a file here may name.
#
# One rather than none, because each is an ordinary English word before it is a
# criterion and a file may reach for "Small" or "Valuable" at the start of a
# sentence without having copied anything. Two together is a restatement in
# progress: nobody names a second criterion except while listing them.
INVEST_CRITERIA = ("Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable")
INVEST_CRITERIA_CEILING = 1


def _shipped_files() -> list[Path]:
    """Every file this skill puts in front of a run, in a stable order.

    Shipped means read at run time: the body, the two references it sends a run
    to, and the scripts it invokes. Tests and their fixtures are excluded and the
    exclusion is deliberate rather than an oversight -- the fixtures are captured
    GitHub responses holding arbitrary third-party strings, so a bracketed token
    or a stamped path inside one is a fact about somebody's repository and not a
    defect in anything this skill ships.
    """
    return [SKILL_MD, *sorted(REFERENCES.glob("*.md")), *sorted(SCRIPTS.glob("*.py"))]


def _load(name: str) -> Any:
    """Import one of this skill's scripts by path, the way its siblings do.

    The scripts are a plugin's payload rather than an installed package, so there
    is no import path to reach them by and every test module in this suite loads
    them like this.
    """
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader, f"could not load {name} from {SCRIPTS}"
    module = importlib.util.module_from_spec(spec)
    # Registered before it is executed, for the reason this suite's other loaders
    # give: `@dataclass` resolves the string annotations that
    # `from __future__ import annotations` produces through
    # `sys.modules[cls.__module__]`, and an unregistered module makes that lookup
    # return None mid-decoration.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _headings(markdown: str) -> list[tuple[int, str, int]]:
    """Every ATX heading in `markdown` as (level, text, line number).

    Line numbers are **1-based**, matching what an editor shows. That is the
    contract `_section_body` depends on, since `str.splitlines()` is 0-based: a
    heading reported at `n` sits at `lines[n - 1]`, so `lines[n]` is already the
    first line under it.

    Lines inside a fenced block are skipped, and here that is load-bearing rather
    than defensive: `story-map-template.md` shows a whole slice for shape, fence
    and frontmatter and a `## Context` heading included. Counted as a heading of
    the template's own, that example would end the section above it early and
    take the frontmatter table out of scope with it.

    Whole-line matching is what separates a heading from one demoted a level:
    `## Required keys` is a substring of `### Required keys`, so a substring
    search would report a section this file had demoted under some other parent.
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
    """The lines the section called `name` contains, as raw lines.

    Finds the heading at whatever level it sits at and bounds the body at the
    next heading of that level or above -- never at the end of the file. Reading
    to the end instead would let a later section answer for this one, which is
    the failure that matters at every call site here: the schema table below
    sits under `### Required keys` and is immediately followed by
    `### Optional keys`, whose rows are exactly the keys the schema says are
    *not* required.

    The two bounds are asymmetric because `_headings` counts from 1 while
    `str.splitlines()` counts from 0. The start needs no adjustment and the stop
    subtracts one to leave out the heading that ends the section, so both ends
    exclude a heading -- which is what makes this a body rather than a span.

    Spans the first heading of that name, and comes back empty for a name no
    heading carries. Every caller below guards the empty case, because a renamed
    heading would otherwise be reported as a missing table or an empty section
    rather than as the rename it is.
    """
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
    """The first markdown table in `body`, as one cell list per row.

    A table is a run of consecutive lines starting with `|`, so prose ends it and
    a second table further down the section is not read. Header row first, with
    the `|---|` alignment row dropped and backticks stripped from every cell --
    code-spanning a key name is a formatting choice, not a renamed key.

    Comes back empty for a body carrying no table, which the caller must guard: a
    key comparison against no rows would report the template as publishing an
    empty schema rather than as having lost its table.
    """
    rows: list[list[str]] = []
    for line in body:
        if not line.lstrip().startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        # Checked only once a header is in hand, so a table whose first line
        # happens to be dashes still reports that line as its header rather than
        # discarding it and promoting a data row into its place.
        if rows and set("".join(cells)) <= set("-:"):
            continue
        rows.append(cells)
    return rows


def _plugin_directory_name() -> str:
    """The directory an installed copy of this plugin sits in, per its manifest.

    Read rather than restated, so that renaming the plugin moves the stamped-path
    scan with it instead of leaving it hunting for a string that no longer occurs
    anywhere -- a scan which then passes on every file forever.

    Returns "" when the manifest names nothing, which the caller must guard: a
    pattern built from an empty name would match any path carrying a version
    segment at all, and reporting those is worse than reporting the manifest.
    """
    return json.loads(PLUGIN_MANIFEST.read_text()).get("name", "")


def _invest_criteria_named(path: Path) -> list[str]:
    """Which of Wake's six criteria `path` writes out, sorted, without repeats.

    Whole words, so "Independently" and "Smaller" are ordinary prose rather than
    the criteria they contain. Distinct rather than counted, because a file that
    says "Small" three times has still named one criterion, and it is how many of
    the six a file reaches for that separates a sentence from a restatement.
    """
    text = path.read_text()
    return sorted(criterion for criterion in INVEST_CRITERIA if re.search(rf"\b{criterion}\b", text))


def _published_marker_token() -> str:
    """The unknown marker's bare token, read from the substrate's own definition.

    Returns "" when the definition cannot be read, which the caller must guard:
    an expectation derived from nothing would hold every shipped token against an
    empty string and report a fork in files that had never spelled the marker.
    """
    match = MARKER_TOKEN.search("\n".join(_section_body(ARTIFACT_FAMILY.read_text(), UNKNOWN_MARKER_SECTION)))
    return match.group(1) if match else ""


def test_skill_cites_plugin_root_and_never_a_stamped_path() -> None:
    """A run can reach every file this skill sends it to, wherever it is installed.

    Three ways that fails, all of them invisible to the session that introduces
    them. A path spelled without `${CLAUDE_PLUGIN_ROOT}` resolves against the
    user's own repository, where nothing this plugin ships exists. A path spelled
    with it but pointing at a file the plugin does not ship is a redirect to
    nothing, which is worse than no redirect at all -- it tells a run a rule
    exists somewhere and gives it nowhere to read it. And a path carrying a
    version stamp works in the cache it was copied from and breaks on the next
    release, for everybody except the person who wrote it.

    The stamp is scanned across every shipped file rather than `SKILL.md` alone.
    A reference file is read by a run just as the body is, and a stamped path in
    one fails the same way a beat later.

    Two of the three checks are negative sweeps, so both patterns are held
    against a known-bad path before either is trusted on the real files. A
    pattern that had stopped matching would otherwise report a clean skill
    forever, and the failure it reports -- nothing -- looks exactly like success.
    """
    assert SKILL_MD.is_file(), f"missing shipped skill body: {SKILL_MD}"
    assert PLUGIN_MANIFEST.is_file(), (
        f"missing plugin manifest: {PLUGIN_MANIFEST}. The stamped-path scan is built from "
        f"the directory name it declares, so nothing below is a check on anything without it"
    )

    skill = SKILL_MD.read_text()

    # The vacuity guard, and the reason it comes first: every check below is over
    # citations found in the text, so a body that had lost all of them would pass
    # each one while sending a run nowhere.
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

    # The scanners' own guard, before either is swept over anything. `REFERENCES`
    # is used as the sample because it is a real path into this plugin's tree, so
    # the bad spellings below are the two an author actually produces: the path as
    # the repository holds it, and the path as an installed cache hands it over.
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
    """The body still tells a second run what it may not do to an existing folder.

    Publishing it is the whole of the enforcement, which is why its absence is
    worth a test on its own. Slice ids are cited from outside this folder -- by
    other slices and by whatever was filed to a tracker -- and the chain's
    freshness mechanism compares an upstream's content hash and never inspects a
    downstream identifier. A re-run that tidied the numbering would therefore
    leave every member reporting `fresh` while every citation into the folder
    pointed at different work, and nothing in this suite would say so.

    Exactly once, not merely present: a body carrying the heading twice has split
    the promise in half, and a reader who opens the first one is told less than
    the rule says.
    """
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
    """The rubric publishes a fleet `product-review` can actually launch.

    Two properties under one name, because a review needs both and neither is
    worth shipping alone. The spine is what an orchestrator quotes a section out
    of, so a renamed heading leaves a caller quoting nothing. The clusters are
    what it fans out over -- one finder each -- so their number is how wide a
    review of a slice set goes and what it leaves unasked.

    A floor rather than an equality. The sibling rubrics pin an exact count
    because their caller was sized against them in the same commit; here the
    caller counts whatever it finds, so a fifth cluster is a wider review and
    only a fourth removed is a question nobody asks again.

    The cluster names are deliberately not asserted. Replacing all four with four
    others of the same shape passes here, because the names are prose a reader
    reviews and pinning them would freeze wording that ought to improve.
    """
    assert ISSUES_PRINCIPLES.is_file(), f"missing shipped rubric: {ISSUES_PRINCIPLES}"

    principles = ISSUES_PRINCIPLES.read_text()
    h2 = [(text, line) for depth, text, line in _headings(principles) if depth == 2]
    h2_names = [text for text, _line in h2]

    # Exactly once, not merely present: an orchestrator quoting a section by name
    # gets one of them, and a rubric carrying the heading twice has split a
    # section nobody can quote whole. It is also what makes the mapping below
    # safe, since collapsing to a dict keeps only the last of a repeated name.
    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' exactly once as an H2 in {ISSUES_PRINCIPLES.name}, "
            f"found {occurrences}; the file shares its heading spine with this suite's other "
            f"rubrics so an orchestrator can quote one section by name, and it carries "
            f"{h2_names}"
        )

    # The order is the reading path a maintainer takes top to bottom: who this is
    # borrowed from, then how to author, then how to review, then how to change
    # the file. Asserted on the line numbers so the check is about sequence and
    # not about what sits between the sections.
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
    """The gate is pointed at, and nowhere in this skill written out again.

    Both halves are needed and neither is worth shipping alone. Without the
    citation a run passes slices through a gate it half remembers; without the
    ban a second copy of a six-part checklist starts diverging one letter at a
    time, and neither copy looks wrong on its own.

    The ban is swept across every shipped file rather than the template alone.
    The template is where a restatement would be most natural, but a run reads
    the body and the rubric too, and a copy in either of those is the same two
    definitions with no rule for choosing between them.

    The ban is a negative sweep, so the gate's own file is run through it first
    as a positive control. A search that had stopped recognising a criterion
    would report every shipped file abstaining, which is indistinguishable from
    the clean skill this is meant to prove.
    """
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

    # The sweep's positive control, and the gate's own file is the honest one to
    # use: it is the document that does restate the criteria, because it is where
    # they are defined. Without it the ban below is a search that would report
    # every file abstaining if the criteria tuple were emptied or the word
    # matching broke -- the one failure that looks exactly like a clean skill.
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
    """No file this skill ships forks a marker dialect of its own.

    The suite has one literal for "nobody has established this value yet", and it
    is published by the substrate. A second token is not a stylistic slip: this
    beat refuses a whole batch over a slice still carrying the marker, so a slice
    written with a fork sails through pre-flight and gets filed against somebody's
    tracker with the open question still in it.

    `tests/test_marker_uniqueness.py` owns the same ban across the tree's
    markdown and this does not duplicate it. That module globs `*.md`, so the one
    file it cannot see is `scripts/preflight.py` -- which reads the token out of
    the substrate at run time precisely so the code holds no copy of it, and whose
    tempting simplification is the hardcoded literal that would put the fork
    somewhere the repo-level scan never looks.
    """
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
    """The published schema and the reader's copy of it still agree.

    `story-map-template.md` is the schema's single home -- it is what an author
    writes a slice from -- while `slice_file.REQUIRED_KEYS` is what refuses a
    slice that is missing one. Two lists, one edited by whoever changes the shape
    and the other by whoever changes the parser, and a key added to either alone
    is a slice set that either passes a reader nothing will accept or is refused
    for a key nobody was told to write.

    The expectation is parsed back out of the template rather than written here,
    the way the substrate's own suite reads the chain members out of the contract
    it checks `MEMBERS` against. A list typed into this module would be a third
    copy, and a third copy can agree with the code while the document a human
    reads has drifted away from both.

    Order is part of the equality, because the template publishes these keys as
    the order a slice states them in and `write_filed_entry` promises to leave
    the existing key order alone.
    """
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
