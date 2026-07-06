# Plan file template

The orchestrator fills in this skeleton during Phase 4, editing the project-local plan file in place. Every plan lives in its own folder: the draft is born as `plans_dir/<topic>-draft/plan.md` at the start of Phase 2, and the folder is renamed to `plans_dir/<slug>/` at Phase 4.2. The folder's fixed member names are `plan.md` (the canonical plan), `research.md`, `probes.md`, and `design.md`. Use the section order below. `finalize_plan.py --repair` auto-normalizes the plan before approval: it fixes em-dashes and task headers and inserts any omitted section or task subsection as `n/a`, so this shape is a target, not a tripwire. It repairs rather than rejects. Keep section headings even when a body is just `n/a`. Predictable shape lets the implementation turn parse the plan with stdlib regex. The `## Verification probes` and `## Research dossiers` appendices are split into the folder members `probes.md` and `research.md` by `finalize_plan.py --archive` on approval, so the archived `plan.md` stays lean.

## Skeleton

````markdown
# {Descriptive title, prose-cased version of the slug}

## Context

{Single paragraph, 3 to 6 sentences. Restate the problem, not the solution. The implementation turn reads this once for global context. No headings inside, no lists, no code blocks.}

## Decisions made

| # | Decision | Chosen | Rejected | Rationale |
|---|----------|--------|----------|-----------|
| 1 | {Decision name} | {Chosen option} | {Rejected option 1, rejected option 2, ...} | {1-line rationale citing Phase 1 evidence or Phase 3 verdict} |

## Architecture

```mermaid
%% Include only when there is non-trivial structure. For single-file or
%% linear changes, leave the heading and write `n/a` as the body.
flowchart LR
    A --> B
```

<!-- deep-plan-task-overview:begin generated: do not edit -->
## Task overview

{Fully generated content owned by `finalize_plan.py --repair`: a `# | Task | Files | Deps | Summary` table rebuilt from the Tasks section on every repair run. Hand edits inside the markers are discarded on the next run.}
<!-- deep-plan-task-overview:end -->

## Tasks

### Task 1: {Short name}

**Target files**:
- {path/to/file.py} (new|modify|delete)
- ...

**Change**:
{Opens with exactly one plain-English summary sentence, then 1 to 3 sentences naming the function/class/route added or changed and the configuration knobs introduced. Reference exact symbol names. No prose about why; the why lives in `## Decisions made`.}

**Tests (TDD)**:   <!-- include ONLY for tasks that create or modify code; omit entirely for markdown, docs, or config tasks -->
- File: {path/to/test_x.py} (new|modify)
- Test name: `{test_function_name}`
- Asserts: {1 to 2 sentences naming the exact assertion: input shape, expected output, expected status code or exception.}
- This test MUST fail before implementation begins. The implementation turn writes the test first, runs it (must fail), then implements, then runs again (must pass).

**Verification**:
```
{exactly one shell command, e.g.}
uv run pytest tests/path/to/test.py::test_name -x
```

**Depends on**: {none | comma-separated integers}

### Task 2: ...

(Same subschema. Numbering is dense: 1, 2, 3, no gaps, no decimals.)

## References

- {project file path}
- {project file path}
- {URL with relevance to the chosen approach}
- JIRA: {ticket-id}        # if applicable

## Open questions

- {bullet, or "none"}

## Verification probes (appendix)

[probe 1]: {command literal}
{stdout, max 20 lines, truncated with `... (truncated, M more lines)` marker}

[probe 2]: ...

## Research dossiers (appendix)

{The Phase 3 dp-research-deep dossiers, verbatim: one `### {decision}` block each
with its Verdict / Gotchas / Versioning / Canonical snippet. Omit when Phase 3 was
skipped. finalize_plan.py --archive moves this section into the folder member `research.md`.}
````

## Formatting rules (strict)

- Every task has the always-present subsections Target files, Change, Verification, Depends on, even if a value is `none` or `n/a`. Include Tests (TDD) only for tasks that create or modify code; omit it for markdown, docs, or config tasks. TDD is mandatory wherever code is written.
- Every task's `**Change**` block opens with exactly one plain-English summary sentence, terminated per the PEP 257/Javadoc rule: the sentence ends at the first period followed by whitespace or end of text, so dots in versions (`v0.5.0`) and file names (`finalize_plan.py`) do not truncate it. `finalize_plan.py --repair` copies this sentence into the generated `## Task overview` table.
- The `## Task overview` region between its HTML-comment markers is fully generated content owned by `finalize_plan.py --repair`; hand edits inside the markers are discarded on the next run.
- Task numbering is dense: 1, 2, 3, no gaps, no decimal subtasks. If a task is too large, split it into two.
- `**Target files**` lists each file on its own line with `(new)`, `(modify)`, or `(delete)` suffix.
- `**Tests (TDD)**`, when present (code tasks), names a file path AND a test function name AND the must-fail-first verification step.
- `**Verification**` is exactly one shell command in a code fence. Multi-step verification splits the task in two.
- `**Depends on**` is either `none` or comma-separated integers referring to other task numbers in this plan.
- Mermaid blocks use ` ```mermaid ` fences. No PlantUML. No ASCII art (per user rule).
- No em-dashes anywhere. Use ` -- `, commas, or rephrase (per user rule).
- No "Generated by Claude Code", no Co-Authored-By, no AI attribution (per user rule).
- All Python verification commands prefer `uv run` if a `pyproject.toml` is present in the project root; fall back to `python3` otherwise.

## Why this shape is AI-consumable

Implementation turn parses the plan with stdlib regex:

```
^### Task (\d+): (.+)$
followed by labelled blocks: \*\*Target files\*\*:, \*\*Change\*\*:, \*\*Tests \(TDD\)\*\*:,
                             \*\*Verification\*\*:, \*\*Depends on\*\*:
```

Each match maps to one `TaskCreate` payload:

- `subject` = `Task N: <name>`
- `description` = `**Change**` paragraph
- acceptance criteria = `**Tests (TDD)**` + `**Verification**` blocks, concatenated
- dependencies = parsed `**Depends on**` integers, mapped to `addBlockedBy`

A task without a `**Tests (TDD)**` block (a docs or config task) is valid; its acceptance criteria come from `**Verification**` alone.

`Decisions made` is read once and injected as a prologue to the first task. `Open questions` blocks `TaskCreate` if non-empty: the implementation turn either resolves them or asks the user before proceeding.

## Section order is load-bearing

`Decisions made` appears immediately after `Context` and before `Architecture` so a model reading the file from the top is reminded of the resolved choices before being asked to think about structure. Putting it at the end of the file works against this.
