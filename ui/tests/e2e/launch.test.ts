/**
 * E2E: App launch + health check.
 *
 * Validates that the Electron app launches successfully and the
 * Python backend responds to health checks.
 */

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { AppPage } from './pages/AppPage'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
})

test.afterEach(async () => {
    await appPage.close()
})

test('app launches and shows main window', async () => {
    // Main window should be visible after splash closes
    const title = await appPage.page.title()
    expect(title).toBeTruthy()

    // The page should have rendered content
    const body = appPage.page.locator('body')
    await expect(body).toBeVisible()
})

test('backend health check returns OK', async () => {
    const healthy = await appPage.isBackendHealthy()
    expect(healthy).toBe(true)
})

test('main page has no accessibility violations', async () => {
    const results = await new AxeBuilder({ page: appPage.page }).analyze()
    expect(results.violations).toEqual([])
})
