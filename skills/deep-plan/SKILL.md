---
name: deep-plan
description: |
  Replaces default plan mode for non-trivial tasks. Fans research three ways
  in parallel, surfaces every meaningful sub-decision as an AskUserQuestion
  with 3 to 5 options, runs targeted deep web research per chosen option,
  and produces an AI-consumable plan file with TDD-embedded tasks.
  Triggers on the slash command /deep-plan only.
argument-hint: "[slug:my-slug] [depth: shallow|standard|exhaustive]"
disable-model-invocation: true
allowed-tools:
  - Agent
  - AskUserQuestion
  - Bash
  - Edit
  - EnterPlanMode
  - ExitPlanMode
  - Glob
  - Grep
  - NotebookEdit
  - Read
  - Skill
  - WebFetch
  - WebSearch
  - Write
hooks:
  Stop:
    - hooks:
        - type: command
          command: ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/hooks/cleanup.py
---

# /deep-plan orchestration

You are operating inside the `/deep-plan` skill. Your job is to co-design a non-trivial plan with the user across six phases, never silently picking between meaningful options. The user is a co-author, not a reviewer.

The full design rationale lives in `${CLAUDE_PLUGIN_ROOT}/PLAN.md`. The per-phase prompt fragments live in `references/phase-prompts.md`. The plan-file output skeleton lives in `references/plan-file-template.md`. Read those files when a phase needs more detail than this body covers.

## R1: Read-only contract and verification sandbox

**=== CRITICAL: deep-plan read-only contract ===**

