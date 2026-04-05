# MEU-71a: Account Management GUI — Task List

> **Project slug**: `account-gui`
> **MEU**: MEU-71a (`account-gui`)
> **Plan**: [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-03-27-account-gui/implementation-plan.md)

---

## Phase 1: FIC Tests (Red)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write `AccountContext.test.tsx` — AC-14 (global selection, MRU tracking) | coder | `context/__tests__/AccountContext.test.tsx` (8 tests) | `npx vitest run src/renderer/src/context/__tests__/` | `[x]` |
| 2 | Write `useAccounts.test.ts` — AC-6 (fetch, create, update, delete, error) | coder | `hooks/__tests__/useAccounts.test.ts` (5 tests) | `npx vitest run src/renderer/src/hooks/__tests__/useAccounts.test.ts` | `[x]` |
| 3 | Write `AccountsHome.test.tsx` — AC-1, AC-2, AC-3, AC-4, AC-15 (MRU cards, table, portfolio total, testids) | coder | `features/accounts/__tests__/AccountsHome.test.tsx` (10 tests) | `npx vitest run src/renderer/src/features/accounts/__tests__/AccountsHome.test.tsx` | `[x]` |
| 4 | Write `AccountDetailPanel.test.tsx` — AC-5, AC-6, AC-7, AC-8 (CRUD form, save, delete, balance update) | coder | `features/accounts/__tests__/AccountDetailPanel.test.tsx` (9 tests) | `npx vitest run src/renderer/src/features/accounts/__tests__/AccountDetailPanel.test.tsx` | `[x]` |
| 5 | Write `BalanceHistory.test.tsx` — AC-9 (sparkline, table, change calc, empty state) | coder | `features/accounts/__tests__/BalanceHistory.test.tsx` (5 tests) | `npx vitest run src/renderer/src/features/accounts/__tests__/BalanceHistory.test.tsx` | `[x]` |
| 6 | Write `AccountReviewWizard.test.tsx` — AC-10, AC-11, AC-12, AC-13, AC-16 (wizard steps, dedup, fetch button, G11 event) | coder | `features/accounts/__tests__/AccountReviewWizard.test.tsx` (10 tests) | `npx vitest run src/renderer/src/features/accounts/__tests__/AccountReviewWizard.test.tsx` | `[x]` |

---

## Phase 2: Implementation (Green)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 7 | Implement `AccountContext.tsx` — global selection + MRU persistence | coder | `context/AccountContext.tsx` | Task 1 tests pass | `[x]` |
| 8 | Extend `useAccounts.ts` — Account interface, CRUD mutations, `useBalanceHistory` hook | coder | `hooks/useAccounts.ts` | Task 2 tests pass | `[x]` |
| 9 | Implement `AccountsHome.tsx` — MRU card strip, All Accounts table, split layout, portfolio total | coder | `features/accounts/AccountsHome.tsx` | Task 3 tests pass | `[x]` |
| 10 | Implement `AccountDetailPanel.tsx` — RHF+Zod CRUD form, balance update, delete confirm | coder | `features/accounts/AccountDetailPanel.tsx` | Task 4 tests pass | `[x]` |
| 11 | Implement `BalanceHistory.tsx` — canvas sparkline + scrollable table | coder | `features/accounts/BalanceHistory.tsx` | Task 5 tests pass | `[x]` |
| 12 | Implement `AccountReviewWizard.tsx` — multi-step wizard, dedup, fetch stub | coder | `features/accounts/AccountReviewWizard.tsx` | Task 6 tests pass | `[x]` |
| 13 | Wire `commandRegistry.ts` — replace console stub with G11 `zorivest:start-review` event | coder | `registry/commandRegistry.ts` L102 | `rg 'start-review' commandRegistry.ts` | `[x]` |
| 14 | Wire `AppShell.tsx` — `AccountProvider`, `zorivest:start-review` listener, wizard render | coder | `components/layout/AppShell.tsx` | `rg 'start-review' AppShell.tsx` | `[x]` |

---

## Phase 3: Type Check + Full Suite

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 15 | TypeScript type check — zero errors | tester | Clean tsc output | `cd ui; npx tsc --noEmit` | `[x]` |
| 16 | Full Vitest suite — all account tests pass | tester | 47 tests across 6 files GREEN | `cd ui; npx vitest run` | `[x]` |

---

## Phase 4: Bug Fixes (Post-Implementation)

> These tasks were added during the current session to fix issues found during live GUI testing.

