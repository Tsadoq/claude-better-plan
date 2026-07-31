# Per-phase detail

`SKILL.md` is the orchestration: it states every phase, its bound, and what it must decide. This file is only what `SKILL.md` defers to -- exact commands, option-set literals, worked examples -- one section per phase that has any, read when that phase names it.

Nothing here restates `SKILL.md`. Where both need a passage, this file names the `SKILL.md` section rather than copying it, because two copies of one instruction drift and the reader cannot tell which copy is current. So Phase 0 and Phase 2 have no section below: `SKILL.md` carries them whole, and Phase 0's sentinel-triggered paths live in `edge-flows.md`.

## Contents

- [Phase 1: the sources question](#phase-1-the-sources-question)
- [Phase 3: agent inputs](#phase-3-agent-inputs)
- [Phase 4: commands and examples](#phase-4-commands-and-examples)
- [Phase 4.6: review targets and finding handling](#phase-46-review-targets-and-finding-handling)
- [Phase 5: what the repair pass does](#phase-5-what-the-repair-pass-does)

## Phase 1: the sources question

`SKILL.md`'s `## Phase 1: Parallel triangulation` launches `dp-source-ingest` only when the user has material to ingest, and asks once when the original prompt carries no signal of it. That question is:

- Question: "Do you have existing material I should ingest? Local files, URLs, Jira IDs, or pasted text. Skip if not."
- Header: "Sources"
- Options:
  1. "No, proceed without sources" (Recommended when the prompt showed no signal)
  2. "Yes, I will paste paths/URLs/IDs in my next message"
  3. "Yes, here is a Jira ticket / URL / file path: ..."

Ask it once. A second ask reads as nagging, and option 1 is the common case.

## Phase 3: agent inputs

Each `dp-research-deep` instance takes five fields:

- `decision` -- the short name from Phase 2.
- `chosen_option` -- the user's pick.
- `rejected_options` -- the others, so the dossier can say why they lose.
- `links_to_validate` -- any URLs Phase 1's `dp-research-shallow` surfaced.
- `success_criteria` -- one or two specific things the dossier must confirm or deny. Without these the agent returns a survey instead of an answer.

The dossier format itself is normative in `agents/dp-research-deep.md`; do not restate it in the launch prompt.

## Phase 4: commands and examples

### 4.1 Slug format

A slug is lowercase `[a-z0-9-]{1,60}`, hyphen-separated, with no leading, trailing, or doubled hyphen. `resolve_slug.py` normalises a near-miss and reports a collision rather than guessing:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/resolve_slug.py \
  --slug <s> --plans-dir <d>
```

### 4.2 The guarded rename

Both guards sit on the `mv` line itself, so a guard that passes for the folder form cannot let the legacy flat form be clobbered:

```
test ! -e <plans_dir>/<slug> && test ! -e <plans_dir>/<slug>.md && mv <plans_dir>/<topic>-draft <plans_dir>/<slug>
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
  --update plan_path=<plans_dir>/<slug>/plan.md --session-id ${CLAUDE_SESSION_ID}
```

Issue the guarded command with project-relative paths (`docs/plans/...`) from the project root when `plans_dir` is inside the project: permission rules prefix-match the literal command string, so an absolute path misses the allowlist and prompts once. Fall back to absolute paths when `plans_dir` is outside the project.

### 4.3 How hard to sweep each lens

`SKILL.md`'s `### 4.3 Synthesis lenses` names the checklist and fixes `deep-modules` as the last lens. How much scrutiny each of the others gets is yours to judge: give one to three of them real attention, chosen by the priorities the user has shown, and skim the rest. Sweeping all of them equally costs a lot of turn and finds little.

### 4.5 Probe examples

A verification probe is a one-line question to the environment, not a test suite:

```
python3 -c "import redis; print(redis.__version__)"
grep -rl 'TokenBucket' src/
uv run pytest --collect-only tests/middleware/
```

Each answers one question in one line. A probe that needs a whole fixture tree is a test, and belongs in the plan as a task rather than here.

## Phase 4.6: review targets and finding handling

`SKILL.md`'s `## Phase 4.6: Adversarial critique` owns which fleets exist, which cluster source each reads, what arms it, and the loop bound. What it defers here is the review target each fleet is handed, and what to do with what comes back. Launch every fleet per `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`, including its `## Triage gate`, which drops clusters with nothing to find before any finder runs.

**Review targets**, one per cluster source:

- `design-principles.md`: the synthesized plan body and its `## Architecture` section, read as a design artifact rather than as prose.
- `test-principles.md`: every task's `**Tests (TDD)**` block.
- `readability-principles.md`: `plan.md`, `design.md`, and `architecture.md` when present, read as documents.
- `plan-integrity-principles.md`: the plan body, the `## Decisions made` table, the Phase 1 evidence, and the Phase 3 dossiers. That cluster is structural -- work never scheduled, a wrong or cyclic `Depends on`, a code task with no `**Tests (TDD)**` block, a task contradicting `## Decisions made` or a dossier, a load-bearing claim with neither probe nor citation -- so the finder needs the evidence, not only the plan. The dossiers are question-first per `agents/dp-research-deep.md` (**The question**, **The answer**, **What we found**, **Sources**, plus any `## Contradiction`); tell it to cite a dossier by section, not by page.

All four are `dp-critic` launched four times, not four agent types: that leaf's whole rubric is caller-supplied, so a cluster source needs only another launch that names it.

**Finding handling.** All four fleets tag findings `material` or `minor`, merge into one list, and share one loop bound; there are no per-fleet knobs.

- A `material` finding that reverses a user decision -> back to Phase 2 for that one decision, quoting the critic's contradiction in the new `AskUserQuestion`. Never reverse a decision the user made without asking them again.
- Any other `material` finding -> fix it in the plan body directly (add the missing task, correct `**Depends on**`, add the missing `**Tests (TDD)**` block, add a probe), then relaunch that finder once if the single re-run is unspent.
- A `minor` finding -> append to `## Open questions`, and only if it is genuinely deferrable: a non-empty `## Open questions` blocks `/deep-plan:deep-plan-execute` later, so parking a real blocker there stalls the next session instead of this one.

Then finalize and present Checkpoint 2 exactly as `SKILL.md`'s `### Checkpoint 2` states.

## Phase 5: what the repair pass does

`finalize_plan.py --repair` runs before the Checkpoint 2 question, never after, so it cannot be skipped by an approval. It rewrites em-dashes, fixes task headers, inserts missing sections and task subsections as `n/a`, strips attribution, and regenerates the `## Task overview` table between its markers, then prints `{ok, fixes, warnings}`.

It does not reject a normal plan; it repairs one. A `warnings` entry names something worth telling the user about (a code task whose `**Tests (TDD)**` block is missing, say) but never something worth re-looping for. `SKILL.md`'s `### Checkpoint 2` states how much of that to relay and the one exit that does warrant looping back to Phase 4; its `## Phase 5` section carries the archive commands and the literal handoff message.
