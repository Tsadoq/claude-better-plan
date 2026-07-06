## Verification probes (appendix)

[probe 1]: ls skills/deep-plan/tests/ skills/deep-plan/tests/golden/
```
golden/
test_agents_contract.py  test_cleanup.py  test_design_review_contract.py
test_finalize.py  test_load_tasks.py  test_resolve_slug.py
test_setup_session.py  test_skill_contract.py  test_template_contract.py
example-plan.md
```
All test files and the golden fixture referenced by tasks exist.

[probe 2]: uvx pytest skills/deep-plan/tests -q
```
......................................                                   [100%]
38 passed in 0.14s
```
Baseline green. Note: `python3 -m pytest` fails on this machine (system python3 has no pytest module), so verification commands use `uvx pytest`.

[probe 3]: dual-read discovery simulation in sandbox (folder plan newer than legacy flat plan)
```
$ ls -t */plan.md *.md | grep -vE '(\.(probes|research)\.md|^README\.md)$'
new-style-plan/plan.md
README.md            <- leaked: line-anchor defeated by decorated ls output
legacy-plan.md
```
`ls -t` orders correctly across both shapes; the README exclusion must be path-anchored (`/(README|[^/]*\.(probes|research))\.md$`) as encoded in Task 10, not line-anchored.

[probe 4]: grep -rln for dotted-sibling naming across *.md, *.py, *.json (excluding docs/plans)
```
README.md
skills/deep-plan-execute/SKILL.md
skills/deep-plan/scripts/finalize_plan.py
skills/deep-plan/tests/test_finalize.py
skills/deep-plan/SKILL.md
skills/deep-plan/references/plan-file-template.md
skills/deep-plan/references/phase-prompts.md
PLAN.md
```
Complete inventory of dotted-sibling touchpoints; `.claude-plugin/*.json` and `agents/dp-*.md` are clean, confirming Task 11's no-manifest-change claim.

[probe 5]: test import mechanism and cross-script imports
```
tests/ has no conftest.py; tests load scripts via importlib from tests/../scripts.
load_tasks.py line 39: from finalize_plan import _header_pos, _section_body, _section_end
pyproject.toml: [tool.ruff], [tool.mypy] configured for the scripts dir.
```
Cross-script import precedent exists, supporting the shared-constants-in-finalize_plan.py merge call.

[probe 6]: uvx ruff check skills/deep-plan; uvx mypy --strict skills/deep-plan/scripts skills/deep-plan/hooks; CI config
```
All checks passed!
Success: no issues found in 5 source files
.github/workflows/ci.yml: pip install ruff mypy pytest (Python 3.12);
  ruff check skills/deep-plan; mypy --strict scripts hooks; python -m pytest tests -v
```
Task 12's full gate is validated locally, and CI runs the same unpinned tools, so local uvx and CI pip stay in parity.
