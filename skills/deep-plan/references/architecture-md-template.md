# architecture.md template

The `architecture.md` folder member is conditional: /deep-plan writes it at Phase 4.4 only when the plan clears the significance test below. It gives the reader the world model the plan assumes — what the affected system looks like today and how the plan reshapes it — so the plan's tasks land in a picture, not a vacuum. It is orchestrator-written and never regenerated or split by finalize_plan.py.

## Significance test (write or skip)

Write architecture.md only when the plan does at least one of:

- introduces a new module, service, or package;
- changes how data flows between existing modules;
- moves responsibility across a boundary (process, service, ownership).

Skip it when the change is reversible within a sprint, contained in one component, or a routine implementation choice. A skipped architecture.md is the common case; writing one for a small plan is ceremony, not rigor.

## Skeleton

````markdown
# Architecture: {plan title}

## Today

{The affected system's modules, each with a one-line responsibility; the data flow between them; key terms defined at first use. One container/component-level diagram:}

```mermaid
flowchart LR
    {module A} --> {module B}
```

## After this plan

{What moves, which boundaries change, and which stay fixed. A second diagram only when the topology itself changes.}
````

Seam rule: the diagram carries topology, the prose carries one-line responsibilities and pointers to rationale — the rationale itself stays in design.md, never duplicated here.
