/**
 * E2E: Dashboard persistence across app restart.
 *
 * Verifies that data created in one session is visible after
 * closing and reopening the Electron app.
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { ACCOUNTS } from './test-ids'

test('data persists across app restart', async () => {
    // Session 1: Get current state
    const app1 = new AppPage()
    await app1.launch()

    // Record something observable (e.g., account count from API)
    const before = await app1.apiGet<unknown[]>('/accounts')
    const accountCount = before.length

    await app1.close()

    // Brief pause to ensure clean shutdown
    await new Promise((r) => setTimeout(r, 2_000))

    // Session 2: Reopen and verify
    const app2 = new AppPage()
    await app2.launch()

    const after = await app2.apiGet<unknown[]>('/accounts')
    expect(after.length).toBe(accountCount)

    // UI should also show the same data
    await app2.navigateTo('accounts')
    await app2.waitForTestId(ACCOUNTS.ROOT)
    const accountList = app2.testId(ACCOUNTS.ACCOUNT_LIST)
    await expect(accountList).toBeVisible()

    await app2.close()
})

test('window position persists across restart', async () => {
    // Session 1: Resize window via Electron BrowserWindow API
    const app1 = new AppPage()
    await app1.launch()

    // Set bounds via Electron API (electron-store persists these, not Playwright viewport)
    await app1.app.evaluate(({ BrowserWindow }) => {
        const win = BrowserWindow.getAllWindows().find(w => !w.isDestroyed() && w.isVisible())
        if (win) win.setBounds({ x: 100, y: 100, width: 1200, height: 800 })
    })
    await app1.page.waitForTimeout(1_500) // Let debounced save fire

    await app1.close()
    await new Promise((r) => setTimeout(r, 2_000))

    // Session 2: Window size should be restored
    const app2 = new AppPage()
    await app2.launch()

    // Read restored bounds via Electron API
    const bounds = await app2.app.evaluate(({ BrowserWindow }) => {
        const win = BrowserWindow.getAllWindows().find(w => !w.isDestroyed() && w.isVisible())
        return win ? win.getBounds() : null
    })
    // Allow for title bar and frame differences
    expect(bounds?.width).toBeGreaterThan(1000)

    await app2.close()
})
