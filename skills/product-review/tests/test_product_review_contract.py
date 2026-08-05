"""Contract tests for `product-review`: which rubric it selects, and what it declares.

`product-review` is the one critic-fleet caller in this plugin whose cluster
source is not fixed. Every other caller names one principles file forever; this
one derives a path per target, from the `Owning skill` columns of
skills/product-artifacts/references/artifact-family.md -- the chain's member
table and the non-member artifacts published beside it -- and a single path
template published in its own SKILL.md. That derivation is what is worth
pinning: a target judged against another beat's rubric reads as a clean review,
and nothing else in this repository would notice.

So the first two tests read the template out of the shipped SKILL.md rather than
keeping a copy of it, run it over the beats the substrate names, and check the
result against the rubrics actually on disk -- from both directions, because
each catches a different drift: no shipped rubric is unreachable, and no
produced path escapes the rubric tree. The rest read the skill's own
declarations: the tool denial that makes it read-only, that it cites its two
contracts instead of restating them, and the runtime rules it publishes as
prose.

Which keys the frontmatter declares is read through tests/guarantees.py rather
than parsed here, which is why that module's `frontmatter_value` is public: a
second parser would eventually disagree with it about folded scalars and YAML
sequences, and this module would then report a declaration the harness never
read. Only the body split is local, because guarantees.py exposes the keys
inside the block and not the remainder.

Scoped deliberately narrow. That the member table's `Owning skill` column is a
complete bijection, and that each beat it names is well formed and invocable, is
pinned by skills/product-status/tests/test_product_status_contract.py; this
module consumes that column and asserts only what the template does with it. The
non-member table has no such second reader, so what this module needs from it is
asserted here and nothing more: that it names a beat at all, and that the beat's
rubric is one the template reaches. Nothing here measures description or
listing-entry length either: tests/test_description_budget.py owns every such
comparison and fails the build on a second one.

Runnable two ways:
    python3 skills/product-review/tests/test_product_review_contract.py
    python3 -m pytest skills/product-review/tests/test_product_review_contract.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "skills" / "product-review" / "SKILL.md"
ARTIFACT_FAMILY = REPO / "skills" / "product-artifacts" / "references" / "artifact-family.md"

# The sections this module reads out of documents it does not own. The two
# tables are what the family publishes about ownership: `## Members` is the
# closed chain, `## Non-member artifacts` is everything else a beat writes into
# the same folder. Reviewability follows from being in the family, not from
# being in the chain, so this module reads both and neither alone.
MEMBERS_HEADING = "## Members"
NON_MEMBERS_HEADING = "## Non-member artifacts"
PROVENANCE_HEADING = "## Provenance"

# The columns this module reads. Cells are looked up by header rather than by
# position: the column *order* of `## Members` is
# test_product_status_contract.py's contract with that table, and a second copy
# of it here would be a second thing to keep in step. `Owning skill` is the one
# column both tables carry, and the only one the rubric path is composed from;
# the other two only name what the row is about, so a table missing its own is a
# table this module cannot report a row of. They are spelled differently because
# they hold different things: a member is one file the chain names, a non-member
# artifact is the folder its beat writes.
MEMBER_COLUMN = "Member"
FOLDER_COLUMN = "Folder"
OWNING_SKILL_COLUMN = "Owning skill"

# The rubric-path template as SKILL.md publishes it, in placeholder form. One
# capture group, referred to twice: the same slot has to fill the directory and
# the filename, so a template that composed the two from different things is
# not lifted at all -- which surfaces as the `expected exactly 1` failure rather
# than as a silent pass over a half-checked mapping.
RUBRIC_TEMPLATE = re.compile(r"skills/<(?P<slot>[^<>/]+)>/references/<(?P=slot)>-principles\.md")

# Where a produced path is allowed to land, full-matched one path at a time.
# The directory segments exclude `.` as well as `/`, so a beat name that walked
# up out of the tree cannot satisfy it.
RUBRIC_TREE = re.compile(r"skills/product-[\w-]+/references/[\w.-]+\.md")

# Every rubric the skill could ever need to reach, as the repository ships them
# today. Globbed from the repo root so the match is over the same relative
# spelling the template produces.
RUBRIC_GLOB = "skills/product-*/references/product-*-principles.md"

# The fan-out shape a rubric has to expose. `RED_FLAGS_HEADING` is a whole
# heading; `CLUSTER_PREFIX` is only the level marker a cluster heading opens
# with, matched with `startswith` and sliced off -- the cluster names themselves
# belong to each rubric and are pinned nowhere here.
RED_FLAGS_HEADING = "## Review-time red flags"
CLUSTER_PREFIX = "### "

# The two contracts the body must cite, spelled as the citation itself rather
# than as a bare filename. The `${CLAUDE_PLUGIN_ROOT}` form is the one a reader
# of an installed plugin can actually follow, and it is what the epic requires.
PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
CITED_CONTRACTS = (
    f"{PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md",
    f"{PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md",
)

# The tools the skill must deny by bare name, and the field that denies them.
# `disallowed-tools` is the only frontmatter field that removes a tool --
# `allowed-tools` grants pre-approval and restricts nothing -- so the read-only
# promise is kept here or nowhere. `Bash` is on the list because a skill holding
# a shell still holds a way to write, and every chain member after the first
# records a hash of its upstream: an edit by the reviewer manufactures the
# staleness it was never asked to judge.
DENIED_FIELD = "disallowed-tools"
DENIED_TOOLS = ("Write", "Edit", "NotebookEdit", "Bash")

# The field that must not appear at all. Its absence, rather than its contents,
# is the assertion; see `test_frontmatter_declares_the_read_only_contract`.
GRANT_FIELD = "allowed-tools"

# One stable token per runtime rule the skill is required to publish, mapped to
# the rule it anchors. Tokens rather than sentences: the wording of a shipped
# report format is its author's, and pinning whole sentences would mean editing
# CI to reword prose.
#
# Each token is one the rejected form of its rule would not carry. `unreviewable`
# is the clearest case: the alternatives it rules out are judging the member
# against some other beat's rubric and saying nothing about it, and both of those
# would still use the words `rubric` and `missing` somewhere.
#
# What this shape cannot do is read the sentence a token sits in, so a body
# stating the opposite of a rule while still carrying its token would pass. That
# is accepted rather than overlooked: the alternative is pinning whole sentences,
# which turns rewording shipped prose into a CI edit. The tokens are chosen so
# that a rule going *absent* is what fails, which is the drift that happens.
RUNTIME_ANCHORS = {
    "main thread": (
        "where it runs, which is what decides whether the recipe's `## Nested fleets` "
        "obligations bind it -- and a backgrounded finder reports no findings"
    ),
    "docs/product/<slug>/*.md": (
        "the slug-enumeration rule, which is a glob over the folder intersected with the "
        "published member set. It has to stay a glob: the frontmatter denies `Bash`, so the "
        "substrate script this replaced could not be run even if the body asked for it"
    ),
    "`Folder` column": (
        "the other half of that rule, which is what reaches a beat owning no chain member: "
        "the family publishes two ownership tables, and a body that enumerated only the "
        "first would compose that beat's rubric path perfectly and never once select it. "
        "The rubric-coverage test above cannot see this -- it asks what the template "
        "*could* reach, and reachability nothing enumerates is reachability on paper"
    ),
    "unreviewable": (
        "the missing-rubric rule, which reports the target and the path it expected rather "
        "than judging it against another beat's rubric or passing over it in silence"
    ),
    "never merged": (
        "the one-block-per-target rule, which keeps a finding attached to the rubric it was "
        "judged against"
    ),
    "re-read": (
        "the re-run rule, which is that every invocation reads current state afresh and "
        "writes nothing"
    ),
}

# The fence that opens and closes a frontmatter block, and the one that opens
# and closes a markdown code block.
FENCE = "---"
CODE_FENCE = "```"


def _guarantees() -> ModuleType:
    """Load the repo-level tests/guarantees.py by path, for its frontmatter parser.

    This repository has one definition of what a top-level frontmatter key is,
    and it is public for exactly this reason. A second parser here would
    eventually disagree with it about folded scalars and YAML sequences, and the
    disagreement would be silent in the permissive direction: this module would
    report a denial the harness never read.

    Loaded inside the one test that needs it rather than at import, so this
    module still runs as a standalone script where the repo-level tests/
    directory is absent.
    """
    source = REPO / "tests" / "guarantees.py"
    spec = importlib.util.spec_from_file_location("guarantees", source)
    assert spec and spec.loader, f"cannot load {source}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _section(text: str, heading: str) -> str | None:
    """One H2 section's body, from just after `heading` to the next `## `, or None.

    Three readers below want one named section out of a document they do not own
    -- the member table, the provenance template, a rubric's red-flag clusters --
    and the span rule is the same for all three.
    """
    marker = f"\n{heading}\n"
    start = text.find(marker)
    if start == -1:
        return None

    body = text[start + len(marker) :]
    end = body.find("\n## ")
    return body if end == -1 else body[:end]


def _cells(row: str) -> list[str]:
    """Split one markdown table row into undecorated cell values.

    Backticks are stripped so assertions compare published names rather than
    the document's formatting choices.
    """
    return [cell.strip().strip("`").strip() for cell in row.strip().strip("|").split("|")]


def _family_table(heading: str, subject_column: str) -> list[dict[str, str]]:
    """One published ownership table as `{column: cell}` per row, in table order.

    Shared by both tables the family publishes, because what this module wants
    from each is the same: rows carrying a subject and the beat that owns it.
    `subject_column` is the header naming what a row is about -- `Member` for
    the chain, `Folder` for what a beat writes beside it -- and is required
    alongside the owning-skill column so that a table which had lost its subject
    is reported here rather than read as a list of ownerless beats.

    Raises rather than returning an empty list when the section, the table, or
    either column is missing. Everything below is a statement about rows, and a
    document that had stopped publishing the contract would satisfy several of
    them by having none.
    """
    section = _section(ARTIFACT_FAMILY.read_text(encoding="utf-8"), heading)
    if section is None:
        raise AssertionError(f"{ARTIFACT_FAMILY} publishes no `{heading}` section")

    # A markdown table is a run of pipe lines: header, separator, then rows.
    pipe_lines = [line for line in section.splitlines() if line.lstrip().startswith("|")]
    if len(pipe_lines) < 3:
        raise AssertionError(
            f"`{heading}` in {ARTIFACT_FAMILY} carries {len(pipe_lines)} pipe lines; "
            f"expected a header, a separator and at least one row"
        )

    columns = _cells(pipe_lines[0])
    for needed in (subject_column, OWNING_SKILL_COLUMN):
        if needed not in columns:
            raise AssertionError(
                f"`{heading}` in {ARTIFACT_FAMILY} has columns {columns}, which do not "
                f"include {needed!r}; those columns are where product-review reads the mapping "
                f"it composes its rubric path from, so an absence is the mapping being gone"
            )

    rows: list[dict[str, str]] = []
    for line in pipe_lines[2:]:
        cells = _cells(line)
        if len(cells) != len(columns):
            raise AssertionError(
                f"`{heading}` row {line!r} has {len(cells)} cells, expected {len(columns)}"
            )
        rows.append(dict(zip(columns, cells, strict=True)))
    return rows


def _member_beats() -> list[str]:
    """The beat owning each chain member, in chain order."""
    return [row[OWNING_SKILL_COLUMN] for row in _family_table(MEMBERS_HEADING, MEMBER_COLUMN)]


def _non_member_beats() -> list[str]:
    """The beat owning each family artifact that is not a chain member.

    A separate reader rather than a flag on the one above, because the two
    tables mean different things and only one of them is the chain: freshness,
    provenance and chain order are statements about members, and a caller that
    conflated the tables would start making them about a folder nothing derives
    from.
    """
    return [
        row[OWNING_SKILL_COLUMN] for row in _family_table(NON_MEMBERS_HEADING, FOLDER_COLUMN)
    ]


def _skill_text() -> str:
    """The shipped `SKILL.md`, with a message rather than an OSError when absent."""
    if not SKILL.is_file():
        raise AssertionError(f"{SKILL} does not exist, so product-review ships no invocable skill")
    return SKILL.read_text(encoding="utf-8")


def _skill_body() -> str:
    """The shipped `SKILL.md` with its frontmatter block removed.

    The complement of what `guarantees.frontmatter_value` reads, split on the
    same two markers: a leading `---` and the next line-initial `---`. The split
    is what makes the checks below mean something. Both halves reach the model,
    but at different moments -- the frontmatter is what the router weighs before
    the skill is picked, while the body is what the model has in front of it
    while acting -- so a rule stated only in frontmatter is a rule the acting
    model never reads. This file's frontmatter comment discusses several of the
    same nouns the body's rules are anchored on, so the split is load-bearing
    rather than tidiness.

    Raises rather than returning "" on a malformed block, because most
    assertions below are written as bans and an empty body satisfies every one.
    """
    text = _skill_text()
    if not text.startswith(FENCE):
        raise AssertionError(
            f"{SKILL} does not open with a {FENCE!r} frontmatter fence, so the harness reads no "
            f"frontmatter from it and every field it declares is inert"
        )

    end = text.find(f"\n{FENCE}", len(FENCE))
    if end == -1:
        raise AssertionError(f"{SKILL}'s frontmatter block is never closed by a {FENCE!r} line")

    return text[end:]


def _provenance_prefix() -> str:
    """The fixed part of the provenance line, read from the file that owns it.

    `## Provenance` in artifact-family.md publishes the whole line as a template
    in a fenced block, and everything up to and including its colon is the part
    a citing file could copy into itself. Read from there rather than written
    out here: a copy would go on matching the retired spelling after the
    published format changed, leaving a ban that protects nothing.

    Located positionally -- the section's first fenced block, that block's first
    non-blank line -- so finding the line needs no fragment of the line.
    """
    section = _section(ARTIFACT_FAMILY.read_text(encoding="utf-8"), PROVENANCE_HEADING)
    if section is None:
        raise AssertionError(f"{ARTIFACT_FAMILY} publishes no `{PROVENANCE_HEADING}` section")

    opened = section.find(CODE_FENCE)
    if opened == -1:
        raise AssertionError(
            f"`{PROVENANCE_HEADING}` in {ARTIFACT_FAMILY} carries no {CODE_FENCE} block, so the "
            f"provenance line's published template cannot be read out of it"
        )

    block = section[opened + len(CODE_FENCE) :]
    closed = block.find(CODE_FENCE)
    fenced = block if closed == -1 else block[:closed]
    template = next((line for line in fenced.splitlines() if line.strip()), "")

    prefix, colon, _rest = template.partition(":")
    if not colon:
        raise AssertionError(
            f"the provenance template in {ARTIFACT_FAMILY} reads {template!r}, which carries no "
            f"colon to end its fixed prefix; the prefix is what a citing file could copy"
        )
    return prefix + colon


def _lift_rubric_templates() -> list[re.Match[str]]:
    """One match per *distinct* rubric-path template published in the body.

    Distinct rather than per occurrence: a body free to show its own mapping in
    a step and again in an example is still publishing one mapping. Two
    different templates, or none, is what means the skill has stopped saying how
    it selects.
    """
    found: dict[str, re.Match[str]] = {}
    for match in RUBRIC_TEMPLATE.finditer(_skill_body()):
        found.setdefault(match.group(0), match)
    return list(found.values())


def _rubric_paths(beats: list[str]) -> set[str]:
    """The rubric path the published template composes for each of `beats`.

    Raises unless the body publishes exactly one template. With two, "reachable"
    has no single answer; with none the set is empty and every statement about
    its members holds vacuously. Which of those happened is
    `test_rubric_template_derives_every_shipped_principles_file`'s report to
    make, so the message here only says that nothing was computed.
    """
    templates = _lift_rubric_templates()
    if len(templates) != 1:
        raise AssertionError(
            f"lifted {len(templates)} path templates from {SKILL.name}, expected exactly 1; "
            f"nothing downstream of the template can be checked"
        )

    template = templates[0]
    slot = f"<{template.group('slot')}>"
    return {template.group(0).replace(slot, beat) for beat in beats}


def _reachable_rubrics() -> set[str]:
    """Every rubric path product-review can select, over the whole family.

    Both published columns, because a beat is selectable for owning something in
    the folder family and not for owning a link in the chain. Reading the member
    table alone is the drift this exists to prevent: it leaves a shipped rubric
    that no invocation can ever reach, which costs a beat its review while every
    other check in this module stays green.
    """
    return _rubric_paths(_member_beats() + _non_member_beats())


def _red_flag_clusters(path: Path) -> list[str]:
    """The H3 cluster names under `## Review-time red flags` in one rubric.

    Empty when the heading is absent as well as when it is present but holds no
    cluster. The two are reported together rather than told apart because they
    cost the same thing: a fleet with no finder to launch.
    """
    section = _section(path.read_text(encoding="utf-8"), RED_FLAGS_HEADING)
    if section is None:
        return []

    return [
        line[len(CLUSTER_PREFIX) :].strip()
        for line in section.splitlines()
        if line.startswith(CLUSTER_PREFIX)
    ]


def test_rubric_template_derives_every_shipped_principles_file() -> None:
    templates = _lift_rubric_templates()

    # Asserted first and on its own: this module keeps no copy of the mapping,
    # so a template reworded out of recognition leaves nothing to check and
    # every set assertion below would hold over an empty set.
    assert len(templates) == 1, (
        f"lifted {len(templates)} path templates from SKILL.md, expected exactly 1. The "
        f"mapping is read out of the shipped file rather than copied here, so it has to stay "
        f"recognisable as {RUBRIC_TEMPLATE.pattern!r} -- one placeholder, spelling both the "
        f"beat's directory and its rubric filename"
    )

    produced = _reachable_rubrics()
    on_disk = {str(path.relative_to(REPO)) for path in REPO.glob(RUBRIC_GLOB)}

    # A glob matching nothing makes the coverage check true of an empty set,
    # which reports as a pass. One rubric ships today, so zero means the rubric
    # tree moved, not that the suite is early.
    assert on_disk, (
        f"no file in this repository matches {RUBRIC_GLOB!r}, so the coverage check below "
        f"weighs the template against nothing and passes however far it has drifted"
    )

    unreachable = on_disk - produced
    assert not unreachable, (
        f"{sorted(unreachable)} exists on disk but no beat published in {ARTIFACT_FAMILY.name} "
        f"produces it, so product-review can never select it -- the template in SKILL.md and the "
        f"`{OWNING_SKILL_COLUMN}` columns of artifact-family.md have drifted"
    )

    # The two assertions below pin the off-chain half of that derivation, which
    # the one above cannot: delete the non-member column and the rubric it
    # reaches in one commit and `unreachable` is empty again, leaving a beat
    # whose red-flag clusters nothing can run. So the capability is asserted
    # directly rather than through the drift it prevents.
    off_chain_beats = _non_member_beats()
    assert off_chain_beats, (
        f"`{NON_MEMBERS_HEADING}` in {ARTIFACT_FAMILY.name} names no owning beat, so every "
        f"rubric this template reaches belongs to a chain member. A beat that writes a family "
        f"artifact outside the closed chain -- a folder beside the members rather than a sixth "
        f"member -- ships a rubric like any other, and that column is the only thing that puts "
        f"one within reach of the single template product-review publishes"
    )

    off_chain = _rubric_paths(off_chain_beats) - _rubric_paths(_member_beats())
    assert off_chain & on_disk, (
        f"`{NON_MEMBERS_HEADING}` reaches {sorted(off_chain)}, none of which ships: no rubric on "
        f"disk is selectable through a beat that owns no chain member. One such rubric ships "
        f"today, so this is that beat's row leaving the table, its rubric leaving the tree, or "
        f"the beat being renamed in one of the two places and not the other"
    )

    for path in sorted(produced):
        assert RUBRIC_TREE.fullmatch(path), (
            f"template produced {path!r}, which escapes skills/product-*/references/; a rubric "
            f"path outside that tree means the template or an `{OWNING_SKILL_COLUMN}` cell now "
            f"names something that is not a product beat"
        )


def test_every_reachable_rubric_exposes_the_cluster_shape() -> None:
    # Only the rubrics that exist. A beat that ships none is the skill's
    # unreviewable report rather than a broken rubric, and which beats those are
    # changes as the suite fills in. What is asserted is that a rubric the skill
    # *will* select can actually drive a fleet: the fan-out is one finder per H3
    # cluster under the red-flags heading, so a rubric carrying none launches
    # nothing and hands back a target that reads as reviewed and clean.
    reachable = _reachable_rubrics()
    present = sorted(path for path in reachable if (REPO / path).is_file())

    assert present, (
        f"none of the {len(reachable)} rubric paths the template reaches exists on disk "
        f"({sorted(reachable)}), so this test checks the shape of nothing. At least one product "
        f"beat ships a rubric today, so an empty set is the template or the Owning skill column "
        f"having drifted -- which "
        f"test_rubric_template_derives_every_shipped_principles_file reports in full"
    )

    for path in present:
        clusters = _red_flag_clusters(REPO / path)
        assert clusters, (
            f"{path} is selectable by product-review but exposes no {CLUSTER_PREFIX.strip()!r} "
            f"cluster under {RED_FLAGS_HEADING!r}. The fleet launches one finder per cluster, so "
            f"this rubric launches none and the member comes back with no findings -- "
            f"indistinguishable in the report from a member that was judged and found clean"
        )


def test_skill_cites_rather_than_restating() -> None:
    body = _skill_body()

    for contract in CITED_CONTRACTS:
        assert contract in body, (
            f"{SKILL.name}'s body never cites {contract!r}. Both contracts are cited by "
            f"{PLUGIN_ROOT} path so a reader of an installed plugin can follow them; without "
            f"the citation the body either restates what they own or leaves the reader with no "
            f"way to find the fleet mechanics and the chain"
        )

    # Both bounds carry weight. The upper is the epic's enumeration ban: naming
    # every member makes this file a second copy of the `## Members` table,
    # which then drifts from it. The lower stops a stub from passing, since a
    # body naming no member satisfies "at most four" trivially. Member names
    # come from the published table rather than a list here, so this is a
    # statement about the real chain.
    members = [row[MEMBER_COLUMN] for row in _family_table(MEMBERS_HEADING, MEMBER_COLUMN)]
    named = [member for member in members if member in body]

    assert len(named) < len(members), (
        f"{SKILL.name} names all {len(members)} chain members ({named}). Cite "
        f"{ARTIFACT_FAMILY.name} and name at most {len(members) - 1} as examples: the member "
        f"set, the chain order and the owning beats are that file's to publish, and a second "
        f"copy of them here is one this skill's tests would not notice going stale"
    )
    assert named, (
        f"{SKILL.name} names none of the chain members {members}, so nothing in it shows a "
        f"reader what the contract it cites is about. One example is what separates a skill "
        f"that cites from a stub that merely avoids restating"
    )

    # Read out of the published contract rather than spelled here, so this ban
    # follows a rename of the format instead of going quietly stale against it.
    prefix = _provenance_prefix()
    assert prefix not in body, (
        f"{SKILL.name}'s body writes the provenance line's format ({prefix!r}) down. That "
        f"format belongs to {ARTIFACT_FAMILY.name}, and this skill has no use for it: "
        f"staleness is out of scope for a review, and a stale member is perfectly reviewable"
    )


def test_frontmatter_declares_the_read_only_contract() -> None:
    # Read through guarantees.py rather than parsed here, so that "declares a
    # key" means the same thing to this module as to the harness-facing rules
    # written against that parser.
    guarantees = _guarantees()
    text = _skill_text()

    declared = guarantees.scalar_text(guarantees.frontmatter_value(text, DENIED_FIELD))
    assert declared, (
        f"{SKILL.name} declares no `{DENIED_FIELD}` with any text in it, so it denies nothing "
        f"and is read-only only by habit. Reported here rather than as four separate misses "
        f"below, because one absent declaration is one repair"
    )

    denied = [entry.strip() for entry in declared.split(",") if entry.strip()]
    for tool in DENIED_TOOLS:
        assert tool in denied, (
            f"`{DENIED_FIELD}` reads {denied}, which does not deny {tool!r}. That field is the "
            f"only one in {SKILL.name} that narrows anything, so a tool left out of it is a "
            f"tool this skill may use -- and a reviewer that can write can edit the member it "
            f"is judging, which changes the hash its downstream member was derived from and "
            f"manufactures the staleness nobody asked it to find"
        )

    granted = guarantees.frontmatter_value(text, GRANT_FIELD)
    assert granted is None, (
        f"{SKILL.name} declares `{GRANT_FIELD}` (value {granted!r}). It grants pre-approval and "
        f"restricts nothing -- every tool stays callable whether or not it is listed -- so a "
        f"list there reads as a boundary while enforcing none, and the next reader has to know "
        f"the field's semantics to see that the real boundary is `{DENIED_FIELD}` alone"
    )


def test_skill_publishes_its_runtime_rules() -> None:
    # Epic constraint 11 makes each beat publish its own rules as prose. Prose
    # is unreadable to CI unless something names the tokens it turns on, so each
    # anchor below is a rule that would otherwise be enforced by nobody.
    body = _skill_body()

    for anchor, rule in RUNTIME_ANCHORS.items():
        assert anchor in body, (
            f"{SKILL.name}'s body never says {anchor!r}, so it does not publish {rule}. A rule "
            f"the skill does not state is one a caller cannot rely on and a reviewer cannot "
            f"check, and nothing else in this repository states it either"
        )


if __name__ == "__main__":
    import traceback

    failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception:  # noqa: BLE001
                failed += 1
                print(f"FAIL {_name}")
                traceback.print_exc()
    sys.exit(1 if failed else 0)
