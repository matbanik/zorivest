# Phase 5: MCP Server (TypeScript)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

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

## Testing Strategy

See [Testing Strategy](testing-strategy.md) for full MCP testing approaches.

- **Speed**: ~50ms per test with mocked `fetch()`
- **IDE restart**: Never needed
- **What it tests**: Tool logic, Zod schema validation, response formatting
- **Limitation**: Doesn't test Python REST API integration

## Exit Criteria

- All Vitest tests pass
- Tool schemas validate input/output correctly
- MCP Inspector shows correct tool registration

## Outputs

- TypeScript MCP tools: `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `calculate_position_size`, `get_screenshot`
- Vitest test suite with mocked `fetch()`
