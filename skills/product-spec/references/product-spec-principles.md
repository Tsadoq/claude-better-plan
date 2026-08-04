# Product spec principles

## Attribution and scope

Three sources stand behind the questions below, and each is cited for something
narrower than the questions built on it. What each one does and does not support
is recorded here because every one of the three is extended, and a reader who
mistakes a question for a quoted authority will defend it on grounds it does not
have. This project is not affiliated with or endorsed by 37signals, by Gregor
Hohpe, by the BMAD-METHOD project, or by any other author cited here.

- **Shape Up, for non-goals being a named slot rather than an afterthought.** Its
  definition of a no-go sits under `Ingredient 5. No-Gos` of chapter 6, "Write
  the Pitch" (`basecamp.com/shapeup/1.5-chapter-06`), one of five ingredients
  that chapter says a pitch always includes. So the slot is precedent. The
  ingredient's own wording is not: it advises mentioning exclusions if the
  concept has any, which is conditional advice rather than a rule that every
  pitch must exclude something. Requiring `## Non-goals` to be populated in every
  `spec.md`, and spending a finder on the section being empty, is this project's
  decision and is defended below on its own terms rather than by that citation.
- **Hohpe, for what makes a decision a decision.** Chapter 8 of *The Software
  Architect Elevator* is "Is This Architecture?", and its primary test is whether
  a document records nontrivial decisions together with the reasoning behind
  them. Secondary to that test is the observation that a decision whose chosen
  option had no downside was probably never a decision at all. Both properties of
  that observation survive into this file deliberately: it is the secondary test
  and not the chapter's thesis, and it says *probably*, so a cost-free exclusion
  is a question to ask an author rather than a proven defect. The chapter is
  paraphrased throughout and nowhere quoted, its text not being openly readable.
  Carrying the observation across from decisions to exclusions -- a non-goal that
  costs nothing was probably never excluded, only unwritten -- is this project's
  own extension, and `### Non-goals with no cost` is as strong as that extension
  is, not as strong as the chapter.
- **BMAD-METHOD, as precedent for a self-contained handoff artifact.** Its own
  documentation (`docs.bmad-method.org`) describes embedding context directly
  into the artifact a build agent works from instead of linking to the documents
  that context came from, which is the trade `spec.md` makes. The caveat travels
  with the citation and may not be separated from it: that self-containment is
  only partial, because the implementation agent still has PRD, architecture and
  epic context prepared for it alongside the artifact it is handed. BMAD
  therefore supports embedding over linking, and supports nothing at all about an
  artifact whose reader opens no ancestor -- which is what this member is asked to
  be, and this project's claim to defend.

Scope: this file is the single source of truth for judging a written `spec.md` --
whether a reader who opens nothing else can act on it, whether it carried its
requirements without altering them, and whether it decided its scope rather than
describing the part somebody happened to write down. It is not the document's
shape. Two boundaries keep it from restating its neighbours:

- **Judgement, not shape.** Which sections the member carries and in what order,
  the provenance line's format and where a finished one comes from, and the
  suite's single unknown-value token are published by
  `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`.
  What each section holds, the two tables' columns, the two permitted forms of an
  `Origin` cell, and the structural conventions this member deliberately does
  without belong to
  `${CLAUDE_PLUGIN_ROOT}/skills/product-spec/references/spec-template.md`. A
  question below may name a section, a column or the marker; it never redefines
  one, and this file nowhere spells the marker's own token.
- **The document, not the product.** A finding says the member failed to
  establish something. It never says the product should be built differently, and
  it never picks the mechanism whose absence it is enforcing. The evidence a
  reviewer has is the document.

A third boundary runs upstream, and it is the one most likely to be crossed by
accident. Every acceptance condition here is a sentence `product-requirements`
wrote, carried across byte for byte. Whether that sentence is ambiguous,
compound, or impossible to test is judged by
`${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/product-requirements-principles.md`
against the member that owns it, and a fault found in a carried sentence is a
re-run of that beat rather than an edit here. The questions below therefore ask
what this member did to the sentence, and never re-litigate the sentence itself.

Orchestrators quote one section, or one H3 cluster, into an agent prompt; nothing
here is duplicated elsewhere.

## Plan-time principles

These act while `spec.md` is being written. Each one pulls against an instinct
that feels like good writing at the time, which is why they are worth stating
rather than trusting.

