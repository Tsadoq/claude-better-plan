"""Budgets over the text this plugin puts into Claude Code's model-facing skill listing.

The listing is the block of skill names and descriptions the harness shows the
model at session start so it can pick a skill. Every model-invocable skill's
frontmatter sits in it whether or not that skill is ever used, so it is the one
cost of this plugin no user can opt out of, and it is shared: the harness
budgets the whole listing at a fraction of the context window and, on overflow,
drops entries starting with the least-recently-invoked skill.

`guarantees.listing_entry` is the single definition of what one file
contributes to that listing. Every assertion about listing cost measures its
result, so the per-entry cap and the aggregate ceiling can never disagree about
what they are measuring. The one budget here that is not about listing cost --
this project's own 40-word routing target, which covers agents as well as
skills -- measures `description` alone and says so where it is stated.

Runnable two ways:
    uvx pytest tests/test_description_budget.py
    python3 -m pytest tests/test_description_budget.py
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def _load_guarantees() -> ModuleType:
    """Load the sibling inventory by path.

    pytest runs with `--import-mode=importlib`, which does not put a test
    file's own directory on `sys.path`, and the repo's other contract modules
    already load their neighbours this way.
    """
    spec = importlib.util.spec_from_file_location("guarantees", HERE / "guarantees.py")
    assert spec and spec.loader, f"cannot load {HERE / 'guarantees.py'}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guarantees = _load_guarantees()


# --- what one skill contributes to the listing ------------------------------

# The two texts every fixture below is built from. Kept as constants so each
# assertion compares against the same string its frontmatter was written with,
# rather than against a second copy that could drift from it.
DESCRIPTION = "Plans a change before building it."
WHEN_TO_USE = "Use when the user asks for a plan."


def _skill_file(*fields: str) -> str:
    """A minimal SKILL.md: the given frontmatter lines, then a body.

    A body is always attached because `listing_entry` is handed whole file
    text. A fixture that stopped at the closing `---` could not tell a parser
    that stops there from one that reads on into the prose, and the prose is
    exactly what the listing must not carry.
    """
    return "---\n" + "\n".join(fields) + "\n---\n\n# Body\n\nProse the listing never shows.\n"


def test_listing_entry_reports_what_reaches_the_listing() -> None:
    """One skill's contribution to the listing -- which is nothing when excluded.

    The four rules are asserted separately because they fail for unrelated
    reasons: two are about which files are in the listing at all, and two are
    about what an included file contributes once it is there.
    """
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


# --- the shipped files against their per-file budgets ------------------------
#
# A skill's or agent's frontmatter is in context from session start whether or
# not the thing is ever used, so this text is the only part of the plugin every
# session pays for. Two limits apply and they fail for different reasons, which
# is why each has its own test. The character cap is the harness's: it applies
# to a skill's whole listing entry, and crossing it truncates the tail in
# silence. The word budget is this project's own routing target: it is measured
# over `description` alone, it covers agents too -- whose descriptions the docs
# give no character limit at all -- and nothing enforces it at runtime.
#
# Both are globbed rather than listed, so a new skill or agent is inside its
# budget the day it is added. These are size checks and not frontmatter-schema
# ones -- which fields the implementer agent must declare is
# `test_agents_contract.py`'s -- but an empty description is still reported, by
# the routing budget below, which every listed skill runs as well: a
# measurement taken on nothing is under every budget and would otherwise pass
# for the wrong reason.
LISTED_SKILLS = tuple(
    str(path.relative_to(REPO)) for path in sorted((REPO / "skills").glob("*/SKILL.md"))
)
AGENTS = tuple(str(path.relative_to(REPO)) for path in sorted((REPO / "agents").glob("*.md")))
ALWAYS_RESIDENT = LISTED_SKILLS + AGENTS

# A parametrisation over an empty sequence reports as "no tests ran" rather
# than as a failure, so a glob that stops matching has to break collection
# instead of going quiet. Asserted per glob, because one of them emptying is
# exactly the case a combined check would hide.
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


# --- the plugin's whole share of the shared listing --------------------------
#
# The per-file budgets above are blind to the total, and the total is what the
# harness actually rations: skills from every installed plugin and the user's
# own share one listing, and on overflow whole entries are dropped, starting
# with the least-recently-invoked skill -- which need not be one of ours. Four
# skills each comfortably inside the per-entry cap can still overrun this
# plugin's share between them, so the sum needs an assertion of its own.


def test_plugin_listing_total_fits_the_shared_budget() -> None:
    """Every listed skill's entry, summed, stays inside this plugin's claimed share.

    Only the total is asserted. Which individual skill is too long is
    `test_listing_entries_fit_the_harness_cap`'s question, and re-answering it
    here would report one edit as two unrelated failures.
    """
    measured = {
        relative_path: guarantees.listing_entry((REPO / relative_path).read_text(encoding="utf-8"))
        for relative_path in LISTED_SKILLS
    }
    entries = {path: entry for path, entry in measured.items() if entry is not None}
    total = sum(len(entry) for entry in entries.values())

    # A ceiling met by measuring nothing is met for the wrong reason, and it
    # reports as a pass either way, so the vacuous case has to fail first.
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


# --- keeping the queued product-* siblings apart -----------------------------
#
# Eight `product-*` skills are queued behind this file, all describing adjacent
# product-lifecycle work, and adjacency is what the shared listing degrades on:
# the model routes between those eight on their description text alone. The
# rule that keeps them apart is that each one's first sentence names the thing
# that skill owns -- `product-spec` says "spec", `product-roadmap` says
# "roadmap" -- and the token is taken from the directory name, so nothing has
# to keep a registry of tokens in step with the folders. Nothing matches the
# glob today: the rule ships dormant and fires on the first sibling to land.

PRODUCT_PREFIX = "product-"

# Deliberately not asserted non-empty, unlike LISTED_SKILLS above. Zero product
# skills is the correct state until the first of them lands, and an empty glob
# here is the rule waiting rather than the rule broken.
PRODUCT_SKILLS = tuple(
    str(path.relative_to(REPO))
    for path in sorted((REPO / "skills").glob(f"{PRODUCT_PREFIX}*/SKILL.md"))
)

# The sentence ends at the first period followed by whitespace or by the end of
# the text -- the PEP 257 rule `finalize_plan.first_sentence` already applies to
# a task's Change block, so a description and a plan read the same way. A bare
# `.` would end the sentence inside `v2.1.105` or `SKILL.md` and hide whatever
# the description says after it. That function itself is not reused here: it
# also escapes `|` for the Markdown table it feeds, which would show up inside
# the sentence this rule quotes back.
_SENTENCE_END = re.compile(r"\.(?=\s|$)")


def _trigger_rule_failure(description: str, token: str) -> str | None:
    """Why `description` fails the `product-*` trigger rule for `token`, or None.

    A failure reads as a clause about the description, so a caller that knows
    which file it came from can say the whole sentence.

    `description` is expected as `guarantees.scalar_text` leaves it -- one
    collapsed line -- because the sentence is quoted back to its author and
    the frontmatter's own line breaks are not part of what a reader sees.
    """
    end = _SENTENCE_END.search(description)
    sentence = description[: end.end()] if end else description
    if re.search(rf"\b{re.escape(token)}\b", sentence, re.IGNORECASE):
        return None
    return f"its first sentence, {sentence!r}, never names {token!r}"


def test_first_sentence_carries_the_skill_noun() -> None:
    """The rule reads the first sentence only, and reads it to the right period.

    Proved on literals rather than through the glob below, which matches
    nothing yet. A rule shipping dormant has no other evidence that it works,
    and the pull request that adds the first sibling is the wrong place to
    discover that it never did.
    """
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
    """Each `product-*` description opens by naming the noun its directory claims.

    Whether the first sentence is *read* correctly is
    `test_first_sentence_carries_the_skill_noun`'s question, asserted once
    there; this asks only whether the shipped file obeys the rule.
    """
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


# --- the cap is asserted here and nowhere else ------------------------------
#
# Two rival per-entry character caps coexisted in this repository, and the
# tighter of them -- 1,024, whose comment called it the harness's own number --
# had no source anywhere. A second cap is worse than none: whichever is tighter
# silently becomes the real rule, while the comment on the looser one goes on
# telling readers something that no longer bites. What follows is not a check
# that the cap holds, which `test_listing_entries_fit_the_harness_cap` above
# already makes, but that there is only one of it.

# `tests/*.py` deliberately takes in `guarantees.py` as well as the test
# modules: the budget constants live there, so a cap reintroduced beside them
# would hide at least as well as one reintroduced in a test.
SCANNED_MODULES = tuple(
    sorted((REPO / "skills").glob("*/tests/test_*.py")) + sorted((REPO / "tests").glob("*.py"))
)

# Same reason as the LISTED_SKILLS assertion above: a glob that stops matching
# leaves the scan vacuous, and a vacuous scan reports as a pass.
assert SCANNED_MODULES, f"no test modules found under {REPO}"

# This module is the one place allowed to assert the cap, and so the one place
# that has to name the retired figure in order to forbid it.
CAP_OWNER = Path(__file__).resolve()

# Word-boundaried, so an unrelated 10240 does not read as the retired cap.
_RETIRED_CAP = re.compile(r"\b1024\b")

# Matched against the source of the expression inside `len(...)`, which is what
# separates a cap on listing text from the many other length checks these
# modules make: cluster counts, word counts, the length of a quoted excerpt.
# It matches on names, so a cap hidden behind a variable named for none of
# these would pass. That is the intended reach: a gate against the idiom coming
# back, not a proof that it cannot.
_LISTING_TEXT_NAMES = ("description", "when_to_use", "listing_entry")


def _length_comparisons(source: str) -> list[tuple[int, str]]:
    """Every `len(<listing text>)` comparison in `source`, as (line, code).

    The comparison rather than the `len()` call is reported, because a length
    that is only interpolated into a failure message is a diagnostic and a
    length that is compared is a cap.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        measured = [_length_argument(operand) for operand in (node.left, *node.comparators)]
        if any(name in text for text in measured if text for name in _LISTING_TEXT_NAMES):
            found.append((node.lineno, ast.unparse(node)))
    return found


