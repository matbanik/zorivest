# Phase 5d: MCP Tools — Trade Planning

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Categories: `trade-planning`, `calculator`

## Tools

### `calculate_position_size` [Specified]

Calculate risk-based position sizing for a candidate trade. Pure calculation; no side effects.

> Also categorized as `calculator` — this is the primary spec for the calculator category.

```typescript
  server.tool(
    'calculate_position_size',
    'Calculate position size based on risk parameters.',
    {
      balance: z.number(),
      risk_pct: z.number().default(1.0),
      entry: z.number(),
      stop: z.number(),
      target: z.number(),
    },
    async ({ balance, risk_pct, entry, stop, target }) => {
      const res = await fetch(`${API_BASE}/calculator/position-size`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ balance, risk_pct, entry, stop, target }),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: trade-planning
- `alwaysLoaded`: false

**Input:** `balance`, `risk_pct` (default 1.0), `entry`, `stop`, `target`
**Output:** JSON with `risk_per_share`, `account_risk_1r`, `share_size`, `position_size`, `reward_risk_ratio`, `potential_profit`
**Side Effects:** None (pure calculation)
**Error Posture:** Returns validation error if stop/entry create invalid risk

---

### `create_trade_plan` [Specified]

Create a forward-looking TradePlan from agent research.

> **Draft spec** — requires review before implementation. Input schema derived from `TradePlan` domain model ([01-domain-layer.md](01-domain-layer.md)).

```typescript
  // Specified — registered in build plan
  server.tool(
    'create_trade_plan',
    'Create a forward-looking trade plan from agent research. Records the thesis, entry/stop/target levels, and strategy rationale before execution.',
    {
      ticker: z.string().describe('Instrument symbol'),
      direction: z.enum(['long', 'short']),
      conviction: z.enum(['high', 'medium', 'low']).default('medium'),
      strategy_name: z.string().describe('Strategy label (e.g. "breakout", "mean_reversion")'),
      strategy_description: z.string().optional().describe('Free-form thesis/rationale'),
      entry: z.number().describe('Planned entry price'),
      stop: z.number().describe('Planned stop-loss price'),
      target: z.number().describe('Planned target/take-profit price'),
      conditions: z.string().describe('Entry conditions that must be met'),
      timeframe: z.string().describe('Expected hold period (e.g. "intraday", "2-5 days", "swing")'),
      account_id: z.string().optional().describe('Target account for the plan'),
    },
    async (body) => {
      const res = await fetch(`${API_BASE}/trade-plans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
- `toolset`: trade-planning
- `alwaysLoaded`: false

**Input:** `ticker`, `direction` (long/short), `conviction` (high/medium/low, default medium), `strategy_name`, `entry`, `stop`, `target`, optional `strategy_description`, `conditions` (string), `timeframe` (required), optional `account_id`
**Output:** JSON with created plan ID, computed `risk_reward_ratio`, `status` (defaults to `"draft"`)
**Side Effects:** Writes TradePlan to database
**Error Posture:** Returns validation error on missing required fields; rejects if identical active plan exists for same ticker
**REST Dependency:** `POST /api/v1/trade-plans` — specified in [04a-api-trades.md](04a-api-trades.md)
**Domain Model:** `TradePlan` — exists in [01-domain-layer.md](01-domain-layer.md)

---

## Cross-References

| Tool | Category File | Description |
|------|--------------|-------------|
| `create_trade` | [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) | Record executed trade (can link back to plan) |
| `simulate_tax_impact` | [05h-mcp-tax.md](05h-mcp-tax.md) | Pre-trade tax impact analysis |
