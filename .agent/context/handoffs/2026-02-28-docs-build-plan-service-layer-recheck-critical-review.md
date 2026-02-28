# Task Handoff Template

## Task

- **Date:** 2026-02-28
- **Task slug:** docs-build-plan-service-layer-recheck-critical-review
- **Owner role:** orchestrator
- **Scope:** Review-only re-check of service-layer redesign consistency across `docs/build-plan` with focus on Phase 04 split integrity and cross-file contracts.

## Inputs

- User request: Re-check what issues still remain, specifically in relation to service layer, and process all `docs/build-plan` files for detailed critical feedback.
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/2026-02-28-service-layer-redesign-plan.md`
  - `.agent/context/handoffs/2026-02-28-service-layer-redesign-walkthrough.md`
  - `docs/build-plan/*.md`
- Constraints:
  - Review-first workflow (no silent fixes)
  - Findings must be severity-ranked with file/line evidence
  - Validate actual file state, not handoff claims alone

## Role Plan

1. orchestrator
2. coder
3. tester
4. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-28-docs-build-plan-service-layer-recheck-critical-review.md` (new review handoff)
- Design notes:
  - No product/docs fixes applied in this session.
  - Review-only deliverable.
- Commands run:
  - N/A (review-only; see Tester Output for evidence commands)
- Results:
  - No implementation changes.

## Tester Output

- Commands run:
  - `git status --short -- docs/build-plan`
  - `git diff -- docs/build-plan/03-service-layer.md docs/build-plan/01-domain-layer.md docs/build-plan/testing-strategy.md docs/build-plan/02-infrastructure.md docs/build-plan/dependency-manifest.md docs/build-plan/output-index.md`
  - `rg -n "ExpectancyService|DeduplicationService|BrokerImportService|PDFImportService|DrawdownService|SQNService|ExcursionService|PFOFAnalysisService|CostOfFreeService|StrategyBreakdownService|MistakeTrackingService|BankImportService|IdentifierResolverService|OptionsGroupingService|RoundTripService|ExecutionQualityService|TransactionLedgerService|BrokerAdapterService" docs/build-plan`
  - `rg -n "TradePlanService|TradeReportService|PortfolioService|DisplayService|AccountReviewService|WatchlistService|tradeplan_service|portfolio_service|display_service|account_review_service|watchlist_service|RoundTripService|DeduplicationService|BrokerAdapterService|PDFImportService|BankImportService|IdentifierResolverService|OptionsGroupingService|ExecutionQualityService|TransactionLedgerService|PFOFAnalysisService|CostOfFreeService|StrategyBreakdownService|ExpectancyService|DrawdownService|SQNService|ExcursionService|MistakeTrackingService|AIReviewService" docs/build-plan`
  - `rg -n "APIRouter\(|include_router\(|router = APIRouter|prefix=|tags=|app.include_router" docs/build-plan/04-rest-api.md docs/build-plan/04a-api-trades.md docs/build-plan/04b-api-accounts.md docs/build-plan/04c-api-auth.md docs/build-plan/04d-api-settings.md docs/build-plan/04e-api-analytics.md docs/build-plan/04f-api-tax.md docs/build-plan/04g-api-system.md`
  - `rg -n "@(\w+_router)\.(get|post|put|delete|patch)\(" docs/build-plan/04a-api-trades.md docs/build-plan/04b-api-accounts.md docs/build-plan/04c-api-auth.md docs/build-plan/04d-api-settings.md docs/build-plan/04e-api-analytics.md docs/build-plan/04f-api-tax.md docs/build-plan/04g-api-system.md`
  - `rg -n "get_expectancy_service|get_drawdown_service|get_eq_service|get_pfof_service|get_strategy_service|get_sqn_service|get_cost_service|get_ai_review_service|get_excursion_service|get_options_grouping_service|get_mistake_service|get_ledger_service|get_trade_plan_service|get_trade_report_service|get_round_trip_service" docs/build-plan/04a-api-trades.md docs/build-plan/04e-api-analytics.md`
  - `rg -n "identifiers/resolve|identifiers_router" docs/build-plan/04-rest-api.md docs/build-plan/04b-api-accounts.md docs/build-plan/05f-mcp-accounts.md`
  - `rg -n 'APIRouter\(prefix="/api/v1/backups|APIRouter\(prefix="/api/v1/config|backup_router|config_router|settings/resolved|settings/reset' docs/build-plan/02a-backup-restore.md`
  - `rg -n "backup_router|config_router|/api/v1/backups|/api/v1/config|/api/v1/settings/resolved|/api/v1/settings/reset" docs/build-plan/04-rest-api.md`
  - Custom deterministic parity scripts (PowerShell one-liners) comparing:
    - Route decorators in `04a`..`04g` vs route registry rows in `04-rest-api.md`
    - Delegated Phase 2A routes in `04d-api-settings.md` vs route registry in `04-rest-api.md`

- Pass/fail matrix:
  - DR-1 Claim-to-state match: **FAIL**
  - DR-2 Residual old terms: **FAIL** (remaining stale service reference)
  - DR-3 Downstream references updated: **FAIL**
  - DR-4 Verification robustness: **FAIL**
  - DR-5 Evidence auditability: **PASS** (commands reproducible)

- Repro failures:
  - `04-rest-api.md` states route registry is "every REST endpoint" and single source of truth, but parity sweep found **40 endpoints missing** from split route files plus **9 delegated Phase 2A routes missing** from registry.

- Coverage/test gaps:
  - No markdown link/anchor validator run; used deterministic grep + structural route parity checks instead.

- Evidence bundle location:
  - Inline command outputs in session + this handoff.

- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable (review-only).

- Mutation score:
  - Not applicable (review-only).

- Contract verification status:
  - **Failed** for Phase 04 route ownership contract and service-layer naming consistency.

## Reviewer Output

- Findings by severity:

  - **High — Phase 04 route registry is materially incomplete while claiming full canonical ownership.**
    - Evidence claim: `docs/build-plan/04-rest-api.md:132` states "every REST endpoint" and "single source of truth".
    - Evidence mismatch: parity sweep found `defined=78`, `registry=38`, `missing_after_param_normalization=40` endpoints from `04a`..`04g` not represented in the registry.
    - Example missing endpoints:
      - `docs/build-plan/04a-api-trades.md:124` `POST /api/v1/trades/{exec_id}/report`
      - `docs/build-plan/04a-api-trades.md:221` `POST /api/v1/trades/{exec_id}/journal-link`
      - `docs/build-plan/04e-api-analytics.md:61` `POST /api/v1/analytics/ai-review`
      - `docs/build-plan/04f-api-tax.md:64` `POST /api/v1/tax/estimate`
      - `docs/build-plan/04g-api-system.md:94` `PUT /api/v1/mcp-guard/config`

  - **High — Phase 2A delegated settings/config/backup endpoints are absent from the Phase 04 canonical registry.**
    - Delegated routes listed in `docs/build-plan/04d-api-settings.md:160-168`.
    - Parity sweep result: `delegated_rows=9`, `missing_in_04_registry=9`.
    - Upstream definitions exist in `docs/build-plan/02a-backup-restore.md:753-810` (`config_router`, `backup_router`), but `docs/build-plan/04-rest-api.md` contains no corresponding entries/imports.

  - **High — Identifier resolution endpoint is specified for MCP but lacks Phase 04 route definition/include contract.**
    - MCP uses it: `docs/build-plan/05f-mcp-accounts.md:76` (`fetchApi('/identifiers/resolve', ...)`).
    - Phase 04 only has a table mention: `docs/build-plan/04b-api-accounts.md:150`.
    - No `identifiers_router` definition/include in `04` split docs.

  - **Medium — Service-layer consolidation drift remains in API dependency names.**
    - Phase 03 consolidated services are defined in `docs/build-plan/03-service-layer.md:27-36`.
    - Split API still references pre-consolidation dependency names:
      - `docs/build-plan/04e-api-analytics.md:18,25,31,37,43,50,57,63,72,82,95,102,117` (e.g., `get_expectancy_service`, `get_drawdown_service`, `get_mistake_service`, `get_ledger_service`).
      - `docs/build-plan/04a-api-trades.md:177,223,274` (`get_trade_plan_service`, `get_trade_report_service`, `get_round_trip_service`).
      - `docs/build-plan/04b-api-accounts.md:75,80,85,101,106,112,118,141` (`get_broker_service`, `get_bank_service`, `get_pdf_service`).

  - **Medium — Residual stale service name in readiness tracking contradicts redesign decisions.**
    - `docs/build-plan/mcp-planned-readiness.md:56` still references `TradePlanService.create()`.
    - Redesign says trade plans are absorbed into `ReportService` (`docs/build-plan/03-service-layer.md:387`, `:699`).

  - **Low — Path parameter naming drift weakens deterministic contract matching.**
    - Registry uses `{id}` while owner files use specific keys:
      - `docs/build-plan/04-rest-api.md:139-143,149` vs `docs/build-plan/04a-api-trades.md:75,83,89,102,201` and `docs/build-plan/04b-api-accounts.md:79`.
    - This causes avoidable false mismatches in automated consistency checks.

- Open questions:
  - Should Phase 04’s top-level registry remain exhaustive (as currently claimed) or be intentionally reduced to "key routes only"? Current wording requires exhaustive coverage.
  - For service consolidation, should API DI names be normalized now (e.g., `get_analytics_service`, `get_report_service`, `get_import_service`) or explicitly documented as compatibility adapters?
  - Should `/identifiers/resolve` live under `accounts` routes, `market_data` routes, or a dedicated identifiers router?

- Verdict:
  - **changes_required**

- Residual risk:
  - Current docs can yield false confidence in implementation readiness and route ownership, especially for MCP tool-to-REST dependencies (reporting, tax estimate/wash sales, identifiers, settings/backup/config).

- Anti-deferral scan result:
  - Blocking documentation contract gaps identified; not safe to mark this area complete without registry/ownership reconciliation.

## Optimization proposal (minimal duplication):

- Keep one canonical machine-readable route manifest (method/path/owner/consumers), generate 04-rest-api table from it.
- Add one DI alias map section documenting consolidated service adapters (or rename all DI getters to consolidated names).
- Add a CI parity check: route decorators + delegated route tables must exactly match the canonical registry.

## Guardrail Output (If Required)

- Safety checks: N/A (docs-only review)
- Blocking risks: N/A
- Verdict: N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review completed with reproducible evidence; multiple high-severity consistency issues remain in the service-layer/Phase-04 contract surface.
- Next steps:
  - 1) Reconcile `04-rest-api.md` route registry with all `04a`..`04g` + delegated `04d/02a` endpoints.
  - 2) Resolve `resolve_identifiers` contract by adding explicit Phase 04 router definition/include and registry row.
  - 3) Normalize or explicitly alias DI/service naming across `04a/04b/04e` to match Phase 03 consolidation.
  - 4) Remove stale `TradePlanService` reference in `mcp-planned-readiness.md`.
