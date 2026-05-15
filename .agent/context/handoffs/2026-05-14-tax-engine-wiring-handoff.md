---
project: "2026-05-14-tax-engine-wiring"
meus: ["MEU-148", "MEU-149", "MEU-150", "MEU-151", "MEU-152", "MEU-153", "TAX-DBMIGRATION"]
status: "complete"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-05-14-tax-engine-wiring/implementation-plan.md"
template_version: "2.1"
agent: "antigravity-gemini"
predecessor: "2026-05-14-tax-optimization-tools-handoff.md"
---

<!-- CACHE BOUNDARY -->

# Handoff — Tax Engine Wiring (Phase 3E Session 5a)

> **Date:** 2026-05-14
> **MEUs:** 148–153 (6 of 6 complete, across 3 sessions) + TAX-DBMIGRATION ad-hoc
> **Status:** ✅ All implementation, verification, and ad-hoc migration complete

## Scope

**MEUs:** MEU-148 through MEU-153 — Tax REST API wiring, MCP tool wiring, YTD summary, deferred loss report, tax alpha report, transaction audit.
**Build Plan Section:** Phase 3E (items 75–80)
**Predecessor:** [2026-05-14-tax-optimization-tools-handoff.md](./2026-05-14-tax-optimization-tools-handoff.md)

## Acceptance Criteria

| AC | Description | Source | Status |
|----|-------------|--------|--------|
| AC-148.1 | Real TaxService wired into main.py lifespan | Spec: 04f-api-tax.md | ✅ |
| AC-148.2 | StubTaxService removed from stubs.py | Spec: 04f-api-tax.md | ✅ |
| AC-148.3 | Route handlers unpack bodies for real service | Spec: 04f-api-tax.md | ✅ |
| AC-148.5 | 2 new routes (deferred-losses, alpha) | Spec: 04f-api-tax.md | ✅ |
| AC-148.6 | record_payment persistence (QuarterlyEstimate) | Spec: 04f-api-tax.md | ✅ |
| AC-148.7 | Route-level integration tests verify real responses | Spec: 04f-api-tax.md | ✅ |
| AC-149.1 | 8 real actions replace 4 stubs in zorivest_tax | Spec: 05h-mcp-tax.md | ✅ |
| AC-149.4 | Zod schemas match Pydantic request schemas | Spec: 05h-mcp-tax.md | ✅ |
| AC-149.5 | Tool annotations set per spec | Spec: 05h-mcp-tax.md | ✅ |
| AC-149.6 | record_payment marked destructiveHint=true | Spec: 05h-mcp-tax.md | ✅ |
| AC-149.7 | Tax disclaimer included in MCP responses | Spec: 05h-mcp-tax.md | ✅ |
| AC-149.8 | seed.ts updated from "4 stubs" to "8 actions" | Local Canon | ✅ |
| AC-149.9 | client-detection.ts describes real tax tools | Local Canon | ✅ |
| AC-149.10 | All 8 actions return real data (not 501) | Spec: 05h-mcp-tax.md | ✅ |
| | **Ad-Hoc: TAX-DBMIGRATION (Inline Schema Migration)** | | |
| AC-MIG.1 | 3 ALTER TABLE statements added to `_inline_migrations` | Local Canon: known-issues.md | ✅ |
| AC-MIG.2 | `zorivest_tax(action:"lots")` returns `success: true` (was 500) | MCP Audit v4 finding I-2 | ✅ |
| AC-MIG.3 | `zorivest_tax(action:"estimate")` returns `success: true` (was 500) | MCP Audit v4 finding I-1 | ✅ |
| AC-MIG.4 | `zorivest_tax(action:"simulate")` returns `success: true` (was 500) | MCP Audit v4 finding I-3 | ✅ |
| AC-MIG.5 | `zorivest_tax(action:"ytd_summary")` returns `success: true` (was 500) | MCP Audit v4 finding I-4 | ✅ |
| AC-MIG.6 | Fresh DB via `create_all()` has all columns | Research-backed | ✅ |
| AC-MIG.7 | Migration idempotent (no error on re-run) | Research-backed | ✅ |

## Changed Files

