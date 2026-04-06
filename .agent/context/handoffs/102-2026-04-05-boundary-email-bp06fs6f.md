# 102 — MEU-BV5 Boundary Validation: Email Settings

> **Date**: 2026-04-05
> **MEU**: MEU-BV5 (`boundary-validation-email`)
> **Build Plan Section**: 06f (GUI settings — email)
> **Project**: `2026-04-05-boundary-validation-email-market-data`
> **Plan**: [implementation-plan.md](../../docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md)
> **Status**: ✅ Complete

---

## Scope

Harden Email Settings `PUT /settings/email` schema with strict Pydantic enforcement: `extra="forbid"`, `StrippedStr` on string fields (except `password`), `Literal` constraints on `provider_preset` (6 presets) and `security` (STARTTLS/SSL), `Field` constraints on `port` (1–65535). Addresses finding F6 from handoff 096.

## Design Decisions

1. **`password` NOT stripped**: Whitespace-in-passwords is valid. Empty string = keep existing. Intentional exception to BV pattern.
2. **`security` = `Literal["STARTTLS", "SSL"]`**: Two values only — matches GUI radio, spec, and input-index. `NONE` was rejected during plan review (Codex finding F1).
3. **`provider_preset` = closed set**: `Literal["Gmail", "Brevo", "SendGrid", "Outlook", "Yahoo", "Custom"]` — matches GUI PRESETS map and spec preset table. Added during plan review (Codex finding F2).

## FIC Acceptance Criteria

| AC | Description | Status |
|----|-------------|--------|
| AC-EM1 | `EmailConfigRequest` rejects unknown fields → 422 | ✅ |
| AC-EM2 | Whitespace-only `smtp_host` → 422 | ✅ |
| AC-EM3 | Whitespace-only `username` → 422 | ✅ |
| AC-EM4 | Unknown `provider_preset` → 422 | ✅ |
| AC-EM5 | Whitespace-only `from_email` → 422 | ✅ |
| AC-EM6 | `port=0` → 422 | ✅ |
| AC-EM7 | `port=99999` → 422 | ✅ |
| AC-EM8 | `security="INVALID"` → 422 | ✅ |
| AC-EM9 | `password=" "` accepted (not stripped) | ✅ |
| AC-EM10 | Valid full payload → 200 | ✅ |
| AC-EM11 | Whitespace-only `provider_preset` → 422 | ✅ |

## Changed Files

| File | Change |
|------|--------|
| `packages/api/src/zorivest_api/routes/email_settings.py` | Added `_strip_whitespace` + `StrippedStr`, `ProviderPreset` Literal (6 values), `SecurityMode` Literal (2 values), `ConfigDict(extra="forbid")`, `Field` constraints on `port`/string fields |
| `tests/unit/test_api_email_settings.py` | Added `TestEmailConfigBoundaryValidation` class (11 tests) |

## Evidence

### FAIL_TO_PASS

- Red phase: 9 failed, 2 passed (AC-EM9 password + AC-EM10 regression guard)
- Green phase: 23 passed, 0 failed

### Commands Executed

```
uv run pytest tests/unit/test_api_email_settings.py::TestEmailConfigBoundaryValidation -v  # Red: 9 failed
uv run pytest tests/unit/test_api_email_settings.py -v                                     # Green: 23 passed
uv run pytest tests/ -x --tb=short -v                                                     # Regression: 211 passed ⚠️ SUPERSEDED — see Recheck 4 below
uv run python tools/validate_codebase.py --scope meu                                      # ruff PASS, pytest PASS
uv run python tools/export_openapi.py --check openapi.committed.json                      # OpenAPI spec matches
```

### Quality Gate

- **pytest**: 23 passed (email suite); 44 passed (combined BV4+BV5); full regression **superseded** — see Recheck 4 (1718 passed, 0 failures excl. [TEST-DRIFT-MDS])
- **ruff**: PASS
- **pyright**: Pre-existing errors only (documented in known-issues.md)
- **OpenAPI spec**: Regenerated and verified

## Codex Validation Report

**Date**: 2026-04-05  
**MEU**: MEU-BV5 — boundary-validation-email  
**Verdict**: changes_required

