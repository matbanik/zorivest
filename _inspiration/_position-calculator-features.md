# Position Calculator Suite — Feature Specification

> **Purpose**: Complete feature definition for all instrument calculators in the Zorivest position sizing toolkit.  
> **Date**: 2026-02-14  
> **Revision**: v2 — incorporates GPT-5.3 Codex feedback (12 findings resolved)  
> **Status**: Feature-complete. Pending GUI/MCP design.

---

## 0. Common Definitions & Validation Contracts

### 0.1 Risk-Percent Input Convention

All instruments accept `Risk %` as **percent points** (e.g., user enters `2` for 2%).

```
risk_fraction = risk_percent / 100
1R = account_balance × risk_fraction
```

> This is the canonical conversion. Implementations MUST normalize to `risk_fraction` before any calculation.

### 0.2 Direction Validation Rules (Stocks, Futures, Forex, Crypto)

| Direction | Rule | Reject If |
|-----------|------|-----------|
| **Long** | `stop < entry < target` | `stop >= entry` or `target <= entry` |
| **Short** | `target < entry < stop` | `stop <= entry` or `target >= entry` |

Calculations MUST be rejected (not computed) when validation fails. Display a clear error message.

> **Options exception**: Options strategies define risk structurally (premium/spread width), not via entry/stop. Direction validation does not apply. See §5 for options-specific validation.

### 0.3 Input Guardrails (All Instruments)

Reject with explicit error when:
- `account_balance <= 0`
- `risk_percent <= 0` or `risk_percent > 100`
- `entry <= 0`, `stop <= 0`, `target <= 0`
- `entry == stop` (division by zero)
- Any denominator in a formula resolves to zero

### 0.4 Per-Instrument Rounding Rules

Position sizing rounds **down** to the instrument's minimum tradeable increment:

| Instrument | Rounding Rule | Example |
|------------|--------------|---------|
| **Stocks** | `floor()` to whole shares | 200.7 → 200 |
| **Futures** | `floor()` to whole contracts | 85.3 → 85 |
| **Forex** | `floor()` to broker lot step (e.g., `0.01`) | 0.2067 → 0.20 |
| **Crypto** | `floor()` to exchange quantity increment (e.g., `0.0001`) | 0.16678 → 0.1667 |
| **Options** | `floor()` to whole contracts | 4.8 → 4 |

### 0.5 Display Rounding Standards

All internal calculations run at **full floating-point precision**. Final display rounding:

| Field | Decimal Places |
|-------|---------------|
| Dollar amounts ($) | 2 |
| Percentages (%) | 2 |
| Ratios (R:R) | 2 |
| Shares / Contracts | 0 (whole) |
| Lots (forex) | 2 |
| Coins (crypto) | Market-specific (4–8 typical) |

### 0.6 Feasibility Cap (All Instruments)

Risk-based sizing can exceed available capital. The final position size MUST be:

```
final_size = min(risk_based_size, capital_based_size, margin_based_size, strategy_constraint)
```

**Canonical rule**: When a constraint does not apply to an instrument, treat it as `+inf` (effectively ignored). This ensures one consistent formula across all instruments.

| Constraint | Formula | N/A Behavior |
|-----------|---------|-------------|
| `risk_based_size` | Core sizing formula (per instrument) | Always applies |
| `capital_based_size` | `floor(account_balance / cost_per_unit)` | `+inf` if not applicable |
| `margin_based_size` | `floor(buying_power / margin_per_unit)` | `+inf` if margin not required |
| `strategy_constraint` | Strategy-specific (e.g., `floor(owned_shares / multiplier)` for Covered Call) | `+inf` if not applicable |

When `final_size < risk_based_size`, display a **warning**: "Position capped by [capital/margin/strategy limit]."

### 0.7 Tick/Pip Increment Validation

For instruments with defined increments (futures ticks, forex pips):
- Validate that entry, stop, and target prices are **multiples of the minimum increment**
- If not: **snap to nearest valid increment** and display a notice to the user
- **Direction-aware snapping for risk fields**: Stop loss snaps **AWAY from entry** (conservative direction) to ensure risk is never understated. Entry and target snap to nearest.
- Implementation:
  - General: `snapped = round(price / increment) × increment`
  - Stop (long): `snapped = floor(stop / increment) × increment` (snaps down, away from entry)
  - Stop (short): `snapped = ceil(stop / increment) × increment` (snaps up, away from entry)

