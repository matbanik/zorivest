# Task Handoff Template

## Task

- **Date:** 2026-02-27
- **Task slug:** build-plan-03-service-layer-wholeness-critical-review
- **Owner role:** orchestrator
- **Scope:** critical review of `docs/build-plan/03-service-layer.md` and cross-file completeness checks for `docs/build-plan/*`

## Inputs

- User request:
  - Review `docs/build-plan/03-service-layer.md`
  - Identify what is missing from `docs/build-plan` to be considered whole
  - Use workflow `.agent/workflows/critical-review-feedback.md`
  - Put feedback results into handoffs
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/TEMPLATE.md`
  - `AGENTS.md`
  - `docs/build-plan/03-service-layer.md`
  - Related build-plan index and phase docs (`04`, `05*`, `06*`, `input-index`, `output-index`, `gui-actions-index`, `mcp-tool-index`, `mcp-planned-readiness`, `build-priority-matrix`)
- Constraints:
  - Review-only session, no product implementation fixes
  - Findings-first output with severity and file/line references
  - Verify actual `docs/build-plan` file state, not handoff claims alone

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder (not used; fixes not requested)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-27-build-plan-03-service-layer-wholeness-critical-review.md` (this review handoff)
- Design notes:
  - No product doc edits applied.
  - Review-only deliverable per workflow.
- Commands run:
  - N/A (no implementation changes)
- Results:
  - No code/docs fixed in this session.

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `pomera_notes.search("Zorivest")`
  - `rg --files docs/build-plan`
  - `rg -n "TODO|TBD|FIXME|TKTK|XXX|to be decided|open question|placeholder|\[\?\]" docs/build-plan`
  - `Get-Content -Raw docs/build-plan/03-service-layer.md`
  - `Get-Content -Raw docs/build-plan/00-overview.md`
  - `Get-Content -Raw docs/build-plan/input-index.md`
  - `Get-Content -Raw docs/build-plan/output-index.md`
  - `rg -n "DeduplicationService|BrokerAdapterService|RoundTripService|ExcursionService|ExecutionQualityService|PFOFAnalysisService|ExpectancyService|DrawdownService|StrategyBreakdownService|IdentifierResolverService|OptionsGroupingService|TransactionLedgerService|AIReviewService|MistakeTrackingService|BankImportService|SQNService|CostOfFreeService|TradeReportService|TaxService|TradePlanService|ReportService" docs/build-plan`
  - `rg -n "/analytics/expectancy|/analytics/drawdown|/analytics/excursion|/fees/summary|/analytics/execution-quality|/analytics/pfof-report|/analytics/strategy-breakdown|/mistakes/summary|/round-trips|/analytics/options-strategy|/banking/import|/identifiers/resolve|/brokers/\{id\}/sync|/analytics/sqn|/analytics/cost-of-free" docs/build-plan/04-rest-api.md docs/build-plan/05-mcp-server.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05d-mcp-trade-planning.md docs/build-plan/05h-mcp-tax.md`
  - Link integrity check across markdown links in `docs/build-plan/*` (outside fenced code)
  - `Get-Content -Raw docs/build-plan/mcp-planned-readiness.md`
  - `Get-Content -Raw docs/build-plan/mcp-tool-index.md`
  - `Get-Content -Raw docs/build-plan/build-priority-matrix.md`
  - `mcp__pomera__pomera_diagnose`
  - `git status --short -- docs/build-plan`
  - `git diff -- docs/build-plan/03-service-layer.md docs/build-plan/04-rest-api.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05f-mcp-accounts.md docs/build-plan/gui-actions-index.md docs/build-plan/input-index.md docs/build-plan/output-index.md`
  - `rg -n "start_account_review|get_account_review_checklist|/api/v1/reports|/api/v1/trades/\{exec_id\}/report|/api/v1/accounts|/api/v1/calculator/position-size|/mcp-guard/config|/mcp-guard$|PUT /api/v1/mcp-guard" docs/build-plan`
  - `rg -n "\[Specified\]|planned|not yet implemented|Status: ✅ Complete|formerly-Planned" docs/build-plan/mcp-planned-readiness.md docs/build-plan/05c-mcp-trade-analytics.md`
- Pass/fail matrix:
  - DR-1 Claim-to-state match: **Fail** (multiple cross-file contract drifts found)
  - DR-2 Residual old/variant references: **Fail** (legacy/contradictory terms and endpoint shapes remain)
  - DR-3 Downstream reference consistency: **Fail** (indexes and phase docs disagree on route/tool contracts)
  - DR-4 Verification robustness: **Fail** (some status docs declare completion while component docs still flag planned/not-implemented)
  - DR-5 Evidence auditability: **Pass** (reproducible `rg`/`git`/file-read sweeps captured)
- Repro failures:
  - Report endpoint shape mismatch (`/api/v1/reports` vs `/api/v1/trades/{exec_id}/report`)
  - MCP account-review tool name mismatch (`start_account_review` vs `get_account_review_checklist`)
  - `03-service-layer.md` outputs list services without matching class stubs
  - `04-rest-api.md` claims accounts/calculator routes in outputs, but route definition sections do not specify them
  - `05c-mcp-trade-analytics.md` marks report tools `[Specified]` while also saying "planned/not yet implemented"
