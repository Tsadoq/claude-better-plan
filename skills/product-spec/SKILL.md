---
name: product-spec
description: |
  Turns validated requirements into a self-contained spec at
  docs/product/<slug>/spec.md: the problem, every in-scope requirement carried
  over verbatim, and the non-goals. Names no technology. Refuses when no
  requirements have been written.
argument-hint: "[slug]"
---

# /product-spec

You read a finished `docs/product/<slug>/requirements.md` and write
`docs/product/<slug>/spec.md`. `product-requirements` is your input and the only
member you derive from. `product-roadmap` sequences the specs this beat produces.
`/deep-plan` is what finally reads one, and it opens this file and nothing
upstream of it.

That last fact is the whole design. A planner never opens `brief.md`,
`discovery.md` or `requirements.md`, so whatever this member leaves out is
information nobody downstream will ever see. Two properties follow from it, and
both of them — along with the reasoning that makes them worth obeying — belong to
the template rather than to this file.

Three reference files govern this, and none of them is restated below. Read them
now; do not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/product-spec/references/spec-template.md`
  is the shape and the rules: which sections `spec.md` carries, what belongs in
  every cell of its two tables, what the member deliberately does not carry, and
  why each of those is so. Every step below says what to decide and sends you
  here for what to write.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-spec/references/product-spec-principles.md`
  is the judgement. Its plan-time principles act while you write; its red-flag
  clusters are how a later review will read what you wrote.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  is the contract: the section names and their order, the provenance rules, and
  the unknown marker's exact literal.

What this beat adds to those three is one decision and one discipline. The
decision is which requirements are in scope, and everything else in the member
follows from it. The discipline is that nothing is improved on the way through.
Both are worth stating because neither is checkable afterwards: a run that
smuggled in a mechanism, or that tidied a sentence as it copied it, leaves a
`spec.md` indistinguishable from the one a careful run leaves.

## Step 1: Refuse unless requirements conform

`$ARGUMENTS` is the slug. If it is empty, ask for it with `AskUserQuestion`
before anything else — a slug names someone else's folder and cannot be guessed.

Ask the substrate whether the upstream is there:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --check-freshness --slug <slug> --product-dir docs/product
```

One call answers presence and provenance for the whole chain: read
`requirements.md`'s state out of the entry's `members` map. Derive no state of
your own from the files. Do not stat the folder, do not read a provenance line
yourself, and do not compute a sha — a second reader of those bytes is a second
answer that can disagree with the one every other beat gets.

Never create the folder either. This beat has no business at the substrate's one
writing entry point: it refuses unless `requirements.md` is already there, and a
`requirements.md` that exists sits in a folder with an index row somebody else
already made.

Then three refusals, in this order. Stop at the first one that fires, name which
of the three it was, and name `product-requirements` as the beat to run:

1. **`requirements.md` is absent.** Its state is `absent`, so there is no
   upstream to carry anything from. Run `product-requirements` for this slug
   first.
2. **Its provenance is `unresolvable`.** The line is missing, malformed, or names
   an upstream that does not exist, so nobody can say which `discovery.md` these
   requirements came from. Carrying from it anyway would put a sha over bytes of
   unknown ancestry into the one member a planner reads, and leave this member's
   provenance looking sound while the chain behind it is broken.
3. **No requirement carries a `REQ` id.** Read the tables in `requirements.md`
   for ids of that form. With none there is nothing to select, nothing for the
   first column of this member's own table, and nothing for a non-goal to name as
   the requirement it leaves out.

`stale` is not one of the three. A `requirements.md` whose own upstream has moved
on is still a set of requirements, and refusing over it would have this beat
re-decide something `product-requirements` owns. Report the state to the user,
say a re-run of that beat would settle it, and carry on.

The third refusal is the one no script can make for you. **Never invent a
requirement id**, do not number the rows yourself, and do not offer to work from
`discovery.md` or `brief.md` instead. Three beats stand between a brief and this
member precisely so that every sentence in it is one somebody already committed
to in a testable form.

## Step 2: Select the requirement set and read out what it answers

Work from `requirements.md` and nothing else. Settle three things before writing
any row:

- **Which `REQ` ids this spec commits to.** This is the beat's one genuine
  decision. The upstream set is the menu rather than the answer, and every id you
  leave out becomes a non-goal in step 4 instead of a silent omission. Ask the
  user with `AskUserQuestion` where the scope is genuinely open —
  `requirements.md` settles what has to be true of the product, never which slice
  is being built now.
- **The problem the selected set addresses.**
- **The validated opportunity it answers, with the `OPP` id it carries
  upstream.** That id is what each carried row will trace to.

Both of the last two are written into this member in full rather than cited. The
template says what "in full" means here and why a citation upstream will not do.

## Step 3: Carry each selected requirement across unchanged

Carry every selected requirement's `REQ` id and its sentence **byte-for-byte**.
The template states exactly what that forbids and why the prohibition is worth
the awkwardness; read it there before writing the first row, because the failure
it prevents feels like tidying rather than like loss while you are committing it.

Where a sentence you have to carry is wrong, or merely bad, neither fix it nor
annotate it. Route the defect to a `product-requirements` re-run, then run this
beat again. That round trip buys one notation in the chain instead
of two, and it is cheap: this beat is a copy with one decision in it, so
re-running costs a fraction of what reconciling two versions of an obligation
costs later.

## Step 4: Write the non-goals, each with what it costs

Exactly two origins are permitted for a non-goal, the template names both, and
there is no third. Every non-goal carries what excluding it costs.

The judgement this step needs is the one the template's own warning is about:
the section is easiest to fill with things nobody wanted, and hardest to fill
honestly. Work it against the rubric's cluster on the subject rather than against
your sense of whether the list looks long enough.

## Step 5: Get the provenance line, then write

Read the finished provenance line off the substrate:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --provenance-line --slug <slug> --member spec.md --product-dir docs/product
```

