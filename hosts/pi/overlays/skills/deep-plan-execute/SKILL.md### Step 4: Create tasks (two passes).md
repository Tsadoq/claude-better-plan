## Step 4: Create tasks (two passes)

Track the parsed `tasks` with the `todo` tool, in plan order, so pi's task list
is the task graph. A task's `blockedBy` may name only tasks that already exist,
so use two passes:

**Pass 1 -- create.** For each task, create one `todo` task:

- subject: `Task {n}: {subject}`
- description: the `change` text, followed by the `target_files` list, the
  `tests` block (if present), and the `verification` command. This is the
  task's acceptance criteria.
- `blockedBy`: the ids of the already-created tasks among its `depends_on`.

Capture each returned id into an `int -> id` map keyed by the task's `n`. Do NOT
assume ids are sequential or numeric.

**Pass 2 -- wire the rest.** For each task with a `depends_on` entry that was not
yet created when it was, update it with `addBlockedBy` set to those ids. If a
`depends_on` integer has no entry in the map (dangling reference), skip it and
warn the user rather than failing.
