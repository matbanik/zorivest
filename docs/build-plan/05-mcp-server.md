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

## Step 5.8: `zorivest_diagnose` MCP Tool

> Self-diagnostics tool that agents can call to debug connectivity, check backend health, and inspect runtime state. Inspired by Pomera's `pomera_diagnose` ([`_mcp-manager-architecture.md`](../../_inspiration/_mcp-manager-architecture.md#performance-metrics-coremcpmetricspy)).

Returns:
- Backend connectivity (Python API health check)
- Database status (unlocked/locked, SQLCipher connected)
- Version info (version string + resolution context: `frozen|installed|dev`)
- Guard state (enabled/locked, calls in window, lock reason)
- Configured market data providers (name + status, **never reveals API keys**)
- MCP server uptime, tool count, Node.js version
- Performance metrics summary (if verbose + metrics middleware active — see Step 5.9)

> [!IMPORTANT]
> This tool is **NOT guarded** — it must always be callable, even when the MCP guard is locked (same pattern as `zorivest_emergency_stop`/`zorivest_emergency_unlock`).

```typescript
// mcp-server/src/tools/diagnostics-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { authState } from '../auth/bootstrap.js';
import { metricsCollector } from '../middleware/metrics.js';

/** Non-throwing auth header helper for diagnostics (always-callable tool). */
function getAuthHeadersSafe(): Record<string, string> {
  return authState.sessionToken
    ? { 'Authorization': `Bearer ${authState.sessionToken}` }
    : {};
}

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

export function registerDiagnosticsTools(server: McpServer) {
  server.tool(
    'zorivest_diagnose',
    'Runtime diagnostics. Returns backend health, DB status, guard state, provider availability, and performance metrics. Never reveals API keys.',
    {
      verbose: z.boolean().default(false).describe(
        'Include per-tool latency percentiles (p50/p95/p99) and payload sizes'
      ),
    },
    async ({ verbose }) => {
      const safeFetch = async (url: string, opts?: RequestInit) => {
        try {
          const res = await fetch(url, opts);
          return res.json();
        } catch {
          return null;
        }
      };

      const [health, version, guard, providers] = await Promise.all([
        safeFetch(`${API_BASE}/health`),
        safeFetch(`${API_BASE}/version/`),
        safeFetch(`${API_BASE}/mcp-guard/status`, { headers: getAuthHeadersSafe() }),
        safeFetch(`${API_BASE}/market-data/providers`, { headers: getAuthHeadersSafe() }),
      ]);

      const report = {
        backend: {
          reachable: health !== null,
          status: health?.status ?? 'unreachable',
        },
        version: version ?? { version: 'unknown', context: 'unknown' },
        database: { unlocked: health?.database_unlocked ?? false },
        guard: guard ?? { status: 'unavailable' },
        providers: (providers ?? []).map((p: any) => ({
          name: p.name,
          enabled: p.is_enabled,
          connected: p.has_key,
          // NOTE: Never include api_key or secret fields
        })),
        mcp_server: {
          uptime_minutes: metricsCollector.getUptimeMinutes(),
          tool_count: server.getRegisteredToolCount?.() ?? 'unknown',
          node_version: process.version,
        },
        metrics: metricsCollector.getSummary(verbose),
      };

      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify(report, null, 2),
        }],
      };
    }
  );
}
```

## Step 5.9: Per-Tool Performance Metrics Middleware

> In-memory metrics collector tracking per-tool latency, call counts, error rates, and payload sizes. Inspired by Pomera's `core/mcp/metrics.py` ([`_mcp-manager-architecture.md`](../../_inspiration/_mcp-manager-architecture.md#performance-metrics-coremcpmetricspy)).

### What's Collected

| Metric | Per-Tool | Session-Level |
|---|---|---|
| Latency | avg, min, max, p50, p95, p99 (ms) | — |
| Call count | ✅ | `total_tool_calls` |
| Error count + rate | ✅ | `overall_error_rate` |
| Payload size (bytes) | avg response size | — |
| Uptime | — | `session_uptime_minutes` |
| Calls/minute | — | `calls_per_minute` |
| Slowest tool | — | by avg latency |
| Most-errored tool | — | by error count |

### Auto-Warnings in `zorivest_diagnose`

