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
   An explicit path is no shortcut past approval: it goes through the same
   Step 2 gate as a looked-up one.
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

The parser refuses a folder plan whose `plan.md` does not carry
`**Status**: approved`, printing `{ok: false, error: "plan is not approved:
..."}` and exiting 1. That means the plan never reached Phase 5 approval, so
stop and send the user back to `/deep-plan` rather than executing a draft.
Append `--allow-unapproved` only when the user is deliberately re-running a
plan they have already approved and since edited. A legacy flat plan
(`<slug>.md` outside a folder) has no Status line and is never checked.

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

- The implementer ships with `Agent` denied outright, so it spawns nothing at all.
  Restricting *which* types some other subagent may spawn would need a
  **user-side** `permissions.deny` rule: the parenthesised `Agent(type)` allowlist
  form is silently ignored inside a subagent definition, and plugins cannot ship
  permissions at all.
- What this plugin *does* ship is that denial plus the `Workflow` one in the
  agent's frontmatter, and the dispatcher's scope audit in Step 5. That is the
  whole enforcement surface; the rest is the trusted-session model.

## Step 5: Dispatch each task, audit its scope, then review its diff

You do not implement tasks. One `dp-implement-task` agent implements each one in a
fresh context that is discarded on return, so the test output, the turn-by-turn
reasoning and the file contents never enter your context at all. You own the task
graph, the dispatch order, the scope audit, and the review of what came back.

Trust nothing you did not see. The agent's summary says what it believes it did;
the audit and the fleet below are how you find out.

Process tasks in topological order (a task runs only after every task it is
blocked by is done). For each task, seven moves:

1. **Mark it `in_progress`** via `TaskUpdate`.
2. **Take the baseline.**

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/scope_audit.py snapshot --root <project root>
   ```

   It prints `{baseline, untracked}`: an unreachable commit recording the working
   tree as it stands, plus the paths that were already untracked when it was taken,
   so the audit cannot blame the task for scratch files that predate it. Keep that
   JSON verbatim -- moves 4 and 5 hand it straight back. Never take the baseline
   through `git stash`: it refuses whenever the index disagrees with disk, and the
   documented "empty output means the tree is clean, use `HEAD`" fallback then
   attributes every pre-existing edit to the task.
3. **Launch exactly one `deep-plan:dp-implement-task`**, passing three scalars: the
   plan path, the task number, and the snapshot's `baseline`. Do not re-type the
   task's fields into the prompt -- the agent fetches its own task body with
   `load_tasks.py --task <n>`, which keeps plan grammar owned by one function.
4. **Read the five-line summary.** If the returned text does not carry one, resume
   that agent once, asking for the summary alone. If it is still missing, run
   `scope_audit.py changed --root <project root> --snapshot '<the move-2 JSON>'`,
   report the paths it names, and mark the task blocked. Silence is not evidence
   that nothing was written.
5. **Audit the task's scope.**

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/scope_audit.py audit \
     --root <project root> --snapshot '<the move-2 JSON>' \
     --targets '<the task's Target files, comma-separated>' \
     --allow '<plan folder>/design.md'
   ```

   It exits non-zero and prints `{ok: false, unexpected: [...]}` when a changed path
   is outside that set. `--allow` carries the plan folder's own `design.md` because
   the agent's implementation note targets it. On a finding, do NOT complete the
   task: report the offending paths to the user and stop. Never auto-revert -- the
   edit may be correct and the plan wrong, and that is the user's call.
6. **Review the diff.** With a clean audit, run the critic fleet from this thread
   per `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`,
   with `deep-plan:dp-critic` as the leaf. The review target is `git diff <baseline>`
   plus the contents of the files the task created. Run it against two cluster
   sources: `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/design-principles.md`
   and `${CLAUDE_PLUGIN_ROOT}/skills/tdd-review/references/test-principles.md`, as
   `fleet_mode` selects (see the `Subagent budget` section).
   A `material` finding re-dispatches this task's implementer once, with those findings as its `findings` input, then re-runs moves 4 to 6.
   `minor` findings are appended to the task's entry in the plan folder's `design.md`.
7. **Complete or block.** With a clean audit, a `status: done` summary and no
   surviving `material` finding, mark the task `completed`. On `status: blocked`, a
   failed audit, or a second fleet run that still returns `material` findings, stop
   and report rather than expanding scope or re-dispatching again.

The agent owns everything inside the increment: the failing test first, the red and
green runs, the execute-time run and craft rules, its own self-check over the diff,
the stability re-run, and the `design.md` note append. All of it is specified in
`agents/dp-implement-task.md`; do not restate it here and do not do it yourself.

Verification commands run exactly as the plan writes them. If one assumes `uv run`
but the project has no `pyproject.toml`, the fallback is `python3` and the
substitution is reported in the summary's `deviations` line.

## Subagent budget

Delegation spends subagents, and the caps count nested children. They live in
`${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`
under `## Session agent budget`: **200 subagents** per session and 20 concurrent.

Do the arithmetic honestly. A task costs one implementer plus the fleet you launch
over its diff: 9 agents at minimum, but the fleet's verify stage launches one agent
per surviving deduped finding and is uncapped, so a task with many findings can pass
20. The per-task figure is a **range of 9 to roughly 20**, not a fixed 12 -- so
derive thresholds from the top of the range, never the bottom. A `material` finding
buys a second implementer and a second fleet for that task, which the range does not
price.

Pick `fleet_mode` from the parsed task count before the first dispatch. It selects
the fleet **you** run in move 6; the implementer is never told it:

| Tasks | `fleet_mode` | What you run in move 6 |
|-------|--------------|------------------------|
| up to 8 | `full` | both fleets, all clusters |
| 9 to 16 | `design-only` | the design clusters as a fleet; you read the tests yourself against `test-principles.md` |
| more than 16 | `inline` | no fleet; you read the diff yourself against both cluster sources |

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
- Marking a task completed without running the fleet over its diff.
- Taking the baseline by hand instead of through the scope-audit script.
- Trusting a summary line in place of the audit or the fleet that would check it.
