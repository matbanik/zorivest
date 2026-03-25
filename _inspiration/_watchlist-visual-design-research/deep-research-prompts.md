# Deep Research Prompts: Watchlist Visual Design

> **Purpose**: Three deep research prompts — one each for Gemini, ChatGPT, and Claude — targeting each platform's research strengths. The goal is to determine the optimal visual design for a trading watchlist in a desktop Electron application.
>
> **Date**: 2026-03-20
> **Related**: MEU-70 (`gui-planning`), MEU-48 expansion item W4

---

## Context Summary (Include with All Prompts)

We are building **Zorivest**, a desktop trading portfolio management application (Electron + React frontend, Python FastAPI backend). The application includes a **Watchlist** feature that currently displays a simple list of tickers with notes.

**Current state:**
- Watchlist entity: `name`, `description`, list of items (each has `ticker` and `notes`)
- Market data APIs exist: `GET /api/v1/market-data/quote?ticker=` returns real-time quotes, `GET /api/v1/market-data/search?query=` returns ticker matches
- The watchlist is displayed in a split-pane layout (list of watchlists on left, selected watchlist items on right)
- Currently shows only: ticker symbol, notes, and an "X items" count badge
- Target users: active retail traders (swing and day trading, primarily US equities)

**Technical constraints:**
- Desktop app (Electron) — no mobile considerations
- React with TanStack Query for data fetching
- Market data comes from multiple providers (Alpha Vantage, Polygon, Yahoo Finance, etc.) via a unified API
- Rate limits apply per provider — need to be mindful of how many quote requests per watchlist refresh
- Real-time websocket feeds are NOT yet implemented — only REST polling
- Dark theme preferred (existing app uses dark UI)

**What we want to learn:**
1. What columns/data points are most useful in a trading watchlist?
2. How should watchlist items be visually organized for quick scanning?
3. What interaction patterns (sorting, grouping, alerts) add the most value?
4. How do the best platforms (TradingView, TC2000, ThinkorSwim, Webull) handle watchlist UX?
5. What's the minimum viable watchlist that's still genuinely useful vs. a full-featured one?
6. How to handle rate limits gracefully when fetching quotes for 20-50 tickers?

---

## Prompt 1: Gemini Deep Research

> **Platform strengths**: Google Search integration, multi-source synthesis, broad web coverage, ability to process and compare many sources simultaneously.

```
Use Deep Research to investigate the following topic comprehensively.

# Research Topic: Optimal Watchlist Visual Design for Desktop Trading Applications (2025-2026)

## Background

[Paste the Context Summary above here]

## Research Questions

Research each of the following in depth. For each, find multiple real-world examples, screenshots, blog posts, YouTube walkthroughs, and documentation from trading platforms.

### 1. Watchlist Column Standards Across Major Platforms

Catalog the exact columns and data points offered by the top 10 trading platforms' watchlists:
- TradingView, TC2000, ThinkorSwim (TD Ameritrade/Schwab), Webull, Fidelity Active Trader Pro
- TradeStation, Interactive Brokers TWS, Quantower, DAS Trader, Sterling Trader
- For each platform, document:
  - Default columns shown out-of-the-box
  - Total number of available columns
  - Which columns are most commonly customized/added
  - How column headers are labeled (full text vs abbreviations)
  - Column width behavior (fixed, auto-resize, user-draggable)

### 2. Visual Design Patterns for Rapid Scanning

Find evidence-based and practitioner-endorsed patterns for how traders visually scan watchlists:
- Color coding: what color schemes work for price change direction (not just red/green — colorblind-accessible alternatives)
- Typography: monospace vs proportional fonts for price data, optimal font sizes
- Sparkline/mini-chart integration: do platforms embed tiny price charts inline?
- Heat maps vs traditional tables: when does each work better?
- Row highlighting: how do platforms indicate "active" or "focused" ticker?
- Density vs readability trade-offs: compact mode vs comfortable spacing

### 3. Interaction Patterns That Add Value

Research the most valued interaction features on watchlists:
- Sorting: single-column, multi-column, custom sort orders
- Grouping: by sector, by watchlist category, by signal type
- Filtering: inline column filters, search within watchlist
- Drag-and-drop reordering
- Right-click context menus (what actions are offered?)
- Click-to-chart: clicking a ticker opens its chart
- Alerts: setting price/volume alerts directly from watchlist rows
- One-click trade: placing orders directly from watchlist

### 4. Minimal Viable Watchlist vs Full-Featured

Determine the "tiers" of watchlist functionality:
- Tier 0 (Minimal): What's the absolute minimum that's still useful for a trader?
- Tier 1 (Functional): What makes a watchlist genuinely productive?
- Tier 2 (Power user): What separates professional-grade from basic?
- Tier 3 (Platform-grade): What do institutional tools offer beyond retail?
- For our purposes: which tier should we target for MVP vs long-term?

### 5. Rate Limit-Aware Data Fetching Patterns

Find technical approaches for populating watchlists with market data under rate limits:
- Staggered polling strategies (round-robin, priority-based)
- Visible-first loading (only fetch quotes for visible rows)
- Cache + TTL patterns for watchlist data
- Fallback display when data is stale or unavailable
- How platforms indicate data freshness (timestamps, color dimming)

## Output Format

Organize your research report with these sections:

1. **Column Comparison Matrix** — Table comparing columns across all 10 platforms
2. **Visual Design Best Practices** — Evidence-based recommendations with examples
3. **Interaction Pattern Catalog** — Ranked by user value, with implementation complexity
4. **Tiered Feature Roadmap** — What to build first, second, third
5. **Technical Patterns for Rate-Limited Data** — Code-level strategies
6. **Recommended Default Configuration** — Suggested default columns for Zorivest
7. **Screenshots/Mockup References** — Links to the best visual examples found
```

