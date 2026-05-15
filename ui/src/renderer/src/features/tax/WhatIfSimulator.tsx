/**
 * WhatIfSimulator — simulation form with G23 FormGuard + results display.
 *
 * Posts to POST /api/v1/tax/simulate and renders per-lot breakdown + tax impact summary.
 *
 * Source: 06g-gui-tax.md L273–294
 * MEU: MEU-154 (AC-154.10, AC-154.11)
 */

import { useState, useCallback, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'

interface SimulationResult {
    ticker: string
    quantity: number
    price: number
    total_proceeds: number
    total_cost_basis: number
    realized_pnl: number
    short_term_gain: number
    long_term_gain: number
    estimated_tax: number
    wash_sale_risk: boolean
    lot_breakdown: LotImpact[]
}

interface LotImpact {
    lot_id: string
    shares_closed: number
    gain_loss: number
    classification: 'ST' | 'LT'
    holding_days: number
}

interface WhatIfSimulatorProps {
    /** Callback to report dirty form state to parent (G23 form guard) */
    onDirtyChange?: (dirty: boolean) => void
}

export default function WhatIfSimulator({ onDirtyChange }: WhatIfSimulatorProps) {
    const [ticker, setTicker] = useState('')
    const [quantity, setQuantity] = useState<number>(0)
    const [price, setPrice] = useState<number>(0)
    const accountId = ''
    const [costBasisMethod, setCostBasisMethod] = useState('fifo')

    const simulateMutation = useMutation<SimulationResult, Error, void>({
        mutationFn: () =>
            apiFetch('/api/v1/tax/simulate', {
                method: 'POST',
                body: JSON.stringify({
                    ticker,
                    quantity,
                    price,
                    account_id: accountId || undefined,
                    cost_basis_method: costBasisMethod,
                }),
            }),
    })

    const handleSubmit = useCallback((e: React.FormEvent) => {
        e.preventDefault()
        simulateMutation.mutate()
    }, [simulateMutation])

    // G23 FormGuard: track dirty state for tab-switching protection
    const isDirty = ticker !== '' || quantity > 0 || price > 0

    // Report dirty state changes to parent
    useEffect(() => {
        onDirtyChange?.(isDirty)
    }, [isDirty, onDirtyChange])

    return (
        <div data-testid={TAX_TEST_IDS.WHAT_IF_SIMULATOR} className="space-y-6">
            {/* Simulation Form */}
            <form onSubmit={handleSubmit} className="bg-bg-elevated rounded-lg border border-bg-subtle p-4 space-y-4">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    What-If Tax Simulator
                </h3>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label htmlFor="sim-ticker" className="block text-xs text-fg-muted mb-1">
                            Ticker
                        </label>
                        <input
                            id="sim-ticker"
                            data-testid={TAX_TEST_IDS.WHAT_IF_TICKER_INPUT}
                            type="text"
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            placeholder="AAPL"
                            required
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        />
                    </div>
                    <div>
                        <label htmlFor="sim-quantity" className="block text-xs text-fg-muted mb-1">
                            Quantity
                        </label>
                        <input
                            id="sim-quantity"
                            data-testid={TAX_TEST_IDS.WHAT_IF_QUANTITY}
                            type="number"
                            min={1}
                            value={quantity || ''}
                            onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                            placeholder="100"
                            required
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        />
                    </div>
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
                            onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                            placeholder="150.00"
                            required
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        />
                    </div>
                    <div>
                        <label htmlFor="sim-method" className="block text-xs text-fg-muted mb-1">
                            Cost Basis Method
                        </label>
                        <select
                            id="sim-method"
                            value={costBasisMethod}
                            onChange={(e) => setCostBasisMethod(e.target.value)}
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
                        disabled={!ticker || quantity <= 0 || price <= 0 || simulateMutation.isPending}
                        className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {simulateMutation.isPending ? 'Simulating…' : 'Run Simulation'}
                    </button>
                    {isDirty && (
                        <span className="text-xs text-fg-muted">
                            ⚡ Unsaved changes
                        </span>
                    )}
                </div>

                {simulateMutation.error && (
                    <div className="text-sm text-red-400">
                        Simulation failed: {simulateMutation.error.message}
                    </div>
                )}
            </form>

            {/* Results */}
            {simulateMutation.data && (
                <div data-testid={TAX_TEST_IDS.WHAT_IF_RESULT} className="space-y-4">
                    {/* Summary */}
                    <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4">
                        <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide mb-3">
                            Simulation Result
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <span className="block text-xs text-fg-muted">Realized P&L</span>
                                <span className={`text-lg font-semibold font-mono ${simulateMutation.data.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    ${simulateMutation.data.realized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">ST Gain</span>
                                <span className="text-lg font-semibold font-mono text-fg">
                                    ${simulateMutation.data.short_term_gain.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">LT Gain</span>
                                <span className="text-lg font-semibold font-mono text-fg">
                                    ${simulateMutation.data.long_term_gain.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">Est. Tax</span>
                                <span className="text-lg font-semibold font-mono text-red-400">
                                    ${simulateMutation.data.estimated_tax.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                        </div>
                        {simulateMutation.data.wash_sale_risk && (
                            <div className="mt-3 px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                                ⚠️ Wash sale risk detected — replacement purchase within 30-day window
                            </div>
                        )}
                    </div>

                    {/* Lot Breakdown */}
                    {simulateMutation.data.lot_breakdown.length > 0 && (
                        <div className="bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden">
                            <div className="px-4 py-3 border-b border-bg-subtle">
                                <h4 className="text-xs text-fg-muted uppercase tracking-wider">Per-Lot Breakdown</h4>
                            </div>
                            <table className="w-full text-sm">
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
                                    {simulateMutation.data.lot_breakdown.map((lot) => (
                                        <tr key={lot.lot_id} className="border-b border-bg-subtle/50">
                                            <td className="px-4 py-2 font-mono text-fg text-xs">{lot.lot_id}</td>
                                            <td className="px-4 py-2 text-right font-mono text-fg">{lot.shares_closed}</td>
                                            <td className={`px-4 py-2 text-right font-mono ${lot.gain_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                ${lot.gain_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </td>
                                            <td className="px-4 py-2 text-center">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                                    lot.classification === 'LT' ? 'bg-blue-500/10 text-blue-400' : 'bg-amber-500/10 text-amber-400'
                                                }`}>
                                                    {lot.classification}
                                                </span>
                                            </td>
                                            <td className="px-4 py-2 text-right text-fg-muted">{lot.holding_days}</td>
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
