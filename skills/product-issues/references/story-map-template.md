# Story map and slice template for docs/product/<slug>/issues/

The shape a slice set must have, and the shape of the one markdown file written
per slice. `roadmap.md` closes the chain with `ITEM<n>` rows, scored and
sequenced; an item is a group of requirements that made sense to score together,
which is a different thing from a piece of work one person can pick up and
finish. This file says how an item becomes those pieces and what each piece
carries.

Nothing below is prose to copy. The vocabulary is borrowed -- the map is
Patton's, the splitting patterns are Cohn's, the gate is Wake's -- and each is
attributed where it is used, because a term used without its source drifts into
whatever the reader already thought it meant.

A slice set is not a chain member. The family is closed at five members,
`brief.md` through `roadmap.md`, published by
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
and `issues/` sits beside them as a folder rather than after them as a sixth.
That has one consequence worth knowing before anything below makes sense: no
freshness check in this suite reads a slice. Nothing will ever tell you that the
roadmap moved after a slice was cut from it, which is why `## References` carries
a sha by hand.

## The slice set

The map is a thinking tool and the folder is the artifact. One is
two-dimensional -- activities across, releases down -- and the other is a flat
list of files, so the map's two axes have to survive the flattening or the
structure was never really decided:

- The **activity** axis survives as the `activity` key on every slice. Two slices
  with the same `activity` sit in the same column, and a column nobody can name
  as an activity is a column that was never on the backbone.
- The **release row** axis survives as the optional `milestone` key, and only
  matters once a set has more than one row. A single-row set leaves it off
  entirely rather than inventing a name for the only row there is.

Each slice is one markdown file in `docs/product/<slug>/issues/`, and that folder
holds nothing else. A file's name is a convenience for whoever lists the folder;
the id in its frontmatter is the identity. Name files so that a plain sort reads
in cut order and the day the two disagree, believe the frontmatter.

Ids are of the form `SLICE-<n>`, drawn from one flat sequence across the whole
set, and both of this form's departures from the family's other ids are
deliberate. `ITEM<n>` in `roadmap.md` and `REQ<n>` in `requirements.md` carry
neither a hyphen nor a fixed width, because both are read inside a table that
supplies its own order. A slice is read as a directory listing, which has no
order except the one its names sort into. So this id is zero-padded to a width
the whole set shares -- two digits for the ordinary set, three for one that will
pass ninety-nine, which a set can, since a single parent takes up to a hundred
sub-issues -- and hyphenated so that the padding does not run into the word.
Choose the width before the first id: widening it later means renumbering, and
the next paragraph is why that is not available.

The number carries the order the slices were cut in and nothing else. Not
priority, not dependency -- `## Blocked by` holds that -- not the activity, not
the release row, not the roadmap item. It is never reused and never renumbered: a
re-run of this beat adds slices, it does not renumber the ones already there.
That matters more here than anywhere upstream, because a slice id is cited from
outside this folder, by other slices' `## Blocked by` sections and by whatever
got filed to a tracker, and no check in this suite would notice a number that
moved.

## The backbone is user activities

