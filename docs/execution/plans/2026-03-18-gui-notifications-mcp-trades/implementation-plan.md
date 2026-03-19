# GUI Notifications + MCP Status + Trades

> **Project slug**: `gui-notifications-mcp-trades`
> **MEUs**: MEU-49 → MEU-46 → MEU-47 (execution order)
> **Phase**: 6 — GUI (Electron + React)
> **Date**: 2026-03-18

Three Phase 6 GUI MEUs that build on the existing shell foundation (MEU-43/44/45 ✅). MEU-49 lays the notification infrastructure consumed by all subsequent GUI pages. MEU-46 adds the MCP Server Status panel and gates E2E Wave 0. MEU-47 builds the Trades page and gates E2E Wave 1.

---

## User Review Required

> [!IMPORTANT]
> **Notification categories diverge from spec.** The existing `useNotifications.tsx` uses categories `trade | system | data | schedule | error`, while `06a-gui-shell.md` specifies `success | info | warning | error | confirmation`. This plan aligns to the **spec categories** since they are the canonical contract and match `sonner`'s built-in toast types. The existing categories will be replaced — no consumer code uses them yet beyond the shell's own `NotificationProvider`.

> [!IMPORTANT]
> **E2E tests require a running Electron app + Python backend.** The pre-written tests in `ui/tests/e2e/` depend on `global-setup.ts` which spawns the full app. E2E Wave 0/1 gates require the tests to **pass against a running app** (canon: `06-gui.md` §E2E). During this project, unit tests provide the primary gate. Full E2E execution is gated on the Electron build pipeline being functional and will be attempted as part of verification — if the app cannot be built/started, this is documented as a blocking prerequisite for wave sign-off, not a waived requirement.

> [!WARNING]
> **AppPage build path mismatch.** `ui/tests/e2e/pages/AppPage.ts` references `build/main/index.js` but `electron-vite` outputs to `out/main/index.js`. This must be fixed before any E2E test execution. Added as a prerequisite task.

> [!IMPORTANT]
> **MEU-46 scope expanded.** `mode-gating.test.ts` (Wave 1) requires `SETTINGS.ROOT`, `SETTINGS.MCP_GUARD.LOCK_TOGGLE`, and `SETTINGS.MCP_GUARD.STATUS` elements in the Settings page. The current `SettingsLayout.tsx` is a stub. MEU-46 now includes a minimal MCP Guard controls section (lock toggle + status display) in the Settings page to satisfy these E2E dependencies.

---

## Project Scope

| # | MEU | Slug | Build Plan Ref | Description |
|---|-----|------|----------------|-------------|
| 1 | MEU-49 | `gui-notifications` | [06a §notify](../../../docs/build-plan/06a-gui-shell.md) | Notification system: 5 spec categories, suppression prefs via REST, error-always-show |
| 2 | MEU-46 | `gui-mcp-status` | [06f §6f.9](../../../docs/build-plan/06f-gui-settings.md) | MCP Server Status panel, IDE config gen, sidebar `data-testid` attrs, MCP Guard controls (lock/status), **E2E Wave 0** (5 tests) |
| 3 | MEU-47 | `gui-trades` | [06b](../../../docs/build-plan/06b-gui-trades.md) | Trades table (TanStack Table), detail panel, screenshot panel, journal form, **E2E Wave 1** (+7 = 12 tests) |

**Out of scope**: Trade Report expansion tabs (Excursion, Fees, Mistakes, Round-Trip, AI Review) — these are Phase 2.75 expansion MEUs.

---

## Spec Sufficiency Gate

