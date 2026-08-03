# PR-FAQ template for brief.md

The shape `docs/product/<slug>/brief.md` is written into. A PR-FAQ is written
as though the product had already launched: the press release says what a
customer gets and why it matters, and the two FAQs answer what that press
release provokes from the two audiences who read it.

Every H2 below is a section of `brief.md`, in the order the member carries
them, and every H3 is one of the press release's eight parts. The section
names and their order are not decided here -- they are published by
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
which this file renders rather than redefines. Nothing below is prose to copy:
each part names what belongs in it and what does not, and the sentences a
brief carries come from the interview and the research sweep.

The press release is one page by convention. No page cap applies to either FAQ
section; they run as long as the questions a real reader would ask.

Three ways to fill a slot, and only three. **Supplied**: the user stated it,
so write it plainly. **Researched**: a public source states it, so write it
with an inline citation to that source. **Unknown**: nobody has established
it, so write the suite's unknown marker, whose literal and payload rules are
defined once under the `## Unknown marker` heading of the artifact-family
contract cited above. A slot is never filled with a plausible figure, and an
invented number is worse than a marked gap: the next member in the chain reads
this one as input and cites what it finds rather than questioning it.

## Press release

The one-page announcement, written for someone outside the company who has
never heard of the product.

### Heading

One line naming the product and the benefit the customer gets from it, as it
would run in the press. No internal codename and no feature list.

### Subheading

One sentence naming the target customer and what they can now do. It sharpens
the heading for the reader who got past it; it does not restate it.

### Summary paragraph

Opens with the dateline -- city, media outlet and launch date -- then gives
the product and its benefit in the words a reader outside the company would
use. A launch date nobody has set takes the marker rather than a guess.

### Problem paragraph

The customer's problem, stated from the customer's side. Not a gap in a
feature set and not an absence of this product: a problem that would still be
a problem if the company never existed. This paragraph is where a problem too
small to be worth solving becomes visible, which is why it is written before
anything about the solution.

### Solution paragraphs

How the product solves that problem, and how it differs from what the customer
does today. The differentiation is written to this construction:

> Today, customers with this problem use x, y, or z products to meet their
> needs. Those products fall short of solving x problem(s). Our product
> addresses these unmet needs in the following ways.

Naming the x, y and z is the step most often skipped. "No alternative exists
today" is almost never true -- the customer has the problem now and is coping
with it somehow, even if the workaround is a spreadsheet or doing without --
and a brief that asserts it has stopped looking rather than finished looking.

### Spokesperson quote

What someone speaking for the company says about why they built it. Authored
for the brief, not collected: it is written as the spokesperson would speak if
the product had launched, and it is never presented as a statement anyone made
or attributed to a named real person without their words. Quotes are never
researched, because the format's device is an authored quote, not evidence.

### Customer quote

What a customer says about what changed for them, in a customer's register
rather than the company's. Authored for the brief on the same terms as the
spokesperson quote: it stands in for the reaction the product is aiming at,
and it is never presented as collected feedback or a real testimonial.

### Getting started

What a reader does next: where the product is, what it costs to begin, and the
first concrete action they take.

## External FAQ

Questions a customer or a journalist would ask after reading the press
release, answered in the same plain register. Nothing here assumes the reader
works at the company. At minimum:

- **Pricing** -- what does it cost, and what does a customer get for each
  price? An undecided price is marked, not estimated.
- **How it works** -- what does the customer actually do, step by step, from
  the outside? Mechanism only where the customer would notice it.
- **Support** -- what happens when it goes wrong, and who does the customer
  reach?
- **Availability** -- who can get it, where, and from when?

## Internal FAQ

Questions a stakeholder inside the company asks before funding the thing. This
is the section where fabrication is most tempting, because every item below
wants a number, and a confident number nobody established is exactly what the
marker exists for. At minimum:

- **Competitive analysis** -- who else serves this customer today, and on what
  basis would a customer choose this instead?
- **Market sizing** -- how large is the addressable market, and what evidence
  of demand exists? A researched figure is written with its source and still
  flagged for an internal bottom-up number, because an analyst's total is not
  the company's own.
- **Per-unit economics** -- what does serving one unit cost, and what does it
  earn?
- **Upfront investment** -- what has to be spent before the first customer is
  served?
- **Regulatory and legal considerations** -- what rules apply, and what would
  have to be cleared before launch?
- **Required capabilities** -- what must the company be able to do that it
  cannot do today?
- **Third-party dependencies** -- whom does this depend on, and what happens
  if they change terms or go away?
- **Risk management** -- what could go wrong, how likely is it, and what is
  the response?
- **What has to be true** -- the assumptions the case rests on, one per line,
  each written so that it could be shown false. An assumption nobody can
  falsify is a belief, and it belongs in the problem paragraph or nowhere.
