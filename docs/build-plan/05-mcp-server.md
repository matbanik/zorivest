# Phase 5: MCP Server (TypeScript)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 4](04-rest-api.md) | Market data tools require [Phase 8](08-market-data.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Expose service layer operations as MCP tools via a TypeScript MCP server that calls the Python REST API. The MCP server uses the `@modelcontextprotocol/sdk` (reference implementation). Each tool is a thin wrapper around a REST endpoint. Test using Vitest with mocked `fetch()` — **no subprocess, no live backend needed**.

> **Build order note**: Phase 4 (REST API) must be complete before Phase 5, since MCP tools call REST endpoints.

## Step 5.1: MCP Tool Definitions

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

  server.tool(
    'attach_screenshot',
    'Attach a screenshot image to a trade. Image must be base64-encoded. The MCP server decodes base64 and forwards as multipart/form-data to the REST API.',
    {
      trade_id: z.string(),
      image_base64: z.string(),
      mime_type: z.string().default('image/png'),
      caption: z.string().default(''),
    },
    async ({ trade_id, image_base64, mime_type, caption }) => {
      // Decode base64 → binary buffer
      const binaryData = Buffer.from(image_base64, 'base64');

      // Build multipart/form-data (canonical contract: field name = 'file')
      const blob = new Blob([binaryData], { type: mime_type });
      const formData = new FormData();
      formData.append('file', blob, `screenshot.${mime_type.split('/')[1]}`);
      formData.append('caption', caption);

      const res = await fetch(`${API_BASE}/trades/${trade_id}/images`, {
        method: 'POST',
        body: formData,  // Content-Type set automatically by FormData
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );

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
}
```

## Step 5.2: Vitest Unit Tests (Mocked Fetch)

```typescript
// tests/typescript/mcp/trade-tools.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('create_trade', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'created', exec_id: 'T001' }))
    );
  });

  it('calls REST API with correct payload', async () => {
    // call the tool handler directly
    // verify fetch was called with correct URL and body
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/trades'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});
```

## Step 5.3: Image MCP Tools

```typescript
// mcp-server/src/tools/image-tools.ts

server.tool(
  'get_screenshot',
  'Retrieve a screenshot image by ID. Returns metadata and base64 image content for display.',
  { image_id: z.number() },
  async ({ image_id }) => {
    // Fetch image metadata
    const metaRes = await fetch(`${API_BASE}/images/${image_id}`);
    if (!metaRes.ok) {
      return { content: [{ type: 'text' as const, text: 'Image not found' }] };
    }
    const meta = await metaRes.json();

    // Fetch full image bytes as base64
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

## Step 5.4: Market Data MCP Tools (from Phase 8)

> These tools are defined in [Phase 8 §8.5](08-market-data.md) and registered in the same MCP server. Listed here for completeness — see Phase 8 for full implementation.

| Tool | Description | REST Endpoint |
|---|---|---|
| `get_stock_quote` | Real-time stock price data | `GET /market-data/quote?ticker=` |
| `get_market_news` | Financial news, filtered by ticker | `GET /market-data/news` |
| `search_ticker` | Search tickers by company name | `GET /market-data/search?query=` |
| `get_sec_filings` | SEC filings for a company | `GET /market-data/sec-filings?ticker=` |
| `list_market_providers` | All configured provider statuses | `GET /market-data/providers` |
| `test_market_provider` | Test a provider's API connection | `POST /market-data/providers/{name}/test` |
| `disconnect_market_provider` | Remove API key and disable provider | `DELETE /market-data/providers/{name}/key` |

### Server Registration

```typescript
// mcp-server/src/index.ts

import { registerTradeTools } from './tools/trade-tools.js';
import { registerMarketDataTools } from './tools/market-data-tools.js';
import { registerSettingsTools } from './tools/settings-tools.js';

const server = new McpServer({ name: 'zorivest', version: '1.0.0' });

registerTradeTools(server);
registerMarketDataTools(server);  // Phase 8 tools
registerSettingsTools(server);    // UI settings tools
```

## Step 5.5: Settings MCP Tools

> Thin wrappers around the settings REST endpoints (see [Phase 4 §4.3](04-rest-api.md)). Allows AI agents to read/write user preferences (display modes, notification settings).

```typescript
// mcp-server/src/tools/settings-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

export function registerSettingsTools(server: McpServer) {

  server.tool(
    'get_settings',
    'Read all user settings or a specific setting by key. Returns key-value pairs for UI preferences, notification settings, and display modes.',
    { key: z.string().optional().describe('Optional specific setting key to read (e.g. "ui.theme", "notification.warning.enabled")') },
    async ({ key }) => {
      const url = key ? `${API_BASE}/settings/${encodeURIComponent(key)}` : `${API_BASE}/settings`;
      const res = await fetch(url);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );

  server.tool(
    'update_settings',
    'Update one or more user settings. Accepts a key-value map.',
    { settings: z.record(z.string()).describe('Map of setting keys to values, e.g. {"ui.theme": "dark", "notification.info.enabled": "false"}') },
    async ({ settings }) => {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data) }] };
    }
  );
}
```

> **Convention**: All setting values are **strings at the API/MCP boundary**. Consumers parse to their native types (e.g., `"true"` → `boolean`, `"280"` → `number`). The `value_type` column in `SettingModel` is metadata for future typed deserialization but is not enforced at the REST layer.

## Testing Strategy

See [Testing Strategy](testing-strategy.md) for full MCP testing approaches.

- **Speed**: ~50ms per test with mocked `fetch()`
- **IDE restart**: Never needed
- **What it tests**: Tool logic, Zod schema validation, response formatting
- **Limitation**: Doesn't test Python REST API integration

> [!NOTE]
> **Logging MCP tools (future expansion):** When the logging settings GUI ([06f-gui-settings.md](06f-gui-settings.md)) is implemented, corresponding MCP tools for reading/updating per-feature log levels (`get_log_settings`, `update_log_level`) should be added here. These will wrap `GET/PUT /api/v1/settings` with `logging.*` key filtering. See [Phase 1A](01a-logging.md) for the logging architecture.

## Exit Criteria

- All Vitest tests pass
- Tool schemas validate input/output correctly
- MCP Inspector shows correct tool registration

## Outputs

- TypeScript MCP tools (trade/image): `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `calculate_position_size`, `get_screenshot`
- TypeScript MCP tools (market data, from Phase 8): `get_stock_quote`, `get_market_news`, `search_ticker`, `get_sec_filings`, `list_market_providers`, `test_market_provider`, `disconnect_market_provider`
- TypeScript MCP tools (settings): `get_settings`, `update_settings`
- Vitest test suite with mocked `fetch()`
