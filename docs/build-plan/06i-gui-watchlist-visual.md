# Phase 6i: GUI — Watchlist Visual Redesign + Plan Size Field

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [MEU-65](06f-gui-settings.md) (market data GUI), [MEU-70](06c-gui-planning.md) (base planning GUI) | Source: [watchlist-design-spec](../../_inspiration/_watchlist-visual-design-research/watchlist-design-spec.md)

---

## Goal

Transform the existing `WatchlistPage.tsx` from a basic list+detail layout into a professional-grade financial data table with real-time quote columns, dark trading palette, tabular figures, and sparklines. Simultaneously close [PLAN-NOSIZE] by adding `position_size`/`shares_planned` fields to `TradePlan` across the full stack.

---

## Scope

### A. Watchlist Visual Redesign (W4)

> Source: [watchlist-design-spec.md](../../_inspiration/_watchlist-visual-design-research/watchlist-design-spec.md)

**Level 1 — Professional Visual Upgrade (this MEU):**

- Dark trading palette (TradingView-aligned `#131722` tokens)
- Price columns: Last, Change $, Change %, Volume
- Typography: Inter font, `font-variant-numeric: tabular-nums lining-nums`
- Right-aligned numerics with ±prefix and ▲/▼ arrows
- Gain color `#26A69A` / Loss color `#EF5350` (never color-only)
- Frozen ticker column, sticky header
- 32px rows, zebra striping, hover highlights
- "Last updated Xs ago" freshness timestamp
- Colorblind-safe toggle (blue/orange alternate palette)

**Level 2+ deferred to future MEUs.** See watchlist-design-spec.md §10 for the full 4-level roadmap (sparklines, sorting, drag-reorder, alerts, context menu, WebSocket streaming).

### B. [PLAN-NOSIZE] — TradePlan Position Size Field

> Source: [known-issues.md](../../.agent/context/known-issues.md) §PLAN-NOSIZE

Full-stack propagation of `position_size` and `shares_planned` fields:

> **Naming note (Human-Approved):** The repo standardized on `shares_planned` (not `shares`) during MEU-70b to avoid ambiguity with trading shares. All layers (entity, model, API, UI) already use `shares_planned`. No alias mapping is needed.

| Layer | File | Change |
|-------|------|--------|
| Domain entity | `entities.py` | Add `position_size: Optional[float]` (`shares_planned` already exists) |
| SQLAlchemy model | `models.py` | Add `Float` + `Integer` columns |
| DB migration | `ALTER TABLE` | Add nullable columns to `trade_plans` |
| API schemas | `plans.py` | Add to `CreatePlanRequest`, `UpdatePlanRequest`, `PlanResponse` |
| API serializer | `plans.py` | Add to `_to_response()` |
| MCP tools | `trade-planning` toolset | Add to plan input/output schemas |
| GUI form | `TradePlanPage.tsx` | Add readonly `position_size` display; `shares_planned` already editable (MEU-70b) |
| Calculator integration | `PositionCalculatorModal.tsx` | Write-back computed `shares_planned` + `position_size` to plan form |

---

## Dependencies

| Dependency | MEU | Required For |
|-----------|-----|-------------|
| Market Data GUI | MEU-65 ⬜ | Price columns (quote API must be configured) |
| Base Planning GUI | MEU-70 ⬜ | Existing watchlist page to enhance |

---

## Design Tokens

### Dark Palette

```css
--bg-primary: #131722;        /* Table background */
--bg-elevated: #1E222D;       /* Cards, panels */
--bg-header: #2A2E39;         /* Header, toolbar */
--color-gain: #26A69A;        /* Muted teal-green */
--color-loss: #EF5350;        /* Warm red */
--color-neutral: #787B86;     /* Unchanged */
--text-primary: #D1D4DC;      /* High contrast */
--text-secondary: #787B86;    /* Headers */
--text-muted: #4C525E;        /* Timestamps */
--row-selected: rgba(41,98,255,0.15);
--row-hover: rgba(255,255,255,0.05);
--row-stripe: rgba(255,255,255,0.02);
--border: #363A45;            /* 1px horizontal */
--accent: #2962FF;            /* Interactive */
```

### Colorblind-Safe Alternate

```css
--color-gain-cb: #2196F3;     /* Blue */
--color-loss-cb: #FF9800;     /* Orange */
```

