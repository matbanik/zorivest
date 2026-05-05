/**
 * E2E: Account CRUD and Balance operations.
 *
 * Wave 2 (MEU-71a): Tests the full account lifecycle through the Electron GUI
 * against the live Python backend.
 *
 *   Create → Select → Update Balance (UI + API) → Edit → Save → Delete
 *
 * Follows established patterns from trade-entry.test.ts:
 * - Uses AppPage POM (apiGet, apiPost, testId, navigateTo)
 * - Uses data-testid constants from test-ids.ts
 * - Backend auto-started by global-setup.ts
 * - Build required before run: `cd ui && npm run build`
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { ACCOUNTS, CONFIRM_DELETE, UNSAVED_CHANGES } from './test-ids'

const API_BASE = 'http://localhost:17787/api/v1'

// Prefix all test account names to identify and clean them
const TEST_PREFIX = 'E2E_'

// ── API helpers (Node-native fetch for setup/teardown) ─────────────────

async function apiCreate(data: Record<string, unknown>): Promise<{ account_id: string }> {
    const body = { account_id: crypto.randomUUID(), ...data }
    const res = await fetch(`${API_BASE}/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`API POST /accounts failed: ${res.status} ${await res.text()}`)
    return res.json() as Promise<{ account_id: string }>
}

async function apiDelete(accountId: string): Promise<void> {
    // cascade="all, delete-orphan" on AccountModel handles balance cleanup
    await fetch(`${API_BASE}/accounts/${accountId}`, { method: 'DELETE' })
}

async function apiList(): Promise<Array<{ account_id: string; name: string }>> {
    const res = await fetch(`${API_BASE}/accounts`)
    return res.json() as Promise<Array<{ account_id: string; name: string }>>
}

// ── Test suite ─────────────────────────────────────────────────────────

test.describe('Account CRUD', () => {
    let appPage: AppPage
    const createdAccountIds: string[] = []

    test.beforeAll(async () => {
        // Clean up leftover test accounts from prior runs
        const accounts = await apiList()
        for (const acct of accounts) {
            if (acct.name.startsWith(TEST_PREFIX)) {
                await apiDelete(acct.account_id)
            }
        }
        await new Promise((r) => setTimeout(r, 500))
    })

    test.beforeEach(async () => {
        appPage = new AppPage()
        await appPage.launch()
        await appPage.navigateTo('accounts')
        await appPage.waitForTestId(ACCOUNTS.ROOT)
    })

    test.afterEach(async () => {
        for (const id of createdAccountIds) {
            try { await apiDelete(id) } catch { /* best-effort */ }
        }
        createdAccountIds.length = 0
        await appPage.close()
    })

    test('create a new account via the form', async () => {
        // Click Add New
        await appPage.testId(ACCOUNTS.ADD_BUTTON).click()
        await appPage.waitForTestId(ACCOUNTS.DETAIL_PANEL)

        // Fill in the form
        await appPage.testId(ACCOUNTS.FORM.NAME).fill(`${TEST_PREFIX}Create`)
        await appPage.testId(ACCOUNTS.FORM.TYPE).selectOption('broker')
        await appPage.testId(ACCOUNTS.FORM.INSTITUTION).fill('Test Broker Inc')
        // Currency selector deferred — see AccountDetailPanel.tsx DEFERRED comment
        await appPage.testId(ACCOUNTS.FORM.NOTES).fill('Created by E2E')

        // Click Create
        await appPage.testId(ACCOUNTS.FORM.SUBMIT).click()

        // Wait for mutation
        await appPage.page.waitForTimeout(2_000)

        // Verify via API
        const accounts = await apiList()
        const created = accounts.find((a) => a.name === `${TEST_PREFIX}Create`)
        expect(created).toBeDefined()

        if (created) createdAccountIds.push(created.account_id)
    })

    test('select account and update balance', async () => {
        // Seed an account via API
        const created = await apiCreate({
            name: `${TEST_PREFIX}Balance`,
            account_type: 'bank',
            institution: 'E2E Bank',
            currency: 'USD',
            is_tax_advantaged: false,
            notes: '',
        })
        createdAccountIds.push(created.account_id)

        // Reload to pick up the new account
        await appPage.page.reload()
        await appPage.waitForTestId(ACCOUNTS.ROOT)

        // Wait for account name to appear
        const nameLocator = appPage.page
            .getByText(`${TEST_PREFIX}Balance`, { exact: true })
            .first()
        await nameLocator.waitFor({ state: 'visible', timeout: 15_000 })

        // Click the row to select the account
        const row = appPage.page
            .locator('[data-testid="account-list"] tbody tr')
            .filter({ hasText: `${TEST_PREFIX}Balance` })
        await row.click()
        await appPage.waitForTestId(ACCOUNTS.DETAIL_PANEL)

        // Click Update Balance
        await appPage.testId(ACCOUNTS.BALANCE.UPDATE_BTN).click()

        // Fill balance amount
        const balanceInput = appPage.testId(ACCOUNTS.BALANCE.INPUT)
        await balanceInput.waitFor({ state: 'visible', timeout: 5_000 })
        await balanceInput.fill('5000.25')

        // Click Save (balance)
        await appPage.testId(ACCOUNTS.BALANCE.SAVE_BTN).click()

        // Wait for mutation to complete and UI to refresh
        await appPage.page.waitForTimeout(3_000)

        // UI assertion: verify the latest balance displays in the detail panel
        const balanceDisplay = appPage.testId(ACCOUNTS.BALANCE.LATEST)
        await expect(balanceDisplay).toContainText('5,000.25', { timeout: 10_000 })

        // API assertion: verify the balance was persisted
        const balancesRes = await fetch(
            `${API_BASE}/accounts/${created.account_id}/balances`,
        )
        const balancesBody = (await balancesRes.json()) as {
            items: Array<{ balance: number }>
            total: number
        }
        expect(balancesBody.total).toBeGreaterThanOrEqual(1)
        expect(balancesBody.items[0].balance).toBeCloseTo(5000.25)
    })

    test('edit existing account fields and save', async () => {
        const created = await apiCreate({
            name: `${TEST_PREFIX}Edit`,
            account_type: 'broker',
            institution: 'Original Corp',
            currency: 'USD',
            is_tax_advantaged: false,
            notes: '',
        })
        createdAccountIds.push(created.account_id)

        // Reload and wait
        await appPage.page.reload()
        await appPage.waitForTestId(ACCOUNTS.ROOT)

        const nameLocator = appPage.page
            .getByText(`${TEST_PREFIX}Edit`, { exact: true })
            .first()
        await nameLocator.waitFor({ state: 'visible', timeout: 15_000 })

        // Select the account
        const row = appPage.page
            .locator('[data-testid="account-list"] tbody tr')
            .filter({ hasText: `${TEST_PREFIX}Edit` })
        await row.click()
        await appPage.waitForTestId(ACCOUNTS.DETAIL_PANEL)

        // Edit the name
        const nameInput = appPage.testId(ACCOUNTS.FORM.NAME)
        await nameInput.clear()
        await nameInput.fill(`${TEST_PREFIX}Edited`)

        // Edit institution
        const instInput = appPage.testId(ACCOUNTS.FORM.INSTITUTION)
        await instInput.clear()
        await instInput.fill('Changed Corp')

        // Click Save
        await appPage.testId(ACCOUNTS.FORM.SUBMIT).click()
        await appPage.page.waitForTimeout(2_000)

        // Verify via API
        const accounts = await apiList()
        const edited = accounts.find((a) => a.account_id === created.account_id)
        expect(edited?.name).toBe(`${TEST_PREFIX}Edited`)
    })

    test('delete account with confirmation', async () => {
        const created = await apiCreate({
            name: `${TEST_PREFIX}Delete`,
            account_type: 'ira',
            institution: 'Disposable',
            currency: 'USD',
            is_tax_advantaged: true,
            notes: '',
        })
        // Don't add to cleanup — we're deleting it in the test

        // Reload and wait
        await appPage.page.reload()
        await appPage.waitForTestId(ACCOUNTS.ROOT)

        const nameLocator = appPage.page
            .getByText(`${TEST_PREFIX}Delete`, { exact: true })
            .first()
        await nameLocator.waitFor({ state: 'visible', timeout: 15_000 })

        // Select the account
        const row = appPage.page
            .locator('[data-testid="account-list"] tbody tr')
            .filter({ hasText: `${TEST_PREFIX}Delete` })
        await row.click()
        await appPage.waitForTestId(ACCOUNTS.DETAIL_PANEL)

        // Click Delete
        await appPage.testId(ACCOUNTS.FORM.DELETE).click()

        // Confirm deletion via ConfirmDeleteModal
        await appPage.testId(CONFIRM_DELETE.CONFIRM_BTN).click()
        await appPage.page.waitForTimeout(2_000)

        // Verify via API — account should be gone
        const accounts = await apiList()
        const deleted = accounts.find((a) => a.account_id === created.account_id)
        expect(deleted).toBeUndefined()
    })

    test('dirty-guard: editing account name and switching shows unsaved changes modal', async () => {
        // Create two accounts via API
        const acctA = await apiCreate({
            name: `${TEST_PREFIX}GuardA`,
            account_type: 'broker',
            institution: 'Guard Test Inc',
            currency: 'USD',
            is_tax_advantaged: false,
            notes: '',
        })
        createdAccountIds.push(acctA.account_id)

        const acctB = await apiCreate({
            name: `${TEST_PREFIX}GuardB`,
            account_type: 'bank',
            institution: 'Guard Test Bank',
            currency: 'USD',
            is_tax_advantaged: false,
            notes: '',
        })
        createdAccountIds.push(acctB.account_id)

        // Reload to pick up both accounts
        await appPage.page.reload()
        await appPage.waitForTestId(ACCOUNTS.ROOT)

        // Wait for both accounts to appear
        const nameA = appPage.page.getByText(`${TEST_PREFIX}GuardA`, { exact: true }).first()
        await nameA.waitFor({ state: 'visible', timeout: 15_000 })

        // Select account A
        const rowA = appPage.page
            .locator('[data-testid="account-list"] tbody tr')
            .filter({ hasText: `${TEST_PREFIX}GuardA` })
        await rowA.click()
        await appPage.waitForTestId(ACCOUNTS.DETAIL_PANEL)

        // Edit the name to make it dirty
        const nameInput = appPage.testId(ACCOUNTS.FORM.NAME)
        await nameInput.clear()
        await nameInput.fill(`${TEST_PREFIX}Modified`)
        await appPage.page.waitForTimeout(300)

        // Click account B — should trigger the guard modal
        const rowB = appPage.page
            .locator('[data-testid="account-list"] tbody tr')
            .filter({ hasText: `${TEST_PREFIX}GuardB` })
        await rowB.click()

        // The UnsavedChangesModal should appear
        await appPage.waitForTestId(UNSAVED_CHANGES.MODAL, 5_000)
        const modal = appPage.testId(UNSAVED_CHANGES.MODAL)
        await expect(modal).toBeVisible()

        // Verify modal has expected buttons
        await expect(appPage.testId(UNSAVED_CHANGES.KEEP_EDITING_BTN)).toBeVisible()
        await expect(appPage.testId(UNSAVED_CHANGES.DISCARD_BTN)).toBeVisible()

        // Click Keep Editing — modal should dismiss
        await appPage.testId(UNSAVED_CHANGES.KEEP_EDITING_BTN).click()
        await appPage.page.waitForTimeout(300)

        // Modal should be gone
        await expect(appPage.testId(UNSAVED_CHANGES.MODAL)).not.toBeVisible()
    })
})
