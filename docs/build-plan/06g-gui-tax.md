# Phase 6g: GUI — Tax Estimator

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 4](04-rest-api.md), P3 Tax Engine (items 36–68 in [Build Priority Matrix](build-priority-matrix.md)) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the tax estimator GUI surface spanning all seven domain model modules (A–G). Provides a Tax Dashboard for year-end summaries, a Lot Viewer for cost-basis management, a Wash Sale Monitor for chain visualization, a What-If Simulator for pre-trade tax impact, a Loss Harvesting Tool for tax-smart selling, and a Quarterly Payments Tracker for estimated tax obligations. All pages consume the Tax REST API endpoints defined in [build-priority-matrix](build-priority-matrix.md) item 61.

> ⚠️ **Disclaimer**: Every tax output screen must display: *"This is an estimator, not tax advice. Always consult a CPA."* — per [Domain Model Reference](domain-model-reference.md).

Tax Profile settings (filing status, bracket, cost basis method, section elections) are configured in [06f-gui-settings.md](06f-gui-settings.md) §Tax Profile Settings.

---

## Tax Dashboard

> **Source**: [Domain Model Reference](domain-model-reference.md) Module F (Reports & Dashboard). Primary landing page for the tax module.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Tax Estimator                                     Tax Year: [ 2026 ▼ ]  [⚙️ Profile]│
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ YTD Summary Cards ──────────────────────────────────────────────────────────┐   │
│  │                                                                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │   │
│  │  │ ST Gains     │  │ LT Gains     │  │ Wash Sale    │  │ Estimated Tax    │ │   │
│  │  │  $12,340     │  │  $8,560      │  │ Adjustments  │  │    $5,870        │ │   │
│  │  │  ▲ 14 trades │  │  ▲ 6 trades  │  │  -$2,100     │  │  @ 37% ST/15% LT│ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │   │
│  │                                                                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │   │
│  │  │ Loss Carry-  │  │ Harvestable  │  │ Tax Alpha    │                       │   │
│  │  │ forward      │  │ Losses       │  │ Savings YTD  │                       │   │
│  │  │  $3,000      │  │  $4,200      │  │  $1,390      │                       │   │
│  │  │  from 2025   │  │  5 positions │  │  lot optim.  │                       │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                       │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ YTD P&L by Symbol ──────────────────────────────────────────────────────────┐   │
│  │  ┌────────┬──────────┬──────────┬──────────┬──────────────────────────────┐  │   │
│  │  │ Ticker │ ST Gain  │ LT Gain  │ Total    │ ████████████████░░░░░ (bar)  │  │   │
│  │  ├────────┼──────────┼──────────┼──────────┼──────────────────────────────┤  │   │
│  │  │ SPY    │ $5,200   │ $3,100   │ $8,300   │ ██████████████████████       │  │   │
│  │  │ AAPL   │ $3,140   │ $2,460   │ $5,600   │ ██████████████               │  │   │
│  │  │ QQQ    │ $1,800   │ $1,500   │ $3,300   │ █████████                    │  │   │
│  │  │ TSLA   │ -$1,200  │ —        │ -$1,200  │ ▓▓▓▓ (red)                   │  │   │
│  │  └────────┴──────────┴──────────┴──────────┴──────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ Quick Actions ──────────────────────────────────────────────────────────────┐   │
│  │  [📊 View Tax Lots]  [🔍 Scan Harvesting]  [🧮 What-If Simulator]           │   │
│  │  [📅 Quarterly Payments]  [⚠️ Wash Sale Monitor]  [📋 Audit Check]          │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ⚠️ This is an estimator, not tax advice. Always consult a CPA.                    │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Summary Card Fields

