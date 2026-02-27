# Phase 5c: MCP Tools — Trade Analytics

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `trade-analytics`
>
> This is the largest category (19 tools). Tools span core trade CRUD, screenshot management, and advanced analytics.

## Core Trade Tools

### `create_trade` [Specified]

Record a new trade execution. Deduplicates by exec_id.

> Also categorized as `trade-planning` — primary spec lives here.

```typescript
// mcp-server/src/tools/trade-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

export function registerTradeTools(server: McpServer) {

  server.tool(
    'create_trade',
    'Record a new trade execution. Deduplicates by exec_id.',
    {
      exec_id: z.string(),
      instrument: z.string(),
      action: z.enum(['BOT', 'SLD']),
      quantity: z.number(),
      price: z.number(),
      account_id: z.string(),
    },
    async ({ exec_id, instrument, action, quantity, price, account_id }) => {
      const res = await fetch(`${API_BASE}/trades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exec_id, instrument, action, quantity, price, account_id }),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `exec_id`, `instrument`, `action` (BOT/SLD), `quantity`, `price`, `account_id`
**Output:** JSON text for created trade or dedup conflict details
**Side Effects:** Writes trade; deduplicates by exec_id

---

### `list_trades` [Specified]

Read trades for review/export.

```typescript
  server.tool(
    'list_trades',
    'List recorded trades with pagination.',
    { limit: z.number().default(50), offset: z.number().default(0) },
    async ({ limit, offset }) => {
      const res = await fetch(`${API_BASE}/trades?limit=${limit}&offset=${offset}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `limit` (default 50), `offset` (default 0)
**Output:** JSON text list/page of trades
**Side Effects:** None (read-only)

---

## Screenshot Tools

### `attach_screenshot` [Specified]

Attach image evidence to a trade from MCP context.

