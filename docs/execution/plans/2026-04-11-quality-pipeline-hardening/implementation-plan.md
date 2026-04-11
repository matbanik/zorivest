---
project: "2026-04-11-quality-pipeline-hardening"
date: "2026-04-11"
source: "known-issues.md (Tier 1–2 CI failures)"
meus: ["CI-FIX-1", "CI-FIX-2", "MEU-TS2", "MEU-TS4"]
status: "approved"
template_version: "2.0"
---

# Implementation Plan: Quality Pipeline Hardening — CI Green + Test Drift

> **Project**: `2026-04-11-quality-pipeline-hardening`
> **Build Plan Section(s)**: known-issues.md — CI Tier 1 failures (CI-FIX-1, CI-FIX-2) + Tier 2 pyright (MEU-TS2) + MEU-TS4 market data test drift
> **Status**: `approved`

---

## Goal

Restore the CI pipeline to a clean, passing state by fixing 4 distinct failures: OpenAPI spec drift, missing UI test mocks, pyright enum-literal errors in test assertions, and market data service test drift from MEU-91. All fixes target test infrastructure only — zero production code changes.

---

## User Review Required

> [!IMPORTANT]
> **No production code changes.** All fixes target test infrastructure, CI artifacts, and test assertions. Zero runtime behavior impact.

> [!IMPORTANT]
> **Tier 3 pyright errors (~169 remaining after Tier 2) are out of scope.** These require an architectural decision (type stubs vs factory functions vs inline suppressions) and are better addressed in a dedicated MEU. Only Tier 2 (~36 string literal → enum) is included here.

---

## Proposed Changes

### CI-FIX-1: OpenAPI Spec Drift

The committed `openapi.committed.json` is stale — it doesn't reflect routes added in recent MEUs (scheduling, market data, accounts archive). The CI quality gate runs `tools/export_openapi.py --check` and fails on the diff.

#### Boundary Inventory

N/A — no external input surfaces. This task regenerates a build artifact.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `uv run python tools/export_openapi.py --check openapi.committed.json` exits 0 | Spec (CI quality gate definition) | N/A |
| AC-2 | Both copies (root + `packages/api/`) are byte-identical | Local Canon (`tools/export_openapi.py` dual-location pattern) | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| OpenAPI spec regeneration command | Spec | `tools/export_openapi.py -o openapi.committed.json` |
| Dual-location copy requirement | Local Canon | Root + `packages/api/src/zorivest_api/` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `openapi.committed.json` (root) | modify | Regenerated from live API |
| `packages/api/src/zorivest_api/openapi.committed.json` | modify | Copied from root |

---

### CI-FIX-2: UI Test Missing Mocks

Two test files mock `@/hooks/useAccounts` but omit the `useArchiveAccount` and `useArchivedAccounts` hooks added in MEU-37. When vitest resolves the imports, these undefined hooks cause 21 test failures.

#### Boundary Inventory

