"""Contract test: SKILL.md frontmatter and the v0.3 wiring.

Guards Task 1 (depth arg + ${CLAUDE_SESSION_ID} hardening) and Task 3 (the
Phase 4.6 critique step + dp-plan-critic agent) against regression. Stdlib only,
so CI does not need pyyaml.

Runnable two ways:
    python3 skills/deep-plan/tests/test_skill_contract.py
    python3 -m pytest skills/deep-plan/tests/test_skill_contract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEEP_PLAN_SKILL = ROOT / "skills" / "deep-plan" / "SKILL.md"
EXECUTE_SKILL = ROOT / "skills" / "deep-plan-execute" / "SKILL.md"
DESIGN_REVIEW_SKILL = ROOT / "skills" / "design-review" / "SKILL.md"
CRITIC_AGENT = ROOT / "agents" / "dp-plan-critic.md"


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def _has_key(fm: str, key: str) -> bool:
    return any(line.strip().startswith(f"{key}:") for line in fm.splitlines())


def test_both_skills_have_valid_frontmatter() -> None:
    for skill in (DEEP_PLAN_SKILL, EXECUTE_SKILL, DESIGN_REVIEW_SKILL):
        assert skill.exists(), f"missing skill file: {skill}"
        fm = _frontmatter(skill.read_text())
        assert fm, f"{skill}: no frontmatter block"
        assert _has_key(fm, "name"), f"{skill}: frontmatter missing name"
        assert _has_key(fm, "description"), f"{skill}: frontmatter missing description"


def test_skill_frontmatter_and_wiring() -> None:
    text = DEEP_PLAN_SKILL.read_text()
    fm = _frontmatter(text)

    # Task 1: argument-hint + depth table + ${CLAUDE_SESSION_ID}.
    assert _has_key(fm, "argument-hint"), "deep-plan SKILL.md needs an argument-hint"
    assert "Depth scaling" in text, "deep-plan SKILL.md must document the depth-scaling table"
    for level in ("shallow", "standard", "exhaustive"):
        assert level in text, f"depth table missing level {level!r}"
    assert "${CLAUDE_SESSION_ID}" in text, "must use the ${CLAUDE_SESSION_ID} substitution"

    # Task 1: no literal placeholder survives.
    assert "<SESSION_ID>" not in text, "literal <SESSION_ID> placeholder must be replaced"

    # Task 3: the critique step is wired and its agent exists.
    assert "Phase 4.6" in text, "SKILL.md must reference Phase 4.6 (adversarial critique)"
    assert CRITIC_AGENT.exists(), f"missing critic agent: {CRITIC_AGENT}"


def test_skill_forbids_plan_mode_tools() -> None:
    text = DEEP_PLAN_SKILL.read_text()
    fm = _frontmatter(text)
    body = text[text.find("\n---", 3) + 4 :]

    # Frontmatter: the plan-mode tools must not be allowed.
    assert "EnterPlanMode" not in fm, "allowed-tools must not include EnterPlanMode"
    assert "ExitPlanMode" not in fm, "allowed-tools must not include ExitPlanMode"

    # Body: no harness plan-file or archive-path wiring survives.
    for banned in ("harness_plan_path", "--harness-plan-path", "archive_plan_path"):
        assert banned not in body, f"banned string {banned!r} found in SKILL.md body"

    # Body: the prohibition is explicit and the load-bearing anchors remain.
    assert "never call EnterPlanMode or ExitPlanMode" in body, (
        "SKILL.md must carry the explicit plan-mode-tool prohibition sentence"
    )
    assert "Phase 4.6" in body, "SKILL.md must still reference Phase 4.6"
    assert "${CLAUDE_SESSION_ID}" in body, "SKILL.md must keep the session-id placeholder"


def test_skill_pins_folder_lifecycle() -> None:
    text = DEEP_PLAN_SKILL.read_text()

    # Folder lifecycle: draft born as a folder, stale detection globs folders.
    assert "*-draft/" in text, "stale-draft detection must glob *-draft/ folders"
    assert "<topic>-draft/plan.md" in text, "draft must be born as <topic>-draft/plan.md"
    assert "<topic>-draft.md" not in text, "flat draft naming must be gone"
    assert "<slug>/plan.md" in text, "canonical plan path must be <slug>/plan.md"

    # Fail-closed rename: both existence guards on the mv line itself.
    rename_lines = [
        ln for ln in text.splitlines() if "mv " in ln and ln.count("test ! -e") == 2
    ]
    assert rename_lines, "rename must guard folder AND legacy flat form on the mv line"

    # The documented permission snippet covers the guard segments.
    assert "Bash(test ! -e docs/plans/*)" in text, (
        "permission snippet must allowlist the test guard segments"
    )

    # design.md seeding references the shared template.
    assert "design-md-template.md" in text, "Phase 4.4 must seed design.md from the template"

    # Archive outputs are folder members, never dotted siblings.
    assert ".probes.md" not in text, "dotted probes sibling must not be an archive output"
    assert ".research.md" not in text, "dotted research sibling must not be an archive output"


def test_execute_skill_targets_the_parser_and_task_api() -> None:
    text = EXECUTE_SKILL.read_text()
    assert "load_tasks.py" in text, "execute skill must invoke the load_tasks.py parser"
    assert "addBlockedBy" in text, "execute skill must wire dependencies via addBlockedBy"


def test_execute_skill_dual_reads_and_gates_on_design_notes() -> None:
    text = EXECUTE_SKILL.read_text()

    # Dual-read discovery: folder plans preferred; the generated README,
    # dotted siblings, and unfinished drafts never match.
    assert '*/plan.md' in text, "discovery must prefer the */plan.md folder glob"
    assert "README" in text, "discovery must exclude the generated README"
    assert "-draft/plan" in text, "discovery must exclude *-draft/ folders"
    assert "load_tasks.py" in text, "execute skill must still invoke load_tasks.py"

    # Design-notes gate: the Implementation notes append is ordered after the
    # verification-pass step and before the TaskUpdate completion wording.
    verify_pos = text.index("Run the `verification` command.")
    notes_pos = text.index("## Implementation notes")
    complete_pos = text.index("mark the task `completed` via `TaskUpdate`")
    assert verify_pos < notes_pos < complete_pos, (
        "design.md notes append must sit between verification and completion"
    )

    # After all tasks: status flip + index refresh, scoped to folder plans.
    assert "**Status**: executed" in text, "completion must flip the plan status"
    assert "--index" in text, "completion must refresh the plans index"
    assert "folder plans" in text, "completion steps must be scoped to folder plans"


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
