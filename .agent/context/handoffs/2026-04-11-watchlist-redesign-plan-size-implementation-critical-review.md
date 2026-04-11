---
date: "2026-04-11"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md"
verdict: "approved"
findings_count: 1
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex GPT-5"
---

# Critical Review: watchlist-redesign-plan-size

> **Review Mode**: `handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/111-2026-04-11-watchlist-redesign-bp06is1+PLAN-NOSIZE.md`
**Review Type**: `implementation review`
**Checklist Applied**: `IR + DR`

Correlation rationale:

- The user provided the work handoff explicitly.
- Its frontmatter project slug `2026-04-11-watchlist-redesign-plan-size` matches `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/`.
- The correlated `task.md` and `implementation-plan.md` describe a single-MEU project (`MEU-70a`), so no sibling-handoff expansion was required.
- `docs/build-plan/06i-gui-watchlist-visual.md` was pulled into scope because the handoff claims full delivery of the watchlist redesign contract.

Working-tree note:

- Review was performed against the current working tree. `git status --short` shows this project’s files are still local/uncommitted, and the reviewed work handoff itself is currently untracked.

## Commands Executed

```powershell
rg -n "plan-position-size|calculator-apply|position_size|plan-save-btn|zorivest:open-calculator" ui/src/renderer/src/features/planning/TradePlanPage.tsx
rg -n "ui\.watchlist\.colorblind_mode|localStorage|settings|api/v1/settings" ui/src/renderer/src/hooks/usePersistedState.ts ui/src/renderer/src/features/planning/WatchlistPage.tsx
rg -n "4000|Math\.random|15_000|setInterval|setTimeout|watchlist-table|colorblind-toggle|watchlist-freshness" ui/src/renderer/src/features/planning/WatchlistPage.tsx ui/src/renderer/src/features/planning/WatchlistTable.tsx ui/src/renderer/src/features/planning/__tests__/planning.test.tsx
rg -n "Frozen ticker column|sticky header|Last updated Xs ago|Colorblind-safe toggle|refetchInterval: 5000|4000 \+ Math\.random|Ticker.*frozen" docs/build-plan/06i-gui-watchlist-visual.md
rg -n "346 passed|stagger interval|coloring, and toggle|WatchlistTable rendering|Professional data table|full verification plan" .agent/context/handoffs/111-2026-04-11-watchlist-redesign-bp06is1+PLAN-NOSIZE.md docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md
uv run pytest tests/unit/test_api_plans.py -x --tb=short -v
uv run pytest tests/unit/test_settings_registry.py -x --tb=short -v
cd ui; npx vitest run src/renderer/src/features/planning/__tests__/watchlist-utils.test.ts
cd ui; npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx
cd ui; npx tsc --noEmit
uv run pyright packages/
uv run ruff check packages/
cd mcp-server; npm run build
git status --short
```

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The watchlist quote refresh contract was not implemented as planned. The build-plan Level 1 contract requires `refetchInterval: 5000` plus staggered `4000 + Math.random() * 1000` timing, but the shipped hook uses per-ticker `setTimeout(..., idx * 200)` and a fixed `setInterval(fetchAll, 15_000)`. This is materially slower than the promised 4-5s refresh cadence and makes the handoff’s redesign completion claim inaccurate. | `docs/build-plan/06i-gui-watchlist-visual.md:135-136`; `ui/src/renderer/src/features/planning/WatchlistPage.tsx:58-81` | Align the hook with the approved cadence or explicitly revise the plan/spec and handoff evidence through `/planning-corrections`. | open |
| 2 | High | The review evidence overstates watchlist test coverage. The approved plan says `planning.test.tsx` adds tests for `WatchlistTable` rendering, coloring, and the colorblind toggle, but the actual watchlist block only covers page render, row presence, and CRUD flows. There are no assertions for quote columns, gain/loss formatting, colorblind-toggle behavior, freshness display, or polling cadence, which is why Finding 1 still passes green. | `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:126`; `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:280-350`; `.agent/context/handoffs/111-2026-04-11-watchlist-redesign-bp06is1+PLAN-NOSIZE.md:33` | Add redesign-specific tests before claiming full watchlist verification, then update the handoff evidence to match what is actually exercised. | open |
| 3 | Medium | The Level 1 “frozen ticker column” requirement is still missing. The stylesheet makes only header cells sticky, while `.wl-ticker` only applies text styling and the ticker cells are rendered as ordinary table cells. Horizontal overflow therefore will not preserve the ticker anchor column promised by the spec. | `docs/build-plan/06i-gui-watchlist-visual.md:26,123`; `ui/src/renderer/src/styles/watchlist-tokens.css:63-71,110-114`; `ui/src/renderer/src/features/planning/WatchlistTable.tsx:83-109` | Implement sticky left positioning for the ticker header/body cells or narrow the spec with source-backed approval. | open |

