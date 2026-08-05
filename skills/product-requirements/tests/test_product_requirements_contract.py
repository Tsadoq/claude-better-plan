
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

REPO_ROOT = SKILL_ROOT.parents[1]

ARTIFACT_FAMILY = SKILL_ROOT.parent / "product-artifacts" / "references" / "artifact-family.md"

REQUIREMENTS_SECTION_BULLET = re.compile(r"^- `requirements\.md`:(.*(?:\n[ \t]+\S.*)*)$", re.MULTILINE)
BACKTICKED_H2 = re.compile(r"`(## [^`]+)`")

PLUGIN_ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"


def _plugin_root_citation(path: Path) -> str:
    return f"{PLUGIN_ROOT_VARIABLE}/{path.relative_to(REPO_ROOT).as_posix()}"


ARTIFACT_FAMILY_CITATION = _plugin_root_citation(ARTIFACT_FAMILY)

UNKNOWN_MARKER_HEADING = "## Unknown marker"
UNKNOWN_MARKER_NAME = UNKNOWN_MARKER_HEADING.removeprefix("## ").lower()
FENCED_BLOCK = re.compile(r"```\n(.+?)\n```", re.DOTALL)

NESTED_SECTIONS = {
    "Scope": ("The system name", "Opportunity coverage"),
    "Requirements": ("Functional requirements", "Non-functional requirements"),
    "Out of scope": (
        "Opportunities not addressed",
        "Quality characteristics not applicable",
    ),
}

ID_NUMBER_PLACEHOLDER = "<n>"
ID_FORM = f"REQ{ID_NUMBER_PLACEHOLDER}"

COVERAGE_SECTION = "Opportunity coverage"
REQUIREMENT_COLUMNS = ("ID", "Pattern", "Requirement", "Traces to", "Source")
DECLARED_TABLES = {
    COVERAGE_SECTION: ("Opportunity", "Covered by", "Note"),
    "Functional requirements": REQUIREMENT_COLUMNS,
    "Non-functional requirements": REQUIREMENT_COLUMNS,
}

NOT_ADDRESSED = "not addressed"

NOTATION_SECTION = "The EARS notation"

EARS_PATTERNS: tuple[tuple[str, tuple[str, ...] | None], ...] = (
    ("Ubiquitous requirements", None),
    ("Event-driven requirements", ("WHEN",)),
    ("State-driven requirements", ("WHILE",)),
    ("Unwanted behaviour requirements", ("IF", "THEN")),
    ("Optional feature requirements", ("WHERE",)),
)

EARS_KEYWORDS = tuple(keyword for _pattern, keywords in EARS_PATTERNS for keyword in keywords or ())

COMPLEX_SYNTAX_SECTION = "Complex requirement syntax"

NOTATION_SECTIONS = (*(pattern for pattern, _keywords in EARS_PATTERNS), COMPLEX_SYNTAX_SECTION)

MODAL_VERB = "SHALL"
SLOT = "<"

GENERIC_FORM_NOTE = "Clause order is significant"

NON_FUNCTIONAL_REUSE = "Non-functional requirements are written in this pattern"

GENERIC_FORM = "<optional preconditions> <optional trigger> the <system name> shall <system response>"

CASING_SECTION = "Casing"

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

CHECKLIST_SECTION = "The quality characteristic checklist"

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

ISO_CHARACTERISTIC_COUNT = 9

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

THRESHOLD_SOURCE_RULE = "A threshold with no source"

JUSTIFICATION_RULE = "justification a reader could disagree with"

PARAPHRASE_DISCLOSURE = "paraphrase, not quotation"

SAFETY_CHARACTERISTIC = "Safety"
SAFETY_RULE = "takes a stated reason"

INVEST_SECTION = "The INVEST gate"

INVEST_LETTERS = (
    "Independent",
    "Negotiable",
    "Valuable",
    "Estimable",
    "Small",
    "Testable",
)

INVEST_ACRONYM = "INVEST"

INVEST_GLOSS_MIN_WORDS = 4

SINGLE_DEFINITION_CLAIM = "the suite's single INVEST definition"
CITING_BEAT = "#21"
CITE_NOT_COPY_RULE = "rather than copying it"

STORY_SHAPED_TERM = "story-shaped"
STORY_SHAPED_DEFINITION = "one deliverable unit"
STORY_SHAPED_EXEMPTION = "exempt from the gate rather than failing it"

INVEST_SOURCE = "Wake"

ATTRIBUTION_SECTION = "Attribution and scope"
RED_FLAGS_SECTION = "Review-time red flags"
PRINCIPLES_SPINE = (
    ATTRIBUTION_SECTION,
    "Plan-time principles",
    RED_FLAGS_SECTION,
    "How to update these guidelines",
)

RED_FLAG_CLUSTER_COUNT = 5

SEVERITY_HINT = "Severity hint:"

CLUSTER_DERIVATIONS: dict[str, tuple[str, ...]] = {
    "Ambiguity and vagueness": ("ambiguity", "vagueness"),
    "Compound requirements": ("complexity",),
    "Unverifiable requirements": ("untestability",),
    "Smuggled implementation": ("inappropriate implementation",),
    "Omission and duplication": ("omission", "duplication"),
}

PAPER_PROBLEM_COUNT = 8
UNCLUSTERED_PROBLEM = "wordiness"

PAPER_ATTRIBUTION = ("Mavin", "RE'09", "not affiliated")

DESIGN_PRINCIPLES = REPO_ROOT / "skills" / "design-review" / "references" / "design-principles.md"
DEFERRED_DESIGN_CLUSTERS = ("Naming", "Comments and obviousness")

