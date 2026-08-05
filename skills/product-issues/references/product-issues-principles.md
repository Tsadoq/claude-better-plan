# Product issues principles

## Attribution and scope

Four sources stand behind the questions below, and every one of them is cited
for something narrower than what is built on it. What each supports and what it
does not is recorded here because the gap between the two is where most of this
file comes from, and a reviewer who mistakes an extension for a quoted authority
will defend it on grounds it does not have. This project is not affiliated with
or endorsed by Alistair Cockburn, by Jeff Patton, by Mike Cohn, by Bill Wake, by
Henrik Kniberg, or by any other author cited here.

- **Mike Cohn, for SPIDR.**
  `mountaingoatsoftware.com/blog/five-simple-but-powerful-ways-to-split-user-stories`,
  which is the live URL: the one issue #21 carried is dead. The article supplies
  five patterns for splitting a story well -- Spike, Path, Interface, Data,
  Rules -- and supplies no diagnosis of a bad split, so no question below may be
  cited to it. It also does not call a spike a last resort; it says a spike
  normally will not be the first technique reached for, and produces knowledge
  that helps develop the functionality later.
- **Jeff Patton, for the backbone and for how a release row runs.** "The new
  backlog", for "backbone" as the term for user activities, and for the guidance
  this file's second cluster is built on: a release row moves across the whole
  backbone rather than completing one column of it.
- **Alistair Cockburn, for the walking skeleton and for elephant carpaccio.**
  Both are named here on secondary attribution only. Patton credits the walking
  skeleton to Cockburn explicitly, on his own site, with the same meaning it
  carries here. Cockburn's own page returned 404 in research and elephant
  carpaccio was confirmed from secondary sources alone, with Kniberg's
  facilitation guide as the canonical write-up of the exercise. Nothing below
  quotes Cockburn, and nothing may start to.
- **Bill Wake, 2003, for INVEST.** Cited for the acronym and its authorship,
  which is worth stating because INVEST is frequently misattributed to Cohn.
  The gate itself is not restated here; see the boundaries below for the file
  that owns it. Wake's same article coins SMART, which is about tasks rather
  than stories and is easy to blend with INVEST -- they are two acronyms from
  one author about two different things.

Five things below reach past those sources, and each is recorded so a reader can
tell which part of a question they are being asked to accept:

- **All four clusters are this project's own.** SPIDR is a set of splitting
  patterns and not a list of failure modes; the walking skeleton is a thing to
  build and not a thing to review; INVEST is a gate on one story and says
  nothing about a set of them. Turning any of that into a question a critic
  answers against written files is this file's work, and each cluster is as
  strong as its own reasoning rather than as strong as the author it borrows
  vocabulary from.
- **That a layer split is the *default*.** The first cluster rests on an
  observation with no source at all: architectural layers are the most legible
  structure in any codebase, so they are what a splitter -- and especially a
  model -- reaches for first. Cohn nowhere says this. It ships as this project's
  own claim, and the questions are written so they catch the shape whether or
  not the claim about its cause is right.
- **The walking skeleton swallowing the release.** Patton's guidance about
  release rows is the source for what a good row looks like. The failure mode
  named in the second cluster -- every slice landing in row one and the first
  demoable increment sliding to the end -- is this file's reading of what goes
  wrong when that guidance is not followed, and neither author describes it.
- **`### Slices with no upstream basis` has no methodological source.** It
  enforces this chain's own rule, that a slice descends from a scored roadmap
  item, and would be meaningless in a project that cuts work some other way.
- **Elephant carpaccio and the story-splitting flowcharts are plan-time advice
  and ship as nothing else.** Neither is a template here. The carpaccio exercise
  is a facilitated workshop, and a template of its steps would be a schedule for
  a session nobody is running. The flowcharts that circulate as posters were not
  traced to a primary source in research, so this file names the technique and
  cites nobody for it -- an uncited pattern is honest, an invented attribution is
  not.

