# GUI Plans, Reports & Multi-Account — Implementation Plan

Build three GUI MEUs in a single project: multi-account badges/filtering (MEU-54), trade report API wiring (MEU-55), and the full planning + watchlist page (MEU-48).

## Project Scope

| Field | Value |
|-------|-------|
| **Slug** | `gui-plans-reports-multiaccnt` |
| **MEUs** | MEU-54, MEU-55, MEU-48 (execution order) |
| **Build-plan sections** | [06b §P1](../../build-plan/06b-gui-trades.md), [06c §16](../../build-plan/06c-gui-planning.md) |
| **In-scope** | Account badges + filter dropdown, TradeReport API wiring, TradePlan page, Watchlist page, Equity-only position calculator (Wave 4 gate) |
| **Out-of-scope** | Full multi-mode calculator (Futures/Options/Forex/Crypto — 06h §Modes), expansion tabs (MEU-120), market data GUI (MEU-65) |
| **E2E Wave 4** | Included — Equity-only MVP calculator satisfies `position-size.test.ts` (2 tests). Full 06h spec deferred per phasing note. |

## Spec Sufficiency

| MEU | Behavior | Source | Resolved? |
|-----|----------|--------|-----------|
| MEU-54 | Account type badges (IRA/Cash/Margin/Paper) | Spec: domain model `AccountType` enum (MEU-2 ✅) | ✅ |
| MEU-54 | Account filter dropdown in trades header | Spec: 06b §filter bar → "account dropdown" | ✅ |
| MEU-54 | Fetch accounts for dropdown | Local Canon: `GET /api/v1/accounts` (MEU-25 ✅) | ✅ |
| MEU-55 | Load existing report on Journal tab | Spec: 06b §Report → `GET /api/v1/trades/{exec_id}/report` | ✅ |
| MEU-55 | Save new / update report | Spec: 06b §Report → `POST`, `PUT` | ✅ |
| MEU-55 | Star rating 1-5 → letter grade A-F mapping | Spec: 06b §Report Form Fields (updated) — API stores `Literal["A","B","C","D","F"]` | ✅ Mapped: {5→A, 4→B, 3→C, 2→D, 1→F} |
| MEU-55 | `followed_plan` bool toggle | Spec: 06b §Report Form Fields (updated) — API: `bool` | ✅ |
| MEU-55 | `emotional_state` free string | Spec: 06b §Report Form Fields (updated) — API: `str`, suggested values | ✅ |
| MEU-48 | Trade plan list+detail layout | Spec: 06c full ASCII layout + field table | ✅ |
| MEU-48 | Conviction indicators (🟢🟡🔴⚪) | Spec: 06c §Plan List Card Fields | ✅ |
| MEU-48 | R:R ratio computation | Spec: 06c §Computed Displays | ✅ |
| MEU-48 | Plan form has 15 fields (spec 10 + API extras) | Local Canon: `plans.py` also has `entry_conditions`, `exit_conditions`, `timeframe`, `account_id`, `linked_trade_id` | ✅ Local Canon (approved API code) |
| MEU-48 | `PATCH /{plan_id}/status` for status transitions | Local Canon: `plans.py:181-201` | ✅ |
| MEU-48 | Status/Conviction filtering is client-side | Local Canon: `GET /trade-plans` only supports `limit`/`offset` — no filter params | ✅ Client-side filter |
| MEU-48 | Equity-only position calculator modal | Spec: 06h §Equity Mode + §Implementation phasing | ✅ |
| MEU-48 | Watchlist CRUD (list, items, add/remove) | Spec: 06c §Watchlist Page + REST endpoints | ✅ |
| MEU-48 | Trade Plan REST endpoints | Local Canon: MEU-66/67/68/69 ✅ | ✅ |

## Feature Intent Contracts

### FIC: MEU-54 — Multi-Account UI

| AC | Criterion | Source |
|----|-----------|--------|
| AC-1 | TradesTable account column shows `AccountType` badge (color-coded chip) next to truncated account ID | Spec (06b matrix item 19) |
| AC-2 | Trades header has account filter dropdown populated from `GET /api/v1/accounts` | Spec (06b §filter bar) |
| AC-3 | Selecting an account in the filter re-queries trades with `account_id` param | Spec + Local Canon (API supports `account_id` filter) |
| AC-4 | "All Accounts" option clears the filter | Spec |
| AC-5 | Account column shows ≥15 characters before truncation (G7 standard) | Emerging Standard G7 |

