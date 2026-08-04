# Requirements template for requirements.md

The shape `docs/product/<slug>/requirements.md` is written into. Where
`discovery.md` argues which customer opportunities are worth pursuing, this
member restates the ones being pursued as sentences a test can be written
against. Everything upstream of it is deliberately prose, and neither a
narrative nor a ranked set of bets is falsifiable one sentence at a time, so
this is the member where that ambiguity gets spent.

This file comes in two parts. What sits above `## Scope` is grammar the author
writes requirements *by*, not a section of the member: `## The EARS notation`
states the sentence shape every requirement takes, `## The quality
characteristic checklist` enumerates the non-functional surface a member has to
account for, and `## The INVEST gate` is the last read a requirement gets before
it ships. Nothing in the three is copied into `requirements.md` -- they supply
sentences, questions and a judgement, and what reaches the member is their
output. From `## Scope` onward, every H2 is a section of
`requirements.md`, in the order the member carries them. Those names and their
order are not decided here -- they are published by
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
which this file renders rather than redefines. Under them, every H3 is content
this beat produces, filed under the H2 whose subject it belongs to. Nothing
below is prose to copy: each part names what belongs in it and what does not.

Every requirement carries an id of the form `REQ<n>` -- `REQ1`, `REQ2`, and so
on -- drawn from one flat sequence across the whole member. The number encodes
nothing: not the opportunity a requirement answers, not the pattern it is
written in. Both of those change during ordinary authoring, and an id built
from either would be renamed by a correction rather than by a decision, while
downstream members and issues already cite the old one.

An id is never reused. Once `REQ7` has appeared in a member, that number stays
retired even after the requirement it named is deleted, so a citation to it can
be read as stale rather than as pointing at something unrelated. No published
source mandates this: INCOSE's requirements-quality rules cover duplicated
requirement content and say nothing about identifier reuse, so id stability is
this project's convention and not an external requirement.

## The EARS notation

Every requirement in this member is one sentence in the Easy Approach to
Requirements Syntax, the notation Mavin et al. published at IEEE RE'09. Five
patterns, one generic form, and a rule for combining them is the whole of it,
and the point of a fixed clause grammar is that a sentence written to one makes
its own missing parts visible. Unconstrained prose does not: "the system should
handle errors gracefully" reads like a requirement, and nobody can say what
would violate it.

The generic form, printed as the paper prints it:

```
<optional preconditions> <optional trigger> the <system name> shall <system response>
```

Clause order is significant, and it is the part of the form most easily lost.
Preconditions come before the trigger because they gate it: what state the
system is in is settled first, and only then does the trigger count. A sentence
that puts its state clause after its trigger states the reverse, which is a
different requirement built from the same words.

`shall` is the notation's only modal verb, and the response clause is the only
place a demand belongs. "Should", "may" and "will" are not weaker requirements;
they are sentences nobody has to satisfy, so a row carrying one is a note filed
in a requirements table.

The five patterns differ only in which of the two optional clauses they fill,
and each has a section below, in the paper's order, from the always-active case
outward. Which pattern a sentence is written in goes in the `Pattern` column of
the tables under `## Requirements`, spelled with the name its section carries
here, so a mis-typed sentence is visible next to the sentence itself.

### Casing

A requirement written into a table below is fully uppercase, through the
subject-verb and not only the keyword:

```
WHEN <trigger> THE SYSTEM SHALL <response>
```

`THE SYSTEM` stands in for whatever `### The system name` declares; the words
are not the mandate, the casing is. Placeholders stay lowercase inside angle
brackets throughout this file because they are slots rather than text, and each
pattern's grammar below is printed the same way -- what is uppercase there is
what a finished requirement carries verbatim.

This follows Kiro, the AWS spec-driven development environment, which generates
a per-feature `requirements.md` in EARS and writes it this way. It does not
follow the notation's own author. The 2009 paper prints its pattern templates
with uppercase keywords but writes every worked example in ordinary sentence
case with a lowercase `shall`, and Alistair Mavin still writes it that way
today, so the uppercase in the paper marks the grammar rather than instances of
it. A reader who goes to the paper will find sentence case there, and should
read this as a deliberate divergence rather than as this template misreading
its source.

