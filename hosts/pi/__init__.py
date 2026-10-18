"""The pi build: generic's rewrites, with pi's own tools wherever pi has one.

pi gets the vendored extensions in ``hosts/pi/extensions/`` plus two npm packages
(see ``package.json``), so an ask becomes the ``questionnaire`` tool, an agent
launch the ``subagent`` tool, task tracking the ``todo`` tool, and the web tools
``web_search``/``web_fetch``. Tool names come from ``hosts/pi/tools.py``.

This profile does not ``extends`` generic, because a parent's tokens run first and
would turn every Claude-only token into a generic phrase before pi's rules could
see it. Instead pi's rules run first and generic's follow as the fallback for
what pi words no differently (root and session placeholders, plan mode); any
generic phrase that survives is defined for pi in ``hosts/pi/HOST.md``.
"""

from __future__ import annotations

from pathlib import Path

from hosts.generic import _SLASH
from hosts.generic import PROFILE as GENERIC
from hosts.pi.tools import NPM_TOOLS, VENDORED_TOOLS
from hosts.profile import Frontmatter, HostProfile

_HERE = Path(__file__).resolve().parent

# Unpacked by position, so this follows the tuples' order in hosts/pi/tools.py.
_QUESTIONNAIRE, _SUBAGENT, _WEB_SEARCH = VENDORED_TOOLS
_WEB_FETCH, _TODO = NPM_TOOLS

# Ordered like generic's map: specific phrasings before the general rule for the
# same token, and every rule that needs the ``deep-plan:dp-`` prefix before
# generic's rule that strips it.
_TOKENS: tuple[tuple[str, str], ...] = (
    # Asking the user.
    (r"\b([Aa])n `?AskUserQuestion`?", rf"\1 `{_QUESTIONNAIRE}` call"),
    (
        r"('s|\b(?:[Tt]he|[Tt]hat|[Oo]ne|own|single|new|corresponding)) `?AskUserQuestion`?",
        rf"\1 `{_QUESTIONNAIRE}` call",
    ),
    (r"(?m)(?:^|(?<=\. ))`?AskUserQuestion`?", f"A `{_QUESTIONNAIRE}` call"),
    (r"`?AskUserQuestion`?", f"the `{_QUESTIONNAIRE}` tool"),
    # The critic fleet's surviving recipe (its Workflow path is overlaid away): one
    # subagent call with ``tasks`` runs every finder, then every verifier, in parallel.
    (
        r"Normative whenever the Workflow tool is absent, denied, or errors\."
        r" Same shape, driven by the caller through the plain Agent tool:",
        f"The one fleet recipe, driven by the caller through the `{_SUBAGENT}` tool:",
    ),
    (
        r"Launch one `deep-plan:dp-critic` per H3 cluster under `## Review-time red flags`"
        r" in the caller's principles file, all in a single message so they run concurrently\.",
        f"Make one `{_SUBAGENT}` call whose `tasks` hold one `{{agent: \"dp-critic\", task}}` entry"
        " per H3 cluster under `## Review-time red flags` in the caller's principles file,"
        " so they run in parallel.",
    ),
    (r"\(again batched in one message\)", f"(again all in one `{_SUBAGENT}` call's `tasks`)"),
    # Launching one agent.
    (r"`Agent` with `subagent_type: deep-plan:(dp-[a-z-]+)`", rf"The `{_SUBAGENT}` tool with `agent: \1`"),
    (r"`?agentType: deep-plan:(dp-[a-z-]+)`?", r"`agent: \1`"),
    # Task tracking through the todo tool, whose tasks carry ``blockedBy``.
    (
        r"(?s)\*\*Requires Claude Code >= v2\.1\.142\*\*.*?dependency wiring is degraded\.",
        f"Tasks are tracked with the `{_TODO}` tool (Step 4); each one's dependencies are\n"
        "its `blockedBy` list.",
    ),
    (r"via `TaskUpdate`", f"via the `{_TODO}` tool"),
    (r"one `TaskCreate`(?: payload)?", f"one `{_TODO}` task"),
    (r"blocks `TaskCreate`", "blocks task creation"),
    (
        r"into harness tasks with real dependencies \(`TaskCreate`, then `addBlockedBy`"
        r" — hence the Claude Code >= v2\.1\.142 floor\)",
        f"into `{_TODO}` tasks with real dependencies (`blockedBy`)",
    ),
    (r"mapped to `addBlockedBy`", "mapped to `blockedBy`"),
    # Command text and slash invocations: pi starts a skill with /skill:<name>.
    (r"(?m)(?:^|(?<=\. ))`?\$ARGUMENTS`?", "The text after the /skill command"),
    (r"`?\$ARGUMENTS`?", "the text after the /skill command"),
    (_SLASH, r"/skill:\2"),
    # Web tools.
    (r"`?WebSearch`?", f"`{_WEB_SEARCH}`"),
    (r"`?WebFetch`?", f"`{_WEB_FETCH}`"),
)

# pi's built-in tools, and which of them each Claude Code tool a ``disallowedTools``
# list can name stands for. A Claude tool absent here (Agent, NotebookEdit,
# Workflow, ExitPlanMode) has no pi built-in, so denying it removes nothing.
_PI_BUILTINS = ("read", "bash", "edit", "write", "grep", "find", "ls")
_BUILTINS_FOR: dict[str, tuple[str, ...]] = {
    "Read": ("read",),
    "Bash": ("bash",),
    "Edit": ("edit",),
    "Write": ("write",),
    "Grep": ("grep",),
    "Glob": ("find", "ls"),
}
# The agents whose job is reading the web; every other agent works locally.
WEB_AGENTS = frozenset({"dp-research-shallow", "dp-research-deep", "dp-source-ingest"})
# The pi built-ins that write files: what denying Claude's Edit and Write removes.
WRITE_TOOLS = frozenset(_BUILTINS_FOR["Edit"] + _BUILTINS_FOR["Write"])


def _agent_frontmatter(values: Frontmatter) -> Frontmatter:
    """Swap Claude's ``disallowedTools`` deny-list for the ``tools:`` allow-list pi's subagent reads."""
    denied = {t.strip() for t in values.pop("disallowedTools", "").split(",")}
    blocked = {builtin for tool in denied for builtin in _BUILTINS_FOR.get(tool, ())}
    tools = [t for t in _PI_BUILTINS if t not in blocked]
    if values.get("name") in WEB_AGENTS:
        tools += [_WEB_SEARCH, _WEB_FETCH]
    return {**values, "tools": ", ".join(tools)}


PROFILE = HostProfile(
    name="pi",
    tokens=_TOKENS + GENERIC.tokens,
    # Generic's dropped keys, except the deny-list _agent_frontmatter turns into tools:
    # (the renderer drops keys before the agent mapping sees them).
    drop_frontmatter=tuple(k for k in GENERIC.drop_frontmatter if k != "disallowedTools"),
    agent_frontmatter=_agent_frontmatter,
    overlays_dir=_HERE / "overlays",
    # extensions/subagent/agents.ts finds agents/ two levels up, and session-end.ts
    # finds skills/ one level up, so both rely on extensions/ sitting at the build root.
    extra_files={
        "extensions": "hosts/pi/extensions",
        "THIRD_PARTY_LICENSES.md": "hosts/pi/THIRD_PARTY_LICENSES.md",
    },
)
