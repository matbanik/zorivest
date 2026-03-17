/**
 * E2E: Mode-gating — MCP Guard lock/unlock.
 *
 * Verifies that when the MCP Guard is locked, trade creation is blocked
 * in the UI, and when unlocked, it's allowed.
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { SETTINGS, TRADES } from './test-ids'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
})

test.afterEach(async () => {
    await appPage.close()
})

test('locked guard disables trade creation', async () => {
    // Navigate to settings and enable lock
    await appPage.navigateTo('settings')
    await appPage.waitForTestId(SETTINGS.ROOT)

    // Toggle lock ON
    const lockToggle = appPage.testId(SETTINGS.MCP_GUARD.LOCK_TOGGLE)
    await lockToggle.click()

    // Verify lock status shows locked
    const status = appPage.testId(SETTINGS.MCP_GUARD.STATUS)
    await expect(status).toContainText(/locked/i)

    // Navigate to trades — add button should be disabled
    await appPage.navigateTo('trades')
    await appPage.waitForTestId(TRADES.ROOT)

    const addButton = appPage.testId(TRADES.ADD_BUTTON)
    await expect(addButton).toBeDisabled()
})

test('unlocked guard allows trade creation', async () => {
    // Navigate to settings and ensure unlock
    await appPage.navigateTo('settings')
    await appPage.waitForTestId(SETTINGS.ROOT)

    // Verify status shows unlocked (default state)
    const status = appPage.testId(SETTINGS.MCP_GUARD.STATUS)
    await expect(status).toContainText(/unlocked/i)

    // Navigate to trades — add button should be enabled
    await appPage.navigateTo('trades')
    await appPage.waitForTestId(TRADES.ROOT)

    const addButton = appPage.testId(TRADES.ADD_BUTTON)
    await expect(addButton).toBeEnabled()
})
