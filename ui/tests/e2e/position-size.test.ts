/**
 * E2E: Position sizing calculator.
 *
 * Tests that calculator inputs produce correct position size output.
 */

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { AppPage } from './pages/AppPage'
import { CALCULATOR } from './test-ids'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    // Navigate to settings or planning where calculator lives
    await appPage.navigateTo('planning')
})

test.afterEach(async () => {
    await appPage.close()
})

test('calculator produces correct position size', async () => {
    // Fill in calculator fields
    await appPage.testId(CALCULATOR.ACCOUNT_SIZE).fill('100000')
    await appPage.testId(CALCULATOR.RISK_PERCENT).fill('2')
    await appPage.testId(CALCULATOR.ENTRY_PRICE).fill('150')
    await appPage.testId(CALCULATOR.STOP_PRICE).fill('145')

    // Wait for calculation
    await appPage.page.waitForTimeout(500)

    // Verify result: $100K × 2% = $2,000 risk / ($150 - $145) = 400 shares
    const shares = await appPage.testId(CALCULATOR.RESULT_SHARES).textContent()
    expect(Number(shares)).toBe(400)

    const dollarRisk = await appPage.testId(CALCULATOR.RESULT_DOLLAR_RISK).textContent()
    expect(dollarRisk).toContain('2,000')
})

test('calculator page has no accessibility violations', async () => {
    const results = await new AxeBuilder({ page: appPage.page }).analyze()
    expect(results.violations).toEqual([])
})
