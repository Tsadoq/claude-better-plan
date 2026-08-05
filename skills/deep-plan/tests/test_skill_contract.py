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

The plain-python runner skips any test that takes a pytest fixture, because
nothing outside pytest can supply the argument.
"""

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

# The substrate under Phase 1's detection. The skill spells this path with
# `${CLAUDE_PLUGIN_ROOT}`, which only the harness expands, so the test reaches
# the same script through the repo root instead.
PRODUCT_ARTIFACT = ROOT / "skills" / "product-artifacts" / "scripts" / "product_artifact.py"


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


def test_phase1_offers_a_detected_product_spec() -> None:
    # The product chain writes docs/product/<slug>/spec.md for exactly this
    # consumer, so Phase 1 has to surface one when it finds one. What keeps the
    # bridge safe rather than merely present is the rule around it: the spec is
    # offered through the question Phase 1 was already asking, it reaches
    # dp-source-ingest only if the user picks it, and it goes silent rather than
    # guess. Prose that names the files without stating that rule reads as a
    # feature and behaves as a coin flip, so both are pinned. File size stays
    # with test_phase_instruction_files_fit_their_token_budgets.
    #
    # The two regions end at different headings because the files differ: in
    # SKILL.md Phase 1 is followed by Phase 2, while phase-prompts.md has no
    # Phase 2 section at all (SKILL.md carries that phase whole), so its Phase 1
    # runs to Phase 3.
    skill_region = _region(DEEP_PLAN_SKILL.read_text(), "## Phase 1", "## Phase 2", "SKILL.md")
    prompts_region = _region(
        PHASE_PROMPTS.read_text(), "## Phase 1", "## Phase 3", "phase-prompts.md"
    )
    regions = (("SKILL.md", skill_region), ("phase-prompts.md", prompts_region))

    for name, region in regions:
        # Every check below reads only the paragraphs naming spec.md, never the
        # whole region. Both regions already said `dp-source-ingest`,
        # `AskUserQuestion` and "exactly one instance of each agent type" before
        # this feature existed, so a region-wide search would come back green
        # with the spec-detection prose deleted. Narrowing is what makes these
        # assertions about the bridge rather than about its neighbours.
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


# The product members Phase 1 may not name. `spec.md` is the one member the
# bridge carries; each of these belongs to a different consumer, so a Phase 1
# offering one has widened the bridge past what was reviewed. Which members the
# product chain has, how a slug normalises and how provenance is written are all
# skills/product-artifacts/tests/'s to own -- this list is only the subset this
# phase is forbidden to mention.
FOREIGN_PRODUCT_MEMBERS = ("brief.md", "discovery.md", "requirements.md", "roadmap.md")

# Every `## Phase ` heading SKILL.md carries, by number rather than by title, so
# retitling a phase stays free while adding, dropping or reordering one has to be
# a visible edit here. guarantees.py pins that each of these headings is present
# and in order; what it cannot say is that there are no others.
#
# This is the second overlap with guarantees.py's `deep-plan-skill.section-sequence`
# (its own note names `## Preflight`/`## Step 5` as the first), and the repetition
# is deliberate rather than missed: derived from that list, this check would agree
# with whatever guarantees.py was last edited to say, and a phase added to both
# files would pass a guard whose entire job is to make that addition deliberate.
# Two hand-typed witnesses is the property being bought.
EXPECTED_PHASE_NUMBERS = ("0", "1", "2", "3", "4", "4.6", "5")

# Checkpoint 1 lives inside the Phase 1 region, so an edit aimed at Phase 1 can
# reach it. These are the strings the user actually reads and answers.
CHECKPOINT1_LITERALS = (
    '"Based on Phase 1 findings, here is what I think we are planning. Confirm scope?"',
    'Header: "Scope"',
    '"Scope is correct, proceed to decision surfacing"',
    '"Narrow to <X>"',
    '"Broaden to <Y>"',
    '"Defer <Z> to a follow-up plan"',
)


def _phase1_contract_violations(skill_text: str, prompts_text: str) -> list[str]:
    """What the Phase 1 spec bridge was forbidden to change, and did.

    Returns one human-readable line per broken contract, empty when both texts
    are clean. It takes text rather than paths so the same checks run against the
    shipped files and against a deliberately broken variant of them, which is the
    only way to show the guard can still fail.
    """
    phases = re.findall(r"^## Phase ([\d.]+)", skill_text, re.MULTILINE)
    if phases != list(EXPECTED_PHASE_NUMBERS):
        # Everything below navigates by these headings, so a structural break is
        # reported alone rather than buried under the region failures it causes.
        return [
            f"SKILL.md carries phases {phases}, expected {list(EXPECTED_PHASE_NUMBERS)} -- "
            f"the spec bridge edits Phase 1 and nothing else, so a phase added, dropped "
            f"or reordered here is either collateral damage or an unreviewed feature"
        ]

    # The two Phase 1 regions end at different headings for the reason
    # test_phase1_offers_a_detected_product_spec records: phase-prompts.md has no
    # Phase 2 section, because SKILL.md carries that phase whole.
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
    # Three invariants the spec bridge must not have moved on its way in: Phase 1
    # names one product member and no other, SKILL.md's phase list is unchanged,
    # and Checkpoint 1 still reads exactly as it did. Task 1's test owns what the
    # bridge has to say; this one owns what it was not allowed to disturb, which
    # is why it re-asserts none of those terms.
    skill_text = DEEP_PLAN_SKILL.read_text()
    prompts_text = PHASE_PROMPTS.read_text()

    violations = _phase1_contract_violations(skill_text, prompts_text)
    assert not violations, "the Phase 1 spec bridge reached past its scope:\n" + "\n".join(
        violations
    )

    # A guard nobody has watched fail is a guard nobody has tested. Perturb the
    # shipped text in memory -- one Checkpoint 1 option dropped, a second product
    # member offered inside Phase 1 -- and require the helper to name both. Nothing
    # on disk is touched, so the test is order-independent. Every string edited
    # below is one the assertion above already pins, `"Broaden to <Y>"` from
    # CHECKPOINT1_LITERALS and the Phase 2 heading from EXPECTED_PHASE_NUMBERS, so
    # wording that drifts out of the file fails there rather than quietly turning
    # a perturbation into a no-op that nothing notices.
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

    # The phase check returns before the other two, so no single perturbation can
    # exercise all three: an added phase needs its own text or that branch ships
    # having never once fired.
    restructured = skill_text + "\n## Phase 6: Unreviewed\n"

    reported = "\n".join(_phase1_contract_violations(restructured, prompts_text))
    assert "phases" in reported, (
        f"the guard stayed silent about a phase appended to SKILL.md, reporting only: "
        f"{reported!r} -- widening the phase list is the failure this check exists for"
    )


def _detection_entries(product_dir: Path, case: str) -> tuple[list[Any], str]:
    """Phase 1's one substrate call against `product_dir`, run as a subprocess.

    Returns the payload's `entries` list, plus a context line naming `case`
    with the process's exit status and everything it wrote. Every assertion in
    the caller ends with that line: substrate drift arrives here as a
    well-formed payload of the wrong shape rather than as an exception, so a
    bare comparison would report `[] != 2` and leave the reader to re-run the
    command by hand to learn what the script actually said.
    """
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
    # The two tests above pin what Phase 1 says; prose cannot notice that the
    # command it names stopped answering. That is the failure this one exists
    # for. `product_artifact.py` is maintained for the product suite, not for
    # this consumer, so a change to its payload leaves the bridge silently doing
    # nothing while every wording assertion above stays green -- the feature
    # reads as built and behaves as absent.
    #
    # Only the two properties Phase 1 actually reads are asserted. Which of
    # `fresh`/`stale`/`unresolvable` a half-written chain earns is
    # skills/product-artifacts/tests/'s state machine to own, so the
    # spec-bearing slug is checked for not being `absent` rather than for any
    # particular state.

    # The overwhelmingly common case: a repository with no docs/product/ at all.
    # Phase 1 has to read "nothing to offer" off this without the run failing.
    entries, context = _detection_entries(tmp_path / "no-docs-product", "absent product directory")
    assert entries == [], (
        f"a product directory that does not exist enumerated {entries!r} rather than nothing. "
        f"An empty enumeration is what sends Phase 1 down its silent path, so anything else "
        f"here is an offer made to a user who has never written a spec. {context}"
    )

    # Two initiatives, one of them as far as spec.md. This is the shape the
    # sole-candidate arm of the rule is decided on, which is why the spec-less
    # slug has to be enumerated too: a payload listing only spec-bearing slugs
    # would make every repository look like a single-initiative one and fire the
    # offer exactly where the rule says stay silent.
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
            if inspect.signature(_fn).parameters:
                # A pytest fixture argument; nothing out here can supply one, so
                # say so rather than reporting a TypeError as a failed contract.
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
