---
name: product-review
description: |
  Runs a critic-fleet review of one docs/product/ chain member, judged against
  the rubric its owning beat ships. Reports findings and never edits the member
  it read.
argument-hint: "[product-member | slug]"
# `Bash` is denied rather than scoped, and no `allowed-tools` key is declared.
# `allowed-tools` is turn-scoped pre-approval and restricts nothing -- every tool
# stays callable whether or not it is listed -- so `disallowed-tools` is the only
# field here that enforces anything. With `Bash` gone this skill holds no tool
# that can write, which is what makes "never edits the member it reviews" a
# property of the tool set rather than a promise in prose; every chain member
# after the first records a hash of its upstream, so an edit by the reviewer
# would manufacture the staleness it was never asked to judge. The price is the
# substrate script: a denied shell cannot run one, which is why step 1 enumerates
# a slug with `Glob` instead of calling `product_artifact.py`.
disallowed-tools: Write, Edit, NotebookEdit, Bash
---

# /product-review

You orchestrate a critic fleet over a member of a `docs/product/<slug>/` chain,
judged against the rubric shipped by the beat that owns that member. You read
and report; you never edit what you read.

Two reference files govern this and neither is restated below. Read both now; do
not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`
  owns every fleet mechanic: the triage gate, the fan-out, the dedup barrier,
  the adversarial verify stage, and the finding format.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  owns the chain: which files are members, what order they come in, and which
  beat owns each one.

Unlike the `/design-review` and `/tdd-review` siblings, this skill's cluster
source is not fixed. Resolving the target and selecting its rubric are one step,
and that step is where the care goes: a member judged against another member's
rubric reads as a clean review, and nothing downstream would catch it.

## Step 1: Resolve the target from $ARGUMENTS

- A path to a member file, such as `docs/product/<slug>/brief.md`: review that
  one member.
- A bare slug: review every member the folder holds, one fleet run each, in the
  chain order the `## Members` table gives.
- Empty: ask with `AskUserQuestion` which slug or member to review. There is no
  useful default target, so do not guess one.

Enumerate a slug with `Glob` over `docs/product/<slug>/*.md`, then intersect the
result with the `Member` column of the artifact-family contract. Intersecting is
what leaves a stray `notes.md` unreviewed, and it needs no filenames of its own.

Two empty results are different findings and are reported differently. A folder
that does not exist is a cold start: say so, and say that the slug may equally
be a typo, since slugs are matched here exactly as given and never normalised. A
folder that exists but holds no member is a project someone has started and not
yet written.

## Step 2: Select the rubric

Read the target member's owning beat from the `Owning skill` column of the
artifact-family contract, then compose one path from that beat name:

```
skills/<owning skill>/references/<owning skill>-principles.md
```

That composition is the entire mapping. Do not keep a second one keyed off the
member's filename, and do not invent a path for a beat the table does not name.

A rubric that is absent, or that exposes no H3 cluster under its
`## Review-time red flags` heading, is unusable — a fleet pointed at it launches
no finder. Report that member as **unreviewable**, naming the member and the
exact path you expected, and carry on to the next target. Never substitute
another member's rubric, never invent clusters of your own, and never let an
unreviewable member sit in the report looking like a clean one. The expected
path is the actionable part: it also names the beat someone would run to create
what is missing. Stop the whole invocation only when no target had a usable
rubric.

Most members have no rubric yet — the suite is still being built — so this is a
main path, not an edge case.

## Step 3: Run the fleet, once per target

Run the fleet exactly as specified in `references/fleet-orchestration.md` (under
the design-review skill) with `agentType: deep-plan:dp-critic` and the rubric
selected in step 2 as the cluster source: one finder per H3 cluster under
`## Review-time red flags` in that file (quote each cluster's questions verbatim
into its finder prompt, and name the file itself — that path is the only thing
that points an otherwise generic critic at product judgement), dedup, then the
adversarial verify stage.

Use the Workflow path when available; on absence, denial, or error, switch to
the fallback without asking. This skill runs from the main thread, so the
recipe's `## Nested fleets` obligations do not apply to it.

Pass the member as text. The critics read with Read, Grep and Glob and have no
Bash, and a member is one small markdown file.

## Step 4: Report

One findings block per member, in chain order, never merged. The member a
finding came from is also the rubric it was judged against, and a merged block
loses both at once.

Within a block, report surviving findings grouped material-then-minor, each as
`[severity] {cluster}/{principle}: {finding} — evidence: {file:line}`. A member
whose fleet survived nothing says so explicitly and names the clusters checked;
a member reported unreviewable in step 2 keeps a block of its own and must not
be mistakable for that.

Close with a one-line verdict carrying both counts: findings, and members that
could not be judged.

This skill only reports. It never edits the member, never writes the rubric that
was missing, and offers fixes only if the user asks.

## Re-run behaviour

Every invocation re-reads the chain, the members and the rubrics from disk, and
writes nothing. Running this twice in a row is running it once.
