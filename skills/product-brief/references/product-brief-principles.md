# Product brief principles

## Attribution and scope

The failure modes below are drawn from published PR-FAQ practice — Amazon's Working Backwards resource and practitioner write-ups of it — and from the product-discovery literature that predates the format. The wording is independently paraphrased and reorganized as questions asked of a finished brief rather than as advice for writing one. This project is not affiliated with or endorsed by Amazon or by any author cited here.

Lean Canvas and the Business Model Canvas are named here as cited comparison points and nowhere else. They are the best-known alternatives for the same job — one page stating a business idea before anything is built — and their most-reported failure is the one cluster 1 catches: the Solution box gets filled in before the Problem box has been validated, and the canvas then reads as a plan for something nobody has shown is wanted. Neither is an alternate template here. `product-brief` writes a PR-FAQ, there is no framework flag, and no red flag below is answered by switching format.

Scope: this file is the single source of truth for judging a written `brief.md` — whether it is honest, and whether the thing it describes is worth doing. It is not the brief's shape. Two boundaries keep it from restating its neighbours:

- **Judgement, not shape.** What each section holds is `pr-faq-template.md`'s job, and the section names, the provenance rules and the unknown marker belong to `artifact-family.md`. A question below may name a section or the marker; it never redefines one.
- **The brief, not the idea.** A finding says the brief failed to establish something, never that the product is a bad idea. The evidence a reviewer has is the document.

Orchestrators quote one section, or one H3 cluster, into an agent prompt; nothing here is duplicated elsewhere.

## Plan-time principles

These act while the brief is being written. They pull against the instinct to make the document persuasive — the honest brief is rarely the exciting one — so name the tension rather than quietly resolving it.

- **Problem before solution.** Write the problem paragraph, and be ready to defend it, before writing a sentence about what the product does. A problem reached by working backwards from a thing already built is a description of that thing.
- **The customer's words, not the company's.** State the problem as the person who has it would state it. A problem expressible only in the company's vocabulary — a missing feature, an unsupported integration — is a gap in a product, not a problem in someone's day.
- **Find today's workaround before claiming the gap.** Everyone with the problem is coping with it now: a spreadsheet, a competitor, an assistant, or doing without. Establishing what that is comes before saying what is missing, because "nothing exists" is a claim about how hard the author looked.
- **Write to be falsified.** Every assumption goes down in a form that evidence could refute. The brief's job is to surface why this might fail while failing is still cheap; a document nobody could disagree with has been optimised for approval.
- **One customer, one problem.** A brief serving three segments has usually chosen none of them. Pick the one whose problem can be told end to end, and let the others be consequences rather than promises.
- **Size the problem, not only the market.** What the problem costs the person who has it decides whether it is worth solving; the market total decides only how many such people exist. A large market for a small annoyance is still a small business.

## Review-time red flags

Each cluster below is quoted verbatim into one critic. Every question is answerable yes/no against a written `brief.md`; "yes" is a finding. Severity hints are defaults — a critic may upgrade or downgrade with evidence. Cite the section and the sentence: a finding the author cannot locate in their own brief is not actionable. A slot carrying the unknown marker is not a finding on its own — the marker is the brief doing its job — unless a question below says otherwise.

### Solution-first writing

The brief was built from what the team can build rather than from a problem someone has.

- Strike every mention of the product from the problem paragraph: is there no problem left standing in what remains?
  Severity hint: material.
- Is the problem stated only in the company's vocabulary — a missing feature, an unsupported integration, an unmet internal requirement — rather than in words the customer would use about their own day?
  Severity hint: material.
- Does every claim about the problem trace back to the team's own belief, with no interview, support ticket, usage figure or cited study behind any of it?
  Severity hint: material.
- Does the press release introduce the capability before it names the person who needs it, so the reader meets the product before the problem?
  Severity hint: minor, material when the problem paragraph never names a customer at all.
