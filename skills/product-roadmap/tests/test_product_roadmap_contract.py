
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"
RICE_TEMPLATE = REFERENCES / "rice-template.md"
ROADMAP_PRINCIPLES = REFERENCES / "product-roadmap-principles.md"

SKILL_MD = SKILL_ROOT / "SKILL.md"
SUBSTRATE_SCRIPT = SKILL_ROOT.parent / "product-artifacts" / "scripts" / "product_artifact.py"

ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"

ROADMAP_SECTION_BULLET = re.compile(r"^- `roadmap\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

SCORED_ITEMS_SECTION = "Scored items"

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

COVERAGE_TABLE_COLUMNS = ("Requirement", "Covered by")

DECLARED_TABLES = (
    ("the scored-items table", SCORE_TABLE_COLUMNS),
    ("the requirement-coverage table", COVERAGE_TABLE_COLUMNS),
)

NOT_COVERED_LITERAL = "not covered"

RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    "Attribution and scope",
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

CLUSTER_LEVEL = 3
RED_FLAG_CLUSTER_COUNT = 5

SEVERITY_HINT = "Severity hint:"

ATTRIBUTION_SECTION = "Attribution and scope"
ATTRIBUTION_CITATIONS = (
    "intercom.com/blog/rice-simple-prioritization-for-product-managers/",
    "basecamp.com/shapeup/1.2-chapter-03",
    "framework.scaledagile.com/wsjf/",
    "agilebusiness.org/dsdm-project-framework/moscow-prioritisation.html",
    "Attractive Quality and Must-Be Quality",
    "prodpad.com/blog/invented-now-next-later-roadmap/",
)

NON_AFFILIATION = "not affiliated"

REPO = SKILL_ROOT.parent.parent

PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


def _plugin_root_citation(path: Path) -> str:
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO).as_posix()}"


CITED_REFERENCES = (
    RICE_TEMPLATE,
    ARTIFACT_FAMILY,
    SKILL_ROOT.parent / "product-spec" / "references" / "product-spec-principles.md",
)

SKILL_CITATIONS = {
    path: _plugin_root_citation(path)
    for path in (RICE_TEMPLATE, ROADMAP_PRINCIPLES, ARTIFACT_FAMILY)
}

UNKNOWN_MARKER_SECTION = "Unknown marker"
MARKER_TOKEN = re.compile(r"\[([A-Z][A-Z ]{2,}):")

FRONT_MATTER_FENCE = "---"

REQUIRED_FRONTMATTER_KEYS = (
    (
        "argument-hint",
        "the slug is the one argument this beat cannot guess, since it names a folder "
        "somebody else made -- a user shown no hint is the user step 1 has to stop and "
        "ask, which is a round trip the hint would have saved",
    ),
)

FORBIDDEN_FRONTMATTER_KEY = "disable-model-invocation"

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

FLAG = re.compile(r"--[a-z][a-z-]*")
DECLARED_FLAG = re.compile(r"""add_argument\(\s*["'](--[a-z][a-z-]*)["']""")


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
        if current and set("".join(cells)) <= set("-:"):
            continue
        current.append(cells)
    return tables


def _roadmap_section_names(substrate: str) -> list[str]:
    bullet = ROADMAP_SECTION_BULLET.search(substrate)
    if bullet is None:
        return []
    return [h2.removeprefix("## ") for h2 in BACKTICKED_H2.findall(bullet.group(1))]


def _clusters(body: list[str]) -> list[tuple[str, list[str]]]:
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
    match = MARKER_TOKEN.search("\n".join(_section_body(substrate, UNKNOWN_MARKER_SECTION)))
    return match.group(1) if match else ""


def _frontmatter_and_body(skill: str) -> tuple[str, str]:
    if not skill.startswith(FRONT_MATTER_FENCE):
        return "", skill
    end = skill.find(f"\n{FRONT_MATTER_FENCE}", len(FRONT_MATTER_FENCE))
    if end == -1:
        return "", ""
    return skill[len(FRONT_MATTER_FENCE) : end], skill[end + len(FRONT_MATTER_FENCE) + 1 :]


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


def _section_prose(markdown: str, name: str) -> str:
    return _prose("\n".join(_section_body(markdown, name)))


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


def test_template_renders_the_substrate_section_schema() -> None:
    assert RICE_TEMPLATE.exists(), f"missing shipped template: {RICE_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

    substrate = ARTIFACT_FAMILY.read_text()
    template = RICE_TEMPLATE.read_text()

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

    member_h2 = h2_names[h2_names.index(published[0]) :]
    assert member_h2 == published, (
        f"{RICE_TEMPLATE.name} carries the member sections {member_h2}, but "
        f"{ARTIFACT_FAMILY.name} publishes {published} for roadmap.md, in that order. The "
        f"substrate owns these names -- the template renders them and never decides them "
        f"-- so this is the template to change, not the bullet"
    )


def test_template_declares_the_columns_its_tables_are_read_by() -> None:
    assert RICE_TEMPLATE.exists(), f"missing shipped template: {RICE_TEMPLATE}"
    assert ARTIFACT_FAMILY.exists(), f"missing substrate contract: {ARTIFACT_FAMILY}"

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

    coverage_cells = [cell for row in tables[1][1:] for cell in row]
    assert any(NOT_COVERED_LITERAL in cell for cell in coverage_cells), (
        f"no cell of the requirement-coverage table in {RICE_TEMPLATE.name} shows the "
        f"literal {NOT_COVERED_LITERAL!r}; its cells are {coverage_cells}. Without it the "
        f"only way to say no item covers a requirement is an empty cell, which is also "
        f"what an unfilled table looks like -- and telling those two apart is the whole "
        f"reason that table exists"
    )


def test_principles_expose_five_red_flag_clusters() -> None:
    assert ROADMAP_PRINCIPLES.exists(), f"missing shipped rubric: {ROADMAP_PRINCIPLES}"

    principles = ROADMAP_PRINCIPLES.read_text()
    h2 = [(text, line) for depth, text, line in _headings(principles) if depth == 2]
    h2_names = [text for text, _line in h2]

    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{ROADMAP_PRINCIPLES.name}, found {occurrences}; the file shares its heading "
            f"spine with the suite's other rubrics so that an orchestrator can quote one "
            f"section by name, and it carries {h2_names}"
        )

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
    assert SKILL_MD.exists(), (
        f"missing shipped skill body: {SKILL_MD}. Without it there is no gate to check, "
        f"and no beat either"
    )

    frontmatter, body = _frontmatter_and_body(SKILL_MD.read_text())

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
