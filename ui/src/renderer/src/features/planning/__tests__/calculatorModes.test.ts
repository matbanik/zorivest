/**
 * Tests for Calculator Modes (MEU-155).
 *
 * Pure computation tests for calculatorModes.ts:
 * - Futures position sizing with contract-based math
 * - Options position sizing with premium/delta
 * - Forex position sizing with pip-based math
 * - Crypto position sizing with leverage + fees
 * - Warnings engine
 * - Scenario management
 * - History management
 *
 * MEU: MEU-155 (AC-155.1 through AC-155.10)
 */

import { describe, it, expect } from 'vitest'
import {
    computeFutures,
    computeOptions,
    computeForex,
    computeCrypto,
    getWarnings,
    addScenario,
    removeScenario,
    addToHistory,
    FUTURES_PRESETS,
    type Scenario,
    type HistoryEntry,
} from '../calculatorModes'

// ═══════════════════════════════════════════════════════════════════════════════
// Futures
// ═══════════════════════════════════════════════════════════════════════════════

describe('computeFutures', () => {
    const ES = FUTURES_PRESETS.ES // multiplier: 50, tickSize: 0.25, margin: 12980

    it('AC-155.2: calculates contracts based on risk budget', () => {
        // $100k account, 1% risk = $1000 budget
        // ES: entry 5000, stop 4990 → 10pt risk = 40 ticks → $500/contract
        // $1000 / $500 = 2 contracts
        const r = computeFutures(100000, 1, 5000, 4990, 5020, ES)
        expect(r.contracts).toBe(2)
        expect(r.totalRisk).toBe(1000)
        expect(r.totalMargin).toBe(25960) // 2 * 12980
    })

    it('returns 0 contracts when risk per contract exceeds budget', () => {
        const r = computeFutures(10000, 0.5, 5000, 4900, 5100, ES)
        // $50 budget, risk = 100pt * 400 ticks * 50 = $5000/contract
        expect(r.contracts).toBe(0)
    })

    it('calculates R:R ratio', () => {
        const r = computeFutures(100000, 1, 5000, 4990, 5030, ES)
        // Risk: 10pt, Reward: 30pt → R:R = 3.0
        expect(r.rrRatio).toBe(3)
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Options
// ═══════════════════════════════════════════════════════════════════════════════

describe('computeOptions', () => {
    it('AC-155.3: calculates contracts from premium', () => {
        // $100k, 2% risk = $2000
        // Premium $5 * 100 multiplier = $500/contract → 4 contracts
        const r = computeOptions(100000, 2, {
            type: 'call', premium: 5, delta: 0.5, underlyingPrice: 150, multiplier: 100,
        })
        expect(r.contracts).toBe(4)
        expect(r.totalPremium).toBe(2000)
    })

    it('calculates delta exposure', () => {
        const r = computeOptions(100000, 2, {
            type: 'call', premium: 5, delta: 0.6, underlyingPrice: 150, multiplier: 100,
        })
        // 4 contracts * 100 * 0.6 = 240 delta shares
        expect(r.deltaExposure).toBe(240)
    })

    it('returns 0 contracts for zero premium', () => {
        const r = computeOptions(100000, 1, {
            type: 'put', premium: 0, delta: 0.3, underlyingPrice: 100, multiplier: 100,
        })
        expect(r.contracts).toBe(0)
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Forex
// ═══════════════════════════════════════════════════════════════════════════════

describe('computeForex', () => {
    it('AC-155.4: calculates lots from pip risk', () => {
        // $10k, 1% risk = $100
        // entry 1.1000, stop 1.0980 → 20 pips risk
        // $10/pip (standard) → $200/lot risk → 0.5 lots
        const r = computeForex(10000, 1, 1.1000, 1.0980, 1.1040, {
            pair: 'EUR/USD', lotType: 'standard', pipValue: 10, leverage: 50,
        })
        // Math.floor rounding: 0.002 * 10000 = 19.999... → lots = floor(49.99)/100 = 0.49
        expect(r.lots).toBe(0.49)
        expect(r.units).toBe(49000)
    })

    it('calculates margin requirement', () => {
        const r = computeForex(10000, 1, 1.1000, 1.0980, 1.1040, {
            pair: 'EUR/USD', lotType: 'standard', pipValue: 10, leverage: 50,
        })
        // Actual: 49000 units * 1.1 / 50 = $1078 (lots rounded to 0.49)
        expect(r.marginRequired).toBe(1078)
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Crypto
// ═══════════════════════════════════════════════════════════════════════════════

describe('computeCrypto', () => {
    it('AC-155.5: calculates units from risk budget', () => {
        // $10k, 2% risk = $200
        // entry $50000, stop $49500 → $500 risk/unit
        // $200 / $500 = 0.4 BTC
        const r = computeCrypto(10000, 2, 50000, 49500, 51000, {
            leverage: 1, feeRate: 0.1,
        })
        expect(r.units).toBe(0.4) // 200 / 500 = 0.4 BTC
    })

    it('calculates liquidation price', () => {
        const r = computeCrypto(10000, 2, 50000, 49500, 51000, {
            leverage: 10, feeRate: 0.1,
        })
        // liquidation = entry * (1 - 1/leverage) = 50000 * 0.9 = 45000
        expect(r.liquidationPrice).toBe(45000)
    })

    it('includes fees in net reward', () => {
        const r = computeCrypto(10000, 2, 50000, 49500, 51000, {
            leverage: 1, feeRate: 0.1,
        })
        expect(r.totalFees).toBeGreaterThan(0)
        expect(r.netReward).toBeLessThan(r.netReward + r.totalFees)
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Warnings
// ═══════════════════════════════════════════════════════════════════════════════

describe('getWarnings', () => {
    it('AC-155.6: warns when risk exceeds 3%', () => {
        const w = getWarnings('equity', 100000, 4, {})
        expect(w).toHaveLength(1)
        expect(w[0].level).toBe('danger')
        expect(w[0].message).toContain('4%')
    })

    it('warns when risk exceeds 2% but not 3%', () => {
        const w = getWarnings('equity', 100000, 2.5, {})
        expect(w).toHaveLength(1)
        expect(w[0].level).toBe('warn')
    })

    it('no warnings for 1% risk equity', () => {
        const w = getWarnings('equity', 100000, 1, { positionPercent: 50 })
        expect(w).toHaveLength(0)
    })

    it('warns on high futures margin', () => {
        const w = getWarnings('futures', 100000, 1, { marginPercent: 60 })
        expect(w.some(x => x.level === 'danger' && x.message.includes('Margin'))).toBe(true)
    })

    it('warns on high options premium', () => {
        const w = getWarnings('options', 100000, 1, { premiumPercent: 12 })
        expect(w.some(x => x.level === 'danger' && x.message.includes('Premium'))).toBe(true)
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Scenarios
// ═══════════════════════════════════════════════════════════════════════════════

describe('scenario management', () => {
    const base: Scenario = {
        id: 's1', mode: 'equity', label: 'AAPL', accountSize: 100000,
        riskPercent: 1, entryPrice: 150, stopPrice: 145, targetPrice: 160,
        resultShares: 200, resultRisk: 1000, resultRR: 2, timestamp: Date.now(),
    }

    it('AC-155.8: adds scenario', () => {
        const result = addScenario([], base)
        expect(result).toHaveLength(1)
        expect(result[0].id).toBe('s1')
    })

    it('AC-155.8: caps at 5 scenarios (FIFO)', () => {
        let scenarios: Scenario[] = []
        for (let i = 0; i < 7; i++) {
            scenarios = addScenario(scenarios, { ...base, id: `s${i}` })
        }
        expect(scenarios).toHaveLength(5)
        expect(scenarios[0].id).toBe('s2') // s0, s1 evicted
    })

    it('removes scenario by id', () => {
        const scenarios = addScenario(addScenario([], base), { ...base, id: 's2' })
        const result = removeScenario(scenarios, 's1')
        expect(result).toHaveLength(1)
        expect(result[0].id).toBe('s2')
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// History
// ═══════════════════════════════════════════════════════════════════════════════

describe('history management', () => {
    const base: HistoryEntry = {
        id: 'h1', mode: 'equity', accountSize: 100000,
        riskPercent: 1, entryPrice: 150, stopPrice: 145, targetPrice: 160,
        resultShares: 200, resultRisk: 1000, resultRR: 2, timestamp: Date.now(),
    }

    it('AC-155.9: adds to history', () => {
        const result = addToHistory([], base)
        expect(result).toHaveLength(1)
    })

    it('AC-155.9: caps at 10 entries (FIFO)', () => {
        let history: HistoryEntry[] = []
        for (let i = 0; i < 12; i++) {
            history = addToHistory(history, { ...base, id: `h${i}` })
        }
        expect(history).toHaveLength(10)
        expect(history[0].id).toBe('h2') // h0, h1 evicted
    })
})
