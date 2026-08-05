---
name: product-review
description: |
  Runs a critic-fleet review of one docs/product/ artifact, judged against the
  rubric its owning beat ships. Reports findings and never edits what it read.
argument-hint: "[product-artifact | slug]"
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

You orchestrate a critic fleet over one artifact of a `docs/product/<slug>/`
family — a member of its chain, or a folder a beat writes beside the members —
judged against the rubric shipped by the beat that owns it. You read and report;
you never edit what you read.

Two reference files govern this and neither is restated below. Read both now; do
not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md`
  owns every fleet mechanic: the triage gate, the fan-out, the dedup barrier,
  the adversarial verify stage, and the finding format.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  owns the family: which files are members, what order they come in, what else a
  beat writes into the folder, and which beat owns each of them.

Unlike the `/design-review` and `/tdd-review` siblings, this skill's cluster
source is not fixed. Resolving the target and selecting its rubric are one step,
and that step is where the care goes: an artifact judged against another beat's
rubric reads as a clean review, and nothing downstream would catch it.

## Step 1: Resolve the target from $ARGUMENTS

A target is one artifact the family contract publishes, from either of its two
tables. Both are reviewed identically; only their shape on disk differs, since a
member is one file and a non-member artifact is a folder of them.

- A path to a member file, such as `docs/product/<slug>/brief.md`: review that
  one member.
- A path to a non-member artifact's folder, `docs/product/<slug>/<artifact>/`:
  review it as a single target. The artifact is the whole set of files inside
  it, so one fleet judges them together — a critic handed one file of a set
  cannot see what the set is missing.
- A bare slug: review every artifact the folder holds, one fleet run each —
  members first in the chain order the `## Members` table gives, then the
  non-member artifacts in the order their table gives.
- Empty: ask with `AskUserQuestion` which slug or artifact to review. There is no
  useful default target, so do not guess one.

Enumerate a slug's members with `Glob` over `docs/product/<slug>/*.md`, then
intersect the result with the `Member` column of the artifact-family contract.
Intersecting is what leaves a stray `notes.md` unreviewed, and it needs no
filenames of its own.

Its non-member artifacts are not found by that glob — it matches files, and they
are folders. The `Folder` column names each one outright, so take the names from
it, look under `docs/product/<slug>/` for each, and keep those that exist and
hold at least one file. `Glob` goes inside such a folder only to collect the
files step 3 hands to the fleet.

Two empty results are different findings and are reported differently. A folder
that does not exist is a cold start: say so, and say that the slug may equally
be a typo, since slugs are matched here exactly as given and never normalised. A
folder that exists but holds nothing either column names is a project someone
has started and not yet written.

## Step 2: Select the rubric

Read the target's owning beat from the `Owning skill` column of the table that
publishes it — both of the artifact-family contract's tables carry that column,
and a target from either is selected the same way — then compose one path from
that beat name:

```
skills/<owning skill>/references/<owning skill>-principles.md
```

That composition is the entire mapping. Do not keep a second one keyed off the
target's filename, and do not invent a path for a beat neither table names.

A rubric that is absent, or that exposes no H3 cluster under its
`## Review-time red flags` heading, is unusable — a fleet pointed at it launches
no finder. Report that target as **unreviewable**, naming the artifact and the
exact path you expected, and carry on to the next target. Never substitute
another beat's rubric, never invent clusters of your own, and never let an
unreviewable target sit in the report looking like a clean one. The expected
path is the actionable part: it also names the beat someone would run to create
what is missing. Stop the whole invocation only when no target had a usable
rubric.

A beat that has not shipped its rubric yet is ordinary while the suite is still
being built, so this is a path to walk, not an error to stop on.

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

Pass the target as text. The critics read with Read, Grep and Glob and have no
Bash; a member is one small markdown file, and a folder artifact is every file
it holds, passed together as the one thing being judged.

## Step 4: Report

One findings block per target, in the order step 1 enumerated them, and
never merged. The target a finding came from is also the rubric it was judged
against, and a merged block loses both at once.

Within a block, report surviving findings grouped material-then-minor, each as
`[severity] {cluster}/{principle}: {finding} — evidence: {file:line}`. A target
whose fleet survived nothing says so explicitly and names the clusters checked;
a target reported unreviewable in step 2 keeps a block of its own and must not
be mistakable for that.

Close with a one-line verdict carrying both counts: findings, and targets that
could not be judged.

This skill only reports. It never edits what it read, never writes the rubric
that was missing, and offers fixes only if the user asks.

## Re-run behaviour

Every invocation re-reads the family, its artifacts and the rubrics from disk,
and writes nothing. Running this twice in a row is running it once.
