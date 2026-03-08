# Task Handoff

## Task

- **Date:** 2026-03-07
- **Task slug:** 012-logging-manager
- **Owner role:** coder
- **Scope:** MEU-1A — LoggingManager, FEATURES registry, bootstrap, QueueListener lifecycle

## Inputs

- Plan: `docs/execution/plans/2026-03-07-logging-infrastructure/implementation-plan.md`
- Spec: `docs/build-plan/01a-logging.md` lines 238–407
- Dependencies: MEU-2A (filters, formatters), MEU-3A (redaction)

## Role Plan

1. coder (FIC + Red + Green)
2. tester (quality gate)
3. reviewer (Codex validation)

## Coder Output

- Changed files:

| File | Change |
|------|--------|
| `packages/infrastructure/src/zorivest_infra/logging/config.py` | NEW — `LoggingManager`, `FEATURES` (12 entries), `get_feature_logger()`, `get_log_directory()`, defaults |
| `tests/unit/test_logging_config.py` | NEW — 21 tests covering AC-1 through AC-14 |

- Commands run:
  - `uv run pytest tests/unit/test_logging_config.py -x --tb=short -v` — Red: ModuleNotFoundError → Green: 21 passed in 0.87s
- Design notes:
  - `shutdown()` made idempotent: sets `_listener = None` after `stop()` to prevent double-stop crash
  - Used `queue.Queue[logging.LogRecord]` for typed queue
  - `configure_from_settings()` reads level from `logging.{feature}.level` settings key pattern
  - Default rotation: 10 MB, 5 backups (spec 01a:282–284)
  - QueueListener uses `respect_handler_level=True` (spec 01a:379–380)
  - Thread safety verified with 3 threads × 50 messages each

## Tester Output

- Commands run:
  - `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/logging/config.py` — All blocking checks passed (1.62s)
  - pyright: PASS, ruff: PASS, pytest: 21 PASS, anti-placeholder: PASS, anti-deferral: PASS
  - Full suite: `uv run pytest tests/unit/test_logging_filters.py tests/unit/test_logging_formatter.py tests/unit/test_logging_redaction.py tests/unit/test_logging_config.py -v` — 57 passed in 0.89s
  - Anti-placeholder: `rg "TODO|FIXME|NotImplementedError" packages/infrastructure/` — CLEAN
- Pass/fail: ALL PASS
- FAIL_TO_PASS: Red=ModuleNotFoundError → Green=21/21 pass

## Negative Cases

- `get_feature_logger("unknown")` raises `ValueError`
- Empty settings dict uses all defaults
- `shutdown()` called twice without error (idempotent)
- Feature level gating: INFO messages filtered when level set to WARNING
- Thread safety: 150 concurrent log entries produce valid JSONL

## Test Mapping

| AC | Test Method(s) |
|----|---------------|
| AC-1 | `TestFeaturesRegistry::test_features_count`, `test_all_expected_features_present` |
| AC-2 | `TestGetFeatureLogger::test_returns_named_logger` |
| AC-3 | `TestGetFeatureLogger::test_unknown_feature_raises_value_error` |
| AC-4 | `TestGetLogDirectory::test_returns_path`, `test_directory_exists_after_call`, `test_contains_zorivest_logs` |
| AC-5 | `TestBootstrap::test_creates_bootstrap_file` |
| AC-6 | `TestBootstrap::test_bootstrap_log_written` |
| AC-7 | `TestConfigureFromSettings::test_creates_feature_files` |
| AC-8 | `TestConfigureFromSettings::test_feature_routing` |
| AC-9 | `TestConfigureFromSettings::test_catchall_routing` |
| AC-10 | `TestUpdateFeatureLevel::test_update_gates_messages` |
| AC-11 | `TestShutdown::test_shutdown_stops_listener` |
| AC-12 | `TestThreadSafety::test_concurrent_logging` |
| AC-13 | `TestConfigureFromSettings::test_settings_level_respected` |
| AC-14 | `TestConfigureFromSettings::test_default_rotation_values` |

## Reviewer Output

- Findings by severity:
- Open questions:
- Verdict:
- Residual risk:
- Anti-deferral scan result:

## Approval Gate

- **Approval status:** pending (awaiting Codex validation)
