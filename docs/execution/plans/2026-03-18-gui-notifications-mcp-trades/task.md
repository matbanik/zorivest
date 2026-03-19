# GUI Notifications + MCP Status + Trades — Task Checklist

## Prerequisites
- [x] Fix `AppPage.ts` build path (`build/main/index.js` → `out/main/index.js`)

## MEU-49: `gui-notifications`
- [x] Rewrite `useNotifications.tsx` — align categories to spec
- [x] Add suppression preferences via TanStack Query
- [x] Add confirmation→defaultAction logic
- [x] Add `console.log` for suppressed notifications
- [x] Normalize `usePersistedState.ts` endpoint paths
- [x] Write unit tests `useNotifications.test.tsx`
- [x] Create handoff `078-2026-03-18-gui-notifications-bp06as1.md`

## MEU-46: `gui-mcp-status`
- [x] Create `McpServerStatusPanel.tsx`
- [x] Add `data-testid` attributes to `NavRail.tsx` (5 nav items)
- [x] Wire `SettingsLayout.tsx` with MCP Status panel + MCP Guard controls
- [x] Write unit tests `McpServerStatusPanel.test.tsx`
- [x] E2E Wave 0: 2/3 pass (AxeBuilder pre-existing). Deferred to MEU-170
- [x] Create handoff `079-2026-03-18-gui-mcp-status-bp06fs6f.9.md`

## MEU-47: `gui-trades`
- [x] Create `TradesTable.tsx`, `TradeDetailPanel.tsx`, `ScreenshotPanel.tsx`, `TradeReportForm.tsx`
- [x] Wire into `TradesLayout.tsx` with list+detail split layout
- [x] Apply `TRADES.*` `data-testid` attributes from `test-ids.ts`
- [x] Write unit tests `trades.test.tsx`
- [x] E2E Wave 1: 3/7 pass (functional). Deferred to MEU-170
- [x] Create handoff `080-2026-03-18-gui-trades-bp06bs1.md`

## Infrastructure Fixes
- [x] AppPage splash→main window fix
- [x] CI build gate (`tsc --noEmit` + `npm run build`)
- [x] Electron runtime guard (Node.js detection)
- [x] E2E workflow/skill/strategy: build prereq + mock-contract docs
- [x] `06-gui.md`: stale path fix + MEU-170 notes
- [x] CI lint fix: 3 unused imports in `test_scheduling_service.py`

## Post-MEU Deliverables
- [x] Update `BUILD_PLAN.md` status (MEU-46/47/49 → ✅, Phase 6 → In Progress)
- [x] Run full vitest suite — 122/122
- [x] Create reflection file
- [x] Update metrics table
- [x] Save session state to pomera_notes (note 614)
- [x] All tasks complete — ready for commit