### MEU-49: `gui-notifications`

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| 5 notification categories (success, info, warning, error, confirmation) | Spec | [06a §Notification Categories](../../../docs/build-plan/06a-gui-shell.md) | ✅ | Table with suppressibility rules |
| Error category locked (always shows) | Spec | [06a §Rules](../../../docs/build-plan/06a-gui-shell.md) | ✅ | "error toasts are hardcoded to always show" |
| Confirmation suppression → defaultAction executes | Spec | [06a §Rules](../../../docs/build-plan/06a-gui-shell.md) | ✅ | Default: cancel |
| Suppressed notifications logged to console | Spec | [06a §Rules](../../../docs/build-plan/06a-gui-shell.md) | ✅ | "info is never lost" |
| Preferences persisted via `PUT /api/v1/settings` | Spec | [06a §Rules](../../../docs/build-plan/06a-gui-shell.md) | ✅ | Using `notification.{category}.enabled` keys |
| Toast library: `sonner` | Spec | [06a §Implementation](../../../docs/build-plan/06a-gui-shell.md) | ✅ | `import { toast } from 'sonner'` |
| React hook: `useNotifications()` | Spec | [06a §Implementation](../../../docs/build-plan/06a-gui-shell.md) | ✅ | Full hook code provided |

### MEU-46: `gui-mcp-status`

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Read-only status panel layout | Spec | [06f §6f.9 wireframe](../../../docs/build-plan/06f-gui-settings.md) | ✅ | Backend, version, DB, guard, tools, uptime |
| Data sources: health, version, guard | Spec | [06f §6f.9 Data Sources](../../../docs/build-plan/06f-gui-settings.md) | ✅ | REST: `GET /health`, `GET /version`, `GET /mcp-guard/status` |
| Data sources: toolset count, uptime | Human-approved | [06f §6f.9 Data Sources](../../../docs/build-plan/06f-gui-settings.md) | ✅ | Spec cites `list_available_toolsets` and `zorivest_diagnose` (MCP tools only — no REST proxy exists). **Scope cut (Human-approved)**: Panel shows "N/A" for these two fields with tooltip; full implementation deferred to MEU-46a (`mcp-rest-proxy`). Canon updated — see `06f-gui-settings.md` §6f.9 Phase 6 partial implementation note. |
| IDE config JSON templates (Cursor, Claude Desktop, Windsurf) | Spec | [06f §6f.9 IDE Config](../../../docs/build-plan/06f-gui-settings.md) | ✅ | Template table provided |
| Copy-to-clipboard | Spec | [06f §6f.9 wireframe](../../../docs/build-plan/06f-gui-settings.md) | ✅ | `[📋 Copy to Clipboard]` button |
| Sidebar `data-testid` attributes for E2E Wave 0 | Spec | [06-gui.md §E2E](../../../docs/build-plan/06-gui.md) | ✅ | `nav-accounts`, `nav-trades`, `nav-planning`, `nav-scheduling`, `nav-settings` |
| MCP Guard controls (lock toggle + status) | Spec | [06f §MCP Guard](../../../docs/build-plan/06f-gui-settings.md) | ✅ | Required by `mode-gating.test.ts` — needs `data-testid`: `settings-page`, `mcp-guard-lock-toggle`, `mcp-guard-status` |
| E2E Wave 0 tests: `launch.test.ts` (3) + `mcp-tool.test.ts` (2) | Spec | [06-gui.md §Wave Table](../../../docs/build-plan/06-gui.md) | ✅ | Tests pre-written |

