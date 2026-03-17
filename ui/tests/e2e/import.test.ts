/**
 * E2E: CSV import flow — file → import → trades in DB.
 *
 * Tests the import workflow: select a CSV file, trigger import,
 * verify trades appear in the database.
 */

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { AppPage } from './pages/AppPage'
import { IMPORT, TRADES } from './test-ids'
import { resolve } from 'path'

let appPage: AppPage

// Path to test fixture CSV
const FIXTURE_CSV = resolve(__dirname, 'fixtures/sample-trades.csv')

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
})

test.afterEach(async () => {
    await appPage.close()
})

test('import CSV file → trades appear in DB', async () => {
    // Navigate to import flow (may be in trades or settings)
    await appPage.navigateTo('trades')
    await appPage.waitForTestId(TRADES.ROOT)

    // Set file input (Playwright can set file inputs directly)
    const fileInput = appPage.testId(IMPORT.FILE_INPUT)
    await fileInput.setInputFiles(FIXTURE_CSV)

    // Select format
    await appPage.testId(IMPORT.FORMAT_SELECT).selectOption('csv')

    // Submit
    await appPage.testId(IMPORT.SUBMIT).click()

    // Wait for import to complete
    await appPage.page.waitForTimeout(5_000)

    // Verify result count is shown
    const resultCount = appPage.testId(IMPORT.RESULT_COUNT)
    const countText = await resultCount.textContent()
    expect(Number(countText)).toBeGreaterThan(0)

    // Cross-check via API
    const trades = await appPage.apiGet<{ data: unknown[] }>('/trades')
    expect(trades.data.length).toBeGreaterThan(0)
})

test('import page has no accessibility violations', async () => {
    await appPage.navigateTo('trades')
    await appPage.waitForTestId(TRADES.ROOT)
    const results = await new AxeBuilder({ page: appPage.page }).analyze()
    expect(results.violations).toEqual([])
})
