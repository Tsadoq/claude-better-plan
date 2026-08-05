
from __future__ import annotations

import importlib.util
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEEP_PLAN_SKILL = ROOT / "skills" / "deep-plan" / "SKILL.md"
EXECUTE_SKILL = ROOT / "skills" / "deep-plan-execute" / "SKILL.md"
DESIGN_REVIEW_SKILL = ROOT / "skills" / "design-review" / "SKILL.md"
PHASE_PROMPTS = ROOT / "skills" / "deep-plan" / "references" / "phase-prompts.md"

PRODUCT_ARTIFACT = ROOT / "skills" / "product-artifacts" / "scripts" / "product_artifact.py"


def _guarantees() -> ModuleType:
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
    fm = _frontmatter(DEEP_PLAN_SKILL.read_text())
    assert _has_key(fm, "argument-hint"), "deep-plan SKILL.md needs an argument-hint"


def test_phase1_offers_a_detected_product_spec() -> None:
    skill_region = _region(DEEP_PLAN_SKILL.read_text(), "## Phase 1", "## Phase 2", "SKILL.md")
    prompts_region = _region(
        PHASE_PROMPTS.read_text(), "## Phase 1", "## Phase 3", "phase-prompts.md"
    )
    regions = (("SKILL.md", skill_region), ("phase-prompts.md", prompts_region))

    for name, region in regions:
        detection = "\n\n".join(p for p in region.split("\n\n") if "spec.md" in p)
        for term in ("docs/product/", "dp-source-ingest", "AskUserQuestion"):
            assert term in detection, (
                f"{name}: Phase 1 mentions no {term!r} alongside the detected spec -- "
                f"the spec must be offered through the existing AskUserQuestion and "
                f"reach dp-source-ingest only once the user picks it, and prose that "
                f"leaves those two ties unstated does not say so"
            )

        lowered = detection.lower()
        for arm in ("exact", "sole"):
            assert arm in lowered, (
                f"{name}: Phase 1 names the detection but not its {arm!r} arm -- "
                f"selection is an exact topic-to-slug match, else the sole "
                f"spec-bearing slug, and prose that omits when it fires is not a rule"
            )
        assert "silent" in lowered or "silence" in lowered, (
            f"{name}: Phase 1 must state the stopping condition as silence -- no "
            f"match, or an exact match whose slug has no spec.md, offers nothing "
            f"rather than falling through to another initiative's spec"
        )
        assert "fall" in lowered, (
            f"{name}: Phase 1 states silence but not that an exact match lacking "
            f"spec.md refuses to fall back to the sole-slug arm -- without that "
            f"clause the two silence cases read as one and seeding a plan from a "
            f"different initiative's spec looks permitted"
        )
        assert "stale" in lowered, (
            f"{name}: Phase 1 must name `stale` inside the offer -- the freshness "
            f"state is reported so the user weighs it, and an offer that withholds "
            f"it has quietly made that call for them"
        )

    for term in ("--check-freshness", "${CLAUDE_PLUGIN_ROOT}"):
        assert term in skill_region, (
            f"SKILL.md: Phase 1 must name {term!r} -- it owns the one substrate call "
            f"detection runs, which is why the fragment can defer the command to it"
        )


FOREIGN_PRODUCT_MEMBERS = ("brief.md", "discovery.md", "requirements.md", "roadmap.md")

EXPECTED_PHASE_NUMBERS = ("0", "1", "2", "3", "4", "4.6", "5")

CHECKPOINT1_LITERALS = (
    '"Based on Phase 1 findings, here is what I think we are planning. Confirm scope?"',
    'Header: "Scope"',
    '"Scope is correct, proceed to decision surfacing"',
    '"Narrow to <X>"',
    '"Broaden to <Y>"',
    '"Defer <Z> to a follow-up plan"',
)


def _phase1_contract_violations(skill_text: str, prompts_text: str) -> list[str]:
    phases = re.findall(r"^## Phase ([\d.]+)", skill_text, re.MULTILINE)
    if phases != list(EXPECTED_PHASE_NUMBERS):
        return [
            f"SKILL.md carries phases {phases}, expected {list(EXPECTED_PHASE_NUMBERS)} -- "
            f"the spec bridge edits Phase 1 and nothing else, so a phase added, dropped "
            f"or reordered here is either collateral damage or an unreviewed feature"
        ]

    regions = (
        ("SKILL.md", _region(skill_text, "## Phase 1", "## Phase 2", "SKILL.md")),
        (
            "phase-prompts.md",
            _region(prompts_text, "## Phase 1", "## Phase 3", "phase-prompts.md"),
        ),
    )

    violations = [
        f"{name}: Phase 1 names {member} -- the bridge offers exactly one product "
        f"member, spec.md, and every other member is a different consumer's contract "
        f"that nothing here has reviewed"
        for name, region in regions
        for member in FOREIGN_PRODUCT_MEMBERS
        if member in region
    ]

    checkpoint1 = _region(skill_text, "### Checkpoint 1", "## Phase 2", "SKILL.md")
    violations += [
        f"SKILL.md: Checkpoint 1 no longer carries {literal} verbatim -- it sits inside "
        f"the Phase 1 region the bridge edits, and the scope question the user answers "
        f"is not the bridge's to reword"
        for literal in CHECKPOINT1_LITERALS
        if literal not in checkpoint1
    ]

    return violations


