# Phase 6h: GUI — Position Calculator

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the position size calculator as a standalone modal tool accessible from anywhere in the application via command palette (`Ctrl+Shift+C`) or from the Trade Plan detail view. Supports **five instrument modes** (Equity, Futures, Options, Forex, Crypto), multi-scenario comparison, calculation history, and one-click plan creation. The calculator is a pure-math tool with zero persistence dependencies — it calls a single REST endpoint.

> **Implementation phasing**: Equity mode is the base implementation (MEU-48). Additional modes (Futures, Options, Forex, Crypto), scenario comparison, calculation history, and Copy-to-Plan are expansion features delivered in a follow-up MEU.

> **Source**: [Input Index §1](input-index.md), [Domain Model Reference](domain-model-reference.md) `PositionSizeCalculator`. Originally documented in [06c-gui-planning.md](06c-gui-planning.md); extracted here for expanded specification.

---

## Calculator Modal

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Position Calculator                                     [✕]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Mode:  [ 📈 Equity ▼ ]    ←── Equity | Futures | Options |    │
│                                    Forex | Crypto               │
│                                                                 │
│  Account:   [ DU123456 — Main Trading ▼ ]   (or "All Accounts")│
│  Balance:   [ 100,000.00 ]     (auto-filled from account)      │
│  Risk %:    [ 1.0        ]                                      │
│                                                                 │
│  ── Instrument Input (changes per mode) ─────────────────      │
│                                                                 │
│  Entry:     [ 619.61     ]                                      │
│  Stop:      [ 615.00     ]                                      │
│  Target:    [ 630.00     ]                                      │
│  (Futures: +Multiplier, +Tick Size, +Margin)                   │
│  (Options: +Premium, +Delta, +Contracts)                       │
│  (Forex:   +Pair, +Lot Size, +Pip Value)                       │
│  (Crypto:  +Leverage, +Fractional Qty)                         │
│                                                                 │
│  ── Results ─────────────────────────────────────────────       │
│                                                                 │
│  Risk per unit:          $4.61                                  │
│  Account risk (1R):      $1,000.00                              │
│  Size:                   216 shares                              │
│  Position value:         $133,835.76                             │
│  Position % of account:  133.8%                                 │
│  Reward:Risk ratio:      2.25:1                                 │
│  Potential profit:       $2,246.94                               │
│                                                                 │
│  ⚠️ Position exceeds account balance (133.8%)                  │
│                                                                 │
│  [Calculate]  [Save Scenario]  [Copy to Plan]  [Clear]         │
│                                                                 │
│  ── Scenario Comparison ─────────────────────────────────       │
│                                                                 │
│  | Scenario | Mode   | Entry  | Stop   | Size | R:R  | Risk   │
│  |----------|--------|--------|--------|------|------|-------  │
│  | A (curr) | Equity | 619.61 | 615.00 | 216  | 2.25 | 1.0%  │
│  | B        |Futures | 5620   | 5600   | 2    | 3.00 | 1.0%  │
│  | C        | Forex  | 1.0850 | 1.0820 | 0.33 | 2.00 | 1.0%  │
│                                                                 │
│  ── Recent Calculations ─────────────────────────────────       │
│  📈 SPY 216 shares @619.61 (1.0% risk) — 2 min ago    [Load]  │
│  📊 /ES 2 contracts @5620 (1.0% risk) — 15 min ago    [Load]  │
│  💱 EUR/USD 0.33 lots @1.0850 (1.0% risk) — 1h ago    [Load]  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Common Input Fields (All Modes)

| Field | Type | Source | Default | Notes |
|-------|------|--------|---------|-------|
| `instrument_mode` | `select` | user input | `Equity` | Equity / Futures / Options / Forex / Crypto |
| `account_id` | `select` | populated from `/api/v1/accounts` | "All Accounts" | "All Accounts" uses portfolio total balance |
| `balance` | `number` | auto-filled from selected account | — | User can override; reverts on account change |
| `risk_pct` | `number` | user input | `1.0` | Percentage of account to risk (1R) |
| `entry` | `number` | user input | — | Entry price per unit |
| `stop` | `number` | user input | — | Stop loss price per unit |
| `target` | `number` | user input | — | Target price per unit |

### Account Resolution

| Selection | Balance Source |
|-----------|---------------|
| Specific account | Latest `BalanceSnapshot.balance` for that account |
| "All Accounts" (default) | Sum of latest balances across all accounts (portfolio total) |
| Manual override | User-entered value (ignores account selection) |

---

## Instrument Modes

The mode selector dynamically shows/hides instrument-specific fields and adjusts computations. All modes share the common inputs above.

### 📈 Equity Mode (Default)

Standard share-based sizing for stocks and ETFs.

| Extra Input | Type | Default | Notes |
|-------------|------|---------|-------|
| *(none)* | — | — | Equity uses only the common fields |

