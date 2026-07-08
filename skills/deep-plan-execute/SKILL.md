---
name: deep-plan-execute
description: |
  Executes a plan produced by /deep-plan: the plan-folder artifact whose
  plan.md carries a ## Decisions made table and per-task **Tests (TDD)**
  blocks, located when no path is given through the approved-plan memo
  recorded at approval. Parses
  the plan's ## Tasks into harness tasks (one TaskCreate each), wires
  Depends on into addBlockedBy, then drives a test-first implementation
  loop task by task in dependency order. Invoke after a /deep-plan plan is
  approved and you are ready to build it, e.g. "implement the plan" or
  "/deep-plan:deep-plan-execute <plan-file>". Not for executing plans
  produced outside /deep-plan.
argument-hint: "[plan-path (plan.md file or plan folder)]"
---

# /deep-plan:deep-plan-execute

You are the implementation driver for a plan produced by `/deep-plan`. Your job
is to turn the plan's `## Tasks` block into real harness tasks with dependencies
and then implement them test-first, one at a time, in dependency order. The plan
file is the contract; do not redesign it. If you disagree with a task, surface it
to the user rather than silently deviating.

**Requires Claude Code >= v2.1.142** for the Task dependency API (`TaskUpdate`
`addBlockedBy`). If `TaskCreate`/`TaskUpdate` are unavailable, fall back to a flat
TodoWrite-style checklist and tell the user dependency wiring is degraded.

## Step 1: Resolve the plan file

1. If `$ARGUMENTS` names a path, use it as the plan file. A plan folder is
   accepted as-is: `load_tasks.py` resolves a folder to its `plan.md` member.
