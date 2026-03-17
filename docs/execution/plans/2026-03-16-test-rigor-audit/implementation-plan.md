# Test Rigor Enhancement — Full Strategy

Synthesized from deep research by Gemini 3.1 Pro, GPT-5.4, and Claude Opus 4.6. Sources at `_inspiration/test_rigor_enhancment_research/`.

## Problem Statement

Zorivest has 1,374 passing tests across 77 Python files, plus 17 MCP server and 8 UI test files — excellent unit coverage with AC traceability, frozen-dataclass enforcement, and import-surface constraints. **But the suite has gaps at several boundaries where the five architectural layers meet:**

| Gap | Risk |
|-----|------|
| Zero E2E tests | GUI→API→DB round-trips untested; IPC failures invisible |
| Zero contract tests | TypeScript MCP ↔ Python API schema drift undetected |
| Limited security tests | Log redaction + API key encryption exist, but no comprehensive security suite (SQLCipher integrity, mode-gating sweep, binary encryption proof) |
| Zero property-based tests | Financial calculation edge cases (overflow, NaN, precision) uncaught |
| Limited GUI tests | 8 UI test files via Vitest, but no E2E Playwright tests |

## Proposed Architecture: Four-Tier Testing Pyramid

All three research sources converge on a **four-tier pyramid** with a contract layer inserted between integration and E2E:

```
                    ┌─────────────┐
                    │    E2E      │  8–12 tests, Playwright Electron
                    │  (<1%)      │  GUI → IPC → API → DB → GUI
                   ─┤─────────────├─
                  │   Contract     │  ~150 tests, OpenAPI + Pact + Zod
                  │   (9%)         │  TS↔Python schema sync, MCP schemas
                 ─┤───────────────├─
               │  Integration       │  ~120 tests, pytest + real SQLCipher
               │  (7%)              │  Repo→DB, API→Service→Repo, UoW
              ─┤───────────────────├─
            │    Unit Tests          │  ~1,374+ tests (existing)
            │    (78%)               │  Domain, services, handlers, components
            ─┴───────────────────────┴─
```

**Target**: ~230 new tests bringing total from ~1,400 to ~1,630.

---

## Phase 1: Codex IR-5 Audit + Quick Wins (Week 0)

> **Owner**: Codex validation agent
> **Goal**: Audit existing tests for assertion strength, fix identified weaknesses

### Task 1.1: IR-5 Test Rigor Audit (Codex)

