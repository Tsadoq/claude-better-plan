"""Contract test: SKILL.md frontmatter schema and the orchestration wiring.

Guards the two skills' frontmatter, the ordering constraints inside their
bodies (an instruction that arrives after the step it governs is an
instruction nobody followed), the token budget the harness truncates against,
and the handful of body anchors that tests/guarantees.py does not already
carry -- each one commented with what it earns. Every other content pin on
these files lives in that inventory, so the wording of a shipped skill can be
rewritten without editing CI. Stdlib only, so CI does not need pyyaml.

Runnable two ways:
    python3 skills/deep-plan/tests/test_skill_contract.py
    python3 -m pytest skills/deep-plan/tests/test_skill_contract.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
DEEP_PLAN_SKILL = ROOT / "skills" / "deep-plan" / "SKILL.md"
EXECUTE_SKILL = ROOT / "skills" / "deep-plan-execute" / "SKILL.md"
DESIGN_REVIEW_SKILL = ROOT / "skills" / "design-review" / "SKILL.md"
PHASE_PROMPTS = ROOT / "skills" / "deep-plan" / "references" / "phase-prompts.md"


def _guarantees() -> ModuleType:
    """Load tests/guarantees.py by path, for the BUDGETS numbers it owns.

    Loaded on demand rather than at import: this module runs standalone as a
    script too, and a missing repo-level tests/ dir should fail only the one
    test that needs it.
    """
    source = ROOT / "tests" / "guarantees.py"
    spec = importlib.util.spec_from_file_location("guarantees", source)
    assert spec and spec.loader, f"cannot load {source}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def _has_key(fm: str, key: str) -> bool:
    return any(line.strip().startswith(f"{key}:") for line in fm.splitlines())


def _offset(text: str, anchor: str, source: str) -> int:
    """Where `anchor` starts, so an ordering check can compare two positions."""
    index = text.find(anchor)
    assert index != -1, f"{source}: {anchor!r} not found"
    return index


def _region(text: str, start_marker: str, end_marker: str, source: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker, start + 1)
    assert start != -1 and end != -1, (
        f"{source}: region markers {start_marker!r}/{end_marker!r} missing"
    )
    return text[start:end]


def test_both_skills_have_valid_frontmatter() -> None:
    for skill in (DEEP_PLAN_SKILL, EXECUTE_SKILL, DESIGN_REVIEW_SKILL):
        assert skill.exists(), f"missing skill file: {skill}"
        fm = _frontmatter(skill.read_text())
        assert fm, f"{skill}: no frontmatter block"
        assert _has_key(fm, "name"), f"{skill}: frontmatter missing name"
        assert _has_key(fm, "description"), f"{skill}: frontmatter missing description"


def test_skill_declares_an_argument_hint() -> None:
    # The only frontmatter key guarantees.py has no field entry for: it carries
    # no fixed value, so all that can be checked is that the key is declared.
    fm = _frontmatter(DEEP_PLAN_SKILL.read_text())
    assert _has_key(fm, "argument-hint"), "deep-plan SKILL.md needs an argument-hint"


def test_phase46_states_its_loop_bound() -> None:
    # The retired depth knob's replacement: one absolute bound, stated in the
    # phase itself. Pinned as two words so the sentence around them stays
    # editable; guarantees.py pins that no depth token came back.
    region = _region(DEEP_PLAN_SKILL.read_text(), "## Phase 4.6", "## Phase 5", "SKILL.md")
    assert "loop once" in region, (
        "Phase 4.6 must state its single absolute loop bound now that the depth table is gone"
    )


def _prompts_phase46() -> str:
    """The Phase 4.6 section of phase-prompts.md."""
    prompts = PHASE_PROMPTS.read_text()
    return _region(prompts, "## Phase 4.6", "## Phase 5", "phase-prompts.md")


def test_phase46_gates_the_fleet_on_triage() -> None:
    # A small plan must be able to arm nothing and pay for no critics at all.
    # Both files gate on the recipe, but for different halves of the phase:
    # SKILL.md owns what arms a fleet and where an unarmed plan goes, and the
    # fragment owns the launch, so each is checked for what it is responsible for.
    skill_region = _region(
        DEEP_PLAN_SKILL.read_text(), "## Phase 4.6", "## Phase 5", "SKILL.md"
    )
    for name, region in (("SKILL.md", skill_region), ("phase-prompts.md", _prompts_phase46())):
        assert "Triage gate" in region, (
            f"{name}: Phase 4.6 must cite the recipe's `## Triage gate` rather than "
            f"launching every cluster unconditionally"
        )

    assert "Checkpoint 2" in skill_region, (
        "SKILL.md: Phase 4.6 must name Checkpoint 2 as where a plan that arms "
        "nothing proceeds to"
    )


def test_retired_plan_critic_agent_file_is_gone() -> None:
    # The plan-integrity checks are now a caller-supplied cluster carried by the
    # haiku readability leaf, not a standalone inherit-model agent. guarantees.py
    # pins that neither orchestration file still names it; only the filesystem
    # can answer whether the agent definition itself was deleted.
    retired = ROOT / "agents" / "dp-plan-critic.md"
    assert not retired.exists(), f"the retired agent file must be deleted: {retired}"


def test_prompts_fragment_cites_the_fleet_recipe() -> None:
    # guarantees.py pins the four principles files this fragment cites; the
    # recipe citation is the fifth, and without it the fragment would have to
    # restate the launch mechanics it is meant to defer.
    assert "fleet-orchestration.md" in _prompts_phase46(), (
        "phase-prompts.md: the Phase 4.6 fragment must quote the fleet recipe "
        "rather than restating how to launch a fleet"
    )


def test_execute_audits_task_scope_before_completion() -> None:
    # The dispatcher attributes changed paths to the task itself: a plain diff
    # omits newly created files, and a bare untracked listing would wrongly
    # blame the task for scratch files already in the user's tree. Both halves
    # are needed, and the untracked snapshot must be taken BEFORE dispatch.
    text = EXECUTE_SKILL.read_text()

    untracked = "git ls-files --others --exclude-standard"
    diff_names = "git diff --name-only"
    dispatch = "deep-plan:dp-implement-task"
    completion = "## Step 6"

    assert text.count(untracked) >= 2, (
        f"expected both a pre-dispatch snapshot and a post-run listing of {untracked!r}, "
        f"found {text.count(untracked)} occurrence(s)"
    )

    source = "deep-plan-execute SKILL.md"
    for earlier, later in (
        (untracked, dispatch),
        (dispatch, diff_names),
        (diff_names, completion),
    ):
        assert _offset(text, earlier, source) < _offset(text, later, source), (
            f"{earlier!r} must appear before {later!r} in the dispatch loop"
        )

    # The audit is only a gate if something depends on its verdict: the task is
    # flipped to `completed` after it, never before.
    assert "`completed`" in text, (
        "the dispatcher must still own the step that flips the harness task to `completed`"
    )


def test_permission_inheritance_mitigation_documented() -> None:
    # A writable subagent inherits the parent's permission mode, so in default
    # mode every Write/Edit/Bash inside every implementer prompts. The user must
    # hear that once, BEFORE the first dispatch, not after task 1 stalls.
    text = EXECUTE_SKILL.read_text()

    # The heading order (Preflight before Step 5) is pinned by guarantees.py's
    # execute-skill.step-sequence; what it cannot say is what the section warns
    # about, which is the whole point of the section.
    section = _region(text, "## Preflight", "\n## Step 5", "deep-plan-execute SKILL.md")
    for needle in ("inherit", "permission", "permissions.deny"):
        assert needle in section, f"the Preflight section must mention {needle!r}"


def test_skill_forbids_plan_mode_tools() -> None:
    # The prohibition sentence in the body is pinned by guarantees.py; the
    # frontmatter is a separate surface, and an allowed-tools entry would grant
    # the tool no matter what the body says.
    fm = _frontmatter(DEEP_PLAN_SKILL.read_text())
    assert "EnterPlanMode" not in fm, "allowed-tools must not include EnterPlanMode"
    assert "ExitPlanMode" not in fm, "allowed-tools must not include ExitPlanMode"


def test_folder_rename_guards_both_naming_forms() -> None:
    # Fail-closed rename: both existence guards must sit on the mv line itself,
    # so a guard that passes for the folder form cannot let the legacy flat form
    # be clobbered. Counting the guards on one line is what makes this checkable;
    # the path literals themselves are pinned by guarantees.py.
    fragments = PHASE_PROMPTS.read_text()
    rename_lines = [
        ln for ln in fragments.splitlines() if "mv " in ln and ln.count("test ! -e") == 2
    ]
    assert rename_lines, (
        "rename must guard folder AND legacy flat form on the mv line (Phase 4 fragment)"
    )


def test_phase46_runs_both_document_clusters_on_one_leaf() -> None:
    # guarantees.py pins that Phase 4.6 cites each of the four principles files
    # and launches `deep-plan:dp-critic`. What it cannot express is the shape
    # that made the merge possible: readability and plan integrity are two
    # launches of that same leaf, so a phase naming a *second* agent type has
    # quietly reintroduced the per-rubric agent this plan removed.
    skill = DEEP_PLAN_SKILL.read_text()
    prompts = PHASE_PROMPTS.read_text()

    region46 = _region(skill, "## Phase 4.6", "## Phase 5", "SKILL.md")
    for source in ("readability-principles.md", "plan-integrity-principles.md"):
        assert source in region46, f"SKILL.md: Phase 4.6 must name the cluster source {source!r}"
        assert source in prompts, f"phase-prompts.md: must mirror the {source!r} wiring"

    for text, name in ((region46, "SKILL.md"), (prompts, "phase-prompts.md")):
        extra = sorted(set(re.findall(r"\bdp-[a-z0-9-]*critic\b", text)) - {"dp-critic"})
        assert not extra, (
            f"{name}: Phase 4.6 names critic agent types other than dp-critic ({extra}); "
            "every cluster source is a launch of the one parametrised leaf"
        )


def test_synthesis_and_probe_phases_defer_to_their_templates() -> None:
    # SKILL.md is the only home for the Phase 4 synthesis rubric; the fragment
    # used to restate it and the two drifted into rival rubrics, which is why it
    # now carries only the commands and examples. So the templates are checked
    # here, and the check that the fragment stopped restating them is the
    # verbatim-overlap test in tests/test_guarantees.py.
    skill = DEEP_PLAN_SKILL.read_text()

    # Phase 4.4 names the architecture template (write-or-skip rubric lives
    # there) and the research coverage preamble.
    region = _region(skill, "### 4.4 Synthesis", "### 4.5", "SKILL.md")
    assert "architecture-md-template.md" in region, (
        "SKILL.md: Phase 4.4 must cite architecture-md-template.md's significance test"
    )
    assert "Coverage" in region, (
        "SKILL.md: Phase 4.4 must compose the research coverage preamble"
    )

    # Phase 4.5 points at the plan template's probe entry shape instead of
    # restating the [probe N] format locally.
    region = _region(skill, "### 4.5 Verification probes", "## Phase 4.6", "SKILL.md")
    assert "plan-file-template.md" in region, (
        "SKILL.md: Phase 4.5 must point at the plan template's probe entry shape"
    )
    assert "[probe" not in region, (
        "SKILL.md: Phase 4.5 must not restate the probe entry format locally"
    )


def test_phase_instruction_files_fit_their_token_budgets() -> None:
    # Both limits live in tests/guarantees.py BUDGETS, which is the single home
    # for every size number this repo enforces; each entry's comment says what
    # constrains it (a truncation window for SKILL.md, a ratchet against
    # re-duplication for the fragment). o200k_base is the closest public
    # tokenizer to the harness's accounting, which is why the SKILL.md entry is
    # set below the window rather than at it.
    import pytest

    tiktoken = pytest.importorskip("tiktoken")
    encoding = tiktoken.get_encoding("o200k_base")
    budgets = _guarantees().BUDGETS

    for path, key in (
        (DEEP_PLAN_SKILL, "deep_plan_skill_tokens"),
        (PHASE_PROMPTS, "phase_prompts_tokens"),
    ):
        limit = budgets[key]
        tokens = len(encoding.encode(path.read_text()))
        assert tokens <= limit, (
            f"{path.name} measures {tokens} o200k_base tokens against the "
            f"BUDGETS[{key!r}] limit of {limit}. Move the {tokens - limit} tokens over "
            f"budget into a reference file, or raise the entry in tests/guarantees.py "
            f"and record beside it what earned the space"
        )


def test_approval_memo_wiring() -> None:
    # The memo is written by one skill and read by the other, so the pin has to
    # sit in the phase that writes it -- a `last_plan_path` mention anywhere
    # else in SKILL.md would not make the handoff work.
    phase5 = _region(
        DEEP_PLAN_SKILL.read_text(), "## Phase 5", "## Output budget", "SKILL.md"
    )
    assert "last_plan_path" in phase5, (
        "Phase 5 of deep-plan SKILL.md must record the last_plan_path memo on approval"
    )

    # Both lookups are pinned by guarantees.py; only their order decides whether
    # the mtime guess can pre-empt the memo the user's own approval recorded.
    text = EXECUTE_SKILL.read_text()
    source = "deep-plan-execute SKILL.md"
    assert _offset(text, "--lookup", source) < _offset(text, "ls -td", source), (
        "the memo lookup must precede the mtime fallback in execute Step 1"
    )


def test_implementer_appends_its_notes_after_the_green_run() -> None:
    # The design-notes gate: notes written before verification would record an
    # increment that never passed. Ordering is the whole assertion -- that both
    # steps exist at all is pinned by guarantees.py.
    agent = (ROOT / "agents" / "dp-implement-task.md").read_text()
    source = "dp-implement-task.md"
    assert _offset(agent, "Prove green", source) < _offset(
        agent, "## Implementation notes", source
    ), "dp-implement-task.md: the design.md notes append must follow the green run"


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