| Card | Source | Computation |
|------|--------|-------------|
| ST Gains | `ytd_summary.st_gains` | Sum of short-term realized gains YTD |
| LT Gains | `ytd_summary.lt_gains` | Sum of long-term realized gains YTD |
| Wash Sale Adjustments | `ytd_summary.wash_sale_adjustments` | Net deferred loss from wash sales |
| Estimated Tax | `ytd_summary.estimated_tax_dollars` | ST gains × marginal rate + LT gains × LT rate |
| Loss Carryforward | `ytd_summary.capital_loss_carryforward` | Unused losses rolled from prior year |
| Harvestable Losses | `harvest_losses().total` | Unrealized losses available for harvesting |
| Tax Alpha Savings | `ytd_summary.tax_alpha` | Dollars saved via lot optimization + harvesting |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/tax/ytd-summary` | YTD tax position summary |
| `GET` | `/api/v1/tax/ytd-summary?group_by=symbol` | P&L breakdown by ticker |

---

## Tax Lot Viewer

> **Source**: [Domain Model Reference](domain-model-reference.md) Module A (Core Tax Engine). TanStack Table displaying all tax lots with cost basis management.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Tax Lots                    Cost Basis Method: [ FIFO ▼ ]   [ Apply to All ]       │
│                              Filter: [Open ▼]  Ticker: [____]  Account: [All ▼]     │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌───────┬────────┬────────┬──────────┬──────────┬──────┬───────┬────────┬────────┐ │
│  │Ticker │Open Dt │Close Dt│Qty       │Cost Basis│Procds│ Gain  │Days    │ST/LT   │ │
│  ├───────┼────────┼────────┼──────────┼──────────┼──────┼───────┼────────┼────────┤ │
│  │SPY    │01/15/26│—       │100       │$619.61   │—     │+$580  │31      │🕐 335d │ │
│  │SPY    │07/02/25│02/01/26│50        │$605.00   │$620  │+$750  │214     │✅ LT   │ │
│  │AAPL   │12/10/25│—       │200       │$198.30   │—     │-$340  │67      │🕐 299d │ │
│  │TSLA   │01/28/26│02/10/26│75        │$410.50   │$394  │-$1238 │13      │❌ ST   │ │
│  └───────┴────────┴────────┴──────────┴──────────┴──────┴───────┴────────┴────────┘ │
│                                                                                      │
│  Legend: 🕐 = days until LT threshold (≥ 366)  ✅ = qualifies as LT  ❌ = ST       │
│                                                                                      │
│  ── Lot Detail (on row click) ─────────────────────────────────────────────────      │
│                                                                                      │
│  Lot ID: L-SPY-20260115-001          Linked Trades: T001, T002                      │
│  Wash Sale Adj: $0.00                Account: DU123456 (Main Trading)               │
│  Original Basis: $619.61             Adjusted Basis: $619.61                         │
│                                                                                      │
│  [Close This Lot]  [Reassign Method]  [View Linked Trades →]                        │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Table Columns

| Column | Source | Notes |
|--------|--------|-------|
| Ticker | `tax_lot.ticker` | Sortable, filterable |
| Open Date | `tax_lot.open_date` | Date lot was created (purchase) |
| Close Date | `tax_lot.close_date` | Null = still open |
| Quantity | `tax_lot.quantity` | Shares/contracts |
| Cost Basis | `tax_lot.cost_basis` | Per-share, adjusted for wash sales |
| Proceeds | `tax_lot.proceeds` | Per-share, populated on close |
| Gain/Loss | `(proceeds - cost_basis) × quantity` | Color-coded green/red |
| Days | `tax_lot.holding_period_days` | Days held |
| ST/LT | `tax_lot.is_long_term` | Countdown to LT threshold for open lots |

### Actions

| Action | Description |
|--------|-------------|
| Close This Lot | Opens lot-closing dialog: select cost basis method, preview tax impact before confirming (Module C4) |
| Reassign Method | Post-trade lot reassignment within T+1 settlement (Module C5) |
| View Linked Trades | Navigate to trade detail in [06b-gui-trades.md](06b-gui-trades.md) |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/tax/lots` | List all lots (filterable: open/closed, ticker, account) |
| `GET` | `/api/v1/tax/lots/{lot_id}` | Lot detail with linked trades |
| `POST` | `/api/v1/tax/lots/{lot_id}/close` | Close a specific lot |
| `PUT` | `/api/v1/tax/lots/{lot_id}/reassign` | Reassign cost basis method (T+1 window) |

---

## Wash Sale Monitor

