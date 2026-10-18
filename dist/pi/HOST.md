# Host conventions (pi build)

This build of the deep-plan plugin targets pi. The skills were written for
Claude Code; where they relied on a Claude-only tool, the text now names the pi
tool this package installs, or one of the phrases below. Each phrase means
exactly what this file says, every time it appears.

## Paths and ids

- `<root>` is the plugin root: the folder holding `skills/`, `agents/`,
  `extensions/`, and this file, two levels above the folder of the skill you
  are running. Write it as that absolute path whenever you run a command or read
  a file under it.
- `<session-id>` is an id for this run. Generate one UUID the first time a step
  needs it and reuse that same value for the rest of the run.

## Asking the user

A `questionnaire` call asks the user and waits for their pick. Give each
question its options, the recommended one first and its label ending in
"(Recommended)"; leave `allowOther` on so the user can type an answer instead.
Option labels must be unique within a question.

Only an explicit pick of an approve option approves. An "Other" answer that does
not pick it (a comment, a question, "looks fine but...") is not approval:
address it and ask again. Never ask for approval in passing ("looks good?") in
plain text.

## Launching agents

`dp-X` names an agent this package ships in `<root>/agents/dp-X.md`; the
`subagent` tool finds it by that name. "Launch dp-X" (or "launch dp-X once")
means one `subagent` call with `agent: "dp-X"` and the step's text as `task`.
Several launches named together go in one call as `tasks: [{agent, task}, ...]`,
which runs them in parallel. Each agent keeps only the tools its file lists; only
`dp-implement-task` may write. The step continues with the returned output.

## Other phrases

- "the text after the /skill command" is whatever the user typed after
  `/skill:<name>`; it may be empty.
- `/skill:<name>` starts the skill in `<root>/skills/<name>/`.
- `todo` is the task-list tool; its tasks carry `blockedBy` dependencies.
- `web_search` and `web_fetch` search the web and read a URL.
- At session end this package runs
  `python3 <root>/skills/deep-plan/hooks/cleanup.py` with no session id, which
  sweeps sandboxes under `/tmp/deep-plan-*` older than its retention window.
