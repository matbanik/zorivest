# Phase 5g: MCP Tools — Scheduling

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `scheduling`
>
> Originally specified in [Phase 9 §9.11](09-scheduling.md).

## Tools

### `create_policy` [Specified]

Create a new pipeline policy from a JSON document with full validation.

```typescript
// mcp-server/src/tools/scheduling-tools.ts

import { z } from 'zod';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

const API_BASE = process.env.ZORIVEST_API_URL || 'http://localhost:8765/api/v1';

export function registerSchedulingTools(server: McpServer) {

  server.tool(
    'create_policy',
    'Create a new pipeline policy from a JSON document. Validates structure, step types, ref integrity, and cron expression.',
    {
      policy_json: z.object({
        name: z.string(),
        schema_version: z.number().default(1),
        trigger: z.object({
          cron_expression: z.string(),
          timezone: z.string().default('UTC'),
          enabled: z.boolean().default(true),
          coalesce: z.boolean().default(true),
          max_instances: z.number().default(1),
          misfire_grace_time: z.number().default(3600),
        }),
        steps: z.array(z.object({
          id: z.string(),
          type: z.string(),
          params: z.record(z.unknown()),
          on_error: z.enum(['fail_pipeline', 'log_and_continue', 'retry_then_fail']).default('fail_pipeline'),
          retry: z.object({
            max_attempts: z.number().default(1),
            backoff_seconds: z.number().default(2),
          }).optional(),
          skip_if: z.object({
            field: z.string(),
            operator: z.string(),
            value: z.unknown(),
          }).optional(),
        })),
      }).describe('Full PolicyDocument JSON object'),
    },
    async ({ policy_json }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_json }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { content: [{ type: 'text' as const, text: `Validation failed:\n${JSON.stringify(data, null, 2)}` }], isError: true };
      }
      return { content: [{ type: 'text' as const, text: `Policy created:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: scheduling
- `alwaysLoaded`: false

**Input:** `policy_json` (full PolicyDocument object)
**Output:** Text payload with created policy or validation errors
**Side Effects:** Writes scheduling policy (requires approval before execution)
**Error Posture:** Returns validation errors with field-level detail

---

### `list_policies` [Specified]

List all pipeline policies with schedule/approval state.

```typescript
  server.tool(
    'list_policies',
    'List all pipeline policies with their schedule status, approval state, and next run time.',
    {
      enabled_only: z.boolean().default(false).describe('Filter to enabled policies only'),
    },
    async ({ enabled_only }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies?enabled_only=${enabled_only}`);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: scheduling
- `alwaysLoaded`: false

**Input:** `enabled_only` (bool, default false)
**Output:** JSON text list of policies
**Side Effects:** None (read-only)

---

### `run_pipeline` [Specified]

Trigger a manual policy run.

```typescript
  server.tool(
    'run_pipeline',
    'Trigger a manual pipeline run for an approved policy. Returns run_id and initial status.',
    {
      policy_id: z.string().describe('Policy UUID to execute'),
      dry_run: z.boolean().default(false).describe('If true, skip steps with side effects'),
    },
    async ({ policy_id, dry_run }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { content: [{ type: 'text' as const, text: `Run failed: ${JSON.stringify(data)}` }], isError: true };
      }
      return { content: [{ type: 'text' as const, text: `Pipeline triggered:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: scheduling
- `alwaysLoaded`: false

**Input:** `policy_id`, `dry_run` (default false)
**Output:** Text payload with `run_id`/initial status or failure detail
**Side Effects:** Executes pipeline side effects unless `dry_run`
**Error Posture:** Returns error if policy not found, not approved, or already running

---

### `preview_report` [Specified]

Dry-run a pipeline and inspect rendered preview.

```typescript
  server.tool(
    'preview_report',
    'Dry-run a pipeline and return the rendered HTML preview without sending emails or saving files.',
    {
      policy_id: z.string().describe('Policy UUID to preview'),
    },
    async ({ policy_id }) => {
      const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run: true }),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: `Preview result:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: scheduling
- `alwaysLoaded`: false

