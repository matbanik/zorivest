# Service Layer Redesign — Walkthrough

## What Changed

Applied 10 research-validated recommendations from the three-model synthesis (Gemini/ChatGPT/Claude) to 6 build plan documents.

### Files Modified

| File | Change Summary |
|------|---------------|
| [03-service-layer.md](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | **Full rewrite** — consolidated ~25 services to ~10, extracted 9 pure analytics to `domain/analytics/`, added Strategy pattern imports, domain exception hierarchy, frozen dataclass returns |
| [01-domain-layer.md](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) | Filesystem tree updated: `domain/analytics/` (9 files), `domain/trades/identity.py`, ~10 service files; `AbstractUnitOfWork` → `UnitOfWork` |
| [testing-strategy.md](file:///p:/zorivest/docs/build-plan/testing-strategy.md) | Added: Hypothesis PBT with invariants, in-memory SQLite integration tests, math testing taxonomy, synthetic fixture corpus, scenario-based tax test organization |
| [02-infrastructure.md](file:///p:/zorivest/docs/build-plan/02-infrastructure.md) | Added WAL mode PRAGMA + per-thread Session factory guidance for PySide6 background tasks |
| [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md) | Added `hypothesis` to test dependencies |
| [output-index.md](file:///p:/zorivest/docs/build-plan/output-index.md) | Updated 15 stale service name references to consolidated names |

### Design Decisions

1. **DeduplicationService + RoundTripService → absorbed into TradeService** (trade lifecycle concern, not independent)
2. **TradePlanService → merged into ReportService** (both are "trade documentation" bounded context)
3. **AccountService + SettingsService → kept separate** (different build phases, different concerns)

### Deferred

- MCP server rewrite to Python (FastMCP) — impacts 15+ documents, separate planning effort

## Verification

**Final grep for 18 old service names across all 48 build plan files: zero hits ✅**

```
rg "ExpectancyService|DeduplicationService|BrokerImportService|PDFImportService|
DrawdownService|SQNService|ExcursionService|PFOFAnalysisService|CostOfFreeService|
StrategyBreakdownService|MistakeTrackingService|BankImportService|
IdentifierResolverService|OptionsGroupingService|RoundTripService|
ExecutionQualityService|TransactionLedgerService|BrokerAdapterService"
→ No results found
```
