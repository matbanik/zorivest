# TJS-Inspired Features & Import Capabilities

> Tracking features identified from [TJS Elite v8.9.8 analysis](file:///p:/zorivest/_inspiration/tjs_elite_analysis.txt) and future import/integration capabilities. This document will grow as more platforms and features are scoped.

---

## Table of Contents

1. [Expectancy Calculator (Monte Carlo)](#1-expectancy-calculator-monte-carlo-simulation)
2. [Drawdown Probability Table](#2-drawdown-probability-table)
3. [MFE / MAE / BSO Analysis](#3-mfe--mae--bso-trade-execution-quality)
4. [SQN — System Quality Number](#4-sqn--system-quality-number)
5. [Mistake Tracking with Cost Attribution](#5-mistake-tracking-with-cost-attribution)
6. [NinjaTrader Trade Import](#6-ninjatrader-trade-import)
7. [Broker Transaction Types](#7-broker-transaction-types)
8. [Monthly P&L Calendar Report](#8-monthly-pl-calendar-report)
9. [Strategy Breakdown Report](#9-strategy-breakdown-report)
10. [Platform Integrations](#10-platform-integrations) — Alpaca, Tradier, IBKR, MT5, Freedom24, OpenAlgo, QuantConnect, FinAgent
11. [Integration Priority](#integration-priority)

---

## 1. Expectancy Calculator (Monte Carlo Simulation)

**Source:** TJS Expectancy sheet + industry research  
**Status:** `[ ]` Not started  
**Priority:** High  
**Module:** Reports / Calculator Tool

### What It Is

The expectancy calculator models the probable outcomes of a trading system over N trades using Monte Carlo simulation. Instead of a single projection, it runs thousands of randomized trade sequences to produce a distribution of possible outcomes, accounting for the randomness of win/loss ordering.

### How TJS Implements It

TJS accepts 5 inputs — starting capital, risk % of capital, win %, payoff ratio, and commission — then simulates ~100 trades using a random number generator. For each trade, it generates a Monte Carlo random value, determines W/L outcome based on win %, applies the payoff ratio and commission, and tracks cumulative capital, drawdown, and peak gain.

### Industry Best Practices

Modern implementations (clearank.com, probabilitycalculator.pro, backtestbase.com) go further:

- **10,000+ simulation runs** with confidence intervals (5th/50th/95th percentile equity curves)
- **Two position-sizing models:** % of account (compounding) vs fixed $ risk (non-compounding)
- **Risk-of-Ruin integration** — probability of hitting a chosen drawdown before recovering
- **Profit Factor:** `(Win% × Avg Win) / (Loss% × Avg Loss)` as a secondary quality metric
- **Break-even win rate calculation** given the current payoff ratio

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Data source** | Auto-populate from actual trade history (win %, avg win/loss, payoff ratio) — or allow manual override for hypothetical scenarios |
| **Simulation engine** | Python backend: `numpy` random sampling, 10,000 iterations |
| **Output** | Fan chart showing 5th/25th/50th/75th/95th percentile equity curves; summary stats (expected return, max DD, risk of ruin, longest streak) |
| **Exposure** | MCP tool (`monte_carlo_expectancy`), GUI chart tab, scheduled report |
| **AI use case** | *"Based on my last 50 trades, what's my expected return over the next 100 trades at 1% risk?"* |

### Key Formulas

```
Net Expectancy  = (Win% × Avg Win) - (Loss% × Avg Loss)
Profit Factor   = (Win% × Avg Win) / (Loss% × Avg Loss)
Break-Even Win% = 1 / (1 + Payoff Ratio)
Risk of Ruin    = ((1 - Edge) / (1 + Edge)) ^ Capital_Units
```

---

## 2. Drawdown Probability Table

**Source:** TJS Drawdown sheet + Balsara tables  
**Status:** `[ ]` Not started  
**Priority:** High  
**Module:** Risk Management / Reports

### What It Is

A precomputed matrix showing the statistical probability of experiencing X consecutive losing trades given your win rate, over a defined number of trades. This is the single most important *risk awareness* tool for traders who don't intuitively understand how common losing streaks are.

### How TJS Implements It

TJS provides a matrix with win rates from 5% to 95% (rows) and consecutive loss counts from 2 to 11 (columns). Each cell shows the probability (0–1) of experiencing at least one run of that many consecutive losses within 100 trades.

**Key insight from the table:** At a 50% win rate over 100 trades:
- 2 consecutive losses: 99.997% probable (virtually certain)
- 4 consecutive losses: 82.7% probable
- 6 consecutive losses: 31.5% probable
- 10 consecutive losses: 2.0% probable

### Industry Best Practices

- **Balsara Risk-of-Ruin Tables** — Academic standard; maps win rate × payoff ratio → ruin probability
- **Configurable trade count** — Not fixed at 100; allow traders to model their actual trade frequency (e.g., 720 trades/year for a 3-trade/day strategy)
- **Dollar-denominated drawdown** — `Risk Amount × Consecutive Losses = Equity Drawdown` (TJS includes this: $100 risk × 10 losses = -$1,000 drawdown)
- **Loss streak probability calculators** (daytradinglife.com) — Excel-based ProbRun formula: probability of 1+ runs of X consecutive losses in N trades

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Static table** | Precomputed matrix for common win rates (20–80%) and streak lengths (2–15), stored as reference data |
| **Dynamic calculator** | Accept trader's actual win % and number of trades → compute personalized streak probabilities |
| **AI intervention** | When a losing streak matches a statistically significant threshold: *"You've hit 5 losses in a row. At your 55% win rate, this happens 19% of the time over 100 trades. Take a break — this is statistically normal."* |
| **Exposure** | MCP tool (`drawdown_probability`), GUI reference table, trigger-based AI alerts |

### Key Formula

```
P(streak ≥ k in n trades) = 1 - P(no run of k losses in n trades)
  where P(no run) uses a recursive Markov chain model

Simplified: P ≈ 1 - (1 - (1-WinRate)^k)^(n/k)  (approximation)
```

---

## 3. MFE / MAE / BSO (Trade Execution Quality)

**Source:** TJS StockTradingLog columns + Tradervue / Trademetria  
**Status:** `[ ]` Not started  
**Priority:** High  
**Module:** Trade Logging / Reports

### What It Is

Three metrics that measure how well a trader captures available profit and manages risk during a trade:

| Metric | Full Name | What It Answers |
|--------|-----------|----------------|
| **MFE** | Maximum Favorable Excursion | *"How much was this trade up at its best point?"* |
| **MAE** | Maximum Adverse Excursion | *"How far did this trade go against me before I closed it?"* |
| **BSO** | Best Scale-Out | *"What was the best price I could have exited at?"* |

### Industry Standard (Tradervue/Trademetria)

Modern trade journals track two variants per trade:

| Variant | MFE | MAE |
|---------|-----|-----|
| **Price-based** | Max favorable price movement (direction-independent) | Max adverse price movement |
| **Position-based** | Max unrealized $ gain during trade | Max unrealized $ loss during trade |

**Tradervue** reports: Price MAE, Price MFE, Position MAE, Position MFE per trade.  
**Trademetria** adds: intraday vs end-of-day variants.

### Analytical Value

- **MFE vs Actual P&L** — Shows how much profit was left on the table. If MFE consistently dwarfs actual P&L, exits are too early.
- **MAE distribution** — If MAE is consistently near the stop loss, stops may be too tight. If MAE is small on winning trades, entries are well-timed.
- **MFE/MAE ratio** — High ratio = good entry timing. A trade that went $2,000 in your favor (MFE) but only $300 against (MAE) before winning had excellent entry quality.

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Schema additions** | `mfe_price`, `mae_price`, `bso_price` on trade record; derived fields `mfe_dollars`, `mae_dollars` |
| **Data population** | Auto-calculate from broker tick/bar data (IBKR high/low after entry) or accept manual input |
| **Aggregate metrics** | Avg MFE, Avg MAE, MFE/MAE ratio, MFE capture ratio (`Actual P&L / MFE`) |
| **Report integration** | Milestones, per-strategy breakdown, trade review panel |
| **AI use case** | *"Your average MFE capture ratio is 38% — you're consistently exiting too early. Consider trailing stops."* |

### Key Formulas

```
Price MFE (Long)  = Highest Price During Trade - Entry Price
Price MAE (Long)  = Entry Price - Lowest Price During Trade
Price MFE (Short) = Entry Price - Lowest Price During Trade
Price MAE (Short) = Highest Price During Trade - Entry Price

Position MFE = Price MFE × Quantity × Contract Multiplier
Position MAE = Price MAE × Quantity × Contract Multiplier

MFE Capture Ratio = Actual Net P&L / Position MFE
```

---

## 4. SQN — System Quality Number

**Source:** Van Tharp's *Definitive Guide to Position Sizing* (2008)  
**Status:** `[ ]` Not started  
**Priority:** Medium  
**Module:** Reports / Strategy Analytics

### What It Is

SQN is a single number that rates the quality of a trading system by measuring the relationship between the average R-multiple (risk-normalized profit) and the standard deviation of R-multiples, adjusted for the number of trades. It's mathematically equivalent to the **t-test statistic** — it tells you whether your edge is statistically significant.

### Formula

```
SQN = √N × (Mean of R-multiples) / (StdDev of R-multiples)

Where:
  R-multiple = Net P&L ÷ Initial Risk Amount
  N = number of trades (capped at 100 for SQN calculation)
  Mean = average of all R-multiples
  StdDev = standard deviation of all R-multiples
```

> **Note:** Van Tharp caps N at 100 in the formula to prevent SQN from growing infinitely with trade count. The raw formula without the cap is identical to the t-test statistic.

### Interpretation Scale

| SQN Range | Rating | Meaning |
|-----------|--------|---------|
| < 0 | Losing system | Negative expectancy — losing money |
| 0 – 1.0 | Very poor | Hard to make money; high variance destroys edge |
| 1.0 – 2.0 | Below average | Marginal edge; position sizing critical |
| 2.0 – 3.0 | Average | Decent system; can be profitable with discipline |
| 3.0 – 5.0 | Good | Strong edge; can compound effectively |
| 5.0 – 7.0 | Excellent | Rare; very consistent returns |
| > 7.0 | Holy Grail | Extremely rare; near-perfect system |

### Why It Matters for Zorivest

SQN allows direct comparison between different strategies (swing vs scalp, stocks vs futures) on a normalized scale. Combined with Zorivest's AI:

- *"Your swing trading system has an SQN of 3.4 (Good), but your scalping system is at 0.8 (Very Poor). Consider dropping scalping."*
- *"Your SQN improved from 1.2 to 2.8 over the last quarter — your edge is strengthening."*

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Prerequisite** | Every trade must have a `risk_amount` field (initial risk in $) |
| **Calculation** | Python: `sqn = math.sqrt(min(n, 100)) * mean(r_multiples) / stdev(r_multiples)` |
| **Segmentation** | Calculate SQN per strategy, per timeframe, per asset class, overall |
| **Exposure** | MCP tool (`system_quality`), GUI stats dashboard, scheduled strategy report |

---

## 5. Mistake Tracking with Cost Attribution

**Source:** TJS StockTracking mistake taxonomy + behavioral trading psychology research  
**Status:** `[ ]` Not started  
**Priority:** Medium  
**Module:** Trade Logging / Journal / Reports

### What It Is

A structured system for categorizing trading errors, tracking their frequency, and calculating their dollar cost. Unlike free-form journaling, a predefined taxonomy forces honest self-assessment and enables quantitative analysis of behavioral patterns.

### TJS Default Taxonomy (12 Types)

| Code | Description | Category |
|------|-------------|----------|
| Bad Exit | Bad exit management | Execution |
| Bad Order | Bad order entry | Execution |
| Bad R/R | Bad reward-to-risk ratio | Planning |
| Bad Stop | Bad stop placement | Risk Management |
| Too Soon | Entered too soon | Timing |
| Too Late | Entered too late | Timing |
| Chart | Faulty chart pattern | Analysis |
| Fear | Fear of missing trade (FOMO) | Psychology |
| Stress | High stress level | Psychology |
| No Plan | Not in trading plan | Discipline |
| Size | Wrong contract size | Risk Management |
| No Rules | Broke multiple rules | Discipline |

### Industry Research Insights

Academic research (FINANS taxonomy, PMC4971609) identifies the most common trading error categories:

- **Slip/lapse** (61%) — Unintended actions (fat fingers, wrong symbol)
- **Situation awareness** (51%) — Misreading market context
- **Teamwork/communication** (40%) — Relevant for managed accounts
- **Decision-making** (35%) — Poor judgment under pressure

Behavioral trading psychology (ACY Education, TradethatSwing) recommends:

- **Dollar-cost attribution per mistake** — *"'Too Late' entries cost me $19,084 this month"*
- **Weekly behavioral scorecards** — Track habit formation and reduction
- **Behavioral metrics beyond mistakes:** emotional state, system adherence %, screen discipline, journal consistency
- **Top 3 recurring errors** — Focus attention on highest-impact behavioral blind spots

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Schema** | `mistake_tags[]` (multi-select from taxonomy + custom) per trade |
| **Taxonomy** | 12 defaults from TJS (user-extensible); grouped by category (Execution, Planning, Risk, Timing, Analysis, Psychology, Discipline) |
| **Cost calculation** | Auto-computed: sum of Net P&L for all trades tagged with each mistake type |
| **Reports** | Mistake frequency table, cost attribution per type, trend over time |
| **AI use case** | *"Your top 3 most expensive mistakes this month: FOMO ($4,200), Bad Exit ($2,800), Too Late ($1,900). FOMO trades have a 23% win rate vs your overall 58%."* |

---

## 6. NinjaTrader Trade Import

**Source:** TJS Import sheet + NinjaTrader export format  
**Status:** `[ ]` Not started  
**Priority:** Low — IBKR API is primary  
**Module:** Data Import

### What It Is

Import trades from NinjaTrader's CSV/Excel export files into Zorivest's trade log. NinjaTrader is a popular platform for futures trading and has a well-defined export format.

### NinjaTrader Export Format

Exported from: NinjaTrader Control Center → Executions tab → Export to CSV.

| Field | Description | Zorivest Mapping |
|-------|-------------|-----------------|
| Trade-# | Sequence number | Internal ID |
| Instrument | Symbol/contract | `symbol` |
| Account | Broker account | `account_id` |
| Strategy | NinjaScript strategy name | `entry_strategy` |
| Market pos. | Long/Short | `direction` |
| Quantity | Number of contracts/shares | `quantity` |
| Entry price | Fill price on entry | `entry_price` |
| Exit price | Fill price on exit | `exit_price` |
| Entry time | Timestamp of entry | `entry_date` + `entry_time` |
| Exit time | Timestamp of exit | `exit_date` + `exit_time` |
| Entry name | NinjaScript entry signal name | `entry_notes` |
| Exit name | NinjaScript exit signal name | `exit_notes` |
| Profit | Gross P&L | `gross_pnl` |
| Cum. profit | Running cumulative P&L | Derived |
| Commission | Trading fees | `fees` |
| MAE | Maximum adverse excursion | `mae_price` |
| MFE | Maximum favorable excursion | `mfe_price` |
| ETD | End Trade Drawdown | Derived |
| Bars | Number of bars in trade | `trade_duration` (converted) |

### Industry Context

- **TradesViz** offers real-time auto-sync with NinjaTrader via a NinjaScript indicator that pushes trades to their API automatically (no CSV export needed)
- **TradeZella** and other journals accept NinjaTrader CSV uploads with field mapping
- **NinjaTrader Developer API** (developer.ninjatrader.com) offers REST + WebSocket APIs for real-time trading data and historical trade retrieval

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Phase 1** | CSV file upload (drag-and-drop or MCP tool) with auto-detection of NinjaTrader format |
| **Phase 2** | Generic import schema — define a universal mapping layer that NinjaTrader (and all future platforms) map into |
| **Phase 3** | NinjaTrader API integration (if demand exists) for real-time sync |
| **Deduplication** | Match by instrument + entry time + quantity to prevent duplicate imports |

### Future Import Targets

| Platform | Import Type | Format | Status |
|----------|------------|--------|--------|
| NinjaTrader | Trades | CSV/Excel export | `[ ]` |
| ThinkorSwim | Trades | CSV export | `[ ]` |
| Tradovate | Trades | CSV export | `[ ]` |
| TradeStation | Trades | CSV export | `[ ]` |
| Broker PDF statements | Account balances | PDF parsing | `[ ]` |
| CSV statements | Account balances | CSV | `[ ]` |
| Image/screenshot | Trades & balances | OCR/AI vision | `[ ]` |

---

## 7. Broker Transaction Types

**Source:** TJS Brokers sheet + IBKR Reporting Guide  
**Status:** `[ ]` Not started  
**Priority:** Medium  
**Module:** Account Management / Ledger

### What It Is

Standardized transaction types for account ledger entries that categorize all non-trade account activity. This separates *trading performance* from *account cash flows*, enabling accurate reporting of actual trading edge vs account growth (which includes deposits/withdrawals/fees).

### Transaction Type Reference

| Type Code | Description | Direction | Example |
|-----------|-------------|-----------|---------|
| `opening_balance` | Starting capital | Credit | Initial account funding |
| `profit` | Trading profit (auto-linked to closed trades) | Credit | Sum of positive closed trade P&L |
| `loss` | Trading loss (auto-linked to closed trades) | Debit | Sum of negative closed trade P&L |
| `deposit` | Cash deposit | Credit | Wire transfer in, ACH deposit |
| `withdrawal` | Cash withdrawal | Debit | Wire transfer out, check |
| `data_feed` | Market data subscription fees | Debit | Monthly data subscription ($10–$150/mo) |
| `fee_other` | Platform/other fees | Debit | Inactivity fee, platform fee, exchange fees |
| `dividend` | Dividend / yield income | Credit | Stock dividend, bond coupon |
| `interest` | Interest earned or paid | Both | Margin interest (debit), cash sweep interest (credit) |
| `reconcile` | Manual balance correction | Both | Adjustment to match broker statement |
| `transfer_in` | Transfer from another account | Credit | Account-to-account transfer |
| `transfer_out` | Transfer to another account | Debit | Account-to-account transfer |
| `other` | Miscellaneous | Both | Anything not categorized above |

### IBKR Activity Statement Mapping

IBKR's Flex Statement / Activity Statement provides these sections that map to transaction types:

| IBKR Section | Zorivest Transaction Type |
|-------------|--------------------------|
| Deposits & Withdrawals | `deposit` / `withdrawal` |
| Dividends | `dividend` |
| Broker Interest Paid and Received | `interest` |
| Other Fees (Market Data, etc.) | `data_feed` / `fee_other` |
| Realized P&L | `profit` / `loss` (linked to trades) |
| Account Transfers | `transfer_in` / `transfer_out` |

### Analytical Value

- **True trading P&L** = Account growth - Deposits + Withdrawals - Dividends - Interest
- **Cost of doing business** = Sum of `data_feed` + `fee_other` + `interest` (debit)
- **Return on Invested Capital** = Trading P&L / (Opening Balance + Net Deposits)

---

## 8. Monthly P&L Calendar Report

**Source:** TJS Calendar sheet + TradesViz/Tradervue/PnLLedger  
**Status:** `[ ]` Not started  
**Priority:** Low  
**Module:** Scheduled Reports (Scheduling Module)

### What It Is

A calendar-grid view showing daily P&L with color-coded cells (green = profit, red = loss), weekly subtotals, and monthly summary. This is the most popular view in modern trade journals — every major platform (TradesViz, Tradervue, PnLLedger, profitlosscalendar.com) features it prominently.

### Industry Standard Features

| Feature | TradesViz | Tradervue | PnLLedger |
|---------|-----------|-----------|-----------|
| Daily P&L cells | ✅ Color-coded | ✅ Color-coded | ✅ Color-coded |
| Weekly summary sidebar | ✅ P&L, win rate, # trades | ✅ P&L, # trades | ✅ Totals |
| Monthly/yearly toggle | ✅ + yearly heatmap | ✅ Monthly only | ✅ All-time dashboard |
| Drill-down on click | ✅ Day explore tab | ✅ Journal for that day | ✅ Journal view |
| Economic events overlay | ✅ Earnings, IPOs | ❌ | ❌ |
| Aggregate vs per-trade P&L toggle | ✅ | ✅ | ❌ |
| PDF/CSV export | ✅ | ✅ | ✅ |

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Trigger** | Scheduler: auto-generate on 1st of each month (or on-demand via MCP) |
| **Content** | Daily P&L grid, weekly subtotals, monthly total (Gross/Net), trade count, win rate, avg P&L/day, best/worst day, month-over-month comparison |
| **Output** | Report table → email template; also available as GUI tab |
| **AI narrative** | *"February was your best month in 3 months: $4,200 net. Tuesdays were your strongest day (+$2,100). You had 2 days with >3% drawdown — both on Fridays."* |
| **Yearly heatmap** | 365-cell grid with color intensity by daily P&L (inspired by TradesViz yearly view) |

---

## 9. Strategy Breakdown Report

**Source:** TJS StockTracking/StockFilter + BacktestBase/ORBSetups  
**Status:** `[ ]` Not started  
**Priority:** Low  
**Module:** Scheduled Reports (Scheduling Module)

### What It Is

A performance analytics engine that slices trade data across multiple dimensions, computing win rate, payoff ratio, expectancy, and frequency for each segment. This answers: *"Which specific type of trade is making me money, and which is losing?"*

### Breakdown Dimensions (8 from TJS + extensions)

| Dimension | Example Values | Key Question |
|-----------|---------------|-------------|
| **Entry Strategy** | Buy, Sell, Breakout, Breakdown, custom... | *Which setup types are profitable?* |
| **Direction** | Trend, Counter-Trend, Flat/Sideways | *Am I better trading with or against the trend?* |
| **Trade Category** | Scalp, Day, Swing, Position, Investment | *Which time horizon suits me?* |
| **Chart Timeframe** | 1Min, 5Min, 15Min, 1H, Daily, Weekly | *Which chart timeframe produces best entries?* |
| **Time of Day** | Pre-market, Morning, Midday, Afternoon, After-hours | *When am I sharpest?* |
| **Day of Week** | Monday through Sunday | *Are Fridays killing me?* |
| **Exit Strategy** | Target, Stop, Trailing, Time-based, Discretionary | *How am I leaving most trades?* |
| **Long vs Short** | Long, Short | *Do I have a directional bias?* |

### Metrics Per Dimension

Each dimension computes a full analytics table:

| Metric | Formula |
|--------|---------|
| Win # / Loss # | Count of W/L trades in segment |
| Win P&L / Loss P&L | Sum of P&L for W/L trades |
| Win Avg / Loss Avg | Mean P&L for W/L trades |
| Win % | Win # / Total # |
| Payoff Ratio | Win Avg / \|Loss Avg\| |
| Expectancy | (Win% × Win Avg) - (Loss% × \|Loss Avg\|) |
| Frequency | Segment # / Total # (what % of trades fall here) |
| SQN | System Quality Number for this segment |

### Industry Best Practices

- **Multi-level grouping** (Freqtrade): Group by enter_tag × exit_tag × pair for granular analysis
- **Long vs Short sub-breakdowns** within each dimension (ORBSetups, BacktestBase)
- **Visual P&L over time charts** per strategy segment
- **Sortino / Calmar ratios** for risk-adjusted comparison between strategies
- **Side-by-side comparison mode** (BacktestBase): Compare two strategies directly

### Zorivest Implementation Plan

| Aspect | Detail |
|--------|--------|
| **Trigger** | Scheduler: weekly or monthly (configurable); also on-demand via MCP |
| **Content** | Per-dimension tables with all metrics above; top/bottom performers highlighted; AI narrative |
| **Output** | Report table → email template; GUI analytics tab |
| **MCP tool** | `strategy_breakdown(dimension, date_range, account_id)` |
| **AI narrative** | *"Your Swing trades have a 68% win rate and 2.1 payoff ratio (Expectancy: $480/trade). Your Scalps have a 52% win rate but only 0.8 payoff ratio (Expectancy: -$12/trade). Recommendation: increase Swing allocation, reduce Scalp frequency."* |

---

---

## 10. Platform Integrations

> Zorivest can consume data from external trading platforms via their MCP servers or REST APIs. This section tracks each platform's capabilities and what Zorivest would consume.

### 10a. Alpaca (Official MCP + REST API)

**Type:** Official MCP Server + REST API  
**Repo:** [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) (517★, MIT)  
**Transport:** stdio (local) or streamable-http (remote)  
**Auth:** API Key + Secret Key, paper trading ($100K simulated) or live  
**Status:** `[ ]` Not started

**MCP Tools Available (~40 tools):**

| Category | Tools | Zorivest Consumes |
|----------|-------|-------------------|
| **Account** | `get_account_info`, `get_all_positions`, `get_open_position` | Balance, buying power, margin → Account snapshot |
| **Portfolio** | `get_portfolio_history(timeframe, period)` | Equity + P&L over time → Account balance history |
| **Orders** | `get_orders`, `place_stock_order`, `place_crypto_order`, `place_option_order`, `cancel_all_orders`, `cancel_order_by_id`, `close_position`, `close_all_positions`, `exercise_options_position` | Order history → Trade log import |
| **Stock Data** | `get_stock_bars`, `get_stock_quotes`, `get_stock_trades`, `get_stock_latest_bar`, `get_stock_latest_quote`, `get_stock_latest_trade`, `get_stock_snapshot` | OHLCV bars → MFE/MAE calc, daily brief |
| **Crypto Data** | `get_crypto_bars`, `get_crypto_quotes`, `get_crypto_trades`, `get_crypto_latest_*`, `get_crypto_snapshot`, `get_crypto_latest_orderbook` | Crypto market data → Portfolio valuation |
| **Options Data** | `get_option_contracts`, `get_option_latest_quote`, `get_option_snapshot` | Greeks, IV → Options analysis |
| **Corporate Actions** | `get_corporate_actions(ca_types, symbols, start, end)` | Dividends, splits, earnings → Daily brief enrichment |
| **Market Calendar** | `get_calendar`, `get_clock` | Trading hours → Scheduler awareness |
| **Watchlists** | `create_watchlist`, `get_watchlists`, `update_watchlist_by_id`, `add/remove_asset`, `delete_watchlist` | Watchlist sync → Zorivest watchlist module |
| **Assets** | `get_asset`, `get_all_assets(status, class, exchange)` | Asset metadata → Contract specifications |

**Key Value for Zorivest:**
- `get_portfolio_history` → account balance time series (no manual entry needed)
- `get_orders` → auto-import closed trades with timestamps, fills, commissions
- `get_stock_snapshot` → real-time data for daily brief + MFE/MAE calculation
- `get_corporate_actions` → earnings/dividend calendar for trade planning

---

### 10b. Tradier (Official MCP)

**Type:** Official MCP Server (cloud-hosted)  
**Docs:** [docs.tradier.com/docs/tradier-mcp](https://docs.tradier.com/docs/tradier-mcp)  
**Transport:** Streamable HTTP at `https://mcp.tradier.com/mcp`  
**Auth:** API Key via header, paper/live toggle  
**Status:** `[ ]` Not started

**MCP Tools Available (~21 tools):**

| Tool | Purpose | Zorivest Consumes |
|------|---------|-------------------|
| `get_user_profile` | Account details, profile settings | Account registration |
| `get_account_balances` | Current balances | Balance snapshot |
| `get_account_historical_balances` | Balance over time | Account balance history |
| `get_positions` | Symbol, qty, cost basis, current value | Holdings → Portfolio view |
| `get_orders` | Order history with status | Trade log import |
| `get_market_quotes` | Last price, change, volume, bid/ask | Market data for daily brief |
| `get_gainloss` | Realized + unrealized P&L | P&L reporting |
| `get_account_history` | Trades, dividends, options, transfers | Transaction ledger |
| `get_historical_data` | Daily/weekly/monthly price bars | MFE/MAE calculation |
| `get_options_chain` | Options chain with Greeks | Options analysis |
| `get_watchlists` / `add_to_watchlist` | Watchlist management | Watchlist sync |
| `get_market_calendar` | Trading days and holidays | Scheduler |
| `place_equity_order` | Stock orders | — (execution layer, not consumed) |
| `place_option_order` | Single-leg options | — |
| `place_multileg_option_order` | Spreads (2–4 legs) | — |
| `place_oco_order` | One-Cancels-Other | — |
| `place_oto_order` | One-Triggers-Other | — |
| `place_otoco_order` | One-Triggers-OCO bracket | — |
| `cancel_order` | Cancel by ID | — |
| `search_tradier_docs` | Built-in API documentation search | Context for AI assistant |

**Key Value for Zorivest:**
- `get_account_historical_balances` → balance time series without manual entry
- `get_gainloss` → realized/unrealized P&L for performance reporting
- `get_account_history` → full transaction history (dividends, fees, transfers) → maps to broker transaction types
- Cloud-hosted MCP → no local server needed, simplest integration

---

### 10c. Interactive Brokers — Community MCP Servers

**Type:** Community-built MCP (3 implementations, all MIT)  
**Status:** `[ ]` Not started — evaluate alongside existing IBKR API integration

| Implementation | Repo | Approach | Stars |
|---------------|------|----------|-------|
| **rcontesti/IB_MCP** | [GitHub](https://github.com/rcontesti/IB_MCP) | Web API (no TWS needed), Docker Compose, FastMCP + FastAPI | 96★ |
| **code-rabi/interactive-brokers-mcp** | [playbooks.com](https://playbooks.com/mcp/code-rabi/interactive-brokers-mcp) | Account data, market data, trade execution, Flex Queries. Alpha state. | — |
| **ibkr-mcp** | [PyPI](https://pypi.org/project/ibkr-mcp/) | `pip install ibkr-mcp`. Portfolio, options analysis, risk monitoring, news. v0.2.5 | — |

**rcontesti/IB_MCP (recommended)** uses the IBKR Web API (standalone, no TWS dependency). Architecture:
- `api_gateway` container → runs IB Client Portal Gateway with auto-tickler (session keep-alive every 60s)
- `mcp_server` container → FastMCP server with manually-built routers for IB endpoints
- Requires browser login for auth, then exposes `http://localhost:5002/mcp/`

**Relevance to Zorivest:** Zorivest already plans direct IBKR API integration. The community MCP servers are useful as *reference implementations* for endpoint mapping, but Zorivest's own IBKR integration should be more tightly controlled. The MCP approach could be used as a *secondary access path* for AI assistants to query IBKR data.

---

### 10d. MetaTrader 5 MCP

**Type:** Community MCP Server  
**Repo:** [Qoyyuum/mcp-metatrader5-server](https://github.com/Qoyyuum/mcp-metatrader5-server)  
**Docs:** [mcp-metatrader5-server.readthedocs.io](https://mcp-metatrader5-server.readthedocs.io/)  
**Install:** `pip install mcp-metatrader5-server` / `uv run mt5mcp`  
**Transport:** stdio or HTTP (`MT5_MCP_TRANSPORT=http`)  
**Constraint:** ⚠️ Windows-only (requires MT5 terminal running)  
**Status:** `[ ]` Not started

**MCP Tools Available:**

| Tool | Purpose | Zorivest Consumes |
|------|---------|-------------------|
| `initialize(path)` | Connect to MT5 terminal | Session setup |
| `login(account, password, server)` | Authenticate | — |
| `get_symbols()` | Available instruments | Asset registry |
| `copy_rates_from_pos(symbol, timeframe, count)` | Historical OHLCV bars | Market data, MFE/MAE |
| `order_send(...)` | Place trades | — (execution only) |
| `positions_get()` | Open positions | Holdings → Portfolio |
| Historical orders/deals | Trading history | Trade log import |

**Key Value for Zorivest:** MT5 is the dominant platform for forex and CFD traders. Zorivest could consume MT5 trade history for journaling. However, the Windows-only requirement and need for a running MT5 terminal limits usage to desktop-only scenarios.

---

### 10e. Tradernet / Freedom24 (REST API + WebSocket)

**Type:** REST API + WebSocket (no MCP server exists yet)  
**Docs:** [freedom24.com/tradernet-api](https://freedom24.com/tradernet-api)  
**Auth:** Login/Password session-based  
**Status:** `[ ]` Not started

**API Capabilities:**

| Endpoint Category | Capabilities |
|-------------------|-------------|
| **Auth** | Login, session management |
| **Securities** | Get lists of available securities |
| **Quotes** | Real-time quote subscriptions via WebSocket |
| **Market Depth** | Level 2 data via WebSocket |
| **Orders** | Place, modify, cancel orders |
| **Portfolio** | Positions, balances |
| **Reports** | Transaction history, trade reports |
| **Reference** | Currencies, trading platforms, office list |

**Python SDK:** Tradernet provides an official Python SDK for API access.

**Key Value for Zorivest:** Freedom24 is popular in Europe/CIS for stock and options trading. No MCP server exists — Zorivest could build a lightweight adapter to consume account data and trade history via the REST API. This would be a Phase 3+ integration.

---

### 10f. OpenAlgo (Unified Broker API)

**Type:** Open-source REST API gateway (Flask + React)  
**Repo:** [marketcalls/openalgo](https://github.com/marketcalls/openalgo) (AGPL-3.0)  
**Docs:** [docs.openalgo.in](https://docs.openalgo.in/)  
**Status:** `[ ]` Not started — primarily India-focused

**What It Is:**

OpenAlgo is a unified API layer across **25+ Indian brokers** (Zerodha, Angel One, Dhan, Upstox, Fyers, Flattrade, etc.). Write once, trade across any supported broker.

**Unified REST API (`/api/v1/`):**

| Endpoint | Purpose |
|----------|---------|
| Place / Modify / Cancel orders | Trade execution |
| Fetch positions, holdings, funds | Account data |
| Orderbook and tradebook | Trade history |
| Real-time and historical market data | Market data |

**Platform Integrations:** TradingView (webhooks), Amibroker (AFL HTTP calls), MetaTrader, N8N, Python SDK, Excel, Google Sheets

**SDKs:** Python (`openalgo` on PyPI), Node.js, Go, .NET, Rust, Java

**Key Value for Zorivest:** OpenAlgo's architecture (unified API → multiple brokers) is exactly the pattern Zorivest should follow for its generic import layer. If Zorivest expands to Indian markets, OpenAlgo could be consumed as a broker gateway. The API design is a useful reference for Zorivest's own multi-broker abstraction.

---

### 10g. QuantConnect MCP (Backtesting & Strategy)

**Type:** Official MCP Server for QuantConnect cloud platform  
**Repo:** [QuantConnect/mcp-server](https://github.com/QuantConnect/mcp-server)  
**Also:** [taylorwilsdon/quantconnect-mcp](https://pypi.org/project/quantconnect-mcp/) (community, v0.3.5)  
**Status:** `[ ]` Not started

**MCP Tools Available:**

| Tool | Purpose | Zorivest Consumes |
|------|---------|-------------------|
| `create_project` / `read_project` / `list_projects` | Manage algo projects | — |
| `create_file` / `read_file` / `update_file` | Edit strategy code | — |
| `compile_project` | Compile strategy | — |
| `create_backtest` | Run backtest | Backtest results |
| `read_backtest` | Get backtest results (P&L, metrics) | Performance metrics → Strategy comparison |
| `list_backtests` | List all backtests | History |
| `read_backtest_chart` | Get equity curves | Visualization |
| `estimate_optimization_time` | Estimate optimization duration | — |
| `deploy_live` / `read_live` | Live trading management | — |

**Key Value for Zorivest:** This bridges Zorivest (journaling/reflection) with QuantConnect (strategy development/backtesting). A trader could:
1. Journal trades in Zorivest → identify pattern
2. Ask AI to write a QuantConnect strategy based on the pattern
3. Backtest via MCP → review results in Zorivest
4. Deploy live → journal live trades back in Zorivest

This creates a **development → test → deploy → journal → improve** feedback loop.

---

### 10h. FinAgent Orchestration (Research Framework)

**Type:** Academic multi-agent framework for algorithmic trading  
**Paper:** [arXiv:2512.02227](https://arxiv.org/pdf/2512.02227) (Dec 2025)  
**Docs:** [finagent-orchestration.readthedocs.io](https://finagent-orchestration.readthedocs.io/)  
**Repo:** [Open-Finance-Lab/FinAgent-Orchestration](https://github.com/Open-Finance-Lab/FinAgent-Orchestration)  
**Status:** `[ ]` Research reference only

**What It Is:**

An orchestration framework that maps each component of an automated trading system to specialized AI agents, organized in pools:

| Agent Pool | Purpose | Zorivest Parallel |
|------------|---------|------------------|
| **Data Agent Pool** | Market data ingestion, cleaning, feature engineering | Market data module |
| **Planner Agent** | Strategy selection, trade plan generation | Trade planning wizard |
| **Portfolio Agent** | Position sizing, risk allocation, portfolio construction | Position calculator |
| **Execution Agent** | Order routing, execution quality, slippage management | Broker integration |
| **Optimizer** | Strategy parameter tuning, walk-forward optimization | — (future) |

**Architecture:**
- Pipeline scheduling with optimization loops
- Phase 1: In-sample training (World Model)
- Phase 2: Out-of-sample inference
- Paper trading + backtesting modes
- Agent integration demos

**Related Work:**
- **FinAgent** (arXiv:2402.18485) — Multimodal foundation agent for trading with tool augmentation
- **FinVerse** (arXiv:2406.06379) — Agent system with 600+ financial APIs

**Key Value for Zorivest:** FinAgent's agent pool architecture maps well to Zorivest's MCP tool design. Each Zorivest MCP tool (`trade_plan`, `position_calc`, `risk_check`, etc.) corresponds to a FinAgent pool. The orchestration pattern (data → plan → size → execute → review) aligns with Zorivest's user flow (daily brief → trade plan → position calc → execute → journal → AI review). This validates Zorivest's architecture as being aligned with academic cutting-edge research.

---

### 10i. Additional MCP Servers Discovered

| Server | Repo/Docs | Type | Coverage |
|--------|-----------|------|----------|
| **Tradovate MCP** | [alexanimal/tradovate-mcp-server](https://github.com/alexanimal/tradovate-mcp-server) | Community | Futures: contracts, positions, orders, accounts |
| **Trade-It MCP** | [Trade-Agent/trade-agent-mcp](https://github.com/Trade-Agent/trade-agent-mcp) | Multi-broker | Stocks, crypto, options via remote MCP (`mcp.tradeit.app`) |
| **QuantInsti MCP** | [quantinsti.com](https://www.quantinsti.com/articles/mcp-server-trading-python-ai/) | Tutorial | Python MCP for IBKR — English-to-order execution |

---

## Integration Priority

| Priority | Platform | Why |
|----------|----------|-----|
| 🔴 **P0** | IBKR (direct API) | Primary broker, already planned |
| 🟡 **P1** | Alpaca MCP | Broad coverage, paper trading, well-maintained official server |
| 🟡 **P1** | Tradier MCP | Cloud-hosted (simplest integration), gain/loss + balance history |
| 🟢 **P2** | QuantConnect MCP | Strategy backtesting feedback loop |
| 🟢 **P2** | NinjaTrader import | CSV import for futures traders |
| ⚪ **P3** | MetaTrader 5 MCP | Forex/CFD traders, Windows-only limitation |
| ⚪ **P3** | Tradernet/Freedom24 | European market, no MCP yet |
| ⚪ **P3** | OpenAlgo | Indian market, reference architecture |
| ⚪ **P3** | FinAgent | Academic reference only |

---