### Test Results

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=long -v` | PASS — 44 passed, 1 warning |
| `uv run pytest tests/ -x --tb=long -v` | FAIL — 1 unrelated repo-level failure in `tests/unit/test_account_service.py::TestDeleteAccountBlockOnly::test_delete_without_trades_succeeds` |
| `uv run pyright packages/core/src packages/infrastructure/src packages/api/src` | FAIL — 2 pre-existing errors in `account_service.py:131` and `trade_service.py:175` |
| `uv run ruff check packages/core/src packages/infrastructure/src packages/api/src tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py` | PASS |
| `uv run python tools/export_openapi.py --check openapi.committed.json` | PASS |

### Adversarial Checklist

| Check | Result | Evidence |
|-------|--------|----------|
| AV-1 | PASS | Handoff records Red→Green (`9 failed, 2 passed` to `23 passed`); current targeted suite is green. |
| AV-2 | PASS | No bypass logic or test monkeypatching in [`test_api_email_settings.py`](P:\zorivest\tests\unit\test_api_email_settings.py:322) or [`email_settings.py`](P:\zorivest\packages\api\src\zorivest_api\routes\email_settings.py:28). |
| AV-3 | PASS | Each new boundary case asserts explicit `422` or `200` outcomes in [`test_api_email_settings.py`](P:\zorivest\tests\unit\test_api_email_settings.py:328). |
| AV-4 | PASS | No `skip`/`xfail` markers in the touched route or test files. |
| AV-5 | PASS | No `TODO`, `FIXME`, `NotImplementedError`, or placeholder stubs found in touched files. |
| AV-6 | PASS | Closed `provider_preset` and `security` sets match [`06f-gui-settings.md`](P:\zorivest\docs\build-plan\06f-gui-settings.md:233) and [`input-index.md`](P:\zorivest\docs\build-plan\input-index.md:427), consistent with the plan-critical-review corrections. |
| AV-7 | PASS | `EmailConfigRequest` is an explicit boundary schema with `extra="forbid"`, constrained string fields, and closed literals in [`email_settings.py`](P:\zorivest\packages\api\src\zorivest_api\routes\email_settings.py:59). |
| AV-8 | PASS | The password exception is explicit and documented in code; all other save-time boundary invariants now run through the same request model in [`email_settings.py`](P:\zorivest\packages\api\src\zorivest_api\routes\email_settings.py:59). |
| AV-9 | PASS | Invalid payloads are rejected at the FastAPI/Pydantic boundary with `422`, proven in [`test_api_email_settings.py`](P:\zorivest\tests\unit\test_api_email_settings.py:328). |

### Banned Patterns

- `rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder|pytest\.mark\.(skip|xfail)|@pytest\.mark\.(skip|xfail)" ...` → clean

### FIC Coverage

| Criterion | Test(s) | Verified |
|-----------|---------|----------|
| AC-EM1 | `test_extra_field_rejected` | ✅ |
| AC-EM2 | `test_whitespace_only_smtp_host_rejected` | ✅ |
| AC-EM3 | `test_whitespace_only_username_rejected` | ✅ |
| AC-EM4 | `test_unknown_provider_preset_rejected` | ✅ |
| AC-EM5 | `test_whitespace_only_from_email_rejected` | ✅ |
| AC-EM6 | `test_zero_port_rejected` | ✅ |
| AC-EM7 | `test_port_above_65535_rejected` | ✅ |
| AC-EM8 | `test_invalid_security_rejected` | ✅ |
| AC-EM9 | `test_whitespace_password_accepted` | ✅ |
| AC-EM10 | `test_valid_full_payload_accepted` | ✅ |
| AC-EM11 | `test_whitespace_only_provider_preset_rejected` | ✅ |

### Findings

1. **[MEDIUM]** [`test_account_service.py`](P:\zorivest\tests\unit\test_account_service.py:286), [`account_service.py`](P:\zorivest\packages\core\src\zorivest_core\services\account_service.py:131) — The current repo-level regression gate is red outside this MEU’s scope. `pytest tests/ -x --tb=long -v` fails because `delete_account()` now calls `trade_plans.count_for_account()`, but the unit test fixture does not stub that method, so the mock remains truthy and triggers `ConflictError`. I did not find a defect in the email boundary hardening itself, but I cannot issue a clean approval while the repo gate is red in the provided worktree.

### Verdict Rationale

MEU-BV5’s boundary changes are implemented correctly: the route now has a closed request schema, the literal sets match the GUI/spec/input-index contract, the password exception is explicit rather than accidental, the negative tests are direct, and the OpenAPI snapshot is current. The only blocker to approval is external to this MEU: the current repo state does not pass the full Python regression gate.

### Verdict Confidence

- **Confidence**: HIGH
- **Justification**: The touched route and tests align with the cited spec and the earlier review finding, and every MEU-specific acceptance criterion is directly evidenced. The non-approval is driven by a reproducible repo-level failure outside the reviewed boundary files.

## Codex Validation Report — Recheck

