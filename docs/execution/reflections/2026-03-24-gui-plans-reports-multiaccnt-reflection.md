# Reflection: GUI Plans, Reports & Multi-Account
**Date:** 2026-03-24  
**MEUs:** MEU-48 (gui-plans), MEU-54 (multi-account-ui), MEU-55 (report-gui)  
**Project:** `2026-03-20-gui-plans-reports-multiaccnt`

---

## What Went Well

### TDD Discipline
- All three MEUs followed the red-green cycle cleanly. The planning unit test suite grew from 0 to ~52 tests, with clear FAIL_TO_PASS evidence at every step.
- The `position-size.test.ts` E2E tests came up green for computation on the first implementation pass.

### Incremental Scoping
- MEU-48 expansion scope (Tier 1–3) was layered on top of the base without scope creep — each tier was clearly justified: Tier 1 = pure frontend, Tier 2 = backend timestamps, Tier 3 = MEU-65-dependent market data fill.
- MEU-70b UX polish (segmented buttons, picker feedback) was cleanly scoped and documented without reopening MEU-48's core.

### E2E Axe Pattern Discovery
- Identified the **Electron + axe-core CSP incompatibility pattern** for future reuse:
  - `@axe-core/playwright` v4.11.1 uses `Target.createTarget` → unsupported in Electron
  - `page.addScriptTag` → blocked by CSP `script-src 'self'`
  - **Solution**: Pass axe source as evaluate argument → `new Function(src)()` bypasses both
- This pattern should be codified into `emerging-standards.md` (E2E axe injection section).

---

## What Was Harder Than Expected

### Accessibility Violations from Background Elements
- The axe scan runs on the full page (not scoped to modal) in Electron. This surfaced violations in `TradePlanPage` filter `<select>` elements that were always visible behind the open calculator modal.
- Lesson: design E2E axe tests to run on a predictable, fully-populated page state — not during modal overlays — OR scope to modal root.

### Finding the Right Axe Injection Strategy
- Three failed approaches before landing on `page.evaluate(new Function(src)())`:
  1. `AxeBuilder.include()` → `Target.createTarget` error
  2. `AxeBuilder` without `.include()` → same error  
  3. `page.addScriptTag({ path })` → CSP violation
- The working pattern is non-obvious and required iterative debugging. Should be documented prominently.

---

## Gaps / Follow-ups

| Item | Status | Owner |
|------|--------|-------|
| `launch.test.ts` axe test pre-existing failure | Known, tracked | MEU-70 follow-up |
| Account balance auto-load for calculator (`C1`) | Deferred | MEU-71 dependency |
| `W4` Watchlist visual redesign | Research complete | Future MEU |
| `position-size.test.ts` axe scan should scope to modal root | Enhancement | E2E Wave 5 |

---

## Rule Adherence Audit (Top 10 rules)

| Rule | Applied? | Notes |
|------|----------|-------|
| TDD: write test first | ✅ | All features had failing tests before implementation |
| `data-testid` on all interactive elements | ✅ | Calculator modal, filters, buttons all testid'd |
| WCAG 2.1 AA via axe | ✅ | E2E Wave 4 gate enforced |
| `refetchInterval: 5_000` (G5) | ✅ | All queries use interval |
| File deletion policy — save to pomera first | ✅ | No files deleted |
| Handoff per MEU | ✅ | 087, 088, 089 created |
| Single responsibility PATCH for status | ✅ | `PATCH /{id}/status` separate from PUT |
| Commit message convention | 🔄 | Prepared — awaiting user approval |
| Emerging standards UX1/UX2/UX3 | ✅ | Documented and followed |
| No placeholder code in handoffs | ✅ | All ACs have mapped tests |

**Rule Adherence: 90%** (1 item pending: commit message)
