# Testing strategy for Zorivest: a multi-runtime desktop trading journal

**Zorivest's 1,357 existing tests provide strong unit coverage, but the application has critical gaps at every boundary where its five architectural layers meet.** The most urgent deficiencies are zero end-to-end tests, zero security-specific tests, and zero contract tests between the TypeScript MCP/Electron layers and the Python FastAPI backend. This report lays out a complete testing strategy across five analysis areas — covering testing pyramid design, intent-based invariant testing, Electron GUI testing, MCP protocol testing, and agentic workflow integration — with concrete tools, patterns, and code-level guidance for each.

The central insight: **Zorivest's multi-runtime architecture requires a four-tier testing pyramid** that inserts a contract testing layer between integration and E2E tests. This contract layer is the highest-ROI investment given the TypeScript↔Python boundary. Below is the full strategy.

---

## Analysis 1: A four-tier pyramid bridges two runtimes

The classical 70/20/10 testing pyramid (unit/integration/E2E) breaks down for applications spanning TypeScript and Python runtimes. The adapted pyramid for Zorivest inserts **contract tests as a distinct layer** — a pattern advocated by Chris Richardson, the Pact Foundation, and Google's testing infrastructure team.

### Recommended test distribution

| Layer | Count target | % of suite | Speed | What it validates |
|---|---|---|---|---|
| Unit (pytest + Vitest) | ~1,300 | 78% | 1–5ms each | Domain logic, calculators, React components, value objects |
| Adapter integration (pytest) | ~120 | 7% | 10–50ms each | Repository→SQLCipher, UoW transactions, backup manager, FastAPI TestClient→Service |
| Contract (Pact + OpenAPI) | ~150 | 9% | 50–200ms each | TypeScript↔Python schema sync, MCP tool schemas, Pydantic↔Zod alignment |
| E2E (Playwright Electron) | 8–12 | <1% | 2–10s each | Critical user journeys crossing all runtimes |

The key architectural question — **where to draw integration test boundaries in Clean Architecture** — has a clear answer from the hexagonal architecture testing literature (QWAN, Luís Soares, Zaur Nasibov). The testing unit in hexagonal architecture is the *use case*, a vertical slice from entry point through domain to adapter. The recommended approach: **"vertical tests until proven you shouldn't,"** compromising only when performance, setup complexity, or combinatorial explosions demand it.

For Zorivest, this means three integration boundary tiers. **Tier 1 (highest priority):** adapter integration tests for every SQLAlchemy repository against real SQLCipher using transaction rollback per test. **Tier 2:** vertical integration tests using FastAPI's `TestClient` hitting real services with test databases. **Tier 3:** cross-runtime contract tests for the TypeScript→Python boundary.

### Contract testing: OpenAPI-as-Contract over Pact

For a single-team, single-repo application like Zorivest, **OpenAPI-as-Contract is lighter and more practical than Pact**. FastAPI auto-generates OpenAPI specs from Pydantic type hints at zero extra cost. The pipeline:

1. FastAPI exports `openapi.json` from Pydantic models (already free)
2. **Orval** (`npm install orval`) reads that spec and generates TypeScript clients, React Query hooks, and Zod schemas
3. CI runs two validation gates: `diff` the live spec against the committed spec, then regenerate TypeScript and `git diff --exit-code`

This catches all schema drift automatically. For the MCP layer specifically, where OpenAPI doesn't apply, use **Pact** with TypeScript consumer tests and Python provider verification. Additional tools worth integrating: **Schemathesis** for property-based API fuzzing from OpenAPI specs, and **openapi-zod-client** for generating Zodios clients with runtime validation.

### SQLCipher changes the integration testing calculus

SQLCipher's **AES-256 encryption adds 5–15% overhead** and introduces testing concerns absent from plain SQLite. The strategy: run unit tests against plain in-memory SQLite for speed, run adapter integration tests against **real SQLCipher with a hardcoded test key**, and add a dedicated encryption verification tier. The critical fixture pattern uses session-scoped engines with function-scoped transaction rollback:

```python
@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite+pysqlcipher://:test-key-123@/test.db")

@pytest.fixture(scope="function")
def db_session(engine):
    conn = engine.connect()
    txn = conn.begin()
    session = Session(bind=conn)
    yield session
    session.close()
    txn.rollback()  # Clean state per test, no residual data
    conn.close()
```