Rate every test function 🟢/🟡/🔴 per IR-5 criteria across all 77 Python, 17 MCP, and 8 UI test files.

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Audit API route tests (12 files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/unit/test_api_*.py` | `pending` |
| Audit domain model tests (8+ files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/unit/test_entit*,tests/unit/test_enum*,tests/unit/test_value* -File` | `pending` |
| Audit service layer tests (10+ files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/unit/test_*service*,tests/unit/test_settings* -File` | `pending` |
| Audit infra/pipeline tests (15+ files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/unit/test_backup*,tests/unit/test_csv*,tests/unit/test_pipeline*,tests/unit/test_step* -File` | `pending` |
| Audit integration tests (6 files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/integration -File` | `pending` |
| Audit MCP server tests (17 files) | `reviewer` | Per-test rating table | `Get-ChildItem mcp-server/tests -File` | `pending` |
| Audit UI tests (8 files) | `reviewer` | Per-test rating table | `Get-ChildItem ui/src -Recurse -Include *.test.ts,*.test.tsx` | `pending` |
| Synthesize findings | `reviewer` | Summary report + verdict | `$f='.agent/context/handoffs/2026-03-16-test-rigor-audit-plan-critical-review.md'; (Select-String -Path $f -Pattern 'Per-test.*rating' -Quiet) -and (Select-String -Path $f -Pattern 'Summary' -Quiet) -and (Select-String -Path $f -Pattern 'verdict' -Quiet)` | `pending` |

**Specific weakness patterns to scan for** (from prior analysis):
- Tautological StrEnum assertion in `test_enums.py`
- `hasattr` checks instead of value assertions in `test_system_service.py`
- `_loaded_at` internal state manipulation in `test_settings_cache.py`
- Status-code-only API assertions without body validation
- `assert_called_once()` without argument verification

---

## Phase 2: Contract Tests + Adapter Integration (Weeks 1–2, est. +135 tests)

> **Owner**: Opus implementation agent
> **Goal**: Guard every architectural boundary with the right type of test

### Task 2.1: OpenAPI-as-Contract CI Validation

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Export FastAPI OpenAPI spec to `openapi.json` in CI | `coder` | CI step generating spec | `uv run python -c "from zorivest_api.main import create_app; import json; print(json.dumps(create_app().openapi()))"` | `pending` |
| Add `diff` gate: committed spec vs live spec | `coder` | CI fails on schema drift | `git diff --no-index --exit-code openapi.json openapi.committed.json` | `pending` |
| Generate Zod schemas from OpenAPI for MCP server | `coder` | `mcp-server/src/generated/api-schemas.ts` | `npx orval --output mcp-server/src/generated/` | `pending` |

**Research-backed**: OpenAPI-as-Contract lighter than Pact for single-repo (Claude), Schemathesis for fuzzing (Gemini), Pact examples (ChatGPT)

### Task 2.2: Repository Contract Tests (SQLCipher)

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Create abstract `RepositoryContractTestSuite` base class | `coder` | `tests/integration/conftest_contracts.py` | `uv run pytest tests/integration/conftest_contracts.py --collect-only -q` | `pending` |
| Implement contract tests for each SQLAlchemy repository | `coder` | Contract tests for Trade, Account, Image, Plan, Report, Watchlist repos | `uv run pytest tests/integration/test_repo_contracts.py -v` | `pending` |
| Add session-scoped SQLCipher engine with per-test transaction rollback | `coder` | Fixture in `tests/integration/conftest.py` | `uv run pytest tests/integration/ -k "sqlcipher" --collect-only -q` | `pending` |

**Research-backed** pattern (Claude + Gemini):
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
    txn.rollback()
    conn.close()
```

### Task 2.3: Schemathesis API Fuzzing

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Add Schemathesis as dev dependency | `coder` | `pyproject.toml` updated | `uv run schemathesis run http://localhost:8765/openapi.json` | `pending` |
| Create CI step for API property-based fuzzing | `coder` | GitHub Actions step | `uv run schemathesis run http://localhost:8765/openapi.json --dry-run` | `pending` |

**Research-backed**: unanimous recommendation across all three research sources for OpenAPI-based API fuzzing.

### Task 2.4: Encryption Verification Tests (+15 tests)

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Binary integrity test: known data not readable in raw file | `coder` | `tests/security/test_encryption_integrity.py` | `uv run pytest tests/security/test_encryption_integrity.py -k "binary" -v` | `pending` |
| PRAGMA integrity_check test | `coder` | Test in same file | `uv run pytest tests/security/test_encryption_integrity.py -k "pragma" -v` | `pending` |
| Wrong-key-fails test | `coder` | Test in same file | `uv run pytest tests/security/test_encryption_integrity.py -k "wrong_key" -v` | `pending` |
| Key rotation test | `coder` | Test in same file | `uv run pytest tests/security/test_encryption_integrity.py -k "rotation" -v` | `pending` |
| Backup file encryption test | `coder` | Test in same file | `uv run pytest tests/security/test_encryption_integrity.py -k "backup" -v` | `pending` |

**Research-backed**: binary hex-dump (Gemini), backup file header check (Claude), PRAGMA integrity_check (ChatGPT)

---

## Phase 3: Property-Based Invariants + MCP Tests (Weeks 3–4, est. +80 tests)

> **Owner**: Opus implementation agent

### Task 3.1: Hypothesis Property-Based Tests for System Invariants

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| **Invariant 1**: No trade record is ever lost | `coder` | `tests/property/test_trade_invariants.py` | `uv run pytest tests/property/test_trade_invariants.py -v` | `pending` |
| **Invariant 2**: Encrypted data never readable without key | `coder` | Combined with encryption tests | `uv run pytest tests/security/test_encryption_integrity.py -k "hypothesis" -v` | `pending` |
| **Invariant 3**: Mode-gating blocks ALL mutations when locked | `coder` | `tests/property/test_mode_gating_invariant.py` | `uv run pytest tests/property/test_mode_gating_invariant.py -v` | `pending` |
| **Invariant 4**: Backup/restore is perfect round-trip | `coder` | `tests/property/test_backup_roundtrip.py` | `uv run pytest tests/property/test_backup_roundtrip.py -v` | `pending` |
| Financial calculation invariants | `coder` | `tests/property/test_financial_invariants.py` | `uv run pytest tests/property/test_financial_invariants.py -v` | `pending` |

**Research-backed** Hypothesis strategies (ChatGPT + Claude):
```python
prices = st.decimals(min_value="0.01", max_value="999999.99", places=2, allow_nan=False)
# Profile: 50 examples locally, 1,000 in CI
settings.register_profile("ci", max_examples=1000)
```

### Task 3.2: MCP Protocol Tests with InMemoryTransport

> **Note**: MCP tests in `discovery-tools.test.ts` and `accounts-tools.test.ts` already use `InMemoryTransport`. New tests extend this existing pattern to cover protocol conformance, adversarial inputs, and contract validation.

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Protocol integration tests (InMemoryTransport) | `coder` | `mcp-server/tests/protocol.test.ts` | `npx vitest run mcp-server/tests/protocol.test.ts` | `pending` |
| Adversarial tests: fuzz all tools with malformed input | `coder` | `mcp-server/tests/adversarial.test.ts` | `npx vitest run mcp-server/tests/adversarial.test.ts` | `pending` |
| Concurrent tool call tests | `coder` | Test in adversarial file | `npx vitest run mcp-server/tests/adversarial.test.ts -t "concurrent"` | `pending` |
| Circuit breaker state transition tests | `coder` | `mcp-server/tests/circuit-breaker.test.ts` | `npx vitest run mcp-server/tests/circuit-breaker.test.ts` | `pending` |
| MCP→FastAPI contract validation | `coder` | `mcp-server/tests/api-contract.test.ts` | `npx vitest run mcp-server/tests/api-contract.test.ts` | `pending` |

**Research-backed** pattern (Claude — InMemoryTransport):
```typescript
const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
await server.connect(serverTransport);
const client = new Client({ name: "test-client", version: "1.0.0" });
await client.connect(clientTransport);
```

---

## Phase 4: E2E + GUI Tests (Weeks 5–6, est. +35 tests)

> **Owner**: Opus implementation agent

### Task 4.1: Playwright Electron Infrastructure

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Create `global-setup.ts` to spawn Python backend | `coder` | `tests/e2e/global-setup.ts` | `Test-Path tests/e2e/global-setup.ts` | `pending` |
| Create `global-teardown.ts` with tree-kill | `coder` | `tests/e2e/global-teardown.ts` | `Test-Path tests/e2e/global-teardown.ts` | `pending` |
| Create Golden Master encrypted test database | `coder` | `tests/e2e/fixtures/golden_seed.db` | `Test-Path tests/e2e/fixtures/golden_seed.db` | `pending` |
| Create Page Object Model classes | `coder` | `tests/e2e/pages/` | `Get-ChildItem tests/e2e/pages -File` | `pending` |
| Create shared `testIds.ts` constants | `coder` | `tests/e2e/test-ids.ts` | `Test-Path tests/e2e/test-ids.ts` | `pending` |

### Task 4.2: Critical Path E2E Tests (8–12 tests)

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| App launch + health check | `coder` | `tests/e2e/launch.test.ts` | `Test-Path tests/e2e/launch.test.ts` | `pending` |
| Trade entry: UI → API → DB → UI display | `coder` | `tests/e2e/trade-entry.test.ts` | `Test-Path tests/e2e/trade-entry.test.ts` | `pending` |
| Position sizing: calculator displays correct results | `coder` | `tests/e2e/position-size.test.ts` | `Test-Path tests/e2e/position-size.test.ts` | `pending` |
| Mode-gating: locked state rejects UI mutations | `coder` | `tests/e2e/mode-gating.test.ts` | `Test-Path tests/e2e/mode-gating.test.ts` | `pending` |
| Backup/restore round-trip | `coder` | `tests/e2e/backup-restore.test.ts` | `Test-Path tests/e2e/backup-restore.test.ts` | `pending` |
| Dashboard persistence across restart | `coder` | `tests/e2e/persistence.test.ts` | `Test-Path tests/e2e/persistence.test.ts` | `pending` |
| MCP tool execution from simulated IDE | `coder` | `tests/e2e/mcp-tool.test.ts` | `Test-Path tests/e2e/mcp-tool.test.ts` | `pending` |
| Import flow: CSV → trades in DB | `coder` | `tests/e2e/import.test.ts` | `Test-Path tests/e2e/import.test.ts` | `pending` |

### Task 4.3: Automated Accessibility + Visual Regression

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Add Axe-core accessibility scans to E2E suite | `coder` | Axe assertions in E2E tests | `$d='tests/e2e/*.test.ts'; (Select-String -Path $d -Pattern 'AxeBuilder' -Quiet) -and (Select-String -Path $d -Pattern 'toHaveNoViolations' -Quiet)` | `pending` |
| Add Playwright `toHaveScreenshot()` with financial data masking | `coder` | Visual regression baselines | `$d='tests/e2e/*.test.ts'; (Select-String -Path $d -Pattern 'toHaveScreenshot' -Quiet) -and (Select-String -Path $d -Pattern 'mask:' -Quiet)` | `pending` |

---

## Phase 5: Security Pipeline + Agentic Workflow Updates (Week 7)

> **Owner**: Opus implementation agent

### Task 5.1: SAST/DAST CI Pipeline

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Add Semgrep to CI (Python + TypeScript) | `coder` | GitHub Actions step | `semgrep scan --config auto packages/ mcp-server/` | `pending` |
| Add Bandit to CI (Python security) | `coder` | GitHub Actions step | `bandit -r packages/ -c pyproject.toml` | `pending` |
| Add pip-audit + npm audit to CI | `coder` | GitHub Actions step | `uv run pip-audit; Set-Location mcp-server; npm audit` | `pending` |
| Add log redaction assertion helpers | `coder` | `tests/security/test_log_redaction_audit.py` | `uv run pytest tests/security/test_log_redaction_audit.py -v` | `pending` |

### Task 5.2: AGENTS.md + Workflow Updates

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Add test rigor rules to AGENTS.md | `coder` | New "Testing Requirements" section | `rg "Testing Requirements" AGENTS.md` | `pending` |
| Create `/e2e-testing` workflow | `coder` | `.agent/workflows/e2e-testing.md` | `Test-Path .agent/workflows/e2e-testing.md` | `pending` |
| Create `/security-audit` workflow | `coder` | `.agent/workflows/security-audit.md` | `Test-Path .agent/workflows/security-audit.md` | `pending` |
| Create `e2e-testing` skill | `coder` | `.agent/skills/e2e-testing/SKILL.md` | `Test-Path .agent/skills/e2e-testing/SKILL.md` | `pending` |
| Add testing decision framework to AGENTS.md | `coder` | Decision tree in AGENTS.md | `rg "testing decision framework" AGENTS.md` | `pending` |

### Task 5.3: Quality Gate Architecture

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Pre-commit: lint + type check + secret detection | `coder` | `.pre-commit-config.yaml` | `Test-Path .pre-commit-config.yaml` | `pending` |
| Pre-push: full unit suite + coverage gate | `coder` | Git hook configuration | `Test-Path .git/hooks/pre-push` | `pending` |
| CI: integration + E2E + security scan | `coder` | GitHub Actions workflow | `Test-Path .github/workflows/ci.yml` | `pending` |

---

## Tool Consensus Across Research Sources

| Tool/Approach | Gemini | GPT-5.4 | Claude | Verdict |
|---------------|--------|---------|--------|---------|
| **Playwright** (E2E) | ✅ Definitive | ✅ Mature | ✅ Only mature option | **Adopt** |
| **Hypothesis** (property) | — | ✅ High-value for finance | ✅ Gold standard | **Adopt** |
| **Schemathesis** (API fuzz) | ✅ Mature | ✅ Mature | ✅ Recommended | **Adopt** |
| **OpenAPI-as-Contract** | ✅ Over Pact | — | ✅ Lighter for monorepo | **Adopt** |
| **InMemoryTransport** (MCP) | — | — | ✅ Gold standard | **Adopt** |
| **Axe-core** (accessibility) | ✅ Industry std | ✅ Catches DOM errors | — | **Adopt** |
| **Semgrep + Bandit** (SAST) | ✅ High maturity | ✅ 5/5 maturity | ✅ Recommended | **Adopt** |
| **Binary encryption test** | ✅ Hex-dump | ✅ PRAGMA integrity | ✅ File bytes | **Adopt** |
| **Pact** (contract) | ✅ For MCP↔API | ✅ Mature | ✅ Only for MCP layer | **Selective** |
| **XState** (model-based) | ✅ Recommended | — | — | **Explore later** |
| **Applitools/Percy** (visual AI) | ✅ Mentioned | ✅ Mentioned | — | **Explore later** |

## Verification Plan

### Automated Tests
```powershell
# Phase 1: Existing test rigor (Codex audit)
uv run pytest tests/ -x --tb=short -q

# Phase 2: Contract + integration
uv run pytest tests/integration/ -v
uv run schemathesis run http://localhost:8765/openapi.json

# Phase 3: Property-based + MCP
uv run pytest tests/property/ -v --hypothesis-show-statistics
Set-Location mcp-server; npx vitest run tests/protocol.test.ts tests/adversarial.test.ts

# Phase 4: E2E
Set-Location tests/e2e; npx playwright test --reporter=html

# Phase 5: Security pipeline
semgrep scan --config auto packages/ mcp-server/src/
bandit -r packages/ -c pyproject.toml
pip-audit
Set-Location mcp-server; npm audit
```

### Manual Verification
- Review Codex IR-5 audit report for completeness
- Spot-check Hypothesis shrink output for financial edge cases
- Visually inspect Playwright E2E test recordings
- Verify Axe-core output excludes charting library false positives
