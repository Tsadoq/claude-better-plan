# Host conventions (generic build)

This build of the deep-plan plugin targets any agent that can read files, write
files, and run shell commands. The skills were written for Claude Code; where
they relied on a Claude-only tool, the text now uses one of the phrases below.
Each phrase means exactly what this file says, every time it appears.

## Paths and ids

- `<root>` is the plugin root: the folder holding `skills/`, `agents/`, and
  this file, two levels above the folder of the skill you are running. Write it
  as that absolute path whenever you run a command or read a file under it.
- `<session-id>` is an id for this run. Generate one UUID the first time a step
  needs it and reuse that same value for the rest of the run.

## an ask

Whenever a step says to ask the user (an ask), put the question to them this way:

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

`dp-X` names an agent file at `<root>/agents/dp-X.md`. To launch it:

- If you can spawn subagents, give one the body of that file (everything after
  its frontmatter) as its instructions, followed by the task the step gives it.
  Keep any read-only rule the file states: only `dp-implement-task` may write.
  Several launches named together run in parallel when your agent allows it.
- Otherwise do the work inline yourself, one agent's job at a time: read the
  file, follow it for that one task, finish its output, then start the next.

Either way, the step continues with the agent's returned output as its result.

## Other phrases

- "the text given with the command" is whatever the user typed after naming
  the skill; it may be empty.
- "the X skill" means the skill in `<root>/skills/X/`; when a step says to run
  it, the user starts it the way your agent starts skills.
- "web search" and "web fetch" mean your agent's tools for searching the web and
  reading a URL, if it has them. Without them, say so once and work from what
  you can read locally.
- Nothing here runs at session end, so stale sandboxes under `/tmp/deep-plan-*`
  are swept by
  `python3 <root>/skills/deep-plan/hooks/cleanup.py < /dev/null`, run by hand.
