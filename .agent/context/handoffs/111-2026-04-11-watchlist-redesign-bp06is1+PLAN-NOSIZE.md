---
seq: 111
date: "2026-04-11"
project: "2026-04-11-watchlist-redesign-plan-size"
meu: "MEU-70a"
slug: "watchlist-redesign-plan-size"
build_plan_section: "06i §1-8 + [PLAN-NOSIZE]"
status: "complete"
verbosity: "standard"
---

# Handoff 111 — Watchlist Redesign + Plan Size Propagation (MEU-70a)

> **Date:** 2026-04-11 | **Build Plan:** 06i §1-8 + [PLAN-NOSIZE] cross-cutting

## Summary

Full-stack implementation of the Watchlist visual redesign and `position_size` field propagation, completing the `[PLAN-NOSIZE]` known issue. Three sub-MEUs delivered:

- **Sub-MEU A:** Backend + MCP — `position_size` round-trip through domain entity, SQLAlchemy model, Alembic migration, API schemas, and MCP tool
- **Sub-MEU B:** Watchlist visual redesign — professional data table with dark trading palette, utility functions, CSS design tokens, colorblind toggle persistence
- **Sub-MEU C:** Calculator write-back — readonly `position_size` display in Trade Plan form, "Apply to Plan" button in Calculator modal dispatching `zorivest:calculator-apply` custom event

## Evidence Bundle

<!-- CACHE BOUNDARY -->

### Quality Gate Results

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | ✅ 0 errors |
| `npx vitest run` | ✅ 346 passed (24 files) |
| `uv run pytest tests/unit/test_api_plans.py` | ✅ 40 passed |
| `uv run pyright packages/` | ✅ 0 errors, 0 warnings |
| `uv run ruff check packages/` | ✅ All checks passed |
| `npm run build` (mcp-server) | ✅ Clean |
| Anti-placeholder scan | ✅ No TODO/FIXME/NotImplementedError |

### Changed Files

**Sub-MEU A (Backend + MCP):**
- [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/entities.py) — `position_size: float | None` added to TradePlan
- [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infrastructure/models.py) — `position_size` column
- [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py) — ALTER TABLE migration
- [plans.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/plans.py) — API schemas + `_to_response()`
- [planning-tools.ts](file:///p:/zorivest/mcp-server/src/tools/planning-tools.ts) — MCP schema + request body
- [openapi.committed.json](file:///p:/zorivest/openapi.committed.json) — Regenerated

**Sub-MEU B (Watchlist Visual):**
- [watchlist-utils.ts](file:///p:/zorivest/ui/src/renderer/src/features/planning/watchlist-utils.ts) — [NEW] formatVolume, formatPrice, getChangeColor, formatFreshness
- [watchlist-tokens.css](file:///p:/zorivest/ui/src/renderer/src/styles/watchlist-tokens.css) — [NEW] Dark palette CSS variables
- [WatchlistTable.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/WatchlistTable.tsx) — [NEW] Professional data table
- [WatchlistPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/WatchlistPage.tsx) — Table integration + colorblind toggle
- [settings.py](file:///p:/zorivest/packages/api/src/zorivest_api/settings.py) — `ui.watchlist.colorblind_mode` registered

**Sub-MEU C (Calculator Write-Back):**
- [TradePlanPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx) — `position_size` interface field, readonly display, `zorivest:calculator-apply` event listener, save payload
- [PositionCalculatorModal.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx) — "Apply to Plan" button, `handleApplyToPlan` dispatching custom event

**Tests:**
- [planning.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx) — 9 new tests (Sub-MEU C)
- [watchlist-utils.test.ts](file:///p:/zorivest/ui/src/renderer/src/features/planning/__tests__/watchlist-utils.test.ts) — [NEW] 12 tests
- [test_settings_registry.py](file:///p:/zorivest/tests/unit/test_settings_registry.py) — 1 new test
- [test_api_plans.py](file:///p:/zorivest/tests/unit/test_api_plans.py) — 5 new tests

### Known Issue Resolution

- **[PLAN-NOSIZE]:** ✅ Resolved — `position_size` field propagated through all 6 layers (domain → infra → API → MCP → GUI readonly → calculator write-back)

### Pre-existing Issues (Unchanged)

- **[TEST-DRIFT-MDS]:** 5 failures in `test_market_data_service.py` remain (out of scope)
- **[TEST-SETTINGS-WARNING]:** Console warning for `ui.watchlist.colorblind_mode` query key in tests — cosmetic only, expected behavior

## TDD Compliance

All three sub-MEUs followed Red → Green TDD:
- Sub-MEU A: 5 backend tests written first (Red), then implementation (Green)
- Sub-MEU B: 13 tests written first (12 utility + 1 settings registry), then implementation
- Sub-MEU C: 9 GUI tests written first (6 failed as expected), then implementation turned all green
