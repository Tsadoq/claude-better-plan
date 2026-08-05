# deep-plan

A Claude Code plugin for deep, co-authored planning of non-trivial work. You are a co-author, not a reviewer: the skill never silently picks between meaningful options, and every plan it produces is an AI-consumable artifact in your repo that a companion command can implement test-first.

## How it works

`/deep-plan <topic>` runs a phased workflow with two hard user gates:

1. **Research** -- three subagents triangulate in parallel: your codebase, a light web sweep, and any sources you provide (files, URLs, Jira tickets). You confirm the scope before anything else happens.
2. **Decisions** -- every meaningful sub-decision (storage, algorithm, library, boundary placement...) becomes its own 3-to-5-option question, asked in dependency order. Each answer is written to the draft plan immediately, so a crashed run never loses a decision.
3. **Deep research** -- one researcher per chosen option validates it against official docs. Contradictions come back to you as a re-ask, never a silent override.
4. **Synthesis and critique** -- one turn drafts the task-by-task plan and then sweeps it against a checklist of six lenses (simplicity, performance, maintainability, minimal-diff, security, deep-modules), assumptions are probed with real shell checks, then a triage-gated critic fleet tries to refute the plan before you ever see it. A small plan arms no critics and pays for none.
5. **Approval and archive** -- you walk the plan through a structured approve/refine/change question (the only approval gate). On approval the plan is archived as a folder in your repo and you are handed off to implementation.

```mermaid
flowchart LR
    R[1 Research] --> S{scope OK?} --> D[2 Decisions] --> DR[3 Deep research] --> SY[4 Synthesis<br/>+ critique] --> A{approve?} --> AR[5 Archive<br/>plan folder]
    A -->|refine / change| D
    AR --> EX["/deep-plan:deep-plan-execute"]
```

`/deep-plan:deep-plan-execute` then turns the plan's tasks into real harness tasks with dependencies (`TaskCreate` + `addBlockedBy`) and dispatches them one at a time in dependency order. Each task goes to a single writable `dp-implement-task` agent in a fresh context, which owns the whole increment -- failing test first, implement, verify, its own nested design and test review of the task's diff, a post-green stability re-run to catch flakes, record an implementation note -- and returns a six-line summary. The diff never reaches the dispatcher, which instead audits what changed against the task's `Target files` (using git, not the agent's own report) and blocks completion on any edit outside them. Approval records a durable memo of the approved plan, which execute consults first (even after `/clear`) before falling back to the newest plan in the project's plans dir. It refuses to start while the plan has open questions.

## Quick start

```
/plugin marketplace add tsadoq/claude-better-plan
/plugin install deep-plan@claude-better-plan
```

Then, in any project:

```
/deep-plan add a rate limiter to the API
/deep-plan slug:rate-limiter add a rate limiter to the API
```

- `slug: my-name` -- an explicit name for the plan folder; otherwise derived from the topic.

After approval (and the recommended `/compact`), implement it:

```
/deep-plan:deep-plan-execute                      # the plan you last approved, else the newest one
/deep-plan:deep-plan-execute docs/plans/my-plan   # or name a plan folder / plan.md
```

Requires Claude Code >= v2.1.142 for the Task dependency API. The plugin's skills are invoked one per message, which works at that floor. Stacking several at the start of one message (`/skill-a /skill-b <topic>`) needs Claude Code >= v2.1.199, which expands the first skill plus up to five more; older versions load only the first.

## The plan folder

Each plan lives in its own folder, `plans_dir/<slug>/` (default `docs/plans/<slug>/`):