2. Otherwise, run the documented lookup:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py --lookup
   ```

   It prints `{ok, project_root, plans_dir, last_plan_path}`. Resolution order:

   - When `last_plan_path` is non-null, use it directly: it is the memo
     recorded at Phase 5 approval, and the script has already verified the
     file exists and still carries a `**Status**: approved` line.
   - Otherwise fall back to the most recently modified plan in the returned
     `plans_dir` (as `PLANS_DIR`), across both shapes (folder plans as
     `<slug>/plan.md`, legacy flat plans as `<slug>.md`):

     ```
     # newest mtime wins across both shapes; the path-anchored exclusion keeps the
     # generated README, legacy dotted siblings, and unfinished *-draft/ folders
     # from ever matching
     ls -td "$PLANS_DIR"/*/plan.md "$PLANS_DIR"/*.md 2>/dev/null | grep -vE '(/(README|[^/]*\.(probes|research))\.md$|-draft/plan\.md$)' | head -1
     ```

   If no plan file can be resolved, ask the user via `AskUserQuestion` for the
   path. Do not guess.

## Step 2: Parse the plan

Run the parser (it lives in the sibling `deep-plan` skill):

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/load_tasks.py --plan <plan-file>
```

It prints JSON `{ok, tasks, decisions, open_questions, plan}`. Each task is
`{n, subject, target_files, change, tests, verification, depends_on:[int]}`.
`tests` is `null` for docs/config tasks. If `ok` is false (no tasks parsed),
stop and tell the user the plan has no `## Tasks` to execute.

## Step 3: Gate on open questions

If `open_questions` is anything other than empty, `none`, or `n/a`
(case-insensitive, ignoring a leading `- `), STOP. Do not create tasks. Present
the open questions to the user via `AskUserQuestion` and ask them to resolve or
explicitly defer each one. Only proceed once `open_questions` is clear. Rationale:
the plan template treats a non-empty `## Open questions` as a hard block on
implementation.

Read `decisions` once and keep them in context as the prologue: they are the
resolved choices the tasks assume. Do not re-litigate them.

## Step 4: Create tasks (two passes)

The Task API has no bulk import and sets dependencies after creation, so use two
passes over the parsed `tasks`, in plan order:

**Pass 1 -- create.** For each task, call `TaskCreate`:

- `subject`: `Task {n}: {subject}`
- `description`: the `change` text, followed by the `target_files` list, the
  `tests` block (if present), and the `verification` command. This is the
  task's acceptance criteria.

Capture the returned id (`{task:{id}}`, an opaque string) into an
`int -> id` map keyed by the task's `n`. Do NOT assume ids are sequential or
numeric.

**Pass 2 -- wire dependencies.** For each task whose `depends_on` is non-empty,
call `TaskUpdate`:

- `taskId`: the id of this task (from the map)
- `addBlockedBy`: `[ map[d] for d in depends_on ]`

Only `addBlockedBy` is relied on here; it is the confirmed field. If a
`depends_on` integer has no entry in the map (dangling reference), skip it and
warn the user rather than failing.

## Step 5: Implement test-first, in dependency order

Process tasks in topological order (a task runs only after every task it is
blocked by is done). For each task, mark it `in_progress` via `TaskUpdate`,
capture a baseline ref for the design review in step 4 (`git stash create`;
empty output means the tree is clean, use `HEAD`), then:

1. **If the task has a `tests` block (code task):** write the test described in
   `tests` FIRST. Quote `## Execute-time run rules` of
   `${CLAUDE_PLUGIN_ROOT}/skills/tdd-review/references/test-principles.md` and
   `## Execute-time craft rules` of
   `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/design-principles.md`
   into the implementation turn alongside the task description; they govern how
   the test and the code are written. Run the `verification` command and
   confirm it FAILS (red). If it passes before you have written any
   implementation, the test is wrong or the behaviour already exists -- stop
   and tell the user.
2. **Implement** the `change` against the `target_files`. Touch only what the
   task names; other tasks own the rest.
3. **Run the `verification` command.** For a code task it must now pass (green).
   For a docs/config task (no `tests` block) the verification command is the
   acceptance check; run it and confirm it passes.
4. **Design-review the task's diff.** Collect the diff of THIS task only, not
   the accumulated run: the loop never commits between tasks, so a plain
   `git diff` would re-review earlier tasks' edits to shared files. Diff the
   baseline ref against the worktree, scoped to the task's `Target files`
   (`git diff <baseline> -- <target files>`), and pass the diff as text
   because the critics have no Bash. Run the design fleet on it per
   `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`
   (one `dp-design-critic` per red-flag cluster, then the verify stage), and
   run the same recipe with `agentType: deep-plan:dp-test-critic` on the same
   task-scoped diff (one finder per `## Review-time red flags` cluster of
   `${CLAUDE_PLUGIN_ROOT}/skills/tdd-review/references/test-principles.md`).
   Fix `material` findings within the task and re-run the `verification`
   command before completing; log `minor` findings in the task completion
   note without blocking. After first green and after any review fixes,
   re-run the task's `verification` command once more; treat a second-run
   failure as a stability finding that blocks completion until the flake is
   understood and fixed. This is the loop's enforcement of the `Re-run
   after green` run rule in test-principles.md.
5. **Record the implementation note (MANDATORY for folder plans).** After
   verification passes and before the task is marked completed: append one
   terse `### Task {N}: {name}` entry (2 to 4 lines: deviations from the plan,
   gotchas hit, non-obvious code shapes) under `## Implementation notes` in
   the plan folder's sibling `design.md`. If a crashed or hand-made folder
   lacks `design.md`, create it first from
   `${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/references/design-md-template.md`.
   Legacy flat plans (no folder) skip this append.
6. On green, mark the task `completed` via `TaskUpdate`. On red you cannot fix
   within the task's scope, stop and report rather than expanding scope.

Run verification commands exactly as written in the plan. If a command assumes
`uv run` but the project has no `pyproject.toml`, fall back to `python3` and note
the substitution.

## Step 6: Completion (folder plans only)

After ALL tasks are completed, for folder plans only:

1. Flip the `**Status**: approved` line in the plan's `plan.md` to
   `**Status**: executed`. When no Status line exists, add
   `**Status**: executed` under the H1 rather than failing.
2. Refresh the plans index:

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/finalize_plan.py \
     --index --plans-dir <plans_dir>
   ```

Legacy flat plans skip both steps: they carry no Status line and may predate
the README index.

## Anti-patterns

- Creating all tasks then implementing out of dependency order.
- Skipping the failing-test-first step for a code task.
- Editing files a task does not list under `Target files`.
- Proceeding past a non-empty `## Open questions`.
- Re-opening a decision already settled in `## Decisions made` without asking.
- Batching unrelated tasks into one `TaskCreate`.
- Marking a task completed with unresolved material design findings.
- Marking a task completed without the post-green stability re-run.
- Marking a task completed without its design.md implementation note (folder plans).
