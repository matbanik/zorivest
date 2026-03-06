# Zorivest — Application Purpose & User Flow Discovery

> This document is a guided questionnaire and user flow blueprint. Answer the questions, refine the flows, and use the results to drive the domain model and development priorities.

---

## Table of Contents

1. [Vision & Purpose](#1-vision--purpose)
2. [Target User Profile](#2-target-user-profile)
3. [Core Problem Statement](#3-core-problem-statement)
4. [Feature Areas & Questions](#4-feature-areas--questions)
5. [Proposed User Flows](#5-proposed-user-flows)
6. [Data Sources & Integrations](#6-data-sources--integrations)
7. [Access Patterns](#7-access-patterns)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Out of Scope (For Now)](#9-out-of-scope-for-now)

---

## 1. Vision & Purpose

### Questions to Answer

| # | Question | Your Answer |
|---|----------|-------------|
| 1.1 | **In one sentence, what does Zorivest do?** | Zorivest is an MCP-first IDE tool for AI-assisted trading meta-cognition — it processes market data and community sentiment into composite daily briefs, helps plan and track opportunities, and enables deep post-trade reflection, all through agentic AI collaboration in the IDE chat. Trades happen elsewhere; Zorivest owns the thinking. |
| 1.2 | **Who is the primary user?** | Retail traders and investors with technical background in programming and data analysis who use an AI-powered IDE (Antigravity, Cursor, etc.) as their primary work environment. |
| 1.3 | **What is the single most important thing Zorivest should do better than any alternative?** | AI prompt/workflow library for trading meta-cognition — composite daily briefs built from multiple timeframes and community sentiment, Socratic post-trade reflection, and pattern discovery across trade history. The library IS the product. |
| 1.4 | **What tools/apps do you currently use for this workflow?** | TC2000, TradingView, custom TradeLogger app, broker apps (IBKR TWS), Antigravity IDE with AI. The problem: these are fragmented and none provide AI meta-cognition. |
| 1.5 | **What is the #1 pain point with your current workflow?** | No integrated system for meta-cognition with AI that combines: (1) multi-timeframe market awareness, (2) community sentiment from free retail sources, (3) personal trade reflection and pattern discovery, and (4) risk/tax calculation in context. Data is scattered, insights are ephemeral. |
| 1.6 | **Should Zorivest ever be a cloud/web app, or always local-first?** | Local-first, encrypted. Future paid SaaS features: aggregator services, remote access, cloud backup/sync across devices. Core always runs locally. |

---

## 2. Target User Profile

### Questions to Answer

| # | Question | Your Answer |
|---|----------|-------------|
| 2.1 | **Trading style?** (mix since this is more about having holistic view and planing trades and maintaining watchlists and getting hihgly customized reports and meta reviews) | |
| 2.2 | **Typical instruments?** (US equities, ETFs Options, Futures, Crypto, Forex) asset does not matter as much as the fact that we want to be able to support all of them. Only limitation will be for now USD currency as main currency of value. | |
| 2.3 | **How many trades per day/week/month?** does not matter | |
| 2.4 | **How many accounts do you actively manage?** No limits, could be up to few dozen | |
| 2.5 | **Do you trade from a single computer or multiple?** For now we will support trading from a single computer. | |
| 2.6 | **Do you use an AI assistant (Claude, ChatGPT) as part of your trading workflow today?** Using Antigravity agentic AI as primary AI assistant. | |

---

## 3. Core Problem Statement

### Questions to Answer

| # | Question | Your Answer |
|---|----------|-------------|
| 3.1 | **Before a trade**: What information do you wish you had organized in one place? | A composite daily brief synthesizing multiple timeframes (past month → past week → last night → this morning) for my watchlist, with community sentiment from free retail sources (Reddit, StockTwits, Finviz). Risk/tax implications of potential plays. Time horizon awareness for each opportunity. |
| 3.2 | **During a trade**: What do you need to see/calculate quickly? | Zorivest is execution-agnostic — trades happen on other platforms (IBKR TWS, broker apps, even phone calls). Zorivest can optionally import data as trades happen, but the focus is on the data produced for analysis, not the execution itself. |
| 3.3 | **After a trade**: What do you wish you could easily review/learn from? | Socratic reflection with the AI: what was happening mentally (FOMO, conviction, doubt) and technically (did I follow the plan? what did I miss?). Pattern discovery across trade history. Recording the full reasoning chain. Building an evolving prompt/workflow library from lessons learned. |
| 3.4 | **End of month/quarter/year**: What reports or summaries do you need? | Narrative performance attribution (not just tables): "73% of your alpha came from morning momentum. Your afternoon mean reversion trades destroyed value." Cumulative edge tracking — big wins are rare, small wins are cumulative. Tax impact summaries. |
| 3.5 | **What data do you currently lose or forget to capture?** | Community sentiment at time of entry, mental/emotional state during the trade, the full reasoning chain that led to the decision, multi-timeframe market context that existed when the plan was made. |
| 3.6 | **How important is security/privacy of your trading data?** | Critical. Local-first, encrypted. All data stays on the machine. The AI prompt/workflow library contains personal trading edge — this is IP. |

---

## 4. Feature Areas & Questions

### 4.1 Trade Logging (Past)

| # | Question | Your Answer |
|---|----------|-------------|
| 4.1.1 | **Should trades auto-import from IBKR, or is manual entry acceptable?** | |
| 4.1.2 | **Do you need to track partial fills separately, or just the final execution?** | |
| 4.1.3 | **What metadata matters most per trade?** (instrument, price, qty, P&L — what else? Timeframe? Strategy name? Setup type?) | |
| 4.1.4 | **How many screenshots per trade do you typically want?** (entry chart, exit chart, daily context, thesis notes?) | |
| 4.1.5 | **Do you annotate screenshots before saving them?** (draw on them, add arrows/text?) | |
| 4.1.6 | **Should the app group related executions into a single "trade"?** (e.g., scale-in with 3 buys + 1 sell = 1 trade) | |

### 4.2 Trade Planning (Future)

| # | Question | Your Answer |
|---|----------|-------------|
| 4.2.1 | **Do you write trade plans before entering a trade?** If so, what do they contain? | |
| 4.2.2 | **What does "conviction level" mean to you?** (How do you rate it today? What factors determine HIGH vs LOW?) | |
| 4.2.3 | **Do you use specific strategies repeatedly?** List some (e.g., "Gap & Go", "VWAP reclaim", "Earnings momentum", "Mean reversion") | |
| 4.2.4 | **Should a plan auto-populate the position size calculator?** (plan's entry/stop/target → calculator) | |
| 4.2.5 | **How should a plan's lifecycle work?** DRAFT → ACTIVE → EXECUTED or EXPIRED? Can you cancel? Re-activate? | |
| 4.2.6 | **Should the AI assistant be able to suggest trade plans?** Or just record your plans? | |

### 4.3 Trade Review / Reports (Past → Learning)

| # | Question | Your Answer |
|---|----------|-------------|
| 4.3.1 | **What does your ideal post-trade review look like?** (Rate the setup? Execution? Did you follow the plan? Lessons?) | |
| 4.3.2 | **Do you tag trades?** (e.g., "momentum", "reversal", "news-driven", "overtraded", "revenge trade") | |
| 4.3.3 | **Do you track emotional state?** (e.g., "calm", "FOMO", "frustrated", "confident") | |
| 4.3.4 | **What aggregate reports do you want?** Examples: win rate by strategy, avg R per setup type, P&L by month, biggest winners/losers, performance by time of day | |
| 4.3.5 | **Do you want the AI to analyze your trade journal and suggest patterns?** (e.g., "You lose money on afternoon reversal trades") | |

### 4.4 Accounts, Portfolio Balance & Display Modes (Present)

| # | Question | Your Answer |
|---|----------|-------------|
| 4.4.1 | **For non-broker accounts (bank, credit, loans), what do you track?** Just balance? Or transactions too? | |
| 4.4.2 | **Do you want a "net worth" / Total Portfolio Balance dashboard across all accounts?** (Sum of all account balances including negative ones like credit cards and loans) | |
| 4.4.3 | **How often do you snapshot balances?** (Daily? Weekly? Only when it changes?) | |
| 4.4.4 | **Should bank/credit accounts auto-import, or is manual balance entry fine?** | |
| 4.4.5 | **Do you transfer money between accounts?** Should those transfers be tracked? | |
| 4.4.6 | **Account types you manage?** (Broker, Bank, Revolving/Credit, Installment/Loan, IRA, 401K — which do you have?) | |

### 4.4a Account Review (Guided Balance Update)

A core feature: a step-by-step wizard that walks through each account to update balances, with API auto-fetch for broker accounts and manual entry for others. Shows live change calculations and updates Total Portfolio in real-time.

| # | Question | Your Answer |
|---|----------|-------------|
| 4.4a.1 | **How often would you run an Account Review?** (Daily at market close? Weekly? On-demand only?) | |
| 4.4a.2 | **Should it auto-trigger?** (e.g., daily at 4:05 PM ET after market close?) Or always manual? | |
| 4.4a.3 | **For broker accounts, should it always try API first?** Or give you the choice each time? | |
| 4.4a.4 | **Should the AI be able to prompt you?** (e.g., "It's been 3 days since your last Account Review") | |

### 4.4b Display Modes (Privacy & Percentage View)

Three toolbar toggles that control how financial data appears everywhere in the GUI:

| Toggle | What it does |
|--------|-------------|
| **$ hide** | Masks ALL dollar amounts as `••••••` — safe for screen sharing |
| **% hide** | Masks ALL percentage values as `••%` — independent from $ hide |
| **% mode** | Shows every dollar value's % of Total Portfolio alongside it (e.g., `$32,370 (6.25%)`) |

| # | Question | Your Answer |
|---|----------|-------------|
| 4.4b.1 | **Do you screen-share while trading?** (Streams, calls, recordings?) This is the primary use case for $ hide. | |
| 4.4b.2 | **Is the % of Total Portfolio view useful?** Seeing every value as a proportion of your total portfolio? | |
| 4.4b.3 | **Should display mode persist across sessions?** Or always reset to "show everything" on startup? | |
| 4.4b.4 | **Keyboard shortcuts for toggles?** (e.g., Ctrl+$ to toggle dollar hide, Ctrl+% for percent hide) | |

### 4.5 Watchlists (Future)

| # | Question | Your Answer |
|---|----------|-------------|
| 4.5.1 | **How many watchlists do you maintain?** What categories? (e.g., "Daily Movers", "Earnings This Week", "Long-term Holds") | |
| 4.5.2 | **What info per ticker?** (Just the symbol? Price alerts? Notes? Technical levels? Sector?) | |
| 4.5.3 | **Should watchlist items link to trade plans?** (Watchlist ticker → "I'm watching this" → Plan created → Trade executed) | |
| 4.5.4 | **Do you want price alerts or notifications?** Or is this purely organizational? | |

### 4.6 Position Size Calculator (Tool)

| # | Question | Your Answer |
|---|----------|-------------|
| 4.6.1 | **Is the calculator from the existing Trade Logger spec exactly what you want?** Any changes? | |
| 4.6.2 | **Should the calculator support options/futures position sizing, or equities only for now?** | |
| 4.6.3 | **Do you want a "portfolio heat" view?** (Total risk across all open positions) | |

### 4.7 Tax Estimation (Tool — Future)

| # | Question | Your Answer |
|---|----------|-------------|
| 4.7.1 | **What's the primary tax concern?** (Wash sales? Estimating quarterly tax payments? Year-end summary? Loss harvesting?) | |
| 4.7.2 | **Do you use a CPA, or do your own taxes?** | |
| 4.7.3 | **What tax-related reports does your CPA need?** (Form 8949 data? Total gains/losses? Wash sale adjustments?) | |
| 4.7.4 | **Do you actively do tax-loss harvesting?** Should the app suggest opportunities? | |
| 4.7.5 | **Do you need estimated quarterly tax calculations?** | |

### 4.8 AI Assistant / MCP Integration

| # | Question | Your Answer |
|---|----------|-------------|
| 4.8.1 | **What should the AI assistant be able to DO?** (Read trades? Create plans? Review journal? Calculate position size? All of the above?) | |
| 4.8.2 | **Should the AI have read-only access, or also write access?** (e.g., can it create a trade plan for you, or just suggest?) | |
| 4.8.3 | **What natural language queries should work?** Examples: "Show me my worst trades this month", "What's my win rate on gap trades?", "Create a plan for AAPL long at 195" | |
| 4.8.4 | **Should the AI see your screenshots?** (Send chart images to Claude for analysis?) | |

---

## 5. Proposed User Flows

### Flow 1: Morning Pre-Market Routine

```
User opens Zorivest
    │
    ├─► Dashboard shows:
    │   • Account balances (last snapshot)
    │   • Open positions (if tracked)
    │   • Active trade plans (ACTIVE status)
    │   • Watchlist highlights
    │
    ├─► User reviews watchlist
    │   • Checks overnight news/moves
    │   • Adds/removes tickers
    │
    ├─► User creates a Trade Plan
    │   • Selects ticker from watchlist (or types new)
    │   • Sets direction (long/short)
    │   • Defines entry, stop, target
    │   • Writes strategy thesis
    │   • Attaches chart screenshot (paste from clipboard)
    │   • Sets conviction level
    │   • Saves as ACTIVE
    │
    └─► Position size calculator auto-fills from plan
        • Shows risk, share size, position size
        • User confirms the numbers make sense
```

**❓ Questions about this flow:**
- Do you do a morning routine like this? What's missing?
- Where do you get your watchlist ideas? (Scanner? Twitter? AI?)
- Do you want alerts when a plan's entry price is hit?

---

### Flow 2: Trade Execution & Live Logging

```
User connects to IBKR TWS
    │
    ├─► Trades auto-import via API
    │   • New executions appear in trades table
    │   • Deduplication by exec_id
    │   • Commission and P&L update when available
    │
    ├─► User attaches screenshot during/after trade
    │   • Ctrl+V pastes chart from clipboard
    │   • Or clicks "Add Screenshot" → file picker
    │   • Adds caption: "Entry — SPY broke above VWAP"
    │
    ├─► Trade links to active plan (if one exists for this ticker)
    │   • Plan status changes: ACTIVE → EXECUTED
    │   • Plan's entry/stop/target compared to actual execution
    │
    └─► Real-time P&L visible in trades table
```

**❓ Questions about this flow:**
- Do you execute from Zorivest, or from TWS/broker directly?
- Should Zorivest auto-match trades to plans by ticker, or manual linking?
- Do you take screenshots during the trade, or only after?

---

### Flow 3: Post-Trade Review / Journaling

```
User selects a completed trade (or group of related fills)
    │
    ├─► Opens Trade Report panel
    │   • Rates setup quality (1-5 stars)
    │   • Rates execution quality (1-5 stars)
    │   • Did you follow the plan? (Yes/No)
    │   • Emotional state during trade (dropdown or free text)
    │   • Lessons learned (free text)
    │   • Tags: ["momentum", "followed-plan", "morning-session"]
    │
    ├─► Reviews screenshots
    │   • Entry chart, exit chart, context chart
    │   • Can add more screenshots after the fact
    │   • Can annotate? (draw on image, or just caption text?)
    │
    ├─► Compares plan vs actual
    │   • Planned entry: $195.00 → Actual: $195.23
    │   • Planned stop: $193.00 → Actual: $193.50 (tightened)
    │   • Planned target: $200.00 → Actual: exited at $198.50
    │
    └─► Saves review → updates trade record
```

**❓ Questions about this flow:**
- Do you review every trade, or just the notable ones?
- How soon after a trade do you review? Same day? Weekend?
- Do you want the AI to prompt you for reviews? ("You have 3 unreviewed trades")

---

### Flow 4: Weekly/Monthly Performance Review

```
User opens Reports section
    │
    ├─► Summary dashboard
    │   • Total P&L this week/month/quarter/year
    │   • Win rate (overall and by strategy)
    │   • Average R-multiple per trade
    │   • Largest winner / largest loser
    │   • Equity curve chart
    │
    ├─► Drill-down views
    │   • Performance by strategy tag
    │   • Performance by time of day
    │   • Performance by ticker/sector
    │   • Performance by conviction level
    │   • "Did I follow the plan?" correlation with P&L
    │
    ├─► AI-assisted insights (via MCP)
    │   • "Your afternoon trades have a 30% win rate vs 65% morning"
    │   • "You tend to exit winners too early (avg 0.8R vs planned 2R)"
    │   • "Revenge trades after losses cost you $2,400 this month"
    │
    └─► Export
        • PDF report
        • CSV export for further analysis
        • Data for CPA (tax relevant)
```

**❓ Questions about this flow:**
- Which of these reports matter most to you right now?
- Do you track R-multiples today? (actual profit ÷ planned risk)
- What time periods matter? (daily summary? weekly? monthly only?)

---

### Flow 5: AI Assistant Interaction (via MCP)

```
User is in their IDE (Cline/Cursor/Claude) working on something else
    │
    ├─► Types: "What were my best trades this week?"
    │   └─► AI calls list_trades + get_trade_reports tools
    │       └─► Returns formatted summary with P&L, tags, ratings
    │
    ├─► Types: "Create a trade plan for NVDA long at 140, stop 135, target 155"
    │   └─► AI calls create_trade_plan tool
    │       └─► Returns plan with computed R:R ratio (3:1), position size
    │
    ├─► Types: "Show me my SPY trade screenshots from today"
    │   └─► AI calls get_trade_screenshots tool
    │       └─► Returns image content inline (MCP image type)
    │
    ├─► Types: "What's my exposure to tech stocks right now?"
    │   └─► AI calls list_trades + accounts tools, aggregates by sector
    │
    ├─► Types: "Calculate position size: $50k account, 1% risk, entry 195, stop 192"
    │   └─► AI calls calculate_position_size tool
    │       └─► Returns: 166 shares, $32,370 position, R:R depends on target
    │
    ├─► Types: "Any wash sale risks if I sell AAPL today?"
    │   └─► AI calls find_wash_sales tool
    │       └─► Returns: "You bought AAPL 28 days ago. Selling at a loss
    │            would trigger wash sale. Wait 3 more days."
    │
    ├─► Types: "What's my total portfolio balance?"
    │   └─► AI calls get_portfolio_balance tool
    │       └─► Returns: "Total Portfolio: $518,153 across 5 accounts
    │            (IBKR 84.52%, IRA 16.44%, Bank 2.40%, Credit -0.41%, Loan -2.95%)"
    │
    ├─► Types: "Start account review"
    │   └─► AI calls start_account_review tool
    │       └─► Walks through each account: "IBKR Margin — last balance $437,903.
    │            Fetch from API or enter manually?"
    │       └─► User: "fetch from API"
    │       └─► AI: "Updated to $440,353. Next: Roth IRA, last $85,200..."
    │
    └─► Types: "Show my portfolio in percentages only, hide dollar amounts"
        └─► AI calls set_display_mode tool
            └─► Returns: "Display mode updated: $ hidden, % visible, % mode ON"
```

**❓ Questions about this flow:**
- Which of these AI interactions are most valuable to you?
- Do you want the AI to be proactive? (e.g., alert you about wash sales before you trade)
- Should the AI be able to change display modes? Or is that GUI-only?
- Should the AI have access to your watchlists and plans, or just executed trades?

---

### Flow 6: Account Management & Portfolio Dashboard

```
User opens Accounts section
    │
    ├─► Portfolio header (always visible):
    │   ┌──────────────────────────────────────────────────────────┐
    │   │  Total Portfolio: $518,153          [$hide] [%hide] [%ref]│
    │   │  (or ••••••  if $ hide is ON)                            │
    │   └──────────────────────────────────────────────────────────┘
    │
    ├─► Account list view
    │   • IBKR Margin (Broker) — $437,903 (84.52%)    🟢 API
    │   • Roth IRA (IRA) — $85,200 (16.44%)           🔒 tax-advantaged
    │   • Chase Checking (Bank) — $12,450 (2.40%)     ✏️ manual
    │   • Chase Sapphire (Revolving) — -$2,100         ✏️ manual
    │   • Auto Loan (Installment) — -$15,300           ✏️ manual
    │   ─────────────────────────────────────────────
    │   Total Portfolio: $518,153
    │
    │   (With % mode ON: percentages shown. With $ hide ON: all $ masked)
    │
    ├─► [Start Account Review] button → guided balance update wizard
    │   • Walks through each account one-by-one
    │   • BROKER: offers API fetch or manual entry
    │   • Others: manual entry with last balance pre-filled
    │   • Shows change: +$2,450 (+0.56%) live
    │   • Skip unchanged accounts
    │   • Summary at end: "Updated 4/5, New Total: $520,603"
    │
    ├─► Click on individual account
    │   • Balance history chart (line graph over time)
    │   • Recent trades (for broker accounts)
    │   • Connection status: API-connected / manual
    │   • Tax badge: taxable / tax-advantaged
    │
    └─► Display mode toggles (toolbar):
        ┌──────┐ ┌──────┐ ┌──────┐
        │  $   │ │  %   │ │ %ref │
        │ hide │ │ hide │ │ mode │
        └──────┘ └──────┘ └──────┘
        • $ hide → all dollar values become "••••••" (screen-sharing safe)
        • % hide → all percentages become "••%" (independent toggle)
        • % mode → show % of Total Portfolio next to every $ value
```

**❓ Questions about this flow:**
- Is the Total Portfolio Balance (including negatives) the right "denominator" for % mode?
- Should each account card show its % of the total portfolio?
- Do you want a balance history chart per account, or just a table of snapshots?
- How prominently should the display mode toggles appear? (Toolbar? Status bar? Menu?)

---

### Flow 7: End-of-Day Routine

```
Market closes
    │
    ├─► Account Review (guided or automatic)
    │   • App prompts: "Market closed — start Account Review?"
    │   • Or auto-triggers if scheduled
    │   • Walks through each account (API fetch for IBKR, manual for others)
    │   • Updates Total Portfolio Balance
    │
    ├─► Review today's trades
    │   • Trade table filtered to today
    │   • Total P&L for the day (shown as $ and % of portfolio if % mode ON)
    │   • Number of trades, win rate
    │
    ├─► Journal unreviewed trades
    │   • Badge shows "3 trades need review"
    │   • Quick-review mode: rate + tag + one-line lesson
    │
    ├─► Update watchlists for tomorrow
    │   • Remove tickers that played out
    │   • Add new tickers from evening scan
    │
    └─► Close app (or leave running for next day)
```

**❓ Questions about this flow:**
- Do you have an end-of-day routine? What does it look like?
- Should the app remind you about unreviewed trades?
- Should Account Review auto-trigger at market close, or always be manual?
- Do you scan for tickers in the evening? How? (TradingView? Finviz? AI?)

---

### Flow 8: Account Review (Guided Balance Update)

```
User clicks [Account Review] in toolbar or dashboard
    │
    ├─► Progress indicator: "Account 1 of 5"
    │
    ├─► Step 1: IBKR Margin (Broker)
    │   ┌────────────────────────────────────────────────┐
    │   │  Last Balance: $437,903.03  (2025-07-02 13:36) │
    │   │  Update method: [API fetch] [Manual entry]     │
    │   │  → User clicks [API fetch]                     │
    │   │  → Fetches $440,353.03 from TWS                │
    │   │  Change: +$2,450.00 (+0.56%)                   │
    │   │  [Skip]  [Update & Next ▶]                     │
    │   └────────────────────────────────────────────────┘
    │
    ├─► Step 2: Roth IRA (IRA) — manual
    │   │  Last Balance: $85,200.00
    │   │  New Balance: [_85,200_] ← pre-filled, user edits
    │   │  Change: $0.00 (0.00%)
    │   │  [Skip]  [Update & Next ▶]
    │
    ├─► Step 3: Chase Checking (Bank) — manual
    │   │  ...
    │
    ├─► Step 4: Chase Sapphire (Revolving) — manual
    │   │  Last Balance: -$2,100.00
    │   │  New Balance: [_-1,800_]
    │   │  Change: +$300.00 (debt reduced)
    │   │  [Skip]  [Update & Next ▶]
    │
    ├─► Step 5: Auto Loan (Installment) — manual
    │   │  Last Balance: -$15,300.00
    │   │  User clicks [Skip] — unchanged this week
    │
    └─► Summary
        ┌──────────────────────────────────────────────┐
        │  Review Complete ✓                            │
        │  Updated: 4 of 5 accounts                    │
        │  Skipped: 1 (Auto Loan)                      │
        │                                              │
        │  Old Total Portfolio: $518,153                │
        │  New Total Portfolio: $521,253 (+$3,100)      │
        │                                              │
        │  [Done]                                      │
        └──────────────────────────────────────────────┘
```

**❓ Questions about this flow:**
- Is the step-by-step wizard the right UX, or would you prefer a table where you edit all balances at once?
- Should accounts with API connections (IBKR) auto-update without asking?
- For manual accounts, should the last balance be pre-filled (so you just hit Enter if unchanged)?
- Would you ever want to update just one account, or always review all?

---

## 6. Data Sources & Integrations

| Source | Integration Type | Priority | Questions |
|--------|-----------------|----------|-----------|
| **Interactive Brokers TWS** | API (ibapi) | P0 | Is this the only broker? |
| **TradingView** | Price fetch (tradingview_ta) | P0 | Do you need more than closing price? |
| **Manual entry** | GUI forms | P0 | For non-IBKR accounts, plans, reviews |
| **Clipboard** | Ctrl+V screenshots | P0 | Primary image input method? |
| **Other brokers?** | TBD | P2? | Do you use any other brokers? (Schwab, Fidelity, etc.) |
| **Bank APIs?** | Plaid? Manual? | P3? | Worth the complexity for balance tracking? |
| **News/sentiment?** | API or scrape | P3? | Do you want market context attached to trades? |
| **Scanner/screener?** | TradingView? Finviz? | P2? | Auto-populate watchlists? |

---

## 7. Access Patterns

### How will users access Zorivest?

| Access Point | Use Case | Priority |
|-------------|----------|----------|
| **Electron + React Desktop GUI** | Primary interface: trade table, charts, screenshots, reviews. Modern web-tech UI with TypeScript, communicates with Python backend via REST on localhost | P0 |
| **TypeScript MCP Server** | AI agent access via IDE: "show trades", "create plan", "calculate size". TypeScript SDK (reference implementation) calls Python REST API | P0 |
| **Python REST API (FastAPI)** | Backend service: serves both the Electron UI and MCP server on localhost. Also available for direct programmatic access | P0 |
| **CLI** | Quick commands: `zorivest balance`, `zorivest plan SPY` | P2? |
| **Mobile?** | View balances/trades on phone — React UI could be adapted for web/mobile later | P3 / Out of scope? |

> **Hybrid Architecture Decision**: The UI layer (Electron + React) and MCP server (TypeScript) communicate with the Python backend exclusively via REST on localhost. This provides a modern, polished UI with hot reload during development, while keeping the Python backend for SQLCipher encryption, Interactive Brokers API, and financial math. See `DESIGN_PROPOSAL.md` for the full architecture.

---

## 8. Non-Functional Requirements

| Requirement | Question | Your Answer |
|-------------|----------|-------------|
| **Privacy** | Must all data be local + encrypted? Can any data go to cloud? | |
| **Startup time** | How fast should the app open? (<1s? <3s? Doesn't matter?) | |
| **Database size** | How many trades do you expect? (1K? 10K? 100K lifetime?) | |
| **Image storage** | How many screenshots per month? (affects DB size) | |
| **Backup** | How should backups work? (Auto? Manual? To where?) | |
| **Portability** | Should the app run from a USB drive? Or installed normally? | |
| **Multi-device** | Same database on multiple computers? (Dropbox sync?) | |
| **Offline** | Must work without internet? (Calculator yes, IBKR connection no) | |

---

## 9. Out of Scope (For Now)

Explicitly listing what Zorivest is **NOT** (at least initially):

| Not This | Why |
|----------|-----|
| ❌ Order execution / auto-trading | Zorivest is a journal/planner, not a trading bot |
| ❌ Real-time streaming quotes | Use your broker's platform for that |
| ❌ Social features / sharing | This is private, encrypted, single-user |
| ❌ Options chain analysis | Complex; use broker tools or dedicated apps |
| ❌ Full accounting / bookkeeping | Use QuickBooks/Wave for that |
| ❌ Mobile app | Desktop-first; mobile is P3 at earliest |
| ❌ Tax filing | Estimates only; always consult CPA |

**❓ Do you disagree with any of these? Should anything move into scope?**

---

## How to Use This Document

1. **Answer the questions** in each section (fill in the "Your Answer" columns)
2. **Review the user flows** — mark which ones match your actual workflow, modify what doesn't fit, add flows that are missing
3. **Prioritize** — highlight which flows are "must have now" vs "nice to have later"
4. **Share with AI** — this document becomes context for building the application. The answered questions drive the domain model, the user flows drive the UI design, and the priorities drive the build order.

Once answered, this document feeds directly into:
- **`DESIGN_PROPOSAL.md`** — architecture decisions
- **`BUILD_PLAN.md`** — implementation order
- **`CLAUDE.md` / `AGENTS.md`** — AI agent context for development