**Input:** `policy_id`
**Output:** Text payload with preview result from dry-run
**Side Effects:** None — dry-run skips email/file side effects

---

### `update_policy_schedule` [Specified]

Change cron/timezone/enabled state for a policy.

```typescript
  server.tool(
    'update_policy_schedule',
    'Update a policy\'s schedule (cron expression, enable/disable, timezone).',
    {
      policy_id: z.string().describe('Policy UUID to update'),
      cron_expression: z.string().optional().describe('New 5-field cron expression'),
      enabled: z.boolean().optional().describe('Enable or disable the schedule'),
      timezone: z.string().optional().describe('IANA timezone (e.g. "America/New_York")'),
    },
    async ({ policy_id, cron_expression, enabled, timezone }) => {
      const getRes = await fetch(`${API_BASE}/scheduling/policies/${policy_id}`);
      if (!getRes.ok) {
        return { content: [{ type: 'text' as const, text: 'Policy not found' }], isError: true };
      }
      const current = await getRes.json();
      const policy = JSON.parse(current.policy_json || '{}');

      if (cron_expression) policy.trigger.cron_expression = cron_expression;
      if (enabled !== undefined) policy.trigger.enabled = enabled;
      if (timezone) policy.trigger.timezone = timezone;

      const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_json: policy }),
      });
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: `Updated:\n${JSON.stringify(data, null, 2)}` }] };
    }
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: scheduling
- `alwaysLoaded`: false

**Input:** `policy_id`, optional `cron_expression`, `enabled`, `timezone`
**Output:** Text payload with updated policy info
**Side Effects:** Writes policy schedule config

---

### `get_pipeline_history` [Specified]

Inspect recent policy execution history.

```typescript
  server.tool(
    'get_pipeline_history',
    'Get recent pipeline execution history with step-level detail.',
    {
      policy_id: z.string().optional().describe('Filter to a specific policy (optional)'),
      limit: z.number().default(10).describe('Number of recent runs to return'),
    },
    async ({ policy_id, limit }) => {
      const url = policy_id
        ? `${API_BASE}/scheduling/policies/${policy_id}/runs?limit=${limit}`
        : `${API_BASE}/scheduling/runs?limit=${limit}`;
      const res = await fetch(url);
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
    }
  );
}
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: scheduling
- `alwaysLoaded`: false

**Input:** optional `policy_id`, `limit` (default 10)
**Output:** JSON text run history with step-level metadata
**Side Effects:** None (read-only)

---

> [!NOTE]
> **Constrained-Client CRUD Consolidation.** For Cursor-class clients (≤40-tool limit), the symmetrical CRUD tools `create_policy`, `list_policies`, and `update_policy_schedule` can be served as a single `manage_policy(action: 'create'|'list'|'update_schedule', ...)` composite tool. The discrete tools above remain canonical — annotation-aware clients use them directly. Operational tools (`run_pipeline`, `preview_report`, `get_pipeline_history`) are **not** CRUD merge candidates — they have distinct semantics and side-effect profiles. See [05j-mcp-discovery.md](05j-mcp-discovery.md) for adaptive client detection.

---

## MCP Resources

```typescript
export function registerSchedulingResources(server: McpServer) {
  server.resource(
    'pipeline://policies/schema',
    'JSON Schema for valid PolicyDocument objects',
    async () => {
      const res = await fetch(`${API_BASE}/scheduling/policies/schema`);
      const schema = await res.json();
      return { contents: [{ uri: 'pipeline://policies/schema', text: JSON.stringify(schema, null, 2), mimeType: 'application/json' }] };
    }
  );

  server.resource(
    'pipeline://step-types',
    'List of registered pipeline step types with their parameter schemas',
    async () => {
      const res = await fetch(`${API_BASE}/scheduling/step-types`);
      const types = await res.json();
      return { contents: [{ uri: 'pipeline://step-types', text: JSON.stringify(types, null, 2), mimeType: 'application/json' }] };
    }
  );
}
```

> **Note:** Policy approval (`approve_policy`) is GUI-only for security. See [06e-gui-scheduling.md](06e-gui-scheduling.md).
