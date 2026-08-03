---
name: product-discovery
description: |
  Turns a written brief into product discovery at docs/product/<slug>/discovery.md:
  an opportunity solution tree, an assumption map, and the riskiest-assumption
  tests worth running first. Refuses when no brief has been written.
argument-hint: "[slug]"
---

# /product-discovery

You read a finished `docs/product/<slug>/brief.md` and write
`docs/product/<slug>/discovery.md`. The brief argues that a product is worth
building; your job is to take that argument apart into claims someone could
actually settle, and to say which of them is worth settling first. What the
resulting document holds, section by section and field by field, is the
template's to state rather than this file's.

Three reference files govern this, and none of them is restated below. Read them
now; do not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/product-discovery/references/opportunity-solution-tree-template.md`
  is the shape: which sections `discovery.md` carries, which columns each table
  declares, how an id is formed, and what belongs in every field.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-discovery/references/product-discovery-principles.md`
  is the judgement. Its plan-time principles act while you write; its red-flag
  clusters are how a later review will read what you wrote.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  is the contract: the section names and their order, the provenance rules, and
  the unknown marker's exact literal.

Two failures this beat exists to prevent, and they are not the same failure. The
first is a tree with an invented root: an outcome reconstructed from the slug or
from what the team already wants to build makes every layer beneath it a
justification rather than a discovery. The second is an invented figure. This is
where market sizing finally gets produced, one beat after the brief marked it
unknown, and a model asked for TAM, SAM and SOM will produce plausible numbers
whether or not anyone established them. The next beat cites what it finds here
rather than re-examining it, so a number invented now becomes a requirement
later.

## Step 1: Refuse unless the brief conforms

`$ARGUMENTS` is the slug. If it is empty, ask for it with `AskUserQuestion`
before anything else — a slug names someone else's folder and cannot be guessed.

Ask the substrate whether the upstream is there:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --check-freshness --slug <slug> --product-dir docs/product
```

One call answers presence for the whole chain: read `brief.md`'s state out of the
entry's `members` map. Derive no state of your own from the files.

Then three refusals, in this order. Stop at the first one that fires, say which
of the three it was, and name `product-brief` as the beat to run:

1. **`brief.md` is absent.** Its state is `absent`, so there is no upstream to
   derive from. Run `product-brief` for this slug first.
2. **`brief.md` is missing one of its required sections.** Read its H2 headings
   against the list the artifact-family contract publishes for `brief.md`, taken
   from that file rather than from memory. A brief missing a section is a brief
   whose owning beat did not finish.
3. **No outcome can be read out of its press release.** The press release has to
   state a business result this discovery could be in service of. If it names
   only a feature, an audience or an intention, refuse.

The third refusal is the one that matters most and the only one no script can
make for you. **Never infer an outcome from the slug**, from the folder's other
members, or from what the solutions in the brief imply someone wants — a tree
with an invented root is the failure this beat exists to prevent, and a brief
carrying all three headings and no statable outcome passes the two mechanical
checks above. Refusing is the correct outcome of this step, not a failure of it:
do not offer to proceed with a placeholder, and do not write the file with the
unknown marker standing in for the root.

## Step 2: Launch the sizing sweep and open the interview in the same turn

Make both calls in **one** turn, research first:

1. `Agent` with `subagent_type: deep-plan:dp-research-shallow`, sweeping for
   market sizing only: published totals for the space, the segment that is
   actually serviceable, and what comparable companies have won of it. Ask for a
   source URL per figure, and treat a figure that arrives without one as not
   researched.
2. `AskUserQuestion`, opening the evidence interview.

The `Agent` call returns once the agent is launched, not once it finishes, and
that agent keeps working while `AskUserQuestion` blocks the turn. The concurrency
is the point: the sweep's latency hides behind the user's answers. Sequencing
them instead doubles the wall clock and buys nothing.

Sizing is the only thing that gets swept. A public source can answer how big a
market is; it cannot answer what a customer of yours is struggling with, and
web-sourced evidence for a customer need is the weakest kind there is.

The interview is narrow and asks only for evidence the user **already holds**:
support tickets, analytics figures, interviews already run, complaints already
heard, and who set the outcome. Harvesting what someone already knows is not
conducting discovery on their behalf — this skill produces the interview
structure and the ordered tests, and runs neither. `AskUserQuestion` takes at
most four questions per call, a structural limit rather than a style preference,
so more questions simply mean another call.

## Step 3: Build the tree, the map and the ordered tests

Work from `brief.md` plus what the interview returned, and nothing else.

- **Never invent an opportunity.** Every row is something the brief states or the
  user reported. An opportunity nobody has evidence for is a hypothesis about a
  customer, which the tree has no layer for.
- **Never leave an evidence cell blank.** Where nothing was observed, write the
  unknown marker, which opens `[UNKNOWN:`. Copy the literal and its payload rules
  from the `## Unknown marker` heading of the artifact-family contract cited
  above rather than reconstructing either from memory. A blank cell reads as
  evidence nobody bothered to write down; the marker reads as a routed question.
- **If the sweep has not returned when the interview closes, write the file
  anyway** with the sizing slots marked. Do not stall the turn waiting for it: a
  background agent's cleanup and resumption cannot be assumed, so waiting risks
  hanging on something that will never arrive. Late figures get in through a
  re-run, which is cheap by construction.

The template owns the rest — the connection rules, the id notation, the fields
each table declares, the derivation the ordered test list falls out of. Follow it
rather than this file on any of them.

## Step 4: Get the provenance line, then write

Read the finished provenance line off the substrate; do not assemble it, and do
not compute a sha yourself:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --provenance-line --slug <slug> --member discovery.md --product-dir docs/product
```

Write its `line` field into `discovery.md` verbatim. If the field is null, the
upstream you refused over in step 1 is still missing — go back rather than
inventing a line.

Say in one line what `## Re-run behaviour` below states, then write the file:
the sections in the order the artifact-family contract publishes them, filled per
the template.

**Never write to `brief.md`.** Not to fix a section, not to record what the
interview turned up, not to tidy a figure. Editing the upstream changes its
bytes, and the sha you have just written into `discovery.md` is over those bytes:
the edit would mark the file you are writing stale the moment you finish it.
Anything the brief gets wrong is reported to the user as a `product-brief` re-run.

## Step 5: Report

Report the path written and how many markers `discovery.md` carries.

Then state plainly what the ranking is not. The quadrant ranks assumptions by
**testing urgency** — the order in which uncertainty gets cheapest to remove. It
is not a delivery priority, a backlog or a roadmap, and reading it as one inverts
the point: testing the riskiest thing first is how you find out cheaply whether
the rest is worth planning at all.

A marker count is not a failure and never a reason to refuse to write. A
`discovery.md` that marks eight unknowns has done its job; one with none, written
from a brief nobody researched, is the one that should worry a reader. Do not
offer to fill markers by estimating — name who could close each one instead,
which the marker's own payload already records.

## Re-run behaviour

A second run replaces `discovery.md` in place, and the previous version is not
recoverable, `docs/product/` being gitignored. Announce that in step 4 as a
statement, not a confirmation prompt: do not ask permission, do not offer to
merge, and do not fall back to filling in only the slots the last run marked.
Every invocation runs the whole beat and produces the whole artifact.

Nothing else on disk changes. This beat creates no folder and refreshes no index:
it refuses unless `brief.md` exists, and a `brief.md` that exists is one whose
folder someone else already made.