---

## Prompt 2: ChatGPT Deep Research

> **Platform strengths**: Structured reasoning, tool-use during research (browsing + code analysis), strong at producing actionable implementation plans, good at comparing technical approaches.

```
I need deep research on watchlist UX design for a desktop trading application.
Do extensive web browsing to find real-world examples, design patterns,
and technical implementations from 2025-2026.

# Topic: Watchlist Component Design for Electron Desktop Trading App

## My Current Setup

[Paste the Context Summary above here]

## What I Need You to Research

### Part 1: Feature Audit of Top Platforms (Priority)

Browse and analyze the watchlist features of these specific platforms. For each, find documentation, help pages, or user guides that describe their watchlist capabilities:

1. **TradingView** — Document their watchlist columns, "details" mode, column customization, and how they handle real-time updates in their desktop/web app. Find their help article on watchlist setup.

2. **TC2000** — Their WatchList is a core feature. Find what columns they offer, how they handle custom conditions/columns, and their color coding approach.

3. **ThinkorSwim** — Document their watchlist gadget, custom columns (thinkScript), and how they organize market data in tabular form.

4. **Webull** — Their mobile-first approach to watchlist design. What data do they show at a glance vs. requiring a tap/click?

5. **Interactive Brokers TWS** — Their "Market Scanner" and watchlist. How does an institutional-grade platform handle this differently?

For each platform, I need:
- Exact list of default watchlist columns
- Available optional columns
- How real-time data is displayed (streaming vs polling indicator)
- Notable UX patterns unique to that platform
- Link to documentation or screenshot

### Part 2: React Component Patterns

Search for open-source React trading dashboard components and watchlist implementations:

1. **React table libraries** suited for financial data:
   - TanStack Table, AG Grid, or custom solutions?
   - Which handles streaming data updates without full re-render?
   - Financial number formatting (green/red, decimals, currency)

2. **Open-source trading dashboards** on GitHub:
   - Find repos with watchlist-like components
   - Document their column structure and data model
   - Note any clever patterns for rate-limited API data

3. **Sparkline/mini-chart libraries** for React:
   - Lightweight options for embedding tiny price charts in table cells
   - Performance considerations for 20-50 sparklines on screen

### Part 3: Data Architecture for Rate-Limited Watchlists

Research technical patterns for:

1. **Stale-while-revalidate** applied to watchlist data
2. **Priority queue** for quote fetching (visible items first, favorites first)
3. **Batch quote APIs** — do any providers support fetching multiple quotes in one request?
4. **Visual freshness indicators** — how to show "this price is 30 seconds old" vs "real-time"
5. **Incremental loading** — fetch 5 most important columns first, then secondary data

### Part 4: Accessibility and Dark Theme Considerations

1. **Color alternatives to red/green** — what trading platforms use for colorblind accessibility?
2. **High-contrast dark themes** — best practices for financial data on dark backgrounds
3. **Keyboard navigation** in data tables — arrow key support, quick-jump by typing ticker symbol

## Output Requirements

Structure your report as:

1. **Platform Feature Matrix** — side-by-side comparison table
2. **Recommended Column Set** — for Zorivest, in priority order, with data source mapping
3. **React Implementation Guide** — specific libraries, component patterns, code snippets
4. **Data Fetching Strategy** — architecture for rate-limited multi-ticker data
5. **Design Specification** — colors, fonts, spacing, interaction patterns for dark theme
6. **Quick Wins** — things we can implement immediately with existing APIs
7. **Strategic Features** — things that need additional infrastructure (websockets, batch APIs)
```

