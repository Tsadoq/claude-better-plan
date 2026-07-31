"""Contract test: the design-review guideline's shape and its fleet wiring.

Pins what a substring cannot express about
skills/design-review/references/design-principles.md and its callers: the
red-flag cluster count a critic is split along, the consumer registry that
keeps this test findable, and which critic type each Phase 4.6 site launches.
The guideline's H2 spine and every path citation are pinned instead by
tests/guarantees.py. Stdlib only, so CI does not need pyyaml.

Runnable two ways:
    python3 skills/design-review/tests/test_design_review_contract.py
    python3 -m pytest skills/design-review/tests/test_design_review_contract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESIGN_PRINCIPLES = ROOT / "skills" / "design-review" / "references" / "design-principles.md"
FLEET_ORCHESTRATION = ROOT / "skills" / "design-review" / "references" / "fleet-orchestration.md"
DESIGN_REVIEW_SKILL = ROOT / "skills" / "design-review" / "SKILL.md"
DEEP_PLAN_SKILL = ROOT / "skills" / "deep-plan" / "SKILL.md"
PERSPECTIVES = ROOT / "skills" / "deep-plan" / "references" / "perspectives.md"
PHASE_PROMPTS = ROOT / "skills" / "deep-plan" / "references" / "phase-prompts.md"


def _section(text: str, heading: str) -> str:
    """Return the body of an H2 section (from its heading to the next H2)."""
    start = text.find(heading)
    if start == -1:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def test_design_principles_structure() -> None:
    assert DESIGN_PRINCIPLES.exists(), f"missing guideline file: {DESIGN_PRINCIPLES}"
    text = DESIGN_PRINCIPLES.read_text()

    red_flags = _section(text, "## Review-time red flags")
    clusters = [line for line in red_flags.splitlines() if line.startswith("### ")]
    assert len(clusters) >= 3, (
        f"expected at least 3 H3 red-flag clusters, found {len(clusters)}: {clusters}"
    )

    attribution = _section(text, "## Attribution and scope")
    for needle in ("2nd edition", "2021", "not affiliated"):
        assert needle in attribution, f"attribution section missing {needle!r}"


def test_registry_names_colocated_pinning_test() -> None:
    registry = _section(DESIGN_PRINCIPLES.read_text(), "## How to update these guidelines")
    assert registry, (
        "design-principles.md lost its '## How to update these guidelines' section"
    )
    assert "skills/design-review/tests/test_design_review_contract.py" in registry, (
        "the consumer registry must name the co-located pinning test path"
    )
    assert "skills/deep-plan/tests/test_design_review_contract.py" not in registry, (
        "stale pinning-test path skills/deep-plan/tests/test_design_review_contract.py "
        "must not survive in the registry"
    )


def test_fleet_recipe_is_cluster_source_parametric() -> None:
    # There is one critic type now, so the recipe's parametricity has moved from
    # the agent to the cluster source: `args.source` is what makes an identical
    # leaf hunt design flaws on one run and test flaws on the next. guarantees.py
    # pins that all four principles files are paired here; what this adds is that
    # the source actually reaches the finder, rather than being documented above
    # a script that drops it.
    assert FLEET_ORCHESTRATION.exists(), f"missing fleet spec: {FLEET_ORCHESTRATION}"
    recipe = FLEET_ORCHESTRATION.read_text()
    assert "args.source" in recipe, (
        "fleet-orchestration.md must thread the caller's cluster source into the "
        "finder prompts as args.source; a leaf launched without it has no rubric"
    )


def test_no_caller_restates_the_session_cap() -> None:
    # Fleet mechanics live in one file. Callers state a target and quote the
    # recipe; they never restate a cap, a gate, or a nesting rule themselves.
    for path in (DEEP_PLAN_SKILL, PHASE_PROMPTS):
        assert "CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION" not in path.read_text(), (
            f"{path.name} restates the session cap; it belongs only in fleet-orchestration.md"
        )


def test_design_review_skill_contract() -> None:
    assert DESIGN_REVIEW_SKILL.exists(), f"missing skill file: {DESIGN_REVIEW_SKILL}"
    text = DESIGN_REVIEW_SKILL.read_text()

    assert text.startswith("---"), "SKILL.md must open with a frontmatter block"
    end = text.find("\n---", 3)
    fm = text[3:end] if end != -1 else ""
    for key in ("name", "description"):
        assert any(line.strip().startswith(f"{key}:") for line in fm.splitlines()), (
            f"design-review SKILL.md frontmatter missing {key!r}"
        )


def test_deep_modules_perspective_wiring() -> None:
    for path in (PERSPECTIVES, PHASE_PROMPTS):
        assert "deep-modules" in path.read_text(), f"{path}: missing the deep-modules perspective"
    assert "design-principles.md" in PERSPECTIVES.read_text(), (
        "perspectives.md must point the deep-modules frame at design-principles.md"
    )


def test_synthesis_lenses_run_in_the_orchestrator_turn() -> None:
    # 4.3 sweeps the lenses inside the synthesis turn. No agent launch, so no
    # barrier and no per-lens draft to merge.
    skill = DEEP_PLAN_SKILL.read_text()
    start = skill.find("### 4.3")
    end = skill.find("### 4.4")
    assert start != -1 and end != -1, "deep-plan SKILL.md must keep sections 4.3 and 4.4"
    region = skill[start:end]

    for needle in ("perspectives.md", "## Synthesis checklist"):
        assert needle in region, f"section 4.3 must point at {needle!r}"

    offending = [ln for ln in region.splitlines() if "in parallel" in ln]
    assert not offending, (
        f"section 4.3 still delegates the lens sweep: {offending[0].strip()!r}"
    )


def test_phase46_design_fleet_wiring() -> None:
    skill = DEEP_PLAN_SKILL.read_text()

    end_fm = skill.find("\n---", 3)
    fm = skill[3:end_fm] if skill.startswith("---") and end_fm != -1 else ""
    assert "Workflow" in fm, "deep-plan SKILL.md allowed-tools must include Workflow"

    start = skill.find("## Phase 4.6")
    end = skill.find("## Phase 5")
    assert start != -1 and end != -1, "deep-plan SKILL.md must keep Phase 4.6 and Phase 5 headings"
    region = skill[start:end]
    assert "dp-critic" in region, (
        "Phase 4.6 of deep-plan SKILL.md must launch the dp-critic fleet"
    )
    assert "design-principles.md" in region, (
        "Phase 4.6 of deep-plan SKILL.md must name the design cluster source; the "
        "critic leaf has no rubric without it"
    )

    assert "design-principles.md" in PHASE_PROMPTS.read_text(), (
        "phase-prompts.md must mirror the Phase 4.6 design fleet"
    )


def test_execute_post_task_review_wiring() -> None:
    # The post-task fleet moved into the implementer agent, so the diff and the
    # critic prompts stay in the context that gets discarded. guarantees.py pins
    # that the dispatcher names no critic at all.
    agent = (ROOT / "agents" / "dp-implement-task.md").read_text()
    for needle in ("deep-plan:dp-critic", "design-principles.md", "test-principles.md"):
        assert needle in agent, f"dp-implement-task.md must reference {needle!r}"


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
