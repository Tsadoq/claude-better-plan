"""The Codex build: the generic build, plus the Codex tools verified in its source.

Codex (openai/codex) exposes ``request_user_input`` for asking and the stable
multi-agent tools for launching; ``hosts/codex/HOST.md`` defines "an ask" and
"launch dp-X" in their terms, so the skills keep generic's phrases and this
profile only adds what Codex words differently: ``$<skill>`` invocations, and
the batched launches that must be collected with ``wait_agent``. Every other
Claude-only primitive renders as generic renders it.
"""

from __future__ import annotations

from hosts.generic import _SKILLS
from hosts.generic import PROFILE as GENERIC
from hosts.profile import HostProfile

# The Codex tools HOST.md names, each found in openai/codex source at commit 8c07694
# (codex-rs/core/src/tools/handlers/); a tool not confirmed there is never named.
CODEX_TOOLS = ("request_user_input", "spawn_agent", "wait_agent", "close_agent")

# These run after generic's map (``extends``), so they match generic's output:
# a slash invocation has already become "the <skill> skill".
_TOKENS: tuple[tuple[str, str], ...] = (
    # Codex starts a skill with $<name>.
    (rf"\bthe ({_SKILLS}) skill\b", r"$\1"),
    # A batched launch (deep-plan Phases 1 and 3) is several spawns collected together.
    (
        r"\*\*Launch in a single message\*\*:",
        "**Launch together** (launch dp-X for each agent named here, then collect them all):",
    ),
)

PROFILE = HostProfile(
    name="codex",
    tokens=_TOKENS,
    # Codex reads the plugin manifest at the build root; copied, so name and version match.
    extra_files={"plugin.json": "plugin.json"},
    extends=GENERIC,
)
