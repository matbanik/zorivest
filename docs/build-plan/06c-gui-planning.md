# Phase 6c: GUI — Trade Planning & Watchlists

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the trade planning surface: a Trade Plan page for thesis-driven pre-trade research, a Watchlist page for monitoring tickers, and a Position Calculator form for risk sizing. All pages follow the **list+detail split layout** pattern (see [Notes Architecture](../_notes-architecture.md)).

---

## Trade Plan Page

> **Source**: [Domain Model Reference](domain-model-reference.md) `TradePlan` entity, [Input Index §5](input-index.md). Follows the list+detail split layout pattern from the [Notes Architecture](../_notes-architecture.md).

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Trade Plans                                          [+ New Plan]  🔍 Filter       │
├──────────────────────────────────┬───────────────────────────────────────────────────┤
│  PLAN LIST (left pane)           │  PLAN DETAIL (right pane)                        │
│  ┌────────────────────────────┐  │                                                  │
│  │ 🟢 SPY Pullback to VWAP   │◄─│─ selected                                       │
│  │    HIGH · Long · Active    │  │  ── Plan Info ─────────────────────────────      │
│  │                            │  │                                                  │
│  │ 🟡 AAPL Earnings Play     │  │  Ticker:       [ SPY             ]               │
│  │    MED · Long · Draft      │  │  Direction:    [ Long ▼ ]                        │
│  │                            │  │  Status:       [ Active ▼ ]                      │
│  │ 🔴 TSLA Short Thesis      │  │  Conviction:   [ HIGH ▼ ]                        │
│  │    LOW · Short · Active    │  │                                                  │
│  │                            │  │  ── Strategy ──────────────────────────────      │
│  │ ⚪ QQQ Range Breakout     │  │                                                  │
│  │    MED · Long · Completed  │  │  Strategy Name:  [ VWAP Pullback        ]       │
│  └────────────────────────────┘  │  Description:                                   │
│                                  │  ┌──────────────────────────────────────────┐   │
│  Filter by:                      │  │ Wait for SPY to pull back to VWAP       │   │
│  Status: [All ▼]                 │  │ after morning breakout. Enter on bounce  │   │
│  Conviction: [All ▼]             │  │ with confirmation from volume.           │   │
│                                  │  └──────────────────────────────────────────┘   │
│  Legend:                         │                                                  │
│  🟢 HIGH conviction             │  ── Entry / Exit Conditions ──────────────       │
│  🟡 MEDIUM conviction           │                                                  │
│  🔴 LOW conviction              │  Entry Price:  [ 615.00    ]                     │
│  ⚪ Completed/Cancelled         │  Stop Loss:    [ 610.00    ]  Risk: $5.00/sh     │
│                                  │  Target Price: [ 625.00    ]  R:R = 2.0:1       │
│                                  │                                                  │
│                                  │  ── Linked Trade ─────────────────────────       │
│                                  │  Linked: T001 (SPY BOT 100 @ 619.61)  [View →] │
│                                  │                                                  │
│                                  │  [Save]  [Delete]  [Cancel]                     │
│                                  │                                                  │
└──────────────────────────────────┴───────────────────────────────────────────────────┘
```

### Plan List Card Fields

Each item in the left pane shows:
- Conviction indicator (colored dot: 🟢 HIGH, 🟡 MEDIUM, 🔴 LOW, ⚪ closed)
- Ticker + plan title
- Direction (Long/Short) + Status badge

### Plan Detail Form Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `ticker` | `text` | user input | Instrument ticker symbol |
| `direction` | `select` | Long / Short | Trade direction |
| `status` | `select` | Draft / Active / Executed / Cancelled | Plan lifecycle |
| `conviction` | `select` | HIGH / MEDIUM / LOW | Confidence level |
| `strategy_name` | `text` | user input | Short name for the strategy |
| `strategy_description` | `textarea` | user input | Full thesis / rationale |
| `entry_price` | `number` | user input | Target entry price |
| `stop_loss` | `number` | user input | Risk management level |
| `target_price` | `number` | user input | Profit target |
| `linked_trade_id` | `readonly` | from executed trade | Auto-linked when plan status → Executed |

### Computed Displays

| Computed | Formula | Display |
|----------|---------|---------|
| Risk per share | `|entry_price - stop_loss|` | Shown next to Stop Loss |
| Reward:Risk ratio | `|target_price - entry_price| / |entry_price - stop_loss|` | Shown next to Target Price |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/trade-plans` | List all plans (with filters) |
| `POST` | `/api/v1/trade-plans` | Create new plan |
| `GET` | `/api/v1/trade-plans/{id}` | Get plan detail |
| `PUT` | `/api/v1/trade-plans/{id}` | Update plan |
| `DELETE` | `/api/v1/trade-plans/{id}` | Delete plan |

