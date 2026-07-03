# Design-critic fleet orchestration

How every caller (the standalone `/design-review` skill, deep-plan Phase 4.6, and the deep-plan-execute post-task review) runs the design-critic fleet. One finder per red-flag cluster from `design-principles.md`, a dedup barrier, then an adversarial verify stage. The mechanics live only here; callers state their review target and quote this recipe.

## Workflow fleet

Preferred path when the Workflow tool is available (see `## Version gate`). The caller substitutes the review target (diff text, plan excerpt, or file paths) and quotes each cluster's questions from `design-principles.md` into the finder prompts.

```javascript
export const meta = {
  name: 'design-critic-fleet',
  description: 'Fan out one design critic per red-flag cluster, dedup, adversarially verify',
  phases: [
    { title: 'Find', detail: 'one finder per red-flag cluster' },
    { title: 'Verify', detail: 'refute each surviving finding' },
  ],
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

// One entry per H3 cluster under `## Review-time red flags` in
// design-principles.md; `questions` is that cluster's bullet list, quoted verbatim.
// args = { clusters: [{name, questions}], target: '<diff text | plan excerpt | file paths>' }
phase('Find')
const found = await parallel(args.clusters.map(c => () =>
  agent(
    `You are checking one red-flag cluster: ${c.name}.\n${c.questions}\n` +
    `Review target:\n${args.target}\n` +
    `Report every "yes" answer as a finding with cluster, severity, principle, evidence (file:line), finding.`,
    { label: `find:${c.name}`, phase: 'Find', schema: FINDINGS_SCHEMA, agentType: 'dp-design-critic' },
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
    { label: `verify:${f.principle}`, phase: 'Verify', schema: VERDICT_SCHEMA, agentType: 'dp-design-critic' },
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

1. **Find.** Launch one `dp-design-critic` (haiku) per H3 cluster under `## Review-time red flags` in `design-principles.md`, all in a single message so they run concurrently. Each prompt carries: the cluster name, that cluster's questions quoted verbatim, and the review target (diff text, plan excerpt, or file paths). Each critic returns one finding per line: `[material|minor] {cluster}/{principle}: {finding} -- evidence: {file:line}` — the same fields as the Workflow schema, so no information is lost relative to the Workflow path.
2. **Dedup.** The caller merges the finder outputs and drops findings sharing the same evidence location and principle.
3. **Verify.** For each surviving finding, launch a fresh `dp-design-critic` instance prompted to REFUTE it (again batched in one message). A finding stands only if the verifier cannot refute it; discard refuted findings.
4. **Route.** Handle surviving findings exactly as in the Workflow path: `material` into the caller's fix loop, `minor` into its non-blocking channel.

## agentType resolution

Probe status: probed 2026-07-03, Claude Code 2.1.200

Plugin-namespaced agentType resolution is undocumented, so it was probed empirically: a headless session loaded this plugin from a local checkout (`--plugin-dir`), confirmed `deep-plan:dp-design-critic` in the agent registry, and ran a one-agent Workflow script with `agentType: "deep-plan:dp-design-critic"` on a trivial one-file review. The namespaced form resolved and the critic returned its schema-shaped result; the bare form (`"dp-design-critic"`) was not needed and remains untested. Callers should use the plugin-namespaced form. `## Fallback` stays normative for environments where Workflow itself is gated (see `## Version gate`), not because of resolution uncertainty.
