"""The behavioural guarantees this plugin's prose must satisfy, and one checker.

Why this file exists
--------------------
The per-skill contract tests used to pin 71 exact prose substrings. That
protected the compliance-driving text but taxed every edit to it, so the
substrings are being removed. This module is what replaces them: a declarative
inventory of what each skill, agent, and reference file must still *do*, checked
by one generic function. Adding a guarantee is a data edit; only a guarantee
that needs a new *kind* of evidence touches `check`.

A guarantee asserts that a behaviour is reachable, never how it is worded. Five
kinds of evidence cover the inventory:

``heading_present``
    The listed headings all appear, as line prefixes, in the listed order. This
    is how callers navigate these files (`text.find("## Phase 4.6")`), so a
    renamed or reordered section is a broken caller.
``anchor_regex``
    Every pattern is found (or, with ``absent``, none is), optionally narrowed
    to a marker-delimited region. Patterns are short machine-readable tokens --
    a placeholder, a tool name, a retired identifier -- never a sentence.
``script_invoked``
    The file invokes a named helper script that exists, and any flag it passes
    is one the script's source actually declares.
``frontmatter_field``
    A top-level frontmatter key is present (or absent), and its value contains
    (or omits) a given token.
``path_exists``
    A file path this file cites resolves to a real file. One entry per critic
    launch site, so a moved principles file cannot leave a caller pointing at
    nothing.

Not asserted here, deliberately: the per-agent `disallowedTools`/`tools`
profile (owned by `skills/deep-plan/tests/test_agents_contract.py`, except the
merged critic leaf's exact profile, which its sibling `test_guarantees.py`
pins), the
`**Tests (TDD)**` field order (owned by
`skills/deep-plan/tests/test_template_contract.py` against
`finalize_plan.TESTS_FIELDS`), and the literal-ordering asserts inside
`test_skill_contract.py`. The one known overlap is `## Preflight` before
`## Step 5`, which `test_skill_contract.py` also asserts; it is kept here
because the step sequence is one guarantee, not nine.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "deep-plan" / "scripts"


class Guarantee(NamedTuple):
    """One behavioural promise, and the evidence that proves it is still kept.

    `path` is repo-relative. `kind` selects the evidence handler; `params` are
    that handler's arguments, so a new guarantee of an existing kind is a data
    edit and nothing more.
    """

    id: str
    path: str
    kind: str
    params: Mapping[str, Any]


BUDGETS: dict[str, int] = {
    "listing_entry_chars": 1536,
    "listing_total_chars": 2666,
    "description_words": 40,
    "deep_plan_skill_tokens": 4999,
    "phase_prompts_tokens": 2400,
    "fleet_recipe_lines": 150,
}



DEEP_PLAN_SKILL = "skills/deep-plan/SKILL.md"
EXECUTE_SKILL = "skills/deep-plan-execute/SKILL.md"
DESIGN_REVIEW_SKILL = "skills/design-review/SKILL.md"
TDD_REVIEW_SKILL = "skills/tdd-review/SKILL.md"
PRODUCT_REVIEW_SKILL = "skills/product-review/SKILL.md"
PHASE_PROMPTS = "skills/deep-plan/references/phase-prompts.md"
EDGE_FLOWS = "skills/deep-plan/references/edge-flows.md"
FLEET_RECIPE = "skills/design-review/references/fleet-orchestration.md"
PERSPECTIVES = "skills/deep-plan/references/perspectives.md"
PLAN_TEMPLATE = "skills/deep-plan/references/plan-file-template.md"
DESIGN_MD_TEMPLATE = "skills/deep-plan/references/design-md-template.md"
ARCHITECTURE_MD_TEMPLATE = "skills/deep-plan/references/architecture-md-template.md"
DESIGN_PRINCIPLES = "skills/design-review/references/design-principles.md"
TEST_PRINCIPLES = "skills/tdd-review/references/test-principles.md"
READABILITY_PRINCIPLES = "skills/deep-plan/references/readability-principles.md"
PLAN_INTEGRITY_PRINCIPLES = "skills/deep-plan/references/plan-integrity-principles.md"
IMPLEMENT_TASK_AGENT = "agents/dp-implement-task.md"
CRITIC_AGENT = "agents/dp-critic.md"

R1 = ("## R1", "## R2")
R2 = ("## R2", "## Anti-patterns")
PHASE_2 = ("## Phase 2", "## Phase 3")
PHASE_43 = ("### 4.3", "### 4.4")
PHASE_44 = ("### 4.4", "### 4.5")
PHASE_46 = ("## Phase 4.6", "### Checkpoint 2")
CHECKPOINT_2 = ("### Checkpoint 2", "## Phase 5")
PHASE_5 = ("## Phase 5", "## Output budget")
PROMPTS_PHASE_46 = ("## Phase 4.6", "## Phase 5")


GUARANTEES: tuple[Guarantee, ...] = (
    Guarantee(
        "deep-plan-skill.section-sequence",
        DEEP_PLAN_SKILL,
        "heading_present",
        {
            "headings": (
                "## R1",
                "## R2",
                "## Anti-patterns",
                "## High-level workflow",
                "## Phase 0",
                "## Phase 1",
                "### Checkpoint 1",
                "## Phase 2",
                "## Phase 3",
                "## Phase 4:",
                "### 4.3",
                "### 4.4",
                "### 4.5",
                "## Phase 4.6",
                "### Checkpoint 2",
                "## Phase 5",
                "## Output budget",
            )
        },
    ),
    Guarantee(
        "deep-plan-skill.read-only-contract-names-its-writable-paths",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {
            "region": R1,
            "patterns": (
                r"plans_dir",
                r"plan\.md",
                r"research\.md",
                r"probes\.md",
                r"design\.md",
                r"architecture\.md",
                r"SANDBOX_DIR",
                r"read-only",
            ),
        },
    ),
    Guarantee(
        "deep-plan-skill.allowlists-the-rename-guard",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": R1, "patterns": (r"Bash\(test ! -e docs/plans/\*\)",)},
    ),
    Guarantee(
        "deep-plan-skill.r2-makes-checkpoint-2-the-only-approval-gate",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": R2, "patterns": (r"Checkpoint 2", r"AskUserQuestion")},
    ),
    Guarantee(
        "deep-plan-skill.r2-forbids-the-plan-mode-tools",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": R2, "patterns": (r"EnterPlanMode", r"ExitPlanMode")},
    ),
    Guarantee(
        "deep-plan-skill.checkpoint-2-gate-is-an-askuserquestion",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": CHECKPOINT_2, "patterns": (r"AskUserQuestion",)},
    ),
    Guarantee(
        "deep-plan-skill.session-id-is-substituted",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": (r"\$\{CLAUDE_SESSION_ID\}",)},
    ),
    Guarantee(
        "deep-plan-skill.no-literal-session-id-placeholder",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": (r"<SESSION_ID>",), "absent": True},
    ),
    Guarantee(
        "deep-plan-skill.no-depth-knob",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": (r"depth:", r"Depth scaling", r"exhaustive"), "absent": True},
    ),
    Guarantee(
        "deep-plan-skill.no-harness-plan-path-wiring",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {
            "patterns": (r"harness_plan_path", r"--harness-plan-path", r"archive_plan_path"),
            "absent": True,
        },
    ),
    Guarantee(
        "deep-plan-skill.no-retired-agent-types",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": (r"dp-plan-critic", r"dp-plan-perspective"), "absent": True},
    ),
    Guarantee(
        "deep-plan-skill.draft-is-born-as-a-folder",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": (r"<topic>-draft/plan\.md", r"<slug>/plan\.md")},
    ),
    Guarantee(
        "deep-plan-skill.no-flat-plan-naming",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": (r"<topic>-draft\.md", r"\.probes\.md", r"\.research\.md"), "absent": True},
    ),
    Guarantee(
        "deep-plan-skill.phase-2-cites-the-design-rubric",
        DEEP_PLAN_SKILL,
        "path_exists",
        {"region": PHASE_2, "target": DESIGN_PRINCIPLES},
    ),
    Guarantee(
        "deep-plan-skill.phase-43-ends-on-the-deep-modules-lens",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": PHASE_43, "patterns": (r"deep-modules",)},
    ),
    Guarantee(
        "deep-plan-skill.phase-44-requires-the-tests-tdd-schema",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": PHASE_44, "patterns": (r"\*\*Tests \(TDD\)\*\*", r"field schema")},
    ),
    Guarantee(
        "deep-plan-skill.phase-44-cites-the-tests-authoring-rubric",
        DEEP_PLAN_SKILL,
        "path_exists",
        {"region": PHASE_44, "target": TEST_PRINCIPLES},
    ),
    Guarantee(
        "deep-plan-skill.phase-44-seeds-design-md-from-its-template",
        DEEP_PLAN_SKILL,
        "path_exists",
        {"region": PHASE_44, "target": DESIGN_MD_TEMPLATE, "cited_as": "references/design-md-template.md"},
    ),
    Guarantee(
        "deep-plan-skill.stale-draft-detection-globs-draft-folders",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"patterns": (r"\*-draft/",)},
    ),
    Guarantee(
        "deep-plan-skill.sentinel-branches-defer-to-the-edge-flows",
        DEEP_PLAN_SKILL,
        "path_exists",
        {"target": EDGE_FLOWS, "cited_as": "references/edge-flows.md"},
    ),
    Guarantee(
        "deep-plan-skill.phase-46-cites-the-design-red-flags",
        DEEP_PLAN_SKILL,
        "path_exists",
        {"region": PHASE_46, "target": DESIGN_PRINCIPLES, "cited_as": "design-principles.md"},
    ),
    Guarantee(
        "deep-plan-skill.phase-46-launches-the-critic-by-agent-type",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": PHASE_46, "patterns": (r"deep-plan:dp-critic",)},
    ),
    Guarantee(
        "deep-plan-skill.phase-46-cites-the-fleet-recipe",
        DEEP_PLAN_SKILL,
        "path_exists",
        {"region": PHASE_46, "target": FLEET_RECIPE},
    ),
    Guarantee(
        "deep-plan-skill.phase-46-cites-the-tests-red-flags",
        DEEP_PLAN_SKILL,
        "path_exists",
        {"region": PHASE_46, "target": TEST_PRINCIPLES},
    ),
    Guarantee(
        "deep-plan-skill.phase-46-cites-the-readability-red-flags",
        DEEP_PLAN_SKILL,
        "path_exists",
        {
            "region": PHASE_46,
            "target": READABILITY_PRINCIPLES,
            "cited_as": "readability-principles.md",
        },
    ),
    Guarantee(
        "deep-plan-skill.phase-46-cites-the-plan-integrity-red-flags",
        DEEP_PLAN_SKILL,
        "path_exists",
        {
            "region": PHASE_46,
            "target": PLAN_INTEGRITY_PRINCIPLES,
            "cited_as": "plan-integrity-principles.md",
        },
    ),
    Guarantee(
        "deep-plan-skill.phase-5-handoff-names-the-conditional-architecture-member",
        DEEP_PLAN_SKILL,
        "anchor_regex",
        {"region": PHASE_5, "patterns": (r"architecture\.md\s+members\s+when\s+present",)},
    ),
    Guarantee(
        "deep-plan-skill.is-slash-command-only",
        DEEP_PLAN_SKILL,
        "frontmatter_field",
        {"field": "disable-model-invocation", "contains": "true"},
    ),
    Guarantee(
        "deep-plan-skill.name-matches-its-directory",
        DEEP_PLAN_SKILL,
        "frontmatter_field",
        {"field": "name", "contains": "deep-plan"},
    ),
    Guarantee(
        "phase-prompts.no-depth-knob",
        PHASE_PROMPTS,
        "anchor_regex",
        {"patterns": (r"depth:", r"Depth scaling", r"exhaustive"), "absent": True},
    ),
    Guarantee(
        "phase-prompts.no-retired-agent-types",
        PHASE_PROMPTS,
        "anchor_regex",
        {"patterns": (r"dp-plan-critic",), "absent": True},
    ),
    Guarantee(
        "phase-prompts.phase-46-names-a-review-target-per-cluster-source",
        PHASE_PROMPTS,
        "anchor_regex",
        {
            "region": PROMPTS_PHASE_46,
            "patterns": (
                r"design-principles\.md",
                r"test-principles\.md",
                r"readability-principles\.md",
                r"plan-integrity-principles\.md",
            ),
        },
    ),
    Guarantee(
        "phase-prompts.rename-guards-both-naming-forms",
        PHASE_PROMPTS,
        "anchor_regex",
        {"patterns": (r"test ! -e .*test ! -e .*mv ",)},
    ),
    Guarantee(
        "edge-flows.covers-every-sentinel-and-r3-trigger",
        EDGE_FLOWS,
        "anchor_regex",
        {
            "patterns": (
                r"prompt_for_plans_dir",
                r"plans_dir_under_protected_path",
                r"no_git",
                r"\*-draft/",
                r"resolve_slug\.py",
            )
        },
    ),
    Guarantee(
        "edge-flows.every-flow-asks-rather-than-acting",
        EDGE_FLOWS,
        "anchor_regex",
        {"patterns": (r"AskUserQuestion",)},
    ),
    Guarantee(
        "edge-flows.persists-the-plans-dir-choice",
        EDGE_FLOWS,
        "script_invoked",
        {"script": "setup_session.py", "flag": "--update"},
    ),
    Guarantee(
        "execute-skill.step-sequence",
        EXECUTE_SKILL,
        "heading_present",
        {
            "headings": (
                "## Step 1",
                "## Step 2",
                "## Step 3",
                "## Step 4",
                "## Preflight",
                "## Step 5",
                "## Subagent budget",
                "## Step 6: Completion (folder plans only)",
                "## Anti-patterns",
            )
        },
    ),
    Guarantee(
        "execute-skill.name-matches-its-directory",
        EXECUTE_SKILL,
        "frontmatter_field",
        {"field": "name", "contains": "deep-plan-execute"},
    ),
    Guarantee(
        "execute-skill.resolves-the-plan-via-the-approval-memo",
        EXECUTE_SKILL,
        "script_invoked",
        {"script": "setup_session.py", "flag": "--lookup"},
    ),
    Guarantee(
        "execute-skill.keeps-the-newest-mtime-fallback",
        EXECUTE_SKILL,
        "anchor_regex",
        {"patterns": (r"ls -td",)},
    ),
    Guarantee(
        "execute-skill.parses-the-plan-with-load-tasks",
        EXECUTE_SKILL,
        "script_invoked",
        {"script": "load_tasks.py"},
    ),
    Guarantee(
        "execute-skill.refreshes-the-plans-index-on-completion",
        EXECUTE_SKILL,
        "script_invoked",
        {"script": "finalize_plan.py", "flag": "--index"},
    ),
    Guarantee(
        "execute-skill.wires-dependencies-with-addblockedby",
        EXECUTE_SKILL,
        "anchor_regex",
        {"patterns": (r"addBlockedBy", r"TaskUpdate")},
    ),
    Guarantee(
        "execute-skill.discovery-prefers-folder-plans-and-skips-non-plans",
        EXECUTE_SKILL,
        "anchor_regex",
        {"patterns": (r"\*/plan\.md", r"README", r"-draft/plan")},
    ),
    Guarantee(
        "execute-skill.audits-task-scope-with-both-halves-of-the-diff",
        EXECUTE_SKILL,
        "anchor_regex",
        {
            "patterns": (
                r"git ls-files --others --exclude-standard",
                r"git diff --name-only",
                r"deep-plan:dp-implement-task",
                r"design\.md",
            )
        },
    ),
    Guarantee(
        "execute-skill.states-the-session-subagent-cap-and-its-degradation",
        EXECUTE_SKILL,
        "anchor_regex",
        {
            "region": ("## Subagent budget", "## Step 6"),
            "patterns": (r"200 subagents", r"`full`", r"`design-only`", r"`inline`"),
        },
    ),
    Guarantee(
        "execute-skill.cites-the-fleet-recipe-as-the-caps-home",
        EXECUTE_SKILL,
        "path_exists",
        {"region": ("## Subagent budget", "## Step 6"), "target": FLEET_RECIPE},
    ),
    Guarantee(
        "execute-skill.step-3-reads-architecture-md-when-present",
        EXECUTE_SKILL,
        "anchor_regex",
        {"region": ("## Step 3", "## Step 4"), "patterns": (r"architecture\.md",)},
    ),
    Guarantee(
        "execute-skill.flips-the-plan-status-on-completion",
        EXECUTE_SKILL,
        "anchor_regex",
        {"patterns": (r"\*\*Status\*\*: executed",)},
    ),
    Guarantee(
        "execute-skill.carries-no-state-schema-knowledge",
        EXECUTE_SKILL,
        "anchor_regex",
        {"patterns": (r"projects\.json", r"XDG_STATE_HOME"), "absent": True},
    ),
    Guarantee(
        "execute-skill.does-not-launch-critics-itself",
        EXECUTE_SKILL,
        "anchor_regex",
        {"patterns": (r"dp-[a-z-]*critic",), "absent": True},
    ),
    Guarantee(
        "fleet-recipe.section-spine",
        FLEET_RECIPE,
        "heading_present",
        {
            "headings": (
                "## Triage gate",
                "## Workflow fleet",
                "## Version gate",
                "## Fallback",
                "## Nested fleets",
                "## Session agent budget",
                "## agentType resolution",
            )
        },
    ),
    Guarantee(
        "fleet-recipe.finding-line-is-the-wire-contract",
        FLEET_RECIPE,
        "anchor_regex",
        {"patterns": (r"\[material\|minor\]", r"\{cluster\}/\{principle\}", r"evidence:")},
    ),
    Guarantee(
        "fleet-recipe.workflow-reads-the-critic-type-from-its-args",
        FLEET_RECIPE,
        "anchor_regex",
        {"patterns": (r"args\.agentType", r"2\.1\.154")},
    ),
    Guarantee(
        "fleet-recipe.carries-a-probe-status-marker",
        FLEET_RECIPE,
        "anchor_regex",
        {"patterns": (r"^Probe status:",)},
    ),
    Guarantee(
        "fleet-recipe.nested-fleets-launch-in-the-foreground",
        FLEET_RECIPE,
        "anchor_regex",
        {"patterns": (r"run_in_background: false",)},
    ),
    Guarantee(
        "fleet-recipe.names-the-session-cap-env-var",
        FLEET_RECIPE,
        "anchor_regex",
        {"patterns": (r"CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION",)},
    ),
    Guarantee(
        "fleet-recipe.pairs-the-design-cluster-with-its-principles-file",
        FLEET_RECIPE,
        "path_exists",
        {"target": DESIGN_PRINCIPLES, "cited_as": "design-principles.md"},
    ),
    Guarantee(
        "fleet-recipe.pairs-the-tests-cluster-with-its-principles-file",
        FLEET_RECIPE,
        "path_exists",
        {"target": TEST_PRINCIPLES, "cited_as": "test-principles.md"},
    ),
    Guarantee(
        "fleet-recipe.pairs-the-readability-cluster-with-its-principles-file",
        FLEET_RECIPE,
        "path_exists",
        {"target": READABILITY_PRINCIPLES, "cited_as": "readability-principles.md"},
    ),
    Guarantee(
        "fleet-recipe.pairs-the-plan-integrity-cluster-with-its-principles-file",
        FLEET_RECIPE,
        "path_exists",
        {"target": PLAN_INTEGRITY_PRINCIPLES},
    ),
    Guarantee(
        "fleet-recipe.registers-the-product-cluster-source",
        FLEET_RECIPE,
        "anchor_regex",
        {"patterns": (r"skills/product-\*/references/product-\*-principles\.md",)},
    ),
    Guarantee(
        "design-principles.section-spine",
        DESIGN_PRINCIPLES,
        "heading_present",
        {
            "headings": (
                "## Attribution and scope",
                "## Plan-time principles",
                "## Review-time red flags",
                "## Execute-time craft rules",
                "## How to update these guidelines",
            )
        },
    ),
    Guarantee(
        "test-principles.section-spine",
        TEST_PRINCIPLES,
        "heading_present",
        {
            "headings": (
                "## Plan-time authoring rules",
                "## Review-time red flags",
                "## Execute-time run rules",
                "## How to update these guidelines",
            )
        },
    ),
    Guarantee(
        "test-principles.carries-no-attribution-section",
        TEST_PRINCIPLES,
        "anchor_regex",
        {"patterns": (r"Attribution",), "absent": True},
    ),
    Guarantee(
        "readability-principles.section-spine",
        READABILITY_PRINCIPLES,
        "heading_present",
        {
            "headings": (
                "## Plan-time authoring rules",
                "## Review-time red flags",
                "## How to update these guidelines",
            )
        },
    ),
    Guarantee(
        "design-review-skill.cites-the-fleet-recipe",
        DESIGN_REVIEW_SKILL,
        "path_exists",
        {"target": FLEET_RECIPE, "cited_as": "references/fleet-orchestration.md"},
    ),
    Guarantee(
        "design-review-skill.cites-its-principles-file",
        DESIGN_REVIEW_SKILL,
        "path_exists",
        {"target": DESIGN_PRINCIPLES, "cited_as": "references/design-principles.md"},
    ),
    Guarantee(
        "design-review-skill.launches-the-critic-by-agent-type",
        DESIGN_REVIEW_SKILL,
        "anchor_regex",
        {"patterns": (r"deep-plan:dp-critic",)},
    ),
    Guarantee(
        "design-review-skill.name-matches-its-directory",
        DESIGN_REVIEW_SKILL,
        "frontmatter_field",
        {"field": "name", "contains": "design-review"},
    ),
    Guarantee(
        "tdd-review-skill.cites-the-fleet-recipe",
        TDD_REVIEW_SKILL,
        "path_exists",
        {"target": FLEET_RECIPE, "cited_as": "fleet-orchestration.md"},
    ),
    Guarantee(
        "tdd-review-skill.cites-its-principles-file",
        TDD_REVIEW_SKILL,
        "path_exists",
        {"target": TEST_PRINCIPLES, "cited_as": "references/test-principles.md"},
    ),
    Guarantee(
        "tdd-review-skill.launches-the-critic-by-agent-type",
        TDD_REVIEW_SKILL,
        "anchor_regex",
        {"patterns": (r"deep-plan:dp-critic",)},
    ),
    Guarantee(
        "product-review-skill.cites-the-fleet-recipe",
        PRODUCT_REVIEW_SKILL,
        "path_exists",
        {"target": FLEET_RECIPE},
    ),
    Guarantee(
        "product-review-skill.launches-the-critic-by-agent-type",
        PRODUCT_REVIEW_SKILL,
        "anchor_regex",
        {"patterns": (r"deep-plan:dp-critic",)},
    ),
    Guarantee(
        "product-review-skill.name-matches-its-directory",
        PRODUCT_REVIEW_SKILL,
        "frontmatter_field",
        {"field": "name", "contains": "product-review"},
    ),
    Guarantee(
        "critic-agent.reads-its-own-cluster-source",
        CRITIC_AGENT,
        "anchor_regex",
        {
            "region": ("**Your cluster source**", "**Your assigned cluster**"),
            "patterns": (r"`Read`",),
        },
    ),
    Guarantee(
        "implement-task-agent.cites-the-execute-time-run-rules",
        IMPLEMENT_TASK_AGENT,
        "path_exists",
        {"target": TEST_PRINCIPLES},
    ),
    Guarantee(
        "implement-task-agent.cites-the-execute-time-craft-rules",
        IMPLEMENT_TASK_AGENT,
        "path_exists",
        {"target": DESIGN_PRINCIPLES},
    ),
    Guarantee(
        "implement-task-agent.cites-the-fleet-recipe",
        IMPLEMENT_TASK_AGENT,
        "path_exists",
        {"target": FLEET_RECIPE, "cited_as": "fleet-orchestration.md"},
    ),
    Guarantee(
        "implement-task-agent.loads-its-task-with-load-tasks",
        IMPLEMENT_TASK_AGENT,
        "script_invoked",
        {"script": "load_tasks.py", "flag": "--task"},
    ),
    Guarantee(
        "implement-task-agent.launches-the-critic-by-agent-type",
        IMPLEMENT_TASK_AGENT,
        "anchor_regex",
        {"patterns": (r"deep-plan:dp-critic",)},
    ),
    Guarantee(
        "implement-task-agent.honours-the-dispatchers-fleet-mode",
        IMPLEMENT_TASK_AGENT,
        "anchor_regex",
        {"patterns": (r"fleet_mode", r"run_in_background: false")},
    ),
    Guarantee(
        "plan-template.names-every-folder-member",
        PLAN_TEMPLATE,
        "anchor_regex",
        {
            "patterns": (
                r"plan\.md",
                r"research\.md",
                r"probes\.md",
                r"design\.md",
                r"architecture\.md",
            )
        },
    ),
    Guarantee(
        "plan-template.no-dotted-sibling-naming",
        PLAN_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"<slug>\.probes\.md", r"<slug>\.research\.md"), "absent": True},
    ),
    Guarantee(
        "plan-template.change-block-is-a-summary-sentence-then-sub-bullets",
        PLAN_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"summary sentence", r"sub-bullets")},
    ),
    Guarantee(
        "plan-template.declares-the-tests-tdd-block",
        PLAN_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"\*\*Tests \(TDD\)\*\*",)},
    ),
    Guarantee(
        "plan-template.no-retired-dossier-section-list",
        PLAN_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"Canonical snippet",), "absent": True},
    ),
    Guarantee(
        "plan-template.cites-the-readability-authoring-rules",
        PLAN_TEMPLATE,
        "path_exists",
        {"target": READABILITY_PRINCIPLES},
    ),
    Guarantee(
        "design-md-template.cites-the-readability-authoring-rules",
        DESIGN_MD_TEMPLATE,
        "path_exists",
        {"target": READABILITY_PRINCIPLES, "cited_as": "readability-principles.md"},
    ),
    Guarantee(
        "design-md-template.states-the-anchor-slug-rule",
        DESIGN_MD_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"anchor slug", r"hyphens")},
    ),
    Guarantee(
        "design-md-template.no-retired-field-block-shape",
        DESIGN_MD_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"\*\*Chosen\*\*",), "absent": True},
    ),
    Guarantee(
        "architecture-md-template.carries-a-diagram-fence",
        ARCHITECTURE_MD_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"```mermaid",)},
    ),
    Guarantee(
        "architecture-md-template.significance-test-carries-its-skip-list",
        ARCHITECTURE_MD_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"reversible",)},
    ),
    Guarantee(
        "architecture-md-template.seam-rule-leaves-rationale-in-design-md",
        ARCHITECTURE_MD_TEMPLATE,
        "anchor_regex",
        {"patterns": (r"design\.md",)},
    ),
    Guarantee(
        "perspectives.points-tests-authoring-at-the-tdd-rubric",
        PERSPECTIVES,
        "path_exists",
        {"target": TEST_PRINCIPLES, "cited_as": "tdd-review/references/test-principles.md"},
    ),
)




class _RegionMissing(Exception):
    """A guarantee narrowed to a region whose start marker is not there."""


def check(guarantee: Guarantee) -> str | None:
    """Verify one guarantee, returning a failure message or None if it holds.

    The message is the guarantee's whole error interface: it names the id, the
    file, and the pattern, path, or field that was absent, so a red case is
    readable without opening either this module or the file under test.
    """
    handler = _HANDLERS.get(guarantee.kind)
    if handler is None:
        return _failure(guarantee, f"unknown guarantee kind {guarantee.kind!r}")

    target = ROOT / guarantee.path
    if not target.is_file():
        return _failure(guarantee, f"the file it names does not exist: {target}")

    try:
        detail = handler(target, target.read_text(encoding="utf-8"), guarantee.params)
    except _RegionMissing as missing:
        return _failure(guarantee, str(missing))
    return None if detail is None else _failure(guarantee, detail)


def _failure(guarantee: Guarantee, detail: str) -> str:
    return f"guarantee {guarantee.id!r} broken in {guarantee.path}: {detail}"


def _narrowed(text: str, params: Mapping[str, Any]) -> str:
    """Return the region a guarantee applies to, or the whole file.

    A region is a (start marker, end marker) pair, matched as substrings the
    way the skills' own callers slice these files. A missing start marker is
    itself a failure: the guarantee is about a section that no longer exists.
    """
    region = params.get("region")
    if region is None:
        return text
    start_marker, end_marker = region
    start = text.find(start_marker)
    if start == -1:
        raise _RegionMissing(f"region start marker {start_marker!r} is absent")
    end = text.find(end_marker, start + len(start_marker))
    return text[start:] if end == -1 else text[start:end]


def _where(params: Mapping[str, Any]) -> str:
    region = params.get("region")
    return "" if region is None else f" within {region[0]!r}..{region[1]!r}"


def _heading_present(path: Path, text: str, params: Mapping[str, Any]) -> str | None:
    """Every listed heading appears as a line prefix, in the listed order."""
    lines = text.splitlines()
    cursor = -1
    for heading in params["headings"]:
        found = next((i for i in range(cursor + 1, len(lines)) if lines[i].startswith(heading)), None)
        if found is None:
            after = "" if cursor < 0 else f" after line {cursor + 1}"
            return f"heading {heading!r} is absent{after}"
        cursor = found
    return None


def _anchor_regex(path: Path, text: str, params: Mapping[str, Any]) -> str | None:
    """Every pattern is found, or -- with `absent` -- none of them is."""
    body = _narrowed(text, params)
    patterns: tuple[str, ...] = params["patterns"]
    hits = [p for p in patterns if re.search(p, body, re.MULTILINE)]
    if params.get("absent", False):
        if hits:
            return f"pattern(s) {hits} must not appear{_where(params)} but do"
        return None
    missing = [p for p in patterns if p not in hits]
    if missing:
        return f"pattern(s) {missing} are absent{_where(params)}"
    return None


def _script_invoked(path: Path, text: str, params: Mapping[str, Any]) -> str | None:
    """A named helper script is invoked, exists, and accepts the flag passed."""
    script = params["script"]
    source = SCRIPTS / script
    if not source.is_file():
        return f"invokes {script}, which does not exist under {SCRIPTS.relative_to(ROOT)}"
    if script not in text:
        return f"does not invoke the helper script {script}"
    flag = params.get("flag")
    if flag is None:
        return None
    if flag not in text:
        return f"does not pass {flag} to {script}"
    if flag not in source.read_text(encoding="utf-8"):
        return f"passes {flag} to {script}, whose source does not declare that flag"
    return None


def _frontmatter_field(path: Path, text: str, params: Mapping[str, Any]) -> str | None:
    """A top-level frontmatter key is present (or absent), with the right value."""
    block = _frontmatter(text)
    if not block:
        return "has no frontmatter block"
    field = params["field"]
    value = _field_value(block, field)
    absent = params.get("absent", False)
    contains = params.get("contains")

    if contains is None:
        if absent:
            return None if value is None else f"frontmatter must not carry {field!r}"
        return None if value is not None else f"frontmatter is missing {field!r}"
    if value is None:
        return f"frontmatter is missing {field!r}, so its value cannot carry {contains!r}"
    if absent:
        return None if contains not in value else f"frontmatter {field!r} must not list {contains!r}"
    return None if contains in value else f"frontmatter {field!r} does not carry {contains!r}"


def _path_exists(path: Path, text: str, params: Mapping[str, Any]) -> str | None:
    """A path this file cites resolves to a real file.

    `target` is the repo-relative file the citation must name; `cited_as` is the
    literal the file writes when the two differ (a `${CLAUDE_PLUGIN_ROOT}`
    prefix, a skill-local `references/` path, or a bare basename), defaulting to
    `target` because most callers cite the full repo-relative path.
    """
    target: str = params["target"]
    cited_as: str = params.get("cited_as", target)
    if not cited_as or not target.endswith(cited_as.rsplit("/", 1)[-1]):
        return f"inventory error: citation {cited_as!r} cannot name {target!r}"

    body = _narrowed(text, params)
    if cited_as not in body:
        return f"does not cite {cited_as!r}{_where(params)}"
    if not (ROOT / target).is_file():
        return f"cites {cited_as!r}, but {target} is not a file"
    return None


_HANDLERS: dict[str, Callable[[Path, str, Mapping[str, Any]], str | None]] = {
    "heading_present": _heading_present,
    "anchor_regex": _anchor_regex,
    "script_invoked": _script_invoked,
    "frontmatter_field": _frontmatter_field,
    "path_exists": _path_exists,
}


def frontmatter_value(text: str, field: str) -> str | None:
    """The value of a top-level frontmatter key in a whole file, or None.

    Public because `test_guarantees.py` reads an agent's `model` and
    `disallowedTools` when it pins the merged critic leaf's profile, and it must
    read them the way a `frontmatter_field` guarantee does. A second
    frontmatter parser would eventually disagree with this one about folded
    scalars, and then the guarantee and the pin would protect different files.
    """
    return _field_value(_frontmatter(text), field)


def listing_entry(text: str) -> str | None:
    """The text one `SKILL.md` contributes to the model-facing skill listing.

    `None` means the file contributes nothing at all. The harness documents
    `disable-model-invocation: true` as removing the skill from Claude's
    context entirely, so its description never reaches the listing and never
    spends any of the listing's shared budget. That is a different answer from
    `""`, which is a skill that *is* listed carrying no text -- unroutable, but
    still an entry -- so callers that sum entries must skip `None` rather than
    treat it as zero-length.

    Otherwise the entry is `description` followed by `when_to_use`, which the
    frontmatter reference describes as appended to `description` in the listing
    and counted against the same per-entry cap. Both are collapsed to one line,
    because that is the form the cap applies to rather than the source's
    indentation, and an absent `when_to_use` contributes nothing.

    The neighbouring flag `user-invocable: false` deliberately does not exclude:
    its documented row reads "Description always in context", and it controls
    slash-menu visibility only. Keying on it would under-count the listing, and
    an aggregate assertion built on an under-count passes while over budget.

    Public because the per-entry cap and the aggregate ceiling have to measure
    the same string. Two definitions of what reaches the listing would drift,
    and the aggregate is the one whose drift is silent.
    """
    if scalar_text(frontmatter_value(text, "disable-model-invocation")).lower() == "true":
        return None
    entry = (
        scalar_text(frontmatter_value(text, "description")),
        scalar_text(frontmatter_value(text, "when_to_use")),
    )
    return " ".join(field for field in entry if field)


_BLOCK_SCALAR = re.compile(r"^[|>][+-]?\d*(?:\s|$)")


def scalar_text(raw: str | None) -> str:
    """One frontmatter value as its reader sees it: a single collapsed line.

    Whitespace is collapsed because both YAML block styles turn the folded
    source lines into single separators, so the result matches the value the
    harness works with rather than the source's line breaks and indentation. A
    missing key reads as `""`, which lets a caller concatenate optional fields
    without a presence check per field.

    Public because more than one budget needs it: the word budget measures
    `description` on its own while the character cap measures the whole entry,
    and the two only stay comparable while they normalise the same way.
    """
    if raw is None:
        return ""
    return " ".join(_BLOCK_SCALAR.sub("", raw.strip(), count=1).split())


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def _field_value(block: str, field: str) -> str | None:
    """The value of a top-level frontmatter key, including folded continuations.

    Keys are matched at column 0, so a commented-out or nested look-alike
    cannot satisfy a guarantee. Continuation lines are the indented ones (a
    folded scalar) plus top-level list items (a YAML sequence).
    """
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(f"{field}:"):
            continue
        value = [line[len(field) + 1 :]]
        for following in lines[index + 1 :]:
            if following and not following.startswith((" ", "\t", "-")):
                break
            value.append(following)
        return "\n".join(value)
    return None
