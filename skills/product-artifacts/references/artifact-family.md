# Artifact family: docs/product/<slug>/

The published contract for the `docs/product/<slug>/` folder family. Every
beat that reads or writes a member of this chain, and every script or test
that inspects one, cites this file rather than restating any of it. Nothing
here is template content: a member's required sections are named, not
drafted, because drafting the prose inside them is out of scope for this
substrate.

## Members

The chain is closed at five members, each derived from its immediate
predecessor. No member has two upstreams, and the order below is fixed.

| Member | Upstream | Position | Owning skill |
|---|---|---|---|
| `brief.md` | (none) | 1 | `product-brief` |
| `discovery.md` | `brief.md` | 2 | `product-discovery` |
| `requirements.md` | `discovery.md` | 3 | `product-requirements` |
| `spec.md` | `requirements.md` | 4 | `product-spec` |
| `roadmap.md` | `spec.md` | 5 | `product-roadmap` |

The "Owning skill" column is the single published home of the member-to-beat
derivation: a skill that needs to know which beat owns a member reads this
column rather than keeping its own copy.

Each member also has a closed set of required H2 section names. Only the
names are pinned here -- the prose a beat writes under each heading is that
beat's concern, not this substrate's.

- `brief.md`: `## Problem`, `## Audience`, `## Success criteria`, `## Non-goals`
- `discovery.md`: `## Signals`, `## Constraints`, `## Open questions`
- `requirements.md`: `## Scope`, `## Requirements`, `## Out of scope`
- `spec.md`: `## Interfaces`, `## Behavior`, `## Edge cases`
- `roadmap.md`: `## Milestones`, `## Sequencing`, `## Risks`

## Provenance

Every member after the first records where it came from with a single
provenance line, matched anywhere in the member's text:

```
**Derived from**: <upstream member> (<git blob sha>)
```

- `<upstream member>` is a bare member filename such as `brief.md`, never a
  slug-qualified or otherwise path-shaped value: members are always siblings
  in one folder, so a path adds nothing a reader does not already have and
  would break the day the family folder moves.
- `<git blob sha>` is exactly 40 lowercase hexadecimal characters, with no
  abbreviation and no surrounding punctuation beyond the parentheses shown
  above.
- The value equals `git hash-object --no-filters` computed over the
  upstream's raw bytes. It is a git blob object id (a header of the literal
  bytes `blob <byte length>\0` followed by the content, hashed with SHA-1),
  computed in pure standard library with no repository, no commit and no
  `git` executable required. Because it applies no content filter, it will
  not match flagless `git hash-object` in a repository that configures a text
  filter or end-of-line conversion for the member, and it is a SHA-1 blob id
  that will not match the object id `git hash-object` reports in a
  SHA-256 repository.

## Staleness

A freshness check compares each member's recorded provenance sha against the
upstream member's content today and reports one of four closed states:

- `fresh` -- the member is present, its provenance line resolves, and the
  recorded sha matches the upstream's current content.
- `stale` -- the member is present and its provenance line resolves, but the
  recorded sha no longer matches the upstream's current content.
- `unresolvable` -- the member is present but its provenance line is missing,
  malformed, or names an upstream member that does not exist. The first
  member in the chain has no upstream and is therefore never `stale` or
  `unresolvable`.
- `absent` -- the member file itself does not exist.

A finding is never an error: staleness, unresolvability and absence are all
things a caller asked to be told about, not failures of the check itself.

## Re-run behaviour

Every entry point this package ships is idempotent and read-only, with one
exception: `--ensure-folder`, which either creates the slug folder and its
index row or no-ops when both already exist, and never overwrites an existing
member file. This is how the package satisfies epic constraint 12 -- every
beat must define and publish its re-run behaviour -- for a package that ships
no `SKILL.md` of its own to publish it from.

## Unknown marker

This file is the canonical home of the suite's single unknown-value marker
token, the one literal a beat writes into any slot that would otherwise carry
an unsourced figure; the literal itself is landed by issue #16, not here.
