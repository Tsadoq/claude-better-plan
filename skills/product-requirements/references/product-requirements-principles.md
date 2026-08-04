# Product requirements principles

## Attribution and scope

The failure modes below are the ones the Easy Approach to Requirements Syntax
was built to address. Its authors -- Mavin, Wilkinson, Harwood and Novak, in
"Easy Approach to Requirements Syntax (EARS)", IEEE RE'09 -- open by naming
eight problems that natural-language requirements are prone to: ambiguity,
vagueness, complexity, omission, duplication, wordiness, inappropriate
implementation, and untestability. The five clusters under "Review-time red
flags" are that list, regrouped and turned into questions asked of a finished
`requirements.md` rather than into advice for writing one, and the wording is
independently paraphrased. This project is not affiliated with or endorsed by
those authors, by the IEEE, or by any other author cited here.

Three things about the regrouping, recorded here so that no cluster below can be
read as the paper's own arrangement:

- **Wordiness carries no cluster, on purpose.** It is the one problem of the
  eight that no question below hunts. A wordy requirement is still one testable
  sentence with one reading, so there is nothing a reviewer could answer yes or
  no about it that would change the member; the shorter of two correct sentences
  is a preference, and a rubric that spends a finder on preferences trains
  authors to argue with it. Seven of eight is a decision, not a transcription
  error.
- **Two clusters fold two problems each.** Ambiguity and vagueness travel
  together because the same sentence usually has both, and omission and
  duplication because both are found by reading the coverage table rather than
  the requirements. Compound requirements is one name for one problem: the paper
  describes its complexity problem as compound requirements containing complex
  sub-clauses, so its own term already covers what a second name would add.
- **Smuggled implementation is wider than the paper's problem.** It carries the
  paper's inappropriate-implementation problem and, with it, requirements phrased
  as interface steps -- clicking a named button, opening a named screen. The
  paper does not discuss user interfaces; folding those in is this project's
  decision, on the grounds that a mechanism is a mechanism whether it arrived as
  a library or as a control.

The other two frameworks a `requirements.md` is written against are attributed
where they are defined, not here. `## The INVEST gate` of the template names Bill
Wake as the criteria's author, and `## The quality characteristic checklist`
names ISO/IEC 25010:2023 and says which of its glosses are paraphrase. A question
below may invoke either framework; it never restates one, so an attribution
argument about INVEST or the ISO model is settled in the template.

Scope: this file is the single source of truth for judging a written
`requirements.md` -- whether each sentence admits exactly one reading, and
whether the set of them accounts for what discovery found. It is not the
document's shape. Two boundaries keep it from restating its neighbours:

- **Judgement, not shape.** What each section holds, which columns a table
  declares, the notation's grammar and its casing, and how an id is formed are
  `requirements-template.md`'s job, and the section names, the provenance rules
  and the unknown marker belong to `artifact-family.md`. A question below may
  name a section, a column, a pattern or the marker; it never redefines one.
- **The document, not the product.** A finding says the member failed to
  establish something, never that the product should be built differently. The
  evidence a reviewer has is the document.

A third boundary runs to a rubric outside this suite. How a name reads and what a
comment has to say are `### Naming` and `### Comments and obviousness` of
`${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/design-principles.md`,
which the design-review fleet quotes over code and plans. Cluster 1 below asks
whether a requirement admits two readings, which rhymes with that file's
vague-name question without restating it -- the subject here is a sentence in a
member, not an identifier in a diff. Per issue #18 this file cites those two
clusters rather than re-deriving them, so a question about naming or commentary
in the plugin's own files is raised there and not as a sixth cluster here.

Orchestrators quote one section, or one H3 cluster, into an agent prompt; nothing
here is duplicated elsewhere.

## Plan-time principles

These act while `requirements.md` is being written. They pull against the
instinct to get the member finished -- the notation is slowest exactly where a
sentence is least settled -- so name the tension rather than quietly resolving
it.

- **Name the system before writing the first requirement.** Every pattern in the
  notation has a slot for the thing being constrained, and the name goes in the
  same words every time. A member that fills that slot from memory produces
  requirements that read as though they constrain three systems, which is
  invisible in any one row.
- **One requirement, one sentence, one demand.** If the sentence needs an "and",
  or could be half-satisfied, split it. Two demands sharing an id will be cited,
  tested and signed off as one, and nothing downstream can separate them again.
- **Write the sentence in the notation before arguing about it.** The point of a
  fixed clause grammar is that a sentence written to one shows its own missing
  parts: no trigger, no state, no measurable response. Prose hides all three, and
  a requirement discussed as prose gets agreed to before anyone notices what it
  does not say.
- **A quality attribute with no threshold is a preference.** A figure, a unit and
  the condition it holds under are what make a non-functional requirement
  passable or failable. Where nobody has established the figure, the honest form
  is the suite's unknown marker rather than a plausible number, because a
  plausible number is the one failure nothing downstream will catch.
