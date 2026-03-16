---
meu: 86
slug: transform-step
phase: 9
priority: P1
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 6
tests_added: 15
tests_passing: 15
---

# MEU-86: TransformStep

## Scope

Implements TransformStep — transforms raw market data through field mapping, Pandera schema validation, quality gating, and security-first write dispositions. Includes field mapping registry (provider→canonical names), OHLCV schema validation with row-level quarantine, quality threshold enforcement, table/column allowlists for parameterized SQL writes, and integer-micros financial precision utilities.

Build plan reference: [09-scheduling.md §9.5](file:///p:/zorivest/docs/build-plan/09-scheduling.md)

## Feature Intent Contract

### Intent Statement
The transform stage that maps, validates, and persists market data with security guardrails and financial precision.

### Acceptance Criteria
- AC-T1: TransformStep auto-registers in STEP_REGISTRY with type_name="transform"
- AC-T2: Params validates required target_table field
- AC-T3: apply_field_mapping() maps 5 known OHLCV fields + captures unmapped in _extra
- AC-T4: apply_field_mapping() returns {_extra: {}} for empty input
- AC-T5: validate_dataframe() passes all-valid OHLCV data (2 rows → 2 valid, 0 quarantined)
- AC-T6: validate_dataframe() quarantines records with negative prices (1 valid, 1 quarantined)
- AC-T7: Quality threshold: 2/10 < 0.8 → failed; 9/10 ≥ 0.8 → passed (2 sub-tests)
- AC-T8: TABLE_ALLOWLIST rejects unknown tables including SQL injection attempts
- AC-T9: validate_columns rejects unknown column names ("DROP TABLE")
- AC-T10: to_micros/from_micros round-trip + edge cases (near-zero, large values) (2 sub-tests)
- AC-T11: parse_monetary avoids classic float precision error (0.1 + 0.2 == 0.3)
- AC-T12: TransformStep declares side_effects=True
- AC-T13: Live UoW write_append creates actual rows in SQLite (COUNT(*) == 2)

### Negative Cases
- Must NOT: Allow writes to tables not in TABLE_ALLOWLIST
- Must NOT: Allow columns not in the table's column allowlist
- Must NOT: Pass quality check when valid_count/total_count < threshold

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-T1 | `tests/unit/test_transform_step.py` | `test_AC_T1_transform_step_auto_registers` |
| AC-T2 | `tests/unit/test_transform_step.py` | `test_AC_T2_params_validates_required_target_table` |
| AC-T3 | `tests/unit/test_transform_step.py` | `test_AC_T3_field_mapping_with_extras` |
| AC-T4 | `tests/unit/test_transform_step.py` | `test_AC_T4_field_mapping_empty_input` |
| AC-T5 | `tests/unit/test_transform_step.py` | `test_AC_T5_validate_valid_ohlcv` |
| AC-T6 | `tests/unit/test_transform_step.py` | `test_AC_T6_validate_quarantines_invalid` |
| AC-T7 | `tests/unit/test_transform_step.py` | `test_AC_T7_quality_below_threshold`, `test_AC_T7_quality_above_threshold` |
| AC-T8 | `tests/unit/test_transform_step.py` | `test_AC_T8_table_allowlist_rejects_unknown` |
| AC-T9 | `tests/unit/test_transform_step.py` | `test_AC_T9_validate_columns_rejects_unknown` |
| AC-T10 | `tests/unit/test_transform_step.py` | `test_AC_T10_micros_round_trip`, `test_AC_T10_micros_precision_edge_cases` |
| AC-T11 | `tests/unit/test_transform_step.py` | `test_AC_T11_parse_monetary_precision` |
| AC-T12 | `tests/unit/test_transform_step.py` | `test_AC_T12_transform_step_side_effects` |
| AC-T13 | `tests/unit/test_transform_step.py` | `test_AC_T13_live_uow_write_append` |

## Design Decisions & Known Risks

- **Decision**: `FIELD_MAPPINGS` uses `(provider, data_type)` tuple key — **Reasoning**: Supports provider-specific mappings while allowing a "generic" catch-all.
- **Decision**: `OHLCV_SCHEMA` uses `strict=False` — **Reasoning**: Allows extra columns (like `_extra`) through validation without rejection.
- **Decision**: `TABLE_ALLOWLIST` is a compile-time dict, not DB-backed — **Reasoning**: Security boundary should be auditable in code, not dynamically configurable.
- **Decision**: `write_append` uses parameterized SQL via `text()` — **Reasoning**: SQLAlchemy `text()` with named params prevents SQL injection while allowing dynamic table/column targeting within the allowlist.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `packages/core/src/zorivest_core/pipeline_steps/transform_step.py` | Created | TransformStep with Params (target_table, mapping, write_disposition, validation_rules, quality_threshold) |
| `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py` | Created | FIELD_MAPPINGS registry + apply_field_mapping() |
| `packages/core/src/zorivest_core/services/validation_gate.py` | Created | Pandera OHLCV schema, validate_dataframe(), check_quality() |
| `packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py` | Created | TABLE_ALLOWLIST, validate_table(), validate_columns(), write_append(), write_replace(), write_merge() |
| `packages/core/src/zorivest_core/domain/precision.py` | Created | to_micros(), from_micros(), parse_monetary() |
| `tests/unit/test_transform_step.py` | Created | 15 tests covering AC-T1 through AC-T13 |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest tests/unit/test_transform_step.py -v` | PASS (15/15) | All green |
| `uv run pytest tests/ --tb=no -q` | PASS (1356/1356, 1 skip) | Full regression |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_transform_step.py` (15 tests) | FAIL (module not found) | PASS |

## Test Rigor Audit (IR-5)

All 15 tests rated 🟢 Strong — MEU-86 had the highest initial test quality:

| Test | Rating | Notes |
|------|--------|-------|
| AC-T1 | 🟢 | Registry key + identity |
| AC-T2 | 🟢 | Positive + negative |
| AC-T3 | 🟢 | All 5 fields + _extra value verified |
| AC-T4 | 🟢 | Edge case: empty input |
| AC-T5 | 🟢 | Real Pandera + DataFrame |
| AC-T6 | 🟢 | Quarantine with negative price |
| AC-T7 (2) | 🟢 | Both sides of threshold |
| AC-T8 | 🟢 | SQL injection attempt tested |
| AC-T9 | 🟢 | "DROP TABLE" column |
| AC-T10 (2) | 🟢 | Round-trip + edge cases |
| AC-T11 | 🟢 | Classic 0.1+0.2 Decimal test |
| AC-T12 | 🟢 | Attribute check |
| AC-T13 | 🟢 | Full integration with COUNT(*) |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
