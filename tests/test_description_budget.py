
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def _load_guarantees() -> ModuleType:
    spec = importlib.util.spec_from_file_location("guarantees", HERE / "guarantees.py")
    assert spec and spec.loader, f"cannot load {HERE / 'guarantees.py'}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guarantees = _load_guarantees()



DESCRIPTION = "Plans a change before building it."
WHEN_TO_USE = "Use when the user asks for a plan."


def _skill_file(*fields: str) -> str:
    return "---\n" + "\n".join(fields) + "\n---\n\n# Body\n\nProse the listing never shows.\n"


def test_listing_entry_reports_what_reaches_the_listing() -> None:
    excluded = guarantees.listing_entry(
        _skill_file(f"description: {DESCRIPTION}", "disable-model-invocation: true")
    )
    assert excluded is None, (
        f"`disable-model-invocation: true` is documented as removing the skill from "
        f"Claude's context entirely, so such a file contributes nothing and "
        f"`listing_entry` must report None. It returned {excluded!r}, which an aggregate "
        f"sum would charge to a budget the harness never spends on this skill -- and the "
        f"flag is the plan's one documented lever for getting back under that budget"
    )

    menu_hidden = guarantees.listing_entry(
        _skill_file(f"description: {DESCRIPTION}", "user-invocable: false")
    )
    assert menu_hidden == DESCRIPTION, (
        f"`user-invocable: false` hides a skill from the slash menu only; its documented "
        f"row reads 'Description always in context'. Expected {DESCRIPTION!r}, got "
        f"{menu_hidden!r}. Excluding it the way `disable-model-invocation` is excluded "
        f"would under-count the listing, so the aggregate would pass while over budget"
    )

    combined = guarantees.listing_entry(
        _skill_file(f"description: {DESCRIPTION}", f"when_to_use: {WHEN_TO_USE}")
    )
    assert combined is not None and combined.startswith(DESCRIPTION) and combined.endswith(WHEN_TO_USE), (
        f"`when_to_use` is documented as appended to `description` in the listing and as "
        f"counting toward the same cap, so the entry is the two in that order. Expected "
        f"{DESCRIPTION!r} then {WHEN_TO_USE!r}, got {combined!r}. Dropping or reordering "
        f"either half measures a string no session is actually paying for"
    )

    description_only = guarantees.listing_entry(_skill_file(f"description: {DESCRIPTION}"))
    assert description_only == DESCRIPTION, (
        f"a skill with no `when_to_use` contributes its description and nothing else. "
        f"Expected {DESCRIPTION!r}, got {description_only!r}. A result carrying the "
        f"literal 'None', or a trailing separator, is the absent key being formatted "
        f"into the entry instead of skipped, which bills the budget for punctuation"
    )


LISTED_SKILLS = tuple(
    str(path.relative_to(REPO)) for path in sorted((REPO / "skills").glob("*/SKILL.md"))
)
AGENTS = tuple(str(path.relative_to(REPO)) for path in sorted((REPO / "agents").glob("*.md")))
ALWAYS_RESIDENT = LISTED_SKILLS + AGENTS

assert LISTED_SKILLS, f"no skills found under {REPO / 'skills'}"
assert AGENTS, f"no agents found under {REPO / 'agents'}"


@pytest.mark.parametrize("relative_path", LISTED_SKILLS, ids=lambda p: p)
def test_listing_entries_fit_the_harness_cap(relative_path: str) -> None:
    entry = guarantees.listing_entry((REPO / relative_path).read_text(encoding="utf-8"))
    if entry is None:
        pytest.skip(
            f"{relative_path} sets `disable-model-invocation: true`, so it has no "
            f"listing entry for the cap to apply to"
        )

    cap = guarantees.BUDGETS["listing_entry_chars"]
    assert len(entry) <= cap, (
        f"{relative_path}: `description` and `when_to_use` together are {len(entry)} "
        f"characters, over the {cap}-character cap on one listing entry. Past the cap "
        f"the harness truncates, so whatever routing keywords sit at the tail stop "
        f"reaching the router: put the key use case first and shorten what follows. "
        f"Raising BUDGETS['listing_entry_chars'] is not an option -- it is the "
        f"harness's number, not ours"
    )


@pytest.mark.parametrize("relative_path", ALWAYS_RESIDENT, ids=lambda p: p)
def test_descriptions_fit_the_routing_budget(relative_path: str) -> None:
    text = (REPO / relative_path).read_text(encoding="utf-8")
    description = guarantees.scalar_text(guarantees.frontmatter_value(text, "description"))
    assert description, (
        f"{relative_path} has no frontmatter `description` with any text in it, so "
        f"there is nothing to measure and the budget below would pass vacuously. A "
        f"skill or agent without one is also unroutable"
    )

    budget = guarantees.BUDGETS["description_words"]
    words = len(description.split())
    assert words <= budget, (
        f"{relative_path}: `description` is {words} words, over the {budget}-word "
        f"routing budget. Every session pays for it whether or not this is ever "
        f"invoked, so state the condition under which it should be picked and stop; "
        f"mechanics -- which phase launches it, which script it calls -- belong in the "
        f"body, which costs nothing until then"
    )