Write its `line` field into `spec.md` verbatim: do not assemble a line, and do
not compute a sha yourself. The `--member spec.md` argument is what makes the
line this member's own — it names the member being written, and the sha comes
back over that member's upstream. If the field is null, the upstream you refused
over in step 1 is still missing; go back rather than inventing a line.

Say in one line what `## Re-run behaviour` below states, then write the file: the
sections in the order the artifact-family contract publishes them, filled per the
template.

**Never write to `requirements.md`.** Not to fix a sentence you had to carry, not
to renumber a row, not to add the id a non-goal wanted. The sha you have just
written into `spec.md` is over `requirements.md`'s bytes, so editing the upstream
would mark the member you are finishing stale the moment you finished it, over an
edit nobody asked for. Anything the upstream gets wrong is reported to the user
as a `product-requirements` re-run.

## Step 6: Report

Report the path written, how many requirements it carries, and how many non-goals
it carries broken down by which of the two origins each came from. That breakdown
earns its line: a list of exclusions all carried from upstream is a list nobody
made a decision in.

Then state the one thing this beat cannot check and nothing downstream will ever
report. Where a spec has **already been consumed by a plan**, replacing it does
not reach that plan: nothing links the two, no freshness check spans them, and
the plan goes on citing requirements this spec no longer carries while reporting
nothing wrong. Say it on every run rather than only when a plan is known to
exist — this beat is given no way to find out whether one does, so a warning
conditional on knowing is a warning that never fires.

Finally, state plainly what this document is not. It is not a plan and not a
design: it says what is being built and what is not, and every question of how it
gets built is `/deep-plan`'s, made with research this beat did not do.

## Re-run behaviour

A second run **replaces `spec.md` wholesale**, from whatever `requirements.md`
says at that moment. The version being overwritten is not recoverable:
`docs/product/` is gitignored, so there is no earlier copy to retrieve and no
diff to read.

That is deliberate, and it is what makes the verbatim carry in step 3 affordable.
The copy this member is built on drifts as its upstream is corrected, and the
answer to that drift is not to reconcile two documents by hand; it is to run this
beat again, cheaply, and let the new provenance line record what it was derived
from. A beat that preserved the old rows instead would accumulate sentences no
upstream still says, while every freshness check reported the member as sound.

Announce the replacement in step 5 as a statement, not a confirmation prompt: do
not ask permission and do not offer to merge the two versions. What does need
saying out loud is the warning step 6 carries, because a plan somebody has
already written is the one thing a replacement cannot reach.

Nothing else on disk changes. This beat creates no folder and refreshes no index:
it refuses unless `requirements.md` exists, and a `requirements.md` that exists
is one whose folder someone else already made.
