/**
 * E2E: ScreenshotPanel — image upload, thumbnail rendering, lightbox.
 *
 * Seeds a trade and image via the REST API, then verifies:
 *   1. Thumbnail <img> actually loads (naturalWidth > 0) — CSP img-src
 *   2. Lightbox opens on click and loads full image
 *
 * This test validates the full stack:
 *   Electron CSP → <img src> → FastAPI /images/{id}/thumbnail → SQLCipher
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { TRADES, SCREENSHOTS } from './test-ids'

const API_BASE = 'http://127.0.0.1:17787/api/v1'

let appPage: AppPage

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
})

test.afterEach(async () => {
    await appPage.close()
})

/**
 * Helper: seed a trade via API using external fetch (not page.request).
 * Returns the exec_id.
 */
async function seedTrade(): Promise<string> {
    const execId = `E2E-SS-${Date.now()}`
    const res = await fetch(`${API_BASE}/trades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            exec_id: execId,
            instrument: 'TSLA',
            action: 'BOT',
            quantity: 10,
            price: 200.0,
            account_id: '5554541',
            time: new Date().toISOString(),
        }),
    })
    if (!res.ok) {
        throw new Error(`seedTrade failed: ${res.status} ${await res.text()}`)
    }
    return execId
}

/**
 * Helper: upload an image to a trade via Node fetch (external to Electron).
 * Bypasses any Electron CSP/CORS constraints on the test-seeding side.
 */
async function seedImage(execId: string): Promise<number> {
    // Create a minimal valid PNG (1x1 red pixel)
    const png1x1 = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
        'base64',
    )

    const formData = new FormData()
    formData.append('file', new Blob([png1x1], { type: 'image/png' }), 'test.png')
    formData.append('caption', 'E2E test image')

    const res = await fetch(`${API_BASE}/trades/${execId}/images`, {
        method: 'POST',
        body: formData,
    })
    if (!res.ok) {
        const body = await res.text()
        throw new Error(`seedImage failed: ${res.status} ${body}`)
    }
    const body = await res.json()
    return body.image_id
}

test('thumbnail image loads in ScreenshotPanel (CSP img-src)', async () => {
    // 1. Seed trade + image via external API call
    const execId = await seedTrade()
    const imageId = await seedImage(execId)
    expect(imageId).toBeGreaterThan(0)

    // 2. Navigate to trades and click a trade row with TSLA
    await appPage.navigateTo('trades')
    await appPage.waitForTestId(TRADES.ROOT)

    const tradeRow = appPage.testId(TRADES.TRADE_ROW).filter({ hasText: 'TSLA' })
    await tradeRow.first().click()

    // 3. Click the "Screenshots" tab
    await appPage.page.getByText('Screenshots').click()

    // 4. Wait for the screenshot panel to appear
    await appPage.waitForTestId(SCREENSHOTS.PANEL)

    // 5. Verify thumbnail is visible
    const thumbnail = appPage.testId(SCREENSHOTS.THUMBNAIL)
    await expect(thumbnail.first()).toBeVisible({ timeout: 5_000 })

    // 6. Verify the <img> inside the thumbnail actually loaded
    //    (CSP violation would cause naturalWidth === 0)
    const imgLoaded = await thumbnail.first().locator('img').evaluate((img: HTMLImageElement) => {
        return img.complete && img.naturalWidth > 0
    })
    expect(imgLoaded).toBe(true)
})

test('lightbox loads full image on thumbnail click', async () => {
    // Seed trade + image
    const execId = await seedTrade()
    await seedImage(execId)

    // Navigate to trades, open trade detail
    await appPage.navigateTo('trades')
    await appPage.waitForTestId(TRADES.ROOT)
    const tradeRow = appPage.testId(TRADES.TRADE_ROW).filter({ hasText: 'TSLA' })
    await tradeRow.first().click()

    // Click Screenshots tab
    await appPage.page.getByText('Screenshots').click()
    await appPage.waitForTestId(SCREENSHOTS.PANEL)

    // Click thumbnail to open lightbox
    const thumbnail = appPage.testId(SCREENSHOTS.THUMBNAIL)
    await thumbnail.first().click()

    // Verify lightbox appears
    await appPage.waitForTestId(SCREENSHOTS.LIGHTBOX, 5_000)
    const lightbox = appPage.testId(SCREENSHOTS.LIGHTBOX)
    await expect(lightbox).toBeVisible()

    // Verify the full image in the lightbox loaded
    const fullImgLoaded = await lightbox.locator('img').evaluate((img: HTMLImageElement) => {
        return img.complete && img.naturalWidth > 0
    })
    expect(fullImgLoaded).toBe(true)
})

test('AC-12 E2E: clipboard paste uploads image via Ctrl+V', async () => {
    // 1. Seed trade (no pre-existing images)
    const execId = await seedTrade()

    // 2. Navigate to trade detail → Screenshots tab
    await appPage.navigateTo('trades')
    await appPage.waitForTestId(TRADES.ROOT)
    const tradeRow = appPage.testId(TRADES.TRADE_ROW).filter({ hasText: 'TSLA' })
    await tradeRow.first().click()
    await appPage.page.getByText('Screenshots').click()
    await appPage.waitForTestId(SCREENSHOTS.PANEL)

    // 3. Verify no thumbnails initially
    const thumbnailsBefore = appPage.testId(SCREENSHOTS.THUMBNAIL)
    await expect(thumbnailsBefore).toHaveCount(0)

    // 4. Focus the screenshot panel, then dispatch a paste event
    //    with a real PNG in the DataTransfer — exercises the actual
    //    onPaste → handleUpload → POST /images → refetch pipeline
    //    inside Electron's Chromium renderer.
    const panel = appPage.testId(SCREENSHOTS.PANEL)
    await panel.focus()

    const png1x1Base64 =
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='

    await panel.evaluate(async (el, pngB64) => {
        // Convert base64 → Blob → File
        const binary = atob(pngB64)
        const bytes = new Uint8Array(binary.length)
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
        const blob = new Blob([bytes], { type: 'image/png' })
        const file = new File([blob], 'paste.png', { type: 'image/png' })

        // Build a DataTransfer containing the image file
        const dt = new DataTransfer()
        dt.items.add(file)

        // Dispatch ClipboardEvent — triggers the React onPaste handler
        const event = new ClipboardEvent('paste', {
            clipboardData: dt,
            bubbles: true,
            cancelable: true,
        })
        el.dispatchEvent(event)
    }, png1x1Base64)

    // 5. Wait for the thumbnail to appear after upload + query refetch
    const thumbnailsAfter = appPage.testId(SCREENSHOTS.THUMBNAIL)
    await expect(thumbnailsAfter.first()).toBeVisible({ timeout: 10_000 })

    // 6. Verify the image actually loaded (not a broken placeholder)
    const imgLoaded = await thumbnailsAfter
        .first()
        .locator('img')
        .evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)
    expect(imgLoaded).toBe(true)
})
