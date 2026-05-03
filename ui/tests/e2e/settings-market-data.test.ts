/**
 * Wave 6 E2E: Market Data Providers settings page (MEU-65).
 *
 * Gate MEU: MEU-65 gui-settings-market-data
 *
 * Covers:
 *   - Provider list renders all 14 providers
 *   - Selecting a provider shows the detail panel
 *   - Free providers show "Free — no API key required" badge
 *   - Test Connection button is present in detail panel
 *   - Accessibility scan (WCAG 2.1 AA)
 */

import { test, expect } from '@playwright/test'
import { pathToFileURL } from 'url'
import { resolve } from 'path'
import { AppPage } from './pages/AppPage'
import { MARKET_DATA_PROVIDERS, SETTINGS, UNSAVED_CHANGES } from './test-ids'

let appPage: AppPage

/**
 * Unlock the app's internal DB so guarded routes return data.
 * Must be called AFTER appPage.launch() so apiPost hits the correct backend.
 */
async function unlockAppDb(): Promise<void> {
    try {
        const keyData = await appPage.apiPost<{ raw_key: string }>('/auth/keys', { name: 'e2e-wave6' })
        await appPage.apiPost('/auth/unlock', { api_key: keyData.raw_key })
    } catch {
        // Already unlocked or dev-unlock mode — safe to ignore
    }
}

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    await unlockAppDb()
})

test.afterEach(async () => {
    await appPage.close()
})

// Navigate: Settings → Market Data Providers card
async function goToMarketPage(): Promise<void> {
    await appPage.navigateTo('settings')
    await appPage.waitForTestId(SETTINGS.ROOT)

    // Click the "Market Data Providers" navigation card (data-testid = settings-market-data-link)
    await appPage.testId('settings-market-data-link').click()
    await appPage.page.waitForTimeout(600)

    await appPage.waitForTestId(MARKET_DATA_PROVIDERS.ROOT)
}

test('provider list renders all 14 providers', async () => {
    await goToMarketPage()

    const list = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_LIST)
    await expect(list).toBeVisible()

    const items = list.locator(`[data-testid="${MARKET_DATA_PROVIDERS.PROVIDER_ITEM}"]`)
    await expect(items).toHaveCount(14, { timeout: 8_000 })
})

test('selecting a provider shows detail panel', async () => {
    await goToMarketPage()

    const items = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_ITEM)
    await expect(items.first()).toBeVisible({ timeout: 8_000 })
    await items.first().click()
    await appPage.page.waitForTimeout(300)

    await appPage.waitForTestId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)
    await expect(appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)).toBeVisible()
})

test('Test Connection button is present in detail panel', async () => {
    await goToMarketPage()

    const items = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_ITEM)
    await expect(items.first()).toBeVisible({ timeout: 8_000 })
    await items.first().click()
    await appPage.waitForTestId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)

    const testBtn = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_TEST_BTN)
    await expect(testBtn).toBeVisible()
    await expect(testBtn).toHaveText('Test Connection')
})

test('free providers show no-API-key badge (Yahoo Finance)', async () => {
    await goToMarketPage()

    const yahooItem = appPage.page
        .locator(`[data-testid="${MARKET_DATA_PROVIDERS.PROVIDER_ITEM}"]`)
        .filter({ hasText: 'Yahoo Finance' })
    await expect(yahooItem).toBeVisible({ timeout: 8_000 })
    await yahooItem.click()
    await appPage.waitForTestId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)

    await expect(appPage.page.locator('text=Free — no API key required')).toBeVisible()
})

test('free providers show no-API-key badge (TradingView)', async () => {
    await goToMarketPage()

    const tvItem = appPage.page
        .locator(`[data-testid="${MARKET_DATA_PROVIDERS.PROVIDER_ITEM}"]`)
        .filter({ hasText: 'TradingView' })
    await expect(tvItem).toBeVisible({ timeout: 8_000 })
    await tvItem.click()
    await appPage.waitForTestId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)

    await expect(appPage.page.locator('text=Free — no API key required')).toBeVisible()
})

