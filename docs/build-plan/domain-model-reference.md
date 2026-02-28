# Domain Model Reference

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) — Referenced by [Phase 1](01-domain-layer.md), [Phase 2](02-infrastructure.md), [Phase 5](05-mcp-server.md), [Phase 6](06-gui.md) ([Trades](06b-gui-trades.md), [Planning](06c-gui-planning.md), [Accounts](06d-gui-accounts.md), [Settings](06f-gui-settings.md), [Tax](06g-gui-tax.md), [Calculator](06h-gui-calculator.md))

---

The domain is organized around **five temporal concerns** plus **two tool modules**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ZORIVEST DOMAIN MODEL                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ══ PRESENT ══════════════════════════════════════════════════════════  │
│                                                                         │
│  Account                                                                │
│  ├── account_id: str (PK)                                              │
│  ├── name: str                                                          │
│  ├── account_type: AccountType  ←── enum:                              │
│  │     BROKER | BANK | REVOLVING | INSTALLMENT | IRA | K401            │
│  ├── institution: str           (e.g., "Interactive Brokers", "Chase") │
│  ├── currency: str              (e.g., "USD")                          │
│  ├── is_tax_advantaged: bool    (IRA/401K = True)                      │
│  ├── notes: str                                                         │
│  ├── sub_accounts: list[str]   (optional sub-account identifiers, §26) │
│  ├── balance_source: BalanceSource (MANUAL/CSV_IMPORT/OFX_IMPORT, §26) │
│  └── balance_snapshots: list[BalanceSnapshot]                          │
│                                                                         │
│  BalanceSnapshot                                                        │
│  ├── id: int (PK)                                                       │
│  ├── account_id: str (FK → Account)                                    │
│  ├── datetime: datetime                                                 │
│  └── balance: Decimal                                                   │
│                                                                         │
│  ══ PAST ═════════════════════════════════════════════════════════════  │
│                                                                         │
│  Trade                                                                  │
│  ├── exec_id: str (PK)                                                 │
│  ├── time: datetime                                                     │
│  ├── instrument: str                                                    │
│  ├── action: TradeAction  ←── enum: BOT | SLD                         │
│  ├── quantity: float                                                    │
│  ├── price: float                                                       │
│  ├── account_id: str (FK → Account)                                    │
│  ├── commission: float                                                  │
│  ├── realized_pnl: float                                               │
│  ├── images: list[ImageAttachment]                                     │
│  └── report: TradeReport (optional, 1:1)                               │
│                                                                         │
│  TradeReport  (post-trade review / meta analysis)                      │
│  ├── id: int (PK)                                                       │
│  ├── trade_id: str (FK → Trade, unique)                                │
│  ├── setup_quality: int (1-5 rating)                                   │
│  ├── execution_quality: int (1-5 rating)                               │
│  ├── followed_plan: bool                                                │
│  ├── emotional_state: str                                               │
│  ├── lessons_learned: str (text)                                       │
│  ├── tags: list[str]  (e.g., ["momentum", "reversal", "news"])        │
│  ├── images: list[ImageAttachment]  (review screenshots)              │
│  └── created_at: datetime                                               │
│                                                                         │
│  ══ FUTURE ═══════════════════════════════════════════════════════════  │
│                                                                         │
│  Watchlist                                                              │
│  ├── id: int (PK)                                                       │
│  ├── name: str                  (e.g., "Momentum Plays", "Earnings")  │
│  ├── description: str                                                   │
│  ├── tickers: list[WatchlistItem]                                      │
│  └── created_at / updated_at: datetime                                 │
│                                                                         │
│  WatchlistItem                                                          │
│  ├── id: int (PK)                                                       │
│  ├── watchlist_id: int (FK → Watchlist)                                │
│  ├── ticker: str                (e.g., "SPY", "AAPL")                 │
│  ├── added_at: datetime                                                 │
│  └── notes: str                                                         │
│                                                                         │
│  TradePlan  (forward-looking trade thesis)                             │
│  ├── id: int (PK)                                                       │
│  ├── ticker: str                                                        │
│  ├── direction: TradeAction     (BOT = bullish, SLD = bearish)         │
│  ├── conviction: ConvictionLevel  ←── enum: LOW | MEDIUM | HIGH | MAX │
│  ├── strategy_name: str         (e.g., "Gap & Go", "VWAP Bounce")     │
│  ├── strategy_description: str  (rich text — the thesis)              │
│  ├── entry_price: float                                                 │
│  ├── stop_loss: float                                                   │
│  ├── target_price: float                                                │
│  ├── entry_conditions: str      (technical indicators / triggers)      │
│  ├── exit_conditions: str       (when to close regardless)             │
│  ├── timeframe: str             (e.g., "intraday", "swing 2-5 days")  │
│  ├── risk_reward_ratio: float   (computed from entry/stop/target)      │
│  ├── status: PlanStatus  ←── enum: DRAFT | ACTIVE | EXECUTED | EXPIRED│
│  ├── linked_trade_id: str (FK → Trade, nullable)  ← after execution  │
│  ├── images: list[ImageAttachment]  (chart setups, annotated screens) │
│  ├── account_id: str (FK → Account, nullable)                         │
│  └── created_at / updated_at: datetime                                 │
│                                                                         │
│  ══ SHARED ═══════════════════════════════════════════════════════════  │
│                                                                         │
│  ImageAttachment  (polymorphic — attached to Trade, TradeReport,       │
│  │                 TradePlan, or standalone)                            │
│  ├── id: int (PK)                                                       │
│  ├── owner_type: str  ("trade" | "report" | "plan")                   │
│  ├── owner_id: str    (FK to the owning entity)                        │
│  ├── data: bytes      (standardized WebP)                               │
│  ├── thumbnail: bytes (pre-generated WebP)                              │
│  ├── mime_type: str    (always "image/webp")                            │
│  ├── caption: str                                                       │
│  ├── width / height: int                                                │
│  ├── file_size: int                                                     │
│  └── created_at: datetime                                               │
│                                                                         │
│  ══ DISPLAY MODES (core feature — affects all GUI + API output) ══════ │
│                                                                         │
│  TotalPortfolioBalance                                                  │
│  ├── Computed: SUM of latest balance for every Account                 │
│  │   (includes negative balances: credit cards, loans)                 │
│  ├── Example: IBKR $437,903 + IRA $85,200 + Bank $12,450              │
│  │            + Credit Card -$2,100 + Auto Loan -$15,300               │
│  │            = Total Portfolio: $518,153                               │
│  ├── Used as: Reference denominator for percentage mode                │
│  └── Updated: Whenever any account balance snapshot changes            │
│                                                                         │
│  DisplayMode  (GUI state — not persisted per-trade, persisted as       │
│  │             user preference in settings)                            │
│  ├── hide_dollars: bool (default False)                                │
│  │   └── When False: ALL dollar amounts masked as "••••••"             │
│  │       Affects: balances, P&L, position sizes, risk amounts,         │
│  │       trade prices, commissions — every $ value in the GUI          │
│  │                                                                      │
│  ├── hide_percentages: bool (default False)                            │
│  │   └── When False: ALL percentage values masked as "••%"             │
│  │       Can be hidden independently from dollars                      │
│  │                                                                      │
│  └── percent_mode: bool (default False)                                │
│      └── When True: Dollar values ALSO show their % of Total Portfolio │
│          Example: Position Size: $32,370 (6.25%)                       │
│          Example: Today's P&L: $1,200 (0.23%)                          │
│          Example: Account Risk (1R): $4,379 (0.85%)                    │
│          The % is always relative to TotalPortfolioBalance              │
│                                                                         │
│  Three toggle buttons in toolbar:                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐                                           │
│  │  $   │ │  %   │ │ %ref │                                           │
│  │ hide │ │ hide │ │ mode │                                           │
│  └──────┘ └──────┘ └──────┘                                           │
│                                                                         │
│  State combinations:                                                    │
│  │ $ visible │ % visible │ % mode │ What you see                      │
│  │───────────│───────────│────────│─────────────────────────────────── │
│  │   ✓       │    ✓      │   off  │ $437,903 (normal)                 │
│  │   ✓       │    ✓      │   on   │ $437,903 (84.52%)                 │
│  │   ✗       │    ✓      │   on   │ •••••• (84.52%)                   │
│  │   ✗       │    ✗      │   on   │ •••••• (••%)                      │
│  │   ✗       │    ✓      │   off  │ •••••• (no % shown — mode off)    │
│  │   ✓       │    ✗      │   on   │ $437,903 (••%)  ← hides % only   │
│                                                                         │
│  Screen-sharing safe: Toggle $ hide ON → no financial data visible.    │
│  Add % hide ON → even relative proportions are hidden.                 │
│                                                                         │
│  ══ ACCOUNT REVIEW (guided balance update workflow) ══════════════════ │
│                                                                         │
│  AccountReview  (periodic guided process to update all balances)       │
│  │                                                                      │
│  │  The user initiates "Account Review" from toolbar or dashboard.     │
│  │  The app walks through EACH account, one at a time:                 │
│  │                                                                      │
│  │  For each Account:                                                   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │
│  │  │  Account Review: IBKR Margin (Broker)                         │ │
│  │  │  Institution: Interactive Brokers                              │ │
│  │  │  Last Balance: $437,903.03  (2025-07-02 13:36)                │ │
│  │  │  ─────────────────────────────────────────────────            │ │
│  │  │                                                                │ │
│  │  │  Update method:                                                │ │
│  │  │    ○ API (auto-fetch from TWS)     ← for BROKER accounts      │ │
│  │  │    ● Manual entry                  ← for all other types       │ │
│  │  │                                                                │ │
│  │  │  New Balance: [___________]                                    │ │
│  │  │                                                                │ │
│  │  │  Change: +$2,450.00 (+0.56%)   ← computed live                │ │
│  │  │                                                                │ │
│  │  │  [Skip]  [Update & Next ▶]                                    │ │
│  │  └────────────────────────────────────────────────────────────────┘ │
│  │                                                                      │
│  │  After all accounts reviewed:                                       │
│  │  ┌────────────────────────────────────────────────────────────────┐ │
│  │  │  Review Complete ✓                                             │ │
│  │  │  Updated: 4 of 5 accounts                                     │ │
│  │  │  Skipped: 1 (Auto Loan — unchanged)                           │ │
│  │  │                                                                │ │
│  │  │  New Total Portfolio: $520,603  (was $518,153, +$2,450)        │ │
│  │  │                                                                │ │
│  │  │  [Done]                                                        │ │
│  │  └────────────────────────────────────────────────────────────────┘ │
│  │                                                                      │
│  │  Behavior rules:                                                    │
│  │  • BROKER accounts: Offer "API fetch" button (calls TWS/IBKR API)  │
│  │  • All other types: Manual entry with last balance pre-filled       │
│  │  • Balance only logged if value actually changed (dedup)            │
│  │  • "Skip" moves to next account without saving                     │
│  │  • Progress bar: "Account 2 of 5"                                  │
│  │  • Keyboard shortcut: Tab → enter amount → Enter → next            │
│  │  • Total Portfolio updates live as each account is confirmed        │
│  │  • MCP tool: `get_account_review_checklist` returns guided prompts   │
│  │  • Can also be triggered on schedule (e.g., daily at market close)  │
│  └── Priority: P0 — core feature, built with Account entity            │
│                                                                         │
│  ══ TOOLS (pure functions, no persistence) ═══════════════════════════ │
│                                                                         │
│  PositionSizeCalculator                                                 │
│  ├── Input:  balance, risk_pct, entry, stop, target                    │
│  └── Output: account_risk_1r, risk_per_share, share_size,             │
│              position_size, position_to_account_pct,                    │
│              reward_risk_ratio, potential_profit                        │
│                                                                         │
│  ══ ANALYTICS & ENRICHMENT (post-trade analysis, auto-calculations) ═══ │
│                                                                         │
│  RoundTrip  (groups executions into entry→exit pairs)                  │
│  ├── id: int (PK)                                                       │
│  ├── account_id: str (FK → Account)                                    │
│  ├── instrument: str                                                    │
│  ├── direction: TradeAction  (BOT = long round-trip, SLD = short)      │
│  ├── entry_executions: list[str] (FK → Trade.exec_id)                  │
│  ├── exit_executions: list[str] (FK → Trade.exec_id)                   │
│  ├── entry_avg_price: Decimal                                           │
│  ├── exit_avg_price: Decimal                                            │
│  ├── total_quantity: float                                              │
│  ├── realized_pnl: Decimal  (computed from avg prices × quantity)      │
│  ├── total_commission: Decimal                                          │
│  ├── opened_at: datetime  (earliest entry execution time)              │
│  ├── closed_at: datetime  (latest exit execution time, nullable)       │
│  ├── status: RoundTripStatus  ←── enum: OPEN | CLOSED | PARTIAL       │
│  └── holding_period_seconds: int  (computed)                            │
│  Source: Build Plan Expansion §3                                        │
│  Priority: P1 — Core for reliable trade history normalization           │
│                                                                         │
│  ExcursionMetrics  (1:1 extension on Trade — computed from bar data)   │
│  ├── trade_exec_id: str (FK → Trade.exec_id, unique)                  │
│  ├── mfe_dollars: Decimal    (Maximum Favorable Excursion in $)        │
│  ├── mfe_pct: float          (MFE as % of entry price)                 │
│  ├── mae_dollars: Decimal    (Maximum Adverse Excursion in $)          │
│  ├── mae_pct: float          (MAE as % of entry price)                 │
│  ├── bso_pct: float          (Best Scale Out % — exit efficiency)      │
│  ├── data_source: str        (which market data provider supplied bars) │
│  └── computed_at: datetime                                              │
│  Source: Build Plan Expansion §7 (merged with TJS §3)                   │
│  Priority: P1 — High-value auto-enrichment; requires market data bars   │
│                                                                         │
│  IdentifierMapping  (CUSIP/ISIN/SEDOL → ticker resolution cache)       │
│  ├── id: int (PK)                                                       │
│  ├── id_type: IdentifierType  ←── enum: CUSIP | ISIN | SEDOL | FIGI   │
│  ├── id_value: str                                                      │
│  ├── ticker: str              (resolved ticker symbol)                  │
│  ├── exchange: str            (e.g., "NYSE", "NASDAQ")                  │
│  ├── security_type: str       (e.g., "Common Stock", "ETF")            │
│  ├── source: str              (e.g., "openfigi", "finnhub", "manual")  │
│  ├── confidence: float        (0.0-1.0)                                 │
│  ├── resolved_at: datetime                                              │
│  └── expires_at: datetime     (cache TTL — delisted securities don't)  │
│  Source: Build Plan Expansion §5                                        │
│  Priority: P2 — Needed for IBKR FlexQuery imports with CUSIP codes      │
│                                                                         │
│  TransactionLedger  (per-trade fee decomposition)                      │
│  ├── id: int (PK)                                                       │
│  ├── trade_exec_id: str (FK → Trade.exec_id)                          │
│  ├── fee_type: FeeType  ←── enum: COMMISSION | EXCHANGE | REGULATORY  │
│  │     | ECN | CLEARING | PLATFORM | OTHER                             │
│  ├── amount: Decimal                                                    │
│  ├── currency: str  (default "USD")                                     │
│  └── description: str  (e.g., "SEC Transaction Fee")                   │
│  Source: Build Plan Expansion §9 (merged with TJS §7)                   │
│  Priority: P1 — High analytical value for fee optimization              │
│                                                                         │
│  OptionsStrategy  (multi-leg options grouping)                          │
│  ├── id: int (PK)                                                       │
│  ├── name: str                (auto-detected or user-assigned)          │
│  ├── strategy_type: StrategyType  ←── enum: VERTICAL | IRON_CONDOR    │
│  │     | BUTTERFLY | CALENDAR | STRADDLE | STRANGLE | CUSTOM           │
│  ├── underlying: str          (e.g., "SPY")                             │
│  ├── leg_exec_ids: list[str]  (FK → Trade.exec_id)                    │
│  ├── net_debit_credit: Decimal  (total premium paid/received)          │
│  ├── max_profit: Decimal      (theoretical, computed from strikes)     │
│  ├── max_loss: Decimal        (theoretical)                             │
│  ├── breakeven_prices: list[Decimal]                                    │
│  └── created_at: datetime                                               │
│  Source: Build Plan Expansion §8                                        │
│  Priority: P2 — Required for accurate options P&L                       │
│                                                                         │
│  MistakeEntry  (trade mistake categorization with cost attribution)    │
│  ├── id: int (PK)                                                       │
│  ├── trade_id: str (FK → Trade.exec_id)                                │
│  ├── category: MistakeCategory  ←── enum: EARLY_EXIT | LATE_EXIT      │
│  │     | OVERSIZED | NO_STOP | REVENGE_TRADE | FOMO_ENTRY              │
│  │     | IGNORED_PLAN | OVERTRADING | CHASING | OTHER                   │
│  ├── estimated_cost: Decimal  (what the mistake cost in $)             │
│  ├── notes: str               (user reflection)                         │
│  ├── auto_detected: bool      (True if classified by rule, not user)   │
│  └── created_at: datetime                                               │
│  Source: Build Plan Expansion §17 (new from TJS §5)                     │
│  Priority: P1 — Strong behavior-change feedback loop                    │
│                                                                         │
│  BrokerModel  (broker constraint configuration)                        │
│  ├── broker_id: str (PK)      (e.g., "ibkr_pro", "alpaca_paper")      │
│  ├── name: str                (display name)                            │
│  ├── pdt_rule: bool           (Pattern Day Trader restriction applies) │
│  ├── pdt_threshold: Decimal   ($25,000 for US brokers)                 │
│  ├── settlement_days: int     (T+1 for US equities and listed options) │
│  ├── max_leverage: dict       ({AssetClass: Decimal})                  │
│  ├── routing_type: RoutingType ←── enum: PFOF | DMA | HYBRID          │
│  ├── commission_schedule: dict (fee structure per asset class)          │
│  ├── supported_order_types: list[str]                                   │
│  ├── supported_asset_classes: list[str]                                 │
│  └── trading_hours: dict      (market open/close, pre/post windows)    │
│  Source: Build Plan Expansion §23                                       │
│  Priority: P2 — Start minimal (PDT, settlement, leverage)               │
│                                                                         │
│  BankTransaction  (imported bank statement transaction)                │
│  ├── id: int (PK)                                                       │
│  ├── account_id: str (FK → Account)                                    │
│  ├── date: date               (transaction date)                        │
│  ├── post_date: date          (settlement date, optional)              │
│  ├── description: str         (payee / memo from bank)                  │
│  ├── amount: Decimal          (positive = credit, negative = debit)    │
│  ├── category: TransactionCategory ←── enum: DEPOSIT | WITHDRAWAL     │
│  │     | TRANSFER_IN | TRANSFER_OUT | FEE | INTEREST | DIVIDEND        │
│  │     | ACH_DEBIT | ACH_CREDIT | WIRE_IN | WIRE_OUT | CHECK           │
│  │     | CARD_PURCHASE | REFUND | ATM | OTHER                          │
│  ├── reference_id: str        (check #, FITID from OFX, internal ref) │
│  ├── dedup_hash: str          (MD5 of date+desc+amount for dedup)      │
│  ├── source: BalanceSource    ←── enum: MANUAL | CSV_IMPORT            │
│  │     | OFX_IMPORT | QIF_IMPORT | PDF_IMPORT | AGENT_SUBMIT           │
│  ├── import_batch_id: str     (groups transactions from same import)    │
│  └── created_at: datetime                                               │
│  Source: Build Plan Expansion §26                                       │
│  Priority: P1 (phased — 26A: CSV+OFX, 26B: QIF, 26C: PDF+CAMT)        │
│                                                                         │
│  ══ TAX ESTIMATOR (comprehensive tax toolset for active traders) ══════ │
│                                                                         │
│  ⚠️  This is a calculator/estimator, NOT tax advice or filing tool.    │
│      Disclaimer required on every output. Always consult a CPA.         │
│                                                                         │
│  ── NEW DOMAIN ENTITIES ─────────────────────────────────────────────  │
│                                                                         │
│  TaxLot  (individual purchase lot for cost basis tracking)             │
│  ├── lot_id: str (PK)                                                   │
│  ├── account_id: str (FK → Account)                                    │
│  ├── ticker: str                                                        │
│  ├── open_date: datetime  (purchase date)                              │
│  ├── close_date: datetime (nullable — None = still open)               │
│  ├── quantity: float                                                    │
│  ├── cost_basis: Decimal  (per-share, adjusted for wash sales)         │
│  ├── proceeds: Decimal    (per-share, populated on close)              │
│  ├── wash_sale_adjustment: Decimal  (deferred loss added to basis)     │
│  ├── is_closed: bool                                                    │
│  ├── holding_period_days: int  (computed from open/close dates)        │
│  ├── is_long_term: bool  (holding_period >= 366 days)                  │
│  └── linked_trade_ids: list[str]  (FK → Trade.exec_id)                │
│                                                                         │
│  WashSaleChain  (tracks deferred losses rolling across trades)         │
│  ├── chain_id: str (PK)                                                │
│  ├── ticker: str                                                        │
│  ├── original_loss: Decimal                                             │
│  ├── deferred_amount: Decimal  (loss trapped in chain)                 │
│  ├── entries: list[WashSaleEntry]                                      │
│  │   ├── lot_id: str (FK → TaxLot)                                     │
│  │   ├── event_type: str  ("disallowed" | "absorbed" | "released")     │
│  │   ├── event_date: datetime                                           │
│  │   └── amount: Decimal                                                │
│  ├── is_resolved: bool  (True when chain fully unwound)                │
│  └── created_at: datetime                                               │
│                                                                         │
│  TaxProfile  (user's tax configuration — stored in settings)           │
│  ├── filing_status: FilingStatus  ←── enum:                            │
│  │     SINGLE | MARRIED_JOINT | MARRIED_SEPARATE | HEAD_OF_HOUSEHOLD   │
│  ├── tax_year: int  (e.g., 2026)                                       │
│  ├── federal_bracket: float  (marginal rate, e.g. 0.37)               │
│  ├── state_tax_rate: float  (e.g., 0.05 for 5%)                       │
│  ├── state: str  (e.g., "NY", "TX")                                   │
│  ├── prior_year_tax: Decimal  (for safe harbor calculation)            │
│  ├── agi_estimate: Decimal  (for NIIT threshold check)                 │
│  ├── capital_loss_carryforward: Decimal  (from prior year)             │
│  ├── wash_sale_method: WashSaleMatchingMethod  ←── enum:               │
│  │     CONSERVATIVE | AGGRESSIVE                                        │
│  │     (Conservative: equity options = substantially identical to stock)│
│  │     (Aggressive: different CUSIP = not identical)                    │
│  ├── default_cost_basis: CostBasisMethod  ←── enum:                    │
│  │     FIFO | LIFO | HIFO | SPEC_ID | MAX_LT_GAIN | MAX_LT_LOSS |    │
│  │     MAX_ST_GAIN | MAX_ST_LOSS                                        │
│  ├── include_drip_wash_detection: bool (default True)                  │
│  ├── include_spousal_accounts: bool (default False)                    │
│  ├── section_475_elected: bool (default False — Mark-to-Market)        │
│  └── section_1256_eligible: bool (default False — futures 60/40)       │
│                                                                         │
│  QuarterlyEstimate  (estimated tax payment tracking)                   │
│  ├── id: int (PK)                                                       │
│  ├── tax_year: int                                                      │
│  ├── quarter: int  (1-4)                                                │
│  ├── due_date: date  (Apr 15, Jun 15, Sep 15, Jan 15)                  │
│  ├── required_payment: Decimal  (computed)                              │
│  ├── actual_payment: Decimal  (user-entered)                           │
│  ├── method: str  ("safe_harbor_100" | "safe_harbor_110" |             │
│  │                  "current_year_90" | "annualized")                   │
│  ├── cumulative_ytd_gains: Decimal  (at time of calculation)           │
│  └── underpayment_penalty_risk: Decimal  (estimated penalty if short)  │
│                                                                         │
│  ── FEATURE MODULES ─────────────────────────────────────────────────  │
│                                                                         │
│  ┌─ MODULE A: Core Tax Engine ──────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  A1. Cost Basis Method Selection                                  │  │
│  │      8 methods: FIFO, LIFO, HIFO, Specific ID,                   │  │
│  │      Maximize LT Gain, Maximize LT Loss,                         │  │
│  │      Maximize ST Gain, Maximize ST Loss                           │  │
│  │      (matches IBKR Tax Optimizer parity for seamless integration) │  │
│  │                                                                    │  │
│  │  A2. ST vs LT Holding Period Classification                      │  │
│  │      Held < 366 days = short-term (ordinary rates up to 37%)     │  │
│  │      Held ≥ 366 days = long-term (0%, 15%, or 20%)               │  │
│  │                                                                    │  │
│  │  A3. Tax Lot Tracking                                             │  │
│  │      Every purchase creates a TaxLot. Every sale closes lots      │  │
│  │      based on the selected cost basis method. Track open lots     │  │
│  │      with unrealized gain/loss and days-to-LT threshold.          │  │
│  │                                                                    │  │
│  │  A4. Options Assignment/Exercise Pairing                          │  │
│  │      When a put is assigned → premium reduces stock cost basis.   │  │
│  │      When a call is exercised → premium added to sale proceeds.   │  │
│  │      Link option trades to resulting stock positions.              │  │
│  │                                                                    │  │
│  │  A5. YTD P&L by Symbol                                           │  │
│  │      Year-to-date realized gains/losses per ticker, broken down   │  │
│  │      by ST vs LT. Critical for knowing position before year-end. │  │
│  │                                                                    │  │
│  │  A6. Capital Loss Carryforward Tracking                           │  │
│  │      $3,000/year deduction limit vs ordinary income.              │  │
│  │      Track unused losses rolling forward across tax years.         │  │
│  │                                                                    │  │
│  │  A7. Tax-Advantaged Account Exclusion                             │  │
│  │      IRA/401K accounts: skip capital gains tax entirely.          │  │
│  │      ⚠️  BUT: IRA purchases still count for cross-account         │  │
│  │      wash sale detection (losses in IRA are permanently destroyed)│  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ MODULE B: Wash Sale Engine ─────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  B1. Basic Wash Sale Detection                                    │  │
│  │      30-day window (before and after sale). Loss deferred,        │  │
│  │      added to replacement lot cost basis.                         │  │
│  │                                                                    │  │
│  │  B2. Wash Sale Chain Tracking                                     │  │
│  │      Deferred losses that roll forward through repeated trades    │  │
│  │      of the same ticker. Track full chain until resolved.         │  │
│  │      Show "trapped losses" that can't be deducted this year.      │  │
│  │                                                                    │  │
│  │  B3. Cross-Account Wash Sale Aggregation                          │  │
│  │      Check ALL accounts (taxable + IRA + spouse) for              │  │
│  │      substantially identical purchases within 30-day window.      │  │
│  │      IRA wash sales PERMANENTLY DESTROY the loss.                 │  │
│  │                                                                    │  │
│  │  B4. Options-to-Stock Wash Sale Matching (Configurable)           │  │
│  │      Method 1 (Conservative): Equity options on AAPL =            │  │
│  │        substantially identical to AAPL stock → triggers wash sale │  │
│  │      Method 2 (Aggressive): Different CUSIP = not identical       │  │
│  │      Let user choose to match their CPA's interpretation.         │  │
│  │                                                                    │  │
│  │  B5. DRIP Wash Sale Detection                                     │  │
│  │      Dividend reinvestment auto-purchases within 30-day window    │  │
│  │      can disallow an entire harvested loss. Flag DRIP conflicts.  │  │
│  │                                                                    │  │
│  │  B6. Auto-Rebalance Wash Sale Warning                             │  │
│  │      Warn if automated DCA or rebalancing could trigger wash      │  │
│  │      sales against manually harvested losses.                     │  │
│  │                                                                    │  │
│  │  B7. Spousal Account Cross-Wash Detection                         │  │
│  │      When filing jointly, spouse's accounts must be checked for   │  │
│  │      wash sale conflicts. Optional — toggled via TaxProfile.      │  │
│  │                                                                    │  │
│  │  B8. Wash Sale Prevention Alerts (Proactive)                      │  │
│  │      BEFORE a trade: "Selling AAPL at a loss now would trigger    │  │
│  │      a wash sale — you bought shares 28 days ago. Wait 3 days."   │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ MODULE C: Tax Optimization Tools ───────────────────────────────┐  │
│  │                                                                    │  │
│  │  C1. Pre-Trade "What-If" Tax Simulator                            │  │
│  │      "What if I sell 100 shares of SPY?" → calculates tax impact  │  │
│  │      using selected lot method, shows ST vs LT classification,    │  │
│  │      wash sale risk, and estimated tax in dollars.                 │  │
│  │      MCP tool: simulate_tax_impact                                │  │
│  │                                                                    │  │
│  │  C2. Tax-Loss Harvesting Scanner                                  │  │
│  │      Scan portfolio for open positions with unrealized losses.    │  │
│  │      Filter out positions that would trigger wash sales.           │  │
│  │      Rank by harvestable loss amount.                             │  │
│  │                                                                    │  │
│  │  C3. Tax-Smart Replacement Suggestions                            │  │
│  │      When harvesting a loss, suggest correlated but NOT            │  │
│  │      substantially identical replacement securities.               │  │
│  │      e.g., Sell VOO at a loss → buy IVV to maintain exposure.     │  │
│  │                                                                    │  │
│  │  C4. Lot Matcher / Close Specific Lots                            │  │
│  │      UI/MCP tool to pick exactly which lots to close on a sale.   │  │
│  │      Show each open lot: basis, unrealized gain/loss, holding     │  │
│  │      period, days until LT threshold.                             │  │
│  │                                                                    │  │
│  │  C5. Post-Trade Lot Reassignment Window                           │  │
│  │      Allow changing lot-matching method after execution but       │  │
│  │      before settlement (T+1). Undo button for tax mistakes.       │  │
│  │                                                                    │  │
│  │  C6. ST vs LT Tax Rate Dollar Comparison                         │  │
│  │      "If you sell now: $2,340 tax (ST @ 37%). Hold 12 more days:  │  │
│  │       $950 tax (LT @ 15%). Waiting saves $1,390."                 │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ MODULE D: Quarterly Estimated Tax Payments ─────────────────────┐  │
│  │                                                                    │  │
│  │  D1. Safe Harbor Calculator                                       │  │
│  │      Two methods to avoid IRS underpayment penalty:               │  │
│  │      • Pay ≥ 90% of current year tax liability, OR                │  │
│  │      • Pay ≥ 100% of prior year liability (110% if AGI > $150K)  │  │
│  │      Tool recommends the lower amount.                            │  │
│  │                                                                    │  │
│  │  D2. Annualized Income Method                                     │  │
│  │      For income that varies wildly quarter-to-quarter.            │  │
│  │      Calculate quarterly payments proportional to actual income   │  │
│  │      per period (IRS Form 2210, Schedule AI logic).               │  │
│  │      Avoids overpaying in slow quarters.                          │  │
│  │                                                                    │  │
│  │  D3. Quarterly Payment Due Date Tracker + Alerts                  │  │
│  │      Track 4 deadlines: Apr 15, Jun 15, Sep 15, Jan 15.          │  │
│  │      Show amount paid vs required per quarter.                    │  │
│  │      Alert when payment deadline approaching.                     │  │
│  │                                                                    │  │
│  │  D4. Underpayment Penalty Preview                                 │  │
│  │      If under-paid for a quarter, estimate the IRS penalty        │  │
│  │      (federal short-term rate + 3%, ~8% annually for 2025/2026). │  │
│  │      Show penalty accrual per quarter to motivate timely payment. │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ MODULE E: Tax Bracket & Rate Integration ───────────────────────┐  │
│  │                                                                    │  │
│  │  E1. Marginal Tax Rate Calculator                                 │  │
│  │      Input: AGI, filing status → compute effective + marginal     │  │
│  │      federal rate, plus state tax rate. Feeds all tax estimates    │  │
│  │      to show actual dollars owed, not just gain/loss amounts.     │  │
│  │                                                                    │  │
│  │  E2. NIIT (Net Investment Income Tax) Alert                       │  │
│  │      3.8% surtax on investment income when MAGI exceeds:          │  │
│  │      $200K single / $250K married joint.                          │  │
│  │      Flag when approaching threshold. Include in estimates.       │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ MODULE F: Reports & Dashboard ──────────────────────────────────┐  │
│  │                                                                    │  │
│  │  F1. Year-End Tax Position Summary                                │  │
│  │      Aggregate: total ST gains, LT gains, wash sale adjustments,  │  │
│  │      estimated tax at user's bracket, remaining loss harvesting   │  │
│  │      potential, capital loss carryforward balance.                 │  │
│  │                                                                    │  │
│  │  F2. Deferred Loss Carryover Report                               │  │
│  │      Dashboard showing total loss "trapped" in wash sale chains.  │  │
│  │      Real P&L vs reported P&L. Critical for day traders.         │  │
│  │                                                                    │  │
│  │  F3. Tax Alpha Savings Summary                                    │  │
│  │      Running tally of tax saved through lot optimization and      │  │
│  │      loss harvesting YTD. "Your tax-smart decisions have saved    │  │
│  │      an estimated $X,XXX this year."                              │  │
│  │                                                                    │  │
│  │  F4. Error Check / Transaction Audit                              │  │
│  │      Scan imported trade history for anomalies: missing cost      │  │
│  │      basis, duplicate exec_ids, impossible prices, corporate      │  │
│  │      action gaps. Catch data issues before tax calculations.      │  │
│  │                                                                    │  │
│  │  F5. Broker 1099-B Reconciliation (Future)                        │  │
│  │      Import broker's reported numbers, compare against            │  │
│  │      Zorivest's calculations. Flag discrepancies.                 │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ MODULE G: Advanced / Conditional ───────────────────────────────┐  │
│  │                                                                    │  │
│  │  G1. Section 475 Mark-to-Market Election Toggle                   │  │
│  │      For Trader Tax Status: all losses become ordinary            │  │
│  │      (no $3K cap), no wash sales apply. Settings toggle.          │  │
│  │      Must be elected by April 15 for following tax year.          │  │
│  │                                                                    │  │
│  │  G2. Section 1256 (60/40) Futures Support                         │  │
│  │      If trading /ES, /NQ etc: 60% LT / 40% ST treatment          │  │
│  │      regardless of holding period. Only if futures in scope.      │  │
│  │                                                                    │  │
│  │  G3. Forex Income Worksheet (IBKR-specific)                       │  │
│  │      Review forex income/loss from multi-currency accounts.       │  │
│  │      Only if forex trading is in scope.                           │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ── INPUTS & OUTPUTS ────────────────────────────────────────────────  │
│                                                                         │
│  TaxEstimator (core calculator — pure math, zero dependencies)         │
│  ├── Input:  trades[], tax_lots[], accounts[], tax_profile,            │
│  │           wash_sale_chains[], quarterly_estimates[]                  │
│  └── Output: per module:                                                │
│      ├── Core: st_gains, lt_gains, wash_sale_adjustments,              │
│      │         lots_by_symbol, holding_period_status                    │
│      ├── Wash: detected_wash_sales[], chain_status[], alerts[]         │
│      ├── Optimization: harvestable_losses[], what_if_results,          │
│      │                 replacement_suggestions[], lot_options[]         │
│      ├── Quarterly: required_payments[], penalty_risk, safe_harbor     │
│      ├── Rates: effective_rate, marginal_rate, niit_applicable,        │
│      │          estimated_tax_dollars, st_vs_lt_savings                 │
│      └── Reports: ytd_summary, deferred_losses, tax_alpha,            │
│                   audit_errors[], reconciliation_diff                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```
