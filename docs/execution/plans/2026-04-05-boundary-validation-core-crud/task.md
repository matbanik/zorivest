# Task — Boundary Validation Core CRUD Hardening

> **Project:** `2026-04-05-boundary-validation-core-crud`
> **Source:** Handoff 096 findings F1–F3

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 1 | Write negative tests for Account schemas (AC-1 through AC-6) | coder | `tests/unit/test_api_accounts.py` — 6+ new test methods | `pytest tests/unit/test_api_accounts.py -x --tb=short -v` — tests FAIL (Red) | `[x]` |
| 2 | Harden `CreateAccountRequest` + `UpdateAccountRequest` schemas | coder | `routes/accounts.py` — enum types, `Field()` constraints, `extra="forbid"` | Tests from #1 PASS (Green) | `[x]` |
| 3 | Fix `account_service.update_account()` invariant validation | coder | `account_service.py` — validate name/enum before reconstruction | Test for blank-name-on-update passes | `[x]` |
| 4 | Quality gate — Accounts MEU | coder | Clean pyright + ruff | `pyright`: 2 pre-existing errors excluded per `[PYRIGHT-PREEXIST]`; `ruff check`: clean | `[x]` |
| 5 | Write negative tests for Trade schemas (AC-1 through AC-9) | coder | `tests/unit/test_api_trades.py` — 11+ new test methods | `pytest tests/unit/test_api_trades.py -x --tb=short -v` — tests FAIL (Red) | `[x]` |
| 6 | Harden `CreateTradeRequest` + `UpdateTradeRequest` schemas | coder | `routes/trades.py` — enum types, `Field()` constraints, `extra="forbid"` | Tests from #5 PASS (Green) | `[x]` |
| 7 | Fix `trade_service.update_trade()` invariant validation | coder | `trade_service.py` — validate action/quantity/instrument before reconstruction | Tests for invalid-action-on-update, zero-qty-on-update pass | `[x]` |
| 8 | Quality gate — Trades MEU | coder | Clean pyright + ruff | `pyright`: 2 pre-existing errors excluded per `[PYRIGHT-PREEXIST]`; `ruff check`: clean | `[x]` |
| 9 | Write negative tests for Plan schemas (AC-1 through AC-9) | coder | `tests/unit/test_api_plans.py` — 11+ new test methods | `pytest tests/unit/test_api_plans.py -x --tb=short -v` — tests FAIL (Red) | `[x]` |
| 10 | Harden `CreatePlanRequest` + `UpdatePlanRequest` + `PatchStatusRequest` schemas | coder | `routes/plans.py` — enum types, `Field()` constraints, `extra="forbid"` | Tests from #9 PASS (Green) | `[x]` |
| 11 | Fix `report_service.update_plan()` invariant validation | coder | `report_service.py` — validate enums/strings before `replace()` | Tests for invalid-enum-on-update, blank-ticker-on-update pass | `[x]` |
| 12 | Quality gate — Plans MEU | coder | Clean pyright + ruff | `pyright`: 2 pre-existing errors excluded per `[PYRIGHT-PREEXIST]`; `ruff check`: clean | `[x]` |
| 13 | Full regression suite | tester | All unit tests pass | `pytest -x --tb=short -m "unit"` | `[x]` |
| 14 | MEU gate validation | tester | `validate_codebase.py --scope meu` passes | `uv run python tools/validate_codebase.py --scope meu` — pyright pre-existing exclusion per `[PYRIGHT-PREEXIST]` | `[x]` |
| 15 | OpenAPI spec regen | coder | `openapi.committed.json` updated | `uv run python tools/export_openapi.py --check openapi.committed.json` | `[x]` |
| 16 | Verify `docs/BUILD_PLAN.md` — no stale references | reviewer | Confirm no hub-level updates needed | `rg "boundary\|validation\|BOUNDARY" docs/BUILD_PLAN.md` — no stale refs | `[x]` |
| 17 | Create handoff 098 (Accounts) | coder | `098-2026-04-05-boundary-accounts-bp04bs1.md` | File exists with evidence bundle | `[x]` |
| 18 | Create handoff 099 (Trades) | coder | `099-2026-04-05-boundary-trades-bp04as1.md` | File exists with evidence bundle | `[x]` |
| 19 | Create handoff 100 (Plans) | coder | `100-2026-04-05-boundary-plans-bp04as2.md` | File exists with evidence bundle | `[x]` |
| 20 | Update MEU registry | coder | 3 new MEU rows in `meu-registry.md` | MEU-BV1, BV2, BV3 present with ✅ status | `[x]` |
| 21 | Create reflection | coder | `docs/execution/reflections/2026-04-05-boundary-validation-core-crud-reflection.md` | File exists | `[x]` |
| 22 | Update metrics | coder | `docs/execution/metrics.md` updated | Row added | `[x]` |
| 23 | Save session to pomera_notes | coder | Note saved with title `Memory/Session/Zorivest-boundary-validation-core-crud-2026-04-05` | Note ID 743 | `[x]` |
| 24 | Prepare commit messages | coder | Commit message(s) drafted | Presented to human | `[x]` |
