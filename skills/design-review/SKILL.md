---
name: design-review
description: |
  Standalone design review of code, diffs, or plan files by a parallel
  critic fleet: one small-model critic per red-flag cluster (module depth,
  information hiding, naming, comments), then adversarial verification.
  Use when the user asks to "design-review" something, review design
  quality, check for shallow modules or information leakage, or audit a
  diff or plan against design principles.
argument-hint: "[path | git ref | plan-file]"
---

# /design-review

You orchestrate a design-critic fleet over a review target. All guideline
content lives in `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/design-principles.md`
and all fleet mechanics live in
`${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`.
Read both now; do not restate their content from memory.

## Step 1: Resolve the review target from $ARGUMENTS

- Empty: the working diff (`git diff HEAD` plus untracked files of interest).
  If the working tree is clean, ask the user what to review instead of
  reviewing nothing.
- A path to a file or directory: those files.
- A git ref or ref range (e.g. `HEAD~3`, `main..feature`): that diff.
- A plan file (markdown with `## Tasks`): the plan body, reviewed as a
  design artifact (its module boundaries and interfaces), not as prose.

Collect the target as text where it is a diff or plan excerpt; pass file
paths where it is files (the critics read them with Read/Grep/Glob — they
have no Bash).

## Step 2: Run the critic fleet

Run the fleet exactly as specified in
`references/fleet-orchestration.md`: one finder per H3 cluster under
`## Review-time red flags` in `references/design-principles.md` (quote each
cluster's questions verbatim into its finder prompt), dedup, then the
adversarial verify stage. Use the Workflow path when available; on absence,
denial, or error, switch to the fallback without asking.

## Step 3: Report

Report surviving findings grouped material-then-minor, each as
`[severity] {cluster}/{principle}: {finding} -- evidence: {file:line}`,
followed by a one-line verdict (`N material, M minor`). If nothing
survives verification, say so explicitly and name the clusters checked.
This skill only reports; it never edits the target. Offer fixes only if
the user asks.
