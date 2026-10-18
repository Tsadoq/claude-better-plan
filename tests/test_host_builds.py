"""Contracts every committed host build under ``dist/<host>/`` must keep.

Each test is parametrized over the profiles in ``hosts/``, so a new host gets all
three contracts the moment its profile lands.
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from render_hosts import diff_build, render  # noqa: E402

from hosts.codex import CODEX_TOOLS  # noqa: E402
from hosts.pi import WEB_AGENTS as PI_WEB_AGENTS  # noqa: E402
from hosts.pi import WRITE_TOOLS as PI_WRITE_TOOLS  # noqa: E402
from hosts.pi.tools import NPM_TOOLS, VENDORED_TOOLS  # noqa: E402
from hosts.profile import HostProfile  # noqa: E402

HOSTS = sorted(p.parent.name for p in (REPO / "hosts").glob("*/__init__.py"))
SOURCE_SKILLS = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))

# Claude Code primitives no other host has; a build naming one tells its model to
# call something that does not exist.
FORBIDDEN = (
    "AskUserQuestion",
    "subagent_type",
    "agentType",
    "TaskCreate",
    "TaskUpdate",
    "TodoWrite",
    "EnterPlanMode",
    "ExitPlanMode",
    "Shift+Tab",
    "${CLAUDE_",
    "$ARGUMENTS",
    "allowed-tools",
    "Workflow tool",
)

# Tool names each host owns, imported from that host's profile package so a rename
# lands here too. A host adds its entry when its profile ships.
HOST_TOOLS: dict[str, tuple[str, ...]] = {
    "pi": VENDORED_TOOLS + NPM_TOOLS,
    "codex": CODEX_TOOLS,
}


def _tool_mention(name: str) -> re.Pattern[str]:
    """How a build would name ``name`` as a tool: backticked, or ``<name> tool``.

    Plain words such as "subagent" or "todo" are ordinary prose, so only the tool
    forms count; a snake_case name is never prose, so it counts bare as well.
    """
    escaped = re.escape(name)
    forms = [f"`{escaped}`", rf"\b{escaped} tool\b"]
    if "_" in name:
        forms.append(rf"\b{escaped}\b")
    return re.compile("|".join(forms))


def _build(host: str) -> Path:
    """``dist/<host>/``, after asserting it holds one SKILL.md per source skill."""
    build = REPO / "dist" / host
    missing = [s for s in SOURCE_SKILLS if not (build / "skills" / s / "SKILL.md").is_file()]
    assert not missing, f"dist/{host}/ lacks SKILL.md for {missing}; run python3 tools/render_hosts.py {host}"
    return build


def _markdown_lines(build: Path) -> list[tuple[str, int, str]]:
    """Every ``(build-relative path, line number, line)`` of every ``.md`` in ``build``."""
    return [
        (md.relative_to(build).as_posix(), n, line)
        for md in sorted(build.rglob("*.md"))
        for n, line in enumerate(md.read_text(encoding="utf-8").splitlines(), start=1)
    ]


@pytest.mark.parametrize("host", HOSTS)
def test_build_has_no_claude_only_tokens(host: str) -> None:
    build = _build(host)
    hits = [
        f"dist/{host}/{rel}:{n}: {token}"
        for rel, n, line in _markdown_lines(build)
        for token in FORBIDDEN
        if token in line
    ]
    assert not hits, "Claude-only tokens survive in the build:\n" + "\n".join(hits)


@pytest.mark.parametrize("host", HOSTS)
def test_build_carries_no_other_host_tools(host: str) -> None:
    build = _build(host)
    foreign = {
        (owner, tool): _tool_mention(tool)
        for owner, tools in HOST_TOOLS.items()
        if owner != host
        for tool in tools
    }
    hits = [
        f"dist/{host}/{rel}:{n}: {tool} (owned by {owner})"
        for rel, n, line in _markdown_lines(build)
        for (owner, tool), pattern in foreign.items()
        if pattern.search(line)
    ]
    assert not hits, "another host's tools are named in the build:\n" + "\n".join(hits)


@pytest.mark.parametrize("host", HOSTS)
def test_build_is_fresh(host: str, tmp_path: Path) -> None:
    profile = importlib.import_module(f"hosts.{host}").PROFILE
    assert isinstance(profile, HostProfile), f"hosts/{host}/__init__.py defines no PROFILE"
    fresh = tmp_path / host
    render(REPO, profile, fresh)
    stale = diff_build(REPO / "dist" / host, fresh)
    assert not stale, (
        f"dist/{host}/ differs from a fresh render at:\n"
        + "\n".join(stale)
        + f"\nrun: python3 tools/render_hosts.py {host}"
    )


# ---- pi build: the sites the pi token map and agent mapping must reach ----

PI_BUILD = REPO / "dist" / "pi"


def _frontmatter(path: Path) -> dict[str, str]:
    """``path``'s top-level frontmatter keys and their same-line values (block values read as "")."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    block = text[4 : text.index("\n---\n", 3)]
    pairs = (line.partition(":") for line in block.splitlines() if line and not line[0].isspace())
    return {key: value.strip() for key, _, value in pairs}


