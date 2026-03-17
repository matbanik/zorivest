/**
 * Base Page Object Model for Zorivest Electron E2E tests.
 *
 * Encapsulates Electron app lifecycle and common navigation patterns.
 * All E2E tests should extend or compose this class.
 */

import { type ElectronApplication, type Page, _electron as electron } from '@playwright/test'
import { resolve } from 'path'
import { SIDEBAR } from '../test-ids'

const MAIN_ENTRY = resolve(__dirname, '../../../build/main/index.js')
const API_BASE = 'http://localhost:8765/api/v1'

export class AppPage {
    app!: ElectronApplication
    page!: Page

    /** Launch the Electron app and wait for the main window. */
    async launch(): Promise<void> {
        this.app = await electron.launch({
            args: [MAIN_ENTRY],
            env: {
                ...process.env,
                NODE_ENV: 'test',
            },
        })

        // Wait for the first BrowserWindow (main window after splash closes)
        this.page = await this.app.firstWindow()
        await this.page.waitForLoadState('domcontentloaded')
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
