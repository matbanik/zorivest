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

const API_BASE = process.env.ZORIVEST_API_URL || 'http://localhost:17787/api/v1';

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

### Existing Resources (MEU-89)

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

### New Resources (MEU-PH9) [Planned]

> Source: [retail-trader-policy-use-cases.md](../../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md) line 1691

| Resource URI | Description | Owner MEU | Spec Ref |
|-------------|-------------|-----------|----------|
| `pipeline://policies/schema` | JSON Schema for PolicyDocument (**existing**) | MEU-89 ✅ | [05g §Resources](05g-mcp-scheduling.md) |
| `pipeline://step-types` | Registered step type schemas (**existing**) | MEU-89 ✅ | [05g §Resources](05g-mcp-scheduling.md) |
| `pipeline://templates` | Available DB templates with names, required variables, descriptions | MEU-PH9 | [09e §9E.2](09e-template-database.md) |
| `pipeline://db-schema` | Queryable table/column schema for `query` step SQL authoring (DENY_TABLES excluded) | MEU-PH9 | [09c §9C.2](09c-pipeline-security-hardening.md) |
| `pipeline://emulator/mock-data` | Sample mock data sets for each `data_type` (used by SIMULATE phase) | MEU-PH9 | [09f §9F.1](09f-policy-emulator.md) |
| `pipeline://providers` | Provider names, supported `data_types[]`, `auth_method`, and `docs_url` for web search | MEU-PH9 | [09d §9D.1](09d-pipeline-step-extensions.md) |

```typescript
// MEU-PH9: New resources added to registerSchedulingResources()
export function registerPipelineSecurityResources(server: McpServer) {
  server.resource(
    'pipeline://templates',
    'List of available email templates with names and required variables',
    async () => {
      const res = await fetch(`${API_BASE}/scheduling/templates`);
      const templates = await res.json();
      return { contents: [{ uri: 'pipeline://templates', text: JSON.stringify(templates, null, 2), mimeType: 'application/json' }] };
    }
  );

  server.resource(
    'pipeline://db-schema',
    'Database table and column schemas for query step SQL authoring (sensitive tables excluded)',
    async () => {
      const res = await fetch(`${API_BASE}/scheduling/db-schema`);
      const schema = await res.json();
      return { contents: [{ uri: 'pipeline://db-schema', text: JSON.stringify(schema, null, 2), mimeType: 'application/json' }] };
    }
  );
  // Backend: GET /scheduling/db-schema filters SqlSandbox.DENY_TABLES server-side.
  // Route owner: scheduling API router (MEU-PH9). Security contract: [09c §9C.2e](09c-pipeline-security-hardening.md).

  server.resource(
    'pipeline://emulator/mock-data',
    'Sample mock data sets for each data_type (used by emulator SIMULATE phase)',
    async () => {
      const res = await fetch(`${API_BASE}/scheduling/emulator/mock-data`);
      const data = await res.json();
      return { contents: [{ uri: 'pipeline://emulator/mock-data', text: JSON.stringify(data, null, 2), mimeType: 'application/json' }] };
    }
  );

  server.resource(
    'pipeline://providers',
    'Provider names, supported data types, auth methods, and docs_url for capability discovery',
    async () => {
      const res = await fetch(`${API_BASE}/market-data/providers`);
      const providers = await res.json();
      return { contents: [{ uri: 'pipeline://providers', text: JSON.stringify(providers, null, 2), mimeType: 'application/json' }] };
    }
  );
}
```

> **Note:** Policy approval (`approve_policy`) is GUI-only for security. See [06e-gui-scheduling.md](06e-gui-scheduling.md).

---

## Pipeline Security Hardening Tools (MEU-PH9)

> Source: [09c](09c-pipeline-security-hardening.md), [09d](09d-pipeline-step-extensions.md), [09e](09e-template-database.md), [09f](09f-policy-emulator.md)
> Prerequisite: MEU-PH2 (SQL sandbox), MEU-PH6 (template database), MEU-PH8 (emulator)
> Status: ⬜ Planned

### Boundary Input Contract (Mandatory per AGENTS.md §195)

| Write Surface | Schema Owner | Extra-Field Policy | Error Mapping |
|--------------|-------------|-------------------|---------------|
| `create_email_template` MCP tool input | Zod schema → `EmailTemplateCreateInput` | `.strict()` — unknown fields rejected | Invalid input → MCP error with `INVALID_PARAMS` code |
| `update_email_template` MCP tool input | Zod schema → `EmailTemplateUpdateInput` | `.strict()` — unknown fields rejected | Invalid input → MCP error with `INVALID_PARAMS` code |
| `emulate_policy` MCP tool input | Zod schema → `PolicyJsonInput` | `.strict()` on wrapper, policy JSON validated by Python `PolicyDocument` | Invalid policy → structured `EmulatorError` (not raw 500) |
| `validate_sql` MCP tool input | Zod schema → `SqlValidateInput` | `.strict()` | Invalid input → MCP error with `INVALID_PARAMS` code |

