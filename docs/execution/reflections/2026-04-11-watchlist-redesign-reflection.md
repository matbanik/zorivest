---
project: "2026-04-11-watchlist-redesign-plan-size"
meu: "MEU-70a"
date: "2026-04-11"
---

# Reflection — Watchlist Redesign + Plan Size Propagation (MEU-70a)

## What Went Well

1. **Cross-cutting field propagation was clean.** Adding `position_size` through 6 layers (entity → model → migration → API → MCP → GUI) took minimal effort because each layer follows consistent patterns established in earlier MEUs.

2. **Custom event pattern works well.** The `zorivest:calculator-apply` / `zorivest:open-calculator` bidirectional event pattern decouples the Calculator modal from the Trade Plan page cleanly. No prop drilling or state lifting needed.

3. **TDD caught real issues.** Writing the 9 Red-phase tests before implementation surfaced the exact insertion points needed in TradePlanPage.tsx and validated the event payload shape before writing a single line of production code.

4. **Sub-MEU decomposition was effective.** Splitting into A (backend), B (visual), C (write-back) allowed focused TDD cycles with clear deliverables.

## What Could Improve

1. **MEU-70a was not in the build priority matrix.** The `06i-gui-watchlist-visual.md` build plan section exists but had no corresponding entry in `build-priority-matrix.md`. This required extra navigation to find the right source references during planning.

2. **Settings query warning in tests.** The `ui.watchlist.colorblind_mode` query key warning appears in all watchlist tests because the MSW mock returns `undefined` for unknown settings. ✅ Resolved in continuation session — added settings mock to 5 test blocks; 1 residual warning remains (React Query timing race, non-blocking).

---

## Continuation Session — Bug Fixes, Critical Review, Test Coverage

### What Happened

User-reported defects triggered a second phase of work:
1. Colorblind toggle only changed its own button color (not table cells)
2. Tickers showed `"-"` everywhere (market data not wired)
3. Notes column showed icons instead of editable text
4. No visual difference between colorblind on/off in dark theme
5. Column headers not sortable

Critical review (3 passes) identified test coverage gaps for freshness rendering, colorblind persistence, and polling cadence.

### Friction Points

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| F1 | 🔴 Critical | **Agent bypassed TDD for bug fixes.** User had to explicitly correct: "perform TDD do not just adjust the code!" | Added failing tests reproducing each bug before fixing. Bug-fix TDD must be default behavior. |
| F2 | 🟡 Medium | **Colorblind toggle placement not documented.** No rationale found for placing it in watchlist view vs global settings. | Design decision was undocumented — should have been recorded in plan's Design Decisions section. |
| F3 | 🟡 Medium | **Market data columns intentionally show placeholders** but tests didn't assert this explicitly, and no MEU dependency was documented. | Added placeholder assertion tests. Market data wiring depends on real-time data MEU. |
| F4 | 🟡 Medium | **Colorblind mode had no visible effect.** Dark/light theme showed identical colors. Tests only verified CSS class changes, not color values. | Fixed getChangeColor() to return distinct color sets per mode. Tests now assert hex values. |
| F5 | 🟢 Minor | **Shared hook (usePersistedState) broke existing test mocks.** All WatchlistPage tests needed settings API handler, but only new tests had it. | Added `{ value: false }` mock to 5 test blocks. Pattern: audit ALL existing tests when adding hooks. |

### Key Lesson: Bug-Fix TDD Protocol

The most impactful friction was the TDD bypass. When a user reports a bug, the natural instinct is to "just fix it." But TDD discipline requires:

1. Write a failing test that reproduces the bug exactly
2. Verify it fails for the right reason (M5)
3. Fix the production code
4. Verify the test passes

This is identical to feature TDD but the trigger is different — a defect report, not a spec.

### Proposed Emerging Standards

- **G18 — Shared Hook Mock Inventory:** When adding a shared hook to an existing component, `rg` all test files rendering that component and update their mocks.
- **G19 — Bug-Fix TDD Protocol:** Bug reports require Red→Green TDD. Write a test reproducing the bug before touching production code. Never skip to "just fix it."

## Metrics (Combined)

| Metric | Primary Session | Continuation | Total |
|--------|----------------|-------------|-------|
| Sub-MEUs | 3 | — (corrections) | 3 |
| New tests | 27 | 10 (5 bug-fix + 5 coverage) | 37 |
| Files changed | ~16 | ~4 | ~18 |
| Known issues resolved | 1 ([PLAN-NOSIZE]) | 1 ([TEST-SETTINGS-WARNING]) | 2 |
| Quality gate | 7/7 green | 82/82 vitest | All green |
| Codex findings | — | 3 High (resolved, 3 rounds) | 3 High |

## Rules Checked

| Rule | Primary | Continuation |
|------|---------|-------------|
| P0: Redirect-to-file pattern | ✅ | ✅ |
| TDD: Tests first | ✅ | ❌→✅ (corrected by user) |
| TDD: Never modify tests to pass | ✅ | ✅ |
| Anti-placeholder scan | ✅ | ✅ |
| Evidence-first completion | ✅ | ✅ |
| Known-issues update | ✅ | ✅ |
| MEU registry update | ✅ | N/A |
| Current-focus update | ✅ | ✅ |
| Handoff creation | ✅ | ✅ (updated) |
| No premature stop | ✅ | ✅ |
