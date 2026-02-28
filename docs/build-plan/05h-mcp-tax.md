# Phase 5h: MCP Tools — Tax

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `tax`
>
> All 8 tools are **Specified** — draft specs below. Input/output derived from [06g-gui-tax.md](06g-gui-tax.md) and [mcp-planned-readiness.md](mcp-planned-readiness.md).

## Tools

### `simulate_tax_impact` [Specified]

Pre-trade what-if tax simulation for a proposed sale.

> Also categorized as `calculator`, `trade-planning` — primary spec lives here.

```typescript
  // Specified — registered in build plan
  server.tool(
    'simulate_tax_impact',
    'Simulate the tax impact of a proposed trade before execution. Shows lot-level close preview, short/long-term capital gains split, estimated tax, wash sale risk, and hold-for-savings hints.',
    {
      ticker: z.string().describe('Instrument symbol to simulate selling'),
      action: z.enum(['sell', 'cover']).describe('Sale type'),
      quantity: z.number().describe('Number of shares/contracts to sell'),
      price: z.number().describe('Expected sale price per share'),
      account_id: z.string().describe('Account holding the position'),
      cost_basis_method: z.enum(['fifo', 'lifo', 'specific_id', 'avg_cost'])
        .default('fifo')
        .describe('Lot selection method for basis calculation'),
    },
    async (body) => {
      const res = await fetch(`${API_BASE}/tax/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** `ticker`, `action` (sell/cover), `quantity`, `price`, `account_id`, `cost_basis_method` (default fifo)
**Output:** JSON with:
- `lots_to_close[]` — per-lot detail (shares, basis, gain/loss, holding_period, wash_risk)
- `summary` — total proceeds, total basis, realized_gain, st_gain, lt_gain
- `estimated_tax` — federal + state estimate based on tax profile
- `wash_sale_risk` — true/false + affected lots
- `hold_savings` — "hold N more days to convert ST→LT, saving $X"
**Side Effects:** None (pure simulation)
**Error Posture:** Returns error if no open lots found for ticker/account
**REST Dependency:** `POST /api/v1/tax/simulate`
**Domain Model:** `TaxLot`, `TaxProfile` — [domain-model-reference.md](domain-model-reference.md)

---

### `estimate_tax` [Specified]

Compute overall tax estimate from profile and trading data.

> Also categorized as `calculator` — primary spec lives here.

```typescript
  // Specified — registered in build plan
  server.tool(
    'estimate_tax',
    'Compute overall estimated tax liability from the tax profile and realized gains/losses. Returns federal + state breakdown with effective rate.',
    {
      tax_year: z.number().default(new Date().getFullYear())
        .describe('Tax year to estimate (defaults to current year)'),
      account_id: z.string().optional()
        .describe('Optional account filter; omit for all accounts'),
      filing_status: z.enum(['single', 'married_joint', 'married_separate', 'head_of_household'])
        .optional()
        .describe('Override filing status (uses profile default if omitted)'),
      include_unrealized: z.boolean().default(false)
        .describe('Include unrealized gains in the estimate'),
    },
    async (body) => {
      const res = await fetch(`${API_BASE}/tax/estimate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** `tax_year` (default current), optional `account_id`, optional `filing_status` override, `include_unrealized` (default false)
**Output:** JSON with:
- `realized_gains` — ST, LT, net
- `federal_estimate` — bracket breakdown, effective rate, estimated tax
- `state_estimate` — state tax (if state configured in profile)
- `total_estimated_tax`
- `effective_rate`
**Side Effects:** None (read-only computation)
**REST Dependency:** `POST /api/v1/tax/estimate`

---

### `find_wash_sales` [Specified]

Detect wash sale chains and conflicts.

> Also categorized as `trade-analytics` — primary spec lives here.

