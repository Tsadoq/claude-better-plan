# Critic-fleet orchestration

How every caller (the standalone `/design-review` and `/tdd-review` skills, deep-plan Phase 4.6, and the deep-plan-execute post-task review) runs a critic fleet. A triage gate arms the clusters worth checking, one finder per armed cluster, a dedup barrier, then an adversarial verify stage. The mechanics live only here; callers state their review target, pick the critic agent type, and quote this recipe. Three pairings are supported:

- `deep-plan:dp-design-critic` with `design-principles.md` (the default).
- `deep-plan:dp-test-critic` with the tdd-review skill's `test-principles.md`.
- `deep-plan:dp-readability-critic` with *either* `readability-principles.md` or `skills/deep-plan/references/plan-integrity-principles.md`. This leaf carries no rubric of its own — its whole question set is caller-supplied — so a second cluster source needs no new agent type, only a second run of the recipe.

## Triage gate

Most review targets have nothing to find in most clusters, and a finder that reads a whole cluster body to conclude "nothing here" costs as much as one that finds a real defect. So the fleet opens with one cheap pass that decides where to spend.

- **One triage agent, not one per cluster.** It is prompted with the cluster *names only* and the review target. It never receives a cluster body, which is what makes it cheap; it is deciding where to look, not looking.
- **It returns the subset of cluster names that plausibly apply.** Only those clusters get a finder. An unarmed cluster costs nothing.
- **Fail open, never closed.** If triage errors, returns nothing parseable, or names no cluster at all, arm every cluster. A gate that silently swallows the review is worse than an ungated one.
- **A finder that returns no findings short-circuits its own verify stage.** This falls out of the dedup barrier: verify launches one agent per surviving finding, so a quiet finder adds zero verify agents.

Callers do not decide whether to triage. They may decide which clusters to *offer* — that is the caller's own gate, described in its own file — but every fleet run passes the offered clusters through this one.

## Workflow fleet

Preferred path when the Workflow tool is available (see `## Version gate`). The caller substitutes the review target (diff text, plan excerpt, or file paths) and quotes each cluster's questions from the chosen principles file into the finder prompts.

```javascript
export const meta = {
  name: 'design-critic-fleet',
  description: 'Fan out one design critic per red-flag cluster, dedup, adversarially verify',
  phases: [
    { title: 'Triage', detail: 'name the clusters worth checking' },
    { title: 'Find', detail: 'one finder per armed cluster' },
    { title: 'Verify', detail: 'refute each surviving finding' },
  ],
}

const TRIAGE_SCHEMA = {
  type: 'object',
  required: ['armed'],
  properties: { armed: { type: 'array', items: { type: 'string' } } },
}

const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['cluster', 'severity', 'principle', 'evidence', 'finding'],
        properties: {
          cluster: { type: 'string' },
          severity: { enum: ['material', 'minor'] },
          principle: { type: 'string' },
          evidence: { type: 'string', description: 'file:line' },
          finding: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['refuted', 'reason'],
  properties: { refuted: { type: 'boolean' }, reason: { type: 'string' } },
}

// One entry per H3 cluster under `## Review-time red flags` in the caller's
// principles file; `questions` is that cluster's bullet list, quoted verbatim.
// args = { clusters: [{name, questions}], target: '<diff text | plan excerpt | file paths>',
//          agentType: '<critic agent type; default deep-plan:dp-design-critic>' }
const critic = args.agentType ?? 'deep-plan:dp-design-critic'

// Triage: names only, no cluster bodies. Fails open — an unusable answer arms
// everything, so the gate can never silently swallow the review.
phase('Triage')
const triage = await agent(
  `Decide where a design review of this target is worth spending effort.\n` +
  `Candidate red-flag clusters: ${args.clusters.map(c => c.name).join(', ')}.\n` +
  `Review target:\n${args.target}\n` +
  `Return the names of only the clusters that plausibly have something to find. ` +
  `You have not been given the clusters' questions; name clusters, do not report findings.`,
  { label: 'triage', phase: 'Triage', schema: TRIAGE_SCHEMA, agentType: critic },
)
const armedNames = new Set(triage?.armed ?? [])
const armed = armedNames.size ? args.clusters.filter(c => armedNames.has(c.name)) : args.clusters
if (armed.length < args.clusters.length) {
  log(`triage armed ${armed.length}/${args.clusters.length}: ${armed.map(c => c.name).join(', ')}`)
}

phase('Find')
const found = await parallel(armed.map(c => () =>
  agent(
    `You are checking one red-flag cluster: ${c.name}.\n${c.questions}\n` +
    `Review target:\n${args.target}\n` +
    `Report every "yes" answer as a finding with cluster, severity, principle, evidence (file:line), finding.`,
    { label: `find:${c.name}`, phase: 'Find', schema: FINDINGS_SCHEMA, agentType: critic },
  )))

// Barrier is deliberate: dedup needs the full finding set before verification spends tokens.
const seen = new Set()
const deduped = found.filter(Boolean).flatMap(r => r.findings).filter(f => {
  const key = `${f.evidence}|${f.principle}`
  if (seen.has(key)) return false
  seen.add(key)
  return true
})

