# 2026-04-05 Boundary Validation Email Market Data - Implementation Critical Review

> Date: 2026-04-06
> Review mode: implementation
> Target plan: `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/`
> Seed handoffs: `101-2026-04-05-boundary-market-data-bp08s8.4.md`, `102-2026-04-05-boundary-email-bp06fs6f.md`
> Canonical review file: `.agent/context/handoffs/2026-04-05-boundary-validation-email-market-data-implementation-critical-review.md`

## Scope and Correlation

- Implementation review mode was selected because the user provided completed work handoffs, and both handoffs point to the same plan folder and shared project slug `2026-04-05-boundary-validation-email-market-data`.
- Full project scope was expanded from the two explicit handoffs plus their shared plan/task files and the correction evidence they reference.
- Reviewed artifacts:
  - `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/implementation-plan.md`
  - `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/task.md`
  - `.agent/context/handoffs/101-2026-04-05-boundary-market-data-bp08s8.4.md`
  - `.agent/context/handoffs/102-2026-04-05-boundary-email-bp06fs6f.md`
  - `packages/api/src/zorivest_api/routes/market_data.py`
  - `packages/api/src/zorivest_api/routes/email_settings.py`
  - `tests/unit/test_market_data_api.py`
  - `tests/unit/test_api_email_settings.py`
  - `tests/unit/test_account_service.py`
  - `tests/unit/test_service_extensions.py`
  - `tests/integration/test_api_roundtrip.py`
  - `tests/integration/test_gui_api_seams.py`
  - `tests/unit/test_api_foundation.py`
  - `tests/unit/test_market_data_service.py`
  - `packages/core/src/zorivest_core/services/market_data_service.py`
  - `.agent/context/known-issues.md`
  - `.agent/context/meu-registry.md`
  - `docs/BUILD_PLAN.md`
  - `docs/execution/reflections/2026-04-05-boundary-validation-email-market-data.md`

## Findings

### Medium - Project evidence artifacts are stale after the correction passes, so the completion record is no longer internally consistent

- The latest correction sections in handoffs 101 and 102 claim the suite state improved to `1718 passed, 15 skipped, 0 failures` when `tests/unit/test_market_data_service.py` is excluded, and `known-issues.md` now records `[TEST-ISOLATION]` as resolved on 2026-04-06 (`.agent/context/known-issues.md:33`).
- The project task file still marks the regression step complete with the older result `211 passed, 1 pre-existing failure ('test_delete_without_trades_succeeds'), 15 skipped` (`docs/execution/plans/2026-04-05-boundary-validation-email-market-data/task.md:19`), even though that specific blocker was fixed in later correction passes.
- The project reflection still reports the old regression metric `211 passed, 1 pre-existing fail` (`docs/execution/reflections/2026-04-05-boundary-validation-email-market-data.md:27`) and still frames the known-issues gap around the earlier account-service failure (`docs/execution/reflections/2026-04-05-boundary-validation-email-market-data.md:16`), which is no longer the current state reflected in the rolling handoffs and `known-issues.md`.
- Fresh evidence from the current tree confirms the later state, not the original task/reflection state:
  - `uv run pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=short -v` -> `44 passed, 1 warning`
  - `uv run pytest tests/ --ignore=tests/unit/test_market_data_service.py -x --tb=short -v` -> `1718 passed, 15 skipped, 3 warnings`
  - `uv run pytest tests/unit/test_market_data_service.py -v` -> `5 failed, 8 passed, 1 warning`
- Under the repo’s evidence-freshness and project-artifact consistency rules, the execution artifacts should describe the latest validated state, not an earlier superseded failure snapshot.

## What Checked Clean

- The BV4 route hardening remains correct in file state:
  - `ProviderConfigRequest` has `extra="forbid"`, `StrippedStr`, and numeric constraints in `packages/api/src/zorivest_api/routes/market_data.py:36`.
  - The boundary tests still pass in `tests/unit/test_market_data_api.py`.
