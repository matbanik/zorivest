# Task Handoff Template

## Task

- **Date:** 2026-02-27
- **Task slug:** docs-build-plan-mcp-session6-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Critically review `.agent/context/handoffs/2026-02-26-mcp-session6-plan.md` and `.agent/context/handoffs/2026-02-26-mcp-session6-walkthrough.md` against current `docs/build-plan/` state (primary targets: `05c-mcp-trade-analytics.md`, `05j-mcp-discovery.md`).

## Inputs

- User request: `[critical-review-feedback.md](.agent/workflows/critical-review-feedback.md) [2026-02-26-mcp-session6-plan.md](.agent/context/handoffs/2026-02-26-mcp-session6-plan.md) [2026-02-26-mcp-session6-walkthrough.md](.agent/context/handoffs/2026-02-26-mcp-session6-walkthrough.md) for docs\build-plan files`
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/2026-02-26-mcp-session6-plan.md`
  - `.agent/context/handoffs/2026-02-26-mcp-session6-walkthrough.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/05j-mcp-discovery.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/mcp-tool-index.md`
- Constraints:
  - Review-only workflow (no silent fixes)
  - Findings-first reporting
  - Validate against actual file state, not artifact claims

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder (optional, not used)
- Optional roles: researcher, guardrail

## Coder Output

- Changed files: `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-session6-plan-critical-review.md`
- Design notes: No product/doc implementation changes performed; review-only handoff created.
- Commands run:
  - Session discipline/context: `pomera_diagnose`, `pomera_notes search "Zorivest"`, `Get-Content -Raw SOUL.md`, `Get-Content -Raw .agent/context/current-focus.md`, `Get-Content -Raw .agent/context/known-issues.md`
  - Artifact reads: `Get-Content -Raw` for workflow, Session 6 plan, Session 6 walkthrough, prior session review handoffs
  - Evidence sweeps: `git status --short -- docs/build-plan`, `git diff -- docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05j-mcp-discovery.md`, `rg -n` checks for PTC/GraphQL/cross-refs/residual `.agent` links
  - Verification replay: executed the exact Session 6 PowerShell verification block from the plan
  - Deterministic checks: heading/annotation checks for analytics tool count and `readOnlyHint` values in `05c`
- Results:
  - Session 6 presence checks all pass as documented (content exists)
  - Critical contract inconsistency found between PTC eligibility rules and current annotations

## Tester Output

- Commands run:
  - `git status --short -- docs/build-plan`
  - `git diff -- docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05j-mcp-discovery.md`
  - `rg -n -i "Programmatic Tool Calling|\bPTC\b|allowed_callers|code_execution|GraphQL|query_analytics|Deferred" docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05j-mcp-discovery.md`
  - `rg -n "05j-mcp-discovery|05c-mcp-trade-analytics" docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05j-mcp-discovery.md`
  - Replayed Session 6 plan verification block (`Select-String` counts + cross-ref assertions)
  - `rg -n "\.agent/context/handoffs" docs/build-plan`
  - Targeted line-state inspection for:
    - `docs/build-plan/05c-mcp-trade-analytics.md` (analytics section + PTC appendix)
    - `docs/build-plan/05j-mcp-discovery.md` (PTC section)
    - `docs/build-plan/05-mcp-server.md` (client mode mapping / adaptive patterns)
  - Deterministic analytics tool count check in `05c` (`## Analytics Tools` to `## Planned Tools`)
- Pass/fail matrix:
  - Session 6 claimed additions exist in `05c` and `05j`: **PASS**
  - Session 6 plan verification script result (5/5): **PASS** (reproduced exactly)
  - PTC eligibility consistency across `05c` and `05j`: **FAIL**
  - Internal reference quality in `05j` PTC section: **FAIL**
  - Documentation portability check (`docs/build-plan` linking to `.agent/context/handoffs`): **FAIL** (hits found in `05c`)
- Repro notes:
  - `git diff` for `05c`/`05j` is not useful in this worktree because these files are currently untracked; direct file-state checks were used.
