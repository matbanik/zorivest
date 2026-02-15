# Position Calculator — GUI & MCP Interface Specification (v2)

> **Purpose**: Complete UI layout, MCP tool definition, and REST API for the position sizing calculator across all 5 instruments.  
> **Depends on**: [_position-calculator-features.md](_position-calculator-features.md) (feature spec v2)  
> **Date**: 2026-02-14 (v2 — incorporates Codex feedback)  

---

## 1. Architectural Overview

All entry points (React GUI, MCP tool, future CLI) call the **same REST endpoint**, which delegates to a shared Python service layer. This follows the project's established pattern from `DESIGN_PROPOSAL.md`.

```
┌──────────────┐     ┌──────────────┐     ┌────────────────────────────┐
│  React GUI   │     │  MCP Tool    │     │  Future CLI / Script       │
│  (Electron)  │     │  (TypeScript)│     │                            │
└──────┬───────┘     └──────┬───────┘     └────────────┬───────────────┘
       │                    │                           │
       │    HTTP POST       │    HTTP POST              │   HTTP POST
       ▼                    ▼                           ▼
┌────────────────────────────────────────────────────────────────────┐
│  POST /api/v1/calculators/position-size                            │
│  FastAPI Route                                                     │
├────────────────────────────────────────────────────────────────────┤
│  PositionSizeService.calculate(instrument, inputs)                 │
│  ├── validate(instrument, inputs)     → errors[]                   │
│  ├── snap_increments(inputs)          → inputs + notices[]         │
│  ├── _calculate_{instrument}(inputs)  → result                     │
│  └── _apply_feasibility_caps(result)  → result + warnings[]        │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. GUI Layout — React Component

The position calculator is a **page** in the Electron React app, accessible from the sidebar navigation. It uses a **tabbed interface** for instrument switching — the same pattern as Market Tools.

### 2.1 Page Structure (ASCII Wireframe)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Position Size Calculator                                (page h1)  │
│  Calculate optimal position size based on your risk tolerance       │
│                                                                     │
│  ┌──────────┬──────────┬─────────┬──────────┬───────────┐          │
│  │  Stocks  │ Futures  │  Forex  │  Crypto  │  Options  │  ← tabs  │
│  └────┬─────┴──────────┴─────────┴──────────┴───────────┘          │
│       │                                                             │
│  ┌────┴────────────────────────────────────────────────────────┐    │
│  │  INPUT SECTION                                               │    │
│  │                                                              │    │
│  │  ┌─ Common Inputs ──────────────────────────────────────┐   │    │
│  │  │ Account  [Default ▼]   Balance  $50,000  Risk% [__]  │   │    │
│  │  │ Entry Price      [$________]   Direction [Long ▼]    │   │    │
│  │  │ Stop Loss        [$________]   Target   [$________]  │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  │                                                              │    │
│  │  ┌─ Instrument-Specific Inputs (conditional) ───────────┐   │    │
│  │  │ (varies by active tab — see §2.3)                     │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  │                                                              │    │
│  │                    [ Calculate ]                              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  RESULTS CARD (visible after first calculation)              │   │
│  │                                                              │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │   │
│  │  │ 1R (Risk $)  │ │ Position Size│ │ Reward : Risk        │ │   │
│  │  │   $1,000     │ │  200 shares  │ │    2.00              │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │   │
│  │                                                              │   │
│  │  Position Value   $30,000     ACC%     60.00%               │   │
│  │  Potential Profit $2,000      (or "Unbounded" for long call)│   │
│  │                                                              │   │
│  │  [Instrument-specific outputs — see §2.4]                   │   │
│  │                                                              │   │
│  │  ┌─ ⚠️ Feasibility Warning (conditional) ───────────────┐  │   │
│  │  │ Position capped by capital: 200 → 166 shares          │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │                                                              │   │
│  │  ┌─ 📐 Increment Notice (conditional) ──────────────────┐  │   │
│  │  │ Stop snapped to nearest tick: 14488.25 → 14488.00     │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─ ▼ Advanced (collapsible, default collapsed) ───────────────┐   │
│  │ (instrument-specific advanced features — see §2.5)           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Account Selector (All Instruments)

The **Account** field is a dropdown populated from the user's configured accounts in the system (stored in the Zorivest SQLite database). It determines the balance/buying power used for all calculations.

| Item | Details |
|------|---------|
| **Widget** | Dropdown with search/filter |
| **Options** | All configured accounts + **"All Accounts (Combined)"** option |
| **Default** | The account marked as `is_default = true` in the system. If no default is set, the first account is selected. |
| **"All Accounts"** | When selected, the displayed balance is the **sum of all account balances**. The API receives `account_id = "all"`. |
| **Balance display** | Read-only currency value shown next to dropdown, auto-populated from selected account |
| **Manual override** | Not allowed — balance is always derived from the selected account. To use a custom value, create a manual/scratch account in settings. |

**Futures behavior**: When the Futures tab is active, the account dropdown still appears, but the resolved value is labeled **"Buying Power"** instead of "Balance" (the account's `buying_power` field is used instead of `balance`).

**How it works in the API**: The GUI sends `account_id` in the request. The backend resolves it to a numeric balance (or buying power for futures) before calculation. MCP agents can also pass `account_id` to reference accounts by name, or pass `account_balance` / `buying_power` directly as a numeric override.

### 2.3 Common Inputs (Stocks, Forex, Crypto)

These fields appear for Stocks, Forex, and Crypto. Futures and Options have modified input layouts (see §2.4.2 and §2.4.5).

| Field | Widget Type | Validation | Default |
|-------|-------------|------------|---------|
| Account | Account selector dropdown (see §2.2) | Required | Default account |
| Balance | Read-only currency display | Auto-populated | From selected account |
| Risk % | Number input with `%` suffix | > 0, ≤ 100 | `2` (stocks), `1` (forex/crypto) |
| Entry Price | Currency input | > 0 | Empty |
| Stop Loss | Currency input | > 0, ≠ entry | Empty |
| Target Price | Currency input | > 0 | Empty |
| Direction | Dropdown: `Long` / `Short` | Required | `Long` |

**Inline validation**: Errors appear below the field in red. Direction validation per [features §0.2](_position-calculator-features.md#02-direction-validation) triggers on blur and re-checks on Calculate.

### 2.4 Instrument-Specific Inputs

These fields appear/disappear when the user switches tabs. Each section replaces the "Instrument-Specific Inputs" area.

#### 2.4.1 Stocks — No Extra Inputs

No additional inputs beyond common fields.

#### 2.4.2 Futures — Modified Common Inputs

Futures uses the selected account's **buying power** instead of balance. When the Futures tab is active, the account selector still appears (same dropdown), but the resolved value label reads **"Buying Power"** and the account's `buying_power` field is used for 1R and all capital-based calculations.

| Field | Widget Type | Default |
|-------|-------------|---------|
| Account | Account selector dropdown (same as §2.2) | Default account |
| Buying Power | Read-only currency display (from account's `buying_power` field) | From selected account |
| Risk % | Number input with `%` suffix | `2` |
| Entry Price | Currency input | Empty |
| Stop Loss | Currency input | Empty |
| Target Price | Currency input | Empty |
| Direction | Dropdown: `Long` / `Short` | `Long` |
| Margin per Contract | Currency input | Empty |
| Tick Size | Number input | Empty |
| Tick Value ($) | Currency input | Empty |

#### 2.4.3 Forex

| Field | Widget Type | Default |
|-------|-------------|---------|
| Account Currency | Dropdown: `USD`, `EUR`, `GBP`, `JPY`, `CHF`, `AUD`, `CAD`, `NZD` | `USD` |
| Currency Pair | Predefined dropdown (e.g., `EUR/USD`, `GBP/JPY`) + `Custom` option | `EUR/USD` |
| Pip Size | Number input (**visible only when pair = Custom**; auto-detected for predefined pairs) | Auto / Empty |
| Conversion Rate | Number input (see conditional visibility below) | Empty |

**Conditional visibility rules:**
- **Pip Size**: Hidden for predefined pairs (auto-detected from registry §9). Visible and required when pair = "Custom".
- **Conversion Rate**: Hidden when account currency matches the pair's quote currency (Case A per [features §3.1](_position-calculator-features.md#31-pip-value-conversion-algorithm)). Visible with a helper label ("Enter XXX/YYY rate") when Case B or C applies. Required when visible.

#### 2.4.4 Crypto

| Field | Widget Type | Default |
|-------|-------------|---------|
| Coin / Token | Free-text input | Empty |

The Coin/Token field is informational — used for labeling results. The calculator does not fetch live prices.

#### 2.4.5 Options — Replaces Entire Input Section

Options has a **fundamentally different input layout**. When the Options tab is selected, the entire input section is replaced (no common Entry/Stop/Target/Direction). The account selector still appears.

```
┌─ Options Inputs ─────────────────────────────────────────────────┐
│                                                                   │
│  Account  [Default ▼]  Balance $50,000   Risk %  [___]            │
│                                                                   │
│  Strategy  [Long Call ▼]       Contract Multiplier  [100]         │
│                                                                   │
│  Input Mode  (○ Per-leg prices  ● Net debit/credit)               │
│     (visible for spreads + iron condor only)                      │
│                                                                   │
│  ── Long Call / Long Put ──────────────────────────               │
│  Strike Price       [$________]                                   │
│  Premium            [$________]                                   │
│                                                                   │
│  ── Vertical Spread (per-leg mode) ────────────────               │
│  Long Leg Premium   [$________]                                   │
│  Short Leg Premium  [$________]                                   │
│  Long Strike        [$________]                                   │
│  Short Strike       [$________]                                   │
│                                                                   │
│  ── Vertical Spread (net mode) ────────────────────               │
│  Net Debit/Credit   [$________]                                   │
│  Strike Width       [$________]                                   │
│                                                                   │
│  ── Iron Condor (per-leg mode) ────────────────────               │
│  Put Long Strike (K1)    [$________]   Put Long Premium   [$___]  │
│  Put Short Strike (K2)   [$________]   Put Short Premium  [$___]  │
│  Call Short Strike (K3)  [$________]   Call Short Premium  [$___] │
│  Call Long Strike (K4)   [$________]   Call Long Premium   [$___] │
│                                                                   │
│  ── Iron Condor (net mode) ────────────────────────               │
│  Net Credit         [$________]                                   │
│  Put Width          [$________]                                   │
│  Call Width         [$________]                                   │
│                                                                   │
│  ── Covered Call ──────────────────────────────────               │
│  Stock Price        [$________]                                   │
│  Strike Price       [$________]                                   │
│  Premium Received   [$________]                                   │
│  Owned Shares       [________]                                    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

