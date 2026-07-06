# Test principles for planning, review, and execution

Scope: this file is the single source of truth for test guidance in the plugin. Orchestrators quote one section (or one H3 cluster) into an agent prompt; nothing here is duplicated elsewhere.

## Plan-time authoring rules

These act while a plan's `**Tests (TDD)**` blocks are being drafted. Every rule maps onto a named field of the block, so a critic can check compliance per task.

- **One behavior per test.** State the single behavior the test protects in one sentence. If that sentence needs an "and", the test — or the task — wants splitting.
- **Lowest observable level.** Choose the lowest level (unit, component, system) at which the behavior can be observed. Moving a test down is free at plan time and expensive after.
- **Fake only what you do not own.** Doubles belong at boundaries outside the plan's code: networks, clocks, third-party services. Anything the plan's own code owns runs real.
- **Setup stays local.** Arrange inside the test itself. Reach for a shared fixture only when it is named and its reuse is justified; anonymous shared state couples tests invisibly.
- **The three phases stay visible.** A reader should see arrange, act, and assert at a glance, in that order, without scrolling or cross-referencing.
- **No production seam exists only for a test.** Never add a hook, flag, parameter, or indirection to production code whose only caller is a test.
- **Failures explain themselves.** A failing assertion must say which behavior broke, not merely that two values differ. Write the message at plan time; it is the test's error interface.

## Review-time red flags

Each cluster below is quoted verbatim into one dp-test-critic finder. Every question is answerable yes/no against a plan's `**Tests (TDD)**` blocks or a task diff; "yes" is a finding. Severity hints are defaults — a critic may upgrade or downgrade with evidence.

### Assertions and failure output

- Does any test assert how the code did something (calls made, order of internal steps) rather than what it produced?
  Severity hint: material.
- Would any assertion still pass if the implementation were replaced by a stub returning the test's own input (tautological test)?
  Severity hint: material.
- Does a bare `assert a == b` fail without saying which behavior broke (mute failure)?
  Severity hint: minor, material when the compared values are opaque blobs.
- Does any test assert a property the type checker already guarantees (redundant type assert)?
  Severity hint: minor.
- Does one test pin so much output at once (broad snapshot, full-object equality) that any unrelated change breaks it?
  Severity hint: minor, material when it guards a public contract.

### Doubles and seams

- Is anything the plan's own code owns replaced by a mock, stub, or patch (self-mocking)?
  Severity hint: material.
- Was a hook, flag, parameter, or extra indirection added to production code only so a test can reach in (test-only seam)?
  Severity hint: material.
- Does a double's canned return diverge from what the real collaborator can produce (contract drift)?
  Severity hint: material.
- Does patching reach through more than one layer to replace something deep inside the unit under test (deep patch)?
  Severity hint: minor, material when it hides an owned dependency.

### Fixtures and setup

- Does a test depend on shared fixture state another test mutates, so outcomes change with execution order (order coupling)?
  Severity hint: material.
- Is the arrange step hidden in a distant fixture or helper, so the test cannot be read alone (remote setup)?
  Severity hint: minor, material when the hidden values drive the assertion.
- Do unexplained literals steer the outcome without a name saying why (magic setup values)?
  Severity hint: minor.
- Are the arrange, act, and assert phases interleaved or repeated so the test's story cannot be followed at a glance?
  Severity hint: minor.

### Level and duplication

- Is any behavior tested above the lowest level that can observe it (wrong level), for example a system test pinning a unit's internal rule?
  Severity hint: material.
- Does a higher-level test re-assert details a lower level already covers, so one change fails many tests (duplicate coverage)?
  Severity hint: minor, material for three or more overlapping tests.
- Does one test protect several behaviors at once, so its name cannot state what failure means (bundled behaviors)?
  Severity hint: minor, material when the behaviors belong to different modules.
- Is a behavior the plan introduces left with no test at any level (coverage hole)?
  Severity hint: material.

## Execute-time run rules

These apply while implementing a task, around the red-green cycle. The execute loop quotes them into each implementation turn.

- **Prove red first.** Run the new test before writing any implementation; it must fail, and fail for the expected reason. A test that starts green is testing something else.
- **Re-run after green.** After the first pass — and again after any review fixes — run the task's tests once more. A flake caught before the task completes costs one command; caught later it costs a debugging session.
- **Never weaken a test to pass it.** When a test fails, either the code is wrong or the test is wrong. Loosening an assertion until it goes green is neither fix; it deletes the behavior's protection silently.
- **Drop type-guaranteed assertions.** Delete asserts that restate what the type system already proves; they add noise to failures and lend false weight to the suite.

## How to update these guidelines

The four H2 headings above and the four-cluster H3 structure under "Review-time red flags" are pinned by `skills/deep-plan/tests/test_test_principles_contract.py` (`test_test_principles_structure`); renaming a section breaks callers that quote it, so change the test and every caller in the same commit. The files that quote sections of this file are:

- `skills/deep-plan/references/plan-file-template.md` (Tests block schema: plan-time authoring rules)
- `agents/dp-plan-perspective.md` and `skills/deep-plan/references/perspectives.md` (perspective drafts: plan-time authoring rules)
- `agents/dp-test-critic.md` (receives one red-flag cluster per instance, quoted by the caller)
- `skills/design-review/references/fleet-orchestration.md` (fleet recipe: pairs dp-test-critic with this file's clusters)
- `skills/deep-plan/SKILL.md` and `skills/deep-plan/references/phase-prompts.md` (Phase 4.4 synthesis: plan-time authoring rules; Phase 4.6: red-flag clusters)
- `skills/deep-plan-execute/SKILL.md` (implementation turns: execute-time run rules; post-task review: red-flag clusters)