The `sqlcipher3` package (v0.6.2+) ships self-contained binary wheels with SQLCipher compiled in — no system dependencies needed, which simplifies CI considerably.

---

## Analysis 2: Intent tests and property-based invariants catch what unit tests miss

Zorivest's existing tests are code correctness tests — they verify *how* things work. **Intent tests verify *what* the system promises**, remaining stable through refactors. Kent Beck's Test Desiderata defines the distinction: tests should be "sensitive to behavior changes and insensitive to structure changes."

The practical difference is stark. A code correctness test asserts `repo._execute("SELECT COUNT(*)")`. An intent test asserts `journal.record_trade(trade); assert journal.find_trade(trade.id).symbol == "AAPL"`. The intent test survives a migration from SQLAlchemy to a different ORM; the code correctness test breaks.

### Four system invariants Zorivest must enforce

Property-based testing with **Hypothesis** transforms invariants from aspirational statements into executable proofs. Hypothesis generates hundreds of random inputs and tries to *falsify* each property, then *shrinks* failures to minimal counterexamples.

**Invariant 1: No trade record is ever lost.** The `RuleBasedStateMachine` is the gold standard here — it models the journal as a state machine with lock/unlock/CRUD rules and checks `trade_count == len(model_trades)` after every operation. Hypothesis explores random operation sequences, including edge cases a human would never think to test.

**Invariant 2: Encrypted data is never readable without the key.** After writing known trade symbols to the database, read the raw `.db` file bytes and assert no plaintext symbols appear. Verify that opening the database with a wrong key raises `DatabaseDecryptionError`.

**Invariant 3: Mode-gating blocks ALL mutations when locked.** Enumerate every mutation method on the journal (using `inspect.getmembers` or decorators) and use `@given(st.sampled_from(MUTATION_METHODS))` to assert that every single one raises `LockedModeError` in locked state. This is exhaustive by design — new mutation methods are automatically covered.

**Invariant 4: Backup/restore is a perfect round-trip.** For any set of trades, `restore(backup(trades)) == trades`. This uses the *invertibility* property pattern from Scott Wlaschin's seven property-based testing patterns.

### Hypothesis strategies for financial data

The `st.decimals(min_value="0.01", max_value="999999.99", places=2, allow_nan=False)` strategy generates financially valid prices. Composite strategies combine symbol, direction, quantity, price, and date into full `TradeRecord` objects. Configure Hypothesis profiles — **50 examples locally, 1,000 in CI** — to balance speed and thoroughness.

Crash recovery testing complements property-based testing. The pattern: insert 10 trades, begin a transaction for trade 11, simulate a crash (raise an exception inside the transaction), reopen the journal, and assert all 10 original trades survive. For backup testing, verify the backup file doesn't contain `b"SQLite format 3"` (the plaintext SQLite header) and doesn't contain any known trade symbols as raw bytes.

---

## Analysis 3: Playwright bridges Electron, Python, and SQLCipher in E2E tests

Playwright's experimental Electron support via `_electron.launch()` is the **only mature option for E2E testing Electron apps** in 2024–2025, endorsed by Electron's official documentation and used in production by teams including Kubeshop, Actual Budget, and Datasette Desktop.

### Multi-process lifecycle management

The core challenge is orchestrating three processes: Python backend, Electron app, and SQLCipher database. The recommended pattern uses Playwright's `globalSetup` to spawn the Python backend, health-check it, and store the PID for teardown:

```typescript
// global-setup.ts
const backendProcess = spawn('python', [
  '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8765'
], { env: { ...process.env, ZORIVEST_ENV: 'test', SQLCIPHER_KEY: 'test-key' } });

await waitForServer('http://127.0.0.1:8765/health', 30000);
process.env.BACKEND_PID = String(backendProcess.pid);
```

Use the `tree-kill` npm package in teardown to kill the entire process tree — Python may spawn subprocesses that `process.kill()` alone won't reach. On CI, add a post-step `pkill -f uvicorn` as a safety net against zombies.

### State isolation: template databases