N/A — no external input surfaces. This task adds mock return values to test fixtures.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `AccountDetailPanel.test.tsx` includes `useArchiveAccount` and `useArchivedAccounts` mocks | Spec (MEU-37 hook exports) | N/A |
| AC-2 | `AccountsHome.test.tsx` includes the same two mocks | Spec (MEU-37 hook exports) | N/A |
| AC-3 | `npx vitest run` — all UI tests pass (23 files, 307 tests) | Local Canon (CI vitest gate) | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Required mock shape for `useArchiveAccount` | Local Canon | `{ mutate: vi.fn(), isPending: false }` — matches production hook signature |
| Required mock shape for `useArchivedAccounts` | Local Canon | `{ accounts: [], isLoading: false, isFetching: false, error: null, refetch: vi.fn() }` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/accounts/__tests__/AccountDetailPanel.test.tsx` | modify | Add 2 mock hooks to `vi.mock` block |
| `ui/src/renderer/src/features/accounts/__tests__/AccountsHome.test.tsx` | modify | Add 2 mock hooks to `vi.mock` block |

---

### MEU-TS2: Pyright Tier 2 — String Literal → Enum

36 pyright `reportArgumentType` errors across 3 test files where raw string literals (`"BOT"`, `"SLD"`, `"high"`, `"draft"`, etc.) are passed to `TradePlan` constructor parameters that now expect strict enum types (`TradeAction`, `ConvictionLevel`, `PlanStatus`).

**Scope correction from original plan:** The original plan listed 5 files (`test_trade_service.py`, `test_account_service.py`, `test_api_trades.py`, `test_api_accounts.py`, `test_api_plans.py`). Actual investigation found the Tier 2 errors in 3 different files: `test_repo_contracts.py`, `test_repositories.py`, `test_report_service.py`.

#### Boundary Inventory

N/A — no external input surfaces. This task replaces string literals with enum members in test constructor calls.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | All `TradePlan` constructor calls use `TradeAction` enum members instead of `"BOT"`/`"SLD"` | Spec (`entities.py` type annotations) | N/A |
| AC-2 | All `TradePlan` constructor calls use `ConvictionLevel` enum members instead of `"high"`/`"medium"` | Spec (`entities.py` type annotations) | N/A |
| AC-3 | All `TradePlan` constructor calls use `PlanStatus` enum members instead of `"draft"`/`"active"` | Spec (`entities.py` type annotations) | N/A |
| AC-4 | `dataclasses.replace()` calls on `TradePlan` use enum members | Spec (`entities.py` type annotations) | N/A |
| AC-5 | All 87 affected tests still pass (StrEnum members are string-compatible at runtime) | Local Canon (StrEnum compatibility) | N/A |
| AC-6 | `uv run pyright tests/` shows 0 Tier 2 `reportArgumentType` errors for string→enum | Spec (pyright strict mode) | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `TradePlan.direction` type | Spec | `TradeAction` enum (`entities.py:L128`) |
| `TradePlan.conviction` type | Spec | `ConvictionLevel` enum (`entities.py:L129`) |
| `TradePlan.status` type | Spec | `PlanStatus` enum (`entities.py:L139`) |
| StrEnum runtime compatibility | Research-backed | Python docs: `StrEnum` members compare equal to their string values |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `tests/integration/test_repo_contracts.py` | modify | Import `ConvictionLevel`, `PlanStatus`; fix 3 constructor args + 1 `replace()` call |
| `tests/integration/test_repositories.py` | modify | Import `ConvictionLevel`, `PlanStatus`; fix 15 constructor args + 1 `replace()` call |
| `tests/unit/test_report_service.py` | modify | Import `ConvictionLevel`, `PlanStatus`, `TradeAction`; fix 21 constructor args |

---

### MEU-TS4: Market Data Service Test Drift

5 tests fail in `test_market_data_service.py` because `get_quote()` was updated in MEU-91 to always try Yahoo Finance first via `_yahoo_quote()`. The existing mock HTTP client doesn't account for this code path.

#### Boundary Inventory

N/A — no external input surfaces. This task patches a private method in test fixtures.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `_yahoo_quote` is patched via class decorator on `TestGetQuote` | Local Canon (MEU-91 `get_quote()` implementation) | N/A |
| AC-2 | `_yahoo_quote` is patched via class decorator on `TestRateLimiting` | Local Canon (MEU-91 `get_quote()` implementation) | N/A |
| AC-3 | All 13 market data service tests pass | Local Canon (test suite) | N/A |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `get_quote()` Yahoo-first fallback pattern | Local Canon | MEU-91 implementation in `market_data_service.py` |
| Test isolation via `@patch.object` | Research-backed | Python `unittest.mock` docs |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `tests/unit/test_market_data_service.py` | modify | Add `@patch.object(MarketDataService, '_yahoo_quote', side_effect=Exception(...))` decorators |

---

## Out of Scope

- Tier 3 pyright errors (~169 remaining): `reportAttributeAccessIssue`, `reportPossiblyUnboundVariable`, `reportMissingImports`, `Column[T]` typing, protocol mismatches
- Production code changes of any kind
- New test creation — only fixing existing test infrastructure

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections. It fixes test infrastructure failures that were tracked in `known-issues.md`, not in the build plan. No `docs/BUILD_PLAN.md` update is required.

```powershell
rg "quality-pipeline-hardening" docs/BUILD_PLAN.md  # Expected: 0 matches
```

---

## Verification Plan

### 1. Per-Task Verification
```powershell
# CI-FIX-1: OpenAPI spec
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt

# CI-FIX-2: UI tests
npx vitest run *> C:\Temp\zorivest\vitest.txt; Get-Content C:\Temp\zorivest\vitest.txt | Select-Object -Last 10

# MEU-TS4: Market data service tests
uv run pytest tests/unit/test_market_data_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-mds.txt; Get-Content C:\Temp\zorivest\pytest-mds.txt | Select-Object -Last 10

# MEU-TS2: Pyright Tier 2 errors
uv run pyright tests/integration/test_repo_contracts.py tests/integration/test_repositories.py tests/unit/test_report_service.py *> C:\Temp\zorivest\pyright-t2.txt; Get-Content C:\Temp\zorivest\pyright-t2.txt | Select-Object -Last 5
```

### 2. Full Validation
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 20
```

### Expected Outcomes

| Check | Before | After |
|-------|--------|-------|
| CI OpenAPI gate | ❌ Drift detected | ✅ Spec matches |
| UI tests (vitest) | ❌ 21 failures | ✅ 23 files, 307 tests pass |
| MDS tests | ❌ 5 failures | ✅ 13 pass |
| Pyright Tier 2 errors | 36 `reportArgumentType` | 0 Tier 2 (205 total, all Tier 3) |
| MEU validation gate | ❌ | ✅ All 8 blocking checks pass |

---

## Execution Order

| Step | Task | Dependency |
|------|------|------------|
| 1 | CI-FIX-2: Add missing UI test mocks | None |
| 2 | CI-FIX-1: Regenerate OpenAPI spec | None |
| 3 | MEU-TS4: Fix MDS test drift | None |
| 4 | MEU-TS2: Enum literal fixes | None |
| 5 | Final verification: MEU validation gate | Steps 1–4 |

Steps 1–4 are independent and can be executed in any order.

---

## Open Questions

None — all behaviors resolved from spec and local canonical docs.

---

## Research References

- Python docs: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum) — confirms string comparability
- Python docs: [`unittest.mock.patch.object`](https://docs.python.org/3/library/unittest.mock.html#patch-object) — class-level decorator pattern
