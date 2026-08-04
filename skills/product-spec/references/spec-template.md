# Spec template for spec.md

The shape `docs/product/<slug>/spec.md` is written into. This member is the
chain's exit. `brief.md`, `discovery.md` and `requirements.md` all exist to make
it correct, and nothing downstream reads any of the three: `/deep-plan` opens
this file and only this file. Two properties decide whether it is any good, and
both are properties of the whole document rather than of any one section below.

**It is self-contained.** The problem, the validated opportunity, the in-scope
requirements with their upstream ids and acceptance conditions, and the non-goals
are all written out here. A reader never opens an upstream member to understand
this one. That means repeating what those three said, in full, and accepting that
the copy will drift from them as they are corrected -- which is what the
provenance line below exists to report, and why a re-run of this beat is cheap.

**It names no technology.** No library, no framework, no vendor, no datastore, no
schema, no API shape, no data model, no file layout, no directory or file name,
and no function or class name appears anywhere below. Mechanism is the next
reader's decision: `/deep-plan` chooses it after research and records the choice,
with the options it rejected and why, in a plan's `## Decisions made` table. A
spec that names a library has made that decision earlier, on less evidence, in a
document nothing reconciles against the plan -- and no freshness check can catch
the disagreement, because both documents are perfectly fresh and merely disagree.

This file comes in two parts. What sits above `## Problem and opportunity` is how
to write the member and is not part of it: nothing in this preamble is copied into
`spec.md`. From `## Problem and opportunity` onward, every H2 is a section of the
member, and there are exactly three. Those names and their order are not decided
here -- they are published by
`${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`,
which this file renders rather than redefines. Under each heading, what follows
names what belongs there and what does not; none of it is prose to copy.

The member opens above its first heading with one provenance line, the only thing
it carries that no section below holds. It is not drafted here and not written by
hand. It is the `line` field of
`product_artifact.py --provenance-line --member spec.md`, copied verbatim:
do not assemble it, and do not compute a sha. That line's format, and what a sha
that stops matching later means, are published by the artifact-family contract
cited above, which is the one place either is written down. This template does not
reproduce the format, because a second copy of it here would be free to go stale
while still reading as authoritative.

The member carries nothing else structural, and three absences are deliberate.
There is no front-matter block of any kind: a spec is read by people and by one
consumer that treats the file as prose, so a header of parseable key-value pairs
serves neither and amounts to a second, machine-readable copy of what the sections
say, free to disagree with them. There is no inline marker convention of this
document's own for unresolved questions, however tempting one looks while
drafting: the suite has exactly one unknown-value token, the artifact-family
contract defines it, and a second convention invented here would compete with it.
And there is no branch, folder or ticket identifier at the top. Other spec formats
open with one, which couples the document to a numbered-folder workflow this chain
does not have, and the slug already in the path is the only identifier this member
needs.

## Problem and opportunity

Why this work exists: the problem somebody has, and the validated opportunity from
`discovery.md` that this spec answers. Both restated in full, in this member's own
words.

`<the problem: who has it, what it costs them today, and what they do instead --
written so that a reader who has never opened brief.md can judge whether it is
worth solving>`

`OPP<n>` -- `<the validated opportunity, restated in full, carrying the id it was
given in discovery.md>`

Restated, not cited. "See `discovery.md`" is the failure this whole member is
built against: a planner sent upstream re-derives the chain on every run, and any
one of those three documents going stale then poisons a plan silently. Length is
not the concern here -- a reader who cannot act on this section will go and read
four documents anyway, which costs more than the paragraph would have.

The opportunity keeps the `OPP` id it carried upstream, and that id is what the
`Traces to` column below points at. Without it the column has nothing to name, and
a requirement in this spec becomes unattributable to anything a customer wanted.
Where a spec answers more than one validated opportunity, each is restated
separately with its own id, because a `Traces to` cell has to name exactly one of
them.

