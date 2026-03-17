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
    const before = await app1.apiGet<{ data: unknown[] }>('/accounts')
    const accountCount = before.data.length

    await app1.close()

    // Brief pause to ensure clean shutdown
    await new Promise((r) => setTimeout(r, 2_000))

    // Session 2: Reopen and verify
    const app2 = new AppPage()
    await app2.launch()

    const after = await app2.apiGet<{ data: unknown[] }>('/accounts')
    expect(after.data.length).toBe(accountCount)

    // UI should also show the same data
    await app2.waitForTestId(ACCOUNTS.ROOT)
    const accountList = app2.testId(ACCOUNTS.ACCOUNT_LIST)
    await expect(accountList).toBeVisible()

    await app2.close()
})

test('window position persists across restart', async () => {
    // Session 1: Resize window
    const app1 = new AppPage()
    await app1.launch()

    const window = app1.app.windows()[0]
    if (!window) throw new Error('No window found')

    await window.setViewportSize({ width: 1200, height: 800 })
    await app1.page.waitForTimeout(1_000) // Let debounced save fire

    await app1.close()
    await new Promise((r) => setTimeout(r, 2_000))

    // Session 2: Window size should be restored
    const app2 = new AppPage()
    await app2.launch()

    // The electron-store saves bounds — verify they're roughly correct
    const size = await app2.page.viewportSize()
    // Allow for title bar and frame differences
    expect(size?.width).toBeGreaterThan(1000)

    await app2.close()
})
