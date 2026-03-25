/**
 * E2E Wave 4: Position sizing calculator.
 *
 * Gate MEU: MEU-48 `gui-plans`
 * Tests: 2 (computation correctness + accessibility)
 *
 * A11y approach: The Electron app enforces CSP (script-src 'self') which blocks
 * page.addScriptTag injection. Instead, read the axe-core source on the Node side
 * and inject it via page.evaluate() passing the source as an argument (bypasses CSP
 * because evaluate() arguments are sent as CDP Runtime.evaluate(expression) not
 * as script tags — the source runs in the page's own context).
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { CALCULATOR } from './test-ids'
import { readFileSync } from 'fs'
import { resolve } from 'path'

let appPage: AppPage

// Read axe-core source once at module load time (Node side — bypasses page CSP)
const axeSource = readFileSync(
    resolve(__dirname, '../../node_modules/axe-core/axe.min.js'),
    'utf-8',
)

test.beforeEach(async () => {
    appPage = new AppPage()
    await appPage.launch()
    // Navigate to planning page (Plans tab is default)
    await appPage.navigateTo('planning')
    // Open the calculator modal via the button in the plan list header
    await appPage.testId('open-calculator-btn').click()
    // Wait for modal to appear
    await appPage.waitForTestId(CALCULATOR.ROOT)
})

test.afterEach(async () => {
    await appPage.close()
})

test('calculator produces correct position size', async () => {
    // Account Size: $100,000 | Risk: 2% | Entry: $150 | Stop: $145
    await appPage.testId(CALCULATOR.ACCOUNT_SIZE).fill('100000')
    await appPage.testId(CALCULATOR.RISK_PERCENT).fill('2')
    await appPage.testId(CALCULATOR.ENTRY_PRICE).fill('150')
    await appPage.testId(CALCULATOR.STOP_PRICE).fill('145')

    // Computation is reactive (useMemo) — no submit needed
    // Expected: $100K × 2% = $2,000 risk / $5/share = 400 shares
    const sharesEl = appPage.testId(CALCULATOR.RESULT_SHARES)
    await expect(sharesEl).toBeVisible()
    const sharesText = await sharesEl.textContent()
    expect(Number(sharesText?.replace(/,/g, ''))).toBe(400)

    // Dollar risk: 400 shares × $5 = $2,000.00
    const dollarRiskEl = appPage.testId(CALCULATOR.RESULT_DOLLAR_RISK)
    await expect(dollarRiskEl).toBeVisible()
    const dollarRiskText = await dollarRiskEl.textContent()
    expect(dollarRiskText).toContain('2,000')
})

test('calculator modal has no accessibility violations', async () => {
    // Inject axe-core into the page by passing its source to page.evaluate.
    // This bypasses the Electron CSP (script-src 'self') because evaluate()
    // arguments are not script tags — they're passed as CDP evaulation params.
    interface AxeViolation {
        id: string
        description: string
        nodes: { target: string[] }[]
    }

    const violations = await appPage.page.evaluate<AxeViolation[], string>(
        (src) => {
            // Run the axe source in the page's context — safe because evaluate sends
            // the function body via CDP, not a <script> tag injection.
            // eslint-disable-next-line no-new-func
            new Function(src)()
            // Scope the scan to the calculator modal so the gate proves
            // modal-level WCAG compliance, not full-page compliance.
            const context =
                document.querySelector('[data-testid="calculator-modal"]') ?? document
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
