# GUI Notifications + MCP Status + Trades — Task Checklist

## Prerequisites
- [x] Fix `AppPage.ts` build path (`build/main/index.js` → `out/main/index.js`)

## MEU-49: `gui-notifications`
- [x] Rewrite `useNotifications.tsx` — align categories to spec (`success | info | warning | error | confirmation`)
- [x] Add suppression preferences via TanStack Query (`GET /api/v1/settings`)
- [x] Add confirmation→defaultAction logic
- [x] Add `console.log` for suppressed notifications
- [x] Normalize `usePersistedState.ts` endpoint paths (`/api/settings/{key}` → `/api/v1/settings/{key}`)
- [x] Write unit tests `useNotifications.test.tsx`
- [x] Create handoff `078-2026-03-18-gui-notifications-bp06as1.md`

## MEU-46: `gui-mcp-status`
- [x] Create `McpServerStatusPanel.tsx` (REST-only: health, version, guard; tool count/uptime = N/A, deferred to MEU-46a)
- [x] ~~Update `06f-gui-settings.md` §6f.9 Data Sources~~ (pre-completed during planning corrections)
- [x] Add `data-testid` attributes to `NavRail.tsx` (5 nav items)
- [x] Wire `SettingsLayout.tsx` with MCP Status panel + MCP Guard controls
  - [x] `data-testid="settings-page"` on root
  - [x] MCP Guard lock toggle (`data-testid="mcp-guard-lock-toggle"`) via `POST /api/v1/mcp-guard/lock|unlock`
  - [x] MCP Guard status indicator (`data-testid="mcp-guard-status"`) via `GET /api/v1/mcp-guard/status`
- [x] Write unit tests `McpServerStatusPanel.test.tsx`
- [ ] E2E Wave 0 tests pass (green): `npx playwright test tests/e2e/launch.test.ts tests/e2e/mcp-tool.test.ts` — must exit 0
- [x] Create handoff `079-2026-03-18-gui-mcp-status-bp06fs6f.9.md`

## MEU-47: `gui-trades`
- [x] Create `TradesTable.tsx` (TanStack Table, 9 columns)
- [x] Create `TradeDetailPanel.tsx` (slide-out, 3 tabs, form with 9 fields)
- [x] Create `ScreenshotPanel.tsx` (upload, paste, lightbox)
- [x] Create `TradeReportForm.tsx` (star ratings, emotional state, tags)
- [x] Wire into `TradesLayout.tsx` with list+detail split layout
- [x] Apply `TRADES.*` `data-testid` attributes from `test-ids.ts`
- [x] Write unit tests `trades.test.tsx`
- [ ] E2E Wave 1 tests pass (green): `npx playwright test tests/e2e/trade-entry.test.ts tests/e2e/mode-gating.test.ts` — must exit 0
- [x] Create handoff `080-2026-03-18-gui-trades-bp06bs1.md`

## Post-MEU Deliverables
- [ ] Update `BUILD_PLAN.md` status column (MEU-46/47/49 → ✅)
- [ ] Update `meu-registry.md` (all 3 MEUs → ✅)
- [ ] Run full vitest suite (`npx vitest run`)
- [ ] Create reflection file
- [ ] Update metrics table
- [ ] Save session state to pomera_notes
- [ ] Prepare commit messages
