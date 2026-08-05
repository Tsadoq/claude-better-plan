---
name: product-issues
description: |
  Turns the items in docs/product/<slug>/roadmap.md into implementable slices at
  docs/product/<slug>/issues/, one markdown file each, then files them as GitHub
  issues if you ask. Refuses when no roadmap has been written.
argument-hint: "[slug]"
---

# /product-issues

You read a finished `docs/product/<slug>/roadmap.md` and write
`docs/product/<slug>/issues/`, a folder holding one markdown file per slice of
work. `product-roadmap` is your input and the only member you derive from. The
roadmap says what gets built and in what order; an item there is a group of
requirements that made sense to score together, which is a different thing from
a piece of work one person can pick up and finish, and supplying those pieces is
the whole of what this beat adds.

`issues/` is not a sixth chain member. The family is closed at five, `brief.md`
through `roadmap.md`, and this folder sits beside them rather than after them.

Two facts follow from that and shape every step below.

**This is the only beat whose output can leave the repository.** Every other one
writes a markdown file that a reviewer reads as a diff and undoes with
`git checkout`. A create call against somebody's tracker cannot be undone, and a
batch that dies halfway leaves an unknown subset filed against a team that did
not ask for it. That is why step 4 shows a dry run first and files nothing
without being told to, and why the destination is asked rather than assumed.

**No freshness check in this suite reads a slice.** Nothing downstream of
`roadmap.md` is a chain member, so nothing will ever tell you that the roadmap
moved after a slice was cut from it, or that a slice id changed under something
citing it. `## Re-run behaviour` at the bottom of this file is therefore read
before a second run touches an existing folder, not after.

Three reference files govern this, and none of them is restated below. Read them
now; do not work from memory on anything they own.