- **Trace forwards and backwards, in that order of difficulty.** Naming the
  opportunity a requirement answers is easy and proves only that the requirement
  did not come from nowhere. Walking every opportunity and every quality
  characteristic to a requirement, an exclusion or the marker is the work, and it
  is the only thing that makes the member readable as complete.
- **Record the gap where the gap is.** An opportunity nobody is addressing and a
  characteristic that does not apply belong in `## Out of scope` with a reason
  someone could disagree with, in the same member as the requirements they are
  the counterpart to. A gap recorded nowhere reads exactly like completeness.

## Review-time red flags

Each cluster below is quoted verbatim into one critic. Every question is
answerable yes/no against a written `requirements.md`; "yes" is a finding.
Severity hints are defaults -- a critic may upgrade or downgrade with evidence.
Cite the id and the cell: a finding the author cannot locate in their own table
is not actionable. A slot carrying the unknown marker is not a finding on its own
-- the marker is the member doing its job -- unless a question below says
otherwise.

### Ambiguity and vagueness

The paper's ambiguity and vagueness problems: a sentence that admits more than
one reading, or whose terms are settled by whoever is reading. Two implementers
build two things and both believe they complied.

- Does any requirement turn on a word whose meaning the reader supplies --
  "appropriate", "user-friendly", "as needed", "sufficient", "robust", "seamless"
  -- so two implementations could both claim to satisfy it?
  Severity hint: material.
- Does any requirement make a comparison -- faster, simpler, more reliable, fewer
  steps -- without naming what it is compared against?
  Severity hint: material.
- Is any pronoun or bare noun phrase in a `Requirement` cell ("it", "the data",
  "the user", "the request") resolvable to more than one thing in its own
  sentence?
  Severity hint: material.
- Does any requirement name a system or component that `### The system name` does
  not list, or refer to a listed one in different words than that table uses?
  Severity hint: material.
- Does any requirement gesture at its trigger or its precondition instead of
  stating it -- "on error", "when required", "under load" -- leaving the reader to
  decide which event or state it means?
  Severity hint: material.
- Is any quantity written without a unit, or with a unit but without the
  condition it holds under -- what load, which percentile, over what window?
  Severity hint: minor, material when it is the only requirement constraining
  that quality characteristic.
- Do two rows use different words for one thing, or one word for two things, so
  the member's vocabulary has to be reconciled by the reader?
  Severity hint: minor.

### Compound requirements

The paper's complexity problem, which it describes as requirements compounded out
of several demands and complex sub-clauses. One row holds two obligations, so a
failed test cannot say which of them broke.

- Does any `Requirement` cell join two demands with "and", "as well as", or a
  semicolon, where each could be satisfied or violated on its own?
  Severity hint: material.
- Could any requirement be half-delivered -- one clause working, the other not --
  and still be reported against a single id?
  Severity hint: material.
- Does any requirement stack two triggers, or a trigger and two preconditions, so
  working out when it applies takes a second reading?
  Severity hint: material.
- Does any requirement carry a second obligation inside a subordinate clause --
  "while also", "including", "so that", "and then" -- so it reads as one sentence
  and delivers as two?
  Severity hint: material.
- Does any row's `Pattern` cell disagree with its sentence: a single pattern
  declared over a sentence that combines two, or the complex pattern declared
  over one that combines nothing?
  Severity hint: material.
- Would splitting any requirement in two leave both halves with the same `Traces
  to` and the same `Source`, so nothing but the sentence was holding them
  together?
  Severity hint: minor.

### Unverifiable requirements

The paper's untestability problem: a requirement nobody could write a test
against, so compliance is decided by argument at the end of the project.

- Is any requirement's response unobservable -- no output, no measurable
  quantity, no state a reader of the finished system could inspect?
  Severity hint: material.
- Does any non-functional requirement name a quality without a threshold -- shall
  be fast, shall be secure, shall be maintainable -- so nothing could fail it?
  Severity hint: material.
- Does any threshold arrive with a `Source` cell that is blank, or that names no
  document, person or measurement, leaving a figure nobody can defend or revise
  on purpose?
  Severity hint: material.
- Is any requirement written about an intention -- the system "shall attempt",
  "shall try to", "shall aim to", "shall support" -- so failing to do the thing
  still satisfies the sentence?
  Severity hint: material.
