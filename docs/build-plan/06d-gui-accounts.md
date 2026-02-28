# Phase 6d: GUI — Account Management

> Part of [Phase 6: GUI](06-gui.md) | Prerequisites: [Phase 4](04-rest-api.md) | Outputs: [Phase 7](07-distribution.md)

---

## Goal

Build the Account Management surface: a list+detail page for Account CRUD, the Account Review wizard for guided balance updates, and a balance history view. All pages follow the **list+detail split layout** pattern (see [Notes Architecture](../_notes-architecture.md)).

---

## Account Page (CRUD)

> **Source**: [Domain Model Reference](domain-model-reference.md) `Account` entity, [Input Index §7](input-index.md).

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Accounts                                   [+ New Account]  [Start Review Wizard]  │
├──────────────────────────────────┬───────────────────────────────────────────────────┤
│  ACCOUNT LIST (left pane)        │  ACCOUNT DETAIL (right pane)                     │
│  ┌────────────────────────────┐  │                                                  │
│  │ 💰 Main Trading (BROKER)  │◄─│─ selected                                       │
│  │    $82,450.00              │  │  ── Account Info ──────────────────────────      │
│  │                            │  │                                                  │
│  │ 💰 Roth IRA (RETIREMENT)  │  │  Name:           [ Main Trading        ]         │
│  │    $215,300.00             │  │  Account Type:   [ BROKER ▼ ]                    │
│  │                            │  │  Institution:    [ Interactive Brokers ]          │
│  │ 🏦 Savings (BANK)         │  │  Currency:       [ USD ▼ ]                       │
│  │    $45,000.00              │  │  Tax-Advantaged:  [□]                            │
│  │                            │  │                                                  │
│  │ 🏦 Checking (BANK)        │  │  Notes:                                          │
│  │    $12,500.00              │  │  ┌──────────────────────────────────────────┐   │
│  │                            │  │  │ Primary day trading account. Paper       │   │
│  │ 🚗 Auto Loan (LOAN)       │  │  │ trading for strategy validation.        │   │
│  │    -$18,500.00             │  │  └──────────────────────────────────────────┘   │
│  └────────────────────────────┘  │                                                  │
│                                  │  ── Latest Balance ───────────────────────       │
│  Portfolio Total: $336,750.00    │  $82,450.00  (as of Jan 15, 2025)                │
│                                  │  [Update Balance]                                │
│  Account Types:                  │                                                  │
│  💰 BROKER / RETIREMENT         │  ── Balance History ──────────────────────       │
│  🏦 BANK / SAVINGS              │  [Sparkline chart — last 90 days]                │
│  🚗 LOAN                        │                                                  │
│  📈 INVESTMENT                   │  [Save]  [Delete]  [Cancel]                     │
│                                  │                                                  │
└──────────────────────────────────┴───────────────────────────────────────────────────┘
```

### Account Form Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `name` | `text` | user input | Display name |
| `account_type` | `select` | AccountType enum | BROKER, BANK, RETIREMENT, LOAN, INVESTMENT, SAVINGS |
| `institution` | `text` | user input | Bank or broker name |
| `currency` | `select` | currency codes | Default USD |
| `is_tax_advantaged` | `checkbox` | user input | Excludes from tax calculations |
| `notes` | `textarea` | user input | Free-text notes |

### Account List Card Fields

- Type icon (💰 for trading/retirement, 🏦 for bank, etc.)
- Account name + type badge
- Latest balance (from most recent `BalanceSnapshot`)

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/accounts` | List all accounts |
| `POST` | `/api/v1/accounts` | Create account |
| `GET` | `/api/v1/accounts/{id}` | Get account detail |
| `PUT` | `/api/v1/accounts/{id}` | Update account |
| `DELETE` | `/api/v1/accounts/{id}` | Delete account |
| `GET` | `/api/v1/accounts/{id}/balances` | Get balance history |
| `POST` | `/api/v1/accounts/{id}/balances` | Record new balance |

---

## Account Review Wizard

> **Source**: [Domain Model Reference](domain-model-reference.md) `AccountReview` process spec. A guided step-by-step wizard for updating all account balances in sequence. Can be triggered from the Accounts page, command palette (`Account Review` action), or programmatically via MCP (`get_account_review_checklist` tool).