---

## Universal Sizing Principle

All calculators follow one pattern with instrument-specific parameters:

```
1R = account_balance × (risk_percent / 100)
risk_based_size = 1R / risk_per_unit
final_size = min(risk_based_size, capital_based_size, margin_based_size)
```

| Instrument | Risk Per Unit | Size Unit | Rounding |
|------------|--------------|-----------|----------|
| Stocks | `ABS(entry - stop)` per share | Shares | Whole (floor) |
| Futures | `ticks × tick_value` per contract | Contracts | Whole (floor) |
| Forex | `stop_pips × pip_value` per lot | Lots | 0.01 step (floor) |
| Crypto | `ABS(entry - stop)` per coin | Coins | Exchange increment (floor) |
| Options | `max_loss_per_contract` (strategy-dependent) | Contracts | Whole (floor) |

---

## Common Outputs (All Instruments)

| Output | Formula | Display |
|--------|---------|---------|
| 1R (Dollar Risk) | `account × (risk_pct / 100)` | $0.00 |
| Position Size | Per-instrument (see rounding rules §0.4) | Per instrument |
| Position Value ($) | Instrument-specific | $0.00 |
| ACC% | `position_value / account × 100` | 0.00% |
| Potential Profit ($) | Instrument-specific | $0.00 |
| Reward/Risk Ratio | `potential_profit / 1R` | 0.00 |
| ⚠ Feasibility Warning | Shown when `final_size < risk_based_size` | Text |

---

## 1. Futures Calculator

> **Source**: `futures-calculator.xlsx` (direct extraction)

### Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Account Buying Power | Total trading capital | $410,000 |
| Tick Size | Minimum price increment | 0.25 |
| Tick Value ($) | Dollar value per tick | $0.50 |
| Margin Requirement | Per-contract margin | $1,600 |
| Risk % | Percent points (see §0.1) | 0.5 |
| Entry Price | Planned entry (must be tick-aligned, see §0.7) | 14500 |
| Stop Loss | SL price (tick-aligned) | 14488 |
| Target Price | TP price (tick-aligned) | 14550 |
| Direction | Long or Short | Long |

### Direction Validation (Fixed — Finding 1)

| Direction | Valid When | Example |
|-----------|-----------|---------|
| **Long** | `stop < entry < target` | Stop 14488 < Entry 14500 < Target 14550 ✅ |
| **Short** | `target < entry < stop` | Target 14450 < Entry 14500 < Stop 14512 ✅ |

### Outputs

| Output | Formula | Example (Long) |
|--------|---------|----------------|
| Max Contracts | `floor(buying_power / margin)` | 256 |
| 1R | `buying_power × (risk_pct / 100)` | $2,050 |
| Ticks per Contract | `ABS(entry - stop) / tick_size` | 48 |
| Risk per Contract ($) | `ticks × tick_value` | $24.00 |
| Risk-based Contracts | `floor(1R / risk_per_contract)` | 85 |
| **Final Contracts** | `min(risk_based, max_contracts)` | 85 |
| Position Size ($) | `margin × final_contracts` | $136,000 |
| ACC% | `position_size / buying_power × 100` | 33.17% |
| Potential Profit ($) | `(ABS(entry - target) / tick_size) × tick_value × final_contracts` | $3,542.50 |
| Reward/Risk | `potential_profit / 1R` | 1.73 |

---

## 2. Stock Position Calculator

> **Sources**: Britannica, Medium, BabyPips, InfinityAlgo, Groww, Strike.money (8+ sources)

### Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Account Balance | Total trading capital | $50,000 |
| Risk % | Percent points (1-2 typical) | 2 |
| Entry Price | Planned buy/sell price | $150.00 |
| Stop Loss | Exit price if wrong | $145.00 |
| Target Price | Take-profit level | $165.00 |
| Direction | Long or Short | Long |

### Direction Validation
Per §0.2: Long requires `stop < entry < target`. Short requires `target < entry < stop`.

### Outputs

| Output | Formula | Example |
|--------|---------|---------|
| 1R | `account × (risk_pct / 100)` | $1,000 |
| Risk per Share | `ABS(entry - stop)` | $5.00 |
| Risk-based Shares | `floor(1R / risk_per_share)` | 200 |
| Capital-based Shares | `floor(account / entry)` | 333 |
| **Final Shares** | `min(risk_based, capital_based)` | 200 |
| Position Size ($) | `final_shares × entry` | $30,000 |
| ACC% | `position_size / account × 100` | 60.00% |
| Potential Profit ($) | `ABS(target - entry) × final_shares` | $3,000 |
| Reward/Risk | `potential_profit / 1R` | 3.00 |

