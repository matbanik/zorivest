/**
 * E2E Wave 11: What-If Tax Simulator.
 *
 * Gate MEU: MEU-154 (gui-tax)
 * Tests: Simulator form renders, ticker select works, result section appears.
 *
 * The ticker field is a <select> populated from open tax lots via /api/v1/tax/lots.
 * Tests intercept the lots API to inject deterministic ticker options.
 *
 * These tests require the Electron app + Python backend running.
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { TAX } from './test-ids'

let appPage: AppPage

/** Inject mock lot data so the ticker <select> is enabled with options. */
async function injectMockLots(page: AppPage['page']) {
    const mockLots = {
        lots: [
            {
                lot_id: 'lot-spy-001',
                ticker: 'SPY',
                quantity: 100,
                cost_basis: 42000,
                proceeds: 0,
                wash_sale_adjustment: 0,
                is_closed: false,
                open_date: '2025-06-01',
                close_date: null,
                linked_trade_ids: ['t1'],
                cost_basis_method: 'FIFO',
                realized_gain_loss: 0,
                acquisition_source: null,
                account_id: 'acct-001',
                materialized_at: null,
                is_user_modified: false,
                source_hash: null,
                sync_status: 'synced',
            },
        ],
        total_count: 1,
    }

    await page.route('**/api/v1/tax/lots**', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockLots),
        })
    })
}

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()

    // Inject mock lots BEFORE navigating to tax (so the simulator query picks them up)
    await injectMockLots(appPage.page)

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

    // Ticker is a <select> — wait for it to be enabled (lots loaded)
    const tickerSelect = appPage.testId(TAX.WHAT_IF_TICKER_INPUT)
    await expect(tickerSelect).toBeEnabled({ timeout: 10_000 })

    // Select SPY from the dropdown (injected by mock lots)
    await tickerSelect.selectOption({ value: 'SPY' })

    const quantityInput = appPage.testId(TAX.WHAT_IF_QUANTITY)
    await quantityInput.fill('100')

    const priceInput = appPage.testId(TAX.WHAT_IF_PRICE)
    await priceInput.fill('450')

    // Verify inputs retained their values
    await expect(tickerSelect).toHaveValue('SPY')
    await expect(quantityInput).toHaveValue('100')
    await expect(priceInput).toHaveValue('450')

    // Submit button should be enabled with all fields filled
    const submitBtn = appPage.testId(TAX.WHAT_IF_SUBMIT)
    await expect(submitBtn).toBeEnabled()
})

test('submitting simulation renders result panel with intercepted data', async () => {
    // Intercept the simulate API call to return deterministic mock data.
    // Field names match the WhatIfSimulator interface: total_st_gain, total_lt_gain, etc.
    const mockResult = {
        ticker: 'SPY',
        quantity: 100,
        price: 450,
        total_st_gain: 1000,
        total_lt_gain: 2000,
        estimated_tax: 750,
        wash_risk: false,
        wash_sale_warnings: [],
        wait_days: 0,
        lot_details: [],
    }

    await appPage.page.route('**/api/v1/tax/simulate', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockResult),
        })
    })

    await appPage.waitForTestId(TAX.WHAT_IF_SIMULATOR)

    // Ticker is a <select> — wait for it to be enabled
    const tickerSelect = appPage.testId(TAX.WHAT_IF_TICKER_INPUT)
    await expect(tickerSelect).toBeEnabled({ timeout: 10_000 })
    await tickerSelect.selectOption({ value: 'SPY' })

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
    expect(resultText).toContain('1,000')    // total_st_gain
    expect(resultText).toContain('2,000')    // total_lt_gain
    expect(resultText).toContain('750')      // estimated_tax
})