### FIC: MEU-55 — Report GUI (API Wiring)

| AC | Criterion | Source |
|----|-----------|--------|
| AC-1 | Switching to Journal tab fetches existing report via `GET /api/v1/trades/{exec_id}/report` | Spec (06b §Report REST) |
| AC-2 | If no report exists (404), form initializes with empty defaults | Spec |
| AC-3 | Save Journal calls `POST` (new) or `PUT` (existing) | Spec (06b §Report REST) |
| AC-4a | Star ratings 1-5 convert to A-F grades on save: {5→A, 4→B, 3→C, 2→D, 1→F} | Spec (06b §Report Form Fields, updated) |
| AC-4b | `followed_plan` sent as `bool` (toggle control) | Spec (06b §Report Form Fields, updated) |
| AC-4c | `emotional_state` sent as free string from dropdown | Spec (06b §Report Form Fields, updated) |
| AC-4d | `linked_plan_id` out of scope (removed from 06b spec) | Spec (06b §Report Form Fields, updated) |
| AC-5 | After save, status bar shows success message | Local Canon (existing TradesLayout pattern) |
| AC-6 | Report data survives tab switches (cached by TanStack Query) | Local Canon (existing data fetching pattern) |

### FIC: MEU-48 — GUI Plans

| AC | Criterion | Source |
|----|-----------|--------|
| AC-1 | Planning route (`/planning`) shows TradePlan + Watchlist tabs | Spec (06c) |
| AC-2 | Trade plan list shows conviction indicators (🟢HIGH/🟡MEDIUM/🔴LOW/⚪closed) | Spec (06c §Card Fields) |
| AC-3 | Plan detail form has all 15 fields with Zod validation (spec 10 + `entry_conditions`, `exit_conditions`, `timeframe`, `account_id`, `linked_trade_id`) | Spec + Local Canon (`plans.py:22-38`) |
| AC-4 | R:R ratio and risk/share compute live as entry/stop/target change | Spec (06c §Computed Displays) |
| AC-5 | Plan CRUD: Create, Read, Update, Delete via REST API | Spec (06c §REST Endpoints) |
| AC-5a | Status transitions use `PATCH /{plan_id}/status` endpoint (separate from PUT) | Local Canon (`plans.py:181-201`) |
| AC-6 | Client-side filter by Status and Conviction (API only supports `limit`/`offset`) | Local Canon |
| AC-7 | `linked_trade_id` shows as readonly field (populated via PATCH status→executed) | Local Canon (`plans.py:192-193`) |
| AC-8 | Watchlist page shows list+detail with item table | Spec (06c §Watchlist Page) |
| AC-9 | Watchlist items support inline add (ticker + notes) and delete | Spec (06c §Watchlist Item Fields) |
| AC-10 | Watchlist CRUD via REST API (7 endpoints) | Spec (06c §REST Endpoints) |
| AC-11 | Data refreshes on 5s interval (G5 standard) | Emerging Standard G5 |
| AC-12 | All interactive elements have `data-testid` attributes | Local Canon (existing pattern) |
| AC-13 | Equity-only position calculator modal opens from planning page | Spec (06h §Equity Mode + §Implementation phasing) |
| AC-14 | Calculator inputs: account size, risk %, entry price, stop price with `data-testid` attrs | Spec (06h §Common Input Fields) |
| AC-15 | Calculator outputs: shares, dollar risk, R:R ratio (Equity formula) | Spec (06h §Equity Mode outputs) |
| AC-16 | E2E Wave 4 tests (`position-size.test.ts` × 2) pass — computation + a11y audit | Spec (BUILD_PLAN.md L208) |

## Proposed Changes

### MEU-54 — Multi-Account UI

#### [MODIFY] [TradesTable.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradesTable.tsx)

- Add `AccountTypeBadge` inline component (color-coded chip for IRA/Cash/Margin/Paper)
- Update account column cell renderer to show badge + truncated ID (≥15 chars per G7)

#### [MODIFY] [TradesLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradesLayout.tsx)

