# design.md template

The `design.md` folder member is the plan's narrative design document: it tells the story of why the plan looks the way it does, one plain-language question per decision. The plan's `## Decisions made` table is only an index into it — each row links here for the full story. It has a two-phase lifecycle:

1. **Plan phase**: at Phase 4.4 synthesis, /deep-plan seeds `plans_dir/<slug>/design.md` from this template — a `## Background` section, then one question-shaped section per row of the plan's decision table.
2. **Execute phase**: /deep-plan:deep-plan-execute appends one terse entry per completed task under the trailing notes section, after that task's verification passes and before the task is marked completed.

Writing rules for every section live in `## Plan-time authoring rules` of `readability-principles.md`; do not restate them here or in the document. Two apply structurally:

- Each decision section's heading is a plain-language question, and its body opens with the decision in its **first sentence** — the story of options weighed comes after, with evidence cited inline mid-sentence, and the section closes with the consequence for the implementer.
- Sections are self-contained: no "as discussed above", no reliance on reading order.

plan.md decision-index rows link to these sections by the anchor slug of the question heading, following the slug rule of readability-principles.md: lowercase the heading, replace spaces with hyphens, strip punctuation other than hyphens and underscores (so "When does a plan deserve an architecture.md?" becomes `#when-does-a-plan-deserve-an-architecturemd`).

## Skeleton

````markdown
# Design: {plan title}

## Background

{The problem and the forces in tension, as prose. What hurts today, what constrains any solution, and what the reader needs to know before any decision makes sense. Define project-specific terms here at first use.}

## {plain-language question, one section per row of the plan's decision table}

{The body opens with the decision in its first sentence. Then the story: which options were weighed, what evidence — cited inline, mid-sentence, pointing at specific findings — tipped the choice, and why the losers lost. Close with the consequence for the implementer: what this decision makes them do or forbids them from doing.}

## Implementation notes

{Starts empty at plan time. During execution, one terse entry is appended per completed task:}

### Task {N}: {name}

{2 to 4 lines: deviations from the plan, gotchas hit, non-obvious code shapes. Nothing else.}
````
