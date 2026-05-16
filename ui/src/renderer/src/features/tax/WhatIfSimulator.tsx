/**
 * WhatIfSimulator — simulation form with G23 FormGuard + results display.
 *
 * Posts to POST /api/v1/tax/simulate and renders per-lot breakdown + tax impact summary.
 * API requires: {ticker, action, quantity, price, account_id, cost_basis_method}
 * API returns: {lot_details[], total_lt_gain, total_st_gain, estimated_tax, wash_risk, wash_sale_warnings[], wait_days}
 *
 * Ticker selector is populated from open lots in the selected account.
 * The simulator is a what-if analysis tool — it does not persist data.
 * Navigation guard (G23) warns before losing entered parameters.
 *
 * Source: 06g-gui-tax.md L273–294
 * MEU: MEU-154 (AC-154.10, AC-154.11)
 */

import { useState, useCallback, useEffect, useMemo } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

/** Matches actual SimulationResult dataclass from API */
interface SimulationResult {
    lot_details: LotDetail[]
    total_lt_gain: number
    total_st_gain: number
    estimated_tax: number
    wash_risk: boolean
    wash_sale_warnings: { warning_type: string; ticker: string; message: string; days_remaining: number }[]
    wait_days: number
}

interface LotDetail {
    lot_id: string
    quantity: number
    gain_amount: number
    is_long_term: boolean
    holding_period_days: number
    tax_type: string  // "short_term" | "long_term"
}

interface Account {
    account_id: string
    name: string
}

/** Open lot from GET /api/v1/tax/lots?status=open */
interface OpenLot {
    lot_id: string
    ticker: string
    quantity: number
    cost_basis: number
    account_id: string
    open_date: string
}

/** Unique ticker with aggregated lot info for the selector */
interface TickerOption {
    ticker: string
    totalShares: number
    lotCount: number
    avgCostBasis: number
}

interface WhatIfSimulatorProps {
    /** Callback to report dirty form state to parent (G23 form guard) */
    onDirtyChange?: (dirty: boolean) => void
}

/** Safe number extraction from API (handles Decimal strings, null, undefined) */
function n(v: unknown): number {
    if (v === null || v === undefined) return 0
    const num = Number(v)
    return isNaN(num) ? 0 : num
}

function formatCurrency(value: number): string {
    const abs = Math.abs(value)
    const formatted = abs.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    return value < 0 ? `-$${formatted}` : `$${formatted}`
}

