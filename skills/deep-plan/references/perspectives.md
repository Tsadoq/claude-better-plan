# dp-plan-perspective catalogue

The perspective fan-out in Phase 4 picks 1 to 3 perspectives from the catalogue below based on the user's evident priorities. Each perspective drafts a `## Tasks` block that the orchestrator merges.

## Perspectives

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

## How to choose

The orchestrator reads the user's prompt and the resolved decisions, then picks 1 to 3 perspectives. Examples:

- "Add a rate limiter" -> performance + security + simplicity (3-way).
- "Rename a private helper" -> minimal-diff (1-way; nothing else applies).
- "Refactor auth middleware" -> security + maintainability (2-way).
- "Add a /healthz endpoint" -> simplicity + maintainability (2-way).
- "Migrate DB" -> minimal-diff + maintainability (2-way).

Cap is 3. Beyond 3, perspectives start contradicting each other in ways the orchestrator cannot reconcile without surfacing a sub-decision back to the user, which is Phase 2's job.
