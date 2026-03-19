# Testing Strategy

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) — Referenced by [Phase 5](05-mcp-server.md), [Phase 1](01-domain-layer.md), [Phase 1A](01a-logging.md), [Phase 2](02-infrastructure.md)
>
> [!NOTE]
> **Logging unit tests (Phase 1A):** The logging infrastructure includes its own comprehensive unit test suite (`test_logging_config.py`) covering `LoggingManager`, `FeatureFilter`, `JsonFormatter`, `RedactionFilter`, and thread safety with concurrent logging. See [Phase 1A §5 — Unit Tests](01a-logging.md) for the full test specification.

---

## MCP Testing Without IDE Restart

Since the MCP server is now written in TypeScript, testing approaches are different from the Python-based workflow. Here are **three approaches**, from fastest to most comprehensive:

### Approach 1: Vitest + Mocked `fetch()` (Recommended for TDD)

```typescript
// Runs entirely in Node.js, no Python backend needed
vi.spyOn(global, 'fetch').mockResolvedValue(
  new Response(JSON.stringify({ status: 'created', exec_id: 'T001' }))
);
// ... call tool handler, verify fetch args and response
```

- **Speed**: ~50ms per test
- **IDE restart**: Never
- **What it tests**: Tool logic, Zod schema validation, response formatting
- **Limitation**: Doesn't test Python REST API integration

### Approach 2: MCP Inspector (Visual Development Tool)

```bash
npx @modelcontextprotocol/inspector
```

- **Speed**: Manual / interactive
- **IDE restart**: Never (separate browser UI)
- **What it tests**: Visual inspection, interactive debugging
- **Use for**: Exploring tool schemas, testing complex arguments

### Approach 3: Vitest with Live Python API (CI/CD)

```typescript
import { spawn, ChildProcess } from 'child_process';

let apiProcess: ChildProcess;

beforeAll(async () => {
  apiProcess = spawn('uv', ['run', '--package', 'zorivest-api',
    'uvicorn', 'zorivest_api.main:app', '--port', '8765']);
  // Poll health endpoint instead of fixed sleep
  const waitForApi = async (url: string, timeoutMs = 10000) => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const res = await fetch(`${url}/health`);
        if (res.ok) return;
      } catch { /* server not ready yet */ }
      await new Promise(r => setTimeout(r, 500));
    }
    throw new Error(`API failed to start within ${timeoutMs}ms`);
  };
  await waitForApi('http://localhost:8765');
});

afterAll(() => apiProcess?.kill());
```

- **Speed**: ~3s startup + test time
- **IDE restart**: Not needed (separate process)
- **What it tests**: Full TypeScript MCP → Python REST round-trip
- **Use for**: CI/CD pipeline and integration verification

### Live Integration Test Example

```typescript
describe('MCP tools against live API', () => {
  it('create_trade round-trip', async () => {
    const res = await fetch('http://localhost:8765/api/v1/trades', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exec_id: 'INT-001', instrument: 'SPY', action: 'BOT',
        quantity: 100, price: 619.61, account_id: 'DU123',
      }),
    });
    const data = await res.json();
    expect(data.status).toBe('created');
  });
});
```

## Test Organization

```bash
# TypeScript MCP tests (fast, mocked)
npx vitest run tests/typescript/mcp/

# TypeScript UI tests
npx vitest run tests/typescript/ui/

# Python unit tests
pytest -m "unit" -x --tb=short

# Python integration tests
pytest -m "integration" -x

# Full suite before commit
pytest -m "not e2e" --tb=short && npx vitest run

# Full CI suite (includes live API integration)
pytest --tb=long -v && npx vitest run --reporter=verbose
```

### Diagnostics, Metrics & GUI Launch Tools

The new MCP tools added in [Phase 5 §5.8–5.11](05-mcp-server.md) follow the standard Vitest + mocked `fetch()` approach (Approach 1):

