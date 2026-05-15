import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import { useAccounts } from '@/hooks/useAccounts'
import TickerAutocomplete from '@/components/TickerAutocomplete'
import {
    type CalcMode,
    type FuturesInputs,
    type OptionsInputs,
    type ForexInputs,
    type ForexLotType,
    type CryptoInputs,
    type Scenario,
    type HistoryEntry,
    CALC_MODES,
    FUTURES_PRESETS,
    computeFutures,
    computeOptions,
    computeForex,
    computeCrypto,
    getWarnings,
    addScenario,
    removeScenario,
    addToHistory,
    getModeRR,
} from './calculatorModes'

// ── Position Calculator (AC-13, AC-14, AC-15, MEU-155) ───────────────────

interface PositionCalculatorModalProps {
    isOpen: boolean
    onClose: () => void
    /** When true, the "Apply to Plan" button is enabled (opened from Trade Plan form). */
    fromPlanContext?: boolean
}

// ── Toggle field keys for Apply to Plan ──────────────────────────────────

const APPLY_TOGGLE_KEYS = ['shares_planned', 'position_size', 'entry_price', 'stop_loss', 'target_price', 'account_id'] as const
type ApplyToggleKey = typeof APPLY_TOGGLE_KEYS[number]

const TOGGLE_LABELS: Record<ApplyToggleKey, string> = {
    shares_planned: 'Shares',
    position_size: 'Position Size',
    entry_price: 'Entry Price',
    stop_loss: 'Stop Loss',
    target_price: 'Target',
    account_id: 'Account',
}

function loadToggles(): Record<ApplyToggleKey, boolean> {
    try {
        const saved = localStorage.getItem('zorivest:calc-apply-toggles')
        if (saved) return JSON.parse(saved)
    } catch { /* ignore */ }
    // Default: all on
    return Object.fromEntries(APPLY_TOGGLE_KEYS.map(k => [k, true])) as Record<ApplyToggleKey, boolean>
}

function saveToggles(toggles: Record<ApplyToggleKey, boolean>) {
    try { localStorage.setItem('zorivest:calc-apply-toggles', JSON.stringify(toggles)) } catch { /* ignore */ }
}

// ── Minimal plan shape for the picker ────────────────────────────────────

interface PlanSummary {
    id: number
    ticker: string
    strategy_name: string
    status: string
    direction: string
}

