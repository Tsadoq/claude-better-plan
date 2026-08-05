
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "skills" / "product-review" / "SKILL.md"
ARTIFACT_FAMILY = REPO / "skills" / "product-artifacts" / "references" / "artifact-family.md"

MEMBERS_HEADING = "## Members"
NON_MEMBERS_HEADING = "## Non-member artifacts"
PROVENANCE_HEADING = "## Provenance"

MEMBER_COLUMN = "Member"
FOLDER_COLUMN = "Folder"
OWNING_SKILL_COLUMN = "Owning skill"

RUBRIC_TEMPLATE = re.compile(r"skills/<(?P<slot>[^<>/]+)>/references/<(?P=slot)>-principles\.md")

RUBRIC_TREE = re.compile(r"skills/product-[\w-]+/references/[\w.-]+\.md")

RUBRIC_GLOB = "skills/product-*/references/product-*-principles.md"

RED_FLAGS_HEADING = "## Review-time red flags"
CLUSTER_PREFIX = "### "

PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
CITED_CONTRACTS = (
    f"{PLUGIN_ROOT}/skills/design-review/references/fleet-orchestration.md",
    f"{PLUGIN_ROOT}/skills/product-artifacts/references/artifact-family.md",
)

DENIED_FIELD = "disallowed-tools"
DENIED_TOOLS = ("Write", "Edit", "NotebookEdit", "Bash")

GRANT_FIELD = "allowed-tools"

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

FENCE = "---"
CODE_FENCE = "```"


def _guarantees() -> ModuleType:
    source = REPO / "tests" / "guarantees.py"
    spec = importlib.util.spec_from_file_location("guarantees", source)
    assert spec and spec.loader, f"cannot load {source}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _section(text: str, heading: str) -> str | None:
    marker = f"\n{heading}\n"
    start = text.find(marker)
    if start == -1:
        return None

    body = text[start + len(marker) :]
    end = body.find("\n## ")
    return body if end == -1 else body[:end]


def _cells(row: str) -> list[str]:
    return [cell.strip().strip("`").strip() for cell in row.strip().strip("|").split("|")]


def _family_table(heading: str, subject_column: str) -> list[dict[str, str]]:
    section = _section(ARTIFACT_FAMILY.read_text(encoding="utf-8"), heading)
    if section is None:
        raise AssertionError(f"{ARTIFACT_FAMILY} publishes no `{heading}` section")

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
    return [row[OWNING_SKILL_COLUMN] for row in _family_table(MEMBERS_HEADING, MEMBER_COLUMN)]


def _non_member_beats() -> list[str]:
    return [
        row[OWNING_SKILL_COLUMN] for row in _family_table(NON_MEMBERS_HEADING, FOLDER_COLUMN)
    ]


def _skill_text() -> str:
    if not SKILL.is_file():
        raise AssertionError(f"{SKILL} does not exist, so product-review ships no invocable skill")
    return SKILL.read_text(encoding="utf-8")


def _skill_body() -> str:
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
    found: dict[str, re.Match[str]] = {}
    for match in RUBRIC_TEMPLATE.finditer(_skill_body()):
        found.setdefault(match.group(0), match)
    return list(found.values())


def _rubric_paths(beats: list[str]) -> set[str]:
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
    return _rubric_paths(_member_beats() + _non_member_beats())


def _red_flag_clusters(path: Path) -> list[str]:
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

    assert len(templates) == 1, (
        f"lifted {len(templates)} path templates from SKILL.md, expected exactly 1. The "
        f"mapping is read out of the shipped file rather than copied here, so it has to stay "
        f"recognisable as {RUBRIC_TEMPLATE.pattern!r} -- one placeholder, spelling both the "
        f"beat's directory and its rubric filename"
    )

    produced = _reachable_rubrics()
    on_disk = {str(path.relative_to(REPO)) for path in REPO.glob(RUBRIC_GLOB)}

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

    prefix = _provenance_prefix()
    assert prefix not in body, (
        f"{SKILL.name}'s body writes the provenance line's format ({prefix!r}) down. That "
        f"format belongs to {ARTIFACT_FAMILY.name}, and this skill has no use for it: "
        f"staleness is out of scope for a review, and a stale member is perfectly reviewable"
    )


def test_frontmatter_declares_the_read_only_contract() -> None:
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
