# Service Layer Research Composite

> Synthesis of independent reviews by **Gemini** (Deep Research), **ChatGPT** (o3 Deep Research), and **Claude** (Opus Extended Thinking) — February 2026

---

## Consensus Matrix

Items where **all three models agree** represent high-confidence recommendations.

| # | Finding | Gemini | ChatGPT | Claude | Confidence |
|---|---------|:------:|:-------:|:------:|:----------:|
| 1 | **Extract pure-math analytics into standalone functions** — ExpectancyService, DrawdownService, SQN, Excursion etc. should NOT be service classes with UoW | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 2 | **Consolidate 25+ services to ~10–12** by bounded context | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 3 | **TaxService's 8 methods are cohesive**, NOT an SRP violation — they all change when tax rules change | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 4 | **Mock-only service tests are insufficient** — must add in-memory SQLite integration tests for services that touch the database | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 5 | **Use Hypothesis property-based testing** for all pure-math analytics (invariants: Kelly ∈ bounds, drawdown ≤ 0, win_rate ∈ [0,1]) | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 6 | **Standardize return types** — mixed None/dict/exceptions is a real problem at the MCP boundary | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 7 | **Unify import services** (Broker CSV, PDF, Bank) under a single ImportService with Strategy pattern for format-specific parsers | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 8 | **Dedup hash is domain logic**, not service logic — move `compute_dedup_hash` into domain layer | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 9 | **Import parsers need fixture-file testing** — mocks cannot protect against real-world CSV/PDF/OFX malformation | ✅ | ✅ | ✅ | 🟢 Unanimous |
| 10 | **Organize tax tests by scenario**, not one monolithic file — split into wash_sales, lots, quarterly_estimates, etc. | ✅ | ✅ | ✅ | 🟢 Unanimous |

---

## Disagreements & Nuanced Positions

| Topic | Gemini | ChatGPT | Claude | Resolution Guidance |
|-------|--------|---------|--------|---------------------|
| **Vertical Slice Architecture** | Recommends hybrid VSA as primary pattern | Not discussed | Not discussed | Gemini-only; consider selectively for complex features but don't overhaul the entire plan |
| **Domain Events** | Recommends synchronous in-process event bus triggered post-UoW commit | Nice-to-have; direct orchestration is simpler for desktop | Unnecessary — PySide6 signals already serve as event system; add message bus only if circular deps emerge | **Defer**. Claude's position is most pragmatic for a single-user desktop app. Reserve for later if coordination pain becomes real |
| **Result Pattern vs Exceptions** | Strongly advocates `Result<T>` dataclass for all services | Recommends hybrid (Result for expected, exceptions for unexpected) | Recommends Pydantic models for success + domain exception hierarchy at MCP boundary | **Hybrid approach**: Pydantic return models for success, domain exceptions for business failures, Result wrapper only at MCP dispatch boundary |
| **MCP Server Language** | Not discussed | Not discussed | **Rewrite MCP server in Python (FastMCP)** to eliminate TS→Python IPC boundary | **Evaluate carefully** — this is Claude's strongest unique recommendation but has significant scope implications. The TS MCP server is already designed across multiple build plan phases |
| **Abstract Base Classes** | Retain for polymorphism | Not discussed | **Drop ABCs**, use Protocols (PEP 544) or duck typing | Protocols are the modern Python approach; **adopt Protocols over ABCs** where polymorphism is needed |
| **SQLite WAL Mode** | Mentions SQLite concurrency as architectural concern | Not discussed | Specific recommendation: enable WAL mode + per-thread Sessions for PySide6 background tasks | **Must-do** — WAL is a well-known SQLite best practice for concurrent read/write |

---

## Consolidated Service Architecture

All three models converge on a similar consolidation. Here's the synthesized target:

| Consolidated Service | Absorbs | Role |
|---------------------|---------|------|
| `TradeService` | TradeService, DeduplicationService, RoundTripService | Trade lifecycle (create, dedup, round-trip matching) |
| `ImportService` | BrokerImportService, PDFImportService, BankImportService, BrokerAdapterService | Unified import pipeline with Strategy pattern parsers |
| `TaxService` | TaxService (keep as-is, 8 methods) | All tax computation — cohesive bounded context |
| `AnalyticsService` | Orchestration facade only — fetches data, calls pure functions, returns results | Thin orchestrator over `domain/analytics/` pure functions |
| `AccountService` | AccountService, SettingsService | Account + user configuration |
| `ImageService` | ImageService (standalone) | Chart/screenshot management |
| `ReportService` | ReportService, TradeReportService | Report creation + trade↔journal linking |
| `ReviewService` | MistakeTrackingService, AIReviewService, TradePlanService | Behavioral analysis bounded context |
| `MarketDataService` | IdentifierResolverService, OptionsGroupingService | Instrument resolution + classification |
| `SystemService` | BackupService, ConfigExportService, CalculatorService | System utilities |

**Pure domain functions** (extracted from service classes into `domain/analytics/`):

```
calculate_expectancy(trades) → ExpectancyResult
calculate_drawdown(trades, simulations) → DrawdownResult
calculate_sqn(trades) → SQNResult
calculate_excursion(trade, bars) → ExcursionResult
calculate_execution_quality(trade, nbbo) → QualityResult
analyze_pfof(trades, period) → PFOFResult
calculate_cost_of_free(trades) → CostResult
breakdown_by_strategy(trades) → list[StrategyResult]
calculate_round_trip_stats(round_trips) → RoundTripStats
```

Each returns a **frozen dataclass** (or Pydantic model), not a raw dict.

---

## Testing Strategy Consensus

### What to Change

| Current Approach | Recommended Approach | Priority |
|-----------------|---------------------|----------|
| Mock UoW for all services | **In-memory SQLite integration tests** for TaxService, ImportService, TradeService | **Must-fix** |
| Example-based tests only for math | **Hypothesis property-based tests** for all 9 pure analytics functions | **Must-fix** |
| 10 test files for 25+ services | Prioritize P0 tests for tax + analytics, P1 for imports | **Should-fix** |
| 1 test file per service | **Scenario-based organization** for complex services (tax, imports) | **Should-fix** |
| No fixture files | **Synthetic fixture corpus**: 5–8 CSV, 4–6 OFX, 3–5 QIF, 3–4 PDF | **Should-fix** |
| No contract tests | **Contract tests for MCP boundary** (TS ↔ Python schema agreement) | **Should-fix** |

### Math Service Testing Taxonomy (Claude's matrix, validated by all three)

| Service | Example-Based | Property-Based | Golden-File | Edge Cases |
|---------|:---:|:---:|:---:|:---:|
| ExpectancyService | ✅ Essential | ✅ Essential | 🔶 Recommended | ✅ Essential |
| DrawdownService | ✅ Essential | ✅ Essential | 🔶 Recommended | ✅ Essential |
| SQNService | ✅ Essential | ✅ Essential | ❌ Unnecessary | ✅ Essential |
| ExcursionService | ✅ Essential | 🔶 Recommended | ❌ Unnecessary | ✅ Essential |

### Key Hypothesis Invariants to Test

| Function | Property |
|----------|----------|
| `calculate_expectancy` | Result is finite; positive when all trades win; negative when all trades lose; bounded by min/max trade P&L |
| `calculate_drawdown` | Always ≤ 0; equals 0 for monotonically increasing equity curves |
| `calculate_sqn` | Sign matches expectancy sign (when σ > 0); scales with √N |
| Kelly fraction | Always ≤ 1.0; ≤ 0 when sum of returns is negative |
| MFE/MAE | MAE ≤ 0; MFE ≥ 0; for winners MFE ≥ P&L; for losers |MAE| ≥ |P&L| |

### Estimated Test Count (Claude)

| Category | Type | DB? | Priority | Tests |
|----------|------|-----|----------|-------|
| Tax calculations | Integration + property | In-memory SQLite | **P0** | 30–50 |
| Pure analytics | Unit + property | None | **P0** | 20–30 |
| Import parsers | Integration + fixture | File fixtures | **P1** | 20–40 |
| Format auto-detection | Unit + parametrized | None | **P1** | 10–15 |
| CRUD services | Integration | In-memory SQLite | **P2** | 10–15 |
| Coordination services | Unit (mock deps) | None | **P2** | 5–10 |
| **Total** | | | | **~100–160** |

---

## Risk Register (Claude, validated by ChatGPT)