**Field constraints (MCP-side Zod schemas):**

- `create_email_template`: `name` z.string().min(1).max(128).regex(/^[a-z0-9][a-z0-9_-]*$/), `body_html` z.string().min(1).max(65536), `body_format` z.enum(["html", "markdown"]).optional()
- `update_email_template`: `name` z.string().min(1).max(128) (path key), all other fields optional with same constraints as create
- `emulate_policy`: `policy_json` z.record(z.unknown()), `phases` z.array(z.enum(["PARSE","VALIDATE","SIMULATE","RENDER"])).optional()
- `validate_sql`: `sql` z.string().min(1).max(10000)

**Create/Update parity:** `body_html` and `subject_template` enforce the same `HardenedSandbox` compile check on both create and update paths (see [09e §9E.0](09e-template-database.md) for Python-side contract).

### `emulate_policy` [Planned]

Dry-run a policy JSON through the 4-phase emulator (PARSE → VALIDATE → SIMULATE → RENDER). Returns structured `EmulatorResult` with output containment (4 KiB MCP cap, SHA-256 hashed RENDER output).

- `readOnlyHint`: true (dry-run, no side effects)
- `destructiveHint`: false
- `toolset`: scheduling

**Input:** `policy_json` (full PolicyDocument object), optional `phases` (list of phases to run)
**Output:** `EmulatorResult` (valid/errors/warnings/template_preview_hash)

---

### `list_step_types` [Planned]

List all registered pipeline step types with their parameter schemas. Includes new types: `query`, `compose`.

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** None
**Output:** Array of step type objects with `type_name`, `side_effects`, `params_schema`

---

### `list_db_tables` [Planned]

List available DB tables with column schemas. Agent uses this to write SQL for `query` steps. Excludes all tables in `SqlSandbox.DENY_TABLES` (same deny contract used by `get_db_row_samples` and `validate_sql`).

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** None
**Output:** Array of table objects with `name`, `columns[]` (name, type, nullable)
**Backend:** Fetches `GET /scheduling/db-schema` (same endpoint as `pipeline://db-schema`). Security contract: [09c §9C.2e](09c-pipeline-security-hardening.md).

---

### `get_db_row_samples` [Planned]

Return sample rows from a table (via `SqlSandbox`, `DENY_TABLES` enforced). Agent uses this to build `sample_data_json` for templates.

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** `table_name`, optional `limit` (default 5, max 20)
**Output:** Array of row dicts
**Backend:** Validates `table_name not in SqlSandbox.DENY_TABLES` before executing `SqlSandbox.execute()`. Security contract: [09c §9C.2e](09c-pipeline-security-hardening.md).

---

### `validate_sql` [Planned]

Pre-flight SQL validation against the AST **allowlist** and `set_authorizer` rules. Checks without executing.

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** `sql` (SQL query string)
**Output:** `{valid: boolean, errors: string[]}`

---

### `list_provider_capabilities` [Planned]

List providers with `docs_url` for agent web search. Agent discovers API capabilities via documentation links.

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** None
**Output:** Array of provider objects with `name`, `data_types[]`, `auth_method`, `docs_url`

---

### `create_email_template` [Planned]

Create a new Jinja2 email template in the DB. Template source is validated against `HardenedSandbox` rules.

- `readOnlyHint`: false
- `destructiveHint`: false
- `toolset`: scheduling

**Input:** `name`, `body_html`, optional `subject_template`, `description`, `required_variables`, `sample_data_json`, `body_format`
**Output:** Created template object

---

### `get_email_template` [Planned]

Retrieve a template by name with source and metadata.

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** `name` (template name)
**Output:** Template object with all fields

---

### `list_email_templates` [Planned]

List all templates with names, descriptions, and required variables.

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** None
**Output:** Array of template summary objects

---

### `update_email_template` [Planned]

Update template source, variables, or sample data. Cannot modify default templates' `is_default` flag.

- `readOnlyHint`: false
- `destructiveHint`: false
- `toolset`: scheduling

**Input:** `name`, optional `body_html`, `subject_template`, `description`, `required_variables`, `sample_data_json`
**Output:** Updated template object

---

### `preview_email_template` [Planned]

Render a template with sample or provided data via `HardenedSandbox`. Returns HTML preview.

- `readOnlyHint`: true
- `toolset`: scheduling

**Input:** `name` (template name), optional `data` (override sample_data_json)
**Output:** Rendered HTML string (subject to 256 KiB output cap)
