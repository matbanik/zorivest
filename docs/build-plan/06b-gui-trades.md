# Phase 6b: GUI — Trades & Journal

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the trades page as the primary data surface — a full-featured TanStack Table with inline image badges, a slide-out detail panel for trade entry/editing, a screenshot panel for image management, and a trade report/journal form for post-trade analysis.

All pages follow the **list+detail split layout** pattern (see [Notes Architecture](../_notes-architecture.md) for the reference implementation).

---

## Trades Table (Full Layout)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Trades                                         [+ New Trade]  [Import]  🔍 Filter  │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐    │
│  │  TRADES TABLE (TanStack Table)                                               │    │
│  ├───────┬────────────┬────────┬───────┬──────────┬────────┬────────┬─────┬──────┤    │
│  │ Time  │ Instrument │ Action │  Qty  │  Price   │Account │ Comm   │ P&L │ 📷   │    │
│  ├───────┼────────────┼────────┼───────┼──────────┼────────┼────────┼─────┼──────┤    │
│  │ 14:32 │ SPY STK    │  BOT   │  100  │  619.61  │ DU123  │  1.02  │     │ 🖼×2 │◄── │
│  │ 14:35 │ AAPL STK   │  SLD   │   50  │  198.30  │ DU123  │  0.52  │+220 │      │    │
│  │ 15:01 │ QQQ STK    │  BOT   │  200  │  501.75  │ U456   │  2.04  │     │ 🖼×1 │    │
│  │ 15:44 │ TSLA OPT   │  SLD   │   10  │   12.50  │ DU123  │  6.50  │-180 │      │    │
│  └───────┴────────────┴────────┴───────┴──────────┴────────┴────────┴─────┴──────┘    │
│                                                                                      │
│  Columns:                                                                            │
│  • Time — sortable, formatted HH:MM (date in row group header when grouped by day)   │
│  • Instrument — ticker + asset class badge (STK/OPT/FUT)                             │
│  • Action — BOT (green) / SLD (red) color-coded                                     │
│  • Qty — right-aligned number                                                        │
│  • Price — right-aligned, 2 decimal places                                           │
│  • Account — truncated account_id with tooltip showing full name                     │
│  • Comm — commission, right-aligned                                                  │
│  • P&L — realized_pnl, green/red color-coded, empty if unrealized                   │
│  • 📷 — image badge: "🖼×N" if images attached, empty otherwise                     │
│                                                                                      │
│  Features:                                                                           │
│  • Column sorting (click header), multi-column sort (Shift+click)                    │
│  • Column resizing (drag header border)                                              │
│  • Row selection → opens detail panel on right                                       │
│  • Filter bar: date range, instrument search, account dropdown, action filter        │
│  • Pagination: 50 rows per page (server-side via ?limit=&offset=)                    │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### TanStack Table Column Definitions

```typescript
// ui/src/components/TradesTable.tsx

import { createColumnHelper } from '@tanstack/react-table';

interface Trade {
  exec_id: string;
  instrument: string;
  action: 'BOT' | 'SLD';
  quantity: number;
  price: number;
  account_id: string;
  commission: number;
  realized_pnl: number | null;
  notes: string | null;
  image_count: number;
  created_at: string;
}

const col = createColumnHelper<Trade>();

export const tradeColumns = [
  col.accessor('created_at', {
    header: 'Time',
    cell: info => new Date(info.getValue()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    sortingFn: 'datetime',
  }),
  col.accessor('instrument', {
    header: 'Instrument',
    cell: info => info.getValue(),
  }),
  col.accessor('action', {
    header: 'Action',
    cell: info => (
      <span className={info.getValue() === 'BOT' ? 'action-buy' : 'action-sell'}>
        {info.getValue()}
      </span>
    ),
  }),
  col.accessor('quantity', {
    header: 'Qty',
    cell: info => info.getValue().toLocaleString(),
    meta: { align: 'right' },
  }),
  col.accessor('price', {
    header: 'Price',
    cell: info => info.getValue().toFixed(2),
    meta: { align: 'right' },
  }),
  col.accessor('account_id', {
    header: 'Account',
    cell: info => <span title={info.getValue()}>{info.getValue().slice(0, 5)}…</span>,
  }),
  col.accessor('commission', {
    header: 'Comm',
    cell: info => info.getValue().toFixed(2),
    meta: { align: 'right' },
  }),
  col.accessor('realized_pnl', {
    header: 'P&L',
    cell: info => {
      const val = info.getValue();
      if (val === null) return '';
      return <span className={val >= 0 ? 'pnl-positive' : 'pnl-negative'}>{val >= 0 ? '+' : ''}{val.toFixed(0)}</span>;
    },
    meta: { align: 'right' },
  }),
  col.accessor('image_count', {
    header: '📷',
    cell: info => info.getValue() > 0 ? `🖼×${info.getValue()}` : '',
    enableSorting: false,
    size: 60,
  }),
];
```

