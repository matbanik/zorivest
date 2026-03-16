# Test Rigor Audit — Full Suite

Perform a comprehensive test rigor audit of all 75 test files (69 unit + 6 integration) containing 1,357 tests. This is a **review-only** task — no code changes, only findings.

## Context

The test suite has been built using strict TDD red-phase protocol across 50+ MEUs. Each test file is linked to FIC acceptance criteria. This audit evaluates whether the tests provide meaningful behavioral coverage or contain weak/vacuous assertions that could pass even with broken production code.

## Grading Criteria (from IR-5)

| Rating | Definition | Example |
|--------|------------|---------|
| 🟢 Strong | Asserts specific values, exercises real behavior, tests both positive and negative paths | `assert delta.days == 30`, `assert result == expected_bytes` |
| 🟡 Adequate | Tests the right thing but uses weak assertions (key-exists, non-empty, mock-was-called without arg check) or couples to private internals | `assert "key" in result`, `mock.assert_called_once()` without verifying args |
| 🔴 Weak | Trivially passes even if code is broken: try/except swallows failures, only checks types not values, patches a private method that may not exist | `try: fn() except: assert dir.exists()` |

### Common Weakness Patterns to Flag

- **Try/except safety nets** that let tests pass when the feature under test actually fails
- **Asserting only key existence** instead of checking the returned value
- **Patching private methods** (`_check_cache`, `_internal`) — fragile; if renamed the patch is silently ignored
- **Testing only the "not found" path** without an insert+get round-trip
- **Missing boundary assertions** — e.g., testing a 30-day delta but only asserting `start < end`
- **Data format assertions** — checking a data URI key exists but not the prefix or payload size
- **Tautological assertions** — condition and assertion are identical (always true)
- **`hasattr` checks** instead of asserting actual field values

## Proposed Tasks

> **Owner**: Codex validation agent
> **Workflow**: `/critical-review-feedback` (IR-5 test rigor audit mode)

### Task 1: Unit Test Layer — API Routes (16 files)

| Field | Value |
|-------|-------|
| **task** | Audit all API route test files for assertion strength |
| **owner_role** | `reviewer` |
| **deliverable** | Per-test 🟢/🟡/🔴 rating table for all 16 API test files |
| **validation** | `Get-ChildItem tests/unit/test_api_*.py` — audit each file |
| **status** | `pending` |

**Files in scope**:
- `test_api_accounts.py`, `test_api_analytics.py`, `test_api_auth.py`
- `test_api_foundation.py`, `test_api_plans.py`, `test_api_reports.py`
- `test_api_settings.py`, `test_api_system.py`, `test_api_tax.py`
- `test_api_trades.py`, `test_api_watchlists.py`
- `test_api_key_encryption.py`
- Plus any remaining `test_api_*.py` files

**Specific concerns to check**:
- Status-code-only assertions without response body validation
- `assert_called_once()` without verifying call arguments
- Parametrized tests that only check status codes (e.g., tax endpoint existence tests)

---

### Task 2: Unit Test Layer — Domain Model (8+ files)

| Field | Value |
|-------|-------|
| **task** | Audit domain entity, enum, event, and exception tests |
| **owner_role** | `reviewer` |
| **deliverable** | Per-test 🟢/🟡/🔴 rating table for all domain test files |
| **validation** | Audit: `test_entities.py`, `test_enums.py`, `test_events.py`, `test_exceptions.py`, `test_calculator.py`, `test_analytics.py`, `test_account_review.py` |
| **status** | `pending` |

**Specific concerns to check**:
- Tautological assertions (condition identical to assertion, always true)
- `hasattr` checks vs actual value assertions
- Frozen-dataclass mutation tests (are they sufficient?)
- Import-surface tests (AST-based) — are allowlists complete?

---

### Task 3: Unit Test Layer — Services (10+ files)

