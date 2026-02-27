# Critical Review: docs/build-plan Alignment with Expansion Implementation Plan

## Scope
- Baseline plan: `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md`
- Reviewed target set: `docs/build-plan/*`
- Goal: validate whether current build-plan docs are aligned to the implementation-plan contracts.

## Executive Verdict
- Alignment is partial.
- Core domain/infrastructure/service additions are mostly present, but API/MCP/index/provider contracts are materially inconsistent and several mapped features are missing or incomplete.

## Findings (Severity-Ordered)

### Critical
1. REST API contract is internally inconsistent for expansion endpoints.
- Evidence:
  - Route summary claims `/sqn`, `/cost-of-free`, and `/import/pdf` (`docs/build-plan/04-rest-api.md:651`, `docs/build-plan/04-rest-api.md:654`).
  - Analytics stub block only defines expectancy/drawdown/execution-quality/pfof/strategy (`docs/build-plan/04-rest-api.md:685`-`docs/build-plan/04-rest-api.md:719`).
  - Import stub block only defines `/import/csv` (`docs/build-plan/04-rest-api.md:758`-`docs/build-plan/04-rest-api.md:767`).
  - Expansion summary line says "CSV/PDF import routes" but cites only `POST /import/csv` (`docs/build-plan/04-rest-api.md:826`).
- Impact: implementation teams cannot trust route contracts.
- Recommendation: unify summary tables, code stubs, and expansion bullets into a single canonical endpoint list.

2. Market-data expansion provider updates from the plan are not applied.
- Evidence:
  - Implementation plan requires OpenFIGI, Alpaca, Tradier additions (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:209`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:218`).
  - Current provider registry still lists legacy 9-provider set only (`docs/build-plan/08-market-data.md:216`-`docs/build-plan/08-market-data.md:302`).
  - No `OpenFIGI`, `Alpaca`, or `Tradier` references were found in `docs/build-plan/08-market-data.md`.
- Impact: identifier resolution and broker-direct integrations have no provider-level contract in Phase 8 docs.
- Recommendation: either apply those provider contracts in Phase 8 or explicitly move ownership out of Phase 8 in the implementation plan.

### High
3. MCP tool contract has drifted from implementation-plan names and coverage.
- Evidence:
  - Implementation plan tool list includes `sync_broker_account`, `get_excursion_metrics`, `ai_review_trade`, and banking mutation/list tools (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:158`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:175`).
  - Current MCP registry uses renamed tools (`sync_broker`, `enrich_trade_excursion`, `score_execution_quality`, `get_expectancy_metrics`, `simulate_drawdown`) and omits `ai_review_trade`, `update_bank_balance`, `submit_bank_transactions`, `list_bank_accounts` (`docs/build-plan/05-mcp-server.md:1264`-`docs/build-plan/05-mcp-server.md:1280`, `docs/build-plan/05-mcp-server.md:1296`-`docs/build-plan/05-mcp-server.md:1501`).
- Impact: route/tool parity and index references become non-deterministic.
- Recommendation: publish a single canonical MCP tool contract and update all indexes against it.

4. Expansion feature coverage gaps remain in indexes and matrix.
- Evidence:
  - Implementation plan expects explicit index additions for expansion outputs/inputs and priority rows (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:231`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:306`).
  - `output-index.md` expansion section includes many outputs but omits SQN/monthly calendar/cost-of-free outputs (`docs/build-plan/output-index.md:311`-`docs/build-plan/output-index.md:325`).
  - `build-priority-matrix.md` has P2.75 expansion rows (`docs/build-plan/build-priority-matrix.md:126`-`docs/build-plan/build-priority-matrix.md:167`) but does not include explicit entries for Bidirectional Trade-Journal linking, SQN, Monthly P&L Calendar, or Cost of Free.
  - `input-index.md` does not contain the planned expansion input groups/field contracts (for example `broker_id`, `broker_hint`, `mistake_category`, `id_type`, `id_value` are absent).
- Impact: planning artifacts disagree on what is actually in-scope and testable.
- Recommendation: run a feature-by-feature index reconciliation pass keyed to expansion features 1-26.

5. GUI alignment is incomplete for planned expansion sections.
- Evidence:
  - `06b-gui-trades.md` includes excursion/fees/mistakes/round-trip components (`docs/build-plan/06b-gui-trades.md:356`, `docs/build-plan/06b-gui-trades.md:404`, `docs/build-plan/06b-gui-trades.md:429`, `docs/build-plan/06b-gui-trades.md:473`-`docs/build-plan/06b-gui-trades.md:478`) but lacks planned sections for Expectancy Dashboard, Monthly P&L Calendar, and Strategy Breakdown.
  - `06d-gui-accounts.md` includes bank import panel and broker sync enhancements (`docs/build-plan/06d-gui-accounts.md:206`-`docs/build-plan/06d-gui-accounts.md:241`, `docs/build-plan/06d-gui-accounts.md:268`-`docs/build-plan/06d-gui-accounts.md:270`) but does not define manual column mapping workflow or manual transaction entry contract from the implementation plan.
- Impact: frontend implementation scope is ambiguous.
- Recommendation: add explicit component contracts for every mapped GUI feature in the implementation plan.

### Medium
6. Domain/dependency details are only partially aligned with the implementation plan.
- Evidence:
  - `01-domain-layer.md` has many expansion enums/ports (`docs/build-plan/01-domain-layer.md:190`-`docs/build-plan/01-domain-layer.md:260`, `docs/build-plan/01-domain-layer.md:489`-`docs/build-plan/01-domain-layer.md:508`) but no `CostBasisMethod` enum called for by the plan.
  - `domain-model-reference.md` adds `institution` on Account (`docs/build-plan/domain-model-reference.md:21`) but not `sub_accounts`/`balance_source` from plan text.
  - `dependency-manifest.md` expansion deps include `ofxtools`, `quiffen`, `chardet`, `lxml`, `pdfplumber`, `alpaca-py` (`docs/build-plan/dependency-manifest.md:88`-`docs/build-plan/dependency-manifest.md:97`) but omit `tabula-py` and `pikepdf` listed in the implementation plan (`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:314`-`_inspiration/import_research/Build Plan Expansion - Implementation Plan.md:323`).
- Impact: integration and parser capability assumptions can diverge from dependency reality.
- Recommendation: normalize dependency and domain deltas in one authoritative checklist.

## Positive Notes
- Domain/service/infrastructure expansion primitives are largely present (`RoundTrip`, `IdentifierResolver`, `Deduplication`, `Excursion`, `OptionsGrouping`, `TransactionLedger`, `Mistake`, `BankImport`).
- Expansion sections are at least linked in core docs, which makes reconciliation feasible.

## Recommended Remediation Order
1. Fix REST summary/stub mismatches in `04-rest-api.md`.
2. Reconcile MCP tool names and missing tool coverage in `05-mcp-server.md`.
3. Decide Phase-8 ownership for OpenFIGI/Alpaca/Tradier and update `08-market-data.md`.
4. Run index/matrix parity update for features 1-26.
5. Close remaining GUI/domain/dependency deltas.
