---
name: product-roadmap
description: |
  Turns the requirements in docs/product/<slug>/spec.md into a roadmap at
  docs/product/<slug>/roadmap.md: every item RICE-scored, given a fixed
  appetite, and placed in a sequence that carries no dates. Refuses when no
  spec has been written.
argument-hint: "[slug]"
---

# /product-roadmap

You read a finished `docs/product/<slug>/spec.md` and write
`docs/product/<slug>/roadmap.md`, the last member of the chain. `product-spec`
is your input and the only member you derive from. The spec says what is being
built and what is not; it says nothing about what comes first, and supplying
that is the whole of what this beat adds.

The order it supplies is meant to be argued with. Every position rests on a
score whose inputs are visible one cell at a time, and every item carries a
fixed budget of time the work has to fit inside. What the member holds, section
by section and cell by cell, is the template's to state rather than this file's.

One fact shapes the rules below and is worth having before any of them. An
`ITEM` id is cited from outside this folder — issues filed elsewhere name one —
and no freshness check in this chain inspects a downstream identifier. Nothing
will ever tell you a number has moved, which is why `## Re-run behaviour` at the
bottom of this file is read before a second run touches an existing member
rather than after.

Three reference files govern this, and none of them is restated below. Read them
now; do not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/product-roadmap/references/rice-template.md`
  is the shape and the units: which sections `roadmap.md` carries, what belongs
  in every cell of its tables, what the four RICE inputs mean and what they are
  counted in, what an appetite is and what may never be done to one, and how an
  `ITEM` id is formed.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-roadmap/references/product-roadmap-principles.md`
  is the judgement. Its plan-time principles act while you write; its red-flag
  clusters are how a later review will read what you wrote.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  is the contract: the section names and their order, the provenance rules, and
  the unknown marker's exact literal.

What this beat adds to those three is two decisions and one discipline. The
decisions are which requirements group into an item and what order the items are
taken in; nothing upstream settles either, which is what makes them this beat's
to make. The discipline is that no number here is ever supplied by the run
itself. All three are worth stating because none of them is checkable
afterwards: an invented Reach and a counted one leave the same cell behind, and
a sequence somebody derived looks exactly like the table above sorted by score.

## Step 1: Refuse unless the spec conforms

`$ARGUMENTS` is the slug. If it is empty, ask for it with `AskUserQuestion`
before anything else — a slug names someone else's folder and cannot be guessed.

Ask the substrate whether the upstream is there:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --check-freshness --slug <slug> --product-dir docs/product
```

One call answers presence and provenance for the whole chain: read `spec.md`'s
state out of the entry's `members` map. Derive no state of your own from the
files. Do not stat the folder, do not read a provenance line yourself, and do
not compute a sha — a second reader of those bytes is a second answer that can
disagree with the one every other beat gets.

Read that entry for `spec.md` and stop there. The call reports every member, and
this beat gates on its **immediate upstream** alone: whether `discovery.md` has
moved under `requirements.md` is a state `product-spec` already decided to live
with, and a run that refuses over it re-opens a question two beats away from
anything it writes.

Never create the folder either. `--ensure-folder` is the only entry point in
this suite that writes anything outside a member, and this beat never reaches
for it: it refuses unless `spec.md` is already there, and a `spec.md` that
exists sits in a folder with an index row somebody else already made.

Then three refusals, in this order. Stop at the first one that fires, say which
of the three it was, and name `product-spec` as the beat to run:

1. **`spec.md` is absent.** Its state is `absent`, so there is nothing to put in
   an order: every item traces to requirements, and there are none.
2. **Its provenance is `unresolvable`.** What puts a member in that state is
   written in the artifact-family contract and nowhere else; read it there. What
   it means here is that nobody can say which `requirements.md` this spec was
   derived from. Ordering work off it anyway would put a sha over bytes of
   unknown ancestry into the member that decides what gets built first, and
   leave this member's provenance looking sound while the chain behind it is
   broken.
3. **No requirement carries a `REQ` id.** Read `spec.md`'s
   `## Requirements in scope` for ids of that form. With none there is nothing
   for an item's `Traces to` cell to name and nothing for the coverage table to
   have a row per, so every item you scored would be untraceable by
   construction.

`stale` is not one of the three. A `spec.md` whose own upstream has moved on is
still a spec, and refusing over it would have this beat re-decide something
`product-spec` owns. Report the state to the user, say a re-run of that beat
would settle it, and carry on.

The third refusal is the one no script can make for you. **Never invent a
requirement id**, do not number the rows yourself, and do not offer to order the
work from `requirements.md` or `brief.md` instead. Four beats stand between a
brief and this member precisely so that everything ranked here is work somebody
already committed to building.

## Step 2: Score every item, and score nothing you have to invent

Work from `spec.md` and nothing else. Settle three things before filling a cell:

- **Which requirements group into one item.** An item is a group of `REQ` ids
  that makes sense to build together, and the grouping is this beat's to decide
  rather than something the spec settles. Ask the user with `AskUserQuestion`
  where it is genuinely open.
- **The period every Reach is counted over**, and **the team size every appetite
  assumes**. Both are fixed here rather than per row, and both are written once
  above the table: a column whose cells quietly measure different windows cannot
  be read down, and no single row shows it.