### MEU-47: `gui-trades`

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| TanStack Table with 9 columns | Spec | [06b §Column Definitions](../../../docs/build-plan/06b-gui-trades.md) | ✅ | Full column helper code provided |
| Trade detail panel (slide-out right) | Spec | [06b §Trade Detail](../../../docs/build-plan/06b-gui-trades.md) | ✅ | Wireframe + form fields table |
| Trade form fields (9 fields) | Spec | [06b §Trade Form Fields](../../../docs/build-plan/06b-gui-trades.md) | ✅ | Field table with types and notes |
| Screenshot panel (upload, paste, lightbox) | Spec | [06b §Screenshot Panel](../../../docs/build-plan/06b-gui-trades.md) | ✅ | Full component code provided |
| Trade journal form (ratings, emotional state, tags) | Spec | [06b §Trade Report](../../../docs/build-plan/06b-gui-trades.md) | ✅ | 8 form fields with types |
| E2E Wave 1: `trade-entry.test.ts` (5) + `mode-gating.test.ts` (2) | Spec | [06-gui.md §Wave Table](../../../docs/build-plan/06-gui.md) | ✅ | Tests pre-written. `mode-gating.test.ts` deps (Settings MCP Guard controls) satisfied by MEU-46 scope expansion. |
| `data-testid` for trades page | Local Canon | [test-ids.ts](../../../ui/tests/e2e/test-ids.ts) | ✅ | `TRADES.*` constants defined |

**Verdict**: All behaviors resolved. Toolset count and uptime scope cut tagged `Human-approved` — deferred to MEU-46a (`mcp-rest-proxy`). Canon already updated (`06f-gui-settings.md` §6f.9, `BUILD_PLAN.md` Phase 6 table).

---

## FIC — Feature Intent Contracts

### FIC-49: Notification System

| # | Acceptance Criterion | Source |
|---|---|---|
| AC-1 | `useNotifications()` hook exposes `notify(category, message)` with 5 categories: `success`, `info`, `warning`, `error`, `confirmation` | Spec |
| AC-2 | `error` category toast always displays regardless of suppression preferences | Spec |
| AC-3 | When `confirmation` is suppressed, the `defaultAction` (`cancel`) executes automatically | Spec |
| AC-4 | Suppressed notifications are logged to `console.log` with `[suppressed:{category}]` prefix | Spec |
| AC-5 | Notification preferences read from `GET /api/v1/settings` via TanStack Query (path: `/api/v1/settings`), using keys `notification.{category}.enabled` | Spec |
| AC-6 | `sonner` `Toaster` component renders positioned bottom-right with dark theme tokens | Spec |
| AC-7 | Unit tests verify: error always shows, category suppression works, console logging on suppress | Spec |

### FIC-46: MCP Server Status Panel

| # | Acceptance Criterion | Source |
|---|---|---|
| AC-1 | `McpServerStatusPanel` component renders: backend status, version, DB status, guard state. Tool count and uptime show "N/A" (MCP-only, no REST proxy yet). | Human-approved |
| AC-2 | "Refresh Status" button re-fetches all REST data sources on demand | Spec |
| AC-3 | IDE Configuration section generates correct JSON for Cursor, Claude Desktop, and Windsurf | Spec |
| AC-4 | "Copy to Clipboard" button copies the generated JSON using `navigator.clipboard.writeText()` | Spec |
| AC-5 | `NavRail` component has `data-testid` attributes: `nav-accounts`, `nav-trades`, `nav-planning`, `nav-scheduling`, `nav-settings` | Spec |
| AC-6 | `SettingsLayout` renders `data-testid="settings-page"` root, MCP Guard lock toggle (`mcp-guard-lock-toggle`), and status indicator (`mcp-guard-status`) via `GET/POST /api/v1/mcp-guard/*` endpoints | Spec |
| AC-7 | E2E Wave 0 tests (`launch.test.ts` × 3, `mcp-tool.test.ts` × 2) pass against running app | Spec |

### FIC-47: Trades Page