**Fresh SQLCipher database per test file** is the sweet spot between isolation and speed. Pre-create an encrypted template database with seed data, copy it per test suite, and point the backend at it. For per-test reset within a suite, expose a test-only `POST /__test__/reset-db` endpoint (guarded by `ZORIVEST_ENV == "test"`). Each parallel worker gets its own database file — SQLCipher uses file-level locking that prevents sharing.

### Assertion strategy and financial data

E2E tests should assert primarily at the **UI level** (what users see), with spot-check API assertions for verification, and rare database assertions only for encryption verification. Never assert at all three levels for the same thing. For financial data, use **tolerance-based assertions** (`expect(pnl).toBeCloseTo(1234.56, 2)`) for calculated values and exact string matching (`toHaveText('$1,234.56')`) for formatted display values. Freeze timestamps in test fixtures using Playwright's clock API.

### Page Object Model for Electron

Playwright officially recommends POM, and it adapts cleanly to Electron. Create one POM per major view (TradingJournalPage, SettingsPage, ImportPage), inject them via Playwright fixtures, and keep actions in the POM while keeping assertions in the test. Centralize test IDs in a shared `testIds.ts` constants file imported by both React components and test code.

### Parallelization with dynamic port allocation

Each parallel worker needs its own Python backend instance on a unique port (`8765 + testInfo.workerIndex`), its own database file, and its own Electron instance. Use Playwright's worker-scoped fixtures for lifecycle management and native sharding (`--shard=1/4`) for CI-level distribution across machines. **Start with `workers: 1`** until the infrastructure is stable, then scale up.

For selectors, prefer `getByRole()` (tests accessibility, most resilient), `getByText()` (user-facing content), then `getByTestId()` (stable contract). Avoid CSS class selectors, XPath, and auto-generated IDs.

---

## Analysis 4: MCP testing requires three layers and adversarial thinking

Testing 40+ MCP tools requires a structured approach spanning unit, integration, and adversarial testing. The **gold standard** is the MCP SDK's `InMemoryTransport`, which creates paired client-server connections without subprocess overhead:

```typescript
const server = createServer(); // Your server factory
const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
await server.connect(serverTransport);

const client = new Client({ name: "test-client", version: "1.0.0" });
await client.connect(clientTransport);

const { tools } = await client.listTools();
const result = await client.callTool("record_trade", { symbol: "AAPL", qty: 100 });
```

This is the approach used by the MCP SDK's own test suite (which uses Vitest internally) and the community reference repository `mkusaka/mcp-server-e2e-testing-example`.

### Three-layer MCP test architecture

**Layer 1 — Unit tests for tool handlers:** Extract each tool handler as a standalone async function and test it directly with Vitest. Mock the HTTP backend with MSW (Mock Service Worker). This covers input validation, business logic, and error handling for each of the 40+ tools.

**Layer 2 — Protocol integration tests with InMemoryTransport:** Test the full JSON-RPC protocol flow including initialization, tool discovery (`tools/list`), tool execution (`tools/call`), and error handling. Verify JSON-RPC error codes: `-32700` for parse errors, `-32601` for method not found, `-32602` for invalid params.

**Layer 3 — Adversarial and scenario tests:** AI agents call tools in unpredictable ways. Fuzz every tool with empty objects, null values, extremely long strings, SQL injection payloads, and unknown parameters. Test tools called in wrong order, rapid repeated calls, and concurrent calls with `Promise.all()`. Verify that failures return `isError: true` with descriptive messages rather than crashing the server.

### Contract testing for the MCP→FastAPI boundary

Create a custom test suite that validates each MCP tool's input schema against the corresponding FastAPI endpoint's OpenAPI schema using Ajv. When the FastAPI spec changes, these tests fail immediately, catching drift before it reaches production. The error mapping chain — Python exception → HTTP status → MCP error code — must be explicitly tested: mock the backend returning 404, 422, 500, and timeout, then verify each maps to the correct MCP response.

### Circuit breaker testing

If using Opossum (the leading Node.js circuit breaker), test all five transitions: closed→open (after error threshold), open→rejected (fail-fast), open→half-open (after reset timeout), half-open→closed (recovery), half-open→open (still failing). Use `vi.useFakeTimers()` to control the reset timeout. In integration tests, force the circuit open by failing the backend, then verify MCP tool calls return fast fallback responses (under 100ms) rather than hanging.

