/**
 * Base Page Object Model for Zorivest Electron E2E tests.
 *
 * Encapsulates Electron app lifecycle and common navigation patterns.
 * All E2E tests should extend or compose this class.
 */

import { type ElectronApplication, type Page, _electron as electron } from '@playwright/test'
import { resolve } from 'path'
import { SIDEBAR } from '../test-ids'

const MAIN_ENTRY = resolve(__dirname, '../../../out/main/index.js')
const API_BASE = 'http://localhost:17787/api/v1'

/**
 * Resolve the Electron executable path from node_modules.
 * Playwright's auto-detection can fail in CI/headless environments.
 */
function resolveElectronPath(): string {
    // electron package exports the path to the binary as its default export
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const electronPath = require('electron') as unknown as string
    return electronPath
}

export class AppPage {
    app!: ElectronApplication
    page!: Page

    /** Launch the Electron app and wait for the main window. */
    async launch(): Promise<void> {
        const executablePath = resolveElectronPath()

        try {
            this.app = await electron.launch({
                executablePath,
                args: [MAIN_ENTRY],
                env: {
                    ...process.env,
                    NODE_ENV: 'test',
                    ZORIVEST_BACKEND_URL:
                        process.env.ZORIVEST_BACKEND_URL || 'http://localhost:17787',
                },
                timeout: 30_000,
            })
        } catch (err) {
            const message = err instanceof Error ? err.message : String(err)
            throw new Error(
                `Electron launch failed.\n` +
                `  executablePath: ${executablePath}\n` +
                `  mainEntry: ${MAIN_ENTRY}\n` +
                `  error: ${message}`,
            )
        }

        // The Electron app creates two windows on startup:
        //   1. Splash (400x300, frameless, show: true)
        //   2. Main window (show: false, becomes visible after ready-to-show)
        //
        // Playwright registers a Page for each BrowserWindow at creation time,
        // not when the window becomes visible. So both pages exist early —
        // we just need to find the one that loaded the renderer (not splash).
        //
        // Strategy: wait for firstWindow (splash), then poll until we find
        // a page whose URL points to the renderer index.html.
        await this.app.firstWindow()

        const POLL_INTERVAL = 500
        const MAX_WAIT = 30_000
        const deadline = Date.now() + MAX_WAIT

        while (Date.now() < deadline) {
            const pages = this.app.windows()
            for (const page of pages) {
                try {
                    const url = page.url()
                    // The main window loads renderer/index.html; the splash loads splash.html
                    if (url.includes('index.html') && !url.includes('splash')) {
                        await page.waitForLoadState('domcontentloaded')
                        this.page = page
                        return
                    }
                } catch {
                    // Page may not be ready yet
                }
            }
            await new Promise((r) => setTimeout(r, POLL_INTERVAL))
        }

        // Diagnostic: dump what we found
        const pageUrls = this.app.windows().map((p) => {
            try { return p.url() } catch { return '<unavailable>' }
        })
        throw new Error(
            `Main window did not load within ${MAX_WAIT}ms.\n` +
            `  Pages found: ${pageUrls.length}\n` +
            `  URLs: ${JSON.stringify(pageUrls)}`,
        )
    }

    /** Close the Electron app. */
    async close(): Promise<void> {
        if (this.app) {
            await this.app.close()
        }
    }

    // ── Navigation ──────────────────────────────────────────────────────

    /**
     * Navigate to a section via the sidebar.
     * Waits for the target page to be visible.
     */
    async navigateTo(
        section: 'accounts' | 'trades' | 'planning' | 'scheduling' | 'settings',
    ): Promise<void> {
        const sidebarMap = {
            accounts: SIDEBAR.NAV_ACCOUNTS,
            trades: SIDEBAR.NAV_TRADES,
            planning: SIDEBAR.NAV_PLANNING,
            scheduling: SIDEBAR.NAV_SCHEDULING,
            settings: SIDEBAR.NAV_SETTINGS,
        }

        await this.page
            .locator(`[data-testid="${sidebarMap[section]}"]`)
            .click()
        // Wait for route transition
        await this.page.waitForTimeout(500)
    }

    // ── API Helpers ─────────────────────────────────────────────────────

    /** Check if the Python backend is healthy. */
    async isBackendHealthy(): Promise<boolean> {
        try {
            const res = await this.page.request.get(`${API_BASE}/health`)
            return res.ok()
        } catch {
            return false
        }
    }

    /**
     * Call a REST API endpoint directly.
     * Useful for verifying DB state after UI actions.
     */
    async apiGet<T = unknown>(path: string): Promise<T> {
        const res = await this.page.request.get(`${API_BASE}${path}`)
        return res.json() as T
    }

    async apiPost<T = unknown>(path: string, data: unknown): Promise<T> {
        const res = await this.page.request.post(`${API_BASE}${path}`, {
            data,
        })
        return res.json() as T
    }

    // ── Locator Helpers ─────────────────────────────────────────────────

    /** Get a locator by data-testid attribute. */
    testId(id: string) {
        return this.page.locator(`[data-testid="${id}"]`)
    }

    /** Wait for a data-testid element to be visible. */
    async waitForTestId(id: string, timeout = 10_000): Promise<void> {
        await this.page
            .locator(`[data-testid="${id}"]`)
            .waitFor({ state: 'visible', timeout })
    }
}
