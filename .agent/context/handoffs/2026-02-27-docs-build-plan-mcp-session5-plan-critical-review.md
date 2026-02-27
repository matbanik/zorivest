# Task Handoff

## Task

- **Date:** 2026-02-27
- **Task slug:** docs-build-plan-mcp-session5-plan-critical-review
- **Owner role:** orchestrator
- **Scope:** Critical review of Session 5 artifacts against actual `docs/build-plan` file state

## Inputs

- User request: Review `.agent/workflows/critical-review-feedback.md`, `.agent/context/handoffs/2026-02-26-mcp-session5-plan.md`, and `.agent/context/handoffs/2026-02-26-mcp-session5-walkthrough.md` for `docs/build-plan` files.
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/2026-02-26-mcp-session5-plan.md`
  - `.agent/context/handoffs/2026-02-26-mcp-session5-walkthrough.md`
  - `docs/build-plan/05a-mcp-zorivest-settings.md`
  - `docs/build-plan/05c-mcp-trade-analytics.md`
  - `docs/build-plan/05g-mcp-scheduling.md`
  - `docs/build-plan/05j-mcp-discovery.md`
- Constraints:
  - Review-only task (no product/doc fixes in this session)
  - Findings-first output with file/line evidence
  - Validate real file state, not just handoff claims

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder (not invoked; review-only)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-session5-plan-critical-review.md` (this review handoff)
- Design notes:
  - No product changes; review-only.
- Commands run:
  - N/A
- Results:
  - N/A

## Tester Output

- Commands run:
  - `git status --short -- docs/build-plan`
  - `git diff -- docs/build-plan/05a-mcp-zorivest-settings.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05g-mcp-scheduling.md`
  - `rg -n -i "manage_settings|manage_policy|query_trade_analytics|constrained client|constrained-client|composite bifurcation|discrete tools remain canonical|emergency_stop|emergency_unlock" docs/build-plan/05a-mcp-zorivest-settings.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05g-mcp-scheduling.md`
  - `rg -n "05j-mcp-discovery\.md|Pattern F|PTC routing|cross-ref|cross reference|Cross-reference" docs/build-plan/05a-mcp-zorivest-settings.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05g-mcp-scheduling.md`
  - `rg -n "get_run_history|get_pipeline_history" docs/build-plan/05g-mcp-scheduling.md docs/build-plan/05-mcp-server.md docs/build-plan/05j-mcp-discovery.md`
  - `rg -n "record_trade" docs/build-plan`
  - metric enum extraction script on `05c-mcp-trade-analytics.md` (`metric_count=12`)
  - Session 5 verification script from plan (`PASS` outputs reproduced)
- Pass/fail matrix:
  - Claimed insertions exist in 05a/05g/05c: **PASS**
  - 05j cross-reference links present in all three files: **PASS**
  - Contract consistency checks (tool names/counts): **FAIL**
  - Verification robustness (detects semantic drift): **FAIL**
- Repro failures:
  - `docs/build-plan/05g-mcp-scheduling.md:287` references `get_run_history`, but canonical tool is `get_pipeline_history` at `:248` and `:254`.
  - `docs/build-plan/05c-mcp-trade-analytics.md:677` claims 14 analytics endpoints, but metric enum at `:685-:689` contains 12 entries.
  - `docs/build-plan/05c-mcp-trade-analytics.md:713` references `record_trade`, but defined tool is `create_trade` at `:9`.
- Coverage/test gaps:
  - Verification in Session 5 artifacts relies on phrase/count presence, not semantic contract checks.
- Evidence bundle location:
  - Command outputs in this session terminal transcript.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - PASS_TO_PASS checks reproduced from artifact.
  - FAIL_TO_PASS not applicable (review-only).
- Mutation score:
  - N/A (docs review).
- Contract verification status:
  - **Failed** (3 contract drifts found).

## Reviewer Output

- Findings by severity:
  - **High:** Wrong operational tool name in CRUD-consolidation note.
    - Evidence: `docs/build-plan/05g-mcp-scheduling.md:287` uses `get_run_history`; actual tool is `get_pipeline_history` (`:248`, `:254`).
    - Also reflected in source artifact at `.agent/context/handoffs/2026-02-26-mcp-session5-plan.md:28`.
    - Impact: implementers can wire/validate against a non-existent MCP tool name.
  - **High:** Composite endpoint count is internally inconsistent.
    - Evidence: `docs/build-plan/05c-mcp-trade-analytics.md:677` says “14 analytics endpoints” but enum at `:685-:689` has 12 metrics (script result: `metric_count=12`).
    - Claim repeated in artifacts: `.agent/context/handoffs/2026-02-26-mcp-session5-plan.md:38`, `.agent/context/handoffs/2026-02-26-mcp-session5-walkthrough.md:9`.
    - Impact: ambiguous implementation/test target for constrained-client composite routing.
  - **High:** Non-existent tool referenced in “What stays separate” table.
    - Evidence: `docs/build-plan/05c-mcp-trade-analytics.md:713` references `record_trade`; only defined write tool is `create_trade` at `:9`. `record_trade` appears nowhere else in `docs/build-plan` (`rg` single hit).
    - Impact: contract drift and onboarding confusion during implementation.
  - **Medium:** Verification evidence is too weak to catch semantic regressions.
    - Evidence: Session 5 verification commands in `.agent/context/handoffs/2026-02-26-mcp-session5-plan.md:56-74` all pass even while the three issues above remain; walkthrough reports `9/9 PASS` at `.agent/context/handoffs/2026-02-26-mcp-session5-walkthrough.md:13-25`.
    - Impact: false confidence and regression leakage into subsequent sessions.

- Open questions:
  - Should `query_trade_analytics` target **12** metrics (current enum) or **14** (artifact claim)? Pick one authoritative number and align all docs.
  - Should composite metric names mirror tool names (`ai_review_trade`, `detect_options_strategy`) or stay abstract (`ai_review`, `detect_strategy`)?

- Verdict:
  - **changes_required**

- Residual risk:
  - Without corrections, Session 6+ work can propagate invalid tool names and incorrect composite coverage assumptions into implementation and tests.

- Anti-deferral scan result:
  - Findings are concrete, reproducible, and bounded to three files plus two artifact docs; no hidden blockers.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for docs-only review.
- Blocking risks:
  - None beyond documented findings.
- Verdict:
  - N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review completed; critical feedback captured with evidence.
- Next steps:
  - Correct the three high-severity contract drifts in `05c`/`05g`.
  - Strengthen Session 5 verification checks to validate tool-name existence and metric-count consistency.
