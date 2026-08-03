# Product discovery principles

## Attribution and scope

The tree this beat writes is Teresa Torres's Opportunity Solution Tree, from her
work at producttalk.org and her book *Continuous Discovery Habits*. The
assumption mapping and the riskiest-assumption ordering are drawn from *Testing
Business Ideas: A Field Guide for Rapid Experimentation*, by David J. Bland and
Alexander Osterwalder (Wiley, 2019), and from Strategyzer's published material
on the same method. The wording below is independently paraphrased and
reorganized as questions asked of a finished `discovery.md` rather than as
advice for drawing a tree. This project is not affiliated with or endorsed by
Teresa Torres, David J. Bland, Alexander Osterwalder, Strategyzer, or any other
author cited here.

Three places where this suite goes beyond its sources, recorded here so that no
question below can be read as one of theirs:

- **The layer-prefixed node ids are this project's invention.** Torres's
  material specifies no id, numbering or parent-reference convention at all, so
  the notation the template defines -- a prefix per layer, and a parent named by
  id -- is ours rather than hers. What the prefixes are and why is the
  template's to state; that Torres never stated them is this section's.
- **Folding adaptability into viability is our decision.** Strategyzer's library
  article "How Assumptions Mapping Can Focus Your Teams on Running Experiments
  That Matter" names four risk types, adding adaptability -- "can the idea
  survive and adapt in a changing environment?" -- to the ones the template's
  category field carries. David J. Bland's own site describes the same method
  without it, so the sources themselves disagree on whether there is a fourth
  category. This suite records durability as a viability assumption. That fold
  is ours, and a reviewer who believes an assumption is genuinely about
  adaptability is disagreeing with our decision rather than with Bland.
- **TAM, SAM and SOM have no attributable origin.** No source consulted names an
  author, firm or book as the trio's originator, so no question below leans on
  one. A finding about the market figures is always about whether this document
  sourced them, never about which authority defines the terms.

Scope: this file is the single source of truth for judging a written
`discovery.md` -- whether its tree holds together and whether it is testing the
things it is most likely to be wrong about. It is not the document's shape. Two
boundaries keep it from restating its neighbours:

- **Judgement, not shape.** What each section holds, which columns a table
  declares and how an id is formed are
  `opportunity-solution-tree-template.md`'s job, and the section names, the
  provenance rules and the unknown marker belong to `artifact-family.md`. A
  question below may name a section, a column or the marker; it never redefines
  one.
- **The document, not the product.** A finding says the discovery failed to
  establish something, never that the solutions are bad ones. The evidence a
  reviewer has is the document.

Orchestrators quote one section, or one H3 cluster, into an agent prompt;
nothing here is duplicated elsewhere.

## Plan-time principles

These act while `discovery.md` is being written. They pull against the instinct
to get to the buildable thing -- the tree is slowest exactly where it is most
useful -- so name the tension rather than quietly resolving it.

- **The outcome is given, never inferred.** Write down who set the outcome and
  what metric would move. An outcome reconstructed from the slug, or from what
  the team is already building, makes every layer beneath it a justification.
- **An opportunity is a need, not a feature in disguise.** Put every row through
  the discriminating question the template states before writing it down. One
  that survives is a need several solutions could address; one that does not is
  a solution filed a layer too high.
- **Establish the evidence, then write the opportunity.** Write down what was
  observed and where as the row goes in, so that an opportunity somebody saw and
  an opportunity somebody assumed are told apart on the page rather than in the
  author's memory. Where nothing was observed, say so in the form the template
  requires; a cell left blank reads as evidence nobody bothered to write down.
- **Write every assumption so a result could refute it.** Phrase it as a claim
  about what would happen, precisely enough that one observation could
  contradict it. A statement nobody could argue with has been written to be
  approved, not tested.
- **One claim per assumption.** If the sentence needs an "and", or could fail
  for two independent reasons, split it. A test against a bundled assumption
  returns a result nobody can act on, because it cannot say which half broke.
- **Let the test order fall out of the mapping.** The order tests are run in is
  derived from the assumption mapping by the rule the template states; it is not
  chosen. Whenever the list differs from what that derivation yields, something
  other than risk picked it -- readiness, enthusiasm, or work already under way.
- **The unknown marker is the document working.** A slot that carries it has
  been honest about what nobody established. The plausible figure is the
  failure, and it is the one failure nothing downstream will catch.

## Review-time red flags

Each cluster below is quoted verbatim into one critic. Every question is
answerable yes/no against a written `discovery.md`; "yes" is a finding.
Severity hints are defaults -- a critic may upgrade or downgrade with evidence.
Cite the section and the row: a finding the author cannot locate in their own
tree is not actionable. A slot carrying the unknown marker is not a finding on
its own -- the marker is the document doing its job -- unless a question below
says otherwise.

### Unfalsifiable assumptions

The assumption mapping records beliefs no result could contradict, so the tests
hanging off them can only confirm.

- Is any assumption stated as a value, preference or truism -- that customers
  want quality, that teams prefer less work -- rather than as a claim about what
  would happen?
  Severity hint: material.
- Would any assumption still read as true whatever its test returned, so
  running the test changes no decision?
  Severity hint: material.
- Does any assumption test's settling result describe what the test will
  produce rather than the observation that would change the decision, so the
  threshold is set after the data arrives?
  Severity hint: material.