What decided the divergence is the ubiquitous pattern. It carries no keyword,
so a rule that uppercases keywords alone leaves always-active requirements
typographically identical to the prose around them, while `THE SYSTEM SHALL`
appears in every pattern and makes any requirement greppable whichever one it
uses.

Punctuation is not part of the notation. The keywords are the clause
boundaries, which is why the paper's own examples use commas freely and Kiro's
use none, and why neither spelling changes what a requirement says.

### Ubiquitous requirements

Behaviour that is always active: no state to be in, no event to wait for,
nothing to switch it on. Both optional clauses of the generic form are empty,
which leaves the system name, the modal and the response.

```
THE <system name> SHALL <system response>
```

Example:

```
THE CONTROL SYSTEM SHALL PREVENT ENGINE OVERSPEED.
```

Non-functional requirements are written in this pattern too, rather than in a
notation of their own: a quality attribute the product must always exhibit is
behaviour that is always active. What makes such a row a requirement rather
than a preference is the threshold and its source, which `### Non-functional
requirements` covers. The pattern supplies the sentence, not the number.

The always-active reading is the one thing to check before reaching for this
pattern. A requirement that holds only some of the time is one of the four
patterns below with its gating clause left off, and dropping that clause does
not make the requirement simpler -- it makes it false.

### Event-driven requirements

A response the system makes once a triggering event is detected. `WHEN` marks
the trigger, and the requirement is about the transition rather than about the
situation that follows it.

```
WHEN <trigger> THE <system name> SHALL <system response>
```

Example:

```
WHEN CONTINUOUS IGNITION IS COMMANDED BY THE AIRCRAFT THE CONTROL SYSTEM SHALL SWITCH ON CONTINUOUS IGNITION.
```

The trigger is a discrete event -- something that happens at a moment -- and
that is the whole of the distinction from the state-driven pattern below. "The
user submits the form" is an event; "the user is logged in" is a state, and the
second one written after `WHEN` produces a requirement that appears to fire
once where it was meant to hold throughout.

### State-driven requirements

Behaviour that holds for as long as the system is in a named state. `WHILE`
marks the state, and the response is continuous: it starts when the state is
entered and stops when the state is left.

```
WHILE <state> THE <system name> SHALL <system response>
```

Example:

```
WHILE THE AIRCRAFT IS IN FLIGHT THE CONTROL SYSTEM SHALL MAINTAIN ENGINE FUEL FLOW ABOVE THE MINIMUM FLIGHT IDLE RATE.
```

The paper permits `DURING` in place of `WHILE` where that reads better. It is a
readability alias and nothing more: the pattern is the same one and the
`Pattern` cell reads state-driven either way. Naming a state a reader can
evaluate matters more than the choice between the two words, because a state
nobody can tell the system is in cannot settle whether the requirement applies.

### Unwanted behaviour requirements

What the system does about situations nobody wants: invalid input, failures,
timeouts, lost signals, disturbances. `IF` marks the unwanted trigger and
`THEN` opens the response, and both are required -- the pair is what keeps the
situation and the system's answer to it in separate clauses.

```
IF <unwanted trigger> THEN THE <system name> SHALL <system response>
```

Example:

```
IF THE COMPUTED AIRSPEED IS UNAVAILABLE THEN THE CONTROL SYSTEM SHALL USE MODELLED AIRSPEED.
```

The notation gives unwanted behaviour a pattern of its own because it is the
category authors omit: the wanted path gets written and the failure path gets
discovered in testing. So this pattern reads as a prompt as much as a grammar.
For each requirement written in one of the other four, the question it asks is
what the system does when that trigger or that state fails to arrive.

An unwanted trigger is still a trigger, so the sentence says what the system
does about the situation and not that the situation is forbidden. "The system
shall not lose the airspeed signal" constrains the world rather than the
system, and nothing can be built to satisfy it.

### Optional feature requirements

Behaviour that exists only in some builds, configurations or variants of the
product. `WHERE` marks the feature whose presence the requirement depends on.

```
WHERE <feature is included> THE <system name> SHALL <system response>
```

Example:

```
WHERE THE CONTROL SYSTEM INCLUDES OVERSPEED PROTECTION THE CONTROL SYSTEM SHALL TEST THE AVAILABILITY OF OVERSPEED PROTECTION ON START-UP.
```

