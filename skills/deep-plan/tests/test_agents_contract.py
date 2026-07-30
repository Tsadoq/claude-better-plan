"""Contract test: every dp-* subagent is read-only via `disallowedTools`.

The deep-plan subagents inherit ambient tools (including any MCP documentation
tools the user has) so they must NOT carry a `tools:` allowlist (an allowlist
strips MCP access). Instead each agent declares a `disallowedTools:` list that
blocks the write tools. Research agents additionally block `Bash` so they have
no shell write vector at all. Plugin-bundled agents may not set
`permissionMode`, `hooks`, or `mcpServers` (the harness ignores them), so the
agents must not declare those fields either.

Runnable two ways:
    python3 skills/deep-plan/tests/test_agents_contract.py
    python3 -m pytest skills/deep-plan/tests/test_agents_contract.py
"""

from __future__ import annotations

import re
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parents[3] / "agents"
DEEP_PLAN = Path(__file__).resolve().parents[1]  # skills/deep-plan

# The one agent that may write. It implements a plan task in a fresh context,
# so blocking the write tools would defeat its purpose; its bound is the
# dispatcher's scope audit plus the `Workflow` denial, not a tool block.
WRITABLE = {"dp-implement-task"}

# Research agents and the critic fleet leaves have no legitimate need for
# Bash, so they block it outright and become genuinely write-free.
# `dp-explore-codebase` keeps it for read-only inspection, and the writable
# implementer needs it to run the task's verification command.
BASH_FREE = {
    "dp-research-shallow",
    "dp-research-deep",
    "dp-source-ingest",
    "dp-design-critic",
    "dp-test-critic",
    "dp-readability-critic",
}

WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
IGNORED_FIELDS = ("permissionMode", "hooks", "mcpServers")


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def _has_tools_allowlist(fm: str) -> bool:
    return any(line.strip().startswith("tools:") for line in fm.splitlines())


def _disallowed_tools(fm: str) -> set[str]:
    for line in fm.splitlines():
        stripped = line.strip()
        if stripped.startswith("disallowedTools:"):
            value = stripped.split(":", 1)[1]
            return {t.strip() for t in value.split(",") if t.strip()}
    return set()


def _agent_files() -> list[Path]:
    return sorted(AGENTS_DIR.glob("dp-*.md"))


def test_every_agent_blocks_write_tools() -> None:
    files = _agent_files()
    assert files, f"no dp-*.md agents found under {AGENTS_DIR}"
    for path in files:
        fm = _frontmatter(path.read_text())
        assert fm, f"{path.name}: missing frontmatter"

        assert not _has_tools_allowlist(fm), (
            f"{path.name}: declares a `tools:` allowlist, which strips ambient "
            "MCP access. Use `disallowedTools:` instead."
        )

        disallowed = _disallowed_tools(fm)
        if path.stem not in WRITABLE:
            missing = WRITE_TOOLS - disallowed
            assert not missing, (
                f"{path.name}: disallowedTools missing write tools {sorted(missing)}"
            )

        if path.stem in BASH_FREE:
            assert "Bash" in disallowed, f"{path.name}: research agent must disallow Bash"

        for field in IGNORED_FIELDS:
            assert not any(line.strip().startswith(f"{field}:") for line in fm.splitlines()), (
                f"{path.name}: declares plugin-ignored field {field!r}"
            )


def test_implement_task_is_the_only_writable_agent() -> None:
    # Exactly one agent may write, and the exemption lives here as a test
    # constant rather than as a marker inside the agent file, so adding a
    # writable agent is a deliberate edit to this contract.
    files = _agent_files()
    assert files, f"no dp-*.md agents found under {AGENTS_DIR}"

    writable = {
        path.stem
        for path in files
        if WRITE_TOOLS - _disallowed_tools(_frontmatter(path.read_text()))
    }
    assert writable == WRITABLE, (
        f"the writable-agent set must be exactly {sorted(WRITABLE)}, found {sorted(writable)}"
    )

    path = AGENTS_DIR / "dp-implement-task.md"
    assert path.exists(), f"missing the implementer agent: {path}"
    fm = _frontmatter(path.read_text())
    assert fm, f"{path.name}: missing frontmatter"

    disallowed = _disallowed_tools(fm)
    assert "Workflow" in disallowed, (
        f"{path.name}: must disallow Workflow -- workflow() nesting is capped at one "
        "level, and the fleet recipe would otherwise prefer that path"
    )
    assert "Agent" not in disallowed, (
        f"{path.name}: must NOT disallow Agent -- it runs its own nested critic fleet"
    )

    for key in ("description", "model", "effort", "maxTurns"):
        assert any(line.strip().startswith(f"{key}:") for line in fm.splitlines()), (
            f"{path.name}: frontmatter missing {key!r}, which the dispatcher relies on"
        )

    assert not _has_tools_allowlist(fm), (
        f"{path.name}: declares a `tools:` allowlist, which strips ambient MCP access"
    )
    for field in IGNORED_FIELDS:
        assert not any(line.strip().startswith(f"{field}:") for line in fm.splitlines()), (
            f"{path.name}: declares plugin-ignored field {field!r}"
        )


def test_no_dangling_agent_references() -> None:
    # A shipped document naming an agent the plugin does not ship is a broken
    # promise to the reader and, for a skill, a launch that fails at runtime.
    root = AGENTS_DIR.parent
    docs = sorted((root / "skills").rglob("*.md"))
    docs += sorted(AGENTS_DIR.glob("*.md"))
    docs += [root / "README.md", root / "PLAN.md"]

    # The golden fixtures freeze superseded plans verbatim; they are test data,
    # not claims about the current tree.
    docs = [p for p in docs if "golden" not in p.parts]
    assert docs, "found no shipped documents to scan"

    # `dp-` needs at least one alnum after the hyphen, so glob forms such as
    # `dp-*` are not matched as names.
    pattern = re.compile(r"\bdp-[a-z0-9]+(?:-[a-z0-9]+)*")

    dangling: list[str] = []
    for path in docs:
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for name in pattern.findall(line):
                if not (AGENTS_DIR / f"{name}.md").exists():
                    dangling.append(f"{path.relative_to(root)}:{lineno}: {name}")

    assert not dangling, "documents name agents the plugin does not ship:\n" + "\n".join(dangling)


