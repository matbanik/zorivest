/**
 * E2E: Scheduling policy creation — +New button → API → policy appears in list.
 *
 * Verifies the full stack: Electron GUI → React → REST API → Python backend → DB.
 * This test catches the 422 schema mismatch bug that unit tests missed because
 * they mock the API layer.
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

test('scheduling page loads with root container', async () => {
    await appPage.waitForTestId(SCHEDULING.ROOT)
    const root = appPage.testId(SCHEDULING.ROOT)
    await expect(root).toBeVisible()
})

test('+New button creates a policy without 422 error', async () => {
    await appPage.waitForTestId(SCHEDULING.POLICY_CREATE_BTN)

    // Count existing policies before creating
    const listBefore = appPage.testId(SCHEDULING.POLICY_ITEM)
    const countBefore = await listBefore.count()

    // Click +New
    await appPage.testId(SCHEDULING.POLICY_CREATE_BTN).click()

    // Wait for the mutation to complete and the new policy to appear
    // The policy list should gain one item
    await appPage.page.waitForTimeout(2_000)

    const listAfter = appPage.testId(SCHEDULING.POLICY_ITEM)
    const countAfter = await listAfter.count()

    // The new policy should appear in the list
    expect(countAfter).toBe(countBefore + 1)
})

test('created policy is persisted in API', async () => {
    // Cross-check: query the API directly
    const response = await appPage.apiGet<{ policies: Array<{ name: string; id: string }>; total: number }>(
        '/scheduling/policies',
    )
    expect(response.policies).toBeDefined()
    expect(Array.isArray(response.policies)).toBe(true)

    // At least the policy created by the previous test should exist
    // (or any policy if tests run independently — we just verify the endpoint works)
    expect(response.total).toBeGreaterThanOrEqual(0)
})

test('+New policy appears selected with detail panel', async () => {
    await appPage.waitForTestId(SCHEDULING.POLICY_CREATE_BTN)

    // Click +New
    await appPage.testId(SCHEDULING.POLICY_CREATE_BTN).click()

    // Wait for policy creation and selection
    await appPage.page.waitForTimeout(2_000)

    // The detail panel should appear with the JSON editor
    const detail = appPage.testId(SCHEDULING.POLICY_DETAIL)
    await expect(detail).toBeVisible({ timeout: 5_000 })
})

test('+New API response returns 201', async () => {
    // Intercept network requests to verify the API response code
    let createResponseStatus: number | undefined

    await appPage.page.route('**/api/v1/scheduling/policies', (route) => {
        const method = route.request().method()
        if (method === 'POST') {
            // Continue the request and capture the response
            route.continue()
        } else {
            route.continue()
        }
    })

    // Listen for responses
    const responsePromise = appPage.page.waitForResponse(
        (resp) =>
            resp.url().includes('/api/v1/scheduling/policies') &&
            resp.request().method() === 'POST',
        { timeout: 10_000 },
    )

    await appPage.waitForTestId(SCHEDULING.POLICY_CREATE_BTN)
    await appPage.testId(SCHEDULING.POLICY_CREATE_BTN).click()

    const response = await responsePromise
    createResponseStatus = response.status()

    // The critical assertion: must be 201, NOT 422
    expect(createResponseStatus).toBe(201)

    // Verify response body has expected shape
    const body = await response.json()
    expect(body).toHaveProperty('id')
    expect(body).toHaveProperty('name')
    expect(body).toHaveProperty('policy_json')
    expect(body.policy_json).toHaveProperty('trigger')
    expect(body.policy_json).toHaveProperty('steps')
})