| Field | Value |
|-------|-------|
| **task** | Audit service-layer test files for assertion strength |
| **owner_role** | `reviewer` |
| **deliverable** | Per-test 🟢/🟡/🔴 rating table for all service test files |
| **validation** | Audit: `test_trade_service.py`, `test_account_service.py`, `test_image_service.py`, `test_system_service.py`, `test_settings_service.py`, `test_report_service.py`, `test_plan_service.py`, `test_watchlist_service.py`, `test_provider_connection_service.py`, `test_settings_cache.py`, `test_settings_resolver.py` |
| **status** | `pending` |

**Specific concerns to check**:
- Mock UoW assertions without verifying call arguments
- Tests that check only `isinstance` or `> 0` instead of exact values
- Internal state manipulation (`_loaded_at = 0.0`) vs proper time mocking
- Missing argument verification on `assert_called_once()`

---

### Task 4: Unit Test Layer — Infrastructure & Pipeline (15+ files)

| Field | Value |
|-------|-------|
| **task** | Audit infrastructure, pipeline, import, and security test files |
| **owner_role** | `reviewer` |
| **deliverable** | Per-test 🟢/🟡/🔴 rating table for all infra/pipeline test files |
| **validation** | Audit: `test_backup_manager.py`, `test_log_redaction.py`, `test_csv_import.py`, `test_ibkr_flexquery.py`, `test_pipeline_runner.py`, `test_policy_validator.py`, `test_step_registry.py`, `test_pydantic_models.py`, `test_ref_resolver.py`, `test_logging_service.py`, and any remaining unit test files |
| **status** | `pending` |

**Specific concerns to check**:
- Backup tests with real I/O — do they verify file contents or just existence?
- Pipeline tests — do they assert step execution order or just final state?
- Security tests — are redaction boundary conditions thoroughly tested?
- Import tests — encoding edge cases, malformed input handling

---

### Task 5: Integration Tests (6 files)

| Field | Value |
|-------|-------|
| **task** | Audit all integration test files for assertion strength |
| **owner_role** | `reviewer` |
| **deliverable** | Per-test 🟢/🟡/🔴 rating table for all 6 integration test files |
| **validation** | Audit: `test_backup_integration.py`, `test_backup_recovery_integration.py`, `test_database_connection.py`, `test_repositories.py`, `test_unit_of_work.py`, `test_wal_concurrency.py` |
| **status** | `pending` |

**Specific concerns to check**:
- Insert+get round-trips present (not just insert-only)
- Transaction rollback actually tested (not just commit)
- WAL concurrency tests — do they assert concurrent access correctness or just non-failure?
- Backup recovery — does it verify restored data matches original?

---

### Task 6: Synthesize Findings

| Field | Value |
|-------|-------|
| **task** | Aggregate per-file ratings into summary report with recommendations |
| **owner_role** | `reviewer` |
| **deliverable** | Summary: total 🟢/🟡/🔴 counts, files with most 🔴 findings, prioritized fix list |
| **validation** | Report written to review handoff file at `.agent/context/handoffs/2026-03-16-test-rigor-audit-critical-review.md` |
| **status** | `pending` |

**Required output**:
1. Per-layer summary table (API / Domain / Services / Infra / Integration)
2. Files with ≥1 🔴 rating (prioritized for fix)
3. Files with ≥3 🟡 ratings (flag as `Low` finding)
4. Specific recommended fixes with file:line references
5. Overall verdict: `approved` or `changes_required`

---

## Verification Plan

### Automated Verification
```powershell
# 1. Confirm all tests still pass (baseline)
uv run pytest tests/ -x --tb=short -q

# 2. Collect test counts per file
uv run pytest tests/ --co -q | Select-String "::" | ForEach-Object { ($_ -split "::")[0] } | Group-Object | Sort-Object Count -Descending

# 3. Search for common weakness patterns
rg "hasattr\(" tests/ --count
rg "assert_called_once\(\)" tests/ --count
rg "isinstance\(" tests/ --count
rg "assert.*> 0" tests/ --count
rg "_loaded_at|_internal|_check" tests/ --count
```

### Manual Verification
- Review the generated rating tables for completeness (every test function rated)
- Spot-check 5 randomly selected 🟢 ratings to confirm they truly assert specific values
- Spot-check all 🔴 ratings to confirm they match the weakness criteria
