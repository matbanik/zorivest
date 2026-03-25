# W4: Watchlist Visual Design Specification

> Synthesized from 3 research documents: [ChatGPT](file:///p:/zorivest/_inspiration/_watchlist-visual-design-research/chatgpt-Platform%20Feature%20Matrix.md), [Claude](file:///p:/zorivest/_inspiration/_watchlist-visual-design-research/claude-Watchlist%20design%20patterns%20that%20serve%20the%20traders%20brain.md), [Gemini](file:///p:/zorivest/_inspiration/_watchlist-visual-design-research/gemini-Trading%20Watchlist%20Design%20Research.md)

---

## 1. Column Hierarchy (Converged from 10-Platform Analysis)

All three sources agree on this priority order. The key insight from Claude's cognitive research: traders spend 80% of viewing time on the left half (F-pattern scanning), and change% has the **highest glance value** of any column.

### Default Columns (MVP)

| # | Column | Align | Glance Value | Source Consensus |
|---|--------|-------|-------------|-----------------|
| 1 | **Ticker** (frozen left) | Left | Anchor | Universal — all 10 platforms |
| 2 | **Last Price** | Right | Medium | Universal |
| 3 | **Change $** | Right | High | Universal (with ±prefix) |
| 4 | **Change %** | Right | **Highest** | Universal — instant sentiment via pre-attentive color |
| 5 | **Volume** | Right | High | Abbreviated: 1.2M, 45.3K |
| 6 | **Notes** indicator | Left | User-defined | Zorivest differentiator — tooltip on hover |

### Level 2 Additions

| Column | Value | Notes |
|--------|-------|-------|
| **Sparkline** (7-day) | Very High | 80×24px SVG, no axes — Tufte's "word-sized graphic" |
| **Day Range** (H/L) | Medium-high | Intraday momentum context |
| **Relative Volume** | High | Unusual volume (3-5× avg) signals investigation |

### Level 3 Additions (Optional/Scrollable)

52-week range, Market cap, Bid/Ask spread, P/E ratio

---

## 2. Visual Design Tokens

### Dark Palette (TradingView-aligned)

| Role | Hex | Usage |
|------|-----|-------|
| Background (primary) | `#131722` | Table background — deep blue-gray, less harsh than pure black |
| Background (elevated) | `#1E222D` | Cards, panels, sidebars |
| Background (header) | `#2A2E39` | Table header, toolbar |
| **Gain** (positive) | `#26A69A` | Muted teal-green — less fatiguing than Robinhood's neon |
| **Loss** (negative) | `#EF5350` | Warm red — slightly orange-tinted |
| Neutral (unchanged) | `#787B86` | TradingView gray midpoint |
| Text (primary) | `#D1D4DC` | High contrast, WCAG AA compliant |
| Text (secondary) | `#787B86` | Headers, labels |
| Text (muted) | `#4C525E` | Timestamps, tertiary |
| Selected row | `rgba(41,98,255,0.15)` | Blue tint overlay |
| Hover row | `rgba(255,255,255,0.05)` | Subtle highlight |
| Zebra stripe | `rgba(255,255,255,0.02)` | Near-invisible alternation |
| Border/divider | `#363A45` | 1px horizontal only — no vertical dividers |
| Accent | `#2962FF` | Buttons, links, focus states |

### Colorblind Mode (Toggle)

| Role | Default | Colorblind-safe |
|------|---------|----------------|
| Gain | `#26A69A` (teal) | `#2196F3` (blue) |
| Loss | `#EF5350` (red) | `#FF9800` (orange) |

> **Critical rule:** Never rely on color alone — always pair with **▲/▼ arrows** and **+/−** prefixes on change values (all 3 sources converge on this).

---

## 3. Typography

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
font-variant-numeric: tabular-nums lining-nums; /* NON-NEGOTIABLE for financial data */
font-synthesis: none;
```

| Element | Size | Weight | Align |
|---------|------|--------|-------|
| Ticker symbol | 13-14px | 600 (semibold) | Left |
| Last price | 13-14px | 500-600 | **Right** |
| Change % | 12-13px | 500 | **Right**, with ±prefix |
| Volume | 11-12px | 400 | Right, abbreviated |
| Column headers | 11px | 500, UPPERCASE | Match content |
| Notes | 12px | 400 | Left |

**Decimal rules:** US equities = 2 decimals (`189.42`). Pennies under $1 = 4 decimals. Change% always 2 decimals with explicit sign (`+2.34%`, `−0.87%`).

---

## 4. Layout Dimensions

| Property | Value | Rationale |
|----------|-------|-----------|
| Row height | **32px** | All 3 sources agree — fits 20+ visible rows |
| Cell padding (H) | 8px per side | Minimum for readability |
| Cell padding (V) | 4px top/bottom | Tight within 32px |
| Header border | 2px solid `#363A45` | Heavier than row dividers |
| Row dividers | 1px solid `#363A45` | Horizontal only |
| Sparkline | 80×24px | Fits within row height |

**Sticky header** — all sources note users lose column identity when headers scroll away.

---

## 5. Sparkline Spec

- **Stroke:** 1.5px line, no fill (optional 15% opacity gradient beneath)
- **Color:** Gain/loss color matching the row (green if current > open, red if below)
- **Reference line:** Optional dashed horizontal at previous close, 10% white opacity
- **End dot:** 3px circle at last data point
- **No axes, labels, or gridlines** — these are word-sized graphics, not charts
- **Render:** Lightweight SVG `<path>` or Canvas — never a full charting library
- **Libraries:** react-sparklines (SVG), or custom `<svg>` path from 7-day close array

---

## 6. Data Fetching Strategy (REST Polling Constraints)

### Architecture (from Gemini)

```
Visible-first loading via IntersectionObserver + TanStack Query:
- Only poll tickers visible in viewport (IntersectionObserver → useQuery.enabled)
- Stagger intervals: refetchInterval: 4000 + Math.random() * 1000
  (prevents "thundering herd" where all rows poll at same ms)
- Show cached data immediately, background-refresh silently
```

### Priority Queue (from Claude)

| Phase | Time | What |
|-------|------|------|
| Phase 1 | 0–4s | ~20 visible viewport rows |
| Phase 2 | 4–8s | Starred/recently-interacted tickers |
| Phase 3 | 8–10s | Background/off-screen tickers |

### Freshness Indicators

- **Global:** Dot in header — green (<10s), yellow (10–30s), red (>30s/interrupted)
- **Per-row:** Text opacity → 70% when not updated in 15+ seconds
- **Flash:** 200–400ms background transition on price update (gain/loss color at 20% opacity)
- **Startup:** Pre-warm from SQLite cache — show stale data instantly, refresh in background

### Batch Quote Endpoint (Future — MEU-65+)

```
GET /api/v1/market-data/quotes?tickers=AAPL,MSFT,TSLA,NVDA
```
Single request for all visible tickers instead of N separate calls. Until built, individual polling with stagger.

---

## 7. Interaction Patterns

| Priority | Pattern | Implementation | Level |
|----------|---------|---------------|-------|
| 1 | **Single-click row → select** | Highlight, update global state | MVP |
| 2 | **Column sorting** | Click header: asc → desc → original order (3-click cycle) | MVP |
| 3 | **Manual drag-and-drop order** | Preserved as "sacred" — sorts are temporary overlays | L2 |
| 4 | **Right-click context menu** | Open chart, Set alert, Remove symbol | L2 |
| 5 | **Spacebar-to-cycle** | Advance through watchlist, loading each chart | L3 |
| 6 | **Color-linked windows** | Click ticker → updates chart pane (Zustand global state) | L3 |
| 7 | **Inline cell editing** | Double-click ticker to replace | L3 |

---

## 8. Anti-Patterns to Avoid

From Claude's documented failures:

| Anti-Pattern | Lesson | Source |
|-------------|--------|--------|
| **Color-only gain/loss** | Excludes ~8% of male users | All 3 sources |
| **Sort instability** | Auto-resorting rows under cursor destroys trust | TradingView, IBKR |
| **Information overload as default** | ThinkorSwim "paralyzingly complex" — opt-in complexity | Claude, Gemini |
| **Modal notifications over actions** | ThinkorSwim popups block buy/sell buttons | Claude |
| **Gamification** | Robinhood: $77.5M in fines for confetti/casino design | Claude |
| **Misleading stale data** | Robinhood: user suicide from incorrect $730K balance display | Claude |
| **Neon colors on dark background** | Causes eye fatigue — use muted, desaturated variants | All 3 sources |

---

## 9. "Feel Professional" Checklist

Before shipping any version, verify (from Claude):

- [ ] Numbers right-aligned with consistent decimal places (2 for US equities)
- [ ] Thousands separators on volume, abbreviated for large (1.2M not 1200000)
- [ ] Change values include explicit **+** prefix for positive
- [ ] `font-variant-numeric: tabular-nums` — all digits same width
- [ ] No layout shift when values update (column widths stable)
- [ ] Row dividers horizontal only, subtle (1px, low opacity)
- [ ] Selected row uses muted blue highlight, not bold primary color
- [ ] Header text smaller, muted, UPPERCASE — subordinate to data
- [ ] Watchlist loads instantly on repeat launch (cached data, not blank screen)

---

## 10. Build Roadmap (Zorivest-Specific)

### Dependencies

- **W2 (price columns)** → needs quote API from MEU-65
- **Batch endpoint** → needs backend work post-MEU-65
- **WebSocket** → Level 4, separate infrastructure

### Level 1: Professional Visual Upgrade (~2 weeks)

> Prerequisite: W2/MEU-65 for price data

- Apply dark palette + typography tokens to existing WatchlistPage
- Add price columns: Last, Change $, Change %, Volume
- Right-align all numerics with tabular figures
- Gain/loss coloring with ▲/▼ arrows
- Frozen ticker column, sticky header
- 32px rows, zebra striping, hover highlights
- "Last updated Xs ago" timestamp

### Level 2: Contextual Awareness (+3 weeks)

- Sparklines (7-day SVG)
- Day range (High/Low)
- Sorting with 3-click cycle (asc → desc → original)
- Drag-and-drop reorder (dnd-kit)
- Freshness indicator (global dot + per-row opacity)
- IntersectionObserver visible-first polling
- Staggered refetch intervals

### Level 3: Power Trader (+4 weeks)

- Column customization (show/hide optional columns)
- Conditional formatting (user-defined color thresholds)
- Right-click context menu
- Keyboard navigation (spacebar cycle, arrow keys)
- Color-linked windows (Zustand global state)
- Desktop alert notifications
- CSV export, column persistence

### Level 4: Platform-Grade (Future)

- WebSocket streaming (replace REST polling)
- Chart linking (click ticker → chart updates)
- Multi-column stable sorting
- Custom scripted columns
- Trade execution integration