export default function WhatIfSimulator({ onDirtyChange }: WhatIfSimulatorProps) {
    const [ticker, setTicker] = useState('')
    const [quantity, setQuantity] = useState<number>(0)
    const [price, setPrice] = useState<number>(0)
    const [accountId, setAccountId] = useState('')
    const [costBasisMethod, setCostBasisMethod] = useState('fifo')

    // Fetch accounts for the account selector
    const { data: accounts = [] } = useQuery<Account[]>({
        queryKey: ['accounts-list'],
        queryFn: async () => {
            try {
                const res = await apiFetch('/api/v1/accounts')
                if (Array.isArray(res)) return res
                if (res && Array.isArray(res.accounts)) return res.accounts
                return []
            } catch {
                return []
            }
        },
    })

    // Auto-select first account if none selected
    useEffect(() => {
        if (!accountId && accounts.length > 0) {
            setAccountId(accounts[0].account_id)
        }
    }, [accounts, accountId])

    // Fetch open lots filtered by selected account — drives the ticker dropdown
    const { data: openLots = [], isLoading: lotsLoading } = useQuery<OpenLot[]>({
        queryKey: ['tax-open-lots', accountId],
        queryFn: async () => {
            try {
                const params = new URLSearchParams({ status: 'open' })
                if (accountId) params.set('account_id', accountId)
                const res = await apiFetch(`/api/v1/tax/lots?${params.toString()}`)
                if (res && Array.isArray(res.lots)) return res.lots
                return []
            } catch {
                return []
            }
        },
        enabled: !!accountId,
    })

    // Aggregate open lots into unique tickers with summary info
    const tickerOptions: TickerOption[] = useMemo(() => {
        const map = new Map<string, { totalShares: number; totalCost: number; lotCount: number }>()
        for (const lot of openLots) {
            const t = lot.ticker
            const existing = map.get(t) || { totalShares: 0, totalCost: 0, lotCount: 0 }
            existing.totalShares += n(lot.quantity)
            existing.totalCost += n(lot.cost_basis) * n(lot.quantity)
            existing.lotCount += 1
            map.set(t, existing)
        }
        return Array.from(map.entries())
            .map(([t, info]) => ({
                ticker: t,
                totalShares: info.totalShares,
                lotCount: info.lotCount,
                avgCostBasis: info.totalShares > 0 ? info.totalCost / info.totalShares : 0,
            }))
            .sort((a, b) => a.ticker.localeCompare(b.ticker))
    }, [openLots])

    // When account changes, reset ticker if it's no longer available
    useEffect(() => {
        if (ticker && tickerOptions.length > 0 && !tickerOptions.some(t => t.ticker === ticker)) {
            setTicker('')
        }
    }, [ticker, tickerOptions])

    // When ticker is selected, auto-fill max quantity from available shares
    const selectedTickerInfo = useMemo(
        () => tickerOptions.find(t => t.ticker === ticker),
        [ticker, tickerOptions]
    )

    const handleTickerChange = useCallback((newTicker: string) => {
        setTicker(newTicker)
        // Auto-fill quantity with total available shares
        const info = tickerOptions.find(t => t.ticker === newTicker)
        if (info) {
            setQuantity(info.totalShares)
        }
        // Reset mutation so user can re-run
        if (simulateMutation.isSuccess || simulateMutation.isError) {
            simulateMutation.reset()
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tickerOptions])

    const simulateMutation = useMutation<SimulationResult, Error, void>({
        mutationFn: () =>
            apiFetch('/api/v1/tax/simulate', {
                method: 'POST',
                body: JSON.stringify({
                    ticker,
                    action: 'sell',  // Required field — default to sell
                    quantity,
                    price,
                    account_id: accountId,
                    cost_basis_method: costBasisMethod,
                }),
            }),
    })

    const handleSubmit = useCallback((e: React.FormEvent) => {
        e.preventDefault()
        simulateMutation.mutate()
    }, [simulateMutation])

    // G23 FormGuard: track dirty state for tab-switching protection
    const hasFormInput = ticker !== '' || quantity > 0 || price > 0
    const hasRun = simulateMutation.isSuccess || simulateMutation.isError
    const isDirty = hasFormInput && !hasRun

    useEffect(() => {
        onDirtyChange?.(isDirty)
    }, [isDirty, onDirtyChange])

    const handleInputChange = useCallback(() => {
        if (hasRun) {
            simulateMutation.reset()
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [hasRun])

    const result = simulateMutation.data
    const hasLots = (result?.lot_details ?? []).length > 0

    return (
        <div data-testid={TAX_TEST_IDS.WHAT_IF_SIMULATOR} className="space-y-6">
            <TaxHelpCard content={TAX_HELP.simulator} />
            {/* Simulation Form */}
            <form onSubmit={handleSubmit} className="bg-bg-elevated rounded-lg border border-bg-subtle p-4 space-y-4">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    What-If Tax Simulator
                </h3>

                <div className="grid grid-cols-2 gap-4">
                    {/* Account selector — first, because it drives ticker options */}
                    <div className="col-span-2">
                        <label htmlFor="sim-account" className="block text-xs text-fg-muted mb-1">
                            Account
                        </label>
                        <select
                            id="sim-account"
                            value={accountId}
                            onChange={(e) => { setAccountId(e.target.value); setTicker(''); handleInputChange() }}
                            required
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        >
                            <option value="" disabled>Select account…</option>
                            {accounts.map((acc) => (
                                <option key={acc.account_id} value={acc.account_id}>
                                    {acc.name} ({acc.account_id.slice(0, 8)}…)
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Ticker — dropdown populated from open lots in the selected account */}
                    <div>
                        <label htmlFor="sim-ticker" className="block text-xs text-fg-muted mb-1">
                            Ticker
                        </label>
                        <select
                            id="sim-ticker"
                            data-testid={TAX_TEST_IDS.WHAT_IF_TICKER_INPUT}
                            value={ticker}
                            onChange={(e) => handleTickerChange(e.target.value)}
                            required
                            disabled={lotsLoading || tickerOptions.length === 0}
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg disabled:opacity-50"
                        >
                            <option value="">
                                {lotsLoading
                                    ? 'Loading lots…'
                                    : tickerOptions.length === 0
                                        ? 'No open lots in this account'
                                        : 'Select ticker…'}
                            </option>
                            {tickerOptions.map((opt) => (
                                <option key={opt.ticker} value={opt.ticker}>
                                    {opt.ticker} — {opt.totalShares} shares ({opt.lotCount} lot{opt.lotCount !== 1 ? 's' : ''}, avg ${opt.avgCostBasis.toFixed(2)})
                                </option>
                            ))}
                        </select>
                        {selectedTickerInfo && (
                            <div className="mt-1 text-xs text-fg-muted">
                                Max sellable: <span className="font-mono font-semibold text-fg">{selectedTickerInfo.totalShares}</span> shares
                            </div>
                        )}
                    </div>

                    {/* Quantity */}
                    <div>
                        <label htmlFor="sim-quantity" className="block text-xs text-fg-muted mb-1">
                            Quantity
                        </label>
                        <input
                            id="sim-quantity"
                            data-testid={TAX_TEST_IDS.WHAT_IF_QUANTITY}
                            type="number"
                            min={1}
                            max={selectedTickerInfo?.totalShares ?? undefined}
                            value={quantity || ''}
                            onChange={(e) => { setQuantity(parseInt(e.target.value) || 0); handleInputChange() }}
                            placeholder={selectedTickerInfo ? `1–${selectedTickerInfo.totalShares}` : '0'}
                            required
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        />
                        {selectedTickerInfo && quantity > selectedTickerInfo.totalShares && (
                            <div className="mt-1 text-xs text-amber-400">
                                ⚠ Exceeds available shares ({selectedTickerInfo.totalShares})
                            </div>
                        )}
                    </div>

                    {/* Price */}
                    <div>
                        <label htmlFor="sim-price" className="block text-xs text-fg-muted mb-1">
                            Simulated Price ($)
                        </label>
                        <input
                            id="sim-price"
                            data-testid={TAX_TEST_IDS.WHAT_IF_PRICE}
                            type="number"
                            step="0.01"
                            min={0.01}
                            value={price || ''}
                            onChange={(e) => { setPrice(parseFloat(e.target.value) || 0); handleInputChange() }}
                            placeholder="150.00"
                            required
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        />
                    </div>

                    {/* Cost basis method */}
                    <div>
                        <label htmlFor="sim-method" className="block text-xs text-fg-muted mb-1">
                            Cost Basis Method
                        </label>
                        <select
                            id="sim-method"
                            value={costBasisMethod}
                            onChange={(e) => { setCostBasisMethod(e.target.value); handleInputChange() }}
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        >
                            <option value="fifo">FIFO</option>
                            <option value="lifo">LIFO</option>
                            <option value="specific_id">Specific ID</option>
                            <option value="avg_cost">Average Cost</option>
                        </select>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        type="submit"
                        data-testid={TAX_TEST_IDS.WHAT_IF_SUBMIT}
                        disabled={!ticker || quantity <= 0 || price <= 0 || !accountId || simulateMutation.isPending}
                        className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {simulateMutation.isPending ? 'Simulating…' : 'Run Simulation'}
                    </button>
                    {hasFormInput && !hasRun && (
                        <span className="text-xs text-fg-muted italic">
                            Click "Run Simulation" to see tax impact
                        </span>
                    )}
                    {hasRun && (
                        <button
                            type="button"
                            onClick={() => {
                                setTicker('')
                                setQuantity(0)
                                setPrice(0)
                                setCostBasisMethod('fifo')
                                simulateMutation.reset()
                            }}
                            className="text-xs text-fg-muted hover:text-fg underline cursor-pointer"
                        >
                            Clear & Reset
                        </button>
                    )}
                </div>

                {simulateMutation.error && (
                    <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2">
                        ❌ Simulation failed: {simulateMutation.error.message}
                    </div>
                )}
            </form>

            {/* Results — mapped from actual API response */}
            {result && (
                <div data-testid={TAX_TEST_IDS.WHAT_IF_RESULT} className="space-y-4" aria-live="polite">
                    {/* Summary */}
                    <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4">
                        <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide mb-3">
                            Simulation Result
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <span className="block text-xs text-fg-muted">ST Gain</span>
                                <span className={`text-lg font-semibold font-mono ${n(result.total_st_gain) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {formatCurrency(n(result.total_st_gain))}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">LT Gain</span>
                                <span className={`text-lg font-semibold font-mono ${n(result.total_lt_gain) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {formatCurrency(n(result.total_lt_gain))}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">Est. Tax</span>
                                <span className={`text-lg font-semibold font-mono ${n(result.estimated_tax) !== 0 ? 'text-red-400' : 'text-fg-muted'}`}>
                                    {formatCurrency(n(result.estimated_tax))}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">Wait Days</span>
                                <span className="text-lg font-semibold font-mono text-fg">
                                    {n(result.wait_days)}
                                </span>
                            </div>
                        </div>
                        {result.wash_risk && (
                            <div className="mt-3 px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                                <span aria-hidden="true">⚠️</span> Wash sale risk detected — replacement purchase within 30-day window
                            </div>
                        )}
                        {(result.wash_sale_warnings ?? []).length > 0 && (
                            <div className="mt-2 space-y-1">
                                {result.wash_sale_warnings.map((w, i) => (
                                    <div key={i} className="text-xs text-amber-400 bg-amber-500/10 px-3 py-1.5 rounded">
                                        {w.message}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Lot Breakdown — uses lot_details from API */}
                    {hasLots && (
                        <div className="bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden">
                            <div className="px-4 py-3 border-b border-bg-subtle">
                                <h4 className="text-xs text-fg-muted uppercase tracking-wider">Per-Lot Breakdown</h4>
                            </div>
                            <table className="w-full text-sm" aria-label="Simulated per-lot breakdown">
                                <thead>
                                    <tr className="border-b border-bg-subtle">
                                        <th className="text-left px-4 py-2 text-fg-muted font-medium">Lot ID</th>
                                        <th className="text-right px-4 py-2 text-fg-muted font-medium">Shares</th>
                                        <th className="text-right px-4 py-2 text-fg-muted font-medium">Gain/Loss</th>
                                        <th className="text-center px-4 py-2 text-fg-muted font-medium">Type</th>
                                        <th className="text-right px-4 py-2 text-fg-muted font-medium">Days Held</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {result.lot_details.map((lot) => (
                                        <tr key={lot.lot_id} className="border-b border-bg-subtle/50">
                                            <td className="px-4 py-2 font-mono text-fg text-xs">{lot.lot_id}</td>
                                            <td className="px-4 py-2 text-right font-mono text-fg">{n(lot.quantity)}</td>
                                            <td className={`px-4 py-2 text-right font-mono ${n(lot.gain_amount) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {formatCurrency(n(lot.gain_amount))}
                                            </td>
                                            <td className="px-4 py-2 text-center">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                                    lot.is_long_term ? 'bg-blue-500/10 text-blue-400' : 'bg-amber-500/10 text-amber-400'
                                                }`}>
                                                    {lot.is_long_term ? 'LT' : 'ST'}
                                                </span>
                                            </td>
                                            <td className="px-4 py-2 text-right text-fg-muted">{n(lot.holding_period_days)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
