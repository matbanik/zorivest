# Phase 5b: MCP Tools — Zorivest Diagnostics

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `zorivest-diagnostics`
>
> Service tools originally specified in [Phase 10](10-service-daemon.md) §10.4.

## Tools

### `zorivest_diagnose` [Specified]

Runtime diagnostics. Returns backend health, DB status, guard state, provider availability, and performance metrics.

```typescript
// mcp-server/src/tools/diagnostics-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { authState } from '../auth/bootstrap.js';
import { metricsCollector } from '../middleware/metrics.js';

function getAuthHeadersSafe(): Record<string, string> {
  return authState.sessionToken
    ? { 'Authorization': `Bearer ${authState.sessionToken}` }
    : {};
}

const API_BASE = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

interface ProviderStatus {
  name: string;
  is_enabled: boolean;
  has_key: boolean;
}

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
          if (!res.ok) return null;
          return res.json();
        } catch { return null; }
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
        database: {
          unlocked: health?.database_unlocked ?? 'unknown',
        },
        guard: guard
          ? { enabled: guard.is_enabled, locked: guard.is_locked, call_count: guard.call_count }
          : { status: 'unavailable' },
        providers: providers
          ? (providers as ProviderStatus[]).map((p) => ({
              name: p.name, is_enabled: p.is_enabled, has_key: p.has_key,
            }))
          : [],
        mcp_server: {
          uptime_minutes: metricsCollector.getUptimeMinutes(),
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
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** `verbose` (bool, default false)
**Output:** Structured JSON text report: backend, version, database, guard, providers, mcp_server, metrics
**Side Effects:** None (read-only)
**Error Posture:** Never throws — uses safe fetch with null fallback. Must never leak API keys.

---

### `zorivest_launch_gui` [Specified]

Launch the desktop GUI from an agent session, or guide installation if not found.

> Full implementation in [05-mcp-server.md](05-mcp-server.md) Step 5.10 (discovery + launch logic).

```typescript
  server.tool(
    'zorivest_launch_gui',
    'Launch the Zorivest desktop GUI. If not installed, opens the download page and returns setup instructions the agent can relay to the user.',
    {
      wait_for_close: z.boolean().default(false).describe(
        'If true, blocks until GUI process exits'
      ),
    },
    async ({ wait_for_close }) => {
      // Discovery: check installed binary, dev repo, PATH, env var
      // Launch: platform-specific detached process
      // Not-installed: open releases page + return setup instructions
      // See 05-mcp-server.md Step 5.10 for full handler
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: core
- `alwaysLoaded`: true

**Input:** `wait_for_close` (bool, default false)
**Output:** JSON text with `gui_found`, `method`, `message`, optional `setup_instructions`
**Side Effects:** May launch app or open releases page in browser
**Error Posture:** Never crashes — returns setup instructions if GUI not found

---

### `zorivest_service_status` [Specified]

Check backend service process-level runtime health. Originally specified in [Phase 10 §10.4](10-service-daemon.md).

```typescript
// mcp-server/src/tools/service.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const API = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

export function registerServiceTools(server: McpServer): void {

  server.tool(
    'zorivest_service_status',
    'Get the current status of the Zorivest backend service, including PID, uptime, memory, CPU, and scheduler state.',
    {},
    async () => {
      try {
        const [health, status] = await Promise.all([
          fetch(`${API}/health`).then(r => r.json()),
          fetch(`${API}/service/status`, {
            headers: { 'Authorization': `Bearer ${getToken()}` },
          }).then(r => r.json()),
        ]);

        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              backend: 'running',
              pid: status.pid,
              uptime_seconds: status.uptime_seconds,
              memory_mb: status.memory_mb,
              cpu_percent: status.cpu_percent,
              version: health.version,
              scheduler: health.scheduler,
              database: health.database,
            }, null, 2),
          }],
        };
      } catch (err) {
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              backend: 'unreachable',
              error: (err as Error).message,
              hint: 'The backend service may not be running. Check OS service status or start it from the Zorivest GUI Settings > Service Manager.',
            }, null, 2),
          }],
          isError: true,
        };
      }
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** none
**Side Effects:** None (read-only, combines `/health` + `/service/status`)
**Error Posture:** Returns `isError: true` with hint if backend unreachable

---

### `zorivest_service_restart` [Specified]

Request graceful backend restart via service wrapper. Originally specified in [Phase 10 §10.4](10-service-daemon.md).

```typescript
  server.tool(
    'zorivest_service_restart',
    'Restart the Zorivest backend service. Triggers a graceful shutdown; the OS service wrapper handles the restart. Returns when the service is back online.',
    {
      confirm: z.literal('RESTART').describe('Confirmation token — must be the literal string "RESTART"'),
    },
    // MCP annotation: { destructiveHint: true, idempotentHint: false }
    async () => {
      try {
        await fetch(`${API}/service/graceful-shutdown`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` },
        });

        // Poll for restart (max 30 seconds)
        const start = Date.now();
        while (Date.now() - start < 30_000) {
          await new Promise(r => setTimeout(r, 2000));
          try {
            const health = await fetch(`${API}/health`).then(r => r.json());
            if (health.status === 'ok') {
              return {
                content: [{
                  type: 'text' as const,
                  text: JSON.stringify({
                    status: 'restarted',
                    version: health.version,
                    uptime_seconds: health.uptime_seconds,
                  }, null, 2),
                }],
              };
            }
          } catch { /* still restarting */ }
        }

        return {
          content: [{
            type: 'text' as const,
            text: 'Service restart timed out after 30 seconds. Check the Zorivest GUI or OS service manager.',
          }],
          isError: true,
        };
      } catch (err) {
        return {
          content: [{
            type: 'text' as const,
            text: `Restart failed: ${(err as Error).message}`,
          }],
          isError: true,
        };
      }
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: true
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** none
**Side Effects:** Operational — triggers service restart
**Error Posture:** Returns `isError: true` on timeout (30s) or connection failure

---

### `zorivest_service_logs` [Specified]

Locate service log directory and files for troubleshooting. Originally specified in [Phase 10 §10.4](10-service-daemon.md).

```typescript
  server.tool(
    'zorivest_service_logs',
    'Get the path to the Zorivest log directory. Returns the absolute path where JSONL log files are stored, per the Phase 1A logging infrastructure.',
    {},
    async () => {
      let logDir: string;
      if (process.platform === 'win32') {
        logDir = `${process.env.LOCALAPPDATA || ''}\\zorivest\\logs`;
      } else if (process.platform === 'darwin') {
        logDir = `${process.env.HOME}/Library/Application Support/zorivest/logs`;
      } else {
        const xdg = process.env.XDG_DATA_HOME || `${process.env.HOME}/.local/share`;
        logDir = `${xdg}/zorivest/logs`;
      }

      const fs = await import('fs/promises');
      let files: string[] = [];
      try {
        files = (await fs.readdir(logDir))
          .filter(f => f.endsWith('.jsonl'))
          .sort();
      } catch { /* directory may not exist yet */ }

      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({
            log_directory: logDir,
            log_files: files,
            hint: 'Log files are in JSONL format (one JSON object per line). Use jq or grep to filter. Feature log files: trades.jsonl, marketdata.jsonl, scheduler.jsonl, etc.',
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
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:** none
**Side Effects:** Reads filesystem metadata only
**Error Posture:** Returns empty file list if log directory doesn't exist yet