- The BV5 route hardening remains correct in file state:
  - `EmailConfigRequest` has `extra="forbid"`, constrained `Literal` fields, preserved password exception semantics, and numeric constraints in `packages/api/src/zorivest_api/routes/email_settings.py:59`.
  - The boundary tests still pass in `tests/unit/test_api_email_settings.py`.
- The prior unrelated blockers called out in the rolling handoffs were actually corrected:
  - `tests/unit/test_account_service.py:277` and `tests/unit/test_account_service.py:296` now stub `trade_plans.count_for_account.return_value = 0`.
  - `tests/unit/test_service_extensions.py:212` now uses a real sample account plus explicit trades/trade_plans stubs.
  - `tests/integration/test_api_roundtrip.py:21`, `tests/integration/test_gui_api_seams.py:30`, and `tests/unit/test_api_foundation.py:254` now contain the env-var cleanup fixtures that resolved `[TEST-ISOLATION]`.
- The remaining `test_market_data_service.py` drift is accurately documented as unrelated:
  - `known-issues.md:41` says 5 tests fail in that module.
  - Fresh run of `uv run pytest tests/unit/test_market_data_service.py -v` reproduced exactly `5 failed, 8 passed, 1 warning`.
- Registry and build-plan tracking for the two MEUs are present:
  - `.agent/context/meu-registry.md:213`
  - `.agent/context/meu-registry.md:214`
  - `docs/BUILD_PLAN.md:267`

## Commands Executed

```powershell
rg -n "_cleanup_dev_unlock|_ensure_dev_unlock|_clear_dev_unlock|test_returns_quote_from_first_enabled_provider|Yahoo Finance is always tried first|TEST-DRIFT-MDS|TEST-ISOLATION|ProviderConfigRequest|EmailConfigRequest|TestProviderConfigBoundaryValidation|TestEmailConfigBoundaryValidation" tests/integration/test_api_roundtrip.py tests/integration/test_gui_api_seams.py tests/unit/test_api_foundation.py tests/unit/test_market_data_service.py packages/core/src/zorivest_core/services/market_data_service.py packages/api/src/zorivest_api/routes/market_data.py packages/api/src/zorivest_api/routes/email_settings.py .agent/context/known-issues.md
rg -n "211 passed|1 pre-existing failure|1718 passed|MEU-BV4|MEU-BV5|BOUNDARY-GAP|F5 Market Data|F6 Email Settings" docs/execution/plans/2026-04-05-boundary-validation-email-market-data/task.md docs/execution/reflections/2026-04-05-boundary-validation-email-market-data.md docs/BUILD_PLAN.md .agent/context/meu-registry.md .agent/context/known-issues.md
uv run pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=short -v *> C:\Temp\zorivest\crf-bv-targeted.txt
uv run pytest tests/ --ignore=tests/unit/test_market_data_service.py -x --tb=short -v *> C:\Temp\zorivest\crf-suite-ignore-mds.txt
uv run pytest tests/unit/test_market_data_service.py -v *> C:\Temp\zorivest\crf-mds-file.txt
uv run pyright packages/core/src packages/infrastructure/src packages/api/src *> C:\Temp\zorivest\crf-pyright.txt
uv run ruff check packages/core/src packages/infrastructure/src packages/api/src tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py *> C:\Temp\zorivest\crf-ruff.txt
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\crf-openapi.txt
```

## Command Results Summary

| Command | Result |
|---|---|
| `pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=short -v` | PASS (`44 passed, 1 warning`) |
| `pytest tests/ --ignore=tests/unit/test_market_data_service.py -x --tb=short -v` | PASS (`1718 passed, 15 skipped, 3 warnings`) |
| `pytest tests/unit/test_market_data_service.py -v` | FAIL (`5 failed, 8 passed, 1 warning`) |
| `pyright packages/core/src packages/infrastructure/src packages/api/src` | FAIL (`2` pre-existing errors already documented in `known-issues.md`) |
| `ruff check ...` | PASS |
| `python tools/export_openapi.py --check openapi.committed.json` | PASS |