---

## Checklist Results

### Implementation Review (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | pass | `uv run pytest tests/unit/test_api_plans.py -x --tb=short -v` reproduced `40 passed`; real-wiring round-trip for `position_size` is present at `tests/unit/test_api_plans.py:736-778`. |
| IR-5 Test rigor audit | fail | `watchlist-utils.test.ts` is mostly strong, but `planning.test.tsx:280-350` does not exercise the redesign behaviors it was supposed to cover. The watchlist portion is only CRUD/row-presence coverage, so the quote cadence drift escaped. |
| IR-6 Boundary validation coverage | pass | `tests/unit/test_api_plans.py` includes create/update extra-field 422 checks and invalid enum/blank-string checks; reproduced green in the targeted pytest run. |

### Docs / Claim Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | The plan and handoff claim redesign-specific UI coverage, but actual `planning.test.tsx` coverage does not match those claims. |
| DR-4 Verification robustness | fail | `npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx` passed while the live watchlist code still violates the approved polling contract. |
| DR-7 Evidence freshness | pass | Reproduced targeted checks on 2026-04-11: `pytest` (40 + 20 passed), `vitest` (65 + 30 passed), `tsc`, `pyright`, `ruff`, and `npm run build` all completed successfully. |

### IR-5 Test Rigor Audit