- `${CLAUDE_PLUGIN_ROOT}/skills/product-issues/references/story-map-template.md`
  is the shape and the rules: the backbone and what may never be on it, what row
  one is and the one question it has to pass, the five SPIDR patterns, where the
  INVEST gate is published, the frontmatter schema every slice carries, and the
  six body sections with the roadmap sha among them.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-issues/references/product-issues-principles.md`
  is the judgement. Its plan-time principles act while you cut; its red-flag
  clusters are how a later review will read the set you wrote.
- `${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md`
  is the contract: the chain's members, the provenance rules, and the unknown
  marker's exact literal.

What this beat adds to those three is two decisions and one discipline. The
decisions are **where the cuts fall** — which slices an item becomes, which
nothing upstream settles — and **where the slices go**, which is the user's to
make and not yours. The discipline is that **nothing is filed that the user has
not seen first**. All three are worth stating because none is checkable
afterwards: a set cut down architectural layers looks exactly as finished as one
cut across a backbone, and a filed issue nobody reviewed looks exactly like a
filed issue somebody did.

## Step 1: Refuse unless the roadmap conforms

`$ARGUMENTS` is the slug. If it is empty, ask for it with `AskUserQuestion`
before anything else — a slug names someone else's folder and cannot be guessed.

Ask the substrate whether the upstream is there:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-artifacts/scripts/product_artifact.py \
  --check-freshness --slug <slug> --product-dir docs/product
```

One call answers presence and provenance for the whole chain: read `roadmap.md`'s
state out of the entry's `members` map. Derive no state of your own from the
files. Do not stat the folder, do not read a provenance line yourself, and do not
compute a sha — a second reader of those bytes is a second answer that can
disagree with the one every other beat gets.

Read that entry for `roadmap.md` and stop there. This beat gates on its
**immediate upstream** alone: whether `spec.md` has moved under `roadmap.md` is a
state `product-roadmap` already decided to live with, and a run that refuses over
it re-opens a question two beats away from anything it writes.

Never create the folder either. `--ensure-folder` is the only entry point in this
suite that writes anything outside a member, and this beat never reaches for it:
it refuses unless `roadmap.md` is already there, and a `roadmap.md` that exists
sits in a folder somebody else already made. The one directory this beat creates
is `issues/` itself, inside a folder that already exists.

Then three refusals, in this order. Stop at the first one that fires, say which
of the three it was, and name `product-roadmap` as the beat to run:

1. **`roadmap.md` is absent.** Its state is `absent`, so there is nothing to cut:
   a slice is cut from an item, and there are no items.
2. **Its provenance is `unresolvable`.** What puts a member in that state is
   written in the artifact-family contract and nowhere else; read it there. What
   it means here is that nobody can say which `spec.md` this roadmap was derived
   from. Slicing it anyway would put work in front of a team on the authority of
   bytes of unknown ancestry, and every slice would record a sha of them.
3. **No item carries an `ITEM` id.** Read `roadmap.md` for ids of that form. With
   none there is nothing for a slice's `roadmap_item` key to name, so every slice
   would be unmoored by construction — and pre-flight refuses a set whose
   `roadmap_item` values are not ids present in that member, so a run that
   carried on would refuse at the far end having done all the work first.

`stale` is not one of the three. A `roadmap.md` whose own upstream has moved on
is still a roadmap, and refusing over it would have this beat re-decide something
`product-roadmap` owns. Report the state to the user, say a re-run of that beat
would settle it, and carry on.

The third refusal is the one no script can make for you. **Never invent an `ITEM`
id**, and do not offer to slice from `spec.md` or `requirements.md` instead. Five
beats stand between a brief and this folder precisely so that everything filed
here is work somebody already committed to building, in an order somebody already
argued for.

## Step 2: Ask where the slices go

Ask with `AskUserQuestion`, and ask before cutting rather than after, because the
answer decides what step 4 does and what the user has to have ready. Two options:

- **markdown** — stop when the folder is written. The slices are on disk,
  reviewable as a diff and revertible with `git checkout`, and nothing leaves the
  repository.
- **GitHub** — write the folder, then file the slices as issues into a repository
  the user names. This needs `owner/name`, and optionally the number of a parent
  issue to file the batch under; ask for both in the same call.

**GitLab and Jira are not implemented.** Say so plainly if either is asked for,
and do not offer to improvise one. This suite captures its fixtures from real
invocations rather than writing them from memory, and neither tracker could be
reached from where this was built: shipping a wire format nobody has exercised,
behind a menu entry that looks like the two that work, is worse than the absence.
What is available instead is the markdown destination, whose files somebody can
paste, import, or file by hand.

The answer changes nothing about step 3. The slices are the same bytes either
way, which is deliberate: a set cut with one tracker in mind is a set carrying
that tracker's assumptions, and this folder outlives any of them.

## Step 3: Cut the slices and write the folder

Work from `roadmap.md` and the story map template. Read that template before
cutting rather than after — the backbone, row one and its test, and the SPIDR
patterns are all its to state, and the split it warns against is exactly the one
a run produces when it has read only the instruction here.

Four things are this step's to settle, and the template says what each one has to
satisfy:

- **The backbone**. The template defines it and gives the one test it has to
  pass; what this step decides is which activities this product's items sit
  under.
- **Row one**, and whether it passes the template's one question. Everything else
  is a later row.
- **Each cut**, made with a named SPIDR pattern rather than by making things
  smaller until they look small.
- **The id width**, settled before the first id is written. The template says why
  it cannot be revised afterwards.

Every slice passes the INVEST gate before its file is written. The gate lives at
`${CLAUDE_PLUGIN_ROOT}/skills/product-requirements/references/requirements-template.md`
under `## The INVEST gate`, is cited by the template, and is restated in neither
place — go and read it.

Then write one markdown file per slice into `docs/product/<slug>/issues/`, and
put nothing else in that folder. Frontmatter keys and body sections are the
template's; two of them are worth naming here because they are the ones a run
gets wrong quietly:

- `roadmap_item` names the `ITEM` id the slice was cut from, and every slice
  carries one. A slice with no upstream basis is work somebody added on the way
  past.
- `## References` carries a sha of `roadmap.md`. Which value it is, where to take
  it from, and what its format must not borrow are all the template's to say, and
  all three are things a run will supply from memory if it does not go and look.

**A slice with an open question in it is not filable.** Where a value nobody has
established would go, the unknown marker goes instead — its literal and payload
rules live under the `## Unknown marker` heading of the artifact-family contract,
so copy them from there rather than reconstructing either. Pre-flight refuses the
whole batch over one such slice rather than filing the rest, because a partial
batch missing exactly the undecided slice looks complete. Decide it, or leave
that slice out of this run.

## Step 4: Show the dry run, then file only on explicit confirmation

If the destination is markdown, report what step 3 wrote and stop:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-issues/scripts/file_issues.py \
  --slug <slug> --product-dir docs/product --destination markdown
```

If it is GitHub, run the same command without `--file` first. That is not a flag
you may skip: without it the run builds a transport that describes every call and
makes none.

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-issues/scripts/file_issues.py \
  --slug <slug> --product-dir docs/product --destination github \
  --repo <owner/name> [--parent <n>]
```

One thing the preview cannot cover, and the user hears it before they confirm
rather than after. Reading the parent issue's current children and its depth is
itself a call, so a dry run does not make it: the run reports `ceilings` as
unread, and the two refusals that rest on those numbers — too many sub-issues
under one parent, too deep a nest — cannot fire until the real run. A batch that
was confirmed on a clean preview can still be refused with nothing filed.

Show the user what came back, in these terms: how many slices are `planned`, how
many were `skipped` as already filed, what `ceilings` says, and the `calls` the
run would have made, each one a summary and the call itself. Then ask for
confirmation **in that turn, for that sequence**. The destination answer in step
2 is not it: that was a choice of where, made before anybody could see what would
be sent.

Only then re-run the same command with `--file` appended. Never put `--file` on
the first run, never file a sequence the user has not been shown, and never file
a shorter or longer set than the one they confirmed.

The script refuses on its own account before any call goes out, and its refusals
are yours to report rather than to work around: a slice carrying the unknown
marker, a batch that would push the parent past a hundred sub-issues or past the
nesting ceiling, and a slice whose `roadmap_item` names no `ITEM` in
`roadmap.md`. Each refuses the whole batch with nothing filed. Fix the slices and
run the dry run again; do not file the remainder by hand.

If a run fails part-way, it prints its report alongside the error. Read `issues`
there before doing anything else: those slices are filed and their ledger entries
are already written, so the fix is a second run, which skips them.

## Step 5: Report

Report the **folder written** and how many slices it holds, how many activities
the backbone came out as, and — where a tracker was the destination — how many
were filed, how many were skipped as already filed, and into which repository.

Then say plainly what this folder is not. It is not a chain member and nothing
checks it: no freshness check reads a slice, so nothing will report that the
roadmap moved under one, and the sha in `## References` is there for a person to
check by hand. It is also not a plan. How any one slice gets built is
`/deep-plan`'s question, asked with research this beat did not do.

## Re-run behaviour

A second run **adds to `issues/`**. It does not rewrite the folder, and the
reason is the ids.

- A slice id is **never renumbered and never reused**. A re-run gives new slices
  the next numbers after the highest ever used in this folder, retired ones
  included, and leaves every existing id exactly as it is.
- A slice already carrying a **`filed_<destination>` entry is skipped** and
  counted as skipped, which is what makes a second run file the remainder rather
  than a duplicate set. Two layers enforce it: the run skips such a slice, and
  the adapter refuses a batch that still contains one. Never delete or edit a
  ledger entry by hand — that is precisely how a duplicate gets filed, and the
  tracker will not tell you.
- A slice that has been filed is **not rewritten in place**. The tracker holds a
  copy of its body and nothing in this beat updates one, so an edit here would
  leave two versions with no way to tell which the implementer read. Cut a new
  slice, and say in it what changed.
- A slice the re-run decides against is retired by **leaving it alone**, not by
  deletion. Its id stays where it is; other slices' `## Blocked by` sections name
  ids, and a deleted file makes a reference nobody can resolve.

Why the rule exists, and not only what it says. A slice id is cited from outside
this folder — by other slices, and by whatever was filed to a tracker where no
check in this suite reaches. The chain's mechanism compares an upstream's content
hash and never inspects a downstream identifier, so a renumbering that tidies the
folder leaves every member reporting `fresh` while every citation into it now
points at different work. A review is the whole of this rule's enforcement.

**This beat never writes to `roadmap.md`.** Not to add an `ITEM` a slice wanted,
not to reword one so a slice traces to it more neatly, not to record that
something was filed. Every slice carries a sha over that file's bytes, so editing
it would date the whole folder the moment the folder was finished, over an edit
nobody asked for. The same holds for every other chain member. Anything the
roadmap gets wrong is reported to the user as a `product-roadmap` re-run.