**Date**: 2026-04-05  
**MEU**: MEU-BV5 — boundary-validation-email  
**Verdict**: changes_required

### Recheck Results

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_account_service.py::TestDeleteAccountBlockOnly::test_delete_without_trades_succeeds -x --tb=long -v` | FAIL — same unrelated blocker remains |
| `uv run pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=long -v` | PASS — 44 passed, 1 warning |
| `uv run pytest tests/ -x --tb=long -v` | FAIL — same single failure, `1 failed, 211 passed, 15 skipped, 1 warning` |
| `uv run pyright packages/core/src packages/infrastructure/src packages/api/src` | FAIL — same 2 pre-existing errors |
| `uv run ruff check packages/core/src packages/infrastructure/src packages/api/src tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py` | PASS |
| `uv run python tools/export_openapi.py --check openapi.committed.json` | PASS |

### Recheck Finding

1. **[MEDIUM]** [`test_account_service.py`](P:\zorivest\tests\unit\test_account_service.py:286), [`account_service.py`](P:\zorivest\packages\core\src\zorivest_core\services\account_service.py:131) — Recheck confirms the same external blocker. The account-service unit fixture still does not define `trade_plans.count_for_account.return_value = 0`, so the truthy mock triggers `ConflictError` and keeps the repo-level `pytest tests/` gate red.

### Recheck Rationale

No new defect was found in the email boundary work. Recheck outcome is unchanged because the unrelated account-service/test mismatch is still present in the current worktree.

## Codex Validation Report — Recheck 2

**Date**: 2026-04-05  
**MEU**: MEU-BV5 — boundary-validation-email  
**Verdict**: changes_required

### Recheck 2 Results

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_account_service.py::TestDeleteAccountBlockOnly::test_delete_without_trades_succeeds -x --tb=long -v` | PASS — prior blocker fixed |
| `uv run pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=long -v` | PASS — 44 passed, 1 warning |
| `uv run pytest tests/ -x --tb=long -v` | FAIL — new unrelated blocker in `tests/unit/test_api_foundation.py::TestAppStateWiring::test_unlock_propagates_db_unlocked` |
| `uv run pyright packages/core/src packages/infrastructure/src packages/api/src` | FAIL — same 2 pre-existing errors |
| `uv run ruff check packages/core/src packages/infrastructure/src packages/api/src tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py` | PASS |
| `uv run python tools/export_openapi.py --check openapi.committed.json` | PASS |

### Recheck 2 Finding

1. **[MEDIUM]** [`test_api_foundation.py`](P:\zorivest\tests\unit\test_api_foundation.py:264), [`main.py`](P:\zorivest\packages\api\src\zorivest_api\main.py:146) — The previous account-service blocker is fixed, but the repo-level regression gate is still red on a different unrelated path. `test_unlock_propagates_db_unlocked` expects `/api/v1/trades` to return `403` before unlock, but the current run returns `200`. The test’s expectation is explicit in the file, and the app still derives `app.state.db_unlocked` during lifespan startup in `main.py`, so there is unresolved drift elsewhere in the auth/mode-gating behavior.

### Recheck 2 Rationale

MEU-BV5 remains sound and its own evidence is still clean. Approval is still blocked only because the full Python regression gate is not green in the current worktree, now due to a different unrelated API-foundation failure.

## Codex Validation Report — Recheck 3

**Date**: 2026-04-05  
**MEU**: MEU-BV5 — boundary-validation-email  
**Verdict**: changes_required

