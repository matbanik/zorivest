# Account Management GUI

**Project slug**: `account-gui`
**MEU**: MEU-71a (`account-gui`)
**Build plan sections**: [`06d-gui-accounts.md`](file:///p:/zorivest/docs/build-plan/06d-gui-accounts.md), [`06-gui.md`](file:///p:/zorivest/docs/build-plan/06-gui.md) §Accounts Home Dashboard

## Background

The Account backend (entity, service, repository, CRUD routes, balance history endpoint) is **complete** (MEU-71 ✅). The `AccountsHome.tsx` component is currently a 10-line stub. This project replaces it with the full Account Management page: MRU cards, All Accounts table, list+detail CRUD, Account Review Wizard, and Balance History sparkline.

> [!NOTE]
> **Frontend-only project.** No Python backend changes are required. All API endpoints (`GET/POST/PUT/DELETE /accounts`, `GET/POST /{id}/balances`) are production-ready from MEU-71. The `useAccounts` hook and `Account` interface already exist in `ui/src/renderer/src/hooks/useAccounts.ts`.

> [!IMPORTANT]
> **Out of scope.** The build plan expansion components (BankImportPanel, BrokerSyncButton, TransactionHistoryTable, ColumnMappingWizard, ManualTransactionForm) depend on future MEUs (IBKR adapter, CSV import). The Account Review Wizard's "Fetch from API" button is rendered for BROKER accounts but shows a disabled state with tooltip "Not yet connected — configure in Settings" since no broker adapters exist.

---

## Spec Sufficiency Gate

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Account list with type icons + latest balance | Spec | `06d` L23-49, L63-67 | ✅ | Left pane of split layout |
| Account detail form (name, type, institution, currency, tax-advantaged, notes) | Spec | `06d` L52-61 | ✅ | Right pane CRUD form |
| Save / Delete / Cancel actions | Spec | `06d` L47 | ✅ | Button bar on detail panel |
| Latest balance display + "Update Balance" button | Spec | `06d` L40-42 | ✅ | Records via `POST /{id}/balances` |
| Balance History sparkline (90 days) + table | Spec | `06d` L174-199 | ✅ | Lightweight Charts sparkline |
| Account Review Wizard — step view | Spec | `06d` L83-118 | ✅ | Progress bar, balance input, change display |
| Account Review Wizard — completion view | Spec | `06d` L120-148 | ✅ | Summary table with portfolio delta |
| Wizard dedup rule (save only if changed) | Spec | `06d` L156 | ✅ | Compare to last snapshot value |
| "Fetch from API" button for BROKER accounts only | Spec | `06d` L154 | ✅ | Disabled stub — no adapter yet |
| MRU account cards (top 3) + "Add New" card | Spec | `06-gui` L286-331 | ✅ | MRU tracking via `SettingModel` |
| All Accounts table with filter/sort + portfolio total | Spec | `06-gui` L302-314 | ✅ | Uses `useAccounts` hook |
| AccountContext provider (global active account) | Spec | `06-gui` L343-378 | ✅ | Context API |
| E2E Wave 2 test IDs (`accounts-page`, `account-list`, `add-account-btn`) | Spec | `06-gui` L411 | ✅ | Already in `test-ids.ts` |
| Account Review triggerable from command palette | Spec | `06d` L83-85, `06a` L222 | ✅ | G11 custom event pattern via AppShell |
| Account Review triggerable from Accounts page button | Spec | `06d` L83 | ✅ | Button dispatches same custom event |

---

## Proposed Changes

### Shared Infrastructure

---

#### [NEW] [AccountContext.tsx](file:///p:/zorivest/ui/src/renderer/src/context/AccountContext.tsx)

Global account selection context (per `06-gui.md` L350-378):
- `activeAccountId: string` state
- `selectAccount(id: string)` — sets active account, updates MRU list
- MRU list persisted via `usePersistedState('ui.accounts.mru')`
- Consumed by Trades, Planning, Tax modules for context filtering

#### [MODIFY] [useAccounts.ts](file:///p:/zorivest/ui/src/renderer/src/hooks/useAccounts.ts)

Extend `Account` interface to include all fields from `AccountResponse`:
- Add `institution: string`, `currency: string`, `is_tax_advantaged: boolean`, `notes: string`
- Add mutation hooks: `useCreateAccount()`, `useUpdateAccount()`, `useDeleteAccount()`
- Add `useBalanceHistory(accountId)` hook for paginated balance history

---

### Accounts Home (Dashboard)

---

#### [MODIFY] [AccountsHome.tsx](file:///p:/zorivest/ui/src/renderer/src/features/accounts/AccountsHome.tsx)

Complete rewrite from 10-line stub to full Account Management page (per `06-gui` L275-398 and `06d` L13-49):

**Layout**: Split layout — left pane + right pane
- **Left pane**: MRU card strip (top 3 recently used + "Add New" card) above account list table
- **Right pane**: Account detail form when account selected, empty state prompt when none selected
- **"Start Review" button** in header opens Account Review Wizard
- Portfolio total displayed in left pane footer

**MRU Cards**: Each card shows account name, type icon, institution, latest balance, "Select" CTA. Data from `useAccounts` hook.

**All Accounts Table**: Type icon, name, institution, balance, last used date, Select/overflow menu. Filterable by account type, sortable by last used.

**Add Account**: "Add New" MRU card or "+" button opens blank detail form.

**Data test IDs**: `data-testid="accounts-page"`, `data-testid="account-list"`, `data-testid="add-account-btn"` (Wave 2)

#### [NEW] [AccountDetailPanel.tsx](file:///p:/zorivest/ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx)

Right pane CRUD form (per `06d` L52-61):
- Form fields: name (text), account_type (select: BROKER/BANK/RETIREMENT/LOAN/INVESTMENT/SAVINGS), institution (text), currency (select), is_tax_advantaged (checkbox), notes (textarea)
- React Hook Form + Zod validation
- Save → `PUT /accounts/{id}` or `POST /accounts` for new
- Delete → `DELETE /accounts/{id}` with confirmation dialog
- Latest balance display + "Update Balance" inline dialog → `POST /{id}/balances`
- Balance History embedded component

#### [NEW] [BalanceHistory.tsx](file:///p:/zorivest/ui/src/renderer/src/features/accounts/BalanceHistory.tsx)

Balance History panel (per `06d` L174-199):
- Sparkline chart using Lightweight Charts (or `<canvas>` fallback)
- Scrollable table: Date, Balance, Change ($ and %)
- Data from `GET /accounts/{id}/balances`

---

### Account Review Wizard + Global Action Wiring

---

#### [NEW] [AccountReviewWizard.tsx](file:///p:/zorivest/ui/src/renderer/src/features/accounts/AccountReviewWizard.tsx)

Full-screen dialog/overlay wizard (per `06d` L83-162). Accepts `isOpen: boolean` + `onClose: () => void` props.

**Step View** (per account):
- Progress bar: "Account N of M" with visual indicator
- Account info: type icon, name, type, institution
- Current balance: last recorded amount + date
- New balance input (numeric, pre-filled with last balance)
- Live change calculation: `+$750.00 (+0.91%)`
- "Fetch from API" button (BROKER accounts only — disabled stub)
- Running portfolio total
- [Skip] and [Update & Next ▶] buttons
- Keyboard: Tab → amount → Enter → next

**Completion View**:
- Summary table: Account, Previous, Updated, Change
- Skipped accounts shown
- New portfolio total with delta
- [Done] button closes wizard

**Dedup rule**: Balance only saved (via `POST /{id}/balances`) if value actually changed from last snapshot.

#### [MODIFY] [commandRegistry.ts](file:///p:/zorivest/ui/src/renderer/src/registry/commandRegistry.ts)

Replace console stub at L97-102 with G11-compliant custom event dispatch (per `emerging-standards.md` G11, `06a` L222):

```typescript
// Before:
action: () => { console.info('[command] Account Review — not yet implemented') },
// After:
action: () => { window.dispatchEvent(new CustomEvent('zorivest:start-review')) },
```

#### [MODIFY] [AppShell.tsx](file:///p:/zorivest/ui/src/renderer/src/components/layout/AppShell.tsx)

Add Account Review wizard ownership following the same G11 pattern used for Position Calculator:
1. Add `reviewOpen` state
2. Add `useEffect` listener for `zorivest:start-review` custom event
3. Render `<AccountReviewWizard isOpen={reviewOpen} onClose={() => setReviewOpen(false)} />`

---

### E2E Wave 2

---

#### [MODIFY] (no file changes) — Wave 2 Activation

E2E `persistence.test.ts` (2 tests) already exists and references `ACCOUNTS.ROOT`, `ACCOUNTS.ACCOUNT_LIST`. Once the components render with the correct `data-testid` attributes, Wave 2 tests become active. No new E2E test files need to be written — only ensure test IDs are applied.

---

### Post-MEU Deliverables

---

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Update MEU-71a status from `⏸` to `✅`

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

Add MEU-71a entry with completion evidence

#### [NEW] Handoff file

`094-2026-03-27-account-gui-bp06ds35a1.md` in `.agent/context/handoffs/`

---

## Feature Intent Contract

### FIC: MEU-71a — Account Management GUI

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | AccountsHome renders MRU card strip (top 3) with account name, type icon, institution, latest balance, and "Select" CTA | Spec: `06-gui` L286-331 |
| AC-2 | AccountsHome renders "Add New" card that opens blank account form | Spec: `06-gui` L331 |
| AC-3 | All Accounts table renders with type icon, name, institution, balance, actions; filterable by type, sortable | Spec: `06-gui` L302-314 |
| AC-4 | Portfolio total displays as sum of latest balances | Spec: `06-gui` L304 |
| AC-5 | Account detail form renders all CRUD fields (name, type, institution, currency, tax-advantaged, notes) with validation | Spec: `06d` L52-61 |
| AC-6 | Save persists via `PUT /accounts/{id}` (update) or `POST /accounts` (create); list refreshes on success | Spec: `06d` L73-77, `06d` L96-109 |
| AC-7 | Delete removes via `DELETE /accounts/{id}` with confirmation dialog; list refreshes on success | Spec: `06d` L77, L148-152 |
| AC-8 | "Update Balance" records via `POST /{id}/balances`; latest balance refreshes | Spec: `06d` L42, L79 |
| AC-9 | Balance History renders sparkline chart (last 90 days) and scrollable date/balance/change table from `GET /{id}/balances` | Spec: `06d` L174-199 |
| AC-10 | Account Review Wizard steps through all accounts with progress bar, balance input, live change calculation, running total | Spec: `06d` L83-118 |
| AC-11 | Wizard only saves balance if value changed (dedup); "Skip" moves to next without saving | Spec: `06d` L156-157 |
| AC-12 | Wizard completion view shows summary table with per-account changes and portfolio delta | Spec: `06d` L120-148 |
| AC-13 | "Fetch from API" button shown only for BROKER accounts (disabled stub with tooltip) | Spec: `06d` L154 |
| AC-14 | AccountContext provider sets global `activeAccountId`; consumed by other modules | Spec: `06-gui` L343-378 |
| AC-15 | `data-testid` attributes applied: `accounts-page`, `account-list`, `add-account-btn` (Wave 2) | Spec: `06-gui` L411 |
| AC-16 | Account Review Wizard opens via command palette (`action:review` → `zorivest:start-review` custom event → AppShell) and via "Start Review" button on Accounts page | Spec: `06d` L83-85, `06a` L222; Local Canon: `emerging-standards.md` G11 |

---

## Verification Plan

### Automated Tests — Unit (Vitest)

New test files:

| Test File | Tests | ACs Covered |
|-----------|-------|-------------|
| `AccountsHome.test.tsx` | MRU cards render, "Add New" card, All Accounts table, portfolio total, account selection | AC-1, AC-2, AC-3, AC-4, AC-14 |
| `AccountDetailPanel.test.tsx` | Form renders fields, save creates, save updates, delete with confirm, balance update | AC-5, AC-6, AC-7, AC-8 |
| `BalanceHistory.test.tsx` | Table renders balance entries, change calculation, empty state | AC-9 |
| `AccountReviewWizard.test.tsx` | Wizard steps, progress bar, skip, dedup, completion summary, fetch button visibility, event-driven open | AC-10, AC-11, AC-12, AC-13, AC-16 |
| `AccountContext.test.tsx` | Context provides activeAccountId, selectAccount updates, MRU tracking | AC-14 |

**Run command** (Cwd: `ui/`):
```powershell
cd ui; npx vitest run src/renderer/src/features/accounts/ src/renderer/src/context/__tests__/ --reporter=verbose *> C:\Temp\zorivest\vitest-accounts.txt; Get-Content C:\Temp\zorivest\vitest-accounts.txt | Select-Object -Last 40
```

### Automated Tests — E2E (Playwright)

Existing E2E `persistence.test.ts` (2 tests) activates when `data-testid` attributes are present.

> [!IMPORTANT]
> **Build before E2E.** Per `06-gui.md` L413-417, `npm run build` is required before every Playwright run — Playwright launches the compiled bundle, not source files.

**Run commands** (Cwd: `ui/`):
```powershell
cd ui; npm run build *> C:\Temp\zorivest\e2e-build.txt; Get-Content C:\Temp\zorivest\e2e-build.txt | Select-Object -Last 20
cd ui; npx playwright test persistence.test.ts *> C:\Temp\zorivest\e2e-wave2.txt; Get-Content C:\Temp\zorivest\e2e-wave2.txt | Select-Object -Last 30
```

### Type Check + Lint

```powershell
cd ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 20
```

### MEU Gate

```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Stop Conditions

Execution **must halt** and return to PLANNING if any of the following occur:

1. **Lightweight Charts incompatibility** — if `lightweight-charts` cannot render inside jsdom/happy-dom test environment and no viable mock strategy exists, halt and decide on canvas fallback
2. **React Hook Form + shadcn integration failure** — if form field bindings produce runtime errors with shadcn Select/Checkbox components, halt and evaluate alternative form library
3. **AppShell circular dependency** — if importing `AccountReviewWizard` into `AppShell.tsx` creates a circular import chain through shared hooks, halt and restructure module boundaries
4. **E2E Wave 2 infrastructure missing** — if `npm run build` fails due to missing Playwright or electron-builder configuration, halt (this is an infrastructure gap, not a code bug)
5. **API contract mismatch** — if the `AccountResponse` schema from the running API differs from the fields documented in the implementation plan, halt and reconcile with the backend