def test_plugin_listing_total_fits_the_shared_budget() -> None:
    measured = {
        relative_path: guarantees.listing_entry((REPO / relative_path).read_text(encoding="utf-8"))
        for relative_path in LISTED_SKILLS
    }
    entries = {path: entry for path, entry in measured.items() if entry is not None}
    total = sum(len(entry) for entry in entries.values())

    assert entries and total > 0, (
        f"nothing was weighed: {len(measured)} file(s) matched skills/*/SKILL.md, "
        f"{len(entries)} of them reach the listing, and together they are {total} "
        f"characters. Either the glob stopped matching, or every skill now sets "
        f"`disable-model-invocation: true`, or their descriptions are empty. The ceiling "
        f"below would pass on that empty sum rather than on a compliant one"
    )

    ceiling = guarantees.BUDGETS["listing_total_chars"]
    largest_first = sorted(entries.items(), key=lambda item: -len(item[1]))
    assert total <= ceiling, (
        f"the {len(entries)} listed skill(s) put {total} characters into the shared skill "
        f"listing, {total - ceiling} over the {ceiling} characters this plugin claims of "
        f"it. The listing is shared with every other installed plugin and with the user's "
        f"own skills, and the harness drops whole entries once it overflows, so this is "
        f"spent from someone else's routing as much as ours. Shorten the largest entries, "
        f"or set `disable-model-invocation: true` on one that is only ever reached by its "
        f"slash command -- the documented way to take an entry out of the listing "
        f"altogether:\n  "
        + "\n  ".join(f"{len(entry)} {path}" for path, entry in largest_first)
    )



PRODUCT_PREFIX = "product-"

PRODUCT_SKILLS = tuple(
    str(path.relative_to(REPO))
    for path in sorted((REPO / "skills").glob(f"{PRODUCT_PREFIX}*/SKILL.md"))
)

_SENTENCE_END = re.compile(r"\.(?=\s|$)")


def _trigger_rule_failure(description: str, token: str) -> str | None:
    end = _SENTENCE_END.search(description)
    sentence = description[: end.end()] if end else description
    if re.search(rf"\b{re.escape(token)}\b", sentence, re.IGNORECASE):
        return None
    return f"its first sentence, {sentence!r}, never names {token!r}"


def test_first_sentence_carries_the_skill_noun() -> None:
    leads = _trigger_rule_failure("Writes the product spec from a brief. Reads the roadmap.", "spec")
    assert leads is None, (
        f"a first sentence naming its own token is the whole rule, so this must pass. "
        f"It was rejected with: {leads}. A rule that cannot be satisfied by an obeying "
        f"description is a rule every sibling's author has to route around"
    )

    buried = _trigger_rule_failure("Use when the user is planning a release. It writes the spec.", "spec")
    assert buried is not None, (
        "a description naming its token only in a later sentence was accepted. First "
        "sentences are what the siblings share and what the router weighs first, so a "
        "whole-description match would pass eight descriptions that open identically"
    )
    assert "Use when the user is planning a release." in buried and "spec" in buried, (
        f"the rejection must quote the first sentence it read and name the token that "
        f"sentence lacked; without both, an author sees only that something is wrong. "
        f"Got: {buried}"
    )

    versioned = _trigger_rule_failure("Reads the v2.1.105 spec.", "spec")
    assert versioned is None, (
        f"the sentence ends at a period followed by whitespace or by the end of the "
        f"text, so the dots inside `v2.1.105` do not end it early. It was rejected "
        f"with: {versioned}. Splitting on a bare `.` truncates the sentence before the "
        f"token and reports a compliant description as broken"
    )


@pytest.mark.parametrize("relative_path", PRODUCT_SKILLS, ids=lambda p: p)
def test_product_skills_lead_with_their_own_noun(relative_path: str) -> None:
    token = Path(relative_path).parent.name.removeprefix(PRODUCT_PREFIX)
    assert token, (
        f"{relative_path} sits in a directory that is the bare prefix {PRODUCT_PREFIX!r}, "
        f"so the rule has no token to look for and would pass on every description. "
        f"A product skill's directory names what it owns"
    )

    text = (REPO / relative_path).read_text(encoding="utf-8")
    description = guarantees.scalar_text(guarantees.frontmatter_value(text, "description"))
    failure = _trigger_rule_failure(description, token)
    assert failure is None, (
        f"{relative_path}: {failure}. The model routes between the adjacent product-* "
        f"skills on this text alone, so each has to name the thing it owns before it "
        f"says anything its siblings also say: put {token!r} in the first sentence, "
        f"which is where a reader and a router both look. The token is the directory "
        f"name without its {PRODUCT_PREFIX!r} prefix and is not configurable -- a skill "
        f"whose description cannot naturally say it is a skill whose folder is misnamed"
    )