The condition is the product having the feature at all, not anything happening
at run time. A feature every build ships is not optional and its requirements
are ubiquitous ones; a feature a user turns on is a state. This pattern earns
its keyword only where two versions of the product genuinely differ.

### Complex requirement syntax

Preconditions and triggers combine. `WHERE`, `WHILE` and `WHEN` can appear in
one sentence, and any of them can precede an `IF` and `THEN` requirement, which
the paper covers as complex requirement syntax rather than as further patterns:

```
WHILE <state> WHEN <trigger> THE <system name> SHALL <system response>
WHERE <feature is included> WHILE <state> IF <unwanted trigger> THEN THE <system name> SHALL <system response>
```

Example:

```
WHILE THE AIRCRAFT IS IN FLIGHT IF THE COMPUTED AIRSPEED IS UNAVAILABLE THEN THE CONTROL SYSTEM SHALL USE MODELLED AIRSPEED.
```

This is a composition rule over the five patterns above, not a sixth pattern.
It licences no keyword of its own, so there is nothing extra to learn and
nothing new to classify a sentence as: the `Pattern` cell names every pattern
the sentence combines, in the order the clauses appear. A cell reading
"complex" would hide which patterns those were from the one reader who has to
check them.

Clause order follows the generic form -- preconditions first, feature before
state, and the trigger last. That order is not a style preference: swapping a
state clause and a trigger changes which of the two gates the other.

A sentence needing three preconditions is usually the point to stop. The
notation permits it, but compound requirements are one of the problems the
notation exists to expose, so a long clause stack is worth re-reading as two
requirements that were written as one.

## The quality characteristic checklist

The nine quality characteristics of ISO/IEC 25010:2023, whose product quality
model this file borrows as its enumeration of the non-functional. The
standard's clause 1 states the model has nine characteristics, each further
subdivided into subcharacteristics, and all nine are below in the order the
model presents them.

They are here because the non-functional surface is the part of a product
nobody recalls in full. A missing function is missing to somebody: they wanted
the behaviour and cannot find it. A missing quality requirement is missing to
nobody until the product is in front of a user who is not getting something
that was never written down. Working through a fixed list makes that surface
enumerable rather than whatever the author happened to think of.

Each characteristic below is a question, and answering it means resolving it to
exactly one of three outcomes:

- **A requirement** under `### Non-functional requirements`, carrying a
  threshold and, in `Source`, where the threshold came from.
- **An exclusion** under `### Quality characteristics not applicable`, with a
  one-line justification a reader could disagree with.
- **The unknown marker** in place of the figure, where the characteristic
  applies but nobody has established a threshold for it yet. The token and its
  payload rules are defined by
  `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
  which is the only place they are written out; copy the literal from there
  rather than reconstructing it.

A threshold with no source is not a fourth outcome. It is the first outcome
with the part that makes it defensible left off, and it is the shortcut worth
naming because it is the one an author under time pressure reaches for: a
figure nobody can attribute cannot be revised later on purpose, only argued
about. Where the number is not known, the marker is the honest answer and the
requirement waits for it.

Silence is not a fourth outcome either. A characteristic somebody read, thought
about and left alone looks exactly like one nobody reached, and these three
outcomes exist to tell those apart. A checklist with a hole in it is worse than
no checklist, because the hole reads as completeness.

The subcharacteristic glosses below are paraphrase, not quotation. They are
written to make each prompt answerable without the standard in hand, and the
standard's own clause 4 definitions were not read while this file was written,
so a wording that has to carry weight -- in a certification argument, or in a
contract -- belongs checked against ISO/IEC 25010:2023 itself rather than
against this list.

### Functional suitability

Does the product do what it is for, correctly, and in a way that fits the task
the user arrived with?

- *Functional completeness* -- the functions cover every task and user
  objective the product claims.
- *Functional correctness* -- the results are right, to the precision the task
  needs.
- *Functional appropriateness* -- the functions make the task easy to
  accomplish rather than merely possible.

This is the one characteristic that overlaps `### Functional requirements`, and
the overlap is not a duplication. What the system does belongs there; how
completely, how correctly or how directly it does it is a threshold, and
thresholds belong here.

### Performance efficiency

Under the load the product is expected to carry, how fast is fast enough, and
what does it consume to get there?

