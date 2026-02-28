# Service Layer Redesign — Implementation Plan

Applying the 10 consensus recommendations from the three-model research validation (Gemini, ChatGPT, Claude) to the Zorivest build plan documentation.

> [!IMPORTANT]
> This changes **build plan documents only** — no source code exists yet. Changes to the plan now cost nothing; changes during implementation are expensive.

## User Review Required

> [!WARNING]
> **MCP Server Language (Claude's Recommendation #2):** Claude's research strongly recommended rewriting the MCP server in Python (FastMCP) to eliminate the TypeScript→Python subprocess boundary. This plan does **NOT** include that change because it affects Phases 4, 5, 5a–5j, and 10 across 15+ documents. If you want to pursue this, it should be a separate planning effort. The current plan assumes the TS MCP server stays.

> [!IMPORTANT]
> **Three decisions needed before execution:**
> 1. **Service consolidation mapping** — do you agree with merging DeduplicationService + RoundTripService into TradeService? Or prefer them as separate collaborators injected into TradeService?
> 2. **ReviewService grouping** — Claude suggested combining MistakeTrackingService + AIReviewService + TradePlanService. TradePlanService is forward-looking (pre-trade) while the others are backward-looking (post-trade). Keep together or split?
> 3. **AccountService + SettingsService merge** — Claude suggested combining these. The current build plan has SettingsService in Phase 2A (backup-restore). Merge or keep separate?

---

## Proposed Changes

### Core Service Layer

#### [MODIFY] [03-service-layer.md](file:///p:/zorivest/docs/build-plan/03-service-layer.md)

This is the primary target — a significant rewrite:

**1. Service consolidation (~25 → ~10)**

Replace the current flat list of 25+ service files with consolidated services:

| New Service | Absorbs | Files |
|------------|---------|-------|
| `TradeService` | + DeduplicationService, RoundTripService | `trade_service.py` |
| `ImportService` | BrokerImportService, PDFImportService, BankImportService, BrokerAdapterService | `import_service.py` |
| `TaxService` | Keep as-is (8 methods are cohesive) | `tax_service.py` |
| `AnalyticsService` | Thin orchestrator — fetches data, calls pure functions | `analytics_service.py` |
| `AccountService` | AccountService (standalone) | `account_service.py` |
| `ImageService` | Keep as-is | `image_service.py` |
| `ReportService` | + TradeReportService | `report_service.py` |
| `ReviewService` | MistakeTrackingService, AIReviewService, TradePlanService | `review_service.py` |
| `MarketDataService` | IdentifierResolverService, OptionsGroupingService | `market_data_service.py` |
| `SystemService` | BackupService, ConfigExportService, CalculatorService | `system_service.py` |

**2. Extract pure-math analytics to `domain/analytics/`**

New pure functions (no classes, no UoW, no state):

```
domain/analytics/
├── __init__.py
├── expectancy.py       → calculate_expectancy(trades) → ExpectancyResult
├── drawdown.py         → drawdown_probability_table(trades, simulations, seed) → DrawdownResult
├── sqn.py              → calculate_sqn(trades) → SQNResult
├── excursion.py        → calculate_mfe_mae(trade, bars) → ExcursionResult
├── execution_quality.py → score_execution(trade, nbbo) → QualityResult
├── pfof.py             → analyze_pfof(trades, period) → PFOFResult
├── cost_of_free.py     → analyze_costs(trades) → CostResult
├── strategy.py         → breakdown_by_strategy(trades) → list[StrategyResult]
└── results.py          → All frozen dataclass result types
```

**3. ImportService with Strategy pattern**

```python
class ImportParser(Protocol):
    def detect(self, file_path: str) -> bool: ...
    def parse(self, file_path: str, config: dict | None = None) -> list[RawTransaction]: ...

class ImportService:
    def __init__(self, uow, parsers: list[ImportParser]):
        self.uow = uow
        self.parsers = parsers

    def import_file(self, file_path: str, account_id: str, format_hint: str = "auto") -> ImportResult:
        parser = self._detect_parser(file_path, format_hint)
        raw = parser.parse(file_path)
        # validate, dedup, persist uniformly
        ...
```

**4. Standardize return types**

- Add domain exception hierarchy: `ZorivestError` → `ValidationError`, `NotFoundError`, `BusinessRuleError`, `BudgetExceededError`
- Services return **frozen dataclasses / Pydantic models** for success
- Services raise **domain exceptions** for expected business failures
- Remove `None` returns for "skipped" — return `ServiceResult(skipped=True, reason="duplicate")`

**5. Move dedup hash to domain layer**

`compute_dedup_hash` → `domain/trades/identity.py` as `trade_fingerprint(trade) → str`

**6. Update test plan table** to match consolidated services + add integration test references

**7. Update filesystem tree** in the code examples

---

### Domain Layer

#### [MODIFY] [01-domain-layer.md](file:///p:/zorivest/docs/build-plan/01-domain-layer.md)

- **Add `domain/analytics/` directory** to the filesystem tree (Step 1.1) with all 9 pure function files
- **Add `domain/trades/identity.py`** for trade fingerprint/dedup hash
- **Consolidate service file listing** from ~25 files to ~10
- **Rename `AbstractUnitOfWork`** → `UnitOfWork` (it's already a Protocol, the "Abstract" prefix is misleading per the research)
- **Add analytics result dataclasses** to the build priority table

---

### Testing Strategy

#### [MODIFY] [testing-strategy.md](file:///p:/zorivest/docs/build-plan/testing-strategy.md)

- **Add in-memory SQLite integration test section** with `conftest.py` fixture for services that touch the database (TaxService, ImportService, TradeService)
- **Expand Property-Based Testing section** with specific Hypothesis invariants per analytics function (currently just mentions "Domain entities, calculator, round-trip service, deduplication")
- **Add math service testing taxonomy table** (Example-Based / Property-Based / Golden-File / Edge Cases matrix)
- **Add synthetic fixture corpus specification** (5–8 CSV, 4–6 OFX, 3–5 QIF, 3–4 PDF)
- **Update Python Unit Tests table** to reflect consolidated service names
- **Add test organization guidance**: scenario-based files for TaxService (`test_tax_wash_sales.py`, `test_tax_lots.py`, `test_tax_quarterly.py`)

---

### Infrastructure

#### [MODIFY] [02-infrastructure.md](file:///p:/zorivest/docs/build-plan/02-infrastructure.md)

- **Add WAL mode PRAGMA** to database initialization:  
  ```python
  engine.execute("PRAGMA journal_mode=wal")
  engine.execute("PRAGMA synchronous=NORMAL")
  ```
- **Add per-thread Session factory** guidance for PySide6 `QThread`/`QThreadPool` background tasks
- **Add note**: connections cannot be shared across threads; each thread needs its own Session

---

### Dependency Manifest

#### [MODIFY] [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md)

- **Add `hypothesis`** to dev dependencies (property-based testing)
- Verify `pydantic` is already listed (for command objects and result models)

---

### Ripple-Effect Checks (Read-Only Audit)

These files reference service names and may need minor updates:

| File | What to Check | Expected Change |
|------|--------------|-----------------|
| [04e-api-analytics.md](file:///p:/zorivest/docs/build-plan/04e-api-analytics.md) | Service names in route → handler mappings | Update `ExpectancyService` → `AnalyticsService` etc. |
| [05c-mcp-trade-analytics.md](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md) | Python service call references | Update service names |
| [05i-mcp-behavioral.md](file:///p:/zorivest/docs/build-plan/05i-mcp-behavioral.md) | MistakeTrackingService / AIReviewService refs | Update to `ReviewService` |
| [build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) | Service names in priority table | Update to consolidated names |

---

## Verification Plan

### Automated Checks

Since this is a documentation-only change (no source code exists yet), there are no unit tests to run. Verification is:

1. **Cross-File Consistency Audit**
   - Grep all 48 build plan files for old service names (e.g., `ExpectancyService`, `DeduplicationService`, `BrokerImportService`) — zero hits expected after updates
   - Command: `rg "ExpectancyService|DeduplicationService|BrokerImportService|PDFImportService|DrawdownService|SQNService|ExcursionService|PFOFAnalysisService|CostOfFreeService|StrategyBreakdownService" docs/build-plan/`

2. **Filesystem Tree Consistency**
   - Compare the service file listing in `01-domain-layer.md` Step 1.1 against the service definitions in `03-service-layer.md` — they must match exactly

3. **Test Plan Alignment**
   - Verify every consolidated service in `03-service-layer.md` has a corresponding entry in the test plan tables of both `03-service-layer.md` and `testing-strategy.md`

### Manual Verification

4. **User review** of the three design decisions flagged in "User Review Required" above
5. **User review** of the updated `03-service-layer.md` to confirm the consolidated architecture matches their expectation for the project