- Coverage/test gaps:
  - Session 6 verification does not assert per-tool eligibility rules (it only checks phrase counts).
  - Verification does not validate consistency with shared client-detection contracts in `05-mcp-server.md`.
- Evidence bundle location:
  - Inline terminal outputs from this review session
- FAIL_TO_PASS / PASS_TO_PASS result: N/A (review-only)
- Mutation score: N/A
- Contract verification status: **Partial pass** (presence checks pass; consistency checks fail)

## Reviewer Output

- Findings by severity:
  - **High:** PTC eligibility rules are internally contradictory across Session 6 target files. `05j` states PTC annotation is added to all `trade-analytics` tools with `readOnlyHint: true` (`docs/build-plan/05j-mcp-discovery.md:381`) and also says "All 12 analytics tools" receive `allowed_callers` (`docs/build-plan/05j-mcp-discovery.md:385`). In `05c`, one of those 12 analytics tools (`enrich_trade_excursion`) is explicitly marked `readOnlyHint: false` (`docs/build-plan/05c-mcp-trade-analytics.md:267`), while the PTC appendix still claims all analytics tools are routed (`docs/build-plan/05c-mcp-trade-analytics.md:728`, `docs/build-plan/05c-mcp-trade-analytics.md:732`, `docs/build-plan/05c-mcp-trade-analytics.md:751`). This leaves implementation behavior ambiguous for at least one tool.
  - **Medium:** The new `05j` PTC section includes a broken/ambiguous intra-file reference. It says adaptive detection is "above" (`docs/build-plan/05j-mcp-discovery.md:376`), but this file has no adaptive-client-detection section before the PTC section (nearest prior top-level sections are `## Vitest Tests` and `## Toolset Registry` at `docs/build-plan/05j-mcp-discovery.md:253`, `docs/build-plan/05j-mcp-discovery.md:327`).
  - **Medium:** Session 6 verification is too weak to catch semantic regressions. The plan checks only keyword counts and cross-ref counts (`.agent/context/handoffs/2026-02-26-mcp-session6-plan.md:45`-`.agent/context/handoffs/2026-02-26-mcp-session6-plan.md:65`) and walkthrough reports 5/5 PASS from those counts (`.agent/context/handoffs/2026-02-26-mcp-session6-walkthrough.md:11`-`.agent/context/handoffs/2026-02-26-mcp-session6-walkthrough.md:19`), yet the eligibility contradiction above still passes.
  - **Low:** `docs/build-plan/05c-mcp-trade-analytics.md` now links directly to an internal handoff artifact (`docs/build-plan/05c-mcp-trade-analytics.md:726`, `docs/build-plan/05c-mcp-trade-analytics.md:773`). This reduces documentation portability and creates brittle dependencies on session-specific `.agent` content.
- Open questions:
  - Should `enrich_trade_excursion` be considered PTC-routable despite `readOnlyHint: false`, or should PTC be restricted to a strict read-only subset?
  - Should the authoritative PTC eligibility rule be "12 analytics tools" or "readOnlyHint=true tools only"?
  - Do we want build-plan docs to reference `.agent/context/handoffs/*`, or should those references move to stable docs under `docs/`?
- Verdict:
  - **changes_required**
- Residual risk:
  - Medium risk of implementation drift and unsafe assumptions if teams follow Session 6 artifacts without resolving PTC eligibility and verification rigor.
- Anti-deferral scan result:
  - Required follow-up is contained and actionable: reconcile the PTC eligibility contract, fix `05j` reference wording, and tighten verification to tool-level assertions.

## Guardrail Output (If Required)

- Safety checks: Not required (docs review only)
- Blocking risks: None runtime-related
- Verdict: N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Session 6 critical review completed against actual `docs/build-plan` file state; changes required.
- Next steps:
  - Reconcile PTC eligibility criteria between `05c` and `05j` (single authoritative rule)
  - Replace count-only verification with per-tool eligibility checks
  - Decide whether to keep or remove `.agent` handoff links from build-plan docs
