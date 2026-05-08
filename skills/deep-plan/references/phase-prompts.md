# Phase-prompt fragments

Long-form per-phase prompts the orchestrator quotes into context as needed. The skill body in `SKILL.md` is the short orchestration; this file is the detail.

## Phase 0: Bootstrap

```
You are at the start of /deep-plan. Before doing anything else:

1. Check the most recent system reminder. If it does NOT contain "Plan mode is active.",
   call EnterPlanMode and stop. The next user turn re-enters this skill in plan mode.

2. Find the harness-issued plan file path. The plan-mode reminder contains a line like
   "Plan File Info: ... create your plan at <ABS_PATH>". Capture <ABS_PATH>.

3. Run setup_session.py to bootstrap session state:
       python3 ~/.claude/skills/deep-plan/scripts/setup_session.py \
         --harness-plan-path <ABS_PATH> \
         --session-id <SESSION_ID>

   The script returns a JSON blob describing the resolved project root, plans_dir, and
   sandbox path, plus optional sentinels:
   - prompt_for_plans_dir: true   -> ask the user via AskUserQuestion (4 options below).
   - no_git: true                 -> ask the user whether to use cwd as project root.

4. Plans-dir options when prompting (Phase 0):
   1. <repo>/.claude/plans/                (Recommended)
   2. <repo>/plans/
   3. <repo>/docs/plans/
   4. <repo-parent>/<repo-name>-plans/

   The default MUST NOT be ~/.claude/plans/. Persist the user's choice via:
       python3 ~/.claude/skills/deep-plan/scripts/setup_session.py \
         --update plans_dir=<ABS_PATH> --session-id <SESSION_ID>

5. After state is bootstrapped, print a single short status sentence to the user and
   proceed to Phase 1. Do not narrate Phase 0's mechanics.
```

## Phase 1: Parallel triangulation

```
Goal: build a shared evidence base from three independent angles before any decision
is taken. Launch up to three subagents in a single message:

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

After each AskUserQuestion resolves, immediately Edit the plan file to append a row to
the `## Decisions made` table. This is the persistence point: do NOT batch.

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

Skip Phase 3 entirely if all Phase 2 decisions selected the obvious "follows existing
convention" option (no novel libraries to research).

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
       python3 ~/.claude/skills/deep-plan/scripts/resolve_slug.py \
         --slug <s> --plans-dir <d>
   - On collision, follow the section "Slug generation and collision handling" in PLAN.md.

2. Update state with the resolved custom_plan_path:
       python3 ~/.claude/skills/deep-plan/scripts/setup_session.py \
         --update custom_plan_path=<plans_dir>/<slug>.md --session-id <SESSION_ID>

3. Perspective fan-out: launch 1 to 3 dp-plan-perspective agents in parallel. Pick from
   {simplicity, performance, maintainability, minimal-diff, security} per the user's
   evident priorities. See references/perspectives.md for selection heuristics.

4. Synthesis: merge perspectives into a single plan body using
   references/plan-file-template.md as the skeleton.
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

After all sub-steps, present Checkpoint 2:
    Q: "Plan written to <custom_plan_path>. What next?"
    Header: "Plan review"
    Options:
      1. "Approve and exit plan mode" (Recommended)
      2. "Refine task <N>"
      3. "Drop task <N>"
      4. "Add a task"
      5. "Change a decision"

The "approve" branch leads to Phase 5. Other branches loop back appropriately.
```

## Phase 5: ExitPlanMode and handoff

```
1. Run finalize_plan.py:
       python3 ~/.claude/skills/deep-plan/scripts/finalize_plan.py \
         --custom <custom_plan_path> --harness <harness_plan_path>

   The script:
   - Validates required sections present (Context, Decisions made, Tasks with all
     subsections, References, Open questions).
   - Copies custom_plan_path to harness_plan_path so ExitPlanMode reads the right file.
   - If the canonical file starts with `<!-- deep-plan-version:`, also mirrors it to
     ~/gits/plan-modes/deep-plan/PLAN.md.
   - Returns "ok" or a list of validation failures.

2. On "ok": call ExitPlanMode with no parameters.

3. On validation failure: surface failures via AskUserQuestion and loop back to Phase 4.

4. On approval (system-reminder-exited-plan-mode fires): emit EXACTLY this message
   and stop the turn:

       Plan approved and written to {custom_plan_path}.

       Recommended next: run `/compact` (or `/clear` if you do not need any planning
       context preserved). The plan file is the canonical input for implementation;
       the planning chatter (agent dossiers, perspective drafts, decision option sets)
       is no longer needed and consumes context.

       After /compact, prompt me to begin implementation.
```
