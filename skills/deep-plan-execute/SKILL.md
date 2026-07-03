---
name: deep-plan-execute
description: |
  Executes a finalized /deep-plan plan file. Parses the plan's ## Tasks into
  harness tasks (one TaskCreate each), wires Depends on into addBlockedBy, then
  drives a test-first implementation loop task by task in dependency order.
  Invoke after a /deep-plan plan is approved and you are ready to build it, e.g.
  "implement the plan" or "/deep-plan:deep-plan-execute <plan-file>".
argument-hint: "[plan-file-path]"
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

1. If `$ARGUMENTS` names a path, use it as the plan file.
2. Otherwise, find the project's `plans_dir` and use the most recently modified
   plan there:

   ```
   ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
   PROJECTS="${XDG_STATE_HOME:-$HOME/.local/state}/deep-plan/projects.json"
   PLANS_DIR="$(python3 -c "import json,sys; d=json.load(open('$PROJECTS')); print(d.get('$ROOT',{}).get('plans_dir',''))" 2>/dev/null)"
   # pick newest *.md that is not a .probes.md / .research.md sibling
   ls -t "$PLANS_DIR"/*.md 2>/dev/null | grep -vE '\.(probes|research)\.md$' | head -1
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
   `tests` FIRST. Run the `verification` command and confirm it FAILS (red). If
   it passes before you have written any implementation, the test is wrong or
   the behaviour already exists -- stop and tell the user.
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
   (one `dp-design-critic` per red-flag cluster, then the verify stage).
   Fix `material` findings within the task and re-run the `verification`
   command before completing; log `minor` findings in the task completion
   note without blocking.
5. On green, mark the task `completed` via `TaskUpdate`. On red you cannot fix
   within the task's scope, stop and report rather than expanding scope.

Run verification commands exactly as written in the plan. If a command assumes
`uv run` but the project has no `pyproject.toml`, fall back to `python3` and note
the substitution.

## Anti-patterns

- Creating all tasks then implementing out of dependency order.
- Skipping the failing-test-first step for a code task.
- Editing files a task does not list under `Target files`.
- Proceeding past a non-empty `## Open questions`.
- Re-opening a decision already settled in `## Decisions made` without asking.
- Batching unrelated tasks into one `TaskCreate`.
- Marking a task completed with unresolved material design findings.