> **Source**: [Domain Model Reference](domain-model-reference.md) Module B (Wash Sale Engine). Visualizes active wash sale chains and proactive prevention alerts.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Wash Sale Monitor                                    [🔄 Scan Now]  [⚙️ Settings]  │
├──────────────────────────────┬───────────────────────────────────────────────────────┤
│  ACTIVE CHAINS (left pane)   │  CHAIN DETAIL (right pane)                           │
│  ┌────────────────────────┐  │                                                      │
│  │ ⚠️ SPY — $2,100 trapped│◄─│─ selected                                           │
│  │    3 events · Active    │  │  ── Chain: SPY ─────────────────────────────        │
│  │                         │  │                                                      │
│  │ ⚠️ AAPL — $450 trapped │  │  Original Loss:    $2,500                            │
│  │    2 events · Active    │  │  Deferred Amount:  $2,100                            │
│  │                         │  │  Status:           Active (not resolved)             │
│  │ ✅ QQQ — Resolved      │  │                                                      │
│  │    4 events · Closed    │  │  ── Chain Events ──────────────────────────          │
│  └────────────────────────┘  │                                                      │
│                              │  1. 01/15 SOLD 50 SPY @ loss → Disallowed ($2,500)   │
│  Summary:                    │  2. 01/20 BOT 50 SPY → Basis adjusted (+$2,500)      │
│  Active chains: 2            │  3. 02/01 SOLD 50 SPY @ loss → Partial release ($400)│
│  Total trapped: $2,550       │                                                      │
│  Cross-account: 1            │  ── Cross-Account Check ─────────────────────        │
│                              │  ⚠️ IRA account DU789 bought SPY on 01/18            │
│                              │     → Loss PERMANENTLY DESTROYED in IRA              │
│                              │                                                      │
│                              │  ── Prevention Alert ─────────────────────────       │
│                              │  🚫 Do NOT sell SPY at a loss until 02/19            │
│                              │     (30-day window from last purchase)                │
│                              │                                                      │
└──────────────────────────────┴───────────────────────────────────────────────────────┘
```

### Chain List Fields

| Field | Source | Notes |
|-------|--------|-------|
| Ticker | `wash_sale_chain.ticker` | Chain ticker |
| Trapped Amount | `wash_sale_chain.deferred_amount` | Loss currently deferred |
| Event Count | `wash_sale_chain.entries.length` | Number of chain events |
| Status | `wash_sale_chain.is_resolved` | Active or Resolved |

### Chain Detail Fields

| Field | Source | Notes |
|-------|--------|-------|
| Original Loss | `wash_sale_chain.original_loss` | Initial loss that triggered chain |
| Deferred Amount | `wash_sale_chain.deferred_amount` | Current trapped loss |
| Event Timeline | `wash_sale_chain.entries[]` | Chronological: disallowed → absorbed → released |
| Cross-Account Flag | aggregated from all accounts | Flags IRA/spouse purchases within 30-day window |
| Prevention Alert | computed from latest purchase | "Wait N days" or "Safe to sell" |

### Alert Types (Module B8 — Proactive)

| Alert | Trigger | Action |
|-------|---------|--------|
| Wash Sale Warning | Selling at a loss with purchase within 30 days | "Wait N days" or "This will trigger wash sale" |
| IRA Permanent Loss | Wash sale triggered by IRA account purchase | "Loss PERMANENTLY DESTROYED" |
| DRIP Conflict | Dividend reinvestment auto-purchase within window | "DRIP on [ticker] will disallow harvested loss" |
| Rebalance Conflict | Scheduled DCA/rebalance would trigger wash sale | "Upcoming rebalance on [date] conflicts" |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/tax/wash-sales` | List all wash sale chains |
| `GET` | `/api/v1/tax/wash-sales/{chain_id}` | Chain detail with events |
| `POST` | `/api/v1/tax/wash-sales/scan` | Trigger full wash sale scan |

---

## What-If Tax Simulator