The top row of the map is the **backbone**: Patton's term, from *The New Backlog*
(<https://jpattonassociates.com/the-new-backlog/>), for the user activities a
person moves through, left to right, in the order they do them. Read it aloud as
a sentence about somebody's day. If it reads as a sentence, it is a backbone.

The backbone is never system components. "Authentication", "API", "database",
"admin screens" is a decomposition of the software, not of anybody's day, and it
is the decomposition a slicing pass produces by default, because architectural
layers are the most legible structure in a codebase and the activities are not
written down anywhere. It fails at the point it is supposed to pay off: a row cut
across component columns is a set of parts, and no row of parts is something a
person can use.

Everything under an activity is detail belonging to it, and the slices of one
item may land under more than one activity. That is ordinary -- an item is a
group of requirements, and requirements from one group routinely touch two things
a user does.

## Row one is the walking skeleton

Rows are cut across the whole backbone, never down one column. Patton's own
guidance is that a release row spans every activity rather than completing one of
them, and the first row has a name and a test.

The name is the **walking skeleton**, which is Alistair Cockburn's term. Patton
credits him for it and borrows it with its meaning unchanged: a thin
implementation that performs one function from one end of the system to the
other, linking the main pieces together, rather than a complete implementation of
any one piece. Nothing here quotes Cockburn, deliberately -- his own page for the
term was unreachable when this file was written, and a paraphrase that is
attributed is honest in a way a quotation nobody could re-check is not.

The test row one has to pass is one question:

> Can someone use it, start to finish, badly?

Badly is the load-bearing word. Slow, ugly, one hard-coded case, a manual step in
the middle, no error handling worth the name -- all of these keep a row one. What
ends it is *start to finish*: a row that a person cannot get through without a
part that does not exist yet is not thin, it is unfinished.

A walking skeleton is not a minimum viable product, and the two are worth keeping
apart because they answer different questions. A minimum viable product is a
claim about the market: the smallest release worth putting in front of real
people to learn whether the thing should exist. A walking skeleton is a claim
about the structure: the pieces connect and something travels the whole way
through them. A walking skeleton can be entirely unreleasable and still be
exactly right. A minimum viable product that does not run end to end is not a
skeleton at all, and calling it one buys a structural guarantee nobody actually
has.

## The five SPIDR patterns

Once the rows exist, the splitting technique for what remains is SPIDR, from Mike
Cohn's *Five Simple but Powerful Ways to Split User Stories*
(<https://www.mountaingoatsoftware.com/blog/five-simple-but-powerful-ways-to-split-user-stories>).
Five patterns, and the point of naming them is that "make it smaller" is not
advice anybody can act on, while "split it by data" is:

- **Spike** -- split the research off from the work. A spike answers a question,
  and what it produces is knowledge that makes the rest possible to build or to
  size, not functionality anybody ships. Normally not the first pattern to reach
  for: one of the four below usually splits the work without spending a slice on
  finding out how.
- **Path** -- split by the routes through the work. Draw the flow and take the
  straight one first; each branch, alternative and error route is a later slice.
- **Interface** -- split by the surface the work is delivered through. One
  screen, one browser, one device, one API before the interface built on it.
- **Data** -- split by the data handled. One source, one field set, one format
  first, the rest afterwards.
- **Rules** -- split by relaxing the rules. Build against a simplified rule set
  now and the full set later: fewer validations, one currency, one tax case, no
  performance target.

Spike is listed first because the acronym spells it first, not because it is
tried first. A set where the early slices are spikes is a set that decided to
research rather than to slice.

## The INVEST gate is cited, not restated

Every slice passes the INVEST gate before it is written to the folder. The gate
is published once for this whole suite, at
`${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/requirements-template.md`
under `## The INVEST gate`, and is not restated here. Two copies of a six-part
gate diverge one letter at a time and neither copy looks wrong on its own; go and
read that section.

Two things about it are this file's business rather than that one's. INVEST is
Bill Wake's, published in 2003
(<https://xp123.com/articles/invest-in-good-stories-and-smart-tasks/>), and is
frequently misattributed to Cohn, whose SPIDR is the section above -- two authors
whose work meets in this file, and getting them the wrong way round makes both
citations useless to whoever follows them.

The other is SMART. Wake's same article coins SMART as a checklist for the
*tasks* underneath a story, and it is named here only so it is not blended with
the gate. Run a slice through a task checklist and it comes back as a task list:
smaller, sharper, and no longer something a person outside the work can see the
point of. The gate above is the one a slice passes; SMART is a different tool for
a level below this one.

## The slice frontmatter

Every slice file opens with a `---` fenced block of flat `key: value` lines, one
per line, no indentation. A value beginning with `{` or `[` is JSON and is
decoded as JSON; every other value is the string it looks like. Flat rather than
nested because every script in this suite is standard library only and there is
no YAML parser to reach for -- an indented line is refused rather than skipped,
so that a format which merely resembles YAML does not quietly start being written
as YAML.

This file is the schema's single published home. `slice_file.py` holds
`REQUIRED_KEYS` as the code's copy of the list below, and this skill's contract
test asserts the two are equal rather than trusting them to stay in step, so a
key added here without a change there fails the suite by design.

### Required keys

Every slice carries all five, in this order. Presence is required; a `labels`
list may be empty, but the key is still there.

| Key | Value |
|---|---|
| `slice` | This slice's own id, of the form `SLICE-<n>`, never reused and never renumbered. |
| `title` | The one-line title the issue is filed under. What it delivers, in a person's words, not a component name. |
| `activity` | The backbone activity this slice sits under. Nothing checks the spelling, so a typo silently opens a second column rather than joining the first. |
| `roadmap_item` | The `ITEM<n>` id in `roadmap.md` this slice was cut from. Pre-flight refuses a set whose ids are not in that member. |
| `labels` | A JSON list of label names, applied at the destination and created there if missing. |

### Optional keys

- `milestone` -- a milestone *title*, not a number. The release row this slice
  belongs to, carried only by sets with more than one row. The filing stage looks
  the title up at the destination and creates it if there is none.
- `filed_<destination>` -- the ledger. Written by the filing stage immediately
  after that slice's create call succeeds, recording the issue's number, its
  database id and its URL, and never written or edited by hand. Its presence is
  what makes a second run leave this slice alone, and no path through this beat
  will file a slice that carries one. Because it is written per slice rather than
  at the end, a run killed halfway leaves an exact record of what got through --
  and deleting one by hand is the way to file a duplicate.

A whole slice, for shape:

```
---
slice: SLICE-03
title: Narrow the roster to one cohort
activity: Review a cohort
roadmap_item: ITEM2
labels: ["product-issues", "size/S"]
milestone: Walking skeleton
---

## Context
...
```

## The body

The body is the issue. Everything past the closing fence is copied byte for byte
and sent as the issue body, so what is written here is what somebody reads on the
tracker, and no part of this beat reformats it. Six sections, these names, this
order, in every slice -- a section that appears in some slices and not others
makes a set that has to be read one file at a time:

- `## Context` -- what somebody needs to pick this up cold: the activity it sits
  under, and the problem the roadmap item is answering. Enough that the slice
  stands alone, not a retelling of the roadmap.
- `## Blocked by` -- the slice ids that have to land first, or `none`. Never
  omitted; see below.
- `## Deliverables` -- what exists when this is done, written as things that
  exist rather than as steps somebody takes.
- `## Acceptance criteria` -- how a person other than the author confirms it is
  done, each one a statement they can check without asking anybody.
- `## Out of scope` -- what a reader would reasonably assume is included and is
  not, naming the slice that covers it where one does. This is the section that
  stops a slice growing back.
- `## References` -- the roadmap sha below, plus whatever else the implementer
  will open.

A slice carrying the unknown marker is not filable. That marker's token is
published by the artifact-family contract cited at the top of this file, and
pre-flight refuses the whole batch over one, because filing is the irreversible
step and a slice with an open question in it is one somebody stopped deciding
halfway. Decide it, or leave the slice out of this run.

### Why `## Blocked by` is a section and not a field

Ordering is body text because the schema above is destination-blind -- one set of
keys, written before anybody has chosen where the slices go -- and a key is worth
having only if every destination can honour it. A machine-readable blocker does
not clear that bar. The linking flags, `--blocked-by` among them, landed in `gh`
2.94.0; every earlier `gh` creates issues perfectly well and cannot express a
blocked-by link at all, so a blocker key would be a promise that fails on
whichever machine is running the older one. The schema therefore has no such key,
and nothing in this beat turns this section into a tracker dependency link. A
destination that could carry ordering on every machine would be reason to revisit
this; until one exists, the text is the record.

Which means the ordering a reader gets is the ordering written in this section,
or none. Name the ids -- `SLICE-02`, not "the roster slice" -- because the ids are
the stable thing, and write `none` rather than dropping the section, so that an
unblocked slice reads as a decision instead of an omission.

### The roadmap sha in `## References`

`## References` carries the git blob sha of `roadmap.md` as it stood when the
slice was cut:

```
Cut from roadmap.md at <40 lowercase hex characters>
```

What a sha of this kind is, and the rules it is held to, are defined by the
artifact-family contract cited at the top of this file and are not restated here.
Take the value from `git hash-object`; do not invent a hash of your own.

It is the same kind of value the chain's provenance lines carry, and it is not
one of them. Nothing downstream of `roadmap.md` is a chain member, so no
provenance line anywhere holds this sha and `--provenance-line` will not produce
it -- that command answers about members. Do not borrow the provenance line's
format for it either: that shape is what a freshness check reads back, and
wearing it here would dress a sha nothing verifies as one that something does.

So this sha is for a person. It is the one thing in a slice that lets somebody
holding a two-month-old issue ask whether the roadmap it was cut from still says
what it said, and it is worth carrying precisely because nothing in this suite
will ever ask that question on their behalf.
