# Phase 5j: MCP Tools — Discovery & Safety

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `discovery`
>
> Meta-tools for dynamic tool discovery, toolset management, and destructive-operation confirmation.
> Architecture rationale: Adaptive tool surfacing based on client capabilities — see [§5.11](05-mcp-server.md#step-511-toolset-configuration) and [§5.12](05-mcp-server.md#step-512-adaptive-client-detection) in the hub file.

## Tools

### `list_available_toolsets` [Specified]

List all toolset groups with their descriptions, tool counts, and loaded status.

```typescript
// mcp-server/src/tools/discovery-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { toolsetRegistry } from '../toolsets/registry.js';
import { getAuthHeaders } from '../auth/bootstrap.js';

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

export function registerDiscoveryTools(server: McpServer) {

  server.tool(
    'list_available_toolsets',
    'List all available toolset groups. Returns name, description, tool count, and whether currently loaded. Use this to discover what capabilities are available before enabling specific toolsets.',
    {},
    async () => {
      const toolsets = toolsetRegistry.getAll();
      const summary = toolsets.map(ts => ({
        name: ts.name,
        description: ts.description,
        tool_count: ts.tools.length,
        loaded: ts.loaded,
        always_loaded: ts.alwaysLoaded,
      }));
      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({ toolsets: summary, total_tools: summary.reduce((n, ts) => n + ts.tool_count, 0) }, null, 2),
        }],
      };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: discovery
- `alwaysLoaded`: true

**Input:** (none)
**Output:** JSON array of toolset objects: `{ name, description, tool_count, loaded, always_loaded }` + `total_tools` count
**Side Effects:** None (read-only)
**Error Posture:** Always succeeds — in-memory registry lookup

---

### `describe_toolset` [Specified]

Get detailed information about a specific toolset including all tool names and descriptions.

```typescript
  server.tool(
    'describe_toolset',
    'Describe a specific toolset: returns all tool names, descriptions, and annotation hints. Use after list_available_toolsets to inspect a category before enabling it.',
    {
      toolset_name: z.string().describe('Toolset name from list_available_toolsets (e.g. "trade-analytics", "tax")'),
    },
    async ({ toolset_name }) => {
      const ts = toolsetRegistry.get(toolset_name);
      if (!ts) {
        return {
          content: [{
            type: 'text' as const,
            text: `Unknown toolset "${toolset_name}". Use list_available_toolsets to see available groups.`,
          }],
          isError: true,
        };
      }
      const detail = {
        name: ts.name,
        description: ts.description,
        loaded: ts.loaded,
        tools: ts.tools.map(t => ({
          name: t.name,
          description: t.description,
          annotations: t.annotations,
        })),
      };
      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify(detail, null, 2),
        }],
      };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: discovery
- `alwaysLoaded`: true

**Input:** `toolset_name` (string)
**Output:** JSON object: `{ name, description, loaded, tools: [{ name, description, annotations }] }`
**Side Effects:** None (read-only)
**Error Posture:** Returns `isError: true` with guidance if toolset name not found

---

### `enable_toolset` [Specified]

Dynamically activate a toolset for the current session. Only available on clients that support `notifications/tools/list_changed`.

```typescript
  server.tool(
    'enable_toolset',
    'Enable a toolset for this session. Registers the tools and sends a tools/list_changed notification. Only works on dynamic clients (clients that support notifications/tools/list_changed). Static clients must restart with a different --toolsets flag.',
    {
      toolset_name: z.string().describe('Toolset to enable (e.g. "tax", "behavioral")'),
    },
    async ({ toolset_name }) => {
      const ts = toolsetRegistry.get(toolset_name);
      if (!ts) {
        return {
          content: [{
            type: 'text' as const,
            text: `Unknown toolset "${toolset_name}". Use list_available_toolsets to see available groups.`,
          }],
          isError: true,
        };
      }
      if (ts.loaded) {
        return {
          content: [{
            type: 'text' as const,
            text: `Toolset "${toolset_name}" is already loaded (${ts.tools.length} tools).`,
          }],
        };
      }

      if (!server.clientSupportsNotification('notifications/tools/list_changed')) {
        return {
          content: [{
            type: 'text' as const,
            text: `Dynamic tool loading is not supported by your IDE. Restart the MCP server with --toolsets ${toolset_name} to include this category.`,
          }],
          isError: true,
        };
      }

      // Register all tools in the toolset
      ts.register(server);
      toolsetRegistry.markLoaded(toolset_name);

      // Notify client that tool list has changed
      await server.notification({ method: 'notifications/tools/list_changed' });

      return {
        content: [{
          type: 'text' as const,
          text: `✅ Toolset "${toolset_name}" enabled (${ts.tools.length} tools). Tools are now available.`,
        }],
      };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: discovery
- `alwaysLoaded`: true

**Input:** `toolset_name` (string)
**Output:** Text confirmation or error with guidance
**Side Effects:** Registers new tools in the MCP server, sends `notifications/tools/list_changed`
**Error Posture:** Returns `isError: true` if toolset unknown or client doesn't support dynamic loading

---

### `get_confirmation_token` [Specified]

Generate a time-limited confirmation token for destructive operations. Required by annotation-unaware clients as a server-side safety gate.

> [!CAUTION]
> **Financial safety tool.** This implements the 2-step confirmation pattern for destructive operations (emergency_stop, create_trade, sync_broker, etc.) on clients that don't support MCP annotations. On annotation-aware clients (Claude Code, Roo Code), IDE-driven approval flows handle confirmation and this tool is informational only.

```typescript
  server.tool(
    'get_confirmation_token',
    'Generate a confirmation token for a destructive operation. Required before executing state-mutating tools on clients without annotation support. Token expires after 60 seconds.',
    {
      action: z.string().describe('Tool name requiring confirmation (e.g. "zorivest_emergency_stop", "create_trade")'),
      params_summary: z.string().describe('Human-readable summary of the operation parameters'),
    },
    async ({ action, params_summary }) => {
      const res = await fetch(`${API_BASE}/confirmation-tokens`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ action, params_summary }),
      });
      const data = await res.json();
      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({
            token: data.token,
            action: action,
            params_summary: params_summary,
            expires_in_seconds: 60,
            instruction: `Pass this token as the confirmation_token parameter when calling ${action}.`,
          }, null, 2),
        }],
      };
    }
  );
}
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: discovery
- `alwaysLoaded`: true

