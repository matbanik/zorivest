# Zorivest — Designing for the AI Improvement Curve

> How to architect an MCP-first trading intelligence system so it automatically gets better as LLMs improve — without changing a single line of code.

---

## What Zorivest Actually Is

**Zorivest is an IDE MCP tool first.** The primary interface is the AI chat in your coding IDE — not a GUI.

| Layer | Purpose |
|---|---|
| **MCP Server (primary)** | AI-assisted meta-cognition: market analysis, trade planning, post-trade reflection, daily briefs, sentiment synthesis |
| **Python FastAPI Backend** | Data processing, API integrations, email delivery, scheduling, database operations |
| **Electron GUI (secondary)** | Configuration panel: API endpoints, email settings, service health, logs, database inspection, email template preview |

**Zorivest doesn't care about trade execution.** Trades happen on other platforms, on the phone with a broker, wherever. Zorivest cares about:

1. **Before** — Finding opportunities, planning how to capitalize, understanding risk/tax implications
2. **During** — Optionally importing data as it happens (but doesn't need to)
3. **After** — Importing trade data, reflecting with AI on what happened mentally and technically, recording lessons

**The core value proposition**: A library of AI prompts and workflows for trading meta-cognition, powered by composite daily briefs built from multiple timeframes and community sentiment — making every trade feel like *"shooting fish in a barrel with a shotgun."*

---

## Quantified LLM Improvement Rates

Models are improving fast — and Zorivest's MCP-first architecture captures this directly:

| Capability | Improvement | Why It Matters for Zorivest |
|---|---|---|
| **Workplace task performance** | +26pp in 1 year | Every MCP workflow gets smarter automatically |
| **General knowledge (MMLU)** | 70% → 90%+ in 3 years | Better market context, more nuanced analysis |
| **Reasoning (ARC-AGI-2)** | Near 0% → 52.9% | Complex multi-factor trade thesis evaluation |
| **Tool use (BFCL v3)** | 61% → 78% | MCP tools called more accurately, fewer errors |
| **Multi-agent coordination** | 45% faster, 60% more accurate | Composite briefs from multiple data sources |

> **Every 6-12 months, the AI behind your MCP tools gets ~25-30% better** — IF your architecture captures it.

---

## The AI Improvement Dividend: Feature-by-Feature

### Scoring Framework

| Score | Category | Meaning |
|---|---|---|
| 🟢 **5** | **Free Upgrade** | Gets better automatically by swapping the model |
| 🔵 **4** | **Unlock** | New capabilities become possible with better models |
| 🟡 **3** | **Compound** | Improvement multiplied by multi-agent orchestration |
| ⚪ **2** | **Marginal** | Some improvement, mostly edge cases |
| ⚫ **1** | **Static** | No AI dependency |

---

### Market Awareness & Daily Briefs (Core Feature)

| Feature | Score | Current State | With Next-Gen Models |
|---|---|---|---|
| **Composite daily brief** | 🟢 5 | Summarizes watchlist across basic timeframes | Rich narrative synthesizing past month → past week → last night → this morning with causal threading: "NVDA weakness this week follows the SOX divergence you noted last month" |
| **Community sentiment synthesis** | 🟢 5 | Basic bullish/bearish from 2-3 sources | Nuanced: detects retail consensus forming, contrarian signals, meme momentum shifts. Distinguishes informed from noise |
| **Multi-timeframe analysis** | 🔵 4 | Separate summaries per timeframe | Integrated: "The daily setup aligns with the weekly trend but conflicts with the monthly mean reversion — here's why that matters for your 2-week time horizon" |
| **Watchlist monitoring** | 🟡 3 | Price alerts + basic news | Contextual alerts: "AAPL approaching your thesis entry zone while sentiment just shifted bearish — the setup you described in your Jan 15 plan is materializing" |
| **Free source aggregation** | ⚪ 2 | API calls to free data sources | Marginal: slightly better at parsing, but API calls are API calls |

### Meta-Cognition & Trade Reflection (Core Feature)

| Feature | Score | Current State | With Next-Gen Models |
|---|---|---|---|
| **Post-trade reflection** | 🟢 5 | "What went well/badly?" templates | Deep Socratic dialogue: "You said your conviction was 8/10 but sized at 2%. Your journal from December shows the same pattern — you recognize setups but don't trust your sizing. What changed since then?" |
| **Mental state recording** | 🔵 4 | Sentiment tagging on journal entries | Detects patterns across entries: revenge trading sequences, FOMO escalation, post-loss tilt. Links emotional states to outcome data |
| **Pattern discovery** | 🟢 5 | Single-dimension queries | "When you trade tech earnings after a loss, using margin, in the afternoon, your win rate drops from 60% to 23%. You've done this 7 times" |
| **AI prompt/workflow library** | 🟢 5 | Static prompt templates | Self-improving prompts: AI suggests workflow refinements based on which prompts produce the most actionable insights for YOUR trading style |
| **Cross-session memory** | 🔵 4 | Manual session summaries | "Last week you hypothesized that semis would underperform if China export controls tightened. That just happened — should we revisit your NVDA thesis?" |

### Trade Planning & Opportunity Tracking

| Feature | Score | Current State | With Next-Gen Models |
|---|---|---|---|
| **Opportunity identification** | 🟢 5 | Watchlist + manual scanning | "Based on your daily brief, three watchlist names are approaching entry zones simultaneously. Here's a priority ranking by your historical edge" |
| **Trade plan generation** | 🟢 5 | Template-based plans | Full thesis with entries, sizing, risk scenarios, time horizon, tax implications — generated from a paragraph of your reasoning |
| **Risk & tax calculation** | 🟡 3 | Math formulas + wash sale rules | Proactive: "This trade pushes your short-term cap gains to $X. Holding 3 more days converts to long-term, saving $Y. Your past 4 similar trades averaged 2.3 days to target" |
| **Time horizon awareness** | 🔵 4 | User-specified hold period | AI evaluates thesis coherence with timeframe: "Your thesis is macro-driven but you're targeting a 3-day hold — the catalyst you're playing takes 2-4 weeks historically" |
| **Cumulative edge tracking** | 🟢 5 | Win rate + P&L stats | Narrative: "Your edge comes from 47 small wins averaging $340, not the 3 big wins. Your system works — stop swinging for home runs" |

### Data Import & Processing

| Feature | Score | Current State | With Next-Gen Models |
|---|---|---|---|
| **Broker data normalization** | 🟢 5 | Parses known CSV formats | Handles ANY format dynamically — new brokers, international formats, screenshots of confirmations |
| **Natural language trade entry** | 🟢 5 | Simple: "Bought 100 AAPL at 195" | Complex: "I scaled into AAPL across 3 fills yesterday, averaged around 195, stop at 190, thesis is the AI capex cycle play I wrote about last week" |
| **Auto-categorization** | 🟢 5 | Basic strategy tagging | Nuanced: "This was a failed breakout that became a fade — tagging as both 'momentum_fail' and 'mean_reversion'" |

### GUI / Configuration (Admin Layer)

| Feature | Score | Current State | With Next-Gen Models |
|---|---|---|---|
| **API endpoint config** | ⚫ 1 | Form fields | Static config UI |
| **Email template preview** | ⚫ 1 | HTML render | Static UI |
| **Service health / logs** | ⚫ 1 | Status dashboard | Static UI |
| **Database inspection** | ⚪ 2 | Query interface | Marginal: natural language DB queries could improve |

---

## Architectural Principles for MCP-First Design

### 1. Prompts ARE the Product

In a traditional app, the code is the product. In Zorivest, **the AI prompt/workflow library is the core IP**.

```
docs/prompts/
├── daily-brief/
│   ├── composite-brief.prompt.yaml      # Multi-timeframe synthesis
│   ├── sentiment-aggregator.prompt.yaml  # Community sentiment
│   └── watchlist-scanner.prompt.yaml     # Opportunity detection
├── meta-cognition/
│   ├── post-trade-reflection.prompt.yaml # Socratic trade review
│   ├── pattern-discovery.prompt.yaml     # Cross-trade patterns
│   └── emotional-audit.prompt.yaml       # Mental state tracking
├── planning/
│   ├── trade-plan-generator.prompt.yaml  # Thesis → plan
│   ├── risk-scenario.prompt.yaml         # What-if analysis
│   └── tax-optimizer.prompt.yaml         # Tax implications
└── import/
    ├── trade-normalizer.prompt.yaml      # Any format → schema
    └── auto-categorizer.prompt.yaml      # Strategy tagging
```

**Key principle**: Prompts are versioned YAML files, not hardcoded strings. When a better model drops, the same prompts produce better results instantly. Over time, you refine prompts based on what works — this library IS Zorivest's competitive advantage.

### 2. Model-Agnostic Abstraction Layer

```
MCP Tool Call → Abstraction Layer → Any LLM Provider
                     ↓
             Swap models via config,
             not code changes
```

When GPT-6 or Claude 5 launches, update ONE config value. Every MCP tool improves immediately.

### 3. Capability-Based MCP Tools

Design MCP tools as **capabilities**, not model calls:

```
✅ analyze_trade()          — not call_gpt4_for_trade_analysis()
✅ generate_daily_brief()   — not run_claude_brief_pipeline()
✅ reflect_on_trade()       — not send_to_openai_for_review()
```

### 4. Free Data Source Strategy

Use the same sources retail traders use — same information means you can predict their conclusions:

| Source Type | Examples | Why Free Matters |
|---|---|---|
| **Price data** | Yahoo Finance, Alpha Vantage, Finnhub | Consensus price levels everyone watches |
| **News** | Google News, Finviz, Benzinga free tier | Same headlines driving retail sentiment |
| **Social sentiment** | Reddit (r/wallstreetbets, r/stocks), StockTwits, X/Twitter | Where retail consensus forms |
| **Technical indicators** | TradingView free charts (via embeds/exports) | The exact charts retail traders are watching |
| **Economic calendars** | Investing.com, ForexFactory | Same events everyone is positioning for |

> **Principle**: We're not trying to out-data institutional traders. We're trying to read the same signals retail traders read, understand what conclusions they'll reach, and plan accordingly.

### 5. Multi-Agent Orchestration for Daily Briefs

The composite daily brief is a perfect multi-agent pipeline:

```
Agent 1: Data Collector    → Gathers price/news/sentiment from APIs
Agent 2: Timeframe Analyst → Synthesizes per-timeframe summaries
Agent 3: Sentiment Scorer  → Rates community sentiment per ticker
Agent 4: Brief Composer    → Combines into personalized narrative
Agent 5: Opportunity Alert → Flags watchlist items near entry zones
```

When each agent gets 25% better, the 5-agent pipeline gets **~3x better** (1.25⁵ = 3.05). This is the compound improvement dividend.

### 6. Evaluation Harnesses

Measure improvement when new models drop:

| Feature | Metric |
|---|---|
| Daily brief quality | Did the brief contain insights you acted on? (user rating 1-5) |
| Trade reflection depth | Did the AI surface a pattern you didn't see? (yes/no) |
| Import accuracy | % of fields correctly parsed from new broker format |
| Sentiment accuracy | Did community sentiment prediction align with next-day price action? |
| Plan quality | Post-trade: was the plan's risk/reward prediction accurate? |

---

## The 4-Tier Feature Classification

### 🟢 Tier 1: "Free Upgrades" (Build First, Improve Forever)

Gets better with EVERY model release, no code changes:

- Composite daily briefs
- Community sentiment synthesis
- Post-trade reflection / Socratic dialogue
- Pattern discovery across trades
- Trade plan generation from thesis
- Broker data normalization
- Natural language MCP queries
- Cumulative edge tracking narratives

### 🔵 Tier 2: "Unlocks" (New Capabilities Each Year)

Become POSSIBLE as models cross capability thresholds:

- Cross-session memory ("you said last week...")
- Mental state pattern detection across journal entries
- Time horizon coherence checking
- Multi-timeframe causal threading in briefs
- Proactive opportunity alerts linked to existing plans

**Build the MCP tool interface now, even if results aren't perfect yet. When models improve, these features "light up."**

### 🟡 Tier 3: "Compound" (Multi-Agent Multipliers)

Benefit from orchestration improvements:

- Multi-source daily brief pipeline
- Risk scenario modeling (multiple agents collaborating)
- Tax optimization across accounts and time horizons

### ⚫ Tier 4: "Static" (Traditional Software)

GUI config, database storage, API endpoint management, email delivery, encryption.

---

## Key Sources

| Source | What It Provides |
|---|---|
| [Anthropic 2026 Agentic Coding Trends](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf) | Three compounding multipliers, multi-agent patterns |
| [Brookings: LLM Work Capabilities](https://www.brookings.edu/wp-content/uploads/2025/11/Rio-Chanona_Einsiedler_Self-Building-Benchmarks_FINAL.pdf) | 26pp improvement in 1 year on workplace tasks |
| [Berkeley BAIR: Compound AI Systems](https://www.databricks.com/glossary/compound-ai-systems) | Modular AI component architecture |
| [Azure AI Agent Orchestration](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) | Sequential, parallel, conditional, event-driven patterns |
| [Entrio: LLM Agnostic Architecture](https://www.entrio.io/blog/implementing-llm-agnostic-architecture-generative-ai-module) | Abstraction layer design |
| [Azure Well-Architected: AI App Design](https://learn.microsoft.com/en-us/azure/well-architected/ai/application-design) | Capability-based design, prompts as configuration |
