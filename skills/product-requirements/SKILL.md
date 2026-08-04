---
name: product-requirements
description: |
  Turns a written discovery into testable requirements at
  docs/product/<slug>/requirements.md: one EARS sentence per thing that must be
  true, functional and non-functional, each traced to the opportunity it answers.
  Refuses when no discovery has been written.
argument-hint: "[slug]"
---

# /product-requirements

You read a finished `docs/product/<slug>/discovery.md` and write
`docs/product/<slug>/requirements.md`. Discovery argues which customer
opportunities are worth answering; your job is to restate those answers as
sentences somebody could write a test against. This is the beat where the
chain's ambiguity gets spent. Everything upstream of you is deliberately prose,
and neither a narrative brief nor a ranked bet is falsifiable one sentence at a
time. What the resulting document holds, section by section and field by field,
is the template's to state rather than this file's.

Three reference files govern this, and none of them is restated below. Read them
now; do not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/requirements-template.md`
  is the shape and the grammar: which sections `requirements.md` carries and what
  belongs in every field, the EARS notation every requirement is written in, the
  casing it mandates, the quality characteristic checklist, the INVEST gate, and
  how a `REQ` id is formed.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/product-requirements-principles.md`
  is the judgement. Its plan-time principles act while you write; its red-flag
  clusters are how a later review will read what you wrote.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  is the contract: the section names and their order, the provenance rules, and
  the unknown marker's exact literal.

Two failures this beat exists to prevent, and they are not the same failure. The
first is a requirement that answers no opportunity. Every row here is downstream
of something a customer was observed struggling with, so a requirement traceable
to no `OPP` id is scope somebody added without deciding to — and it will be built,
because by the next beat it is indistinguishable from the ones discovery earned.
The second is a requirement nobody could fail. A sentence that reads like a
constraint and admits no test is worse than a missing requirement: the missing one
is visible in the coverage table, and the untestable one occupies the row that
would have shown it missing.

## Step 1: Refuse unless discovery conforms

`$ARGUMENTS` is the slug. If it is empty, ask for it with `AskUserQuestion`
before anything else — a slug names someone else's folder and cannot be guessed.

Ask the substrate whether the upstream is there:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --check-freshness --slug <slug> --product-dir docs/product
```

One call answers presence and provenance for the whole chain: read
`discovery.md`'s state out of the entry's `members` map. Derive no state of your
own from the files. Do not stat the folder, do not read a provenance line
yourself, and do not compute a sha — a second reader of those bytes is a second
answer that can disagree with the one every other beat gets.

Never create the folder either. `--ensure-folder` is the only entry point in this
suite that writes anything outside a member, and this beat never reaches for it:
it refuses unless `discovery.md` is already there, and a `discovery.md` that
exists sits in a folder with an index row somebody else already made.

Then three refusals, in this order. Stop at the first one that fires, say which of
the three it was, and name `product-discovery` as the beat to run:

1. **`discovery.md` is absent.** Its state is `absent`, so there is no upstream to
   derive from at all. Run `product-discovery` for this slug first.
2. **Its provenance is `unresolvable`.** The line is missing, malformed, or names
   an upstream that does not exist, so nobody can say which `brief.md` this
   discovery was derived from. Deriving from it anyway would put a sha over bytes
   of unknown ancestry into `requirements.md` and make this member's provenance
   look sound while the chain behind it is broken.
3. **No opportunity node carries an `OPP` id.** Read the tree in `discovery.md`
   for ids of that form. With none, there is nothing for a requirement's `Traces
   to` cell to name and nothing for the coverage table to have a row per, so every
   requirement you wrote would be untraceable by construction.

`stale` is not one of the three. A `discovery.md` whose own brief has moved on is
still a discovery, and refusing over it would have this beat re-decide something
`product-discovery` owns. Report the state to the user, say a re-run of that beat
would settle it, and carry on.

The third refusal is the one no script can make for you, and the one worth
refusing over. **Never invent an opportunity id**, do not renumber the tree to
produce one, and do not write the member with the coverage table left out. Do not
offer to proceed from the brief instead: two beats stand between a brief and a
requirement precisely so that the sentences here answer something observed rather
than something argued.

## Step 2: Take the opportunity set and name the system

Work from `discovery.md` and nothing else. Read out, before writing any
requirement:

- **Every `OPP` id in the tree**, including the ones no solution was proposed for.
  The coverage table has a row per id, so the set is fixed here rather than
  accumulated as you write. Collecting it afterwards from the requirements you
  happened to produce yields a table that indexes your own output instead of
  checking it.
- **The one name for the thing being constrained.** Every requirement sentence has
  a slot for the system it constrains, and the template states what that name is
  and where it may come from.

Ask the user with `AskUserQuestion` only where `discovery.md` genuinely does not
answer one of these. It settles what the opportunities are; it does not always
settle what the system is called.

## Step 3: Write the requirements, then work the checklist and the gate over them

The order matters and is not the order the template's sections appear in.

1. **One requirement per thing that has to be true**, each written in an EARS
   pattern, each naming the `OPP` id it answers. The template owns the grammar,
   the casing and the id notation; follow it rather than this file on any of them.
2. **Then the quality characteristic checklist**, over the set you have. It is
   what makes the non-functional surface enumerable rather than whatever came to
   mind, so it is worked through after the functional rows exist and not instead
   of them.
3. **Then the INVEST gate**, over the requirements it applies to. It judges a
   requirement already written, so running it first would be judging a sentence
   nobody had committed to.

Two rules while writing, both of which the rubric will be read against later:

- **Never leave a slot to a plausible value.** A threshold nobody established
  takes the unknown marker, whose literal and payload rules live under the
  `## Unknown marker` heading of the artifact-family contract cited above. Copy
  them from there rather than reconstructing either from memory. A number you
  produced is cited by the next beat and never questioned again.
