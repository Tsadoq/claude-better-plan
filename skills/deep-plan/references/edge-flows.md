# Edge flows

The rare paths of `/deep-plan`. Every phase in `SKILL.md` runs in every session; nothing below does. Each flow fires only when `setup_session.py` reports its sentinel, or when a draft or slug turns out to already exist -- so read the one flow whose trigger you just saw, not the file.

| Trigger | Flow |
|---|---|
| sentinel `prompt_for_plans_dir` | [Choosing plans_dir](#choosing-plans_dir) |
| sentinel `plans_dir_under_protected_path` | [A plans_dir under a protected path](#a-plans_dir-under-a-protected-path) |
| sentinel `no_git` | [No git repository](#no-git-repository) |
| a `*-draft/` folder already exists (Phase 0 step 4) | [R3: a stale draft](#r3-a-stale-draft) |
| `resolve_slug.py` reports the slug taken (Phase 4.1) | [R3: a slug collision](#r3-a-slug-collision) |

The two R3 flows share one rule: **never assume an existing plan file is still valid.** Read it, then ask. Silently resuming a draft the user abandoned for a reason, or overwriting a plan they still want, both cost more than one question.

## Choosing plans_dir

Ask via `AskUserQuestion`, header "Plans dir":

1. `<repo>/docs/plans/` (Recommended)
2. `<repo>/plans/`
3. `<repo-parent>/<repo-name>-plans/`
4. `<repo>/.claude/plans/` -- warn in the option description that this is a protected path where every write prompts

The default MUST NOT be `~/.claude/plans/`: a plan belongs with the code it plans. Persist the answer, so the question is asked once per project rather than once per session:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deep-plan/scripts/setup_session.py \
  --update plans_dir=<ABS_PATH> --session-id ${CLAUDE_SESSION_ID}
```

## A plans_dir under a protected path

The sentinel carries the offending path. A remembered `plans_dir` under `.claude/` cannot be allowlisted, so every plan write prompts for the rest of the session.

Offer the move via `AskUserQuestion` (`<repo>/docs/plans/` recommended; keeping the current directory stays a valid choice). On a move, persist the new location with the `--update plans_dir=` command above. **Never migrate silently** -- the user may have put it there deliberately, and moving files they did not ask you to move is a write outside the read-only contract of R1.

## No git repository

The project root could not be resolved from git. Ask via `AskUserQuestion` whether to treat the current working directory as the project root, or to stop so the user can `cd` somewhere else. Do not guess: an out-by-one root puts `plans_dir` in the wrong project.

## R3: a stale draft

Reached from Phase 0 step 4, BEFORE Phase 2 may create a new draft. A draft folder means an earlier run was abandoned partway through its decisions.

1. Read the draft's `## Context` and `## Decisions made` (for a draft folder, from its `plan.md` member).
2. Ask via `AskUserQuestion`: resume from the draft, overwrite it, or start fresh under another topic name.
3. Default to **resume**, seeding Phase 2 with the decisions the draft already resolved -- that is what the draft is for. Overwrite deletes it.

No orphan draft may reach Phase 4: the Phase 4.2 rename has exactly one draft folder to move.

## R3: a slug collision

Reached from Phase 4.1 when `resolve_slug.py` reports the slug already exists, as the folder `plans_dir/<slug>/` or the legacy flat file `plans_dir/<slug>.md`. Also reached from Phase 4.2 when a rename guard trips, which means the collision appeared after 4.1 checked.

1. Read the existing plan's `## Context` and `## Decisions made`.
2. Ask via `AskUserQuestion`: refine the existing plan, overwrite it, add a `-v2` suffix, or supply a custom suffix.
3. Default to **refine** when the existing plan is similar to the current intent: seed the current plan from it, then edit in place. Default to the **`-v2` suffix** when it is unrelated, auto-incrementing to `-v3`, `-v4` if those are taken too.

Never resolve a collision with a bare `mv`. The Phase 4.2 rename is the single fail-closed point, and a guard that trips is this flow's trigger, not an error to work around.
