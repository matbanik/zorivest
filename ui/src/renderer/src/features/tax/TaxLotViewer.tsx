/**
 * TaxLotViewer — lot table with filters, ST/LT badges, disabled action buttons.
 *
 * Fetches GET /api/v1/tax/lots with filters (status, ticker, account).
 * "Close This Lot" and "Reassign Method" buttons are disabled with tooltip.
 *
 * Source: 06g-gui-tax.md L107, L120–139
 * MEU: MEU-154 (AC-154.7, AC-154.8)
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

interface TaxLot {
    lot_id: string
    ticker: string
    quantity: number
    cost_basis: number
    proceeds: number
    wash_sale_adjustment: number
    is_closed: boolean
    open_date: string
    close_date: string | null
    linked_trade_ids: string[]
    cost_basis_method: string | null
    realized_gain_loss: number
    acquisition_source: string | null
    account_id: string
    // Phase 3F provenance fields (MEU-216)
    materialized_at: string | null
    is_user_modified: boolean
    source_hash: string | null
    sync_status: string
}

/** Safe number formatting — avoids crash on null/undefined */
function fmtNum(val: number | null | undefined, fractionDigits = 2): string {
    if (val == null || isNaN(val)) return '0.00'
    return val.toLocaleString(undefined, { minimumFractionDigits: fractionDigits })
}

/** Compute classification from open_date */
function getClassification(openDate: string): 'ST' | 'LT' {
    const days = Math.floor((Date.now() - new Date(openDate).getTime()) / (1000 * 60 * 60 * 24))
    return days >= 366 ? 'LT' : 'ST'
}

/** Days until long-term status (366 days from open) */
function getDaysToLT(openDate: string): number {
    const days = Math.floor((Date.now() - new Date(openDate).getTime()) / (1000 * 60 * 60 * 24))
    return Math.max(366 - days, 0)
}

