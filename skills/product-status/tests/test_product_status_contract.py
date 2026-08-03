"""Contract tests for `product-status`: what it reads, and what it declares.

`product-status` reports which beat a caller should run next, so it needs to
know which beat owns each chain member. That derivation is published in one
place -- the `Owning skill` column of `## Members` in
skills/product-artifacts/references/artifact-family.md -- and this module pins
it by parsing that table rather than keeping a second copy of it here, which is
the drift a citing skill exists to avoid.

The second half of the module reads the shipped `SKILL.md` itself: the tool
declaration that makes the skill read-only, the single script path its grant
and its body must keep in step, the runtime rules it publishes as prose, and
that it cites the member contract instead of growing a second copy of it.

Scoped deliberately narrow: member chain order, the provenance literal and the
required H2 headings are already pinned by
skills/product-artifacts/tests/test_artifact_family_contract.py and are not
re-asserted here; the provenance prefix appears below only as a string the
skill's body must not contain, and is read out of the published contract rather
than copied, so no copy of the format lands here either. Nothing here measures
description or listing-entry length: tests/test_description_budget.py owns every
such comparison and fails the build on a second one.

Runnable two ways:
    python3 skills/product-status/tests/test_product_status_contract.py
    python3 -m pytest skills/product-status/tests/test_product_status_contract.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

SKILLS = Path(__file__).resolve().parents[2]
ARTIFACT_FAMILY = SKILLS / "product-artifacts" / "references" / "artifact-family.md"
ARTIFACT_SCRIPTS = SKILLS / "product-artifacts" / "scripts"
SKILL = SKILLS / "product-status" / "SKILL.md"

# The table's columns, in published order. `_members_table` reads cells
# positionally, so this is the parser's contract with the document.
MEMBERS_TABLE_COLUMNS = ("Member", "Upstream", "Position", "Owning skill")

# The chain is closed at five members (artifact-family.md's `## Members`).
CHAIN_LENGTH = 5

# The placeholder the column carried before any beat claimed a member.
UNFILLED = "tbd"

# The tools the skill must deny by bare name. `disallowed-tools` is the field
# that actually narrows -- `allowed-tools` only auto-approves what a caller
# would otherwise be prompted for -- so the read-only promise is kept here and
# nowhere else in the frontmatter.
DENIED_TOOLS = ("Write", "Edit", "Agent", "Skill")

# A `Bash` entry with no argument specifier auto-approves every command, which
# is the one shape the grant must not take: this skill runs a single read-only
# query and nothing else.
BARE_BASH = "Bash"

# The published argument the skill takes, as its hint spells it.
SLUG_HINT = "[slug]"

# The path tail shared by the frontmatter Bash grant and the body's citation of
# the substrate. The two spell the directory above it differently on purpose --
# the grant hops through `${CLAUDE_SKILL_DIR}/..` because `${CLAUDE_PLUGIN_ROOT}`
# is not substituted inside an `allowed-tools` rule, while the body cites
# `${CLAUDE_PLUGIN_ROOT}` as the epic requires -- so this tail is the longest
# string both can be held to.
SCRIPT_TAIL = "product-artifacts/scripts/product_artifact.py"

# One stable token per runtime rule the skill is required to publish, each
# mapped to the rule it anchors. Tokens rather than sentences: the wording of a
# shipped report format is its author's, and pinning it would mean rewording
# prose only by editing CI.
#
# Each token is chosen to be one the rejected form of its rule would not carry.
# `earliest` is the clearest case: the rule this skill walks by is chain order,
# stopping at the first member that is absent or stale, and the alternative it
# replaced -- all absent members outranking all stale ones -- recommends
# building on an upstream already reported as out of date. Both spellings would
# still say `chain order` somewhere, so `chain order` would not tell them apart.
RUNTIME_ANCHORS = {
    "earliest": "the walk order, which fixes the earliest broken member rather than the first gap",
    "product-issues": "the recommendation the chain walk reaches when no member needs work",
    "product-brief": "the cold-start recommendation, and the only one a slug-less run emits",
    "no recommendation": "the no-slug rule, which lists every slug and recommends nothing",
    "re-read": "the re-run rule, which is that every invocation reads current state afresh",
}

# The git plumbing #23 bans this skill from shelling to. A command name from
# outside this repository, so unlike the provenance prefix it has no published
# home here to be read out of.
FORBIDDEN_COMMAND = "hash-object"

# A citing body names a member or two by way of example. Naming all five is the
# enumeration the epic's cite-don't-restate rule exists to prevent.
MAX_MEMBERS_NAMED = CHAIN_LENGTH - 1

# The fence that opens and closes a frontmatter block, and the one that opens
# and closes a markdown code block.
FENCE = "---"
CODE_FENCE = "```"


def _load(name: str, directory: Path) -> Any:
    """Load a shipped script by path.

    pytest runs with `--import-mode=importlib`, which does not put a test
    file's own directory on `sys.path`, and the repo's other contract modules
    already load their neighbours this way.
    """
    spec = importlib.util.spec_from_file_location(name, directory / f"{name}.py")
    assert spec and spec.loader, f"cannot load {directory / f'{name}.py'}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


product_artifact = _load("product_artifact", ARTIFACT_SCRIPTS)


def _cells(row: str) -> list[str]:
    """Split one markdown table row into undecorated cell values.

    Backticks are stripped so assertions compare published names rather than
    the document's formatting choices.
    """
    return [cell.strip().strip("`").strip() for cell in row.strip().strip("|").split("|")]


def _members_table() -> list[tuple[str, str, str, str]]:
    """Parse `## Members` into one `(member, upstream, position, owning_skill)` per row.

    Rows come back in table order. Raises instead of returning an empty list
    when the section, the table, or its expected columns are missing: every
    assertion in this module is a statement about rows, and all of them would
    pass vacuously against a document that had stopped publishing the contract.
    """
    heading = "\n## Members\n"
    text = ARTIFACT_FAMILY.read_text()
    start = text.find(heading)
    if start == -1:
        raise AssertionError(f"{ARTIFACT_FAMILY} publishes no `## Members` section")

    section = text[start + len(heading) :]
    next_heading = section.find("\n## ")
    if next_heading != -1:
        section = section[:next_heading]

    # A markdown table is a run of pipe lines: header, separator, then rows.
    pipe_lines = [line for line in section.splitlines() if line.lstrip().startswith("|")]
    if len(pipe_lines) < 3:
        raise AssertionError(
            f"`## Members` in {ARTIFACT_FAMILY} carries {len(pipe_lines)} pipe lines; "
            f"expected a header, a separator and at least one member row"
        )

    columns = _cells(pipe_lines[0])
    if columns != list(MEMBERS_TABLE_COLUMNS):
        raise AssertionError(
            f"`## Members` columns are {columns}, expected {list(MEMBERS_TABLE_COLUMNS)}; "
            f"cells are read positionally, so reordered columns would mislabel every row"
        )

    rows: list[tuple[str, str, str, str]] = []
    for line in pipe_lines[2:]:
        cells = _cells(line)
        if len(cells) != len(MEMBERS_TABLE_COLUMNS):
            raise AssertionError(
                f"`## Members` row {line!r} has {len(cells)} cells, expected "
                f"{len(MEMBERS_TABLE_COLUMNS)}"
            )
        member, upstream, position, owning_skill = cells
        rows.append((member, upstream, position, owning_skill))
    return rows


def _provenance_prefix() -> str:
    """The fixed part of the provenance line, read from the file that owns it.

    `## Provenance` in artifact-family.md publishes the whole line as a template
    in a fenced block, and everything up to and including its colon is the part
    a citing file could copy into itself. Read from there rather than written
    out here: a copy in this module would go on matching the retired spelling
    after the published format changed, leaving a ban that protects nothing and
    says nothing about it.

    Located positionally -- the section's first fenced block, that block's first
    non-blank line -- so finding the line needs no fragment of the line.
    """
    heading = "\n## Provenance\n"
    text = ARTIFACT_FAMILY.read_text()
    start = text.find(heading)
    if start == -1:
        raise AssertionError(f"{ARTIFACT_FAMILY} publishes no `## Provenance` section")

    section = text[start + len(heading) :]
    next_heading = section.find("\n## ")
    if next_heading != -1:
        section = section[:next_heading]

    opened = section.find(CODE_FENCE)
    if opened == -1:
        raise AssertionError(
            f"`## Provenance` in {ARTIFACT_FAMILY} carries no {CODE_FENCE} block, so the "
            f"provenance line's published template cannot be read out of it"
        )

    block = section[opened + len(CODE_FENCE) :]
    closed = block.find(CODE_FENCE)
    body = block if closed == -1 else block[:closed]
    template = next((line for line in body.splitlines() if line.strip()), "")

    prefix, colon, _rest = template.partition(":")
    if not colon:
        raise AssertionError(
            f"the provenance template in {ARTIFACT_FAMILY} reads {template!r}, which carries "
            f"no colon to end its fixed prefix; the prefix is what a citing file could copy"
        )
    return prefix + colon


def _split_skill() -> tuple[str, str]:
    """The shipped `SKILL.md` as `(frontmatter block, body)`.

    Raises rather than returning empty strings when the file or its fences are
    missing. Every assertion below is a statement about something the file
    declares or states, and a file that declares nothing would satisfy most of
    them by having no offending text in it.
    """
    if not SKILL.is_file():
        raise AssertionError(f"{SKILL} does not exist, so product-status ships no invocable skill")

    text = SKILL.read_text()
    if not text.startswith(FENCE):
        raise AssertionError(
            f"{SKILL} does not open with a {FENCE!r} frontmatter fence, so the harness reads "
            f"no frontmatter from it and every field it declares is inert"
        )

    end = text.find(f"\n{FENCE}", len(FENCE))
    if end == -1:
        raise AssertionError(f"{SKILL}'s frontmatter block is never closed by a {FENCE!r} line")

    return text[len(FENCE) : end], text[end:]


def _frontmatter_fields() -> dict[str, str]:
    """The frontmatter block as `{key: raw value}`, one entry per top-level key.

    Keys are matched at column 0, so the YAML comment above the Bash grant, and
    any indented look-alike, cannot satisfy a check. Only single-line values are
    read: every field asserted below is a short scalar, and one moved into a
    folded block or a YAML sequence reads back empty, which the presence checks
    report rather than skip over.
    """
    fields: dict[str, str] = {}
    for line in _split_skill()[0].splitlines():
        if line.startswith((" ", "\t", "#")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key] = value.strip()
    return fields


def _tool_entries(fields: dict[str, str], field: str) -> list[str]:
    """One tool field's entries, split on commas at the top level only.

    A comma inside a `Bash(...)` specifier belongs to the specifier. Splitting
    naively would report such a rule as two entries, neither of which is the
    bare string `Bash`, so a check for a bare grant would pass on text that
    never contained one.

    Raises when the field is absent or empty: "no entry here is a bare `Bash`"
    and "these four tools are denied" are both vacuously true of a field that
    declares nothing.
    """
    raw = fields.get(field, "")
    if not raw:
        raise AssertionError(
            f"{SKILL} declares no `{field}` with any text in it, so the checks that read it "
            f"would pass on an absent declaration. Frontmatter keys present: {sorted(fields)}"
        )

    entries: list[str] = []
    current = ""
    depth = 0
    for char in raw:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(depth - 1, 0)
        if char == "," and depth == 0:
            entries.append(current.strip())
            current = ""
        else:
            current += char
    entries.append(current.strip())
    return [entry for entry in entries if entry]


def test_owning_skill_column_is_a_complete_bijection() -> None:
    rows = _members_table()

    # Asserted first: a parser that found nothing must fail here rather than
    # sail through every check below on an empty list.
    assert len(rows) == CHAIN_LENGTH, (
        f"`## Members` has {len(rows)} rows, expected the closed chain's {CHAIN_LENGTH}: {rows}"
    )

    for row in rows:
        member, _upstream, _position, owning_skill = row
        assert owning_skill and owning_skill != UNFILLED, (
            f"member {member!r} has no owning skill (cell reads {owning_skill!r}), so no "
            f"reader can derive which beat owns it: {row}"
        )

    owning_skills = [row[3] for row in rows]
    assert len(set(owning_skills)) == len(owning_skills), (
        f"each member must be owned by a distinct beat, found {owning_skills}"
    )

    positions = [row[2] for row in rows]
    expected_positions = [str(n) for n in range(1, CHAIN_LENGTH + 1)]
    assert positions == expected_positions, (
        f"position cells must read {expected_positions} in row order, found {positions}"
    )


def test_named_beats_are_well_formed() -> None:
    # The bijection test only proves the cells are filled and distinct, which
    # arbitrary text also satisfies. This checks each names something shaped
    # like a beat, and -- one way only, per the plan's decision 3 -- that any
    # beat already on disk is invocable. The reverse direction is deliberately
    # absent: `skills/product-*/` also globs the substrate package, which owns
    # no member, so requiring every product-* skill to appear in the table
    # would be false by construction.
    for row in _members_table():
        member, _upstream, _position, owning_skill = row
        assert owning_skill.startswith("product-"), (
            f"owning skill {owning_skill!r} for {member!r} is not a product-* beat name: {row}"
        )
        skill_dir = SKILLS / owning_skill
        if skill_dir.is_dir():
            assert (skill_dir / "SKILL.md").is_file(), (
                f"{skill_dir} exists but ships no SKILL.md, so {owning_skill!r} names a "
                f"folder rather than an invocable beat"
            )


def test_table_matches_the_shipped_member_tuple() -> None:
    # product_artifact.py's MEMBERS comment promises it must not drift from
    # this table, and nothing else checks it. The assertions above read member
    # names from the table, so table and implementation agreeing is what makes
    # those assertions statements about the shipped chain.
    tabled = [row[0] for row in _members_table()]
    assert tabled == list(product_artifact.MEMBERS), (
        f"`## Members` lists {tabled} but product_artifact.MEMBERS is "
        f"{list(product_artifact.MEMBERS)}; the table is the published source of truth"
    )


def test_frontmatter_declares_the_read_only_contract() -> None:
    fields = _frontmatter_fields()

    # Both fields are read up front: each raises on an absent or empty
    # declaration, which is the failure that would otherwise make the
    # assertions below statements about nothing.
    allowed = _tool_entries(fields, "allowed-tools")
    denied = _tool_entries(fields, "disallowed-tools")

    for tool in DENIED_TOOLS:
        assert tool in denied, (
            f"`disallowed-tools` reads {denied}, which does not deny {tool!r}. That field is "
            f"the only one in {SKILL.name} that narrows anything -- `allowed-tools` merely "
            f"auto-approves -- so a tool left out here is a tool this skill may use, and a "
            f"reporting skill that can write, edit or delegate is no longer read-only"
        )

    assert BARE_BASH not in allowed, (
        f"`allowed-tools` carries a bare {BARE_BASH!r} entry: {allowed}. That auto-approves "
        f"every shell command rather than the one read-only query this skill runs, so the "
        f"grant would stop being the audit boundary it is written to be"
    )

    hint = fields.get("argument-hint", "").strip("\"'")
    assert hint == SLUG_HINT, (
        f"`argument-hint` reads {hint!r}, expected {SLUG_HINT!r}. It is what the slash menu "
        f"shows, and the brackets are what tell a caller the slug is optional -- which is the "
        f"whole difference between the single-slug report and the listing"
    )

    disabled = fields.get("disable-model-invocation", "").strip().lower()
    assert disabled in ("", "false"), (
        f"`disable-model-invocation` reads {disabled!r}. Set true, the skill leaves the "
        f"model-facing listing entirely and only an explicit slash command can reach it, so "
        f"the model could no longer answer 'where am I' by picking this skill"
    )

    hidden = fields.get("user-invocable", "").strip().lower()
    assert hidden != "false", (
        f"`user-invocable` reads {hidden!r}, which takes /product-status out of the slash "
        f"menu. A status report is something a user asks for by name at least as often as "
        f"the model routes to it"
    )


def test_grant_and_body_name_one_script() -> None:
    # One file names one script twice, in two variable syntaxes, because
    # ${CLAUDE_PLUGIN_ROOT} does not expand inside an allowed-tools rule. This
    # is what makes a rename fail loudly instead of silently unhooking the
    # grant, leaving a prompt on every run and no other symptom.
    frontmatter, body = _split_skill()
    grant = _frontmatter_fields().get("allowed-tools", "")

    for label, text in (("the `allowed-tools` grant", grant), ("the body", body)):
        assert SCRIPT_TAIL in text, (
            f"{label} of {SKILL.name} does not name {SCRIPT_TAIL!r}. The grant and the body "
            f"must point at one file: if only one of them is updated when the script moves, "
            f"the grant stops matching the real invocation and every run prompts instead. "
            f"Frontmatter as parsed: {frontmatter.strip()!r}"
        )


def test_skill_publishes_its_runtime_rules() -> None:
    # Epic constraint 11 makes each beat publish its own rules as prose. Prose
    # is unreadable to CI unless something names the tokens it turns on, so
    # each anchor below is a rule that would otherwise be enforced by nobody.
    body = _split_skill()[1]

    for anchor, rule in RUNTIME_ANCHORS.items():
        assert anchor in body, (
            f"{SKILL.name}'s body never says {anchor!r}, so it does not publish {rule}. A "
            f"rule the skill does not state is one a caller cannot rely on and a reviewer "
            f"cannot check, and nothing else in this repository states it either"
        )


def test_skill_does_not_reimplement_freshness() -> None:
    body = _split_skill()[1]

    # The provenance prefix is read out of the published contract rather than
    # spelled here, so this ban follows a rename of the format instead of going
    # quietly stale against it.
    for internal in (FORBIDDEN_COMMAND, _provenance_prefix()):
        assert internal not in body, (
            f"{SKILL.name}'s body names {internal!r}, which belongs to the substrate alone. "
            f"Shelling to git plumbing, or writing the provenance line's format down here, "
            f"puts a second copy of the drift rule in this repository -- and the copy that "
            f"is prose rather than code is the one nothing tests"
        )


def test_skill_cites_rather_than_enumerating() -> None:
    # Both bounds carry weight and neither alone is enough. The upper bound is
    # the epic's enumeration ban; the lower is what stops a near-empty stub
    # from passing, since a body naming no member at all satisfies "at most
    # four" trivially. Member names come from the published table rather than a
    # list here, so this is a statement about the real chain.
    members = [row[0] for row in _members_table()]
    body = _split_skill()[1]
    named = [member for member in members if member in body]

    assert len(named) <= MAX_MEMBERS_NAMED, (
        f"{SKILL.name} names {len(named)} of the {len(members)} chain members ({named}), at "
        f"or above the whole set. Naming them all makes this file a second copy of the "
        f"`## Members` table, which then drifts from it: cite {ARTIFACT_FAMILY.name} and "
        f"name at most {MAX_MEMBERS_NAMED} members as examples"
    )
    assert named, (
        f"{SKILL.name} names none of the chain members {members}, so nothing in it shows a "
        f"reader what the contract it cites is about. One example is what separates a skill "
        f"that cites from a stub that merely avoids restating"
    )

    assert ARTIFACT_FAMILY.name in body, (
        f"{SKILL.name} never cites {ARTIFACT_FAMILY.name}. The enumeration ban above is only "
        f"half a rule: a body that neither restates the contract nor points at it leaves a "
        f"reader with no way to find the chain order, the member set or the state names"
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
