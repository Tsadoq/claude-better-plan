
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
    spec = importlib.util.spec_from_file_location("guarantees", HERE / "guarantees.py")
    assert spec and spec.loader, f"cannot load {HERE / 'guarantees.py'}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guarantees = _load_guarantees()
Guarantee = guarantees.Guarantee

assert guarantees.GUARANTEES, "tests/guarantees.py declares no guarantees"


@pytest.mark.parametrize("guarantee", guarantees.GUARANTEES, ids=lambda g: g.id)
def test_every_guarantee_holds(guarantee: Guarantee) -> None:
    failure = guarantees.check(guarantee)
    assert failure is None, failure


COUNTEREXAMPLES = (
    Guarantee("false.missing-file", "skills/deep-plan/no-such-file.md", "anchor_regex", {"patterns": ("x",)}),
    Guarantee("false.unknown-kind", guarantees.DEEP_PLAN_SKILL, "no_such_kind", {}),
    Guarantee(
        "false.headings-out-of-order",
        guarantees.DEEP_PLAN_SKILL,
        "heading_present",
        {"headings": ("## Phase 5", "## Phase 0")},
    ),
    Guarantee(
        "false.pattern-absent-inside-its-region",
        guarantees.DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": guarantees.R1, "patterns": ("Checkpoint 1",)},
    ),
    Guarantee(
        "false.banned-pattern-is-present",
        guarantees.DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": ("## Phase 0",), "absent": True},
    ),
    Guarantee(
        "false.flag-the-script-does-not-declare",
        guarantees.EXECUTE_SKILL,
        "script_invoked",
        {"script": "load_tasks.py", "flag": "--index"},
    ),
    Guarantee(
        "false.frontmatter-value-is-absent",
        guarantees.DEEP_PLAN_SKILL,
        "frontmatter_field",
        {"field": "allowed-tools", "contains": "EnterPlanMode"},
    ),
    Guarantee(
        "false.citation-absent-inside-its-region",
        guarantees.DEEP_PLAN_SKILL,
        "path_exists",
        {
            "region": guarantees.PHASE_2,
            "target": guarantees.READABILITY_PRINCIPLES,
            "cited_as": "readability-principles.md",
        },
    ),
)


@pytest.mark.parametrize("guarantee", COUNTEREXAMPLES, ids=lambda g: g.id)
def test_check_reports_a_guarantee_that_does_not_hold(guarantee: Guarantee) -> None:
    failure = guarantees.check(guarantee)
    assert failure is not None, (
        f"check() accepted the false guarantee {guarantee.id!r}, so this kind of "
        f"evidence is no longer being verified: {guarantee}"
    )
    assert guarantee.id in failure, (
        f"the failure message for {guarantee.id!r} does not name the guarantee, so a "
        f"red case cannot be traced back to the inventory: {failure!r}"
    )



CRITIC_AGENT = Path(guarantees.CRITIC_AGENT).name
CRITIC_MODEL = "haiku"
CRITIC_DENIED = frozenset({"Write", "Edit", "NotebookEdit", "Bash", "Agent", "ExitPlanMode"})


def test_exactly_one_critic_agent_with_the_shared_profile() -> None:
    critics = sorted(p.name for p in (REPO / "agents").glob("*critic*.md"))
    assert critics == [CRITIC_AGENT], (
        f"the plugin must ship exactly one critic agent, agents/{CRITIC_AGENT}, because "
        f"a critic's whole rubric is caller-supplied. Found: {critics}"
    )

    text = (REPO / "agents" / CRITIC_AGENT).read_text(encoding="utf-8")
    model = (guarantees.frontmatter_value(text, "model") or "").strip()
    assert model == CRITIC_MODEL, (
        f"agents/{CRITIC_AGENT} must declare `model: {CRITIC_MODEL}` -- a fleet is one "
        f"leaf per cluster, so the model cost multiplies. Found model: {model!r}"
    )

    raw = guarantees.frontmatter_value(text, "disallowedTools") or ""
    denied = {tool.strip() for tool in raw.split(",") if tool.strip()}
    assert denied == CRITIC_DENIED, (
        f"agents/{CRITIC_AGENT} must deny exactly {sorted(CRITIC_DENIED)}, the profile all "
        f"three predecessors shared: it is a read-only leaf that spawns nothing. Found "
        f"{sorted(denied)} -- extra {sorted(denied - CRITIC_DENIED)}, missing "
        f"{sorted(CRITIC_DENIED - denied)}"
    )



FINDING_LINE = "[material|minor]"

REFUTE_INSTRUCTION = re.compile(r"\brefute\b", re.IGNORECASE)


def _matching_lines(pattern: re.Pattern[str], text: str) -> list[str]:
    return [
        f"{lineno}: {line.strip()}"
        for lineno, line in enumerate(text.splitlines(), 1)
        if pattern.search(line)
    ]


