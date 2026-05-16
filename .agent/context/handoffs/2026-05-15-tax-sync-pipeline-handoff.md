---
date: "2026-05-15"
project: "tax-sync-pipeline"
meu: "MEU-216, MEU-217, MEU-218"
status: "complete"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-05-15-tax-sync-pipeline/implementation-plan.md"
build_plan_section: "bp03as82a-82c"
agent: "antigravity"
reviewer: "codex"
predecessor: "2026-05-14-tax-gui-handoff.md"
---

# Handoff: 2026-05-15-tax-sync-pipeline-handoff

> **Status**: `complete`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-216 (Sync Schema), MEU-217 (Sync Service), MEU-218 (Full-Stack Wiring)
**Build Plan Section**: [03a-tax-data-sync.md](file:///p:/zorivest/docs/build-plan/03a-tax-data-sync.md)
**Predecessor**: [2026-05-14-tax-gui-handoff.md](file:///p:/zorivest/.agent/context/handoffs/2026-05-14-tax-gui-handoff.md)

---

## Acceptance Criteria

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-216-1 | TaxLot has `materialized_at` field | Spec | test_tax_sync_schema.py::test_taxlot_has_materialized_at | ✅ |
| AC-216-2 | TaxLot has `is_user_modified` field | Spec | test_tax_sync_schema.py::test_taxlot_has_is_user_modified | ✅ |
| AC-216-3 | TaxLot has `source_hash` field | Spec | test_tax_sync_schema.py::test_taxlot_has_source_hash | ✅ |
| AC-216-4 | TaxLot has `sync_status` field | Spec | test_tax_sync_schema.py::test_taxlot_has_sync_status | ✅ |
| AC-216-5 | TaxLotModel has matching columns | Spec | test_tax_sync_schema.py::test_taxlotmodel_has_provenance_columns | ✅ |
| AC-216-6 | SETTINGS_REGISTRY has `tax.conflict_resolution` | Spec | test_tax_sync_schema.py::test_conflict_resolution_setting | ✅ |
| AC-217-1 | sync_lots creates lots from BOT trades | Spec | test_tax_sync_service.py::test_sync_creates_lots_from_bot_trades | ✅ |
| AC-217-2 | sync_lots is idempotent | Spec | test_tax_sync_service.py::test_sync_is_idempotent | ✅ |
| AC-217-3 | SHA-256 change detection | Spec | test_tax_sync_service.py::test_sha256_change_detection | ✅ |
| AC-217-4 | Returns SyncReport | Spec | test_tax_sync_service.py::test_sync_returns_sync_report | ✅ |
| AC-217-5 | Flags orphaned lots | Spec | test_tax_sync_service.py::test_flags_orphaned_lots | ✅ |
| AC-217-6 | flag strategy flags conflicts | Spec | test_tax_sync_service.py::test_flag_strategy_flags_conflicts | ✅ |
| AC-217-7 | auto_resolve strategy resolves | Spec | test_tax_sync_service.py::test_auto_resolve_strategy | ✅ |
| AC-217-8 | block strategy raises SyncAbortError | Spec | test_tax_sync_service.py::test_block_strategy_raises | ✅ |
| AC-217-9 | Per-account scoping | Spec | test_tax_sync_service.py::test_per_account_scoping | ✅ |
| AC-217-10 | Populates materialized_at on create | Spec | test_tax_sync_service.py::test_populates_materialized_at | ✅ |
| AC-218-1 | POST /api/v1/tax/sync-lots returns 200 | Spec | test_tax_sync_api.py::test_sync_lots_returns_200 | ✅ |
| AC-218-2 | account_id parameter scopes sync | Spec | test_tax_sync_api.py::test_account_id_passed_to_service | ✅ |
| AC-218-4 | Response has all count fields | Spec | test_tax_sync_api.py::test_response_has_all_count_fields | ✅ |
| AC-218-5 | SyncAbortError → 409 Conflict | Spec | test_tax_sync_api.py::test_block_mode_returns_409 | ✅ |
| AC-218-9 | API response mirrors service report | Spec (G25) | test_tax_sync_parity.py::test_api_response_mirrors_service_report | ✅ |
| AC-218-10 | All three surfaces expose sync_lots | Spec (G25) | test_tax_sync_parity.py::TestTriSurfaceAvailability (4 tests) | ✅ |

<!-- CACHE BOUNDARY -->

---

## Evidence

### FAIL_TO_PASS

| Test | Red Output | Green Output | File:Line |
|------|-----------|--------------|-----------|
| 6 schema tests | `ModuleNotFoundError` / `AssertionError` | 6 passed | test_tax_sync_schema.py |
| 10 service tests | `AttributeError: 'TaxService' has no attribute 'sync_lots'` | 10 passed | test_tax_sync_service.py |
| 4 API tests | `assert 404 == 200` (endpoint missing) | 4 passed | test_tax_sync_api.py |
| 5 parity tests | `assert '/sync-lots' in route_paths` | 5 passed | test_tax_sync_parity.py |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/ -x --tb=short` | 0 | 3668 passed, 23 skipped |
| `uv run pyright packages/` | 0 | 0 errors, 0 warnings |
| `uv run ruff check packages/` | 0 | All checks passed |
| `npx tsc --noEmit` (mcp-server) | 0 | Clean |
| `npx tsc --noEmit` (ui) | 0 | Clean |

### Quality Gate Results

```
pyright: 0 errors, 0 warnings
ruff: 0 violations
pytest: 3668 passed, 0 failed, 23 skipped
anti-placeholder: not run (no new stubs)
```

---

## Changed Files

| File | Action | Lines | Summary |
|------|--------|-------|---------|
| `packages/core/.../entities.py` | modified | 221-226 | +4 provenance fields to TaxLot |
| `packages/core/.../settings.py` | modified | 289-302 | +tax.conflict_resolution setting |
| `packages/core/.../exceptions.py` | modified | 56-62 | +SyncAbortError exception |
| `packages/core/.../tax_service.py` | modified | 1770-1970 | +sync_lots(), SyncReport, SyncConflict VOs |
| `packages/infrastructure/.../models.py` | modified | 885-896 | +4 provenance columns to TaxLotModel |
| `packages/infrastructure/.../tax_repository.py` | modified | 72-80,230-260 | Provenance field mapping |
| `packages/api/.../routes/tax.py` | modified | 469-491 | +POST /api/v1/tax/sync-lots endpoint |
| `mcp-server/src/compound/tax-tool.ts` | modified | 228-258 | +sync_lots action in compound tool |
| `ui/.../tax/TaxDashboard.tsx` | modified | 13-14,91-145 | +Process Tax Lots button + sync mutation |
| `ui/.../tax/test-ids.ts` | modified | 22 | +SYNC_BUTTON test ID |
| `tests/unit/test_tax_sync_schema.py` | new | 1-177 | MEU-216 FIC (6 tests) |
| `tests/unit/test_tax_sync_service.py` | new | 1-350+ | MEU-217 FIC (10 tests) |
| `tests/unit/test_tax_sync_api.py` | new | 1-150 | MEU-218 API FIC (4 tests) |
| `tests/unit/test_tax_sync_parity.py` | new | 1-155 | G25 parity tests (5 tests) |
| `tests/unit/test_tax_entities.py` | modified | 20,54-59 | Field count 14→18 |
| `tests/unit/test_settings_registry.py` | modified | 32-168 | Registry count 28→29 |
| `docs/BUILD_PLAN.md` | modified | 686-688,826 | MEU-216/217/218 → ✅, P3 count 33→36 |

---

## Codex Validation Report

_Left blank for reviewer agent._

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-05-15 | antigravity | Initial handoff — MEU-216/217/218 complete |
| Updated | 2026-05-16 | antigravity | MEU-218h/i ad-hoc additions: ARIA accessibility remediation, contextual help panels, Electron link fix, G26/G27 emerging standards |

---

## Ad-Hoc Additions (2026-05-16)

### MEU-218h — ARIA Accessibility Remediation (Tasks 77–80)

Deep audit and remediation of WCAG 2.1 AA accessibility across 8 tax tabs:
- **Tab navigation**: WAI-ARIA tab pattern (`role="tablist/tab/tabpanel"`) in `TaxLayout`
- **Dynamic regions**: `role="status/alert"` + `aria-live` for Audit, Simulator, Wash Sale, Quarterly
- **Labeling**: `aria-label` on tables/interactions; `aria-hidden="true"` on decorative emoji
- **State**: `aria-expanded`, `aria-current` on navigation/disclosure elements

### MEU-218i — Contextual Help Panels (Tasks 81–97)

Integrated `TaxHelpCard` component across all 8 tax tabs:
- **Content**: `tax-help-content.ts` — structured data with What/Source/Calculation/Learn More per tab
- **Component**: `TaxHelpCard.tsx` — collapsible card with WAI-ARIA disclosure, `localStorage` persistence
- **Integration**: All 8 tabs (Dashboard, Lots, WashSale, Simulator, Harvesting, Quarterly, Audit, Profiles)
- **Bug fix (Task #97)**: Replaced `<a target="_blank">` with `window.electron.openExternal()` for IRS links

### New Emerging Standards

| Standard | Title | Severity | Summary |
|----------|-------|----------|---------|
| G26 | Contextual Help Panel Pattern | 🟡 Medium | Feature modules must include collapsible inline help cards with What/Source/Calculation sections, localStorage persistence, and ARIA disclosure |
| G27 | Electron External Links Must Use Preload Bridge | 🔴 Critical | Never use `<a target="_blank">` in Electron — always use `window.electron.openExternal()` |

### Additional Changed Files

| File | Action | Summary |
|------|--------|---------|
| `ui/.../tax/TaxHelpCard.tsx` | new | Shared help card component with ARIA disclosure + localStorage |
| `ui/.../tax/tax-help-content.ts` | new | Structured help content for all 8 tax tabs |
| `ui/.../tax/TaxDashboard.tsx` | modified | +TaxHelpCard integration |
| `ui/.../tax/TaxLotViewer.tsx` | modified | +TaxHelpCard integration |
| `ui/.../tax/WashSaleMonitor.tsx` | modified | +TaxHelpCard + flex-col wrapper |
| `ui/.../tax/WhatIfSimulator.tsx` | modified | +TaxHelpCard integration |
| `ui/.../tax/LossHarvestingTool.tsx` | modified | +TaxHelpCard integration |
| `ui/.../tax/QuarterlyTracker.tsx` | modified | +TaxHelpCard integration |
| `ui/.../tax/TransactionAudit.tsx` | modified | +TaxHelpCard integration |
| `ui/.../tax/TaxProfileManager.tsx` | modified | +TaxHelpCard + flex-col wrapper |
| `ui/.../tax/test-ids.ts` | modified | +HELP_CARD test ID |
| `.agent/docs/emerging-standards.md` | modified | +G26 (Help Panel) + G27 (Electron links) |
| `docs/.../task.md` | modified | Tasks 77–97 added for ad-hoc MEU-218h/i |
| `docs/.../implementation-plan.md` | modified | MEU-218h/i sections documented |
