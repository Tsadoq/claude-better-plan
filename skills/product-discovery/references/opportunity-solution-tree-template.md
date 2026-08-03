# Opportunity Solution Tree template for discovery.md

The shape `docs/product/<slug>/discovery.md` is written into. Where `brief.md`
argues that a product is worth building, this member takes that argument apart:
the outcome it is aiming at, the customer opportunities that could move it, the
solutions worth considering, and the assumptions each one rests on, ordered by
which is riskiest to be wrong about.

Every H2 below is a section of `discovery.md`, in the order the member carries
them. The section names and their order are not decided here -- they are
published by
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
which this file renders rather than redefines. Every H3 is one of the five
framework artifacts this beat produces, filed under the H2 whose subject it
belongs to. Nothing below is prose to copy: each part names what belongs in it
and what does not.

Three ways to fill a slot, and only three. **Supplied**: the user or `brief.md`
stated it, so write it plainly. **Researched**: a public source states it, so
write it with an inline citation to that source. **Unknown**: nobody has
established it, so write the suite's unknown marker, whose literal and payload
rules are defined once under the `## Unknown marker` heading of the
artifact-family contract cited above. A slot is never filled with a plausible
figure. This member is read as input by the one after it, which cites what it
finds rather than questioning it, so an invented figure here becomes a
requirement later.

## Signals

What is known, and who says so. Both sections below carry claims that a reader
can trace: the tree's opportunities to the evidence behind them, and the market
figures to the method and source that produced them.

### The tree

Four layers, each with its own table, and four connection rules. The rules are
stated rather than drawn, so that a broken connection is something a reader
sees rather than interprets:

1. **One outcome, and it is the root.** Exactly one row in the Outcome table,
   naming the business result this discovery is in service of. It has no
   parent, so its table declares no parent column.
2. **Every opportunity names one parent, and it may be another opportunity.**
   The parent is either the outcome or another opportunity: Torres does not
   treat opportunities as a flat layer, writing instead about "top-level
   opportunities" and instructing teams to "structure each branch one at a time
   creating parent-child and sibling relationships." A scheme permitting only
   an outcome as parent would forbid a shape the framework requires.
3. **Every solution names exactly one parent opportunity.** Not the outcome and
   not two opportunities at once. A solution wired straight to the outcome is
   the jump this whole artifact exists to prevent, and a solution serving
   "several opportunities" is usually two solutions not yet told apart.
4. **Every assumption test names exactly one parent solution.** A test that
   settles nothing about a specific solution is a study, not a test.

A rendered diagram of the tree is optional and may be included anywhere in this
section. The tables are the normative form: they are what carries the ids, and
a diagram that disagrees with them is wrong by construction.

Ids are prefixed by layer -- `OUT<n>`, `OPP<n>`, `SOL<n>`, `AT<n>` -- rather
than drawn from one sequence. The prefix is what makes rule 3's violation
visible in the parent cell itself: a `SOL` row whose parent reads `OUT1` is
wrong on sight, with nothing to cross-reference and no other table to open. A
single sequence would render the same violation as `S4`'s parent being `S1`,
which reads exactly like a correct row. The prefixes are therefore load-bearing
notation and not decoration; simplifying them away removes the property, not
the noise.

That notation is this project's invention. No id, numbering or parent-reference
convention appears anywhere in Torres's own material, so nothing about the
scheme below should be read as hers.

**Outcome**

| Outcome id | Outcome statement | How it is measured | Source |
|---|---|---|---|
| `OUT1` | `<the business result this discovery serves>` | `<the metric that would move, and in which direction>` | `<where the outcome comes from: brief.md, or whoever set it>` |

**Opportunities**

Each row is a customer need, pain point or desire, phrased as the customer
would experience it and never as a feature. The discriminating question for a
solution wearing an opportunity's clothing is Torres's: is there more than one
way to address this? If only one, it is a solution and belongs in the table
below.

`Evidence` is mandatory and never blank. An opportunity nobody has evidence for
is a hypothesis about a customer, which is a different thing from a customer's
need, and the difference is invisible once the cell is empty.

| Opportunity id | Parent | Need, pain or desire | Evidence |
|---|---|---|---|
| `OPP1` | `<an OUT or OPP id>` | `<what the customer is trying to get done, and what is in the way>` | `<what was observed, and where: an interview, a ticket, an analytics figure -- or the unknown marker>` |

**Solutions**

| Solution id | Parent | Solution | What it would change for the customer |
|---|---|---|---|
| `SOL1` | `<exactly one OPP id>` | `<what would be built or changed>` | `<what the customer could then do that they cannot do now>` |

**Assumption tests**

One row per test worth running against a solution. This table records what
could be run; `### Riskiest assumption tests` records the order they are run
in, and the two are not the same list.

| Assumption test id | Parent | Assumption it settles | The test | What result would settle it |
|---|---|---|---|---|
| `AT1` | `<exactly one SOL id>` | `<the assumption from the mapping table below>` | `<the cheapest thing that could be done to find out>` | `<the observation that would change the decision, stated before the test is run>` |

### Market sizing

Three nested figures: the total addressable market contains the serviceable
available market, which contains the share obtainable. Every figure carries the
method that produced it and the source that method drew on. A figure with no
source takes the unknown marker -- this is the section of the whole chain where
a confident invented number is most likely and most costly, because a market
size is the one figure nobody downstream re-derives.

