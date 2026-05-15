/**
 * E2E Wave 11: Tax Dashboard page.
 *
 * Gate MEU: MEU-154 (gui-tax)
 * Tests: Navigation to /tax route, dashboard summary cards render, disclaimer,
 *        and axe-core accessibility check.
 *
 * These tests require the Electron app + Python backend running.
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { TAX } from './test-ids'
import { readFileSync } from 'fs'
import { resolve } from 'path'

let appPage: AppPage

// Read axe-core source once at module load time (bypasses Electron CSP)
const axeSource = readFileSync(
    resolve(__dirname, '../../node_modules/axe-core/axe.min.js'),
    'utf-8',
)

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    await appPage.navigateTo('tax')
})

test.afterEach(async () => {
    await appPage.close()
})

test('tax page loads with root container', async () => {
    await appPage.waitForTestId(TAX.ROOT)
    const root = appPage.testId(TAX.ROOT)
    await expect(root).toBeVisible()
})

test('dashboard tab is active by default', async () => {
    await appPage.waitForTestId(TAX.DASHBOARD)
    const dashboard = appPage.testId(TAX.DASHBOARD)
    await expect(dashboard).toBeVisible()
})

test('dashboard renders summary cards', async () => {
    await appPage.waitForTestId(TAX.DASHBOARD)
    const cards = appPage.testId(TAX.SUMMARY_CARD)
    // Dashboard spec (06g-gui-tax.md) defines 7 summary cards
    const count = await cards.count()
    expect(count).toBe(7)
})

test('disclaimer is visible', async () => {
    await appPage.waitForTestId(TAX.DISCLAIMER)
    const disclaimer = appPage.testId(TAX.DISCLAIMER)
    await expect(disclaimer).toBeVisible()
    const text = await disclaimer.textContent()
    expect(text).toContain('not tax advice')
})

test('tax dashboard has no accessibility violations', async () => {
    await appPage.waitForTestId(TAX.DASHBOARD)

    interface AxeViolation {
        id: string
        description: string
        nodes: { target: string[] }[]
    }

    const violations = await appPage.page.evaluate<AxeViolation[], string>(
        (src) => {
            // eslint-disable-next-line no-new-func
            new Function(src)()
            const context =
                document.querySelector('[data-testid="tax-page"]') ?? document
            return (window as unknown as { axe: { run: (ctx: Element | Document) => Promise<{ violations: AxeViolation[] }> } }).axe
                .run(context)
                .then((r) => r.violations)
        },
        axeSource,
    )

    if (violations.length > 0) {
        const summary = violations
            .map(
                (v) =>
                    `${v.id}: ${v.description} (${v.nodes
                        .map((n) => n.target.join(', '))
                        .join(' | ')})`,
            )
            .join('\n')
        throw new Error(`Accessibility violations found:\n${summary}`)
    }
    expect(violations).toEqual([])
})