def test_phase1_bridge_leaves_members_phases_and_checkpoint1_intact() -> None:
    skill_text = DEEP_PLAN_SKILL.read_text()
    prompts_text = PHASE_PROMPTS.read_text()

    violations = _phase1_contract_violations(skill_text, prompts_text)
    assert not violations, "the Phase 1 spec bridge reached past its scope:\n" + "\n".join(
        violations
    )

    widened = skill_text.replace('"Broaden to <Y>"', "", 1).replace(
        "## Phase 2", "Offer `docs/product/<slug>/roadmap.md` too.\n\n## Phase 2", 1
    )

    reported = "\n".join(_phase1_contract_violations(widened, prompts_text))
    for expected in ("roadmap.md", "Checkpoint 1"):
        assert expected in reported, (
            f"the guard stayed silent about {expected!r} against text that breaks it, "
            f"reporting only: {reported!r} -- a contract check that cannot fail is not "
            f"protecting the contract"
        )

    restructured = skill_text + "\n## Phase 6: Unreviewed\n"

    reported = "\n".join(_phase1_contract_violations(restructured, prompts_text))
    assert "phases" in reported, (
        f"the guard stayed silent about a phase appended to SKILL.md, reporting only: "
        f"{reported!r} -- widening the phase list is the failure this check exists for"
    )