- **`zorivest_diagnose`** — mock the 4 parallel `fetch()` calls (`/health`, `/version/`, `/mcp-guard/status`, `/market-data/providers`) to test reachable vs unreachable scenarios. Verify API keys are never included in output. Verify unauthenticated mode returns partial results with auth-dependent fields as `"unavailable"`.
- **`MetricsCollector`** — pure unit tests (no mocking needed). Verify percentile calculations, ring buffer bounds, error rate computation, and auto-warnings.
- **`withMetrics()` wrapper** — verify latency recording and error tracking; test composition with `withGuard()`.
- **`zorivest_launch_gui`** — mock `existsSync()` and `exec()` to test all 4 discovery methods, platform-specific launch commands, and the not-installed fallback response.

## Test Infrastructure Setup

### `conftest.py` — Shared Fixtures

```python
# tests/conftest.py

import pytest
from datetime import datetime
from zorivest_core.domain.entities import Trade, ImageAttachment


@pytest.fixture
def sample_trade():
    return Trade(
        exec_id="TEST001",
        time=datetime(2025, 7, 2, 13, 25, 21),
        instrument="SPY STK (USD)",
        action="BOT",
        quantity=100.0,
        price=619.61,
        account_id="DU3584717",
    )


@pytest.fixture
def sample_raw_image():
    """Pre-standardization input: real PNG bytes with correct PNG MIME type."""
    PNG_1X1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
        b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return ImageAttachment(
        data=PNG_1X1,
        mime_type="image/png",
        caption="Test image (raw input)",
        width=1, height=1,
    )


@pytest.fixture
def sample_stored_image():
    """Post-standardization: WebP bytes with image/webp MIME (DB state)."""
    # Minimal valid RIFF/WEBP header for test purposes
    WEBP_STUB = b"RIFF\x00\x00\x00\x00WEBP_test_data"
    return ImageAttachment(
        data=WEBP_STUB,
        mime_type="image/webp",
        caption="Test image (stored WebP)",
        width=1, height=1,
    )


def make_trade(exec_id="TEST001", **overrides):
    defaults = dict(
        exec_id=exec_id,
        time=datetime.now(),
        instrument="SPY STK (USD)",
        action="BOT",
        quantity=100.0,
        price=619.61,
        account_id="DU3584717",
    )
    defaults.update(overrides)
    return Trade(**defaults)


def make_raw_image(data=None, **overrides):
    """Factory for pre-standardization test images (user input)."""
    defaults = dict(
        data=data or b"\x89PNG_fake",
        mime_type="image/png",
        caption="Test (raw)",
        width=100, height=100,
    )
    defaults.update(overrides)
    return ImageAttachment(**defaults)


def make_stored_image(data=None, **overrides):
    """Factory for post-standardization test images (DB state)."""
    defaults = dict(
        data=data or b"RIFF\x00\x00\x00\x00WEBP_fake",
        mime_type="image/webp",
        caption="Test (stored)",
        width=100, height=100,
    )
    defaults.update(overrides)
    return ImageAttachment(**defaults)
```

