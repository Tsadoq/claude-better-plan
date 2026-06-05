## Research dossiers (appendix)

### Decision 1: drop plan mode entirely

Verdict: Sound. Plan mode's read-only behavior is enforced only at the prompt level, not the tool level. Every affordance (the ~/.claude/plans/ file, Ultraplan rendering, /plan prefix, ExitPlanMode gate with auto-switch to acceptEdits, session naming, showClearContextOnPlanAccept) is a UI convenience layer, not a safety guarantee; none is load-bearing for this skill. AskUserQuestion has no documented limit on rounds or options and requires no permission prompt, making it a viable approval gate. Multi-phase orchestration (subagents, file writes, question rounds) works in normal default mode without restriction.

Gotchas:
- ExitPlanMode requires a permission prompt; with plan mode dropped the skill must never call EnterPlanMode or ExitPlanMode.
- Research subagents are NOT read-only by default; only `disallowedTools: Write, Edit, NotebookEdit` in the agent definition is reliable (`permissionMode` frontmatter on subagents is ignored in auto mode). The dp-* agents already do this.
- Native plan mode's session auto-naming and clear-context-on-accept disappear; the skill manages context discipline via the /compact handoff recommendation.
- `.claude/` is a protected directory: a plans dir under it triggers a permission prompt on every write in default mode.

Versioning: Claude Code v2.1.83+ floor (auto mode handling); skills are markdown, no library dependency. `disallowed-tools` skill frontmatter clears on next user message (turn-scoped). No `permissionMode` field exists for skills.

Canonical mechanism: skill frontmatter cannot grant permissions; the session's existing permission mode is always the baseline.

Sources: code.claude.com/docs/en/permission-modes, /tools-reference, /skills, /sub-agents; claude-code#19874.

### Decision 2/6: draft-in-repo lifecycle and permissions

Verdict: Viable without permission stutter, but the smooth-write mechanism is NOT skill frontmatter `allowed-tools` (parsed but not enforced; claude-code#37683 closed not-planned). It is a `permissions.allow` path rule in project `.claude/settings.json`: `Edit(/docs/plans/**)` and `Write(/docs/plans/**)` (leading `/` anchors to project root). Plugins cannot ship permissions (plugin settings.json supports only `agent` and `subagentStatusLine`), so the user adds the rule once, or accepts a per-file prompt with "don't ask again until session end".

Gotchas:
- Default mode prompts on every file-modification tool call absent an allow rule; first append would stall without one.
- `.claude/` is protected: writes there always prompt regardless of allow rules; the plans dir must live outside `.claude/`.
- Bash `mv` prompts in default mode unless allowlisted (`Bash(mv docs/plans/*)` -- one `*` spans arguments) or the session is in acceptEdits.
- PreToolUse hook `permissionDecision: allow` is layered under deny/ask rules; the path allow rule is cleaner.

Versioning: `Edit(/path/**)` gitignore-style syntax is the current canonical form; `//` prefix means absolute filesystem path; Windows paths normalize to POSIX.

Canonical snippet:
```json
{"permissions": {"allow": ["Edit(/docs/plans/**)", "Write(/docs/plans/**)", "Bash(mv docs/plans/*)"]}}
```

Sources: code.claude.com/docs/en/permissions, /permission-modes, /plugins; claude-code#37683.

### Decision 4: single AskUserQuestion approval gate

Verdict: Supported by prior art. Superpowers writing-plans runs a three-check mechanical self-review and fixes issues inline BEFORE presenting its gate (matching repair-before-gate); neither superpowers nor planning-with-files uses plan mode or ExitPlanMode for approval. Deep-plan improves on superpowers by separating approval from execution-path choice and offering structured edit options.

Gotchas:
- Plan-mode system prompts explicitly forbid AskUserQuestion for plan approval; if the skill ever entered plan mode, the gate becomes unreachable by design. Staying out of plan mode is load-bearing (claude-code#29950: plan-mode tool prompts override skill guardrails).
- ExitPlanMode has a known timing bug where the approval prompt appears before users read the plan (#28288); inline rendering before the question avoids it.
- Post-rejection write actions are a documented plan-mode regression (#21292); another reason to stay out.
- Context clearing on ExitPlanMode approval can destroy multi-phase skill state (#18599); the chosen shape never triggers it.
- No reported failure mode of users skimming AskUserQuestion gates; the dominant prior-art failure is agents skipping gates entirely (instruction-compliance, mitigated by R2).

Versioning: superpowers SKILL.md read at main, June 2026; planning-with-files v2.1.139 (May 2026); claude-code#29950 verified present through v2.1.63.

Canonical snippet (superpowers self-review, adapted): spec-coverage map, placeholder scan, consistency check, fix inline, then gate.

Sources: raw.githubusercontent.com/obra/superpowers writing-plans SKILL.md; claude-code#29950, #28288, #21292, #18599.