def _length_argument(operand: ast.expr) -> str | None:
    """The source of `x` in an operand of the form `len(x)`, else None."""
    if (
        isinstance(operand, ast.Call)
        and isinstance(operand.func, ast.Name)
        and operand.func.id == "len"
        and operand.args
    ):
        return ast.unparse(operand.args[0])
    return None


def test_no_second_description_cap_survives() -> None:
    """The per-entry character cap is asserted in this module and nowhere else."""
    rival_caps: list[str] = []
    retired_figure: list[str] = []
    for module in SCANNED_MODULES:
        if module.resolve() == CAP_OWNER:
            continue
        source = module.read_text(encoding="utf-8")
        where = module.relative_to(REPO)
        rival_caps += [f"{where}:{line}: {code}" for line, code in _length_comparisons(source)]
        retired_figure += [
            f"{where}:{lineno}: {line.strip()}"
            for lineno, line in enumerate(source.splitlines(), 1)
            if _RETIRED_CAP.search(line)
        ]

    assert not rival_caps, (
        f"{len(rival_caps)} length comparison(s) over listing text live outside "
        f"tests/test_description_budget.py, which owns the per-entry cap. Two caps "
        f"cannot both be the rule: the tighter one wins in silence and the other's "
        f"comment starts lying. Delete the assertion below, or move it here so the "
        f"cap and its justification stay together:\n  " + "\n  ".join(rival_caps)
    )

    assert not retired_figure, (
        f"the retired 1,024-character cap is still named in {len(retired_figure)} "
        f"place(s). It was never the harness's figure -- the documented cap went from "
        f"250 to 1,536 in v2.1.105 and 1,024 appears in neither state -- so a reader "
        f"who finds it will budget against a number nothing enforces:\n  "
        + "\n  ".join(retired_figure)
    )
