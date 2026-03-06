# Task Handoff

## Task

- **Date:** 2026-03-06
- **Task slug:** build-plan-corrections-recheck-2
- **Owner role:** reviewer
- **Scope:** Recheck the latest `docs/build-plan/` corrections after the previous validation handoff, focusing on whether the substantive MCP and workflow issues are now resolved.

## Inputs

- User request:
  - Recheck the plan again
- Prior review artifacts:
  - `.agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`
  - `.agent/context/handoffs/2026-03-06-build-plan-corrections-validation.md`
- Current files inspected:
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/00-overview.md`
  - `.agent/context/current-focus.md`
  - `AGENTS.md`
  - `GEMINI.md`
  - `tools/validate_build_plan.py`
- Current-source checks:
  - MCP lifecycle capability negotiation
  - MCP tools output compatibility guidance
  - TypeScript SDK issue `#911` status

## Role Plan

1. orchestrator
2. tester
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-06-build-plan-corrections-recheck-2.md`
- Design notes:
  - Review-only session. No plan files were modified.
  - The recheck targeted the newly changed MCP plan sections and the validator itself.
- Commands run:
  - `git status --short -- docs/build-plan .agent/context/current-focus.md AGENTS.md GEMINI.md .agent/context/handoffs`
  - `git diff -- docs/build-plan .agent/context/current-focus.md AGENTS.md GEMINI.md`
  - `python tools/validate_build_plan.py`
  - `rg -n "Day-1 Baseline Contract|prototype mode|single-client|multi-client|rollout gate|Gate A|Gate B|Gate C|first MCP prototype|first constrained MCP slice|evidence gate|static stdio|one supported client target|small tool set" docs/build-plan/00-overview.md docs/build-plan/05-mcp-server.md docs/BUILD_PLAN.md`
  - `rg -n "GPT-5.4|GPT 5.3|Time is not a constraint|Token usage is not a constraint|Do not bring up time or token usage|reviewer runs commands|does NOT execute trades" AGENTS.md GEMINI.md .agent/context/current-focus.md`
  - current-source checks against MCP spec pages and the TS SDK issue tracker
- Results:
  - Confirmed that the validator fix landed and now passes with warnings only.
  - Confirmed that the auth-lifecycle contradiction, capability-first detection gap, and reviewer-baseline drift are materially improved.
  - Identified two remaining design issues and two residual doc-quality gaps.

## Tester Output

- Commands run:
  - grep sweeps
  - build-plan validator
  - current-source web verification
- Pass/fail matrix:
  - Build-plan validator: pass with warnings
  - Capability-first detection correction: pass
  - Reviewer baseline lock in current focus: pass
  - Constrained day-1 MCP slice: fail
  - Explicit rollout-stage policy in overview: fail
- Repro failures:
  - None
- Coverage/test gaps:
  - This remains a documentation-state validation. No runtime transport or SDK execution tests were run.

## Reviewer Output

- Findings by severity:
  - **High-1:** The plan is still starting Phase 5 too broadly. `05-mcp-server.md` now correctly says the 37-tool default is no longer Cursor-driven and that Antigravity is the day-1 client at `docs/build-plan/05-mcp-server.md:747`, `docs/build-plan/05-mcp-server.md:750`, and `docs/build-plan/05-mcp-server.md:836`. That fixes the target mismatch. But it still means the day-1 MCP slice is `dynamic` with all default toolsets loaded rather than a constrained first cohort. This remains materially more ambitious than the earlier senior recommendation for a small first toolset and is still the biggest design-risk item left.
  - **Medium-1:** The rollout-staging correction is still not explicit in the plan spine. `00-overview.md` has strong evidence gates at `docs/build-plan/00-overview.md:100`, `docs/build-plan/00-overview.md:114`, and `docs/build-plan/00-overview.md:118`, but it still does not define the missing `prototype mode` / `single-client production baseline` / `multi-client platform mode` progression. The plan now has stronger local decisions, but the overall rollout model is still implied rather than stated.
  - **Medium-2:** The structured-output correction is now directionally sound but still incomplete. `05-mcp-server.md` now stages output behavior at `docs/build-plan/05-mcp-server.md:1012`: day-1 text-only, `outputSchema` later, dual-format after SDK `#911` is resolved. That is a defensible simplification and aligns with current protocol/client reality, but the day-1 text-only mode still needs a mandated stable envelope shape if you want predictable reviewer/tester behavior before `structuredContent` is introduced.
  - **Low-1:** The build-plan validator now passes, but it still reports three quality warnings: missing `## Goal` in `05-mcp-server.md`, missing `## Exit Criteria` in `07-distribution.md`, and no prerequisites line in `05-mcp-server.md`. These are not blockers, but they do mean the docs set is not yet internally uniform.

- Resolved Since Last Check:
  - **Resolved:** The auth-lifecycle contradiction is fixed. `05-mcp-server.md` now gives an implementable HTTP-only credential flow at `docs/build-plan/05-mcp-server.md:281`, with the API key sourced from each incoming MCP HTTP request rather than from cached secret replay.
  - **Resolved:** Client detection is now capability-first rather than name-first at `docs/build-plan/05-mcp-server.md:788` through `docs/build-plan/05-mcp-server.md:835`, which aligns with the MCP lifecycle model.
  - **Resolved:** Reviewer-baseline drift in the active plan state is fixed in `current-focus.md` at `.agent/context/current-focus.md:11`, `.agent/context/current-focus.md:18`, and `.agent/context/current-focus.md:30`.
  - **Resolved:** The validator no longer falsely fails the `_inspiration` relocation changes; `python tools/validate_build_plan.py` now passes.

- Open questions:
  - Do you want the first MCP slice to optimize for delivery speed or for exercising the full dynamic-toolset architecture immediately?
  - If day-1 output stays text-only, what exact JSON envelope is required for all MCP tool responses?
  - Are the remaining `AGENTS.md` / `GEMINI.md` directive updates intentionally out of scope for this plan pass?

- Verdict:
  - **approved with conditions**
  - The plan is materially improved and no longer has the earlier blocking contradictions. The remaining issues are about controlling Phase 5 scope, not about internal inconsistency.

- Residual risk:
  - If implementation starts with the full 37-tool dynamic baseline, you will validate more architecture surface area faster, but you also increase the chance that the first MCP sprint turns into SDK/client integration work instead of product progress.

## Final Summary

- Status:
  - Recheck completed. The plan is significantly healthier than the previous validation state.
- Next steps:
  1. Decide whether to keep the 37-tool dynamic day-1 baseline or explicitly cut a smaller first MCP cohort.
  2. Add a short rollout-stage section to `00-overview.md`.
  3. Define a stable text-envelope contract for day-1 MCP outputs if `structuredContent` remains deferred.