**Strategy dropdown values** (C1 fix — long call/put split):

| Enum Value | Display Label |
|------------|--------------|
| `long_call` | Long Call |
| `long_put` | Long Put |
| `bull_call_spread` | Bull Call Spread |
| `bear_put_spread` | Bear Put Spread |
| `bull_put_spread` | Bull Put Spread |
| `bear_call_spread` | Bear Call Spread |
| `iron_condor` | Iron Condor |
| `covered_call` | Covered Call |

**Conditional field visibility** (driven by strategy + input mode):

| Strategy | Per-Leg Fields | Net Fields | Special Fields |
|----------|---------------|------------|----------------|
| Long Call | Strike, Premium | — | — |
| Long Put | Strike, Premium | — | — |
| Debit Spread (Bull Call, Bear Put) | Long Premium, Short Premium, Long Strike, Short Strike | Net Debit, Strike Width | — |
| Credit Spread (Bull Put, Bear Call) | Long Premium, Short Premium, Long Strike, Short Strike | Net Credit, Strike Width | — |
| Iron Condor | 4 strikes (K1-K4), 4 premiums | Net Credit, Put Width, Call Width | — |
| Covered Call | — | — | Stock Price, Strike, Premium Received, **Owned Shares** |

### 2.5 Instrument-Specific Outputs