export default function TaxLotViewer() {
    const [statusFilter, setStatusFilter] = useState<'open' | 'closed' | 'all'>('all')
    const [tickerFilter, setTickerFilter] = useState('')

    const queryParams = new URLSearchParams()
    if (statusFilter !== 'all') queryParams.set('status', statusFilter)
    if (tickerFilter) queryParams.set('ticker', tickerFilter)

    const { data: lots = [], isLoading, error } = useQuery<TaxLot[]>({
        queryKey: ['tax-lots', statusFilter, tickerFilter],
        queryFn: async () => {
            try {
                const res = await apiFetch(`/api/v1/tax/lots?${queryParams.toString()}`)
                // API returns { lots: [...], total_count: N }
                if (Array.isArray(res)) return res
                if (res && Array.isArray(res.lots)) return res.lots
                return []
            } catch {
                return []
            }
        },
    })

    if (error) {
        return (
            <div className="flex items-center justify-center h-32 text-red-400 text-sm">
                Failed to load lots: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
        )
    }

    return (
        <div data-testid={TAX_TEST_IDS.LOT_VIEWER} className="space-y-4">
            <TaxHelpCard content={TAX_HELP.lots} />
            {/* Filters */}
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <label htmlFor="lot-status-filter" className="text-xs text-fg-muted">
                        Status
                    </label>
                    <select
                        id="lot-status-filter"
                        data-testid={TAX_TEST_IDS.LOT_FILTER_STATUS}
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value as 'open' | 'closed' | 'all')}
                        className="rounded border border-border bg-bg px-2 py-1 text-sm text-fg"
                    >
                        <option value="all">All</option>
                        <option value="open">Open</option>
                        <option value="closed">Closed</option>
                    </select>
                </div>
                <div className="flex items-center gap-2">
                    <label htmlFor="lot-ticker-filter" className="text-xs text-fg-muted">
                        Ticker
                    </label>
                    <input
                        id="lot-ticker-filter"
                        data-testid={TAX_TEST_IDS.LOT_FILTER_TICKER}
                        type="text"
                        value={tickerFilter}
                        onChange={(e) => setTickerFilter(e.target.value.toUpperCase())}
                        placeholder="e.g. AAPL"
                        className="rounded border border-border bg-bg px-2 py-1 text-sm text-fg w-24"
                    />
                </div>
            </div>

            {/* Lot Table */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm" aria-label="Tax lots">
                        <thead>
                            <tr className="border-b border-bg-subtle">
                                <th className="text-left px-4 py-2 text-fg-muted font-medium">Ticker</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Qty</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Cost Basis</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Proceeds</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Gain/Loss</th>
                                <th className="text-center px-4 py-2 text-fg-muted font-medium">Type</th>
                                <th className="text-left px-4 py-2 text-fg-muted font-medium">Method</th>
                                <th className="text-center px-4 py-2 text-fg-muted font-medium">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading ? (
                                <tr>
                                    <td colSpan={8} className="px-4 py-8 text-center text-fg-muted">
                                        Loading lots…
                                    </td>
                                </tr>
                            ) : lots.length === 0 ? (
                                <tr>
                                    <td colSpan={8} className="px-4 py-8 text-center text-fg-muted">
                                        No lots found
                                    </td>
                                </tr>
                            ) : (
                                lots.map((lot) => (
                                    <tr
                                        key={lot.lot_id}
                                        data-testid={TAX_TEST_IDS.LOT_ROW}
                                        className="border-b border-bg-subtle/50 hover:bg-bg-subtle/30"
                                    >
                                        <td className="px-4 py-2 font-mono text-fg">{lot.ticker}</td>
                                        <td className="px-4 py-2 text-right font-mono text-fg">
                                            {fmtNum(lot.quantity, 0)}
                                        </td>
                                        <td className="px-4 py-2 text-right font-mono text-fg">
                                            ${fmtNum(lot.cost_basis)}
                                        </td>
                                        <td className="px-4 py-2 text-right font-mono text-fg">
                                            ${fmtNum(lot.proceeds)}
                                        </td>
                                        <td className={`px-4 py-2 text-right font-mono font-semibold ${(lot.realized_gain_loss ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {(lot.realized_gain_loss ?? 0) >= 0 ? '+' : ''}
                                            ${fmtNum(lot.realized_gain_loss)}
                                        </td>
                                        <td className="px-4 py-2 text-center">
                                            {(() => {
                                                const cls = getClassification(lot.open_date)
                                                const daysToLT = getDaysToLT(lot.open_date)
                                                return (
                                                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                                                        cls === 'LT'
                                                            ? 'bg-blue-500/10 text-blue-400'
                                                            : 'bg-amber-500/10 text-amber-400'
                                                    }`}>
                                                        {cls}
                                                        {/* AC-154.8: Days-to-LT countdown for open ST lots */}
                                                        {cls === 'ST' && !lot.is_closed && daysToLT > 0 && (
                                                            <span className="text-fg-muted" title={`${daysToLT} days until long-term`}>
                                                                <span aria-hidden="true">🕐</span> {daysToLT}d
                                                            </span>
                                                        )}
                                                    </span>
                                                )
                                            })()}
                                        </td>
                                        <td className="px-4 py-2 text-sm text-fg-muted">{lot.cost_basis_method ?? '—'}</td>
                                        <td className="px-4 py-2 text-center">
                                            <div className="flex items-center justify-center gap-1">
                                                {/* AC-154.7: Disabled buttons with tooltip */}
                                                <button
                                                    data-testid={TAX_TEST_IDS.LOT_CLOSE_BTN}
                                                    disabled
                                                    aria-label="Close lot — coming soon"
                                                    title="Coming soon — Module C4/C5"
                                                    className="px-2 py-1 text-xs rounded border border-bg-subtle text-fg-muted/40 cursor-not-allowed"
                                                >
                                                    Close
                                                </button>
                                                <button
                                                    data-testid={TAX_TEST_IDS.LOT_REASSIGN_BTN}
                                                    disabled
                                                    aria-label="Reassign cost basis method — coming soon"
                                                    title="Coming soon — Module C4/C5"
                                                    className="px-2 py-1 text-xs rounded border border-bg-subtle text-fg-muted/40 cursor-not-allowed"
                                                >
                                                    Reassign
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
