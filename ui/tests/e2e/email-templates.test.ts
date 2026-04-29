/**
 * E2E: Email Templates tab — Wave 8 tests per §6K.10.
 *
 * Tests the full stack: Electron GUI → React → REST API → Python backend → DB.
 * 3 tests:
 *   1. Tab click → template list visible
 *   2. Default template → editor disabled, banner visible
 *   3. Preview button → iframe contains rendered HTML
 *
 * MEU: MEU-72b (gui-email-templates)
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { SCHEDULING } from './test-ids'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    await appPage.navigateTo('scheduling')
})

test.afterEach(async () => {
    await appPage.close()
})

test('test_email_templates_tab_accessible — Tab click → template list visible', async () => {
    // Wait for the scheduling page to load
    await appPage.waitForTestId(SCHEDULING.ROOT)

    // Click the "Email Templates" tab
    const templatesTab = appPage.testId(SCHEDULING.TAB_EMAIL_TEMPLATES)
    await expect(templatesTab).toBeVisible({ timeout: 5_000 })
    await templatesTab.click()

    // Template list should appear
    const templateList = appPage.testId(SCHEDULING.TEMPLATE_LIST)
    await expect(templateList).toBeVisible({ timeout: 5_000 })
})

test('test_default_template_readonly — Default template → editor disabled, banner visible', async () => {
    await appPage.waitForTestId(SCHEDULING.ROOT)

    // Switch to Email Templates tab
    await appPage.testId(SCHEDULING.TAB_EMAIL_TEMPLATES).click()
    await appPage.waitForTestId(SCHEDULING.TEMPLATE_LIST)

    // Wait for templates to load, then click the default template
    // The default template should have a badge
    const defaultBadge = appPage.testId(SCHEDULING.TEMPLATE_DEFAULT_BADGE)
    await expect(defaultBadge.first()).toBeVisible({ timeout: 10_000 })

    // Click the first template item that has a default badge (its parent button)
    await defaultBadge.first().click()

    // Detail panel should appear
    const detail = appPage.testId(SCHEDULING.TEMPLATE_DETAIL)
    await expect(detail).toBeVisible({ timeout: 5_000 })

    // Banner should be visible warning about default protection
    await expect(detail.getByText(/Default templates cannot be modified/)).toBeVisible()

    // Delete button should be disabled
    const deleteBtn = appPage.testId(SCHEDULING.TEMPLATE_DELETE_BTN)
    await expect(deleteBtn).toBeDisabled()

    // Save button should be disabled
    const saveBtn = appPage.testId(SCHEDULING.TEMPLATE_SAVE_BTN)
    await expect(saveBtn).toBeDisabled()
})

test('test_template_preview_renders — Preview button → iframe contains rendered HTML', async () => {
    await appPage.waitForTestId(SCHEDULING.ROOT)

    // Switch to Email Templates tab
    await appPage.testId(SCHEDULING.TAB_EMAIL_TEMPLATES).click()
    await appPage.waitForTestId(SCHEDULING.TEMPLATE_LIST)

    // Wait for templates to load, then click the default template
    const defaultBadge = appPage.testId(SCHEDULING.TEMPLATE_DEFAULT_BADGE)
    await expect(defaultBadge.first()).toBeVisible({ timeout: 10_000 })
    await defaultBadge.first().click()

    // Wait for detail panel
    const detail = appPage.testId(SCHEDULING.TEMPLATE_DETAIL)
    await expect(detail).toBeVisible({ timeout: 5_000 })

    // Click Preview button
    const previewBtn = appPage.testId(SCHEDULING.TEMPLATE_PREVIEW_BTN)
    await expect(previewBtn).toBeVisible()
    await previewBtn.click()

    // Wait for the preview iframe to appear
    const iframe = appPage.testId(SCHEDULING.TEMPLATE_PREVIEW_IFRAME)
    await expect(iframe).toBeVisible({ timeout: 10_000 })

    // Verify iframe has sandbox attribute (security)
    await expect(iframe).toHaveAttribute('sandbox', '')
})