---

## Prompt 3: Claude Deep Research

> **Platform strengths**: Nuanced technical analysis, ability to identify subtle patterns and failure modes, strong at reasoning about system design trade-offs, excellent at synthesizing qualitative insights.

```
Use your research capabilities to investigate watchlist design patterns
in trading platforms. I need a deep, nuanced analysis — not just a
feature list, but an understanding of WHY certain patterns work and
how they serve the trader's cognitive needs.

# Research Topic: Cognitive Design of Trading Watchlists

## Context

[Paste the Context Summary above here]

## Research Directions

### Direction 1: The Information Architecture Problem

A watchlist is fundamentally an information density challenge: traders
want maximum data in minimum screen space, while maintaining the ability
to scan and act quickly.

Research and analyze:

1. **Information hierarchy in financial tables** — What data points
   do traders actually look at FIRST when scanning a watchlist? Is there
   eye-tracking research or UX studies specific to trading interfaces?
   Find evidence for:
   - Visual scan patterns (F-pattern, Z-pattern, or columnar?)
   - Which data point triggers the "investigate further" action
   - How many columns is "too many" before cognitive overload
   - The role of muscle memory in fixed-column layouts

2. **Data density vs actionability** — Compare the approaches:
   - ThinkorSwim: Dense, customizable, hundreds of columns available
   - TradingView: Clean, focused, ~10 default columns
   - TC2000: Middle ground with conditional formatting
   - Which approach leads to better trading outcomes (if any research exists)?

3. **The "glance value" metric** — For each common watchlist column,
   assess: How much actionable information does a trader get from
   a single glance (1-2 seconds)?
   - Last price: glance value = LOW (meaningless without context)
   - Change %: glance value = HIGH (instant sentiment)
   - Volume vs avg: glance value = HIGH (unusual activity signal)
   - 52-week range position: glance value = MEDIUM (context)
   - Sparkline: glance value = HIGH (trend at a glance)
   - Bid/Ask spread: glance value = MEDIUM (liquidity signal)
   Validate or challenge these assessments with evidence.

### Direction 2: The Interaction Model

2. **Sort, filter, group — which matters most?** Look for evidence:
   - Do traders actually use sorting? Or do they prefer manual ordering?
   - Is grouping (by sector, by signal type) used in practice?
   - What filtering patterns are most useful within a watchlist?
   - How important is drag-and-drop reordering vs automatic reordering?

3. **Context menu design** — What right-click actions on a watchlist
   row are most valuable? Research what platforms offer:
   - Open chart
   - Set alert
   - Place order
   - View news/filings
   - Add to/remove from watchlist
   - Copy ticker to clipboard
   Which of these sees the most usage?

4. **Alert integration** — How do the best platforms integrate price/
   volume alerts INTO the watchlist display vs as a separate feature?

### Direction 3: Design Trade-offs for Our Constraints

Given our specific constraints (REST polling, rate limits, dark theme,
Electron desktop), analyze the trade-offs:

1. **Polling frequency vs data freshness** — What refresh interval
   is acceptable for:
   - Day traders (need sub-second? Or is 5-15 second polling OK?)
   - Swing traders (1-5 minute refresh adequate?)
   - Pre/post market monitoring?

2. **Visual staleness indicators** — How should we show that data
   is N seconds old? Research approaches:
   - Timestamp in corner
   - Color dimming (data fades as it ages)
   - "Live" indicator dot
   - Last updated timestamp per row

3. **Rate limit UX** — When we can only fetch 5 quotes/second due
   to API limits, how should 50-ticker watchlists behave?
   - Progressive loading (show what we have, fill in the rest)
   - Priority loading (favorites first, rest alphabetically)
   - Stale data display (show cached data with "last updated" time)
   - Loading skeleton vs spinner vs "—" placeholders

4. **Dark theme color palette** research — Find the specific color
   values (HSL/RGB) used by major trading platforms for:
   - Positive change (gain)
   - Negative change (loss)
   - Neutral/unchanged
   - Selected row highlight
   - Header background
   - Alternating row colors in dark mode
   - How they handle colorblind accessibility

### Direction 4: The Minimum Viable Experience

1. **What makes a watchlist "feel" professional** — Identify the
   specific details that separate amateur-looking watchlists from
   professional ones:
   - Column alignment (right-align numbers, left-align text)
   - Decimal precision (2 vs 4 decimal places by context)
   - Thousand separators and currency formatting
   - Monospace vs proportional fonts for numbers
   - Header formatting (ALL CAPS, Title Case, lowercase?)
   - Row height and padding ratios

2. **Progressive enhancement path** — Design a roadmap from
   "basic but useful" to "power trader ready":
   - Level 1: ticker, last price, change %, notes
   - Level 2: + volume, day range, sparkline
   - Level 3: + custom columns, conditional formatting, alerts
   - Level 4: + streaming data, multi-chart sync, trade execution
   For each level, what's the implementation effort and user value?

## Output Format

Structure your report as a design analysis:

1. **Information Architecture Recommendations** — What to show, why, in what order
2. **Interaction Design Guide** — How users should interact with the watchlist
3. **Visual Design Specification** — Colors, typography, spacing rationale
4. **Progressive Enhancement Roadmap** — Build path from L1 to L4
5. **Technical Constraints Analysis** — What our polling/rate-limit constraints mean for UX
6. **Anti-Patterns** — What NOT to do, based on documented failures
7. **Recommended MVP Scope** — The smallest watchlist that would be genuinely useful
```