- *Time behaviour* -- response, processing and throughput figures.
- *Resource utilization* -- how much CPU, memory, storage and bandwidth are
  used while doing it.
- *Capacity* -- the maximum limits the product is built to reach: users,
  requests, records, connections.

A performance threshold with no load condition attached is not yet a
threshold. "Responds in 200ms" is satisfiable by one user on an idle machine
and says nothing about the case anyone cares about, so the condition the figure
holds under belongs in the requirement sentence.

### Compatibility

What else does this product have to live alongside or exchange information
with?

- *Co-existence* -- it shares an environment with other products without
  degrading either.
- *Interoperability* -- it exchanges information with named other products and
  uses what it receives.

### Interaction capability

Can the people who have to use this product work out how, and does it hold up
for the ones who do not use it the way its designer imagined?

- *Appropriateness recognizability* -- a user can tell whether the product
  fits their need.
- *Learnability* -- a user can learn to use it, to a stated level, in a stated
  time.
- *Operability* -- it is easy to operate and to control once learned.
- *User error protection* -- it prevents errors, or catches them before they
  cost anything.
- *User engagement* -- the interaction is pleasant and satisfying to continue.
- *Inclusivity* -- people across the range of ages, cultures, languages and
  abilities in scope can use it.
- *User assistance* -- users with the widest range of needs can achieve their
  goals, with help available where they need it.
- *Self-descriptiveness* -- the product explains itself, without a reader
  having to go elsewhere.

The longest list of the nine, and the one most often disposed of in a single
line. A product with no human interface can rule the whole characteristic out
-- "no user interface exists" is a reason a reader can check -- but ruling it
out is still a decision that gets written down, and a product with any
interface at all owes each of the eight an answer.

### Reliability

When it is meant to be working, is it, and what happens the rest of the time?

- *Faultlessness* -- it operates without fault under normal use.
- *Availability* -- it is operational and accessible when required, to a stated
  figure.
- *Fault tolerance* -- it keeps operating as intended despite faults in
  hardware or software.
- *Recoverability* -- after a failure it recovers the data affected and
  re-establishes the state, within a stated time.

### Security

What is being protected here, from whom, and how would anybody know afterwards?

- *Confidentiality* -- data is accessible only to those authorised to have it.
- *Integrity* -- unauthorised modification of code or data is prevented.
- *Non-repudiation* -- actions and events can be proven to have happened, so
  they cannot later be denied.
- *Accountability* -- an action can be traced to the entity that took it.
- *Authenticity* -- an identity or a resource can be proven to be the one
  claimed.
- *Resistance* -- the product keeps operating while under attack.

Security is where implementation detail smuggles itself in most easily. A row
requiring a named library, algorithm or vendor has stated a mechanism rather
than a property, and the property is what a reviewer can still judge once the
mechanism is replaced.

### Maintainability

What will it cost the next person to change this, and how will they know they
did not break it?

- *Modularity* -- the product is composed of parts a change can be confined
  to.
- *Reusability* -- assets can be used in more than one system.
- *Analysability* -- the effect of a change, or the cause of a failure, can be
  determined.
- *Modifiability* -- it can be changed without introducing defects or
  degrading quality.
- *Testability* -- criteria can be established for the product and tests run
  against them.

### Flexibility

What has to be able to change about the environment, the scale or the
deployment without the product being rewritten?

- *Adaptability* -- it adapts to different or evolving hardware, software and
  usage environments.
- *Installability* -- it can be installed and uninstalled successfully in its
  target environment.
- *Replaceability* -- it can replace another product serving the same purpose.
- *Scalability* -- it handles growing or shrinking workloads, or growth in its
  own capabilities.

### Safety

Could this product, working exactly as specified, contribute to harm to a
person, to property or to the environment?

- *Operational constraint* -- operation is constrained to safe parameters or
  states when a hazard is encountered.
- *Risk identification* -- courses of events that could expose life, property
  or the environment to unacceptable risk are identified.
- *Fail safe* -- on failure, the product reverts automatically to a safe
  condition.
- *Hazard warning* -- unacceptable risks are signalled in time for an operator
  to react.
- *Safe integration* -- safety is maintained during and after integration with
  other components.

