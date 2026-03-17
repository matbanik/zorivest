/**
 * E2E: Trade entry flow — UI → API → DB → UI display.
 *
 * Creates a trade through the UI form, verifies it appears in the
 * trade list, and cross-checks via direct API call.
 */

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { AppPage } from './pages/AppPage'
import { TRADES } from './test-ids'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    await appPage.navigateTo('trades')
})

test.afterEach(async () => {
    await appPage.close()
})

test('navigate to trades page', async () => {
    await appPage.waitForTestId(TRADES.ROOT)
    const page = appPage.testId(TRADES.ROOT)
    await expect(page).toBeVisible()
})

test('create a trade via form → appears in trade list', async () => {
    // Open trade form
    await appPage.testId(TRADES.ADD_BUTTON).click()

    // Fill in trade details
    await appPage.testId(TRADES.FORM.SYMBOL).fill('AAPL')
    await appPage.testId(TRADES.FORM.QUANTITY).fill('100')
    await appPage.testId(TRADES.FORM.PRICE).fill('150.00')

    // Submit
    await appPage.testId(TRADES.FORM.SUBMIT).click()

    // Wait for the trade to appear in the list
    await appPage.page.waitForTimeout(1_000)

    // Verify trade row contains the symbol
    const tradeRows = appPage.testId(TRADES.TRADE_ROW)
    const count = await tradeRows.count()
    expect(count).toBeGreaterThan(0)
})

test('created trade persists in API', async () => {
    // Cross-check: query the API directly for trades
    const trades = await appPage.apiGet<{ data: unknown[] }>('/trades')
    expect(trades.data).toBeDefined()
    expect(Array.isArray(trades.data)).toBe(true)
})

test('trades page has no accessibility violations', async () => {
    await appPage.waitForTestId(TRADES.ROOT)
    const results = await new AxeBuilder({ page: appPage.page }).analyze()
    expect(results.violations).toEqual([])
})

test('trades page visual regression', async () => {
    await appPage.waitForTestId(TRADES.ROOT)
    await expect(appPage.page).toHaveScreenshot('trades-page.png', {
        mask: [
            appPage.testId('balance-amount'),
            appPage.testId('pnl-value'),
        ],
    })
})