| Output | Computation | Format |
|--------|-------------|--------|
| `risk_per_share` | `\|entry - stop\|` | Currency |
| `account_risk_1r` | `balance × risk_pct / 100` | Currency |
| `share_size` | `floor(account_risk_1r / risk_per_share)` | Integer (rounded down) |
| `position_size` | `share_size × entry` | Currency |
| `position_to_account_pct` | `position_size / balance × 100` | Percentage |
| `reward_risk_ratio` | `\|target - entry\| / risk_per_share` | Ratio (N:1) |
| `potential_profit` | `share_size × \|target - entry\|` | Currency |

---

### 📊 Futures Mode

Contract-based sizing with multiplier, tick size, and margin requirements.

| Extra Input | Type | Default | Notes |
|-------------|------|---------|-------|
| `contract_multiplier` | `number` | preset per symbol | Point value per contract (e.g., /ES = $50, /NQ = $20, /CL = $1,000) |
| `tick_size` | `number` | preset per symbol | Minimum price increment (e.g., /ES = 0.25, /NQ = 0.25, /CL = 0.01) |
| `tick_value` | `number` | computed | `tick_size × contract_multiplier` |
| `margin_per_contract` | `number` | user input | Initial margin requirement per contract |

**Preset Symbols** (auto-fill multiplier + tick on symbol entry):

| Symbol | Multiplier | Tick Size | Tick Value | Typical Margin |
|--------|-----------|-----------|------------|----------------|
| /ES | $50 | 0.25 | $12.50 | ~$15,700 |
| /NQ | $20 | 0.25 | $5.00 | ~$21,000 |
| /YM | $5 | 1.00 | $5.00 | ~$11,000 |
| /RTY | $50 | 0.10 | $5.00 | ~$8,300 |
| /CL | $1,000 | 0.01 | $10.00 | ~$7,500 |
| /GC | $100 | 0.10 | $10.00 | ~$11,500 |
| /MES | $5 | 0.25 | $1.25 | ~$1,570 |
| /MNQ | $2 | 0.25 | $0.50 | ~$2,100 |

| Output | Computation | Format |
|--------|-------------|--------|
| `risk_per_contract` | `\|entry - stop\| × contract_multiplier` | Currency |
| `account_risk_1r` | `balance × risk_pct / 100` | Currency |
| `contract_size` | `floor(account_risk_1r / risk_per_contract)` | Integer |
| `total_margin` | `contract_size × margin_per_contract` | Currency |
| `margin_to_account_pct` | `total_margin / balance × 100` | Percentage |
| `position_value` | `contract_size × entry × contract_multiplier` | Currency |
| `reward_risk_ratio` | `\|target - entry\| / \|entry - stop\|` | Ratio (N:1) |
| `potential_profit` | `contract_size × \|target - entry\| × contract_multiplier` | Currency |

---

### 📋 Options Mode

Premium-based sizing with delta-adjusted exposure and contract multiplier (100 shares/contract).

| Extra Input | Type | Default | Notes |
|-------------|------|---------|-------|
| `option_type` | `select` | `Call` | Call / Put |
| `premium` | `number` | user input | Option premium per share |
| `delta` | `number` | user input | Option delta (0.0–1.0). Used for delta-adjusted exposure |
| `underlying_price` | `number` | user input | Current price of underlying stock |
| `contracts_multiplier` | `number` | `100` | Shares per contract (100 for US equity options) |

| Output | Computation | Format |
|--------|-------------|--------|
| `max_loss_per_contract` | `premium × contracts_multiplier` | Currency |
| `account_risk_1r` | `balance × risk_pct / 100` | Currency |
| `contract_count` | `floor(account_risk_1r / max_loss_per_contract)` | Integer |
| `total_premium` | `contract_count × premium × contracts_multiplier` | Currency |
| `delta_shares` | `contract_count × contracts_multiplier × delta` | Decimal |
| `delta_exposure` | `delta_shares × underlying_price` | Currency |
| `delta_exposure_pct` | `delta_exposure / balance × 100` | Percentage |
| `breakeven` | Call: `entry + premium`, Put: `entry - premium` | Currency |
| `reward_risk_ratio` | `\|target - breakeven\| × contracts_multiplier / max_loss_per_contract` | Ratio (N:1) |
| `potential_profit` | `contract_count × \|target - breakeven\| × contracts_multiplier` | Currency |

> **Note**: For bought options (long calls/puts), max loss = total premium paid. For more complex strategies (spreads, etc.), use the max-loss override field.

---

### 💱 Forex Mode

Pip-based sizing with standard/mini/micro lot support.