- Does the target customer read as whoever the built thing would suit — a segment the company already serves, with no sign another was considered?
  Severity hint: minor.

### Selling rather than truth-seeking

The brief is written to get approved rather than to surface why the idea might fail.

- Does the brief contain no statement that could turn out false — no assumption, no risk, no condition — so there is nothing for an approver to disagree with?
  Severity hint: material.
- Is any quantity — a count, a percentage, a currency amount, a date — stated with neither a source nor the unknown marker, so a reader cannot tell whether anyone established it?
  Severity hint: material.
- Are the what-has-to-be-true assumptions written so that no evidence could refute them ("customers value quality"), making the list decorative?
  Severity hint: material.
- Do the authored quotes carry an argument that appears nowhere else in the brief, so an invented voice is doing the persuading?
  Severity hint: material.
- Reading the internal FAQ against the canonical item list in `pr-faq-template.md` rather than against anything stated here, does it answer only the questions that flatter the idea and leave a required item unaddressed?
  Severity hint: minor, material when the omitted item is the one the idea most obviously turns on.
- Is the risk section written as reassurance ("we are confident that…") rather than as exposure of what would have to go wrong?
  Severity hint: minor.

### Discounting existing workarounds

The brief claims nothing like this exists today without naming what customers do right now.

- Does the brief assert that no alternative exists, that the space is greenfield, or that customers have no way to do this today?
  Severity hint: material.
- Does the solution paragraph name no product, tool or manual routine the customer uses now, leaving the differentiation with nothing to differ from?
  Severity hint: material.
- Are the named alternatives all direct competitors, with no manual workaround — a spreadsheet, an email thread, an assistant, doing without — among them?
  Severity hint: material.
- Does the brief say how the alternatives fall short without saying what they get right, so the comparison could not have been made by anyone who used them?
  Severity hint: minor, material when that shortfall is the brief's whole differentiation.
- Is leaving the current workaround treated as free — no migration, no habit, no retraining — so adoption needs no explanation?
  Severity hint: minor.

### Solving a non-meaningful problem

The problem is real but not worth anyone's money or attention.

- Is the problem's cost to the person who has it left unstated — neither how often it bites nor what it costs them when it does — so the brief establishes only that the problem exists?
  Severity hint: material.
- Is a market total the only evidence of demand, with nothing showing that people with this problem already spend money, time or effort on it?
  Severity hint: material.
- Would a customer plausibly keep their current workaround even at zero switching cost, because the improvement is smaller than the bother of changing?
  Severity hint: material.
- Does the brief serve so many use cases or segments that no single customer's problem is told end to end?
  Severity hint: material.
- Does the getting-started step assume a reader already looking for this product, so the brief presumes the demand it was meant to establish?
  Severity hint: minor.

## How to update these guidelines

The four H2 headings above and the four-cluster H3 structure under "Review-time red flags" are pinned by `skills/product-brief/tests/test_product_brief_contract.py` (`test_principles_expose_four_red_flag_clusters`); renaming a section breaks callers that quote it by name, and adding a fifth cluster changes how many finders a review launches, so change the test and every caller in the same commit. The files that quote sections of this file are:

- `skills/product-brief/SKILL.md` (cites this file by `${CLAUDE_PLUGIN_ROOT}` path as the rubric a brief is written against, and restates no cluster)
- `skills/product-review/SKILL.md` (fleet review of `brief.md`: one finder per red-flag cluster, quoted verbatim; composes this path from the member's owning beat rather than naming it, so a rename that puts this file beyond that composition's reach fails `test_rubric_template_derives_every_shipped_principles_file`, not any test here)

This file cites two others and copies neither. `${CLAUDE_PLUGIN_ROOT}/skills/product-brief/references/pr-faq-template.md` owns what each section of a brief holds, and `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md` owns the section names, the provenance format and the unknown marker. On disagreement, those files win and a question here is the thing that changes.