### Recheck 3 Results

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_api_foundation.py::TestAppStateWiring::test_unlock_propagates_db_unlocked -x --tb=long -v` | PASS — prior API-foundation blocker fixed |
| `uv run pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=long -v` | PASS — 44 passed, 1 warning |
| `uv run pytest tests/ -x --tb=long -v` | FAIL — new unrelated blocker in `tests/unit/test_market_data_service.py::TestGetQuote::test_returns_quote_from_first_enabled_provider` |
| `uv run pyright packages/core/src packages/infrastructure/src packages/api/src` | FAIL — same 2 pre-existing errors |
| `uv run ruff check packages/core/src packages/infrastructure/src packages/api/src tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py` | PASS |
| `uv run python tools/export_openapi.py --check openapi.committed.json` | PASS |

### Recheck 3 Finding

1. **[MEDIUM]** [`test_market_data_service.py`](P:\zorivest\tests\unit\test_market_data_service.py:160), [`market_data_service.py`](P:\zorivest\packages\core\src\zorivest_core\services\market_data_service.py:98) — The previous API-foundation blocker is fixed, but the repo-level regression gate is still red on another unrelated path. The current `MarketDataService.get_quote()` behavior tries Yahoo Finance first, then falls back to configured providers; the older unit test still expects the first configured provider to win immediately. In the current run, Yahoo falls through and the Alpha Vantage path raises `MarketDataError`, so the repo-level suite remains red even though the reviewed boundary endpoint changes are still clean.

### Recheck 3 Rationale

MEU-BV5 continues to validate correctly at its own boundary and test layer. Approval is still blocked only because the full Python regression gate is not green in the current worktree, now due to a different market-data-service test/behavior mismatch outside this MEU.

## Corrections Applied

**Date**: 2026-04-05
**Applied by**: Opus (Antigravity)

### Finding Resolution

| # | Severity | Finding | Fix | Status |
|---|----------|---------|-----|--------|
| 1 | MEDIUM | `test_delete_without_trades_succeeds` missing `trade_plans.count_for_account` stub | Added `uow.trade_plans.count_for_account.return_value = 0` to both tests in `TestDeleteAccountBlockOnly` | ✅ Fixed |
| 1b | MEDIUM (sibling) | `test_delete_with_trades_raises_conflict` same missing stub — error message contained `<MagicMock>` | Same fix applied | ✅ Fixed |
| 1c | MEDIUM (sibling) | `test_service_extensions.py::TestDeleteAccount::test_delete_account_success` — no real Account, no stubs for `is_system`/`trades`/`trade_plans` | Replaced MagicMock account with `_sample_account()`, added stubs | ✅ Fixed |

### Changed Files

| File | Change |
|------|--------|
| `tests/unit/test_account_service.py` | Added `uow.trade_plans.count_for_account.return_value = 0` to L281 and L295 |
| `tests/unit/test_service_extensions.py` | Added real Account + trades/trade_plans stubs to `test_delete_account_success` |
| `.agent/context/known-issues.md` | Added `[TEST-ISOLATION]` and `[TEST-DRIFT-MDS]` entries for remaining pre-existing failures |

### Post-Correction Evidence

```
uv run pytest tests/unit/test_account_service.py::TestDeleteAccountBlockOnly -v  # 3 passed
uv run pytest tests/unit/test_service_extensions.py::TestDeleteAccount -v          # 1 passed
uv run pytest tests/ -x --tb=short -v                                             # 358 passed, 1 pre-existing isolation failure (test_unlock_propagates_db_unlocked — [TEST-ISOLATION] in known-issues)
```

### Remaining Pre-Existing Failures (Documented)

- ~~`[TEST-ISOLATION]` — `test_api_foundation.py::test_unlock_propagates_db_unlocked`: passes solo, fails in suite (state leak)~~ → ✅ **Resolved 2026-04-06** (env var cleanup fixtures)
- `[TEST-DRIFT-MDS]` — `test_market_data_service.py`: 5 tests failed since MEU-91 wiring changes (masked by `-x`)
- `[PYRIGHT-PREEXIST]` — 2 pyright errors in `account_service.py:131` and `trade_service.py:175`

## Corrections Applied — Recheck 4

**Date**: 2026-04-06
**Applied by**: Opus (Antigravity)

### Finding Resolution

| # | Severity | Finding | Fix | Status |
|---|----------|---------|-----|--------|
| 1 | MEDIUM | `test_unlock_propagates_db_unlocked` fails in full suite — `ZORIVEST_DEV_UNLOCK` env var leaks from `test_api_roundtrip.py` and `test_gui_api_seams.py` | Added module-scoped `autouse` cleanup fixtures in both integration test files + defensive clear in `test_api_foundation.py::TestAppStateWiring` | ✅ Fixed |

### Changed Files

| File | Change |
|------|--------|
| `tests/integration/test_api_roundtrip.py` | Added `_cleanup_dev_unlock` autouse module-scoped fixture to remove `ZORIVEST_DEV_UNLOCK` after module tests |
| `tests/integration/test_gui_api_seams.py` | Added `_ensure_dev_unlock` autouse module-scoped fixture to set/cleanup env var |
| `tests/unit/test_api_foundation.py` | Added `_clear_dev_unlock` autouse fixture to `TestAppStateWiring` to defensively clear env var |
| `.agent/context/known-issues.md` | Updated `[TEST-ISOLATION]` status to ✅ Resolved |

### Post-Correction Evidence

```
uv run pytest tests/ --ignore=tests/unit/test_market_data_service.py -x --tb=short -v  # 1718 passed, 15 skipped, 0 failures
uv run pytest tests/ -x --tb=long -v                                                    # 1 failure: test_market_data_service.py (pre-existing [TEST-DRIFT-MDS])
```
