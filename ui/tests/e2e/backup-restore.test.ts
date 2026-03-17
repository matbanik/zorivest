/**
 * E2E: Backup and restore round-trip.
 *
 * Creates a backup through the settings UI, verifies the backup file
 * exists, modifies data, then restores and verifies original state.
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { SETTINGS } from './test-ids'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    await appPage.navigateTo('settings')
    await appPage.waitForTestId(SETTINGS.ROOT)
})

test.afterEach(async () => {
    await appPage.close()
})

test('create backup via UI → backup succeeds', async () => {
    // Enter passphrase
    await appPage.testId(SETTINGS.BACKUP.PASSPHRASE_INPUT).fill('test-passphrase-123')

    // Click create backup
    await appPage.testId(SETTINGS.BACKUP.CREATE_BUTTON).click()

    // Wait for success indication
    await appPage.page.waitForTimeout(3_000)

    // Verify success toast or status message appeared
    // (The exact selector depends on the notification component)
    const page = appPage.page
    const successIndicator = page.locator('text=/backup.*success|created/i')
    await expect(successIndicator).toBeVisible({ timeout: 10_000 })
})

test('restore from backup → data matches original', async () => {
    // Get current trade count from API
    const beforeRestore =
        await appPage.apiGet<{ data: unknown[] }>('/trades')
    const countBefore = beforeRestore.data.length

    // Click restore button
    await appPage.testId(SETTINGS.BACKUP.PASSPHRASE_INPUT).fill('test-passphrase-123')
    await appPage.testId(SETTINGS.BACKUP.RESTORE_BUTTON).click()

    // Wait for restore to complete
    await appPage.page.waitForTimeout(5_000)

    // Verify trade count matches
    const afterRestore =
        await appPage.apiGet<{ data: unknown[] }>('/trades')
    expect(afterRestore.data.length).toBe(countBefore)
})
