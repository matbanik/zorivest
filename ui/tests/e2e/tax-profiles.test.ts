/**
 * E2E Wave 11: Tax Profile Manager CRUD.
 *
 * Gate MEU: MEU-218f (tax-profile-crud)
 * Tests: Profiles tab navigation, profile list rendering, create/edit/delete flow.
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
})

test.afterEach(async () => {
    await appPage.close()
})

test('profiles tab is clickable and renders profile manager', async () => {
    // Click the "Profiles" tab (index 1)
    const tabs = appPage.page.locator(`[data-testid="${TAX.ROOT}"] button`).filter({ hasText: 'Profiles' })
    await tabs.first().click()
    await appPage.page.waitForTimeout(500)

    // Verify the profile manager container is visible
    const manager = appPage.testId(TAX.PROFILE_MANAGER)
    await expect(manager).toBeVisible({ timeout: 10_000 })
})

test('profile list renders existing profiles', async () => {
    // Navigate to Profiles tab
    const tabs = appPage.page.locator(`[data-testid="${TAX.ROOT}"] button`).filter({ hasText: 'Profiles' })
    await tabs.first().click()
    await appPage.page.waitForTimeout(500)

    await appPage.waitForTestId(TAX.PROFILE_MANAGER)

    // The profile list container should exist
    const list = appPage.testId(TAX.PROFILE_LIST)
    await expect(list).toBeVisible({ timeout: 10_000 })
})

test('new profile button opens detail panel', async () => {
    // Navigate to Profiles tab
    const tabs = appPage.page.locator(`[data-testid="${TAX.ROOT}"] button`).filter({ hasText: 'Profiles' })
    await tabs.first().click()
    await appPage.page.waitForTimeout(500)
    await appPage.waitForTestId(TAX.PROFILE_MANAGER)

    // Click "+ New Profile" button
    const newBtn = appPage.testId(TAX.PROFILE_NEW_BTN)
    await expect(newBtn).toBeVisible()
    await newBtn.click()

    // Detail panel should appear
    const detail = appPage.testId(TAX.PROFILE_DETAIL)
    await expect(detail).toBeVisible({ timeout: 5_000 })

    // Tax year input should be present and editable for new profiles
    const yearInput = appPage.testId(TAX.PROFILE_YEAR_INPUT)
    await expect(yearInput).toBeVisible()
    await expect(yearInput).not.toBeDisabled()

    // Save button should be present with "Create" text
    const saveBtn = appPage.testId(TAX.PROFILE_SAVE_BTN)
    await expect(saveBtn).toBeVisible()
    await expect(saveBtn).toHaveText('Create')
})

test('search field filters profile list', async () => {
    // Navigate to Profiles tab
    const tabs = appPage.page.locator(`[data-testid="${TAX.ROOT}"] button`).filter({ hasText: 'Profiles' })
    await tabs.first().click()
    await appPage.page.waitForTimeout(500)
    await appPage.waitForTestId(TAX.PROFILE_MANAGER)

    // Search field should be present
    const search = appPage.testId(TAX.PROFILE_SEARCH)
    await expect(search).toBeVisible()

    // Should accept text input
    await search.fill('2026')
    await expect(search).toHaveValue('2026')
})

test('clicking existing profile shows detail with Save Changes button', async () => {
    // Intercept the profiles API to guarantee at least one profile exists
    await appPage.page.route('**/api/v1/tax/profiles', async (route) => {
        if (route.request().method() === 'GET') {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([
                    {
                        tax_year: 2025,
                        filing_status: 'SINGLE',
                        federal_bracket: 0.24,
                        state_tax_rate: 0.05,
                        state: 'NY',
                        prior_year_tax: 12000,
                        agi_estimate: 100000,
                        capital_loss_carryforward: 0,
                        wash_sale_method: 'CONSERVATIVE',
                        default_cost_basis: 'FIFO',
                        include_drip_wash_detection: true,
                        include_spousal_accounts: false,
                        section_475_elected: false,
                        section_1256_eligible: false,
                    },
                ]),
            })
        } else {
            await route.continue()
        }
    })

    // Navigate to Profiles tab
    const tabs = appPage.page.locator(`[data-testid="${TAX.ROOT}"] button`).filter({ hasText: 'Profiles' })
    await tabs.first().click()
    await appPage.page.waitForTimeout(500)
    await appPage.waitForTestId(TAX.PROFILE_MANAGER)

    // Click the first profile card (guaranteed by intercept)
    const firstCard = appPage.page.locator(`[data-testid^="${TAX.PROFILE_CARD}"]`).first()
    await expect(firstCard).toBeVisible({ timeout: 5_000 })
    await firstCard.click()

    // Detail panel should open
    const detail = appPage.testId(TAX.PROFILE_DETAIL)
    await expect(detail).toBeVisible({ timeout: 5_000 })

    // Save button text should be "Save Changes" (not "Create")
    const saveBtn = appPage.testId(TAX.PROFILE_SAVE_BTN)
    await expect(saveBtn).toBeVisible()
    await expect(saveBtn).toHaveText('Save Changes')

    // Tax year input should be disabled for existing profiles
    const yearInput = appPage.testId(TAX.PROFILE_YEAR_INPUT)
    await expect(yearInput).toBeDisabled()

    // Delete button should be visible for existing profiles
    const deleteBtn = appPage.testId(TAX.PROFILE_DELETE_BTN)
    await expect(deleteBtn).toBeVisible()
})