def test_no_false_harness_claims() -> None:
    # Two claims were wrong and load-bearing: nested agents DO work (the whole
    # delegated execute design depends on it), and the ignored frontmatter
    # fields are ignored, not rejected. A false statement about the harness is
    # corrected in place, including inside history and rationale tables.
    root = AGENTS_DIR.parent
    docs = [root / "README.md", root / "PLAN.md"]
    docs += sorted((root / "skills").rglob("*.md"))
    docs = [p for p in docs if "golden" not in p.parts]

    banned = (
        re.compile(r"subagents? cannot (?:spawn|delegate)", re.IGNORECASE),
        re.compile(r"subagents? cannot have these", re.IGNORECASE),
    )

    offenders: list[str] = []
    for path in docs:
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for rx in banned:
                if rx.search(line):
                    offenders.append(f"{path.relative_to(root)}:{lineno}: {line.strip()[:90]}")

    assert not offenders, "false harness claims survive:\n" + "\n".join(offenders)


def test_design_critic_agent_present() -> None:
    path = AGENTS_DIR / "dp-design-critic.md"
    assert path.exists(), f"missing design critic agent: {path}"
    fm = _frontmatter(path.read_text())
    assert fm, f"{path.name}: missing frontmatter"

    assert not _has_tools_allowlist(fm), (
        f"{path.name}: declares a `tools:` allowlist, which strips ambient MCP access"
    )

    disallowed = _disallowed_tools(fm)
    required = WRITE_TOOLS | {"Bash", "Agent"}
    missing = required - disallowed
    assert not missing, f"{path.name}: disallowedTools missing {sorted(missing)}"


def _phase3_region(text: str, source: str) -> str:
    start = text.find("## Phase 3")
    end = text.find("## Phase 4")
    assert start != -1 and end != -1, f"{source}: Phase 3/Phase 4 headings missing"
    return text[start:end]


def test_research_deep_dossier_format() -> None:
    research = (AGENTS_DIR / "dp-research-deep.md").read_text()

    # The dossier is question-first, as bold-label blocks (no internal H2s,
    # so it nests under a ### heading in the plan appendix without breaking
    # the H2-based appendix slicing).
    labels = ["**The question**", "**The answer**", "**What we found**", "**Sources**"]
    pos = -1
    for label in labels:
        found = research.find(label, pos + 1)
        assert found > pos, (
            f"dp-research-deep.md: dossier label {label!r} missing or out of order"
        )
        pos = found
    assert "## Contradiction" in research, (
        "dp-research-deep.md must keep the ## Contradiction escape hatch"
    )
    assert "## Verdict" not in research, (
        "dp-research-deep.md: the retired ## Verdict dossier heading must not resurface"
    )

    # The orchestration files stop restating the dossier section list and
    # point at the agent file as its normative home.
    for path in (DEEP_PLAN / "SKILL.md", DEEP_PLAN / "references" / "phase-prompts.md"):
        region = _phase3_region(path.read_text(), path.name)
        assert "Canonical snippet" not in region, (
            f"{path.name}: Phase 3 must not restate the retired dossier section list"
        )
        assert "dp-research-deep.md" in region, (
            f"{path.name}: Phase 3 must name dp-research-deep.md as the dossier's home"
        )

    # The dossier's downstream consumer is now the plan-integrity cluster, run by
    # the readability leaf; the Phase 4.6 fragment briefs it on the question-first
    # labels in place of the retired standalone critic's own input section.
    fragment = (DEEP_PLAN / "references" / "phase-prompts.md").read_text()
    assert "The question" in fragment, (
        "phase-prompts.md must brief the plan-integrity run on the question-first "
        "dossier labels now that the standalone critic is gone"
    )


def test_test_critic_agent_present() -> None:
    path = AGENTS_DIR / "dp-test-critic.md"
    assert path.exists(), f"missing test critic agent: {path}"
    fm = _frontmatter(path.read_text())
    assert fm, f"{path.name}: missing frontmatter"

    assert not _has_tools_allowlist(fm), (
        f"{path.name}: declares a `tools:` allowlist, which strips ambient MCP access"
    )

    disallowed = _disallowed_tools(fm)
    required = WRITE_TOOLS | {"Bash", "Agent"}
    missing = required - disallowed
    assert not missing, f"{path.name}: disallowedTools missing {sorted(missing)}"

    assert "dp-test-critic" in BASH_FREE, "dp-test-critic must be registered bash-free"


def test_readability_critic_agent_present() -> None:
    path = AGENTS_DIR / "dp-readability-critic.md"
    assert path.exists(), f"missing readability critic agent: {path}"
    fm = _frontmatter(path.read_text())
    assert fm, f"{path.name}: missing frontmatter"

    assert not _has_tools_allowlist(fm), (
        f"{path.name}: declares a `tools:` allowlist, which strips ambient MCP access"
    )

    disallowed = _disallowed_tools(fm)
    required = WRITE_TOOLS | {"Bash", "Agent"}
    missing = required - disallowed
    assert not missing, f"{path.name}: disallowedTools missing {sorted(missing)}"

    assert "dp-readability-critic" in BASH_FREE, (
        "dp-readability-critic must be registered bash-free"
    )


if __name__ == "__main__":
    import sys
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