DESIGN_PRINCIPLES_CITATION = _plugin_root_citation(DESIGN_PRINCIPLES)
REQUIREMENTS_TEMPLATE_CITATION = _plugin_root_citation(REQUIREMENTS_TEMPLATE)

TRACEABILITY_CLUSTER = "Omission and duplication"

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


def _table_cells(row: str) -> list[str]:
    return [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]


def _table(body: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body:
        if not line.lstrip().startswith("|"):
            if rows:
                break
            continue
        cells = _table_cells(line)
        if rows and set("".join(cells)) <= set("-:"):
            continue
        rows.append(cells)
    return rows


def _requirements_section_names(substrate: str) -> list[str]:
    bullet = REQUIREMENTS_SECTION_BULLET.search(substrate)
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


def _unwrapped(lines: list[str]) -> str:
    return " ".join("\n".join(lines).split())


def _fenced_lines(body: list[str]) -> list[str]:
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
    if not skill.startswith("---"):
        return skill
    end = skill.find("\n---", 3)
    return "" if end == -1 else skill[end + len("\n---") :]


def _require_h2_span(template: str, section: str, purpose: str) -> tuple[int, int]:
    headings = _headings(template)
    h2_names = [text for text, _ in _at_level(headings, 2)]
    assert h2_names.count(section) == 1, (
        f"expected '## {section}' to appear exactly once as an H2 in "
        f"{REQUIREMENTS_TEMPLATE.name}, found {h2_names.count(section)}; it is "
        f"{purpose}, and the template has {h2_names}"
    )
    return _section_span(headings, 2, section, len(template.splitlines()))


def _require_notation_span(template: str) -> tuple[int, int]:
    return _require_h2_span(
        template,
        NOTATION_SECTION,
        "where the grammar every requirement is written in is stated",
    )


def _require_checklist_span(template: str) -> tuple[int, int]:
    return _require_h2_span(
        template,
        CHECKLIST_SECTION,
        "where the non-functional surface is enumerated so that it is something a "
        "reader can check rather than whatever the author thought of",
    )


def _require_invest_span(template: str) -> tuple[int, int]:
    return _require_h2_span(
        template,
        INVEST_SECTION,
        f"{SINGLE_DEFINITION_CLAIM}, which issue {CITING_BEAT} cites instead of carrying its own",
    )


def _cluster_spans(principles: str) -> list[tuple[str, tuple[int, int]]]:
    headings = _headings(principles)
    section_start, section_end = _section_span(headings, 2, RED_FLAGS_SECTION, len(principles.splitlines()))
    clusters = [(text, line) for text, line in _at_level(headings, 3) if section_start < line < section_end]
    if not clusters:
        return []
    stops = [line for _name, line in clusters[1:]] + [section_end]
    return [(name, (start, stop)) for (name, start), stop in zip(clusters, stops, strict=True)]


def _guarantees() -> ModuleType:
    source = REPO_ROOT / "tests" / "guarantees.py"
    spec = importlib.util.spec_from_file_location("guarantees", source)
    assert spec and spec.loader, f"cannot load {source}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_prompts_every_iso_25010_characteristic() -> None:
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
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    checklist_start, checklist_end = _require_checklist_span(template)

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
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    gate = _section_body(lines, _require_invest_span(template))

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
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    h3_names = [text for text, _ in _at_level(headings, 3)]
    notation_start, notation_end = _require_notation_span(template)

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
    assert REQUIREMENTS_TEMPLATE.exists(), f"missing shipped template: {REQUIREMENTS_TEMPLATE}"

    template = REQUIREMENTS_TEMPLATE.read_text()
    lines = template.splitlines()
    headings = _headings(template)
    notation = _unwrapped(_section_body(lines, _require_notation_span(template)))

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

    h2_line = dict(h2)
    ordered = [h2_line[name] for name in required_sections]
    assert ordered == sorted(ordered), (
        f"{REQUIREMENTS_TEMPLATE.name} must carry requirements.md's sections in "
        f"the order {ARTIFACT_FAMILY.name} publishes {required_sections}; found "
        f"them at lines {ordered}"
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
    assert REQUIREMENTS_PRINCIPLES.exists(), f"missing shipped rubric: {REQUIREMENTS_PRINCIPLES}"

    principles = REQUIREMENTS_PRINCIPLES.read_text()
    lines = principles.splitlines()
    headings = _headings(principles)
    h2 = _at_level(headings, 2)
    h2_names = [text for text, _ in h2]

    for section in PRINCIPLES_SPINE:
        occurrences = h2_names.count(section)
        assert occurrences == 1, (
            f"expected '## {section}' to appear exactly once as an H2 in "
            f"{REQUIREMENTS_PRINCIPLES.name}, found {occurrences}; it shares its heading "
            f"spine with the plugin's other rubric files so that an orchestrator can "
            f"quote one section by name, and it has {h2_names}"
        )

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
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    skill = SKILL_MD.read_text()
    body = _acting_body(skill)
    assert body, (
        f"{SKILL_MD.name} opens a `---` frontmatter block that never closes, so the whole "
        f"file is frontmatter as far as the harness reads it and no rule below could be "
        f"satisfied by text a run acts on"
    )
    assert not re.search(r"^description:", body, re.MULTILINE), (
        f"{SKILL_MD.name}'s frontmatter survived into what `_acting_body` returned as its "
        f"body, so this module and tests/guarantees.py no longer agree on where the block "
        f"ends"
    )

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
    assert SKILL_MD.exists(), f"missing shipped skill body: {SKILL_MD}"

    skill = SKILL_MD.read_text()

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