Scope: this file is the single source of truth for judging a written slice set
under `docs/product/<slug>/issues/` -- whether the cuts follow use rather than
architecture, whether anything can be demonstrated early, whether each slice
descends from something upstream, and whether one of them could be picked up
alone. It is not the slice set's shape. Three boundaries keep it from restating
its neighbours:

- **Judgement, not shape.** The backbone, the test row one must pass, the SPIDR
  patterns, the slice frontmatter keys and the six body sections are published
  by
  `${CLAUDE_PLUGIN_ROOT}/skills/product-issues/references/story-map-template.md`.
  The chain, the provenance line and the suite's single unknown-value marker are
  published by
  `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`.
  The INVEST gate belongs to
  `${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/requirements-template.md`
  under `## The INVEST gate`. A question below may name a section, a key or the
  marker; it never redefines one, and this file nowhere spells the marker's own
  token or the six INVEST letters.
- **The slices, not the roadmap.** Which items were worth building, and in what
  order, was decided upstream. A slice whose `roadmap_item` names nothing is
  reported here; whether that item deserved its score or its position is judged
  by
  `${CLAUDE_PLUGIN_ROOT}/skills/product-roadmap/references/product-roadmap-principles.md`
  against the member that owns it, and a fault found in a carried id is a
  `product-roadmap` re-run rather than an edit here.
- **The written set, not the tracker.** The evidence a reviewer has is the
  markdown. A finding says a slice failed to establish something; it never says
  which slice should have come first, and it never supplies the slice that is
  missing. Whether filing worked, what got created, and what a second run skips
  are the filing script's concern and are not judged here.

Orchestrators quote one section, or one H3 cluster, into an agent prompt;
nothing here is duplicated elsewhere.

## Plan-time principles

These act while the slice set is being cut. Each pulls against something that
feels like diligence at the time, which is why they are worth stating rather
than trusting.

- **Cut past the point where it feels silly.** This is the discipline elephant
  carpaccio teaches, and the only part of it that travels outside a workshop: a
  slice that still reads as reasonable is usually two slices whose join nobody
  has looked at. The exercise is Cockburn's, with Kniberg's facilitation guide as
  the canonical write-up, and it is a session with a facilitator rather than
  anything this beat can hand you. Run it if you can; if you cannot, keep the
  one habit -- when a slice contains an "and", it is a candidate, and the second
  cut is nearly always cheaper than the first.
- **Reach for a flowchart when the split will not come, not before.** The
  story-splitting flowcharts are a prompt for a stuck author: they ask whether
  the story has multiple paths, multiple data types, multiple rules, and hand
  back a cut. That is what they are good for. They are not a specification, none
  is shipped here, and this project cites no primary source for them because
  research found none it could stand behind. A cut you can explain in your own
  words beats one you can only justify by naming the box it came out of.
- **Name the activity a slice serves before you name the code it touches.** In
  that order the layer split cannot form, and in the other order it is already
  made: the parts of the system are written down and the parts of somebody's day
  are not, so whichever you reach for first is the one you will cut along.
- **Row one is a demonstration, not a milestone.** Everything you add to it is
  defensible on its own and the row is what pays for the feedback. Ask the row-
  one test the template publishes before each addition, and when the answer is
  that the thing already passes, the addition belongs in a later row.
- **Name the roadmap item while you are still holding it.** A slice records the
  item it was cut from at the moment of cutting or never: an hour later the
  basis is a reconstruction, and reconstructed bases are how work nobody scored
  enters a set looking exactly like work somebody did.
- **Write the acceptance criteria for a reader who was not there.** At cutting
  time every omission is filled in by the conversation in the room, which is the
  one thing that will not be attached to the issue. If a criterion needs you to
  explain it, it is not written yet.
- **Say what is out of scope, specifically.** A slice is defined as much by the
  adjacent work a reader would otherwise assume is included. General disclaimers
  exclude nothing; naming the neighbouring slice does.

## Review-time red flags

