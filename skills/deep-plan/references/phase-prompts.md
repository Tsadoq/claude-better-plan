# Phase-prompt fragments

Long-form per-phase prompts the orchestrator quotes into context as needed. The skill body in `SKILL.md` is the short orchestration; this file is the detail.

## Contents

- [Phase 0: Bootstrap](#phase-0-bootstrap)
- [Phase 1: Parallel triangulation](#phase-1-parallel-triangulation)
- [Phase 2: Decision surfacing](#phase-2-decision-surfacing)
- [Phase 3: Targeted deep research](#phase-3-targeted-deep-research)
- [Phase 4: Synthesis and verification](#phase-4-synthesis-and-verification)
- [Phase 4.6: Adversarial critique](#phase-46-adversarial-critique)
- [Phase 5: Archive and handoff](#phase-5-archive-and-handoff)

## Phase 0: Bootstrap

```
You are at the start of /deep-plan. Before doing anything else:

0. Parse $ARGUMENTS for the optional `slug:<value>` and `depth:<shallow|standard|exhaustive>`
   tokens (there is no native key:value parser). Default depth=standard. The rest of
   $ARGUMENTS is the topic. Every per-phase cap below is read from the "Depth scaling" table
   in SKILL.md; where a fragment gives a number, treat it as the standard-depth value.

1. Check the most recent system reminder. If it contains "Plan mode is active.", print one
   sentence asking the user to toggle plan mode off (Shift+Tab) and stop the turn. This
   skill never runs inside plan mode (SKILL.md R2); there is no second code path for it.

2. Run setup_session.py to bootstrap session state:
       python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
         --session-id ${CLAUDE_SESSION_ID}

   The script returns a JSON blob describing the resolved project root, plans_dir, and
   sandbox path, plus optional sentinels:
   - prompt_for_plans_dir: true             -> ask the user via AskUserQuestion (options below).
   - no_git: true                           -> ask the user whether to use cwd as project root.
   - plans_dir_under_protected_path: <path> -> the remembered plans_dir lives under .claude/,
     where every write prompts and cannot be allowlisted. Offer the move via AskUserQuestion
     (<repo>/docs/plans/ recommended; keeping the current dir stays allowed). Never migrate
     silently.

3. Plans-dir options when prompting (Phase 0):
   1. <repo>/docs/plans/                   (Recommended)
   2. <repo>/plans/
   3. <repo-parent>/<repo-name>-plans/
   4. <repo>/.claude/plans/                (warn: protected path, every write prompts)

   The default MUST NOT be ~/.claude/plans/. Persist the user's choice via:
       python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
         --update plans_dir=<ABS_PATH> --session-id ${CLAUDE_SESSION_ID}

4. Stale-draft detection (R3, BEFORE Phase 2 may create a new draft): glob plans_dir/*-draft/
   alongside the legacy flat form plans_dir/*-draft.md. If a draft exists (left by an
   abandoned run), read its ## Context and ## Decisions made (for a draft folder, from
   its plan.md member), then ask via AskUserQuestion [resume from draft, overwrite, start
   fresh under another topic name]. Default: resume (seed Phase 2 with the draft's
   already-resolved decisions). Overwrite deletes the stale draft. No orphan draft may
   reach Phase 4.

5. Slug collision (R3, reached from Phase 4.1 when resolve_slug.py reports the slug
   already exists as the folder plans_dir/<slug>/ or the legacy flat file
   plans_dir/<slug>.md): read the existing plan's ## Context and ## Decisions made,
   then ask via AskUserQuestion [refine existing, overwrite, new with -v2 suffix,
   custom suffix]. Default when similar to current intent: refine (seed the current
   plan from the existing file, then edit in place). Default when unrelated: -v2
   suffix (auto-incremented to -v3, -v4 if taken). Never assume an existing plan
   file is still valid.

6. After state is bootstrapped, print a single short status sentence to the user and
   proceed to Phase 1. Do not narrate Phase 0's mechanics.
```

## Phase 1: Parallel triangulation

```
Goal: build a shared evidence base from three independent angles before any decision
is taken. Launch up to three subagents in a single message (fan-out scales by depth per
the SKILL.md Depth scaling table; shallow runs explore + shallow only):

- dp-explore-codebase  (haiku, always)
- dp-research-shallow  (haiku, always)
- dp-source-ingest     (sonnet, ONLY if the user has provided source material)

Decide whether to launch dp-source-ingest by:
- Parsing the original /deep-plan prompt for: file paths (start with /, ~, or ./),
  URLs, Jira-style IDs matching [A-Z]+-\d+, or pasted-text indicators.
- If none, ask the user once via AskUserQuestion:
    "Do you have existing material I should ingest? Local files, URLs, Jira IDs,
     or pasted text. Skip if not."
    Header: "Sources"
    Options:
      1. "No, proceed without sources" (Recommended if no signal)
      2. "Yes, I will paste paths/URLs/IDs in my next message"
      3. "Yes, here is a Jira ticket / URL / file path: ..."

After all launched agents return, synthesise their outputs into:
- patterns_found:        from dp-explore-codebase
- candidate_libraries:   from dp-research-shallow
- user_source_summary:   from dp-source-ingest (or "none")
- open_unknowns:         union of unresolved questions

Checkpoint 1 (always blocks): paraphrase scope back via AskUserQuestion:
    Q: "Based on Phase 1 findings, here is what I think we are planning.
        Confirm scope?"
    Header: "Scope"
    Options:
      1. "Scope is correct, proceed to decision surfacing" (Recommended)
      2. "Narrow to <specific_subscope>"
      3. "Broaden to <larger_scope>"
      4. "Defer <specific_aspect> to a follow-up plan"

If the answer is anything other than option 1, re-loop into Phase 1 with the adjusted
scope. Do not proceed to Phase 2 without explicit scope confirmation.
```

## Phase 2: Decision surfacing

```
Goal: enumerate two to five sub-decisions worth surfacing, generate option sets inline,
and resolve them sequentially with the user in dependency order.

Generate options inline (orchestrator-only). DO NOT spawn an agent for option generation.
Phase 1 evidence is already in your context.

Heuristics for "what counts as a sub-decision" (surface IFF at least one holds AND you
cannot trivially infer the answer from Phase 1 evidence):
- Architectural axis: storage backend, transport, sync vs async, in-process vs out.
- Algorithm or data-structure family with measurable trade-offs.
- Library choice when 2+ credible options exist in the Phase 1 shortlist.
- Boundary placement: middleware vs decorator vs base class vs separate service.
- Test strategy when the codebase has heterogeneous testing patterns.

Skip surfacing when:
- The codebase already has one dominant pattern (3+ examples of pattern X, 0 of others).
  Log under "Decisions made" with rationale "follows existing convention".
- The user's prompt explicitly fixes the choice ("use Redis").

Cap: at most 5 surfaced decisions per plan. Excess goes to "Open questions".

Build a dependency DAG of decisions. Present sequentially in topological order, each via
its own AskUserQuestion call. Each option set has 3 to 5 options, with the recommended
option marked "(Recommended)" and listed first.

Immediately before asking the FIRST decision, create the draft plan file
plans_dir/<topic>-draft/plan.md (Write; the Write creates the folder) seeded with the
skeleton's title, ## Context paragraph, and an empty ## Decisions made table, then
record it:
    python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
      --update plan_path=<plans_dir>/<topic>-draft/plan.md --session-id ${CLAUDE_SESSION_ID}

After each AskUserQuestion resolves, immediately Edit the draft to append a row to
the `## Decisions made` table. This is the persistence point: do NOT batch. The draft is
crash-safe: every resolved decision survives an abandoned run.

If choosing option X for decision N invalidates an option for decision M (downstream),
recompute M's options before asking. Example: choosing "Redis" as rate-limit store
forecloses "use SQLite atomic counters" later.
```

## Phase 3: Targeted deep research

```
Goal: for every chosen option needing corroboration, do deep web/library research with
citations.

Launch one dp-research-deep agent per decision branch IN PARALLEL in a single message.
Cap at 4 parallel instances. If more than 4 decisions need research, batch in waves of 4.
Depth scales this (SKILL.md table): shallow skips Phase 3 entirely; exhaustive runs
multiple waves and does not skip while any novelty remains.

Skip Phase 3 entirely if all Phase 2 decisions selected the obvious "follows existing
convention" option (no novel libraries to research), or whenever depth=shallow.

Inputs to each agent:
- decision: short name from Phase 2
- chosen_option: the user's pick
- rejected_options: the other options
- links_to_validate: any URLs from Phase 1 dp-research-shallow
- success_criteria: 1 to 2 specific things the dossier must confirm or deny

Each agent returns a dossier with sections: ## Verdict, ## Gotchas, ## Versioning,
## Canonical snippet, and optionally ## Contradiction.

If any dossier returns ## Contradiction, loop back to Phase 2 for that decision only.
Quote the contradicting evidence in the new AskUserQuestion. Do not silently override
the user's earlier choice.
```

## Phase 4: Synthesis and verification

```
Sub-steps in order:

1. Slug generation (orchestrator inline):
   - Construct slug from {user_intent_keywords, top_2_decision_choices}.
   - Format: [a-z0-9-]{1,60}, lowercase, hyphen-separated, no leading/trailing or
     double hyphens.
   - Run resolve_slug.py to normalise and check for collision:
       python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/resolve_slug.py \
         --slug <s> --plans-dir <d>
   - On collision, follow the R3 slug-collision flow (Phase 0 fragment, step 5).

2. Rename the Phase 2 draft folder to its final name (Phase 4.2, the single fail-closed
   rename point; guard BOTH the folder and the legacy flat form, and on guard failure
   follow the R3 collision flow instead of clobbering), then record the new path:
       test ! -e <plans_dir>/<slug> && test ! -e <plans_dir>/<slug>.md && mv <plans_dir>/<topic>-draft <plans_dir>/<slug>
       python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
         --update plan_path=<plans_dir>/<slug>/plan.md --session-id ${CLAUDE_SESSION_ID}
   Issue the guarded command with project-relative paths (docs/plans/...) from the
   project root when plans_dir is inside the project (permission rules prefix-match the
   literal command string); fall back to absolute paths otherwise (may prompt once).
   From here on every plan write edits plans_dir/<slug>/plan.md in place. It is the
   single canonical plan file; there is no mirror.

3. Perspective fan-out: launch dp-plan-perspective agents in parallel. One instance
   always carries the deep-modules perspective; the picked count scales by depth
   (SKILL.md table): shallow=1, standard=1 to 3, exhaustive=3, each picked from
   {simplicity, performance, maintainability, minimal-diff, security} per the user's
   evident priorities. See references/perspectives.md for selection heuristics.

4. Synthesis: merge perspectives into a single plan body using
   references/plan-file-template.md as the skeleton, editing plans_dir/<slug>/plan.md
   in place over the draft-seeded sections. Include the **Tests (TDD)** subsection
   only for tasks that produce or modify code, carrying the template's full field
   schema per code task and applying ## Plan-time authoring rules of
   ${CLAUDE_PLUGIN_ROOT}/skills/tdd-review/references/test-principles.md;
   omit it for markdown, docs, or config tasks. Append the Phase 3 dossiers
   verbatim under a ## Research dossiers appendix so they survive into the
   archived folder members.
   In the same sub-step, seed <plans_dir>/<slug>/design.md from
   references/design-md-template.md: one D{N} subsection per decision row with the
   expanded rationale and evidence links (into the sibling research.md when Phase 3
   ran; Phase 1 evidence inline or n/a otherwise). Leave ## Implementation notes
   empty; the execute skill appends to it per completed task.
   Merge rules:
   - When perspectives disagree on task ordering or test scope, prefer the union (additive).
   - When perspectives disagree on architectural choice, that means a sub-decision was
     missed; loop back to Phase 2.

5. Verification probes: run inline Bash checks against design assumptions. Examples:
       python3 -c "import redis; print(redis.__version__)"
       grep -rl 'TokenBucket' src/
       uv run pytest --collect-only tests/middleware/
   Capture each probe's output into the plan's `## Verification probes` appendix as:
       [probe N]: <command>
       <stdout, truncated to ~20 lines>
   Probes run sequentially for deterministic ordering. Probes that need to write
   fixtures write under the sandbox; the hook permits this.

After all sub-steps, proceed to Phase 4.6 (adversarial critique) before Checkpoint 2.
```

## Phase 4.6: Adversarial critique

```
Goal: try to refute the synthesized plan before the user is asked to approve it.

Launch one dp-plan-critic (inherit) with: the synthesized plan body, the ## Decisions made
table, the Phase 1 evidence, and the Phase 3 dossiers. It returns findings under
## Missing tasks, ## Wrong or missing dependencies, ## Code tasks lacking tests,
## Decisions contradicted by research, and ## Untested assumptions, each tagged
material|minor, plus a one-line ## Verdict.

In the same launch message, run the design fleet per
${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md: one
dp-design-critic (haiku) per red-flag cluster in design-principles.md, reviewing the
synthesized plan body and its ## Architecture section as a design artifact, then the
recipe's adversarial verify stage (Workflow path when available, fallback otherwise).
Also run the same recipe with agentType deep-plan:dp-test-critic: one finder per H3
cluster of ## Review-time red flags in
${CLAUDE_PLUGIN_ROOT}/skills/tdd-review/references/test-principles.md, reviewing
every task's **Tests (TDD)** block. Design and test findings carry the same
material|minor tags, merge into the handling below, and share the depth loop
bounds; no separate knobs.

Count and loop bound scale by depth (SKILL.md Depth scaling table):
- shallow:    one quick pass, no loop.
- standard:   one pass, loop back at most once if material findings remain.
- exhaustive: re-run until a pass has no material findings, capped at 3 rounds.

Act on findings:
- Material finding that reverses a user decision -> loop back to Phase 2 for that decision,
  quoting the critic's contradiction in the new AskUserQuestion. Never reverse it silently.
- Other material findings -> fix inline in the plan body (add the missing task, fix
  **Depends on**, add the missing **Tests (TDD)** block, add a verification probe), then
  re-run the critic if the depth loop bound allows.
- Minor findings -> append to ## Open questions (kept genuinely deferrable, since a
  non-empty ## Open questions blocks /deep-plan:deep-plan-execute later).

When the loop bound is reached or no material findings remain, finalize mechanically
BEFORE asking: complete the draft-to-slug folder rename if still pending, then run the
finalize_plan.py --repair pass (semantics in the Phase 5 fragment). Then present
Checkpoint 2:
    Q: "Plan written to <plans_dir>/<slug>/plan.md. What next?"
    Header: "Plan review"
    Options:
      1. "Approve and finalize" (Recommended)
      2. "Refine task <N>"
      3. "Drop task <N>"
      4. "Add a task"
      5. "Change a decision"

This question IS the approval gate (SKILL.md R2). The "approve" branch leads to Phase 5.
Other branches loop back appropriately.
```

## Phase 5: Archive and handoff

```
1. The repair pass runs BEFORE the Checkpoint 2 question (it cannot be skipped,
   because it precedes the approval):
       python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/finalize_plan.py \
         --repair --plan <plans_dir>/<slug>/plan.md

   finalize_plan.py auto-repairs the plan (em-dashes, task headers, missing
   sections and task subsections inserted as n/a, attribution stripped, the
   ## Task overview table regenerated between its markers) and prints
   {ok, fixes, warnings}. It does NOT reject a normal plan: it repairs in
   one pass. Paraphrase any non-empty fixes/warnings to the user in two or three
   lines (for example, a code task missing its **Tests (TDD)** block). Only
   ok=false (empty plan, or no tasks at all) warrants looping back to Phase 4.

2. On approval (Checkpoint 2 option 1, "Approve and finalize"): split the appendix
   sections into folder members in place (source and destination are the same file),
   record the approved-plan memo, then emit EXACTLY the handoff message:
       python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/finalize_plan.py \
         --archive --plan <plans_dir>/<slug>/plan.md --plans-dir <plans_dir> --slug <slug>

       python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
         --update last_plan_path=<plans_dir>/<slug>/plan.md --session-id ${CLAUDE_SESSION_ID}

       Plan approved and written to {plans_dir}/{slug}/plan.md (with research.md,
       probes.md, and design.md members when present; plans index refreshed at
       {plans_dir}/README.md).

       Recommended next: run `/compact` (or `/clear` if you do not need any planning
       context preserved). The lean plan file is the canonical input for implementation;
       the planning chatter (agent dossiers, perspective drafts, decision option sets)
       is no longer needed and consumes context.

       After /compact, prompt me to begin implementation.
```
