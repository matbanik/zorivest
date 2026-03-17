# Phase 1 IR-5 Summary

Full per-test audit output for `2026-03-16-test-rigor-audit`.

## Method

- Scope: all Python unit tests, Python integration tests, MCP Vitest suites, and UI Vitest suites.
- Unit of audit: test function or declared test case (`def test_*`, class test method, `it(...)`, `test(...)`). Parameterized runtime expansions are not double-counted because the task asked for per-test-function review.
- Rating basis: IR-5 criteria from `.agent/workflows/critical-review-feedback.md`.

## Execution Baseline

- `uv run pytest tests/ --tb=no -q` -> `1373 passed, 1 skipped`
- `Set-Location mcp-server; npx vitest run` -> `160 passed`
- `Set-Location ui; npx vitest run` -> `56 passed`

## Totals

- Declared tests audited: 1469
- Python declarations: 1257 | 🟢 985 | 🟡 201 | 🔴 71
- TypeScript declarations: 212 | 🟢 199 | 🟡 13 | 🔴 0
- Overall: 🟢 1184 | 🟡 214 | 🔴 71

## By Category

- API Route Tests: 167 tests | 🟢 90 | 🟡 74 | 🔴 3
- Domain Model Tests: 349 tests | 🟢 296 | 🟡 12 | 🔴 41
- Service Layer Tests: 268 tests | 🟢 220 | 🟡 35 | 🔴 13
- Infra and Pipeline Tests: 425 tests | 🟢 340 | 🟡 73 | 🔴 12
- Integration Tests: 48 tests | 🟢 39 | 🟡 7 | 🔴 2
- MCP Server Tests: 156 tests | 🟢 151 | 🟡 5 | 🔴 0
- UI Tests: 56 tests | 🟢 48 | 🟡 8 | 🔴 0

## Highest-Risk Files

| File | 🟢 | 🟡 | 🔴 |
|---|---:|---:|---:|
| `tests/unit/test_ports.py` | 7 | 3 | 8 |
| `tests/unit/test_exceptions.py` | 4 | 0 | 6 |
| `tests/unit/test_market_data_entities.py` | 14 | 0 | 6 |
| `tests/unit/test_events.py` | 12 | 0 | 5 |
| `tests/unit/test_commands_dtos.py` | 39 | 0 | 4 |
| `tests/unit/test_analytics.py` | 24 | 0 | 3 |
| `tests/unit/test_pipeline_enums.py` | 14 | 0 | 3 |
| `tests/unit/test_scheduling_models.py` | 10 | 6 | 2 |
| `tests/unit/test_csv_import.py` | 25 | 5 | 2 |
| `tests/unit/test_report_service.py` | 16 | 3 | 2 |
| `tests/unit/test_rate_limiter.py` | 4 | 1 | 2 |
| `tests/unit/test_step_registry.py` | 17 | 1 | 2 |
| `tests/unit/test_entities.py` | 42 | 0 | 2 |
| `tests/unit/test_enums.py` | 15 | 0 | 2 |
| `tests/unit/test_provider_registry.py` | 15 | 0 | 2 |
| `tests/unit/test_service_extensions.py` | 12 | 0 | 2 |
| `tests/unit/test_logging_config.py` | 12 | 8 | 1 |
| `tests/unit/test_api_foundation.py` | 15 | 5 | 1 |
| `tests/unit/test_logging_formatter.py` | 5 | 5 | 1 |
| `tests/unit/test_api_settings.py` | 8 | 4 | 1 |

## Companion Tables

- `api.md` -> API Route Tests
- `domain.md` -> Domain Model Tests
- `service.md` -> Service Layer Tests
- `infra-pipeline.md` -> Infra and Pipeline Tests
- `integration.md` -> Integration Tests
- `mcp.md` -> MCP Server Tests
- `ui.md` -> UI Tests

Machine-readable export: `docs/execution/plans/2026-03-16-test-rigor-audit/phase1-ir5-per-test-ratings.csv`
