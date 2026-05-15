/**
 * Calculator Mode Expansion — instrument-specific position sizing.
 *
 * Provides 5 modes: Equity (existing), Futures, Options, Forex, Crypto
 * Each mode has unique input fields and computation logic.
 *
 * Source: implementation-plan.md §MEU-155
 * MEU: MEU-155 (AC-155.1 through AC-155.10)
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export type CalcMode = 'equity' | 'futures' | 'options' | 'forex' | 'crypto'

export const CALC_MODES: { value: CalcMode; label: string; icon: string }[] = [
    { value: 'equity', label: 'Equity', icon: '📈' },
    { value: 'futures', label: 'Futures', icon: '📊' },
    { value: 'options', label: 'Options', icon: '🎯' },
    { value: 'forex', label: 'Forex', icon: '💱' },
    { value: 'crypto', label: 'Crypto', icon: '₿' },
]

// ── Futures ───────────────────────────────────────────────────────────────────

export interface FuturesInputs {
    multiplier: number
    tickSize: number
    margin: number
}

export const FUTURES_PRESETS: Record<string, FuturesInputs> = {
    ES: { multiplier: 50, tickSize: 0.25, margin: 12980 },
    NQ: { multiplier: 20, tickSize: 0.25, margin: 17600 },
    YM: { multiplier: 5, tickSize: 1, margin: 9020 },
    CL: { multiplier: 1000, tickSize: 0.01, margin: 6270 },
    GC: { multiplier: 100, tickSize: 0.10, margin: 10200 },
}

export function computeFutures(
    accountSize: number,
    riskPercent: number,
    entryPrice: number,
    stopPrice: number,
    targetPrice: number,
    inputs: FuturesInputs,
) {
    const riskBudget = accountSize * (riskPercent / 100)
    const ticksRisk = Math.abs(entryPrice - stopPrice) / inputs.tickSize
    const dollarRiskPerContract = ticksRisk * inputs.tickSize * inputs.multiplier
    const contracts = dollarRiskPerContract > 0 ? Math.floor(riskBudget / dollarRiskPerContract) : 0
    const totalRisk = contracts * dollarRiskPerContract
    const totalMargin = contracts * inputs.margin
    const ticksReward = Math.abs(targetPrice - entryPrice) / inputs.tickSize
    const dollarRewardPerContract = ticksReward * inputs.tickSize * inputs.multiplier
    const totalReward = contracts * dollarRewardPerContract
    const rrRatio = totalRisk > 0 ? totalReward / totalRisk : 0

    return {
        contracts,
        totalRisk: Math.round(totalRisk * 100) / 100,
        totalMargin: Math.round(totalMargin * 100) / 100,
        totalReward: Math.round(totalReward * 100) / 100,
        rrRatio: Math.round(rrRatio * 100) / 100,
        marginPercent: accountSize > 0 ? Math.round((totalMargin / accountSize) * 1000) / 10 : 0,
    }
}

// ── Options ───────────────────────────────────────────────────────────────────

export interface OptionsInputs {
    type: 'call' | 'put'
    premium: number
    delta: number
    underlyingPrice: number
    multiplier: number // typically 100
}

export function computeOptions(
    accountSize: number,
    riskPercent: number,
    inputs: OptionsInputs,
) {
    const riskBudget = accountSize * (riskPercent / 100)
    const maxLossPerContract = inputs.premium * inputs.multiplier
    const contracts = maxLossPerContract > 0 ? Math.floor(riskBudget / maxLossPerContract) : 0
    const totalPremium = contracts * maxLossPerContract
    const notionalExposure = contracts * inputs.multiplier * inputs.underlyingPrice
    const deltaExposure = contracts * inputs.multiplier * inputs.delta

    return {
        contracts,
        totalPremium: Math.round(totalPremium * 100) / 100,
        notionalExposure: Math.round(notionalExposure * 100) / 100,
        deltaExposure: Math.round(deltaExposure * 100) / 100,
        premiumPercent: accountSize > 0 ? Math.round((totalPremium / accountSize) * 1000) / 10 : 0,
    }
}

// ── Forex ─────────────────────────────────────────────────────────────────────

export type ForexLotType = 'standard' | 'mini' | 'micro'

export interface ForexInputs {
    pair: string
    lotType: ForexLotType
    pipValue: number
    leverage: number
}

const LOT_SIZES: Record<ForexLotType, number> = {
    standard: 100_000,
    mini: 10_000,
    micro: 1_000,
}

export function computeForex(
    accountSize: number,
    riskPercent: number,
    entryPrice: number,
    stopPrice: number,
    targetPrice: number,
    inputs: ForexInputs,
) {
    const riskBudget = accountSize * (riskPercent / 100)
    const pipsRisk = Math.abs(entryPrice - stopPrice) * 10_000 // 4-decimal pairs
    const dollarRiskPerLot = pipsRisk * inputs.pipValue
    const lots = dollarRiskPerLot > 0 ? Math.floor((riskBudget / dollarRiskPerLot) * 100) / 100 : 0
    const lotSize = LOT_SIZES[inputs.lotType]
    const units = Math.round(lots * lotSize)
    const totalRisk = lots * dollarRiskPerLot
    const marginRequired = (units * entryPrice) / inputs.leverage
    const pipsReward = Math.abs(targetPrice - entryPrice) * 10_000
    const totalReward = lots * pipsReward * inputs.pipValue
    const rrRatio = totalRisk > 0 ? totalReward / totalRisk : 0

    return {
        lots: Math.round(lots * 100) / 100,
        units,
        totalRisk: Math.round(totalRisk * 100) / 100,
        totalReward: Math.round(totalReward * 100) / 100,
        marginRequired: Math.round(marginRequired * 100) / 100,
        rrRatio: Math.round(rrRatio * 100) / 100,
    }
}

// ── Crypto ────────────────────────────────────────────────────────────────────

export interface CryptoInputs {
    leverage: number
    feeRate: number // as percentage, e.g. 0.1 for 0.1%
}

export function computeCrypto(
    accountSize: number,
    riskPercent: number,
    entryPrice: number,
    stopPrice: number,
    targetPrice: number,
    inputs: CryptoInputs,
) {
    const riskBudget = accountSize * (riskPercent / 100)
    const riskPerUnit = Math.abs(entryPrice - stopPrice)
    const units = riskPerUnit > 0 ? riskBudget / riskPerUnit : 0
    const positionValue = units * entryPrice
    const marginRequired = positionValue / inputs.leverage
    const entryFee = positionValue * (inputs.feeRate / 100)
    const exitFee = units * targetPrice * (inputs.feeRate / 100)
    const totalFees = entryFee + exitFee
    const rewardPerUnit = Math.abs(targetPrice - entryPrice)
    const grossReward = units * rewardPerUnit
    const netReward = grossReward - totalFees
    const totalRisk = riskBudget + entryFee
    const rrRatio = totalRisk > 0 ? netReward / totalRisk : 0

    // Liquidation price (long position assumption)
    const liquidationPrice = entryPrice * (1 - 1 / inputs.leverage)

    return {
        units: Math.round(units * 1e6) / 1e6, // 6 decimal precision for crypto
        positionValue: Math.round(positionValue * 100) / 100,
        marginRequired: Math.round(marginRequired * 100) / 100,
        totalFees: Math.round(totalFees * 100) / 100,
        netReward: Math.round(netReward * 100) / 100,
        totalRisk: Math.round(totalRisk * 100) / 100,
        rrRatio: Math.round(rrRatio * 100) / 100,
        liquidationPrice: Math.round(liquidationPrice * 100) / 100,
    }
}

// ── Warnings ──────────────────────────────────────────────────────────────────

export interface CalcWarning {
    level: 'info' | 'warn' | 'danger'
    message: string
}

export function getWarnings(
    mode: CalcMode,
    accountSize: number,
    riskPercent: number,
    result: Record<string, number>,
): CalcWarning[] {
    const warnings: CalcWarning[] = []

    // Common warnings
    if (riskPercent > 3) {
        warnings.push({ level: 'danger', message: `Risk ${riskPercent}% exceeds 3% — high risk` })
    } else if (riskPercent > 2) {
        warnings.push({ level: 'warn', message: `Risk ${riskPercent}% exceeds 2% — elevated risk` })
    }

    // Mode-specific warnings
    switch (mode) {
        case 'futures':
            if (result.marginPercent > 50) {
                warnings.push({ level: 'danger', message: `Margin ${result.marginPercent}% exceeds 50% of account` })
            } else if (result.marginPercent > 25) {
                warnings.push({ level: 'warn', message: `Margin ${result.marginPercent}% exceeds 25% of account` })
            }
            break
        case 'options':
            if (result.premiumPercent > 10) {
                warnings.push({ level: 'danger', message: `Premium ${result.premiumPercent}% exceeds 10% of account` })
            } else if (result.premiumPercent > 5) {
                warnings.push({ level: 'warn', message: `Premium ${result.premiumPercent}% exceeds 5% of account` })
            }
            break
        case 'crypto':
            if (result.liquidationPrice > 0) {
                const liquidationDist = Math.abs(result.liquidationPrice / (result.positionValue / result.units) - 1) * 100
                if (liquidationDist < 5) {
                    warnings.push({ level: 'danger', message: `Liquidation only ${liquidationDist.toFixed(1)}% away from entry` })
                }
            }
            break
    }

    return warnings
}

// ── Scenario Comparison ───────────────────────────────────────────────────────

export interface Scenario {
    id: string
    mode: CalcMode
    label: string
    accountSize: number
    riskPercent: number
    entryPrice: number
    stopPrice: number
    targetPrice: number
    resultShares: number
    resultRisk: number
    resultRR: number
    timestamp: number
}

const MAX_SCENARIOS = 5

export function addScenario(scenarios: Scenario[], scenario: Scenario): Scenario[] {
    const updated = [...scenarios, scenario]
    return updated.slice(-MAX_SCENARIOS)
}

export function removeScenario(scenarios: Scenario[], id: string): Scenario[] {
    return scenarios.filter((s) => s.id !== id)
}

// ── Calculation History ───────────────────────────────────────────────────────

export interface HistoryEntry {
    id: string
    mode: CalcMode
    accountSize: number
    riskPercent: number
    entryPrice: number
    stopPrice: number
    targetPrice: number
    resultShares: number
    resultRisk: number
    resultRR: number
    timestamp: number
}

const MAX_HISTORY = 10

export function addToHistory(history: HistoryEntry[], entry: HistoryEntry): HistoryEntry[] {
    const updated = [...history, entry]
    // FIFO eviction
    return updated.slice(-MAX_HISTORY)
}

// ── Mode Result Union + Helper ────────────────────────────────────────────────

/** Discriminated union of all mode-specific computation results. */
export type ModeResult =
    | ReturnType<typeof computeFutures>
    | ReturnType<typeof computeOptions>
    | ReturnType<typeof computeForex>
    | ReturnType<typeof computeCrypto>

/** Type-safe extraction of rrRatio from any mode result. Options mode has no rrRatio. */
export function getModeRR(result: ModeResult | null): number {
    if (!result) return 0
    if ('rrRatio' in result) return result.rrRatio
    return 0
}