| Condition | Warning |
|---|---|
| Error rate > 10% | `Tool 'X' has 15% error rate (3/20 calls)` |
| p95 > 2000ms (non-network tools) | `Tool 'X' p95 latency is 2500ms` |

**Excluded from slow warnings**: `get_stock_quote`, `get_market_news`, `get_sec_filings`, `search_ticker` (network-bound, expected to be slow).

### Design Decisions

| Decision | Rationale |
|---|---|
| In-memory only (no persistence) | Per-session data; resets on restart to avoid stale metrics |
| Ring buffer (last 1000 per tool) | Bounded memory; old latencies age out |
| Singleton module-level instance | One collector per MCP server process |
| No external dependencies | Uses only Node.js built-ins (`performance.now()`) |

### Implementation

```typescript
// mcp-server/src/middleware/metrics.ts

interface ToolMetrics {
  callCount: number;
  errorCount: number;
  latencies: number[];      // ms, ring buffer (last 1000)
  payloadSizes: number[];   // bytes, ring buffer (last 1000)
}

interface MetricsSummary {
  session_uptime_minutes: number;
  total_tool_calls: number;
  overall_error_rate: number;
  calls_per_minute: number;
  slowest_tool: string | null;
  most_errored_tool: string | null;
  per_tool?: Record<string, {
    call_count: number;
    error_count: number;
    error_rate: number;
    latency: { avg: number; min: number; max: number; p50: number; p95: number; p99: number };
    avg_payload_bytes: number;
  }>;
  warnings: string[];
}

const RING_BUFFER_SIZE = 1000;
const NETWORK_TOOLS = new Set([
  'get_stock_quote', 'get_market_news', 'get_sec_filings', 'search_ticker',
]);

export class MetricsCollector {
  private tools = new Map<string, ToolMetrics>();
  private startTime = Date.now();

  record(toolName: string, latencyMs: number, payloadBytes: number, isError: boolean): void {
    let metrics = this.tools.get(toolName);
    if (!metrics) {
      metrics = { callCount: 0, errorCount: 0, latencies: [], payloadSizes: [] };
      this.tools.set(toolName, metrics);
    }
    metrics.callCount++;
    if (isError) metrics.errorCount++;

    // Ring buffer: keep last N entries
    if (metrics.latencies.length >= RING_BUFFER_SIZE) metrics.latencies.shift();
    metrics.latencies.push(latencyMs);
    if (metrics.payloadSizes.length >= RING_BUFFER_SIZE) metrics.payloadSizes.shift();
    metrics.payloadSizes.push(payloadBytes);
  }

  getUptimeMinutes(): number {
    return Math.round((Date.now() - this.startTime) / 60000);
  }

  getSummary(verbose: boolean): MetricsSummary {
    const warnings: string[] = [];
    let totalCalls = 0;
    let totalErrors = 0;
    let slowestTool: string | null = null;
    let slowestAvg = 0;
    let mostErroredTool: string | null = null;
    let mostErrors = 0;
    const perTool: Record<string, any> = {};

    for (const [name, m] of this.tools.entries()) {
      totalCalls += m.callCount;
      totalErrors += m.errorCount;

      const sorted = [...m.latencies].sort((a, b) => a - b);
      const avg = sorted.length ? sorted.reduce((s, v) => s + v, 0) / sorted.length : 0;
      const percentile = (p: number) => {
        if (!sorted.length) return 0;
        const idx = Math.ceil(p * sorted.length) - 1;
        return Math.round(sorted[Math.max(0, idx)]);
      };
      const errorRate = m.callCount ? m.errorCount / m.callCount : 0;

      if (avg > slowestAvg) { slowestAvg = avg; slowestTool = name; }
      if (m.errorCount > mostErrors) { mostErrors = m.errorCount; mostErroredTool = name; }

      // Auto-warnings
      if (errorRate > 0.10) {
        warnings.push(`Tool '${name}' has ${Math.round(errorRate * 100)}% error rate (${m.errorCount}/${m.callCount} calls)`);
      }
      if (percentile(0.95) > 2000 && !NETWORK_TOOLS.has(name)) {
        warnings.push(`Tool '${name}' p95 latency is ${percentile(0.95)}ms`);
      }

      if (verbose) {
        const avgPayload = m.payloadSizes.length
          ? Math.round(m.payloadSizes.reduce((s, v) => s + v, 0) / m.payloadSizes.length)
          : 0;
        perTool[name] = {
          call_count: m.callCount,
          error_count: m.errorCount,
          error_rate: Math.round(errorRate * 10000) / 10000,
          latency: {
            avg: Math.round(avg),
            min: sorted.length ? Math.round(sorted[0]) : 0,
            max: sorted.length ? Math.round(sorted[sorted.length - 1]) : 0,
            p50: percentile(0.50),
            p95: percentile(0.95),
            p99: percentile(0.99),
          },
          avg_payload_bytes: avgPayload,
        };
      }
    }

    const uptimeMin = this.getUptimeMinutes();
    return {
      session_uptime_minutes: uptimeMin,
      total_tool_calls: totalCalls,
      overall_error_rate: totalCalls ? Math.round((totalErrors / totalCalls) * 10000) / 10000 : 0,
      calls_per_minute: uptimeMin > 0 ? Math.round((totalCalls / uptimeMin) * 100) / 100 : 0,
      slowest_tool: slowestTool,
      most_errored_tool: mostErroredTool,
      per_tool: verbose ? perTool : undefined,
      warnings,
    };
  }
}

export const metricsCollector = new MetricsCollector();

/**
 * Wraps an MCP tool handler with performance metrics recording.
 * Composable with withGuard: withMetrics('name', withGuard(handler))
 */
export function withMetrics<T>(
  toolName: string,
  handler: (args: T) => Promise<McpResult>
): (args: T) => Promise<McpResult> {
  return async (args: T) => {
    const start = performance.now();
    try {
      const result = await handler(args);
      const elapsed = performance.now() - start;
      const payloadSize = JSON.stringify(result).length;
      metricsCollector.record(toolName, elapsed, payloadSize, !!result.isError);
      return result;
    } catch (err) {
      metricsCollector.record(toolName, performance.now() - start, 0, true);
      throw err;
    }
  };
}
```

