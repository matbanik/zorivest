# Phase 5i: MCP Tools — Behavioral

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `behavioral`

## Tools

### `track_mistake` [Specified]

Tag a trade with a mistake category and estimated cost for behavior analytics.

```typescript
  server.tool(
    'track_mistake',
    'Tag a trade with a mistake category (EARLY_EXIT, REVENGE_TRADE, etc.) and estimated cost',
    {
      trade_exec_id: z.string(),
      category: z.string(),
      estimated_cost: z.number().optional(),
      notes: z.string().optional(),
    },
    async (body) => fetchApi('/mistakes', { method: 'POST', body })
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: behavioral
- `alwaysLoaded`: false

**Input:** `trade_exec_id`, `category` (string), optional `estimated_cost` (number), optional `notes`
**Output:** JSON text created/updated mistake entry
**Side Effects:** Writes behavioral data
**Error Posture:** Returns error if trade_exec_id not found

---

### `get_mistake_summary` [Specified]

Aggregate mistake patterns over a period.

```typescript
  server.tool(
    'get_mistake_summary',
    'Mistakes by category, total cost, and trend analysis',
    {
      account_id: z.string().optional(),
      period: z.string().default('ytd'),
    },
    async (args) => fetchApi('/mistakes/summary', { params: args })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: behavioral
- `alwaysLoaded`: false

**Input:** optional `account_id`, `period` (default `"ytd"`)
**Output:** JSON text category totals/trend summary
**Side Effects:** None (read-only)
**Error Posture:** Returns empty summary if no mistakes recorded

---

### `link_trade_journal` [Specified]

Create bidirectional link between a trade execution and a journal entry.

> Also categorized as `trade-analytics` — primary spec lives here.

```typescript
  server.tool(
    'link_trade_journal',
    'Bidirectional link between trade execution and journal entry',
    {
      trade_exec_id: z.string(),
      journal_entry_id: z.string(),
    },
    async ({ trade_exec_id, journal_entry_id }) =>
      fetchApi(`/trades/${trade_exec_id}/journal-link`, {
        method: 'POST', body: { journal_entry_id }
      })
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: behavioral
- `alwaysLoaded`: false

**Input:** `trade_exec_id`, `journal_entry_id`
**Output:** JSON text link confirmation
**Side Effects:** Writes link relation
**Error Posture:** Returns error if either ID not found
