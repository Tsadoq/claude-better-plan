# Plan integrity principles

## Scope

The checks that decide whether a synthesized plan is *sound as a plan* — whether it schedules all the work, orders it correctly, tests what it changes, obeys the decisions the user made, and rests on verified claims. This is structural review, not narrative review: `readability-principles.md` asks whether the artifacts *read* well, and this file asks whether they *hold up*.

Quoted by Phase 4.6 as a cluster source for `deep-plan:dp-readability-critic`, which carries this file's cluster alongside its own. The critic leaf supplies no rubric of its own; every question it applies comes from a file like this one.

Two boundaries keep this cluster from duplicating its neighbours:

- **Test *structure*, not test *quality*.** Whether a code task has a `**Tests (TDD)**` block and whether its named test can fail first is checked here. Assertion strength, doubles, fixtures and test level belong to the `dp-test-critic` fleet running alongside; do not restate its findings.
- **Findings, not rewrites.** The orchestrator owns `plan.md`. A finding names the defect and cites its location; it never proposes replacement task text.

Cite everything. Evidence is a task number, a `## Decisions made` row, or a dossier section — a finding the orchestrator cannot locate is not actionable.

## Review-time red flags

### Plan integrity

- **Missing tasks.** Does the plan imply work it never schedules — a module referenced but never created, a migration with no rollback, config or wiring a code task assumes exists, a behaviour with tests but no implementation?
- **Wrong or missing dependencies.** Does any task consume an artifact a later task builds, or carry a `Depends on` pointing at the wrong task number, or omit an edge that would let tasks run out of order, or close a dependency cycle?
- **Code tasks lacking tests.** Does any task whose `Target files` include code have no `**Tests (TDD)**` block, or a block missing one of the canonical field bullets, or name a test that cannot fail first because it asserts something already true?
- **Decisions contradicted.** Does any task do the opposite of what a `## Decisions made` row settled, or ignore a Phase 3 dossier finding or its `## Contradiction` section, without that reversal being surfaced back to the user?
- **Untested assumptions.** Does any load-bearing claim carry neither a verification probe nor a citation — a library version that may not exist, an API shape that may have changed, a performance assumption, a repo path that may be wrong?
- **Unfalsifiable acceptance.** Does any task's `Verification` command pass whether or not the change was made, leaving the task with no acceptance check at all?

Tag each finding:

- **material** — the plan produces wrong, broken or unsafe work as written, or it contradicts a user decision. Worth blocking approval. A material finding that reverses a decision names the decision row, so the orchestrator can route it back to Phase 2 rather than fixing it silently.
- **minor** — a real but non-blocking gap. Belongs in `## Open questions`, not a re-loop.

## How to update these guidelines

`skills/deep-plan/tests/test_plan_integrity_contract.py` pins this file: the three H2 headings in order, the single `### Plan integrity` cluster, its five-question floor, and coverage of each check class inherited from the retired standalone plan critic. Adding a question is free; removing one means proving the check is covered elsewhere first.

Consumers:

- `skills/deep-plan/SKILL.md` and `skills/deep-plan/references/phase-prompts.md` (Phase 4.6: quoted as a cluster source)
- `skills/design-review/references/fleet-orchestration.md` (cluster-source pairing list)
