/**
 * E2E Wave 11: What-If Tax Simulator.
 *
 * Gate MEU: MEU-154 (gui-tax)
 * Tests: Simulator form renders, ticker input works, result section appears.
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
    // Switch to Simulator tab
    await appPage.page.locator('[data-testid="tax-tab-simulator"]').click()
    await appPage.page.waitForTimeout(500)
})

test.afterEach(async () => {
    await appPage.close()
})

test('simulator tab renders simulator container', async () => {
    await appPage.waitForTestId(TAX.WHAT_IF_SIMULATOR)
    const simulator = appPage.testId(TAX.WHAT_IF_SIMULATOR)
    await expect(simulator).toBeVisible()
})

test('simulator has ticker input field', async () => {
    await appPage.waitForTestId(TAX.WHAT_IF_SIMULATOR)
    const tickerInput = appPage.testId(TAX.WHAT_IF_TICKER_INPUT)
    await expect(tickerInput).toBeVisible()
})

test('simulator form accepts input and submit button state reflects validation', async () => {
    await appPage.waitForTestId(TAX.WHAT_IF_SIMULATOR)

    // Fill in the simulation form fields
    const tickerInput = appPage.testId(TAX.WHAT_IF_TICKER_INPUT)
    await tickerInput.fill('SPY')

    const quantityInput = appPage.testId(TAX.WHAT_IF_QUANTITY)
    await quantityInput.fill('100')

    const priceInput = appPage.testId(TAX.WHAT_IF_PRICE)
    await priceInput.fill('450')

    // Verify inputs retained their values
    await expect(tickerInput).toHaveValue('SPY')
    await expect(quantityInput).toHaveValue('100')
    await expect(priceInput).toHaveValue('450')

    // Submit button should be enabled with all fields filled
    const submitBtn = appPage.testId(TAX.WHAT_IF_SUBMIT)
    await expect(submitBtn).toBeEnabled()
})

test('submitting simulation renders result panel with intercepted data', async () => {
    // Intercept the simulate API call to return deterministic mock data.
    // This proves the success-path rendering independently of backend state.
    const mockResult = {
        ticker: 'SPY',
        quantity: 100,
        price: 450,
        total_proceeds: 45000,
        total_cost_basis: 42000,
        realized_pnl: 3000,
        short_term_gain: 1000,
        long_term_gain: 2000,
        estimated_tax: 750,
        wash_sale_risk: false,
        lot_breakdown: [],
    }

    await appPage.page.route('**/api/v1/tax/simulate', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockResult),
        })
    })

    await appPage.waitForTestId(TAX.WHAT_IF_SIMULATOR)

    // Fill form with valid data
    await appPage.testId(TAX.WHAT_IF_TICKER_INPUT).fill('SPY')
    await appPage.testId(TAX.WHAT_IF_QUANTITY).fill('100')
    await appPage.testId(TAX.WHAT_IF_PRICE).fill('450')

    // Click submit to trigger the intercepted API call
    const submitBtn = appPage.testId(TAX.WHAT_IF_SUBMIT)
    await submitBtn.click()

    // Wait for the result panel to appear (intercepted response is instant)
    const resultPanel = appPage.testId(TAX.WHAT_IF_RESULT)
    await expect(resultPanel).toBeVisible({ timeout: 5000 })

    // Assert the result panel contains expected values from the mock
    const resultText = await resultPanel.textContent()
    expect(resultText).toContain('3,000')    // realized_pnl
    expect(resultText).toContain('750')       // estimated_tax
})