---

## Usage Guide

### How to Use These Prompts

1. **Gemini** (breadth-focused): Use [Gemini Deep Research](https://gemini.google.com) with the full prompt. Gemini will search extensively across many sources and produce a comprehensive catalog. Best for building the **feature comparison matrix**.

2. **ChatGPT** (implementation-focused): Use [ChatGPT Deep Research](https://chatgpt.com) mode. ChatGPT will browse, analyze, and produce actionable implementation plans. Best for the **React component guide** and technical architecture.

3. **Claude** (analysis-focused): Use [Claude Research](https://claude.ai) with extended thinking. Claude will produce nuanced analysis of trade-offs, failure modes, and design principles. Best for making **design DECISIONS** and understanding cognitive aspects.

### Combining Results

After running all three, create a synthesis document by:

1. Extract Gemini's **column comparison matrix** — the broadest feature catalog
2. Take ChatGPT's **React implementation guide** — the most actionable technical advice
3. Use Claude's **information architecture analysis** — the deepest design rationale
4. Cross-reference column recommendations that appear in 2+ reports (high confidence)
5. Flag contradictions between reports (areas needing human judgment)
6. Save synthesis to `_inspiration/_watchlist-visual-design-research/synthesis.md`

### Key Context to Paste

When pasting the Context Summary into each prompt, also consider attaching:
- The current `WatchlistPage.tsx` implementation (for technical context)
- The `06c-gui-planning.md` specification (for product requirements)
- The existing market data API surface (`market_data.py` routes)
