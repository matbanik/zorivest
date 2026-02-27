# Phase 5f: MCP Tools — Accounts

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Category: `accounts`

## Tools

### `sync_broker` [Specified]

Trigger broker sync/import workflow.

```typescript
  server.tool(
    'sync_broker',
    'Sync account data and import trades from a configured broker',
    { broker_id: z.string().describe('Broker ID, e.g. "ibkr_pro", "alpaca_paper"') },
    async ({ broker_id }) => fetchApi(`/brokers/${broker_id}/sync`, { method: 'POST' })
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: true
- `idempotentHint`: false
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** `broker_id` (string, e.g. `"ibkr_pro"`, `"alpaca_paper"`)
**Output:** JSON text sync summary/status
**Side Effects:** Writes imported trade data

---

### `list_brokers` [Specified]

List configured broker adapters.

```typescript
  server.tool(
    'list_brokers',
    'List configured broker adapters with sync status',
    {},
    async () => fetchApi('/brokers')
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** none
**Output:** JSON text list of broker configs/status
**Side Effects:** None (read-only)

---

### `resolve_identifiers` [Specified]

Batch resolve CUSIP/ISIN/SEDOL/FIGI to tradable identifiers.

```typescript
  server.tool(
    'resolve_identifiers',
    'Batch resolve CUSIP/ISIN/SEDOL to ticker symbols',
    {
      identifiers: z.array(z.object({
        id_type: z.enum(['cusip', 'isin', 'sedol', 'figi']),
        id_value: z.string(),
      })),
    },
    async ({ identifiers }) =>
      fetchApi('/identifiers/resolve', { method: 'POST', body: identifiers })
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** `identifiers` array of `{id_type, id_value}`
**Output:** JSON text resolution list (batch)
**Side Effects:** None (read-only lookup)

---

### `import_bank_statement` [Specified]

Import banking statement files into account ledger.

```typescript
  server.tool(
    'import_bank_statement',
    'Import a bank statement file (CSV, OFX, QIF). Provide file path.',
    {
      file_path: z.string(),
      account_id: z.string(),
      format_hint: z.enum(['auto', 'csv', 'ofx', 'qif']).default('auto'),
    },
    async ({ file_path, account_id, format_hint }) =>
      uploadFile('/banking/import', file_path, { account_id, format_hint })
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** `file_path`, `account_id`, `format_hint` (default `"auto"`)
**Output:** JSON text import summary (rows/duplicates/errors)
**Side Effects:** Multipart upload from local file path; writes ledger data

---

### `import_broker_csv` [Specified]

Import broker CSV with format detection.

```typescript
  server.tool(
    'import_broker_csv',
    'Import broker trade CSV with auto-detection of broker format',
    {
      file_path: z.string(),
      account_id: z.string(),
      broker_hint: z.string().default('auto'),
    },
    async ({ file_path, account_id, broker_hint }) =>
      uploadFile('/import/csv', file_path, { account_id, broker_hint })
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** `file_path`, `account_id`, `broker_hint` (default `"auto"`)
**Output:** JSON text import summary
**Side Effects:** Multipart upload; writes trade data

---

### `import_broker_pdf` [Specified]

Import broker PDF statement.

```typescript
  server.tool(
    'import_broker_pdf',
    'Import broker PDF statement. Extracts tables via pdfplumber.',
    {
      file_path: z.string(),
      account_id: z.string(),
    },
    async ({ file_path, account_id }) =>
      uploadFile('/import/pdf', file_path, { account_id })
  );
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: false
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** `file_path`, `account_id`
**Output:** JSON text extraction/import summary
**Side Effects:** Multipart upload; writes trade data

---

### `list_bank_accounts` [Specified]

List linked bank accounts and balances.

```typescript
  server.tool(
    'list_bank_accounts',
    'List bank accounts with current balance and last updated timestamp',
    {},
    async () => fetchApi('/banking/accounts')
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** none
**Output:** JSON text account list with balance/updated fields
**Side Effects:** None (read-only)

---

### `get_account_review_checklist` [Specified]

Generate a read-only account staleness checklist for balance review.

```typescript
  interface BrokerSummary {
    broker_id: string;
    name: string;
    last_sync: string | null;
  }

  interface BankAccountSummary {
    account_id: string;
    name: string;
    last_updated: string | null;
  }

  // DRAFT — Planned tool
  server.tool(
    'get_account_review_checklist',
    'Generate a read-only account staleness checklist. Returns accounts with stale balances and suggested update actions.',
    {
      scope: z.enum(['all', 'stale_only', 'broker_only', 'bank_only']).default('stale_only')
        .describe('Which accounts to include in the review'),
      stale_threshold_days: z.number().default(7)
        .describe('Consider balances older than this many days as stale'),
    },
    async ({ scope, stale_threshold_days }) => {
      // Fetch all accounts with their last-updated timestamps
      const [brokers, banks] = await Promise.all([
        fetchApi('/brokers'),
        fetchApi('/banking/accounts'),
      ]);

      // Filter based on scope and staleness
      const now = Date.now();
      const threshold = stale_threshold_days * 24 * 60 * 60 * 1000;

      const allAccounts = [
        ...(brokers?.content ? JSON.parse(brokers.content[0].text) as BrokerSummary[] : []).map(
          (b) => ({ type: 'broker' as const, id: b.broker_id, name: b.name, last_sync: b.last_sync })
        ),
        ...(banks?.content ? JSON.parse(banks.content[0].text) as BankAccountSummary[] : []).map(
          (b) => ({ type: 'bank' as const, id: b.account_id, name: b.name, last_updated: b.last_updated })
        ),
      ];

      const review = allAccounts
        .filter(a => {
          if (scope === 'broker_only' && a.type !== 'broker') return false;
          if (scope === 'bank_only' && a.type !== 'bank') return false;
          if (scope === 'stale_only') {
            const lastDate = new Date(a.last_sync || a.last_updated || 0).getTime();
            return (now - lastDate) > threshold;
          }
          return true;
        })
        .map(a => ({
          ...a,
          is_stale: (now - new Date(a.last_sync || a.last_updated || 0).getTime()) > threshold,
          suggested_action: a.type === 'broker' ? `sync_broker ${a.id}` : 'Manual balance update needed',
        }));

      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({
            review_scope: scope,
            stale_threshold_days,
            total_accounts: allAccounts.length,
            accounts_needing_review: review.length,
            accounts: review,
          }, null, 2),
        }],
      };
    }
  );
```

#### Annotations

- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: accounts
- `alwaysLoaded`: false

**Input:** `scope` (enum: all/stale_only/broker_only/bank_only), `stale_threshold_days` (default 7)
**Output:** JSON with account review checklist — each account shows staleness status and suggested next action
**Side Effects:** None (read-only assessment)
**Error Posture:** Returns empty review if no accounts configured

---

## Shared Helper: File Upload

```typescript
  const uploadFile = async (
    endpoint: string,
    filePath: string,
    fields: Record<string, string>,
  ) => {
    const fs = await import('node:fs');
    const path = await import('node:path');
    const fileBuffer = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);
    const formData = new FormData();
    formData.append('file', new Blob([fileBuffer]), fileName);
    for (const [k, v] of Object.entries(fields)) {
      formData.append(k, v);
    }
    return fetchApi(endpoint, { method: 'POST', body: formData, rawBody: true });
  };
```