Each cluster below is quoted verbatim into one critic. Every question is
answerable yes or no against a written slice set; "yes" is a finding. Severity
hints are defaults -- a critic may upgrade or downgrade with evidence. Cite the
slice file, and the section or frontmatter key inside it: a finding the author
cannot locate in their own files is not actionable.

The four paragraphs that follow are preconditions for the questions rather than
an introduction to them: what a critic is given, where the definitions live, and
which observations are not findings. Two clusters cannot be answered correctly
without them, so a caller that quotes a cluster carries this preamble with it or
names this file so the critic reads it -- and a critic that was handed neither
should say so rather than answer anyway.

A critic is handed the whole set rather than one file. Several questions below
are only answerable read across it -- whether one release row holds everything,
whether two slices split one behaviour, whether an item is covered at all -- and
a review that reads slice by slice will pass every one of them.

Several questions turn on a definition this file does not hold: the backbone and
the `activity` axis that carries it, the test row one has to pass, how the
release-row axis is expressed at all, which frontmatter keys are required and
which are optional, the id form, and what each body section is for. None of them
is written out below. `## Attribution and scope` names the
template that fixes all of them and is the only place any of them is defined;
open it rather than assuming a value, because a question that had restated one
would go on asking about the old definition for as long as it took anybody to
notice.

Two things are not findings on their own, unless a question says otherwise. A
slot carrying the suite's unknown marker is the beat doing its job and reporting
what nobody established. A `filed_<destination>` entry is a record that filing
happened; it says nothing about whether the slice was worth filing, and a set
that is already in a tracker is judged exactly as one that is not.

The first two clusters ask about the cut and the last two about what a reader
gets. The cut is where the expensive failures are: a set of individually
well-written issues that partitions the codebase by layer passes every question
in the fourth cluster and is still unusable as a plan.

### The horizontal or layer slice

Architectural layers are the most legible structure in any codebase, so they are
the split that arrives first: a schema slice, an API slice, a UI slice. Each is
a unit of work and none is a unit of use. The set looks complete, the estimates
look sound, and nothing in it can be demonstrated until the last piece lands --
which is also the first moment anybody could have given feedback worth acting
on.

SPIDR is Cohn's and describes how to split well; it carries no diagnosis of a
bad split, and no question here may be cited to it. That layers are the default
a splitter reaches for is this project's own claim.

- Does any slice's title name a layer, a tier or a component -- a schema, an
  endpoint, a service, a screen, a migration -- rather than something a person
  can do?
  Severity hint: material.
- Is any `## Acceptance criteria` section written entirely in terms nobody
  outside the team could observe -- a table exists, a route responds, a module
  imports?
  Severity hint: material.
- Do two or more slices split one user-visible behaviour between them, so the
  behaviour appears only when the last of them lands?
  Severity hint: material.
- Does any slice's `## Deliverables` partition the codebase rather than the
  behaviour, the slice owning a directory or a layer and no outcome?
  Severity hint: material.
- Does any slice justify itself only by the slice it unblocks, without being
  identified as a spike -- the one SPIDR pattern the template allows to produce
  something other than working software?
  Severity hint: material.
- Is the set orderable in exactly one sequence, each slice blocked by the one
  before it, so nothing in it could ship early or be dropped?
  Severity hint: material.
- Does any slice's `activity` name a part of the system rather than one of the
  backbone activities the story map holds?
  Severity hint: minor, material where more than one slice does it.

### The walking skeleton that swallowed the release

Row one is meant to be the thinnest end-to-end path through the backbone, and it
attracts everything. Each addition is defensible by itself -- it is obviously
needed for the thing to be usable -- so the row that was supposed to be
demonstrable in days becomes the release, and the first increment anybody could
react to is now at the end of it. The set shows it plainly: row one grows, the
later rows thin out.

Patton is the source for how a release row runs, across the whole backbone
rather than completing one column, and he credits the walking skeleton to
Cockburn. Cockburn's own page was unreachable in research, so nothing here
quotes him. The failure mode itself is this file's reading and is neither
author's.

