# Product roadmap principles

## Attribution and scope

Seven sources stand behind the questions below, and every one of them is cited
for something narrower than what is built on it. What each supports and what it
does not is recorded here because the gap between the two is where most of this
file comes from, and a reviewer who mistakes an extension for a quoted authority
will defend it on grounds it does not have. This project is not affiliated with
or endorsed by Intercom, by 37signals, by Scaled Agile, Inc., by the Agile
Business Consortium, by ProdPad, by Itamar Gilad, or by any other author cited
here.

- **Intercom, for the RICE score.** Sean McBride, 5 January 2018
  (`intercom.com/blog/rice-simple-prioritization-for-product-managers/`), for
  all four inputs and their units. What the post does not supply is a caveat:
  two keyword-scoped passes over the full article found none about false
  precision, confidence inflation or cross-team comparison, and the only
  adjacent lines defend the method. No question below may be cited to it.
- **Shape Up, chapter 3, "Set Boundaries", for appetite.**
  `basecamp.com/shapeup/1.2-chapter-03`, for the definition -- the time we want
  to spend rather than an estimate of what it will take -- for its unit, a time
  budget for a standard team size, and for "fixed time, variable scope". Note
  the chapter number: appetite is defined in chapter 3, not in chapter 6 where
  the pitch ingredients live. Shape Up nowhere combines an appetite with a
  scoring formula; chapters 3, 6 and 8 were checked, and chapter 8, "The Betting
  Table", is explicitly qualitative.
- **Scaled Agile, for WSJF.** `framework.scaledagile.com/wsjf/`, which the older
  `scaledagileframework.com/wsjf/` now redirects to, for the formula -- relative
  cost of delay divided by relative job duration -- for cost of delay's three
  components, and for the modified Fibonacci scale. The instruction that the
  numbers are relative to one backlog rather than cardinal is the source's own
  and travels with any use of it.
- **The Agile Business Consortium, for MoSCoW's categories.**
  `agilebusiness.org/dsdm-project-framework/moscow-prioritisation.html`, the
  body that owns DSDM, for "Must Have, Should Have, Could Have, Won't Have this
  time" -- the lowercase letters standing for nothing, and the "this time"
  qualifier being part of the category rather than a gloss. The page supplies no
  author, no year, and no critique.
- **Kano, Seraku, Takahashi and Tsuji, 1984, for three category names.**
  "Attractive Quality and Must-Be Quality", *Journal of the Japanese Society for
  Quality Control* 14(2), 147 to 156, verified on the journal's own archive; its
  pagination is preferred over the 39 to 48 some reference managers carry. The
  English abstract names attractive, must-be and one-dimensional quality. The
  paper itself is in Japanese and supplies nothing further that could be read.
- **ProdPad, for the argument against dating unstarted work.**
  `prodpad.com/blog/invented-now-next-later-roadmap/`, for the Now/Next/Later
  invention claim and for the argument verbatim: "It doesn't make sense to go
  into detail about big, far-off ideas, just like it doesn't make sense to
  assign them deadlines." That argument is why this member carries no dates. Its
  Now/Next/Later horizons are not adopted, this member ordering work by a score
  and a sequence instead.
- **Itamar Gilad, for padded confidence.**
  `itamargilad.com/prioritization-techniques-2/`, for the observed pattern:
  people "use opinions and sparse data to estimate Impact and Ease, and yet
  assign a high Confidence value". Gilad is a practitioner writing about scoring
  generally and is not first-party for RICE, so the citation supports the
  pattern and not the method.

Seven things below reach past those sources, and each is recorded so that a
reader can tell which part of a question they are being asked to accept:

- **Pairing a RICE score with an appetite column.** Neither source does it.
  Intercom's post has no budget in it and Shape Up has no formula, so the
  arrangement, and the rule that an appetite is never raised to meet an effort,
  are this project's synthesis of the two.
- **The person-months to team-calendar-weeks conversion.** Stated by neither
  source: Intercom is silent on calendar time and Shape Up on person-months. The
  four-weeks-to-a-month figure and the team-size divisor are the template's own
  convention, and nothing is borrowed in them.