| Extra Input | Type | Default | Notes |
|-------------|------|---------|-------|
| `currency_pair` | `text` | user input | e.g., EUR/USD, GBP/JPY |
| `lot_type` | `select` | `Standard` | Standard (100K) / Mini (10K) / Micro (1K) |
| `pip_value` | `number` | auto-calculated | Per-pip value for selected lot type. USD pairs: Standard=$10, Mini=$1, Micro=$0.10 |
| `leverage` | `number` | `50` | Account leverage (e.g., 50:1) |

**Pip Value Reference** (per standard lot):

| Pair Type | Pip Size | Pip Value (Std) | Notes |
|-----------|----------|-----------------|-------|
| XXX/USD | 0.0001 | $10.00 | EUR/USD, GBP/USD, AUD/USD |
| USD/XXX | 0.0001 | varies | Depends on current rate |
| XXX/JPY | 0.01 | varies | EUR/JPY, GBP/JPY (¥1,000/pip → convert) |

| Output | Computation | Format |
|--------|-------------|--------|
| `risk_pips` | `\|entry - stop\| / pip_size` | Pips |
| `risk_per_lot` | `risk_pips × pip_value` | Currency |
| `account_risk_1r` | `balance × risk_pct / 100` | Currency |
| `lot_size` | `account_risk_1r / risk_per_lot` | Decimal (e.g., 0.33) |
| `units` | `lot_size × lot_units` | Integer (100K/10K/1K) |
| `margin_required` | `units × entry / leverage` | Currency |
| `margin_to_account_pct` | `margin_required / balance × 100` | Percentage |
| `reward_risk_ratio` | `\|target - entry\| / \|entry - stop\|` | Ratio (N:1) |
| `potential_profit` | `lot_size × \|target - entry\| / pip_size × pip_value` | Currency |

---

### 🪙 Crypto Mode

Fractional quantity sizing with optional leverage for perpetual futures.

| Extra Input | Type | Default | Notes |
|-------------|------|---------|-------|
| `leverage` | `number` | `1` | 1× = spot (no leverage), 2×–125× for perps/futures |
| `fee_rate` | `number` | `0.1` | Trading fee % (e.g., 0.1% maker). Applied to entry + exit |

| Output | Computation | Format |
|--------|-------------|--------|
| `risk_per_unit` | `\|entry - stop\|` | Currency |
| `account_risk_1r` | `balance × risk_pct / 100` | Currency |
| `quantity` | `account_risk_1r / risk_per_unit` | Decimal (supports fractional, e.g., 0.0342 BTC) |
| `position_value` | `quantity × entry` | Currency |
| `margin_required` | `position_value / leverage` | Currency |
| `margin_to_account_pct` | `margin_required / balance × 100` | Percentage |
| `estimated_fees` | `position_value × fee_rate / 100 × 2` | Currency (entry + exit) |
| `reward_risk_ratio` | `\|target - entry\| / \|entry - stop\|` | Ratio (N:1) |
| `potential_profit` | `(quantity × \|target - entry\|) - estimated_fees` | Currency (net of fees) |
| `liquidation_price` | Long: `entry × (1 - 1/leverage)`, Short: `entry × (1 + 1/leverage)` | Currency (if leveraged) |

---

## Warning Rules

### Common Warnings (All Modes)

| Condition | Severity | Message |
|-----------|----------|---------|
| `position_to_account_pct > 100` | ⚠️ Warning | Position exceeds account balance (N%) |
| `risk_pct > 3` | ⚠️ Warning | Risk exceeds 3% of account |
| `reward_risk_ratio < 1` | ⚠️ Warning | Reward less than risk (N:1) |
| `entry == stop` | 🔴 Error | Entry and stop cannot be equal (division by zero) |
| `balance <= 0` | 🔴 Error | Balance must be positive |

### Futures-Specific Warnings

| Condition | Severity | Message |
|-----------|----------|---------|
| `margin_to_account_pct > 50` | ⚠️ Warning | Margin exceeds 50% of account |
| `contract_size == 0` | ⚠️ Warning | Risk too small for even 1 contract at this stop distance |

### Options-Specific Warnings

| Condition | Severity | Message |
|-----------|----------|---------|
| `delta < 0.1` | ⚠️ Warning | Very low delta — high probability of expiring worthless |
| `delta_exposure_pct > 200` | ⚠️ Warning | Delta-adjusted exposure exceeds 2× account |

### Forex-Specific Warnings

| Condition | Severity | Message |
|-----------|----------|---------|
| `margin_to_account_pct > 50` | ⚠️ Warning | Margin exceeds 50% of account |
| `leverage > 100` | ⚠️ Warning | Leverage exceeds 100:1 — extreme risk |

### Crypto-Specific Warnings

| Condition | Severity | Message |
|-----------|----------|---------|
| `leverage > 20` | ⚠️ Warning | High leverage (N×) — liquidation at N% move |
| `estimated_fees > account_risk_1r × 0.1` | ⚠️ Warning | Fees exceed 10% of risk budget |