- Does row one hold every slice in the set -- no later row expressed at all --
  while the set is large enough that nothing in it could be demonstrated until
  the last slice lands? A small single-row set is what the template expects and
  is not this finding.
  Severity hint: material.
- Does row one complete some backbone activities in depth while leaving others
  with no slice at all, so what is called a row is a column?
  Severity hint: material.
- Is any row-one slice's `## Acceptance criteria` written for the finished
  behaviour rather than for the pass the template's row-one test asks for?
  Severity hint: material.
- Does the earliest demonstrable slice sit behind a chain of `## Blocked by`
  entries, so nothing can be shown until most of the set has landed?
  Severity hint: material.
- Does row one carry a slice whose value is robustness, scale, permissions or
  polish -- work that improves a path rather than establishing one?
  Severity hint: material.
- Is row one described as a minimum viable product, two things the template
  keeps deliberately apart?
  Severity hint: material.
- Do the later rows hold materially fewer slices than row one, so the set
  front-loads everything and has nothing left to sequence?
  Severity hint: minor, material where a later row is empty.

### Slices with no upstream basis

The set descends from a roadmap that already decided what is in scope and in
what order. A slice carrying no roadmap item is not a smaller piece of that
decision -- it is a new decision, taken by whoever was cutting, and on the page
it is indistinguishable from the rest. The failure is cheap to make: a slicing
conversation surfaces obvious work nobody scored, and obvious work is exactly
what gets added.

This cluster has no methodological source. It enforces this chain's own rule and
would mean nothing in a project that cuts work some other way.

- Does any slice carry no `roadmap_item`, or one whose id no row of the roadmap
  holds?
  Severity hint: material.
- Does any slice's `## References` omit the roadmap blob sha it was cut from, so
  nobody can tell which version of the roadmap it descends from?
  Severity hint: material.
- Do the slices of one roadmap item, taken together, deliver something that item
  did not ask for?
  Severity hint: material.
- Is any sequenced roadmap item covered by no slice at all while items below it
  are covered, so the set skipped one without saying so?
  Severity hint: material.
- Does any slice's `## Context` supply a justification of its own -- a customer
  request, an escalation, a bug someone filed -- instead of pointing at the item
  that carries the basis?
  Severity hint: material.
- Does the set cite more distinct roadmap items than the roadmap's own sequence
  holds, so an item was named to give a slice a basis rather than read off one?
  Severity hint: material.
- Does any slice cite the roadmap as a whole rather than one item, so the basis
  is the document and not a decision inside it?
  Severity hint: minor.

### The issue body that cannot be picked up alone

Every slice becomes an issue somebody opens on its own, days later, with the
conversation that produced it gone. The test is not whether the body is complete
but whether it is self-contained: can an implementer holding this file and the
repository start? The failure is invisible at authoring time, because everything
the body leaves out is in the room while it is being written.

INVEST is Wake's, 2003, and is frequently misattributed to Cohn. The gate itself
lives in the requirements template named in `## Attribution and scope`; the
questions here apply it one slice at a time and never restate it.

- Does any body refer to a decision, a conversation or a document it does not
  name, so a reader has to find out who was in the room?
  Severity hint: material.
- Is any `## Acceptance criteria` entry unverifiable -- no observable outcome,
  or an outcome only its author could judge?
  Severity hint: material.
- Does any slice depend on another and say so nowhere in `## Blocked by`?
  Severity hint: material.
- Do two slices carry the same id, or does any `## Blocked by` entry name an id
  no slice in the set holds, so a reader cannot resolve what they are waiting
  for?
  Severity hint: material.
- Does any `## Deliverables` list read as a project rather than a slice --
  several separable outcomes, each of which could have been cut out on its own?
  Severity hint: material.
- Does any title mean nothing outside its own row -- "part 2", "the rest of it",
  "follow-up" -- so an issue in a tracker names no change anybody receives?
  Severity hint: material.
- Does any body carry a placeholder, a to-be-decided, or a heading the template
  supplied and nobody filled in?
  Severity hint: material.