**Input:** `action` (string — tool name), `params_summary` (string — human-readable description)
**Output:** JSON: `{ token, action, params_summary, expires_in_seconds, instruction }`
**Side Effects:** Creates a time-limited token on the server (60s TTL)
**Error Posture:** Returns error if action is not a recognized destructive tool

> **Cross-reference:** REST endpoint `POST /api/v1/confirmation-tokens` specified in [Phase 4](04-rest-api.md) (Session 4).

---

## Vitest Tests

```typescript
// mcp-server/tests/discovery-tools.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('list_available_toolsets', () => {
  it('returns all registered toolsets', async () => {
    // Mock toolsetRegistry.getAll() to return test toolsets
    // Verify response includes name, description, tool_count, loaded
  });

  it('includes total_tools count', async () => {
    // Verify total_tools sums all tool_count values
  });
});

describe('describe_toolset', () => {
  it('returns tool details for known toolset', async () => {
    // Mock registry.get('trade-analytics')
    // Verify response includes tools array with names and annotations
  });

  it('returns isError for unknown toolset', async () => {
    const result = await handler({ toolset_name: 'nonexistent' });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain('list_available_toolsets');
  });
});

describe('enable_toolset', () => {
  it('registers tools and sends notification on dynamic client', async () => {
    // Mock server.clientSupportsNotification → true
    // Mock toolset registration
    // Verify server.notification called with tools/list_changed
  });

  it('returns error on static client', async () => {
    // Mock server.clientSupportsNotification → false
    // Verify isError and --toolsets guidance
  });

  it('returns info if toolset already loaded', async () => {
    // Mock ts.loaded = true
    // Verify no re-registration, informational message
  });
});

describe('get_confirmation_token', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ token: 'ctk_test123' }))
    );
  });

  it('calls REST API with action and params_summary', async () => {
    const result = await handler({
      action: 'zorivest_emergency_stop',
      params_summary: 'Lock all tools due to suspected loop',
    });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/confirmation-tokens'),
      expect.objectContaining({ method: 'POST' })
    );
    const data = JSON.parse(result.content[0].text);
    expect(data.token).toBe('ctk_test123');
    expect(data.expires_in_seconds).toBe(60);
  });
});
```

---

## Toolset Registry

> [!NOTE]
> The `ToolsetRegistry` is a singleton in-memory registry initialized at server startup. It reads the `--toolsets` CLI flag (or `ZORIVEST_TOOLSET_CONFIG` env var pointing to `toolset-config.json`) and determines which toolsets to load eagerly vs defer. See [§5.11](05-mcp-server.md) for the authoritative toolset definitions.

```typescript
// mcp-server/src/toolsets/registry.ts

interface ToolsetDefinition {
  name: string;
  description: string;
  tools: ToolSpec[];
  register: (server: McpServer) => void;
  loaded: boolean;
  alwaysLoaded: boolean;
}

class ToolsetRegistry {
  private toolsets = new Map<string, ToolsetDefinition>();

  register(def: ToolsetDefinition): void {
    this.toolsets.set(def.name, def);
  }

  getAll(): ToolsetDefinition[] {
    return Array.from(this.toolsets.values());
  }

  get(name: string): ToolsetDefinition | undefined {
    return this.toolsets.get(name);
  }

  markLoaded(name: string): void {
    const ts = this.toolsets.get(name);
    if (ts) ts.loaded = true;
  }
}

export const toolsetRegistry = new ToolsetRegistry();
```

---

## PTC Routing (Anthropic Clients)

> Programmatic Tool Calling enables batch analytics processing. See [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) for per-tool details and the full PTC appendix.

### Client Detection Trigger

During `initialize`, the adaptive client detection ([§5.10](05-mcp-server.md)) identifies Anthropic-class clients via:
- User-agent containing `claude` or `anthropic`
- `capabilities.tools.listChanged` support
- Environment override: `ZORIVEST_CLIENT_MODE=anthropic`

When detected, the server adds `allowed_callers: ["code_execution"]` to all `trade-analytics` category tools that have `readOnlyHint: true`. This enables the agent to batch-call analytics endpoints in a code execution sandbox. Tools with `readOnlyHint: false` (e.g., `enrich_trade_excursion`) are excluded.

### Affected Tools

All 11 read-only analytics tools (`readOnlyHint: true`) in [05c](05c-mcp-trade-analytics.md) § Analytics Tools receive `allowed_callers`. `enrich_trade_excursion` (`readOnlyHint: false`), trade CRUD, screenshot, and report tools are excluded (write operations or binary I/O).

### Expected Impact

| Metric | Without PTC | With PTC |
|--------|-------------|----------|
| Tool calls for multi-metric analysis | 4-8 sequential | 1 (batched) |
| Token overhead | ~4K per call × N | ~2K (single batched result) |
| Measured reduction (Anthropic) | — | **37%** |