Safety is the one characteristic the unknown marker cannot dispose of.
Declaring it out of scope takes a stated reason about this product, because
nothing in the standard or its commentary treats safety as normally
inapplicable -- the commentary runs the other way, that safety is reaching
products well outside the traditionally safety-critical industries. So the
marker, which says a threshold is not yet established, is not available here as
a way of saying the question does not arise.

Safety's five glosses are the weakest in this file, and weaker in a way the
paraphrase note above does not cover. The other eight characteristics were
glossed from sources that set a characteristic's subcharacteristics out as a
set, and that agree with each other on the set. These five were assembled from
scattered commentary that no one source presented together. So they are good
enough to ask the question with and not good enough to answer it against: check
them in the standard before any of them reaches a safety case.

## The INVEST gate

The last read a requirement gets before it ships, and the only one that is about
how the requirement will be delivered rather than about what it says. The
notation decides whether a sentence is well formed; the checklist decides
whether the non-functional surface is covered; this decides whether a
requirement somebody is going to build is one piece of work. It is Bill Wake's
six criteria, published in 2003 as *INVEST in Good Stories, and SMART Tasks*,
each condensed here to a line from his own wording:

- **Independent** -- it does not overlap another requirement in concept, so the
  two can be scheduled and implemented in either order.
- **Negotiable** -- it fixes what is wanted, not a contract for features: the
  details are co-created by the customer and the developer during the work.
- **Valuable** -- the value is value to the customer specifically, not to just
  anybody, so a developer's own concern belongs restated as something the
  customer would call important.
- **Estimable** -- it can be estimated closely enough to rank and schedule,
  which is a weaker thing than estimated exactly.
- **Small** -- a few person-weeks of work at the outside, which is also what
  makes the estimate above one anybody can give.
- **Testable** -- whoever wrote it understood what they wanted well enough that
  they could have written the test for it.

This section is the suite's single INVEST definition. Every other beat that
needs the criteria -- the story-slicing beat of issue #21 first among them --
cites it rather than copying it. Two copies of a six-part gate diverge one
letter at a time, and neither copy looks wrong on its own.

A requirement is story-shaped when a downstream beat could cut it into one
deliverable unit: something a team builds, demonstrates and finishes. The gate
runs on those, and only on those. Most requirements in a member are not
story-shaped -- a latency threshold, a retention limit and a casing rule are all
requirements that nobody delivers as a piece of work -- and a requirement that
is not story-shaped is exempt from the gate rather than failing it.

Writing that exemption down is not a courtesy to the author. An exemption nobody
recorded reads as an oversight, and the next reader's fix for an apparent
oversight is to run all six criteria over everything: a threshold then fails
Small for not being a story it never claimed to be, and the honest answer is to
rewrite it as one, which is how a requirement acquires an implementation it did
not need.

## Scope

What every requirement below is about, and which of `discovery.md`'s
opportunities they are answerable to. Both are written before any requirement,
because both are what a requirement is read against.

### The system name

One name, written once, for the thing being constrained. Every requirement
below names it in the same words.

| The system | Where the name comes from |
|---|---|
| `<the one name every requirement below uses for the thing being built>` | `<the brief, the discovery outcome, or whoever named it>` |

Naming it here rather than per requirement is not tidiness. Each requirement
sentence has a slot for the system it constrains, and a member that fills that
slot inconsistently -- "the service", "the platform", "the API" -- produces
requirements that read as though they constrain three different systems, which
is invisible in any one row and obvious only in aggregate.

Sub-systems are named here too if requirements below constrain them
individually. What is not permitted is a requirement naming a system this
section does not.

### Opportunity coverage

One row per `OPP` id in `discovery.md`, whether or not it produced a
requirement. The table is the member's backward traceability: a requirement
naming its opportunity proves that requirement did not come from nowhere, and
says nothing at all about an opportunity that quietly produced nothing.

| Opportunity | Covered by | Note |
|---|---|---|
| `OPP1` | `<the REQ ids covering it, or the literal: not addressed>` | `<what the requirements do about it -- or, when it is not addressed, the same reason recorded under Opportunities not addressed below>` |

`Covered by` has exactly two permitted forms: one or more `REQ` ids, or the
literal `not addressed`. A blank cell is not a third form. An empty cell means
either that nobody wrote a requirement or that nobody filled in the table, and
the whole point of the row is to tell those two apart.