---

## Watchlist Page

> **Source**: [Domain Model Reference](domain-model-reference.md) `Watchlist` + `WatchlistItem`, [Input Index §6](input-index.md).

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Watchlists                                        [+ New Watchlist]                │
├──────────────────────────────────┬───────────────────────────────────────────────────┤
│  WATCHLIST LIST (left pane)      │  WATCHLIST DETAIL (right pane)                   │
│  ┌────────────────────────────┐  │                                                  │
│  │ 📋 Core Holdings (5)      │◄─│─ selected                                       │
│  │ 📋 Earnings Watch (3)     │  │  Name: [ Core Holdings          ]               │
│  │ 📋 Sector Rotation (8)    │  │  Description: [ Main portfolio tickers ]         │
│  └────────────────────────────┘  │                                                  │
│                                  │  ── Items ─────────────────────────────────      │
│                                  │                                                  │
│                                  │  ┌─────────┬──────────────────────┬──────────┐  │
│                                  │  │ Ticker  │ Notes                │ Actions  │  │
│                                  │  ├─────────┼──────────────────────┼──────────┤  │
│                                  │  │ SPY     │ Core S&P 500 ETF     │  [✏️] [🗑]│  │
│                                  │  │ QQQ     │ Nasdaq 100 ETF       │  [✏️] [🗑]│  │
│                                  │  │ AAPL    │ Earnings Apr 25      │  [✏️] [🗑]│  │
│                                  │  │ MSFT    │ Cloud growth play    │  [✏️] [🗑]│  │
│                                  │  │ NVDA    │ AI infrastructure    │  [✏️] [🗑]│  │
│                                  │  └─────────┴──────────────────────┴──────────┘  │
│                                  │                                                  │
│                                  │  [+ Add Ticker]    Ticker: [____] Notes: [____] │
│                                  │                                                  │
│                                  │  [Save]  [Delete Watchlist]                      │
│                                  │                                                  │
└──────────────────────────────────┴───────────────────────────────────────────────────┘
```

### Watchlist Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `name` | `text` | user input | Watchlist name |
| `description` | `text` | user input | Optional description |

### Watchlist Item Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `ticker` | `text` | user input | Instrument ticker |
| `notes` | `text` | user input | Per-ticker notes |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/watchlists` | List all watchlists |
| `POST` | `/api/v1/watchlists` | Create watchlist |
| `GET` | `/api/v1/watchlists/{id}` | Get watchlist with items |
| `PUT` | `/api/v1/watchlists/{id}` | Update watchlist name/description |
| `DELETE` | `/api/v1/watchlists/{id}` | Delete watchlist |
| `POST` | `/api/v1/watchlists/{id}/items` | Add item to watchlist |
| `DELETE` | `/api/v1/watchlists/{id}/items/{ticker}` | Remove item |

---

## Position Calculator

> Full specification moved to [06h-gui-calculator.md](06h-gui-calculator.md). The calculator opens as a modal dialog from the command palette (`Ctrl+Shift+C`) or from the Trade Plan detail view via **Copy to Plan** integration.

---

## Exit Criteria

- Trade Plan page displays plans with conviction indicators, filter by status/conviction
- Plan detail form saves all fields including strategy description and entry/exit conditions
- R:R ratio computes live as entry/stop/target values change
- Watchlist page supports CRUD for watchlists and their items

## Outputs

- React components: `TradePlanPage`, `PlanDetailPanel`, `WatchlistPage`, `WatchlistDetailPanel`
- Plan list with conviction-colored cards and status badges
- Watchlist item CRUD with inline add/edit/delete
- Position calculator accessible via cross-reference to [06h-gui-calculator.md](06h-gui-calculator.md)