### Advanced Features (collapsible GUI)

| Feature | Description |
|---------|-------------|
| ATR-based Stop | Auto-calculate stop from ATR × multiplier |
| Margin/Leverage | Adjusts `capital_based_shares` using buying power (2:1 or 4:1) |
| Commission Impact | Subtract round-trip commission from profit |

---

## 3. Forex Position Calculator

> **Sources**: Afterprime, Forex Factory, Myfxbook, BabyPips, Dukascopy, ZuluTrade, CFI (16 sources)

### Key Concepts

| Concept | Description |
|---------|-------------|
| Pip | 0.0001 for most pairs, 0.01 for JPY pairs |
| Lot Sizes | Standard (100,000), Mini (10,000), Micro (1,000), Nano (100) |

### Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Account Balance | Total trading capital | $10,000 |
| Account Currency | Account denomination | USD |
| Risk % | Percent points (1-2 typical) | 1 |
| Currency Pair | **Predefined dropdown** (auto pip-size detection) | EUR/USD |
| Entry Price | Planned entry | 1.0850 |
| Stop Loss | SL price | 1.0800 |
| Target Price | TP price | 1.0950 |
| Direction | Long or Short | Long |
| Conversion Rate | Manual FX rate (see §3.1) | Required for Case B & C |

### Direction Validation
Per §0.2.

### 3.1 Pip Value Conversion Algorithm (Fixed — Finding 4)

Three cases, determined by the relationship between account currency and the pair's base/quote:

```
pair = BASE/QUOTE      (e.g., EUR/USD → base=EUR, quote=USD)
lot_size = 100000       (standard lot; scale for mini/micro/nano)

CASE A: account_currency == quote_currency
   pip_value = pip_size × lot_size
   Example: USD account, EUR/USD → pip_value = 0.0001 × 100000 = $10

CASE B: account_currency == base_currency
   pip_value = (pip_size × lot_size) / current_pair_rate
   Example: EUR account, EUR/USD, rate=1.0850
            pip_value = (0.0001 × 100000) / 1.0850 = €9.22

CASE C: account_currency is NEITHER base NOR quote
   Requires a conversion pair rate (account_currency / quote_currency)
   pip_value = (pip_size × lot_size) / conversion_rate
   Example: GBP account, EUR/USD, GBP/USD rate=1.2700
            pip_value = (0.0001 × 100000) / 1.2700 = £7.87
```

**Interim behavior (no live rates — Finding 12):**
- User MUST manually enter the conversion rate for Cases B and C
- If conversion rate field is empty for a cross-currency pair: reject calculation with error "Conversion rate required for [pair] with [account_currency] account"
- Display which conversion pair is needed (e.g., "Enter GBP/USD rate")

### Outputs

| Output | Formula | Example |
|--------|---------|---------|
| 1R | `account × (risk_pct / 100)` | $100 |
| Stop Distance (pips) | `ABS(entry - stop) / pip_size` | 50 |
| Pip Value | See §3.1 algorithm | $10.00 |
| Risk-based Lots | `1R / (stop_pips × pip_value)` | 0.20 |
| Margin-based Lots | `floor(account_balance × leverage / (lot_size × entry_price))` | 1.08 |
| **Final Lots** | `floor_to_step(min(risk_lots, margin_lots), 0.01)` | 0.20 |
| Lot Breakdown | Decompose into Standard / Mini / Micro | 2 mini lots |
| Position Value ($) | `final_lots × lot_size × entry` | $21,700 |
| Potential Profit ($) | `ABS(target - entry) / pip_size × pip_value × final_lots` | $200 |
| Reward/Risk | `potential_profit / 1R` | 2.00 |

**Margin-based Lots formula**: `margin_lots = floor(account_balance × leverage / (lot_size × entry_price))` where `lot_size = 100,000` for standard lots. If leverage is not provided, `margin_lots = +inf` (no margin cap applied).

### Advanced Features (collapsible GUI)

| Feature | Description |
|---------|-------------|
| Leverage Ratio | Used for margin_lots calculation; display position value / account |
| Margin Required | Based on leverage setting |
| Spread (pips) | Deducted from effective entry for profit estimate |
| Commission per Trade | Deducted from profit estimate |