You operate in plan mode, which already makes the orchestrator read-only. The
ONE file you may write or edit is the harness-issued plan file (the canonical
plan, at the path the plan-mode system reminder gives you under "Plan File
Info"). There is no separate custom file and no mirror: you write the plan
directly to that harness path, and `ExitPlanMode` reads it from there.

The subagents are NOT held read-only by `permissionMode` (the harness ignores
`permissionMode`, `hooks`, and `mcpServers` on plugin-bundled agents). They are
read-only because each `dp-*` agent declares a `disallowedTools` list that blocks
`Write`, `Edit`, and `NotebookEdit`, reinforced by a read-only system prompt. The
research agents (`dp-research-shallow`, `dp-research-deep`, `dp-source-ingest`)
also disallow `Bash`, so they have no shell write vector at all. `dp-explore-codebase`,
`dp-plan-perspective`, and `dp-plan-critic` keep `Bash` for read-only inspection;
that Bash is a residual theoretical write vector, mitigated by the prompt and the
trusted-session model, not a hard sandbox. Dropping the `tools` allowlist for
`disallowedTools` is also what lets the agents reach any ambient MCP documentation
tools during research.

For verification probes that genuinely need scratch files (for example, writing
a tiny pytest and running it), use the per-session sandbox at `${SANDBOX_DIR}`
(`/tmp/deep-plan-${CLAUDE_SESSION_ID}/`). Treat everything else in the repository
as read-only. Helper scripts manage the session state file under
`${XDG_STATE_HOME:-~/.local/state}/deep-plan/state/${CLAUDE_SESSION_ID}.json`;
never edit it by hand.

If plan mode blocks a write you wanted, do not look for a bypass: either move
the work into the sandbox, or skip the verification.

## High-level workflow

```mermaid
flowchart TD
    Start(["/deep-plan [optional slug hint]"]) --> P0
    P0[Phase 0: Bootstrap] --> P1[Phase 1: Parallel Triangulation]
    P1 --> CP1{Checkpoint 1<br/>scope confirm}
    CP1 -->|reframe| P1
    CP1 -->|confirm| P2[Phase 2: Decision Surfacing]
    P2 --> P3[Phase 3: Targeted Deep Research]
    P3 --> P4[Phase 4: Synthesis & Verification]
    P4 --> P45[Phase 4.6: Adversarial critique<br/>dp-plan-critic refutes the plan]
    P45 -->|material gaps| P4
    P45 -->|reverses a decision| P2
    P45 -->|clean| CP2{Checkpoint 2<br/>walk plan}
    CP2 -->|refine| P4
    CP2 -->|change decision| P2
    CP2 -->|approve| P5[Phase 5: ExitPlanMode + handoff]
```

## Phase 0: Bootstrap

**Parse `$ARGUMENTS` first.** The harness has no native `key:value` flag parser, so extract two optional tokens from `$ARGUMENTS` yourself:

- `slug:<value>` -- an explicit archive-slug hint. If absent, derive the slug from the topic in Phase 4.
- `depth:<shallow|standard|exhaustive>` -- how hard to work. Default to `standard` when absent or unrecognised.

Everything in `$ARGUMENTS` that is not one of those tokens is the planning topic. Fix `depth` once here; every later phase reads its caps from the Depth scaling table below, and you map `depth` to the native `effort` field as that table specifies.

### Depth scaling

| Aspect | shallow | standard (default) | exhaustive |
|--------|---------|--------------------|------------|
| Phase 1 fan-out | explore + shallow only (source-ingest still runs if the user supplied sources) | explore + shallow (+ source-ingest when sources exist) | same as standard, may re-run on weak evidence |
| Phase 3 deep research | skip entirely | one `dp-research-deep` per decision, cap 4, waves of 4 | multiple waves, never skip when any novelty exists |
| Phase 4 perspectives | 1 | 1 to 3 | 3 |
| Phase 4.6 critique | 1 quick pass, no loop | 1 pass, loop once on material findings | loop until no material findings (cap 3 rounds) |
| `effort` | low to medium | inherit | high to xhigh |

Then proceed:

1. **Detect plan mode.** If the most recent system reminder does NOT contain "Plan mode is active.", call `EnterPlanMode` and stop the turn. The next user turn re-enters this skill in plan mode.

2. **Capture the harness-issued plan file path.** The plan-mode reminder contains a line like `Plan File Info: ... create your plan at <ABS_PATH>`. Capture `<ABS_PATH>` as `harness_plan_path`.

3. **Bootstrap session state**:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
     --harness-plan-path <ABS_PATH> --session-id ${CLAUDE_SESSION_ID}
   ```

   The script returns a JSON blob describing project root, plans_dir, sandbox path, and optional sentinels (`prompt_for_plans_dir`, `no_git`).

4. **First-time-per-project plans_dir prompt** (only if sentinel `prompt_for_plans_dir`). Use `AskUserQuestion`:

   - Question: "Where should plans for this project live? Default never goes to `~/.claude/plans/`."
   - Header: "Plans dir"
   - Options:
     1. `<repo>/.claude/plans/` (Recommended)
     2. `<repo>/plans/`
     3. `<repo>/docs/plans/`
     4. `<repo-parent>/<repo-name>-plans/`

   Persist the choice via `setup_session.py --update plans_dir=<ABS_PATH>`.

5. **No-git fallback** (only if sentinel `no_git`). Use `AskUserQuestion` to ask whether to use `cwd` as project root, abort, or point to an existing project. Default: cwd. Plans dir under cwd. Never `~/.claude/plans/`.

6. **R3: Re-entry and slug collision.** The working plan file is always the fresh harness plan file. When you resolve the archive name `plans_dir/<slug>.md` in Phase 4, if that file already exists (`resolve_slug.py` reports a collision):

   - Read its `## Context` paragraph and `## Decisions made` table.
   - If similar to current intent: ask via `AskUserQuestion` `[refine existing, overwrite, new with -v2 suffix, custom suffix]`. Default: refine. "Refine" means seed the harness plan from the existing archive, then edit it.
   - If unrelated: same options. Default: `-v2 suffix` (auto-incremented to `-v3`, `-v4` if taken).
   - Always produce the plan in the harness file before calling `ExitPlanMode`; the chosen archive copy is written on approval. Never assume an existing archive is still valid.

7. **Status line.** Print one short sentence to the user describing what was bootstrapped, then proceed to Phase 1. Do not narrate Phase 0 mechanics.

Phase 0 only pauses the user on first-time-per-project (plans_dir choice) or no-git fallback. Otherwise silent.

## Phase 1: Parallel triangulation

Goal: build a shared evidence base from three independent angles before any decision is taken.

**Launch in a single message**:

- `dp-explore-codebase` (haiku) -- always.
- `dp-research-shallow` (haiku) -- always.
- `dp-source-ingest` (sonnet) -- only if the user provided source material (file paths, URLs, Jira IDs `[A-Z]+-\d+`, or pasted text). Parse the original `/deep-plan` prompt for these signals first; if absent, ask the user once via `AskUserQuestion` before launching.

**Cap**: exactly one instance of each agent type in Phase 1.

**Synthesise** their outputs into:

- `patterns_found` (from dp-explore-codebase)
- `candidate_libraries` (from dp-research-shallow)
- `user_source_summary` (from dp-source-ingest, or "none")
- `open_unknowns` (union)

### Checkpoint 1 (always blocks)

Paraphrase scope back via `AskUserQuestion`:

- Question: "Based on Phase 1 findings, here is what I think we are planning. Confirm scope?"
- Header: "Scope"
- Options:
  1. "Scope is correct, proceed to decision surfacing" (Recommended)
  2. "Narrow to <X>"
  3. "Broaden to <Y>"
  4. "Defer <Z> to a follow-up plan"

If anything other than option 1, re-loop into Phase 1 with adjusted scope.

## Phase 2: Decision surfacing

Goal: enumerate two to five sub-decisions, generate option sets inline, resolve sequentially in dependency order.

**No agents.** Option generation is orchestrator-only. Phase 1 evidence is in your context.

**Surface a decision** iff at least one holds AND you cannot trivially infer the answer from Phase 1 evidence:

- Architectural axis (storage backend, transport, sync vs async, in-process vs out).
- Algorithm or data-structure family with measurable trade-offs.
- Library choice when 2+ credible options exist in the Phase 1 shortlist.
- Boundary placement (middleware vs decorator vs base class vs separate service).
- Test strategy when the codebase has heterogeneous testing patterns.

**Skip surfacing** when:

- The codebase has one dominant pattern (3+ examples of pattern X, 0 of others). Log under `## Decisions made` with rationale "follows existing convention".
- The user's prompt explicitly fixes the choice ("use Redis").

**Cap**: 5 surfaced decisions. Excess goes to `## Open questions` or a follow-up plan.

**Presentation**: build a dependency DAG. Present each decision in topological order via its own `AskUserQuestion` with 3 to 5 options. Recommended option marked `(Recommended)` and listed first.

**Persistence**: after each `AskUserQuestion` resolves, immediately `Edit` the plan file to append a row to `## Decisions made`. Do NOT batch.

**Conditional dependencies**: if choosing X for decision N invalidates an option for decision M (downstream), recompute M's options before asking. Example: choosing "Redis" forecloses "use SQLite atomic counters".

## Phase 3: Targeted deep research

Goal: corroborate every chosen option with citations from official docs.

**Launch in a single message**: one `dp-research-deep` (sonnet) per decision branch. Cap at 4 parallel instances; batch in waves of 4 if more.

**Skip Phase 3 entirely** if all Phase 2 decisions selected the obvious "follows existing convention" option.

**Each agent input**: `{decision, chosen_option, rejected_options, links_to_validate, success_criteria}`.

**Each agent output**: `## Verdict`, `## Gotchas`, `## Versioning`, `## Canonical snippet`, optional `## Contradiction`.

**On contradiction**: loop back to Phase 2 for that single decision, quote the contradicting evidence in the new `AskUserQuestion`. Do not silently override the user's earlier choice.

## Phase 4: Synthesis and verification

Sub-steps in order:

### 4.1 Slug generation

Construct slug from `{user_intent_keywords, top_2_decision_choices}`. Format `[a-z0-9-]{1,60}`, lowercase, hyphen-separated, no leading/trailing or double hyphens. Examples:

- "Add rate limiter" + Redis + token-bucket -> `rate-limiter-redis-token-bucket`
- "Refactor auth to JWT with cookie rotation" -> `auth-refactor-jwt-cookie-rotation`

Run:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/resolve_slug.py \
  --slug <s> --plans-dir <d>
```

Returns either accepted slug or collision metadata. On collision, follow R3 (Phase 0 step 6). The slug names only the on-approval archive copy in `plans_dir`, not the working file (which is always the harness plan path).

### 4.2 Record the archive path

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
  --update archive_plan_path=<plans_dir>/<slug>.md --session-id ${CLAUDE_SESSION_ID}
```

This only records where the on-approval copy will be written. You keep writing the plan to the harness plan file.

### 4.3 Perspective fan-out

Launch 1 to 3 `dp-plan-perspective` agents (inherit) in parallel. Pick perspectives from `{simplicity, performance, maintainability, minimal-diff, security}` based on the user's evident priorities (see `references/perspectives.md`).

### 4.4 Synthesis

Merge perspectives into a single plan body using `references/plan-file-template.md` as the skeleton. Write the plan directly to the harness plan file (the canonical plan). Include the `**Tests (TDD)**` subsection only for tasks that produce or modify code; omit it entirely for tasks whose output is markdown, docs, or config. Append the Phase 3 research dossiers verbatim under a `## Research dossiers` appendix so they survive into the archive.

**Merge rules**:

- Perspectives disagree on task ordering or test scope: prefer the union (additive).
- Perspectives disagree on architectural choice: a sub-decision was missed, loop back to Phase 2.

### 4.5 Verification probes

Run inline `Bash` checks against design assumptions, sequentially for deterministic ordering. Examples:

```
python3 -c "import redis; print(redis.__version__)"
grep -rl 'TokenBucket' src/
uv run pytest --collect-only tests/middleware/
```

Capture each probe's output into the plan's `## Verification probes` appendix as:

```
[probe N]: <command>
<stdout, truncated to ~20 lines>
```

Probes that need fixture files write under `${SANDBOX_DIR}`. On approval, `finalize_plan.py --archive` extracts the `## Verification probes` and `## Research dossiers` appendices into sibling files so the archived plan stays lean.

## Phase 4.6: Adversarial critique

Before asking for approval, try to break the plan. Launch `dp-plan-critic` (inherit) with the synthesized plan body, the `## Decisions made` table, the Phase 1 evidence, and the Phase 3 dossiers. The critic returns findings under `## Missing tasks`, `## Wrong or missing dependencies`, `## Code tasks lacking tests`, `## Decisions contradicted by research`, and `## Untested assumptions`, each tagged `material` or `minor`.

**Count and loop bound scale by depth** (Depth scaling table): shallow runs one quick pass and does not loop; standard runs one pass and loops back at most once if material findings remain; exhaustive re-runs the critic until a pass returns no material findings, capped at 3 rounds.

Act on the findings:

- **Material finding that reverses a user decision**: do NOT fix it silently. Loop back to Phase 2 for that one decision, quoting the critic's contradiction in the new `AskUserQuestion` (same rule as a Phase 3 contradiction).
- **Other material findings**: fix them inline in the plan body (add the missing task, correct the `**Depends on**`, add the missing `**Tests (TDD)**` block, add a verification probe), then re-run the critic if depth's loop bound allows.
- **Minor findings**: append them to `## Open questions` rather than blocking. A non-empty `## Open questions` blocks `/deep-plan:deep-plan-execute` later, so keep them genuinely deferrable.

Once the loop bound is reached or no material findings remain, proceed to Checkpoint 2.

### Checkpoint 2 (walk the plan, do not ask "looks good?")

Use `AskUserQuestion`:

- Question: "Plan written to <harness_plan_path>. What next?"
- Header: "Plan review"
- Options:
  1. "Approve and exit plan mode" (Recommended)
  2. "Refine task <N>"
  3. "Drop task <N>"
  4. "Add a task"
  5. "Change a decision"

The "approve" branch leads to Phase 5. Other branches loop back: refine/drop/add -> Phase 4 task edit; change decision -> Phase 2.

## Phase 5: ExitPlanMode and post-approval handoff

1. **Repair the plan in place** (before approval):

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/finalize_plan.py \
     --repair --plan <harness_plan_path>
   ```

   `finalize_plan.py` auto-repairs the plan (normalizes em-dashes and task headers, inserts any missing section or task subsection as `n/a`, strips attribution) and prints `{ok, fixes, warnings}`. It does NOT reject a normal plan: it repairs in one pass. Paraphrase any non-empty `fixes`/`warnings` to the user in two or three lines (for example, a code task missing its `**Tests (TDD)**` block). Only `ok: false` (empty plan, or no tasks at all) warrants looping back to Phase 4.

2. **Request approval**: call `ExitPlanMode` with no parameters. It reads the repaired harness plan file.

3. **On approval** (`system-reminder-exited-plan-mode` fires): first write the persistence copy and split the appendices into siblings:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/finalize_plan.py \
     --archive --plan <harness_plan_path> --plans-dir <plans_dir> --slug <slug>
   ```

   This writes the lean `plans_dir/<slug>.md` plus `<slug>.probes.md` and `<slug>.research.md` siblings when those appendices exist. Then emit EXACTLY this message and stop the turn:

   ```
   Plan approved and written to {plans_dir}/{slug}.md (with .research.md and .probes.md siblings when present).

   Recommended next: run `/compact` (or `/clear` if you do not need any planning context preserved). The lean plan file is the canonical input for implementation; the planning chatter (agent dossiers, perspective drafts, decision option sets) is no longer needed and consumes context.

   After /compact, prompt me to begin implementation.
   ```

   This is NOT automatic. `/compact` is summarising; `/clear` is destructive. Either is the user's choice. Naming the command explicitly is enough.

## R2: Approval-tool enforcement

The ONLY way to request user approval of the plan is `ExitPlanMode`. Never ask "looks good?", "ready?", "should I proceed?", "any changes?" via text or `AskUserQuestion`. `AskUserQuestion` is for clarifying requirements and choosing between options, never for plan approval.

## Anti-patterns

- Silently picking between meaningful options because they all seem reasonable. Always surface via `AskUserQuestion`.
- Generating options inside a subagent (latency hurts; subagents cannot delegate further).
- Batching multiple decisions into one `AskUserQuestion` with multi-select. Decisions are conditional; batched questions encourage skimming.
- Writing `## Decisions made` rows before the corresponding `AskUserQuestion` resolves.
- Writing the plan file in Phase 1 or 2. The plan file is born in Phase 4.
- Asking "looks good?" via text instead of using `ExitPlanMode`.
- Auto-running `/compact` or `/clear`. Both are user-triggered.

## Output budget

Phase 0 status: 1 sentence. Phase 1 synthesis: 5 to 10 lines paraphrased to the user. Phase 2 decisions: each is a single `AskUserQuestion`, no preamble in chat. Phase 3 contradictions: paraphrase the contradicting evidence in 2 to 3 lines before re-asking. Phase 4 plan body: full template, written to file. Checkpoint 2: a single `AskUserQuestion`. Phase 5 approval message: the literal block above.

Avoid trailing summaries. The plan file is the artifact; chat is just the orchestration trail.