---

## Multi-Scenario Comparison

Save the current calculation as a named scenario and compare side-by-side:

- **Save Scenario** — adds current inputs + outputs to the comparison table
- **Table columns**: Scenario label, Entry, Stop, Target, Shares, R:R, Risk %, Position Size, Position %
- **Highlight best R:R** and **smallest position %** across scenarios
- Scenarios persist in React state during the session (not persisted to backend)
- Maximum 5 scenarios per session (oldest drops off)

---

## Calculation History

Recent calculations are stored in React state (session-scoped):

| Field | Source |
|-------|--------|
| Ticker (inferred) | From context if launched from plan, otherwise manual label |
| Shares | `share_size` result |
| Entry | `entry` input |
| Risk % | `risk_pct` input |
| Timestamp | Client-side `Date.now()` |

- **Load** — restores inputs from a history entry
- Maximum 10 entries (FIFO eviction)
- History clears on app restart (not persisted to backend)

---

## Copy to Plan Integration

When invoked from the calculator, **Copy to Plan** creates a new Trade Plan pre-filled with:

| Plan Field | Calculator Source |
|------------|-------------------|
| `entry_price` | `entry` |
| `stop_loss` | `stop` |
| `target_price` | `target` |
| `direction` | Inferred: `entry > stop` → Long, `entry < stop` → Short |

Navigates to [06c-gui-planning.md](06c-gui-planning.md) Trade Plan page with the new plan pre-filled in the detail pane.

---

## Keyboard Flow

The calculator is designed for rapid keyboard use:

| Key | Action |
|-----|--------|
| `Tab` | Move to next input field |
| `Shift+Tab` | Move to previous input |
| `Enter` | Calculate (when focus is on any input) |
| `Ctrl+S` | Save current scenario |
| `Escape` | Close modal |
| `Ctrl+Shift+C` | Open/toggle calculator (global) |

---

## REST Endpoint Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/calculator/position-size` | Calculate position size |
| `GET` | `/api/v1/accounts` | Populate account dropdown + resolve balance |

---

## Exit Criteria

**Base (MEU-48 — Equity mode):**
- Calculator modal opens from command palette (Ctrl+Shift+C) and from Trade Plan detail
- Equity mode inputs (account size, risk %, entry, stop, target) compute correct outputs
- Warning messages display (position > account, risk > 3%, R:R < 1, entry == stop)
- Division-by-zero guarded when entry == stop
- Tab/Enter keyboard flow works without mouse
- **Playwright E2E**: Calculator modal opens via Ctrl+Shift+C, equity computation renders correct outputs (see [GUI Shipping Gate](06-gui.md#gui-shipping-gate-mandatory-for-all-gui-meus))

**Expansion (follow-up MEU):**
- Mode selector switches between Equity, Futures, Options, Forex, and Crypto
- Instrument-specific fields show/hide dynamically on mode change
- Account dropdown populates with all accounts + "All Accounts" default
- Balance auto-fills from selected account's latest snapshot
- All output fields compute correctly per instrument mode
- Futures presets auto-fill multiplier/tick on symbol entry
- Options breakeven and delta-adjusted exposure compute correctly
- Forex pip-based sizing works with standard/mini/micro lots
- Crypto fractional quantity and liquidation price compute correctly
- Warning messages display per-mode (margin, leverage, delta, fees)
- Save Scenario adds row to comparison table with mode column (max 5)
- Cross-mode scenario comparison renders correctly (Equity vs Futures vs Forex)
- Recent calculations list shows last 10 with mode icon and Load button
- Copy to Plan creates pre-filled trade plan and navigates to planning page
- **Playwright E2E (Wave 10+ — define before implementation):** Mode switching renders correct fields, scenario comparison table populates, calculation history loads saved entry, Copy-to-Plan navigates to planning page with pre-filled fields (see [GUI Shipping Gate](06-gui.md#gui-shipping-gate-mandatory-for-all-gui-meus))

## Outputs

**Base (MEU-48 — Equity mode):**
- React component: `PositionCalculatorModal` (Equity computation only)
- Keyboard-driven modal with global shortcut (Ctrl+Shift+C)
- `data-testid` attrs matching E2E Wave 4 `CALCULATOR` constants

**Expansion (follow-up MEU):**
- React components: `InstrumentModeSelector`, `ScenarioComparisonTable`, `CalculationHistory`, `FuturesPresetSelector`
- 5 instrument modes with dynamic field rendering
- Futures symbol presets (/ES, /NQ, /YM, /RTY, /CL, /GC, /MES, /MNQ)
- Account selector with balance auto-resolution
- Multi-scenario comparison with cross-mode support (session-scoped, max 5)
- Calculation history with mode icons (session-scoped, max 10)
- Copy to Plan integration with [06c-gui-planning.md](06c-gui-planning.md)