---

## Trade Detail Panel (Slide-Out Right)

When a trade row is selected, a detail panel slides in from the right side of the split layout:

```
┌────────────────────────────────────┬─────────────────────────────────────────────┐
│  TRADES TABLE                      │  TRADE DETAIL                               │
│  (left pane, ~60% width)           │  (right pane, ~40% width)                   │
│                                    │                                             │
│  [table as above]                  │  exec_id: T001                              │
│                                    │  ────────────────────────────────────        │
│  ▸ SPY BOT 100 @ 619.61 ◄─selected│  Instrument: [SPY STK          ]            │
│    AAPL SLD 50 @ 198.30            │  Action:     [BOT ▼]  Qty: [100 ]           │
│    QQQ BOT 200 @ 501.75           │  Price:      [619.61 ]                       │
│    TSLA SLD 10 @ 12.50            │  Account:    [DU123456 ▼]                    │
│                                    │  Commission: [1.02    ]                      │
│                                    │  Realized P&L: [      ]                     │
│                                    │                                             │
│                                    │  Notes:                                     │
│                                    │  ┌─────────────────────────────────────┐    │
│                                    │  │ Entered on pullback to VWAP.        │    │
│                                    │  │ Target 625 based on prior high.     │    │
│                                    │  └─────────────────────────────────────┘    │
│                                    │                                             │
│                                    │  [Save]  [Delete]  [Cancel]                 │
│                                    │                                             │
│                                    │  ── Screenshots ────────────────────        │
│                                    │  [Screenshot Panel — see below]             │
│                                    │                                             │
└────────────────────────────────────┴─────────────────────────────────────────────┘
```

### Trade Form Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `exec_id` | `readonly` | auto-generated or imported | Primary key, not editable after creation |
| `instrument` | `text` | user input | Ticker + asset class (e.g. "SPY STK") |
| `action` | `select` | `BOT` / `SLD` | Color-coded in display |
| `quantity` | `number` | user input | Positive integer |
| `price` | `number` | user input | Execution price, 2 decimals |
| `account_id` | `select` | populated from `/api/v1/accounts` | Dropdown of user accounts |
| `commission` | `number` | user input | Default 0.00 |
| `realized_pnl` | `number` | user input or calculated | Optional, populated on closing trades |
| `notes` | `textarea` | user input | Free-text trade notes |

---

## Screenshot Panel (React + Electron)

> Migrated from original `06-gui.md`. Embedded within the Trade Detail Panel.

```
┌─────────────────────────────────────────────────────────────────┐
│  SCREENSHOT PANEL                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ thumb 1  │  │ thumb 2  │  │  + Add   │     [Delete] [View] │
│  │ 📷       │  │ 📷       │  │          │                     │
│  │ "Entry"  │  │ "Exit"   │  │          │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│  Caption: Entry screenshot SPY 2025-07-02                      │
└─────────────────────────────────────────────────────────────────┘
```

### Key React/Electron Components for Images

- **TanStack Table** with custom cell renderer for thumbnail badge column
- **CSS lightbox / react-medium-image-zoom** for full-size image viewing with zoom
- **HTML File Input + Drag/Drop** for screenshot import
- **Electron clipboard API** (`clipboard.readImage()`) for paste-from-clipboard (Ctrl+V)
- Image processing (thumbnail generation) remains in the Python backend via REST

```typescript
// ui/src/components/ScreenshotPanel.tsx

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

const API = (window as any).__ZORIVEST_API_URL__ ?? 'http://localhost:8765/api/v1';

interface TradeImage {
  id: number;
  caption: string;
  mime_type: string;
  file_size: number;
  thumbnail_url: string;
}

export function ScreenshotPanel({ tradeId }: { tradeId: string }) {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Fetch thumbnails for the selected trade
  const { data: images = [] } = useQuery<TradeImage[]>({
    queryKey: ['trade-images', tradeId],
    queryFn: () => fetch(`${API}/trades/${tradeId}/images`).then(r => r.json()),
  });

  // Upload via file input or drag-and-drop
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return fetch(`${API}/trades/${tradeId}/images`, {
        method: 'POST', body: formData,
      }).then(r => r.json());
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trade-images', tradeId] }),
  });

  // Paste from clipboard (Ctrl+V) — uses Electron clipboard API
  const handlePaste = async () => {
    const { clipboard, nativeImage } = window.electronAPI;
    const img = clipboard.readImage();
    if (!img.isEmpty()) {
      const blob = new Blob([img.toPNG()], { type: 'image/png' });  // Server standardizes to WebP
      uploadMutation.mutate(new File([blob], 'clipboard.png'));  // Backend converts on ingestion
    }
  };

  return (
    <div className="screenshot-panel">
      {/* Thumbnail strip */}
      <div className="thumbnail-strip">
        {images.map(img => (
          <div key={img.id} className="thumb" onClick={() => setSelectedId(img.id)}>
            <img src={`${API}/images/${img.id}/thumbnail`} alt={img.caption} />
            <span>{img.caption}</span>
          </div>
        ))}
        <label className="thumb add-btn">
          + Add
          <input type="file" hidden accept="image/*"
            onChange={e => e.target.files?.[0] && uploadMutation.mutate(e.target.files[0])} />
        </label>
      </div>

      {/* Full-size viewer (lightbox) */}
      {selectedId && (
        <div className="lightbox" onClick={() => setSelectedId(null)}>
          <img src={`${API}/images/${selectedId}/full`} alt="Full size" />
        </div>
      )}

      <button onClick={handlePaste}>📋 Paste (Ctrl+V)</button>
    </div>
  );
}
```