### Future Enhancement
- **Live exchange rate API** for automatic pip-value conversion (eliminates manual rate entry)

---

## 4. Crypto Position Calculator

> **Sources**: Altrady, Flipster, InfinityAlgo, Amsflow, Deriv Academy, Bookmap (8+ sources)

### Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Account Balance | Total trading capital | $25,000 |
| Risk % | Percent points (**0.5-1 recommended**) | 1 |
| Coin/Token | Asset traded | BTC |
| Entry Price | Planned entry | $45,000 |
| Stop Loss | SL price | $43,500 |
| Target Price | TP price | $49,500 |
| Direction | Long or Short | Long |

### Direction Validation
Per §0.2.

### Outputs

| Output | Formula | Example |
|--------|---------|---------|
| 1R | `account × (risk_pct / 100)` | $250 |
| Risk per Coin | `ABS(entry - stop)` | $1,500 |
| Risk-based Coins | `1R / risk_per_coin` | 0.16667 |
| Capital-based Coins | `account / entry` | 0.55556 |
| **Final Coins** | `floor_to_step(min(risk_coins, capital_coins), exchange_increment)` | 0.1666 |
| Position Value ($) | `final_coins × entry` | $7,497 |
| ACC% | `position_value / account × 100` | 29.99% |
| Potential Profit ($) | `ABS(target - entry) × final_coins` | $749.70 |
| Reward/Risk | `potential_profit / 1R` | 3.00 |

### Key Differences from Stocks

| Aspect | Stocks | Crypto |
|--------|--------|--------|
| Output unit | Whole shares | **Fractional coins** |
| Default risk % | 1-2% | **0.5-1%** |
| Trading hours | Market hours | **24/7** |
| Typical stop distance | 2-5% | **5-15%** (BTC) |

### Advanced Features (collapsible GUI)

| Feature | Description |
|---------|-------------|
| Leverage Multiplier | Adjusts effective position display (not risk calc) |
| Exchange Fee % | Deducted from profit estimate |
| Altcoin Volatility Warning | Flag when stop is tight on high-vol assets |

---

## 5. Options Position Calculator

> **Sources**: OpenAI GPT-5.2 research, Fidelity, Schwab, TradingBlock, OptionStrat, CBOE, OptionsForge (24+ sources)

### 5.1 Options-Specific Validation (Finding 7)

Options do NOT use the global direction/stop validation from §0.2. Instead:

| Validation | Rule |
|-----------|------|
| Premium | Must be > 0 |
| Strike(s) | Must be > 0 |
| Width (spreads) | `ABS(strike1 - strike2) > 0` |
| Credit (credit spreads) | Must be > 0 AND < Width |
| Debit (debit spreads) | Must be > 0 AND < Width |
| Covered Call stock price | Must be > 0; must own ≥ 100 shares per contract (strategy constraint) |
| Contract Multiplier | Must be > 0 (default: 100) |

### 5.2 Supported Strategies

#### Strategy 1a: Long Call (Bullish)

| Field | Formula |
|-------|---------|
| Inputs | Strike price (K), Premium paid |
| Construction | Buy 1 call at strike K |
| Max Risk | `premium × multiplier` |
| Max Reward | **Unlimited** (API returns `null` for profit and R:R) |
| Breakeven | `K + premium` |

#### Strategy 1b: Long Put (Bearish)

| Field | Formula |
|-------|---------|
| Inputs | Strike price (K), Premium paid |
| Construction | Buy 1 put at strike K |
| Max Risk | `premium × multiplier` |
| Max Reward | `(K - premium) × multiplier` |
| Breakeven | `K - premium` |

#### Strategy 2: Vertical Spread — Explicit Breakeven Formulas (Fixed — Finding 6)

**4 variants** (all 2-leg, same expiration):

| Variant | Direction | Legs | Max Risk | Max Reward | Breakeven |
|---------|-----------|------|----------|-----------|-----------|
| **Bull Call** | Bullish | Buy low call, sell high call | `debit × M` | `(width - debit) × M` | `low_strike + debit` |
| **Bear Put** | Bearish | Buy high put, sell low put | `debit × M` | `(width - debit) × M` | `high_strike - debit` |
| **Bull Put** | Bullish | Sell high put, buy low put | `(width - credit) × M` | `credit × M` | `high_strike - credit` |
| **Bear Call** | Bearish | Sell low call, buy high call | `(width - credit) × M` | `credit × M` | `low_strike + credit` |

