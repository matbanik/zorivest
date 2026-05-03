/**
 * E2E Wave 4: Position sizing calculator + trade plan dirty-guard.
 *
 * Gate MEU: MEU-48 `gui-plans`, MEU-198 `gui-form-guard-crud`
 * Tests: 3 (computation correctness + accessibility + dirty-guard)
 *
 * A11y approach: The Electron app enforces CSP (script-src 'self') which blocks
 * page.addScriptTag injection. Instead, read the axe-core source on the Node side
 * and inject it via page.evaluate() passing the source as an argument (bypasses CSP
 * because evaluate() arguments are sent as CDP Runtime.evaluate(expression) not
 * as script tags — the source runs in the page's own context).
 */

import { test, expect } from '@playwright/test'
import { AppPage } from './pages/AppPage'
import { CALCULATOR, UNSAVED_CHANGES } from './test-ids'
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

// ── Wave 4 extension: Trade Plan dirty-guard (MEU-198) ─────────────────

const API_BASE = 'http://localhost:17787/api/v1'
const TEST_PREFIX = 'E2E_PlanGuard_'

interface CreatedPlan {
    id: number
    ticker: string
}

async function apiCreatePlan(data: Record<string, unknown>): Promise<CreatedPlan> {
    const res = await fetch(`${API_BASE}/trade-plans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(`Plan create failed: ${res.status} ${await res.text()}`)
    return res.json()
}

async function apiDeletePlan(planId: number): Promise<void> {
    await fetch(`${API_BASE}/trade-plans/${planId}`, { method: 'DELETE' })
}

test('dirty-guard: editing trade plan and switching shows unsaved changes modal', async () => {
    // Stand up a fresh AppPage for this test (no calculator modal)
    const guardApp = new AppPage()
    await guardApp.launch()

    const createdPlanIds: number[] = []

    try {
        // Create two trade plans via API
        const planA = await apiCreatePlan({
            ticker: `${TEST_PREFIX}AAPL`,
            strategy_name: `${TEST_PREFIX}StrategyA`,
            direction: 'long',
            conviction: 'medium',
            entry_price: 150,
            stop_loss: 145,
            target_price: 170,
        })
        createdPlanIds.push(planA.id)

        const planB = await apiCreatePlan({
            ticker: `${TEST_PREFIX}MSFT`,
            strategy_name: `${TEST_PREFIX}StrategyB`,
            direction: 'long',
            conviction: 'high',
            entry_price: 400,
            stop_loss: 390,
            target_price: 450,
        })
        createdPlanIds.push(planB.id)

        // Navigate to planning page
        await guardApp.navigateTo('planning')

        // Wait for plan list to render and reload to pick up API-created plans
        await guardApp.page.reload()
        await guardApp.waitForTestId('trade-plan-page')

        // Wait for plan A card to appear
        const cardA = guardApp.testId(`plan-card-${planA.id}`)
        await cardA.waitFor({ state: 'visible', timeout: 15_000 })

        // Select plan A
        await cardA.click()
        await guardApp.waitForTestId('plan-detail-panel')

        // Edit the ticker field to make the form dirty
        const tickerInput = guardApp.testId('plan-ticker')
        await tickerInput.clear()
        await tickerInput.fill(`${TEST_PREFIX}DIRTY`)
        await guardApp.page.waitForTimeout(300)

        // Click plan B card — should trigger the guard modal
        const cardB = guardApp.testId(`plan-card-${planB.id}`)
        await cardB.click()

        // The UnsavedChangesModal should appear
        await guardApp.waitForTestId(UNSAVED_CHANGES.MODAL, 5_000)

        // Click "Keep Editing" — modal should close, form should preserve dirty value
        await guardApp.testId(UNSAVED_CHANGES.KEEP_EDITING_BTN).click()

        // Modal should be gone
        await guardApp.page
            .locator(`[data-testid="${UNSAVED_CHANGES.MODAL}"]`)
            .waitFor({ state: 'detached', timeout: 3_000 })

        // The ticker field should still have the dirty value
        await expect(tickerInput).toHaveValue(`${TEST_PREFIX}DIRTY`)
    } finally {
        // Cleanup: delete created plans
        for (const id of createdPlanIds) {
            await apiDeletePlan(id)
        }
        await guardApp.close()
    }
})
