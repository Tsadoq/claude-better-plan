# Design principles for the critic fleet

## Attribution and scope

The concepts in this file are derived from "A Philosophy of Software Design", 2nd edition (2021), by John Ousterhout. The wording is independently paraphrased, operationalized as checkable questions, and reorganized by pipeline stage rather than book order. This project is not affiliated with or endorsed by the author or the publisher. The book title appears only in this section; file names, skill names, and agent prompts refer to these ideas as "design principles" or by cluster name.

Scope: this file is the single source of truth for design guidance in the plugin. Orchestrators quote one section (or one H3 cluster) into an agent prompt; nothing here is duplicated elsewhere.

## Plan-time principles

These act while the design is still fluid: option generation, decision surfacing, and plan synthesis. Weigh candidate designs against them; they trade against each other, so name the tension rather than silently picking.

- **Deep modules.** Prefer modules whose interface is much smaller than the functionality behind it. A module's value is functionality minus interface; a wide, thin wrapper subtracts value.
- **Simple interface over simple implementation.** When complexity must live somewhere, put it inside the module. It is better for one implementer to suffer than for every caller to.
- **Somewhat general-purpose modules.** Design the interface for the class of problem, implement only today's need. An interface shaped exactly like its first caller will warp every later caller.
- **Layer-distinct abstractions.** Each layer should change the vocabulary. If a layer's interface restates the layer below it, the layer is not abstracting; consider removing it.
- **Pull complexity downward.** Configuration knobs, edge-case handling, and "the caller must remember to" rules are complexity exported upward. Absorb them below the interface where one owner handles them once.
- **Define errors out of existence.** Prefer semantics where the error case cannot occur (idempotent deletes, clamping ranges, empty-collection returns) over raising and forcing every caller to handle it. Exceptions are part of the interface; fewer is deeper.
- **Design it twice.** For any decision worth surfacing, sketch at least two genuinely different designs before choosing. The second sketch is cheap and routinely beats the first.
- **Increments are abstractions, not features.** When slicing work into tasks, slice along module boundaries so each increment delivers a whole abstraction, not a horizontal layer of many half-abstractions.

## Review-time red flags

Each cluster below is quoted verbatim into one dp-design-critic finder. Every question is answerable yes/no against a concrete diff, plan, or file; "yes" is a finding. Severity hints are defaults — a critic may upgrade or downgrade with evidence.

### Module depth and interfaces

- Is any new module's interface as complicated as the functionality it hides (shallow module)? Severity hint: material for new public modules, minor for internal helpers.
- Does any method do little besides call another method with a similar signature (pass-through method)? Severity hint: material when it adds a layer, minor when transitional.
- Does the interface expose internals the caller does not need for common use (overexposure)? Severity hint: material.
- Does a general-purpose mechanism contain knowledge of a specific caller or use case (special-general mixture)? Severity hint: material.
- Can one of the methods only be understood by reading another (conjoined methods)? Severity hint: minor, material if they sit in different modules.

### Information hiding and decomposition

- Does the same design knowledge (a format, a protocol, an ordering rule) appear in more than one module, so a change in one forces a change in the other (information leakage)? Severity hint: material.
- Is code split by execution order (parse step, transform step, write step) rather than by knowledge, so one concept smears across the steps (temporal decomposition)? Severity hint: material.
- Does the same nontrivial code pattern repeat where a single abstraction should exist (repetition)? Severity hint: minor for two occurrences, material for three or more.

### Naming

- Is any name so generic (data, info, manager, util, process) that it could label half the identifiers in the codebase (vague name)? Severity hint: minor, material for public API names.
- Was a name visibly hard to pick — hedged, compound-of-compounds, or inconsistent with its siblings (hard to pick name)? A hard-to-name entity usually has an unclear design. Severity hint: minor, but flag the underlying entity.
- Would describing what the variable or function holds take a full sentence that its name does not even summarize (hard to describe)? Severity hint: minor.

### Comments and obviousness

- Does any comment restate what the adjacent code already says at the same level of detail (comment repeats code)? Severity hint: minor.
- Does interface documentation describe implementation details a caller should not depend on (implementation contaminates interface)? Severity hint: material.
- Would a first-time reader need information that is neither in the code nor in a comment — units, invariants, ownership, why not the obvious alternative (nonobvious code)? Severity hint: material when it guards a correctness rule, minor otherwise.

## Execute-time craft rules

These apply while writing code, before any review runs. The execute loop quotes them alongside the task description.

- **Comments first, as a design tool.** Write the interface comment before the body. If the comment is hard to write, the abstraction is wrong; fix the design, not the comment.
- **Precise names.** Pick names that create an accurate image of the entity, consistent with sibling names. If a precise name will not come, treat it as a design smell, not a thesaurus problem.
- **Consistency beats local preference.** Match the conventions already in the file and module — naming style, error style, comment density — even where a different style would be better in isolation.
- **Keep the common case simple.** The most frequent call pattern should need the least code and no configuration. Rare cases may be verbose; common ones may not.
- **Defaults for common cases.** Parameters that almost always take one value get that value as a default. Forcing every caller to state the obvious is complexity pulled upward.

## How to update these guidelines

The five H2 headings above and the H3 cluster structure under "Review-time red flags" are pinned by `skills/deep-plan/tests/test_design_review_contract.py` (`test_design_principles_structure`); renaming a section breaks callers that quote it, so change the test and every caller in the same commit. The files that quote sections of this file are:

- `skills/design-review/SKILL.md` (standalone review: all four red-flag clusters)
- `skills/design-review/references/fleet-orchestration.md` (fleet recipe: one finder per cluster)
- `skills/deep-plan/SKILL.md` (Phase 2 framing and the deep-modules perspective: plan-time principles; Phase 4.6: red-flag clusters)
- `skills/deep-plan/references/perspectives.md` (deep-modules perspective: plan-time principles)
- `skills/deep-plan-execute/SKILL.md` (post-task review: red-flag clusters; craft rules quoted into implementation turns)
- `agents/dp-design-critic.md` (receives one cluster per instance, quoted by the caller)
