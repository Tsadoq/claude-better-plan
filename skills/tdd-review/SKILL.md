---
name: tdd-review
description: |
  Standalone review of the Tests (TDD) blocks in a plan produced by
  /deep-plan, run by a parallel critic fleet: one small-model test critic
  per red-flag cluster (assertions and failure output, test doubles and
  seams, fixtures and setup, test level and duplication), then adversarial
  verification. Use when the user asks to review planned tests, check TDD
  quality, or assess assertions, doubles, fixtures, or flaky-test craft in
  a deep-plan plan file. Not for reviewing diffs, pull requests, or
  already-implemented code.
argument-hint: "[plan-file]"
---

# /tdd-review

You orchestrate a test-critic fleet over a plan's `**Tests (TDD)**` blocks.
All guideline content lives in
`${CLAUDE_PLUGIN_ROOT}/skills/tdd-review/references/test-principles.md`
and all fleet mechanics live in
`${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`.
Read both now; do not restate their content from memory.

## Step 1: Resolve the plan file from $ARGUMENTS

- A path to a plan.md file: use it directly.
- A plan folder: use its `plan.md` member.
- Empty: ask the user via AskUserQuestion which plan file to review rather
  than guessing.

The review target is the plan's per-task `**Tests (TDD)**` blocks, passed
as text excerpts (the critics read files with Read/Grep/Glob — they have
no Bash).

## Step 2: Run the critic fleet

Run the fleet exactly as specified in
`references/fleet-orchestration.md` (under the design-review skill) with
`agentType: deep-plan:dp-test-critic`: one finder per H3 cluster under
`## Review-time red flags` in `references/test-principles.md` (quote each
cluster's questions verbatim into its finder prompt), dedup, then the
adversarial verify stage. Use the Workflow path when available; on absence,
denial, or error, switch to the fallback without asking.

## Step 3: Report

Report surviving findings grouped material-then-minor, each as
`[severity] {cluster}/{principle}: {finding} -- evidence: {task/field}`,
followed by a one-line verdict (`N material, M minor`). If nothing
survives verification, say so explicitly and name the clusters checked.
This skill only reports; it never edits the target. Offer fixes only if
the user asks.
