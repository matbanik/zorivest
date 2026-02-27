# Phase 5a: MCP Tools — Zorivest Settings

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `zorivest-settings`

## Tools

### `get_settings` [Specified]

Read all user settings or a specific setting by key.

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
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** optional `key` (string)
**Output:** JSON text key-value payload (string-valued settings boundary)
**Side Effects:** None (read-only)
**Error Posture:** Returns empty/404 if key not found

---

### `update_settings` [Specified]

Update one or more settings keys.

```typescript
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

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** `settings` map (string → string)
**Output:** JSON text update result
**Side Effects:** Writes settings
**Error Posture:** Returns validation error on invalid keys

> **Convention**: Setting values at the MCP boundary are **strings**. Consumers parse to their native types (e.g., `"true"` → `boolean`, `"280"` → `number`). The `value_type` column in `SettingModel` is metadata for future typed deserialization but is not enforced at the REST layer.

---

> [!NOTE]
> **Constrained-Client CRUD Consolidation.** For Cursor-class clients (≤40-tool limit), `get_settings` and `update_settings` can be served as a single `manage_settings(action: 'get'|'update', ...)` composite tool. The discrete tools above remain canonical — annotation-aware clients (Claude Code, Roo Code) use them directly. Emergency tools (`zorivest_emergency_stop`, `zorivest_emergency_unlock`) are explicitly **not** merge candidates due to their distinct safety posture and always-callable requirement. See [05j-mcp-discovery.md](05j-mcp-discovery.md) for the adaptive client detection that selects the appropriate tool surface.

---

### `zorivest_emergency_stop` [Specified]

Immediately lock all guarded MCP tool access.

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
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: true
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** `reason` (string, default `"agent_self_lock"`)
**Output:** Text confirmation
**Side Effects:** Locks all guarded MCP tools
**Error Posture:** Always callable — not guard-blocked

---

### `zorivest_emergency_unlock` [Specified]

Re-enable MCP tools after emergency lock.

```typescript
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

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** `confirm` (literal `"UNLOCK"`)
**Output:** Text confirmation of unlocked/failed state
**Side Effects:** Unlocks guard
**Error Posture:** Always callable — requires explicit token

---

### `get_log_settings` [Specified]

Read logging configuration for runtime log controls.

> [!NOTE]
> Depends on [Phase 1A logging architecture](01a-logging.md). Input schema and handler may be adjusted during Phase 1A implementation.

```typescript
  // DRAFT — Not yet registered in build plan
  server.tool(
    'get_log_settings',
    'Read logging.* settings for per-feature runtime log level controls. Returns current log levels for each feature module.',
    {
      prefix: z.string().optional().describe('Filter to settings starting with this prefix, e.g. "logging.trades"'),
    },
    async ({ prefix }) => {
      const filterKey = prefix || 'logging.';
      const res = await fetch(`${API_BASE}/settings`);
      const allSettings = await res.json();
      // Filter to logging.* keys only
      const logSettings = Object.fromEntries(
        Object.entries(allSettings).filter(([k]) => k.startsWith(filterKey))
      );
      return { content: [{ type: 'text' as const, text: JSON.stringify(logSettings) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** optional `prefix` (string, default `"logging."`)
**Output:** JSON key-value map of matching logging settings
**Side Effects:** None (read-only, wraps `GET /settings` with filter)
**Error Posture:** Returns empty map if no matching keys
**Dependencies:** [Phase 1A logging architecture](01a-logging.md), [Phase 6f settings GUI](06f-gui-settings.md)

---

### `update_log_level` [Specified]

Update per-feature runtime log levels.

> [!NOTE]
> Depends on [Phase 1A logging architecture](01a-logging.md). Valid feature modules and level values may be adjusted during Phase 1A implementation.

```typescript
  // DRAFT — Not yet registered in build plan
  server.tool(
    'update_log_level',
    'Update runtime log level for a specific feature module. Valid levels: DEBUG, INFO, WARNING, ERROR.',
    {
      feature: z.string().describe('Feature module name, e.g. "trades", "marketdata", "scheduler"'),
      level: z.enum(['DEBUG', 'INFO', 'WARNING', 'ERROR']).describe('New log level'),
    },
    async ({ feature, level }) => {
      const key = `logging.${feature}.level`;
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: level }),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify({ updated: key, level, result: data }) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** `feature` (string), `level` (enum: DEBUG/INFO/WARNING/ERROR)
**Output:** JSON confirmation with updated key and level
**Side Effects:** Writes `logging.<feature>.level` setting
**Error Posture:** Returns error if feature name doesn't match a valid module
**Dependencies:** [Phase 1A logging architecture](01a-logging.md)
