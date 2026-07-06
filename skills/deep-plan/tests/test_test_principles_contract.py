"""Contract test: the test-guidance content and its wiring.

Pins the structure of skills/deep-plan/references/test-principles.md
(the single source of truth for test guidance) so orchestrators that quote
its sections by heading never silently break. Stdlib only, so CI does not
need pyyaml.

Runnable two ways:
    python3 skills/deep-plan/tests/test_test_principles_contract.py
    python3 -m pytest skills/deep-plan/tests/test_test_principles_contract.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "deep-plan" / "scripts"
TEST_PRINCIPLES = ROOT / "skills" / "deep-plan" / "references" / "test-principles.md"
PERSPECTIVE_AGENT = ROOT / "agents" / "dp-plan-perspective.md"
PERSPECTIVES = ROOT / "skills" / "deep-plan" / "references" / "perspectives.md"
DEEP_PLAN_SKILL = ROOT / "skills" / "deep-plan" / "SKILL.md"
PHASE_PROMPTS = ROOT / "skills" / "deep-plan" / "references" / "phase-prompts.md"
PLAN_CRITIC = ROOT / "agents" / "dp-plan-critic.md"
EXECUTE_SKILL = ROOT / "skills" / "deep-plan-execute" / "SKILL.md"

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


def test_perspective_agent_drafts_full_tests_schema() -> None:
    agent_text = PERSPECTIVE_AGENT.read_text()
    # Labels come from finalize_plan.TESTS_FIELDS (never re-typed here) so the
    # perspective drafts cannot omit fields the template requires.
    for label in finalize.TESTS_FIELDS:
        assert f"- {label}:" in agent_text, (
            f"dp-plan-perspective.md output format missing a '- {label}:' bullet"
        )
    for path in (PERSPECTIVE_AGENT, PERSPECTIVES):
        assert "test-principles.md" in path.read_text(), (
            f"{path.name} must point Tests-block authoring at test-principles.md"
        )


def test_phase46_launches_test_critic_fleet() -> None:
    skill = DEEP_PLAN_SKILL.read_text()
    start = skill.find("## Phase 4.6")
    end = skill.find("## Phase 5")
    assert start != -1 and end != -1, "deep-plan SKILL.md must keep Phase 4.6 and Phase 5 headings"
    region = skill[start:end]
    for needle in ("dp-test-critic", "test-principles.md"):
        assert needle in region, f"Phase 4.6 of deep-plan SKILL.md must reference {needle!r}"

    assert "dp-test-critic" in PHASE_PROMPTS.read_text(), (
        "phase-prompts.md must mirror the Phase 4.6 test fleet"
    )
    assert "dp-test-critic" in PLAN_CRITIC.read_text(), (
        "dp-plan-critic.md must delegate test-quality judgment to the dp-test-critic fleet"
    )


def test_execute_loop_quotes_run_rules_and_rechecks_stability() -> None:
    text = EXECUTE_SKILL.read_text()
    for needle in (
        "test-principles.md",
        "dp-test-critic",
        "Execute-time run rules",
        "Execute-time craft rules",
    ):
        assert needle in text, f"deep-plan-execute SKILL.md must reference {needle!r}"

    # Ordering anchors: each occurs exactly once in Step 5 (unlike the
    # run-the-verification wording, which appears in both the red and green
    # steps), so the stability re-run is pinned between the post-task fleet
    # review and completion.
    fleet_anchor = "Design-review the task's diff."
    stability_anchor = "re-run the task's `verification` command once more"
    completed_anchor = "mark the task `completed` via `TaskUpdate`"
    for anchor in (fleet_anchor, completed_anchor):
        assert text.count(anchor) == 1, f"ordering anchor {anchor!r} must occur exactly once"
    assert stability_anchor in text, "the post-green stability re-run sentence is missing"
    assert text.index(fleet_anchor) < text.index(stability_anchor) < text.index(completed_anchor), (
        "stability re-run must sit after the post-task fleet review and before completion"
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