### Layout — Step View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Account Review                                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ◻◻◻◻◻                     │
│  Account 2 of 5                                            Progress: 40%   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🏦  Main Trading Account                                                 │
│  Type: BROKER  ·  Institution: Interactive Brokers                         │
│                                                                             │
│  ── Current Balance ───────────────────────────────────────────────        │
│                                                                             │
│  Last recorded:  $82,450.00  (Jan 15, 2025)                               │
│                                                                             │
│  ── Update Balance ───────────────────────────────────────────────         │
│                                                                             │
│  New balance: [ 83,200.00    ]                                             │
│                                                                             │
│  Change: +$750.00 (+0.91%)                                                 │
│                                                                             │
│  [Fetch from API]     ← only for BROKER accounts (calls TWS/IBKR API)     │
│                                                                             │
│  ────────────────────────────────────────────────────────────────           │
│                                                                             │
│  Running Portfolio Total:  $337,500.00  (was $336,750.00, +$750.00)        │
│                                                                             │
│  [Skip]  [Update & Next ▶]                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layout — Completion View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Account Review                                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Review Complete ✓                                                         │
│                                                                             │
│  Updated: 4 of 5 accounts                                                 │
│  Skipped: 1 (Auto Loan — unchanged)                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Account            │  Previous    │  Updated     │  Change    │       │
│  ├─────────────────────┼─────────────┼──────────────┼────────────┤       │
│  │  Main Trading       │  $82,450    │  $83,200     │  +$750     │       │
│  │  Roth IRA           │  $215,300   │  $216,100    │  +$800     │       │
│  │  Savings            │  $45,000    │  $45,120     │  +$120     │       │
│  │  Checking           │  $12,500    │  $12,800     │  +$300     │       │
│  │  Auto Loan          │  -$18,500   │  (skipped)   │     —      │       │
│  └─────────────────────┴─────────────┴──────────────┴────────────┘       │
│                                                                             │
│  New Total Portfolio: $339,720.00  (was $336,750.00, +$2,970.00)          │
│                                                                             │
│  [Done]                                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Wizard Behavior Rules

| Rule | Description |
|------|-------------|
| **BROKER accounts** | Show "Fetch from API" button (calls TWS/IBKR API for live balance) |
| **All other types** | Manual entry only, last balance pre-filled |
| **Deduplication** | Balance only logged if value actually changed from last snapshot |
| **Skip** | Moves to next account without saving a snapshot |
| **Progress bar** | Shows "Account N of M" with visual progress indicator |
| **Keyboard shortcuts** | `Tab` → enter amount → `Enter` → next account |
| **Live total** | Running portfolio total updates as each account is confirmed |
| **MCP integration** | `get_account_review_checklist` tool returns guided prompts for AI agents |
| **Scheduled trigger** | Can be auto-triggered on schedule (e.g., daily at market close) |

### REST Endpoints Consumed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/accounts` | Get all accounts for wizard steps |
| `GET` | `/api/v1/accounts/{id}/balances?limit=1` | Get latest balance |
| `POST` | `/api/v1/accounts/{id}/balances` | Record updated balance |

---

## Balance History View

Embedded within the Account Detail panel (right pane). Shows a sparkline chart of the last 90 days of `BalanceSnapshot` entries and a scrollable table of all entries.