| # | Risk | L | I | Score | Mitigation |
|---|------|:-:|:-:|:-----:|------------|
| 1 | Over-engineering multiplies AI agent implementation cost (25+ classes, ABCs, UoW hierarchy) | 5 | 4 | **20** | Consolidate to ~10 services; drop ABCs; use Protocols |
| 2 | TypeScript MCP server creates fragile serialization boundary (subprocess lifecycle, Decimal serialization, stdout corruption) | 4 | 4 | **16** | Evaluate FastMCP in Python; at minimum, define strict serialization contracts |
| 3 | Testing coverage gap for tax calculations (wash sales, cost basis, lot matching) | 3 | 5 | **15** | Mandate in-memory SQLite integration tests + property-based invariants |
| 4 | Mixed return types cause silent MCP failures (None vs dict vs exception vs domain object) | 4 | 3 | **12** | Enforce uniform contract: Pydantic models + domain exceptions |
| 5 | SQLite threading with PySide6 background tasks (shared connections, lock contention) | 3 | 4 | **12** | Enable WAL mode; per-thread Session factory; short write transactions |

---

## Final Recommendations (Priority Order)

| # | Recommendation | Effort | Impact | Priority | When |
|---|---------------|:------:|:------:|:--------:|:----:|
| 1 | **Consolidate 25+ services to ~10** by bounded context; extract 9 analytics to pure functions in `domain/analytics/` | M | H | **Must** | Now (design) |
| 2 | **Standardize service contract**: Pydantic/frozen dataclass returns for success + domain exception hierarchy for failures | S | H | **Must** | Now (design) |
| 3 | **Add in-memory SQLite integration tests** for TaxService, ImportService, and TradeService — ban mock-only tests for these | M | H | **Must** | Sprint 1 |
| 4 | **Enable SQLite WAL mode** + per-thread Session factory for PySide6 background tasks | S | H | **Must** | Sprint 1 |
| 5 | **Drop ABCs in favor of Protocols (PEP 544)** — use concrete UoW + concrete repositories | S | M | **Must** | Now (design) |
| 6 | **Use Pydantic command objects** for mutation methods (4+ params); plain kwargs for simple queries | S | M | **Should** | Now (design) |
| 7 | **Add Hypothesis property-based tests** for all 9 pure analytics functions with documented invariants | M | M | **Should** | Sprint 2 |
| 8 | **Unify import services** with Strategy pattern; create synthetic fixture corpus (5–8 CSV, 4–6 OFX, 3–5 QIF, 3–4 PDF) | M | M | **Should** | Sprint 2 |
| 9 | **Move dedup hash to domain layer** — `domain/trades/identity.py` not service layer | S | M | **Should** | Sprint 1 |
| 10 | **Defer domain events** — use direct service calls + PySide6 signals; add simple message bus only when circular deps emerge | S | L | **Nice** | Future |

> **Effort**: S = hours, M = 1–3 days | **Impact**: H = prevents architectural failure, M = improves quality, L = polish

---

## Source Concordance

Each recommendation is backed by agreement across multiple independent research sessions:

| Recommendation | ChatGPT Evidence | Claude Evidence | Gemini Evidence |
|---------------|-----------------|-----------------|-----------------|
| Consolidate services | "layers everywhere, clarity nowhere" failure mode; functional core, imperative shell | Martin Fowler's "subject area" definition; nano-service anti-pattern | Facade pattern for analytics; Strategy for imports |
| In-memory SQLite tests | "your app's persistence layer isn't an external dependency"; mocks prove wiring not behavior | "Do not mock the repository"; zero disparity between test and production | Mocking SQLAlchemy "fundamentally fails to verify the ORM" |
| Property-based testing | Hypothesis for "no NaNs", "drawdown never negative", bounds checking | Specific invariants per function; `st.decimals` for money | Financial math invariants; Kelly criterion bounds |
| Standardize returns | Result/Either for expected failures; exceptions for system errors | Pydantic models + domain exceptions + MCP dispatch catch-all | Generic `Result<T>` dataclass; `to_mcp_payload()` serialization |
| Pure domain functions | "architectural self-harm" to inject UoW into pure computation | "These are single-function wrappers masquerading as services" | Analytics don't require orchestration, repos, or state management |
