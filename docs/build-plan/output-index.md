# Output Index — Complete Computed Output Catalog

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Companion: [Input Index](input-index.md) · [GUI Actions Index](gui-actions-index.md)

Canonical registry of **every computed or derived output** the system produces — calculation results, summary aggregations, classification flags, and warning messages. Each row links to the computation formula and source endpoint.

---

## Legend

| Column | Meaning |
|--------|---------|
| **Type** | Currency ($) · Percentage (%) · Ratio (N:1) · Integer (#) · Decimal (\#.\#) · Enum · Text · Boolean |
| **Surface** | 🖥️ GUI (displayed in UI) · 🤖 MCP (returned in tool response) · 🔌 API (in REST response body) |
| **Source** | REST endpoint or computation context that produces this output |
| **Status** | ✅ Defined (full contract) · 🔶 Domain modeled · 📋 Planned |

---

## 1. Position Calculator — Equity Mode

| # | Output | Type | Computation | Surface | Source | Status | Plan Files |
|---|--------|------|-------------|---------|--------|--------|------------|
| 1.1 | `risk_per_share` | $ | `|entry - stop|` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [05](05-mcp-server.md), [06h](06h-gui-calculator.md) |
| 1.2 | `account_risk_1r` | $ | `balance × risk_pct / 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [05](05-mcp-server.md), [06h](06h-gui-calculator.md) |
| 1.3 | `share_size` | # | `floor(account_risk_1r / risk_per_share)` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [05](05-mcp-server.md), [06h](06h-gui-calculator.md) |
| 1.4 | `position_size` | $ | `share_size × entry` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [05](05-mcp-server.md), [06h](06h-gui-calculator.md) |
| 1.5 | `position_to_account_pct` | % | `position_size / balance × 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1.6 | `reward_risk_ratio` | N:1 | `|target - entry| / risk_per_share` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [05](05-mcp-server.md), [06h](06h-gui-calculator.md) |
| 1.7 | `potential_profit` | $ | `share_size × |target - entry|` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |

---

## 1a. Position Calculator — Futures Mode

| # | Output | Type | Computation | Surface | Source | Status | Plan Files |
|---|--------|------|-------------|---------|--------|--------|------------|
| 1a.1 | `tick_value` | $ | `tick_size × contract_multiplier` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.2 | `risk_per_contract` | $ | `|entry - stop| × contract_multiplier` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.3 | `account_risk_1r` | $ | `balance × risk_pct / 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.4 | `contract_size` | # | `floor(account_risk_1r / risk_per_contract)` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.5 | `total_margin` | $ | `contract_size × margin_per_contract` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.6 | `margin_to_account_pct` | % | `total_margin / balance × 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.7 | `position_value` | $ | `contract_size × entry × contract_multiplier` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.8 | `reward_risk_ratio` | N:1 | `|target - entry| / |entry - stop|` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1a.9 | `potential_profit` | $ | `contract_size × |target - entry| × contract_multiplier` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |

---

## 1b. Position Calculator — Options Mode

| # | Output | Type | Computation | Surface | Source | Status | Plan Files |
|---|--------|------|-------------|---------|--------|--------|------------|
| 1b.1 | `max_loss_per_contract` | $ | `premium × contracts_multiplier` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.2 | `account_risk_1r` | $ | `balance × risk_pct / 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.3 | `contract_count` | # | `floor(account_risk_1r / max_loss_per_contract)` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.4 | `total_premium` | $ | `contract_count × premium × contracts_multiplier` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.5 | `delta_shares` | #.# | `contract_count × contracts_multiplier × delta` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.6 | `delta_exposure` | $ | `delta_shares × underlying_price` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.7 | `delta_exposure_pct` | % | `delta_exposure / balance × 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.8 | `breakeven` | $ | Call: `entry + premium`, Put: `entry - premium` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.9 | `reward_risk_ratio` | N:1 | `|target - breakeven| × multiplier / max_loss` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1b.10 | `potential_profit` | $ | `contract_count × |target - breakeven| × multiplier` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |

---

## 1c. Position Calculator — Forex Mode

| # | Output | Type | Computation | Surface | Source | Status | Plan Files |
|---|--------|------|-------------|---------|--------|--------|------------|
| 1c.1 | `risk_pips` | #.# | `|entry - stop| / pip_size` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.2 | `risk_per_lot` | $ | `risk_pips × pip_value` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.3 | `account_risk_1r` | $ | `balance × risk_pct / 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.4 | `lot_size` | #.# | `account_risk_1r / risk_per_lot` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.5 | `units` | # | `lot_size × lot_units` (100K/10K/1K) | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.6 | `margin_required` | $ | `units × entry / leverage` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.7 | `margin_to_account_pct` | % | `margin_required / balance × 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.8 | `reward_risk_ratio` | N:1 | `|target - entry| / |entry - stop|` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1c.9 | `potential_profit` | $ | `lot_size × |target - entry| / pip_size × pip_value` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |

---

## 1d. Position Calculator — Crypto Mode

| # | Output | Type | Computation | Surface | Source | Status | Plan Files |
|---|--------|------|-------------|---------|--------|--------|------------|
| 1d.1 | `risk_per_unit` | $ | `|entry - stop|` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.2 | `account_risk_1r` | $ | `balance × risk_pct / 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.3 | `quantity` | #.# | `account_risk_1r / risk_per_unit` (fractional) | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.4 | `position_value` | $ | `quantity × entry` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.5 | `margin_required` | $ | `position_value / leverage` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.6 | `margin_to_account_pct` | % | `margin_required / balance × 100` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.7 | `estimated_fees` | $ | `position_value × fee_rate / 100 × 2` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.8 | `reward_risk_ratio` | N:1 | `|target - entry| / |entry - stop|` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.9 | `potential_profit` | $ | `(quantity × |target - entry|) - estimated_fees` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |
| 1d.10 | `liquidation_price` | $ | Long: `entry × (1 - 1/leverage)`, Short: `entry × (1 + 1/leverage)` | 🖥️🤖🔌 | `POST /calculator/position-size` | ✅ | [06h](06h-gui-calculator.md) |

---

## 2. Calculator Warnings

| # | Output | Type | Condition | Severity | Surface | Status | Plan Files |
|---|--------|------|-----------|----------|---------|--------|------------|
| 2.1 | Position exceeds balance | Text | `position_to_account_pct > 100` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.2 | High risk percentage | Text | `risk_pct > 3` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.3 | Reward less than risk | Text | `reward_risk_ratio < 1` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.4 | Entry equals stop | Text | `entry == stop` | 🔴 | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.5 | Non-positive balance | Text | `balance <= 0` | 🔴 | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.6 | High margin (Futures/Forex) | Text | `margin_to_account_pct > 50` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.7 | Zero contracts (Futures) | Text | `contract_size == 0` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.8 | Low delta (Options) | Text | `delta < 0.1` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.9 | High delta exposure (Options) | Text | `delta_exposure_pct > 200` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.10 | Extreme leverage (Forex) | Text | `leverage > 100` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.11 | High leverage (Crypto) | Text | `leverage > 20` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |
| 2.12 | Fees exceed risk budget (Crypto) | Text | `estimated_fees > account_risk_1r × 0.1` | ⚠️ | 🖥️🤖🔌 | ✅ | [06h](06h-gui-calculator.md) |

---

## 3. Trade Computed Fields

| # | Output | Type | Computation | Surface | Source | Status | Plan Files |
|---|--------|------|-------------|---------|--------|--------|------------|
| 3.1 | `realized_pnl` | $ | `(sell_price - buy_price) × quantity - commission` | 🖥️🔌 | `GET /trades`, IBKR import | ✅ | [04](04-rest-api.md), [06b](06b-gui-trades.md) |
| 3.2 | Action color | Enum | `BOT` → green, `SLD` → red | 🖥️ | client-side | ✅ | [06b](06b-gui-trades.md) |
| 3.3 | P&L color | Enum | `≥ 0` → green, `< 0` → red | 🖥️ | client-side | ✅ | [06b](06b-gui-trades.md) |
| 3.4 | Screenshot badge count | # | Count of images per trade | 🖥️ | `GET /trades/{id}/images` | ✅ | [06b](06b-gui-trades.md) |

---

## 4. Tax Dashboard Summary Cards

| # | Output | Type | Source Field | Surface | Source Endpoint | Status | Plan Files |
|---|--------|------|-------------|---------|-----------------|--------|------------|
| 4.1 | ST Gains YTD | $ | `ytd_summary.st_gains` | 🖥️🔌 | `GET /tax/ytd-summary` | 📋 | [06g](06g-gui-tax.md) |
| 4.2 | LT Gains YTD | $ | `ytd_summary.lt_gains` | 🖥️🔌 | `GET /tax/ytd-summary` | 📋 | [06g](06g-gui-tax.md) |
| 4.3 | Wash Sale Adjustments | $ | `ytd_summary.wash_sale_adjustments` | 🖥️🔌 | `GET /tax/ytd-summary` | 📋 | [06g](06g-gui-tax.md) |
| 4.4 | Estimated Tax | $ | `ST × marginal + LT × lt_rate` | 🖥️🔌 | `GET /tax/ytd-summary` | 📋 | [06g](06g-gui-tax.md) |
| 4.5 | Loss Carryforward | $ | `ytd_summary.capital_loss_carryforward` | 🖥️🔌 | `GET /tax/ytd-summary` | 📋 | [06g](06g-gui-tax.md) |
| 4.6 | Harvestable Losses | $ | `harvest_losses().total` | 🖥️🔌 | `GET /tax/harvest` | 📋 | [06g](06g-gui-tax.md) |
| 4.7 | Tax Alpha Savings | $ | `ytd_summary.tax_alpha` | 🖥️🔌 | `GET /tax/ytd-summary` | 📋 | [06g](06g-gui-tax.md) |
| 4.8 | P&L by Symbol breakdown | table | Per-ticker ST/LT/Total gains | 🖥️🔌 | `GET /tax/ytd-summary?group_by=symbol` | 📋 | [06g](06g-gui-tax.md) |

---

## 5. Tax Lot Computed Fields

| # | Output | Type | Computation | Surface | Source | Status | Plan Files |
|---|--------|------|-------------|---------|--------|--------|------------|
| 5.1 | Gain/Loss | $ | `(proceeds - cost_basis) × quantity` | 🖥️🔌 | `GET /tax/lots` | 📋 | [06g](06g-gui-tax.md) |
| 5.2 | Holding period days | # | `close_date - open_date` (or current date if open) | 🖥️🔌 | `GET /tax/lots` | 📋 | [06g](06g-gui-tax.md) |
| 5.3 | ST/LT classification | Enum | `≥ 366 days` → LT, else ST | 🖥️🔌 | `GET /tax/lots` | 📋 | [06g](06g-gui-tax.md) |
| 5.4 | Days-to-LT countdown | # | `366 - holding_period_days` (for open lots) | 🖥️ | client-side | 📋 | [06g](06g-gui-tax.md) |
| 5.5 | Adjusted basis | $ | `original_basis + wash_sale_adjustment` | 🖥️🔌 | `GET /tax/lots/{id}` | 📋 | [06g](06g-gui-tax.md) |

---

## 6. Wash Sale Monitor Outputs

| # | Output | Type | Source | Surface | Endpoint | Status | Plan Files |
|---|--------|------|--------|---------|----------|--------|------------|
| 6.1 | Active chain count | # | aggregated | 🖥️🔌 | `GET /tax/wash-sales` | 📋 | [06g](06g-gui-tax.md) |
| 6.2 | Total trapped amount | $ | sum of `deferred_amount` | 🖥️🔌 | `GET /tax/wash-sales` | 📋 | [06g](06g-gui-tax.md) |
| 6.3 | Cross-account chain count | # | chains spanning multiple accounts | 🖥️🔌 | `GET /tax/wash-sales` | 📋 | [06g](06g-gui-tax.md) |
| 6.4 | Chain event timeline | list | chronological: disallowed → absorbed → released | 🖥️🔌 | `GET /tax/wash-sales/{id}` | 📋 | [06g](06g-gui-tax.md) |
| 6.5 | Prevention alert | Text | "Wait N days" or "Safe to sell" | 🖥️ | computed from latest purchase | 📋 | [06g](06g-gui-tax.md) |
| 6.6 | IRA permanent loss flag | Bool | wash sale triggered by IRA purchase | 🖥️🔌 | `GET /tax/wash-sales/{id}` | 📋 | [06g](06g-gui-tax.md) |
| 6.7 | DRIP conflict alert | Text | DRIP auto-purchase within wash window | 🖥️ | computed | 📋 | [06g](06g-gui-tax.md) |

---

## 7. What-If Simulator Outputs

| # | Output | Type | Source | Surface | Endpoint | Status | Plan Files |
|---|--------|------|--------|---------|----------|--------|------------|
| 7.1 | Lots closed (breakdown) | table | which lots selected by method | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |
| 7.2 | Per-lot gain/loss | $ | `(price - lot.cost_basis) × lot.quantity` | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |
| 7.3 | ST/LT classification per lot | Enum | `lot.is_long_term` + days held | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |
| 7.4 | Short-term tax estimate | $ | `st_gain × marginal_rate` | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |
| 7.5 | Long-term tax estimate | $ | `lt_gain × lt_rate` | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |
| 7.6 | Total estimated tax | $ | `st_tax + lt_tax` | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |
| 7.7 | Hold-savings tip | Text | "Wait N days → save $X" (Module C6) | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |
| 7.8 | Wash sale risk flag | Bool | conflict with existing chain (Module B8) | 🖥️🤖🔌 | `POST /tax/simulate` | 📋 | [06g](06g-gui-tax.md) |

---

## 8. Loss Harvesting Outputs

| # | Output | Type | Source | Surface | Endpoint | Status | Plan Files |
|---|--------|------|--------|---------|----------|--------|------------|
| 8.1 | Unrealized loss per ticker | $ | `(current_price - cost_basis) × qty` | 🖥️🤖🔌 | `GET /tax/harvest` | 📋 | [06g](06g-gui-tax.md) |
| 8.2 | Wash risk per ticker | Enum | Safe / DRIP conflict / 30-day window / IRA | 🖥️🤖🔌 | `GET /tax/harvest` | 📋 | [06g](06g-gui-tax.md) |
| 8.3 | Replacement suggestions | list | correlated non-identical securities (Module C3) | 🖥️🤖🔌 | `GET /tax/harvest` | 📋 | [06g](06g-gui-tax.md) |
| 8.4 | Total harvestable (safe) | $ | sum of safe-only losses | 🖥️🤖🔌 | `GET /tax/harvest` | 📋 | [06g](06g-gui-tax.md) |
| 8.5 | Total harvestable (all) | $ | sum of all unrealized losses | 🖥️🤖🔌 | `GET /tax/harvest` | 📋 | [06g](06g-gui-tax.md) |
| 8.6 | Estimated tax savings | $ | `total_safe × marginal_rate` | 🖥️🤖🔌 | `GET /tax/harvest` | 📋 | [06g](06g-gui-tax.md) |

---

## 9. Quarterly Payments Outputs

| # | Output | Type | Source | Surface | Endpoint | Status | Plan Files |
|---|--------|------|--------|---------|----------|--------|------------|
| 9.1 | Required payment per quarter | $ | method-dependent calculation | 🖥️🤖🔌 | `GET /tax/quarterly` | 📋 | [06g](06g-gui-tax.md) |
| 9.2 | Quarter status | Enum | PAID / OVER / DUE / UPCOMING | 🖥️🔌 | `GET /tax/quarterly` | 📋 | [06g](06g-gui-tax.md) |
| 9.3 | Shortfall amount | $ | `required - actual` | 🖥️🔌 | `GET /tax/quarterly` | 📋 | [06g](06g-gui-tax.md) |
| 9.4 | Underpayment penalty estimate | $ | `shortfall × (fed_rate + 3%) / 4` | 🖥️🔌 | `GET /tax/quarterly` | 📋 | [06g](06g-gui-tax.md) |
| 9.5 | Safe harbor method comparison | table | 4 methods side-by-side | 🖥️🔌 | `GET /tax/quarterly/compare` | 📋 | [06g](06g-gui-tax.md) |
| 9.6 | Due date per quarter | date | Apr 15, Jun 15, Sep 15, Jan 15 | 🖥️🔌 | `GET /tax/quarterly` | 📋 | [06g](06g-gui-tax.md) |

---

## 10. Transaction Audit Outputs

| # | Output | Type | Severity | Surface | Endpoint | Status | Plan Files |
|---|--------|------|----------|---------|----------|--------|------------|
| 10.1 | Missing cost basis | Text | 🔴 Error | 🖥️🔌 | `POST /tax/audit` | 📋 | [06g](06g-gui-tax.md) |
| 10.2 | Duplicate exec_id | Text | 🔴 Error | 🖥️🔌 | `POST /tax/audit` | 📋 | [06g](06g-gui-tax.md) |
| 10.3 | Impossible price | Text | 🟡 Warning | 🖥️🔌 | `POST /tax/audit` | 📋 | [06g](06g-gui-tax.md) |
| 10.4 | Corporate action gap | Text | 🟡 Warning | 🖥️🔌 | `POST /tax/audit` | 📋 | [06g](06g-gui-tax.md) |
| 10.5 | Orphaned lot | Text | 🟡 Warning | 🖥️🔌 | `POST /tax/audit` | 📋 | [06g](06g-gui-tax.md) |
| 10.6 | Missing account | Text | 🔴 Error | 🖥️🔌 | `POST /tax/audit` | 📋 | [06g](06g-gui-tax.md) |

---

## 11. Account Computed Fields

| # | Output | Type | Source | Surface | Endpoint | Status | Plan Files |
|---|--------|------|--------|---------|----------|--------|------------|
| 11.1 | Balance history sparkline | chart | time-series of snapshots | 🖥️ | `GET /accounts/{id}/balances` | 🔶 | [06d](06d-gui-accounts.md) |
| 11.2 | Net worth (all accounts) | $ | sum of latest balance per account | 🖥️🔌 | `GET /accounts` | ✅ | [06d](06d-gui-accounts.md) |
| 11.3 | Tax-advantaged total | $ | sum for IRA/401k accounts only | 🖥️ | client-side aggregation | 🔶 | [06d](06d-gui-accounts.md) |

---

## 12. Market Data Outputs

| # | Output | Type | Source | Surface | Endpoint | Status | Plan Files |
|---|--------|------|--------|---------|----------|--------|------------|
| 12.1 | Stock quote (price, volume, change) | object | provider auto-routing | 🖥️🤖🔌 | `GET /market-data/quote/{ticker}` | ✅ | [08](08-market-data.md) |
| 12.2 | Ticker search results | list | fuzzy match on name/symbol | 🤖🔌 | `GET /market-data/search?q=` | ✅ | [08](08-market-data.md) |
| 12.3 | News articles | list | ticker-scoped headlines | 🤖🔌 | `GET /market-data/news/{ticker}` | ✅ | [08](08-market-data.md) |
| 12.4 | SEC filings | list | ticker-scoped filings | 🤖🔌 | `GET /market-data/filings/{ticker}` | ✅ | [08](08-market-data.md) |
| 12.5 | Provider connection test result | Bool + Text | `success` + error message | 🖥️🤖🔌 | `POST /market-data/providers/{name}/test` | ✅ | [08](08-market-data.md) |

---

## 13. MCP Guard Status

| # | Output | Type | Source | Surface | Endpoint | Status | Plan Files |
|---|--------|------|--------|---------|----------|--------|------------|
| 13.1 | Guard status (active/locked) | Enum | `McpGuardModel.is_locked` | 🖥️🤖🔌 | `GET /mcp-guard` | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 13.2 | Calls in last minute | # | sliding window counter | 🖥️🔌 | `GET /mcp-guard` | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 13.3 | Calls in last hour | # | sliding window counter | 🖥️🔌 | `GET /mcp-guard` | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 13.4 | Lock reason | Text | `McpGuardModel.lock_reason` | 🖥️🤖🔌 | `GET /mcp-guard` | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |
| 13.5 | Locked-at timestamp | datetime | `McpGuardModel.locked_at` | 🖥️🔌 | `GET /mcp-guard` | ✅ | [04](04-rest-api.md), [06f](06f-gui-settings.md) |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total computed outputs | 120 |
| Sections | 17 (incl. sub-sections 1a–1d) |
| ✅ Defined (full contract) | 72 |
| 🔶 Domain modeled | 2 |
| 📋 Planned | 46 |
| Calculator outputs (§1–§2) | 57 |
| Tax outputs (§4–§10) | 46 |
| Trade/account outputs (§3, §11) | 7 |
| Market data outputs (§12) | 5 |
| Guard status outputs (§13) | 5 |