test('Test All button is visible in provider list panel', async () => {
    await goToMarketPage()

    const testAllBtn = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_TEST_ALL_BTN)
    await expect(testAllBtn).toBeVisible()
    await expect(testAllBtn).toHaveText('Test All')
})

test('market data providers page has no accessibility violations', async () => {
    await goToMarketPage()

    const items = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_ITEM)
    await expect(items.first()).toBeVisible({ timeout: 8_000 })
    await items.first().click()

    // Wait for detail panel to be fully rendered before axe scan
    const detail = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)
    await expect(detail).toBeVisible({ timeout: 10_000 })
    await appPage.page.waitForTimeout(500) // settle animations

    // AxeBuilder and inline addScriptTag({ content }) are both blocked in
    // Electron's sandboxed renderer (sandbox: true + contextIsolation: true).
    // Loading axe-core via a file:// URL works because the file protocol is
    // allowed by the renderer's web security settings.
    const axePath = resolve(__dirname, '../../node_modules/axe-core/axe.min.js')
    const axeUrl = pathToFileURL(axePath).href
    await appPage.page.addScriptTag({ url: axeUrl })

    const violations = await appPage.page.evaluate(async () => {
        const axeResults = await (window as any).axe.run(document, {
            runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
        })
        return (axeResults.violations as any[]).map((v: any) => ({
            id: v.id,
            impact: v.impact,
            description: v.description,
            nodeHtml: v.nodes[0]?.html?.substring(0, 200) ?? '',
        }))
    })
    expect(violations).toEqual([])
})

test('dirty-guard: editing API key and switching provider shows unsaved changes modal', async () => {
    await goToMarketPage()

    // Select the first provider (usually Alpha Vantage — an API-key provider)
    const items = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_ITEM)
    await expect(items.first()).toBeVisible({ timeout: 8_000 })
    await items.first().click()
    await appPage.waitForTestId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)

    // Type into the API key field to make the form dirty
    const apiKeyInput = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_API_KEY_INPUT)
    // Some providers may not have an API key input (free providers) — find one that does
    const isApiKeyVisible = await apiKeyInput.isVisible().catch(() => false)

    if (isApiKeyVisible) {
        await apiKeyInput.fill('test-dirty-key-e2e')
        await appPage.page.waitForTimeout(300)

        // Click a different provider — should trigger the guard modal
        await items.nth(1).click()

        // The UnsavedChangesModal should appear
        await appPage.waitForTestId(UNSAVED_CHANGES.MODAL, 5_000)
        const modal = appPage.testId(UNSAVED_CHANGES.MODAL)
        await expect(modal).toBeVisible()

        // Verify Discard button is present
        await expect(appPage.testId(UNSAVED_CHANGES.DISCARD_BTN)).toBeVisible()

        // Click Discard — modal should dismiss, navigates to the new provider
        await appPage.testId(UNSAVED_CHANGES.DISCARD_BTN).click()
        await appPage.page.waitForTimeout(500)

        // Modal should be gone
        await expect(appPage.testId(UNSAVED_CHANGES.MODAL)).not.toBeVisible()
    } else {
        // If first provider is a free one, try the 3rd item instead
        await items.nth(2).click()
        await appPage.waitForTestId(MARKET_DATA_PROVIDERS.PROVIDER_DETAIL)
        const apiKeyInput2 = appPage.testId(MARKET_DATA_PROVIDERS.PROVIDER_API_KEY_INPUT)
        const isVisible2 = await apiKeyInput2.isVisible().catch(() => false)

        if (isVisible2) {
            await apiKeyInput2.fill('test-dirty-key-e2e')
            await appPage.page.waitForTimeout(300)
            await items.nth(3).click()

            await appPage.waitForTestId(UNSAVED_CHANGES.MODAL, 5_000)
            await expect(appPage.testId(UNSAVED_CHANGES.MODAL)).toBeVisible()
            await appPage.testId(UNSAVED_CHANGES.DISCARD_BTN).click()
            await appPage.page.waitForTimeout(300)
            await expect(appPage.testId(UNSAVED_CHANGES.MODAL)).not.toBeVisible()
        }
    }
})
