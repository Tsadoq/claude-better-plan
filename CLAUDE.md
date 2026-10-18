# CLAUDE.md

Single-plugin Claude Code marketplace: the repo root is both the plugin root and the marketplace root, and its source tree is Claude-native; other hosts install rendered builds from `dist/`. The plugin (`deep-plan`) ships two pipelines — plan-and-build (`/deep-plan`, `/deep-plan:deep-plan-execute`) and the product chain (`/product-brief` → `/product-issues`) — plus three review commands. Everything shipped is markdown prompt content and stdlib-only Python; the only runtime dependencies are the pi build's npm extensions in `package.json`.

## Layout

- `skills/<name>/SKILL.md` — one command each (12 total). `skills/product-artifacts/` is the exception: no SKILL.md, it is the shared substrate for the product chain (`scripts/product_artifact.py`, `references/artifact-family.md`).
- `skills/<name>/references/` — templates and principles files, loaded only when a run reads them.
- `skills/<name>/scripts/` — stdlib-only helpers (`setup_session.py`, `finalize_plan.py`, `load_tasks.py`, `resolve_slug.py` under deep-plan; six filing modules under product-issues).
- `skills/deep-plan/hooks/cleanup.py` — bound to `SessionEnd` (a test forbids `Stop:`).
- `agents/` — six `dp-*` subagents. Exactly one may write (`dp-implement-task`); `test_agents_contract.py` pins this.
- `lib/artifact_common.py` — slug + generated-region primitives shared by both pipelines.
- `tests/` — cross-skill contracts; per-skill contract tests live in `skills/<name>/tests/`.
- `hosts/<host>/` — render profiles (`generic`, `codex`, `pi`): `PROFILE` in `__init__.py`, a `HOST.md` shipped at the build root, optional `overlays/`. Codex `extends` generic; pi does not (it runs its own rules, then generic's). `hosts/pi/` also vendors the pi TypeScript extensions.
- `tools/render_hosts.py` — renders the source into `dist/<host>/`; `--check` reports stale builds. `tools/smoke_pi.sh` — manual end-to-end check of `dist/pi` in a real pi (`SMOKE_MODEL`, `SMOKE_TIMEOUT`, `KEEP`; symlinks your real pi `auth.json`).
- `dist/<host>/` — generated, committed builds (`dist/` is tracked). Never hand-edited.
- `plugin.json` + `.agents/plugins/marketplace.json` (Codex, points at `./dist/codex`), `package.json` (pi, points at `./dist/pi`; pins `undici` 8.11.2, peer-depends on `@earendil-works/pi-agent-core`), `install.sh` (any agent; installs `dist/generic` and resolves its plugin-root placeholder). All three manifests carry the version; CI bumps them together.
- `docs/plans/` — gitignored dogfood output, not documentation. `docs/*.md` is the real documentation.

## Commands (the CI gate)

```
uvx ruff check lib skills tools hosts
uvx mypy --strict          # scope from pyproject.toml
uvx pytest -q              # discovery from pyproject testpaths (13 entries)
```

## Rules that bite

- **Contract tests pin behavior, not wording.** `GUARANTEES` in `tests/guarantees.py` declares what each shipped file must still do; `BUDGETS` caps sizes (skill-listing chars, description words, token budgets). Reword freely; never delete a guaranteed behavior. A budget never justifies dropping one.
- **Doc scans.** Tests scan `README.md`, `PLAN.md`, and all shipped markdown for `dp-*` names that don't exist in `agents/` and for false harness claims. Keep agent names exact.
- **Never hand-edit the version** in `.claude-plugin/plugin.json` (or `plugin.json` / `package.json`). CI auto-bumps from Conventional Commit types (`feat:`/`fix:` cut a release). Layout-moving changes must be `feat:`/`fix:` typed — the bump re-keys the installed plugin cache. Doc-only changes use `docs:`.
- **Builds go stale.** After any change to `skills/`, `agents/`, `lib/`, `PLAN.md`, or `hosts/`, run `python3 tools/render_hosts.py` and commit `dist/` with it; `test_build_is_fresh` fails otherwise. Fix a build by editing the source or the profile, never `dist/`.
- **Generated regions** (the `plans_dir/README.md` index, `## Task overview` tables, `docs/product/README.md`) sit between HTML-comment markers and are never hand-edited — regenerate via `finalize_plan.py` / `product_artifact.py`.
- **Hot reload**: `SKILL.md` and `references/` changes apply within a session; `agents/` changes need `/reload-plugins` or a restart.
- Python is ruff-clean and `mypy --strict` (py312, line length 110); helpers stay stdlib-only.
