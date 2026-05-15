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
    // Intercept the wash-sales API to return deterministic chain data.
    // This proves the chain→detail rendering path independently of backend state.
    const mockWashSales = {
        chains: [
            {
                chain_id: 'e2e-chain-001',
                ticker: 'TSLA',
                adjustment_amount: -500,
                trade_count: 3,
                first_trade_date: '2026-01-10',
                last_trade_date: '2026-02-05',
                status: 'active',
                trades: [
                    { exec_id: 'e1', date: '2026-01-10', action: 'SLD', quantity: 50, price: 200, wash_amount: 300 },
                    { exec_id: 'e2', date: '2026-01-25', action: 'BOT', quantity: 50, price: 180, wash_amount: 200 },
                ],
            },
        ],
        disallowed_total: 500,
        affected_tickers: ['TSLA'],
    }

    await appPage.page.route('**/api/v1/tax/wash-sales', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockWashSales),
        })
    })

    // Navigate to wash sales tab (re-triggers the intercepted fetch)
    await appPage.page.locator('[data-testid="tax-tab-wash-sales"]').click()
    await appPage.page.waitForTimeout(1000)

    await appPage.waitForTestId(TAX.WASH_SALE_MONITOR)

    // The intercepted data guarantees at least one chain is present
    const chains = appPage.testId(TAX.WASH_SALE_CHAIN)
    await expect(chains.first()).toBeVisible({ timeout: 5000 })
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