- Is any assumption a claim about intentions or a distant future -- what
  customers will value in three years, what a market will do -- that no
  available evidence could reach?
  Severity hint: material.
- Is any assumption written about the team rather than about the world ("we
  believe we can execute well"), so the only evidence would be the team's own
  confidence?
  Severity hint: minor, material when it sits in the important, no-evidence
  quadrant.
- Are the assumption's terms left undefined -- "quickly", "at scale",
  "affordably" -- so two readers would call the same result a pass and a
  failure?
  Severity hint: minor, material when the vague term is the thing being tested.

### Compound assumptions

One row holds two claims, so a result cannot say which of them broke.

- Does any assumption join two claims with "and", "so that", or a comma, where
  each could come out differently?
  Severity hint: material.
- Could any assumption fail for two independent reasons, leaving a failed test
  unable to say which reason applied?
  Severity hint: material.
- Does any assumption name two actors -- two segments, the customer and the
  company, two systems -- so that evidence about one says nothing about the
  other?
  Severity hint: material.
- Is any assumption a conditional whose antecedent is itself untested and
  appears in no other row, so the row assumes two things while testing one?
  Severity hint: material.
- Is any row's category arguable between two of the values the template's
  category field allows, which usually means the sentence holds a desirability
  claim and a feasibility one at the same time?
  Severity hint: minor, material when the two halves would be tested by
  different instruments.
- Does one assumption test claim to settle several assumptions at once, so no
  single row's status can be read off its result?
  Severity hint: minor.

### Solutions attached straight to the outcome

The middle layer is present in form but does no work, so the document jumps
from the business result to the thing the team was going to build anyway.

- Does any solution name the outcome, rather than exactly one opportunity, as
  its parent?
  Severity hint: material.
- Is any opportunity the solution restated as a need -- a customer who "needs a
  dashboard", "needs an integration" -- so that only one way of addressing it
  exists and the layer is a relabelled feature?
  Severity hint: material.
- Does every opportunity have exactly one solution under it, with no
  opportunity carrying two, so the two layers are one list written twice?
  Severity hint: material.
- Does any opportunity's evidence cell describe the benefit a solution would
  deliver rather than something observed about a customer?
  Severity hint: material.
- Do the opportunities appear only where a solution needed a parent, so no
  opportunity was recorded that nothing in the document proposes to address?
  Severity hint: minor, material when the tree carries no unaddressed
  opportunity at all.
- Is the outcome restated in the solution rows -- a solution described by the
  metric it would move rather than by what a customer could then do -- so the
  intervening customer need is skipped in the prose even where the ids connect?
  Severity hint: minor.

### Experiments chosen for interest rather than risk

The tests that got designed are the ones the team wanted to run, not the ones
that would settle what the document is most likely wrong about.

- Does the riskiest-assumption list include a test for an assumption the
  mapping marks as having evidence, or as unimportant?
  Severity hint: material.
- Does an assumption in the important, no-evidence quadrant reach the end of
  the document with no test designed for it, while a lower-risk assumption has
  one?
  Severity hint: material.
- Is the list ordered by anything other than the cost of testing -- by build
  readiness, by what is already underway, by which result the team expects?
  Severity hint: material.
- Would any listed test cost more than the decision it informs is worth -- a
  build, a pilot, a full integration -- where a cheaper instrument could settle
  the same assumption?
  Severity hint: material.
- Is the list presented as a delivery sequence -- phases, sprints, a roadmap --
  rather than as the order in which uncertainty gets cheapest to remove?
  Severity hint: minor, material when a later item is described as depending on
  an earlier one shipping.
- Does the list say what a test would establish without saying what a failure
  would mean for the solution it hangs off, so no result closes anything down?
  Severity hint: minor.
- Are the switch-interview questions written to confirm the pull of the
  proposed solution, with nothing that would surface the anxiety of switching
  or the habit of the present?
  Severity hint: minor, material when the interview is the only test designed.

## How to update these guidelines

The four H2 headings above and the four-cluster H3 structure under
"Review-time red flags" are pinned by
`skills/product-discovery/tests/test_product_discovery_contract.py`
(`test_principles_expose_four_red_flag_clusters`); renaming a section breaks
callers that quote it by name, and adding a fifth cluster changes how many
finders a review launches, so change the test and every caller in the same
commit. That test pins three more things a maintainer would otherwise meet as a
surprise: the four H2 sections must appear in the order above, and every cluster
must carry at least one line ending in a question mark and at least one
`Severity hint:` line. Rewriting a question as a statement, or dropping a
cluster's hints, is a red test rather than a style change.

The files that quote sections of this file are:

- `skills/product-discovery/SKILL.md` (cites this file by
  `${CLAUDE_PLUGIN_ROOT}` path as the rubric a `discovery.md` is written
  against, and restates no cluster)

No review skill quotes the clusters yet; the reviewing beat ships separately,
and whichever file ships it adds itself to the list above in the same commit.

This file cites two others and copies neither.
`${CLAUDE_PLUGIN_ROOT}/skills/product-discovery/references/opportunity-solution-tree-template.md`
owns what each section of a `discovery.md` holds, which columns its tables
declare and how an id is formed, and
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
owns the section names, the provenance format and the unknown marker. On
disagreement, those files win and a question here is the thing that changes.