- Does any requirement's response name an outcome outside the system's control
  (a customer's satisfaction, a third party's uptime, a team's velocity), so no
  test of this system could settle it?
  Severity hint: minor, material when the release is judged by that requirement.
- Does any story-shaped requirement fail the Testable criterion as
  `## The INVEST gate` of the template defines it, while carrying no note that
  says why it shipped anyway?
  Severity hint: minor.

### Smuggled implementation

The paper's problem of inappropriate implementation, widened to interface steps:
the sentence constrains a mechanism instead of a behaviour, which puts a design
decision past the beat that would have argued about it.

- Does any requirement name a technology, library, protocol, vendor, data store
  or wire format, so it is satisfied by a build choice rather than by a
  behaviour?
  Severity hint: material.
- Does any requirement describe a person operating a control -- clicking a named
  button, opening a named screen, filling a named field -- rather than what the
  system does?
  Severity hint: material.
- Does any requirement prescribe an internal mechanism -- shall cache, shall
  queue, shall retry three times, shall write to a table -- while leaving the
  observable behaviour that mechanism exists for unstated?
  Severity hint: material.
- Is any requirement written from the builder's side ("the system shall be
  implemented using", "shall be deployed on"), so it constrains the team rather
  than the product?
  Severity hint: material.
- Does any requirement restate a step of a plan the team already has, so a
  decision somebody made is recorded as a need somebody has?
  Severity hint: material.
- Would any requirement have to be re-worded to survive a change every reader
  would call internal -- a swapped library, a renamed screen, a different
  storage layout?
  Severity hint: minor, material when more than one requirement would.

### Omission and duplication

The paper's omission and duplication problems, which are the two failures found
by reading the coverage table rather than the requirements: something discovery
established has no requirement and no recorded reason, or one need is expressed
twice and only one copy gets maintained.

- Does any row of `### Opportunity coverage` carry a blank `Covered by` cell, so
  an opportunity nobody wrote a requirement for is indistinguishable from a table
  nobody finished?
  Severity hint: material.
- Is any `OPP` id from `discovery.md` missing from the coverage table altogether,
  so the omission is invisible rather than recorded?
  Severity hint: material.
- Does any coverage row read `not addressed` with no matching row under
  `### Opportunities not addressed`, or does any row there name an opportunity
  the coverage table shows as covered?
  Severity hint: material.
- Do two requirements express one need in different words, so a later change
  lands in one of them and the member starts contradicting itself?
  Severity hint: material.
- Does any `Traces to` cell name an `OPP` id that `discovery.md` does not carry,
  or a quality characteristic the checklist never raised?
  Severity hint: material.
- Is any quality characteristic absent from both requirement tables and from
  `### Quality characteristics not applicable`, so nobody can tell whether it was
  considered?
  Severity hint: material.
- Does any reason under `### Opportunities not addressed` amount to "not yet
  decided", which is an open question wearing an exclusion's clothes?
  Severity hint: minor.
- Are two rows distinguishable only by their ids -- the same sentence, the same
  trace, two numbers?
  Severity hint: minor.

## How to update these guidelines

The four H2 headings above and the five-cluster H3 structure under "Review-time
red flags" are pinned by
`skills/product-requirements/tests/test_product_requirements_contract.py`;
renaming a section breaks callers that quote it by name, and changing the number
of clusters changes how many finders a review launches, so change the test and
every caller in the same commit. Three tests there own different parts of this
file, and each pins things a maintainer would otherwise meet as a surprise:

- `test_principles_expose_five_red_flag_clusters` -- the four H2 sections appear
  exactly once each and in the order above, and exactly five H3 clusters nest
  inside the red-flags section, each carrying at least one line ending in a
  question mark and at least one `Severity hint:` line. Rewriting a question as a
  statement, or dropping a cluster's hints, is a red test rather than a style
  change. Five where both sibling rubrics carry four: the fifth cluster is the
  finder assigned to broken traceability, which is the single failure this beat
  exists to prevent.
- `test_every_cluster_names_the_paper_problem_it_derives_from` -- the five cluster
  names, in this order, and the requirement that each cluster's own body names the
  paper problem it comes from. A critic is handed one cluster and no more of this
  file, so grounding recorded only in "Attribution and scope" reaches nobody
  reviewing. That test also pins the attribution itself -- author, venue,
  disclaimer -- and that wordiness is recorded as the one problem of the eight no
  cluster carries.
- `test_principles_cite_their_neighbours_rather_than_restating_them` -- the three
  `${CLAUDE_PLUGIN_ROOT}` citations below, that the two design-review clusters
  named in "Attribution and scope" still exist in that file, that the omission
  cluster names `### Opportunity coverage` and the `not addressed` literal its
  questions are answered against, and that this file nowhere spells the unknown
  marker's token.

The files that quote sections of this file are:

- `skills/product-requirements/SKILL.md` (cites this file by
  `${CLAUDE_PLUGIN_ROOT}` path as the rubric a `requirements.md` is written
  against, and restates no cluster)
- `skills/product-review/SKILL.md` (fleet review of `requirements.md`: one finder
  per red-flag cluster, quoted verbatim; composes this path from the member's
  owning beat rather than naming it, so a rename that puts this file beyond that
  composition's reach fails
  `test_rubric_template_derives_every_shipped_principles_file`, not any test
  here)

This file cites three others and copies none.
`${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/requirements-template.md`
owns what each section of a `requirements.md` holds, the notation and its casing,
the quality characteristic checklist, the INVEST gate and how an id is formed;
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
owns the section names, the provenance format and the unknown marker; and
`${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/design-principles.md` owns
the naming and comment questions this file defers rather than re-deriving. On
disagreement, those files win and a question here is the thing that changes.