| # | Acceptance Criterion | Source |
|---|---|---|
| AC-1 | `TradesTable` renders TanStack Table with 9 columns: Time, Instrument, Action, Qty, Price, Account, Comm, P&L, 📷 | Spec |
| AC-2 | Column sorting (click header) and multi-column sort (Shift+click) work | Spec |
| AC-3 | Row selection opens `TradeDetailPanel` slide-out on the right | Spec |
| AC-4 | `TradeDetailPanel` contains editable form with 9 fields, Save/Delete/Cancel buttons | Spec |
| AC-5 | "+ New Trade" button opens empty `TradeDetailPanel` for creation | Spec |
| AC-6 | `ScreenshotPanel` supports file upload, drag-and-drop, and clipboard paste (Ctrl+V) | Spec |
| AC-7 | `TradeReportForm` with star ratings (1-5), emotional state dropdown, tags chip input, lessons textarea | Spec |
| AC-8 | Trade detail tabs: `[Info] [Journal] [Screenshots]` | Spec |
| AC-9 | All `TRADES.*` `data-testid` attributes from `test-ids.ts` are applied | Local Canon |
| AC-10 | E2E Wave 1 tests (`trade-entry.test.ts` × 5, `mode-gating.test.ts` × 2) pass against running app. `mode-gating.test.ts` deps (Settings MCP Guard controls) satisfied by MEU-46. | Spec |

---

## Proposed Changes

### MEU-49: Notification System

---

#### [MODIFY] [useNotifications.tsx](file:///p:/zorivest/ui/src/renderer/src/hooks/useNotifications.tsx)

Rewrite to align with spec categories. Replace existing `trade | system | data | schedule | error` categories with `success | info | warning | error | confirmation`. Add:
- Suppression preferences loaded from REST settings via TanStack Query (`GET /api/v1/settings`)
- `console.log` for suppressed notifications
- Confirmation suppression → `defaultAction` logic
- Proper `sonner` toast method mapping (`toast.success`, `toast.warning`, `toast.error`, `toast.message`)

#### [NEW] [useNotifications.test.tsx](file:///p:/zorivest/ui/src/renderer/src/hooks/__tests__/useNotifications.test.tsx)

Unit tests covering AC-1 through AC-7: category mapping, error always shows, suppression behavior, console logging.

---

### MEU-46: MCP Server Status Panel

---

#### [NEW] [McpServerStatusPanel.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/McpServerStatusPanel.tsx)

Read-only status panel with:
- Connection status section: backend (via `GET /health`), version (via `GET /version`), DB status (derived from health), guard state (via `GET /api/v1/mcp-guard/status`)
- Tool count and uptime fields show "N/A — requires MCP proxy" (deferred to MEU-46a)
- IDE Configuration section with tab-style selector (Cursor / Claude Desktop / Windsurf)
- JSON code block with generated config
- Copy to clipboard button
- Refresh Status button

#### [MODIFY] [NavRail.tsx](file:///p:/zorivest/ui/src/renderer/src/components/layout/NavRail.tsx)

Add `data-testid` attributes to all 5 nav items: `nav-accounts`, `nav-trades`, `nav-planning`, `nav-scheduling`, `nav-settings`.

#### [MODIFY] [SettingsLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/SettingsLayout.tsx)

Replace stub with full settings layout. Must include:
- `data-testid="settings-page"` on root element (required by E2E `mode-gating.test.ts`)
- MCP Server Status panel section
- MCP Guard controls section with:
  - Lock toggle (`data-testid="mcp-guard-lock-toggle"`) — calls `POST /api/v1/mcp-guard/lock` or `/unlock`
  - Status indicator (`data-testid="mcp-guard-status"`) — reads from `GET /api/v1/mcp-guard/status`, displays "Locked" or "Unlocked"

#### [NEW] [McpServerStatusPanel.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/__tests__/McpServerStatusPanel.test.tsx)

Unit tests: renders status fields, generates correct IDE JSON for each target, clipboard copy works.

---

### MEU-47: Trades Page

---

#### [MODIFY] [TradesLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradesLayout.tsx)

Replace placeholder with full trades page implementing list+detail split layout. Contains `TradesTable` on the left (~60%) and `TradeDetailPanel` on the right (~40%).

#### [NEW] [TradesTable.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradesTable.tsx)

TanStack Table with 9 column definitions from `06b-gui-trades.md`. Includes: sorting, column resizing, row selection, filter bar, pagination (50 rows/page via `?limit=&offset=`).