- Does `## Out of scope` disclaim in general terms without naming the adjacent
  work a reader would otherwise assume was included?
  Severity hint: minor.
- Does any `## References` section point only at the roadmap, leaving the
  implementer nothing about the code they are about to change?
  Severity hint: minor.

## How to update these guidelines

The four H2 headings above, and the *number* of H3 clusters under "Review-time
red flags", are pinned by
`skills/product-issues/tests/test_product_issues_contract.py`, which requires at
least four. Renaming a section breaks a caller that quotes it
by name, and the cluster count is how wide a review fans out -- one finder per
cluster -- so adding or removing one changes what a review costs and what goes
unasked, and the test and every caller change in the same commit.

Each bullet in a cluster is one question and one `Severity hint:` line beneath
it. A critic is handed one cluster's questions and this file's path, and nothing
else: prose inside a cluster gives it nothing to answer, and a hint sitting under
anything but a question routes a finding nobody asked for. Rewriting a question
as a statement is therefore a change to what the fleet does, not a change of
style. The preamble above the first cluster is the exception a maintainer has to
respect -- it carries preconditions two clusters need, which is why it says so
in its own first paragraph rather than leaving a caller to guess that quoting a
cluster alone is enough.

This file nowhere spells the suite's unknown-marker token, and nowhere spells
the six INVEST letters. Both live in the contracts named in `## Attribution and
scope`, and the same contract test checks that no file this skill ships
introduces a second marker token beside the substrate's.

One thing a maintainer meets immediately: **`product-review` selects this rubric,
and what makes it selectable is a row in another file.** That skill composes a
rubric path from the `Owning skill` column of the artifact-family contract, and
the chain is still closed at five members none of which is a slice set --
`product-issues` writes a subfolder, not a sixth member. What reaches this rubric
is instead that contract's `## Non-member artifacts` table, whose `Folder` column
carries the subfolder and whose `Owning skill` column names the beat the path is
composed from; `product-review` enumerates from the `Folder` column, which is the
difference between a path that could be composed and a target anything actually
picks up. Both halves are pinned in
`skills/product-review/tests/test_product_review_contract.py`:
`test_rubric_template_derives_every_shipped_principles_file` checks the first and
`test_skill_publishes_its_runtime_rules` the second. Delete that row, or stop
enumerating from it, and one of those two reports it. The fix to refuse is
unchanged should reachability ever break again: renaming this file out of the
first test's glob silences its report and selects nothing.

Two things are deliberately unpinned, and a maintainer should know which before
trusting a green suite:

- **The cluster names.** Renaming one, or replacing all four with four others of
  the same shape, is a green suite and a judgement call. The names are prose a
  reader reviews.
- **The arguments, as opposed to the citations.** The five recorded extensions,
  the reason no flowchart and no carpaccio template ships, and every plan-time
  principle are held by review alone. A token is checkable and an argument is
  not, and pinning sentences would freeze wording that ought to improve -- so a
  caveat deleted from an extension still goes unnoticed by the suite. That is
  the one place this file's honesty rests on a reader rather than a test.

The files that quote sections of this file are:

- `skills/product-issues/SKILL.md` (cites this file by `${CLAUDE_PLUGIN_ROOT}`
  path as the rubric a slice set is cut against, and restates no cluster)
- `skills/product-review/SKILL.md` (one finder per red-flag cluster, quoted
  verbatim)

This file cites four others and copies none.
`${CLAUDE_PLUGIN_ROOT}/skills/product-issues/references/story-map-template.md`
owns the backbone, the row-one test, the SPIDR patterns, the slice frontmatter
keys and the six body sections;
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
owns the chain, the provenance line and the unknown marker;
`${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/requirements-template.md`
owns the INVEST gate; and
`${CLAUDE_PLUGIN_ROOT}/skills/product-roadmap/references/product-roadmap-principles.md`
owns every judgement about the roadmap this set descends from. On disagreement,
those files win and a question here is the thing that changes.
