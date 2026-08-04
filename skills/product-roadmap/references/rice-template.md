# RICE template for roadmap.md

The shape `docs/product/<slug>/roadmap.md` is written into. `spec.md` says what is
being built and what is not; it says nothing about what comes first. This member
supplies the order, and supplies it as something a reader can argue with: every
position rests on a score whose inputs are visible one cell at a time, and every
item carries a fixed budget of time the work has to fit inside.

It carries no dates. No quarter, no sprint, no target month, and no heading named
after one. A date on unstarted work is a number nobody has a basis for, and
writing one here turns an ordering that was meant to be revised into a commitment
somebody will be held to. The ban holds in every section below, including the
risks. The one period this member does name is Reach's measurement window, and
that is how far ahead a count is measured over rather than when anything ships --
the two are easy to conflate and the distinction is worth holding on to.

This file comes in two parts. What sits above `## Scored items` is the grammar an
author scores *by*, not a section of the member: `## The RICE score` states what
the four inputs mean and what units they are in, and `## The appetite` states the
budget each item is scored against. Nothing in either is copied into
`roadmap.md` -- they supply numbers and a judgement, and what reaches the member
is their output. From `## Scored items` onward, every H2 is a section of the
member, and there are exactly three. Those names and their order are not decided
here -- they are published by
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
which this file renders rather than redefines. Nothing below is prose to copy:
each section names what belongs in it and what does not.

The member opens above its first heading with one provenance line, the only thing
it carries that no section below holds. It is not drafted here and not written by
hand. It is the `line` field of `product_artifact.py --provenance-line --member
roadmap.md`, copied verbatim: do not assemble it, and do not compute a sha. That
line's format, and what a sha that stops matching later means, are published by
the artifact-family contract cited above, which is the one place either is
written down.

Every item carries an id of the form `ITEM<n>` -- `ITEM1`, `ITEM2`, and so on --
drawn from one flat sequence across the whole member. The number encodes nothing:
not the item's rank, not its position in the sequence, not the requirements
grouped under it. All three change during ordinary re-scoring, and an id built
from any of them would be renamed by a recalculation rather than by a decision.

An id is never reused and never renumbered. That matters more here than in the
members upstream, because an `ITEM` id is cited from outside this folder --
issues filed elsewhere name it -- and no freshness check in this chain inspects a
downstream identifier. Nothing will ever tell you a number has moved, so a
renumbering that tidies the table silently repoints every citation to it.

`ITEM` rather than a betting-table word is deliberate. Appetite is borrowed from
Shape Up below and its provenance is stated there, but Shape Up's process is not
implemented here, and taking its vocabulary for the id namespace would claim
otherwise.

## The RICE score

The score is Intercom's, published by Sean McBride in 2018. Four inputs, one
formula, and the whole of its value is that a position somebody disagrees with
can be traced to the input they disagree about:

```
score = (reach x impact x confidence) / effort
```

- **Reach** -- how many people or events the work touches, as a count over a
  named period. A count, not a proportion: "most of them" is not a Reach.
- **Impact** -- a fixed five-point scale, and the values are not spaced the way a
  reader guesses: `3` for massive impact, `2` for high, `1` for medium, `0.5` for
  low, `0.25` for minimal. There is nothing between the points and nothing above
  `3`. An item that seems to need a `5` is being argued for rather than scored.
- **Confidence** -- one of three percentages: `100%` for high confidence, `80%`
  for medium, `50%` for low. Anything below `50%` is not a fourth tier; the
  source's word for it is a total moonshot, and the honest thing to do with one
  is to write that down rather than to round it up into the bottom tier.
- **Effort** -- the total work in person-months, one person working for one
  month. Rough on purpose: whole numbers, or `0.5` for anything well under a
  month. A cell reading `2.75` claims a precision the other three inputs cannot
  support.

Reach's period is not prescribed. McBride names the quarter as his own team's
convention -- "how many customers will this project impact over a single
quarter?" -- and not as part of the method, so this file does not print one
either. Each roadmap names its own period once, above the table in
`## Scored items`, and every Reach cell in that roadmap is counted over that same
period. A member whose rows quietly measure different windows has a column that
cannot be read down, which is invisible in any one row.

