# Critic-fleet orchestration

How every caller (the standalone `/design-review`, `/tdd-review`, and `/product-review` skills, deep-plan Phase 4.6, and the deep-plan-execute post-task review) runs a critic fleet. A triage gate arms the clusters worth checking, one finder per armed cluster, a dedup barrier, then an adversarial verify stage. This file is the caller's half of that, and the only home for it: the fan-out, the wire the two halves meet on, and the budget. Callers state their review target, name their cluster source, and quote this recipe. How a leaf judges what it reads — and how hard it leans on a finding in verify mode — belongs to `agents/dp-critic.md` and is deliberately not restated here, because five callers quote this file and pay for every line of it whether or not a fleet ever runs.

Every finder is the same agent type, `deep-plan:dp-critic`, and it carries no rubric of its own, so what varies between runs is the cluster source, not the agent. The caller passes one principles-file path explicitly — `design-principles.md` (the default), the tdd-review skill's `test-principles.md`, `skills/deep-plan/references/readability-principles.md`, `skills/deep-plan/references/plan-integrity-principles.md`, or a product beat's own rubric at `skills/product-*/references/product-*-principles.md`, one per beat and composed by the caller from the reviewed artifact's owning beat rather than listed here — alongside the cluster name, and the leaf reads that file itself. Selection never rests on which agent description best matches the review; there is only one to match.

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
  name: 'critic-fleet',
  description: 'Fan out one critic per red-flag cluster, dedup, adversarially verify',
  phases: [
    { title: 'Triage', detail: 'name the clusters worth checking' },
    { title: 'Find', detail: 'one finder per armed cluster' },
    { title: 'Verify', detail: 'adversarially re-check each surviving finding' },
  ],
}

const TRIAGE_SCHEMA = {
  type: 'object', required: ['armed'],
  properties: { armed: { type: 'array', items: { type: 'string' } } },
}

// The five finding fields, declared once so `required` is derived, never drifts.
const FINDING = {
  cluster: { type: 'string' },
  severity: { enum: ['material', 'minor'] },
  principle: { type: 'string' },
  evidence: { type: 'string', description: 'file:line' },
  finding: { type: 'string' },
}
const FINDING_ITEM = { type: 'object', required: Object.keys(FINDING), properties: FINDING }
const FINDINGS_SCHEMA = {
  type: 'object', required: ['findings'],
  properties: { findings: { type: 'array', items: FINDING_ITEM } },
}

const VERDICT_SCHEMA = {
  type: 'object', required: ['refuted', 'reason'],
  properties: { refuted: { type: 'boolean' }, reason: { type: 'string' } },
}

// args = { clusters: [{name, questions}], target: '<diff text | plan excerpt | file paths>',
//          source: '<principles-file path>',
//          agentType: '<critic agent type; default deep-plan:dp-critic>' }
// One `clusters` entry per H3 cluster under `## Review-time red flags` in the
// caller's principles file; `questions` is that cluster's bullet list, verbatim.
const critic = args.agentType ?? 'deep-plan:dp-critic'

phase('Triage')
const triage = await agent(
  `Decide where a review against ${args.source} is worth spending effort.\n` +
  `Candidate red-flag clusters: ${args.clusters.map(c => c.name).join(', ')}.\n` +
  `Review target:\n${args.target}\n` +
  `Return the names of only the clusters that plausibly have something to find. ` +
  `You have not been given the clusters' questions; name clusters, do not report findings.`,
  { label: 'triage', phase: 'Triage', schema: TRIAGE_SCHEMA, agentType: critic },
)
// Fails open per `## Triage gate`: an unusable answer arms every cluster.
const armedNames = new Set(triage?.armed ?? [])
const armed = armedNames.size ? args.clusters.filter(c => armedNames.has(c.name)) : args.clusters
if (armed.length < args.clusters.length) {
  log(`triage armed ${armed.length}/${args.clusters.length}: ${armed.map(c => c.name).join(', ')}`)
}

phase('Find')
const found = await parallel(armed.map(c => () =>
  agent(
    `Your cluster source is ${args.source}.\n` +
    `You are checking one red-flag cluster from it: ${c.name}.\n${c.questions}\n` +
    `Review target:\n${args.target}\n` +
    `Report every finding those questions turn up.`,
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
    `Verify mode: one prior finding to re-check against ${args.source}.\n` +
    `Finding: [${f.severity}] ${f.cluster}/${f.principle}: ${f.finding} -- evidence: ${f.evidence}\n` +
    `Review target:\n${args.target}`,
    { label: `verify:${f.principle}`, phase: 'Verify', schema: VERDICT_SCHEMA, agentType: critic },
  ).then(v => ({ ...f, refuted: v?.refuted ?? false }))))

