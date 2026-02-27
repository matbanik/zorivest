# Phase 5e: MCP Tools — Market Data

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `market-data`
>
> Implementation details in [Phase 8](08-market-data.md). Registered in the MCP server alongside all other tools.

## Tools

### `get_stock_quote` [Specified]

Fetch latest quote for a ticker.

```typescript
// mcp-server/src/tools/market-data-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { fetchApi } from '../utils/api-client.js';

export function registerMarketDataTools(server: McpServer) {

  server.tool(
    'get_stock_quote',
    'Fetch the latest stock quote for a given ticker symbol.',
    { ticker: z.string().describe('Stock ticker symbol, e.g. "AAPL"') },
    async ({ ticker }) => fetchApi(`/market-data/quote?ticker=${ticker}`)
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: market-data
- `alwaysLoaded`: false

**Input:** `ticker` (string)
**Output:** JSON text quote object (price, change, volume, timestamp)
**Side Effects:** None — network-bound, expected variable latency
**Error Posture:** Returns error if ticker not found or provider unavailable

---

### `get_market_news` [Specified]

Fetch recent market news globally or filtered by ticker.

```typescript
  server.tool(
    'get_market_news',
    'Fetch recent financial news articles, optionally filtered by ticker.',
    {
      ticker: z.string().optional().describe('Filter to news about this ticker'),
      count: z.number().default(5).describe('Number of articles to return'),
    },
    async ({ ticker, count }) => {
      const params = new URLSearchParams();
      if (ticker) params.set('ticker', ticker);
      params.set('count', String(count));
      return fetchApi(`/market-data/news?${params}`);
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: market-data
- `alwaysLoaded`: false

**Input:** optional `ticker`, `count` (default 5)
**Output:** JSON text array of articles
**Side Effects:** None — network-bound

---

### `search_ticker` [Specified]

Resolve partial symbol/company name to candidates.

```typescript
  server.tool(
    'search_ticker',
    'Search for ticker symbols by company name or partial symbol.',
    { query: z.string().describe('Search query — company name or partial ticker') },
    async ({ query }) => fetchApi(`/market-data/search?query=${encodeURIComponent(query)}`)
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: market-data
- `alwaysLoaded`: false

**Input:** `query` (string)
**Output:** JSON text list of ticker matches

---

### `get_sec_filings` [Specified]

Retrieve SEC filings for a ticker.

```typescript
  server.tool(
    'get_sec_filings',
    'Retrieve SEC filings (10-K, 10-Q, 8-K) for a given ticker.',
    { ticker: z.string() },
    async ({ ticker }) => fetchApi(`/market-data/sec-filings?ticker=${ticker}`)
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: market-data
- `alwaysLoaded`: false

**Input:** `ticker` (string)
**Output:** JSON text filings list

---

### `list_market_providers` [Specified]

Inspect configured market-data provider status.

> Also categorized as `zorivest-settings` — primary spec lives here.

```typescript
  server.tool(
    'list_market_providers',
    'List all configured market data providers with their enabled/key/test status.',
    {},
    async () => fetchApi('/market-data/providers')
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: market-data
- `alwaysLoaded`: false

**Input:** none
**Output:** JSON text list with enabled/key/test status
**Side Effects:** None (read-only)

---

### `test_market_provider` [Specified]

Validate a provider's API key/connection.

> Also categorized as `zorivest-diagnostics` — primary spec lives here.

```typescript
  server.tool(
    'test_market_provider',
    'Test a market data provider API key and connection.',
    { provider_name: z.string().describe('Provider ID, e.g. "polygon", "alpha_vantage"') },
    async ({ provider_name }) =>
      fetchApi(`/market-data/providers/${provider_name}/test`, { method: 'POST' })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: market-data
- `alwaysLoaded`: false

**Input:** `provider_name` (string)
**Output:** JSON text success/failure detail
**Side Effects:** None (no persistent data write)

---

### `disconnect_market_provider` [Specified]

Remove provider key and disable provider.

> Also categorized as `zorivest-settings` — primary spec lives here.

```typescript
  // MCP annotation: { destructiveHint: true, idempotentHint: false }
  server.tool(
    'disconnect_market_provider',
    'Remove API key and disable a market data provider. Requires explicit confirmation.',
    {
      provider_name: z.string(),
      confirm_destructive: z.literal(true).describe('Must be true to confirm destructive operation'),
    },
    async ({ provider_name }) =>
      fetchApi(`/market-data/providers/${provider_name}/key`, { method: 'DELETE' })
  );
}
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: true
- `idempotentHint`: true
- `toolset`: market-data
- `alwaysLoaded`: false

**Input:** `provider_name` (string), `confirm_destructive` (must be `true`)
**Output:** JSON text removal status
**Side Effects:** **Destructive** — removes provider credential config
**Error Posture:** Returns error if provider not found

---

## REST Endpoint Mapping

| Tool | REST Endpoint |
|------|--------------|
| `get_stock_quote` | `GET /market-data/quote?ticker=` |
| `get_market_news` | `GET /market-data/news` |
| `search_ticker` | `GET /market-data/search?query=` |
| `get_sec_filings` | `GET /market-data/sec-filings?ticker=` |
| `list_market_providers` | `GET /market-data/providers` |
| `test_market_provider` | `POST /market-data/providers/{name}/test` |
| `disconnect_market_provider` | `DELETE /market-data/providers/{name}/key` |