def _detection_entries(product_dir: Path, case: str) -> tuple[list[Any], str]:
    proc = subprocess.run(
        [
            sys.executable,
            str(PRODUCT_ARTIFACT),
            "--check-freshness",
            "--product-dir",
            str(product_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    context = (
        f"[{case}] `product_artifact.py --check-freshness --product-dir {product_dir}` "
        f"exited {proc.returncode} and wrote:\n{proc.stdout}{proc.stderr}"
    )

    assert proc.returncode == 0, (
        f"Phase 1 makes this call before its sources question on every /deep-plan run, so a "
        f"non-zero exit is an error shown to a user who asked for none of it. {context}"
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"the detection call stopped printing JSON ({exc}), leaving Phase 1 nothing to "
            f"read a slug list out of. {context}"
        ) from exc

    entries = payload.get("entries")
    assert isinstance(entries, list), (
        f"the payload carries no `entries` list, and that key is the entire detection input -- "
        f"the selection rule has nothing to run against without it. {context}"
    )
    return entries, context


def test_phase1_detection_call_behaves_as_phase1_documents(tmp_path: Path) -> None:

    entries, context = _detection_entries(tmp_path / "no-docs-product", "absent product directory")
    assert entries == [], (
        f"a product directory that does not exist enumerated {entries!r} rather than nothing. "
        f"An empty enumeration is what sends Phase 1 down its silent path, so anything else "
        f"here is an offer made to a user who has never written a spec. {context}"
    )

    product_dir = tmp_path / "docs" / "product"
    (product_dir / "alpha").mkdir(parents=True)
    (product_dir / "alpha" / "spec.md").write_text("# Alpha spec\n")
    (product_dir / "beta").mkdir()
    (product_dir / "beta" / "brief.md").write_text("# Beta brief\n")

    entries, context = _detection_entries(product_dir, "two slugs, one spec-bearing")

    assert len(entries) == 2, (
        f"two slug folders enumerated {len(entries)} entries. Phase 1 counts spec-bearing slugs "
        f"against the whole list, so a list that drops slugs settles the sole-candidate rule on "
        f"the wrong denominator. {context}"
    )
    for entry in entries:
        assert "slug" in entry, (
            f"an entry arrived with no `slug` key: {entry!r}. The slug is what the normalised "
            f"topic is matched against and what the offered path is built from. {context}"
        )
        assert isinstance(entry.get("members"), dict), (
            f"entry {entry.get('slug')!r} carries no `members` mapping: {entry!r}. Whether a "
            f"slug has a spec is read out of that mapping and nowhere else. {context}"
        )

    spec_states = {entry["slug"]: entry["members"].get("spec.md") for entry in entries}
    assert spec_states.get("alpha") not in (None, "absent"), (
        f"the slug holding a spec.md reported it as {spec_states.get('alpha')!r}; the states "
        f"were {spec_states!r}. Phase 1 offers on any state but `absent`, so this one reading "
        f"is the detection itself. {context}"
    )
    assert spec_states.get("beta") == "absent", (
        f"the slug with no spec.md reported it as {spec_states.get('beta')!r}; the states were "
        f"{spec_states!r}. `absent` is how Phase 1 rules a slug out, and a slug it cannot rule "
        f"out makes the sole-candidate arm offer whichever spec it happens to find. {context}"
    )


def test_phase46_states_its_loop_bound() -> None:
    region = _region(DEEP_PLAN_SKILL.read_text(), "## Phase 4.6", "## Phase 5", "SKILL.md")
    assert "loop once" in region, (
        "Phase 4.6 must state its single absolute loop bound now that the depth table is gone"
    )


def _prompts_phase46() -> str:
    prompts = PHASE_PROMPTS.read_text()
    return _region(prompts, "## Phase 4.6", "## Phase 5", "phase-prompts.md")


def test_phase46_gates_the_fleet_on_triage() -> None:
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
    retired = ROOT / "agents" / "dp-plan-critic.md"
    assert not retired.exists(), f"the retired agent file must be deleted: {retired}"


def test_prompts_fragment_cites_the_fleet_recipe() -> None:
    assert "fleet-orchestration.md" in _prompts_phase46(), (
        "phase-prompts.md: the Phase 4.6 fragment must quote the fleet recipe "
        "rather than restating how to launch a fleet"
    )


def test_execute_audits_task_scope_before_completion() -> None:
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

    assert "`completed`" in text, (
        "the dispatcher must still own the step that flips the harness task to `completed`"
    )


def test_permission_inheritance_mitigation_documented() -> None:
    text = EXECUTE_SKILL.read_text()

    section = _region(text, "## Preflight", "\n## Step 5", "deep-plan-execute SKILL.md")
    for needle in ("inherit", "permission", "permissions.deny"):
        assert needle in section, f"the Preflight section must mention {needle!r}"


def test_skill_forbids_plan_mode_tools() -> None:
    fm = _frontmatter(DEEP_PLAN_SKILL.read_text())
    assert "EnterPlanMode" not in fm, "allowed-tools must not include EnterPlanMode"
    assert "ExitPlanMode" not in fm, "allowed-tools must not include ExitPlanMode"


def test_folder_rename_guards_both_naming_forms() -> None:
    fragments = PHASE_PROMPTS.read_text()
    rename_lines = [
        ln for ln in fragments.splitlines() if "mv " in ln and ln.count("test ! -e") == 2
    ]
    assert rename_lines, (
        "rename must guard folder AND legacy flat form on the mv line (Phase 4 fragment)"
    )


def test_phase46_runs_both_document_clusters_on_one_leaf() -> None:
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
    skill = DEEP_PLAN_SKILL.read_text()

    region = _region(skill, "### 4.4 Synthesis", "### 4.5", "SKILL.md")
    assert "architecture-md-template.md" in region, (
        "SKILL.md: Phase 4.4 must cite architecture-md-template.md's significance test"
    )
    assert "Coverage" in region, (
        "SKILL.md: Phase 4.4 must compose the research coverage preamble"
    )

    region = _region(skill, "### 4.5 Verification probes", "## Phase 4.6", "SKILL.md")
    assert "plan-file-template.md" in region, (
        "SKILL.md: Phase 4.5 must point at the plan template's probe entry shape"
    )
    assert "[probe" not in region, (
        "SKILL.md: Phase 4.5 must not restate the probe entry format locally"
    )


def test_phase_instruction_files_fit_their_token_budgets() -> None:
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
    phase5 = _region(
        DEEP_PLAN_SKILL.read_text(), "## Phase 5", "## Output budget", "SKILL.md"
    )
    assert "last_plan_path" in phase5, (
        "Phase 5 of deep-plan SKILL.md must record the last_plan_path memo on approval"
    )

    text = EXECUTE_SKILL.read_text()
    source = "deep-plan-execute SKILL.md"
    assert _offset(text, "--lookup", source) < _offset(text, "ls -td", source), (
        "the memo lookup must precede the mtime fallback in execute Step 1"
    )


def test_implementer_appends_its_notes_after_the_green_run() -> None:
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
            if inspect.signature(_fn).parameters:
                print(f"SKIP {_name} (needs a pytest fixture)")
                continue
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception:  # noqa: BLE001
                failed += 1
                print(f"FAIL {_name}")
                traceback.print_exc()
    sys.exit(1 if failed else 0)
