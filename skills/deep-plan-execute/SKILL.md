---
name: deep-plan-execute
description: |
  Use after a /deep-plan plan is approved and you are ready to build it:
  "implement the plan", or /deep-plan:deep-plan-execute <plan-path>. Dispatches
  the plan's tasks in dependency order, one writable agent each. Not for plans
  produced outside /deep-plan.
argument-hint: "[plan-path (plan.md file or plan folder)]"
---

# /deep-plan:deep-plan-execute

You are the dispatcher for a plan produced by `/deep-plan`. Your job is to turn the
plan's `## Tasks` block into real harness tasks with dependencies, then dispatch
each one to a writable implementer agent in dependency order and audit what it
changed. The plan file is the contract; do not redesign it. If you disagree with a
task, surface it to the user rather than silently deviating.

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
resolved choices the tasks assume. Do not re-litigate them. Their full stories
live in the plan folder's sibling `design.md`, a narrative design document (one
plain-language-question section per decision) each decision row links into;
consult it when a task's rationale is unclear. When the plan folder also
contains an `architecture.md` member, read it now: it carries the Today / After
world model the tasks assume.

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

## Preflight: warn about inherited permissions once

Subagents **inherit** the parent session's permission mode, and plugin-bundled
agents cannot set `permissionMode` (the harness ignores it, along with `hooks` and
`mcpServers`). So in default mode every `Write`, `Edit`, and `Bash` call inside
every implementer raises its own approval prompt -- dozens per task, and the user
is answering them for work they cannot see.

Before the first dispatch, tell the user this once, in one or two sentences. Name
the durable fix: a project-local `.claude/settings.json` allowlist covering the
tools the plan's tasks actually need. Offer to stop so they can add it. Then
proceed with whatever they choose -- a noisy run is their call to accept.

Never suggest a permission-bypass flag as the workaround. Not as a shortcut, not
as an aside, not even if the prompting is severe.

Two related bounds, so nobody looks for a shipped control that does not exist:

- Restricting which agent types the implementer may spawn needs a **user-side**
  `permissions.deny` rule. The parenthesised `Agent(type)` allowlist form is
  silently ignored inside a subagent definition, and plugins cannot ship
  permissions at all.
- What this plugin *does* ship is the `Workflow` denial in the agent's frontmatter
  plus the dispatcher's scope audit in Step 5. That is the whole enforcement
  surface; the rest is the trusted-session model.

## Step 5: Dispatch each task, then audit its scope

You do not implement tasks. One `dp-implement-task` agent implements each one in a
fresh context that is discarded on return, so the diff, the test output, and the
critic findings never enter your context at all. You own the task graph, the
dispatch order, and the scope audit.

Process tasks in topological order (a task runs only after every task it is
blocked by is done). For each task, six moves:

1. **Mark it `in_progress`** via `TaskUpdate`.
2. **Capture the baseline ref**: `git stash create`. Empty output means the tree
   is clean, so use `HEAD`.
3. **Snapshot pre-existing untracked paths**:

   ```
   git ls-files --others --exclude-standard
   ```

   Keep this list. Without it the audit in move 5 would blame the task for every
   scratch file already sitting in the user's tree.
4. **Launch exactly one `deep-plan:dp-implement-task`**, passing only four
   scalars: the plan path, the task number, the baseline ref, and `fleet_mode`
   (see `## Subagent budget`). Do not re-type the task's fields into the prompt --
   the agent fetches its own task body with `load_tasks.py --task <n>`, which
   keeps plan grammar owned by one function. Then read its six-line summary. That
   summary is all you get, and all you need.
5. **Audit the task's scope.** Build the task-attributable path set:

   ```
   git diff --name-only <baseline>
   git ls-files --others --exclude-standard
   ```

   The set is the union of those two, MINUS the move-3 snapshot. Both halves are
   required: a plain diff omits files the task newly created, while a bare
   untracked listing would wrongly attribute pre-existing scratch files.

   Compare that set against the task's `Target files`. The plan folder's own
   `design.md` is always in scope, since the agent's implementation note targets
   it. If any path remains outside, do NOT complete the task: report the
   offending paths to the user and stop. Never auto-revert -- the edit may be
   correct and the plan wrong, and that is the user's call.
6. **Complete or block.** With a clean audit and a `status: done` summary, mark
   the task `completed`. On `status: blocked`, or a failed audit, stop and report
   rather than expanding scope or re-dispatching blindly.

The agent owns everything inside the increment: the failing test first, the red
and green runs, the execute-time run and craft rules, the task-scoped diff, its
own nested design and test critic fleets, the material-finding fixes, the
stability re-run, and the `design.md` note append. All of it is specified in
`agents/dp-implement-task.md`; do not restate it here and do not do it yourself.

Verification commands run exactly as the plan writes them. If one assumes `uv run`
but the project has no `pyproject.toml`, the fallback is `python3` and the
substitution is reported in the summary's `deviations` line.

## Subagent budget

Delegation spends subagents, and the caps count nested children. They live in
`${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`
under `## Session agent budget`: **200 subagents** per session and 20 concurrent.

Do the arithmetic honestly. One implementer plus 8 finders is 9 agents per task at
minimum, but the fleet's verify stage launches one agent per surviving deduped
finding and is uncapped, so a task with many findings can pass 20. The per-task
figure is a **range of 9 to roughly 20**, not a fixed 12 -- so derive thresholds
from the top of the range, never the bottom.

Pick `fleet_mode` from the parsed task count before the first dispatch:

| Tasks | `fleet_mode` | What the implementer runs |
|-------|--------------|---------------------------|
| up to 8 | `full` | both nested fleets, all clusters |
| 9 to 16 | `design-only` | the four design clusters as a fleet; tests reviewed inline |
| more than 16 | `inline` | no nested fleet; the implementer reviews its own diff |

Announce the chosen mode and its reason in one sentence before dispatching the
first task. If a blocked task forces a re-dispatch, that consumes budget the
table did not price: re-announce the mode, downgrading it when the remaining
task count no longer fits.

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
- Implementing a task in the dispatcher context instead of dispatching it.
- Marking a task completed with an unaudited diff.
- Reading a diff in the orchestrator; the whole point is that it stays below.
