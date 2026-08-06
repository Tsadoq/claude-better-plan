# CLAUDE.md

Single-plugin Claude Code marketplace: the repo root is both the plugin root and the marketplace root. The plugin (`deep-plan`) ships two pipelines — plan-and-build (`/deep-plan`, `/deep-plan:deep-plan-execute`) and the product chain (`/product-brief` → `/product-issues`) — plus three review commands. Everything shipped is markdown prompt content and stdlib-only Python; there are no runtime dependencies.

## Layout

- `skills/<name>/SKILL.md` — one command each (12 total). `skills/product-artifacts/` is the exception: no SKILL.md, it is the shared substrate for the product chain (`scripts/product_artifact.py`, `references/artifact-family.md`).
- `skills/<name>/references/` — templates and principles files, loaded only when a run reads them.
- `skills/<name>/scripts/` — stdlib-only helpers (`setup_session.py`, `finalize_plan.py`, `load_tasks.py`, `resolve_slug.py` under deep-plan; six filing modules under product-issues).
- `skills/deep-plan/hooks/cleanup.py` — bound to `SessionEnd` (a test forbids `Stop:`).
- `agents/` — six `dp-*` subagents. Exactly one may write (`dp-implement-task`); `test_agents_contract.py` pins this.
- `lib/artifact_common.py` — slug + generated-region primitives shared by both pipelines.
- `tests/` — cross-skill contracts; per-skill contract tests live in `skills/<name>/tests/`.
- `docs/plans/` — gitignored dogfood output, not documentation. `docs/*.md` is the real documentation.

## Commands (the CI gate)

```
uvx ruff check lib skills
uvx mypy --strict          # scope from pyproject.toml
uvx pytest -q              # discovery from pyproject testpaths (13 entries)
```

## Rules that bite

- **Contract tests pin behavior, not wording.** `GUARANTEES` in `tests/guarantees.py` declares what each shipped file must still do; `BUDGETS` caps sizes (skill-listing chars, description words, token budgets). Reword freely; never delete a guaranteed behavior. A budget never justifies dropping one.
- **Doc scans.** Tests scan `README.md`, `PLAN.md`, and all shipped markdown for `dp-*` names that don't exist in `agents/` and for false harness claims. Keep agent names exact.
- **Never hand-edit the version** in `.claude-plugin/plugin.json`. CI auto-bumps from Conventional Commit types (`feat:`/`fix:` cut a release). Layout-moving changes must be `feat:`/`fix:` typed — the bump re-keys the installed plugin cache. Doc-only changes use `docs:`.
- **Generated regions** (the `plans_dir/README.md` index, `## Task overview` tables, `docs/product/README.md`) sit between HTML-comment markers and are never hand-edited — regenerate via `finalize_plan.py` / `product_artifact.py`.
- **Hot reload**: `SKILL.md` and `references/` changes apply within a session; `agents/` changes need `/reload-plugins` or a restart.
- Python is ruff-clean and `mypy --strict` (py312, line length 110); helpers stay stdlib-only.