### Typography

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
font-variant-numeric: tabular-nums lining-nums;
font-synthesis: none;
```

| Element | Size | Weight | Align |
|---------|------|--------|-------|
| Ticker | 13-14px | 600 | Left |
| Last price | 13-14px | 500-600 | Right |
| Change % | 12-13px | 500 | Right |
| Volume | 11-12px | 400 | Right |
| Headers | 11px | 500, UPPERCASE | Match content |

### Layout

| Property | Value |
|----------|-------|
| Row height | 32px |
| Cell padding (H) | 8px |
| Cell padding (V) | 4px |
| Header border | 2px solid `#363A45` |
| Row dividers | 1px solid `#363A45`, horizontal only |

---

## Column Hierarchy

| # | Column | Align | Notes |
|---|--------|-------|-------|
| 1 | **Ticker** (frozen) | Left | Semibold, anchor |
| 2 | **Last Price** | Right | 2 decimal places |
| 3 | **Change $** | Right | ±prefix, ▲/▼ arrow |
| 4 | **Change %** | Right | ±prefix, 2 decimals |
| 5 | **Volume** | Right | Abbreviated (1.2M) |
| 6 | **Notes** indicator | Left | Icon + tooltip |

---

## Data Fetching

- Individual `GET /api/v1/market-data/quote?ticker=X` per visible ticker
- TanStack Query with `refetchInterval: 5000` (existing pattern)
- Stagger intervals: `4000 + Math.random() * 1000` to prevent thundering herd
- Show cached data immediately, background refresh
- Staleness: reduce text opacity to 70% when data >15s old
- Global freshness indicator in watchlist header

---

## Files Changed

### Watchlist Redesign

| Action | File | Description |
|--------|------|-------------|
| MODIFY | `ui/src/renderer/src/features/planning/WatchlistPage.tsx` | Replace item list with professional data table |
| NEW | `ui/src/renderer/src/features/planning/WatchlistTable.tsx` | Data table component with price columns |
| NEW | `ui/src/renderer/src/styles/watchlist-tokens.css` | Design token CSS variables |
| MODIFY | `ui/src/renderer/src/features/planning/__tests__/planning.test.tsx` | Add tests for price column rendering, coloring, format |

### [PLAN-NOSIZE] Full Stack

| Action | File | Description |
|--------|------|-------------|
| MODIFY | `packages/core/src/zorivest_core/domain/entities.py` | Add `position_size` to `TradePlan` (`shares_planned` already exists) |
| MODIFY | `packages/infrastructure/src/zorivest_infra/database/models.py` | Add columns to `TradePlanModel` |
| MODIFY | `packages/api/src/zorivest_api/routes/plans.py` | Add to request/response schemas + `_to_response()` |
| MODIFY | `mcp-server/src/tools/trade-planning-tools.ts` | Add fields to plan tool schemas |
| MODIFY | `ui/src/renderer/src/features/planning/TradePlanPage.tsx` | Add readonly `position_size` display; `shares_planned` stays editable (MEU-70b) |
| MODIFY | `ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx` | Write-back `shares_planned` + `position_size` to plan form |

---

## Verification Plan

### Automated Tests

```bash
# Backend (position_size fields)
cd p:\zorivest && uv run python -m pytest tests/unit/test_api_plans.py -v

# Frontend (watchlist visual + plan size)
cd p:\zorivest\ui && npx vitest run src/renderer/src/features/planning/__tests__/planning.test.tsx

# Full UI regression
cd p:\zorivest\ui && npx vitest run --reporter=verbose

# Type check
cd p:\zorivest\ui && npx tsc --noEmit
```

### Visual Verification

- Browser subagent screenshot of watchlist with price columns
- Verify tabular numeral alignment (decimal points line up)
- Verify gain/loss coloring with ▲/▼ arrows
- Verify dark palette against design tokens

---

## Anti-Patterns to Avoid

Documented in [watchlist-design-spec.md](../../_inspiration/_watchlist-visual-design-research/watchlist-design-spec.md) §8:

- ❌ Color-only gain/loss (always pair with ▲/▼)
- ❌ Sort instability (temporary sorts never destroy manual order)
- ❌ Neon colors on dark background (use muted variants)
- ❌ Misleading stale data (always show freshness indicators)
- ❌ Layout shift when values update (tabular figures prevent this)
