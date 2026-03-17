import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright configuration for Zorivest Electron E2E tests.
 *
 * Phase 4 of Test Rigor Audit.
 *
 * Usage:
 *   npx playwright test                    # Run all E2E tests
 *   npx playwright test launch.test.ts     # Run specific test
 *   npx playwright test --headed           # Watch in browser
 */
export default defineConfig({
    testDir: './tests/e2e',
    fullyParallel: false, // Electron tests share app state
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: 1, // Single worker — one Electron app at a time
    reporter: [['html', { open: 'never' }], ['list']],
    timeout: 60_000,
    expect: {
        timeout: 10_000,
        toHaveScreenshot: {
            maxDiffPixelRatio: 0.01,
        },
    },

    globalSetup: './tests/e2e/global-setup.ts',
    globalTeardown: './tests/e2e/global-teardown.ts',

    use: {
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
    },
})