### Middleware Composition

```typescript
// mcp-server/src/index.ts — middleware wrapping order

// Registration: metrics wraps guard wraps handler
// handler → withGuard(handler) → withMetrics('tool_name', withGuard(handler))

// Unguarded tools (diagnose, guard, gui) still get metrics:
// handler → withMetrics('tool_name', handler)
```

## Step 5.10: `zorivest_launch_gui` MCP Tool

> Allows AI agents to launch the Zorivest GUI. If the GUI is not installed, opens the download page and returns structured setup instructions to the agent. Inspired by Pomera's `pomera_launch_gui` ([`_mcp-manager-architecture.md`](../../_inspiration/_mcp-manager-architecture.md#remote-gui-launch-via-mcp-pomera_launch_gui)).

### GUI Discovery (4 methods, tried in order)

| # | Method | How it finds the GUI |
|---|---|---|
| 1 | Packaged Electron app | Check standard install paths (`%LOCALAPPDATA%/Programs/Zorivest` on Windows, `/Applications/Zorivest.app` on macOS, `/usr/bin/zorivest` on Linux) |
| 2 | Development mode | Navigate from MCP server dir → repo root → `ui/` → check for `package.json` |
| 3 | PATH lookup | `which zorivest` / `where zorivest` — system-installed binary |
| 4 | Environment variable | `ZORIVEST_GUI_PATH` → custom install location |

### Cross-Platform Process Detachment

> [!WARNING]
> Python-level subprocess flags (`creationflags`, `start_new_session`) do NOT fully escape IDE-spawned MCP server contexts. OS shell commands are required. See Pomera's implementation notes in [`_mcp-manager-architecture.md`](../../_inspiration/_mcp-manager-architecture.md#cross-platform-process-detachment).

| Platform | Strategy | Why |
|---|---|---|
| **Windows** | `start "" "zorivest.exe"` via `child_process.exec` | `start` fully detaches from IDE process tree |
| **macOS** | `open -a Zorivest` or `nohup ... &` | `open` is macOS-native app launcher |
| **Linux** | `setsid zorivest > /dev/null 2>&1 &` | `setsid` creates new session leader |

### Not-Installed Fallback Flow

When the GUI executable is not found at any discovery path:

1. **Opens the GitHub releases page** in the user's default browser
2. **Returns structured setup instructions to the agent** so the agent can guide the user through installation:

