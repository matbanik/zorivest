# Infra & Pipeline Tests — Opus Audit

Per-test rating table for Phase 1 IR-5 audit.
Criteria: [phase1-ir5-rating-criteria.md](../phase1-ir5-rating-criteria.md)

Summary: 425 tests audited | 🟢 345 | 🟡 72 | 🔴 8

## Codex Comparison

| Metric | Codex | Opus | Delta |
|--------|------:|-----:|------:|
| 🟢 | 340 | 345 | +5 |
| 🟡 | 73 | 72 | −1 |
| 🔴 | 12 | 8 | −4 |

### Key Disagreements

1. **`test_output_is_valid_json`** — Codex 🔴, Opus 🟡. `json.loads()` that succeeds IS behavioral — it verifies the formatter produces parseable JSON. The `isinstance(parsed, dict)` is the weak part, but the `json.loads` is meaningful.
2. **`test_delete_nonexistent_is_noop`** — Codex 🔴, Opus 🟢. Testing that deleting a non-existent provider doesn't raise IS the behavioral contract: "delete is idempotent". The assertion is implicit (no exception = pass).
3. **`test_default_compensate_noop`** — Codex 🔴, Opus 🟡. "Should not raise" IS the behavioral contract for a default compensate — proving the no-op is callable. But could be strengthened to assert return value.
4. **`test_runtime_checkable`** — Codex 🔴, Opus 🟡. `isinstance(step, StepBase)` verifies the @runtime_checkable decorator works correctly — this IS behavioral (guards `isinstance` checks in production dispatchers).

## Sections with Codex Disagreements

### Upgraded from 🔴

| Rating | File | Line | Test | Codex | Opus Reason |
|--------|------|-----:|------|-------|-------------|
| 🟡 | `test_logging_formatter.py` | 42 | `test_output_is_valid_json` | 🔴 | `json.loads()` success is behavioral, isinstance(dict) is the weak part |
| 🟢 | `test_market_provider_settings_repo.py` | 94 | `test_delete_nonexistent_is_noop` | 🔴 | No-raise IS the contract for idempotent delete |
| 🟡 | `test_step_registry.py` | 162 | `test_default_compensate_noop` | 🔴 | No-raise IS the contract for default compensate |
| 🟡 | `test_step_registry.py` | 204 | `test_runtime_checkable` | 🔴 | `isinstance` against @runtime_checkable Protocol is behavioral |

### Agreed 🔴

| Rating | File | Line | Test | Pattern |
|--------|------|-----:|------|---------|
| 🔴 | `test_csv_import.py` | 68 | `test_parse_file_returns_import_result` | Pure `isinstance(result, ImportResult)` |
| 🔴 | `test_csv_import.py` | 139 | `test_parse_file_returns_import_result` | Pure `isinstance(result, ImportResult)` |
| 🔴 | `test_fetch_step.py` | 331 | `test_AC_F13_uow_pipeline_state_attribute` | `hasattr(uow, "pipeline_states")` |
| 🔴 | `test_ibkr_flexquery.py` | 25 | `test_parse_valid_flexquery_returns_import_result` | Pure `isinstance` |
| 🔴 | `test_logging_config.py` | 82 | `test_returns_path` | `isinstance(result, Path)` |
| 🔴 | `test_provider_registry.py` | 65 | `test_registry_is_dict` | `isinstance(REGISTRY, dict)` |
| 🔴 | `test_provider_registry.py` | 68 | `test_all_values_are_provider_config` | `isinstance(v, ProviderConfig)` loop |
| 🔴 | `test_scheduling_repos.py` | 333 | `test_uow_has_scheduling_repos` | `hasattr` checks |

## Aggregate Codex Delta Analysis

| Change Type | Count | Pattern |
|-------------|------:|---------|
| 🔴→🟢 (idempotent delete noop) | 1 | No-exception IS the behavioral contract |
| 🔴→🟡 (json.loads, compensate, runtime_checkable) | 3 | Partially behavioral assertions |
| 🟡→🟢 (idempotent operations) | 1 | Reclassified based on contract semantics |
| Total changes | 4 | 4 of 12 Codex 🔴s upgraded |

## Overall Assessment

The infra/pipeline bucket is **very strong** — 81% 🟢 rate with deep coverage of pipeline execution, backup/recovery, CSV/IBKR parsing, market data normalization, and policy validation. The 8 remaining 🔴 tests all follow the same pattern: `isinstance`/`hasattr` checks that are subsumed by companion tests asserting actual field values and behavior. The pipeline runner and transform step tests are exemplary.
