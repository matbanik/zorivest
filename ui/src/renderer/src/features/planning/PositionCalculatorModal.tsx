import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import TickerAutocomplete from '@/components/TickerAutocomplete'

// ── Equity Position Calculator (AC-13, AC-14, AC-15) ─────────────────────

interface PositionCalculatorModalProps {
    isOpen: boolean
    onClose: () => void
}

export default function PositionCalculatorModal({ isOpen, onClose }: PositionCalculatorModalProps) {
    const [accountSize, setAccountSize] = useState<number>(100000)
    const [riskPercent, setRiskPercent] = useState<number>(1)
    const [entryPrice, setEntryPrice] = useState<number>(0)
    const [stopPrice, setStopPrice] = useState<number>(0)
    const [targetPrice, setTargetPrice] = useState<number>(0)
    const [copyFeedback, setCopyFeedback] = useState(false)
    const [ticker, setTicker] = useState('')  // C4: ticker field
    const [quoteFetching, setQuoteFetching] = useState(false)  // C3: loading state
    const { setStatus } = useStatusBar()
    const prevEntryRef = useRef<number>(0)  // C3: preserve user entry price on fail

    // Keyboard shortcuts
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) onClose()
        }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [isOpen, onClose])

    // C3: Fetch live quote when ticker changes — auto-fill entry price
    useEffect(() => {
        if (!ticker) return

        let cancelled = false
        setQuoteFetching(true)
        apiFetch<{ last_price: number }>(`/api/v1/market-data/quote?ticker=${encodeURIComponent(ticker)}`)
            .then((quote) => {
                if (!cancelled) {
                    setEntryPrice(Math.round(quote.last_price * 100) / 100)
                    setQuoteFetching(false)
                }
            })
            .catch((err: unknown) => {
                if (!cancelled) {
                    setQuoteFetching(false)
                    setStatus(`Could not fetch quote: ${err instanceof Error ? err.message : 'error'}`)
                    // AC-C3-4: preserve existing entry price — no setEntryPrice call
                }
            })
        return () => { cancelled = true }
    }, [ticker, setStatus])

    // Listen for pre-fill events from Trade Plan (T2)
    useEffect(() => {
        const handler = (e: Event) => {
            const detail = (e as CustomEvent).detail
            if (detail) {
                if (detail.entry_price != null) setEntryPrice(detail.entry_price)
                if (detail.stop_loss != null) setStopPrice(detail.stop_loss)
                if (detail.target_price != null) setTargetPrice(detail.target_price)
                if (detail.ticker) setTicker(detail.ticker)  // C4: pick up ticker
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
    }, [])

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" data-testid="calculator-modal" role="dialog" aria-modal="true" aria-labelledby="calc-modal-heading">
            <div className="bg-bg-elevated border border-bg-subtle rounded-lg shadow-xl w-[420px] max-h-[90vh] overflow-y-auto">
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
                            placeholder="Search ticker..."
                            data-testid="calc-ticker"
                        />
                        {quoteFetching && (
                            <span
                                data-testid="calc-quote-loading"
                                className="text-xs text-fg-muted mt-1 block"
                            >
                                Fetching quote…
                            </span>
                        )}
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
