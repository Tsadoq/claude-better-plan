# Critic-fleet orchestration

How every caller (the standalone $design-review, $tdd-review, and $product-review skills, deep-plan Phase 4.6, and the deep-plan-execute post-task review) runs a critic fleet. A triage gate arms the clusters worth checking, one finder per armed cluster, a dedup barrier, then an adversarial verify stage. This file is the caller's half of that, and the only home for it: the fan-out, the wire the two halves meet on, and the budget. Callers state their review target, name their cluster source, and quote this recipe. How a leaf judges what it reads — and how hard it leans on a finding in verify mode — belongs to `agents/dp-critic.md` and is deliberately not restated here, because five callers quote this file and pay for every line of it whether or not a fleet ever runs.

Every finder is the same agent type, `dp-critic`, and it carries no rubric of its own, so what varies between runs is the cluster source, not the agent. The caller passes one principles-file path explicitly — `design-principles.md` (the default), $tdd-review's `test-principles.md`, `skills/deep-plan/references/readability-principles.md`, `skills/deep-plan/references/plan-integrity-principles.md`, or a product beat's own rubric at `skills/product-*/references/product-*-principles.md`, one per beat and composed by the caller from the reviewed artifact's owning beat rather than listed here — alongside the cluster name, and the leaf reads that file itself. Selection never rests on which agent description best matches the review; there is only one to match.

## Triage gate

Most review targets have nothing to find in most clusters, and a finder that reads a whole cluster body to conclude "nothing here" costs as much as one that finds a real defect. So the fleet opens with one cheap pass that decides where to spend.

- **One triage agent, not one per cluster.** It is prompted with the cluster *names only* and the review target. It never receives a cluster body, which is what makes it cheap; it is deciding where to look, not looking.
- **It returns the subset of cluster names that plausibly apply.** Only those clusters get a finder. An unarmed cluster costs nothing.
- **Fail open, never closed.** If triage errors, returns nothing parseable, or names no cluster at all, arm every cluster. A gate that silently swallows the review is worse than an ungated one.
- **A finder that returns no findings short-circuits its own verify stage.** This falls out of the dedup barrier: verify launches one agent per surviving finding, so a quiet finder adds zero verify agents.

Callers do not decide whether to triage. They may decide which clusters to *offer* — that is the caller's own gate, described in its own file — but every fleet run passes the offered clusters through this one.

## Workflow fleet

This build has no Workflow path: every fleet runs the `## Fallback` recipe below.

## Fallback

The one fleet recipe; launch each agent below as HOST.md says:

1. **Find.** Launch dp-critic once per H3 cluster under `## Review-time red flags` in the caller's principles file, all in a single message so they run concurrently. Each prompt carries four things: the cluster-source path, the cluster name, that cluster's questions quoted verbatim, and the review target (diff text, plan excerpt, or file paths). The source path is not decoration — it is the only thing that tells an otherwise identical leaf whether it is hunting design, test, readability, or plan-integrity flaws. Each critic returns one finding per line: `[material|minor] {cluster}/{principle}: {finding} -- evidence: {file:line}`.
2. **Dedup.** The caller merges the finder outputs and drops findings sharing the same evidence location and principle.
3. **Verify.** For each surviving finding, launch a fresh `dp-critic` in verify mode, carrying that one finding and the same cluster source (again batched in one message). The adversarial stance is the agent's own, so the prompt need not argue for it; the caller only routes the verdict, keeping the findings that come back `stands` and discarding the ones that come back `refuted`.
4. **Route.** Handle surviving findings this way: `material` into the caller's fix loop, `minor` into its non-blocking channel.

## Nested fleets

Every fleet in this plugin is launched from the main thread. No subagent launches one, and the deep-plan-execute implementer — which used to review its own diff this way — no longer holds the `Agent` tool; its dispatcher runs the fleet over the returned diff instead. Two things forced that:

- **A subagent's children run detached from the conversation that needs them.** Launches from inside a subagent default to *background*, and a backgrounded launch returns an acknowledgement rather than a result, so a nested fleet reports zero findings and looks like a clean review — the worst available failure mode. `run_in_background: false` is the documented cure and still binds every main-thread caller, but a completion notification from a nested child routes to the main conversation rather than to the subagent waiting on it (anthropics/claude-code issue 75043), so the nested caller can be left waiting on a result it will never be handed.
- **Namespaced agent-type resolution from inside a subagent is unverified.** The one probe on record ran from a main thread.

A subagent that still needs its own work reviewed reads it against the same cluster questions itself and says so in its summary. That is the only reviewing a subagent does here; the fleet waits for the thread that launched it.

## Session agent budget

Two hard caps apply. Both count nested children against the launching session, and both defaults can be raised but neither can be turned off, so a caller cannot opt out of budgeting.

- **200 subagents per session** (`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`).
- **20 concurrent subagents** (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`).

A fleet's own agent count is *not* fixed. Triage is one, find is one per armed cluster, but verify launches one agent per surviving deduped finding and is bounded only by how much the finders found. A target with many real defects therefore costs more agents than a clean one — which is the right direction, but it means a caller cannot budget a fleet as a single number. Callers that run one fleet per unit of work (per task, per file) must state their per-unit cost as a **range** and degrade on the upper end, not the lower. Budgeting on the minimum is how a run dies two thirds of the way through a large plan.