These appear within the Results Card alongside common outputs.

| Instrument | Extra Outputs |
|------------|--------------|
| **Futures** | Max Contracts (from buying power), Ticks/Contract, Risk/Contract, Ticks to Target, Potential Profit/Contract |
| **Stocks** | Risk per Share, Risk-based Shares, Capital-based Shares, Final Shares |
| **Forex** | Stop Distance (pips), Pip Value, Lot, Mini-lot, Micro-lot Breakdown, Position Value |
| **Crypto** | Risk per Coin, Coins (fractional to 8 decimals) |
| **Options** | Max Loss/Contract, Risk-based Contracts, Final Contracts, Total Max Risk, Total Max Profit (or "Unbounded"), Breakeven(s) |

**Unbounded reward handling (C6 fix)**: For Long Call, max reward is unlimited. The GUI displays "Unbounded" for Potential Profit and "—" for Reward/Risk ratio instead of numeric values.

### 2.6 Advanced Section (Collapsible)

Default state: **collapsed**. Toggle button: `▶ Advanced Options` / `▼ Advanced Options`.

All fields below are optional. They're passed as **flat top-level fields** in the API request (not nested — C3 fix).

| Instrument | Advanced Fields |
|------------|----------------|
| **Stocks** | ATR Period (integer), ATR Multiplier (float, for ATR-based stops), Commission per Trade ($) |
| **Futures** | Commission per Trade ($) |
| **Forex** | Leverage Ratio (float), Spread (pips, float), Commission per Trade ($) |
| **Crypto** | Leverage Multiplier (float), Exchange Fee % (float) |
| **Options** | Commission per Contract ($), Implied Volatility (%, float), Greeks Display (informational — Delta, Theta, Vega) |

### 2.7 UX Behaviors

