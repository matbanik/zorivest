/**
 * E2E Wave 11: Tax Lot Viewer.
 *
 * Gate MEU: MEU-154 (gui-tax)
 * Tests: Lot table renders, sort/filter present, disabled close/reassign buttons.
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
    // Switch to Lots tab
    await appPage.page.locator('[data-testid="tax-tab-lots"]').click()
    await appPage.page.waitForTimeout(500)
})

test.afterEach(async () => {
    await appPage.close()
})

test('lots tab renders lot viewer container', async () => {
    await appPage.waitForTestId(TAX.LOT_VIEWER)
    const viewer = appPage.testId(TAX.LOT_VIEWER)
    await expect(viewer).toBeVisible()
})

test('close-lot button exists per lot row and is disabled', async () => {
    await appPage.waitForTestId(TAX.LOT_VIEWER)
    const lotRows = appPage.testId(TAX.LOT_ROW)
    const rowCount = await lotRows.count()

    if (rowCount === 0) {
        // No lots in DB — buttons only render per-row, so none expected
        const closeBtn = appPage.testId(TAX.LOT_CLOSE_BTN)
        expect(await closeBtn.count()).toBe(0)
        return
    }

    // Each lot row has a Close button
    const closeBtn = appPage.testId(TAX.LOT_CLOSE_BTN)
    const count = await closeBtn.count()
    expect(count).toBe(rowCount)
    for (let i = 0; i < count; i++) {
        await expect(closeBtn.nth(i)).toBeDisabled()
    }
})

test('reassign-method button exists per lot row and is disabled', async () => {
    await appPage.waitForTestId(TAX.LOT_VIEWER)
    const lotRows = appPage.testId(TAX.LOT_ROW)
    const rowCount = await lotRows.count()

    if (rowCount === 0) {
        // No lots in DB — buttons only render per-row, so none expected
        const reassignBtn = appPage.testId(TAX.LOT_REASSIGN_BTN)
        expect(await reassignBtn.count()).toBe(0)
        return
    }

    // Each lot row has a Reassign button
    const reassignBtn = appPage.testId(TAX.LOT_REASSIGN_BTN)
    const count = await reassignBtn.count()
    expect(count).toBe(rowCount)
    for (let i = 0; i < count; i++) {
        await expect(reassignBtn.nth(i)).toBeDisabled()
    }
})