The other three inputs are the source's own units and are not local conventions.
Rescaling Impact, adding a confidence tier, or switching Effort to person-weeks
makes this roadmap's numbers incomparable with any other, while leaving every
cell looking perfectly ordinary.

## The appetite

Appetite is Shape Up's term, from Basecamp's Ryan Singer: the amount of time the
organisation wants to spend on something, as opposed to an estimate of what it
will take. Estimates start with a design and end with a number; an appetite
starts with a number and ends with a design. It is decided before the shape of
the work is known, which is exactly what makes it a budget rather than a
forecast.

Its unit is team calendar time against a fixed team size -- a time budget for a
standard team, in weeks. Shape Up's own two sizes are a small batch at one or two
weeks and a big batch at six.

**An appetite is never an input to the score.** The formula above has four terms
and this is not a fifth: it multiplies nothing and divides nothing. It sits
beside the score because a reader needs both and they answer different questions.
The score says how this work compares with the rest of the table. The appetite
says how much of the organisation's time it is allowed to take before it stops
being worth doing at all.

Fixed time, variable scope is Shape Up's own named principle, and it is what the
`Appetite` column commits to. When the Effort a scoring turned up will not fit
the appetite, exactly two things may happen: the scope is reshaped until it fits,
or the item is dropped. Raising the appetite to match the effort is the one move
that is not available. It converts the budget into an estimate, at which point
the column has nothing left to say that `Effort` did not already say.

Effort and appetite are in different units, and the conversion between them is
this template's own convention. Neither source states one: Intercom's post is
silent on calendar time and Shape Up's chapters are silent on person-months, so
nothing below is borrowed and none of it is anybody else's rule.

```
team calendar weeks = (effort in person-months x 4) / people on the team
```

Four weeks to a month is the approximation this file adopts. The team size is
the term that makes the conversion mean anything, so a roadmap names it once,
beside Reach's period, above the table in `## Scored items`.

The conversion is a check on whether an item plausibly fits the appetite it was
given. It is not a way of producing the appetite: an appetite computed from an
effort is an estimate wearing the word, and the whole point of the column is that
somebody decided the number before the work was designed.

## Scored items

Every item, scored, whether or not it appears in `## Sequence` below. This
section is the evidence; the sequence is the commitment, and keeping them apart
is what stops the second from being a sorted view of the first.

One line above the table names the two things the whole table is read against:
the period every Reach cell is counted over, and the team size every Appetite
assumes. Both are this roadmap's own choices, and neither is recoverable from the
cells once the line is missing.

| ID | Item | Traces to | Reach | Impact | Confidence | Effort | Score | Appetite |
|---|---|---|---|---|---|---|---|---|
| `ITEM1` | `<the work, in one line>` | `<one or more REQ ids from spec.md>` | `<the count, and what it was counted from>` | `<3, 2, 1, 0.5 or 0.25, and why that point>` | `<100%, 80% or 50%, and what supports it>` | `<person-months, and what the figure rests on>` | `<the computed number>` | `<team calendar weeks>` |

- **ID** -- the item's `ITEM<n>` id, as described above.
- **Item** -- what the work is, in one line, in words somebody who has not read
  `spec.md` would still recognise. An item is a group of requirements that make
  sense to build together, so this cell names the group rather than restating its
  parts.
- **Traces to** -- one or more `REQ` ids from `spec.md`'s
  `## Requirements in scope`. Never blank. An item that traces to nothing is work
  nobody specified, arriving in the one document that decides what gets built
  first.
- **Reach**, **Impact**, **Confidence**, **Effort** -- the four inputs, in the
  units `## The RICE score` fixes, each carrying its basis in the same cell as
  its figure.
- **Score** -- the number the formula produces from the four cells to its left,
  and one number: a re-scored item's previous score is not kept beside its
  current one. Two scores in a row is two answers with no rule for choosing
  between them, and a reader takes whichever supports the position they already
  hold.
- **Appetite** -- the budget in team calendar weeks, decided before the work was
  shaped, as `## The appetite` describes.

Each of the four input cells carries a figure **and its basis** -- the ticket
count it was read off, the person who supplied it, the comparable piece of work
it was judged against. A figure with no basis is not a third thing a cell can
hold. It is the first thing with the part that makes it revisable left off: a
number nobody can attribute cannot be corrected later on purpose, only argued
about, and this table exists to be argued with precisely.

