"""The generic host build: any agent that reads markdown skills and has a shell.

It assumes no tool beyond reading, writing, and running commands, so every
Claude-only primitive becomes a phrase whose meaning ``HOST.md`` defines once:
"an ask", "launch dp-X", the root and session placeholders. Other profiles
``extends`` this one and override only what their host does better.
"""

from __future__ import annotations

from pathlib import Path

from hosts.profile import ROOT, SESSION, HostProfile

_HERE = Path(__file__).resolve().parent
# The skill names a slash invocation can name; read from the tree this profile
# ships with, so a new skill is rewritten without touching the profile.
_SKILLS = "|".join(
    sorted((p.parent.name for p in (_HERE.parents[1] / "skills").glob("*/SKILL.md")), key=len, reverse=True)
)
# A slash invocation (``/deep-plan``, ``/deep-plan:deep-plan-execute``); group 2 is
# the skill name. Longest names first, so deep-plan-execute is never cut short.
_SLASH = rf"(?<![\w./}}~-])/(deep-plan:)?({_SKILLS})(?![\w/-]|\.\w)"

# Ordered: specific phrasings run before the general rule for the same token, and
# agent launches run before the bare ``deep-plan:dp-`` prefix rule that would
# otherwise strip what they match on. Sentence-exact rules each rewrite one source
# passage. When the source rewords one whose passage holds a Claude-only token, the
# leftover-token test in tests/test_host_builds.py fails and names the line; the
# few without one (Workflow-path asides) go stale silently, so reread them then.
_TOKENS: tuple[tuple[str, str], ...] = (
    # Asking the user.
    (r"('s|\b(?:[Aa]n?|[Tt]he|[Oo]ne|own|single|new|corresponding)) `?AskUserQuestion`?", r"\1 ask"),
    (r"(?m)(?:^|(?<=\. ))`?AskUserQuestion`?", "An ask"),
    (r"`?AskUserQuestion`?", "an ask"),
    # Launching an agent.
    (r"`Agent` with `subagent_type: deep-plan:(dp-[a-z-]+)`", r"Launch \1"),  # opens a list item
    (r"`?agentType: deep-plan:(dp-[a-z-]+)`?", r"launch \1"),
    (r"\b([Ll])aunch (?:exactly )?one `?deep-plan:(dp-[a-z-]+)`?", r"\1aunch \2 once"),
    (r"deep-plan:dp-", "dp-"),
    # Placeholders Claude Code substitutes and other hosts do not.
    (r"\$\{CLAUDE_PLUGIN_ROOT\}", ROOT),
    (r"\$\{CLAUDE_SESSION_ID\}", SESSION),
    (r"(?m)(?:^|(?<=\. ))`?\$ARGUMENTS`?", "The text given with the command"),
    (r"`?\$ARGUMENTS`?", "the text given with the command"),
    # Slash invocations, most specific phrasing first. _SLASH never matches a path
    # segment such as skills/deep-plan/, nor a file such as /deep-plan.md.
    (rf"(?m)^(#+ ){_SLASH}", r"\1\3"),
    (rf"{_SLASH} (plans?)\b", r"\2 \3"),
    (rf"\bthe `{_SLASH}` skill", r"the \2 skill"),
    (rf"\bthe `{_SLASH}`", r"the \2 skill"),
    (rf"`{_SLASH}`", r"the \2 skill"),
    (_SLASH, r"the \2 skill"),
    # Web tools, which an agent may or may not have (HOST.md says what to do without).
    (r"`?WebSearch`?", "web search"),
    (r"`?WebFetch`?", "web fetch"),
    # Native plan mode, which no other host has.
    (r", EnterPlanMode, ExitPlanMode", ""),
    (
        r", `Agent`, and -- defensively, since the skill itself never uses plan mode -- `ExitPlanMode`",
        ", and `Agent`",
    ),
    # Phase 0 step 1 guards against plan mode; the stub keeps the step numbering
    # that other files cite ("Phase 0 step 4").
    (
        r"(?m)^1\. \*\*Plan-mode guard\.\*\* .*$",
        "1. **No plan-mode guard.** This host has no plan mode to leave; go straight to step 2.",
    ),
    (r"\(`disallowedTools` blocks", "(your read-only rule forbids"),
    (r"Your `disallowedTools` blocks", "Your read-only rule forbids"),
    # Task tracking: the execute dispatcher keeps a checklist instead of harness tasks.
    (
        r"(?s)\*\*Requires Claude Code >= v2\.1\.142\*\*.*?dependency wiring is degraded\.",
        "Task tracking is a markdown checklist in the plan file (Step 4); you enforce its\n"
        "dependency order yourself.",
    ),
    (
        r"\*\*Mark it `in_progress`\*\* via `TaskUpdate`\.",
        "**Mark it in progress** in the checklist (Step 4).",
    ),
    (r"into one `TaskCreate`", "into one checklist line"),  # deep-plan-execute/SKILL.md
    # The same model as plan-file-template.md and PLAN.md describe it.
    (r"one `TaskCreate` payload", "one task entry"),
    (r"blocks `TaskCreate`", "blocks dispatch"),
    (
        r"into harness tasks with real dependencies \(`TaskCreate`, then `addBlockedBy`"
        r" — hence the Claude Code >= v2\.1\.142 floor\)",
        "into a dependency-ordered checklist",
    ),
    # The critic fleet's surviving recipe, once its Workflow path is overlaid away.
    (
        r"Normative whenever the Workflow tool is absent, denied, or errors\."
        r" Same shape, driven by the caller through the plain Agent tool:",
        "The one fleet recipe; launch each agent below as HOST.md says:",
    ),
    (
        r" — the same fields as the Workflow schema, so no information is lost relative to the Workflow path",
        "",
    ),
    (r"exactly as in the Workflow path:", "this way:"),
    (r" \(see `## agentType resolution`\)", ""),
)

PROFILE = HostProfile(
    name="generic",
    tokens=_TOKENS,
    # Claude Code frontmatter no other host reads; ``disallowed-tools`` goes too so
    # the comment above it (which names ``allowed-tools``) leaves with it.
    drop_frontmatter=(
        "allowed-tools",
        "disallowed-tools",
        "hooks",
        "effort",
        "model",
        "maxTurns",
        "disallowedTools",
    ),
    overlays_dir=_HERE / "overlays",
)