phase('Verify')
const verified = await parallel(deduped.map(f => () =>
  agent(
    `Adversarially verify this design finding. Try to REFUTE it; default to refuted if the evidence does not hold.\n` +
    `Finding: [${f.severity}] ${f.cluster}/${f.principle}: ${f.finding} -- evidence: ${f.evidence}\n` +
    `Review target:\n${args.target}`,
    { label: `verify:${f.principle}`, phase: 'Verify', schema: VERDICT_SCHEMA, agentType: critic },
  ).then(v => ({ ...f, refuted: v?.refuted ?? false }))))

return { findings: verified.filter(Boolean).filter(f => !f.refuted) }
```

The returned findings carry `{cluster, severity: material|minor, principle, evidence, finding}`. Callers route `material` findings into their fix loop and `minor` findings into their non-blocking channel (Open questions at plan-time, the task completion note at execute-time).

## Version gate

The Workflow tool is not universally present:

- Requires Claude Code >= 2.1.154.
- Paid plans only, and off by default on Pro (users enable it via /config).
- Org-disableable via the `disableWorkflows` setting or `CLAUDE_CODE_DISABLE_WORKFLOWS`.
- Not programmatically feature-detectable: there is no API that reports whether Workflow is available before calling it, and a call in default permission modes surfaces an approval card the user may deny.

Callers therefore attempt the Workflow path and treat absence, denial, or error as an immediate switch to `## Fallback` — never as a reason to skip the review.

## Fallback

Normative whenever the Workflow tool is absent, denied, or errors. Same shape, driven by the caller through the plain Agent tool:

1. **Find.** Launch one critic of the caller-chosen agent type (haiku) per H3 cluster under `## Review-time red flags` in the caller's principles file — `dp-design-critic` with `design-principles.md`, `dp-test-critic` with the tdd-review skill's `test-principles.md` — all in a single message so they run concurrently. Each prompt carries: the cluster name, that cluster's questions quoted verbatim, and the review target (diff text, plan excerpt, or file paths). Each critic returns one finding per line: `[material|minor] {cluster}/{principle}: {finding} -- evidence: {file:line}` — the same fields as the Workflow schema, so no information is lost relative to the Workflow path.
2. **Dedup.** The caller merges the finder outputs and drops findings sharing the same evidence location and principle.
3. **Verify.** For each surviving finding, launch a fresh instance of the same critic agent type prompted to REFUTE it (again batched in one message). A finding stands only if the verifier cannot refute it; discard refuted findings.
4. **Route.** Handle surviving findings exactly as in the Workflow path: `material` into the caller's fix loop, `minor` into its non-blocking channel.

## Nested fleets

A fleet may be launched by a subagent rather than by the main thread — the deep-plan-execute implementer runs its own post-task review this way, so the diff never crosses back up to the dispatcher. A nested caller has two extra obligations:

- **Pass `run_in_background: false` on every `Agent` launch.** Subagents default to *background*, and a backgrounded launch returns an acknowledgement rather than a result. A fleet whose finders were backgrounded reports zero findings and looks like a clean review, which is the worst available failure mode.
- **Take the `## Fallback` path directly; do not attempt the Workflow path.** `workflow()` nesting is capped at one level, so a nested Workflow call throws. This is the one case where skipping the Workflow attempt is correct rather than a shortcut.

Namespaced agent-type resolution *from inside a subagent* has been probed for `deep-plan:dp-design-critic` only, and that probe used an unnamespaced type (see `## agentType resolution`). Treat resolution of any other type from a nested caller as unverified: if a launch fails to resolve, degrade to inline self-review against the same cluster questions and say so in the return summary. Never let a resolution failure become a skipped review.

## Session agent budget

Two hard caps apply, and both count nested children against the launching session:

- **200 subagents per session** (`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`).
- **20 concurrent subagents** (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`).

Both defaults can be raised, but neither can be turned off, so a caller cannot opt out of budgeting.

A fleet's own agent count is *not* fixed. Triage is one, find is one per armed cluster, but verify launches one agent per surviving deduped finding and is bounded only by how much the finders found. A target with many real defects therefore costs more agents than a clean one — which is the right direction, but it means a caller cannot budget a fleet as a single number.

Callers that run one fleet per unit of work (per task, per file) must state their per-unit cost as a **range** and degrade on the upper end, not the lower. Budgeting on the minimum is how a run dies two thirds of the way through a large plan.

## agentType resolution

Probe status: probed 2026-07-03, Claude Code 2.1.200

Plugin-namespaced agentType resolution is undocumented, so it was probed empirically: a headless session loaded this plugin from a local checkout (`--plugin-dir`), confirmed `deep-plan:dp-design-critic` in the agent registry, and ran a one-agent Workflow script with `agentType: "deep-plan:dp-design-critic"` on a trivial one-file review. The namespaced form resolved and the critic returned its schema-shaped result; the bare form (`"dp-design-critic"`) was not needed and remains untested. Callers should use the plugin-namespaced form. `## Fallback` stays normative for environments where Workflow itself is gated (see `## Version gate`), not because of resolution uncertainty. `deep-plan:dp-test-critic` relies on the same namespaced mechanism but has not been separately probed, so `## Fallback` stays normative for it until a first Workflow run confirms resolution.
