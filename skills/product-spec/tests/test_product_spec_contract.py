
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent.parent
REFERENCES = SKILL_ROOT / "references"
SPEC_TEMPLATE = REFERENCES / "spec-template.md"

SKILL_MD = SKILL_ROOT / "SKILL.md"
SUBSTRATE_SCRIPT = SKILL_ROOT.parent / "product-artifacts" / "scripts" / "product_artifact.py"

SPEC_PRINCIPLES = REFERENCES / "product-spec-principles.md"

ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"

SPEC_SECTION_BULLET = re.compile(r"^- `spec\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

PROVENANCE_ENTRY_POINT = "--provenance-line"

PROVENANCE_STATEMENTS = ("do not assemble", "do not compute a sha")

DECLARED_TABLES = {
    "Requirements in scope": ("ID", "Acceptance condition", "Traces to"),
    "Non-goals": ("Non-goal", "Origin", "Cost of excluding it"),
}

FRONT_MATTER_FENCE = "---"

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


ATTRIBUTION_SECTION = "Attribution and scope"
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    ATTRIBUTION_SECTION,
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

CLUSTER_LEVEL = 3
RED_FLAG_CLUSTER_COUNT = 5

SEVERITY_HINT = "Severity hint:"

SHAPE_UP_SOURCE = "1.5-chapter-06"
HOHPE_SOURCE = "Is This Architecture?"
BMAD_SOURCE = "docs.bmad-method.org"
ATTRIBUTION_CITATIONS = (SHAPE_UP_SOURCE, HOHPE_SOURCE, BMAD_SOURCE)

NON_AFFILIATION = "not affiliated"

BMAD_CAVEAT = "partial"

UNSUPPORTED_SUB_CLAIM = "Look for Decisions!"

PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"
REQUIREMENTS_PRINCIPLES = (
    SKILL_ROOT.parent / "product-requirements" / "references" / "product-requirements-principles.md"
)


def _plugin_root_citation(path: Path) -> str:
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


NEIGHBOUR_CITATIONS = {
    path: _plugin_root_citation(path)
    for path in (SPEC_TEMPLATE, ARTIFACT_FAMILY, REQUIREMENTS_PRINCIPLES)
}

SKILL_CITATIONS = {
    path: _plugin_root_citation(path) for path in (SPEC_TEMPLATE, SPEC_PRINCIPLES, ARTIFACT_FAMILY)
}

UNKNOWN_MARKER_PREFIX = "[UNKNOWN:"

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

FORBIDDEN_ENTRY_POINT = "--ensure-folder"

FLAG = re.compile(r"--[a-z][a-z-]*")
DECLARED_FLAG = re.compile(r"""add_argument\(\s*["'](--[a-z][a-z-]*)["']""")

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

REQUIRED_FRONTMATTER_KEYS = (
    (
        "argument-hint",
        "the slug is the one argument this beat cannot guess, since it names a folder "
        "somebody else made -- a user shown no hint is the user step 1 has to stop and "
        "ask, which is a round trip the hint would have saved",
    ),
)

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

REFUSAL_SECTION = "Step 1: Refuse unless requirements conform"
REFUSAL_BEAT = "product-requirements"

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

NOT_A_REFUSAL_STATE = "stale"
NOT_A_REFUSAL_PHRASE = "not one of the three"


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


def _table(body: list[str]) -> list[list[str]]:
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


def _paragraphs(body: list[str]) -> list[str]:
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
    bullet = SPEC_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _frontmatter_and_body(skill: str) -> tuple[str, str]:
    if not skill.startswith("---"):
        return "", skill
    end = skill.find("\n---", 3)
    if end == -1:
        return "", ""
    return skill[3:end], skill[end + len("\n---") :]


def _frontmatter_keys(frontmatter: str) -> dict[str, str]:
    keys: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line or line[0].isspace():
            continue
        key, separator, value = line.partition(":")
        if separator:
            keys.setdefault(key, value.strip().strip("\"'"))
    return keys


def _prose(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def _invocations(body: str) -> list[str]:
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
    lines = markdown.splitlines()
    headings = _headings(markdown)
    return "\n".join(_section_body(lines, _section_span(headings, 2, name, len(lines))))


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", _prose(text))


def test_spec_template_follows_the_published_member_shape() -> None:
    assert SPEC_TEMPLATE.exists(), f"missing shipped template: {SPEC_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = SPEC_TEMPLATE.read_text()

    published = _spec_section_names(substrate)
    assert published, (
        f"no spec.md section bullet found in {ARTIFACT_FAMILY.name} under "
        f"{SPEC_SECTION_BULLET.pattern!r}; the template's headings are checked against "
        f"that bullet, so nothing below is a check on anything until it parses"
    )

    lines = template.splitlines()
    headings = _headings(template)
    h2_names = [text for depth, text, _line in headings if depth == 2]

    assert h2_names == published, (
        f"{SPEC_TEMPLATE.name} carries the H2 sections {h2_names}, but "
        f"{ARTIFACT_FAMILY.name} publishes {published} for spec.md, in that order. The "
        f"substrate owns these names -- the template renders them and never decides them "
        f"-- so this is the template to change, not the bullet"
    )

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
    assert SPEC_PRINCIPLES.exists(), f"missing shipped rubric: {SPEC_PRINCIPLES}"

    principles = SPEC_PRINCIPLES.read_text()
    lines = principles.splitlines()
    headings = _headings(principles)
    h2 = [(text, line) for depth, text, line in headings if depth == 2]
    h2_names = [text for text, _line in h2]

    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{SPEC_PRINCIPLES.name}, found {occurrences}; the file shares its heading "
            f"spine with the suite's other rubrics so that an orchestrator can quote one "
            f"section by name, and it carries {h2_names}"
        )

    h2_line = dict(h2)
    spine_lines = [h2_line[section] for section in PRINCIPLES_SPINE]
    assert spine_lines == sorted(spine_lines), (
        f"{SPEC_PRINCIPLES.name} must carry its spine sections in the order "
        f"{list(PRINCIPLES_SPINE)}, the order its sibling rubrics use; found them at "
        f"lines {spine_lines}"
    )

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

    assert UNSUPPORTED_SUB_CLAIM not in principles, (
        f"{SPEC_PRINCIPLES.name} names {UNSUPPORTED_SUB_CLAIM!r}. The book chapter cited "
        f"in '## {ATTRIBUTION_SECTION}' is not openly readable and nothing consulted "
        f"established that it carries a section of that name -- the phrase belongs to an "
        f"accessible precursor essay, and lifting it into the book's citation turns a "
        f"careful attribution into an invented one"
    )

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

    assert body.strip(), (
        f"{SKILL_MD.name} yielded no body to read. Either the file is empty or it opens a "
        f"{FRONT_MATTER_FENCE!r} frontmatter block and never closes it, which leaves the "
        f"harness reading the whole file as frontmatter and a run with no instructions at "
        f"all"
    )

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
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    _frontmatter, body = _frontmatter_and_body(SKILL_MD.read_text())

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