- Coverage/test gaps:
  - No dedicated e2e test snippets for expansion analytics/import routes despite route claims
  - Service-layer tests listed do not cover all expansion services referenced in outputs
- Evidence bundle location:
  - Inline command evidence in this handoff; source docs under `docs/build-plan/*`
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable (docs-only review session)
- Mutation score:
  - Not applicable
- Contract verification status:
  - **changes_required**

## Reviewer Output

- Findings by severity:
  - **High**: `04-rest-api.md` output claims accounts + calculator routes are delivered, but no explicit route definitions exist in its route sections.
    - Evidence: `docs/build-plan/04-rest-api.md:1077` vs section headers at `:13`, `:234`, `:701`, `:895`
    - Downstream dependencies expecting those routes:
      - `docs/build-plan/06d-gui-accounts.md:73-79`
      - `docs/build-plan/06h-gui-calculator.md:348-349`
      - `docs/build-plan/gui-actions-index.md:96-98`
  - **High**: Trade report REST contract drift across build-plan files.
    - API doc uses trade-scoped report route:
      - `docs/build-plan/04-rest-api.md:128-140`
    - GUI Trades expects trade-scoped POST/GET/PUT:
      - `docs/build-plan/06b-gui-trades.md:340-342`
    - GUI actions index uses separate `/api/v1/reports` CRUD and marks it defined:
      - `docs/build-plan/gui-actions-index.md:62-64`
  - **High**: Service-layer outputs claim expansion services not represented by explicit service stubs in `03-service-layer.md`.
    - Listed only in output bullets:
      - `docs/build-plan/03-service-layer.md:358-360`
    - Stub class blocks stop earlier (`RoundTripService`...`BankImportService`):
      - `docs/build-plan/03-service-layer.md:157-225`
  - **High**: Import contract gap between API routes and service-layer contract.
    - API defines broker CSV/PDF import routes:
      - `docs/build-plan/04-rest-api.md:852-864`
    - Service layer defines `BankImportService` only:
      - `docs/build-plan/03-service-layer.md:219-224`
    - Testing strategy expects dedicated `PDFImportService`:
      - `docs/build-plan/testing-strategy.md:254`
  - **Medium**: MCP account-review tool naming inconsistency.
    - GUI/domain references `start_account_review`:
      - `docs/build-plan/06d-gui-accounts.md:85`
      - `docs/build-plan/06d-gui-accounts.md:161`
      - `docs/build-plan/domain-model-reference.md:205`
    - MCP spec/index define `get_account_review_checklist`:
      - `docs/build-plan/05f-mcp-accounts.md:216`
      - `docs/build-plan/mcp-tool-index.md:72`
  - **Medium**: Internal contradiction in MCP analytics doc status text.
    - Same file marks report tools `[Specified]`:
      - `docs/build-plan/05c-mcp-trade-analytics.md:571`
      - `docs/build-plan/05c-mcp-trade-analytics.md:622`
    - Later says planned/not implemented:
      - `docs/build-plan/05c-mcp-trade-analytics.md:715`
      - `docs/build-plan/05c-mcp-trade-analytics.md:768`
    - Conflicts with readiness doc declaring all formerly planned tools complete:
      - `docs/build-plan/mcp-planned-readiness.md:3-5`
  - **Medium**: Indexes still show large non-whole status while several tools/routes are marked specified elsewhere.
    - Inputs summary:
      - `docs/build-plan/input-index.md:700-701`
    - Outputs summary:
      - `docs/build-plan/output-index.md:377-378`
    - GUI actions summary:
      - `docs/build-plan/gui-actions-index.md:315-316`
  - **Low**: Minor snippet validity issue in REST API docs.
    - `Literal` used in request schema without import in shown snippet:
      - use: `docs/build-plan/04-rest-api.md:121-123`
      - imports shown: `docs/build-plan/04-rest-api.md:18-25`
- Open questions:
  - Should report CRUD be canonicalized as trade-scoped only (`/trades/{exec_id}/report`) or split into standalone `/reports` resources?
  - Are account/calculator routes intentionally omitted from `04-rest-api.md` route sections because they are documented elsewhere, or was this an incomplete phase merge?
  - Should `start_account_review` remain as an alias for backward compatibility, or be fully replaced with `get_account_review_checklist` across docs?
- Verdict:
  - **changes_required**
- Residual risk:
  - Proceeding without contract consolidation risks implementation drift across API, MCP, GUI, and test planning; teams could build incompatible surfaces while all docs appear individually "reasonable".
- Anti-deferral scan result:
  - Passed for this handoff: findings include concrete file/line references and explicit follow-up actions, not generic deferments.

## Guardrail Output (If Required)

- Safety checks:
  - Not required (docs-only critical review)
- Blocking risks:
  - None beyond documented contract inconsistencies
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review complete; handoff recorded; no fixes applied.
- Next steps:
  - 1) Canonicalize route/tool contracts (reports, accounts/calculator, MCP account-review naming).
  - 2) Reconcile `03` service contracts with `04/05` routes/tools (add missing service specs or downgrade claims).
  - 3) Synchronize index status rows (`input-index`, `output-index`, `gui-actions-index`) after canonical contract decisions.

