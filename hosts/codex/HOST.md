# Host conventions (Codex build)

This build of the deep-plan plugin targets Codex. The skills were written for
Claude Code; where they relied on a Claude-only tool, the text now uses one of
the phrases below. Each phrase means exactly what this file says, every time it
appears.

## Mode

Run these skills in Codex's Default collaboration mode. Plan mode forbids
writing files, and the skills write their plan folder from the first decision
on, so a Plan-mode run cannot keep its record.

## Paths and ids

- `<root>` is the plugin root: the folder holding `skills/`, `agents/`, and
  this file, two levels above the folder of the skill you are running. Write it
  as that absolute path whenever you run a command or read a file under it.
- `<session-id>` is an id for this run. Generate one UUID the first time a step
  needs it and reuse that same value for the rest of the run.

## an ask

Whenever a step says to ask the user (an ask), put the question to them this way.

If `request_user_input` is available, call it. It takes at most 3 questions,
each with 2 to 3 options, and adds a free-form "Other" itself. Put the
recommended option first, its label ending in "(Recommended)", then the next
two; any option beyond those stays reachable through "Other", so name the ones
you dropped in the question text.

Otherwise (Default mode usually does not offer it):

1. Write the question, then numbered options, the recommended one first and
   marked "(Recommended)", then a last line "Other: type it".
2. Make the ask the last thing in your message, then end your turn. Never ask
   and keep working in the same turn.
3. Treat the user's next reply as the answer: a number picks that option, any
   other text is the "Other" answer.

Only an explicit pick of an approve option approves. A reply that does not pick
it (a comment, a question, "looks fine but...") is not approval: address it and
ask again. Never ask for approval in passing ("looks good?") mid-message.

## launch dp-X

`dp-X` names an agent file at `<root>/agents/dp-X.md`. To launch it, call
`spawn_agent` with a `message` holding the body of that file (everything after
its frontmatter), then the task the step gives it. Codex agents cannot be
limited to some tools, so the message itself carries any read-only rule the
file states: only `dp-implement-task` may write, and every other agent's message
ends with "Do not edit, write, or delete any file."

Several launches named together are one `spawn_agent` call each, all made before
you wait; then call `wait_agent` until every one has reached a final status.
Call `close_agent` on each agent once you have its output. The step continues
with each agent's final message as its result.

## Other phrases

- "the text given with the command" is whatever the user typed after the
  skill's name; it may be empty.
- `$<skill>` names the skill in `<root>/skills/<skill>/`; the user starts it by
  typing `$<skill>`.
- Task tracking is the markdown checklist `$deep-plan-execute` keeps in the plan
  file, not a Codex tool.
- "web search" and "web fetch" mean your tools for searching the web and
  reading a URL, if you have them. Without them, say so once and work from what
  you can read locally.
- Codex runs nothing at session end, so stale sandboxes under
  `/tmp/deep-plan-*` are swept by the next pi or Claude Code session, or by hand
  with `python3 <root>/skills/deep-plan/hooks/cleanup.py < /dev/null`.
