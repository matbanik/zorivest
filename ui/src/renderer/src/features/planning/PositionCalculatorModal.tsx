import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import { useAccounts } from '@/hooks/useAccounts'
import TickerAutocomplete from '@/components/TickerAutocomplete'

// ── Equity Position Calculator (AC-13, AC-14, AC-15) ─────────────────────

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

                    {/* Outputs (AC-15) */}
                    <div className="border-t border-bg-subtle pt-4">
                        <h3 className="text-xs text-fg-muted mb-3 uppercase tracking-wider">Results</h3>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="px-3 py-2 rounded-md bg-bg">
                                <span className="block text-xs text-fg-muted">Shares</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg font-semibold text-fg font-mono" data-testid="calc-shares-output">
                                        {result.shares.toLocaleString()}
                                    </span>
                                    {/* C2: Copy-to-clipboard */}
                                    <button
                                        data-testid="calc-copy-shares-btn"
                                        onClick={handleCopyShares}
                                        className="text-fg-muted hover:text-fg text-xs cursor-pointer transition-colors"
                                        aria-label="Copy shares to clipboard"
                                        title="Copy shares to clipboard"
                                    >
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
                                <span
                                    className={`text-lg font-semibold font-mono ${result.rrRatio >= 2 ? 'text-green-400' : result.rrRatio >= 1 ? 'text-yellow-400' : 'text-red-400'}`}
                                    data-testid="calc-rr-output"
                                >
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

                        {/* Warning for >100% position (AC-15) */}
                        {result.positionPercent > 100 && (
                            <div className="mt-3 px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-xs" data-testid="calc-oversize-warning">
                                ⚠️ Position is {result.positionPercent}% of account — exceeds 100%
                            </div>
                        )}

                        <div className="mt-3 text-xs text-fg-muted text-center">
                            Risk/Share: ${result.riskPerShare.toFixed(2)} · Position: {result.positionPercent}% of account
                        </div>
                    </div>

                    {/* Apply to Plan — plan picker + toggle switches */}
                    {fromPlanContext && (
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