---

## Trade Report / Journal Form

When viewing a trade's detail panel, a "Journal" tab provides post-trade analysis fields. This is a separate React component rendered within the trade detail panel.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRADE DETAIL  ·  [Info]  [Journal]  [Screenshots]                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Trade: SPY BOT 100 @ 619.61 (T001)                                   │
│  ────────────────────────────────────────────────────────────           │
│                                                                         │
│  Setup Quality:     ⭐⭐⭐⭐☆  (4/5)                                  │
│  Execution Quality: ⭐⭐⭐☆☆  (3/5)                                  │
│                                                                         │
│  Followed Plan?     [Yes ▼]     Linked Plan: [SPY pullback →]          │
│                                                                         │
│  Emotional State:   [Confident ▼]                                      │
│  Options: Confident | Fearful | Greedy | Impulsive | Hesitant | Calm   │
│                                                                         │
│  Lessons Learned:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Entry was good — waited for confirmation. Should have sized    │   │
│  │ up given high conviction. Exit was premature, left 2R on the  │   │
│  │ table.                                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Tags:  [ entry-timing ] [ sizing ] [ + Add tag ]                      │
│                                                                         │
│  ── Screenshots ────────────────────────────────────────                │
│  [Screenshot Panel links to Screenshots tab]                            │
│                                                                         │
│  [Save Report]                                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Report Form Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `trade_id` | `readonly` | from selected trade | Links report to trade |
| `setup_quality` | `rating` (1–5 stars) | user input | Star rating component |
| `execution_quality` | `rating` (1–5 stars) | user input | Star rating component |
| `followed_plan` | `select` | Yes / No / Partially / N/A | Links to TradePlan if Yes |
| `linked_plan_id` | `select` | populated from `/api/v1/plans` | Optional — shows only if followed_plan != N/A |
| `emotional_state` | `select` | predefined enum | Confident, Fearful, Greedy, Impulsive, Hesitant, Calm |
| `lessons_learned` | `textarea` | user input | Free-text journaling |
| `tags` | `tag-input` | user input | Chip-style tag input with autocomplete from existing tags |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/trades/{exec_id}/report` | Create trade report |
| `GET` | `/api/v1/trades/{exec_id}/report` | Get report for trade |
| `PUT` | `/api/v1/trades/{exec_id}/report` | Update trade report |

---

## Build Plan Expansion: Trade Detail Tabs

> Source: [Build Plan Expansion Ideas](../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §3, §7–§12, §17

The existing Trade Detail Panel tabs (`[Info] [Journal] [Screenshots]`) are extended with new tabs from the expansion features:

```
TRADE DETAIL · [Info] [Journal] [Screenshots] [Excursion] [Fees] [Mistakes] [Round-Trip] [AI Review]
```

### Excursion Tab (§7 — MFE/MAE/BSO)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Excursion Metrics — SPY BOT 100 @ 619.61                              │
│  ────────────────────────────────────────────────────────────           │
│                                                                         │
│  MFE (Max Favorable Excursion):  +$2.41  (+0.39%)                      │
│  MAE (Max Adverse Excursion):    -$0.85  (-0.14%)                      │
│  BSO (Best Scale Out %):         62.3%                                 │
│                                                                         │
│  Data source: Alpha Vantage  ·  Computed: Jan 15, 2025 14:45           │
│                                                                         │
│  Trade efficiency:  You captured 62% of the available move.             │
│  ─── Excursion Chart ────────────────────────────────────               │
│  [Lightweight Charts mini-chart showing price path with                 │
│   MFE marker (green ▲) and MAE marker (red ▼)]                         │
│                                                                         │
│  [Recalculate]   — re-fetches bar data and recalculates                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mistakes Tab (§17)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Mistakes — SPY BOT 100 @ 619.61                                       │
│  ────────────────────────────────────────────────────────────           │
│                                                                         │
│  Category:       [ Early Exit ▼ ]    ← MistakeCategory enum            │
│  Options: Early Exit | Late Exit | Oversized | No Stop | Revenge       │
│           FOMO Entry | Ignored Plan | Overtrading | Chasing | Other    │
│                                                                         │
│  Estimated Cost:  [$120.00    ]     ← what the mistake cost             │
│  Notes:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Exited at $621.50 when target was $625. Left ~$350 on          │   │
│  │ the table. Fear of reversal after prior loss.                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Auto-detected:  ☐                  ← checked if rule-classified       │
│                                                                         │
│  [Save Mistake]                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Fee Breakdown Tab (§9)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Fee Breakdown — SPY BOT 100 @ 619.61                                  │
│  ────────────────────────────────────────────────────────────           │
│                                                                         │
│  ┌──────────────────┬──────────┬────────────────────┐                  │
│  │ Fee Type         │ Amount   │ Description         │                  │
│  ├──────────────────┼──────────┼────────────────────┤                  │
│  │ Commission       │ $1.00    │ IBKR tiered         │                  │
│  │ Exchange         │ $0.01    │ NYSE transaction fee │                  │
│  │ Regulatory       │ $0.01    │ SEC fee              │                  │
│  │ ECN              │ —        │                      │                  │
│  ├──────────────────┼──────────┼────────────────────┤                  │
│  │ **Total**        │ **$1.02**│                      │                  │
│  └──────────────────┴──────────┴────────────────────┘                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Execution Quality Badge (§10) — Inline in Info Tab

> Displayed as a badge next to the trade header in the Info tab. Shows A–F grade if NBBO data is available, or "N/A — No NBBO data" if not.

### Round-Trip Viewer (§3) — Sub-Panel

> When viewing a trade that is part of a round-trip, a collapsible section shows related executions, aggregate P&L, and holding period.

### Options Strategy Detector (§8) — Inline Notice

> If a trade is identified as part of a multi-leg options strategy, a badge shows the detected strategy type (e.g., "🦋 Iron Condor") and links to the strategy detail view.

### AI Review Tab (§12) — Opt-In

> Multi-persona AI trade review with budget cap. Requires explicit opt-in. Shows personas (Risk Manager, Trend Analyst, Contrarian) with formatted feedback.

### New React Components

| Component | Source §§ | Description |
|-----------|----------|-------------|
| `ExcursionPanel` | §7 | MFE/MAE/BSO metrics + mini-chart |
| `MistakeForm` | §17 | Mistake category selector + cost attribution |
| `FeeBreakdownTable` | §9 | Per-trade fee decomposition table |
| `RoundTripDetail` | §3 | Collapsible round-trip aggregate view |
| `ExecutionQualityBadge` | §10 | A–F grade badge (conditional on NBBO data) |
| `OptionsStrategyBadge` | §8 | Strategy type badge for multi-leg trades |
| `AIReviewPanel` | §12 | Multi-persona AI review results display |

---

## Exit Criteria

- Trades table displays all domain columns with sorting and filtering
- Trade detail panel opens on row selection with editable form
- New trade creation via "+ New Trade" button works end-to-end
- Screenshot panel supports upload, paste, and lightbox viewing
- Trade report/journal form saves with star ratings, tags, and lessons
- Image badge column shows correct count per trade

## Outputs

- React components: `TradesTable`, `TradeDetailPanel`, `ScreenshotPanel`, `TradeReportForm`
- TanStack Table column definitions with custom cell renderers
- Trade CRUD forms consuming [Phase 4](04-rest-api.md) REST endpoints
- Trade Report form consuming report REST endpoints

### Build Plan Expansion Components

- `ExcursionPanel` — MFE/MAE/BSO metrics with mini-chart (§7)
- `MistakeForm` — mistake category + cost attribution (§17)
- `FeeBreakdownTable` — per-trade fee decomposition (§9)
- `RoundTripDetail` — collapsible round-trip viewer (§3)
- `ExecutionQualityBadge` — A–F execution grade (§10)
- `OptionsStrategyBadge` — multi-leg strategy badge (§8)
- `AIReviewPanel` — multi-persona AI review (§12, opt-in)
- `ExpectancyDashboard` — win rate, avg win/loss, expectancy per trade, Kelly % (§13)
- `MonthlyPnLCalendar` — calendar heatmap of daily P&L with color coding (§20)
- `StrategyBreakdownPanel` — P&L breakdown by strategy_name with totals (§21)

