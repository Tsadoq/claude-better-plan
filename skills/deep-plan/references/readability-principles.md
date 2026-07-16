# Readability principles for plan artifacts

Scope: this file is the single source of truth for narrative-artifact readability in the plugin — how plan.md, design.md, architecture.md, research.md, and probes.md stay readable by someone who was not in the planning session. Orchestrators and templates quote one section (or the H3 cluster) by heading; nothing here is duplicated elsewhere.

## Plan-time authoring rules

These act while any plan artifact is being written. They apply across the whole artifact set, not per file.

- **Decision first.** A section that records a decision states that decision in its first sentence. The story of how it was reached comes after, never instead.
- **Question before verdict.** Never state a verdict, answer, or conclusion before the question it resolves has been posed. A reader who has not seen the question cannot judge the answer.
- **Traceable evidence.** Every evidence citation points at a specific finding a reader can locate — a section, a probe entry, an annotated source — never at a bundled blob like a whole file or "the research".
- **Self-contained sections.** Each section reads alone, with no implicit back-references ("as discussed above", "the earlier option"). If a section needs another's content, it links to it explicitly.
- **Jargon defined at first use.** Every project-specific term is defined where it first appears; when the term recurs in a second file, re-anchor it in a short clause rather than assuming the reader arrived in order.
- **Summary sentence, then sub-bullets.** A task's Change block opens with exactly one plain-English summary sentence, then continues in structured sub-bullets naming exact symbols, files, and knobs — never a run-on clause chain.
- **Probes explain themselves.** A probe entry carries four parts: why the check ran, the command, what was observed, and what a failure would have meant.
- **One slug rule for cross-file links.** Anchors in cross-file links follow the GitHub heading-slug rule: lowercase the heading, replace spaces with hyphens, strip punctuation other than hyphens and underscores (so "When does a plan deserve an architecture.md?" becomes `when-does-a-plan-deserve-an-architecturemd`). This is the single definition; the design template quotes it for authors and finalize_plan.py implements it for the link check.

## Review-time red flags

The cluster below is quoted verbatim into one dp-readability-critic finder. Every question is answerable yes/no against the finished artifacts (plan.md, design.md, architecture.md when present); "yes" is a finding. Severity hints are defaults — a critic may upgrade or downgrade with evidence.

### Artifact readability

- Is a project-specific term used before any artifact in the set defines it (undefined jargon)?
  Severity hint: minor, material when the term names a load-bearing concept of the plan.
- Is a verdict, answer, or decision stated before the question it resolves has been posed (verdict before question)?
  Severity hint: material.
- Does an evidence pointer cite a bundle (a whole file, a whole dossier, "the research") rather than a specific finding a reader can locate (untraceable evidence)?
  Severity hint: material.
- Does a section assume context that neither it nor any artifact in the set supplies (missing context)?
  Severity hint: material.
- Is any section empty, or does a heading dangle with no body before the next heading of the same or higher level (dangling section)?
  Severity hint: minor, material when the empty section is one the plan's contract requires.

## How to update these guidelines

The three H2 headings above and the single-cluster H3 structure under "Review-time red flags" are pinned by `skills/deep-plan/tests/test_readability_contract.py` (`test_readability_principles_structure`); renaming a section breaks callers that quote it, so change the test and every caller in the same commit. The files that quote sections of this file are:

- `skills/deep-plan/references/design-md-template.md` (authoring-rules pointer and the anchor-slug rule)
- `skills/deep-plan/references/plan-file-template.md` (formatting rules: authoring-rules pointer)
- `agents/dp-research-deep.md` (jargon-at-first-use pointer)
- `agents/dp-readability-critic.md` (receives the red-flag cluster, quoted by the caller)
- `skills/deep-plan/SKILL.md` (Phase 4.6: the red-flag cluster) and `skills/deep-plan/references/phase-prompts.md` (Phase 4.4 authoring: plan-time authoring rules; Phase 4.6: the red-flag cluster)
- `skills/deep-plan/scripts/finalize_plan.py` (implements the anchor-slug rule and the dangling-section warning mechanically)