- **The `ITEM` id convention.** Not Intercom's and deliberately not Shape Up's
  vocabulary, since borrowing a betting-table word would claim that Shape Up's
  process is implemented here. One flat sequence, never reused and never
  renumbered, is this project's rule, adopted because these ids are cited from
  outside the folder and no freshness check in the chain inspects a downstream
  identifier.
- **`### False precision` and `### Padded confidence` are not the RICE post's
  caveats.** The post carries none, so neither cluster may cite it. False
  precision from multiplying four rough estimates has no primary source at all
  -- Hubbard and Savage were searched and returned only secondary summaries --
  and ships as this project's own. Padded confidence rests on Gilad's
  observation above, which is a practitioner's and not Intercom's.
- **MoSCoW is cited for its categories and for nothing else.** The coining
  attribution usually given -- Dai Clegg, 1994 -- appears only in secondary
  aggregators while the owning body's page names no author and no year, so it is
  not shipped. The familiar critique, that MoSCoW fixes no order within Must
  Have, appears in no consulted source either, and ships below as this file's
  commentary rather than as the method's own documentation.
- **Kano ships as three categories, not five.** "Indifferent" and "reverse", and
  the paired functional and dysfunctional question format the method is known
  for, could not be confirmed from an English abstract of a Japanese paper. They
  are not claimed here, and the guidance below asks nothing that depends on
  them.
- **`### A score that ratifies a ranking already made` and `### An ordering with
  no rejected alternative` are this project's, not Hohpe's.** Both were expected
  to rest on *The Software Architect Elevator*. Chapter 8 is confirmed as "Is
  This Architecture?", and its primary test -- a document records nontrivial
  decisions together with the reasoning behind them -- is what the fourth
  cluster carries across from architecture documents to a sequence. The test is
  Hohpe's and the carry is not. The third cluster has no source at all: chapter 6
  is "Making Decisions", nothing in its surfaced sections covers a score written
  to ratify a decision already taken, and the chapter could not be read.

RICE's four inputs and an appetite answer one question: which of these, first,
for this team. Three questions they cannot answer have better instruments, and
reaching for one is a decision about the roadmap rather than a finding against
it -- nothing in `## Review-time red flags` asks whether the right instrument
was chosen.

- **Cost of delay.** RICE has no term for it. An item that loses value every
  week it waits scores exactly the same a month before its window closes as a
  year before, because none of Reach, Impact, Confidence or Effort moves with
  time. WSJF names it directly: cost of delay over job duration, with cost of
  delay split into user-business value, **Time Criticality**, and risk reduction
  or opportunity enablement. Where deadlines, regulatory dates or a closing
  market window are what actually order the work, WSJF asks the question this
  file cannot. Its scores are relative to one backlog, which is Scaled Agile's
  own instruction and rules out exactly the comparison the fifth cluster below
  warns about.
- **Obligation rather than order.** MoSCoW sorts into Must Have, Should Have,
  Could Have and Won't Have this time, and fits where the question is what a
  release has to contain rather than what comes first. It gives no ordering
  inside Must Have, so a team that needs both a contract and a sequence carries
  MoSCoW upstream, in the scope decision `spec.md` records, and still scores
  here.
- **Which qualities are worth having at all.** Kano sorts features by how
  satisfaction responds to them: attractive quality delights when present and is
  not missed when absent, must-be quality goes unremarked when present and is
  unacceptable when absent, and one-dimensional quality tracks how much is
  delivered. RICE's Impact is a single number and cannot say that a must-be
  feature delivered at eighty per cent is a failure while an attractive one at
  eighty per cent is a win. Where a candidate set differs in kind rather than in
  size, Kano decides what is worth scoring before this file decides what comes
  first.

