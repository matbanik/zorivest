# Task Handoff — MEU-12 Service Layer

## Task

- **Date:** 2026-03-08
- **Task slug:** service-layer
- **Owner role:** coder
- **Scope:** MEU-12 — Service Layer (build-priority-matrix item 6, 03-service-layer.md §3.1)

## Inputs

- User request: Implement 4 services per matrix-6: TradeService, AccountService, ImageService, SystemService
- Specs/docs referenced: `03-service-layer.md`, `build-priority-matrix.md` item 6, `commands.py`, `ports.py`
- Constraints: Use actual command names from `commands.py` (CreateTrade, AttachImage, CreateAccount, UpdateBalance). No stub services.

## Role Plan

1. coder
2. tester
- Optional roles: reviewer, guardrail (deferred to project-level review)

## Coder Output

- Changed files:

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/domain/exceptions.py` | NEW — 6-class hierarchy (ZorivestError, ValidationError, NotFoundError, BusinessRuleError, BudgetExceededError, ImportError) |
| `packages/core/src/zorivest_core/domain/trades/__init__.py` | NEW — trades subpackage init |
| `packages/core/src/zorivest_core/domain/trades/identity.py` | NEW — SHA-256 trade fingerprint (6 fields) |
| `packages/core/src/zorivest_core/application/ports.py` | MODIFIED — Added AccountRepository, BalanceSnapshotRepository, RoundTripRepository Protocols; TradeRepository.exists_by_fingerprint_since/list_for_account; UnitOfWork.accounts/balance_snapshots/round_trips |
| `packages/core/src/zorivest_core/services/trade_service.py` | NEW — create_trade (exec_id + fingerprint dedup), get_trade, match_round_trips |
| `packages/core/src/zorivest_core/services/account_service.py` | NEW — create_account, get_account, list_accounts, add_balance_snapshot |
| `packages/core/src/zorivest_core/services/image_service.py` | NEW — attach_image, get_trade_images, get_thumbnail |
| `packages/core/src/zorivest_core/services/system_service.py` | NEW — calculator wrapper (thin delegate to domain function) |
| `packages/core/src/zorivest_core/services/__init__.py` | NEW — re-exports 4 services |

- Commands run: `uv run pytest tests/unit/test_*.py -v`, `uv run pyright`, `uv run ruff check --fix`
- Results: 33 tests pass, pyright 0 errors, ruff clean

## Tester Output

- Commands run: `uv run pytest tests/unit/test_exceptions.py tests/unit/test_trade_fingerprint.py tests/unit/test_trade_service.py tests/unit/test_account_service.py tests/unit/test_image_service.py tests/unit/test_system_service.py -v --tb=short`
- Pass/fail matrix: 33 passed / 0 failed
- Test mapping:
  - `test_exceptions.py` (10 tests): hierarchy, distinctness, catchability, messages
  - `test_trade_fingerprint.py` (9 tests): determinism, collision resistance, SHA-256 format
  - `test_trade_service.py` (7 tests): create success, exec_id dedup, fingerprint dedup, get, round-trips
  - `test_account_service.py` (3 tests): create, snapshot success, snapshot unknown account
  - `test_image_service.py` (3 tests): attach, nonexistent trade, get images
  - `test_system_service.py` (2 tests): delegation, frozen dataclass

- Negative Cases:
  - BusinessRuleError on duplicate exec_id
  - BusinessRuleError on fingerprint match within 30-day window
  - NotFoundError on missing trade/account
  - NotFoundError on image attach to nonexistent trade

## Reviewer Output

- Findings by severity: N/A — reviewed at project level via `2026-03-08-infra-services-implementation-critical-review.md`
- Verdict: approved (post-corrections)

## Guardrail Output (If Required)

- Not applicable — no high-risk changes in this MEU

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Complete — all code, tests, and quality gates pass
- Next steps: MEU-13 (SQLAlchemy Models)
