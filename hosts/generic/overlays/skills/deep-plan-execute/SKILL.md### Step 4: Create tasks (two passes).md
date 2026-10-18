## Step 4: Track tasks in a checklist

Append a `## Progress` section to the end of the plan's `plan.md` holding one
line per parsed task, in plan order:

```
- [ ] Task {n}: {subject} (after: {depends_on, comma-separated, or "none"})
```

That checklist is the task graph. A task may be dispatched only once every task
in its `after:` list is checked; picking the next one is your job, so re-read the
checklist before each dispatch rather than trusting memory. In progress means
` (in progress)` appended to the line; completed means `[x]`; blocked means
` (blocked: <reason>)` appended. If a `depends_on` integer names no parsed task
(dangling reference), drop it from `after:` and warn the user rather than
failing. Each task's acceptance criteria are its `change` text, `target_files`,
`tests` block (if present), and `verification` command, as `load_tasks.py`
returns them.