ICE is deliberately absent, and its absence is a judgement rather than an
oversight. It is RICE with Reach removed, so every question it answers is one
RICE answers with an extra term, and a "when this fits instead" entry naming a
strict subset teaches a reader nothing. Its provenance is also weak -- no
first-party source was reachable and the best attribution found is second-hand
-- but that is the lesser reason, and it would stay out on merit alone.

Scope: this file is the single source of truth for judging a written
`roadmap.md` -- whether its numbers rest on anything, whether its order was
decided or merely sorted, and whether any of it could be compared with anybody
else's. It is not the document's shape. Three boundaries keep it from restating
its neighbours:

- **Judgement, not shape.** Which sections the member carries and in what order,
  the provenance line's format, and the suite's single unknown-value marker are
  published by
  `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`.
  What the four inputs mean and what units they are in, the appetite's unit, both
  tables' columns, the `ITEM` id rules and the conversion between effort and
  appetite belong to
  `${CLAUDE_PLUGIN_ROOT}/skills/product-roadmap/references/rice-template.md`. A
  question below may name a section, a column or the marker; it never redefines
  one, and this file nowhere spells the marker's own token.
- **The document, not the plan.** A finding says the member failed to establish
  something. It never says a different item should have come first, and it never
  supplies the number it is asking for. The evidence a reviewer has is the
  document.
- **The order, not the scope.** Which requirements are in scope was decided
  upstream. A `REQ` id no item covers is reported here as an uncovered
  requirement and never as one that should not have been specified; whether the
  requirement was worth writing is judged by
  `${CLAUDE_PLUGIN_ROOT}/skills/product-spec/references/product-spec-principles.md`
  against the member that owns it, and a fault found in a carried id is a
  `product-spec` re-run rather than an edit here.

Orchestrators quote one section, or one H3 cluster, into an agent prompt;
nothing here is duplicated elsewhere.

## Plan-time principles

These act while `roadmap.md` is being written. Each pulls against something that
feels like diligence at the time, which is why they are worth stating rather
than trusting.

- **A figure and its basis are one thing.** Every input cell carries the number
  and what the number rests on -- the ticket count it was read off, the person
  who supplied it, the comparable piece of work it was judged against. A figure
  with no basis is not a rougher figure. It is one nobody can correct on purpose
  later, only argue about, and this table exists to be argued with precisely.
- **Where the basis does not exist, the cell says so.** The marker is not a
  failure state, and an input carrying it costs the item its score rather than
  its place in the document. A number invented to keep a row looking finished
  arrives with three decimals and outranks a well-sourced item on a table nobody
  re-derives.
- **Decide the appetite before the shape is known.** That is the whole of what
  makes it a budget. Once an effort is in hand, the appetite that gets written is
  an estimate wearing the word, and the column has nothing left to say that
  `Effort` did not already say.
- **Let the score be beaten, and say what beat it.** The sequence is derived, not
  sorted. Dependencies and appetite windows both honestly outrank a score, and
  naming which of the two moved an item is what keeps a departure a decision
  rather than a mistake somebody will silently correct.
- **Write the rejected ordering down while you still remember why.** A year on,
  the order that was chosen and the first order anybody typed look identical on
  the page. The rejected alternative is the only part of the section that tells
  them apart, and it is unrecoverable once the discussion is over.
- **No dates, and the harmless ones are the ones to watch.** A quarter beside an
  entry, a sprint number, a target month. ProdPad's argument is the one to hold:
  it makes no more sense to date a big, far-off idea than to detail one. A date
  turns an ordering meant to be revised into a commitment somebody is held to,
  and it usually lands on the entry nobody has started.
- **Score one table, and score it only against itself.** Impact points and
  appetite weeks mean what this roadmap's period and team size make them mean.
  They are not a currency. Carrying a score to another team's table compares two
  numbers whose units were never the same, and both of them look like numbers.

## Review-time red flags

Each cluster below is quoted verbatim into one critic. Every question is
answerable yes or no against a written `roadmap.md`; "yes" is a finding.
Severity hints are defaults -- a critic may upgrade or downgrade with evidence.
Cite the section, and the row and cell where there is one: a finding the author
cannot locate in their own document is not actionable. A cell carrying the
suite's unknown marker is the member doing its job and is not a finding on its
own, unless a question below says otherwise.

