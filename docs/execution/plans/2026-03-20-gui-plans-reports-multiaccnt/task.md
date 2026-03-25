# Task — GUI Plans, Reports & Multi-Account

## MEU-54: Multi-Account UI

- [x] Add `AccountTypeBadge` component to `TradesTable.tsx`
- [x] Update account column: badge + ≥15 char truncation (G7)
- [x] Add account filter dropdown to `TradesLayout.tsx`
- [x] Fetch accounts via `GET /api/v1/accounts` for dropdown
- [x] Pass `account_id` filter to trades query
- [x] Tests: badge rendering, filter dropdown, re-query on filter change
- [x] Handoff: `087-2026-03-20-multi-account-ui-bp06bs19.md`

## MEU-55: Report GUI (API Wiring)

- [x] Replace local state with `useQuery` for report loading
- [x] Add `useMutation` for POST (new) / PUT (existing) report
- [x] Star-to-grade mapping: `{5:'A', 4:'B', 3:'C', 2:'D', 1:'F'}` (and reverse on load)
- [x] Convert `followed_plan` from 3-state string to `bool` toggle (API: `bool`)
- [x] Keep `emotional_state` as free-string dropdown (matches API)
- [x] Remove `linked_plan_id` (not in report API schema)
- [x] Handle 404 (no existing report) → empty defaults
- [x] Add `useStatusBar` feedback on save
- [x] Tests: load existing, empty defaults on 404, save POST/PUT, star→grade mapping, bool toggle
- [x] Handoff: `088-2026-03-20-report-gui-bp06bs20.md`

## MEU-48: GUI Plans (Base — Completed)

- [x] Create `TradePlanPage.tsx` — list+detail split, conviction indicators, form, R:R
- [x] Create `WatchlistPage.tsx` — list+detail split, item table, inline add/delete
- [x] Create `PositionCalculatorModal.tsx` — Equity-only MVP (06h §Equity Mode)
  - [x] Inputs: account size, risk %, entry price, stop price (with CALCULATOR `data-testid` attrs)
  - [x] Outputs: shares, dollar risk, R:R ratio, position value
  - [x] Warning for position > 100% account
  - [x] `Ctrl+Shift+C` global shortcut, `Escape` close, `Enter` calculate
- [x] Update `PlanningLayout.tsx` — tabbed layout (Plans | Watchlists) + calculator trigger
- [x] Zod validation for plan form (15 fields: spec 10 + `entry_conditions`, `exit_conditions`, `timeframe`, `account_id`, `linked_trade_id`)
- [x] Live R:R ratio and risk/share computation
- [x] Client-side filter by Status + Conviction (API only supports `limit`/`offset`)
- [x] `linked_trade_id` as readonly (populated via `PATCH /{plan_id}/status` → executed)
- [x] Status transitions via `PATCH /{plan_id}/status` (separate from PUT)
- [x] `refetchInterval: 5_000` on all queries (G5)
- [x] `data-testid` on all interactive elements
- [x] Tests: plan CRUD, PATCH status, conviction indicators, R:R, watchlist CRUD, calculator computation, tab switching
- [x] E2E Wave 4: `position-size.test.ts` × 2 tests pass (computation + a11y)
- [x] Handoff: `089-2026-03-20-gui-plans-bp06cs16.md`

## MEU-48 Expansion + MEU-70 Scope (Deferred Items)

> These items are documented for execution during MEU-70 (`gui-planning`).
> Dependencies on MEU-65 and MEU-71 are noted per item.

### Tier 1 — Pure Frontend (existing APIs, no blockers)

- [x] **T2**: Wire calculator INTO Trade Plan form — pre-fill entry/stop/target via `zorivest:open-calculator` custom event (G11)
- [x] **T3**: Account dropdown on Trade Plan form — `GET /api/v1/accounts`, `<select>` with name (type)
- [x] **T4**: Link executed plan → trade picker — show trade selector `GET /api/v1/trades?ticker=` when status=executed, sets `linked_trade_id`
- [x] **T6**: Strategy name combobox — `<input list>` with `<datalist>` suggestions from distinct `strategy_name` values, allows free text
- [x] **C2**: Copy-to-clipboard button on shares output in calculator — `navigator.clipboard`, ✓ feedback
- [x] **W3**: Better watchlist item display — ticker list (up to 5 + overflow count) instead of "X items"

### Tier 2 — Needs Backend Change (no external dependency)

- [x] **T5**: Status timestamps — added `executed_at`/`cancelled_at` to entity, model, `PlanResponse`, `_to_response()`. `patch_plan_status` auto-sets timestamps on transitions.
- [ ] **C1**: Account balance auto-load for calculator — deferred (related to [PLAN-NOSIZE])

### Tier 3 — Build Now, Functional After MEU-65

- [x] **Shared**: Created `<TickerAutocomplete>` component — debounced 300ms → `GET /api/v1/market-data/search?query=`, dropdown with symbol + name, keyboard nav, click-outside-close
- [x] **C3**: Ticker → auto-fill entry price — fetches `GET /api/v1/market-data/quote?ticker=X`, populates entry price, loading indicator, graceful failure (MEU-65 complete)
- [x] **W2**: Watchlist price data columns — `watchlist-price-{ticker}` + `watchlist-change-{ticker}` per item, ▲/▼ with text-gain/text-loss (MEU-65 complete)

### Tier 4 — Research Complete ✅

- [x] **W4**: Watchlist visual design — research synthesized from ChatGPT, Claude, Gemini into [watchlist-design-spec.md](file:///C:/Users/Mat/.gemini/antigravity/brain/f3a68182-5214-4e02-97c3-526903b1975d/watchlist-design-spec.md)
- [x] Deep research prompts completed — column hierarchy, visual tokens, typography, sparklines, data fetching, interaction patterns, anti-patterns, 4-level build roadmap

## Post-MEU Deliverables

- [x] Run full regression: `cd p:\zorivest\ui && npx vitest run` — **207 tests pass (15 files)** (includes C3, W2, T4)
- [x] Run type check: `cd p:\zorivest\ui && npx tsc --noEmit` — 0 errors
- [x] Run backend plan tests: `uv run pytest tests/unit/test_api_plans.py` — 18 tests pass
- [x] Update `meu-registry.md` — add MEU-48 to Phase 6, MEU-54/55 to P1 section (resolved: registry is BUILD_PLAN.md, updated directly)
- [x] Update `BUILD_PLAN.md` — MEU-48/54/55 → ✅, progress counts updated (P0-Phase6=7/10, P1=4/4, Total=85/179)
- [x] Create reflection file: `docs/execution/reflections/2026-03-24-gui-plans-reports-multiaccnt-reflection.md`
- [x] Update metrics table: row added for MEU-48/54/55 session (2026-03-20–24)
- [x] Save session state to pomera_notes (note ID 679)
- [x] Prepare commit messages (see pomera_notes ID 679 output_content)
- [x] Create handoff files (087, 088, 089)