```json
{
  "gui_found": false,
  "message": "Zorivest GUI is not installed. A browser window has been opened to the download page.",
  "setup_instructions": {
    "desktop_app": {
      "description": "Download the Zorivest desktop app (recommended)",
      "url": "https://github.com/matbanik/zorivest/releases/latest",
      "windows": "Download and run the .exe installer from the releases page",
      "macos": "Download and open the .dmg from the releases page",
      "linux": "Download and run the .AppImage from the releases page"
    },
    "from_source": {
      "description": "Run from source (developers)",
      "steps": [
        "git clone https://github.com/matbanik/zorivest",
        "cd zorivest/ui",
        "npm install",
        "npm run dev"
      ]
    },
    "env_hint": "Set ZORIVEST_GUI_PATH=/path/to/zorivest to use a custom install location"
  }
}
```

### Tool Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `wait_for_close` | bool | `false` | If true, blocks until GUI process exits |

### Implementation

```typescript
// mcp-server/src/tools/gui-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { exec } from 'child_process';
import { existsSync } from 'fs';
import { join } from 'path';

const RELEASES_URL = 'https://github.com/matbanik/zorivest/releases/latest';

interface GuiDiscoveryResult {
  found: boolean;
  path: string | null;
  method: 'installed' | 'dev' | 'path' | 'env' | null;
}

function getStandardInstallPaths(): string[] {
  const platform = process.platform;
  if (platform === 'win32') {
    return [
      join(process.env.LOCALAPPDATA ?? '', 'Programs', 'Zorivest', 'Zorivest.exe'),
      join(process.env.PROGRAMFILES ?? '', 'Zorivest', 'Zorivest.exe'),
    ];
  } else if (platform === 'darwin') {
    return ['/Applications/Zorivest.app'];
  } else {
    return ['/usr/bin/zorivest', '/usr/local/bin/zorivest'];
  }
}

function resolveDevModePath(): string | null {
  // Navigate from mcp-server/ → repo root → ui/package.json
  const repoRoot = join(__dirname, '..', '..', '..');
  const uiPkg = join(repoRoot, 'ui', 'package.json');
  return existsSync(uiPkg) ? join(repoRoot, 'ui') : null;
}

function findInPath(name: string): string | null {
  const cmd = process.platform === 'win32' ? 'where' : 'which';
  try {
    const { execSync } = require('child_process');
    return execSync(`${cmd} ${name}`, { encoding: 'utf-8' }).trim().split('\n')[0];
  } catch {
    return null;
  }
}

function discoverGui(): GuiDiscoveryResult {
  // Method 1: Standard install paths
  for (const p of getStandardInstallPaths()) {
    if (existsSync(p)) return { found: true, path: p, method: 'installed' };
  }
  // Method 2: Development mode
  const devPath = resolveDevModePath();
  if (devPath) return { found: true, path: devPath, method: 'dev' };
  // Method 3: PATH lookup
  const pathResult = findInPath('zorivest');
  if (pathResult) return { found: true, path: pathResult, method: 'path' };
  // Method 4: Environment variable
  const envPath = process.env.ZORIVEST_GUI_PATH;
  if (envPath && existsSync(envPath)) return { found: true, path: envPath, method: 'env' };

  return { found: false, path: null, method: null };
}

function launchDetached(target: string, isDev: boolean): void {
  const platform = process.platform;
  if (isDev) {
    // Dev mode: run npm run dev in the ui/ directory
    const cmd = platform === 'win32'
      ? `start "" cmd /c "cd /d ${target} && npm run dev"`
      : `cd "${target}" && nohup npm run dev > /dev/null 2>&1 &`;
    exec(cmd, { windowsHide: true });
    return;
  }
  // Production: launch the packaged executable
  if (platform === 'win32') {
    exec(`start "" "${target}"`, { windowsHide: true });
  } else if (platform === 'darwin') {
    exec(`open "${target}"`);
  } else {
    exec(`setsid "${target}" > /dev/null 2>&1 &`);
  }
}

function openInBrowser(url: string): void {
  const cmd = process.platform === 'win32' ? 'start' :
              process.platform === 'darwin' ? 'open' : 'xdg-open';
  exec(`${cmd} ${url}`);
}

export function registerGuiTools(server: McpServer) {
  server.tool(
    'zorivest_launch_gui',
    'Launch the Zorivest desktop GUI. If not installed, opens the download page and returns setup instructions the agent can relay to the user.',
    {
      wait_for_close: z.boolean().default(false).describe(
        'If true, blocks until GUI process exits'
      ),
    },
    async ({ wait_for_close }) => {
      const discovery = discoverGui();

      if (!discovery.found) {
        openInBrowser(RELEASES_URL);
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              gui_found: false,
              message: 'Zorivest GUI is not installed. A browser window has been opened to the download page.',
              setup_instructions: {
                desktop_app: {
                  description: 'Download the Zorivest desktop app (recommended)',
                  url: RELEASES_URL,
                  windows: 'Download and run the .exe installer from the releases page',
                  macos: 'Download and open the .dmg from the releases page',
                  linux: 'Download and run the .AppImage from the releases page',
                },
                from_source: {
                  description: 'Run from source (developers)',
                  steps: [
                    'git clone https://github.com/matbanik/zorivest',
                    'cd zorivest/ui',
                    'npm install',
                    'npm run dev',
                  ],
                },
                env_hint: 'Set ZORIVEST_GUI_PATH=/path/to/zorivest to use a custom install location',
              },
            }, null, 2),
          }],
        };
      }

      // GUI found — launch it
      if (wait_for_close) {
        // Foreground mode: spawn and wait for exit
        const { execSync } = require('child_process');
        try {
          execSync(`"${discovery.path!}"`, { stdio: 'ignore', windowsHide: true });
        } catch {
          // GUI closed with non-zero exit — ignore
        }
      } else {
        launchDetached(discovery.path!, discovery.method === 'dev');
      }

      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({
            gui_found: true,
            method: discovery.method,
            message: `Zorivest GUI launched via ${discovery.method} (${discovery.path}).`,
          }),
        }],
      };
    }
  );
}
```

