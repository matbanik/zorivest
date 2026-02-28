# Zorivest service layer needs surgery, not more patterns

**Zorivest's 25+ service architecture over-applies enterprise patterns to a single-user SQLite desktop app.** The "Architecture Patterns with Python" approach was designed for MADE.com's concurrent e-commerce warehouse system — not a personal trading journal. The highest-impact change is consolidating to **8–12 services**, extracting pure calculations into standalone functions, and writing the MCP server in Python to eliminate the TypeScript→Python serialization boundary entirely. These changes cost nothing now (it's a build plan) and prevent significant implementation complexity later, especially since an AI coding agent will be the implementer.

---

## Phase 1: The architecture is 60% right and 40% over-engineered

### Unit of Work earns its keep — barely

SQLAlchemy's `Session` already implements Unit of Work internally. The official docs state: *"Whenever the database is about to be queried, or when the transaction is about to be committed, the Session first flushes all pending changes... This is known as the unit of work pattern."* Wrapping it in another UoW class creates a double abstraction.

However, a **thin UoW wrapper provides two genuine benefits** even for SQLite: it narrows SQLAlchemy's enormous Session API to just `commit()`, `rollback()`, and repository access, and it enables a `FakeUnitOfWork` for fast unit tests without touching any database. The Cosmic Python book acknowledges the redundancy but argues: *"By coupling to the Session interface, you're choosing to couple to all the complexity of SQLAlchemy."*

**The verdict**: Keep one concrete `UnitOfWork` class (a context manager around Session). Drop the abstract base class — you're never swapping SQLite for PostgreSQL in a desktop app, so the `AbstractUnitOfWork` adds zero value. The book's own authors have admitted: *"In real life, we've sometimes found ourselves deleting ABCs from our production code, because Python makes it too easy to ignore them."*

### 25+ services is the nano-service anti-pattern applied to a monolith

Martin Fowler's original Service Layer definition is clear: *"The operations available to clients of a Service Layer are implemented as scripts, organized several to a class defining a subject area of related logic."* The operative phrase is **subject area** — not individual operation. Having separate `ExpectancyService`, `DrawdownService`, `SQNService`, and `ExcursionService` classes violates this guidance. These are single-function wrappers masquerading as services.

The specific problem is that **9 analytics "services" are pure mathematical functions with no database access, no side effects, and no state**. They don't belong in the service layer at all. The Cosmic Python book itself distinguishes domain services (pure logic) from application services (orchestration) and explicitly states: *"Not Everything Has to Be an Object: A Domain Service Function."* Python's multi-paradigm nature means `calculate_expectancy(trades)` as a function in `domain/analytics/expectancy.py` is cleaner than `ExpectancyService(uow).calculate()`.

**Recommended consolidation from ~29 services to ~10:**

| Consolidated service | Absorbs | Rationale |
|---|---|---|
| `TradeService` | TradeService, DeduplicationService, RoundTripService | Trade lifecycle is one bounded context |
| `AnalyticsService` | Orchestrates all 9 pure-function analytics | Fetches data, calls pure functions, returns results |
| `TaxService` | TaxService (keep as-is with 8 methods) | Cohesive: all methods change when tax rules change |
| `ImportService` | BrokerImportService, PDFImportService, BankImportService, BrokerAdapterService | Import is one workflow; format detection → parsing → validation |
| `AccountService` | AccountService, SettingsService | Account and settings share user-configuration domain |
| `ReportService` | TradeReportService, ReportService | Report generation is one concern |
| `ReviewService` | MistakeTrackingService, AIReviewService, TradePlanService | Behavioral analysis is one bounded context |
| `ImageService` | ImageService | Standalone — chart/screenshot management |
| `MarketDataService` | IdentifierResolverService, OptionsGroupingService | Market data resolution and instrument classification |
| `SystemService` | BackupService, ConfigExportService, CalculatorService | System utilities |

The 9 analytics calculations (`calculate_expectancy`, `calculate_drawdown`, `calculate_sqn`, `calculate_excursion`, `calculate_execution_quality`, `analyze_pfof`, `calculate_cost_of_free`, `calculate_strategy_breakdown`, `calculate_round_trip_stats`) become **pure functions in `domain/analytics/`** — no class wrapping needed.

### Constructor DI works fine at 10 services, breaks at 25+

The Cosmic Python book's "bootstrap script" (composition root) approach — manual DI using closures and `functools.partial` — works cleanly for **up to ~10–15 services** with shallow dependency graphs. At 25+ services with cross-dependencies (TradeService → DeduplicationService → IdentifierResolverService), the bootstrap script becomes a fragile, order-dependent wiring graph.

**With the recommended consolidation to ~10 services, manual DI remains perfectly manageable.** The bootstrap script becomes straightforward: create repositories, create UoW, wire services. No framework needed. If the service count stays at 25+, the `dependency-injector` library (the most mature Python DI framework at ~6K GitHub stars) would be justified — but consolidation eliminates that need.

### Mixed return types are a real problem at the MCP boundary

Services returning `None`, `dict`, exceptions, or domain objects create friction when a TypeScript MCP server consumes them. The MCP specification defines a clear contract: tool results have `structuredContent` (JSON object matching an `outputSchema`), `content` (text for display), and `isError` (boolean). Python services need to map cleanly to this.

**The minimum-friction pattern is a two-layer approach.** Inside Python, services raise **domain-specific exceptions** organized in a hierarchy (`TradingJournalError` → `ValidationError`, `NotFoundError`, `BusinessRuleError`, etc.) and return **Pydantic models** for success cases. At the MCP dispatch boundary, a single catch-all handler converts these:

- Success: Pydantic model → `.model_dump()` → `structuredContent`
- Business error: `TradingJournalError` → `{isError: true, content: [{type: "text", text: "..."}]}`
- Unexpected error: `Exception` → `{isError: true, content: [{type: "text", text: "Internal error"}]}`

This aligns with MCP's design principle: *"Tool errors should be reported within the result object, not as MCP protocol-level errors. This allows the LLM to see and potentially handle the error."* Pydantic models also auto-generate JSON Schema via `model_json_schema()`, which maps directly to MCP's `inputSchema` and `outputSchema`.

### Domain events are unnecessary — PySide6 signals already exist

With ~10 consolidated services and a single-process desktop app, direct service calls handle all coordination. The trading app's key workflows — trade imported → recalculate analytics → update tax lots → refresh UI — are sequential orchestration, not event-driven pub/sub. A `TradeService.import_trades()` method can directly call `AnalyticsService.recalculate()` and `TaxService.update_lots()`.

**PySide6's signal/slot mechanism already serves as the event system** for UI reactivity. When a service completes a calculation, it can emit a Qt signal that the UI layer observes. This is simpler, debuggable (direct call stacks vs. event chains), and idiomatic for Qt applications. Add a simple in-process message bus (~20 lines of code, per the Cosmic Python pattern) only if circular dependencies between services emerge later.

---

## Phase 2: Service contracts need Pydantic at the boundary and exceptions inside

### Core services should accept Pydantic commands for mutations, kwargs for queries

For **mutations** (create trade, record payment, import file) with 4+ parameters, Pydantic `BaseModel` command objects provide validation, JSON Schema generation, and clean serialization. For **simple queries** (get lots by account ID, fetch trade by ID) with 1–3 parameters, plain keyword arguments avoid unnecessary ceremony.

```python
# Mutation: Pydantic command
class CreateTradeCommand(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: Decimal = Field(gt=0, decimal_places=4)
    date: date
    account_id: int

# Query: plain kwargs
def get_trade(self, trade_id: int) -> Trade: ...
```

This pattern matters because Pydantic's `ValidationError` fires **before** service logic runs, keeping services clean. And `model_json_schema()` automatically produces MCP `inputSchema` — no manual schema maintenance.

### TaxService's 8 methods are cohesive, not a violation

The 8 methods (`simulate_impact`, `estimate`, `find_wash_sales`, `get_lots`, `quarterly_estimate`, `record_payment`, `harvest_scan`, `ytd_summary`) all operate on the same domain concepts (tax lots, gains/losses, tax years) and all change for the same reason: **when tax rules change**. This passes Robert C. Martin's SRP test. Multiple software design sources confirm: *"A class can have multiple methods as long as they're all related to the same responsibility"* and *"Over-abstraction is the wrong way of applying SRP."*

**Split only if** the class exceeds ~400 lines or `harvest_scan` and `find_wash_sales` develop complex, independently evolving algorithms. At that point, extract a `TaxOptimizationService` (harvest scanning, wash sale detection, impact simulation) from a core `TaxService` (lot management, estimates, payments, summaries).

### Import services need a pipeline architecture

The three import services (Broker, PDF, Bank) share a common workflow: detect format → parse → validate → deduplicate → persist. Rather than three separate service classes, a single `ImportService` with a **strategy pattern** for format-specific parsers is cleaner:

- `ImportService.import_file(path, source_hint)` → auto-detects format, dispatches to appropriate parser
- Format parsers (`CSVParser`, `OFXParser`, `QIFParser`, `PDFParser`) are injected strategies
- Each parser returns a common `list[RawTransaction]` type
- `ImportService` handles deduplication, validation, and persistence uniformly

This eliminates the coordination problem of having `BrokerImportService` and `BankImportService` duplicating deduplication and persistence logic.

### Analytics functions return typed result dataclasses

Each pure calculation function returns a frozen dataclass with all computed metrics, not a raw dict or tuple:

```python
@dataclass(frozen=True)
class ExpectancyResult:
    expectancy: Decimal
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    trade_count: int
```

This makes the AnalyticsService's API surface self-documenting, enables IDE autocomplete, and serializes cleanly through the MCP boundary via Pydantic's `from_attributes=True`.

---

## Phase 3: Test with real SQLite, not mocks — and use Hypothesis for math

### The confidence gap is real: in-memory SQLite beats mocks

**Do not mock the repository for services that touch the database.** Since the production database IS SQLite, in-memory SQLite provides zero disparity between test and production — and it's fast (no disk I/O). Multiple practitioners converge on this: *"The disparity between a mock and the dependency it mimics has to be as small as possible. When implementing a database mock, keeping this disparity small is particularly hard."*

Three concrete examples of bugs that mocks miss:

- **`TaxService.find_wash_sales`**: The 30-day lookback requires a date-range query (`WHERE sale_date BETWEEN ? AND ?`). Mocks can't verify off-by-one errors on boundary dates (does "30 days" include or exclude day 30?), correct handling of chained wash sales where the adjusted basis propagates forward, or cross-account detection that depends on JOIN behavior. An in-memory SQLite test with seed data catches all three.

- **`RoundTripService` execution matching**: Matching buys to sells for P&L depends on chronological ordering. With identical timestamps, SQLite's `ORDER BY` behavior matters. Partial fills that split a 100-share buy across two sells require stateful queries. Mock tests typically return pre-ordered data, hiding sort-order bugs.

- **`BankImportService` format detection**: File encoding (UTF-8 BOM vs Latin-1 vs Windows-1252) and malformed headers are I/O-level bugs. The `ofxparse2` library was forked specifically to add encoding detection. QIF format is notoriously inconsistent across banks — *"different banks just seem to make stuff up."* These bugs require testing against actual file bytes, not mocked return values.

**The recommended test infrastructure**: a `conftest.py` fixture that creates a fresh in-memory SQLite database per test function, runs `Base.metadata.create_all()`, seeds with representative data, and tears down after the test.

### Property-based testing with Hypothesis catches edge cases humans miss

The 9 pure analytics functions are **ideal Hypothesis candidates** because they're deterministic, stateless, and have mathematical invariants that must hold for all valid inputs. Specific properties:

**Expectancy**: bounded by min and max trade P&L; positive when all trades win; negative when all trades lose; equals the mean P&L (by definition). **Drawdown**: always ≤ 0; equals 0 for monotonically increasing equity curves; absolute value ≤ total equity range. **SQN**: sign matches expectancy sign (when σ > 0); scales with √N; undefined when σ = 0. **MAE/MFE excursion**: MAE ≤ 0 for every trade; MFE ≥ 0; for winning trades, MFE ≥ P&L; for losing trades, |MAE| ≥ |P&L|.

Use Hypothesis's `st.decimals(places=2, allow_nan=False, allow_infinity=False)` for money, `st.dates()` for trade dates, and custom `@st.composite` strategies for generating valid trade objects. Combine `@given` for broad coverage with `@example` decorators for known edge cases (empty list, single trade, all-zero P&L).

### Testing taxonomy by service tier

| Category | Test type | Database? | Priority | Estimated tests |
|---|---|---|---|---|
| Tax calculations (wash sales, lots, harvest) | Integration + property-based | In-memory SQLite | **P0 — must have** | 30–50 |
| Pure analytics (expectancy, drawdown, SQN, excursion) | Unit + property-based | None needed | **P0 — must have** | 20–30 |
| Import parsers (CSV, OFX, QIF, PDF) | Integration + fixture-based | File fixtures | **P1 — should have** | 20–40 |
| Format auto-detection | Unit + parametrized | None | **P1 — should have** | 10–15 |
| CRUD services (validation logic only) | Integration | In-memory SQLite | **P2 — good to have** | 10–15 |
| Coordination/orchestration services | Unit (mock dependencies) | None | **P2 — good to have** | 5–10 |

**Fixture file counts per format**: 5–8 CSV (date formats, delimiters, encodings, malformed data), 4–6 OFX (v1 SGML, v2 XML, investment accounts, malformed headers), 3–5 QIF (checking, investment, ambiguous types), 3–4 PDF (text-extractable, scanned, multi-page, password-protected). All fixtures should be **synthetic** — no real financial data in the repo.

**Total estimated test count: ~100–160 tests** for comprehensive coverage. This is achievable and proportionate for a personal tool.

### Four services MUST have unit tests; the rest can defer

**Non-negotiable P0 testing** (regulatory and correctness risk):

- **Tax calculations**: IRS penalties for incorrect wash sale detection or cost basis errors are real, even for a personal tool. Every `TaxService` method needs test coverage, especially `find_wash_sales` (the 30-day lookback is a notorious bug factory) and `harvest_scan` (must correctly identify unrealized losses without triggering wash sales).

- **Pure analytics functions**: These produce the numbers the user makes trading decisions from. Wrong expectancy or drawdown calculations lead to real financial losses. Since they're pure functions, testing is trivial — no setup, no teardown, just input→output assertions.

**P1 testing** (data integrity risk): Import parsers. A parsing bug that misreads a trade date or quantity corrupts the entire downstream analysis. Each parser needs fixture-file coverage for happy paths and known edge cases.

**Deferrable to integration testing** (low logic density): CRUD operations, settings management, backup/export, and coordination services. Per Martin Fowler: *"Don't test trivial code. Don't worry, Kent Beck said it's ok."*

---

## Phase 4: Five risks that could sink the implementation

### Risk 1 — Over-engineering multiplies AI agent implementation cost

**Severity: High. Likelihood: High (it's already happening in the design).**

The build plan specifies 25+ service classes, abstract base classes, UoW hierarchy, and repository abstractions — patterns designed for MADE.com's concurrent e-commerce platform. For a single-user SQLite desktop app, each unnecessary abstraction layer multiplies the files an AI coding agent must generate, understand, and maintain coherently. Research from vFunction shows AI agents *"rarely incorporate strategies such as retry logic, circuit breakers... you'll usually get a happy-path implementation"* — meaning the agent will generate the boilerplate but miss the subtle cross-cutting logic that justifies these patterns.

**Mitigation**: Consolidate to ~10 services. Drop ABCs in favor of Protocols (PEP 544) or duck typing. Keep architecture to 2–3 layers (models → services → repositories). Each service in one file so the AI agent can implement it in a single context window.

### Risk 2 — TypeScript MCP server creates a fragile serialization boundary

**Severity: High. Likelihood: High.**

A TypeScript MCP server calling Python services via subprocess introduces five failure modes: subprocess lifecycle management (Python crashes go undetected — known MCP SDK bug where *"the client does not detect the broken pipe... calls hang indefinitely"*), stdout corruption (any Python `print()` or library warning breaks JSON-RPC framing), `Decimal` serialization (critical for financial data, notoriously problematic in JSON), cold-start latency per request, and error propagation across language boundaries.

**Mitigation**: **Write the MCP server in Python using FastMCP** (`pip install mcp`). This eliminates the entire TypeScript→Python IPC layer. The AI assistant spawns the Python MCP server as a subprocess via stdio — the standard pattern. The MCP server directly imports and calls service classes. Zero serialization boundary, zero subprocess management, zero language mismatch.

### Risk 3 — SQLite threading with PySide6 background tasks

**Severity: Medium. Likelihood: Medium.**

PySide6's event loop runs on the main thread. Background analytics (recalculating drawdown for 10K trades) must run on QThread/QThreadPool to avoid freezing the UI. SQLite connections **cannot be shared across threads** — each thread needs its own Session. Without WAL mode, a background write locks the entire database, blocking UI reads.

**Mitigation**: Enable WAL mode on database creation (`PRAGMA journal_mode=wal; PRAGMA synchronous=NORMAL`). Simon Willison's benchmarks show WAL improves combined read/write throughput from **1,843 updates/s + 29 selects/s** to **11,641 updates/s + 462,251 selects/s**. Create per-thread SQLAlchemy Sessions. Keep write transactions short. Use PySide6 signals to pass results back to the main thread.

### Risk 4 — Mixed return types cause silent MCP failures

**Severity: Medium. Likelihood: High.**

If some services return `None`, others return `dict`, others raise exceptions, and others return domain objects, the MCP dispatch layer must handle every variant — and will inevitably miss cases. Silent failures where the LLM receives `null` instead of an error message are particularly dangerous because they're invisible.

**Mitigation**: Enforce a uniform contract: all services return **Pydantic models** for success, raise **domain exceptions** (from a hierarchy rooted at `TradingJournalError`) for failures. The MCP dispatch layer has exactly two code paths: serialize success or translate exception. Define this contract in a `ServiceProtocol` and enforce it in code review / testing.

### Risk 5 — Testing coverage gap for tax calculations

**Severity: High. Likelihood: Medium.**

Wash sale detection, cost basis adjustment, and tax lot matching are the most algorithmically complex parts of the app — and the most consequential if wrong (IRS implications). If the testing strategy relies on mocked repositories, date-boundary bugs, chained wash sale propagation errors, and cross-account detection failures will ship undetected.

**Mitigation**: Mandate in-memory SQLite integration tests for all `TaxService` methods. Require property-based tests for wash sale invariants (adjusted basis ≥ 0, total deferred losses = total basis adjustments). Create a "golden file" test suite with manually calculated IRS examples.

---

## Phase 5: Prioritized recommendations matrix

| # | Recommendation | Effort | Impact | Priority | Phase |
|---|---|---|---|---|---|
| 1 | **Consolidate 25+ services to ~10** by grouping by bounded context and extracting pure analytics into standalone functions | **M** | **H** | **Must** | Design (now) |
| 2 | **Write MCP server in Python (FastMCP)** — eliminate TypeScript→Python subprocess boundary entirely | **M** | **H** | **Must** | Design (now) |
| 3 | **Define uniform service contract**: Pydantic return models + domain exception hierarchy + MCP dispatch catch-all | **S** | **H** | **Must** | Design (now) |
| 4 | **Drop abstract base classes**, use concrete UoW + concrete repositories. Use Protocols (PEP 544) only where polymorphism is needed (e.g., import parser strategies) | **S** | **M** | **Must** | Design (now) |
| 5 | **Enable SQLite WAL mode** in database initialization and create per-thread Session factory for PySide6 background tasks | **S** | **H** | **Must** | Implementation (Sprint 1) |
| 6 | **Use Pydantic command objects** for mutation methods (4+ params) that auto-generate MCP `inputSchema`; plain kwargs for simple queries | **S** | **M** | **Should** | Design (now) |
| 7 | **Mandate in-memory SQLite integration tests** for TaxService and import parsers; ban mocked-repository tests for these services | **M** | **H** | **Should** | Implementation (Sprint 1–2) |
| 8 | **Add Hypothesis property-based tests** for all 9 pure analytics functions with documented invariants per function | **M** | **M** | **Should** | Implementation (Sprint 2–3) |
| 9 | **Create synthetic fixture files** (5–8 CSV, 4–6 OFX, 3–5 QIF, 3–4 PDF) with known edge cases for import parser testing | **M** | **M** | **Should** | Implementation (Sprint 2) |
| 10 | **Reserve domain events for later** — use direct service calls + PySide6 signals for coordination; add a simple message bus only when circular dependencies emerge | **S** | **L** | **Nice** | Future (if needed) |

### How to read this matrix

**Effort**: S = hours, M = 1–3 days, L = 1+ weeks. **Impact**: H = prevents architectural failure or major bugs, M = improves quality/maintainability, L = nice-to-have polish. **Priority**: Must = do before implementation begins, Should = do in early sprints, Nice = defer until pain is felt.

Recommendations 1–4 are **design-time changes that cost near-zero now** but would require major refactoring later. The build plan is the cheapest place to make these corrections. Recommendations 5–9 are **implementation-time practices** that should be established in the first sprint and maintained throughout. Recommendation 10 is an explicit **YAGNI decision** — the architecture should be designed so events *can* be added later, but they shouldn't be built speculatively.

The overarching principle: the "Architecture Patterns with Python" book provides excellent patterns for the right context. **Cherry-pick Repository, Service Layer, and thin UoW.** Leave Aggregates, CQRS, domain events, and the abstract hierarchy for the web-scale concurrent systems they were designed for. A Hacker News commenter who builds trading systems put it perfectly: *"These kinds of patterns, especially an adherence to a ports and adapters architecture, has been critical for me in building trading systems."* The key word is *judicious* — adopt what earns its complexity, skip what doesn't.