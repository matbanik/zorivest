# Task Handoff: Service Layer Recheck Corrections

## Task

- **Date:** 2026-02-28
- **Task slug:** docs-build-plan-service-layer-recheck-corrections
- **Owner role:** coder
- **Scope:** Fix all 6 findings from the service-layer recheck critical review.
- **Source review:** [2026-02-28-docs-build-plan-service-layer-recheck-critical-review.md](2026-02-28-docs-build-plan-service-layer-recheck-critical-review.md)

## Verified Findings (6/6 confirmed)

| # | Severity | Summary | Status |
|---|----------|---------|--------|
| F1 | High | Route registry missing ~40 endpoints from 04a-04g | ✅ Fixed |
| F2 | High | 9 Phase 2A delegated routes missing from registry | ✅ Fixed |
| F3 | High | `/identifiers/resolve` lacks router definition | ✅ Fixed |
| F4 | Medium | 22 stale DI names across API split files | ✅ Fixed |
| F5 | Medium | Stale `TradePlanService.create()` in readiness tracking | ✅ Fixed |
| F6 | Low | Path param naming drift (`{id}` vs `{exec_id}`) | ✅ Fixed |

## Design Decisions Made

1. **Registry scope**: Keep exhaustive — single source of truth claim preserved.
2. **DI naming**: Renamed all to consolidated names (`get_analytics_service`, `get_import_service`, `get_report_service`, `get_trade_service`, `get_review_service`).
3. **Identifiers router**: Dedicated `identifiers_router` added to Router Manifest; registry row owned by `04b-api-accounts.md`.

## Changed Files

| File | Change |
|------|--------|
| `04-rest-api.md` | Route registry expanded 38→95 rows; `identifiers_router` added to Router Manifest |
| `04e-api-analytics.md` | 11 DI names normalized (8→`get_analytics_service`, 2→`get_review_service`, 1→`get_analytics_service`) |
| `04a-api-trades.md` | 3 DI names normalized (2→`get_report_service`, 1→`get_trade_service`) |
| `04b-api-accounts.md` | 8 DI names normalized (3 broker + 4 bank + 1 pdf → `get_import_service`) |
| `mcp-planned-readiness.md` | `TradePlanService.create()` → `ReportService.create_trade_plan()` |

## Verification Results

```
# Stale DI names → zero hits ✅
rg "get_expectancy_service|get_drawdown_service|..." docs/build-plan/
→ No results found

# Stale TradePlanService → only structural heading in 03 (correct) ✅
rg "TradePlanService" docs/build-plan/
→ 03-service-layer.md:387 (heading: "absorbs TradePlanService")

# identifiers_router present ✅
rg "identifiers_router" docs/build-plan/04-rest-api.md
→ Line 103 (import) + Line 116 (include)
```

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
