# Task: Account API Completion + Calculator Integration

## MEU-71: Account API Completion

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Extend `BalanceSnapshotRepository` protocol with `get_latest()` and paginated `list_for_account()` | coder | `ports.py` | pyright PASS | [x] |
| 2 | Implement `get_latest()` and paginated `list_for_account()` in `SqlAlchemyBalanceSnapshotRepository` | coder | `repositories.py` | pyright PASS | [x] |
| 3 | Add `list_balance_history()` and `get_portfolio_total()` to `AccountService` | coder | `account_service.py` | pyright PASS | [x] |
| 4 | Add `GET /{id}/balances` endpoint, enrich `AccountResponse` with latest balance | coder | `accounts.py` | pyright PASS | [x] |
| 5 | Write RED phase unit tests for service + API (AC-1 through AC-6) | tester | `test_account_service.py`, `test_api_accounts.py` | 10 tests PASS | [x] |
| 6 | Write RED phase repo contract tests (AC-4, AC-7) | tester | `test_repo_contracts.py` | 7 tests PASS | [x] |
| 7 | Implement GREEN phase — all service, API, repo code | coder | All modified files | 27 tests PASS | [x] |
| 8 | Run MEU gate for MEU-71 | tester | Clean gate output | All 8 checks PASS (22.39s) | [x] |

## MEU-71b: Calculator Account Integration

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 9 | Create `useAccounts` hook | coder | `useAccounts.ts` | tsc PASS | [x] |
| 10 | Add account dropdown to `PositionCalculatorModal` with auto-fill and override logic | coder | `PositionCalculatorModal.tsx` | tsc PASS | [x] |
| 11 | Write tests for hook + modal (AC-1 through AC-6) | tester | `useAccounts.test.ts`, `planning.test.tsx` | 10 new tests PASS | [x] |
| 12 | Implement GREEN phase — hook + modal integration | coder | All modified TS files | 59 tests PASS (0 errors) | [x] |
| 13 | Run MEU gate for MEU-71b | tester | Clean gate output | All 8 checks PASS (21.66s) | [x] |

## Post-MEU Deliverables

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 14 | Run full regression | tester | Green test suite | All checks PASS | [x] |
| 15 | Regenerate OpenAPI spec | coder | `openapi.committed.json` | Regenerated | [x] |
| 16 | Update `build-priority-matrix.md` status (MEU-71/71b tracked in meu-registry only) | reviewer | N/A (matrix has no MEU-level tracking) | [x] |
| 17 | Update `meu-registry.md` with completion evidence | reviewer | `meu-registry.md` | MEU-71 + MEU-71b entries added | [x] |
| 18 | Create handoff | reviewer | 092 + 093 handoff files | Created and reviewed | [x] |
| 19 | Save session state to `pomera_notes` | orchestrator | Pomera note | [x] (note 707) |
| 20 | Prepare proposed commit messages | orchestrator | Commit messages | See below | [x] |

### Proposed Commit Messages

```
feat(accounts): complete account API enrichment (MEU-71)

- Add get_latest() and paginated list_for_account() to BalanceSnapshotRepository
- Add balance history endpoint GET /{id}/balances with enriched AccountResponse
- Add get_portfolio_total() to AccountService
- FK enforcement test for orphan account_id references
- 27 tests pass (unit + integration + contract)

feat(calculator): integrate account selection into position calculator (MEU-71b)

- Add useAccounts hook with portfolio total computation
- Add account dropdown defaulting to All Accounts (per 06h spec)
- Auto-fill balance from latest_balance on account selection
- Support zero-total portfolios (accountSize init=0, isLoading-gated effect)
- Manual override preserved, account switch reverts to API value
- 12 new tests (5 hook + 7 component), 3 existing tests made explicit
- MEU gate: all 8 checks PASS
```
