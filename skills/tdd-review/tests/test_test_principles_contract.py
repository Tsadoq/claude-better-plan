
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

LENSES = (
    "simplicity",
    "performance",
    "maintainability",
    "minimal-diff",
    "security",
    "deep-modules",
)

PERSPECTIVES_PINNING_TESTS = (
    "skills/tdd-review/tests/test_test_principles_contract.py",
    "skills/design-review/tests/test_design_review_contract.py",
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


finalize = _load("finalize_plan")


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _clusters(section: str) -> list[str]:
    parts = section.split("\n### ")
    return ["### " + part for part in parts[1:]]


def test_test_principles_structure() -> None:
    assert TEST_PRINCIPLES.exists(), f"missing guideline file: {TEST_PRINCIPLES}"
    text = TEST_PRINCIPLES.read_text()

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


def test_tdd_review_skill_contract() -> None:
    assert TDD_REVIEW_SKILL.exists(), f"missing skill wrapper: {TDD_REVIEW_SKILL}"
    text = TDD_REVIEW_SKILL.read_text()
    frontmatter = text[: text.index("\n---", 3)]

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


def test_lens_catalogue_is_a_synthesis_checklist() -> None:
    text = PERSPECTIVES.read_text()

    checklist = _section(text, "## Synthesis checklist")
    assert checklist, "perspectives.md must carry a '## Synthesis checklist' section"
    for lens in LENSES:
        assert lens in checklist, f"synthesis checklist missing the {lens!r} lens"

    registry = _section(text, "## How to update these guidelines")
    assert registry, "perspectives.md must carry a '## How to update these guidelines' section"
    for pinning in PERSPECTIVES_PINNING_TESTS:
        assert pinning in registry, f"perspectives.md registry missing pinning test {pinning!r}"


def test_phase46_launches_test_critic_fleet() -> None:
    skill = DEEP_PLAN_SKILL.read_text()
    start = skill.find("## Phase 4.6")
    end = skill.find("## Phase 5")
    assert start != -1 and end != -1, "deep-plan SKILL.md must keep Phase 4.6 and Phase 5 headings"
    region = skill[start:end]
    assert "test-principles.md" in region, (
        "Phase 4.6 of deep-plan SKILL.md must name test-principles.md as a cluster source; "
        "one critic type serves all four fleets, so the source is the whole wiring"
    )

    assert "test-principles.md" in PHASE_PROMPTS.read_text(), (
        "phase-prompts.md must mirror the Phase 4.6 test fleet"
    )
    integrity = ROOT / "skills" / "deep-plan" / "references" / "plan-integrity-principles.md"
    assert "test-principles.md" in integrity.read_text(), (
        "plan-integrity-principles.md must defer test-quality judgment to the fleet "
        "running against test-principles.md"
    )


def test_execute_loop_quotes_run_rules_and_rechecks_stability() -> None:
    agent = (ROOT / "agents" / "dp-implement-task.md").read_text()
    for needle in ("dp-critic", "Execute-time run rules", "Execute-time craft rules"):
        assert needle in agent, f"dp-implement-task.md must reference {needle!r}"

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
