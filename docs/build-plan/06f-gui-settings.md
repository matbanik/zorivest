# Phase 6f: GUI — Settings Pages

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 4](04-rest-api.md), [Phase 2A](02a-backup-restore.md) | Parent: [Phase 6 GUI](06-gui.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Consolidate all settings and configuration pages: Market Data Providers (migrated from original `06-gui.md`), Email Provider Configuration, Display Mode Preferences, and Tax Profile settings. All pages follow the same list+detail or form-based layout patterns.

---

## Market Data Settings Page

> **Source**: Adapted from [`_market_tools_api-architecture.md`](../../_inspiration/_market_tools_api-architecture.md) GUI specification. Uses a list+detail layout (modern React pattern) instead of nested provider tabs.

The Market Data Settings page lets users configure API keys and monitor connection status for all 9 market data providers. It consumes the REST endpoints defined in [Phase 8 §8.4](08-market-data.md).

### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings > Market Data Providers                  [Test All Connections]  │
├───────────────────────┬─────────────────────────────────────────────────────┤
│  PROVIDER LIST        │  PROVIDER DETAIL                                  │
│  ┌─────────────────┐  │                                                   │
│  │ ✅ Alpha Vantage │◄─│─ selected ──────────────────────────────────────┐ │
│  │ ❌ Polygon.io    │  │  Provider: Alpha Vantage                       │ │
│  │ ⚪ Finnhub       │  │                                                │ │
│  │ ✅ Fin.Mod.Prep  │  │  ┌─ API Configuration 🔒 ──────────────────┐  │ │
│  │ ⚪ EODHD         │  │  │ API Key: [*************************]     │  │ │
│  │ ⚪ Nasdaq Data   │  │  │           [Get API Key ↗]                │  │ │
│  │ ⚪ SEC API       │  │  └──────────────────────────────────────────┘  │ │
│  │ ✅ API Ninjas    │  │                                                │ │
│  │ ⚪ Benzinga      │  │  ┌─ Rate Limiting ──────────────────────────┐  │ │
│  └─────────────────┘  │  │ Requests/min: [  5  ]  Timeout: [  30  ] │  │ │
│                       │  └──────────────────────────────────────────┘  │ │
│  Status legend:       │                                                │ │
│  ✅ = connected       │  ┌─ Connection Status ────────────────────────┐ │ │
│  ❌ = failed          │  │ ✅ Connection successful                   │ │ │
│  ⚪ = not tested      │  │           [Test Connection]                │ │ │
│                       │  └──────────────────────────────────────────┘  │ │
│                       │                                                │ │
│                       │  ┌─ Provider Info ────────────────────────────┐ │ │
│                       │  │ Free Tier: 25 requests/day                │ │ │
│                       │  │ Real-time and historical stock data,      │ │ │
│                       │  │ technical indicators                      │ │ │
│                       │  └──────────────────────────────────────────┘  │ │
│                       │                                                │ │
│                       │      [Save Changes]                            │ │
│                       └────────────────────────────────────────────────┘ │
└───────────────────────┴─────────────────────────────────────────────────────┘
```

### Provider Settings Page (React)

```typescript
// ui/src/components/ProviderSettingsPage.tsx

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

const API = (window as any).__ZORIVEST_API_URL__ ?? 'http://localhost:8765/api/v1';

interface ProviderStatus {
  provider_name: string;
  is_enabled: boolean;
  has_api_key: boolean;
  rate_limit: number;
  timeout: number;
  last_test_status: string | null;  // "success" | "failed" | null
}

export function ProviderSettingsPage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [rateLimit, setRateLimit] = useState(60);
  const [timeout, setTimeout] = useState(30);
  const [isEnabled, setIsEnabled] = useState(true);

  // Fetch all providers
  const { data: providers = [] } = useQuery<ProviderStatus[]>({
    queryKey: ['market-providers'],
    queryFn: () => fetch(`${API}/market-data/providers`).then(r => r.json()),
  });

  // Save provider configuration
  const saveMutation = useMutation({
    mutationFn: async () => {
      return fetch(`${API}/market-data/providers/${encodeURIComponent(selected!)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey || undefined,
          rate_limit: rateLimit,
          timeout,
          is_enabled: isEnabled,
        }),
      }).then(r => r.json());
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['market-providers'] }),
  });

  // Test connection for a single provider
  const testMutation = useMutation({
    mutationFn: async (name: string) => {
      return fetch(`${API}/market-data/providers/${encodeURIComponent(name)}/test`, {
        method: 'POST',
      }).then(r => r.json());
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['market-providers'] }),
  });

  // Test all providers sequentially
  const testAllMutation = useMutation({
    mutationFn: async () => {
      for (const p of providers.filter(p => p.has_api_key)) {
        await fetch(`${API}/market-data/providers/${encodeURIComponent(p.provider_name)}/test`, {
          method: 'POST',
        });
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['market-providers'] }),
  });

  const statusIcon = (p: ProviderStatus) =>
    p.last_test_status === 'success' ? '✅' :
    p.last_test_status === 'failed' ? '❌' : '⚪';

  return (
    <div className="provider-settings">
      <header>
        <h2>Market Data Providers</h2>
        <button onClick={() => testAllMutation.mutate()}>Test All Connections</button>
      </header>
      <div className="split-layout">
        {/* Provider list */}
        <ul className="provider-list">
          {providers.map(p => (
            <li key={p.provider_name}
                className={selected === p.provider_name ? 'selected' : ''}
                onClick={() => { setSelected(p.provider_name); setApiKey(''); }}>
              {statusIcon(p)} {p.provider_name}
            </li>
          ))}
        </ul>
        {/* Provider detail */}
        {selected && (
          <div className="provider-detail">
            <h3>{selected}</h3>
            <label className="toggle">
              <input type="checkbox" checked={isEnabled}
                     onChange={e => setIsEnabled(e.target.checked)} />
              Enabled
            </label>
            <label>API Key:
              <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
                     placeholder="Enter API key" />
            </label>
            <label>Requests/min:
              <input type="number" value={rateLimit} onChange={e => setRateLimit(+e.target.value)} />
            </label>
            <label>Timeout (s):
              <input type="number" value={timeout} onChange={e => setTimeout(+e.target.value)} />
            </label>
            <div className="actions">
              <button onClick={() => saveMutation.mutate()}>Save Changes</button>
              <button onClick={() => testMutation.mutate(selected)}>Test Connection</button>
            </div>
            <div className="connection-status">
              {statusIcon(providers.find(p => p.provider_name === selected)!)}
              {' '}{providers.find(p => p.provider_name === selected)?.last_test_status ?? 'Not tested'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

### Design Decisions (vs. Inspiration Doc)

| Inspiration Feature | Build Plan Decision | Rationale |
|---|---|---|
| Nested 9-tab provider interface | List+detail split layout | Cleaner UX; 9 tabs clutters the tab bar |
| Auto-save on every keystroke | Explicit "Save Changes" button | Standard React pattern; avoids excessive REST calls |
| ScrolledText status log | Toast notifications | Standard desktop app UX |
| Font customization | CSS global styling | Not needed as a per-widget feature |

---

## Email Provider Configuration

> **Source**: [Input Index §16](input-index.md). Allows users to configure SMTP credentials for report email delivery. SMTP passwords are Fernet-encrypted at rest (same pattern as market data API keys).

### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings > Email Provider                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Provider Preset:   [ Gmail ▼ ]                                            │
│  Presets: Gmail | Brevo | SendGrid | Outlook | Yahoo | Custom              │
│                                                                             │
│  ── Connection Details (auto-filled from preset) ──────────────────        │
│                                                                             │
│  SMTP Host:    [ smtp.gmail.com    ]                                       │
│  Port:         [ 587              ]                                        │
│  Security:     (●) STARTTLS  ( ) SSL                                       │
│                                                                             │
│  ── Credentials 🔒 ───────────────────────────────────────────────         │
│                                                                             │
│  Username:     [ user@gmail.com    ]                                       │
│  Password:     [ ****************  ]     (Fernet-encrypted at rest)        │
│  From Email:   [ user@gmail.com    ]                                       │
│                                                                             │
│  ── Actions ──────────────────────────────────────────────────────         │
│                                                                             │
│  [Test Connection]  [Save]                                                 │
│                                                                             │
│  Status: ✅ Test email sent successfully                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Email Config Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `provider_preset` | `select` | dropdown | Auto-fills host/port/security |
| `smtp_host` | `text` | auto-filled or manual | Editable after preset |
| `port` | `number` | auto-filled | 587 (STARTTLS) or 465 (SSL) |
| `security` | `radio` | STARTTLS / SSL | Linked to port selection |
| `username` | `text` | user input | Provider-specific format |
| `password` | `password` | user input | Fernet-encrypted at rest in DB |
| `from_email` | `text` | user input | Sender address |

### Preset Auto-Fill Map

| Preset | Host | Port | Security |
|--------|------|------|----------|
| Gmail | smtp.gmail.com | 587 | STARTTLS |
| Brevo | smtp-relay.brevo.com | 587 | STARTTLS |
| SendGrid | smtp.sendgrid.net | 587 | STARTTLS |
| Outlook | smtp-mail.outlook.com | 587 | STARTTLS |
| Yahoo | smtp.mail.yahoo.com | 465 | SSL |
| Custom | (empty) | 587 | STARTTLS |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/settings/email` | Get current email config |
| `PUT` | `/api/v1/settings/email` | Save email config |
| `POST` | `/api/v1/settings/email/test` | Send test email |

---

## Display Mode Settings

> **Source**: [Domain Model Reference](domain-model-reference.md) `DisplayMode` entity. Three independent toggle flags for privacy and display preferences.

### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings > Display Preferences                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ── Privacy ───────────────────────────────────────────────────────         │
│                                                                             │
│  [■] Hide dollar amounts ($)                                               │
│      Replaces all dollar values with "•••" throughout the app              │
│                                                                             │
│  [□] Hide percentages (%)                                                  │
│      Replaces percentage values with "•••"                                 │
│                                                                             │
│  ── Display Format ────────────────────────────────────────────────        │
│                                                                             │
│  [■] Show values as percentages                                            │
│      When enabled, P&L and position values show as % of account            │
│      instead of absolute dollar amounts                                    │
│                                                                             │
│  ── Preview ───────────────────────────────────────────────────────        │
│                                                                             │
│  With current settings:                                                    │
│  Balance: •••     P&L: +2.3%     Position: 12.5%                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Display Mode Fields

| Setting Key | Type | Default | Description |
|---|---|---|---|
| `display.hide_dollars` | `boolean` | `false` | Mask all dollar amounts |
| `display.hide_percentages` | `boolean` | `false` | Mask all percentage values |
| `display.percent_mode` | `string` | `daily` | Percentage display mode (daily/total) |

Settings persisted via `PUT /api/v1/settings` using the `usePersistedState` hook (see [06a-gui-shell.md](06a-gui-shell.md)).

### Validation Error Display

All settings pages share the same error handling for `PUT /settings` validation failures (see [Phase 2A §2A.2b](02a-backup-restore.md)):

- **422 response** → Parse `detail.errors` (keyed by setting) and render per-field error text below the corresponding input
- **Error text style** — Red (`var(--danger)`) inline message below the field, matching standard form error pattern
- **No client-side validation duplication** — The `SettingsValidator` on the server is the single source of truth. The GUI does not re-implement range checks, enum constraints, or security validation; it only renders errors the server returns
- **All-or-nothing** — If any field fails validation, no fields are saved. The toast notification summarizes: `"Validation failed for {n} field(s)"`

---

## Tax Profile Settings (P3 — Placeholder)

> **Source**: [Domain Model Reference](domain-model-reference.md), [Build Priority Matrix](build-priority-matrix.md) Phase 3A. This page will be built when the tax estimator features reach implementation.

### Layout (Future)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings > Tax Profile                                         (P3)       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Filing Status:    [ Married Filing Jointly ▼ ]                            │
│  Tax Year:         [ 2025 ▼ ]                                              │
│  State:            [ California ▼ ]                                        │
│                                                                             │
│  ── Federal Brackets ──────────────────────────────────────────────        │
│  (auto-populated from filing status + year)                                │
│                                                                             │
│  ── Section Elections ─────────────────────────────────────────────        │
│  [□] Section 475 (Mark-to-Market)                                          │
│  [□] Section 1256 (60/40 Futures)                                          │
│  [□] Forex Worksheet                                                       │
│                                                                             │
│  ── Exclusions ────────────────────────────────────────────────────        │
│  Exclude these accounts from tax calculations:                             │
│  [■] Roth IRA  [■] Traditional IRA  [□] 401(k)                           │
│                                                                             │
│  [Save Profile]                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tax Profile Fields (Future)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `filing_status` | `select` | FilingStatus enum | Single, MFJ, MFS, HoH, QW |
| `tax_year` | `select` | current or prior year | Drives bracket lookup |
| `state` | `select` | US states | For state tax calculation |
| `section_475` | `boolean` | toggle | Mark-to-Market election |
| `section_1256` | `boolean` | toggle | 60/40 futures split |
| `forex_worksheet` | `boolean` | toggle | Forex-specific reporting |
| `excluded_accounts` | `multi-select` | from account list | IRA, 401(k) exclusions |

---

## 6f.4: Logging Settings (Phase 1A)

> [!NOTE]
> **Stub section** — full implementation depends on [Phase 1A Logging Infrastructure](01a-logging.md). Expand when logging is implemented.

### Purpose

Provide a GUI page for adjusting per-feature log levels and rotation settings at runtime, without restarting the application. All values are persisted via `PUT /api/v1/settings` using `logging.*` namespaced keys.

### Settings Fields

| Field | Type | Setting Key | Default | Notes |
|-------|------|-------------|---------|-------|
| Trade logging level | `select` | `logging.trades.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Account logging level | `select` | `logging.accounts.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Market data logging level | `select` | `logging.marketdata.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Tax engine logging level | `select` | `logging.tax.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Scheduler logging level | `select` | `logging.scheduler.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Database logging level | `select` | `logging.db.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Calculator logging level | `select` | `logging.calculator.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Images logging level | `select` | `logging.images.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| API logging level | `select` | `logging.api.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Frontend logging level | `select` | `logging.frontend.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| App logging level | `select` | `logging.app.level` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Max log file size (MB) | `number` | `logging.rotation_mb` | `10` | Global: applies to all feature files |
| Backup file count | `number` | `logging.backup_count` | `5` | Global: rotated files to keep |

### Wireframe

```
┌──────────────────────────────────────────────────────────┐
│  ⚙️ Logging Settings (Phase 1A)                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Per-Feature Log Levels                                  │
│  ─────────────────────                                   │
│  Trades          [ INFO     ▾ ]                          │
│  Accounts        [ INFO     ▾ ]                          │
│  Market Data     [ INFO     ▾ ]                          │
│  Tax Engine      [ INFO     ▾ ]                          │
│  Scheduler       [ INFO     ▾ ]                          │
│  Database        [ INFO     ▾ ]                          │
│  Calculator      [ INFO     ▾ ]                          │
│  Images          [ INFO     ▾ ]                          │
│  API             [ INFO     ▾ ]                          │
│  Frontend        [ INFO     ▾ ]                          │
│  Application     [ INFO     ▾ ]                          │
│  Options: DEBUG | INFO | WARNING | ERROR | CRITICAL      │
│                                                          │
│  Rotation Settings (Global)                              │
│  ──────────────────────────                              │
│  Max file size   [ 10 ] MB                               │
│  Backup count    [ 5  ]                                  │
│                                                          │
│  ℹ️ Changes take effect immediately.                      │
│  Log files: {APP_DATA}/zorivest/logs/                    │
└──────────────────────────────────────────────────────────┘
```

### Implementation Hook

```typescript
// Uses the same usePersistedState pattern as other settings pages
const [tradeLevel, setTradeLevel] = usePersistedState('logging.trades.level', 'INFO');
const [rotationMb, setRotationMb] = usePersistedState('logging.rotation_mb', '10');
```

---

## 6f.5: Backup & Restore Settings Page

> **Source**: [Phase 2A](02a-backup-restore.md) — Encrypted backup/restore architecture

### Layout

Vertical stack within the Settings sidebar:

```
┌─────────────────────────────────────────────────────┐
│  Backup & Restore                                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ Manual Backup ─────────────────────────────────┐ │
│  │  [Create Backup Now]           Last: 2h ago     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Automatic Backups ─────────────────────────────┐ │
│  │  Interval: [300] seconds    [●] Enabled         │ │
│  │  Change threshold: [100]                        │ │
│  │  Compression: [●] Enabled                       │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Restore ───────────────────────────────────────┐ │
│  │  [Select Backup File...]  [Verify]  [Restore]   │ │
│  │  Status: Ready                                  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Backup History ────────────────────────────────┐ │
│  │  Date         │ Size   │ Type   │ Actions       │ │
│  │  2026-02-17   │ 1.2 MB │ Auto   │ [Verify] [↗]  │ │
│  │  2026-02-16   │ 1.1 MB │ Manual │ [Verify] [↗]  │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### REST Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Create manual backup | `POST` | `/api/v1/backups` |
| List backups | `GET` | `/api/v1/backups` |
| Verify backup | `POST` | `/api/v1/backups/verify` |
| Restore from backup | `POST` | `/api/v1/backups/restore` |

### Behavior

- **Create Backup**: triggers `POST /backups`, shows spinner, displays result toast
- **Verify**: non-destructive check (hash verification + DB open test), shows pass/fail
- **Restore**: confirmation dialog (uses `dialog.confirm_restore` setting), progress indicator, auto-reload after success
- **Backup History**: fetched from `GET /backups`, row actions for verify and open-in-explorer

> **Passphrase handling**: Verify and restore use the **session-unlocked passphrase** — no second prompt. If the session has expired, the GUI shows a re-authentication modal before proceeding.

---

## 6f.6: Config Export/Import

> **Source**: [Phase 2A](02a-backup-restore.md) — JSON config export/import (non-sensitive only)

### Layout

Card within Settings sidebar:

```
┌─────────────────────────────────────────────────────┐
│  Config Export / Import                              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Export your application settings as a portable      │
│  JSON file (excludes API keys and passwords).        │
│                                                      │
│  [Export Config]                                      │
│                                                      │
│  ─────────────────────────────────────────────────── │
│                                                      │
│  Import settings from a previously exported file.    │
│                                                      │
│  [Select File...]  [Preview Changes]  [Import]       │
│                                                      │
│  Preview:                                            │
│  ┌───────────────────────────────────────────────┐   │
│  │ display.hide_dollars: false → true            │   │
│  │ logging.rotation_mb: 10 → 20                  │   │
│  │ + backup.auto_interval_seconds: 600 (new)     │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### REST Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Export config | `GET` | `/api/v1/config/export` |
| Preview import | `POST` | `/api/v1/config/import?dry_run=true` |
| Apply import | `POST` | `/api/v1/config/import` |

### Behavior

- **Export**: triggers file download of `zorivest-config-{date}.json`
- **Preview**: shows diff of current vs imported settings (dry-run mode)
- **Import**: confirmation dialog, applies accepted keys only, shows rejected/unknown keys in warning toast

---

## 6f.7: Reset to Default

All settings pages gain a "Reset to Default" capability:

- Each setting row shows its source: **User**, **Default**, or **Hardcoded** (from `GET /api/v1/settings/resolved`)
- User-overridden settings show a small ↻ (reset) icon button
- Clicking reset calls `DELETE /api/v1/settings/{key}` and the value falls back to the next tier
- Bulk "Reset All to Defaults" button at the bottom of each settings category

---

## 6f.8: MCP Guard Settings

> Circuit breaker + panic button for MCP tool access.
> Model: [`McpGuardModel`](02-infrastructure.md) | REST: [§4.6](04-rest-api.md) | MCP middleware: [§5.6](05-mcp-server.md)

### Wireframe

```
┌──────────────────────────────────────────────────────────┐
│  Settings > MCP Guard                                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─ Status ─────────────────────────────────────┐        │
│  │ 🟢 MCP Tools: Active                        │        │
│  │    Last 1 min: 3 calls                       │        │
│  │    Last 1 hr:  47 calls                      │        │
│  └──────────────────────────────────────────────┘        │
│                                                          │
│  ── Thresholds ─────────────────────────────────         │
│  [●] Enable MCP Guard                                    │
│  Calls per minute:  [ 60  ]                              │
│  Calls per hour:    [ 500 ]                              │
│                                                          │
│  [Save]                                                  │
│                                                          │
│  ── Emergency ─────────────────────────────────          │
│  [🔴 Emergency Stop — Lock All MCP Tools]                │
│  ⚠️ This immediately blocks all AI agent access.          │
│     Unlock from this page when ready.                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

When locked, the status section changes to:

```
│  ┌─ Status ─────────────────────────────────────┐        │
│  │ 🔴 MCP Tools: LOCKED                        │        │
│  │    Locked at: 2026-02-17 21:45:00            │        │
│  │    Reason: manual                            │        │
│  │                                              │        │
│  │    [🟢 Unlock MCP Tools]                     │        │
│  └──────────────────────────────────────────────┘        │
```

### React Component

> All `/mcp-guard/*` requests use the shared `apiFetch()` wrapper which injects the session token from `useAuth()` context (same pattern as all other settings pages).

```tsx
// src/renderer/pages/settings/McpGuardSettingsPage.tsx

export function McpGuardSettingsPage() {
  const { data: status } = useQuery({
    queryKey: ['mcp-guard-status'],
    queryFn: () => apiFetch(`${API}/mcp-guard/status`).then(r => r.json()),
    refetchInterval: 5000,  // poll every 5s for live counters
  });

  const lockMutation = useMutation({
    mutationFn: () => apiFetch(`${API}/mcp-guard/lock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'manual' }),
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mcp-guard-status'] }),
  });

  const unlockMutation = useMutation({
    mutationFn: () => apiFetch(`${API}/mcp-guard/unlock`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mcp-guard-status'] }),
  });

  const saveMutation = useMutation({
    mutationFn: (config: McpGuardConfigUpdate) =>
      apiFetch(`${API}/mcp-guard/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mcp-guard-status'] }),
  });

  return (
    <div className="mcp-guard-settings">
      <h2>MCP Guard</h2>

      {/* Status card */}
      <div className={`status-card ${status?.is_locked ? 'locked' : 'active'}`}>
        <span>{status?.is_locked ? '🔴 LOCKED' : '🟢 Active'}</span>
        {status?.is_locked ? (
          <>
            <p>Locked: {status.locked_at} — {status.lock_reason}</p>
            <button className="unlock-btn" onClick={() => unlockMutation.mutate()}>
              🟢 Unlock MCP Tools
            </button>
          </>
        ) : (
          <p>Last 1 min: {status?.recent_calls_1min} | Last 1 hr: {status?.recent_calls_1hr}</p>
        )}
      </div>

      {/* Thresholds */}
      <fieldset>
        <legend>Thresholds</legend>
        <label className="toggle">
          <input type="checkbox" checked={isEnabled} onChange={...} /> Enable MCP Guard
        </label>
        <label>Calls per minute: <input type="number" value={callsPerMin} ... /></label>
        <label>Calls per hour: <input type="number" value={callsPerHr} ... /></label>
        <button onClick={() => saveMutation.mutate({ is_enabled: isEnabled, calls_per_minute_limit: callsPerMin, calls_per_hour_limit: callsPerHr })}>Save</button>
      </fieldset>

      {/* Emergency stop */}
      {!status?.is_locked && (
        <div className="emergency-section">
          <button className="emergency-btn" onClick={() => lockMutation.mutate()}>
            🔴 Emergency Stop — Lock All MCP Tools
          </button>
          <p className="warning">⚠️ This immediately blocks all AI agent access.</p>
        </div>
      )}
    </div>
  );
}
```

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/mcp-guard/status` | Poll guard state + live counters |
| `PUT` | `/api/v1/mcp-guard/config` | Save thresholds and enabled toggle |
| `POST` | `/api/v1/mcp-guard/lock` | Emergency stop |
| `POST` | `/api/v1/mcp-guard/unlock` | Restore MCP access |

---

## Exit Criteria

- Market Data Settings page displays all 9 providers with connection status
- API key save/test/remove cycle works end-to-end via REST
- Email provider preset auto-fills SMTP fields
- Email test connection sends a test email and reports success/failure
- Display mode toggles immediately affect all dollar/percentage displays
- Tax Profile page renders (P3 placeholder — full validation deferred)
- Backup page: create, verify, restore cycle works end-to-end
- Config export produces valid JSON; import with preview applies non-sensitive settings only
- Reset to Default removes user override and falls back correctly
- MCP Guard page displays status, accepts threshold changes, and lock/unlock cycle works

## Outputs

- React components: `ProviderSettingsPage`, `EmailSettingsPage`, `DisplaySettingsPage`, `TaxProfilePage` (P3)
- React components: `BackupSettingsPage`, `ConfigExportImportCard` — see [Phase 2A](02a-backup-restore.md)
- React component: `McpGuardSettingsPage` — circuit breaker + panic button
- Email preset auto-fill configuration map
- Display mode toggle with live preview
- Reset to Default ↻ buttons on all settings rows
- Settings pages consume: `GET/PUT /settings`, `GET /settings/resolved`, `POST/GET /backups`, `GET /config/export`, `POST /config/import`, `DELETE /settings/{key}`, `GET/PUT /mcp-guard/config`, `GET /mcp-guard/status`, `POST /mcp-guard/lock`, `POST /mcp-guard/unlock`
