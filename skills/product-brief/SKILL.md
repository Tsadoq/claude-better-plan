---
name: product-brief
description: |
  Turns a raw product idea into a PR-FAQ brief at docs/product/<slug>/brief.md.
  Interviews you and researches in parallel, then marks every value nobody has
  established instead of inventing one.
argument-hint: "[raw product idea]"
---

# /product-brief

You turn a raw product idea into an Amazon-style PR-FAQ, written to
`docs/product/<slug>/brief.md`. That file heads the artifact chain every later
product beat reads, so what you write here is quoted downstream as established
fact rather than re-examined.

Three reference files govern this, and none of them is restated below. Read them
now; do not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/product-brief/references/pr-faq-template.md`
  is the shape: which sections a brief carries and what belongs in each.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-brief/references/product-brief-principles.md`
  is the judgement. Its plan-time principles act while you write; its red-flag
  clusters are how a later review will read what you wrote.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  is the contract: the section names and their order, the provenance rules, and
  the unknown marker's exact literal.

The failure this skill exists to prevent is fabrication. A PR-FAQ demands market
sizing, unit economics and customer quotes, and a model asked for that document
will produce plausible figures whether or not anyone has established them. A
marked gap is cheap; an invented number is cited by the next beat and never
questioned again.

## Step 1: Resolve the slug and ensure the folder

`$ARGUMENTS` is the raw idea. If it is empty, ask for it with `AskUserQuestion`
before anything else — there is no useful default idea.

Propose a short slug from the idea and run:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --ensure-folder --slug <slug> --product-dir docs/product
```

It prints `{slug, path, created, index}`. Use the `slug` and `path` it returns,
not the ones you proposed: it normalises the slug and regenerates the product
index in the same call. Never create the folder yourself and never normalise a
slug yourself — a locally created folder is a folder with no index row, which is
a state `--ensure-folder` exists to make unreachable.

If `created` is false the folder already exists; that is not an error, and how a
second run behaves is settled in step 4.

## Step 2: Launch the research sweep and open the interview in the same turn

Make both calls in **one** turn, research first:

1. `Agent` with `subagent_type: deep-plan:dp-research-shallow`, sweeping from the
   raw idea: who serves this customer today and at what price, which manual
   workarounds people use instead, and any published sizing for the space. Ask
   for a source URL per claim, and treat a claim that arrives without one as not
   researched.
2. `AskUserQuestion`, opening the interview.

The `Agent` call returns once the agent is launched, not once it finishes, and
that agent keeps working while `AskUserQuestion` blocks the turn. The
concurrency is the point: the sweep's latency hides behind the user's answers.
Sequencing them instead doubles the wall clock and buys nothing.

Sweep from the raw idea rather than from whatever the interview leaves blank.
The rubric's workaround cluster catches briefs asserting that nothing like this
exists today, and that claim is most often wrong exactly when it is stated
confidently — so it gets checked whether or not the user sounded sure.

The interview asks only what no public source can answer: who the customer is
and what they do about this today, what the problem costs them, what the pricing
intent is, what has to be true for this to work, and when it could be available.
`AskUserQuestion` takes at most four questions per call — a structural limit, not
a style preference, so more questions simply mean another call. Never ask the
user to supply a quote; see step 3.

## Step 3: Merge under the provenance taxonomy

Three ways to fill a slot, and only three:

- **Supplied** — the user stated it. Write it plainly.
- **Researched** — a public source states it. Write it with an inline citation to
  that source, so a reader can check it rather than trust you.
- **Unknown** — nobody has established it. Write the unknown marker, which opens
  `[UNKNOWN:`. Copy the literal and its payload from the `## Unknown marker`
  heading of the artifact-family contract cited above rather than reconstructing
  either from memory; that file is where both are defined.

Two carve-outs the taxonomy alone would get wrong. The template states each at
the slot it applies to; they are repeated here because the merge is the moment
the taxonomy above would otherwise decide them, and it decides both wrongly:

- **Market sizing** is written with its citation *and* still flagged for an
  internal bottom-up number. An analyst's total is not this company's number, and
  the citation lends it precisely the authority that makes it dangerous
  downstream.
- **Quotes are never researched.** The spokesperson and customer quotes are
  authored for the brief and labelled as authored. Do not hunt for a real
  testimonial, do not put words in a named real person's mouth, and do not ask
  the user to produce one.

**If the sweep has not returned when the interview closes, write the brief
anyway** with those slots marked. Do not stall the turn waiting for it: a
background agent's cleanup and resumption cannot be assumed, so waiting risks
hanging on something that will never arrive. Late findings get in through a
re-run, which is cheap by construction.

## Step 4: Announce, then write

If `brief.md` already exists, say in one line that this run replaces brief.md in
place and that the previous version is not recoverable, `docs/product/` being
gitignored. That is an announcement, not a confirmation prompt: do not ask
permission, do not offer to merge, and do not fall back to filling in only the
marked slots. Every invocation runs the whole beat and produces the whole
artifact.

Then write the file: the sections in the order the artifact-family contract
publishes them, filled per the template.

`brief.md` carries no provenance line. It heads the chain and has no upstream to
derive from, so the line every later member records — whose format the
artifact-family contract owns — would have nothing to record here.

## Step 5: Report

Report the path written and how many markers the brief carries.

A marker count is not a failure and never a reason to refuse to write. A brief
that marks twelve unknowns has done its job; a brief with none, written from an
idea nobody has researched, is the one that should worry a reader. Do not offer
to fill markers by estimating — name who could close each one instead, which the
marker's own payload already records.
