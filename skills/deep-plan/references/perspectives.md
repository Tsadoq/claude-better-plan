# Plan synthesis lenses

Six frames for reading a draft `## Tasks` block. They are not separate drafts to merge — Phase 4.3 sweeps them one at a time inside the single synthesis turn, so a lens costs a pass of attention rather than an agent.

## Synthesis checklist

Draft the `## Tasks` block once, then sweep it lens by lens, amending in place. One pass per lens, in this order:

1. `simplicity` — is any task building more than the evidence demands?
2. `performance` — does any task sit on a hot path with no latency budget stated?
3. `maintainability` — will a reader six months out understand why each task exists?
4. `minimal-diff` — does any task touch a file no other task needed?
5. `security` — does any task cross a trust boundary without validating it?
6. `deep-modules` — always swept last, because it reshapes task boundaries rather than task contents.

Each lens's full frame is in `## The lenses` below; read the frame before sweeping with it. Emphasis is not uniform: `## Which lenses to emphasise` says which frames deserve real scrutiny for a given change, and which get a quick look. Every lens still gets its pass.

`**Tests (TDD)**` blocks follow `## Plan-time authoring rules` of `${CLAUDE_PLUGIN_ROOT}/skills/tdd-review/references/test-principles.md`, whatever lens is being applied.

## The lenses

### simplicity

Frame: prefer the smallest possible change. Reuse existing utilities. Avoid new abstractions, new dependencies, new layers of indirection. If a function in the codebase already does 80% of the work, modify it in place rather than introducing a parallel implementation. Fewer files changed beats elegance.

Use when: the user says "simple", "minimal", "just", "small", or the change is genuinely scoped (one feature, one bug, one rename).

Anti-pattern this guards against: over-engineering Phase 1 evidence into a framework when a single function would do.

### performance

Frame: assume the change runs on the hot path until proven otherwise. Pick algorithms with predictable big-O behaviour. Prefer in-process caches over network calls. Batch where possible. Avoid synchronous I/O inside async handlers. Annotate latency budgets in task descriptions.

Use when: the user mentions throughput, latency, scale, RPS, p99, "production load", or the feature is request-path code.

Anti-pattern this guards against: shipping an n+1 query or an unnecessary round trip because nobody owned performance at design time.

### maintainability

Frame: optimise for the reader six months from now. Prefer named functions over lambdas, explicit error types over bare exceptions, dependency injection over module-level singletons. Tests cover behaviour (not implementation). Public APIs get docstrings. Configuration lives in `pyproject.toml` or `.env`.

Use when: the change is in a long-lived part of the codebase (auth, data layer, public API), or the user mentions "long-term", "stable", "production", "team".

Anti-pattern this guards against: clever code that passes review but rots within two quarters.

### minimal-diff

Frame: change the least possible to make the test pass. No drive-by refactors. No "while I'm here" cleanups. Touch only the files strictly required. Keep formatting consistent with neighbouring code even if newer style would be preferred.

Use when: the change is a hotfix, the codebase has a freeze, the user explicitly says "don't touch X", or the work is one task in a larger sequence and other tasks own the surrounding cleanup.

Anti-pattern this guards against: bundling a tested fix with an untested refactor, making the diff hard to review and the fix hard to revert.

### security

Frame: assume the input is hostile. Validate at boundaries (HTTP, DB, IPC, env). Default-deny on auth and authz. Constant-time comparison for secrets. No secrets in logs. SQL via parameterised queries; never string-concatenated. Test the rejection paths, not just the happy path.

Use when: the change touches auth, secrets, network ingress, file uploads, deserialisation, regex against user input, or anything that meets one of the OWASP top 10 categories.

Anti-pattern this guards against: a feature that ships secure-by-accident and breaks the moment someone touches it.

### deep-modules

Frame: apply the `## Plan-time principles` section of `${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/design-principles.md` (read it before drafting). Prefer deep modules: small interfaces hiding real functionality. Pull complexity downward rather than exporting knobs and caller obligations. Define errors out of existence where semantics allow. Slice tasks along module boundaries so each increment delivers a whole abstraction.

Use when: always, and swept last. This lens is never deprioritised, because it changes where task boundaries fall rather than what a task contains.

Anti-pattern this guards against: a plan whose tasks each work in isolation but compose into shallow wrappers, leaked formats, and pass-through layers nobody designed on purpose.

## Which lenses to emphasise

Every lens gets a pass, but attention is finite. Read the user's prompt and the resolved decisions, then give 1 to 3 lenses real scrutiny and the rest a quick look. Examples (emphasised lenses only; `deep-modules` is always swept in addition):

- "Add a rate limiter" -> performance + security + simplicity.
- "Rename a private helper" -> minimal-diff; nothing else has much to say.
- "Refactor auth middleware" -> security + maintainability.
- "Add a /healthz endpoint" -> simplicity + maintainability.
- "Migrate DB" -> minimal-diff + maintainability.

Emphasise at most 3. Past that the lenses start pulling in opposite directions, and reconciling them means surfacing a sub-decision back to the user, which is Phase 2's job rather than Phase 4's. `deep-modules` never counts against the 3: it constrains module shape instead of competing on priorities.

## How to update these guidelines

Two contract tests pin this file; both must stay green after any edit here:

- `skills/tdd-review/tests/test_test_principles_contract.py` — pins `## Synthesis checklist`, all six lens names, this registry section, and the pointer to the tdd-review authoring rubric.
- `skills/design-review/tests/test_design_review_contract.py` — pins that the `deep-modules` lens points at `design-principles.md`.

Renaming a lens means editing both tests and Phase 4.3 of `skills/deep-plan/SKILL.md`, which names the lens set.
