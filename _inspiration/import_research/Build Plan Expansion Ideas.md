# Build Plan Expansion: Research-Backed Implementation Ideas for Zorivest

> Extracted from analysis of [Local Trading Journal Software Search](file:///p:/zorivest/_inspiration/import_research/Local%20Trading%20Journal%20Software%20Search.md) and [Retail Trading Platform & Broker Analysis](file:///p:/zorivest/_inspiration/import_research/Retail%20Trading%20Platform%20%26%20Broker%20Analysis.md). Each point includes implementation approach, architectural details, challenges, and relevant references.

---

## Table of Contents

1. [IBroker Interface Pattern](#1-ibroker-interface-pattern)
2. [Unified Adapter Layer (CCXT-style)](#2-unified-adapter-layer-ccxt-style)
3. [Round-Trip Execution Matching](#3-round-trip-execution-matching)
4. [Tax-Lot Accounting (FIFO/LIFO/HIFO)](#4-tax-lot-accounting-fifolifohifo)
5. [CUSIP/ISIN/SEDOL → Ticker Resolution](#5-cusipisinsedol--ticker-resolution)
6. [Smart Deduplication](#6-smart-deduplication)
7. [MFE/MAE/BSO Auto-Enrichment](#7-mfemaebso-auto-enrichment) ← *merged with TJS §3*
8. [Multi-Leg Options Grouping](#8-multi-leg-options-grouping)
9. [Transaction Ledger & Fee Cataloging](#9-transaction-ledger--fee-cataloging) ← *merged with TJS §7*
10. [Execution Quality Score](#10-execution-quality-score)
11. [PFOF Impact Analysis](#11-pfof-impact-analysis)
12. [Multi-Persona AI Review](#12-multi-persona-ai-review)
13. [Expectancy & Edge Dashboard](#13-expectancy--edge-dashboard) ← *merged with TJS §1*
14. [Drawdown Probability Table](#14-drawdown-probability-table) ← *new from TJS §2*
15. [SQN — System Quality Number](#15-sqn--system-quality-number) ← *new from TJS §4*
16. [Bidirectional Trade-Journal Linking](#16-bidirectional-trade-journal-linking)
17. [Mistake Tracking with Cost Attribution](#17-mistake-tracking-with-cost-attribution) ← *new from TJS §5*
18. [Broker CSV Import Framework](#18-broker-csv-import-framework) ← *consolidated §15-19 + NinjaTrader*
19. [PDF Broker Statement Extraction](#19-pdf-broker-statement-extraction)
20. [Monthly P&L Calendar Report](#20-monthly-pl-calendar-report) ← *new from TJS §8*
21. [Strategy Breakdown Report](#21-strategy-breakdown-report) ← *new from TJS §9*
22. ["Cost of Free" Report](#22-cost-of-free-report)
23. [Broker Constraint Modeling](#23-broker-constraint-modeling)
24. [Alpaca Direct API Integration](#24-alpaca-direct-api-integration) ← *new*
25. [Tradier Direct API Integration](#25-tradier-direct-api-integration) ← *new*
26. [Bank Account Statement Import](#26-bank-account-statement-import) ← *new from banking research*

---

## 1. IBroker Interface Pattern

**Source:** LEAN Engine (QuantConnect) `IBrokerage` interface, TradeTally parser architecture  
**Priority:** P0 — Foundation layer, must be built first  
**Module:** `core/brokers/`

### Implementation Approach

Define a Python abstract base class (`IBroker`) that every broker integration must implement. This ensures all broker-specific code is isolated behind a clean contract, keeping journal/analytics logic completely decoupled.

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

class IBroker(ABC):
    """Abstract interface that all broker integrations must implement."""

    @abstractmethod
    async def get_account(self) -> AccountSnapshot:
        """Return current balances, buying power, margin."""

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Return all open positions."""

    @abstractmethod
    async def get_trade_history(
        self, start: datetime, end: datetime
    ) -> List[RawExecution]:
        """Return raw executions within date range."""

    @abstractmethod
    async def get_balance_history(
        self, start: datetime, end: datetime
    ) -> List[BalanceSnapshot]:
        """Return account balance snapshots over time."""

    @abstractmethod
    def parse_csv(self, file_path: str) -> List[RawExecution]:
        """Parse a broker-specific CSV export into raw executions."""

    @abstractmethod
    def get_broker_model(self) -> BrokerModel:
        """Return broker constraints (fees, margin rules, trading hours)."""
```

### Architectural Details

- **Directory structure:** `core/brokers/ibkr.py`, `core/brokers/alpaca.py`, `core/brokers/tradier.py`, etc.
- **Factory pattern:** `BrokerFactory.create("ibkr", config)` dynamically instantiates the correct broker — mirrors LEAN's `IBrokerageFactory` and `BrokerageSetupHandler.cs`
- **Dual modes per broker:** Each broker supports both API mode (live data) and CSV mode (file import), sharing the same output type (`RawExecution`)
- **BrokerModel dataclass:** Encapsulates fee schedules, margin requirements, trading hours, PDT rules — directly inspired by LEAN's `DefaultBrokerageModel.cs`

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Brokers change their API/CSV formats without warning (Ghostfolio's #1 problem) | Version-stamp each parser; add format detection headers; integration tests with sample CSVs |
| Options/futures have contract multipliers, special symbology per broker | Normalize all symbols to OCC-standard format during ingestion |
| Rate limiting across different broker APIs | Per-broker rate limiter with exponential backoff in base class |
| Auth mechanisms vary wildly (API keys, OAuth, session cookies) | Auth adapter pattern within each broker implementation |

### Reference Implementations

- [QuantConnect/Lean `IBrokerage` interface](https://github.com/QuantConnect/Lean/blob/master/Common/Interfaces/IBrokerageFactory.cs)
- [TradeTally parser modules](https://github.com/GeneBO98/tradetally) — `backend/src/services/parsers/`

---

## 2. Unified Adapter Layer (CCXT-style)

**Source:** Freqtrade's CCXT abstraction, OpenAlgo unified API, Hummingbot connectors  
**Priority:** P0 — Build alongside IBroker interface  
**Module:** `core/adapters/`

### Implementation Approach

Create a middleware layer that normalizes the output of all `IBroker` implementations into a single canonical schema. This is the "translator" between broker-specific data and Zorivest's internal data model.

```python
class UnifiedTradeSchema:
    """Canonical trade record — all broker data normalizes to this."""
    id: str                    # Zorivest-internal UUID
    broker: str                # "ibkr", "alpaca", "tradier"
    account_id: str
    symbol: str                # Normalized (e.g., "AAPL", not CUSIP)
    asset_class: AssetClass    # EQUITY, OPTION, FUTURE, FOREX, CRYPTO
    direction: Direction       # LONG, SHORT
    quantity: Decimal
    entry_price: Decimal
    exit_price: Optional[Decimal]
    entry_time: datetime       # UTC-normalized
    exit_time: Optional[datetime]
    commissions: Decimal
    fees: Decimal              # Non-commission fees (routing, exchange, etc.)
    currency: str              # ISO 4217
    contract_multiplier: Decimal  # 1 for stocks, 100 for US options, etc.
    raw_data: dict             # Preserved original broker data for audit
```

### Architectural Details

- **Adapter per broker:** Each adapter maps broker-specific field names → `UnifiedTradeSchema` fields
- **Currency normalization:** Convert all amounts to base currency using ECB/IBKR FX rates at execution timestamp
- **Timezone normalization:** All timestamps converted to UTC on ingestion — use `pytz` or `zoneinfo` with broker-specific timezone mappings
- **Instrument resolver:** Before storing, resolve any CUSIP/ISIN/SEDOL to standard ticker (see §5)

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Partial fills — one order → multiple executions | Aggregate by order ID; maintain `partial_fill_group_id` |
| Broker CSV headers change across versions | Dynamic header detection + fallback mapping dictionary |
| Multi-currency accounts (IBKR has ~27 currencies) | Store original currency alongside converted base amount |
| Options symbology differs per broker | Parse to OCC standard: `SYMBOL YYMMDD C/P STRIKE` |

---

## 3. Round-Trip Execution Matching

**Source:** TradeTally's round-trip detection, TradeNote's date-locking, Portfolio Performance's lot matching  
**Priority:** P0 — Core import pipeline stage  
**Module:** `core/matching/`

### Implementation Approach

The matching engine converts raw executions into completed "round-trip" trades by maintaining a running inventory of open lots per symbol. The algorithm processes executions chronologically:

```
Algorithm: Round-Trip Matcher
Input: sorted list of RawExecution[] for a single account+symbol

1. Initialize open_lots = []  (priority queue by entry_time)
2. For each execution:
   a. If OPENING (buy for long / sell-short for short):
      → Push {qty, price, time, fees} onto open_lots
   b. If CLOSING (sell for long / buy-to-cover for short):
      → Pop lots from open_lots using selected method (FIFO/LIFO/HIFO)
      → Match closing qty against lot qty:
         - If closing_qty == lot_qty → complete match, emit Trade
         - If closing_qty < lot_qty → partial match, split lot
         - If closing_qty > lot_qty → match multiple lots (aggregate)
      → Calculate P&L: (exit_price - entry_price) × qty × multiplier - fees
      → Emit completed Trade record
3. Remaining open_lots = open positions
```

### Architectural Details

- **Disposition detection:** Determine if execution opens or closes a position by checking current inventory sign. If `current_long_qty > 0` and a `SELL` arrives, it's a close. If `current_long_qty == 0` and a `SELL` arrives, it's a short open.
- **Multi-fill aggregation:** Group partial fills by order ID → compute volume-weighted average price (VWAP) for the combined fill
- **Options exercise/assignment:** Special handling for options that expire ITM — generate synthetic closing execution at strike price
- **Corporate actions:** Stock splits require retroactive adjustment of historical lot prices/quantities

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Same symbol, different asset classes (stock vs option on same underlying) | Disambiguate by full OCC symbol, not just ticker |
| Short positions covering through multiple buys across days | Maintain running lot inventory across import batches, not per-CSV |
| Options expiration generating synthetic trades | Detect missing closing executions for expired options; generate synthetic closings |
| Wash sale rule detection (30-day lookback) | Track sold lots for 30 days; flag repurchase within window |
| Reversals (long → flat → short in one sequence of fills) | Process fills one-by-one; detect when inventory crosses zero |

---

## 4. Tax-Lot Accounting (FIFO/LIFO/HIFO)

**Source:** RP2 library (FIFO/LIFO/HIFO with IRS Form 8949 output), Portfolio Performance  
**Priority:** P1 — Required for tax estimator module  
**Module:** `core/accounting/`

### Implementation Approach

Each open lot is stored as a record with `{symbol, quantity, cost_basis, open_date, broker}`. When a closing execution arrives, the accounting method selects which lot(s) to match:

| Method | Selection Rule | Tax Advantage |
|--------|---------------|--------------|
| **FIFO** | Oldest lot first | Default IRS method; simple audit trail |
| **LIFO** | Newest lot first | Maximizes short-term losses for tax harvesting |
| **HIFO** | Highest cost-basis lot first | Minimizes realized gains (best tax optimization) |
| **Specific ID** | User-selected lot | Maximum control; requires broker support |

### Architectural Details

```python
class TaxLotManager:
    def __init__(self, method: AccountingMethod = AccountingMethod.FIFO):
        self.open_lots: Dict[str, List[TaxLot]] = defaultdict(list)
        self.method = method

    def add_lot(self, lot: TaxLot):
        self.open_lots[lot.symbol].append(lot)

    def close_lots(self, symbol: str, qty: Decimal, close_price: Decimal,
                   close_date: datetime) -> List[ClosedLot]:
        lots = self._sort_lots(symbol)
        closed = []
        remaining_qty = qty
        for lot in lots:
            if remaining_qty <= 0:
                break
            matched_qty = min(lot.remaining_qty, remaining_qty)
            gain = (close_price - lot.cost_basis) * matched_qty * lot.multiplier
            holding_period = (close_date - lot.open_date).days
            closed.append(ClosedLot(
                lot=lot, matched_qty=matched_qty, gain=gain,
                term="long" if holding_period > 365 else "short"
            ))
            lot.remaining_qty -= matched_qty
            remaining_qty -= matched_qty
        return closed

    def _sort_lots(self, symbol: str) -> List[TaxLot]:
        if self.method == AccountingMethod.FIFO:
            return sorted(self.open_lots[symbol], key=lambda l: l.open_date)
        elif self.method == AccountingMethod.LIFO:
            return sorted(self.open_lots[symbol], key=lambda l: l.open_date, reverse=True)
        elif self.method == AccountingMethod.HIFO:
            return sorted(self.open_lots[symbol], key=lambda l: l.cost_basis, reverse=True)
```

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Wash sale rule: repurchasing within 30 days of selling at a loss | Track 61-day window (30 before + 30 after); adjust cost basis of replacement lot |
| Corporate actions (splits, mergers) alter cost basis retroactively | Corporate action handler adjusts all affected open lots |
| Different accounting methods per account (IRS allows per-account selection) | Store method preference per account in settings |
| Options exercise converts to stock position with adjusted cost basis | Exercise handler: `stock_cost_basis = strike + option_premium_paid` |

### Reference Implementations

- [RP2](https://github.com/eprbell/rp2) — Python FIFO/LIFO/HIFO with IRS Form 8949, transaction auditing
- [capitalg](https://github.com/dleber/capitalg) — Long/short-term gain separation with audit trail

---

## 5. CUSIP/ISIN/SEDOL → Ticker Resolution

**Source:** TradeTally (Finnhub + Gemini AI), OpenFIGI API  
**Priority:** P1 — Required for CSV import from Schwab, European brokers  
**Module:** `core/identifiers/`

### Implementation Approach

Build a resolver chain that tries multiple services in priority order:

```
Resolution Chain:
1. Local cache (SQLite lookup table of known mappings)
2. OpenFIGI API (free, rate-limited — 25 req/min unauthenticated, higher with API key; supports CUSIP/ISIN/SEDOL/FIGI)
3. Finnhub symbol search (free tier: 60 calls/min)
4. Fallback: AI inference (use LLM to guess ticker from context — TradeTally approach)
```

### OpenFIGI Integration

OpenFIGI (Bloomberg's open API) is the primary resolver. It's free but **rate-limited** (see [API docs](https://www.openfigi.com/api/documentation)), supports batch mapping of up to 100 identifiers per request, and handles all major identifier types. Build a durable local cache + retry queue + background backfill to stay within limits:

```python
import httpx

async def resolve_identifiers(identifiers: list[dict]) -> list[dict]:
    """Resolve CUSIP/ISIN/SEDOL to ticker via OpenFIGI."""
    # Each identifier: {"idType": "ID_CUSIP", "idValue": "037833100"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openfigi.com/v3/mapping",
            json=identifiers,
            headers={"X-OPENFIGI-APIKEY": settings.openfigi_key}
        )
    return resp.json()  # Returns ticker, exchange, security type
```

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Same CUSIP can map to multiple securities across exchanges | Use `exchCode` filter to narrow to user's broker's primary exchange |
| Delisted securities have no current ticker | Store historical CUSIP→ticker mappings; flag as delisted |
| Options have OCC symbology, not CUSIPs | Options bypass identifier resolution; parse OCC format directly |
| Rate limiting on free APIs | Local cache first; batch 100 per OpenFIGI call; respect 25 req/min free tier |

---

## 6. Smart Deduplication

**Source:** TradeNote's date-locking, TradeTally duplicate detection  
**Priority:** P1 — Critical for reliable imports  
**Module:** `core/import/dedup.py`

### Implementation Approach

Two-layer deduplication: exact match prevention and fuzzy match detection.

**Layer 1 — Exact Match (hash-based):**
```python
def compute_execution_hash(exec: RawExecution) -> str:
    """Deterministic hash from immutable execution properties."""
    key = f"{exec.broker}|{exec.account_id}|{exec.symbol}|"
    key += f"{exec.timestamp.isoformat()}|{exec.quantity}|"
    key += f"{exec.price}|{exec.side}"
    return hashlib.sha256(key.encode()).hexdigest()
```
Store all hashes in a `dedup_hashes` table. Reject any execution whose hash already exists.

**Layer 2 — Fuzzy Match (tolerance-based):**
Detect "near-duplicates" caused by timestamp rounding, price formatting differences, or fee adjustments:
```python
def is_fuzzy_duplicate(new: RawExecution, existing: List[RawExecution]) -> bool:
    for ex in existing:
        if (ex.symbol == new.symbol and
            abs(ex.timestamp - new.timestamp) < timedelta(seconds=5) and
            abs(ex.quantity - new.quantity) < 0.01 and
            abs(ex.price - new.price) < 0.005):
            return True
    return False
```

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Same trade appears in multiple CSV exports (overlapping date ranges) | Hash-based exact dedup catches this |
| Broker reformats timestamps (e.g., seconds → milliseconds) | Normalize all timestamps to second precision before hashing |
| Fee corrections: same trade re-appears with adjusted commission | Match on core fields (symbol/time/qty/price), update fees if changed |
| Incremental imports: user imports Jan-Mar, then Jan-Jun | Use idempotency hash + broker execution ID + bounded lookback window (30 days); do NOT rely on monotonic timestamp cutoff — late broker corrections and out-of-order imports require hash-based dedup, not timestamp ordering |

---

## 7. MFE/MAE/BSO Auto-Enrichment

**Source:** TJS StockTradingLog columns + TradeNote auto-calc + Tradervue/Trademetria + TraderSync  
**Priority:** P1 — High-value auto-enrichment  
**Module:** `core/enrichment/excursions.py`

> **Merged from:** TJS §3 (MFE/MAE/BSO definition, formulas, schema) + Expansion §7 (auto-calculation from bar data).
>
> Three metrics measure trade execution quality:
> - **MFE** (Maximum Favorable Excursion) — *"How much was this trade up at its best?"*
> - **MAE** (Maximum Adverse Excursion) — *"How far did it go against me?"*
> - **BSO** (Best Scale-Out) — *"What was the best exit price I could have gotten?"*
>
> **Schema additions:** `mfe_price`, `mae_price`, `bso_price`, `mfe_dollars`, `mae_dollars`, `capture_ratio` on trade record.
>
> **Key formulas:**
> ```
> Price MFE (Long)  = Highest Price During Trade - Entry Price
> Price MAE (Long)  = Entry Price - Lowest Price During Trade
> Position MFE = Price MFE × Quantity × Contract Multiplier
> MFE Capture Ratio = Actual Net P&L / Position MFE
> ```
>
> **Aggregate metrics:** Avg MFE, Avg MAE, MFE/MAE ratio, MFE capture ratio per strategy.
>
> **AI use case:** *"Your average MFE capture ratio is 38% — you're consistently exiting too early. Consider trailing stops."*

### Implementation Approach

Upon import, for each completed trade, query historical bar data from the market data provider to determine:
- **MFE:** Highest high (for longs) or lowest low (for shorts) during the trade's lifecycle
- **MAE:** Lowest low (for longs) or highest high (for shorts) during the trade's lifecycle

```python
async def calculate_excursions(trade: Trade, bars: List[Bar]) -> ExcursionResult:
    """Calculate MFE/MAE from intraday bars during trade lifecycle."""
    # Filter bars to trade's active period
    active_bars = [b for b in bars
                   if trade.entry_time <= b.timestamp <= trade.exit_time]

    if trade.direction == Direction.LONG:
        mfe_price = max(b.high for b in active_bars)
        mae_price = min(b.low for b in active_bars)
    else:  # SHORT
        mfe_price = min(b.low for b in active_bars)
        mae_price = max(b.high for b in active_bars)

    # Convert to dollar amounts
    mfe_dollars = abs(mfe_price - trade.entry_price) * trade.quantity * trade.multiplier
    mae_dollars = abs(mae_price - trade.entry_price) * trade.quantity * trade.multiplier
    capture_ratio = trade.net_pnl / mfe_dollars if mfe_dollars > 0 else 0

    return ExcursionResult(
        mfe_price=mfe_price, mae_price=mae_price,
        mfe_dollars=mfe_dollars, mae_dollars=mae_dollars,
        capture_ratio=capture_ratio
    )
```

### Bar Resolution Selection

| Trade Duration | Bar Resolution | Data Source |
|---------------|---------------|-------------|
| < 1 hour (scalp) | 1-min bars | IBKR / Alpaca API |
| 1–8 hours (day trade) | 5-min bars | IBKR / Alpaca API |
| 1–5 days (swing) | 15-min bars | IBKR / Alpaca API |
| > 5 days (position) | Daily bars | IBKR / Alpaca / free EOD APIs |

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Historical intraday bar data has limited lookback (IBKR: ~1 year for 1-min) | Calculate MFE/MAE at import time; store results permanently |
| Bar data may not be available for all instruments (OTC, illiquid) | Fallback: mark as "MFE/MAE unavailable — insufficient bar data" |
| Options: bars are for the option contract, not the underlying | Use option price bars, not underlying stock bars; note that option bars may have gaps |
| After-hours trades: bars may be sparse or missing | Flag trades with after-hours entries; use consolidated bars if available |
| API rate limits for historical data requests | Batch bar requests; prioritize recent trades; background queue for older trades |

---

## 8. Multi-Leg Options Grouping

**Source:** TOS spread analytics, Tastytrade curve analysis, TradeTally options template grouping  
**Priority:** P1 — Essential for options traders  
**Module:** `core/matching/strategies.py`

### Implementation Approach

Group individual option executions into recognized multi-leg strategies using pattern recognition on the legs' strikes, expirations, and directions:

```python
class StrategyDetector:
    PATTERNS = {
        "VERTICAL_SPREAD": lambda legs: (
            len(legs) == 2 and
            legs[0].expiration == legs[1].expiration and
            legs[0].option_type == legs[1].option_type and
            legs[0].side != legs[1].side
        ),
        "IRON_CONDOR": lambda legs: (
            len(legs) == 4 and
            # 2 puts + 2 calls, all same expiration
            sum(1 for l in legs if l.option_type == "PUT") == 2 and
            sum(1 for l in legs if l.option_type == "CALL") == 2
        ),
        "BUTTERFLY": lambda legs: (
            len(legs) == 3 and
            # 1x lower, -2x middle, 1x upper (or inverse)
            True  # Complex strike/qty ratio detection
        ),
    }
```

### Strategy Types to Recognize

| Strategy | Leg Count | Detection Rule |
|----------|-----------|---------------|
| Vertical (Bull/Bear Call/Put) | 2 | Same expiry, same type, different strikes, opposite sides |
| Iron Condor | 4 | 2 puts + 2 calls, same expiry, alternating buy/sell |
| Butterfly | 3 | 3 strikes, middle qty = 2× outer qty |
| Straddle | 2 | Same strike, same expiry, different types (call+put) |
| Strangle | 2 | Different strikes, same expiry, different types |
| Calendar/Diagonal | 2 | Same strike (calendar) or different (diagonal), different expiries |
| Covered Call/Put | 2 | 1 stock position + 1 short option |

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Legs executed at different times (legging in) | Group by strategy tag if broker provides one; fallback: time-proximity + structure matching |
| Partial execution: only 2 of 4 iron condor legs fill | Show as "incomplete strategy" with filled legs; allow manual grouping |
| Adjustments (rolling a spread) create new legs | Track strategy lifecycle: open → adjust → close; show each version |

---

## 9. Transaction Ledger & Fee Cataloging

**Source:** TJS Brokers sheet + IBKR Reporting Guide + NinjaTrader hidden fee analysis  
**Priority:** P2 — Important for "Cost of Free" report  
**Module:** `core/accounting/`

> **Merged from:** TJS §7 (Broker Transaction Types — ledger entries) + Expansion §9 (Fee taxonomy).
>
> This section covers two complementary layers:
> 1. **Transaction Ledger** — Categorizes all non-trade account activity (deposits, withdrawals, dividends, fees) to separate *trading performance* from *account cash flows*
> 2. **Fee Taxonomy** — Classifies all per-trade and periodic costs for accurate cost attribution

### Transaction Types (Ledger Layer)

| Type Code | Description | Direction | Example |
|-----------|-------------|-----------|---------|
| `opening_balance` | Starting capital | Credit | Initial account funding |
| `profit` | Trading profit (auto-linked to closed trades) | Credit | Sum of positive closed trade P&L |
| `loss` | Trading loss (auto-linked to closed trades) | Debit | Sum of negative closed trade P&L |
| `deposit` | Cash deposit | Credit | Wire transfer in, ACH deposit |
| `withdrawal` | Cash withdrawal | Debit | Wire transfer out |
| `data_feed` | Market data subscription fees | Debit | Monthly data subscription |
| `fee_other` | Platform/other fees | Debit | Inactivity, platform, exchange fees |
| `dividend` | Dividend / yield income | Credit | Stock dividend, bond coupon |
| `interest` | Interest earned or paid | Both | Margin interest (debit), cash sweep (credit) |
| `reconcile` | Manual balance correction | Both | Adjustment to match broker statement |
| `transfer_in` / `transfer_out` | Inter-account transfer | Both | Account-to-account |

**Analytical Value:**
- **True trading P&L** = Account growth - Deposits + Withdrawals - Dividends - Interest
- **Return on Invested Capital** = Trading P&L / (Opening Balance + Net Deposits)

### Implementation Approach

Define a comprehensive fee taxonomy that captures every cost a trader encounters:

```python
class FeeCategory(Enum):
    COMMISSION = "commission"         # Per-trade commission
    ROUTING_FEE = "routing_fee"       # ECN/exchange routing (ARCA, EDGX, etc.)
    EXCHANGE_FEE = "exchange_fee"     # Exchange transaction fees
    CLEARING_FEE = "clearing_fee"    # Clearinghouse fees
    REGULATORY_FEE = "regulatory"    # SEC fee, TAF fee, FINRA
    DATA_FEE = "data_fee"           # Market data subscriptions
    PLATFORM_FEE = "platform_fee"   # Software subscription (DAS, Sierra Chart)
    MARGIN_INTEREST = "margin_interest"  # Interest on margin loans
    MARGIN_CALL_FEE = "margin_call"  # Penalty for margin violations
    INACTIVITY_FEE = "inactivity"   # Monthly inactivity charges
    WITHDRAWAL_FEE = "withdrawal"   # Wire/ACH withdrawal fees
    FX_CONVERSION = "fx_conversion"  # Currency conversion spread/fee
    ASSIGNMENT_FEE = "assignment"    # Options assignment/exercise fees
    OTHER = "other"
```

### Per-Trade vs Periodic Fees

| Type | Frequency | Source | Attribution |
|------|-----------|--------|------------|
| Commission, routing, exchange, clearing, regulatory | Per-trade | Broker execution report | Direct to trade |
| Data fee, platform fee | Monthly | Manual entry or broker bill | Allocated across all trades in period |
| Margin interest | Daily | Broker statement | Attributed to margin positions |
| Inactivity, withdrawal, FX | Event-based | Broker statement | General overhead |

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Brokers bundle fees into "commission" without breakdown | Parse IBKR's detailed Flex report (separates SEC/TAF/exchange fees); estimate for less transparent brokers |
| Data feed costs vary by exchange (CME, NYSE, NASDAQ have separate fees) | Maintain fee schedule database per broker × data package |
| Some fees are implicit (PFOF = hidden cost via worse fills) | Track as estimated slippage in separate `implicit_cost` field |

---

## 10. Execution Quality Score

**Source:** DAS Trader DMA analysis, SEC Rule 605/606 reports  
**Priority:** P2 — Differentiator for serious traders (gated on data availability)  
**Module:** `core/enrichment/execution_quality.py`

> [!WARNING]
> This feature requires tick-level or second-level NBBO quote data at fill time. Most retail APIs do not provide this. Gate behind available quote-data providers (IBKR historical ticks, Polygon.io); when unavailable, degrade to broker-level spread proxy metrics (average effective spread from Rule 605 reports).

### Implementation Approach

For each trade, calculate an execution quality score comparing the fill price against the National Best Bid and Offer (NBBO) at the moment of execution:

```python
def calculate_execution_quality(trade: Trade, nbbo_at_fill: NBBO) -> ExecutionQuality:
    """Score execution quality vs NBBO benchmark."""
    if trade.direction == Direction.LONG:
        # Buying: compare fill to ask price
        price_improvement = nbbo_at_fill.ask - trade.entry_price
        midpoint_improvement = nbbo_at_fill.midpoint - trade.entry_price
    else:
        # Selling: compare fill to bid price
        price_improvement = trade.entry_price - nbbo_at_fill.bid
        midpoint_improvement = trade.entry_price - nbbo_at_fill.midpoint

    slippage = -price_improvement  # Negative improvement = slippage
    slippage_bps = (slippage / trade.entry_price) * 10000  # Basis points

    return ExecutionQuality(
        price_improvement_cents=price_improvement * 100,
        slippage_bps=slippage_bps,
        fill_vs_midpoint=midpoint_improvement,
        effective_spread=abs(trade.entry_price - nbbo_at_fill.midpoint) * 2,
        score=_grade_execution(slippage_bps)  # A/B/C/D/F
    )
```

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| NBBO at exact fill time requires tick-level quote data | Use 1-second quote snapshots; IBKR provides historical ticks |
| Multiple fills at different prices make scoring complex | Compute VWAP of fills; compare VWAP against NBBO midpoint at first fill time |
| After-hours trades have no NBBO | Score only regular-session trades; flag AH trades as "unscored" |
| Options have wide bid-ask spreads; scoring is less meaningful | Use mark price (midpoint) benchmark instead of NBBO for options |

---

## 11. PFOF Impact Analysis

**Source:** Retail Platform & Broker Analysis §"Mathematical Reality of Retail Trading"  
**Priority:** P2  
**Module:** `core/analytics/pfof.py`

### Implementation Approach

Flag each trade by its likely routing method (PFOF vs DMA) based on the broker, then correlate with execution quality scores:

```python
# Broker routing classification
BROKER_ROUTING = {
    "robinhood": RoutingType.PFOF,
    "webull": RoutingType.PFOF,
    "schwab": RoutingType.HYBRID,    # PFOF on Lite, DMA on Pro pricing
    "ibkr_lite": RoutingType.PFOF,
    "ibkr_pro": RoutingType.DMA,
    "lightspeed": RoutingType.DMA,
    "das_trader": RoutingType.DMA,
    "tastytrade": RoutingType.PFOF,   # Routes primarily through CBOE
}
```

### Report Output

```
PFOF Impact Report (March 2026) — ESTIMATE
═══════════════════════════════════════════
DMA Trades (142):     Avg slippage: -0.2 bps    Total cost: $47.30
PFOF Trades (89):     Avg slippage: -3.8 bps    Total cost: $312.50
                                                 ──────────
ESTIMATED PFOF EXCESS COST:                      $265.20/mo ±30%
                                                 $3,182/year
Confidence: Moderate (based on aggregate routing data, not per-trade)
Methodology: Broker-level routing classification × execution quality delta

AI Narrative: "Based on aggregate routing data (not per-trade attribution),
your PFOF-routed trades on Webull experienced ~19× worse slippage than your
DMA trades on IBKR Pro. Switching your Webull volume to IBKR Pro could save
an estimated ~$265/month, which exceeds the $10/mo platform cost."
```

### Data Sources

- **SEC Rule 606 reports:** Quarterly reports that each broker publishes disclosing where they route orders. Parseable from broker websites.
- **SEC Rule 605 reports:** Market-center-level execution quality statistics. Available from exchange websites.

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Can't definitively prove a specific trade was routed via PFOF | Use broker-level classification as proxy; label all outputs as **estimates** with methodology disclosure — Rule 606 reports are aggregate (quarterly), not per-trade truth |
| IBKR Lite uses PFOF but IBKR Pro doesn't — same broker, different routing | Classify at account-type level, not broker level |
| Market conditions affect slippage independent of routing | Compare fills during same time window to control for volatility |
| Overconfident reporting can mislead users | Include confidence band (±30%) on all PFOF cost figures; surface methodology notes in report footer |

---

## 12. Multi-Persona AI Review

**Source:** deltalytix AI journal, academic research on persona-driven LLM trading agents (arXiv)  
**Priority:** P2 — Opt-in experiment (not default per-trade pipeline)  
**Module:** `ai/reviewers/`

### Implementation Approach

Run three distinct AI "personas" on each trade or weekly review to generate a structured debate:

| Persona | System Prompt Focus | Purpose |
|---------|-------------------|---------|
| **Bull** (Defender) | "Find reasons why this trade was well-executed. Defend the entry, exit, and risk management." | Prevent excessive self-criticism |
| **Bear** (Critic) | "Identify every flaw in this trade. What rules were broken? What was missed?" | Surface blind spots |
| **Coach** (Neutral) | "Provide an objective assessment. Weigh both sides and give specific, actionable advice for next time." | Synthesize into improvement plan |

```python
async def multi_persona_review(trade: Trade, context: TradeContext) -> Review:
    trade_summary = format_trade_for_review(trade, context)

    bull_review = await llm.generate(
        system="You are a supportive trading coach. Defend this trade.",
        prompt=trade_summary
    )
    bear_review = await llm.generate(
        system="You are a harsh trading critic. Find every flaw.",
        prompt=trade_summary
    )
    coach_review = await llm.generate(
        system="You are an objective mentor. Synthesize the bull and bear views.",
        prompt=f"{trade_summary}\n\nBull says: {bull_review}\nBear says: {bear_review}"
    )
    return Review(bull=bull_review, bear=bear_review, coach=coach_review)
```

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| LLM hallucination: inventing market facts | Include actual price data, volume, and context in the prompt |
| Token cost for 3 separate LLM calls per trade | Use the coach's summary as the default visible view; show bull/bear on expansion |
| Persona drift over extended conversations | Reset system prompts for each review; don't carry history between trades |
| Cost and diminishing returns | Ship as opt-in weekly review experiment with quality telemetry; cap at user's configured LLM budget; do not run per-trade by default (recent multi-agent literature shows mixed gains vs simpler ensembling — [arXiv:2508.17536](https://arxiv.org/abs/2508.17536)) |

---

## 13. Expectancy & Edge Dashboard

**Source:** TJS Expectancy sheet + Retail Trading Platform & Broker Analysis  
**Priority:** High (P1)  
**Module:** `core/analytics/edge.py`

> **Merged from:** TJS §1 (Expectancy Calculator with Monte Carlo simulation) + Expansion §13 (Edge Formula Dashboard with visualization).
>
> This combines the Monte Carlo simulation engine with the live edge dashboard into a single analytical powerhouse.

### Implementation Approach

Implement the full edge equation as a live, interactive dashboard:

```
Edge = (WinRate × AvgWin) - (LossRate × AvgLoss) - Commissions - Slippage

Where:
  WinRate    = # winning trades / total trades
  LossRate   = 1 - WinRate
  AvgWin     = mean P&L of winning trades
  AvgLoss    = mean |P&L| of losing trades
  Commissions = total commissions per trade (avg)
  Slippage   = estimated execution cost per trade (avg)
```

### Dashboard Elements

1. **Edge waterfall chart:** Visual breakdown showing how each component contributes to net edge (bar chart with green for win contribution, red for loss erosion, gray for costs)
2. **Sensitivity analysis:** "What if" sliders — *"If your win rate improved by 5%, your edge would increase from $42/trade to $78/trade"*
3. **Edge over time:** Rolling 30-day edge plotted as time series — detect trending up/down
4. **Per-strategy edge comparison:** Side-by-side edge components for each strategy tag
5. **Commission impact calculator:** *"Your commissions cost $4,200 this year. On IBKR Pro they would cost $2,100. On Webull (with PFOF slippage) they would effectively cost $5,800."*

### Monte Carlo Simulation Engine (from TJS §1)

**Data source:** Auto-populate from actual trade history (win %, avg win/loss, payoff ratio) — or allow manual override for hypothetical scenarios.

**Simulation:** Python `numpy` random sampling, 10,000 iterations, two position-sizing models:
- **% of account** (compounding) vs **fixed $ risk** (non-compounding)

**Output:** Fan chart showing 5th/25th/50th/75th/95th percentile equity curves; summary stats: expected return, max drawdown, risk of ruin, longest win/loss streak.

**Key formulas:**
```
Net Expectancy  = (Win% × Avg Win) - (Loss% × Avg Loss)
Profit Factor   = (Win% × Avg Win) / (Loss% × Avg Loss)
Break-Even Win% = 1 / (1 + Payoff Ratio)
Risk of Ruin    = ((1 - Edge) / (1 + Edge)) ^ Capital_Units
```

**AI use case:** *"Based on your last 50 trades, what's your expected return over the next 100 trades at 1% risk?"*

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Slippage is estimated, not directly measurable for most brokers | Use execution quality score (§10) as proxy; show confidence range |
| Small sample sizes give unreliable edge estimates | Show confidence intervals; require minimum 30 trades for reliable display |
| Edge varies across market conditions (trending vs. choppy vs. low-vol) | Allow filtering by market regime (VIX ranges) |
| Non-stationary edge: past performance doesn't guarantee future results | Show rolling-window edge to detect regime changes |

---

## 14. Drawdown Probability Table

**Source:** TJS Drawdown sheet + Balsara Risk-of-Ruin tables  
**Priority:** High (P1) — companion to Expectancy & Edge Dashboard  
**Module:** `core/analytics/drawdown.py`

> **New from TJS §2.** A precomputed matrix showing the statistical probability of experiencing X consecutive losing trades given your win rate, over a defined number of trades.

### Implementation Approach

- **Static table:** Precomputed matrix for win rates 20–80% and streak lengths 2–15, stored as reference data
- **Dynamic calculator:** Accept trader's actual win % and number of trades → compute personalized streak probabilities
- **AI-triggered intervention:** When a losing streak matches a statistically significant threshold: *"You've hit 5 losses in a row. At your 55% win rate, this happens 19% of the time over 100 trades. Take a break — this is statistically normal."*

### Key Formula

```
P(streak ≥ k in n trades) = 1 - P(no run of k losses in n trades)
  where P(no run) uses a recursive Markov chain model

Simplified: P ≈ 1 - (1 - (1-WinRate)^k)^(n/k)
```

### Key Insight

At a 50% win rate over 100 trades: 4 consecutive losses is 83% probable; 6 consecutive losses is 31% probable. Most traders dramatically underestimate how common losing streaks are.

---

## 15. SQN — System Quality Number

**Source:** Van Tharp's *Definitive Guide to Position Sizing* (2008)  
**Priority:** Medium (P2)  
**Module:** `core/analytics/sqn.py`

> **New from TJS §4.** A single number rating system quality by measuring the relationship between average R-multiple and standard deviation, adjusted for trade count. Mathematically equivalent to a t-test statistic.

### Formula

```
SQN = √N × (Mean of R-multiples) / (StdDev of R-multiples)

Where:
  R-multiple = Net P&L ÷ Initial Risk Amount
  N = number of trades (capped at 100 per Van Tharp)
```

### Interpretation

| SQN Range | Rating | Meaning |
|-----------|--------|---------|
| < 0 | Losing system | Negative expectancy |
| 1.0 – 2.0 | Below average | Marginal edge |
| 2.0 – 3.0 | Average | Decent with discipline |
| 3.0 – 5.0 | Good | Strong edge; can compound |
| 5.0 – 7.0 | Excellent | Very consistent returns |
| > 7.0 | Holy Grail | Extremely rare |

### Zorivest Integration

- **Prerequisite:** Every trade needs a `risk_amount` field
- **Segmentation:** Calculate SQN per strategy, per timeframe, per asset class, overall
- **AI use case:** *"Your swing trading system has SQN 3.4 (Good), but scalping is 0.8 (Very Poor). Consider dropping scalping."*

---

## 16. Bidirectional Trade-Journal Linking

**Source:** journalit (Obsidian plugin), deltalytix AI journal  
**Priority:** P2  
**Module:** `core/journal/linking.py`

### Implementation Approach

Create a rich linking system between three entity types: **Trades**, **Journal Entries**, and **Strategy Notes**.

```python
class EntityLink:
    source_type: EntityType   # TRADE, JOURNAL, STRATEGY, TAG
    source_id: str
    target_type: EntityType
    target_id: str
    link_type: LinkType       # MENTIONS, TAGGED_WITH, REVIEWED_BY, CAUSED_BY
    created_at: datetime

# Usage examples:
# Trade → Journal:   trade_123 REVIEWED_BY journal_456
# Journal → Trade:   journal_456 MENTIONS trade_789
# Trade → Strategy:  trade_123 TAGGED_WITH strategy_breakout
# Journal → Tag:     journal_456 TAGGED_WITH tag_fomo
```

### Features

- **Click a trade → see all journal entries** that mention or review it
- **Click a journal entry → see all referenced trades** with inline P&L summaries
- **Search by strategy → see all trades + all journal reflections** for that strategy
- **"Related trades" suggestions:** When writing a journal entry about AAPL, suggest recent AAPL trades for linking
- **Mistake tag backlinks:** Click "FOMO" tag → see every trade and journal entry tagged with FOMO

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Users rarely manually create links | Auto-link: detect trade symbols in journal text; suggest links on save |
| Link integrity during trade merges/deletes | Cascade-on-delete or soft-delete with orphan link cleanup |

---

## 17. Mistake Tracking with Cost Attribution

**Source:** TJS StockTracking mistake taxonomy + behavioral trading psychology research  
**Priority:** Medium (P2)  
**Module:** `core/journal/mistakes.py`

> **New from TJS §5.** A structured system for categorizing trading errors, tracking frequency, and calculating dollar cost per mistake type.

### Default Taxonomy (12 Types from TJS)

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

### Implementation

- **Schema:** `mistake_tags[]` (multi-select from taxonomy + custom) per trade
- **Cost calculation:** Auto-computed: sum of Net P&L for all trades tagged with each mistake type
- **Reports:** Mistake frequency table, cost attribution per type, trend over time
- **AI use case:** *"Your top 3 most expensive mistakes: FOMO ($4,200), Bad Exit ($2,800), Too Late ($1,900). FOMO trades have a 23% win rate vs your overall 58%."*

### Integration with Multi-Persona AI Review (§12)

The Bear persona's critique automatically suggests mistake tags. The Coach persona tracks recurring patterns across multiple reviews.

---

## 18. Broker CSV Import Framework

**Source:** TraderLog, Wingman Tracker, TradeInsights, TJS Import sheet, TraderFyles  
**Priority:** P1 (TOS, NinjaTrader) / P2 (Webull, Lightspeed, E*TRADE, Tastytrade)  
**Module:** `core/brokers/parsers/`

> Consolidated from TJS §6 (NinjaTrader) and individual broker research. Each broker gets a parser module under the `IBroker.parse_csv()` interface (§1). All parsers output `List[RawExecution]` which feeds into the Round-Trip Matcher (§3) and Deduplication (§6) pipeline.

### Supported Brokers

| Broker | Priority | Export Path | Key Columns | Parsing Notes |
|--------|----------|-------------|-------------|---------------|
| **ThinkorSwim** | P1 | Monitor → Account Statement → Export | `Exec Time`, `Spread`, `Side`, `Qty`, `Pos Effect`, `Symbol`, `Exp`, `Strike`, `Type`, `Price`, `Net Price` | Multi-section CSV (detect "Trade History" header); options use dot prefix (`.AAPL260116C225`); `Spread` column identifies multi-leg strategies; commission = `(Price - Net Price) × Qty` |
| **NinjaTrader** | P1 | Control Center → Executions → Export CSV | `Trade-#`, `Instrument`, `Account`, `Strategy`, `Market pos.`, `Quantity`, `Entry price`, `Exit price`, `Entry time`, `Exit time`, `Profit`, `Commission`, `MAE`, `MFE` | Cleanest format — round-trip trades already paired; includes MFE/MAE in export; `Strategy` column maps to `entry_strategy` tag |
| **Webull** | P2 | App → More → Statements → Trade → CSV | `Date`, `Time`, `Symbol`, `Side`, `Qty`, `Price`, `Amount`, `Commission`, `Fee` | Minimal data (no order ID, no NBBO); no `Pos Effect` — must infer open/close from round-trip matcher; options format varies across app versions |
| **Lightspeed** | P2 | Execution log or DAS Trader export | `Date`, `Time`, `Symbol`, `B/S`, `Qty`, `Price`, `Route`, `Commission`, `ECN Fee`, `SEC Fee` | Most granular fee breakdown of any broker (ECN rebates, TAF, NSCC); `Route` column contains ECN names for execution quality analysis; DAS Trader vs Lightspeed have slight format differences |
| **E*TRADE** | P2 | Website → Accounts → Transactions → Download | `Transaction Date`, `Transaction Type`, `Security Type`, `Symbol`, `Quantity`, `Price`, `Commission`, `Amount` | Uses CUSIP codes sometimes (→ identifier resolver §5); includes non-trade items (dividends, interest) — filter by `Transaction Type`; Morgan Stanley acquisition may change format |
| **Tastytrade** | P2 | Desktop/web → History → Transactions → CSV | `Date`, `Type`, `Sub Type`, `Action`, `Symbol`, `Instrument Type`, `Description`, `Quantity`, `Price`, `Commission`, `Fees`, `Value` | Rich spread metadata in `Description` field (e.g., "SOLD 1/17 AAPL 225 CALL @2.15"); options use internal symbology → map to OCC; filter `Type` == "Trade" to exclude dividends/fees |

### Universal Parser Architecture

```python
class CSVParser(ABC):
    """Base class for all broker CSV parsers."""

    @abstractmethod
    def detect(self, headers: List[str]) -> bool:
        """Return True if this parser handles the given CSV headers."""

    @abstractmethod
    def parse(self, rows: List[dict]) -> List[RawExecution]:
        """Parse CSV rows into RawExecution objects."""

# Auto-detection: try each parser's detect() method on the file headers
def auto_detect_broker(csv_path: str) -> CSVParser:
    headers = read_csv_headers(csv_path)
    for parser_cls in REGISTERED_PARSERS:
        parser = parser_cls()
        if parser.detect(headers):
            return parser
    raise UnknownBrokerFormat(f"No parser matches headers: {headers}")
```

### Cross-Cutting Challenges

| Challenge | Mitigation |
|-----------|------------|
| Header names change across broker versions | Dynamic header detection with fallback synonym dictionaries |
| Options symbology varies per broker | Normalize all to OCC standard: `SYMBOL YYMMDD C/P STRIKE` |
| Non-trade rows mixed with trade data | Filter by transaction type field; route non-trade items to Transaction Ledger (§9) |
| Multi-section CSVs (TOS, NinjaTrader) | Detect section headers; extract only the relevant trade section |
| Encoding issues (Latin-1, UTF-8 BOM) | Auto-detect encoding with `chardet`; strip BOM |

---

## 19. PDF Broker Statement Extraction

**Source:** pdf-broker-2-ghostfolio, Portfolio Performance PDF importers  
**Priority:** P3 — European market requirement (last-resort fallback)  
**Module:** `core/import/pdf_extractor.py`

> **Maintenance advisory:** PDF layouts drift frequently across broker statement redesigns. Treat PDF extraction as a last-mile fallback when CSV/OFX exports are unavailable — not as a primary ingestion path. Per-broker PDF configs require ongoing maintenance as institutions update their statement templates.

### Implementation Approach

Use Python libraries for structured PDF text extraction:

```python
# Option 1: pdfplumber (table-aware extraction)
import pdfplumber

def extract_trades_from_pdf(pdf_path: str) -> List[RawExecution]:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Map table columns to trade fields
                trades = parse_table_to_executions(table)

# Option 2: tabula-py (Java-based, excellent table detection)
import tabula

def extract_with_tabula(pdf_path: str) -> pd.DataFrame:
    return tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)

# Option 3: AI-powered extraction (for unstructured PDFs)
async def extract_with_ai(pdf_path: str) -> List[RawExecution]:
    """Use LLM vision to extract trades from complex/graphical PDFs."""
    pages = render_pdf_to_images(pdf_path)
    for page_image in pages:
        result = await llm.generate_with_vision(
            system="Extract all trade executions from this broker statement.",
            image=page_image,
            output_format=TradeExtractionSchema
        )
```

### European Broker Formats

| Broker | Country | PDF Structure | Difficulty |
|--------|---------|--------------|------------|
| Trade Republic | Germany | Clean tabular | Medium |
| DEGIRO | Netherlands/EU | Transaction overview table | Medium |
| Flatex | Germany/Austria | German-language, variable layout | Hard |
| Interactive Investor | UK | Mixed tabular + narrative | Hard |
| Sunrise | Switzerland | Complex multi-section | Very Hard |

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| PDFs have no standardized structure — every broker is different | Build per-broker template with coordinate/regex-based extraction |
| Language localization (German, French, Dutch) | Multi-language field name dictionaries |
| Number formatting varies (1.234,56 vs 1,234.56) | Locale-aware number parser using `babel` library |
| Scanned PDFs (images, not text) | OCR with `tesseract` + LLM vision as fallback |

---

## 20. Monthly P&L Calendar Report

**Source:** TJS Calendar sheet + TradesViz/Tradervue/PnLLedger  
**Priority:** Low (P3) — table-stakes journal feature  
**Module:** `reports/calendar.py`

> **New from TJS §8.** A calendar-grid view showing daily P&L with color-coded cells (green = profit, red = loss), weekly subtotals, and monthly summary.

### Implementation

| Aspect | Detail |
|--------|--------|
| **Content** | Daily P&L grid, weekly subtotals, monthly totals (Gross/Net), trade count, win rate, avg P&L/day, best/worst day |
| **Output** | GUI calendar tab (static view, no scheduling dependency initially); later → email template via scheduler |
| **Yearly heatmap** | 365-cell grid with color intensity by daily P&L (inspired by TradesViz yearly view) |
| **AI narrative** | *"February was your best month in 3 months: $4,200 net. Tuesdays were strongest (+$2,100). You had 2 days with >3% drawdown — both on Fridays."* |

### Industry Standard Features

| Feature | TradesViz | Tradervue | PnLLedger |
|---------|-----------|-----------|-----------|
| Daily P&L cells | ✅ Color-coded | ✅ Color-coded | ✅ Color-coded |
| Weekly summary sidebar | ✅ P&L, win rate | ✅ P&L, # trades | ✅ Totals |
| Drill-down on click | ✅ Day explore tab | ✅ Journal for that day | ✅ Journal view |
| Economic events overlay | ✅ Earnings, IPOs | ❌ | ❌ |

---

## 21. Strategy Breakdown Report

**Source:** TJS StockTracking/StockFilter + BacktestBase/ORBSetups, Freqtrade  
**Priority:** Medium (P2) — core AI use case  
**Module:** `reports/strategy_breakdown.py`

> **New from TJS §9.** A performance analytics engine that slices trade data across multiple dimensions.

### Breakdown Dimensions (8)

| Dimension | Example Values | Key Question |
|-----------|---------------|-------------|
| **Entry Strategy** | Breakout, Breakdown, custom... | *Which setup types are profitable?* |
| **Direction** | Trend, Counter-Trend, Sideways | *Am I better with or against the trend?* |
| **Trade Category** | Scalp, Day, Swing, Position | *Which time horizon suits me?* |
| **Chart Timeframe** | 1Min, 5Min, 15Min, Daily | *Which chart timeframe produces best entries?* |
| **Time of Day** | Pre-market, Morning, Midday, Afternoon | *When am I sharpest?* |
| **Day of Week** | Mon–Fri | *Are Fridays killing me?* |
| **Exit Strategy** | Target, Stop, Trailing, Discretionary | *How am I leaving most trades?* |
| **Long vs Short** | Long, Short | *Do I have a directional bias?* |

### Metrics Per Dimension

| Metric | Formula |
|--------|---------|
| Win % | Win # / Total # |
| Payoff Ratio | Win Avg / \|Loss Avg\| |
| Expectancy | (Win% × Win Avg) - (Loss% × \|Loss Avg\|) |
| Frequency | Segment # / Total # |
| SQN | System Quality Number for this segment |

**AI narrative:** *"Your Swing trades: 68% win rate, 2.1 payoff (Expectancy: $480/trade). Scalps: 52% win rate, 0.8 payoff (Expectancy: -$12/trade). Increase Swing allocation, reduce Scalps."*

---

## 22. "Cost of Free" Report

**Source:** Retail Platform & Broker Analysis — "Mathematical Reality" conclusions  
**Priority:** P2  
**Module:** `reports/cost_of_free.py`

### Implementation Approach

Monthly report aggregating ALL trading costs — explicit and implicit — to show the true cost of trading:

```
══════════════════════════════════════════════════
      TOTAL COST OF TRADING — March 2026
══════════════════════════════════════════════════

EXPLICIT COSTS (directly billed)
  Commissions ................ $   342.00
  Exchange fees .............. $    28.50
  Regulatory fees (SEC/TAF) .. $     4.75
  Data subscriptions ......... $    89.00
  Platform fees .............. $   150.00
  Margin interest ............ $   187.20
  ────────────────────────────────────────
  Subtotal Explicit .......... $   801.45

IMPLICIT COSTS (estimated from execution quality)
  Slippage (avg 1.2 bps × 231 trades) .. $   412.30
  Spread cost (avg effective spread) .... $   198.50
  ────────────────────────────────────────
  Subtotal Implicit .................... $   610.80

══════════════════════════════════════════════════
  TOTAL COST OF TRADING ................ $ 1,412.25
  Per-trade average .................... $     6.11
  As % of gross P&L ................... 14.8%
══════════════════════════════════════════════════

BROKER COMPARISON (what-if analysis):
  Your setup (Webull + data): $1,412/mo
  IBKR Pro + DMA routing:    $  891/mo  (save $521/mo)
  Lightspeed + DAS:          $1,050/mo  (save $362/mo)
```

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Slippage is estimated, not measured | Use execution quality score as best estimate; show confidence range |
| Platform/data fees require manual input from user | Provide pre-populated templates for common broker+platform combos |
| "What-if" comparison requires fee schedules of other brokers | Maintain fee database for top 10 brokers (update quarterly) |

---

## 23. Broker Constraint Modeling

**Source:** LEAN's `DefaultBrokerageModel.cs`, Backtrader broker simulation, paperbroker  
**Priority:** P3  
**Module:** `core/brokers/models/`

### Implementation Approach

Model each broker's rules as a `BrokerModel` dataclass:

```python
@dataclass
class BrokerModel:
    name: str
    trading_hours: TradingHours
    margin_requirements: MarginRequirements
    pdt_rule: bool                 # Pattern Day Trader restriction
    pdt_threshold: Decimal         # $25,000 for US brokers
    commission_schedule: CommissionSchedule
    supported_order_types: List[OrderType]
    supported_asset_classes: List[AssetClass]
    max_leverage: Dict[AssetClass, Decimal]  # 4:1 intraday, 2:1 overnight for US equities
    routing_type: RoutingType      # PFOF, DMA, HYBRID
    settlement_days: int           # T+1 for US equities and listed options (SEC T+1 framework)

# Pre-built models
IBKR_PRO = BrokerModel(
    name="Interactive Brokers Pro",
    pdt_rule=True, pdt_threshold=Decimal("25000"),
    max_leverage={"equity": Decimal("4"), "option": Decimal("1")},
    routing_type=RoutingType.DMA,
    settlement_days=1,
    # ...
)
```

### Use Cases

1. **PDT Warning:** *"You've made 3 day trades this week. One more triggers PDT restriction on your Webull account (<$25K)."*
2. **Margin Check:** *"This position would put you at 85% margin utilization. IBKR's auto-liquidation triggers at 100%."*
3. **Trading Hours Alert:** *"You're entering a trade on AAPL at 7:45 PM EST. Webull allows this, but your TOS account doesn't support extended hours."*
4. **Fee Preview:** *"This trade will cost: $0.65 commission + $0.02 TAF + estimated $0.15 slippage = $0.82 total."*

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Broker rules change frequently (margin requirements shift with volatility) | Store as versioned config files; provide update mechanism |
| PDT rule calculation requires tracking trades across 5 rolling days | Maintain rolling 5-day trade counter per account |
| Some constraints are per-account, not per-broker | Allow per-account overrides (e.g., portfolio margin vs Reg-T) |

---

## 24. Alpaca Direct API Integration

**Source:** Alpaca API v2 documentation, `alpaca-py` Python SDK  
**Priority:** P1 — Broad coverage, paper trading, official SDK  
**Module:** `core/brokers/alpaca.py`

> **Architecture:** Zorivest wraps Alpaca's REST API behind its own MCP tools — identical to the IBKR pattern. No dependency on Alpaca's MCP server; their MCP server serves only as an architectural reference.

### Auth & Configuration

- **API Base:** `https://api.alpaca.markets/v2/` (live) / `https://paper-api.alpaca.markets/v2/` (paper)
- **Auth:** API Key ID + Secret Key — supports both HTTP Basic Auth and dedicated headers (`APCA-API-KEY-ID`, `APCA-API-SECRET-KEY`); prefer header-based auth for clarity
- **SDK:** `alpaca-py` (official, pip-installable) — wraps all REST endpoints
- **User flow:** Settings → Broker Connections → Add Alpaca → Enter API Key + Secret → Zorivest stores encrypted → MCP tools call REST API directly

### Zorivest MCP Tool ↔ Alpaca Endpoint Mapping

| Zorivest MCP Tool | Alpaca API Endpoint | Purpose |
|-------------------|---------------------|--------|
| `import_trades(broker="alpaca")` | `GET /v2/orders?status=closed` | Pull closed orders → round-trip matching → trade log |
| `sync_account(broker="alpaca")` | `GET /v2/account` | Balance, buying power, margin → account snapshot |
| `sync_positions(broker="alpaca")` | `GET /v2/positions` | Open positions → portfolio view |
| `get_balance_history(broker="alpaca")` | `GET /v2/account/portfolio/history` | Equity time series → balance chart |
| `get_bars(symbol, timeframe)` | `GET /v2/stocks/{symbol}/bars` | Historical bars → MFE/MAE calculation |
| `get_corporate_actions(symbols)` | `GET /v2/corporate-actions` | Dividends, splits → daily brief enrichment |
| `get_options_chain(symbol)` | `GET /v2/options/contracts` | Greeks, IV → options analysis |
| `get_crypto_bars(symbol)` | `GET /v2/crypto/{symbol}/bars` | Crypto market data → portfolio valuation |

### Key Value

- **Paper trading:** Free $100K simulated environment — Zorivest users can test import/sync without real money
- **Corporation actions API:** Earnings, dividends, splits feed directly into daily brief enrichment
- **Crypto + Stocks + Options** from a single API — reduces integration complexity

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Rate limits (200 requests/min for free tier) | Implement request throttling with backoff; cache responses |
| Order history doesn't include P&L directly | Calculate from fill prices via round-trip matcher (§3) |
| Paper vs live API have different base URLs | Store `environment` flag per connection; route accordingly |
| WebSocket streaming for real-time data requires persistent connection | Use SSE for trade updates; REST polling for periodic syncs |

---

## 25. Tradier Direct API Integration

**Source:** Tradier Brokerage API v1 documentation  
**Priority:** P1 — Cloud-hosted, gain/loss + balance history built-in  
**Module:** `core/brokers/tradier.py`

> **Architecture:** Same as Alpaca — Zorivest wraps Tradier's REST API behind its own MCP tools. Tradier's MCP server serves only as an architectural reference for tool organization.

### Auth & Configuration

- **API Base:** `https://api.tradier.com/v1/` (live) / `https://sandbox.tradier.com/v1/` (paper)
- **Auth:** Bearer token via `Authorization: Bearer <TOKEN>` header
- **SDK:** `tradier-python` (community) or raw `httpx` requests
- **User flow:** Settings → Broker Connections → Add Tradier → Enter Bearer Token → Zorivest stores encrypted → MCP tools call REST API directly

### Zorivest MCP Tool ↔ Tradier Endpoint Mapping

| Zorivest MCP Tool | Tradier API Endpoint | Purpose |
|-------------------|----------------------|--------|
| `import_trades(broker="tradier")` | `GET /v1/accounts/{id}/history` | Transaction history → trade log |
| `sync_account(broker="tradier")` | `GET /v1/accounts/{id}/balances` | Balance, equity → account snapshot |
| `sync_positions(broker="tradier")` | `GET /v1/accounts/{id}/positions` | Holdings → portfolio |
| `get_gainloss(broker="tradier")` | `GET /v1/accounts/{id}/gainloss` | Realized P&L → performance reporting |
| `get_balance_history(broker="tradier")` | `GET /v1/accounts/{id}/history` (filtered) | Balance time series |
| `get_bars(symbol, timeframe)` | `GET /v1/markets/history` | Historical bars → MFE/MAE |
| `get_options_chain(symbol)` | `GET /v1/markets/options/chains` | Greeks, IV → options analysis |
| `get_calendar()` | `GET /v1/markets/calendar` | Trading days → scheduler awareness |

### Key Value

- **`get_gainloss` endpoint:** Returns realized/unrealized P&L directly — no round-trip matching needed for P&L reporting
- **`get_account_history`:** Full transaction history (dividends, fees, transfers) → maps directly to Transaction Ledger (§9)
- **Cloud-only API:** No local gateway needed (unlike IBKR's TWS requirement) — simplest integration path
- **Sandbox environment:** Free paper trading for development/testing

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| Bearer token must be refreshed manually by user if it expires | Guide user through token regeneration; detect 401 and prompt re-auth |
| Smaller user base than TOS/IBKR/Schwab | Position as proof-of-concept for broker adapter pattern; validates IBroker interface |
| Historical data limited to daily bars for free tier | Supplement with Alpaca or IBKR bar data for intraday MFE/MAE |
| Options chain data structure differs from IBKR | Normalize to common `OptionsChain` schema in adapter layer |

---

## 26. Bank Account Statement Import

**Source:** [Bank Account Integration Analysis](file:///p:/zorivest/_inspiration/import_research/Bank%20Account%20Integration%20Analysis.md), [Trader Banking Preferences: 2025 Analysis](file:///p:/zorivest/_inspiration/import_research/Trader%20Banking%20Preferences_%202025%20Analysis.md), GitHub open-source projects ([ofxtools](https://github.com/csingley/ofxtools), [ofxparse](https://github.com/jseutter/ofxparse), [ofxstatement](https://github.com/kedder/ofxstatement), [csv2ofx](https://github.com/reubano/csv2ofx), [Firefly III Data Importer](https://github.com/firefly-iii/data-importer), [bank-statement-parser](https://github.com/felgru/bank-statement-parser), [pdf_statement_reader](https://github.com/marlanperumal/pdf_statement_reader), [quiffen](https://github.com/isaacharrisholt/quiffen))  
**Priority:** P1 (phased) — Bank account balances are required for net-worth dashboard, PDT threshold monitoring, and cash-in-transit tracking  
**Module:** `core/banking/importers/`, `core/banking/models.py`

> **Phased delivery:**
> - **26A (P1):** CSV + OFX/QFX + manual column mapping GUI + manual entry — covers ~90% of user needs
> - **26B (P2):** QIF support — legacy/UK banks
> - **26C (P3):** PDF extraction + CAMT.053 — highest complexity, lowest immediate ROI; PDF layouts drift frequently across bank statement redesigns, creating a long-lived maintenance burden (Firefly III precedent)

### Context

Traders use bank accounts as active infrastructure — not just storage. The [banking research](file:///p:/zorivest/_inspiration/import_research/Trader%20Banking%20Preferences_%202025%20Analysis.md) identifies 15 institutions across 6 countries. Unlike broker accounts, banks rarely offer direct REST APIs to consumers. The primary data access method is **file export** (CSV, OFX/QFX, PDF statements) downloaded from the bank's dashboard, supplemented by **manual entry** for any institution.

Zorivest will **not** implement aggregator APIs (Plaid, Finicity, Yodlee) or Open Banking protocols (PSD2, CDR, Account Aggregator) — those add regulatory complexity, per-connection costs, and credential-sharing concerns unsuitable for a local-first desktop app.

### Supported File Formats

| Format | Extensions | Structure | Python Library | Coverage |
|--------|-----------|-----------|---------------|----------|
| **OFX/QFX** | `.ofx`, `.qfx` | SGML (v1) or XML (v2) — Open Financial Exchange standard | `ofxtools` (1,004 commits, stdlib-only), `ofxparse` (6.2K downstream users) | ~60% of US/CA banks (Fidelity, Schwab, Chase, Ally, TD Bank) |
| **CSV** | `.csv` | Varies wildly per bank — requires per-bank column mapping | `pandas` + per-bank config (Firefly III model: 559 community configs across 30+ countries) | ~95% of all banks (every bank exports CSV) |
| **QIF** | `.qif` | Quicken Interchange Format — line-delimited, field-prefixed | `quiffen` (parser + DataFrame export) | Legacy format; Quicken users, some UK banks |
| **PDF** | `.pdf` | Tabular data embedded in PDF — requires extraction | `pdfplumber`, `tabula-py`, `pypdf_table_extraction` (Camelot) | ~100% of banks issue PDF statements |
| **CAMT.053** | `.xml` | ISO 20022 bank-to-customer statement — EU/SEPA standard | `lxml` + schema validation | European banks, especially SEPA zone |

### Data Model

```python
# core/banking/models.py

class BankAccount:
    id: str                      # uuid4
    name: str                    # "Chase Business Checking"
    institution: str             # "chase" — matches config registry key
    account_type: AccountType    # CHECKING, SAVINGS, CMA, MONEY_MARKET, CREDIT_CARD
    currency: str                # ISO 4217: "USD", "EUR", "GBP"
    last_balance: Decimal
    last_balance_date: datetime
    balance_source: BalanceSource  # MANUAL, CSV_IMPORT, OFX_IMPORT, PDF_IMPORT
    is_primary: bool             # For net-worth rollup ordering
    sub_accounts: List[BankAccount]  # Relay sub-account hierarchy
    notes: str?

class BankTransaction:
    id: str                      # uuid4
    account_id: str              # FK → BankAccount
    date: datetime               # Transaction date
    post_date: datetime?         # Settlement/posting date (if different)
    description: str             # Raw description from bank
    amount: Decimal              # Positive = inflow, negative = outflow
    running_balance: Decimal?    # Running balance if provided by bank
    category: TransactionCategory  # See taxonomy below
    source: TransactionSource    # MANUAL, CSV_IMPORT, OFX_IMPORT, PDF_IMPORT, QIF_IMPORT
    reference_id: str?           # FITID (OFX), check number, or bank ref
    dedup_hash: str              # MD5(date + description + amount) for overlap detection
    notes: str?

class TransactionCategory(Enum):
    DEPOSIT = "deposit"          # Incoming cash
    WITHDRAWAL = "withdrawal"    # ATM, cashier
    TRANSFER_IN = "transfer_in"  # Inter-account inbound
    TRANSFER_OUT = "transfer_out"  # Inter-account outbound → brokerage funding
    FEE = "fee"                  # Account maintenance, wire fees
    INTEREST = "interest"        # Interest earned on balance
    DIVIDEND = "dividend"        # Dividend payment from sweep fund (e.g., SPAXX)
    ACH_DEBIT = "ach_debit"      # Automated clearing house outbound
    ACH_CREDIT = "ach_credit"    # Automated clearing house inbound
    WIRE_IN = "wire_in"          # Incoming wire
    WIRE_OUT = "wire_out"        # Outgoing wire
    CHECK = "check"              # Check payment
    CARD_PURCHASE = "card_purchase"  # Debit card transaction
    REFUND = "refund"            # Merchant refund
    OTHER = "other"              # Unclassified
```

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Bank Statement Import Pipeline               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐   ┌──────────┐   ┌────────────┐   ┌────────────┐ │
│  │ Format  │──▶│  Parser  │──▶│  Dedup &   │──▶│   Store    │ │
│  │ Detect  │   │ (per-fmt)│   │ Reconcile  │   │  (SQLite)  │ │
│  └─────────┘   └──────────┘   └────────────┘   └────────────┘ │
│       │              │              │                  │        │
│   Extension +     OFX Parser    Hash-based         Transactions│
│   magic bytes     CSV Parser    dedup via          + Balance   │
│   header sniff    QIF Parser    dedup_hash         snapshot    │
│                   PDF Parser    + FITID match                  │
│                   CAMT Parser                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Stage 1 — Format Detection:**
```python
def detect_format(file_path: str) -> FileFormat:
    ext = Path(file_path).suffix.lower()
    if ext in ('.ofx', '.qfx'):
        return FileFormat.OFX
    if ext == '.qif':
        return FileFormat.QIF
    if ext == '.xml':
        # Distinguish CAMT.053 from OFX v2
        with open(file_path) as f:
            head = f.read(500)
        if 'BkToCstmrStmt' in head:
            return FileFormat.CAMT053
        if '<OFX>' in head or 'OFXHEADER' in head:
            return FileFormat.OFX
    if ext == '.csv':
        return FileFormat.CSV
    if ext == '.pdf':
        return FileFormat.PDF
    raise UnsupportedFormat(f"Unknown file format: {ext}")
```

**Stage 2 — Parsing:**

#### OFX/QFX Parser (Highest Fidelity)

OFX is the ideal import format — it's structured, standardized, and contains dedup-safe transaction IDs (FITID). Python's `ofxtools` library handles both SGML (v1.x) and XML (v2.x) OFX, plus Quicken's proprietary QFX extensions.

```python
from ofxtools.Parser import OFXTree

def parse_ofx(file_path: str) -> BankStatementResult:
    parser = OFXTree()
    parser.parse(file_path)
    ofx = parser.convert()
    
    account = ofx.statements[0]  # BankAccount or CreditCardAccount
    transactions = []
    for txn in account.transactions:
        transactions.append(BankTransaction(
            date=txn.dtposted,                    # Transaction date
            post_date=txn.dtavail,                # Availability date
            description=txn.name or txn.memo,     # Payee or memo
            amount=txn.trnamt,                    # Signed decimal
            reference_id=txn.fitid,               # UNIQUE per institution
            category=infer_category(txn.trntype), # CREDIT, DEBIT, XFER, etc.
        ))
    return BankStatementResult(
        transactions=transactions,
        closing_balance=account.ledgerbal.balamt,
        as_of_date=account.ledgerbal.dtasof,
        account_id=account.acctid,       # Last 4 or full account number
        institution_id=account.bankid,   # Routing number
    )
```

**OFX `trntype` → Zorivest category mapping:**

| OFX TRNTYPE | Zorivest Category | Description |
|-------------|------------------|-------------|
| `CREDIT` | `deposit` | Generic credit |
| `DEBIT` | `withdrawal` | Generic debit |
| `XFER` | `transfer_in` / `transfer_out` | Inter-account transfer (sign determines direction) |
| `INT` | `interest` | Interest earned |
| `DIV` | `dividend` | Dividend payment |
| `FEE` | `fee` | Service charge |
| `SRVCHG` | `fee` | Service charge |
| `CHECK` | `check` | Check payment |
| `PAYMENT` | `ach_debit` | Electronic payment |
| `DEP` | `deposit` | Deposit |
| `ATM` | `withdrawal` | ATM withdrawal |
| `POS` | `card_purchase` | Point of sale |
| `DIRECTDEBIT` | `ach_debit` | Direct debit |
| `DIRECTDEP` | `ach_credit` | Direct deposit |
| `REPEATPMT` | `ach_debit` | Recurring payment |

#### CSV Parser (Widest Coverage)

CSV is universal but non-standardized — every bank uses different column names, date formats, amount conventions (single amount vs. split debit/credit columns), and row ordering. Zorivest adopts the **Firefly III configuration model**: a JSON/YAML config file per bank that declares column mappings.

**Bank-specific configuration registry:**

```yaml
# core/banking/configs/us/fidelity.yaml
bank_id: fidelity
bank_name: "Fidelity Investments"
country: US
detection:
  # Auto-detect this bank from CSV headers
  header_fingerprint:
    - "Date,Transaction,Name,Memo,Amount"
    - "Run Date,Action,Symbol,Description,Type,Quantity,Price ($),Commission ($),Fees ($),Accrued Interest ($),Amount ($),Settlement Date"
format:
  delimiter: ","
  encoding: utf-8
  has_header: true
  skip_rows: 0           # Lines before header row to skip
  date_format: "%m/%d/%Y"
  decimal_separator: "."
  grouping_separator: ","
columns:
  date: "Date"
  description: "Name"
  memo: "Memo"           # Appended to description
  amount: "Amount"       # Single column (positive=credit, negative=debit)
  # Alternatively:
  # debit: "Withdrawal"
  # credit: "Deposit"
  balance: null           # Fidelity CSV doesn't include running balance
  reference: null         # No reference column
  category: "Transaction" # Maps to internal category inference
post_processing:
  strip_currency_symbols: true
  invert_sign: false      # Some banks export debits as positive
  trim_whitespace: true
```

```yaml
# core/banking/configs/us/chase.yaml
bank_id: chase
bank_name: "JPMorgan Chase"
country: US
detection:
  header_fingerprint:
    - "Transaction Date,Post Date,Description,Category,Type,Amount,Memo"
format:
  delimiter: ","
  encoding: utf-8
  has_header: true
  date_format: "%m/%d/%Y"
  decimal_separator: "."
columns:
  date: "Transaction Date"
  post_date: "Post Date"
  description: "Description"
  amount: "Amount"        # Negative = debit, positive = credit
  category: "Category"    # Chase provides its own categories
  memo: "Memo"
  reference: null
  balance: null
post_processing:
  strip_currency_symbols: true
  invert_sign: false
```

```yaml
# core/banking/configs/us/schwab.yaml
bank_id: schwab
bank_name: "Charles Schwab"
country: US
detection:
  header_fingerprint:
    - "Date,Type,Check #,Description,Withdrawal,Deposit,RunningBalance"
format:
  delimiter: ","
  has_header: true
  date_format: "%m/%d/%Y"
columns:
  date: "Date"
  description: "Description"
  debit: "Withdrawal"     # Split debit/credit columns
  credit: "Deposit"
  balance: "RunningBalance"
  reference: "Check #"
  category: "Type"
post_processing:
  strip_currency_symbols: true
```

**CSV auto-detection algorithm:**

```python
def detect_bank_from_csv(file_path: str, configs: Dict[str, BankConfig]) -> BankConfig:
    """Match CSV headers against registered bank fingerprints."""
    with open(file_path, encoding='utf-8') as f:
        # Read first 5 lines for header detection
        header_lines = [f.readline().strip() for _ in range(5)]
    
    header = None
    for line in header_lines:
        if any(line.startswith(fp) for fp in sum(
            [c.detection.header_fingerprint for c in configs.values()], []
        )):
            header = line
            break
    
    if header is None:
        return None  # → Fall back to manual column mapping GUI
    
    for bank_id, config in configs.items():
        for fingerprint in config.detection.header_fingerprint:
            if header.startswith(fingerprint):
                return config
    return None
```

**Fallback — Manual Column Mapping GUI:**

When auto-detection fails (unknown bank), Zorivest presents a column mapping UI:

```
┌── Import CSV — Map Columns ──────────────────────────────────┐
│                                                               │
│  File: Downloads/BankStatement_Feb2026.csv                   │
│  Detected: 847 rows, 7 columns, comma-delimited              │
│                                                               │
│  Column 1: "Trans Date"    → [Date ▼]                        │
│  Column 2: "Post Date"     → [Post Date ▼]                   │
│  Column 3: "Description"   → [Description ▼]                 │
│  Column 4: "Category"      → [Category ▼]                    │
│  Column 5: "Type"          → [Ignore ▼]                      │
│  Column 6: "Amount"        → [Amount ▼]                      │
│  Column 7: "Memo"          → [Notes ▼]                       │
│                                                               │
│  Date format:  [MM/DD/YYYY ▼]                                │
│  Account:      [Chase Business Checking ▼]                   │
│                                                               │
│  Preview (first 5 rows):                                      │
│  ┌──────────┬──────────┬───────────────┬──────────┐          │
│  │ Date     │ Post     │ Description   │ Amount   │          │
│  ├──────────┼──────────┼───────────────┼──────────┤          │
│  │ 02/15/26 │ 02/16/26 │ AMZN MKTP US  │ -47.32   │          │
│  │ 02/14/26 │ 02/14/26 │ ACH DEPOSIT   │ 5000.00  │          │
│  └──────────┴──────────┴───────────────┴──────────┘          │
│                                                               │
│  ☑ Save this mapping as a new bank config                    │
│    Config name: [my_local_credit_union]                       │
│                                                               │
│  [Cancel]                                    [Import]         │
└───────────────────────────────────────────────────────────────┘
```

**Key:** When the user maps columns and checks "Save this mapping," Zorivest generates a YAML config file in `core/banking/configs/custom/`, making future imports auto-detected.

#### QIF Parser

Quicken Interchange Format — legacy but still exported by some banks (especially UK). Uses the `quiffen` library:

```python
from quiffen import Qif

def parse_qif(file_path: str) -> BankStatementResult:
    qif = Qif.parse(file_path)
    transactions = []
    for account in qif.accounts.values():
        for txn in account.transactions:
            transactions.append(BankTransaction(
                date=txn.date,
                description=txn.payee or txn.memo,
                amount=txn.amount,
                reference_id=txn.check_number,
                category=txn.category.name if txn.category else "other",
            ))
    return BankStatementResult(transactions=transactions)
```

#### PDF Parser (Most Complex — Last-Resort Fallback)

PDF statement parsing is inherently fragile — every bank uses a different layout. Zorivest adopts a **two-tier strategy:**

1. **Structured extraction** (text-based PDFs) — `pdfplumber` or `tabula-py` to extract tabular data
2. **OCR fallback** (scanned PDFs) — `pytesseract` or `easyocr` for image-based statements

**Per-bank PDF configuration** (inspired by [pdf_statement_reader](https://github.com/marlanperumal/pdf_statement_reader)):

```yaml
# core/banking/configs/us/fidelity_pdf.yaml
bank_id: fidelity_pdf
format: pdf
extraction_method: pdfplumber   # pdfplumber | tabula | ocr
page_area:                      # Coordinates of the transaction table
  x0: 30
  y0: 200
  x1: 580
  y1: 750
column_boundaries: [30, 120, 380, 460, 540]  # x-coordinates of column separators
header_pattern: "Date.*Description.*Withdrawals.*Deposits.*Balance"
transaction_pattern: "^(\d{2}/\d{2})\s+(.+?)\s+([\d,.]+)?\s+([\d,.]+)?\s+([\d,.]+)$"
skip_patterns:
  - "^Page \d+ of \d+"
  - "^Continued on next page"
  - "^OPENING BALANCE"
  - "^CLOSING BALANCE"
balance_pattern: "Closing Balance[:\s]+\$?([\d,.]+)"
```

**PDF extraction pipeline:**

```python
import pdfplumber
import re

def parse_pdf_statement(file_path: str, config: PDFBankConfig) -> BankStatementResult:
    transactions = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # Option A: Table extraction (structured PDFs)
            if config.extraction_method == 'pdfplumber':
                table = page.extract_table({
                    'vertical_strategy': 'explicit',
                    'horizontal_strategy': 'text',
                    'explicit_vertical_lines': config.column_boundaries,
                })
                if table:
                    for row in table:
                        if is_transaction_row(row, config):
                            transactions.append(parse_row(row, config))
            
            # Option B: Text extraction + regex (semi-structured PDFs)
            else:
                text = page.extract_text(layout=True)
                for line in text.split('\n'):
                    match = re.match(config.transaction_pattern, line.strip())
                    if match:
                        transactions.append(parse_regex_match(match, config))
    
    return BankStatementResult(transactions=transactions)
```

#### CAMT.053 Parser (EU/SEPA)

ISO 20022 `BkToCstmrStmt` — structured XML used by European banks. Rich metadata including IBAN, BIC, remittance info, and status codes.

```python
from lxml import etree

def parse_camt053(file_path: str) -> BankStatementResult:
    tree = etree.parse(file_path)
    ns = {'camt': 'urn:iso:std:iso:20022:tech:xsd:camt.053.001.08'}
    transactions = []
    for entry in tree.findall('.//camt:Ntry', ns):
        amt = Decimal(entry.find('camt:Amt', ns).text)
        direction = entry.find('camt:CdtDbtInd', ns).text  # CRDT or DBIT
        if direction == 'DBIT':
            amt = -amt
        transactions.append(BankTransaction(
            date=entry.find('camt:BookgDt/camt:Dt', ns).text,
            description=entry.find('.//camt:RmtInf/camt:Ustrd', ns).text,
            amount=amt,
            reference_id=entry.find('camt:AcctSvcrRef', ns).text,
        ))
    return BankStatementResult(transactions=transactions)
```

### Deduplication Strategy

Bank statement imports **always overlap** — users re-download monthly statements that include transactions from the previous import. Three-layer dedup prevents duplicates:

| Layer | Method | Applies To | Confidence |
|-------|--------|-----------|------------|
| **L1: FITID** | OFX Financial Transaction ID — globally unique per institution | OFX/QFX only | 100% |
| **L2: Hash** | `MD5(date + description + amount)` — composite fingerprint | All formats | ~95% (fails on same-day, same-amount transactions to same payee) |
| **L3: Window** | If L2 hash matches AND transaction falls within existing date range of imported data, skip | All formats | Used to resolve L2 collisions |

```python
def deduplicate(new_txns: List[BankTransaction],
                existing_txns: List[BankTransaction]) -> List[BankTransaction]:
    existing_fitids = {t.reference_id for t in existing_txns if t.reference_id}
    existing_hashes = {t.dedup_hash for t in existing_txns}
    
    unique_txns = []
    for txn in new_txns:
        # L1: FITID match (OFX only, 100% reliable)
        if txn.reference_id and txn.reference_id in existing_fitids:
            continue
        # L2: Hash match
        if txn.dedup_hash in existing_hashes:
            continue
        unique_txns.append(txn)
    
    return unique_txns
```

**Edge case — same-day identical transactions:** When two genuinely different transactions share the same date+description+amount (e.g., two $5.00 Starbucks charges), L2 hash collision creates a false positive. Mitigation: append a sequence counter to the hash: `MD5(date + desc + amount + N)` where N is the Nth occurrence. The import preview GUI flags these for manual confirmation.

### Manual Entry (GUI + MCP)

Every bank account must support manual balance updates and transaction entry — the universal fallback.

**GUI — Update Balance:**
```
┌── Update Balance ─────────────────────────────────┐
│  Account: [Chase Business Checking ▼]             │
│  Current Balance: $47,231.89                      │
│  Last Updated: 2026-02-18 via CSV Import          │
│                                                   │
│  New Balance:    [$____________]                   │
│  As of Date:     [2026-02-20]                     │
│  Notes:          [Monthly reconciliation]         │
│  [Cancel]                          [Update]       │
└───────────────────────────────────────────────────┘
```

**GUI — Add Manual Transaction:**
```
┌── Add Bank Transaction ───────────────────────────┐
│  Account:     [Fidelity CMA ▼]                    │
│  Date:        [2026-02-20]                        │
│  Type:        [● Deposit  ○ Withdrawal]           │
│  Amount:      [$5,000.00]                         │
│  Description: [ACH from Chase]                    │
│  Category:    [Transfer In ▼]                     │
│  Reference:   [Optional ref #]                    │
│  Notes:       [Funding for AAPL trade]            │
│  [Cancel]                             [Save]      │
└───────────────────────────────────────────────────┘
```

**MCP Tool Definitions:**

```python
# Balance management
update_bank_balance(
    account_id: str,
    balance: Decimal,
    as_of_date: str,         # ISO date
    currency: str = "USD",
    notes: str? = None
) -> AccountBalanceResult

# Manual transaction entry  
add_bank_transaction(
    account_id: str,
    date: str,               # ISO date
    amount: Decimal,         # Positive = inflow, negative = outflow
    description: str,
    category: str = "other",
    reference_id: str? = None,
    notes: str? = None
) -> TransactionResult

# File import
import_bank_statement(
    file_path: str,
    format: str = "auto",    # auto, csv, ofx, qfx, qif, pdf, camt053
    account_id: str? = None, # If not provided, detect from file or prompt
    bank: str? = None,       # For CSV: specify bank config, or auto-detect
    dry_run: bool = False    # Preview without committing
) -> ImportResult

# List bank accounts
list_bank_accounts() -> List[BankAccountSummary]
```

### AI-Assisted Import (Agent Bypass)

An agentic AI (via MCP) can bypass the file-based import pipeline entirely and submit pre-parsed transaction data directly. This is the escape hatch for any format that the built-in parsers can't handle — the agent does the extraction (OCR, screenshot reading, email parsing, copy-paste from a web portal) and submits structured data.

**MCP Tool — `submit_bank_transactions`:**

```python
submit_bank_transactions(
    account_id: str,                    # Target bank account UUID
    transactions: List[Dict],           # Pre-parsed transaction records
    closing_balance: Decimal? = None,   # Statement closing balance (for reconciliation)
    balance_date: str? = None,          # ISO date of closing balance
    source_description: str = "",       # Free-text: how the agent obtained the data
    deduplicate: bool = True            # Run dedup against existing records
) -> SubmitResult

# Each transaction dict in the list:
{
    "date": "2026-02-15",              # REQUIRED — ISO 8601 date
    "amount": -47.32,                  # REQUIRED — positive=inflow, negative=outflow
    "description": "AMZN MKTP US",     # REQUIRED — payee/description
    "post_date": "2026-02-16",         # Optional — settlement date
    "category": "card_purchase",       # Optional — from TransactionCategory enum
    "reference_id": "TXN-20260215-001",# Optional — bank reference or check number
    "running_balance": 12453.21,       # Optional — running balance after this txn
    "notes": "Amazon order #114-123"   # Optional — free-text notes
}
```

**Return value — `SubmitResult`:**

```python
{
    "success": True,
    "imported_count": 23,              # Transactions committed
    "duplicate_count": 5,              # Skipped by dedup
    "flagged_count": 2,                # Potential hash collisions (logged but imported)
    "balance_match": True,             # Did running balances reconcile?
    "balance_drift": 0.00,             # Difference from expected (0 = perfect)
    "warnings": [                      # Non-fatal issues
        "2 transactions have identical hashes — flagged as potential duplicates"
    ]
}
```

**Agent Instructions (embed in MCP tool description / system prompt):**

> **`submit_bank_transactions` — AI Agent Usage Guide**
>
> Use this tool when you have extracted bank transaction data from a source
> that the built-in parsers cannot handle. Common scenarios:
>
> 1. **OCR'd PDF** — You used vision/OCR to read a scanned bank statement image or PDF
> 2. **Screenshot** — The user shared a screenshot of their bank portal
> 3. **Copy-paste** — The user pasted raw text from their online banking dashboard
> 4. **Email** — The user forwarded a transaction alert email
> 5. **Unsupported CSV** — A CSV from a bank with no config, and the user doesn't want to map columns manually
>
> **Before calling this tool:**
>
> 1. Call `list_bank_accounts()` to get the `account_id` for the target account.
>    If the account doesn't exist, ask the user to create it first via the GUI.
>
> 2. Extract transactions into the required format. Each transaction MUST have:
>    - `date` — ISO 8601 format (`YYYY-MM-DD`). If the bank shows `02/15/2026`,
>      convert to `2026-02-15`.
>    - `amount` — Decimal number. **Inflows are positive, outflows are negative.**
>      If the bank shows `$47.32` as a debit/withdrawal, submit as `-47.32`.
>      If the bank shows `$5,000.00` as a deposit/credit, submit as `5000.00`.
>      Strip currency symbols, commas, and whitespace.
>    - `description` — The payee or transaction description exactly as shown.
>
> 3. If you can determine the `category`, map it to one of:
>    `deposit`, `withdrawal`, `transfer_in`, `transfer_out`, `fee`, `interest`,
>    `dividend`, `ach_debit`, `ach_credit`, `wire_in`, `wire_out`, `check`,
>    `card_purchase`, `refund`, `other`
>
>    If unsure, omit the field (defaults to `other`).
>
> 4. If the statement shows a closing balance, include `closing_balance` and
>    `balance_date` — Zorivest uses these to cross-check against the sum of
>    imported transactions.
>
> 5. Set `source_description` to explain how you obtained the data, e.g.:
>    `"OCR extraction from scanned Chase statement PDF (Feb 2026)"`
>    `"Parsed from user-pasted text of Ally Bank portal"`
>    This is stored as an audit trail.
>
> 6. Leave `deduplicate: true` (default) unless the user explicitly says to
>    force-import all records. Dedup uses the same 3-layer strategy as file
>    imports (FITID → hash → date window).
>
> **Validation rules applied server-side:**
>
> - `date` must parse as a valid ISO date and not be in the future
> - `amount` must be a non-zero decimal number
> - `description` must be a non-empty string (max 500 chars)
> - `category` (if provided) must be a valid `TransactionCategory` value
> - Duplicate `dedup_hash` values within the same submission are flagged
> - If `closing_balance` is provided, the server validates that:
>   `existing_balance + sum(new_transactions) ≈ closing_balance` (within ±$0.01)
>   A mismatch produces a warning but does NOT block the import.

**Example — Agent processes an OCR'd PDF:**

```
User: "Here's my Relay bank statement PDF for February. Import the transactions."
Agent: [Uses vision to OCR the PDF, extracts 34 transactions]
Agent: [Calls list_bank_accounts() → finds "Relay Operating" with id "abc-123"]
Agent: [Calls submit_bank_transactions(
    account_id="abc-123",
    transactions=[
        {"date": "2026-02-01", "amount": -1500.00, "description": "WIRE TO IBKR", "category": "wire_out"},
        {"date": "2026-02-03", "amount": 8750.00, "description": "CLIENT PAYMENT ACH", "category": "ach_credit"},
        ...  # 32 more transactions
    ],
    closing_balance=23412.67,
    balance_date="2026-02-28",
    source_description="OCR extraction from scanned Relay Financial PDF statement (Feb 2026)"
)]
```

**Example — Agent processes pasted text:**

```
User: "Here are my recent Chase transactions:
  02/18  AMAZON.COM          -89.99
  02/17  PAYROLL DIRECT DEP   5,432.10
  02/16  STARBUCKS #4521      -6.25"

Agent: [Parses the text, normalizes dates and amounts]
Agent: [Calls submit_bank_transactions(
    account_id="chase-biz-456",
    transactions=[
        {"date": "2026-02-18", "amount": -89.99, "description": "AMAZON.COM", "category": "card_purchase"},
        {"date": "2026-02-17", "amount": 5432.10, "description": "PAYROLL DIRECT DEP", "category": "ach_credit"},
        {"date": "2026-02-16", "amount": -6.25, "description": "STARBUCKS #4521", "category": "card_purchase"}
    ],
    source_description="Parsed from user-pasted text of Chase Business Checking portal"
)]
```

### Bank Configuration Registry

Inspired by [Firefly III's import-configurations](https://github.com/firefly-iii/import-configurations) repository (559 commits, 30+ countries, 100+ contributors), Zorivest ships with pre-built configs for the 15 banks from the research:

| Country | Bank | Config File | CSV | OFX | PDF | Notes |
|---------|------|-------------|-----|-----|-----|-------|
| US | Fidelity CMA | `us/fidelity.yaml` | ✅ | ✅ QFX | ✅ | `Accounts_History.csv` export; QFX from account downloads |
| US | Charles Schwab | `us/schwab.yaml` | ✅ | ✅ OFX | ✅ | Split debit/credit columns; running balance included |
| US | Chase | `us/chase.yaml` | ✅ | ✅ QFX | ✅ | Chase provides its own categories; negative=debit |
| US | Ally Bank | `us/ally.yaml` | ✅ | ✅ QFX | ✅ | Standard format |
| US | Wealthfront | `us/wealthfront.yaml` | ✅ | ❌ | ✅ | CSV only; no OFX export |
| US | Relay | `us/relay.yaml` | ✅ QBO | ❌ | ✅ | QuickBooks CSV format; up to 20 sub-accounts |
| US | Mercury | `us/mercury.yaml` | ✅ QBO | ❌ | ✅ | QuickBooks CSV and NetSuite CSV formats |
| CA | TD Bank | `ca/td.yaml` | ✅ | ✅ OFX | ✅ | Canadian date format (DD/MM/YYYY) |
| UK | Starling | `gb/starling.yaml` | ✅ | ❌ | ✅ | UK date format; GBP/EUR accounts |
| UK | Revolut | `gb/revolut.yaml` | ✅ | ❌ | ✅ | Multi-currency CSV; `ofxstatement-revolut` plugin exists |
| IN | HDFC | `in/hdfc.yaml` | ✅ | ❌ | ✅ | INR; NetBanking CSV export |
| IN | IDFC First | `in/idfc.yaml` | ✅ | ❌ | ✅ | 3-in-1 account CSV |
| AU | Macquarie | `au/macquarie.yaml` | ✅ | ✅ OFX | ✅ | AUD; standard format |
| Global | Wise | `global/wise.yaml` | ✅ | ❌ | ✅ | Multi-currency; one CSV per currency balance |
| — | *Custom* | `custom/*.yaml` | ✅ | — | — | User-created via column mapping GUI |

Users can create custom configs via the column mapping GUI — saved to `core/banking/configs/custom/` and auto-loaded on subsequent imports.

### Import Preview & Reconciliation Dashboard

Before committing any import, Zorivest shows a preview dashboard:

```
┌── Import Preview ─────────────────────────────────────────────┐
│  File: BankStatement_Feb2026.ofx                              │
│  Format: OFX v2.0 (auto-detected)                            │
│  Bank: Fidelity Investments                                   │
│  Account: ****4521 (Checking)                                │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Summary                                             │     │
│  ├─────────────────────────────────────────────────────┤     │
│  │ Total transactions:     147                         │     │
│  │ New (will import):       23  ← unique               │     │
│  │ Duplicates (skipped):   124  ← already in database  │     │
│  │ Flagged for review:       2  ← possible L2 collisions│    │
│  │                                                     │     │
│  │ Date range: 2026-01-01 → 2026-02-20                │     │
│  │ Net change: +$3,412.67                              │     │
│  │ Closing balance: $47,231.89                         │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ⚠ 2 transactions flagged for review:                        │
│  ┌──────────┬──────────────────┬──────────┬─────────────┐   │
│  │ Date     │ Description      │ Amount   │ Issue       │   │
│  ├──────────┼──────────────────┼──────────┼─────────────┤   │
│  │ 02/15/26 │ STARBUCKS #4521  │ -$5.75   │ Hash match  │   │
│  │ 02/15/26 │ STARBUCKS #4521  │ -$5.75   │ Possible dup│   │
│  └──────────┴──────────────────┴──────────┴─────────────┘   │
│                                                               │
│  [Cancel]     [Import 23 new]     [Import all 25]            │
└───────────────────────────────────────────────────────────────┘
```

### Features

- **Auto-detect file format** from extension + magic bytes + header sniffing
- **Auto-detect bank** from CSV column headers using fingerprint matching
- **Three-layer deduplication** (FITID → hash → date window) prevents duplicates across overlapping imports
- **Manual column mapping GUI** for unknown banks with config save/reuse
- **Import preview** with duplicate/collision flagging before commit
- **Rolling balance reconciliation** — if the bank's CSV includes a running balance column, Zorivest validates that imported transactions produce the expected balance progression (catches missing transactions)
- **Multi-currency support** — Wise/Revolut CSVs contain per-currency statements; Zorivest tracks separate `CurrencyBalance` per bank account
- **Sub-account hierarchy** — Relay's 20 sub-accounts import as child records under a parent `BankAccount`
- **PDF encrypted statement handling** — auto-decrypt password-protected PDFs via `pikepdf`
- **Category inference** from bank-provided categories (Chase) or OFX `trntype` codes, with manual override
- **Export** — bank + brokerage transactions → unified CSV for tax accountant or TurboTax import

### Challenges

| Challenge | Mitigation |
|-----------|------------|
| CSV formats change when banks update their export UI | Header fingerprints are flexible (startsWith match); version the config files; users can update custom configs via GUI |
| PDF layouts are fragile and break across statement redesigns | Per-bank PDF configs with `page_area` and `column_boundaries`; fallback to full-page text extraction + regex |
| Same-day identical transactions cause hash collisions | Sequence counter in hash; import preview flags collisions for manual review |
| International date formats (DD/MM/YYYY vs MM/DD/YYYY) | Per-bank `date_format` config; ambiguous dates flagged in preview |
| Encoding issues (Latin-1, Windows-1252, UTF-8 BOM) | Auto-detect encoding via `chardet`; fallback chain: UTF-8 → Latin-1 → Windows-1252 |
| Password-protected PDF statements | `pikepdf` decryption; prompt user for password in GUI |
| Banks may include non-transaction rows (summaries, headers, page breaks) | `skip_patterns` regex list in per-bank config; strip known non-data rows |
| Amount localization (€1.234,56 vs $1,234.56) | Per-bank `decimal_separator` and `grouping_separator` in config (Firefly III issue #4106 pattern) |

### Dependencies

| Library | Version | Purpose | License | Size |
|---------|---------|---------|---------|------|
| `ofxtools` | ≥0.9 | OFX/QFX parsing (SGML + XML) | MIT | Stdlib only |
| `pdfplumber` | ≥0.11 | PDF text + table extraction | MIT | ~2MB |
| `tabula-py` | ≥2.9 | PDF table extraction (Java-based) | MIT | Requires JRE |
| `pikepdf` | ≥9.0 | PDF decryption | MPL-2.0 | ~15MB (QPDF) |
| `quiffen` | ≥2.0 | QIF format parsing | MIT | Pure Python |
| `chardet` | ≥5.0 | Encoding auto-detection | LGPL | Pure Python |
| `lxml` | ≥5.0 | CAMT.053 XML parsing | BSD | ~8MB |
| `pandas` | (existing) | CSV parsing and data manipulation | BSD | Already in deps |

> **Note:** `tabula-py` requires a Java Runtime Environment (JRE). If JRE is unavailable, fall back to `pdfplumber`-only extraction. The dependency is optional.

---

## Reference

- **Source documents:** [Local Trading Journal Software Search](file:///p:/zorivest/_inspiration/import_research/Local%20Trading%20Journal%20Software%20Search.md), [Retail Trading Platform & Broker Analysis](file:///p:/zorivest/_inspiration/import_research/Retail%20Trading%20Platform%20%26%20Broker%20Analysis.md), [Bank Account Integration Analysis](file:///p:/zorivest/_inspiration/import_research/Bank%20Account%20Integration%20Analysis.md), [Trader Banking Preferences: 2025 Analysis](file:///p:/zorivest/_inspiration/import_research/Trader%20Banking%20Preferences_%202025%20Analysis.md)
- **Cross-referenced:** [_tjs_inspired_features.md](file:///p:/zorivest/docs/_tjs_inspired_features.md) (§1–10 for original TJS feature plans)
- **Open-source references (§26):** [ofxtools](https://github.com/csingley/ofxtools), [ofxparse](https://github.com/jseutter/ofxparse), [ofxstatement](https://github.com/kedder/ofxstatement) (50+ bank plugins), [csv2ofx](https://github.com/reubano/csv2ofx), [Firefly III data-importer](https://github.com/firefly-iii/data-importer), [Firefly III import-configurations](https://github.com/firefly-iii/import-configurations) (559 commits, 30+ countries), [bank-statement-parser](https://github.com/felgru/bank-statement-parser), [pdf_statement_reader](https://github.com/marlanperumal/pdf_statement_reader), [quiffen](https://github.com/isaacharrisholt/quiffen)
- **Date:** 2026-02-20, updated with TJS merges + API integrations + bank statement import
