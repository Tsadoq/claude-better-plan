# design.md template

The `design.md` folder member captures the why behind a plan: the expanded per-decision rationale that does not fit the plan's decision table, and the why-the-code-looks-this-way notes recorded during execution. It has a two-phase lifecycle:

1. **Plan phase**: at Phase 4.4 synthesis, /deep-plan seeds `plans_dir/<slug>/design.md` from this template, one `D{N}` subsection per row of the plan's decision table, carrying the expanded reasoning and evidence links.
2. **Execute phase**: /deep-plan:deep-plan-execute appends one terse entry per completed task under the trailing notes section, after that task's verification passes and before the task is marked completed.

Keep every entry terse and scoped: design.md is a design document, not a chronological journal. Entries state decisions, deviations, and non-obvious code shapes, never a narrative of the work.

## Skeleton

````markdown
# Design rationale: {plan title}

## Decisions

### D{N}: {decision name; one subsection per row of the plan's decision table}

**Chosen**: {the selected option, restated}

**Rejected**: {each rejected option with the concrete reason it lost}

**Why**: {the expanded reasoning that does not fit a table cell: constraints, trade-offs, evidence weighed. A short paragraph, not a page.}

**Evidence**: {links into the sibling `research.md` when Phase 3 ran; when Phase 3 was skipped, cite the Phase 1 evidence inline or write `n/a` -- research.md does not exist for every plan}

## Implementation notes

{Starts empty at plan time. During execution, one terse entry is appended per completed task:}

### Task {N}: {name}

{2 to 4 lines: deviations from the plan, gotchas hit, non-obvious code shapes. Nothing else.}
````
