/**
 * E2E Wave 11: Quarterly Estimated Tax Tracker.
 *
 * Gate MEU: MEU-154 (gui-tax)
 * Tests: Tracker renders, quarter cards visible, payment entry input present.
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
    // Switch to Quarterly tab
    await appPage.page.locator('[data-testid="tax-tab-quarterly"]').click()
    await appPage.page.waitForTimeout(500)
})

test.afterEach(async () => {
    await appPage.close()
})

test('quarterly tab renders tracker container', async () => {
    await appPage.waitForTestId(TAX.QUARTERLY_TRACKER)
    const tracker = appPage.testId(TAX.QUARTERLY_TRACKER)
    await expect(tracker).toBeVisible()
})

test('quarterly tracker renders payment input', async () => {
    await appPage.waitForTestId(TAX.QUARTERLY_TRACKER)
    const paymentInput = appPage.testId(TAX.QUARTERLY_PAYMENT_INPUT)
    await expect(paymentInput).toBeVisible()
})

test('quarterly tracker renders submit button', async () => {
    await appPage.waitForTestId(TAX.QUARTERLY_TRACKER)
    const submitBtn = appPage.testId(TAX.QUARTERLY_PAYMENT_SUBMIT)
    await expect(submitBtn).toBeVisible()
})

test('payment input accepts numeric value', async () => {
    await appPage.waitForTestId(TAX.QUARTERLY_TRACKER)
    const paymentInput = appPage.testId(TAX.QUARTERLY_PAYMENT_INPUT)
    await paymentInput.fill('5000')

    // Verify the value was accepted
    await expect(paymentInput).toHaveValue('5000')
})