Where: `width = high_strike - low_strike`, `M = multiplier (default 100)`

#### Strategy 3: Iron Condor

| Field | Formula |
|-------|---------|
| Construction | Bull put spread + Bear call spread (same expiration) |
| Legs | Buy low put (K1), sell mid put (K2), sell mid call (K3), buy high call (K4) |
| Put Width | `K2 - K1` |
| Call Width | `K4 - K3` |
| Max Risk | `(max(put_width, call_width) - total_credit) × M` |
| Max Reward | `total_credit × M` |
| Breakeven (lower) | `K2 - total_credit` |
| Breakeven (upper) | `K3 + total_credit` |

#### Strategy 4: Covered Call

| Field | Formula |
|-------|---------|
| Inputs | Stock price, Strike price (K), Premium received, **Owned Shares** |
| Construction | Own 100 shares + sell 1 call |
| **Strategy Constraint** | `floor(owned_shares / multiplier)` — caps max contracts to shares owned |
| Max Risk | `(stock_price - premium) × M` (stock drops to 0) |
| Max Reward | `(strike - stock_price + premium) × M` |
| Breakeven | `stock_price - premium` |

### 5.3 Unified Options Sizing

```
max_loss_per_contract = (see table below)
risk_based_contracts = floor(1R / max_loss_per_contract)
final_contracts = min(risk_based_contracts, strategy_constraint)
```

| Strategy | MaxLossPerContract ($) |
|----------|----------------------|
| Long Call/Put | `premium × M` |
| Debit Spread | `debit × M` |
| Credit Spread | `(width - credit) × M` |
| Iron Condor | `(max(W_put, W_call) - credit) × M` |
| Covered Call | `(stock_price - premium) × M` |

### 5.4 Input Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Mode A: Per-leg prices** | Enter individual premium for each leg; system computes net debit/credit | More precise |
| **Mode B: Net debit/credit** | Enter single net price for the spread | Simpler |

### Inputs

| Input | Required For | Description |
|-------|-------------|-------------|
| Account Balance | All | Trading capital |
| Risk % | All | Percent points |
| Strategy Type | All | Dropdown selection |
| Contract Multiplier | All | Default 100 |
| Per-leg prices | Mode A | Individual premium per leg |
| Net Debit/Credit | Mode B | Single net spread price |
| Strike(s) | Spreads + IC | Per leg |
| Stock Price | Covered Call | Current underlying |

### Outputs

| Output | Formula | Display |
|--------|---------|---------|
| 1R | `account × (risk_pct / 100)` | $0.00 |
| Max Loss / Contract ($) | Strategy-dependent | $0.00 |
| Risk-based Contracts | `floor(1R / max_loss)` | 0 |
| **Final Contracts** | `min(risk_based, strategy_limit)` | 0 |
| Total Max Risk ($) | `final_contracts × max_loss` | $0.00 |
| Total Max Profit ($) | `final_contracts × max_profit` | $0.00 |
| Breakeven(s) | Strategy-dependent (see §5.2) | $0.00 |
| Reward/Risk Ratio | `total_max_profit / total_max_risk` | 0.00 |

### Advanced Features (collapsible GUI)

| Feature | Description |
|---------|-------------|
| Commission per Contract | Deducted from profit, added to risk |
| Implied Volatility | User input for theoretical pricing (informational) |
| Greeks Display | Delta, Theta, Vega — informational only |

---

## GUI Design Notes

> **Full specification**: See [_position-calculator-gui-mcp.md](_position-calculator-gui-mcp.md) for complete GUI layout, MCP tool definition, REST API contract, and service layer design.

Summary of key decisions:
- **Instrument switching**: Horizontal tabs (Stocks | Futures | Forex | Crypto | Options)
- **Single MCP tool**: `calculate_position_size` with `instrument` parameter
- **Single REST endpoint**: `POST /api/v1/calculators/position-size`
- All Advanced features in a **collapsible section** (collapsed by default)
- MCP tool interface mirrors GUI inputs/outputs
- **Validation is instrument-specific** (§0.2 for directional instruments, §5.1 for options)
- Feasibility warnings displayed when position is capped (§0.6)
- Price increment notices displayed when values are snapped (§0.7)
