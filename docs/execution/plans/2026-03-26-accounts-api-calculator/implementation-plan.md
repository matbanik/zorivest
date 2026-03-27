# Account API Completion + Calculator Integration

**Project slug**: `accounts-api-calculator`
**MEUs**: MEU-71 (account-entity-api) → MEU-71b (calculator-integration)
**Build plan sections**: `06d-gui-accounts.md` §Account Routes, `06h-gui-calculator.md` §Account Resolution

## Background

The Account backend (entity, service, repository ports, CRUD routes, balance snapshot) is **90% complete**. This project delivers the missing API surface (balance history endpoint, enriched response with latest balance, portfolio total) and integrates account balance auto-loading into the Position Calculator modal.

> [!NOTE]
> **FK constraints already exist.** The build plan described "migrate Trade/TradePlan `account_id` from string to FK." After code review, FK constraints are **already implemented** at the SQLAlchemy model layer: `TradeModel.account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)` (models.py:47), `TradePlanModel.account_id = Column(String, ForeignKey("accounts.account_id"), nullable=True)` (models.py:137). No Alembic migration is required. This project adds an integration test to verify FK enforcement.

---

## Spec Sufficiency Gate

### MEU-71: Account Entity + API

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Account CRUD (create, get, list, update, delete) | Spec | `06d-gui-accounts.md` L69-79 | ✅ Already built | `accounts.py` routes |
| `POST /{id}/balances` record balance | Spec | `06d-gui-accounts.md` L79 | ✅ Already built | `accounts.py` L118-139 |
| `GET /{id}/balances` list balance history | Spec | `06d-gui-accounts.md` L78 | ❌ Missing | New endpoint needed |
| `AccountResponse` includes latest balance | Spec | `06d-gui-accounts.md` L41, L67 | ❌ Missing | Enrich response schema |
| Portfolio total (sum of latest balances) | Spec | `06h-gui-calculator.md` L92 | ❌ Missing | New endpoint or computed in list |
| FK constraint enforcement | Spec | `06d-gui-accounts.md` L62 | ❌ Missing | Add integration test for FK enforcement |

### MEU-71b: Calculator Integration

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Account dropdown in calculator | Spec | `06h-gui-calculator.md` L29-30, L80 | ❌ Missing | Replace manual input |
| Balance auto-fill from selected account | Spec | `06h-gui-calculator.md` L81, L91 | ❌ Missing | Fetch latest balance |
| "All Accounts" portfolio total | Spec | `06h-gui-calculator.md` L92 | ❌ Missing | Sum all latest balances |
| Manual override allowed | Spec | `06h-gui-calculator.md` L81, L93 | ❌ Missing | User can edit balance |
| Revert on account change | Spec | `06h-gui-calculator.md` L81 | ❌ Missing | Reset to API value |

---

## Proposed Changes

### MEU-71: Account API Completion

---

#### [MODIFY] [account_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/account_service.py)

Add two new service methods:

1. `list_balance_history(account_id, limit, offset)` — delegates to `BalanceSnapshotRepository.list_for_account()` with pagination
2. `get_portfolio_total()` — fetches all accounts, for each gets latest balance snapshot, sums them

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Extend `BalanceSnapshotRepository` protocol:
- Add `get_latest(account_id: str) -> Optional[BalanceSnapshot]` method
- Add `list_for_account(account_id: str, limit: int, offset: int) -> list[BalanceSnapshot]` with pagination params

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

Extend `SqlAlchemyBalanceSnapshotRepository` (currently only has `save()` and `list_for_account(account_id)`):
- Add `get_latest(account_id: str) -> BalanceSnapshot | None` — query most recent by `datetime DESC LIMIT 1`
- Update `list_for_account()` to accept `limit: int` and `offset: int` pagination params

#### [MODIFY] [accounts.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/accounts.py)

1. Add `GET /{id}/balances` endpoint — returns paginated balance history
2. Add `BalanceSnapshotResponse` schema
3. Enrich `AccountResponse` with `latest_balance: float | None` and `latest_balance_date: str | None`
4. Modify `get_account` and `list_accounts` to populate latest balance in response

> **Backward compatibility**: `GET /api/v1/accounts` continues to return `AccountResponse[]` (bare array). The P1 `{items, total}` wrapper is NOT applied here — 19 existing consumer locations (`TradePlanPage.tsx`, `TradesLayout.tsx`, tests) expect `Account[]`. P1 pagination applies only to the new `GET /{id}/balances` endpoint.

#### [MODIFY] [test_api_accounts.py](file:///p:/zorivest/tests/unit/test_api_accounts.py)

Add tests:
- `TestListBalanceHistory.test_list_balances_200` — verifies GET returns balance snapshots
- `TestListBalanceHistory.test_list_balances_empty` — verifies empty list for account with no snapshots
- `TestListBalanceHistory.test_list_balances_404_unknown_account` — verifies 404 for unknown account
- `TestGetAccount.test_get_account_includes_latest_balance` — verifies enriched response

#### [MODIFY] [test_account_service.py](file:///p:/zorivest/tests/unit/test_account_service.py)

Add tests:
- `TestListBalanceHistory.test_list_history_delegates_to_repo`
- `TestGetPortfolioTotal.test_sums_latest_balances`
- `TestGetPortfolioTotal.test_returns_zero_no_accounts`

#### [MODIFY] [test_repositories.py](file:///p:/zorivest/tests/integration/test_repositories.py)