- **Write for a reader with no history.** The test is not whether the document is
  complete but whether somebody who has never opened the brief, the discovery or
  the requirements can act on it. Restating what those three said is the work of
  this member, not a failure of concision, and a cross-reference is the one
  shortcut that destroys it.
- **Copy the condition, then stop touching it.** The sentence goes across
  unchanged, including the clauses whose order looks wrong and the punctuation
  that looks careless. Its notation puts its clauses in a fixed order, and that
  order is what makes a missing part visible, so a smoothed sentence is a
  different requirement rather than a tidier one. Paraphrasing is the degradation
  to watch for precisely because it feels like editing.
- **Buy readability where nothing can drift.** The problem and the opportunity
  are this member's own prose and are where it earns being read by a person. The
  requirement rows are not: a gloss added beside a carried condition gives one
  obligation two readings, and the shorter one wins with every reader.
- **Decide the scope, then record what deciding it cost.** Selecting which
  requirements are in scope is this beat's substantive act, and the requirements
  it left out are the evidence that a selection happened. A requirement dropped
  silently makes the in-scope table indistinguishable from a copy somebody
  abandoned halfway.
- **Prefer an exclusion somebody will resent.** The non-goals worth writing are
  the ones with a name attached: who asked for this, what the product gives up
  without it. A section filled with things nobody wanted reads as decided scope
  and is not.
- **Send mechanism downstream, including the mechanism you are sure of.** The
  obvious implementation is the tempting one to name, because naming it feels
  like saving the next reader time. It creates a second decision record, made
  earlier and on less evidence than the plan's, that no freshness check can catch
  -- both documents stay perfectly fresh and merely disagree.

## Review-time red flags

Each cluster below is quoted verbatim into one critic. Every question is
answerable yes or no against a written `spec.md`; "yes" is a finding. Severity
hints are defaults -- a critic may upgrade or downgrade with evidence. Cite the
section, and the row and cell where there is one: a finding the author cannot
locate in their own document is not actionable. A slot carrying the suite's
unknown marker is the member doing its job and is not a finding on its own,
unless a question below says otherwise.

### Named mechanism

The member's hardest rule, and the one whose violations look most helpful. This
document decides what is true of the built thing, and nothing about how it is
built; a spec that names an implementation has made that choice earlier and on
less evidence than the plan will, in a document nothing reconciles against it.

Before reporting a mechanism inside an `Acceptance condition` cell, check whether
the words are the upstream sentence. Those cells are carried byte for byte and
may not be edited here, so a mechanism that arrived with the sentence is a
`product-requirements` re-run and is reported as one. A mechanism this member
added, anywhere else, is this member's own.

- Does any section name a library, framework, language, vendor, hosted service,
  datastore or protocol?
  Severity hint: material.
- Does any section name a file, directory, module, function, class, table or
  column that would exist only once the thing is built?
  Severity hint: material.
- Does the document specify a wire format, a schema, an interface signature or a
  data model, so a shape a planner would have researched is settled here instead?
  Severity hint: material.
- Does any row prescribe an internal mechanism -- caching, queueing, retrying,
  batching, a background job -- while leaving unstated the behaviour that
  mechanism would exist for?
  Severity hint: material.
- Does the member compare two possible implementations, or record why one was
  rejected, so it is a plan wearing a spec's headings?
  Severity hint: material.
- Is the problem in `## Problem and opportunity` described in terms of what the
  current system does internally, rather than what somebody cannot do today and
  what that costs them?
  Severity hint: material.
- Does any non-goal exclude a mechanism rather than a capability -- not building a
  named component, rather than not delivering something a reader wanted?
  Severity hint: minor, material when it is the only substantive non-goal, since
  the section then records a design choice instead of a scope decision.

### Unreadable without the brief

The property the whole member exists for. Nothing downstream reads `brief.md`,
`discovery.md` or `requirements.md`, so anything this document points at instead
of stating is information its only reader does not have. The failure is invisible
to whoever writes it, because the author has just read all three.

- Does any section refer the reader to an upstream member, a ticket, an issue or
  a design document for something the reader needs in order to act?
  Severity hint: material.
- Is the problem stated only by naming it, so a reader cannot tell who has it,
  what it costs them today, or what they do instead?
  Severity hint: material.
- Is any validated opportunity present as an id and a phrase rather than restated
  in full, so what was validated has to be looked up?
  Severity hint: material.
