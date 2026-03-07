---
meu: 4
slug: value-objects
phase: 1
priority: P0
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 2
tests_added: 23
tests_passing: 66
---

# MEU-4 Handoff: Value Objects

## Scope

Implement the 5 frozen value object dataclasses from `01-domain-layer.md` §1.2: Money, PositionSize, Ticker, Conviction, ImageData. All include `__post_init__` validation per Standing Project Rule #2.

Build plan reference: [01-domain-layer.md §1.2](../../docs/build-plan/01-domain-layer.md)

## Feature Intent Contract

### Intent Statement

The domain exposes 5 frozen value objects with best-practice validation. Negative money is rejected, tickers are uppercased, image dimensions must be positive, and all are immutable.

### Acceptance Criteria

| AC | Description | Test(s) | Status |
|----|-------------|---------|--------|
| AC-1 | `Money` frozen dataclass with `amount` (Decimal) and `currency` (str, default "USD") | `test_money_construction`, `test_money_default_currency_is_usd` | ✅ |
| AC-2 | `Money` rejects negative amount | `test_money_rejects_negative_amount` | ✅ |
| AC-3 | `Money` rejects empty currency | `test_money_rejects_empty_currency` | ✅ |
| AC-4 | `PositionSize` frozen dataclass: `share_size` (int), `position_size` (Decimal), `risk_per_share` (Decimal) | `test_position_size_construction` | ✅ |
| AC-5 | `PositionSize` rejects negative share_size | `test_position_size_rejects_negative_share_size` | ✅ |
| AC-6 | `Ticker` normalizes symbol to uppercase | `test_ticker_normalizes_to_uppercase`, `test_ticker_already_uppercase_unchanged` | ✅ |
| AC-7 | `Ticker` rejects empty/whitespace-only symbol | `test_ticker_rejects_empty_symbol`, `test_ticker_rejects_whitespace_only_symbol` | ✅ |
| AC-8 | `Conviction` frozen dataclass with ConvictionLevel | `test_conviction_construction` | ✅ |
| AC-9 | `ImageData` frozen dataclass with data, mime_type, width, height | `test_image_data_construction` | ✅ |
| AC-10 | `ImageData` rejects non-positive width/height | `test_image_data_rejects_non_positive_width`, `test_image_data_rejects_non_positive_height` | ✅ |
| AC-11 | `ImageData` rejects empty data | `test_image_data_rejects_empty_data` | ✅ |
| AC-12 | All value objects are frozen (FrozenInstanceError) | `test_money_is_frozen`, `test_position_size_is_frozen`, `test_ticker_is_frozen`, `test_conviction_is_frozen`, `test_image_data_is_frozen` | ✅ |
| AC-13 | Import surface: `__future__`, `dataclasses`, `decimal`, `zorivest_core.domain.enums` only | `test_import_surface_value_objects` | ✅ |

### Negative Cases

- Must NOT allow negative Money amounts
- Must NOT preserve lowercase in Ticker symbols
- Must NOT allow zero or negative image dimensions
- Must NOT allow mutable attribute assignment on any value object

### Test Mapping

| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | `tests/unit/test_value_objects.py` | `test_money_construction` |
| AC-1 | `tests/unit/test_value_objects.py` | `test_money_default_currency_is_usd` |
| AC-1 | `tests/unit/test_value_objects.py` | `test_money_zero_amount_allowed` |
| AC-2 | `tests/unit/test_value_objects.py` | `test_money_rejects_negative_amount` |
| AC-3 | `tests/unit/test_value_objects.py` | `test_money_rejects_empty_currency` |
| AC-4 | `tests/unit/test_value_objects.py` | `test_position_size_construction` |
| AC-5 | `tests/unit/test_value_objects.py` | `test_position_size_rejects_negative_share_size` |
| AC-6 | `tests/unit/test_value_objects.py` | `test_ticker_normalizes_to_uppercase` |
| AC-6 | `tests/unit/test_value_objects.py` | `test_ticker_already_uppercase_unchanged` |
| AC-7 | `tests/unit/test_value_objects.py` | `test_ticker_rejects_empty_symbol` |
| AC-7 | `tests/unit/test_value_objects.py` | `test_ticker_rejects_whitespace_only_symbol` |
| AC-8 | `tests/unit/test_value_objects.py` | `test_conviction_construction` |
| AC-9 | `tests/unit/test_value_objects.py` | `test_image_data_construction` |
| AC-10 | `tests/unit/test_value_objects.py` | `test_image_data_rejects_non_positive_width` |
| AC-10 | `tests/unit/test_value_objects.py` | `test_image_data_rejects_non_positive_height` |
| AC-11 | `tests/unit/test_value_objects.py` | `test_image_data_rejects_empty_data` |
| AC-12 | `tests/unit/test_value_objects.py` | `test_money_is_frozen` |
| AC-12 | `tests/unit/test_value_objects.py` | `test_position_size_is_frozen` |
| AC-12 | `tests/unit/test_value_objects.py` | `test_ticker_is_frozen` |
| AC-12 | `tests/unit/test_value_objects.py` | `test_conviction_is_frozen` |
| AC-12 | `tests/unit/test_value_objects.py` | `test_image_data_is_frozen` |
| AC-13 | `tests/unit/test_value_objects.py` | `test_import_surface_value_objects` |
| (integrity) | `tests/unit/test_value_objects.py` | `test_module_has_expected_classes` |

## Design Decisions & Known Risks

- **Decision**: `Ticker.__post_init__` uses `object.__setattr__` — **Reasoning**: Frozen dataclasses cannot use normal assignment in `__post_init__`. `object.__setattr__` is the standard workaround. — **ADR**: inline (minor)
- **Decision**: Zero is allowed for Money but negative is not — **Reasoning**: Zero balance or zero-cost trades are valid domain scenarios; negative money is always invalid. — **ADR**: inline (minor)
- **Decision**: `PositionSize` only validates `share_size ≥ 0` — **Reasoning**: `position_size` and `risk_per_share` can be zero (edge case from calculator). Negative shares has no domain meaning.
- **Risk**: `ImageData` does not validate mime_type — differs from `ImageAttachment.mime_type` enforcement. By design: ImageData is a raw payload, mime validation belongs to the entity layer.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `packages/core/src/zorivest_core/domain/value_objects.py` | Created | 5 frozen value object dataclasses, 82 lines |
| `tests/unit/test_value_objects.py` | Created | 23 test functions across 8 test classes, 235 lines |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest tests/unit/test_value_objects.py -x --tb=short -v` (Red) | FAIL | ModuleNotFoundError — expected |
| `uv run pytest tests/unit/test_value_objects.py -x --tb=short -v` (Green) | PASS (23 tests) | 0.04s |
| `uv run pytest tests/unit/ -x --tb=short -v` | PASS (66 tests) | 0.07s |
| `uv run pyright packages/core/src/` | PASS | 0 errors, 0 warnings, 0 informations |
| `uv run ruff check packages/core/src/ tests/` | PASS | All checks passed |

## FAIL_TO_PASS Evidence

| Criterion | Test | Red Phase | Green Phase | Status |
|-----------|------|-----------|-------------|--------|
| AC-1 | `test_money_construction` | FAIL (ModuleNotFoundError) | PASS | ✅ FAIL_TO_PASS |
| AC-2 | `test_money_rejects_negative_amount` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-3 | `test_money_rejects_empty_currency` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-4 | `test_position_size_construction` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-5 | `test_position_size_rejects_negative_share_size` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-6 | `test_ticker_normalizes_to_uppercase` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-7 | `test_ticker_rejects_empty_symbol` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-12 | `test_money_is_frozen` | FAIL | PASS | ✅ FAIL_TO_PASS |
| AC-13 | `test_import_surface_value_objects` | FAIL | PASS | ✅ FAIL_TO_PASS |
| (regression) | Prior MEUs (43 tests) | PASS | PASS | ✅ PASS_TO_PASS |

---

## Codex Validation Report

{Left blank — Codex fills this section during validation-review workflow}
