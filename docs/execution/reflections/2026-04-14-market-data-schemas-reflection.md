# Reflection — MEU-PW3: Market Data Schemas

**Date:** 2026-04-14
**MEU:** MEU-PW3 (`market-data-schemas`)
**Build Plan Section:** 09-scheduling §9.5c (§49.6)

## What Went Well

- TDD discipline held — all 67 tests written before any implementation.
- Clean Red→Green transition with zero test modifications.
- Found and fixed a **latent bug** in `validate_dataframe()`: Pandera uses `float('nan')` not `None` for column-level failure indices. Without this MEU, missing-column data would silently pass validation.

## What Was Learned

1. **Pandera NaN semantics**: `failure_cases["index"]` returns `NaN` (float) for column-level errors, not Python `None`. The `is not None` check is insufficient — must use `pd.isna()`.
2. **ORM table count coupling**: Adding new models requires updating `EXPECTED_TABLES` set and count assertions in `test_models.py` — a coupling worth documenting.
3. **Field mapping completeness**: The `_extra` key pattern in `apply_field_mapping()` provides a clean forward-compatibility mechanism for unmapped provider fields.

## What Could Improve

- Consider adding a schema auto-discovery mechanism to eliminate manual `SCHEMA_REGISTRY` updates when new schemas are added.
- The `validate_dataframe()` function could benefit from structured error reporting (returning error details, not just valid/quarantined splits).

## Metrics

- **Test count:** 67 new tests (25 ORM + 21 schema + 21 mapping)
- **Files changed:** 4 modified, 3 new
- **Duration:** ~45 min (planning review + Red + Green + verification)
- **MEU gate:** 8/8 pass
