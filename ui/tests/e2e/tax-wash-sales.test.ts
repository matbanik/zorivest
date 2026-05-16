/**
 * E2E Wave 11: Wash Sale Monitor.
 *
 * Gate MEU: MEU-154 (gui-tax)
 * Tests: Monitor renders, chain list/detail pattern.
 *
 * These tests require the Electron app + Python backend running.
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { TAX } from './test-ids'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    await appPage.navigateTo('tax')
    // Switch to Wash Sales tab
    await appPage.page.locator('[data-testid="tax-tab-wash-sales"]').click()
    await appPage.page.waitForTimeout(500)
})

test.afterEach(async () => {
    await appPage.close()
})

test('wash sales tab renders monitor container', async () => {
    await appPage.waitForTestId(TAX.WASH_SALE_MONITOR)
    const monitor = appPage.testId(TAX.WASH_SALE_MONITOR)
    await expect(monitor).toBeVisible()
})

test('wash sale monitor shows chains or empty state', async () => {
    await appPage.waitForTestId(TAX.WASH_SALE_MONITOR)
    const monitor = appPage.testId(TAX.WASH_SALE_MONITOR)
    const text = await monitor.textContent()
    // Must contain either the heading "Wash Sale Monitor" or chain data
    expect(text).toContain('Wash Sale')
})

test('chain detail panel renders with intercepted chain data', async () => {
    // Intercept the wash-sales POST API to return deterministic chain data.
    // Mock matches the WashSaleChain interface used by WashSaleMonitor.tsx.
    const mockChains: object[] = [
        {
            chain_id: 'e2e-chain-001',
            ticker: 'TSLA',
            loss_lot_id: 'lot-tsla-001',
            loss_date: '2026-01-10',
            loss_amount: -800,
            disallowed_amount: 500,
            status: 'ABSORBED',
            loss_open_date: '2025-11-15',
            entries: [
                {
                    entry_id: 'ent-1',
                    chain_id: 'e2e-chain-001',
                    event_type: 'LOSS_DISALLOWED',
                    lot_id: 'lot-tsla-001',
                    amount: 500,
                    event_date: '2026-01-10',
                    account_id: 'acct-001',
                },
                {
                    entry_id: 'ent-2',
                    chain_id: 'e2e-chain-001',
                    event_type: 'BASIS_ADJUSTED',
                    lot_id: 'lot-tsla-002',
                    amount: 500,
                    event_date: '2026-01-25',
                    account_id: 'acct-001',
                },
            ],
        },
    ]

    // Set up route intercept — fulfills any /wash-sales request
    await appPage.page.route('**/api/v1/tax/wash-sales', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockChains),
        })
    })

    // Switch to Dashboard first to ensure Wash Sales tab triggers a fresh fetch
    await appPage.page.locator(`[data-testid="${TAX.ROOT}"] button`).filter({ hasText: 'Dashboard' }).first().click()
    await appPage.page.waitForTimeout(300)

    // Now switch to Wash Sales — this triggers the POST fetch which hits our intercept
    await appPage.page.locator('[data-testid="tax-tab-wash-sales"]').click()
    await appPage.page.waitForTimeout(2000)

    await appPage.waitForTestId(TAX.WASH_SALE_MONITOR)

    // The intercepted data guarantees at least one chain is present
    const chains = appPage.testId(TAX.WASH_SALE_CHAIN)
    await expect(chains.first()).toBeVisible({ timeout: 15_000 })
    const count = await chains.count()
    expect(count).toBeGreaterThan(0)

    // Click the first chain to open the detail panel
    await chains.first().click()
    await appPage.page.waitForTimeout(500)

    // Assert the detail panel is visible and contains the mock chain's ticker
    const detail = appPage.testId(TAX.WASH_SALE_CHAIN_DETAIL)
    await expect(detail).toBeVisible()
    const detailText = await detail.textContent()
    expect(detailText).toContain('TSLA')
    expect(detailText!.length).toBeGreaterThan(10)
})
