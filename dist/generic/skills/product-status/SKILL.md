---
name: product-status
description: |
  Reports the status of a docs/product/ slug: which chain artifacts exist,
  which have gone stale, and the one beat to run next.
argument-hint: "[slug]"
---

This build targets generic. Read <root>/HOST.md once before following any step below.

# product-status

You report where a `docs/product/<slug>/` chain stands and what to run next. You
read and report; you never write, never edit, and never delegate. The text given with the command
optionally names one slug.

The chain order, the member set, which beat owns each member, and the four state
names are all published in
`<root>/skills/product-artifacts/references/artifact-family.md`.
Read it now and take every one of them from there. This file restates none of
them, so anything it seems to say about the chain is an example, not a contract.

## Step 1: Ask the substrate once

The freshness computation already exists and already answers the whole question.
Run it exactly once:

```
python3 <root>/skills/product-artifacts/scripts/product_artifact.py \
  --check-freshness --product-dir docs/product [--slug <slug>]
```

Pass `--slug <slug>` only when the text given with the command names one; omit it otherwise. Read
the JSON it prints as text: `entries` holds one entry per slug, and each entry's
`members` map is already in chain order with one state per member. Derive no
state of your own from the files, and run no other flag of this script -- the
rest are not granted, and one of them writes.

## Step 2: Report the chain, then recommend once

For a named slug, emit one line per member in the order the output already
carries them, naming the member and its state, and then exactly one
recommendation. Nothing else: this skill's whole job is a report format.

Call out any member whose state is `unresolvable` prominently, above the
recommendation. It is the one finding a caller cannot act on by running a beat.

## The single recommendation

Walk the members in chain order and stop at the first one that is `absent` or
`stale`. Recommend that member's owning beat -- from the table's `Owning skill`
column -- as a run when the member is absent and as a re-run when it is stale.
Fix the earliest broken thing, so no beat is ever recommended on top of an
upstream you have just reported as out of date. If no member is `absent` or
`stale`, recommend `product-issues`.

An `unresolvable` member is skipped by this walk and never changes the answer: a
malformed provenance line is fixed by an edit, not by re-running the beat that
wrote it. Reporting it is enough.

The cold start needs no branch of its own. An empty or missing folder has
`brief.md` absent at position 1, so the walk already arrives at `product-brief`.

## With no slug

Emit one line per slug and no recommendation. Which project matters next is a
judgement the folder cannot supply, so do not dress a guess as an answer.

The one exception is zero slugs, where there is nothing to choose between:
report the cold start and recommend `product-brief`.

## When the named slug has no folder

Report the cold start, then list the slugs that do exist. A typo and a new
project look identical in the output, and the list makes a typo obvious without
guessing at near matches or asking the user anything.

## Re-run behaviour

Every invocation re-reads current state from disk and writes nothing -- no
member, no folder, no index. Running this twice in a row is running it once.