def test_fleet_recipe_keeps_the_wire_contract_and_sheds_leaf_prose() -> None:
    recipe = (REPO / guarantees.FLEET_RECIPE).read_text(encoding="utf-8")
    critic = (REPO / guarantees.CRITIC_AGENT).read_text(encoding="utf-8")

    assert FINDING_LINE in recipe, (
        f"{guarantees.FLEET_RECIPE} no longer states the finding line "
        f"{FINDING_LINE!r}, which is the wire between the two halves, not leaf-side "
        f"detail: the caller parses those fields to dedup and route findings when it "
        f"runs the `## Fallback` path, so the grammar has to stay where both parties "
        f"can see it"
    )

    budget = guarantees.BUDGETS["fleet_recipe_lines"]
    length = len(recipe.splitlines())
    assert length <= budget, (
        f"{guarantees.FLEET_RECIPE} is {length} lines, over its {budget}-line budget. "
        f"Four callers quote this file, so it pays for itself in every orchestrator's "
        f"context: move leaf-side prose into agents/{CRITIC_AGENT}, or raise "
        f"BUDGETS['fleet_recipe_lines'] and record beside it why the caller's half "
        f"needs the room"
    )

    in_recipe = _matching_lines(REFUTE_INSTRUCTION, recipe)
    assert not in_recipe, (
        f"{guarantees.FLEET_RECIPE} instructs the critic how hard to lean on a "
        f"finding in verify mode. That stance is the leaf's own, and agents/"
        f"{CRITIC_AGENT} already carries it; the recipe should name the verdict it "
        f"routes (`refuted`) and not the act it delegates. Offending line(s):\n  "
        + "\n  ".join(in_recipe)
    )

    assert REFUTE_INSTRUCTION.search(critic), (
        f"agents/{CRITIC_AGENT} no longer tells a verify-mode instance to refute the "
        f"finding it was handed. Nothing else does either -- the recipe deliberately "
        f"stopped -- so a verifier would default to confirming whatever it is shown, "
        f"and the fleet's adversarial stage would rubber-stamp every finding"
    )


CONTRACT_TESTS = sorted((REPO / "skills").glob("*/tests/test_*contract*.py"))

assert CONTRACT_TESTS, f"no contract-test modules found under {REPO / 'skills'}"

MAX_MARKER_WORDS = 3


def _substring_assertion_literals(module: Path) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(module.read_text())):
        if not isinstance(node, ast.Assert) or not isinstance(node.test, ast.Compare):
            continue
        compare = node.test
        if not isinstance(compare.ops[0], ast.In):
            continue
        left = compare.left
        if isinstance(left, ast.Constant) and isinstance(left.value, str):
            found.append((node.lineno, left.value))
    return found


@pytest.mark.parametrize("module", CONTRACT_TESTS, ids=lambda p: p.name)
def test_no_contract_test_asserts_prose(module: Path) -> None:
    offenders = [
        f"{module.relative_to(REPO)}:{lineno}: {literal!r}"
        for lineno, literal in _substring_assertion_literals(module)
        if len(literal.split()) > MAX_MARKER_WORDS
    ]
    assert not offenders, (
        f"{module.name} pins wording rather than structure. Each assertion below "
        f"compares a literal of more than {MAX_MARKER_WORDS} words, so the sentence "
        f"it quotes cannot be reworded without a CI failure; move the pin to "
        f"tests/guarantees.py as a named Guarantee, or restate it structurally:\n  "
        + "\n  ".join(offenders)
    )



_COMMAND_LINE = re.compile(r"^\s*(?:[-*]\s*)?(?:python3|uvx?|git|test\s|grep|mv|ls|cd|pytest)\b")

SHARED_RUN_WORDS = 12

MIN_COMPARABLE_WORDS = 900


def _prose_words(path: Path) -> list[tuple[str, int]]:
    words: list[tuple[str, int]] = []
    in_data_fence = False
    continuing = False
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_data_fence = bool(stripped[3:].strip()) and not in_data_fence
            continue
        if in_data_fence:
            continue
        skipped = continuing or bool(_COMMAND_LINE.match(line))
        continuing = skipped and stripped.endswith("\\")
        if skipped:
            continue
        words.extend((word, lineno) for word in stripped.split())
    return words


def _shared_passages(
    left: list[tuple[str, int]], right: list[tuple[str, int]], size: int
) -> list[str]:
    left_grams: dict[str, int] = {}
    for i in range(len(left) - size + 1):
        left_grams.setdefault(" ".join(w for w, _ in left[i : i + size]), left[i][1])

    passages: list[str] = []
    start: int | None = None
    end = 0
    left_line = 0

    def flush() -> None:
        assert start is not None
        text = " ".join(w for w, _ in right[start : end + size])
        quoted = text if len(text) <= 140 else f"{text[:140]}..."
        passages.append(
            f"SKILL.md:{left_line} <-> phase-prompts.md:{right[start][1]}: {quoted!r}"
        )

    for i in range(len(right) - size + 1):
        gram = " ".join(w for w, _ in right[i : i + size])
        if gram in left_grams:
            if start is None:
                start, left_line = i, left_grams[gram]
            end = i
        elif start is not None:
            flush()
            start = None
    if start is not None:
        flush()
    return passages


def test_phase_instruction_files_share_no_verbatim_prose() -> None:
    skill = REPO / guarantees.DEEP_PLAN_SKILL
    prompts = REPO / guarantees.PHASE_PROMPTS

    skill_words = _prose_words(skill)
    prompt_words = _prose_words(prompts)
    for path, words in ((skill, skill_words), (prompts, prompt_words)):
        assert len(words) >= MIN_COMPARABLE_WORDS, (
            f"{path.relative_to(REPO)} contributed only {len(words)} comparable words, "
            f"below the {MIN_COMPARABLE_WORDS}-word floor. The overlap check below is "
            f"then vacuous: fix the exclusion rules in _prose_words rather than trusting "
            f"a green run"
        )

    passages = _shared_passages(skill_words, prompt_words, SHARED_RUN_WORDS)
    assert not passages, (
        f"{len(passages)} passage(s) of {SHARED_RUN_WORDS}+ words appear verbatim in both "
        f"phase-instruction files, so an edit to one leaves the other stating something "
        f"different. Keep each passage in exactly one file and have phase-prompts.md cite "
        f"the SKILL.md section instead of restating it:\n  " + "\n  ".join(passages)
    )