Several questions turn on a unit -- Impact's scale, Confidence's tiers, Effort's
rounding, the two permitted forms of a `Covered by` cell. None of them is
written out below. `## Attribution and scope` names the template that fixes all
of them and is the only place any of them is defined; open it rather than
assuming a value, because a question that had restated one would go on asking
about the old unit for as long as it took anybody to notice.

Two of the five clusters ask about arithmetic and three ask about a decision.
The arithmetic ones are cheaper to answer, and answering them first is fine, but
they are not where the expensive failures are: a table of perfectly well-formed
numbers that ratifies an order somebody had already agreed on passes every
question in the first two clusters.

### False precision

Four rough estimates multiplied and divided produce a number that looks far more
exact than any of them. The score's whole value is that a disagreement can be
traced to the input it is about, and a number quoted past the precision its
inputs support hides that trace while producing a ranking no input actually
supports.

This cluster is this project's own and the RICE post carries no caveat to cite
for it. Report the number that overstates, never the method.

- Does any `Score` cell carry more precision than its inputs can produce --
  decimal places that the four cells to its left could not have generated?
  Severity hint: material.
- Does any `Effort` cell hold a value outside the rounding the template fixes
  for person-months, claiming a precision the other three inputs cannot support?
  Severity hint: material.
- Does any `Impact` cell hold a value that is not one of the points the
  template's scale offers, or a value between two of them?
  Severity hint: material.
- Is any `Reach` cell a proportion, a share or a qualifier -- "most users", "the
  majority" -- rather than a count over the period the member names?
  Severity hint: material.
- Does any input cell carry a figure and no basis, so the number can never be
  corrected on purpose and can only be argued about?
  Severity hint: material.
- Does `## Sequence` separate two items whose scores differ by less than the
  rounding in their own inputs, without naming what else decided between them?
  Severity hint: material.
- Does any basis read as an opinion in the grammar of a measurement -- a count
  with no source, an estimate attributed to nobody, a comparison to work that is
  not named?
  Severity hint: minor, material where it is the basis of the highest-scoring
  row.

### Padded confidence

The one input that costs nothing to raise. Confidence is a claim about the
evidence behind the other three, so a high value on thin evidence does not
merely overstate one cell -- it multiplies through and moves the item's
position. The failure is invisible in any single row and obvious read down the
column.

Gilad's observation is the source for the pattern: people estimate the other
inputs from opinions and sparse data, and assign a high confidence anyway.

- Does any `Confidence` cell hold a value outside the tiers the template fixes,
  so a fourth tier has been invented?
  Severity hint: material.
- Does any top-tier `Confidence` cell sit beside inputs whose own bases are
  estimates, opinions or one person's judgement?
  Severity hint: material.
- Does `## Risks` name a risk against an item whose confidence is at the top
  tier, so the document says both that the evidence is settled and that it is
  not?
  Severity hint: material.
- Does every item carry the same confidence, so the column distinguishes nothing
  and drops out of the formula?
  Severity hint: material.
- Has an item weaker than the lowest tier been written up at that tier rather
  than recorded as a total moonshot with no supportable confidence?
  Severity hint: material.
- Does any confidence cell give its basis as the team's belief in the work, its
  importance, or somebody's commitment to it, rather than as evidence about the
  other three inputs?
  Severity hint: material.
- Is a low-scoring item lifted to the top of `## Sequence` by its confidence
  alone, its other three inputs being unremarkable?
  Severity hint: minor, material where the same is true of more than one item.

### A score that ratifies a ranking already made

The expensive failure, and a well-formed table hides it completely. A roadmap
written to justify an order somebody had already agreed on is arithmetically
perfect and evidentially worthless, and nothing in the document separates it
from one whose order the numbers produced. That is why the questions here ask
about the fit between the table and the sequence rather than about either alone.