```typescript
  // Specified — registered in build plan
  server.tool(
    'find_wash_sales',
    'Scan trades for wash sale rule violations within the 30-day window. Returns detected chains with affected lots and disallowed loss amounts.',
    {
      account_id: z.string().describe('Account to scan for wash sales'),
      ticker: z.string().optional().describe('Filter to specific ticker'),
      date_range_start: z.string().optional().describe('ISO date to start scan (default: start of tax year)'),
      date_range_end: z.string().optional().describe('ISO date to end scan (default: today)'),
    },
    async (body) => {
      const res = await fetch(`${API_BASE}/tax/wash-sales`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** `account_id` (required), optional `ticker`, `date_range_start`, `date_range_end`
**Output:** JSON with:
- `wash_sales[]` — each: `{sell_trade, buy_trade, disallowed_loss, adjusted_basis, wash_window}`
- `total_disallowed` — sum of all disallowed losses
- `affected_tickers` — distinct tickers involved
**Side Effects:** None (read-only scan)
**REST Dependency:** `POST /api/v1/tax/wash-sales`

---

### `get_tax_lots` [Specified]

List/inspect lots for tax-aware lot selection.

```typescript
  // Specified — registered in build plan
  server.tool(
    'get_tax_lots',
    'List tax lots for a position, showing cost basis, holding period, gain/loss, and eligibility for each lot selection method.',
    {
      account_id: z.string().describe('Account ID'),
      ticker: z.string().optional().describe('Filter to specific ticker (omit for all positions)'),
      status: z.enum(['open', 'closed', 'all']).default('open')
        .describe('Lot status filter'),
      sort_by: z.enum(['acquired_date', 'cost_basis', 'gain_loss'])
        .default('acquired_date')
        .describe('Sort order for returned lots'),
    },
    async ({ account_id, ticker, status, sort_by }) => {
      const params = new URLSearchParams({ account_id, status, sort_by });
      if (ticker) params.set('ticker', ticker);
      const res = await fetch(`${API_BASE}/tax/lots?${params}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** `account_id`, optional `ticker`, `status` (default `"open"`), `sort_by` (default `"acquired_date"`)
**Output:** JSON with:
- `lots[]` — each: `{lot_id, ticker, quantity, cost_basis, date_acquired, holding_period_days, is_long_term, current_value, unrealized_gain_loss}`
- `summary` — total lots, total basis, total unrealized
**Side Effects:** None (read-only)
**REST Dependency:** `GET /api/v1/tax/lots`

---

### `get_quarterly_estimate` [Specified]

Compute quarterly estimated tax payment obligations (read-only).

```typescript
  // Specified — registered in build plan
  server.tool(
    'get_quarterly_estimate',
    'Compute quarterly estimated tax payment obligations. Returns required amounts, cumulative totals, and underpayment penalties.',
    {
      quarter: z.enum(['Q1', 'Q2', 'Q3', 'Q4']).describe('Tax quarter'),
      tax_year: z.number().default(new Date().getFullYear()),
      estimation_method: z.enum(['annualized', 'actual', 'prior_year'])
        .default('annualized')
        .describe('Method for computing required payment'),
    },
    async ({ quarter, tax_year, estimation_method }) => {
      const params = new URLSearchParams({
        quarter, tax_year: String(tax_year), estimation_method,
      });
      const res = await fetch(`${API_BASE}/tax/quarterly?${params}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** `quarter` (Q1–Q4), `tax_year`, `estimation_method` (default `"annualized"`)
**Output:** JSON with:
- `required_payment` — computed minimum payment for safe harbor
- `cumulative_required` — YTD required total
- `cumulative_paid` — YTD paid total
- `underpayment` — shortfall amount
- `penalty_estimate` — estimated underpayment penalty
- `due_date` — IRS deadline for this quarter
**Side Effects:** None (read-only)
**REST Dependency:** `GET /api/v1/tax/quarterly`

---

### `record_quarterly_tax_payment` [Specified]

Record a quarterly estimated tax payment.

```typescript
  // Specified — registered in build plan
  server.tool(
    'record_quarterly_tax_payment',
    'Record an actual estimated tax payment for a quarter. Requires confirmation.',
    {
      quarter: z.enum(['Q1', 'Q2', 'Q3', 'Q4']).describe('Tax quarter'),
      tax_year: z.number().default(new Date().getFullYear()),
      payment_amount: z.number().describe('Payment amount in dollars'),
      confirm: z.literal(true).describe('Must be true to confirm recording the payment'),
    },
    async (body) => {
      const res = await fetch(`${API_BASE}/tax/quarterly/payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** `quarter` (Q1–Q4), `tax_year`, `payment_amount`, `confirm` (must be `true`)
**Output:** JSON with:
- `recorded_payment` — confirmed amount
- `cumulative_paid` — updated YTD paid total
- `remaining_shortfall` — updated underpayment
**Side Effects:** Writes payment record
**REST Dependency:** `POST /api/v1/tax/quarterly/payment`

---

### `harvest_losses` [Specified]

Scan portfolio for harvestable tax losses.

> Also categorized as `trade-analytics` — primary spec lives here.

```typescript
  // Specified — registered in build plan
  server.tool(
    'harvest_losses',
    'Scan portfolio for tax-loss harvesting opportunities. Returns ranked losses with wash sale risk annotations.',
    {
      account_id: z.string().optional().describe('Filter to specific account'),
      min_loss_threshold: z.number().default(100)
        .describe('Minimum unrealized loss to include ($)'),
      exclude_wash_risk: z.boolean().default(false)
        .describe('Exclude positions with recent buys in 30-day wash window'),
    },
    async ({ account_id, min_loss_threshold, exclude_wash_risk }) => {
      const params = new URLSearchParams();
      if (account_id) params.set('account_id', account_id);
      params.set('min_loss_threshold', String(min_loss_threshold));
      params.set('exclude_wash_risk', String(exclude_wash_risk));
      const res = await fetch(`${API_BASE}/tax/harvest?${params}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** optional `account_id`, `min_loss_threshold` (default $100), `exclude_wash_risk` (default false)
**Output:** JSON with:
- `opportunities[]` — each: `{ticker, lots, unrealized_loss, holding_period, wash_risk, wash_window_end}`
- `total_harvestable` — sum of all qualifying losses
- `total_wash_risk` — sum of losses with wash risk
- `net_harvestable` — `total_harvestable - total_wash_risk` (if excluding)
**Side Effects:** None (read-only scan)
**REST Dependency:** `GET /api/v1/tax/harvest`

---

### `get_ytd_tax_summary` [Specified]

Return year-to-date tax summary dashboard data.

```typescript
  // Specified — registered in build plan
  server.tool(
    'get_ytd_tax_summary',
    'Year-to-date tax summary for dashboard display. Aggregates realized gains, wash sale adjustments, and estimated tax across all accounts.',
    {
      tax_year: z.number().default(new Date().getFullYear()),
      account_id: z.string().optional().describe('Filter to specific account'),
    },
    async ({ tax_year, account_id }) => {
      const params = new URLSearchParams({ tax_year: String(tax_year) });
      if (account_id) params.set('account_id', account_id);
      const res = await fetch(`${API_BASE}/tax/ytd-summary?${params}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: tax
- `alwaysLoaded`: false

**Input:** `tax_year` (default current year), optional `account_id`
**Output:** JSON with:
- `realized_st_gain` — short-term realized
- `realized_lt_gain` — long-term realized
- `total_realized` — net
- `wash_sale_adjustments` — total disallowed losses
- `trades_count` — number of closed trades
- `estimated_federal_tax`
- `estimated_state_tax`
- `quarterly_payments` — Q1–Q4 status
**Side Effects:** None (read-only aggregation)
**REST Dependency:** `GET /api/v1/tax/ytd-summary`