#### [NEW] [TradeDetailPanel.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradeDetailPanel.tsx)

Slide-out detail panel with tabs: `[Info] [Journal] [Screenshots]`. Info tab has the 9 trade form fields. React Hook Form + Zod validation.

#### [NEW] [ScreenshotPanel.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/ScreenshotPanel.tsx)

Thumbnail strip, file upload input, Ctrl+V paste via Electron clipboard API, lightbox viewer.

#### [NEW] [TradeReportForm.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradeReportForm.tsx)

Journal tab: star ratings (setup/execution quality), followed-plan select, emotional state dropdown, lessons textarea, tag chip input.

#### [NEW] [trades.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx)

Unit tests: table renders columns, detail panel opens on row click, form validates required fields, screenshot panel renders upload button.

---

### Build Plan Hub Update

---

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Update status column for MEU-49, MEU-46, MEU-47 from ⬜ to ✅ after execution completes.

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 0 | Prerequisite: Fix `AppPage.ts` build path | Opus | Modified `AppPage.ts` | `rg 'out/main/index.js' ui/tests/e2e/pages/AppPage.ts` finds match | ⬜ |
| 1 | MEU-49: Rewrite `useNotifications` with spec categories | Opus | Modified `useNotifications.tsx` | Unit tests pass | ⬜ |
| 1a | MEU-49: Normalize `usePersistedState` endpoint paths to `/api/v1/settings/{key}` | Opus | Modified `usePersistedState.ts` | `rg '/api/v1/settings' ui/src/renderer/src/hooks/usePersistedState.ts` | ⬜ |
| 2 | MEU-49: Unit tests for notification system | Opus | `useNotifications.test.tsx` | `npx vitest run src/renderer/src/hooks` | ⬜ |
| 3 | MEU-49: Handoff | Opus | `001-2026-03-18-gui-notifications-bp06as1.md` | Handoff file exists, FIC criteria addressed | ⬜ |
| 4 | MEU-46: Create `McpServerStatusPanel` (REST-only sources; tool count/uptime = N/A) | Opus | New component file | Vitest unit tests pass | ⬜ |
| 4a | ~~MEU-46: Update `06f-gui-settings.md` §6f.9 Data Sources~~ (pre-completed during planning corrections) | Opus | Modified `06f-gui-settings.md` | Canon notes toolset count/uptime deferred to MEU-46a REST proxy | ✅ |
| 5 | MEU-46: Add `data-testid` to `NavRail` | Opus | Modified `NavRail.tsx` | Grep for all 5 test IDs | ⬜ |
| 6 | MEU-46: Wire `SettingsLayout` with MCP Status panel + MCP Guard controls | Opus | Modified `SettingsLayout.tsx` | `rg 'settings-page.*mcp-guard-lock-toggle.*mcp-guard-status' -U` finds all 3 test IDs | ⬜ |
| 7 | MEU-46: Unit tests for MCP Status panel + Guard controls | Opus | `McpServerStatusPanel.test.tsx` | `npx vitest run src/renderer/src/features/settings` | ⬜ |
| 8 | MEU-46: E2E Wave 0 tests pass (green) | Opus | All 5 wave tests pass | `npx playwright test tests/e2e/launch.test.ts tests/e2e/mcp-tool.test.ts` — must exit 0 | ⬜ |
| 9 | MEU-46: Handoff | Opus | `002-2026-03-18-gui-mcp-status-bp06fs6f.9.md` | Handoff file exists | ⬜ |
| 10 | MEU-47: Create `TradesTable` with TanStack Table | Opus | New component file | Columns render, sorting works in tests | ⬜ |
| 11 | MEU-47: Create `TradeDetailPanel` with form | Opus | New component file | Form fields match spec | ⬜ |
| 12 | MEU-47: Create `ScreenshotPanel` | Opus | New component file | Upload/paste logic in tests | ⬜ |
| 13 | MEU-47: Create `TradeReportForm` | Opus | New component file | Star ratings, tags, emotional state in tests | ⬜ |
| 14 | MEU-47: Wire into `TradesLayout` with split layout | Opus | Modified `TradesLayout.tsx` | List+detail layout renders | ⬜ |
| 15 | MEU-47: Unit tests for trades components | Opus | `trades.test.tsx` | `npx vitest run src/renderer/src/features/trades` | ⬜ |
| 16 | MEU-47: E2E Wave 1 tests pass (green) | Opus | All 7 wave tests pass | `npx playwright test tests/e2e/trade-entry.test.ts tests/e2e/mode-gating.test.ts` — must exit 0 | ⬜ |
| 17 | MEU-47: Handoff | Opus | `003-2026-03-18-gui-trades-bp06bs1.md` | Handoff file exists | ⬜ |
| 18 | Post-MEU: Update `BUILD_PLAN.md` status | Opus | Modified hub file | Grep confirms ✅ for MEU-46/47/49 | ⬜ |
| 19 | Post-MEU: Update `meu-registry.md` | Opus | Modified registry | All 3 MEUs show ✅ | ⬜ |
| 20 | Post-MEU: Run full vitest suite | Opus | Green CI | `npx vitest run` | ⬜ |
| 21 | Post-MEU: Reflection file | Opus | `docs/execution/reflections/2026-03-18-gui-notifications-mcp-trades-reflection.md` | File exists | ⬜ |
| 22 | Post-MEU: Metrics table | Opus | Updated `docs/execution/metrics.md` | Row for this project | ⬜ |
| 23 | Post-MEU: Session state | Opus | Pomera note saved | Note ID returned | ⬜ |
| 24 | Post-MEU: Commit messages | Opus | Proposed messages | Presented to human | ⬜ |