## Adversarial Verification Checklist

| Check | Result | Notes |
|---|---|---|
| AV-1 Failing-then-passing proof | PASS | The project-specific boundary suites stay green, and the previously reported unrelated blockers in account-service and API foundation were corrected in current file state. |
| AV-2 No bypass hacks | PASS | No skip/xfail or assertion bypasses were introduced in the reviewed correction files. |
| AV-3 Changed paths exercised by assertions | PASS | The BV4/BV5 boundary assertions remain explicit and green in the current tree. |
| AV-4 No skipped/xfail masking | PASS | No masking found in the reviewed target files. |
| AV-5 No unresolved placeholders | PASS | No TODO/FIXME/NotImplementedError found in the reviewed target files. |
| AV-6 Source-backed criteria | PASS | The boundary contracts still match the cited spec and local-canon sources in the plan and handoffs. |
| AV-7 Boundary schema enforcement | PASS | The reviewed write boundaries still have explicit Pydantic schemas with closed extra-field policy. |
| AV-8 Create/update parity | PASS | No new parity gap was found in the BV4/BV5 routes under review. |
| AV-9 Invalid input produces 4xx | PASS | Current BV4/BV5 route suites still prove controlled `422` behavior for invalid payloads. |

## Open Questions / Assumptions

- This review treats `[TEST-DRIFT-MDS]` as out-of-scope technical debt for BV4/BV5 approval because it is already documented in `known-issues.md`, reproduced independently, and does not originate in the reviewed route/schema files.
- This review applies the repo’s evidence-freshness rule to project artifacts, so stale task/reflection metrics are treated as a real completion issue even though product behavior for the reviewed MEUs is currently correct.

## Verdict

`changes_required`

## Residual Risk

- Runtime risk on the reviewed BV4/BV5 boundaries is low from the evidence I checked; the remaining issue is process integrity, not a new boundary bug.
- The project should not be treated as fully closed until the task/reflection artifacts are refreshed to match the latest validated state and clearly separate unrelated pre-existing failures from this project's delivered behavior.

## Recheck - 2026-04-06

### Result

- No new findings.
- The prior evidence-freshness finding is resolved in current file state:
  - `docs/execution/plans/2026-04-05-boundary-validation-email-market-data/task.md` now records the refreshed full-regression state (`1718 passed, 15 skipped, 0 failures` excluding `[TEST-DRIFT-MDS]`) and an explicit evidence-refresh correction item.
  - `docs/execution/reflections/2026-04-05-boundary-validation-email-market-data.md` now records the refreshed metrics, marks the earlier evidence drift as resolved, and documents the post-completion correction passes coherently.
- The reviewed BV4/BV5 boundary hardening remains clean in current file state, and the unrelated residual blockers remain accurately separated from this project:
  - `uv run pytest tests/unit/test_market_data_api.py tests/unit/test_api_email_settings.py -x --tb=short -v` -> `44 passed, 1 warning`
  - `uv run pytest tests/ --ignore=tests/unit/test_market_data_service.py -x --tb=short -v` -> `1718 passed, 15 skipped, 3 warnings`
  - `uv run pytest tests/unit/test_market_data_service.py -v` -> `5 failed, 8 passed, 1 warning`
  - `uv run pyright packages/core/src packages/infrastructure/src packages/api/src` -> same 2 pre-existing errors already documented in `known-issues.md`
  - `uv run ruff check ...` -> PASS
  - `uv run python tools/export_openapi.py --check openapi.committed.json` -> PASS

## Updated Verdict

`approved`

## Updated Residual Risk

- No new runtime risk was found in the reviewed BV4/BV5 scope on recheck.
- The unrelated `[TEST-DRIFT-MDS]` and `[PYRIGHT-PREEXIST]` items remain open technical debt outside this review scope, but they are now documented consistently with the project artifacts.