> **Source**: [Domain Model Reference](domain-model-reference.md) Module C1 (Pre-Trade "What-If" Simulator). Allows users to preview tax impact before executing a trade.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  What-If Tax Simulator                                                               │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ── Scenario Input ──────────────────────────────────────────────────────────        │
│                                                                                      │
│  Ticker:    [ SPY        ]     Action:   [ SELL ▼ ]                                 │
│  Quantity:  [ 100        ]     Price:    [ 625.00  ]                                │
│  Account:   [ DU123456 ▼ ]     Method:   [ FIFO ▼  ]                               │
│                                                                                      │
│  [Simulate]                                                                          │
│                                                                                      │
│  ── Results ─────────────────────────────────────────────────────────────────        │
│                                                                                      │
│  Lots Closed:                                                                        │
│  ┌──────────┬──────────┬──────────┬────────┬──────────┬──────────────────┐          │
│  │ Lot ID   │ Qty      │ Basis    │ Procds │ Gain     │ Classification   │          │
│  ├──────────┼──────────┼──────────┼────────┼──────────┼──────────────────┤          │
│  │ L-001    │ 50       │ $619.61  │ $625   │ +$269.50 │ 🕐 ST (31 days) │          │
│  │ L-002    │ 50       │ $605.00  │ $625   │ +$1,000  │ ✅ LT (214 days)│          │
│  └──────────┴──────────┴──────────┴────────┴──────────┴──────────────────┘          │
│                                                                                      │
│  ┌─ Tax Impact Summary ──────────────────────────────────────────────────┐          │
│  │  Short-Term Gain:    $269.50   × 37%  =  $99.72                      │          │
│  │  Long-Term Gain:     $1,000.00 × 15%  =  $150.00                     │          │
│  │  Total Estimated Tax:                     $249.72                     │          │
│  │                                                                        │          │
│  │  ⏱️ Hold L-001 for 335 more days → save $74.83 (LT rate: $40.43)    │          │
│  │                                                                        │          │
│  │  ⚠️ Wash Sale Risk: None                                             │          │
│  └────────────────────────────────────────────────────────────────────────┘          │
│                                                                                      │
│  [Save Scenario]  [Compare Scenarios]                                               │
│                                                                                      │
│  ⚠️ This is an estimator, not tax advice. Always consult a CPA.                    │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Input Fields

| Field | Type | Notes |
|-------|------|-------|
| `ticker` | `text` | Instrument to simulate selling |
| `action` | `select` | SELL (default) |
| `quantity` | `number` | Number of shares to sell |
| `price` | `number` | Expected sale price |
| `account_id` | `select` | Account holding the lots |
| `cost_basis_method` | `select` | FIFO / LIFO / HIFO / Spec ID / Max LT Gain / Max LT Loss / Max ST Gain / Max ST Loss |

### Output Fields

| Output | Source | Notes |
|--------|--------|-------|
| Lots Closed | simulation result | Which lots would be closed under selected method |
| Per-lot Gain/Loss | `(price - lot.cost_basis) × lot.quantity` | Color-coded |
| ST vs LT Classification | `lot.is_long_term` | With days-held count |
| ST Tax Estimate | `st_gain × marginal_rate` | From TaxProfile |
| LT Tax Estimate | `lt_gain × lt_rate` | 0% / 15% / 20% based on bracket |
| Hold Savings Tip | Module C6 | "Wait N days → save $X" for lots near LT threshold |
| Wash Sale Risk | Module B8 | Flags if sale would trigger or conflict with existing chain |

### Scenario Comparison

Users can save multiple scenarios and compare side-by-side (e.g., "Sell 100 at FIFO" vs "Sell 100 at HIFO"):