### Registration

```typescript
// mcp-server/src/index.ts  (additions)

import { registerDiagnosticsTools } from './tools/diagnostics-tools.js';
import { registerGuiTools } from './tools/gui-tools.js';

// Unguarded tools (always available, even when guard is locked)
registerGuardTools(server);
registerDiagnosticsTools(server);
registerGuiTools(server);

// Guarded tools get both middleware wrappers:
// withMetrics('create_trade', withGuard(handler))
```

## Step 5.11: Vitest Tests for New Tools

### Diagnostics Tests

```typescript
// mcp-server/tests/diagnostics.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('zorivest_diagnose', () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it('returns full report when backend is reachable', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'ok' })))       // /health
      .mockResolvedValueOnce(new Response(JSON.stringify({ version: '1.0.0', context: 'dev' }))) // /version
      .mockResolvedValueOnce(new Response(JSON.stringify({ is_locked: false })))    // /mcp-guard
      .mockResolvedValueOnce(new Response(JSON.stringify([                         // /providers
        { name: 'alpha_vantage', is_enabled: true, has_key: true },
      ])));
    // invoke handler, parse JSON response
    // expect(report.backend.reachable).toBe(true);
    // expect(report.providers[0].name).toBe('alpha_vantage');
    // expect(report.providers[0]).not.toHaveProperty('api_key');
  });

  it('reports unreachable when backend is down', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('ECONNREFUSED'));
    // invoke handler
    // expect(report.backend.reachable).toBe(false);
    // expect(report.database.unlocked).toBe(false);
  });

  it('never reveals API keys in provider list', async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify([
        { name: 'polygon', is_enabled: true, has_key: true, api_key: 'SECRET_KEY_123' },
      ]))
    );
    // invoke handler
    // expect(JSON.stringify(report)).not.toContain('SECRET_KEY_123');
  });
});
```

### GUI Launch Tests

```typescript
// mcp-server/tests/gui.test.ts

import { describe, it, expect, vi } from 'vitest';

describe('zorivest_launch_gui', () => {
  it('returns setup instructions when GUI is not found', async () => {
    // Mock discoverGui → { found: false }
    // invoke handler
    // expect(result.gui_found).toBe(false);
    // expect(result.setup_instructions.desktop_app.url).toContain('releases');
    // expect(exec).toHaveBeenCalledWith(expect.stringContaining('releases'));
  });

  it('launches GUI when found at standard path', async () => {
    // Mock discoverGui → { found: true, path: 'C:/...', method: 'installed' }
    // invoke handler
    // expect(result.gui_found).toBe(true);
    // expect(exec).toHaveBeenCalledWith(expect.stringContaining('start'));
  });

  it('uses npm run dev in development mode', async () => {
    // Mock discoverGui → { found: true, path: '/repo/ui', method: 'dev' }
    // invoke handler
    // expect(exec command).toContain('npm run dev');
  });
});
```