```typescript
  server.tool(
    'attach_screenshot',
    'Attach a screenshot image to a trade. Image must be base64-encoded. The MCP server decodes base64 and forwards as multipart/form-data to the REST API.',
    {
      trade_id: z.string(),
      image_base64: z.string(),
      mime_type: z.string().default('image/webp').describe('Advisory only — backend standardizes all images to WebP'),
      caption: z.string().default(''),
    },
    async ({ trade_id, image_base64, mime_type, caption }) => {
      const binaryData = Buffer.from(image_base64, 'base64');
      const blob = new Blob([binaryData], { type: mime_type });
      const formData = new FormData();
      formData.append('file', blob, `screenshot.${mime_type.split('/')[1]}`);
      formData.append('caption', caption);

      const res = await fetch(`${API_BASE}/trades/${trade_id}/images`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `trade_id`, `image_base64`, `mime_type` (advisory, default `"image/webp"`), `caption`
**Output:** JSON text for stored image metadata/IDs
**Side Effects:** MCP decodes base64 and uploads multipart file

---

### `get_trade_screenshots` [Specified]

List screenshot metadata for a trade.

```typescript
  server.tool(
    'get_trade_screenshots',
    'Get metadata for all screenshots attached to a trade.',
    { trade_id: z.string() },
    async ({ trade_id }) => {
      const res = await fetch(`${API_BASE}/trades/${trade_id}/images`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `trade_id`
**Output:** JSON text array of image metadata
**Side Effects:** None (read-only)

---

### `get_screenshot` [Specified]

Retrieve a screenshot with display-ready content.

```typescript
// mcp-server/src/tools/image-tools.ts

server.tool(
  'get_screenshot',
  'Retrieve a screenshot image by ID. Returns metadata and base64 image content for display.',
  { image_id: z.number() },
  async ({ image_id }) => {
    const metaRes = await fetch(`${API_BASE}/images/${image_id}`);
    if (!metaRes.ok) {
      return { content: [{ type: 'text' as const, text: 'Image not found' }] };
    }
    const meta = await metaRes.json();

    const imgRes = await fetch(`${API_BASE}/images/${image_id}/full`);
    const imgBuffer = Buffer.from(await imgRes.arrayBuffer());

    return {
      content: [
        { type: 'text' as const, text: `Caption: ${meta.caption}\nSize: ${meta.width}×${meta.height}` },
        {
          type: 'image' as const,
          data: imgBuffer.toString('base64'),
          mimeType: meta.mime_type,
        },
      ],
    };
  }
);
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `image_id` (number)
**Output:** Mixed MCP content: text metadata + image (base64)
**Side Effects:** None (read-only)

---

## Analytics Tools

### `get_round_trips` [Specified]

Analyze closed/open execution pairs.

```typescript
  server.tool(
    'get_round_trips',
    'List round-trips (entry→exit pairs) for an account',
    {
      account_id: z.string().optional(),
      status: z.enum(['open', 'closed', 'all']).default('all'),
    },
    async (args) => fetchApi('/round-trips', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** optional `account_id`, `status` (open/closed/all, default all)
**Output:** JSON text round-trip list

---

### `enrich_trade_excursion` [Specified]

Compute MFE/MAE/BSO metrics for a trade.

```typescript
  server.tool(
    'enrich_trade_excursion',
    'Calculate MFE/MAE/BSO metrics for a trade using historical bar data',
    { trade_exec_id: z.string() },
    async ({ trade_exec_id }) =>
      fetchApi(`/analytics/excursion/${trade_exec_id}`, { method: 'POST' })
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `trade_exec_id`
**Output:** JSON text excursion metric payload

---

### `get_fee_breakdown` [Specified]

Summarize fee attribution.

```typescript
  server.tool(
    'get_fee_breakdown',
    'Decompose trade fees by type (commission, exchange, regulatory, ECN)',
    {
      account_id: z.string().optional(),
      period: z.string().default('ytd'),
    },
    async (args) => fetchApi('/fees/summary', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** optional `account_id`, `period` (default ytd)
**Output:** JSON text fee decomposition

---

### `score_execution_quality` [Specified]

Grade fill quality vs market benchmarks.

```typescript
  server.tool(
    'score_execution_quality',
    'Grade trade execution quality vs NBBO. Gated on NBBO data availability.',
    { trade_exec_id: z.string() },
    async ({ trade_exec_id }) =>
      fetchApi(`/analytics/execution-quality?trade_id=${trade_exec_id}`)
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `trade_exec_id`
**Output:** JSON text quality score/grade

---

### `estimate_pfof_impact` [Specified]

Estimate routing cost impact from PFOF behavior.

```typescript
  server.tool(
    'estimate_pfof_impact',
    'Estimate PFOF cost impact. Labeled as ESTIMATE — not auditable.',
    {
      account_id: z.string(),
      period: z.string().default('ytd'),
    },
    async (args) => fetchApi('/analytics/pfof-report', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `account_id`, `period` (default ytd)
**Output:** JSON text estimate report

---

### `get_expectancy_metrics` [Specified]

Compute expectancy/edge/Kelly metrics.

```typescript
  server.tool(
    'get_expectancy_metrics',
    'Win rate, avg win/loss, expectancy per trade, Kelly %, edge metrics',
    {
      account_id: z.string().optional(),
      period: z.string().default('all'),
    },
    async (args) => fetchApi('/analytics/expectancy', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** optional `account_id`, `period` (default all)
**Output:** JSON text expectancy metrics

---

### `simulate_drawdown` [Specified]

Run Monte Carlo drawdown simulations.

> Also categorized as `calculator` — primary spec lives here.

```typescript
  server.tool(
    'simulate_drawdown',
    'Monte Carlo drawdown probability table with recommended risk %',
    {
      account_id: z.string().optional(),
      simulations: z.number().int().min(100).max(100000).default(10000),
    },
    async (args) => fetchApi('/analytics/drawdown', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** optional `account_id`, `simulations` (100–100000, default 10000)
**Output:** JSON text probability table/recommended risk outputs

---

### `get_strategy_breakdown` [Specified]

Break P&L down by strategy tags.

```typescript
  server.tool(
    'get_strategy_breakdown',
    'P&L breakdown by strategy name from TradeReport tags',
    { account_id: z.string().optional() },
    async (args) => fetchApi('/analytics/strategy-breakdown', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** optional `account_id`
**Output:** JSON text strategy-level breakdown

---

### `get_sqn` [Specified]

Compute System Quality Number metrics.

```typescript
  server.tool(
    'get_sqn',
    'System Quality Number (SQN) — Van Tharp metric with grade classification',
    {
      account_id: z.string().optional(),
      period: z.string().default('all'),
    },
    async (args) => fetchApi('/analytics/sqn', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** optional `account_id`, `period` (default all)
**Output:** JSON text SQN value + grade

---

### `get_cost_of_free` [Specified]

Compute hidden costs from free-routing model.

```typescript
  server.tool(
    'get_cost_of_free',
    '"Cost of Free" report — hidden costs of PFOF routing + fee impact',
    {
      account_id: z.string().optional(),
      period: z.string().default('ytd'),
    },
    async (args) => fetchApi('/analytics/cost-of-free', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** optional `account_id`, `period` (default ytd)
**Output:** JSON text cost-of-free report

---

### `ai_review_trade` [Specified]

Run multi-persona AI review on a trade.

> Also categorized as `behavioral` — primary spec lives here.

```typescript
  server.tool(
    'ai_review_trade',
    'Multi-persona AI trade review. Opt-in with budget cap. Personas: Risk Manager, Trend Analyst, Contrarian.',
    {
      trade_exec_id: z.string(),
      review_type: z.enum(['single', 'weekly']).default('single'),
      budget_cap: z.number().optional().describe('Max spend in cents'),
    },
    async (body) => fetchApi('/analytics/ai-review', { method: 'POST', body })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `trade_exec_id`, `review_type` (single/weekly), optional `budget_cap` (cents)
**Output:** JSON text structured review output
**Side Effects:** Potentially external-AI spend; budget-cap aware

---

### `detect_options_strategy` [Specified]

Classify multi-leg options structure from executions.

```typescript
  server.tool(
    'detect_options_strategy',
    'Auto-detect multi-leg options strategy type from execution IDs',
    {
      leg_exec_ids: z.array(z.string()).min(2),
    },
    async ({ leg_exec_ids }) =>
      fetchApi('/analytics/options-strategy', { method: 'POST', body: { leg_exec_ids } })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `leg_exec_ids` array (min 2)
**Output:** JSON text detected strategy classification

---

## Report Tools

### `create_report` [Specified]

Create a post-trade TradeReport via MCP.

```typescript
  // Specified — registered in build plan
  server.tool(
    'create_report',
    'Create a post-trade review report for a completed trade. Records execution quality assessment, plan adherence, emotional state, and lessons learned.',
    {
      trade_id: z.string().describe('Trade execution ID to report on'),
      setup_quality: z.enum(['A', 'B', 'C', 'D', 'F']).describe('Grade for trade setup quality'),
      execution_quality: z.enum(['A', 'B', 'C', 'D', 'F']).describe('Grade for execution quality'),
      followed_plan: z.boolean().describe('Whether the trader followed the original plan'),
      emotional_state: z.enum(['calm', 'anxious', 'fearful', 'greedy', 'frustrated', 'confident', 'neutral'])
        .default('neutral')
        .describe('Emotional state during the trade'),
      lessons_learned: z.string().optional().describe('Free-form reflection on the trade'),
      tags: z.array(z.string()).default([]).describe('Strategy/category tags for the report'),
    },
    async (body) => {
      const res = await fetch(`${API_BASE}/trades/${body.trade_id}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }], isError: true };
      }
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `trade_id`, `setup_quality` (A–F), `execution_quality` (A–F), `followed_plan` (bool), `emotional_state`, optional `lessons_learned`, `tags[]`
**Output:** JSON with created report ID + echoed fields
**Side Effects:** Writes TradeReport
**REST Dependency:** `POST /api/v1/trades/{id}/report` — specified in [04-rest-api.md](04-rest-api.md) Step 4.1a
**Domain Model:** `TradeReport` — [01-domain-layer.md](01-domain-layer.md)

---

### `get_report_for_trade` [Specified]

Fetch report linked to a specific trade.

```typescript
  // Specified — registered in build plan
  server.tool(
    'get_report_for_trade',
    'Retrieve the post-trade review report for a specific trade execution.',
    {
      trade_id: z.string().describe('Trade execution ID to get report for'),
    },
    async ({ trade_id }) => {
      const res = await fetch(`${API_BASE}/trades/${trade_id}/report`);
      if (!res.ok) {
        return { content: [{ type: 'text' as const, text: `No report found for trade ${trade_id}` }], isError: true };
      }
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: false

**Input:** `trade_id`
**Output:** JSON TradeReport payload or "not found" message
**Side Effects:** None (read-only)
**REST Dependency:** `GET /api/v1/trades/{id}/report`

---

## Cross-References

| Tool | Category File | Description |
|------|--------------|-------------|
| `link_trade_journal` | [05i-mcp-behavioral.md](05i-mcp-behavioral.md) | Bidirectional trade↔journal linking |
| `find_wash_sales` | [05h-mcp-tax.md](05h-mcp-tax.md) | Wash sale detection (also trade-analytics) |
| `harvest_losses` | [05h-mcp-tax.md](05h-mcp-tax.md) | Loss harvesting scan (also trade-analytics) |

---

## Appendix: Composite Bifurcation (Constrained Clients)

> [!IMPORTANT]
> This appendix documents the **composite tool alternative** for Cursor-class clients (≤40-tool limit). The 19 discrete tools above remain canonical. Annotation-aware clients (Claude Code, Roo Code) use discrete tools directly. For Anthropic-class clients, see also Pattern F (PTC routing) in [05j-mcp-discovery.md](05j-mcp-discovery.md).

### `query_trade_analytics` (Composite)

Single enum-dispatch tool that routes to the 12 analytics endpoints. Replaces individual analytics tools on constrained clients.

```typescript
// Generated from discrete tool specs — single source of truth
server.tool(
  'query_trade_analytics',
  'Run a trade analytics query. Dispatches to the appropriate analytics endpoint based on metric.',
  {
    metric: z.enum([
      'round_trips', 'mfe_mae', 'fee_breakdown', 'execution_quality',
      'pfof_impact', 'expectancy', 'drawdown', 'strategy_breakdown',
      'sqn', 'cost_of_free', 'ai_review', 'detect_strategy'
    ]).describe('Analytics metric to compute'),
    account_id: z.string().optional().describe('Filter by account'),
    period: z.string().default('ytd').describe('Time period'),
    trade_exec_id: z.string().optional().describe('Specific trade (for per-trade metrics)'),
  },
  async (params) => {
    // Dispatch to corresponding REST endpoint based on params.metric
    // Implementation auto-generated from discrete tool schemas
  }
);
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-analytics
- `alwaysLoaded`: true (on constrained clients)

### What stays separate

| Tool(s) | Reason |
|---------|--------|
| `create_trade`, `list_trades` | Trade CRUD — different safety posture (write vs read-only) |
| `attach_screenshot`, `get_trade_screenshots`, `get_screenshot` | Image management — different I/O patterns (multipart/base64) |
| `create_report`, `get_report_for_trade` | Report CRUD — planned, different write semantics |

### Composite generation

The composite schema is **code-generated** from the discrete tool specs to maintain a single source of truth. When a discrete tool is added or modified, the composite is regenerated. This avoids the maintenance burden of a hand-maintained duplicate surface.

---

## Appendix: PTC Routing (Anthropic Clients)

> [!NOTE]
> **Pattern F** from the MCP tool architecture optimization research. Anthropic-only; other clients use discrete tools or the composite above.

For Anthropic-class clients that support Programmatic Tool Calling (PTC), the 11 read-only analytics tools (`readOnlyHint: true`) are marked with `allowed_callers: ["code_execution"]`. This allows the agent to batch-call REST endpoints via Python `asyncio.gather()` in a code execution sandbox, returning one summarized result instead of 11 individual round-trips.

### Annotation Addition

Read-only analytics tools (§ Analytics Tools above, where `readOnlyHint: true`) receive an additional annotation when serving Anthropic clients:

```typescript
// Added by adaptive client detection (05j) for Anthropic-class clients
annotations: {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
  // PTC routing — allows code_execution sandbox to call these tools
  allowed_callers: ['code_execution'],
}
```

### How It Works

| Step | Action |
|------|--------|
| 1 | Adaptive client detection ([05j](05j-mcp-discovery.md)) identifies Anthropic-class client |
| 2 | Analytics tools served with `allowed_callers: ["code_execution"]` |
| 3 | Agent writes Python to batch-call endpoints: `asyncio.gather(fetch('/round-trips'), fetch('/mfe-mae'), ...)` |
| 4 | Single summarized result returned instead of 11 sequential tool calls |

### Impact

- **37% token reduction** on complex multi-tool workflows (Anthropic-measured)
- Batch processing eliminates per-tool round-trip overhead
- Agent retains full control over which metrics to compute

### What's NOT PTC-routed

| Tool(s) | Reason |
|---------|--------|
| `create_trade`, `list_trades` | Write operations — require individual safety gates |
| `enrich_trade_excursion` | Writes computed MFE/MAE/BSO metrics (`readOnlyHint: false`) |
| `attach_screenshot`, `get_trade_screenshots`, `get_screenshot` | Binary I/O — not suitable for batch text responses |
| `create_report`, `get_report_for_trade` | Write + planned — not yet implemented |

---

## Appendix: GraphQL-Style Composite Evaluation

> Tier 3, item 8 from the MCP tool architecture optimization research.

### Concept

A single `query_analytics(query: "...")` tool that accepts structured queries, reducing 19 tools to 1-2. Works on all clients regardless of PTC support.

```typescript
// Hypothetical — NOT IMPLEMENTED
server.tool(
  'query_analytics',
  'Run structured analytics queries against trade data',
  {
    query: z.string().describe('Structured query: e.g. "round_trips(account_id=ABC, status=closed)"'),
  },
  async ({ query }) => { /* parse + dispatch */ }
);
```

### Evaluation

| Criterion | Assessment |
|-----------|------------|
| Tool count reduction | ✅ Strong — 19→1 |
| Client compatibility | ✅ Universal — no PTC or annotation support needed |
| Query syntax hallucination | ⚠️ High risk — free-form string invites malformed queries |
| Validation complexity | ⚠️ High — must parse and validate query DSL |
| Marginal benefit over existing patterns | ❌ Low — Composite (Pattern C) already covers constrained clients; PTC covers Anthropic |

### Decision: **Deferred**

The composite bifurcation (Pattern C, Session 5) and PTC routing (Pattern F, above) together address the primary optimization targets:
- **Constrained clients** (Cursor): `query_trade_analytics` composite with 12-metric enum
- **Anthropic clients**: PTC batch processing via `allowed_callers`
- **Annotation-aware clients** (Claude Code): Discrete tools with full annotations

GraphQL-style adds implementation complexity (query parser, validation, error handling) without sufficient marginal benefit at the current 12-metric scale. **Revisit if analytics tools exceed ~25 metrics** or if a client emerges that supports neither composites nor PTC.
