"""Contract test: the test-guidance content and its wiring.

Pins the structure of skills/tdd-review/references/test-principles.md
(the single source of truth for test guidance) so orchestrators that quote
its sections by heading never silently break, and pins the tdd-review
skill wrapper that owns the rubric. Stdlib only, so CI does not need
pyyaml.

Runnable two ways:
    python3 skills/tdd-review/tests/test_test_principles_contract.py
    python3 -m pytest skills/tdd-review/tests/test_test_principles_contract.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "deep-plan" / "scripts"
TEST_PRINCIPLES = ROOT / "skills" / "tdd-review" / "references" / "test-principles.md"
TDD_REVIEW_SKILL = ROOT / "skills" / "tdd-review" / "SKILL.md"
PERSPECTIVES = ROOT / "skills" / "deep-plan" / "references" / "perspectives.md"
DEEP_PLAN_SKILL = ROOT / "skills" / "deep-plan" / "SKILL.md"
PHASE_PROMPTS = ROOT / "skills" / "deep-plan" / "references" / "phase-prompts.md"
EXECUTE_SKILL = ROOT / "skills" / "deep-plan-execute" / "SKILL.md"

# The synthesis lenses, all six of which the synthesis turn sweeps in-turn.
LENSES = (
    "simplicity",
    "performance",
    "maintainability",
    "minimal-diff",
    "security",
    "deep-modules",
)

# perspectives.md is asserted on from two skills' contract tests; its own
# registry section must name both so an edit there cannot orphan a pin.
PERSPECTIVES_PINNING_TESTS = (
    "skills/tdd-review/tests/test_test_principles_contract.py",
    "skills/design-review/tests/test_design_review_contract.py",
)

PRINCIPLES_H2 = (
    "## Plan-time authoring rules",
    "## Review-time red flags",
    "## Execute-time run rules",
    "## How to update these guidelines",
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


finalize = _load("finalize_plan")


def _section(text: str, heading: str) -> str:
    """Return the body of an H2 section (from its heading to the next H2)."""
    start = text.find(heading)
    if start == -1:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _clusters(section: str) -> list[str]:
    """Split an H2 section body into its H3 cluster bodies."""
    parts = section.split("\n### ")
    return ["### " + part for part in parts[1:]]


def test_test_principles_structure() -> None:
    assert TEST_PRINCIPLES.exists(), f"missing guideline file: {TEST_PRINCIPLES}"
    text = TEST_PRINCIPLES.read_text()

    for heading in PRINCIPLES_H2:
        assert heading in text, f"test-principles.md missing section {heading!r}"

    red_flags = _section(text, "## Review-time red flags")
    clusters = _clusters(red_flags)
    assert len(clusters) == 4, (
        f"expected exactly 4 H3 red-flag clusters, found {len(clusters)}"
    )
    for cluster in clusters:
        name = cluster.splitlines()[0]
        assert any(line.rstrip().endswith("?") for line in cluster.splitlines()), (
            f"red-flag cluster {name!r} has no checkable yes/no question"
        )

    assert "Attribution" not in text, (
        "test-principles.md must not carry an attribution section (independent rephrasing)"
    )


def test_tdd_review_skill_contract() -> None:
    assert TDD_REVIEW_SKILL.exists(), f"missing skill wrapper: {TDD_REVIEW_SKILL}"
    text = TDD_REVIEW_SKILL.read_text()
    # Search from offset 3 to skip the opening "---" delimiter and find the
    # closing one, so `frontmatter` is everything between the two fences.
    end = text.index("\n---", 3)
    frontmatter, body = text[:end], text[end:]

    # Line-anchored key checks: a top-level YAML key starts at column 0, so a
    # commented-out or nested look-alike cannot satisfy them.
    lines = frontmatter.splitlines()
    assert any(line == "name: tdd-review" for line in lines), (
        "frontmatter missing top-level 'name: tdd-review' key"
    )
    assert any(line.startswith("description:") for line in lines), (
        "frontmatter missing top-level 'description' key"
    )
    assert "disable-model-invocation" not in frontmatter, (
        "tdd-review must stay model-invocable: drop the disable-model-invocation key"
    )

    desc_start = next(i for i, line in enumerate(lines) if line.startswith("description:"))
    desc_lines = [lines[desc_start]]
    for line in lines[desc_start + 1 :]:
        if not line.startswith((" ", "\t")):
            break
        desc_lines.append(line)
    description = "\n".join(desc_lines)
    # 1024 chars is Claude Code's budget for skill descriptions surfaced to
    # the model-invocation router; longer descriptions get truncated there.
    assert len(description) < 1024, (
        f"description is {len(description)} chars; model-invocable descriptions must stay under 1024"
    )

    for pointer in (
        "references/test-principles.md",
        "fleet-orchestration.md",
        "deep-plan:dp-test-critic",
    ):
        assert pointer in body, f"tdd-review SKILL.md body missing pointer {pointer!r}"


def test_lens_catalogue_is_a_synthesis_checklist() -> None:
    # The lenses are swept inside the synthesis turn, not drafted by a fan-out
    # of agents, so the catalogue must read as a checklist one reader walks.
    # Nine-field Tests coverage is NOT asserted here: test_template_contract.py
    # owns it against references/plan-file-template.md, in TESTS_FIELDS order.
    text = PERSPECTIVES.read_text()

    checklist = _section(text, "## Synthesis checklist")
    assert checklist, "perspectives.md must carry a '## Synthesis checklist' section"
    for lens in LENSES:
        assert lens in checklist, f"synthesis checklist missing the {lens!r} lens"

    registry = _section(text, "## How to update these guidelines")
    assert registry, "perspectives.md must carry a '## How to update these guidelines' section"
    for pinning in PERSPECTIVES_PINNING_TESTS:
        assert pinning in registry, f"perspectives.md registry missing pinning test {pinning!r}"

    assert "tdd-review/references/test-principles.md" in text, (
        "perspectives.md must point Tests-block authoring at the tdd-review rubric path"
    )


def test_phase46_launches_test_critic_fleet() -> None:
    skill = DEEP_PLAN_SKILL.read_text()
    start = skill.find("## Phase 4.6")
    end = skill.find("## Phase 5")
    assert start != -1 and end != -1, "deep-plan SKILL.md must keep Phase 4.6 and Phase 5 headings"
    region = skill[start:end]
    for needle in ("dp-test-critic", "tdd-review/references/test-principles.md"):
        assert needle in region, f"Phase 4.6 of deep-plan SKILL.md must reference {needle!r}"

    assert "dp-test-critic" in PHASE_PROMPTS.read_text(), (
        "phase-prompts.md must mirror the Phase 4.6 test fleet"
    )
    # Test-quality judgment stays with the dp-test-critic fleet: the plan-integrity
    # cluster that replaced the standalone critic checks Tests-block *structure* only.
    integrity = ROOT / "skills" / "deep-plan" / "references" / "plan-integrity-principles.md"
    assert "dp-test-critic" in integrity.read_text(), (
        "plan-integrity-principles.md must defer test-quality judgment to the dp-test-critic fleet"
    )


def test_execute_loop_quotes_run_rules_and_rechecks_stability() -> None:
    # The per-task loop, and with it the run rules and the stability re-run, now
    # live in the implementer agent. The agent reads the rule sections itself
    # instead of having the dispatcher quote them into a prompt.
    agent = (ROOT / "agents" / "dp-implement-task.md").read_text()
    for needle in (
        "tdd-review/references/test-principles.md",
        "dp-test-critic",
        "Execute-time run rules",
        "Execute-time craft rules",
    ):
        assert needle in agent, f"dp-implement-task.md must reference {needle!r}"

    # Ordering: red before green, and the stability re-run after green.
    red_pos = agent.index("Prove red")
    green_pos = agent.index("Prove green")
    stability_pos = agent.index("Re-run `verification`")
    assert red_pos < green_pos < stability_pos, (
        "dp-implement-task.md: the loop must run red, then green, then the "
        f"stability re-run (found {red_pos}, {green_pos}, {stability_pos})"
    )

    assert "stability finding" in agent, (
        "a second-run failure must be named a stability finding that blocks completion"
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