- **Each item's appetite, decided before its effort is known.** That order is
  the whole of what makes it a budget rather than an estimate, and the template
  says what may follow when the two do not fit.

Then score every item, giving each of the four inputs a figure **and its basis**
in the same cell — the ticket count it was read off, the person who supplied it,
the comparable piece of work it was judged against.

**Never invent an input.** Where the basis does not exist, the cell carries the
suite's unknown marker in place of the figure; the literal and its payload rules
live under the `## Unknown marker` heading of the artifact-family contract cited
above, so copy them from there rather than reconstructing either. An item
carrying the marker in any of its four inputs **has no `Score`**, and that cell
carries the marker too — the template says what a score computed through a
number nobody has does to the table around it, and it is the passage to read
before deciding an input is close enough.

## Step 3: Derive the sequence, and record what beat the score

Three things come out of this step, and the template argues for each of them at
length. Read that argument before working the step rather than after, because
all three cost something now and pay later, and a run that has met only the
instruction takes the cheaper option every time.

- The order is **derived, not sorted** — not the scored table ranked by `Score`.
- Two things routinely **outrank** a score, dependencies and appetite windows,
  and each departure from score order says which of the two it was.
- The **rejected ordering** is recorded below the list: at least one sequence
  that was seriously considered, and what decided against it.

What this file adds is that the third is not optional. A sequence arrives
looking finished without it, and it is the one part of this member that cannot
be reconstructed later by anybody, including the person who wrote it.

An item with no `Score` cannot appear in the sequence at all, there being
nothing to have ranked it by. Its row stays where it is, marker and all.

## Step 4: Get the provenance line, then write

Read the finished provenance line off the substrate. It is one line, naming the
upstream member and the git blob hash of that member's bytes at the moment this
one is written:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --provenance-line --slug <slug> --member roadmap.md --product-dir docs/product
```

Write its `line` field into `roadmap.md` verbatim: do not assemble a line, and
do not compute a sha yourself. The `--member roadmap.md` argument is what makes
the line this member's own — it names the member being written, and the sha
comes back over that member's upstream. If the field is null, the upstream you
refused over in step 1 is still missing; go back rather than inventing a line.

Say in one line what `## Re-run behaviour` below states, then write the file:
the sections in the order the artifact-family contract publishes them, filled
per the template.

**Never write to `spec.md`.** Not to fix a requirement an item had to group
around, not to add a `REQ` id you wanted, not to reword one so an item traces to
it more neatly. The sha you have just written into `roadmap.md` is over
`spec.md`'s bytes, so editing the upstream would mark the member you are
finishing stale the moment you finished it, over an edit nobody asked for.
Anything the spec gets wrong is reported to the user as a `product-spec` re-run.

## Step 5: Report

Report the **path written**, how many items the member carries, how many of
those carry no score, and how many `REQ` ids no item covers.

The last two counts earn their line. A roadmap where a third of the items are
unscored rests on a third less evidence than the table appears to hold, and an
uncovered requirement is either a decision somebody made or work that fell out
of the roadmap unnoticed. Neither is visible in a report that counts only what
the member does hold.

Neither is a reason to refuse to write, and neither is closed by supplying the
missing thing yourself. An unscored item and an uncovered requirement are both
findings, and the cell that says so is the useful part.

Then state plainly what this document is not. It is not a plan and not a
schedule, and the second half of that is the one worth saying out loud: a reader
who takes an ordering for a delivery date will hold somebody to it, and this
member gives them nothing to hold. Every question of how a given item gets built
is `/deep-plan`'s, made with research this beat did not do.

## Re-run behaviour

A second run **revises `roadmap.md` in place**. Like `product-requirements`,
this beat does not overwrite its member, and the reason is the same one: the
ids.

- An item that survives the re-run **keeps the number** it already has, however
  much its wording, its inputs or its score changed.
- A new item takes the next number after the **highest ever used** in this file,
  retired numbers included. Never the count of live items: a retirement would
  then free a number for something else.
- An item the re-run drops is retired by **absence from `## Sequence`**, never
  by deletion. Its row stays in `## Scored items` and its id stays with the row.
- A re-scored item's **previous score is not** kept beside its current one. The
  member states one score per item, because two numbers in a row is two answers
  with no rule for choosing between them, and a reader takes whichever supports
  the position they already hold.

Why the rule exists, and not only what it says. An `ITEM` id is cited from
outside this folder — the issues filed against a roadmap item name it, and they
live where no freshness check reaches. The chain's mechanism compares an
upstream's content hash and never inspects a downstream identifier, so a
renumbering that tidies the table leaves every member reporting `fresh` while
every citation into it now points at different work. A review is the whole of
this rule's enforcement. Read it as bookkeeping you are free to tidy and the
breakage is silent, surfaces beats later, and looks like somebody else's
mistake.

Announce the revision in step 4 as a statement, not a confirmation prompt: do
not ask permission and do not offer to start the file again instead. The version
being revised is not recoverable, `docs/product/` being `gitignored`, so the
file you are reading is the only record of what its ids and its scores were.

Nothing else on disk changes. This beat creates no folder and refreshes no
index: it refuses unless `spec.md` exists, and a `spec.md` that exists is one
whose folder someone else already made.