Every `OPP` id from `discovery.md` appears here exactly once, including the
ones nothing was written for. Listing only the covered ones would make the
table an index of the requirements rather than a check on them.

## Requirements

The requirements themselves, split by what they constrain: behaviour in the
first subsection, quality attributes in the second. The split is by subject
only. Both subsections use one notation and one table, so a reviewer judges
every row against the same grammar.

Both tables declare the same five columns, and what each column holds is
defined here once rather than in either subsection:

- **ID** -- the requirement's `REQ<n>` id, as described above.
- **Pattern** -- which requirement pattern the sentence is written in, spelled
  as `## The EARS notation` spells it, so that a mis-typed sentence is visible
  next to the sentence itself.
- **Requirement** -- the requirement, written in full in the notation and in
  the casing it mandates. This is the normative cell; every other column is
  about it.
- **Traces to** -- what the requirement answers to: one or more `OPP` ids
  from `discovery.md`, or, for a requirement produced by the quality
  characteristic checklist rather than by an opportunity, the name of that
  characteristic. Never blank, for the same reason `Covered by` is never
  blank.
- **Source** -- where the requirement's content came from: the upstream
  member, a named person, a standard, or a measured figure's origin. A
  threshold with no source is not a requirement anyone can defend.

The two subsections repeat the header row because a markdown table cannot
inherit one. They are not two declarations of the columns: the definitions
above are the only ones, and a subsection that starts meaning something
different by a column has diverged from this file rather than extended it.

### Functional requirements

What the system does, one row per requirement.

| ID | Pattern | Requirement | Traces to | Source |
|---|---|---|---|---|
| `REQ1` | `<the pattern the sentence below is written in>` | `<the requirement, written in the notation>` | `<one or more OPP ids>` | `<where its content came from>` |

One requirement per row, and one requirement per sentence. A row joining two
demands with "and" is two requirements that will be cited, tested and
satisfied separately, and nothing downstream can split them back apart once
they share an id.

### Non-functional requirements

What the system must be like while it does it: one row per quality attribute
being constrained, in the same table and the same notation as above.

| ID | Pattern | Requirement | Traces to | Source |
|---|---|---|---|---|
| `REQ2` | `<the pattern the sentence below is written in>` | `<the requirement, naming the quality characteristic it constrains and the threshold that settles it>` | `<one or more OPP ids, or the quality characteristic this answers>` | `<where the threshold came from>` |

A non-functional requirement without a threshold is a preference. "The system
shall be fast" cannot be passed or failed; a figure, a unit and the condition
it holds under can. The threshold's origin belongs in `Source`, because a
number nobody can attribute is one nobody can revise later on purpose.

## Out of scope

What this member deliberately does not require, and why. This section is what
makes the two lists above readable as complete: an opportunity or a quality
characteristic that is missing from them is either recorded here with a reason
or is an omission, and without this section those two are the same thing.

Nothing arrives here by being forgotten. A line here is a decision someone
made, written in the same member as the requirements it is the counterpart to.

### Opportunities not addressed

One row per opportunity whose `Covered by` cell reads `not addressed`, and the
reason it does.

| Opportunity | Reason it is not addressed |
|---|---|
| `OPP2` | `<why no requirement answers it: out of this release, superseded, not worth it, or blocked on something named>` |

The two lists are kept in step by construction: every `not addressed` in the
coverage table has a row here, and every row here reads `not addressed` there.
A reason recorded only here leaves the coverage table looking incomplete, and a
`not addressed` recorded only there is the silent drop this section exists to
prevent.

"Not yet decided" is not a reason. An opportunity nobody has ruled on has not
been placed, and the honest form of that is the suite's unknown marker in the
coverage table's note rather than an exclusion nobody agreed to.

### Quality characteristics not applicable

One row per quality characteristic that this product is not being held to, and
why not.

| Quality characteristic | Why it does not apply |
|---|---|
| `<the characteristic's name>` | `<what about this product makes it inapplicable, stated as something a reader could disagree with>` |

A characteristic is inapplicable because of something true about this product,
not because nobody got to it. "No user interface exists, so there is nothing
for a user to learn" is a reason a reader can check and contest; "not relevant
here" is the absence of one.