| Member | Content |
|--------|---------|
| `plan.md` | The canonical plan: context, decisions table, a generated at-a-glance `## Task overview` table, and the tasks with embedded TDD criteria. Carries a `**Status**` line (`draft` -> `approved` -> `executed`). |
| `design.md` | The why, told as a narrative design document: a Background section, then one plain-language-question section per decision (the plan's decisions table links into them), plus terse per-task implementation notes appended during execution. |
| `architecture.md` | Conditional: the Today / After world model, written only for architecturally significant plans (skipped when the change is reversible within a sprint, contained in one component, or routine). |
| `research.md` | The question-first research dossiers with an opening coverage table (one row per decision), split out on archive so `plan.md` stays lean. |
| `probes.md` | The verification probes -- why each ran, the command, what was observed, and what a failure would have meant -- split out the same way. |

Archiving also regenerates `plans_dir/README.md`, a browsable index of every plan with title, status, and date. The index and the task-overview table are fully generated between HTML-comment markers: never hand-edit them, re-run `finalize_plan.py --repair` / `--index` instead (that is also how you resolve a merge conflict in them). Plans created by older plugin versions as flat files with legacy dotted siblings are still discovered read-only; they are never rewritten.

## Configuration

The first run in a project asks where plans should live (recommended: `<repo>/docs/plans/`; never `~/.claude/plans/`) and remembers the answer in `$XDG_STATE_HOME/deep-plan/projects.json` (default `~/.local/state/deep-plan/`). Edit that file to change it.

To make plan writes prompt-free in default permission mode, allowlist the plan paths once per project in `.claude/settings.json` (plugins cannot ship permissions; the `test ! -e` rule covers the guard of the fail-closed rename, which is permission-checked per segment):

```json
{"permissions": {"allow": ["Edit(/docs/plans/**)", "Write(/docs/plans/**)", "Bash(mv docs/plans/*)", "Bash(test ! -e docs/plans/*)"]}}
```

Execute time needs a wider allowlist, because the implementer agent writes real source files. Subagents **inherit** the parent session's permission mode and plugin-bundled agents cannot set their own, so in default mode every `Write`, `Edit`, and `Bash` inside every implementer prompts separately. Allowlist what your plan's tasks actually touch:

```json
{"permissions": {"allow": ["Edit(/src/**)", "Write(/src/**)", "Bash(uv run pytest*)"]}}
```

## Guardrails

- **Read-only planning.** A prompt-level contract lets the orchestrator write only the plan folder and a per-session `/tmp` sandbox (for verification probes that need scratch files; cleaned up on session end). Planning subagents are held read-only by `disallowedTools`, which also leaves them free to use any ambient MCP documentation tools during research.
- **One writable agent, bounded by audit.** `dp-implement-task` is the single exception: it must write to implement a task. It is bounded not by a tool block but by the dispatcher's scope audit -- git's report of what changed, compared against the task's `Target files`, with completion blocked on anything outside them -- plus a `Workflow` denial in its frontmatter.
- **Approval is structural.** The plan is approved through one structured walk-the-plan question, never a plain-text "looks good?". Mechanical finalization (auto-repair, rename, overview regeneration) runs before the question, so it cannot be skipped.
- **No native plan mode.** Its read-only guarantee is prompt-level anyway, and its injected workflow competes with this one; if plan mode is active, Phase 0 asks you to toggle it off. The full rationale is in `PLAN.md`.
- **Crash-safe and re-entrant.** The plan lives in your repo from the first resolved decision; stale drafts and slug collisions are surfaced as resume/overwrite/rename questions, never silently clobbered.

## Design review

A parallel critic fleet (a cheap triage pass that names the clusters worth checking, then one small-model `dp-critic` per armed red-flag cluster, then an adversarial verify pass on each finding) reviews design quality at plan time, critique time, and after each executed task's tests go green; `/design-review [path | git ref | plan-file]` runs the same fleet standalone. A sibling test fleet -- the same `dp-critic` agent handed `test-principles.md` as its cluster source -- runs through the same parametrized recipe against the plan's `**Tests (TDD)**` blocks at critique time and against each task's diff at execute time; `/tdd-review [plan-file]` runs it standalone against a deep-plan plan's Tests (TDD) blocks. At execute time both fleets run *inside* the implementer agent, so the diff stays one level down. The plan's structural soundness -- unscheduled work, wrong `Depends on` edges, code tasks with no tests, contradicted decisions, unverified claims -- is checked by that same leaf carrying a fourth cluster source, `plan-integrity-principles.md`, rather than by a separate agent. The design guidelines live in `skills/design-review/references/design-principles.md`, independently paraphrased from a named source with no affiliation (see that file's `## Attribution and scope`); the test guidelines live in `skills/tdd-review/references/test-principles.md`. The fleet prefers the harness Workflow tool and falls back to a plain agent fan-out where Workflow is unavailable.

## Development

This repo is a single-plugin marketplace: the repo root is the plugin root. Orchestration lives in `skills/*/SKILL.md` with prompt fragments and templates under `references/`; the stdlib-only helper scripts live in `skills/deep-plan/scripts/`; contract tests are co-located per skill under `skills/<skill>/tests/` (discovery is owned by `pyproject.toml`); subagent definitions in `agents/`. Each guidelines file is pinned by its own contract test -- `test_design_review_contract.py`, `test_test_principles_contract.py`, `test_readability_contract.py`, `test_plan_integrity_contract.py` -- and `test_agents_contract.py` pins that exactly one agent may write and that no shipped document names an agent the plugin does not ship.

```
/plugin marketplace add /absolute/path/to/claude-better-plan   # local checkout
uvx ruff check skills                                          # the CI gate, locally
uvx mypy --strict skills/deep-plan/scripts skills/deep-plan/hooks
uvx pytest -q
```

CI pins `pytest>=9,<10` (the major the suite is verified under) and installs `tiktoken` for the token-budget contract test. `SKILL.md` and `references/` edits hot-reload within a session; changes under `agents/` need `/reload-plugins` or a restart. Contract tests pin structure and behaviour, never wording: what each file must still *do* is declared in `GUARANTEES` in `tests/guarantees.py`, so rephrasing a sentence does not break CI but deleting the behaviour behind it does. Releases flow through the Conventional Commits auto-bump CI (a `feat:`/`fix:` commit on main bumps `plugin.json`); layout-moving changes (a renamed skill, a moved reference) must land as `feat:`- or `fix:`-typed commits, because that version bump is what re-keys the installed plugin cache onto the new layout. Never edit the version by hand.

## Authoring budgets

"The repo is big" and "the plugin is expensive" are different claims. Most of this tree never enters a model's context. Frontmatter descriptions are always resident, a `SKILL.md` loads when invoked and re-attached, and `references/` content costs nothing until read.

The limits live in `BUDGETS` in `tests/guarantees.py`; no assertion hard-codes its own size. A budget never justifies dropping a behavior named by `GUARANTEES`.

## See also

- `PLAN.md`: current design rationale and phase-by-phase semantics.