| Behavior | Description |
|----------|-------------|
| **Account selection** | Changing the account dropdown updates the displayed balance immediately. The selected account persists across tab switches. "All Accounts (Combined)" sums balances from all configured accounts. |
| **Tab switching** | Preserves input values between tabs where field names match (Account, Risk %). Instrument-specific fields reset to defaults on tab switch. |
| **Real-time validation** | Fields validate on blur. Direction validation runs when Entry, Stop, Target, or Direction change. |
| **Calculate button** | Sends POST to `/api/v1/calculators/position-size`. Button shows spinner while request is in-flight. |
| **Error display** | Validation errors from the API (422) are mapped to inline field errors. Non-field errors appear as a banner above the results. |
| **Feasibility warnings** | Displayed as amber banners in the results section. Explain which constraint capped the position and the before/after sizes. |
| **Increment notices** | Displayed as info banners. Show original value and snapped value. **Snapping is direction-aware** for risk fields: stop is snapped AWAY from entry (conservative — never reduces stop distance). See [features §0.7](_position-calculator-features.md#07-tickpip-increment-validation). |
| **Results persistence** | Results remain visible until the user calculates again or changes tabs. |
| **Keyboard shortcuts** | `Enter` triggers Calculate when focus is in any input field. |

---

## 3. React Component Hierarchy

```
PositionCalculatorPage
├── PageHeader
│   ├── Title: "Position Size Calculator"
│   └── Description: "Calculate optimal position size based on your risk tolerance"
│
├── InstrumentTabs
│   └── Tab[] — "Stocks" | "Futures" | "Forex" | "Crypto" | "Options"
│
├── AccountSelector (shared across all tabs — see §2.2)
│   ├── AccountDropdown (populated from system accounts)
│   └── BalanceDisplay (read-only, auto-populated — labeled "Buying Power" for Futures)
│
├── InputSection
│   ├── CommonInputs (hidden when Options or Futures tab is active)
│   │   ├── BalanceDisplay (read-only, from AccountSelector)
│   │   ├── RiskPercentInput
│   │   ├── EntryPriceInput
│   │   ├── StopLossInput
│   │   ├── TargetPriceInput
│   │   └── DirectionSelect
│   │
│   ├── FuturesInputs (visible only on Futures tab — includes modified common fields)
│   │   ├── BuyingPowerDisplay (read-only, from AccountSelector)
│   │   ├── RiskPercentInput
│   │   ├── EntryPriceInput
│   │   ├── StopLossInput
│   │   ├── TargetPriceInput
│   │   ├── DirectionSelect
│   │   ├── MarginInput
│   │   ├── TickSizeInput
│   │   └── TickValueInput
│   │
│   ├── ForexInputs (visible only on Forex tab)
│   │   ├── AccountCurrencySelect
│   │   ├── CurrencyPairSelect
│   │   ├── PipSizeInput (conditional — custom pair only)
│   │   └── ConversionRateInput (conditional — Cases B & C)
│   │
│   ├── CryptoInputs (visible only on Crypto tab)
│   │   └── CoinTokenInput
│   │
│   ├── OptionsInputs (visible only on Options tab — replaces all common inputs)
│   │   ├── BalanceDisplay (read-only, from AccountSelector)
│   │   ├── RiskPercentInput
│   │   ├── StrategySelect (8 strategies — see §2.3.5)
│   │   ├── ContractMultiplierInput
│   │   ├── InputModeToggle (Per-leg / Net — visible for spreads + iron condor)
│   │   ├── LongOptionFields (strike, premium — for Long Call / Long Put)
│   │   ├── SpreadPerLegFields (2 premiums, 2 strikes — for vertical spreads)
│   │   ├── SpreadNetFields (net debit/credit, width — for vertical spreads)
│   │   ├── IronCondorPerLegFields (4 premiums, 4 strikes)
│   │   ├── IronCondorNetFields (net credit, put width, call width)
│   │   └── CoveredCallFields (stock price, strike, premium, owned_shares)
│   │
│   └── CalculateButton
│
├── ResultsSection (visible after first calculation)
│   ├── PrimaryMetrics (1R | Position Size | R:R or "—") — card layout
│   ├── SecondaryMetrics (Position Value, ACC%, Potential Profit or "Unbounded")
│   ├── InstrumentSpecificOutputs (conditional per instrument)
│   ├── FeasibilityWarning (conditional)
│   └── IncrementNotice (conditional)
│
└── AdvancedSection (collapsible)
    └── InstrumentAdvancedFields (conditional per instrument — see §2.5)
```

---

## 4. REST API

### `POST /api/v1/calculators/position-size`

Single endpoint for all instruments. The `instrument` field determines which inputs are required and which formulas are applied.

#### 4.1 Stock Request Example

```json
{
  "instrument": "stocks",
  "account_id": "default",
  "risk_percent": 2,
  "entry_price": 150.00,
  "stop_loss": 145.00,
  "target_price": 165.00,
  "direction": "long"
}
```

#### 4.2 Futures Request Example

```json
{
  "instrument": "futures",
  "account_id": "default",
  "risk_percent": 1,
  "entry_price": 14500,
  "stop_loss": 14488,
  "target_price": 14550,
  "direction": "long",
  "margin_per_contract": 800,
  "tick_size": 0.25,
  "tick_value": 12.50
}
```

#### 4.3 Forex Request Example

```json
{
  "instrument": "forex",
  "account_id": "default",
  "risk_percent": 1,
  "entry_price": 1.0850,
  "stop_loss": 1.0800,
  "target_price": 1.0950,
  "direction": "long",
  "account_currency": "USD",
  "currency_pair": "EUR/USD"
}
```

#### 4.4 Forex Custom Pair Request Example

```json
{
  "instrument": "forex",
  "account_id": "default",
  "risk_percent": 1,
  "entry_price": 7.2500,
  "stop_loss": 7.2000,
  "target_price": 7.3500,
  "direction": "long",
  "account_currency": "USD",
  "currency_pair": "custom",
  "pip_size": 0.0001,
  "conversion_rate": 7.25
}
```

#### 4.5 Options Request — Long Call

```json
{
  "instrument": "options",
  "account_id": "default",
  "risk_percent": 2,
  "strategy": "long_call",
  "contract_multiplier": 100,
  "strike": 150.00,
  "premium": 5.00
}
```

#### 4.6 Options Request — Iron Condor (per-leg)

```json
{
  "instrument": "options",
  "account_id": "default",
  "risk_percent": 2,
  "strategy": "iron_condor",
  "contract_multiplier": 100,
  "input_mode": "per_leg",
  "put_long_strike": 140,
  "put_short_strike": 145,
  "call_short_strike": 155,
  "call_long_strike": 160,
  "put_long_premium": 1.00,
  "put_short_premium": 2.50,
  "call_short_premium": 2.00,
  "call_long_premium": 0.75
}
```

#### 4.7 Options Request — Iron Condor (net)

```json
{
  "instrument": "options",
  "account_id": "default",
  "risk_percent": 2,
  "strategy": "iron_condor",
  "contract_multiplier": 100,
  "input_mode": "net",
  "net_credit": 2.75,
  "put_width": 5,
  "call_width": 5
}
```

#### 4.8 Options Request — Covered Call

```json
{
  "instrument": "options",
  "account_id": "default",
  "risk_percent": 2,
  "strategy": "covered_call",
  "contract_multiplier": 100,
  "stock_price": 148.00,
  "strike": 155.00,
  "premium_received": 3.50,
  "owned_shares": 500
}
```

#### 4.9 Success Response (200)

```json
{
  "success": true,
  "instrument": "stocks",
  "results": {
    "one_r": 1000.00,
    "risk_per_unit": 5.00,
    "risk_based_size": 200,
    "capital_based_size": 333,
    "final_size": 200,
    "position_value": 30000.00,
    "account_percent": 60.00,
    "potential_profit": 3000.00,
    "reward_risk_ratio": 3.00
  },
  "warnings": [],
  "notices": []
}
```

#### 4.10 Unbounded Reward Response — Long Call (200)

For strategies with unlimited reward (Long Call), `potential_profit` and `reward_risk_ratio` are `null`:

```json
{
  "success": true,
  "instrument": "options",
  "results": {
    "one_r": 1000.00,
    "max_loss_per_contract": 500.00,
    "risk_based_contracts": 2,
    "final_contracts": 2,
    "total_max_risk": 1000.00,
    "total_max_profit": null,
    "reward_risk_ratio": null,
    "breakevens": [155.00]
  },
  "warnings": [],
  "notices": []
}
```

#### 4.11 Capped Position Response (200 with warnings)

```json
{
  "success": true,
  "instrument": "stocks",
  "results": { "...": "..." },
  "warnings": [
    {
      "type": "feasibility_cap",
      "message": "Position capped by available capital",
      "field": "final_size",
      "risk_based": 200,
      "capped_to": 166,
      "capped_by": "capital"
    }
  ],
  "notices": [
    {
      "type": "increment_snap",
      "message": "Stop snapped away from entry to nearest tick (conservative)",
      "field": "stop_loss",
      "original": 14488.25,
      "snapped_to": 14488.00
    }
  ]
}
```

#### 4.12 Validation Error Response (422)

```json
{
  "success": false,
  "errors": [
    {
      "field": "stop_loss",
      "message": "Long position requires stop < entry (got stop=155.00, entry=150.00)"
    },
    {
      "field": "risk_percent",
      "message": "Risk percent must be > 0 and ≤ 100"
    }
  ]
}
```

---

## 5. MCP Tool Definition

A **single MCP tool** exposes the calculator to AI agents. The MCP server wraps the REST API call with proper error handling.

### Tool: `calculate_position_size`

```typescript
// mcp-server/src/tools/calculator-tools.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

const API_BASE = 'http://localhost:8765/api/v1';

export function registerCalculatorTools(server: McpServer) {
  server.tool(
    'calculate_position_size',
    `Calculate optimal position size for risk management.

Determines how many shares, contracts, lots, or coins to trade based on:
- Account balance and risk tolerance (% of account)
- Entry, stop loss, and target prices (directional instruments)
- Instrument-specific parameters (margin, pip size, option strategy, etc.)

Supported instruments: stocks, futures, forex, crypto, options.
Options strategies: long_call, long_put, bull_call_spread, bear_put_spread,
  bull_put_spread, bear_call_spread, iron_condor, covered_call.

Returns: position size, dollar risk (1R), reward/risk ratio, position value,
and any feasibility warnings if the position was capped.
For long_call: potential_profit and reward_risk_ratio are null (unbounded).`,
    {
      // ── Required (all instruments) ──
      instrument: {
        type: 'string',
        enum: ['stocks', 'futures', 'forex', 'crypto', 'options'],
        description: 'Trading instrument type'
      },
      account_id: {
        type: 'string',
        description: 'Account identifier from configured accounts. Use "default" for the default account, "all" for combined balance of all accounts, or a specific account ID. If omitted, account_balance or buying_power must be provided instead.'
      },
      account_balance: {
        type: 'number',
        description: 'Direct numeric override for account balance (ignored for futures — use buying_power). Not needed if account_id is provided.'
      },
      risk_percent: {
        type: 'number',
        description: 'Risk per trade as percent (e.g. 2 for 2%)'
      },

      // ── Common directional (stocks/futures/forex/crypto) ──
      entry_price: {
        type: 'number',
        description: 'Planned entry price'
      },
      stop_loss: {
        type: 'number',
        description: 'Stop loss price'
      },
      target_price: {
        type: 'number',
        description: 'Target/take-profit price'
      },
      direction: {
        type: 'string',
        enum: ['long', 'short'],
        description: 'Trade direction'
      },

      // ── Futures-specific ──
      buying_power: {
        type: 'number',
        description: 'Futures: direct numeric override for buying power. Not needed if account_id is provided (resolved from account).'
      },
      margin_per_contract: {
        type: 'number',
        description: 'Futures: margin required per contract'
      },
      tick_size: {
        type: 'number',
        description: 'Futures: minimum price increment'
      },
      tick_value: {
        type: 'number',
        description: 'Futures: dollar value per tick'
      },

      // ── Forex-specific ──
      account_currency: {
        type: 'string',
        description: 'Forex: account denomination (e.g. USD, EUR, GBP)'
      },
      currency_pair: {
        type: 'string',
        description: 'Forex: currency pair (e.g. EUR/USD) or "custom"'
      },
      pip_size: {
        type: 'number',
        description: 'Forex: pip size (required when currency_pair = "custom")'
      },
      conversion_rate: {
        type: 'number',
        description: 'Forex: manual FX conversion rate (required for cross-currency pairs)'
      },

      // ── Crypto-specific ──
      coin_token: {
        type: 'string',
        description: 'Crypto: coin/token symbol (e.g. BTC, ETH)'
      },

      // ── Options-specific ──
      strategy: {
        type: 'string',
        enum: ['long_call', 'long_put', 'bull_call_spread', 'bear_put_spread',
               'bull_put_spread', 'bear_call_spread', 'iron_condor', 'covered_call'],
        description: 'Options: strategy type'
      },
      contract_multiplier: {
        type: 'number',
        description: 'Options: contract multiplier (default 100)'
      },
      input_mode: {
        type: 'string',
        enum: ['per_leg', 'net'],
        description: 'Options: pricing input mode (for spreads and iron condor)'
      },

      // Options — Long Call / Long Put
      strike: { type: 'number', description: 'Options: strike price (long call/put, covered call)' },
      premium: { type: 'number', description: 'Options: premium paid (long call/put)' },

      // Options — Vertical Spread (per-leg)
      long_leg_premium: { type: 'number', description: 'Options per-leg: long leg premium' },
      short_leg_premium: { type: 'number', description: 'Options per-leg: short leg premium' },
      long_strike: { type: 'number', description: 'Options per-leg: long strike price' },
      short_strike: { type: 'number', description: 'Options per-leg: short strike price' },

      // Options — Vertical Spread (net)
      net_debit: { type: 'number', description: 'Options net: net debit (debit spreads)' },
      net_credit: { type: 'number', description: 'Options net: net credit (credit spreads, iron condor)' },
      strike_width: { type: 'number', description: 'Options net: strike width (vertical spreads)' },

      // Options — Iron Condor (per-leg, 4 legs)
      put_long_strike: { type: 'number', description: 'Iron condor: put long strike (K1)' },
      put_short_strike: { type: 'number', description: 'Iron condor: put short strike (K2)' },
      call_short_strike: { type: 'number', description: 'Iron condor: call short strike (K3)' },
      call_long_strike: { type: 'number', description: 'Iron condor: call long strike (K4)' },
      put_long_premium: { type: 'number', description: 'Iron condor per-leg: put long premium' },
      put_short_premium: { type: 'number', description: 'Iron condor per-leg: put short premium' },
      call_short_premium: { type: 'number', description: 'Iron condor per-leg: call short premium' },
      call_long_premium: { type: 'number', description: 'Iron condor per-leg: call long premium' },

      // Options — Iron Condor (net)
      put_width: { type: 'number', description: 'Iron condor net: put wing width' },
      call_width: { type: 'number', description: 'Iron condor net: call wing width' },

      // Options — Covered Call
      stock_price: { type: 'number', description: 'Covered call: current stock price' },
      premium_received: { type: 'number', description: 'Covered call: premium received' },
      owned_shares: { type: 'integer', description: 'Covered call: number of shares owned (for strategy constraint)' },

      // ── Advanced (all optional, flat) ──
      atr_period: { type: 'integer', description: 'Stocks: ATR period for ATR-based stops' },
      atr_multiplier: { type: 'number', description: 'Stocks: ATR multiplier for stop distance' },
      leverage: { type: 'number', description: 'Forex/Crypto: leverage ratio or multiplier' },
      spread_pips: { type: 'number', description: 'Forex: spread in pips' },
      exchange_fee_percent: { type: 'number', description: 'Crypto: exchange fee as percent' },
      commission: { type: 'number', description: 'Commission per trade or per contract' },
      implied_volatility: { type: 'number', description: 'Options: implied volatility (informational)' },
    },
    async (params) => {
      try {
        const res = await fetch(`${API_BASE}/calculators/position-size`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
        });

        const data = await res.json();

        if (!res.ok) {
          // 422 validation errors or 5xx server errors
          return {
            content: [{
              type: 'text',
              text: JSON.stringify({
                success: false,
                status: res.status,
                errors: data.errors || data.detail || 'Unknown error',
              }, null, 2)
            }],
            isError: true,
          };
        }

        return {
          content: [{
            type: 'text',
            text: JSON.stringify(data, null, 2)
          }]
        };
      } catch (error) {
        // Network errors (backend not running, timeout, etc.)
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: `Network error: ${error instanceof Error ? error.message : String(error)}`,
              hint: 'Ensure the Zorivest backend is running on localhost:8765',
            }, null, 2)
          }],
          isError: true,
        };
      }
    }
  );
}
```

---

## 6. Python Service Layer

### Class Hierarchy

```
packages/core/src/zorivest_core/services/

position_sizing/
├── __init__.py
├── service.py              # PositionSizeService (entry point)
├── models.py               # Request/Response DTOs, enums
├── validators.py           # Input validation per instrument
├── calculators/
│   ├── __init__.py
│   ├── base.py             # BaseCalculator (shared formulas)
│   ├── stocks.py           # StocksCalculator
│   ├── futures.py          # FuturesCalculator
│   ├── forex.py            # ForexCalculator
│   ├── crypto.py           # CryptoCalculator
│   └── options.py          # OptionsCalculator
└── constants.py            # Currency pairs, pip sizes, etc.
```

### PositionSizeService

```python
class PositionSizeService:
    """Orchestrates position sizing across all instruments."""

    _calculators: dict[Instrument, BaseCalculator]

    def calculate(self, request: PositionSizeRequest) -> PositionSizeResponse:
        """
        1. Validate inputs (instrument-specific rules)
           - Directional: features §0.2, §0.3
           - Options: features §5.1
        2. Snap increments if needed (features §0.7), collect notices
           - Direction-aware: stop snaps AWAY from entry (conservative)
        3. Run instrument calculator
        4. Apply feasibility caps (features §0.6), collect warnings
           - final = min(risk, capital, margin, strategy) where N/A = +inf
        5. Round outputs for display (features §0.5)
        6. Return PositionSizeResponse with results, warnings, notices
        """
```

### BaseCalculator

Shared logic:
- `calculate_one_r(capital, risk_pct)` → `capital × (risk_pct / 100)`
  - Note: `capital` = `account_balance` for most instruments; `buying_power` for futures
- `calculate_reward_risk(profit, risk)` → `profit / risk` (returns `None` if profit is unbounded)
- `calculate_account_percent(position_value, capital)` → `(position_value / capital) × 100`
- `apply_rounding(size, instrument)` → per [features §0.4](_position-calculator-features.md#04-per-instrument-rounding-rules)
- `apply_feasibility_cap(risk_size, capital_size, margin_size, strategy_constraint)` → `min(...)` where any N/A constraint = `float('inf')`

### Per-Instrument Calculators

Each extends `BaseCalculator` and implements `calculate(inputs) → InstrumentResult`:
- All formulas from the feature spec §1–§5
- Each returns a typed result DTO with instrument-specific fields
- Options calculator dispatches to strategy-specific methods

---

## 7. Pydantic Models (Request/Response DTOs)

### Enums

```python
from enum import Enum

class Instrument(str, Enum):
    STOCKS = "stocks"
    FUTURES = "futures"
    FOREX = "forex"
    CRYPTO = "crypto"
    OPTIONS = "options"

class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"

class OptionsStrategy(str, Enum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    BULL_PUT_SPREAD = "bull_put_spread"
    BEAR_CALL_SPREAD = "bear_call_spread"
    IRON_CONDOR = "iron_condor"
    COVERED_CALL = "covered_call"

class InputMode(str, Enum):
    PER_LEG = "per_leg"
    NET = "net"
```

### Request Model

```python
from pydantic import BaseModel, Field, model_validator

class PositionSizeRequest(BaseModel):
    instrument: Instrument
    account_id: str | None = Field(None, description='Account ID: "default", "all", or specific ID')
    account_balance: float | None = Field(None, gt=0, description='Numeric override (not needed if account_id provided)')
    risk_percent: float = Field(gt=0, le=100)

    # ── Directional instruments ──
    entry_price: float | None = Field(None, gt=0)
    stop_loss: float | None = Field(None, gt=0)
    target_price: float | None = Field(None, gt=0)
    direction: Direction | None = None

    # ── Futures ──
    buying_power: float | None = Field(None, gt=0)
    margin_per_contract: float | None = Field(None, gt=0)
    tick_size: float | None = Field(None, gt=0)
    tick_value: float | None = Field(None, gt=0)

    # ── Forex ──
    account_currency: str | None = None
    currency_pair: str | None = None
    pip_size: float | None = Field(None, gt=0)
    conversion_rate: float | None = Field(None, gt=0)

    # ── Crypto ──
    coin_token: str | None = None

    # ── Options ──
    strategy: OptionsStrategy | None = None
    contract_multiplier: int | None = Field(None, gt=0)
    input_mode: InputMode | None = None

    # Options — Long Call / Long Put
    strike: float | None = Field(None, gt=0)
    premium: float | None = Field(None, gt=0)

    # Options — Vertical Spread (per-leg)
    long_leg_premium: float | None = Field(None, gt=0)
    short_leg_premium: float | None = Field(None, gt=0)
    long_strike: float | None = Field(None, gt=0)
    short_strike: float | None = Field(None, gt=0)

    # Options — Vertical Spread (net)
    net_debit: float | None = Field(None, gt=0)
    net_credit: float | None = Field(None, gt=0)
    strike_width: float | None = Field(None, gt=0)

    # Options — Iron Condor (per-leg, 4 legs)
    put_long_strike: float | None = Field(None, gt=0)
    put_short_strike: float | None = Field(None, gt=0)
    call_short_strike: float | None = Field(None, gt=0)
    call_long_strike: float | None = Field(None, gt=0)
    put_long_premium: float | None = Field(None, gt=0)
    put_short_premium: float | None = Field(None, gt=0)
    call_short_premium: float | None = Field(None, gt=0)
    call_long_premium: float | None = Field(None, gt=0)

    # Options — Iron Condor (net)
    put_width: float | None = Field(None, gt=0)
    call_width: float | None = Field(None, gt=0)

    # Options — Covered Call
    stock_price: float | None = Field(None, gt=0)
    premium_received: float | None = Field(None, gt=0)
    owned_shares: int | None = Field(None, gt=0)

    # ── Advanced (all optional, flat — not nested) ──
    atr_period: int | None = Field(None, gt=0)
    atr_multiplier: float | None = Field(None, gt=0)
    leverage: float | None = Field(None, gt=0)
    spread_pips: float | None = Field(None, ge=0)
    exchange_fee_percent: float | None = Field(None, ge=0, le=100)
    commission: float | None = Field(None, ge=0)
    implied_volatility: float | None = Field(None, ge=0)

    @model_validator(mode='after')
    def validate_instrument_fields(self):
        """Ensure required fields are present per instrument.
        See features spec §0.2 (direction), §0.3 (guardrails), §5.1 (options).
        """
        # Futures: buying_power required
        if self.instrument == Instrument.FUTURES:
            if not self.buying_power:
                raise ValueError("buying_power is required for futures")

        # Directional instruments: entry/stop/target/direction required
        if self.instrument in (Instrument.STOCKS, Instrument.FUTURES,
                               Instrument.FOREX, Instrument.CRYPTO):
            for field in ('entry_price', 'stop_loss', 'target_price', 'direction'):
                if getattr(self, field) is None:
                    raise ValueError(f"{field} is required for {self.instrument.value}")

        # Options: strategy required
        if self.instrument == Instrument.OPTIONS:
            if not self.strategy:
                raise ValueError("strategy is required for options")
            # Covered call: owned_shares required
            if self.strategy == OptionsStrategy.COVERED_CALL:
                if not self.owned_shares:
                    raise ValueError("owned_shares is required for covered_call strategy")

        # Forex: validate custom pair needs pip_size
        if self.instrument == Instrument.FOREX:
            if self.currency_pair == 'custom' and not self.pip_size:
                raise ValueError("pip_size is required when currency_pair is 'custom'")

        return self
```

### Response Models

```python
class Warning(BaseModel):
    type: str          # "feasibility_cap"
    message: str
    field: str
    risk_based: float
    capped_to: float
    capped_by: str     # "capital" | "margin" | "strategy"

class Notice(BaseModel):
    type: str          # "increment_snap"
    message: str
    field: str
    original: float
    snapped_to: float

class PositionSizeResponse(BaseModel):
    success: bool
    instrument: Instrument
    results: dict      # Instrument-specific result fields
    warnings: list[Warning] = Field(default_factory=list)
    notices: list[Notice] = Field(default_factory=list)

class ValidationErrorItem(BaseModel):
    field: str
    message: str

class ValidationErrorResponse(BaseModel):
    success: bool = False
    errors: list[ValidationErrorItem] = Field(default_factory=list)
```

---

## 8. FastAPI Route

```python
# packages/api/src/zorivest_api/routes/calculators.py
from fastapi import APIRouter, Depends, HTTPException
from zorivest_core.services.position_sizing import (
    PositionSizeService, PositionSizeRequest,
    PositionSizeResponse, ValidationErrorResponse
)

router = APIRouter(prefix="/calculators", tags=["calculators"])

@router.post(
    "/position-size",
    response_model=PositionSizeResponse,
    responses={422: {"model": ValidationErrorResponse}},
)
async def calculate_position_size(
    request: PositionSizeRequest,
    service: PositionSizeService = Depends(get_position_size_service),
):
    return service.calculate(request)
```

---

## 9. Currency Pair Registry (Forex)

Predefined dropdown values with auto-detected pip sizes:

| Category | Pairs | Pip Size |
|----------|-------|----------|
| **Majors** | EUR/USD, GBP/USD, USD/CHF, AUD/USD, NZD/USD, USD/CAD | 0.0001 |
| **Majors (JPY)** | USD/JPY | 0.01 |
| **Crosses** | EUR/GBP, EUR/AUD, EUR/CAD, GBP/AUD, GBP/CAD, AUD/NZD, EUR/NZD | 0.0001 |
| **Crosses (JPY)** | EUR/JPY, GBP/JPY, AUD/JPY, CAD/JPY, NZD/JPY, CHF/JPY | 0.01 |
| **Custom** | User-entered pair with manual pip size | User-specified (`pip_size` field required) |

The dropdown provides auto pip-size detection. A "Custom" option allows manual pair entry with user-specified `pip_size`.

---

## 10. Design Decisions Summary

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Instrument switching | Horizontal tabs | Matches Market Tools pattern; 5 tabs fit without overflow |
| 2 | MCP tool count | 1 tool (`calculate_position_size`) | Simpler for AI agents; instrument param routes logic server-side |
| 3 | REST endpoints | 1 endpoint (`POST /calculators/position-size`) | Single service layer; instrument-specific dispatch internal |
| 4 | Options input layout | Separate from common inputs | Fundamentally different structure (no entry/stop/target) |
| 5 | Validation location | Server-side (Python) | Single source of truth; UI shows field errors from API response |
| 6 | Advanced fields shape | Flat top-level (not nested) | One canonical shape across GUI, REST, MCP, Pydantic (C3 fix) |
| 7 | Futures capital field | `buying_power` required, `account_balance` ignored | Eliminates 1R ambiguity (C4 fix) |
| 8 | Long Call/Put split | Separate `long_call` + `long_put` enums | Distinct payoff models; call has unbounded reward (C1 fix) |
| 9 | Iron Condor schema | Full 4-leg fields (8 strikes + 8 premiums, or net + 2 widths) | No data loss (C2 fix) |
| 10 | Unbounded reward | `null` for `potential_profit` and `reward_risk_ratio` | Avoids serialization ambiguity — `null` over `Infinity` or string (C6 fix) |
| 11 | Covered Call constraint | `owned_shares` input → `floor(owned_shares / multiplier)` | Enables strategy_constraint enforcement (C5 fix) |
| 12 | Stop snapping direction | Risk fields snap AWAY from entry (conservative) | Never understates risk (M2 fix) |
| 13 | Feasibility formula | `min(risk, capital, margin, strategy)` — N/A = `+inf` | One canonical formula, consistent across all instruments (H1 fix) |

---

## Appendix A: Codex Feedback Resolution Map

| Finding | Severity | Resolution | Section |
|---------|----------|------------|---------|
| C1 — Long Call/Put merged | Critical | Split into `long_call` + `long_put` with separate strike/premium | §2.3.5, §5, §7 |
| C2 — Iron Condor schema | Critical | Full 4-leg fields + separate put/call widths for net mode | §2.3.5, §4.6, §4.7, §5, §7 |
| C3 — Advanced inconsistent | Critical | Flat top-level fields everywhere, all advanced fields enumerated | §2.5, §4.x, §5, §7 |
| C4 — Futures capital ambiguity | Critical | `buying_power` required for futures, replaces `account_balance` | §2.3.2, §4.2, §5, §7 |
| C5 — Covered Call missing owned_shares | Critical | `owned_shares` added to GUI/API/MCP/model | §2.3.5, §4.8, §5, §7 |
| C6 — Long Call unbounded reward | Critical | `null` for profit and R:R in unbounded strategies | §2.4, §4.10, §7 |
| H1 — Feasibility formula inconsistent | High | Canonical `min()` formula, N/A = `+inf` | §6, §10 |
| H2 — Forex custom pair missing pip_size | High | `pip_size` field added, required for custom pairs | §2.3.3, §4.4, §5, §7 |
| H3 — margin_lots undefined | High | See feature spec update (§3 forex) |
| H4 — MCP error handling | High | `response.ok` check, 422/5xx handling, network catch | §5 |
| H5 — Invalid JSON examples | High | Replaced with valid JSON per-instrument examples | §4.1–§4.8 |
| H6 — Mutable list defaults | High | `Field(default_factory=list)` in Pydantic models | §7 |
| H7 — Options typing too loose | High | `InputMode` enum, `gt=0` on all strike/premium fields | §7 |
| M1 — Cross-reference pointers | Medium | Explicit links to `_position-calculator-features.md` sections | §2.2, §2.6, §6 |
| M2 — Snap understates risk | Medium | Direction-aware conservative snapping for risk fields | §2.6 |
