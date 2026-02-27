# Phase 5: MCP Server (Shared Infrastructure Hub)

> Expose Zorivest service-layer operations as [Model Context Protocol](https://modelcontextprotocol.io/) tools for agentic IDE interaction.
>
> Prereq: [Phase 4 (REST API)](04-rest-api.md) | Consumers: [Phase 6 (GUI)](06-gui.md), [Phase 9 (Scheduling)](09-scheduling.md)

---

> **Hub-only file.** All MCP tool contracts live in their respective category files below.
> This file retains only **shared infrastructure**: auth bootstrap, guard middleware, metrics middleware, SDK compatibility, test patterns, and exit criteria.

## Category Files

| File | Category | Specified | Planned | Future | Total |
|------|----------|-----------|---------|--------|-------|
| [05a-mcp-zorivest-settings.md](05a-mcp-zorivest-settings.md) | `zorivest-settings` | 4 | — | 2 | 6 |
| [05b-mcp-zorivest-diagnostics.md](05b-mcp-zorivest-diagnostics.md) | `zorivest-diagnostics` | 5 | — | — | 5 |
| [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) | `trade-analytics` | 17 | 2 | — | 19 |
| [05d-mcp-trade-planning.md](05d-mcp-trade-planning.md) | `trade-planning`, `calculator` | 1 | 1 | — | 2 |
| [05e-mcp-market-data.md](05e-mcp-market-data.md) | `market-data` | 7 | — | — | 7 |
| [05f-mcp-accounts.md](05f-mcp-accounts.md) | `accounts` | 7 | 1 | — | 8 |
| [05g-mcp-scheduling.md](05g-mcp-scheduling.md) | `scheduling` | 6 | — | — | 6 |
| [05h-mcp-tax.md](05h-mcp-tax.md) | `tax` | — | 8 | — | 8 |
| [05i-mcp-behavioral.md](05i-mcp-behavioral.md) | `behavioral` | 3 | — | — | 3 |
| [05j-mcp-discovery.md](05j-mcp-discovery.md) | `discovery` | 4 | — | — | 4 |
| **Totals** | | **54** | **12** | **2** | **68** |

---

## Step 5.1: Trade Tools

> **Spec location:** [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) (core trades, screenshots, analytics), [05d-mcp-trade-planning.md](05d-mcp-trade-planning.md) (position sizing, trade plans)

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

## Step 5.3: Image Tools

> **Spec location:** [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) (`get_screenshot`, `attach_screenshot`, `get_trade_screenshots`)

## Step 5.4: Market Data Tools

> **Spec location:** [05e-mcp-market-data.md](05e-mcp-market-data.md)

## Step 5.5: Settings & Guard Tools

> **Spec location:** [05a-mcp-zorivest-settings.md](05a-mcp-zorivest-settings.md) (settings CRUD, emergency stop/unlock, future logging tools)

> **Convention**: Setting values at the `GET/PUT /settings` and MCP `get_settings`/`update_settings` boundary are **strings**. Consumers parse to their native types (e.g., `"true"` → `boolean`, `"280"` → `number`). The `value_type` column in `SettingModel` is metadata for future typed deserialization but is not enforced at the REST layer.
>
> **Exception**: The `GET /settings/resolved` and `/config/export|import` routes (defined in [Phase 2A](02a-backup-restore.md)) return **typed JSON values** (bool, int, float) because those endpoints use the `SettingsResolver` which performs type coercion.

## Testing Strategy

See [Testing Strategy](testing-strategy.md) for full MCP testing approaches.

- **Speed**: ~50ms per test with mocked `fetch()`
- **IDE restart**: Never needed
- **What it tests**: Tool logic, Zod schema validation, response formatting
- **Limitation**: Doesn't test Python REST API integration

---

## Step 5.6: MCP Guard Middleware

> Circuit breaker + panic button for MCP tool access.
> Model: [`McpGuardModel`](02-infrastructure.md) | REST: [§4.6](04-rest-api.md) | GUI: [§6f.8](06f-gui-settings.md)
>
> **Tool specs:** `zorivest_emergency_stop`, `zorivest_emergency_unlock` → [05a-mcp-zorivest-settings.md](05a-mcp-zorivest-settings.md)

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

---

## Step 5.7: MCP Auth Bootstrap

The MCP server must unlock the encrypted database before any tools can function. The auth handshake uses the envelope encryption architecture defined in [Phase 4 §4.5](04-rest-api.md).

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

### IDE Configuration

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

> [!NOTE]
> **Design Decision (2026-02-26):** The MCP server always runs as a separate process.
> Embedding inside Electron was evaluated and rejected due to 5 shared-process security
> risks: trust boundary collapse (shared memory), IDE-initiated attacks on pre-authenticated
> sessions, MCP Guard bypass, session scope inflation (full owner role), and expanded
> Electron attack surface. The standalone model ensures clean auth separation (passphrase
> for GUI, API key for MCP) and independent process lifecycle.

---

## Step 5.8: Diagnostics & GUI Launch Tools

> **Spec location:** [05b-mcp-zorivest-diagnostics.md](05b-mcp-zorivest-diagnostics.md) (`zorivest_diagnose`, `zorivest_launch_gui`, `zorivest_service_status`, `zorivest_service_restart`, `zorivest_service_logs`)

> [!IMPORTANT]
> `zorivest_diagnose` is **NOT guarded** — it must always be callable, even when the MCP guard is locked (same pattern as `zorivest_emergency_stop`/`zorivest_emergency_unlock`).

### GUI Discovery (4 methods, tried in order)

| # | Method | How it finds the GUI |
|---|---|---|
| 1 | Packaged Electron app | Check standard install paths (`%LOCALAPPDATA%/Programs/Zorivest` on Windows, `/Applications/Zorivest.app` on macOS, `/usr/bin/zorivest` on Linux) |
| 2 | Development mode | Navigate from MCP server dir → repo root → `ui/` → check for `package.json` |
| 3 | PATH lookup | `which zorivest` / `where zorivest` — system-installed binary |
| 4 | Environment variable | `ZORIVEST_GUI_PATH` → custom install location |

### Cross-Platform Process Detachment

> [!WARNING]
> Python-level subprocess flags (`creationflags`, `start_new_session`) do NOT fully escape IDE-spawned MCP server contexts. OS shell commands are required.

| Platform | Strategy | Why |
|---|---|---|
| **Windows** | `start "" "zorivest.exe"` via `child_process.exec` | `start` fully detaches from IDE process tree |
| **macOS** | `open -a Zorivest` or `nohup ... &` | `open` is macOS-native app launcher |
| **Linux** | `setsid zorivest > /dev/null 2>&1 &` | `setsid` creates new session leader |

---

## Step 5.9: Per-Tool Performance Metrics Middleware

> In-memory metrics collector tracking per-tool latency, call counts, error rates, and payload sizes.

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

## Step 5.10: Registration Index

```typescript
// mcp-server/src/index.ts

import { registerSettingsTools } from './tools/settings-tools.js';
import { registerGuardTools } from './tools/guard-tools.js';
import { registerDiagnosticsTools } from './tools/diagnostics-tools.js';
import { registerGuiTools } from './tools/gui-tools.js';
import { registerTradeTools } from './tools/trade-tools.js';
import { registerMarketDataTools } from './tools/market-data-tools.js';
import { registerExpansionTools } from './tools/expansion-tools.js';
import { registerSchedulingTools } from './tools/scheduling-tools.js';
import { registerServiceTools } from './tools/service.js';
import { withGuard } from './middleware/mcp-guard.js';

// Unguarded tools (always available, even when guard is locked)
registerGuardTools(server);
registerDiagnosticsTools(server);
registerGuiTools(server);

// Guarded tools get both middleware wrappers:
// withMetrics('create_trade', withGuard(handler))
registerSettingsTools(server);
registerTradeTools(server);
registerMarketDataTools(server);
registerExpansionTools(server);
registerSchedulingTools(server);
registerServiceTools(server);
```

## Step 5.10a: Expansion Tools

> **Spec location:** [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) (analytics tools), [05f-mcp-accounts.md](05f-mcp-accounts.md) (broker/banking tools), [05i-mcp-behavioral.md](05i-mcp-behavioral.md) (behavioral tools)

### Expansion Tool Registry

| Tool Name | Source §§ | Category File |
|-----------|----------|---------------|
| `sync_broker` | §1, §2 | [05f](05f-mcp-accounts.md) |
| `list_brokers` | §1, §24, §25 | [05f](05f-mcp-accounts.md) |
| `get_round_trips` | §3 | [05c](05c-mcp-trade-analytics.md) |
| `resolve_identifiers` | §5 | [05f](05f-mcp-accounts.md) |
| `enrich_trade_excursion` | §7 | [05c](05c-mcp-trade-analytics.md) |
| `detect_options_strategy` | §8 | [05c](05c-mcp-trade-analytics.md) |
| `get_fee_breakdown` | §9 | [05c](05c-mcp-trade-analytics.md) |
| `score_execution_quality` | §10 | [05c](05c-mcp-trade-analytics.md) |
| `estimate_pfof_impact` | §11 | [05c](05c-mcp-trade-analytics.md) |
| `get_expectancy_metrics` | §13 | [05c](05c-mcp-trade-analytics.md) |
| `simulate_drawdown` | §14 | [05c](05c-mcp-trade-analytics.md) |
| `get_strategy_breakdown` | §21 | [05c](05c-mcp-trade-analytics.md) |
| `get_sqn` | §15 | [05c](05c-mcp-trade-analytics.md) |
| `get_cost_of_free` | §22 | [05c](05c-mcp-trade-analytics.md) |
| `ai_review_trade` | §12 | [05c](05c-mcp-trade-analytics.md) |
| `track_mistake` | §17 | [05i](05i-mcp-behavioral.md) |
| `get_mistake_summary` | §17 | [05i](05i-mcp-behavioral.md) |
| `link_trade_journal` | §16 | [05i](05i-mcp-behavioral.md) |
| `import_bank_statement` | §26 | [05f](05f-mcp-accounts.md) |
| `import_broker_csv` | §18 | [05f](05f-mcp-accounts.md) |
| `import_broker_pdf` | §19 | [05f](05f-mcp-accounts.md) |
| `list_bank_accounts` | §26 | [05f](05f-mcp-accounts.md) |

> [!NOTE]
> **Name Authority (CR2-3):** The canonical tool names are those defined in the category files. All downstream references must use the canonical names.

## Step 5.10b: Vitest Tests

### Diagnostics Tests

> **Spec location:** [05b-mcp-zorivest-diagnostics.md](05b-mcp-zorivest-diagnostics.md) for tool contracts. Test patterns below.

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
  });

  it('launches GUI when found at standard path', async () => {
    // Mock discoverGui → { found: true, path: 'C:/...', method: 'installed' }
  });

  it('uses npm run dev in development mode', async () => {
    // Mock discoverGui → { found: true, path: '/repo/ui', method: 'dev' }
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

---

## Step 5.11: Toolset Configuration

> **Spec location:** [05j-mcp-discovery.md](05j-mcp-discovery.md) (meta-tools, confirmation tokens)

Toolsets group related MCP tools into named categories for selective loading. This is the primary mechanism for keeping the active tool count within IDE limits.

### Toolset Definitions (Authoritative)

| Toolset | Category File(s) | Tools | Default Loaded | Description |
|---------|-----------------|-------|---------------|-------------|
| `core` | 05a, 05b | 11 | ✅ Always | Settings, emergency stop/unlock, diagnostics, GUI launch, service tools |
| `discovery` | 05j | 4 | ✅ Always | Meta-tools for toolset browsing, enabling, and confirmation tokens |
| `trade-analytics` | 05c | 19 | ✅ Default | Trade CRUD, screenshots, analytics, reports |
| `trade-planning` | 05c, 05d | 3 | ✅ Default | Position calculator, trade plans (includes `create_trade` cross-tagged from 05c) |
| `market-data` | 05e | 7 | ⬜ Deferred | Stock quotes, news, SEC filings, ticker search |
| `accounts` | 05f | 8 | ⬜ Deferred | Account management, broker sync, CSV import |
| `scheduling` | 05g | 6 | ⬜ Deferred | Policy CRUD, pipeline execution, scheduler status |
| `tax` | 05h | 8 | ⬜ Deferred | Tax estimation, wash sales, lot management, harvesting |
| `behavioral` | 05i | 3 | ⬜ Deferred | Mistake tracking, expectancy, Monte Carlo |

**Default active tools:** `core` + `discovery` + `trade-analytics` + `trade-planning` = **37 tools** (fits under Cursor's 40-tool limit).

### `--toolsets` CLI Flag

Users and IDE configurations specify which toolsets to load at startup:

```bash
# Default (core + discovery always loaded, plus defaults)
npx @zorivest/mcp-server --api-url http://localhost:8765

# Explicit toolset selection
npx @zorivest/mcp-server --toolsets trade-analytics,market-data,accounts

# All toolsets (not recommended for Cursor/Windsurf)
npx @zorivest/mcp-server --toolsets all
```

`core` and `discovery` are **always loaded** regardless of the `--toolsets` flag (15 tools minimum).

### `toolset-config.json`

Persistent toolset preferences file (optional, overridden by `--toolsets` flag):

```json
{
  "defaultToolsets": ["trade-analytics", "trade-planning"],
  "clientOverrides": {
    "cursor": ["trade-analytics"],
    "claude-code": ["all"]
  }
}
```

---

## Step 5.12: Adaptive Client Detection

During the MCP `initialize` handshake, the server inspects the client's declared capabilities to select the optimal tool surfacing strategy.

### Detection Flowchart

```
Server starts → receives initialize request from IDE
  ├─ Client is Anthropic (Claude Code, Claude Desktop, API)
  │  → Mark deferred toolsets with defer_loading: true
  │  → Expose Tool Search meta-tool
  │  → 15 core + discovery tools always loaded
  │  → Remaining tools discoverable via BM25/regex search
  │
  ├─ Client supports tools.listChanged (Gemini CLI, Cline, Antigravity)
  │  → Expose meta-tools: list_available_toolsets, describe_toolset, enable_toolset
  │  → Start with default toolsets (37 core tools)
  │  → Agent dynamically loads categories via notifications/tools/list_changed
  │
  └─ Client is capability-limited (Cursor, Windsurf)
      → Use --toolsets flag / env var to pre-select categories
      → Load only selected toolsets (stays under 40-tool limit)
      → No dynamic changes during session
```

### Client Identification

| Signal | Where | Example Values |
|--------|-------|---------------|
| `clientInfo.name` | MCP `initialize` request | `"claude-code"`, `"cursor"`, `"windsurf"`, `"cline"`, `"antigravity"` |
| `capabilities.tools.listChanged` | MCP `initialize` request | `true` / absent |
| `ZORIVEST_CLIENT_MODE` | Environment variable | `anthropic`, `dynamic`, `static` (manual override) |

### Mode Mapping

| `clientInfo.name` | Detected Mode | Rationale |
|-------------------|--------------|----------|
| `claude-code`, `claude-desktop` | `anthropic` | Supports `defer_loading` + Tool Search |
| `cline`, `roo-code`, `antigravity`, `gemini-cli` | `dynamic` | Supports `tools.listChanged` notifications |
| `cursor`, `windsurf` | `static` | No dynamic tool changes; pre-select via `--toolsets` |
| (unknown) | `static` | Safe default — respects IDE limits |

The `ZORIVEST_CLIENT_MODE` env var overrides auto-detection for testing or edge cases.

---

## Step 5.13: Adaptive Design Patterns

Six optimization patterns adapt server behavior per detected client mode. Patterns A, B, D, E are implemented in this session; Patterns C (composites) and F (PTC) are deferred to Sessions 5 and 6.

### Pattern A: Adaptive Response Compression

Tool results are adjusted based on client context budget:

| Client Type | Response Mode | Behavior |
|-------------|--------------|----------|
| Anthropic (200K context) | `detailed` | Full JSON: metadata, audit fields, nested objects |
| Gemini (2M context) | `detailed` | Full payloads — can afford them |
| Cursor / Windsurf (tight budget) | `concise` | Strip UUIDs, timestamps, raw audit data; key fields only |

A session-level `responseFormat` flag is set during `initialize` and checked by every tool handler.

### Pattern B: Tiered Tool Descriptions

| Client Type | Description Tier | Length |
|-------------|-----------------|--------|
| Has Tool Search (Anthropic) | **Rich** — "when to use" / "when NOT to use" / examples / discriminators | 200-400 chars |
| Eager-loaded (all others) | **Minimal** — verb + noun + one discriminator | 50-100 chars |

Richer descriptions improve Tool Search discovery accuracy. For eager-loaded clients, shorter descriptions save tokens.

### Pattern D: Adaptive Server Instructions

MCP `server instructions` field provides per-client chaining guidance:

| Client Type | Instruction Focus |
|-------------|------------------|
| Anthropic | "Use tool_search to discover tools. Prefer sequential execution. For multi-metric analysis, use code_execution to batch calls." |
| Dynamic | "Available categories: [list]. Use list_available_toolsets/enable_toolset to load categories on demand." |
| Static | "You have [N] tools from [X, Y] categories. Other categories require server restart with different --toolsets flag." |

### Pattern E: Safety Confirmation Adaptation

> [!CAUTION]
> **Critical for financial trading.** Different clients handle `destructiveHint` differently.

| Client Type | Safety Mechanism |
|-------------|------------------|
| Annotation-aware (Claude Code, Roo Code) | IDE-driven approval flow. `destructiveHint: true` → IDE prompts user. |
| Annotation-unaware (Cursor, others) | **Server-side 2-step gate**: destructive tools require a `confirmation_token`. Token obtained from `get_confirmation_token` tool ([05j](05j-mcp-discovery.md)). Forces 2-call execution. |

Destructive tools requiring confirmation: `zorivest_emergency_stop`, `create_trade`, `sync_broker`, `disconnect_market_provider`, `zorivest_service_restart`.

> **Cross-reference:** REST endpoint `POST /api/v1/confirmation-tokens` specified in [Phase 4](04-rest-api.md) (Session 4).

---

## Step 5.14: Tool Registration Flow

The updated registration flow composes annotations, guard, and metrics middleware:

```typescript
// mcp-server/src/registration.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { toolsetRegistry } from './toolsets/registry.js';

export function registerToolsForClient(
  server: McpServer,
  clientMode: 'anthropic' | 'dynamic' | 'static',
  requestedToolsets: string[]
): void {
  // 1. Always register core + discovery (alwaysLoaded)
  for (const ts of toolsetRegistry.getAll()) {
    if (ts.alwaysLoaded) {
      ts.register(server);
      toolsetRegistry.markLoaded(ts.name);
    }
  }

  // 2. Register requested/default toolsets
  const toLoad = requestedToolsets.length > 0
    ? requestedToolsets
    : toolsetRegistry.getDefaults();

  for (const name of toLoad) {
    const ts = toolsetRegistry.get(name);
    if (ts && !ts.loaded) {
      if (clientMode === 'anthropic') {
        // Mark as deferred — Anthropic Tool Search will index them
        ts.registerDeferred(server);
      } else {
        ts.register(server);
        toolsetRegistry.markLoaded(name);
      }
    }
  }
}
```

### Annotation Registration

Each tool is registered with its annotation object from the `#### Annotations` block:

```typescript
server.tool(
  'get_settings',
  'Read all user settings or a specific setting by key.',
  { key: z.string().optional() },
  handler,
  {
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
    },
  }
);
```

### Middleware Composition Order

```
Tool call → withMetrics() → withGuard() → withConfirmation() → handler
```

- `withMetrics()` — always applied (records latency, payload size, errors)
- `withGuard()` — applied to all guarded tools (not applied to emergency stop/unlock, diagnose)
- `withConfirmation()` — applied to destructive tools on annotation-unaware clients only

---

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
- Expansion MCP tools delegate correctly to REST endpoints
- `zorivest_service_status` returns health + process metrics when backend is up
- `zorivest_service_restart` triggers graceful shutdown and polls for recovery
- `zorivest_service_logs` returns log directory path and file listing
- All tools have MCP annotation blocks (`readOnlyHint`, `destructiveHint`, `idempotentHint`)
- `--toolsets` flag correctly filters tool registration (default ≤ 40 tools)
- Client detection selects appropriate mode (anthropic/dynamic/static)
- Meta-tools (`list_available_toolsets`, `describe_toolset`, `enable_toolset`) return accurate state
- `get_confirmation_token` issues valid 60s tokens for destructive operations
- `enable_toolset` sends `notifications/tools/list_changed` on dynamic clients
- `enable_toolset` returns guidance on static clients

## Outputs

- **Tool specs**: 68 tools across 10 category files (see [Category Files](#category-files) above)
- **Shared infrastructure** (this file):
  - MCP guard middleware: `withGuard()` wrapper, `guardCheck()` REST client
  - MCP metrics middleware: `withMetrics()` wrapper, `MetricsCollector` class
  - Auth bootstrap: `bootstrapAuth()`, `getAuthHeaders()`
  - Toolset registry: `ToolsetRegistry` class, `--toolsets` CLI flag
  - Client detection: `detectClientMode()`, `ZORIVEST_CLIENT_MODE` env var
  - Adaptive patterns: response compression, tiered descriptions, server instructions, safety confirmation
  - Registration flow: `registerToolsForClient()` with annotation composition
- Vitest test suite with mocked `fetch()`

## MCP SDK Compatibility

> [!IMPORTANT]
> The `@modelcontextprotocol/sdk` is pinned to `^1.26.0` in the [dependency manifest](dependency-manifest.md). All code in this file targets the v1.x API surface.

| Aspect | Our Target | Notes |
|--------|-----------|-------|
| Import path | `@modelcontextprotocol/sdk/server/mcp.js` | v1.x convenience import |
| Tool registration | `server.tool(name, desc, schema, handler)` | Convenience API; `registerTool()` is also available |
| Tool output | `content: [{ type: 'text', text: ... }]` | Structured `outputSchema` support available in v1.25+ but not yet adopted |
| Zod schemas | `z.string()`, `z.number()`, etc. | Zod is the schema library for tool input validation |

### Migration Rules

- **Do not upgrade past v1.x** without updating all `server.tool(...)` calls and import paths
- **Run `tsc --noEmit`** after any SDK version bump to verify compilation
- **Add CI smoke test**: compile MCP server bootstrap against locked SDK version
