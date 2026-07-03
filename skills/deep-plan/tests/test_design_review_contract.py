"""Contract test: the design-review guideline content and its wiring.

Pins the structure of skills/design-review/references/design-principles.md
(the single source of truth for design guidance) so orchestrators that quote
its sections by heading never silently break. Stdlib only, so CI does not
need pyyaml.

Runnable two ways:
    python3 skills/deep-plan/tests/test_design_review_contract.py
    python3 -m pytest skills/deep-plan/tests/test_design_review_contract.py
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
PERSPECTIVE_AGENT = ROOT / "agents" / "dp-plan-perspective.md"
PHASE_PROMPTS = ROOT / "skills" / "deep-plan" / "references" / "phase-prompts.md"
EXECUTE_SKILL = ROOT / "skills" / "deep-plan-execute" / "SKILL.md"

PRINCIPLES_H2 = (
    "## Attribution and scope",
    "## Plan-time principles",
    "## Review-time red flags",
    "## Execute-time craft rules",
    "## How to update these guidelines",
)


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

    for heading in PRINCIPLES_H2:
        assert heading in text, f"design-principles.md missing section {heading!r}"

    red_flags = _section(text, "## Review-time red flags")
    clusters = [line for line in red_flags.splitlines() if line.startswith("### ")]
    assert len(clusters) >= 3, (
        f"expected at least 3 H3 red-flag clusters, found {len(clusters)}: {clusters}"
    )

    attribution = _section(text, "## Attribution and scope")
    for needle in ("2nd edition", "2021", "not affiliated"):
        assert needle in attribution, f"attribution section missing {needle!r}"


def test_fleet_orchestration_contract() -> None:
    assert FLEET_ORCHESTRATION.exists(), f"missing fleet spec: {FLEET_ORCHESTRATION}"
    text = FLEET_ORCHESTRATION.read_text()

    assert "2.1.154" in text, "fleet spec must document the Workflow version floor 2.1.154"
    assert "## Fallback" in text, "fleet spec must carry a `## Fallback` section"
    for token in ("material", "minor"):
        assert token in text, f"fleet spec missing severity token {token!r}"
    assert any(line.startswith("Probe status:") for line in text.splitlines()), (
        "fleet spec must carry a `Probe status:` marker line"
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

    body = text[end + 4 :]
    for pointer in ("references/fleet-orchestration.md", "references/design-principles.md"):
        assert pointer in body, f"design-review SKILL.md body must point at {pointer!r}"


def test_deep_modules_perspective_wiring() -> None:
    for path in (PERSPECTIVES, PERSPECTIVE_AGENT, PHASE_PROMPTS):
        assert "deep-modules" in path.read_text(), f"{path}: missing the deep-modules perspective"
    assert "design-principles.md" in PERSPECTIVES.read_text(), (
        "perspectives.md must point the deep-modules frame at design-principles.md"
    )

    skill = DEEP_PLAN_SKILL.read_text()
    start = skill.find("### 4.3")
    end = skill.find("### 4.4")
    assert start != -1 and end != -1, "deep-plan SKILL.md must keep sections 4.3 and 4.4"
    assert "deep-modules" in skill[start:end], (
        "section 4.3 of deep-plan SKILL.md must launch the deep-modules perspective"
    )


def test_phase2_design_framing() -> None:
    skill = DEEP_PLAN_SKILL.read_text()
    start = skill.find("## Phase 2")
    end = skill.find("## Phase 3")
    assert start != -1 and end != -1, "deep-plan SKILL.md must keep Phase 2 and Phase 3 headings"
    assert "design-principles.md" in skill[start:end], (
        "Phase 2 of deep-plan SKILL.md must point option generation at design-principles.md"
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
    for needle in ("dp-design-critic", "fleet-orchestration.md"):
        assert needle in region, f"Phase 4.6 of deep-plan SKILL.md must reference {needle!r}"

    assert "dp-design-critic" in PHASE_PROMPTS.read_text(), (
        "phase-prompts.md must mirror the Phase 4.6 design fleet"
    )


def test_execute_post_task_review_wiring() -> None:
    text = EXECUTE_SKILL.read_text()
    for needle in ("dp-design-critic", "fleet-orchestration.md"):
        assert needle in text, f"deep-plan-execute SKILL.md must reference {needle!r}"


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