### `pyproject.toml` — Test Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Pure unit tests",
    "integration: Integration tests with real DB",
    "mcp: MCP protocol tests",
    "e2e: End-to-end tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["packages/*/src"]
omit = ["*/tests/*", "*/__pycache__/*"]
```

## Build Plan Expansion Test Entries

> Source: [Build Plan Expansion Ideas](../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §1–§26
>
> [!NOTE]
> **Services are consolidated** — see [Phase 3](03-service-layer.md) for the full architecture. Pure-math analytics are now domain functions in `domain/analytics/`, not services.

### Python Unit Tests (Consolidated Services)

| Service | Test Module | Key Assertions |
|---------|-------------|----------------|
| `TradeService` (incl dedup, round-trips) | `test_trade_service.py` | Trade create, exec_id dedup, fingerprint dedup, round-trip matching |
| `ImportService` (incl CSV, OFX, QIF, PDF) | `test_import_service.py` | Parser detection, format dispatch, dedup during import |
| `TaxService` | `test_tax_service.py` | Tax estimation, wash sales, lot matching, quarterly estimates |
| `AnalyticsService` (thin orchestrator) | `test_analytics_service.py` | Data fetch + delegation to pure functions |
| `ReportService` (incl trade plans) | `test_report_service.py` | Report CRUD, journal linking, trade plan creation |
| `ReviewService` (mistakes + AI) | `test_review_service.py` | Mistake classification, AI budget enforcement |
| `MarketDataService` | `test_market_data_service.py` | Identifier resolution, options grouping |

### Pure Domain Function Tests (No Mocks, No UoW)

| Function | Test Module | Key Assertions |
|----------|-------------|----------------|
| `calculate_expectancy()` | `test_analytics_expectancy.py` | Win rate, avg win/loss, Kelly % with known datasets |
| `drawdown_probability_table()` | `test_analytics_drawdown.py` | Monte Carlo with seed reproducibility |
| `calculate_sqn()` | `test_analytics_sqn.py` | SQN calculation, grade classification |
| `calculate_mfe_mae()` | `test_analytics_excursion.py` | MFE/MAE/BSO from synthetic bar data |
| `score_execution()` | `test_analytics_quality.py` | NBBO scoring, grade assignment |
| `analyze_pfof()` | `test_analytics_pfof.py` | PFOF cost estimation |
| `analyze_costs()` | `test_analytics_costs.py` | Hidden cost aggregation |
| `breakdown_by_strategy()` | `test_analytics_strategy.py` | Strategy P&L breakdown |
| `trade_fingerprint()` | `test_trade_fingerprint.py` | Hash determinism, collision resistance |

### Hypothesis Property-Based Tests (Math Invariants)

> **Dependency**: `hypothesis` ✅ Installed (`hypothesis>=6.130` in `[dependency-groups] dev`)

All pure analytics functions get property-based tests in `tests/unit/test_analytics_properties.py`:

| Function | Invariant | Strategy |
|----------|-----------|----------|
| `calculate_expectancy()` | Result is always finite; win_rate ∈ [0, 1]; positive when all trades win | `st.lists(st.floats(allow_nan=False), min_size=1)` |
| `drawdown_probability_table()` | max_drawdown_median ≤ 0; equals 0 for monotonically increasing equity | `st.lists(st.floats(min_value=-1e4, max_value=1e4), min_size=2)` |
| `calculate_sqn()` | SQN sign matches expectancy sign (when σ > 0); scales with √N | `st.lists(st.floats(), min_size=5)` |
| Kelly fraction | Always ≤ 1.0; ≤ 0 when sum of returns is negative | Derived from expectancy |
| MFE/MAE | MAE ≤ 0; MFE ≥ 0; for winners MFE ≥ P&L; for losers \|MAE\| ≥ \|P&L\| | `st.floats()` for prices + bar data |

### Math Service Testing Taxonomy

| Function | Example-Based | Property-Based | Golden-File | Edge Cases |
|----------|:---:|:---:|:---:|:---:|
| `calculate_expectancy()` | ✅ Essential | ✅ Essential | 🔶 Recommended | ✅ Essential |
| `drawdown_probability_table()` | ✅ Essential | ✅ Essential | 🔶 Recommended | ✅ Essential |
| `calculate_sqn()` | ✅ Essential | ✅ Essential | ❌ Unnecessary | ✅ Essential |
| `calculate_mfe_mae()` | ✅ Essential | 🔶 Recommended | ❌ Unnecessary | ✅ Essential |

### In-Memory SQLite Integration Tests

> [!IMPORTANT]
> **Mock-only service tests are insufficient** for services that touch the database. TaxService, ImportService, and TradeService MUST have in-memory SQLite integration tests to catch SQL bugs, ORM errors, and constraint violations that mocks cannot detect.

```python
# tests/integration/conftest.py — In-memory SQLite fixture for service integration tests

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from zorivest_infra.database.models import Base
from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def integration_uow():
    """Real UoW against in-memory SQLite — same schema, zero disk I/O."""
    engine = create_engine("sqlite:///:memory:")
    engine.execute("PRAGMA journal_mode=wal")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return SqlAlchemyUnitOfWork(session_factory=Session)
```

| Test Module | Target Service | What Mocks Can't Catch |
|-------------|---------------|------------------------|
| `test_tax_service_integration.py` | TaxService | Wash sale 30-day boundary (SQL date math), FIFO lot ordering |
| `test_import_service_integration.py` | ImportService | Foreign key constraints, dedup hash collision handling |
| `test_trade_service_integration.py` | TradeService | Fingerprint dedup across concurrent creates |

### Synthetic Fixture Corpus (Import Testing)

| Format | Count | Variants |
|--------|-------|----------|
| CSV (broker) | 5–8 files | IBKR FlexQuery, TD Ameritrade, Fidelity, Schwab, Alpaca |
| OFX/QFX | 4–6 files | Chase, Wells Fargo, Citi, BoA |
| QIF | 3–5 files | Quicken export, GnuCash export |
| PDF | 3–4 files | Monthly statement, annual tax summary, trade confirmation |

Fixture location: `tests/fixtures/import/`

### Tax Test Organization (Scenario-Based)

Complex services get scenario-based test files instead of one monolithic file:

```
tests/integration/tax/
├── test_wash_sales.py          # 30-day window, chain detection
├── test_lots.py                # FIFO/LIFO ordering, basis tracking
├── test_quarterly_estimates.py # Q1–Q4 estimation methods
├── test_harvest_scan.py        # Loss harvesting opportunities
└── test_ytd_summary.py         # Year-to-date aggregation
```

### TypeScript MCP Tests (Expansion Tools)

```bash
# Expansion MCP tools (fast, mocked)
npx vitest run tests/typescript/mcp/expansion-tools.test.ts
```

| Tool | Key Assertions |
|------|----------------|
| `sync_broker` | Calls `POST /brokers/{id}/sync`, returns sync result |
| `get_expectancy_metrics` | Passes period and account_id as query params |
| `simulate_drawdown` | Validates simulations range (100–100K) |
| `track_mistake` | Sends category + cost in POST body |
| `import_bank_statement` | Sends file_path + format_hint in POST body |
| `resolve_identifiers` | Sends array of {id_type, id_value} in POST body |

### TypeScript MCP Tests (Discovery Meta-Tools)

> Source: [05j-mcp-discovery.md](05j-mcp-discovery.md) | Vitest + mocked registry

```bash
# Discovery meta-tools (fast, mocked)
npx vitest run tests/typescript/mcp/discovery-tools.test.ts
```

| Tool | Key Assertions |
|------|----------------|
| `list_available_toolsets` | Returns all 8 toolsets with name, description, enabled flag, tool_count |
| `describe_toolset` | Returns tool list with annotations (readOnlyHint, destructiveHint, idempotentHint); error on unknown toolset |
| `enable_toolset` | Toggles enabled state; blocked when MCP Guard is locked; `core` toolset cannot be disabled |
| `get_confirmation_token` | Generates MCP-local crypto-random token for destructive tools; error on non-destructive tools; token expires after TTL |

### Integration Tests (Expansion)

| Category | Test | Approach |
|----------|------|----------|
| Broker Sync | IBKR FlexQuery mock → parse → import | Python integration (mock HTTP) |
| Bank Import | OFX/CSV fixture → parse → dedup → store | Python integration (real DB) |
| Identifier Resolution | OpenFIGI mock → resolve → cache | Python integration (mock HTTP) |
| Analytics → API → MCP | Expectancy via API → MCP tool response | Vitest live API (Approach 3) |

### Phase 10: Service Daemon

> Source: [Phase 10](10-service-daemon.md)

#### TypeScript — Vitest + Mocked `fetch()` (ServiceManager + MCP)

| Component | Key Assertions |
|-----------|----------------|
| `ServiceManager.getStatus()` | Mocks `child_process.execSync` per platform; parses running/stopped + PID |
| `ServiceManager.start()` | Verifies correct OS command dispatched (Windows UAC, `launchctl`, `systemctl`) |
| `ServiceManager.stop()` | Verifies correct OS stop command dispatched |
| `ServiceManager.setAutoStart()` | Mocks `sc config`/`launchctl`/`systemctl enable` commands |
| `zorivest_service_status` | Mocks `fetch(/health)` + `fetch(/service/status)` — reachable and unreachable |
| `zorivest_service_restart` | Mocks `fetch(/service/graceful-shutdown)` + polls for recovery |
| `zorivest_service_logs` | Mocks `fs.readdirSync` — returns log directory path + file list |

#### Python — TestClient Integration

| Test | Endpoint | Key Assertions |
|------|----------|----------------|
| `test_service_status_returns_metrics` | `GET /api/v1/service/status` | PID, uptime, memory, CPU fields present |
| `test_graceful_shutdown` | `POST /api/v1/service/graceful-shutdown` | Returns 200 + `shutting_down` status |
| `test_health_includes_service_fields` | `GET /api/v1/health` | `uptime_seconds`, `scheduler`, `database` present |
| `test_service_endpoints_require_auth` | `GET/POST /api/v1/service/*` | 403 without session |

## Drift-Resistant Feature Validation

> **Status:** Partially implemented — OpenAPI contract CI, repository contract tests, Schemathesis fuzzing, and encryption verification tests are live (Phase 2 of [Test Rigor Audit](../execution/plans/2026-03-16-test-rigor-audit/)). Consumer-driven Pact contracts and mutation testing remain planned.

Beyond standard unit/integration/e2e tests, the following validation layers are required for production-grade drift resistance:

### OpenAPI Contract CI ✅

| Aspect | Detail |
|---|---|
| **Tool** | `tools/export_openapi.py` + `openapi.committed.json` |
| **What it validates** | FastAPI spec hasn't drifted from committed snapshot |
| **When to run** | Every CI run (`.github/workflows/ci.yml`) |
| **Failure policy** | Blocking — spec drift = CI fails |
| **Command** | `uv run python tools/export_openapi.py --check openapi.committed.json` |

### Repository Contract Tests ✅

| Aspect | Detail |
|---|---|
| **File** | `tests/integration/test_repo_contracts.py` (37 tests) |
| **Repos covered** | Trade (8), Account (6), TradePlan (6), TradeReport (4), MarketProviderSettings (6), Image (7) |
| **What it validates** | CRUD round-trip, get-missing, list-all, delete, delete-noop, update for every SQLAlchemy repo |
| **Fixtures** | `tests/integration/conftest.py` — session-scoped engine + per-test savepoint rollback |
| **Command** | `uv run pytest tests/integration/test_repo_contracts.py -v` |

### Schemathesis API Fuzzing ✅ (Local)

| Aspect | Detail |
|---|---|
| **Tool** | `schemathesis>=3.38` + `hypothesis>=6.130` (dev deps) |
| **Runner** | `tools/fuzz_api.py` (supports `--dry-run`, `--endpoints`, `--max-examples`) |
| **What it validates** | Property-based fuzzing of all API endpoints against OpenAPI spec |
| **When to run** | Manual pre-release; CI step deferred to MEU-168 |
| **Command** | `uv run python tools/fuzz_api.py --url http://localhost:8765` |

### Encryption Verification Tests ✅

| Aspect | Detail |
|---|---|
| **File** | `tests/security/test_encryption_integrity.py` (14 tests / 6 classes) |
| **What it validates** | Binary integrity (plaintext not in raw file), PRAGMA checks, key rotation, WAL mode, backup encryption, envelope encryption (passphrase + API key) |
| **Requires** | `sqlcipher3-binary` (skips gracefully when unavailable) |
| **Command** | `uv run pytest tests/security/test_encryption_integrity.py -v` |

### Contract Tests — Consumer-Driven (Planned)

| Aspect | Python Backend → TypeScript MCP/GUI |
|---|---|
| **Tool** | `pact-python` (provider), `@pact-foundation/pact` (consumer) |
| **What it validates** | REST API contracts between Python backend and TypeScript consumers |
| **When to run** | Per-PR (consumer-side), nightly (provider verification) |
| **Failure policy** | Blocking — contract break = merge blocked |

### Property-Based Tests ✅ (Phase 3.1)

| Aspect | Detail |
|---|---|
| **Tool** | `Hypothesis` (Python) |
| **Files** | `tests/property/test_financial_invariants.py` (14), `test_trade_invariants.py` (3), `test_mode_gating_invariant.py` (3), `test_backup_roundtrip.py` (4) |
| **Total tests** | 24 |
| **What it validates** | Financial calc invariants (expectancy, SQN), trade entity roundtrip, MCP Guard mode-gating, backup/restore fidelity |
| **Key invariants** | "Expectancy always finite", "win_rate ∈ [0,1]", "SQN sign matches mean", "locked guard blocks all", "backup → restore preserves data" |
| **When to run** | Per-commit — integrates with pytest |
| **Command** | `uv run pytest tests/property/ -v` |

> [!NOTE]
> **Encryption invariant** (data never readable without key) is covered by Phase 2.4's `tests/security/test_encryption_integrity.py` and not duplicated here.

### MCP Protocol Tests ✅ (Phase 3.2)

| Aspect | Detail |
|---|---|
| **Tool** | Vitest + `InMemoryTransport` (TypeScript) |
| **Files** | `mcp-server/tests/protocol.test.ts` (7), `adversarial.test.ts` (8), `api-contract.test.ts` (8) |
| **Total tests** | 23 |
| **What it validates** | Wire protocol shape, capabilities, tool naming, adversarial input handling (empty/long/unicode/SQLi strings, null args), concurrency safety, OpenAPI alignment |
| **When to run** | Per-commit |
| **Command** | `npx vitest run tests/protocol.test.ts tests/adversarial.test.ts tests/api-contract.test.ts` |

> [!NOTE]
> **Circuit breaker state transition tests** are deferred to **MEU-169** (`guard-auto-trip`). MCP Guard (MEU-38) is implemented with manual lock/unlock + rate limits, but the automatic `CLOSED→OPEN→HALF_OPEN` state machine described in [friction-inventory.md §FR-2.4](friction-inventory.md) and [05-mcp-server.md §5.9](05-mcp-server.md) has not been built yet. Tests will be added when auto-tripping logic is implemented.

### Mutation Testing

| Aspect | Python | TypeScript |
|---|---|---|
| **Tool** | `mutmut` | `StrykerJS` + `@stryker-mutator/vitest-runner` |
| **Target** | `packages/core/src/` (domain + services) | `mcp-server/src/`, `ui/src/` (core logic only) |
| **Starting threshold** | 60% killed | 60% killed |
| **Ratchet policy** | Increase by 5% per phase; target 80% by Phase 4 | Match Python threshold after Phase 6 |
| **When to run** | Nightly + pre-release (expensive) | Nightly + pre-release |
| **Failure policy** | Blocking for release, advisory for PRs |

### Feature Eval Suites

| Category | Definition | Tracking |
|---|---|---|
| **FAIL_TO_PASS** | Tests that failed before the change and pass after | At least one per FIC acceptance criterion |
| **PASS_TO_PASS** | Tests that passed before and still pass after | Full existing suite — zero regressions allowed |

Track eval results per feature in the handoff artifact. Use the following template:

```markdown
### Feature Eval: [Feature Name]

| Criterion | Test | Before | After | Status |
|---|---|---|---|---|
| AC-1 | `test_xyz` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-2 | `test_abc` | FAIL | PASS | ✅ FAIL_TO_PASS |
| (regression) | `test_existing_*` | PASS | PASS | ✅ PASS_TO_PASS |
```

### E2E Testing (Playwright Electron)

> Status: **Scaffolded** — 20 tests in 8 files, activated incrementally via 6 waves (see [06-gui.md](06-gui.md) §E2E Waves).

| Aspect | Detail |
|---|---|
| **Tool** | Playwright `_electron` with `@axe-core/playwright` |
| **Location** | `ui/tests/e2e/` |
| **Config** | `ui/playwright.config.ts` |
| **Runner** | `cd ui && npm run build && npx playwright test` |
| **Workers** | 1 (Electron tests share app state) |

#### Incremental Activation (Waves)

E2E tests activate incrementally as GUI pages are built. Each wave has a gate MEU whose completion enables its tests. See [06-gui.md](06-gui.md) §E2E Waves for the full schedule.

| Wave | Gate MEU | Tests | Cumulative |
|:----:|----------|:-----:|:----------:|
| 0 | MEU-46 `gui-mcp-status` | `launch` (3) + `mcp-tool` (2) | **5** |
| 1 | MEU-47 `gui-trades` | `trade-entry` (5) + `mode-gating` (2) | **12** |
| 2 | MEU-71 `gui-accounts` | `persistence` (2) | **14** |
| 3 | MEU-74 `gui-backup-restore` | `backup-restore` (2) | **16** |
| 4 | MEU-48 `gui-plans` | `position-size` (2) | **18** |
| 5 | MEU-96/99 import GUI | `import` (2) | **20** |

> [!IMPORTANT]
> **Build before every E2E run.** Wave 0 tests require `npm run build` (alias for `electron-vite build`) and a healthy Python backend (automated by `global-setup.ts`). Playwright launches the compiled `out/main/index.js`, not the source files — source changes are invisible until you rebuild. Each subsequent wave additionally requires `data-testid` attributes added to the corresponding GUI components.

#### Infrastructure Files

| File | Purpose |
|---|---|
| `global-setup.ts` | Spawns Python backend, polls `/api/v1/health` with timeout |
| `global-teardown.ts` | Cross-platform tree-kill (`taskkill /T /F` on Windows) |
| `test-ids.ts` | 100+ shared `data-testid` constants (sidebar, trades, settings, calculator, import) |
| `pages/AppPage.ts` | Page Object Model: Electron lifecycle, sidebar navigation, API helpers, `testId()` locator |

#### Test Inventory

| File | Tests | Coverage |
|---|:---:|---|
| `launch.test.ts` | 3 | App launch, backend health, axe-core a11y scan |
| `trade-entry.test.ts` | 5 | Create trade, verify list + API, a11y, visual regression |
| `position-size.test.ts` | 2 | Calculator output, a11y |
| `mode-gating.test.ts` | 2 | Lock disables / unlock enables trade creation |
| `backup-restore.test.ts` | 2 | Backup + restore data fidelity |
| `persistence.test.ts` | 2 | Data + window bounds survive restart |
| `mcp-tool.test.ts` | 2 | MCP guard check + settings API |
| `import.test.ts` | 2 | CSV import → trades in DB, a11y |
| **Total** | **20** | |

#### Accessibility & Visual Regression

- **AxeBuilder** (WCAG 2.1 AA) assertions in `launch`, `trade-entry`, `position-size`, `import` tests
- **`toHaveScreenshot()`** with financial data masking (`balance-amount`, `pnl-value`) in `trade-entry.test.ts`
- Visual regression baselines auto-generated on first run

### Mock-Contract Validation Rule

> [!CAUTION]
> **Unit test mocks must match the real API response shape.** Never hand-write mock response objects from memory or TS-convention guesses.

The `locked` vs `is_locked` bug (Pass 2-3 of GUI review, 2026-03-18) demonstrated this failure mode: all 122 unit tests passed, but the app was broken at runtime because TS interfaces used `locked` while the Python `McpGuardStatus` model returned `is_locked`. The mocks matched the wrong TS interface, masking the contract drift.

**When writing unit tests that mock API responses:**

1. **Check the Python model** — read the Pydantic model or route handler (e.g., `packages/api/src/zorivest_api/routes/`)
2. **Or check the OpenAPI spec** — search `openapi.committed.json` for the endpoint path and response schema
3. **Mirror exact field names** — copy field names into your TS `interface` and mock data

| Source of truth | Location |
|---|---|
| Python Pydantic models | `packages/api/src/zorivest_api/` |
| OpenAPI committed spec | `openapi.committed.json` |
| OpenAPI CI check | `uv run python tools/export_openapi.py --check openapi.committed.json` |