### Metrics Tests

```typescript
// mcp-server/tests/metrics.test.ts

import { describe, it, expect } from 'vitest';
import { MetricsCollector, withMetrics } from '../src/middleware/metrics.js';

describe('MetricsCollector', () => {
  it('records latency and computes percentiles', () => {
    const mc = new MetricsCollector();
    for (let i = 1; i <= 100; i++) mc.record('test_tool', i, 500, false);
    const summary = mc.getSummary(true);
    expect(summary.per_tool?.test_tool.latency.p50).toBeCloseTo(50, 0);
    expect(summary.per_tool?.test_tool.latency.p95).toBeCloseTo(95, 0);
  });

  it('tracks error count and rate', () => {
    const mc = new MetricsCollector();
    for (let i = 0; i < 10; i++) mc.record('test_tool', 10, 100, i < 2);
    const summary = mc.getSummary(true);
    expect(summary.per_tool?.test_tool.error_count).toBe(2);
    expect(summary.per_tool?.test_tool.error_rate).toBeCloseTo(0.2);
  });

  it('warns when error rate exceeds 10%', () => {
    const mc = new MetricsCollector();
    for (let i = 0; i < 10; i++) mc.record('bad_tool', 10, 100, i < 3);
    const summary = mc.getSummary(true);
    expect(summary.warnings).toContainEqual(expect.stringContaining('error rate'));
  });

  it('excludes network tools from slow warnings', () => {
    const mc = new MetricsCollector();
    mc.record('get_stock_quote', 5000, 100, false);
    const summary = mc.getSummary(true);
    expect(summary.warnings).not.toContainEqual(expect.stringContaining('get_stock_quote'));
  });

  it('uses ring buffer to bound memory', () => {
    const mc = new MetricsCollector();
    for (let i = 0; i < 2000; i++) mc.record('test_tool', i, 100, false);
    const summary = mc.getSummary(true);
    // latency min should reflect ring buffer truncation, not i=0
    expect(summary.per_tool?.test_tool.latency.min).toBeGreaterThanOrEqual(1000);
  });
});

describe('withMetrics wrapper', () => {
  it('records successful call metrics', async () => {
    const handler = withMetrics('test_tool', async () => ({
      content: [{ type: 'text' as const, text: 'ok' }],
    }));
    await handler({});
    // verify metricsCollector recorded a call
  });

  it('records failed call metrics', async () => {
    const handler = withMetrics('test_tool', async () => {
      throw new Error('fail');
    });
    await expect(handler({})).rejects.toThrow('fail');
    // verify metricsCollector recorded an error
  });
});
```

## Exit Criteria

- All Vitest tests pass
- Tool schemas validate input/output correctly
- MCP Inspector shows correct tool registration
- Guard middleware blocks/allows tools based on guard state
- `zorivest_diagnose` returns valid report when backend is up AND when it's down
- `zorivest_diagnose` never reveals API keys in output
- `zorivest_launch_gui` launches GUI when found at any discovery path
- `zorivest_launch_gui` returns setup instructions and opens browser when GUI is not installed
- `MetricsCollector` accurately computes latency percentiles and error rates
- `withMetrics()` composes correctly with `withGuard()`

## Outputs

- TypeScript MCP tools (trade/image): `create_trade`, `list_trades`, `attach_screenshot`, `get_trade_screenshots`, `calculate_position_size`, `get_screenshot`
- TypeScript MCP tools (market data, from Phase 8): `get_stock_quote`, `get_market_news`, `search_ticker`, `get_sec_filings`, `list_market_providers`, `test_market_provider`, `disconnect_market_provider`
- TypeScript MCP tools (settings): `get_settings`, `update_settings`
- TypeScript MCP tools (guard): `zorivest_emergency_stop`, `zorivest_emergency_unlock`
- TypeScript MCP tools (diagnostics): `zorivest_diagnose`
- TypeScript MCP tools (GUI): `zorivest_launch_gui`
- MCP guard middleware: `withGuard()` wrapper, `guardCheck()` REST client
- MCP metrics middleware: `withMetrics()` wrapper, `MetricsCollector` class
- Vitest test suite with mocked `fetch()`