The **MCP Inspector** (`@modelcontextprotocol/inspector`) provides manual validation during development and a CLI mode for CI automation. The official `modelcontextprotocol/conformance` repository contains standardized conformance tests worth running against Zorivest's MCP server.

---

## Analysis 5: Agentic workflows need AGENTS.md, TDD, and layered quality gates

AGENTS.md — now stewarded by the **Agentic AI Foundation under the Linux Foundation** — is supported by Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and 60,000+ open-source projects. For a multi-runtime application like Zorivest, **hierarchical AGENTS.md files** provide runtime-specific guidance: a root file with universal rules, plus subdirectory files for `frontend/`, `backend/`, `tests/security/`, and `tests/e2e/`.

### The agentic TDD workflow

The recommended workflow, drawn from Tweag's Agentic Coding Handbook and McKinsey's QuantumBlack research, treats **tests as prompts** that constrain AI agents toward correct behavior:

1. Agent reads AGENTS.md, identifies affected runtimes and required test types
2. Agent writes or updates tests *first* (TDD), following the decision framework below
3. Agent implements code to pass those tests
4. Automated validation runs: lint, type check, unit tests, security scan
5. Decision gate evaluates whether E2E tests are needed
6. CI pipeline validates everything independently
7. Human reviews the PR

### When E2E tests are mandatory vs optional

**Require E2E** when the change touches: IPC bridge between Electron and Python, authentication or session management, routing or navigation, backup/restore workflows, database schema or encryption, or any multi-step user workflow. **Unit/integration only** suffices for: pure business logic, single-component UI changes, backend utilities, documentation, and test-only changes.

### Four-layer quality gate architecture

- **Pre-commit (instant):** lint changed files, type check, secret detection with GitLeaks, fast unit tests
- **Pre-push (comprehensive):** full unit suite, coverage gate (≥80% on new code), Bandit/Semgrep security scan
- **CI pipeline (authoritative):** all previous checks plus integration tests, E2E tests across OS matrix (Ubuntu/macOS/Windows), CodeQL deep analysis, SBOM generation
- **PR review (human + AI):** mandatory human security review for changes touching encryption, auth, or schema

### OWASP adaptation for local-first desktop apps

The **OWASP Desktop App Security Top 10** and the newer **DASVS (Desktop Application Security Verification Standard)** from AFINE provide the security testing framework. Zorivest should target **DASVS Level 2** (enhanced, for sensitive data) with Level 3 controls for cryptography. The critical security tests: verify API binds to `127.0.0.1` only, verify no plaintext in database file bytes, verify backup files are encrypted (no `SQLite format 3` header), verify wrong key fails with clear error, verify no sensitive data in logs, and run `npm audit` + `pip-audit` + Semgrep on every commit.

---

## Concrete implementation roadmap

The strategy above represents approximately **250 new tests** bringing Zorivest from 1,357 to ~1,600. Prioritized by impact:

**Phase 1 (Week 1–2): Contract and adapter tests.** Add OpenAPI-as-Contract CI validation with Orval codegen. Expand adapter integration tests for all repositories against real SQLCipher. Add 15 encryption verification tests. Estimated: +135 tests.

**Phase 2 (Week 3–4): Property-based invariants and MCP tests.** Implement Hypothesis stateful tests for the four system invariants. Add InMemoryTransport-based MCP protocol tests for all 40+ tools. Add circuit breaker state transition tests. Estimated: +80 tests.

**Phase 3 (Week 5–6): E2E and agentic infrastructure.** Set up Playwright Electron with global setup/teardown for the Python backend. Implement 8–12 E2E tests for critical paths (launch, trade entry, dashboard, persistence across restart, backup/restore, mode-gating). Deploy hierarchical AGENTS.md and four-layer quality gates. Estimated: +35 tests.

The result is a testing strategy where **every architectural boundary is guarded by the right type of test at the right level of the pyramid** — unit tests for domain logic, adapter integration tests for SQLCipher, contract tests for TypeScript↔Python, property-based tests for system invariants, MCP protocol tests for AI tool interactions, and a thin E2E layer for the critical paths that tie everything together.