### Session 2 (MEU-149 — MCP Wiring)

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/compound/tax-tool.ts` | rewritten | 4 stubs → 8 real actions with fetchApi proxy |
| `mcp-server/src/toolsets/seed.ts` | modified | "4 stub actions" → "8 actions", removed "tax stubs" |
| `mcp-server/src/client-detection.ts` | modified | "501 Not Implemented" → real tool descriptions |
| `mcp-server/tests/tax-tool.test.ts` | new | 15 Vitest tests for schema + proxy + metadata |
| `packages/api/src/zorivest_api/routes/tax.py` | modified | Fixed harvest route pyright errors (wrong params) |
| `docs/BUILD_PLAN.md` | modified | MEU-148–153 marked ✅ |

### Session 3 (TAX-DBMIGRATION — Inline Schema Migration)

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/main.py` | modified | Extracted `_get_inline_migrations()` module-level function; added 3 ALTER TABLE for `tax_lots` (`cost_basis_method`, `realized_gain_loss`, `acquisition_source`) |
| `tests/integration/test_inline_migrations.py` | new | 3 TDD tests: old-shape migration, idempotency, fresh-DB column assertion |
| `.agent/context/known-issues.md` | modified | TAX-DBMIGRATION moved from active to archived |
| `.agent/context/known-issues-archive.md` | modified | TAX-DBMIGRATION entry added with resolution details |

### Session 1 (MEU-148, MEU-150–153 — Service + API)

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/tax_service.py` | modified | record_payment persistence, ytd_summary, deferred_loss, tax_alpha, run_audit |
| `packages/api/src/zorivest_api/routes/tax.py` | modified | Stub retirement, real service wiring, new routes |
| `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | modified | QuarterlyEstimate repo registration |
| `tests/integration/test_tax_routes.py` | new | 20 integration tests |
| `tests/unit/test_tax_ytd_summary.py` | new | YTD summary TDD tests |
| `tests/unit/test_tax_deferred_loss.py` | new | Deferred loss TDD tests |
| `tests/unit/test_tax_alpha.py` | new | Tax alpha TDD tests |
| `tests/unit/test_tax_audit.py` | new | Transaction audit TDD tests |

## Evidence Bundle

| Gate | Result |
|------|--------|
| pytest (full suite) | 3627 passed, 23 skipped, 0 failed (post-migration) |
| pyright (packages/) | 0 errors, 0 warnings |
| ruff (packages/) | All checks passed |
| tsc (mcp-server/) | 0 errors |
| vitest (tax-tool.test.ts) | 15 passed |
| anti-placeholder scan | 1 match — catch clause only (valid defensive handler) |
| migration red phase | 1 failed (expected) — 3 columns missing before fix |
| migration green phase | 3 passed — old-shape, idempotency, fresh-DB |
| REST endpoint recovery | 4/4 endpoints return 200 (lots, estimate, simulate, ytd_summary) |
| MCP smoke: `zorivest_tax(action:"lots")` | `success: true`, 0 lots (AC-MIG.2) |
| MCP smoke: `zorivest_tax(action:"estimate")` | `success: true`, estimate data returned (AC-MIG.3) |
| MCP smoke: `zorivest_tax(action:"simulate")` | `success: true`, simulation data returned (AC-MIG.4) |
| MCP smoke: `zorivest_tax(action:"ytd_summary")` | `success: true`, YTD + quarterly payments returned (AC-MIG.5) |

## Design Decisions

1. **Compound tool pattern:** Used same router-dispatch pattern as `account-tool.ts` for consistency. Each action has strict Zod schema validated by router before dispatch.
2. **Tax disclaimer injection:** Added disclaimer text to every MCP response via `textResult()` helper, satisfying AC-149.7 without modifying individual action handlers.
3. **Harvest route simplification:** The harvest endpoint delegates to `get_trapped_losses()` rather than the full `scan_harvest_candidates()` which requires market data (current prices + tax profile) not accessible at the API layer.
4. **Idempotent payment recording:** `record_payment` checks for existing quarterly estimate before creating, preventing duplicate records.

## Registry Updates

- `BUILD_PLAN.md`: MEU-148 through MEU-153 all marked ✅

## Remaining Work

- **MEU-154 (gui-tax):** Tax estimator GUI (React) — Phase 12+ E2E wave
- **MEU-155 (gui-calculator):** Position calculator GUI — Phase 10+ E2E wave
- **MEU-156 (tax-section-toggles):** Section 475/1256/Forex toggles
- Phase 3E backend+MCP is now **fully complete** (6/6 MEUs + TAX-DBMIGRATION). Remaining Phase 3E items are GUI-only (MEU-154–156).
- **TAX-DBMIGRATION resolved** — all 4 tax endpoints recovered from 500 errors caused by missing columns.

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created (Session 1) | 2026-05-14 | antigravity-gemini | MEU-148, 150–153 implemented |
| Created (Session 2) | 2026-05-14 | antigravity-gemini | MEU-149 implemented, full handoff |
| Updated (Session 3) | 2026-05-14 | antigravity-gemini | TAX-DBMIGRATION ad-hoc: 3 ALTER TABLE + 3 TDD tests + 4 endpoints recovered |