| Scenario | Method | ST Tax | LT Tax | Total | Wash Risk |
|----------|--------|--------|--------|-------|-----------|
| A: FIFO  | FIFO   | $99.72 | $150   | $249  | None      |
| B: HIFO  | HIFO   | $0     | $180   | $180  | None      |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/tax/simulate` | Run what-if simulation |

---

## Loss Harvesting Tool

> **Source**: [Domain Model Reference](domain-model-reference.md) Module C2–C3 (Tax-Loss Harvesting Scanner + Replacement Suggestions).

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Tax-Loss Harvesting                           [🔍 Scan Portfolio]  Account: [All ▼] │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────┬──────────┬────────────┬──────────┬──────────────┬────────────────────┐ │
│  │ Ticker  │ Unreal.  │ Wash Risk  │ Days Held│ Replacement  │ Action             │ │
│  │         │ Loss     │            │          │              │                    │ │
│  ├─────────┼──────────┼────────────┼──────────┼──────────────┼────────────────────┤ │
│  │ TSLA    │ -$2,100  │ ✅ Safe    │ 45       │ TSLL, ARKK   │ [Simulate] [Sell]  │ │
│  │ AAPL    │ -$1,340  │ ⚠️ DRIP   │ 67       │ MSFT, QQQ    │ [Simulate] [Sell]  │ │
│  │ AMZN    │ -$760    │ ⚠️ 30-day │ 12       │ GOOG, META   │ [Simulate] [—]     │ │
│  │ VTI     │ -$320    │ ✅ Safe    │ 180      │ ITOT, SCHB   │ [Simulate] [Sell]  │ │
│  └─────────┴──────────┴────────────┴──────────┴──────────────┴────────────────────┘ │
│                                                                                      │
│  Total Harvestable (Safe):  $2,420                                                  │
│  Total Harvestable (All):   $4,520                                                  │
│  Estimated Tax Savings:     $895 (at 37% ST rate)                                   │
│                                                                                      │
│  Legend: ✅ Safe = no wash sale conflict  ⚠️ = potential conflict (hover for detail)│
│                                                                                      │
│  ⚠️ This is an estimator, not tax advice. Always consult a CPA.                    │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Table Columns

| Column | Source | Notes |
|--------|--------|-------|
| Ticker | open lot ticker | Grouped by ticker |
| Unrealized Loss | `current_price - cost_basis` × qty | Ranked by largest loss |
| Wash Risk | wash sale check | Safe / DRIP conflict / 30-day window / IRA conflict |
| Days Held | `lot.holding_period_days` | For ST vs LT awareness |
| Replacement | Module C3 suggestions | Correlated non-identical: VOO→IVV, QQQ→QQQM, SPY→SPLG |
| Actions | buttons | Simulate (opens What-If) or Sell (if safe) |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/tax/harvest` | Scan for harvestable losses |
| `POST` | `/api/v1/tax/simulate` | Preview tax impact of harvesting |

---

## Quarterly Payments Tracker

> **Source**: [Domain Model Reference](domain-model-reference.md) Module D (Quarterly Estimated Tax Payments).

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Quarterly Estimated Tax Payments                    Tax Year: [ 2026 ▼ ]           │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Method: [ Safe Harbor — 100% Prior Year ▼ ]    Prior Year Tax: $18,000             │
│                                                                                      │
│  ── Timeline ────────────────────────────────────────────────────────────────        │
│                                                                                      │
│  Q1 (Apr 15)          Q2 (Jun 15)         Q3 (Sep 15)        Q4 (Jan 15)            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Required:    │    │ Required:    │    │ Required:    │    │ Required:    │       │
│  │   $4,500     │    │   $4,500     │    │   $4,500     │    │   $4,500     │       │
│  │              │    │              │    │              │    │              │       │
│  │ Paid:        │    │ Paid:        │    │ Paid:        │    │ Paid:        │       │
│  │ ✅ $4,500    │    │ ✅ $5,000    │    │ ⏳ $0        │    │ — upcoming   │       │
│  │              │    │              │    │              │    │              │       │
│  │ Status: PAID │    │ Status: OVER │    │ Status: DUE  │    │ Status: —    │       │
│  │              │    │ (+$500)      │    │ Due in 14d   │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                                      │
│  ── Underpayment Penalty Preview ────────────────────────────────────────────        │
│                                                                                      │
│  Q3 shortfall: $4,500    Penalty rate: 8% annual    Est. penalty: $90               │
│  ⚠️ Pay by Sep 15 to avoid penalty accrual                                         │
│                                                                                      │
│  ── Payment Entry ───────────────────────────────────────────────────────────        │
│                                                                                      │
│  Quarter: [ Q3 ▼ ]    Amount: [ ________ ]    Date Paid: [ __________ ]             │
│  [Record Payment]                                                                    │
│                                                                                      │
│  ── Method Comparison ───────────────────────────────────────────────────────        │
│                                                                                      │
│  | Method               | Annual Required | Per Quarter | Status     |              │
│  |──────────────────────|────────────────|────────────|───────────|              │
│  | Safe Harbor 100%     | $18,000        | $4,500     | ✅ current |              │
│  | Safe Harbor 110%     | $19,800        | $4,950     |            |              │
│  | Current Year 90%     | $16,200        | $4,050     | ⬇️ lower   |              │
│  | Annualized           | varies         | varies     | 📊 complex |              │
│                                                                                      │
│  ⚠️ This is an estimator, not tax advice. Always consult a CPA.                    │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Quarter Card Fields

