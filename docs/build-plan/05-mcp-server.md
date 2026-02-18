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

> **Convention**: Setting values at the `GET/PUT /settings` and MCP `get_settings`/`update_settings` boundary are **strings**. Consumers parse to their native types (e.g., `"true"` → `boolean`, `"280"` → `number`). The `value_type` column in `SettingModel` is metadata for future typed deserialization but is not enforced at the REST layer.
>
> **Exception**: The `GET /settings/resolved` and `/config/export|import` routes (defined in [Phase 2A](02a-backup-restore.md)) return **typed JSON values** (bool, int, float) because those endpoints use the `SettingsResolver` which performs type coercion.

## Testing Strategy

See [Testing Strategy](testing-strategy.md) for full MCP testing approaches.

- **Speed**: ~50ms per test with mocked `fetch()`
- **IDE restart**: Never needed
- **What it tests**: Tool logic, Zod schema validation, response formatting
- **Limitation**: Doesn't test Python REST API integration

> [!NOTE]
> **Logging MCP tools (future expansion):** When the logging settings GUI ([06f-gui-settings.md](06f-gui-settings.md)) is implemented, corresponding MCP tools for reading/updating per-feature log levels (`get_log_settings`, `update_log_level`) should be added here. These will wrap `GET/PUT /api/v1/settings` with `logging.*` key filtering. See [Phase 1A](01a-logging.md) for the logging architecture.

## Step 5.7: MCP Auth Bootstrap (Standalone Mode)

In standalone mode the MCP server must unlock the encrypted database before any tools can function. The auth handshake uses the envelope encryption architecture defined in [Phase 4 §4.5](04-rest-api.md).

### Boot Sequence

```
┌─────────────┐                       ┌───────────────┐
│  IDE Client  │──Bearer zrv_sk_...──▶│  MCP Server   │
│  (Cursor,    │                       │  (TS, :8766)  │
│   Windsurf)  │                       └──────┬────────┘
                                              │
                                    POST /api/v1/auth/unlock
                                    { "api_key": "zrv_sk_..." }
                                              │
                                              ▼
                                     ┌────────────────┐
                                     │  Python API    │
                                     │  (:8765)       │
                                     │  → KeyVault    │
                                     │  → SQLCipher   │
                                     └────────────────┘
                                              │
                                     { session_token, role }
                                              │
                                              ▼
                              MCP server stores session_token
                              All proxied REST calls include:
                              Authorization: Bearer <session_token>
```

### Implementation

```typescript
// mcp-server/src/auth/bootstrap.ts

interface AuthState {
  sessionToken: string | null;
  role: string | null;
  expiresAt: number | null;
}

const authState: AuthState = { sessionToken: null, role: null, expiresAt: null };

export async function bootstrapAuth(apiKey: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/unlock`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(`Auth failed (${res.status}): ${err.detail ?? 'unknown'}`);
  }

  const data = await res.json();
  authState.sessionToken = data.session_token;
  authState.role = data.role;
  authState.expiresAt = Date.now() + data.expires_in * 1000;
}

export function getAuthHeaders(): Record<string, string> {
  if (!authState.sessionToken) {
    throw new Error('MCP server not authenticated. Call bootstrapAuth first.');
  }
  return { 'Authorization': `Bearer ${authState.sessionToken}` };
}
```

### IDE Configuration (Standalone)

```json
// .cursor/mcp.json (or equivalent IDE config)
{
  "mcpServers": {
    "zorivest": {
      "url": "http://localhost:8766/mcp",
      "headers": {
        "Authorization": "Bearer zrv_sk_<your_api_key>"
      }
    }
  }
}
```

> [!IMPORTANT]
> The API key in the IDE config is used **once** during bootstrap to obtain a session token. The MCP server never stores the raw API key after bootstrap. If the session expires, the MCP server re-authenticates using the original header value.

### Embedded Mode

When the MCP server runs inside Electron (embedded mode), the GUI has already unlocked the database via passphrase. The MCP server receives a pre-authenticated session token from the main process — no API key bootstrap is needed.

## Step 5.6: MCP Guard Middleware

> Circuit breaker + panic button for MCP tool access.
> Model: [`McpGuardModel`](02-infrastructure.md) | REST: [§4.6](04-rest-api.md) | GUI: [§6f.8](06f-gui-settings.md)

### Guard Check Flow

```
MCP Tool Call
  → guardCheck()
    → POST /api/v1/mcp-guard/check
      → [locked?]           → MCP error: "MCP guard is locked: {reason}"
      → [enabled + OK?]     → increment counter → execute tool
      → [threshold hit?]    → auto-lock + MCP error: "Rate limit exceeded"
      → [disabled?]         → skip check → execute tool
```

### Middleware Implementation

```typescript
// mcp-server/src/middleware/mcp-guard.ts

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765';

interface GuardCheckResult {
  allowed: boolean;
  reason?: string;
}