| # | Task | Owner | Root Cause | Fix | Validation | Status |
|---|------|-------|-----------|-----|------------|--------|
| BF-1 | "Add New +" GUI freeze | coder | `selectAccount(null)` was a no-op — no create form existed | Added `showCreateForm` state + inline `CreateAccountForm` in right pane | Vitest 47 tests GREEN | `[x]` |
| BF-2 | 422 on POST /api/v1/accounts | coder | `useCreateAccount` didn't send `account_id` (required by API) | Added `account_id: crypto.randomUUID()` to mutation payload | Live POST → 201 Created | `[x]` |
| BF-3 | `useAccounts.test.ts` AC-6 timeout | coder | Per-hook `retry:1` overrode test wrapper's `retry:false`, causing TanStack Query backoff during test | Removed per-hook retry overrides; app-level QueryClient `retry:2` handles production, test wrappers use `retry:false` | `mockRejectedValueOnce` test passes | `[x]` |

---

## Phase 5: E2E Wave 2

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| E2E-1 | Build Electron bundle | tester | `out/` compiled | `cd ui; npm run build` | `[x]` |
| E2E-2 | Fix `persistence.test.ts` — API response shape | coder | Fix `apiGet` type from `{data:[]}` to bare `unknown[]` | `persistence.test.ts` compiles | `[x]` |
| E2E-3 | Fix `persistence.test.ts` — add accounts navigation | coder | Add `navigateTo('accounts')` before asserting `ACCOUNTS.ROOT` | Test reaches accounts page | `[x]` |
| E2E-4 | Fix `persistence.test.ts` — window bounds API | coder | Replace Playwright `setViewportSize`/`viewportSize()` with Electron `BrowserWindow.setBounds`/`getBounds` | Window bounds read/write through correct API | `[x]` |
| E2E-5 | Run E2E Wave 2 — both tests pass | tester | 2/2 passed (13.1s) | `cd ui; npx playwright test persistence.test.ts` | `[x]` |

---

## Phase 6: Post-MEU Deliverables

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 17 | Update `BUILD_PLAN.md` — MEU-71a `⏸` → `✅` | coder | `docs/BUILD_PLAN.md` L263 | `rg 'MEU-71a' BUILD_PLAN.md` | `[x]` |
| 18 | Update `meu-registry.md` — add MEU-71a entry | coder | `.agent/context/meu-registry.md` | `rg '71a' meu-registry.md` | `[x]` |
| 19 | Create handoff `094-2026-03-27-account-gui-bp06ds35a1.md` | coder | `.agent/context/handoffs/094-...md` | File exists with evidence | `[x]` |
| 20 | Save session to pomera_notes | coder | Note ID: 712 | `pomera_notes get --note_id 712` | `[x]` |
| 21 | Update handoff with bug fixes + E2E evidence | coder | Updated handoff 094 | File reflects BF-1/2/3 + E2E | `[x]` |
| 22 | Create reflection | coder | `docs/execution/reflections/2026-03-27-account-gui-reflection.md` | File exists | `[x]` |

---

## Phase 7: Critical Review Corrections

> Corrections from `2026-03-27-account-gui-implementation-critical-review.md`

| # | Finding | Severity | Fix | Validation | Status |
|---|---------|----------|-----|------------|--------|
| F1 | BROKER "Fetch from API" button missing | High | Added disabled stub button in wizard + 2 tests | vitest passes | `[x]` |
| F2 | Table missing filter/sort/Last Used/Actions | High | Added filter/sort controls, 2 new columns, portfolio total consolidated to filter bar | vitest passes | `[x]` |
| F3 | Wizard always starts at index 0 | Medium | Reads `activeAccountId` from context + 1 test | vitest passes | `[x]` |
| F4 | AccountContext uses `useState` not `usePersistedState` | Medium | Migrated to `usePersistedState` + 2 tests + stateful mock | vitest passes | `[x]` |
| F5 | E2E evidence stale | Low | Resolved — clean build passes 2/2 (13.7s) | Playwright PASS | `[x]` |
| F2b | `AccountDetailPanel` missing `isNew`/`onCreated` props | High | Added props + create mode fork in onSave | tsc clean | `[x]` |
| F2c | Vitest: duplicate portfolio total text | Medium | Removed footer (redundant with filter bar) | vitest passes | `[x]` |
| F4b | AccountContext tests: async mutation timing | Medium | Added `waitFor` + stateful `apiFetchMock` | vitest passes | `[x]` |
| F6 | Create-mode exposes invalid actions | Medium | Added `!isNew` guards on Balance/Delete/BalanceHistory + "Create" label | vitest passes | `[x]` |
| F6b | Missing create-mode tests | Medium | 2 new tests: hidden UI + Create label | vitest 54/54 GREEN | `[x]` |