This cluster has no source. It is this project's own, and the chapter it was
expected to rest on does not cover it.

- Is `## Sequence` exactly `## Scored items` sorted by `Score`, while the
  section itself names dependencies or appetite windows that would have moved
  something?
  Severity hint: material.
- Does any departure from score order go unexplained, so the sequence is neither
  the score's order nor a stated decision?
  Severity hint: material.
- Does any input cell give its basis as the position the item was given, the
  priority it was assigned, or a commitment already made, rather than as
  evidence about that input?
  Severity hint: material.
- Does a stated reason for a departure rest on something no cell in
  `## Scored items` records -- a promise, an escalation, an executive preference
  -- so the table and the order are built on different evidence?
  Severity hint: material.
- Does the recorded rejected ordering differ from the chosen one only in the
  positions of the lowest-scoring items, so nothing that was actually contested
  was ever in question?
  Severity hint: material.
- Is the top-ranked item the one an ordinary reader would have expected first,
  with every input at the top of its range and each basis a single unattributed
  sentence?
  Severity hint: minor, material where more than one of its inputs is
  unattributed.
- Do two items with materially different inputs land close enough in `Score` to
  leave the chosen order the only readable one, with nothing said about the gap?
  Severity hint: minor.

### An ordering with no rejected alternative

A sequence records what somebody chose; the rejected alternative records that
choosing happened. Without it a reader cannot tell an order that was decided
from the first order anybody typed, and the two are identical on the page. The
test being applied is the one any decision record has to pass: a nontrivial
choice, and the reasoning behind it.

The test is Hohpe's. Carrying it from architecture decisions to a roadmap
sequence is this project's extension, and this cluster is as strong as that
extension rather than as strong as the chapter.

- Is no rejected ordering recorded at all beneath `## Sequence`?
  Severity hint: material.
- Is a rejected ordering named without what decided against it, so the
  alternative was listed rather than rejected?
  Severity hint: material.
- Is the rejected ordering one nobody would have proposed -- score order
  reversed, or the items shuffled -- so it is an alternative in form only?
  Severity hint: material.
- Does the reason for rejecting it restate the chosen order's advantage instead
  of naming what the rejected one would have cost?
  Severity hint: material.
- Does `## Sequence` depart from score order without attributing the departure
  to a dependency or to an appetite window?
  Severity hint: material.
- Does any entry in `## Sequence` carry a quarter, a sprint, a month or a target
  date, so an ordering has been written as a schedule nobody decided?
  Severity hint: material.
- Does any item appear in `## Sequence` with no `Score`, so it was placed in an
  order there was nothing to have ranked it by?
  Severity hint: material.
- Is the rejected ordering recorded as an option the team may revisit rather
  than as one that was decided against?
  Severity hint: minor.

### Impact compared across teams as one currency

Every number here is relative to one table. Reach is counted over a period this
roadmap names, appetite assumes a team size this roadmap names, and Impact's
five points mean whatever this roadmap's rows have used them to mean. A score
lifted out of that context and set beside another team's is two different units
printed to the same number of digits.

This cluster has no source and is this project's own. The failure it looks for
is at its worst inside a single member, where one column is silently read as if
its rows shared a unit.

- Does the member fail to name Reach's measurement period above the table, so no
  cell in that column can be read down against another?
  Severity hint: material.
- Does the member fail to name the team size every `Appetite` assumes, so the
  column's weeks convert from nothing?
  Severity hint: material.
- Do two `Reach` cells count over different windows -- one over a quarter,
  another over a year or a release -- while the column is read as one?
  Severity hint: material.
- Does any `Appetite` cell assume a team other than the one the member names?
  Severity hint: material.
- Are the five `Impact` points used to mean different things in different rows
  -- a `3` for a revenue figure in one and for a qualitative judgement in
  another -- so the column ranks nothing?
  Severity hint: material.
- Does the member compare any score, rank or appetite with a figure from another
  team, another product or another roadmap?
  Severity hint: material.