def _pi_agent_tools(agent: str) -> list[str]:
    """The ``tools:`` list of ``dist/pi/agents/<agent>.md``, comma-separated in the build."""
    path = PI_BUILD / "agents" / f"{agent}.md"
    tools = _frontmatter(path).get("tools")
    assert tools, f"dist/pi/agents/{agent}.md has no tools: list"
    return [t.strip() for t in tools.split(",")]


def test_pi_research_agents_can_reach_the_web() -> None:
    for agent in sorted(PI_WEB_AGENTS):
        tools = _pi_agent_tools(agent)
        missing = [t for t in ("web_search", "web_fetch") if t not in tools]
        assert not missing, f"{agent} lacks {missing} in the pi build; its tools are {tools}"


def test_pi_agents_other_than_the_implementer_cannot_write() -> None:
    agents = sorted(p.stem for p in (PI_BUILD / "agents").glob("dp-*.md"))
    assert agents, "dist/pi/agents/ holds no dp-*.md"
    offending = [
        f"{agent}: {tool}"
        for agent in agents
        if agent != "dp-implement-task"
        for tool in _pi_agent_tools(agent)
        if tool in PI_WRITE_TOOLS
    ]
    assert not offending, "read-only agents hold a write tool in the pi build:\n" + "\n".join(offending)


def _section(text: str, heading: str) -> str:
    """The lines from ``heading`` up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    found = re.search(rf"(?m)^{re.escape(heading)}", text)  # a heading line, not a mention of one
    assert found, f"no {heading!r} heading"
    start = found.start()
    nxt = re.search(rf"(?m)^#{{1,{level}}} ", text[start + len(heading) :])
    return text[start : start + len(heading) + nxt.start()] if nxt else text[start:]


def test_pi_build_routes_asks_launches_and_commands_to_pi_tools() -> None:
    skills = PI_BUILD / "skills"
    deep_plan = (skills / "deep-plan/SKILL.md").read_text(encoding="utf-8")
    fleet = (skills / "design-review/references/fleet-orchestration.md").read_text(encoding="utf-8")
    execute = (skills / "deep-plan-execute/SKILL.md").read_text(encoding="utf-8")
    expected = {
        "deep-plan/SKILL.md ### Checkpoint 2": (
            _section(deep_plan, "### Checkpoint 2"),
            ("`questionnaire`",),
        ),
        "deep-plan/SKILL.md": (deep_plan, ("/skill:deep-plan-execute",)),
        "design-review/references/fleet-orchestration.md ## Fallback": (
            _section(fleet, "## Fallback"),
            ("`subagent`", "`tasks`"),
        ),
        "deep-plan-execute/SKILL.md": (execute, ("`todo`", "`blockedBy`")),
    }
    missing = [
        f"dist/pi/skills/{where}: {phrase}"
        for where, (text, phrases) in expected.items()
        for phrase in phrases
        if phrase not in text
    ]
    assert not missing, "the pi build lacks its pi-tool phrasing at:\n" + "\n".join(missing)


def test_pi_extensions_find_the_paths_they_resolve() -> None:
    # agents.ts reads agents/ two levels above extensions/subagent/; session-end.ts runs
    # cleanup.py one level above extensions/. The pi profile's extra_files owns that layout.
    extensions = PI_BUILD / "extensions"
    assert (extensions / "subagent/agents.ts").is_file(), "dist/pi/extensions/subagent/agents.ts is missing"
    assert (extensions / "session-end.ts").is_file(), "dist/pi/extensions/session-end.ts is missing"
    agents = extensions / "subagent" / ".." / ".." / "agents"
    cleanup = extensions / ".." / "skills/deep-plan/hooks/cleanup.py"
    assert list(agents.glob("dp-*.md")), f"agents.ts would find no agents at {agents.resolve()}"
    assert cleanup.is_file(), f"session-end.ts would find no cleanup.py at {cleanup.resolve()}"


# ---- Codex build: the verified Codex tools HOST.md defines, and the sites that use them ----

CODEX_BUILD = REPO / "dist" / "codex"


def test_codex_build_names_the_verified_codex_tools() -> None:
    host = (CODEX_BUILD / "HOST.md").read_text(encoding="utf-8")
    deep_plan = (CODEX_BUILD / "skills/deep-plan/SKILL.md").read_text(encoding="utf-8")
    ask, spawn, wait, close = (f"`{tool}`" for tool in CODEX_TOOLS)
    expected = {
        "HOST.md ## an ask": (_section(host, "## an ask"), (ask,)),
        "HOST.md ## launch dp-X": (_section(host, "## launch dp-X"), (spawn, wait, close)),
        "skills/deep-plan/SKILL.md ### Checkpoint 2": (_section(deep_plan, "### Checkpoint 2"), ("an ask",)),
        "skills/deep-plan/SKILL.md ## Phase 1": (
            _section(deep_plan, "## Phase 1: Parallel triangulation"),
            ("launch dp-",),
        ),
        "skills/deep-plan/SKILL.md": (deep_plan, ("$deep-plan-execute",)),
    }
    missing = [
        f"dist/codex/{where}: {phrase}"
        for where, (text, phrases) in expected.items()
        for phrase in phrases
        if phrase not in text
    ]
    assert not missing, "the Codex build lacks its Codex convention at:\n" + "\n".join(missing)
    assert "/deep-plan:" not in deep_plan, "dist/codex/skills/deep-plan/SKILL.md keeps a /deep-plan: command"