- Add `useQuery` for `GET /api/v1/accounts` to fetch account list
- Add account filter dropdown to header bar
- Pass selected `account_id` filter to trades query params

---

### MEU-55 — Report GUI (API Wiring)

#### [MODIFY] [TradeReportForm.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradeReportForm.tsx)

- Replace local `useState` with TanStack `useQuery` for loading existing report
- Add `useMutation` for save (POST new / PUT existing)
- Star-to-grade mapping on save: `{5:'A', 4:'B', 3:'C', 2:'D', 1:'F'}` (reverse on load)
- Convert `followed_plan` to `bool` toggle (API: `followed_plan: bool`)
- Keep `emotional_state` as free-string dropdown (API accepts any string)
- Remove `linked_plan_id` (not in report API)
- Add loading/error states
- Call `useStatusBar` for save feedback

#### [MODIFY] [TradeDetailPanel.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradeDetailPanel.tsx)

- Pass `onReportSave` callback down or let TradeReportForm handle its own API calls
- Invalidate report query on save

---

### MEU-48 — GUI Plans

#### [NEW] [TradePlanPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx)

- List+detail split layout for trade plans
- Left pane: plan cards with conviction indicators (🟢🟡🔴⚪), ticker, direction, status
- Filter dropdowns (status, conviction)
- Plan detail form with all 15 fields + Zod validation (spec 10 + `entry_conditions`, `exit_conditions`, `timeframe`, `account_id`, `linked_trade_id`)
- Live R:R ratio and risk/share computation
- `linked_trade_id` as readonly (populated via `PATCH /{plan_id}/status` → executed)
- Status transitions via `PATCH /{plan_id}/status` (separate from PUT for field updates)
- Client-side status/conviction filtering (API only supports `limit`/`offset`)
- CRUD via `apiFetch` + TanStack Query
- `refetchInterval: 5_000` (G5)

#### [NEW] [WatchlistPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/WatchlistPage.tsx)

- List+detail split layout for watchlists
- Left pane: watchlist names with item counts
- Right pane: watchlist detail form + items table
- Inline add ticker (ticker + notes inputs)
- Item delete via `DELETE /api/v1/watchlists/{id}/items/{ticker}`
- Watchlist CRUD (create, update name/description, delete)

#### [NEW] [PositionCalculatorModal.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx)

- Equity-only MVP modal dialog (06h §Equity Mode)
- Inputs: account size, risk %, entry price, stop price (with `data-testid` attrs from `test-ids.ts` CALCULATOR constants)
- Outputs: shares (`floor(risk_1r / risk_per_share)`), dollar risk, R:R ratio, position value
- Warning for position > 100% of account
- Keyboard: `Ctrl+Shift+C` global shortcut, `Escape` close, `Enter` calculate
- Not included (deferred): Futures/Options/Forex/Crypto modes, scenario comparison, history, Copy-to-Plan

#### [MODIFY] [PlanningLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PlanningLayout.tsx)

- Replace stub with tabbed layout: "Trade Plans" | "Watchlists"
- Lazy-load TradePlanPage and WatchlistPage
- Include PositionCalculatorModal (triggered via button or `Ctrl+Shift+C`)

---

### Tests

#### [NEW] [planning.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx) ✅

- TradePlanPage component tests (list rendering, conviction indicators, form fields, R:R computation, CRUD)
- WatchlistPage component tests (list rendering, item add/remove, CRUD)
- PositionCalculatorModal tests (Equity computation, data-testid attrs, warning display)
- PlanningLayout tab switching

#### [MODIFY] [trades.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/__tests__/trades.test.tsx) ✅

- Added MEU-54 tests: account type badge rendering, account filter dropdown
- Added MEU-55 tests: TradeReportForm API wiring (load existing, save new, update)

---

### Post-MEU Deliverables

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Update MEU-48, MEU-54, MEU-55 status from ⬜ to ✅
- Add MEU-70 expansion scope (all Tier 1-3 items) to description
- Add forward-reference notes on MEU-65 and MEU-71 for unblocking Tier 3 items
- Validate no stale references from this project

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- Add MEU-48 row to Phase 6 section
- Add MEU-54, MEU-55 rows to P1 section

---

## MEU-48 Expansion Scope (Deferred to MEU-70)

> The following enhancements were identified during MEU-48 base implementation.
> They are scoped for execution during **MEU-70** (`gui-planning`), with dependencies noted.

