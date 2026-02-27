# Task Handoff

## Task

- **Date:** 2026-02-27
- **Task slug:** docs-build-plan-mcp-spec-completion-critical-review
- **Owner role:** orchestrator
- **Scope:** Critical review of MCP spec-completion artifacts against live `docs/build-plan/*` state

## Inputs

- User request:
  - Review `docs/build-plan` using:
    - `.agent/workflows/critical-review-feedback.md`
    - `.agent/context/handoffs/2026-02-26-mcp-spec-completion-plan.md`
    - `.agent/context/handoffs/2026-02-26-mcp-spec-completion-walkthrough.md`
- Specs/docs referenced:
  - `SOUL.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `docs/build-plan/*` files in MCP + index + related GUI/API planning scope
- Constraints:
  - Review-only session (no silent fixes)
  - Findings-first output
  - Validate actual file state, not handoff claims alone

## Role Plan

1. orchestrator -> scope claims + target files
2. tester -> run deterministic claim/consistency sweeps
3. reviewer -> severity-ranked findings + verdict

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-spec-completion-critical-review.md` (this review handoff only)
- Design notes:
  - No product/docs fixes applied; review-only per workflow.
- Commands run:
  - None for implementation.
- Results:
  - No implementation changes.

## Tester Output

- Commands run:
  - `git status --short -- docs/build-plan`
  - `git diff -- docs/build-plan/{03-service-layer.md,04-rest-api.md,05a-mcp-zorivest-settings.md,05c-mcp-trade-analytics.md,05d-mcp-trade-planning.md,05f-mcp-accounts.md,05h-mcp-tax.md,mcp-tool-index.md,mcp-planned-readiness.md}`
  - `rg -n "\[(Planned|Future)\]" docs/build-plan -g "05*-mcp-*.md"`
  - `rg -n -C 1 "simulate_tax_impact|estimate_tax|find_wash_sales|get_tax_lots|get_quarterly_estimate|record_quarterly_tax_payment|harvest_losses|get_ytd_tax_summary|create_report|get_report_for_trade|create_trade_plan|get_account_review_checklist|get_log_settings|update_log_level" docs/build-plan -g "05*-mcp-*.md"`
  - `rg -n "4\.9|Tax Routes|/api/v1/tax/|/api/v1/trades/\{id\}/report|/api/v1/trade-plans" docs/build-plan/04-rest-api.md`
  - `rg -n "TaxService|ReportService|TradePlanService|simulate_impact|estimate\(|find_wash_sales|get_lots|quarterly_estimate|record_payment|harvest_scan|ytd_summary|get_for_trade|create\(" docs/build-plan/03-service-layer.md`
  - `rg -n "POST /api/v1/plans|/api/v1/trade-plans|/api/v1/trades/\{id\}/report" docs/build-plan`
  - `rg -n "quarterly_estimate|get_quarterly_estimate" docs/build-plan/build-priority-matrix.md docs/build-plan/05h-mcp-tax.md docs/build-plan/mcp-tool-index.md docs/build-plan/mcp-planned-readiness.md`
  - `rg -n "🔶|📋" docs/build-plan/input-index.md docs/build-plan/output-index.md docs/build-plan/gui-actions-index.md`
  - `rg -n "not yet specified|\bplanned\b|\bfuture\b" docs/build-plan/05a-mcp-zorivest-settings.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05d-mcp-trade-planning.md docs/build-plan/05f-mcp-accounts.md docs/build-plan/05h-mcp-tax.md`
  - `rg -n "#### Annotations" docs/build-plan -g "05?-mcp-*.md"`
- Pass/fail matrix:
  - Claim: all promoted tools now have `[Specified]` headers in category files -> **PASS**
  - Claim: planned/future status headers removed -> **PASS**
  - Claim: promoted REST/service contracts exist in `04-rest-api.md` and `03-service-layer.md` -> **PASS**
  - Claim: cross-cutting index/status updates complete -> **FAIL**
  - Cross-file consistency (route names/methods/aliases) -> **FAIL**
  - Verification robustness in walkthrough artifact -> **FAIL**
- Repro failures:
  - Multiple contradictions listed in reviewer findings (below), reproducible via `rg` line checks.
- Coverage/test gaps:
  - No automated markdown link/anchor checker run; checks were targeted grep + direct line reads.
- Evidence bundle location:
  - This handoff + command transcript from current session.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - `FAIL_TO_PASS`: not executed (review-only)
  - `PASS_TO_PASS`: not executed (review-only)
- Mutation score:
  - N/A (docs review)
- Contract verification status:
  - **Failed** (inconsistencies remain across MCP category files, indexes, and related planning docs)

## Reviewer Output

- Findings by severity:

  - **High** — Contradictory tool contract state remains in files marked as fully specified  
    - `docs/build-plan/05h-mcp-tax.md:5` still says all 8 tools are planned, while every tool header is `[Specified]`.  
    - `docs/build-plan/05c-mcp-trade-analytics.md:569` section still titled `## Planned Tools` for `create_report`/`get_report_for_trade`.  
    - `docs/build-plan/05d-mcp-trade-planning.md:58` and `docs/build-plan/05f-mcp-accounts.md:233` still carry `DRAFT — Planned tool` comments on `[Specified]` tools.  
    - This conflicts with walkthrough claim: "68/68 tools fully specified".

  - **High** — Explicit REST dependency statements are incorrect in promoted tool specs  
    - `docs/build-plan/05h-mcp-tax.md:208` declares `get_tax_lots` dependency as `POST /api/v1/tax/lots`.  
    - Canonical API spec is `GET /api/v1/tax/lots` at `docs/build-plan/04-rest-api.md:970`.  
    - `docs/build-plan/mcp-planned-readiness.md:108` and `docs/build-plan/mcp-tool-index.md:76` both state GET, so category spec is internally inconsistent.

  - **High** — "Not yet specified" residuals contradict current API state  
    - `docs/build-plan/05c-mcp-trade-analytics.md:617` claims report route is not yet specified; route exists at `docs/build-plan/04-rest-api.md:128` and `:134`.  
    - `docs/build-plan/05d-mcp-trade-planning.md:99` claims trade plan route is not yet specified; route exists at `docs/build-plan/04-rest-api.md:153` and `:167`.

  - **High** — Batch 5 cross-cutting update claim is not true in current docs state  
    - `docs/build-plan/mcp-planned-readiness.md:15` says index entries were upgraded from 🔶/📋 to ✅.  
    - Counterexamples remain:
      - `docs/build-plan/input-index.md:516`, `:517`, `:518` (`simulate_tax_impact`, `harvest_losses`, `create_trade_plan`) still 📋/🔶.
      - `docs/build-plan/output-index.md:139` (`harvest_losses`) still 📋.
      - `docs/build-plan/gui-actions-index.md:72` (`create_trade_plan`) still 🔶.

  - **Medium** — Route/alias drift remains across downstream planning docs  
    - Trade-plan endpoint drift:
      - Canonical: `/api/v1/trade-plans` (`docs/build-plan/04-rest-api.md:153`).
      - Still documented as `/api/v1/plans` in `docs/build-plan/gui-actions-index.md:72` and `docs/build-plan/06c-gui-planning.md:90`.
    - Tax alias drift:
      - `docs/build-plan/build-priority-matrix.md:246` still lists `quarterly_estimate` and only 7 tools (missing `record_quarterly_tax_payment`).
      - Canonical tool is `get_quarterly_estimate` in `docs/build-plan/05h-mcp-tax.md:212` and `docs/build-plan/mcp-tool-index.md:77`.

  - **Low** — Readiness metrics are stale/internally inconsistent  
    - `docs/build-plan/mcp-planned-readiness.md:163` says total annotation blocks = 68.  
    - Current count in category files is 69 (`rg -n "#### Annotations" docs/build-plan -g "05?-mcp-*.md"`), so summary metrics are stale.

- Open questions:
  - Should `input-index.md` / `output-index.md` / `gui-actions-index.md` status icons represent **specification completeness** or **implementation completion**?  
    - If implementation-progress oriented, `mcp-planned-readiness.md:15` should be rewritten to avoid claiming these were upgraded as part of MCP spec completion.

- Verdict:
  - **changes_required**

- Residual risk:
  - If these inconsistencies remain, agents and implementers may select wrong endpoints/methods (`/plans` vs `/trade-plans`, POST vs GET) and over-trust completion status from walkthrough/readiness artifacts.

- Anti-deferral scan result:
  - No new TODO deferrals introduced in this session. Existing drift is concrete and reproducible.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed with reproducible evidence; no fixes applied.
- Next steps:
  1. Decide status semantics for index files (spec-complete vs implementation-complete).
  2. Patch high-severity contradictions in `05c/05d/05h` and route drifts in downstream index/planning docs.
  3. Re-run the same grep sweep and issue a follow-up validation handoff.
