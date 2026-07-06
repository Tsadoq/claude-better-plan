## Research dossiers (appendix)

### Decision 1: Folder per plan, slug-named

**Verdict**: The chosen design (`<slug>/` folder, no number prefix, fixed member file names, draft renamed via `mv` at synthesis time) holds up. It matches OpenSpec's `openspec/changes/<name>/` pattern almost exactly (slug-named folder, fixed members `proposal.md`, `design.md`, `tasks.md`, `specs/`), and OpenSpec's own `archive` command validates the rename-at-a-lifecycle-transition pattern (https://raw.githubusercontent.com/Fission-AI/OpenSpec/main/docs/commands.md). Spec-kit is the outlier: it requires a numeric prefix (`001-slug`), but only because the number is shared between the git branch name and the specs folder so `create-new-feature.sh` can avoid collisions across concurrent feature branches (https://raw.githubusercontent.com/github/spec-kit/main/scripts/bash/create-new-feature.sh). deep-plan's plan folders are not paired 1:1 with git branches, so this rationale does not transfer.

**Gotchas**:
1. Spec-kit's numbering exists so the folder name doubles as a collision-free git branch name; deep-plan has no numeric coordination mechanism, so concurrent sessions could independently pick the same slug with no arbiter.
2. Spec-kit fails closed on collision (`[ -d "$FEATURE_DIR" ]` triggers an error and exits) rather than silently overwriting; the draft-to-slug `mv` should copy this behavior.
3. Neither tool documents mid-flight renaming of an active folder; OpenSpec's only documented folder move is a one-way terminal transition. Keep the rename to the single Phase 4.1 lifecycle point.
4. Neither project documents slug-collision handling as a first-class case; deep-plan keeps its own (R3 flow, fail closed).
5. Spec-kit's regex special-cases timestamp-shaped names to avoid misparsing; mixing naming schemes inside plans_dir can silently break ordering logic.

**Versioning**: sources fetched from each repo's `main` branch on 2026-07-06 (unpinned); design precedent, not a runtime dependency.

**Canonical snippet** (https://raw.githubusercontent.com/Fission-AI/OpenSpec/main/README.md):

```
openspec/changes/add-dark-mode/
+-- proposal.md   # why we're doing this, what's changing
+-- specs/        # requirements and scenarios (delta specs)
+-- design.md     # technical approach
+-- tasks.md      # implementation checklist
```

### Decision 2: Lean plan splits as folder members plus generated index

**Verdict**: Directionally sound but only half-precedented. Spec-kit's `/plan` command generates `research.md` as an artifact explicitly separate from `plan.md` (https://github.com/github/spec-kit/blob/main/templates/commands/plan.md), confirming the separate-evidence convention. However, no reference tool maintains an auto-regenerated index file: log4brains builds a static site into a separate output directory rather than overwriting an in-repo hand-touched file, and spec-kit and OpenSpec rely on the filesystem listing as the de facto index. The `plans_dir/README.md` regeneration is a novel mechanism that must design its own anti-clobber convention.

**Gotchas**:
1. No reference tool generates a cross-feature index; treat README regeneration as novel, not established.
2. log4brains never writes generated output into files users hand-edit; ADRs are "immutable: only its status can change".
3. OpenSpec's state model is binary (active vs archived); richer status vocabularies are deep-plan-specific inventions.
4. log4brains/MADR status words (proposed/accepted/deprecated/superseded) do not map onto archive-flow statuses; extend rather than adopt.
5. The closest protection convention is Stencil.js's generated-readme markers (custom content on one side of a literal marker line, everything else freely overwritten); an explicit marker boundary, not a bare banner, is the safe mechanism (https://stenciljs.com/docs/docs-readme).
6. Generated-index files are not git-merge-aware: concurrent branches archiving different plans conflict on README.md. Rule: regenerate deterministically, never hand-resolve.

**Versioning**: markdown/file-layout convention, no runtime constraint; spec-kit template cited at `main` as of 2026-07-06.

**Canonical snippet**:

```
specs/001-create-taskify/
+-- spec.md          # functional spec
+-- plan.md          # technical implementation plan (lean)
+-- research.md      # Phase 0 output, separate from plan
+-- data-model.md
+-- quickstart.md
```

### Decision 3: Generated Task overview table and summary-first Change blocks

**Verdict**: Embedding an auto-generated table inside an otherwise hand-authored markdown file, delimited by BEGIN/END HTML-comment markers, is established prior art: doctoc does exactly this for TOCs and terraform-docs for module docs, both confirmed from primary sources. The chosen design (repair script + in-file generated table + one-sentence Change opener) is well-supported and does not need a split tasks.md. Spec-kit and OpenSpec split human/machine artifacts into separate files but publish no rationale for the split, so there is no authoritative argument overriding the single-file choice.

**Gotchas**:
1. Hand edits inside the generated block are silently destroyed on the next run by design; doctoc's pragma says "DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE". The region between markers is fully disposable.
2. terraform-docs' inject mode requires the markers to already exist; content inside is fully replaced, content outside preserved.
3. Regeneration happens in place wherever the markers live: search for existing markers first, fall back to a fixed default anchor only when absent.
4. The first-sentence rule needs the PEP 257/Javadoc terminator ("first period followed by a blank, tab, or line terminator") because periods inside abbreviations, paths, and version numbers would otherwise truncate the summary (https://peps.python.org/pep-0257/).
5. Use HTML comments for markers: invisible in rendered markdown, which matters since plan.md is read rendered.

**Versioning**: Python stdlib only; any Python 3.8+ suffices. The design borrows the doctoc/terraform-docs marker convention, not their tooling.

**Canonical snippet**:

```markdown
<!-- BEGIN_GENERATED_TASK_OVERVIEW -->
| Task | Files | Depends on | Summary |
|------|-------|------------|---------|
| Task 1: Add repair script | finalize_plan.py | none | Adds a stdlib repair pass. |
<!-- END_GENERATED_TASK_OVERVIEW -->
```

### Decision 4: design.md with two-phase rationale lifecycle

**Verdict**: The chosen design works but is a genuine synthesis, not a precedented pattern: neither Kiro nor OpenSpec appends to design.md per completed task. Kiro's design.md is authored once during the Design phase before tasks execute (https://kiro.dev/docs/specs/); OpenSpec's design.md is created pre-implementation and only revised when "implementation reveals the approach won't work" (https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md). The per-task append is closer to what independent commentary recommends (capture rationale mid-implementation while it is fresh) than to what either tool ships; it should work but cannot cite Kiro/OpenSpec as-is.

**Gotchas**:
1. Kiro only mutates design.md through an explicit user-triggered Refine action; automatic per-task appends diverge from that model and can accumulate drift between narrative and tasks.
2. OpenSpec scopes design.md edits to plan corrections, not a chronological log; per-task appends risk turning design.md into a noisy journal. Keep entries terse and scoped.
3. OpenSpec discards design rationale on archive by default (only specs carry forward); deep-plan's folder plus index provide the retrieval story OpenSpec lacks.
4. A per-plan design.md forfeits MADR's per-decision addressability (`status: superseded by ADR-0123`); a later decision cannot cite one specific past decision without reading the plan's design doc.
5. The most-cited root cause of stale design docs is "no one owns the updates"; the append step must be enforced as a mandatory gated step (after verification passes), not an aspirational convention.

**Versioning**: documentation-convention decision, no runtime constraint. MADR templates use YAML front matter if status-field parity is ever wanted.

**Canonical snippet** (OpenSpec docs/concepts.md design.md outline):

```markdown