---

## Verification Plan

### Automated Tests

**Unit tests (vitest)**:
```bash
# MEU-49: Notification system
npx vitest run src/renderer/src/hooks/__tests__/useNotifications.test.tsx

# MEU-46: MCP Status panel
npx vitest run src/renderer/src/features/settings/__tests__/McpServerStatusPanel.test.tsx

# MEU-47: Trades components
npx vitest run src/renderer/src/features/trades/__tests__/trades.test.tsx

# Full suite
npx vitest run
```

**TypeScript compilation**:
```bash
# Verify all source files compile (renderer tsconfig)
cd ui && npx tsc --noEmit
```

**E2E test execution** (Wave 0 + Wave 1):
```bash
# Wave 0 (requires running app — see AppPage prerequisite)
cd ui && npx playwright test tests/e2e/launch.test.ts tests/e2e/mcp-tool.test.ts

# Wave 1 (requires running app + Settings MCP Guard controls)
cd ui && npx playwright test tests/e2e/trade-entry.test.ts tests/e2e/mode-gating.test.ts
```

> **Note**: If the Electron app cannot be built/started, document the blocker in the handoff. The E2E gate is real (not waived), but blocked on build pipeline readiness.

### Manual Verification

1. **Notification toasts**: Start dev server (`npm run dev`), trigger notifications from different categories, verify error cannot be suppressed
2. **MCP Status panel**: Navigate to Settings page, verify status panel renders with connection info, test Copy to Clipboard for IDE configs
3. **Trades table**: Navigate to Trades, verify table renders with 9 columns, click a row to open detail panel, test "+ New Trade" flow

---

## Handoff Files

| MEU | Handoff Path |
|-----|-------------|
| MEU-49 | `.agent/context/handoffs/001-2026-03-18-gui-notifications-bp06as1.md` |
| MEU-46 | `.agent/context/handoffs/002-2026-03-18-gui-mcp-status-bp06fs6f.9.md` |
| MEU-47 | `.agent/context/handoffs/003-2026-03-18-gui-trades-bp06bs1.md` |