This is also the section where readability is bought. Every requirement below is
copied word for word and may not be smoothed, so if this document is going to read
as something written for a person, it reads that way here.

## Requirements in scope

The requirements this spec commits to, one per row. Every one of them is already
written in `requirements.md`; this section selects which of them are in scope and
copies them across unchanged.

| ID | Acceptance condition | Traces to |
|---|---|---|
| `REQ1` | `<the sentence from the upstream Requirement cell, copied byte for byte>` | `<the OPP id from the section above that this requirement answers>` |

- **ID** -- the upstream `REQ<n>`, unchanged: not renumbered, not re-prefixed, and
  not reordered into a sequence of this member's own. Upstream ids are permanent
  citation targets that issues and later members already point at, and this beat
  mints no identifiers.
- **Acceptance condition** -- the requirement's sentence, copied byte for byte out
  of the upstream `Requirement` cell. The column is named for what the sentence
  does here rather than for what it was: upstream it is a demand being made, and in
  this member it is what somebody checks the built thing against.
- **Traces to** -- the `OPP` id from `## Problem and opportunity` that this
  requirement answers. The name is the one `requirements.md`'s own table already
  uses for a row pointing at what it answers, reused rather than replaced by a
  second word for the same relationship. Never blank: a requirement whose cell is
  empty either answers nothing or was never checked, and the column exists to tell
  those apart.

Byte for byte means exactly that: no rewording, no repunctuating, no change of
case, and above all no reordering of clauses. The notation these sentences are
written in always puts its clauses in the same order, and that fixed order is what
makes a sentence's missing parts visible, so a sentence whose clauses have moved is
a different requirement rather than a tidier one. Paraphrasing is the degradation
to watch for here precisely because it feels like editing rather than like loss.

An upstream sentence that reads badly, or that says the wrong thing, is not fixed
on the way through. It is reported as a `product-requirements` re-run, and this
beat is run again afterwards.

There is no plain-language gloss beside the condition, and adding one is the change
to resist. Two readings of one obligation sitting side by side means a planner takes
the shorter one, which reintroduces the drift the verbatim copy exists to prevent,
one reader at a time.

A requirement that exists upstream and that this spec is not building does not
belong here and does not simply go missing either. It goes in `## Non-goals` with
its id, which is what makes this table a selection somebody made rather than a copy
somebody left half-finished.

## Non-goals

What this spec deliberately excludes, and what excluding it costs.

| Non-goal | Origin | Cost of excluding it |
|---|---|---|
| `<what is not being built, in one line>` | `<the upstream Out of scope row this carries, or the REQ id left out of the table above>` | `<who wanted it, or what is given up by not having it>` |

- **Non-goal** -- the excluded thing, stated positively enough that a reader can
  tell what would have been built. "Better performance" names no exclusion anybody
  could check.
- **Origin** -- where the exclusion comes from, and it has exactly two permitted
  forms: a row carried from `requirements.md`'s `## Out of scope`, or a `REQ` id
  that is present upstream and absent from `## Requirements in scope`. There is no
  third form. An exclusion with no origin is something one person assumed, arriving
  in the one section a reader trusts to be decisions.
- **Cost of excluding it** -- who wanted this, or what the product gives up without
  it. This is the cell that makes the section worth reading.

The section is never empty. Every product excludes something, and a spec with no
non-goals has not decided its scope -- it has only described the part somebody
happened to write down.

The failure to watch for is the opposite one: a section filled to look complete,
where everything excluded is something nobody wanted anyway. That is what the cost
column is against. The second origin is the strongest defence against it, because a
requirement somebody wrote down and nobody is building has a cost on its face and
needs no argument constructed for it, whereas a carried reason like "not this
release" can be true and still cost nothing.

A `REQ` id appears in at most one of the two tables above. An id in both says the
spec is building the requirement and not building it, and an id in neither is the
silent drop this section exists to prevent.