- Does any `Traces to` cell name an opportunity id that `## Problem and
  opportunity` does not restate, leaving a requirement pointed at something this
  document never says?
  Severity hint: material.
- Does the member use a term of art, a persona name, a segment or a metric that
  it never defines and that a reader outside the chain would not know?
  Severity hint: material.
- Does any non-goal or requirement row depend on a distinction drawn upstream --
  two similar-sounding things told apart there and not here -- so the row is
  ambiguous in this document while unambiguous in the last one?
  Severity hint: minor, material where the two readings differ in scope.
- Would a reader have to open an upstream member to judge whether the problem is
  worth solving at all?
  Severity hint: material.

### Requirement without its acceptance condition

The carry itself. A requirement id in this member is a promise that the sentence
beside it is the sentence upstream; when it is not, nothing detects the
difference, because both documents are well formed and the provenance line
reports only that the upstream file has not moved.

- Is any `Acceptance condition` cell blank, or filled with a summary, a title or
  a restatement rather than the upstream sentence?
  Severity hint: material.
- Does any condition read as smoothed prose -- clauses reordered, a trigger or
  precondition folded in or dropped, punctuation or casing tidied -- so it is no
  longer the sentence that was written?
  Severity hint: material.
- Does any row carry a plain-language gloss beside its condition, giving one
  obligation two readings for a reader to choose between?
  Severity hint: material.
- Does any `ID` cell hold an identifier this member minted -- renumbered,
  re-prefixed, or resequenced into an order of its own -- so an upstream citation
  now points at a different row?
  Severity hint: material.
- Is any `Traces to` cell blank, so a requirement that answers nothing cannot be
  told apart from a column nobody finished?
  Severity hint: material.
- Do two rows carry the same id, or does one id appear in both this table and
  `## Non-goals`, so the member is building a requirement and not building it?
  Severity hint: material.
- Has an upstream sentence that reads badly been fixed here rather than reported
  as a re-run of the beat that owns it?
  Severity hint: material.
- Does any row add a qualifier, a scope note or a caveat to the condition that
  the upstream sentence does not carry?
  Severity hint: minor, material when the qualifier narrows what would be
  accepted.

### No stated non-goals

Whether the member decided its scope or only described it. This is the cheaper of
the two non-goal failures to find and the easier one to fix: the section is
missing, empty, or holds fewer decisions than the in-scope table implies were
made.

- Is `## Non-goals` absent, empty, or a table with a header row and nothing under
  it?
  Severity hint: material.
- Does any requirement id present in `requirements.md` appear in neither
  `## Requirements in scope` nor `## Non-goals`, so a requirement was dropped
  without anybody recording that it was?
  Severity hint: material.
- Does the member carry no non-goal whose origin is a deferred requirement id,
  even though the in-scope table is a selection from a longer upstream list?
  Severity hint: material.
- Does any `Origin` cell take a third form -- neither a row carried from the
  upstream out-of-scope section nor a requirement id absent from the table above?
  Severity hint: material.
- Is any `Origin` cell blank, so an exclusion one person assumed is sitting in
  the section a reader trusts to hold decisions?
  Severity hint: material.
- Is any non-goal stated as the absence of a quality -- "better performance",
  "full support", "scalability" -- rather than as something a reader could tell
  was not built?
  Severity hint: material.
- Does any non-goal restate a requirement that is also in scope, in different
  words, so the two tables disagree without sharing an id?
  Severity hint: minor.

### Non-goals with no cost

The expensive failure, and the one a full-looking section hides. A list of things
nobody wanted describes scope; a list of things somebody wanted decides it. The
question a reviewer is really asking of each row is whether anything was given up
-- and where nothing was, the exclusion was probably never made, only left
unwritten.

- Is any `Cost of excluding it` cell blank, or does it restate the non-goal in
  other words instead of saying what is given up?
  Severity hint: material.
- Does any cost cell name no person, team, customer, segment or capability -- so
  there is nobody the exclusion could disappoint?
  Severity hint: material.
- Does every row's cost amount to "nobody needed this", so no row in the section
  cost the product anything?
  Severity hint: material.
- Does any cost cell give the reason for the exclusion -- out of this release, not
  in the appetite, deferred -- in the column that is supposed to hold its price?
  Severity hint: material.
- Does any cost read as an open question rather than a cost, hedging that the
  exclusion may be revisited instead of saying what living without it means?
  Severity hint: material.