export async function guardCheck(): Promise<GuardCheckResult> {
  // Session token injected via getAuthHeaders() — same auth model as all other REST calls
  const res = await fetch(`${API_BASE}/api/v1/mcp-guard/check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
  });
  return res.json();
}

/**
 * Wraps an MCP tool handler with guard check.
 * If guard denies, returns MCP error content instead of executing.
 */
export function withGuard<T>(
  handler: (args: T) => Promise<McpResult>
): (args: T) => Promise<McpResult> {
  return async (args: T) => {
    const check = await guardCheck();
    if (!check.allowed) {
      return {
        content: [{
          type: 'text' as const,
          text: `⛔ MCP guard blocked this call: ${check.reason}. Unlock via GUI → Settings → MCP Guard, or via zorivest_emergency_unlock tool.`,
        }],
        isError: true,
      };
    }
    return handler(args);
  };
}
```

### Emergency Stop Tool

```typescript
// mcp-server/src/tools/guard-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765';

export function registerGuardTools(server: McpServer) {
  server.tool(
    'zorivest_emergency_stop',
    'Emergency: Lock all MCP tool access. Use if you detect runaway behavior or a loop.',
    { reason: z.string().default('agent_self_lock') },
    async ({ reason }) => {
      const res = await fetch(`${API_BASE}/api/v1/mcp-guard/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ reason }),
      });
      const data = await res.json();
      return {
        content: [{
          type: 'text' as const,
          text: `🔒 MCP tools locked. Reason: "${reason}". Unlock via GUI → Settings → MCP Guard, or via zorivest_emergency_unlock tool.`,
        }],
      };
    }
  );

  server.tool(
    'zorivest_emergency_unlock',
    'Unlock MCP tools after an emergency stop. Requires confirmation token.',
    { confirm: z.literal('UNLOCK') },
    async () => {
      const res = await fetch(`${API_BASE}/api/v1/mcp-guard/unlock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      });
      const data = await res.json();
      return {
        content: [{
          type: 'text' as const,
          text: data.is_locked
            ? `⚠️ Unlock failed — guard is still locked. Check REST API logs.`
            : `🟢 MCP tools unlocked. Guard is active and accepting calls.`,
        }],
      };
    }
  );
}
```

### Registration

```typescript
// mcp-server/src/index.ts  (additions)

import { registerGuardTools } from './tools/guard-tools.js';
import { withGuard } from './middleware/mcp-guard.js';

// Register guard tool (emergency stop is NOT itself guarded — always available)
registerGuardTools(server);

// Wrap existing tool handlers with guard middleware
// (Applied during registration in registerTradeTools, registerMarketDataTools, etc.)
```

### Vitest Tests

```typescript
// mcp-server/tests/guard.test.ts

import { describe, it, expect, vi } from 'vitest';

describe('MCP Guard Middleware', () => {
  it('allows tool execution when guard is disabled', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ allowed: true }))
    );
    const handler = withGuard(async () => ({
      content: [{ type: 'text' as const, text: 'ok' }],
    }));
    const result = await handler({});
    expect(result.content[0].text).toBe('ok');
  });

  it('blocks tool execution when guard is locked', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ allowed: false, reason: 'manual' }))
    );
    const handler = withGuard(async () => ({
      content: [{ type: 'text' as const, text: 'ok' }],
    }));
    const result = await handler({});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain('MCP guard blocked');
  });

  it('emergency stop tool calls lock endpoint', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ is_locked: true }))
    );
    // Import and invoke the handler directly
    const { registerGuardTools } = await import('../src/tools/guard-tools.js');
    const mockServer = { tool: vi.fn() };
    registerGuardTools(mockServer as any);
    // Extract the emergency_stop handler (first registered tool)
    const [, , , handler] = mockServer.tool.mock.calls[0];
    const result = await handler({ reason: 'test-lock' });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/mcp-guard/lock'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ reason: 'test-lock' }),
      })
    );
    expect(result.content[0].text).toContain('MCP tools locked');
  });

  it('emergency unlock tool calls unlock endpoint', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ is_locked: false }))
    );
    const { registerGuardTools } = await import('../src/tools/guard-tools.js');
    const mockServer = { tool: vi.fn() };
    registerGuardTools(mockServer as any);
    // Extract the emergency_unlock handler (second registered tool)
    const [, , , handler] = mockServer.tool.mock.calls[1];
    const result = await handler({ confirm: 'UNLOCK' });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/mcp-guard/unlock'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(result.content[0].text).toContain('MCP tools unlocked');
  });

  it('blocks tool execution when rate limit exceeded', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ allowed: false, reason: 'rate_limit_exceeded' }))
    );
    const handler = withGuard(async () => ({
      content: [{ type: 'text' as const, text: 'ok' }],
    }));
    const result = await handler({});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain('rate_limit_exceeded');
  });
});
```

## Exit Criteria

- All Vitest tests pass
- Tool schemas validate input/output correctly
- MCP Inspector shows correct tool registration
- Guard middleware blocks/allows tools based on guard state

## Outputs

- TypeScript MCP tools (trade/image): `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `calculate_position_size`, `get_screenshot`
- TypeScript MCP tools (market data, from Phase 8): `get_stock_quote`, `get_market_news`, `search_ticker`, `get_sec_filings`, `list_market_providers`, `test_market_provider`, `disconnect_market_provider`
- TypeScript MCP tools (settings): `get_settings`, `update_settings`
- TypeScript MCP tools (guard): `zorivest_emergency_stop`, `zorivest_emergency_unlock`
- MCP guard middleware: `withGuard()` wrapper, `guardCheck()` REST client
- Vitest test suite with mocked `fetch()`