Where no basis exists, the cell carries the suite's unknown marker in place of
the figure. The token and its payload rules are defined by
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
which is the only place they are written out; copy the literal from there rather
than reconstructing it. An item carrying the marker in any of its four inputs has
no `Score`: that cell carries the marker too. A score computed through a number
nobody has is the single most damaging thing this member can contain, because it
arrives with three decimal places and outranks a well-sourced item on a table
nobody re-derives.

The second table is the check on the first. One row per `REQ` id in `spec.md`'s
`## Requirements in scope`, including every one that no item covers.

| Requirement | Covered by |
|---|---|
| `REQ1` | `<the ITEM ids covering it, or the literal: not covered>` |

`Covered by` has exactly two permitted forms: one or more `ITEM` ids, or the
literal `not covered`. A blank cell is not a third form. An empty cell means
either that no item covers the requirement or that nobody filled the table in,
and telling those two apart is the entire reason the table is here.

Listing only the covered requirements would make this an index of the items
rather than a check on them. A specified requirement that no item covers is
either a decision somebody made or work that fell out of the roadmap unnoticed,
and this beat does not get to make those look the same.

An item that is not in `## Sequence` keeps its row here. Retirement is absence
from the sequence, never deletion from this table: the row and its id stay
forever, because the id is cited from outside and a deleted row leaves those
citations pointing at nothing while every file in the chain still reports fresh.

## Sequence

The order the work is actually taken in, as an ordered list of `ITEM` ids and
nothing else:

```
1. ITEM3
2. ITEM1
3. ITEM7
```

This is a position, not a schedule. The list says what comes after what; it says
nothing about when any of it starts, and a quarter, a sprint number or a month
written beside an entry is the failure this section is most exposed to.

The order is **derived, not sorted**. It is not `## Scored items` ranked by
`Score`. A sorted copy would make this section a view of the table above rather
than a decision anybody made, and there would be nothing here for a reader to
disagree with -- which is the same as saying nobody would need to read it.

Two things routinely outrank the score, and each departure from score order names
which of the two it was:

- **Dependencies.** An item that cannot usefully start until another has finished
  goes after it, however the two scored.
- **Appetite windows.** What is actually available to spend is lumpy. One
  six-week item and three two-week items do not fit the same window, so a
  lower-scoring item that fits can honestly precede a higher-scoring one that
  does not.

Below the list, record **the ordering that was rejected**: at least one sequence
that was seriously considered, and what decided against it. This is the part of
the section that is worth reading a year later. Without it a reader cannot tell
an order somebody chose from the first order somebody wrote down, and the two
look identical on the page.

An item may be absent from this list. Absence is how an item is retired or
deferred -- its row stays in `## Scored items`, marker and all -- and an item
with no `Score` cannot appear here at all, since there is nothing to have ranked
it by.

## Risks

What would make the ordering above wrong: specifically, what could invalidate an
appetite or a confidence. Not a general register of project worries -- every
entry names the item and the cell it would move.

| Risk | What it would invalidate | What would show it |
|---|---|---|
| `<what could turn out otherwise>` | `<the ITEM id, and which cell: its appetite, its confidence, or its position>` | `<the observation that would settle it, and roughly when it is available>` |

- **Risk** -- the thing that could turn out otherwise, stated so that a reader
  could tell whether it had happened.
- **What it would invalidate** -- the named `ITEM` id and the cell that would
  move. A risk that invalidates nothing on either table above is a worry, and
  belongs wherever this team keeps worries rather than in the document that
  decides what is built first.
- **What would show it** -- the observation that would settle the question. Not a
  date: "when the pilot integration is attempted" is a signal, and "by the end of
  the quarter" is a deadline dressed as one.

The two cells worth the most attention here are the appetite and the confidence,
for opposite reasons. An appetite is a decision, so what threatens it is somebody
deciding differently -- and that is a risk this document can name in advance. A
confidence is a claim about evidence, so what threatens it is evidence arriving,
which is the ordinary case rather than an exception. A `100%` cell with a risk
against it is a `50%` cell that has not been re-read.