- Has any unit been rescaled -- Impact stretched past the top of its scale, an
  extra confidence tier added, `Effort` given in weeks rather than person-months
  -- so this roadmap's numbers are incomparable with every other while each cell
  looks ordinary?
  Severity hint: material.
- Is any row's `Reach` a count of a different kind of thing from the rest of the
  column -- accounts in one, events in another, sessions in a third -- so the
  multiplication means something different in each?
  Severity hint: minor, material where the rows it affects are adjacent in
  `## Sequence`.

## How to update these guidelines

The four H2 headings above, their order, and the *number* of H3 clusters under
"Review-time red flags" are pinned by
`test_principles_expose_five_red_flag_clusters` in
`skills/product-roadmap/tests/test_product_roadmap_contract.py`. Renaming a
section breaks a caller that quotes it by name, and the cluster count is how
wide a review fans out -- one finder per cluster -- so adding or removing one
changes what a review costs and what goes unasked, and the test and every caller
change in the same commit.

That test pins one thing more: every cluster stays answerable. Each bullet is
one question and one `Severity hint:` line beneath it, and the pairing is what
is checked rather than the presence of each kind somewhere in the cluster.
Rewriting a question as a statement is therefore a red test rather than a style
change, and so is a hint that drifts away from the question it belongs to. A
critic is handed one cluster and nothing else: prose gives it nothing to answer,
and a hint under anything but a question routes a finding nobody asked for.

`test_principles_attribution_stays_checkable`, in the same module, pins
`## Attribution and scope` on three counts. The citation tokens survive, each
being the one thing research settled about its source. The non-affiliation
sentence survives. And two absences hold: the three `${CLAUDE_PLUGIN_ROOT}`
redirects still name files the plugin ships, and this file still nowhere spells
the unknown marker's token. The last two expectations are derived rather than
written into the test -- the redirects from the paths those files occupy, the
token from the substrate's own definition -- so neither can pass while pointing
at something that has moved.

Two things are deliberately unpinned, and a maintainer should know which before
trusting a green suite:

- **The cluster names.** Renaming one, or replacing all five with five others of
  the same shape, is a green suite and a judgement call. The names are prose a
  reader reviews.
- **The arguments, as opposed to the citations.** The seven recorded extensions,
  the guidance on when WSJF, MoSCoW or Kano fit instead, and the reason ICE is
  dropped are held by review alone. A token is checkable and an argument is not,
  and pinning sentences would freeze wording that ought to improve -- so a
  caveat deleted from an extension still goes unnoticed by the suite. That is
  the one place this file's honesty rests on a reader rather than a test.

This file's own name is not this file's to choose, and a rename splits across
two test directories. `skills/product-review/SKILL.md` composes each rubric's
path from its member's owning beat; a rename that still looks like a rubric but
stops matching that composition fails
`test_rubric_template_derives_every_shipped_principles_file` in
`skills/product-review/tests/test_product_review_contract.py`, with a message
about the substrate rather than about this beat. A rename that stops looking
like a rubric at all is invisible to that test, and fails the existence check in
this beat's own contract test instead. Either way the rename is caught, but not
in the place a reader would guess.

The files that quote sections of this file are:

- `skills/product-roadmap/SKILL.md` (cites this file by `${CLAUDE_PLUGIN_ROOT}`
  path as the rubric a `roadmap.md` is written against, and restates no cluster)
- `skills/product-review/SKILL.md` (fleet review of `roadmap.md`: one finder per
  red-flag cluster, quoted verbatim)

This file cites three others and copies none.
`${CLAUDE_PLUGIN_ROOT}/skills/product-roadmap/references/rice-template.md` owns
the four inputs and their units, the appetite's unit and the rule that it is
never raised, both tables' columns, the `ITEM` id rules and the effort-to-
appetite conversion;
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
owns the section names, the provenance format and the unknown marker; and
`${CLAUDE_PLUGIN_ROOT}/skills/product-spec/references/product-spec-principles.md`
owns every judgement about the requirements this member orders. On disagreement,
those files win and a question here is the thing that changes.