export default function PositionCalculatorModal({ isOpen, onClose, fromPlanContext = false }: PositionCalculatorModalProps) {
    const [accountSize, setAccountSize] = useState<number>(0)
    const [riskPercent, setRiskPercent] = useState<number>(1)
    const [entryPrice, setEntryPrice] = useState<number>(0)
    const [stopPrice, setStopPrice] = useState<number>(0)
    const [targetPrice, setTargetPrice] = useState<number>(0)
    const [copyFeedback, setCopyFeedback] = useState(false)
    const [ticker, setTicker] = useState('')  // C4: ticker field
    const [quoteFetching, setQuoteFetching] = useState(false)  // C3: loading state
    const [selectedAccount, setSelectedAccount] = useState<string>('__ALL__')  // MEU-71b: default All Accounts per 06h L80
    const { setStatus } = useStatusBar()
    const { accounts, portfolioTotal, isLoading } = useAccounts()  // MEU-71b: account data

    // MEU-155: Mode selector state
    const [calcMode, setCalcMode] = useState<CalcMode>('equity')

    // MEU-155: Futures mode state
    const [futuresInputs, setFuturesInputs] = useState<FuturesInputs>({ multiplier: 50, tickSize: 0.25, margin: 12980 })
    const [futuresPreset, setFuturesPreset] = useState<string>('ES')

    // MEU-155: Options mode state
    const [optionsInputs, setOptionsInputs] = useState<OptionsInputs>({
        type: 'call', premium: 0, delta: 0.5, underlyingPrice: 0, multiplier: 100,
    })

    // MEU-155: Forex mode state
    const [forexInputs, setForexInputs] = useState<ForexInputs>({
        pair: 'EUR/USD', lotType: 'standard', pipValue: 10, leverage: 50,
    })

    // MEU-155: Crypto mode state
    const [cryptoInputs, setCryptoInputs] = useState<CryptoInputs>({
        leverage: 1, feeRate: 0.1,
    })

    // MEU-155: Scenario comparison state
    const [scenarios, setScenarios] = useState<Scenario[]>([])

    // MEU-155: History state
    const [history, setHistory] = useState<HistoryEntry[]>([])

    // Plan picker state
    const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null)
    const [planSearch, setPlanSearch] = useState('')
    const [applyToggles, setApplyToggles] = useState<Record<ApplyToggleKey, boolean>>(loadToggles)

    // Fetch trade plans for the picker
    const { data: plans = [] } = useQuery<PlanSummary[]>({
        queryKey: ['trade-plans-for-calc'],
        queryFn: async () => {
            try {
                const result = await apiFetch<PlanSummary[]>('/api/v1/trade-plans?limit=200')
                return result
            } catch { return [] }
        },
        enabled: isOpen,
        refetchInterval: 10_000,
    })

    // Filtered plans for picker
    const filteredPlans = useMemo(() => {
        if (!planSearch) return plans
        const q = planSearch.toLowerCase()
        return plans.filter(p =>
            p.ticker.toLowerCase().includes(q) ||
            p.strategy_name.toLowerCase().includes(q) ||
            String(p.id).includes(q)
        )
    }, [plans, planSearch])

    // Selected plan label
    const selectedPlanLabel = useMemo(() => {
        if (!selectedPlanId) return ''
        const p = plans.find(pl => pl.id === selectedPlanId)
        if (!p) return ''
        return `#${p.id} ${p.ticker} — ${p.strategy_name || p.direction}`
    }, [selectedPlanId, plans])

    // Toggle handler
    const handleToggle = useCallback((key: ApplyToggleKey) => {
        setApplyToggles(prev => {
            const next = { ...prev, [key]: !prev[key] }
            saveToggles(next)
            return next
        })
    }, [])

    // MEU-71b AC-2/AC-3/AC-5: Handle account selection → auto-fill balance
    const handleAccountChange = useCallback((accountId: string) => {
        setSelectedAccount(accountId)
        if (accountId === '__ALL__') {
            // AC-3: Portfolio total
            setAccountSize(portfolioTotal)
        } else if (accountId && accountId !== '') {
            // AC-2: Individual account balance
            const acct = accounts.find(a => a.account_id === accountId)
            if (acct?.latest_balance != null) {
                setAccountSize(acct.latest_balance)
            }
        }
        // AC-1: "" (Manual) — keep existing value, no auto-fill
    }, [accounts, portfolioTotal])

    // MEU-71b: one-shot initial fill when accounts finish loading and default is __ALL__
    // With accountSize=0 initial, zero-total portfolios are correct by default (0=0).
    // Only sync when there's a positive balance to fill in.
    // handleAccountChange covers all subsequent switches (including back to __ALL__).
    const initialFillDone = useRef(false)
    useEffect(() => {
        if (!initialFillDone.current && !isLoading && selectedAccount === '__ALL__' && portfolioTotal > 0) {
            initialFillDone.current = true
            setAccountSize(portfolioTotal)
        }
    }, [isLoading, portfolioTotal, selectedAccount])

    // Keyboard shortcuts
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) onClose()
        }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [isOpen, onClose])

    // C3: Fetch live quote when ticker is *selected* from autocomplete dropdown
    // (Not on every keystroke — that caused the modal to jump due to "Fetching quote…" layout shift)
    const handleTickerSelect = useCallback((result: { symbol: string }) => {
        const sym = result.symbol
        setTicker(sym)

        // Auto-switch calculator mode based on known instrument patterns.
        // Futures: match against FUTURES_PRESETS keys (ES, NQ, YM, CL, GC).
        // Forex: detect pairs like EUR/USD, EURUSD, GBP/JPY.
        // Crypto: detect common crypto tickers (BTC, ETH, SOL, etc.) or BTC-USD patterns.
        const upperSym = sym.toUpperCase()
        if (upperSym in FUTURES_PRESETS) {
            setCalcMode('futures')
            setFuturesPreset(upperSym)
            setFuturesInputs(FUTURES_PRESETS[upperSym])
        } else if (/^[A-Z]{3}\/[A-Z]{3}$/.test(upperSym) || /^[A-Z]{6}$/.test(upperSym) && ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD'].some(c => upperSym.includes(c) && upperSym.length === 6)) {
            setCalcMode('forex')
        } else if (/^(BTC|ETH|SOL|ADA|XRP|DOGE|DOT|AVAX|MATIC|LINK)([-/]?(USD|USDT|USDC|EUR|BTC))?$/i.test(upperSym)) {
            setCalcMode('crypto')
        }
        // Equity is the default — no switch needed

        setQuoteFetching(true)
        apiFetch<{ price: number }>(`/api/v1/market-data/quote?ticker=${encodeURIComponent(sym)}`)
            .then((quote) => {
                const price = Math.round(quote.price * 100) / 100
                setEntryPrice(price)
                // Auto-fill stop and target when both are still at 0 (fresh calculator)
                setStopPrice((prev) => (prev === 0 ? price : prev))
                setTargetPrice((prev) => (prev === 0 ? price : prev))
                setQuoteFetching(false)
            })
            .catch((err: unknown) => {
                setQuoteFetching(false)
                setStatus(`Could not fetch quote: ${err instanceof Error ? err.message : 'error'}`)
                // AC-C3-4: preserve existing entry price — no setEntryPrice call
            })
    }, [setStatus])

    // Listen for pre-fill events from Trade Plan (T2)
    useEffect(() => {
        const handler = (e: Event) => {
            const detail = (e as CustomEvent).detail
            if (detail) {
                if (detail.entry_price != null) setEntryPrice(detail.entry_price)
                if (detail.stop_loss != null) setStopPrice(detail.stop_loss)
                if (detail.target_price != null) setTargetPrice(detail.target_price)
                if (detail.ticker) setTicker(detail.ticker)  // C4: pick up ticker
                // Auto-select the originating plan in the picker
                if (detail.plan_id != null && detail.plan_id !== '__new__') {
                    setSelectedPlanId(detail.plan_id)
                    setPlanSearch('')
                }
            }
        }
        window.addEventListener('zorivest:open-calculator', handler)
        return () => window.removeEventListener('zorivest:open-calculator', handler)
    }, [])

    // Equity computation (AC-15)
    const result = useMemo(() => {
        const risk1R = accountSize * (riskPercent / 100)
        const riskPerShare = Math.abs(entryPrice - stopPrice)
        const shares = riskPerShare > 0 ? Math.floor(risk1R / riskPerShare) : 0
        const dollarRisk = shares * riskPerShare
        const rewardPerShare = Math.abs(targetPrice - entryPrice)
        const rrRatio = riskPerShare > 0 ? rewardPerShare / riskPerShare : 0
        const positionValue = shares * entryPrice
        const positionPercent = accountSize > 0 ? (positionValue / accountSize) * 100 : 0

        return {
            risk1R,
            riskPerShare,
            shares,
            dollarRisk,
            rrRatio: Math.round(rrRatio * 100) / 100,
            positionValue,
            positionPercent: Math.round(positionPercent * 10) / 10,
        }
    }, [accountSize, riskPercent, entryPrice, stopPrice, targetPrice])

    // MEU-155: Mode-specific computation results
    const modeResult = useMemo(() => {
        switch (calcMode) {
            case 'futures':
                return computeFutures(accountSize, riskPercent, entryPrice, stopPrice, targetPrice, futuresInputs)
            case 'options':
                return computeOptions(accountSize, riskPercent, optionsInputs)
            case 'forex':
                return computeForex(accountSize, riskPercent, entryPrice, stopPrice, targetPrice, forexInputs)
            case 'crypto':
                return computeCrypto(accountSize, riskPercent, entryPrice, stopPrice, targetPrice, cryptoInputs)
            default:
                return null
        }
    }, [calcMode, accountSize, riskPercent, entryPrice, stopPrice, targetPrice, futuresInputs, optionsInputs, forexInputs, cryptoInputs])

    // MEU-155: Mode-specific warnings
    const warnings = useMemo(() => {
        const resultData = calcMode === 'equity'
            ? { positionPercent: result.positionPercent }
            : (modeResult ?? {})
        return getWarnings(calcMode, accountSize, riskPercent, resultData as Record<string, number>)
    }, [calcMode, accountSize, riskPercent, result.positionPercent, modeResult])

    // MEU-155: Futures preset handler
    const handleFuturesPreset = useCallback((preset: string) => {
        setFuturesPreset(preset)
        const p = FUTURES_PRESETS[preset]
        if (p) setFuturesInputs(p)
    }, [])

    // MEU-155: Save scenario
    const handleSaveScenario = useCallback(() => {
        const shares = calcMode === 'equity' ? result.shares : 0
        const risk = calcMode === 'equity' ? result.dollarRisk : 0
        const rr = calcMode === 'equity' ? result.rrRatio : getModeRR(modeResult)
        const scenario: Scenario = {
            id: `s-${Date.now()}`,
            mode: calcMode,
            label: ticker || `${calcMode}-${scenarios.length + 1}`,
            accountSize, riskPercent, entryPrice, stopPrice, targetPrice,
            resultShares: shares, resultRisk: risk, resultRR: rr,
            timestamp: Date.now(),
        }
        setScenarios(prev => addScenario(prev, scenario))
    }, [calcMode, result, modeResult, ticker, accountSize, riskPercent, entryPrice, stopPrice, targetPrice, scenarios.length])

    // MEU-155: Auto-add to history on meaningful computation
    const lastHistoryRef = useRef<string>('')
    useEffect(() => {
        if (entryPrice <= 0 || stopPrice <= 0) return
        const key = `${calcMode}-${accountSize}-${riskPercent}-${entryPrice}-${stopPrice}-${targetPrice}`
        if (key === lastHistoryRef.current) return
        lastHistoryRef.current = key
        const shares = calcMode === 'equity' ? result.shares : 0
        const risk = calcMode === 'equity' ? result.dollarRisk : 0
        const rr = calcMode === 'equity' ? result.rrRatio : getModeRR(modeResult)
        const entry: HistoryEntry = {
            id: `h-${Date.now()}`,
            mode: calcMode,
            accountSize, riskPercent, entryPrice, stopPrice, targetPrice,
            resultShares: shares, resultRisk: risk, resultRR: rr,
            timestamp: Date.now(),
        }
        setHistory(prev => addToHistory(prev, entry))
    }, [calcMode, accountSize, riskPercent, entryPrice, stopPrice, targetPrice, result, modeResult])

    // MEU-155: Load from history
    const handleLoadHistory = useCallback((entry: HistoryEntry) => {
        setCalcMode(entry.mode)
        setAccountSize(entry.accountSize)
        setRiskPercent(entry.riskPercent)
        setEntryPrice(entry.entryPrice)
        setStopPrice(entry.stopPrice)
        setTargetPrice(entry.targetPrice)
    }, [])

    // C2: Copy shares to clipboard
    const handleCopyShares = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(String(result.shares))
            setCopyFeedback(true)
            setTimeout(() => setCopyFeedback(false), 1500)
        } catch {
            // Clipboard not available in some environments
        }
    }, [result.shares])

    const handleReset = useCallback(() => {
        setAccountSize(100000)
        setRiskPercent(1)
        setEntryPrice(0)
        setStopPrice(0)
        setTargetPrice(0)
        setTicker('')  // C4: reset ticker
        setQuoteFetching(false)  // C3: clear loading state
        setSelectedAccount('')  // MEU-71b: reset account selection
        setSelectedPlanId(null)
        setPlanSearch('')
    }, [])

    // Apply calculator results to the selected trade plan
    const handleApplyToPlan = useCallback(() => {
        if (!selectedPlanId) return
        const detail: Record<string, unknown> = { plan_id: selectedPlanId }
        if (applyToggles.shares_planned) detail.shares_planned = result.shares
        if (applyToggles.position_size) detail.position_size = result.positionValue
        if (applyToggles.entry_price) detail.entry_price = entryPrice || undefined
        if (applyToggles.stop_loss) detail.stop_loss = stopPrice || undefined
        if (applyToggles.target_price) detail.target_price = targetPrice || undefined
        if (applyToggles.account_id) {
            // Send '__ALL__' so Trade Plan can resolve to largest-balance account
            detail.account_id = selectedAccount === '' ? undefined : selectedAccount
        }
        window.dispatchEvent(new CustomEvent('zorivest:calculator-apply', { detail }))
        setStatus(`Applied to plan #${selectedPlanId}`)
        onClose()
    }, [selectedPlanId, applyToggles, result.shares, result.positionValue, selectedAccount, entryPrice, stopPrice, targetPrice, setStatus, onClose])

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 bg-black/50 flex items-start justify-center z-50 pt-[10vh]" data-testid="calculator-modal" role="dialog" aria-modal="true" aria-labelledby="calc-modal-heading">
            <div className="bg-bg-elevated border border-bg-subtle rounded-lg shadow-xl w-[500px] max-h-[80vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-bg-subtle">
                    <h2 id="calc-modal-heading" className="text-md font-semibold text-fg">🧮 Position Calculator</h2>
                    <button
                        onClick={onClose}
                        className="text-fg-muted hover:text-fg cursor-pointer"
                        data-testid="close-calculator"
                        aria-label="Close calculator"
                    >
                        ✕
                    </button>
                </div>

                <div className="p-4 space-y-4">
                    {/* MEU-155: Mode selector */}
                    <div className="flex gap-1 p-1 rounded-lg bg-bg" data-testid="calc-mode-selector">
                        {CALC_MODES.map((m) => (
                            <button
                                key={m.value}
                                data-testid={`calc-mode-${m.value}`}
                                onClick={() => setCalcMode(m.value)}
                                className={`flex-1 px-2 py-1 text-xs rounded-md transition-colors cursor-pointer ${
                                    calcMode === m.value
                                        ? 'bg-accent/20 text-accent font-medium'
                                        : 'text-fg-muted hover:text-fg'
                                }`}
                            >
                                {m.icon} {m.label}
                            </button>
                        ))}
                    </div>

                    {/* C4: Ticker search + C3: quote loading indicator */}
                    <div>
                        <label className="block text-xs text-fg-muted mb-1">Ticker</label>
                        <TickerAutocomplete
                            value={ticker}
                            onChange={setTicker}
                            onSelect={handleTickerSelect}
                            placeholder="Search ticker..."
                            data-testid="calc-ticker"
                        />
                        {/* Fixed-height container prevents layout shift when loading indicator appears/disappears */}
                        <div className="h-5 mt-1">
                            {quoteFetching && (
                                <span
                                    data-testid="calc-quote-loading"
                                    className="text-xs text-fg-muted block"
                                >
                                    Fetching quote…
                                </span>
                            )}
                        </div>
                    </div>

                    {/* MEU-71b: Account Selection (AC-1) */}
                    <div>
                        <label htmlFor="calc-account-select" className="block text-xs text-fg-muted mb-1">Account</label>
                        <select
                            id="calc-account-select"
                            data-testid="calc-account-select"
                            value={selectedAccount}
                            onChange={(e) => handleAccountChange(e.target.value)}
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        >
                            <option value="">Manual</option>
                            <option value="__ALL__">All Accounts ({portfolioTotal.toLocaleString(undefined, { style: 'currency', currency: 'USD' })})</option>
                            {accounts.map((acct) => (
                                <option key={acct.account_id} value={acct.account_id}>
                                    {acct.name} {acct.latest_balance != null ? `($${acct.latest_balance.toLocaleString()})` : ''}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Inputs (AC-14) */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label htmlFor="calc-account-size" className="block text-xs text-fg-muted mb-1">Account Size ($)</label>
                            <input
                                id="calc-account-size"
                                data-testid="calc-account-size"
                                type="number"
                                value={accountSize}
                                onChange={(e) => setAccountSize(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                        </div>
                        <div>
                            <label htmlFor="calc-risk-percent" className="block text-xs text-fg-muted mb-1">Risk %</label>
                            <input
                                id="calc-risk-percent"
                                data-testid="calc-risk-percent"
                                type="number"
                                step="0.1"
                                value={riskPercent}
                                onChange={(e) => setRiskPercent(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                        <div>
                            <label htmlFor="calc-entry-price" className="block text-xs text-fg-muted mb-1">Entry Price</label>
                            <input
                                id="calc-entry-price"
                                data-testid="calc-entry-price"
                                type="number"
                                step="0.01"
                                value={entryPrice || ''}
                                onChange={(e) => setEntryPrice(parseFloat(e.target.value) || 0)}
                                placeholder="0.00"
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                        </div>
                        <div>
                            <label htmlFor="calc-stop-price" className="block text-xs text-fg-muted mb-1">Stop Price</label>
                            <input
                                id="calc-stop-price"
                                data-testid="calc-stop-price"
                                type="number"
                                step="0.01"
                                value={stopPrice || ''}
                                onChange={(e) => setStopPrice(parseFloat(e.target.value) || 0)}
                                placeholder="0.00"
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                        </div>
                        <div>
                            <label htmlFor="calc-target-price" className="block text-xs text-fg-muted mb-1">Target Price</label>
                            <input
                                id="calc-target-price"
                                data-testid="calc-target-price"
                                type="number"
                                step="0.01"
                                value={targetPrice || ''}
                                onChange={(e) => setTargetPrice(parseFloat(e.target.value) || 0)}
                                placeholder="0.00"
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                        </div>
                    </div>

                    {/* MEU-155: Mode-specific inputs */}
                    {calcMode === 'futures' && (
                        <div className="space-y-2" data-testid="calc-futures-inputs">
                            <div className="flex gap-2">
                                <label className="block text-xs text-fg-muted mb-1">Preset</label>
                                <select data-testid="calc-futures-preset" value={futuresPreset} onChange={(e) => handleFuturesPreset(e.target.value)} className="px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg">
                                    {Object.keys(FUTURES_PRESETS).map((k) => <option key={k} value={k}>{k}</option>)}
                                </select>
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                                <div><label className="block text-xs text-fg-muted">Multiplier</label><input data-testid="calc-futures-multiplier" type="number" value={futuresInputs.multiplier} onChange={(e) => setFuturesInputs(p => ({ ...p, multiplier: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                                <div><label className="block text-xs text-fg-muted">Tick Size</label><input data-testid="calc-futures-tick" type="number" step="0.01" value={futuresInputs.tickSize} onChange={(e) => setFuturesInputs(p => ({ ...p, tickSize: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                                <div><label className="block text-xs text-fg-muted">Margin</label><input data-testid="calc-futures-margin" type="number" value={futuresInputs.margin} onChange={(e) => setFuturesInputs(p => ({ ...p, margin: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                            </div>
                        </div>
                    )}

                    {calcMode === 'options' && (
                        <div className="space-y-2" data-testid="calc-options-inputs">
                            <div className="grid grid-cols-2 gap-2">
                                <div><label className="block text-xs text-fg-muted">Type</label><select data-testid="calc-options-type" value={optionsInputs.type} onChange={(e) => setOptionsInputs(p => ({ ...p, type: e.target.value as 'call' | 'put' }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg"><option value="call">Call</option><option value="put">Put</option></select></div>
                                <div><label className="block text-xs text-fg-muted">Premium</label><input data-testid="calc-options-premium" type="number" step="0.01" value={optionsInputs.premium || ''} onChange={(e) => setOptionsInputs(p => ({ ...p, premium: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" placeholder="0.00" /></div>
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                                <div><label className="block text-xs text-fg-muted">Delta</label><input data-testid="calc-options-delta" type="number" step="0.01" value={optionsInputs.delta} onChange={(e) => setOptionsInputs(p => ({ ...p, delta: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                                <div><label className="block text-xs text-fg-muted">Underlying</label><input data-testid="calc-options-underlying" type="number" step="0.01" value={optionsInputs.underlyingPrice || ''} onChange={(e) => setOptionsInputs(p => ({ ...p, underlyingPrice: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" placeholder="0.00" /></div>
                                <div><label className="block text-xs text-fg-muted">Multiplier</label><input type="number" value={optionsInputs.multiplier} onChange={(e) => setOptionsInputs(p => ({ ...p, multiplier: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                            </div>
                        </div>
                    )}

                    {calcMode === 'forex' && (
                        <div className="space-y-2" data-testid="calc-forex-inputs">
                            <div className="grid grid-cols-2 gap-2">
                                <div><label className="block text-xs text-fg-muted">Lot Type</label><select data-testid="calc-forex-lot" value={forexInputs.lotType} onChange={(e) => setForexInputs(p => ({ ...p, lotType: e.target.value as ForexLotType }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg"><option value="standard">Standard (100K)</option><option value="mini">Mini (10K)</option><option value="micro">Micro (1K)</option></select></div>
                                <div><label className="block text-xs text-fg-muted">Leverage</label><input data-testid="calc-forex-leverage" type="number" value={forexInputs.leverage} onChange={(e) => setForexInputs(p => ({ ...p, leverage: +e.target.value || 1 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                            </div>
                            <div><label className="block text-xs text-fg-muted">Pip Value ($)</label><input data-testid="calc-forex-pip" type="number" step="0.01" value={forexInputs.pipValue} onChange={(e) => setForexInputs(p => ({ ...p, pipValue: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                        </div>
                    )}

                    {calcMode === 'crypto' && (
                        <div className="space-y-2" data-testid="calc-crypto-inputs">
                            <div className="grid grid-cols-2 gap-2">
                                <div><label className="block text-xs text-fg-muted">Leverage</label><input data-testid="calc-crypto-leverage" type="number" value={cryptoInputs.leverage} onChange={(e) => setCryptoInputs(p => ({ ...p, leverage: +e.target.value || 1 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                                <div><label className="block text-xs text-fg-muted">Fee Rate (%)</label><input data-testid="calc-crypto-fee" type="number" step="0.01" value={cryptoInputs.feeRate} onChange={(e) => setCryptoInputs(p => ({ ...p, feeRate: +e.target.value || 0 }))} className="w-full px-2 py-1 text-xs rounded bg-bg border border-bg-subtle text-fg" /></div>
                            </div>
                        </div>
                    )}

                    {/* Outputs — equity mode (AC-15) */}
                    {calcMode === 'equity' && (
                    <div className="border-t border-bg-subtle pt-4">
                        <h3 className="text-xs text-fg-muted mb-3 uppercase tracking-wider">Results</h3>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="px-3 py-2 rounded-md bg-bg">
                                <span className="block text-xs text-fg-muted">Shares</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg font-semibold text-fg font-mono" data-testid="calc-shares-output">
                                        {result.shares.toLocaleString()}
                                    </span>
                                    <button data-testid="calc-copy-shares-btn" onClick={handleCopyShares} className="text-fg-muted hover:text-fg text-xs cursor-pointer transition-colors" aria-label="Copy shares to clipboard" title="Copy shares to clipboard">
                                        {copyFeedback ? '✓' : '📋'}
                                    </button>
                                </div>
                            </div>
                            <div className="px-3 py-2 rounded-md bg-bg">
                                <span className="block text-xs text-fg-muted">Dollar Risk (1R)</span>
                                <span className="text-lg font-semibold text-fg font-mono" data-testid="calc-dollar-risk-output">
                                    ${result.dollarRisk.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div className="px-3 py-2 rounded-md bg-bg">
                                <span className="block text-xs text-fg-muted">R:R Ratio</span>
                                <span className={`text-lg font-semibold font-mono ${result.rrRatio >= 2 ? 'text-green-400' : result.rrRatio >= 1 ? 'text-yellow-400' : 'text-red-400'}`} data-testid="calc-rr-output">
                                    {result.rrRatio.toFixed(2)}
                                </span>
                            </div>
                            <div className="px-3 py-2 rounded-md bg-bg">
                                <span className="block text-xs text-fg-muted">Position Value</span>
                                <span className="text-lg font-semibold text-fg font-mono" data-testid="calc-position-value-output">
                                    ${result.positionValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                        </div>
                        {result.positionPercent > 100 && (
                            <div className="mt-3 px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-xs" data-testid="calc-oversize-warning">
                                ⚠️ Position is {result.positionPercent}% of account — exceeds 100%
                            </div>
                        )}
                        <div className="mt-3 text-xs text-fg-muted text-center">
                            Risk/Share: ${result.riskPerShare.toFixed(2)} · Position: {result.positionPercent}% of account
                        </div>
                    </div>
                    )}

                    {/* Outputs — mode-specific results (MEU-155) */}
                    {calcMode !== 'equity' && modeResult && (
                    <div className="border-t border-bg-subtle pt-4" data-testid="calc-mode-results">
                        <h3 className="text-xs text-fg-muted mb-3 uppercase tracking-wider">Results — {CALC_MODES.find(m => m.value === calcMode)?.label}</h3>
                        <div className="grid grid-cols-2 gap-2">
                            {Object.entries(modeResult).map(([k, v]) => (
                                <div key={k} className="px-3 py-1.5 rounded-md bg-bg">
                                    <span className="block text-xs text-fg-muted">{k.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase())}</span>
                                    <span className="text-sm font-semibold text-fg font-mono" data-testid={`calc-result-${k}`}>
                                        {typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 6 }) : String(v)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                    )}

                    {/* MEU-155: Warnings */}
                    {warnings.length > 0 && (
                        <div className="space-y-1" data-testid="calc-warnings">
                            {warnings.map((w, i) => (
                                <div key={i} className={`px-3 py-1.5 rounded-md text-xs ${
                                    w.level === 'danger' ? 'bg-red-500/10 border border-red-500/20 text-red-400'
                                    : w.level === 'warn' ? 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-400'
                                    : 'bg-blue-500/10 border border-blue-500/20 text-blue-400'
                                }`} data-testid="calc-warning">
                                    {w.level === 'danger' ? '🚨' : w.level === 'warn' ? '⚠️' : 'ℹ️'} {w.message}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* MEU-155: Scenario comparison */}
                    <div className="border-t border-bg-subtle pt-3">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-xs text-fg-muted uppercase tracking-wider">Scenarios</h3>
                            <button data-testid="calc-save-scenario" onClick={handleSaveScenario} className="text-xs px-2 py-0.5 rounded bg-accent/10 text-accent hover:bg-accent/20 cursor-pointer">+ Save</button>
                        </div>
                        {scenarios.length > 0 ? (
                            <div className="space-y-1 max-h-24 overflow-y-auto" data-testid="calc-scenarios">
                                {scenarios.map((s) => (
                                    <div key={s.id} className="flex items-center gap-2 px-2 py-1 rounded bg-bg text-xs" data-testid="calc-scenario-row">
                                        <span className="text-fg-muted">{CALC_MODES.find(m => m.value === s.mode)?.icon}</span>
                                        <span className="text-fg flex-1 truncate">{s.label}</span>
                                        <span className="text-fg-muted font-mono">R:R {s.resultRR.toFixed(2)}</span>
                                        <button onClick={() => setScenarios(prev => removeScenario(prev, s.id))} className="text-fg-muted hover:text-red-400 cursor-pointer">×</button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-xs text-fg-muted">Save current inputs to compare scenarios</p>
                        )}
                    </div>

                    {/* MEU-155: History */}
                    {history.length > 0 && (
                    <div className="border-t border-bg-subtle pt-3">
                        <h3 className="text-xs text-fg-muted mb-2 uppercase tracking-wider">History ({history.length})</h3>
                        <div className="space-y-1 max-h-20 overflow-y-auto" data-testid="calc-history">
                            {[...history].reverse().map((h) => (
                                <button key={h.id} onClick={() => handleLoadHistory(h)} className="flex items-center gap-2 w-full px-2 py-1 rounded bg-bg text-xs hover:bg-bg-subtle cursor-pointer text-left" data-testid="calc-history-row">
                                    <span className="text-fg-muted">{CALC_MODES.find(m => m.value === h.mode)?.icon}</span>
                                    <span className="text-fg font-mono">${h.entryPrice.toFixed(2)}</span>
                                    <span className="text-fg-muted">→</span>
                                    <span className="text-fg font-mono">${h.targetPrice.toFixed(2)}</span>
                                    <span className="text-fg-muted ml-auto">{new Date(h.timestamp).toLocaleTimeString()}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                    )}

                    {/* Apply to Plan — plan picker + toggle switches (equity only) */}
                    {fromPlanContext && calcMode === 'equity' && (
                        <div className="border-t border-bg-subtle pt-4">
                            <h3 className="text-xs text-fg-muted mb-2 uppercase tracking-wider">Apply to Trade Plan</h3>

                            {/* Plan search + selection */}
                            <div className="mb-3">
                                {selectedPlanLabel ? (
                                    <div className="flex items-center gap-2">
                                        <div className="flex-1 px-3 py-1.5 text-sm rounded-md bg-bg border border-accent/30 text-fg">
                                            {selectedPlanLabel}
                                        </div>
                                        <button
                                            onClick={() => { setSelectedPlanId(null); setPlanSearch('') }}
                                            className="text-fg-muted hover:text-fg text-xs cursor-pointer"
                                            title="Clear selection"
                                        >
                                            ×
                                        </button>
                                    </div>
                                ) : (
                                    <>
                                        <input
                                            data-testid="calc-plan-search"
                                            type="text"
                                            value={planSearch}
                                            onChange={(e) => setPlanSearch(e.target.value)}
                                            placeholder="Filter plans..."
                                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg mb-1"
                                        />
                                        <div className="max-h-32 overflow-y-auto rounded-md border border-bg-subtle text-sm">
                                            {filteredPlans.map((p) => (
                                                <div
                                                    key={p.id}
                                                    data-testid={`calc-plan-option-${p.id}`}
                                                    onClick={() => { setSelectedPlanId(p.id); setPlanSearch('') }}
                                                    className="px-3 py-1.5 cursor-pointer transition-colors text-fg hover:bg-bg-subtle flex items-center gap-2"
                                                >
                                                    <span className="text-fg-muted text-xs">#{p.id}</span>
                                                    <span>{p.ticker}</span>
                                                    <span className="text-fg-muted text-xs truncate">{p.strategy_name || p.direction}</span>
                                                    <span className={`ml-auto text-xs ${p.status === 'active' ? 'text-blue-400' : p.status === 'executed' ? 'text-green-400' : 'text-fg-muted'}`}>
                                                        {p.status}
                                                    </span>
                                                </div>
                                            ))}
                                            {filteredPlans.length === 0 && (
                                                <div className="px-3 py-1.5 text-fg-muted text-xs">No plans found</div>
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Toggle switches */}
                            <div className="mb-3">
                                <span className="block text-xs text-fg-muted mb-2">Select what to copy to the plan:</span>
                                <div className="grid grid-cols-3 gap-x-3 gap-y-2">
                                    {APPLY_TOGGLE_KEYS.map((key) => (
                                        <label key={key} className="flex items-center gap-1.5 text-xs text-fg-muted cursor-pointer select-none">
                                            <button
                                                type="button"
                                                role="switch"
                                                aria-checked={applyToggles[key]}
                                                data-testid={`calc-toggle-${key}`}
                                                onClick={() => handleToggle(key)}
                                                className={`relative inline-flex h-4 w-7 items-center rounded-full transition-colors cursor-pointer ${applyToggles[key] ? 'bg-green-500' : 'bg-red-500/70'}`}
                                            >
                                                <span className={`inline-block h-3 w-3 rounded-full bg-white transition-transform ${applyToggles[key] ? 'translate-x-3.5' : 'translate-x-0.5'}`} />
                                            </button>
                                            {TOGGLE_LABELS[key]}
                                        </label>
                                    ))}
                                </div>
                                {/* Copying status summary */}
                                <div className="mt-2 text-xs text-fg-muted">
                                    {APPLY_TOGGLE_KEYS.some(k => applyToggles[k])
                                        ? <>Copying: <span className="text-green-400">{APPLY_TOGGLE_KEYS.filter(k => applyToggles[k]).map(k => TOGGLE_LABELS[k]).join(', ')}</span></>
                                        : <span className="text-red-400">Nothing selected</span>
                                    }
                                </div>
                            </div>

                            {/* Apply button */}
                            <div className="flex justify-center">
                                <button
                                    data-testid="calc-apply-to-plan-btn"
                                    onClick={handleApplyToPlan}
                                    disabled={!selectedPlanId}
                                    className={`px-4 py-1.5 text-sm rounded-md border transition-colors ${
                                        selectedPlanId
                                            ? 'border-accent/30 bg-accent/5 text-accent hover:bg-accent/10 cursor-pointer'
                                            : 'border-bg-subtle bg-bg text-fg-muted/50 cursor-not-allowed'
                                    }`}
                                    title={selectedPlanId ? `Apply values to plan #${selectedPlanId}` : 'Select a plan first'}
                                >
                                    📋 Apply to Plan{selectedPlanId ? ` #${selectedPlanId}` : ''}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Contribution CTA — non-equity modes don't support Apply to Plan yet */}
                    {fromPlanContext && calcMode !== 'equity' && (
                        <div
                            data-testid="calc-contribute-cta"
                            className="border-t border-bg-subtle pt-4"
                        >
                            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3">
                                <div className="flex items-start gap-3">
                                    <span className="text-lg mt-0.5">🚀</span>
                                    <div className="flex-1 space-y-1.5">
                                        <h3 className="text-sm font-medium text-amber-300">
                                            {CALC_MODES.find(m => m.value === calcMode)?.label} Trade Plans — Coming Soon
                                        </h3>
                                        <p className="text-xs text-fg-muted leading-relaxed">
                                            Position sizing for {CALC_MODES.find(m => m.value === calcMode)?.label.toLowerCase()} works great — but trade plans and trade records don't support this instrument type yet. We're building multi-asset trade planning and would love your help.
                                        </p>
                                        <button
                                            onClick={() => window.electron.openExternal('https://github.com/matbanik/zorivest/issues')}
                                            className="inline-flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 transition-colors mt-1 cursor-pointer bg-transparent border-none p-0"
                                        >
                                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 16 16">
                                                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                                            </svg>
                                            Contribute on GitHub →
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 pt-2 border-t border-bg-subtle">
                        <button
                            data-testid="calc-reset-btn"
                            onClick={handleReset}
                            className="px-4 py-1.5 text-sm rounded-md border border-bg-subtle bg-bg text-fg-muted hover:text-fg cursor-pointer"
                        >
                            Reset
                        </button>
                        <button
                            onClick={onClose}
                            className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer ml-auto"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
