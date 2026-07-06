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

from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parents[3] / "agents"

# Research agents and the critic fleet leaves have no legitimate need for
# Bash, so they block it outright and become genuinely write-free. The
# Bash-keeping agents (explore, perspective, plan critic) need it for
# read-only inspection.
BASH_FREE = {
    "dp-research-shallow",
    "dp-research-deep",
    "dp-source-ingest",
    "dp-design-critic",
    "dp-test-critic",
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
        missing = WRITE_TOOLS - disallowed
        assert not missing, f"{path.name}: disallowedTools missing write tools {sorted(missing)}"

        if path.stem in BASH_FREE:
            assert "Bash" in disallowed, f"{path.name}: research agent must disallow Bash"

        for field in IGNORED_FIELDS:
            assert not any(line.strip().startswith(f"{field}:") for line in fm.splitlines()), (
                f"{path.name}: declares plugin-ignored field {field!r}"
            )


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
