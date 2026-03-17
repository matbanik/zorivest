# Test Rigor Enhancement — Task List

**Project**: Full test suite rigor audit + architecture enhancement
**Plan**: [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-03-16-test-rigor-audit/implementation-plan.md)
**Research**: `_inspiration/test_rigor_enhancment_research/` (Gemini, GPT-5.4, Claude Opus)
**Baseline**: 1,374 pytest tests (77 Python files) + 17 MCP test files + 8 UI test files
**Target**: ~230 new tests (~1,400 → ~1,630)

---

## Phase 1: Codex IR-5 Audit + Quick Wins (Week 0)

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Audit API route tests (12 files) | `reviewer` | Per-test 🟢/🟡/🔴 rating table | `Get-ChildItem tests/unit/test_api_*.py` | `done` |
| Audit domain model tests (8+ files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/unit/test_entit*,tests/unit/test_enum*,tests/unit/test_value* -File` | `done` |
| Audit service layer tests (10+ files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/unit/test_*service*,tests/unit/test_settings* -File` | `done` |
| Audit infra/pipeline tests (15+ files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/unit/test_backup*,tests/unit/test_csv*,tests/unit/test_pipeline*,tests/unit/test_step* -File` | `done` |
| Audit integration tests (6 files) | `reviewer` | Per-test rating table | `Get-ChildItem tests/integration -File` | `done` |
| Audit MCP server tests (17 files) | `reviewer` | Per-test rating table | `Get-ChildItem mcp-server/tests -File` | `done` |
| Audit UI tests (8 files) | `reviewer` | Per-test rating table | `Get-ChildItem ui/src -Recurse -Include *.test.ts,*.test.tsx` | `done` |


---

## Phase 2: Contract Tests + Adapter Integration (Weeks 1–2, +135 tests)

### 2.1 OpenAPI-as-Contract CI Validation

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Export FastAPI OpenAPI spec + diff gate | `coder` | `tools/export_openapi.py` + `openapi.committed.json` | `uv run python tools/export_openapi.py --check openapi.committed.json` | `done` |
| Create GitHub Actions CI workflow | `coder` | `.github/workflows/ci.yml` | `Test-Path .github/workflows/ci.yml` | `done` |
| Generate Zod schemas from OpenAPI for MCP | `coder` | `mcp-server/src/generated/api-schemas.ts` | — | `deferred` |

### 2.2 Repository Contract Tests

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Create shared conftest with session-scoped engine | `coder` | `tests/integration/conftest.py` | `uv run pytest tests/integration/test_repo_contracts.py --collect-only -q` | `done` |
| Implement contract tests for 6 SQLAlchemy repos | `coder` | 37 tests (Trade, Account, Image, Plan, Report, MarketProvider) | `uv run pytest tests/integration/test_repo_contracts.py -v` | `done` |

### 2.3 Schemathesis API Fuzzing

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Add Schemathesis + Hypothesis to dev deps | `coder` | `pyproject.toml` updated | `uv run python -c "import schemathesis"` | `done` |
| Create API fuzzing runner script | `coder` | `tools/fuzz_api.py` | `Test-Path tools/fuzz_api.py` | `done` |

### 2.4 Encryption Verification Tests

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Binary integrity, PRAGMA, key rotation, WAL, backup, envelope encryption | `coder` | `tests/security/test_encryption_integrity.py` (14 tests / 6 classes) | `uv run pytest tests/security/test_encryption_integrity.py -v` | `done` |

---

## Phase 3: Property-Based Invariants + MCP Tests (Weeks 3–4, +80 tests)

### 3.1 Hypothesis Property-Based Tests for System Invariants

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Invariant 1: No trade record ever lost | `coder` | `tests/property/test_trade_invariants.py` | `uv run pytest tests/property/test_trade_invariants.py -v` | `done` |
| Invariant 2: Encrypted data never readable without key | `coder` | Covered by Phase 2.4 `test_encryption_integrity.py` | `uv run pytest tests/security/test_encryption_integrity.py -v` | `done` |
| Invariant 3: Mode-gating blocks ALL mutations when locked | `coder` | `tests/property/test_mode_gating_invariant.py` | `uv run pytest tests/property/test_mode_gating_invariant.py -v` | `done` |
| Invariant 4: Backup/restore is perfect round-trip | `coder` | `tests/property/test_backup_roundtrip.py` | `uv run pytest tests/property/test_backup_roundtrip.py -v` | `done` |
| Financial calculation invariants | `coder` | `tests/property/test_financial_invariants.py` | `uv run pytest tests/property/test_financial_invariants.py -v` | `done` |

### 3.2 MCP Protocol Tests with InMemoryTransport

> Existing tests in `discovery-tools.test.ts` and `accounts-tools.test.ts` already use `InMemoryTransport`. New tests extend this pattern.

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Protocol integration tests | `coder` | `mcp-server/tests/protocol.test.ts` | `npx vitest run tests/protocol.test.ts` | `done` |
| Adversarial tests: fuzz all tools with malformed input | `coder` | `mcp-server/tests/adversarial.test.ts` | `npx vitest run tests/adversarial.test.ts` | `done` |
| Concurrent tool call tests | `coder` | Included in adversarial file | `npx vitest run tests/adversarial.test.ts -t "concurrent"` | `done` |
| Circuit breaker state transition tests | `coder` | ⏸ DEFERRED — no implementation exists | N/A | `deferred` |
| MCP→FastAPI contract validation | `coder` | `mcp-server/tests/api-contract.test.ts` | `npx vitest run tests/api-contract.test.ts` | `done` |

---

## Phase 4: E2E + GUI Tests (Weeks 5–6, +35 tests)

### 4.1 Playwright Electron Infrastructure

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Create `global-setup.ts` (spawn Python backend) | `coder` | `ui/tests/e2e/global-setup.ts` | `Test-Path ui/tests/e2e/global-setup.ts` | `done` |
| Create `global-teardown.ts` (tree-kill) | `coder` | `ui/tests/e2e/global-teardown.ts` | `Test-Path ui/tests/e2e/global-teardown.ts` | `done` |
| Create `playwright.config.ts` | `coder` | `ui/playwright.config.ts` | `Test-Path ui/playwright.config.ts` | `done` |
| Create Page Object Model classes | `coder` | `ui/tests/e2e/pages/AppPage.ts` | `Test-Path ui/tests/e2e/pages/AppPage.ts` | `done` |
| Create shared `test-ids.ts` constants | `coder` | `ui/tests/e2e/test-ids.ts` | `Test-Path ui/tests/e2e/test-ids.ts` | `done` |

### 4.2 Critical Path E2E Tests (8–12 tests)

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| App launch + health check | `coder` | `ui/tests/e2e/launch.test.ts` | `Test-Path ui/tests/e2e/launch.test.ts` | `done` |
| Trade entry: UI → API → DB → UI display | `coder` | `ui/tests/e2e/trade-entry.test.ts` | `Test-Path ui/tests/e2e/trade-entry.test.ts` | `done` |
| Position sizing: calculator results | `coder` | `ui/tests/e2e/position-size.test.ts` | `Test-Path ui/tests/e2e/position-size.test.ts` | `done` |
| Mode-gating: locked state rejects UI mutations | `coder` | `ui/tests/e2e/mode-gating.test.ts` | `Test-Path ui/tests/e2e/mode-gating.test.ts` | `done` |
| Backup/restore round-trip | `coder` | `ui/tests/e2e/backup-restore.test.ts` | `Test-Path ui/tests/e2e/backup-restore.test.ts` | `done` |
| Dashboard persistence across restart | `coder` | `ui/tests/e2e/persistence.test.ts` | `Test-Path ui/tests/e2e/persistence.test.ts` | `done` |
| MCP tool execution from simulated IDE | `coder` | `ui/tests/e2e/mcp-tool.test.ts` | `Test-Path ui/tests/e2e/mcp-tool.test.ts` | `done` |
| Import flow: CSV → trades in DB | `coder` | `ui/tests/e2e/import.test.ts` | `Test-Path ui/tests/e2e/import.test.ts` | `done` |

### 4.3 Accessibility + Visual Regression

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Axe-core accessibility scans | `coder` | AxeBuilder assertions in launch, trade-entry, position-size, import tests | `rg 'AxeBuilder' ui/tests/e2e/` | `done` |
| Playwright `toHaveScreenshot()` with financial data masking | `coder` | Visual regression in trade-entry test | `rg 'toHaveScreenshot' ui/tests/e2e/` | `done` |

> [!NOTE]
> E2E tests are scaffolded and TypeScript-valid but **cannot execute** until the Electron app is built (`npm run build`) and the Python backend is running. Visual regression baselines will be generated on first run.

---

## Phase 5: Security Pipeline + Agentic Workflow (Week 7)

### 5.1 SAST/DAST CI Pipeline

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Add Semgrep (Python + TypeScript) | `coder` | GitHub Actions step | `semgrep scan --config auto packages/ mcp-server/` | `done` |
| Add Bandit (Python security) | `coder` | GitHub Actions step | `bandit -r packages/ -c pyproject.toml` | `done` |
| Add pip-audit + npm audit | `coder` | GitHub Actions step | `uv run pip-audit; Set-Location mcp-server; npm audit` | `done` |
| Log redaction assertion helpers | `coder` | `tests/security/test_log_redaction_audit.py` | `uv run pytest tests/security/test_log_redaction_audit.py -v` | `done` |

### 5.2 AGENTS.md + Workflow Updates

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Add testing requirements section to AGENTS.md | `coder` | New section in AGENTS.md | `rg "Testing Requirements" AGENTS.md` | `done` |
| Create `/e2e-testing` workflow | `coder` | `.agent/workflows/e2e-testing.md` | `Test-Path .agent/workflows/e2e-testing.md` | `done` |
| Create `/security-audit` workflow | `coder` | `.agent/workflows/security-audit.md` | `Test-Path .agent/workflows/security-audit.md` | `done` |
| Create `e2e-testing` skill | `coder` | `.agent/skills/e2e-testing/SKILL.md` | `Test-Path .agent/skills/e2e-testing/SKILL.md` | `done` |
| Add testing decision framework | `coder` | Decision tree in AGENTS.md | `rg "testing decision framework" AGENTS.md` | `done` |

### 5.3 Quality Gate Architecture

| task | owner_role | deliverable | validation | status |
|------|-----------|-------------|------------|--------|
| Pre-commit: lint + type check + secret detection | `coder` | `.pre-commit-config.yaml` | `Test-Path .pre-commit-config.yaml` | `done` |
| Pre-push: full unit suite + coverage gate | `coder` | Git hook configuration | `Test-Path .git/hooks/pre-push` | `deferred` |
| CI: integration + E2E + security scan | `coder` | GitHub Actions workflow | `Test-Path .github/workflows/ci.yml` | `done` |

---

## Baseline Commands

```powershell
# Current state (as of 2026-03-16)
uv run pytest tests/ --tb=no -q            # 1435 passed, 2 failed, 15 skipped
# 2 failures: test_store_render_step.py (plotly/playwright deps, MEU-87)
Set-Location mcp-server; npx vitest run    # MCP tool tests (183 passed)
uv run ruff check packages/ tests/         # 20 fixable errors

# Weakness pattern scan
rg "hasattr\(" tests/ --count
rg "assert_called_once\(\)" tests/ --count
rg "assert.*> 0" tests/ --count
```