return { findings: verified.filter(Boolean).filter(f => !f.refuted) }
```

The returned findings carry `{cluster, severity: material|minor, principle, evidence, finding}`. Callers route `material` findings into their fix loop and `minor` findings into their non-blocking channel (Open questions at plan-time, the task completion note at execute-time).

## Version gate

The Workflow tool is not universally present: it needs Claude Code >= 2.1.154 on a paid plan, is off by default on Pro (users enable it via /config), and is org-disableable through the `disableWorkflows` setting or `CLAUDE_CODE_DISABLE_WORKFLOWS`. None of that is programmatically feature-detectable — no API reports whether Workflow is available before you call it, and a call in default permission modes surfaces an approval card the user may deny.

Callers therefore attempt the Workflow path and treat absence, denial, or error as an immediate switch to `## Fallback` — never as a reason to skip the review.

## Fallback

Normative whenever the Workflow tool is absent, denied, or errors. Same shape, driven by the caller through the plain Agent tool:

1. **Find.** Launch one `deep-plan:dp-critic` per H3 cluster under `## Review-time red flags` in the caller's principles file, all in a single message so they run concurrently. Each prompt carries four things: the cluster-source path, the cluster name, that cluster's questions quoted verbatim, and the review target (diff text, plan excerpt, or file paths). The source path is not decoration — it is the only thing that tells an otherwise identical leaf whether it is hunting design, test, readability, or plan-integrity flaws. Each critic returns one finding per line: `[material|minor] {cluster}/{principle}: {finding} -- evidence: {file:line}` — the same fields as the Workflow schema, so no information is lost relative to the Workflow path.
2. **Dedup.** The caller merges the finder outputs and drops findings sharing the same evidence location and principle.
3. **Verify.** For each surviving finding, launch a fresh `deep-plan:dp-critic` in verify mode, carrying that one finding and the same cluster source (again batched in one message). The adversarial stance is the agent's own, so the prompt need not argue for it; the caller only routes the verdict, keeping the findings that come back `stands` and discarding the ones that come back `refuted`.
4. **Route.** Handle surviving findings exactly as in the Workflow path: `material` into the caller's fix loop, `minor` into its non-blocking channel.

## Nested fleets

A fleet may be launched by a subagent rather than by the main thread — the deep-plan-execute implementer runs its own post-task review this way, so the diff never crosses back up to the dispatcher. A nested caller has two extra obligations:

- **Pass `run_in_background: false` on every `Agent` launch.** Subagents default to *background*, and a backgrounded launch returns an acknowledgement rather than a result. A fleet whose finders were backgrounded reports zero findings and looks like a clean review, which is the worst available failure mode.
- **Take the `## Fallback` path directly; do not attempt the Workflow path.** `workflow()` nesting is capped at one level, so a nested Workflow call throws. This is the one case where skipping the Workflow attempt is correct rather than a shortcut.

Namespaced agent-type resolution *from inside a subagent* is unverified: the one probe on record ran from a main thread (see `## agentType resolution`), and it named the predecessor of today's `deep-plan:dp-critic`. If a launch fails to resolve, degrade to inline self-review against the same cluster questions and say so in the return summary. Never let a resolution failure become a skipped review.

## Session agent budget

Two hard caps apply. Both count nested children against the launching session, and both defaults can be raised but neither can be turned off, so a caller cannot opt out of budgeting.

- **200 subagents per session** (`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`).
- **20 concurrent subagents** (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`).

A fleet's own agent count is *not* fixed. Triage is one, find is one per armed cluster, but verify launches one agent per surviving deduped finding and is bounded only by how much the finders found. A target with many real defects therefore costs more agents than a clean one — which is the right direction, but it means a caller cannot budget a fleet as a single number. Callers that run one fleet per unit of work (per task, per file) must state their per-unit cost as a **range** and degrade on the upper end, not the lower. Budgeting on the minimum is how a run dies two thirds of the way through a large plan.

## agentType resolution

Probe status: probed 2026-07-03, Claude Code 2.1.200

Plugin-namespaced agentType resolution is undocumented, so it was probed empirically: a headless session loaded this plugin from a local checkout (`--plugin-dir`), confirmed the critic agent of the day in the agent registry, and ran a one-agent Workflow script with its plugin-namespaced `agentType` on a trivial one-file review. The namespaced form resolved and the critic returned its schema-shaped result; the bare, un-namespaced form was not needed and remains untested. Callers should use the plugin-namespaced form, `deep-plan:dp-critic`. Two caveats on how far that probe carries: it ran against the design critic that `deep-plan:dp-critic` later absorbed, so the merged agent's own registry entry is untested, and it ran from a main thread, so nested resolution is untested (see `## Nested fleets`). `## Fallback` therefore stays normative — for gated Workflow environments (see `## Version gate`) and for resolution uncertainty alike.