Add repo contract tests:
- `TestBalanceSnapshotRepo.test_get_latest_returns_most_recent` — verifies chronological ordering
- `TestBalanceSnapshotRepo.test_get_latest_returns_none_for_empty` — verifies None for no snapshots
- `TestBalanceSnapshotRepo.test_list_for_account_pagination` — verifies limit/offset
- `TestBalanceSnapshotRepo.test_fk_enforcement_rejects_orphan_trade` — verifies Trade with non-existent account_id raises IntegrityError

---

### MEU-71b: Calculator Integration

---

#### [NEW] [useAccounts.ts](file:///p:/zorivest/ui/src/renderer/src/hooks/useAccounts.ts)

New TanStack Query hook:
- `useAccounts()` — fetches account list from `GET /api/v1/accounts`
- Returns `{ accounts, portfolioTotal, isLoading }`
- Computes portfolio total client-side from `latest_balance` fields

#### [MODIFY] [PositionCalculatorModal.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx)

1. Add `<select>` dropdown for account selection (replaces static `accountSize` input):
   - "Manual" option (default) — keeps manual balance entry
   - "All Accounts" — auto-fills with portfolio total
   - Individual accounts — auto-fills with `latest_balance`
2. When account selected: auto-fill `accountSize` from API balance
3. Balance input remains editable (manual override)
4. On account change: revert balance to API value (per spec)
5. Add `data-testid="calc-account-select"` for E2E

#### [NEW] [test_useAccounts.test.ts](file:///p:/zorivest/ui/src/renderer/src/hooks/__tests__/useAccounts.test.ts)

Unit tests for the hook:
- Portfolio total computation
- Empty accounts list handling
- Account selection balance resolution

#### [MODIFY] [PositionCalculatorModal.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/__tests__/PositionCalculatorModal.test.tsx)

Add tests:
- Account dropdown renders with fetched accounts
- Selecting account auto-fills balance
- "All Accounts" fills portfolio total
- Manual override preserves user value
- Account change reverts to API balance

---

### Post-MEU Deliverables

---

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Update MEU-71 and MEU-71b status from `⏸` to `✅`

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

Update MEU-71 and MEU-71b status and add completion evidence

#### [NEW] Handoff files

- `091-2026-03-26-accounts-api-bp06ds1.md` (MEU-71)
- `092-2026-03-26-calculator-accounts-bp06hs1.md` (MEU-71b)

#### OpenAPI spec regeneration

Since `packages/api/` routes are modified, must run: `uv run python tools/export_openapi.py -o openapi.committed.json`

---

## Feature Intent Contracts

### FIC: MEU-71 — Account API Completion

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `GET /api/v1/accounts/{id}/balances` returns paginated balance snapshot list (200) | Spec: `06d` L78 |
| AC-2 | `GET /api/v1/accounts/{id}/balances` returns 404 for unknown account | Spec: `06d` L78, error pattern |
| AC-3 | `AccountResponse` includes `latest_balance` (float or null) and `latest_balance_date` (ISO string or null) | Spec: `06d` L41, L67 |
| AC-4 | `SqlAlchemyBalanceSnapshotRepository` implements `get_latest()` and paginated `list_for_account()` | Spec: `06d` L78 + infra contract |
| AC-5 | `AccountService.list_balance_history()` delegates to repository with limit/offset | Spec: `06d` L78 |
| AC-6 | `AccountService.get_portfolio_total()` returns sum of all latest balances | Spec: `06h` L92 |
| AC-7 | FK enforcement: Trade with non-existent `account_id` raises IntegrityError | Spec: `06d` L62 |

### FIC: MEU-71b — Calculator Account Integration

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | Calculator shows account dropdown with "Manual", "All Accounts", and individual accounts | Spec: `06h` L29-30, L80 |
| AC-2 | Selecting a specific account auto-fills balance from `latest_balance` | Spec: `06h` L81, L91 |
| AC-3 | Selecting "All Accounts" auto-fills balance with portfolio total | Spec: `06h` L92 |
| AC-4 | User can manually edit balance after auto-fill (manual override) | Spec: `06h` L93 |
| AC-5 | Changing account selection reverts balance to API value | Spec: `06h` L81 |
| AC-6 | `useAccounts` hook fetches from `GET /api/v1/accounts` and computes portfolio total | Spec: `06h` L351 |

---

## Verification Plan

### Automated Tests

**Python (MEU-71):**
```bash
uv run pytest tests/unit/test_account_service.py tests/unit/test_api_accounts.py -x --tb=short -v *> C:\Temp\zorivest\pytest-accounts.txt; Get-Content C:\Temp\zorivest\pytest-accounts.txt | Select-Object -Last 40
```

**TypeScript (MEU-71b):**
```bash
npx vitest run src/hooks/__tests__/useAccounts.test.ts src/features/planning/__tests__/PositionCalculatorModal.test.tsx *> C:\Temp\zorivest\vitest-calc.txt; Get-Content C:\Temp\zorivest\vitest-calc.txt | Select-Object -Last 40
```

**MEU Gate:**
```bash
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

**OpenAPI Regeneration:**
```bash
uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi.txt; Get-Content C:\Temp\zorivest\openapi.txt
```

### Manual Verification

None required — all ACs are covered by automated unit tests. E2E Wave 4 calculator tests already pass and the account dropdown is additive (non-breaking).