| File | Rating | Notes |
|------|--------|-------|
| `tests/unit/test_api_plans.py` | Strong | Asserts concrete response values, includes negative-path 422/404/409 checks, and includes a real-wiring POST→GET round-trip for `position_size`. |
| `tests/unit/test_settings_registry.py` | Strong | Concrete metadata assertions for the new registry key; low ambiguity. |
| `ui/src/renderer/src/features/planning/__tests__/watchlist-utils.test.ts` | Adequate | Most assertions are value-specific, but zero/null color cases only assert “not gain/loss”, which would miss some wrong neutral colors. |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` (watchlist section) | Weak | No assertions for columns, formatting, toggle persistence, freshness, or polling cadence despite the plan/handoff claiming those behaviors were covered. |
| `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` (`position_size` section) | Strong | Readonly display, event dispatch/listener behavior, and PUT payload propagation are asserted with concrete values. |

---

## Verdict

`changes_required` — the backend/API/MCP `position_size` propagation is well covered and reproduced cleanly, but the watchlist redesign portion is not complete against the approved Level 1 contract and the current verification story materially overclaims what the UI tests prove.

---

## Follow-Up Actions

1. Route the correction pass through `/planning-corrections`.
2. Fix `WatchlistPage.tsx` quote refresh timing to match the approved 4-5s staggered contract, or explicitly revise the plan/build-plan with a source-backed decision.
3. Add redesign-specific UI tests in `planning.test.tsx` for quote columns, gain/loss formatting, colorblind toggle behavior, freshness display, and the polling cadence.
4. Implement the frozen ticker column or narrow the promised Level 1 scope with explicit approval.

## Residual Risk

If corrections stop after the polling fix alone, the watchlist redesign can still regress quietly because the current UI suite does not protect the core visual/data-contract behaviors that made this review fail.

---

## Recheck (2026-04-11)

**Workflow**: `/planning-corrections` recheck
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Quote refresh cadence mismatched approved 4-5s contract | open | ✅ Fixed |
| Watchlist redesign tests overstated coverage | open | ❌ Still open |
| Frozen ticker column missing | open | ✅ Fixed |

### Confirmed Fixes

- The quote timing now matches the previously flagged contract: [WatchlistPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/WatchlistPage.tsx:83) defines `REFRESH_BASE_MS = 4000`, `REFRESH_JITTER_MS = 1000`, and [WatchlistPage.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/WatchlistPage.tsx:110) now uses `setInterval(fetchAll, 5000)`.
- The frozen ticker column is implemented: [watchlist-tokens.css](/p:/zorivest/ui/src/renderer/src/styles/watchlist-tokens.css:104) makes `.wl-ticker` sticky with `left: 0`, and [watchlist-tokens.css](/p:/zorivest/ui/src/renderer/src/styles/watchlist-tokens.css:113) gives the header ticker cell higher stacking order.
- The test file did gain meaningful watchlist assertions for quote formatting and gain/loss coloring in [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:1380).

### Remaining Findings

- **Medium** — The watchlist verification gap is reduced but not closed. `planning.test.tsx` now asserts table formatting and color changes, but it still does not cover the remaining behaviors that were part of the redesign contract: colorblind-toggle interaction/persistence, freshness rendering, or polling cadence. The watchlist page test block at [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:280) still focuses on CRUD flows, and the added table-focused block at [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:1380) covers formatting/colors/notes only. During recheck, `npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx` still emitted repeated React Query warnings for `["settings","ui.watchlist.colorblind_mode"]`, which further indicates the toggle persistence path is not cleanly exercised by the suite.

### Recheck Evidence

- `uv run pytest tests/unit/test_api_plans.py -x --tb=short -v` → `40 passed`
- `cd ui; npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx` → `77 passed`
- `cd ui; npx tsc --noEmit` → passed

### Verdict

`changes_required` — two of the three original findings are closed, but the review thread cannot be approved until the UI tests cover the remaining redesign behaviors cleanly enough to catch regressions in toggle persistence, freshness, and polling.

---

## Recheck (2026-04-11, Pass 3)

**Workflow**: `/planning-corrections` recheck
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Quote refresh cadence mismatched approved 4-5s contract | fixed | ✅ Still fixed |
| Watchlist redesign tests overstated coverage | open | ✅ Fixed |
| Frozen ticker column missing | fixed | ✅ Still fixed |

### Confirmed Fixes

- The watchlist tests now cover the previously missing redesign behaviors:
  - freshness rendering in [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:1531)
  - colorblind toggle persistence via Settings API in [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:1560)
  - quote polling cadence in [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:1640)
- Reproduced `npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx` now at `82 passed`, so the prior coverage gap is closed.

### Remaining Findings

- **Low** — The focused vitest run is green but still emits repeated React Query warnings for `["settings","ui.watchlist.colorblind_mode"]`. The generic watchlist-page tests still mock unmatched settings requests as `{}` in [planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:280), while [usePersistedState.ts](/p:/zorivest/ui/src/renderer/src/hooks/usePersistedState.ts:17) reads `result.value` and can pass through `undefined` before the final `data ?? defaultValue` fallback. This does not invalidate the corrected watchlist behavior, but it is still noisy test evidence and worth cleaning in a follow-up.

### Recheck Evidence

- `uv run pytest tests/unit/test_api_plans.py -x --tb=short -v` → `40 passed`
- `cd ui; npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx` → `82 passed`
- `cd ui; npx tsc --noEmit` → passed

### Verdict

`approved` — the previously blocking watchlist findings are now closed. One low-severity warning remains in test output, but it does not materially misstate shipped behavior or the corrected redesign contract.