### Tier 1 — Pure Frontend (existing APIs, execute during MEU-70)

#### [MODIFY] [TradePlanPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/TradePlanPage.tsx)

- **T2**: Wire calculator INTO New/Edit Trade Plan form — pre-fill `entry_price`, `stop_loss`, `target_price` from plan, write-back computed values
- **T3**: Account dropdown — `GET /api/v1/accounts`, render `<select>` with `name (account_type)`, same pattern as [TradesLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/trades/TradesLayout.tsx)
- **T4**: Link executed plan → trade picker — when `status=executed`, show trade dropdown from `GET /api/v1/trades?ticker=`, sets `linked_trade_id`
- **T6**: Strategy name combobox — derive distinct `strategy_name` values client-side from fetched plans, render as `<datalist>` or custom combobox, allow free text

#### [MODIFY] [PositionCalculatorModal.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx)

- **C2**: Copy-to-clipboard button on shares output — `navigator.clipboard.writeText()` with toast

#### [MODIFY] [WatchlistPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/WatchlistPage.tsx)

- **W3**: Better watchlist item display — replace "X items" badge with ticker list, prep layout for price columns

### Tier 2 — Backend Changes (no external dependency, execute during MEU-70)

#### [MODIFY] [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py)

- **T5**: Add `executed_at: Optional[datetime] = None` and `cancelled_at: Optional[datetime] = None` to `TradePlan`

#### [MODIFY] [plans.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/plans.py)

- **T5**: Add `executed_at`, `cancelled_at` to `PlanResponse`. In `PATCH /{plan_id}/status`: set timestamp when `status → executed` or `cancelled`

#### [MODIFY] [accounts.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/accounts.py)

- **C1**: Add `GET /accounts/{id}/balances` route (returns list or latest). `BalanceSnapshotRepository.list_for_account()` already exists. Optionally embed `latest_balance: Optional[float]` in `AccountResponse`.

#### SQLAlchemy model + migration

- Add `executed_at`, `cancelled_at` columns to `TradePlanModel`
- Alembic migration for new columns

### Tier 3 — Build During MEU-70, Functional After MEU-65

#### [NEW] [TickerAutocomplete.tsx](file:///p:/zorivest/ui/src/renderer/src/components/TickerAutocomplete.tsx)

- **Shared component** (C4/T1/W1): debounced input → `GET /api/v1/market-data/search?query=`, dropdown with symbol + company name
- Graceful fallback: "No market data provider configured" on 503
- Props: `onSelect(ticker, price?)`, `placeholder`, `value`
- Used in: Calculator, TradePlanPage ticker field, WatchlistPage add-ticker

#### [MODIFY] [PositionCalculatorModal.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx)

- **C3**: Ticker field + auto-fill entry price from `GET /api/v1/market-data/quote?ticker=`

#### [MODIFY] [WatchlistPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/WatchlistPage.tsx)

- **W2**: Price data columns per watchlist item — last price, change $, change %, volume. Rate-limit: stagger 200ms between fetches.

### Tier 4 — Requires Research (Before MEU-70 Execution)

- **W4**: Optimal watchlist visual design — columns, layout, interaction patterns
- Deep research prompts prepared for Gemini, ChatGPT, Claude (see artifact `implementation_plan.md` §Deep Research Prompts)
- Research output target: `_inspiration/_watchlist-visual-design-research/synthesis.md`

### Dependency Graph