```
┌─────────────────────────────────────────────────────────────────┐
│  Balance History — Main Trading                                │
│                                                                 │
│  [Sparkline: ───────╱──╲───╱╱──── ]    Last 90 days            │
│                                                                 │
│  ┌──────────────┬─────────────┬──────────────────┐             │
│  │ Date         │ Balance     │ Change           │             │
│  ├──────────────┼─────────────┼──────────────────┤             │
│  │ Jan 15, 2025 │ $83,200.00  │ +$750.00 (+0.9%) │             │
│  │ Jan 14, 2025 │ $82,450.00  │ -$320.00 (-0.4%) │             │
│  │ Jan 13, 2025 │ $82,770.00  │ +$1,100 (+1.3%)  │             │
│  │ ...          │             │                  │             │
│  └──────────────┴─────────────┴──────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Chart Library

Use **Lightweight Charts** (same library used for financial charts elsewhere in the app) for the balance sparkline. Falls back to a simple HTML `<canvas>` sparkline if the full chart library is too heavy for this use case.

---

## Build Plan Expansion: Account Enhancements

> Source: [Build Plan Expansion Ideas](../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §1, §24, §25, §26

### Bank Statement Import Panel (§26)

Added to the Account Detail right pane for BANK and SAVINGS account types:

```
┌─────────────────────────────────────────────────────────────────┐
│  Import Bank Statement                                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Drag & drop a bank statement file here                    │ │
│  │ or [Browse...]                                            │ │
│  │                                                            │ │
│  │ Supported: CSV, OFX/QFX, QIF                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Format:  [Auto-detect ▼]                                      │
│  Bank:    [Auto-detect ▼]   ← auto-detected from CSV headers  │
│                                                                 │
│  [Import]  ← triggers POST /api/v1/banking/import              │
│                                                                 │
│  Last import: Jan 15, 2025 — 42 transactions (2 duplicates)    │
└─────────────────────────────────────────────────────────────────┘
```

### Broker Sync Button Enhancements (§1, §24, §25)

The existing "Fetch from API" button in the Account Review Wizard is enhanced for multiple broker types:

| Account Broker | Button Label | Action |
|---------------|-------------|--------|
| Interactive Brokers | "Fetch from IBKR" | Calls IBKR FlexQuery adapter |
| Alpaca (§24) | "Fetch from Alpaca" | Calls Alpaca REST adapter |
| Tradier (§25) | "Fetch from Tradier" | Calls Tradier REST adapter |
| Other/Manual | (no button) | Manual entry only |

> The button dynamically adapts to the broker type configured for the account. Multiple broker adapters can be configured per account.

### Transaction History Tab (§26)

For BANK/SAVINGS accounts, a new "Transactions" tab appears in the Account Detail panel:

```
┌─────────────────────────────────────────────────────────────────┐
│  Transactions — Checking (Chase)                                │
│                                                                 │
│  ┌────────────┬────────────────────────┬──────────┬──────────┐ │
│  │ Date       │ Description            │ Amount   │ Category │ │
│  ├────────────┼────────────────────────┼──────────┼──────────┤ │
│  │ Jan 15     │ ACH Transfer - Savings │ +$500.00 │ Transfer │ │
│  │ Jan 14     │ Amazon.com             │ -$42.99  │ Purchase │ │
│  │ Jan 13     │ Payroll Deposit        │ +$3,200  │ ACH Cred │ │
│  │ Jan 12     │ Gas Station            │ -$45.00  │ Purchase │ │
│  └────────────┴────────────────────────┴──────────┴──────────┘ │
│                                                                 │
│  Source: OFX Import  ·  Batch: 2025-01-15-001                  │
└─────────────────────────────────────────────────────────────────┘
```

### New React Components

| Component | Source §§ | Description |
|-----------|----------|-------------|
| `BankImportPanel` | §26 | Drag-and-drop statement import with format detection |
| `TransactionHistoryTable` | §26 | Bank transaction list with category badges |
| `BrokerSyncButton` | §1, §24, §25 | Dynamic broker-aware fetch button |
| `ColumnMappingWizard` | §26 | Manual CSV column mapping for unrecognized bank formats |
| `ManualTransactionForm` | §26 | Manual bank transaction entry form (date, amount, description, category) |

---

## Exit Criteria

- Account CRUD page displays all accounts with type icons and latest balances
- Portfolio total computes correctly as sum of all latest balances
- Account Review wizard steps through all accounts in sequence
- Wizard shows "Fetch from API" button only for BROKER accounts
- Balance only saved when value actually changes (dedup)
- Completion view shows summary table with changes
- Balance history sparkline renders for selected account

## Outputs

- React components: `AccountPage`, `AccountDetailPanel`, `AccountReviewWizard`, `BalanceHistory`
- Account CRUD form with all domain fields
- Account Review wizard with progress bar, skip, and API fetch
- Balance sparkline using Lightweight Charts
- Portfolio total computed from latest balance snapshots

### Build Plan Expansion Components

- `BankImportPanel` — drag-and-drop bank statement import (§26)
- `TransactionHistoryTable` — bank transaction list with categories (§26)
- `BrokerSyncButton` — dynamic broker-specific fetch button (§1, §24, §25)
- `ColumnMappingWizard` — manual CSV column mapping for unrecognized bank formats (§26)
- `ManualTransactionForm` — manual bank transaction entry form (§26)

