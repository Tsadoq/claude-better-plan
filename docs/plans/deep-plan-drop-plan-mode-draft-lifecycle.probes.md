## Verification probes (appendix)

All probes are PRE-CHANGE baselines captured before implementation; the touchpoint counts and state-field listings describe the current code, which the tasks drive to zero or to the new shape.

[probe 1]: grep -rcE "EnterPlanMode|ExitPlanMode|harness" SKILL.md phase-prompts.md plan-file-template.md README.md PLAN.md
README.md:9
plan-file-template.md:1
phase-prompts.md:12
SKILL.md:23
PLAN.md:41

[probe 2]: grep -n -A 3 "PERMITTED_UPDATE_KEYS" skills/deep-plan/scripts/setup_session.py
89:PERMITTED_UPDATE_KEYS = {
90:    "plans_dir",
91:    "archive_plan_path",
92:    "harness_plan_path",
(set continues; phase/decisions confirmed present by exploration)

[probe 3]: uv run pytest skills/deep-plan/tests --collect-only -q
error: No `project` table found in: `/Users/tsadoq/gits/claude-better-plan/pyproject.toml`
=> all verification commands use python3 -m pytest instead

[probe 4]: python3 -m pytest skills/deep-plan/tests --collect-only -q
25 tests collected in 0.05s

[probe 5]: grep -n "harness|plan mode|ExitPlanMode" skills/deep-plan-execute/SKILL.md
5:  harness tasks (one TaskCreate each), wires Depends on into addBlockedBy, then
15:is to turn the plan's ## Tasks block into real harness tasks with dependencies
=> "harness tasks" means TaskCreate tasks, not plan-mode coupling; no changes needed

[probe 6]: grep -rn "plan-mode|plan mode" .claude-plugin/
plugin.json:4: description "Replaces default plan mode for non-trivial work: ..."
plugin.json:11: keyword "plan-mode"
marketplace.json:4: "tsadoq's plan-mode plugins for Claude Code."
marketplace.json:9: "Triangulated, decision-surfacing replacement for default plan mode."