- Is any excluded requirement's cost stated more weakly than the requirement
  itself was -- an upstream sentence somebody wrote as necessary, excluded here at
  no stated price?
  Severity hint: material.
- Could any row be deleted with nothing lost, because the thing excluded was
  never in anybody's scope to begin with?
  Severity hint: minor, material when it is true of most of the section.

## How to update these guidelines

The four H2 headings above, their order, and the *number* of H3 clusters under
"Review-time red flags" are pinned by
`test_principles_expose_the_fleet_fan_out_shape` in
`skills/product-spec/tests/test_product_spec_contract.py`. Renaming a section
breaks a caller that quotes it by name, and the cluster count is how wide a
review fans out -- one finder per cluster -- so adding or removing one changes
what a review costs and what goes unasked, and the test and every caller change
in the same commit. The cluster *names* are not pinned anywhere: renaming one, or
replacing all five with five others, is a green suite and a judgement call, so it
is reviewed as prose and not caught by a test. That test does pin four further
things a maintainer would otherwise meet as a surprise:

- **Every cluster stays answerable.** Each of the five must carry at least one
  line ending in a question mark and at least one `Severity hint:` line. Emptying
  a cluster into prose, or stripping its hints, is a red test rather than a style
  change: a critic is handed one cluster and nothing else, so prose gives it
  nothing to answer and a hintless finding cannot be triaged. The floor is one of
  each, though, so rewriting six of a cluster's seven questions as statements
  still passes -- keeping every question a question is on the author.
- **The attribution keeps its three checkable tokens and its disclaimer.**
  `1.5-chapter-06`, `Is This Architecture?` and `docs.bmad-method.org` are each
  the one thing research settled about their source, and the non-affiliation
  sentence covers all three. The BMAD caveat is checked *per block*: the word
  `partial` has to sit in the same paragraph or bullet as the citation, because a
  caveat one bullet away is one a reader quoting the citation will not carry.
- **Two things stay absent.** The file may not spell the suite's unknown-marker
  token, whose only home is the artifact-family contract. And it may not carry the
  exact phrase naming a "look for decisions" section of Hohpe's chapter, which is
  the tidy-sounding detail no consulted source supported -- the phrase belongs to
  an accessible precursor essay rather than to the book. Both absences are
  asserted over the whole file rather than over the attribution alone. The second
  is one exact string, so a near-miss paraphrase of it would pass; the ban exists
  to stop the phrase being copied back in, not to police every wording of the
  claim, and reintroducing the claim in other words is the same error.
- **Every ban keeps its redirect.** The three `${CLAUDE_PLUGIN_ROOT}` citations
  this file carries are asserted present, and each expectation is built from the
  cited file's own path, so a citation cannot pass while naming a file the plugin
  does not ship there. This is the other half of what the bans above do: each one
  forbids restating a rule and sends the reviewer to its owner, and a redirect
  deleted on its own leaves a rubric that forbids four things and says nowhere to
  look them up. Moving a cited file is therefore a red test, not a broken link.

This file's own name is not this file's to choose, and a rename splits across two
test directories. `skills/product-review/SKILL.md` composes each rubric's path
from its member's owning beat; a rename that still looks like a rubric but stops
matching that composition fails
`test_rubric_template_derives_every_shipped_principles_file` in
`skills/product-review/tests/test_product_review_contract.py`, with a message
about the substrate rather than about this beat. A rename that stops looking like
a rubric at all is invisible to that test, and fails the existence check in this
beat's own contract test instead. Either way the rename is caught, but not in the
place a reader would guess.

The files that quote sections of this file are:

- `skills/product-spec/SKILL.md` (cites this file by `${CLAUDE_PLUGIN_ROOT}` path
  as the rubric a `spec.md` is written against, and restates no cluster)
- `skills/product-review/SKILL.md` (fleet review of `spec.md`: one finder per
  red-flag cluster, quoted verbatim)

This file cites three others and copies none.
`${CLAUDE_PLUGIN_ROOT}/skills/product-spec/references/spec-template.md` owns what
each section holds, the two tables' columns, the permitted forms of an `Origin`
cell and the conventions the member does without;
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
owns the section names, the provenance format and the unknown marker; and
`${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/product-requirements-principles.md`
owns every judgement about a carried sentence itself. On disagreement, those
files win and a question here is the thing that changes.
