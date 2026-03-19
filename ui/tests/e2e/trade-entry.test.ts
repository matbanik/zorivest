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

    // Verify AAPL specifically appears in a trade row (not just count > 0)
    const tradeRows = appPage.testId(TRADES.TRADE_ROW)
    const count = await tradeRows.count()
    expect(count).toBeGreaterThan(0)

    // Find the row containing 'AAPL'
    const aaplRow = tradeRows.filter({ hasText: 'AAPL' })
    await expect(aaplRow).toHaveCount(1)
})

test('created trade persists in API', async () => {
    // Cross-check: query the API directly for trades
    const trades = await appPage.apiGet<{ items: Array<{ instrument?: string }>; total: number; limit: number; offset: number }>('/trades')
    expect(trades.items).toBeDefined()
    expect(Array.isArray(trades.items)).toBe(true)

    // Verify AAPL specifically exists in the API response
    const aaplTrade = trades.items.find((t) => t.instrument === 'AAPL')
    expect(aaplTrade).toBeDefined()
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