- **Never name a mechanism.** A requirement that names a button, a screen, a
  library or an endpoint has smuggled a solution into the document that exists to
  constrain one, and the rubric has a cluster whose whole job is finding it.

## Step 4: Get the provenance line, then write

Read the finished provenance line off the substrate; do not assemble it, and do
not compute a sha yourself:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --provenance-line --slug <slug> --member requirements.md --product-dir docs/product
```

Write its `line` field into `requirements.md` verbatim. The `--member` argument is
what makes the line this member's own: it names the member being written, and the
sha comes back over that member's upstream. If the field is null, the upstream you
refused over in step 1 is still missing — go back rather than inventing a line.

Say in one line what `## Re-run behaviour` below states, then write the file: the
sections in the order the artifact-family contract publishes them, filled per the
template.

**Never write to `discovery.md`.** Not to fix a tree, not to add an id you needed,
not to reword an opportunity so a requirement traces to it more neatly. Editing
the upstream changes its bytes, and the sha you have just written into
`requirements.md` is over those bytes: the edit would mark the file you are
writing stale the moment you finish it. Anything discovery gets wrong is reported
to the user as a `product-discovery` re-run.

## Step 5: Report

Report the path written, how many requirements it carries, how many `OPP` ids came
back `not addressed`, and how many unknown markers are in it.

Then state plainly what this document is not. It is not a design and not a plan:
it says what has to be true of the product, and every question of how is the next
beat's. A reader who takes a requirement for a work item will estimate it, and a
non-functional row carrying a latency threshold is not a work item.

An uncovered opportunity is not a failure and never a reason to refuse to write. A
`requirements.md` recording three opportunities as `not addressed` has done its
job; one covering all of them, written from a discovery nobody interrogated, is
the one that should worry a reader. Do not close a gap by writing a requirement
nobody asked for — the row saying nothing answers it is the finding.

## Re-run behaviour

A second run **revises `requirements.md` in place**. This is the one beat in the
suite that does not overwrite its member, and the reason is the ids.

- A requirement that survives the re-run keeps the number it already has, however
  much its wording, its pattern or its `Traces to` cell changed.
- A new requirement takes the next number after the highest ever used in this
  file, retired numbers included. Never the count of live requirements: a deletion
  would then free a number for something else.
- A requirement the re-run drops moves to `## Out of scope` with the reason it went
  there, rather than disappearing.
- A retired number is never reused. `REQ7` names one requirement for the life of
  the folder, whether or not `REQ7` is still live.

Why the rule exists, and not only what it says. `REQ` ids are cited by the beats
downstream of this one: a spec references a requirement by number, and so does
whatever plan is written from that spec. Nothing in the chain will ever tell you a
number has moved — the freshness mechanism compares the upstream's content hash
and never inspects a downstream identifier, so a wholesale renumber leaves every
member reporting `fresh` while every citation in the folder now points at a
different sentence. A review is the whole of this rule's enforcement. Read it as
bookkeeping you are free to tidy and the breakage is silent, surfaces beats later,
and looks like somebody else's mistake.

Announce the revision in step 4 as a statement, not a confirmation prompt: do not
ask permission and do not offer to overwrite instead. The previous version is not
recoverable, `docs/product/` being gitignored, so the ids in the file you are
reading are the only record of what they were.

Nothing else on disk changes. This beat creates no folder and refreshes no index:
it refuses unless `discovery.md` exists, and a `discovery.md` that exists is one
whose folder someone else already made.