| Field | Source | Notes |
|-------|--------|-------|
| Required | `quarterly_estimate.required_payment` | Computed from selected method |
| Paid | `quarterly_estimate.actual_payment` | User-entered payment amount |
| Status | computed | PAID / OVER / DUE / UPCOMING |
| Due Date | `quarterly_estimate.due_date` | Apr 15, Jun 15, Sep 15, Jan 15 |
| Shortfall | `required - actual` | If positive, penalty may accrue |
| Penalty | `quarterly_estimate.underpayment_penalty_risk` | Federal rate + 3% annualized |

### Payment Entry Fields

| Field | Type | Notes |
|-------|------|-------|
| `quarter` | `select` | Q1 / Q2 / Q3 / Q4 |
| `amount` | `number` | Payment amount |
| `date_paid` | `date` | Date payment was made |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/tax/quarterly` | List all quarterly estimates |
| `POST` | `/api/v1/tax/quarterly` | Record a payment |
| `GET` | `/api/v1/tax/quarterly/compare` | Compare safe harbor methods |

---

## Transaction Audit

> **Source**: [Domain Model Reference](domain-model-reference.md) Module F4 (Error Check / Transaction Audit). Scans imported trades for data quality issues before tax calculations.

### Audit Checks

| Check | Severity | Description |
|-------|----------|-------------|
| Missing cost basis | 🔴 Error | Trade has no matching TaxLot open |
| Duplicate exec_id | 🔴 Error | Same execution ID appears multiple times |
| Impossible price | 🟡 Warning | Price deviates > 50% from ticker's range that day |
| Corporate action gap | 🟡 Warning | Stock split/merger not reflected in basis |
| Orphaned lot | 🟡 Warning | TaxLot with no matching trade |
| Missing account | 🔴 Error | Trade references non-existent account |

### REST Endpoint Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/tax/audit` | Run transaction audit scan |

---

## Exit Criteria

- Tax Dashboard displays all 7 summary cards with live data
- YTD P&L by Symbol table renders with per-ticker ST/LT breakdown
- Tax Lot Viewer shows open/closed lots with correct ST/LT classification and days-to-LT countdown
- Lot closing dialog previews tax impact before confirming
- Wash Sale Monitor displays active chains with event timelines
- Cross-account wash sale detection flags IRA permanent losses
- What-If Simulator shows per-lot breakdown, tax estimate at user's bracket, and hold-savings tips
- Scenario comparison renders side-by-side for different cost basis methods
- Loss Harvesting scanner ranks positions by harvestable amount and filters wash conflicts
- Replacement suggestions display correlated non-identical securities
- Quarterly Payments tracker shows 4-quarter timeline with payment entry
- Safe harbor method comparison table renders correctly
- Transaction Audit reports errors and warnings from imported trade data
- All screens display disclaimer: "This is an estimator, not tax advice."

## Outputs

- React components: `TaxDashboard`, `TaxLotViewer`, `LotDetailPanel`, `WashSaleMonitor`, `WashSaleChainDetail`, `WhatIfSimulator`, `ScenarioComparison`, `LossHarvestingTool`, `QuarterlyPaymentsTracker`, `TransactionAudit`
- Summary cards with live-updating values from Tax REST API
- TanStack Table for tax lots with sorting, filtering, grouping
- Wash sale chain visualization (event timeline)
- What-if scenario input form with per-lot result breakdown
- Quarterly payment entry with safe harbor comparison
- Disclaimer component shared across all tax screens