| Figure | Value | Method | Source |
|---|---|---|---|
| TAM -- Total Addressable Market: the revenue opportunity if the whole market were served | `<figure>` | `<top-down, bottom-up or value-theory>` | `<the research, dataset or internal figure it came from>` |
| SAM -- Serviceable Available Market: the portion of TAM reachable by what the company can actually serve and sell to | `<figure>` | `<top-down, bottom-up or value-theory>` | `<as above>` |
| SOM -- Share Obtainable: the portion of SAM realistically won, given competition and capacity | `<figure>` | `<top-down, bottom-up or value-theory>` | `<as above>` |

The method is one of exactly three named approaches. **Top-down** narrows from
published industry totals to the relevant segment. **Bottom-up** builds from
the company's own units, prices and reachable customers. **Value-theory**
estimates the value delivered to a customer and the share of it that can be
priced. None of the three is preferred: sources naming them rank them not at
all, and a bottom-up figure built on invented unit counts is worse than a
sourced top-down one.

Two naming notes, so that a reader meeting a different expansion elsewhere does
not think one of the two is a mistake. SAM is written here as *Serviceable
Available Market*; *Serviceable Addressable Market* is in equally live use for
the same concept. And this trio has no attributable origin: no source
consulted attributes it to a named author, firm or book, so it is not cited to
one.

## Constraints

What has to be true for the solutions above to work, and how much of it is
currently taken on faith.

### Assumption mapping

One row per assumption, with these six fields and no others. An assumption is
written so that it could be shown false; a statement nobody could falsify is a
belief and belongs in the tree's evidence column or nowhere.

| Assumption | Category | Importance | Evidence | Quadrant | Test |
|---|---|---|---|---|---|
| `<the belief, phrased so a result could contradict it>` | `<desirability, feasibility or viability>` | `<important or unimportant>` | `<have evidence or no evidence>` | `<the pair above, read as one cell>` | `<the AT id that would settle it, or the unknown marker if none is designed yet>` |

`Category` is closed at three values. **Desirability**: does the market want
this? **Feasibility**: can it be delivered at scale? **Viability**: is it
profitable enough? An assumption about whether the idea survives a changing
environment is recorded as a viability assumption -- that fold is this
template's own mapping, not one the source states, and it exists so that
durability has somewhere to go without opening a fourth category a discovery
beat could rarely answer.

`Importance` and `Evidence` are coarse buckets, not scores. The grid they come
from has binary axes -- important against unimportant, have evidence against
no evidence -- so a number here would claim a precision the framework does not
have and invite arithmetic on it.

`Quadrant` is therefore derived, not chosen: it is the pair of the two fields
before it, restated as one cell because it is what the next section is drawn
from. Only one of the four is named in the source: the important, no-evidence
corner, "beliefs that are critical for success and yet have the least amount of
evidence to support them." The other three are described by position rather
than given invented labels. (The widely used label *leap-of-faith assumptions*
for that corner traces to Eric Ries's *The Startup Way*, not to the assumption
mapping literature, so it is not used here as though it were the source's own.)

## Open questions

What is not yet known, and the instruments for finding out.

### Riskiest assumption tests

An ordered list, most urgent first. The order is derived, not chosen:

1. Take only the assumptions in the important, no-evidence quadrant. An
   assumption with evidence behind it is not what a test buys information
   about, and an unimportant one buys information nobody will act on.
2. Order those by the cost of testing them, cheapest first -- the smallest
   experiment that could settle the biggest assumption.

Write the list as `AT` ids with one line each saying what a failure would mean
for the solution it hangs off. If the derivation yields nothing -- no
assumption sits in that quadrant -- say so; an empty list is a finding about
the assumptions, not a gap in this section.

This order is testing urgency. It is not a delivery order and not a backlog:
the point of testing the riskiest thing first is to find out cheaply whether
the rest is worth planning at all.

### JTBD switch-interview structure

The structure for interviewing someone about why they switched. This section
produces the structure; it does not conduct the interview or name the people to
talk to.

The interview reconstructs one real switch, working backward from the moment
the person decided, and locates four forces along the timeline it recovers.
The **Four Forces of Progress** are:

- **Push of the situation** -- what about the old way stopped working.
- **Pull of the new solution** -- what the new way seemed to offer.
- **Anxiety of the new solution** -- what about switching was worrying.
- **Habit of the present** -- what was comfortable about carrying on.

The working hypothesis is that a switch happens when push plus pull outweigh
anxiety plus habit, and that the two forces on the second line are the ones
teams routinely forget to ask about. Both are reasons a switch did *not*
happen, so an interview that only collects push and pull will find every
customer eager to switch and be wrong.

Reconstruct the timeline in the interviewee's own terms rather than against a
fixed list of stages. What the interviewer is looking for is the first thought,
the events that pushed the person forward, the anxieties that held them back,
and the moment they finally decided. No stage count is fixed here on purpose:
sources disagree about how many stages the timeline has, and the numbered event
labels in common circulation could not be confirmed as the framework's own
vocabulary. Recording six or eleven named stages as though the count were
settled would freeze someone else's shorthand into this template.

Record the structure as the questions this interview would open with and the
four forces they are meant to surface, not as a script. The questions that
matter in a real switch interview are the follow-ups, which nobody can write
in advance.