```
MEU-65 (market-data-gui) ←── unblocks C3, C4, T1, W1, W2 (Tier 3)
MEU-71 (gui-accounts)    ←── unblocks C1 full UX (Tier 2)
No blocker               ←── Tier 1 (T2/T3/T4/T6/C2/W3) + Tier 2 backend (T5/C1)
```

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | MEU-54: Account type badge + filter | coder | `TradesTable.tsx`, `TradesLayout.tsx` | `vitest run` — badge, filter tests | `[x]` |
| 2 | MEU-54: Tests | tester | `trades.test.tsx` additions | `vitest run` — all pass | `[x]` |
| 3 | MEU-55: Wire TradeReportForm to API | coder | `TradeReportForm.tsx` | `vitest run` — report API tests | `[x]` |
| 4 | MEU-55: Tests | tester | `trades.test.tsx` additions | `vitest run` — all pass | `[x]` |
| 5 | MEU-48: TradePlanPage (15 fields + PATCH status) | coder | `TradePlanPage.tsx` | `vitest run` — plan CRUD, R:R, indicators | `[x]` |
| 6 | MEU-48: WatchlistPage | coder | `WatchlistPage.tsx` | `vitest run` — watchlist CRUD, item add/remove | `[x]` |
| 7 | MEU-48: PositionCalculatorModal (Equity MVP) | coder | `PositionCalculatorModal.tsx` | `vitest run` — calculator computation, testid | `[x]` |
| 8 | MEU-48: PlanningLayout tabs + calculator trigger | coder | `PlanningLayout.tsx` | `vitest run` — tab switching, modal open | `[x]` |
| 9 | MEU-48: Tests (27 new) | tester | `planning.test.tsx` | `vitest run` — 207 total, all pass | `[x]` |
| 10 | Type check | tester | N/A | `tsc --noEmit` — 0 errors | `[x]` |
| 11 | Full regression | tester | N/A | `vitest run` — 207 tests pass | `[x]` |
| 12 | Handoffs (3 files) | reviewer | `087-*.md`, `088-*.md`, `089-*.md` | `Get-ChildItem .agent/context/handoffs/08[789]-*.md` — count ≥ 3 | `[x]` |
| 13 | BUILD_PLAN.md update | coder | `BUILD_PLAN.md` | MEU-48/54/55 → ✅, total 85/179 | `[x]` |
| 14 | MEU registry update | coder | `BUILD_PLAN.md` | BUILD_PLAN.md serves as registry; updated directly | `[x]` |
| 15 | MEU-48 expansion scope documented | planner | `task.md`, `implementation-plan.md` | All Tier 1-4 items listed with dependencies | `[x]` |
| 16 | BUILD_PLAN.md MEU-70 forward-reference | coder | `BUILD_PLAN.md` | MEU-70 description has enhancement checklist | `[x]` |
| 17 | Deep research prompts (watchlist UX) | researcher | `implementation_plan.md` artifact | 3 prompts (Gemini, ChatGPT, Claude) present | `[x]` |
| 18 | Reflection | reviewer | `reflections/2026-03-24-*.md` | `Test-Path` — True | `[x]` |
| 19 | Metrics update | reviewer | `metrics.md` | `rg -c 'gui-plans-reports-multiaccnt'` — ≥ 1 | `[x]` |

## Verification Plan

### Automated Tests

All tests run via:
```bash
cd p:\zorivest\ui && npm test
```

**MEU-54 tests** (in `trades.test.tsx`) ✅:
- Account badge renders correct type chip for IRA/Cash/Paper/Margin
- Account filter dropdown populates from mock accounts
- Selecting account filter triggers re-query with `account_id` param
- Account column shows ≥15 chars (G7)

**MEU-55 tests** (in `trades.test.tsx`) ✅:
- TradeReportForm loads existing report from API on mount
- TradeReportForm shows empty defaults on 404
- Save calls POST for new report, PUT for existing
- Field names match API schema (setup_quality, execution_quality, etc.)

**MEU-48 tests** (in `planning.test.tsx`) ✅:
- TradePlanPage renders plan list with conviction indicators
- Plan detail form validates required fields
- R:R ratio computes correctly from entry/stop/target
- Plan CRUD: create, update, delete with mock API
- WatchlistPage renders watchlist list with item counts
- Watchlist item add/remove
- PositionCalculatorModal: Equity computation (100K × 2% / $5 = 400 shares)
- PositionCalculatorModal: all 6 `data-testid` attrs render
- PlanningLayout tab switching between Plans and Watchlists

### Full Regression ✅

```bash
cd p:\zorivest\ui && npx vitest run --reporter=verbose
```

180 tests pass (133 existing + 27 MEU-48 + 20 MEU-54/55).

## Handoff Files

| SEQ | File | MEU |
|-----|------+-----|
| 087 | `087-2026-03-20-multi-account-ui-bp06bs19.md` | MEU-54 |
| 088 | `088-2026-03-20-report-gui-bp06bs20.md` | MEU-55 |
| 089 | `089-2026-03-20-gui-plans-bp06cs16.md` | MEU-48 |
