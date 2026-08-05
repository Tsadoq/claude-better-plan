
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

SKILLS = Path(__file__).resolve().parents[2]
ARTIFACT_FAMILY = SKILLS / "product-artifacts" / "references" / "artifact-family.md"
ARTIFACT_SCRIPTS = SKILLS / "product-artifacts" / "scripts"
SKILL = SKILLS / "product-status" / "SKILL.md"

MEMBERS_TABLE_COLUMNS = ("Member", "Upstream", "Position", "Owning skill")

CHAIN_LENGTH = 5

UNFILLED = "tbd"

DENIED_TOOLS = ("Write", "Edit", "Agent", "Skill")

BARE_BASH = "Bash"

SLUG_HINT = "[slug]"

SCRIPT_TAIL = "product-artifacts/scripts/product_artifact.py"

RUNTIME_ANCHORS = {
    "earliest": "the walk order, which fixes the earliest broken member rather than the first gap",
    "product-issues": "the recommendation the chain walk reaches when no member needs work",
    "product-brief": "the cold-start recommendation, and the only one a slug-less run emits",
    "no recommendation": "the no-slug rule, which lists every slug and recommends nothing",
    "re-read": "the re-run rule, which is that every invocation reads current state afresh",
}

FORBIDDEN_COMMAND = "hash-object"

MAX_MEMBERS_NAMED = CHAIN_LENGTH - 1

FENCE = "---"
CODE_FENCE = "```"


def _load(name: str, directory: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, directory / f"{name}.py")
    assert spec and spec.loader, f"cannot load {directory / f'{name}.py'}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


product_artifact = _load("product_artifact", ARTIFACT_SCRIPTS)


def _cells(row: str) -> list[str]:
    return [cell.strip().strip("`").strip() for cell in row.strip().strip("|").split("|")]


def _members_table() -> list[tuple[str, str, str, str]]:
    heading = "\n## Members\n"
    text = ARTIFACT_FAMILY.read_text()
    start = text.find(heading)
    if start == -1:
        raise AssertionError(f"{ARTIFACT_FAMILY} publishes no `## Members` section")

    section = text[start + len(heading) :]
    next_heading = section.find("\n## ")
    if next_heading != -1:
        section = section[:next_heading]

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
    fields: dict[str, str] = {}
    for line in _split_skill()[0].splitlines():
        if line.startswith((" ", "\t", "#")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key] = value.strip()
    return fields


def _tool_entries(fields: dict[str, str], field: str) -> list[str]:
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
    tabled = [row[0] for row in _members_table()]
    assert tabled == list(product_artifact.MEMBERS), (
        f"`## Members` lists {tabled} but product_artifact.MEMBERS is "
        f"{list(product_artifact.MEMBERS)}; the table is the published source of truth"
    )


def test_frontmatter_declares_the_read_only_contract() -> None:
    fields = _frontmatter_fields()

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
    body = _split_skill()[1]

    for anchor, rule in RUNTIME_ANCHORS.items():
        assert anchor in body, (
            f"{SKILL.name}'s body never says {anchor!r}, so it does not publish {rule}. A "
            f"rule the skill does not state is one a caller cannot rely on and a reviewer "
            f"cannot check, and nothing else in this repository states it either"
        )


def test_skill_does_not_reimplement_freshness() -> None:
    body = _split_skill()[1]

    for internal in (FORBIDDEN_COMMAND, _provenance_prefix()):
        assert internal not in body, (
            f"{SKILL.name}'s body names {internal!r}, which belongs to the substrate alone. "
            f"Shelling to git plumbing, or writing the provenance line's format down here, "
            f"puts a second copy of the drift rule in this repository -- and the copy that "
            f"is prose rather than code is the one nothing tests"
        )


def test_skill_cites_rather_than_enumerating() -> None:
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
