/**
 * TaxDashboard — summary cards + YTD P&L by Symbol table.
 *
 * Fetches GET /api/v1/tax/ytd-summary and renders:
 * - 7 summary cards (ST Gains, LT Gains, Wash Sale Adj, Estimated Tax,
 *   Loss Carryforward, Harvestable Losses, Tax Alpha)
 * - YTD P&L by Symbol table via group_by=symbol
 *
 * Source: 06g-gui-tax.md L44–75, L82
 * MEU: MEU-154 (AC-154.4, AC-154.5, AC-154.6)
 */

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'

interface YtdSummary {
    realized_st_gain: number
    realized_lt_gain: number
    total_realized: number
    wash_sale_adjustments: number
    estimated_tax: number
    estimated_federal_tax: number
    estimated_state_tax: number
    trades_count: number
    /** Capital loss carryforward from prior year — optional, defaults to 0 */
    capital_loss_carryforward?: number
    /** Unrealized losses available for harvesting — optional, populated when harvest scan runs */
    harvestable_losses?: number
    /** Dollars saved via lot optimization + harvesting — optional, computed */
    tax_alpha?: number
}

interface SymbolBreakdown {
    ticker: string
    short_term_pnl: number
    long_term_pnl: number
    total_pnl: number
}

const SUMMARY_CARDS: { label: string; key: keyof YtdSummary; format?: 'currency' | 'percent' }[] = [
    { label: 'ST Gains', key: 'realized_st_gain', format: 'currency' },
    { label: 'LT Gains', key: 'realized_lt_gain', format: 'currency' },
    { label: 'Wash Sale Adj', key: 'wash_sale_adjustments', format: 'currency' },
    { label: 'Estimated Tax', key: 'estimated_tax', format: 'currency' },
    { label: 'Loss Carryforward', key: 'capital_loss_carryforward', format: 'currency' },
    { label: 'Harvestable Losses', key: 'harvestable_losses', format: 'currency' },
    { label: 'Tax Alpha', key: 'tax_alpha', format: 'currency' },
]

function formatCurrency(value: number): string {
    const abs = Math.abs(value)
    const formatted = abs.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    return value < 0 ? `-$${formatted}` : `$${formatted}`
}

function valueColor(value: number): string {
    if (value > 0) return 'text-green-400'
    if (value < 0) return 'text-red-400'
    return 'text-fg-muted'
}

export default function TaxDashboard() {
    const currentYear = new Date().getFullYear()
    const [taxYear, setTaxYear] = useState(currentYear)

    // Fetch YTD summary
    const { data: summary, isLoading, error } = useQuery<YtdSummary>({
        queryKey: ['tax-ytd-summary', taxYear],
        queryFn: () => apiFetch(`/api/v1/tax/ytd-summary?tax_year=${taxYear}`),
    })

    // Fetch symbol breakdown — API may not support group_by=symbol yet;
    // if it returns a non-array (e.g. the same summary dict), fall back to [].
    const { data: symbols = [] } = useQuery<SymbolBreakdown[]>({
        queryKey: ['tax-ytd-symbols', taxYear],
        queryFn: async () => {
            try {
                const res = await apiFetch(`/api/v1/tax/ytd-summary?tax_year=${taxYear}&group_by=symbol`)
                return Array.isArray(res) ? res : []
            } catch {
                return []
            }
        },
    })

    // Year options: current year ± 5
    const yearOptions = useMemo(() => {
        const years: number[] = []
        for (let y = currentYear - 5; y <= currentYear; y++) years.push(y)
        return years
    }, [currentYear])

    if (error) {
        return (
            <div className="flex items-center justify-center h-32 text-red-400 text-sm">
                Failed to load tax summary: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
        )
    }

    return (
        <div data-testid={TAX_TEST_IDS.DASHBOARD} className="space-y-6">
            {/* Year Selector (AC-154.6) */}
            <div className="flex items-center gap-3">
                <label htmlFor="tax-year-select" className="text-sm text-fg-muted">
                    Tax Year
                </label>
                <select
                    id="tax-year-select"
                    data-testid={TAX_TEST_IDS.YEAR_SELECTOR}
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    className="rounded border border-border bg-bg px-2 py-1.5 text-sm text-fg min-w-[100px]"
                >
                    {yearOptions.map((y) => (
                        <option key={y} value={y}>
                            {y}
                        </option>
                    ))}
                </select>
            </div>

            {/* Summary Cards (AC-154.4) */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {SUMMARY_CARDS.map(({ label, key, format }) => {
                    const value = summary?.[key] ?? 0
                    return (
                        <div
                            key={key}
                            data-testid={TAX_TEST_IDS.SUMMARY_CARD}
                            className="bg-bg-elevated rounded-lg border border-bg-subtle p-4"
                        >
                            <span className="block text-xs text-fg-muted uppercase tracking-wider mb-1">
                                {label}
                            </span>
                            {isLoading ? (
                                <span className="text-lg font-semibold text-fg-muted font-mono">—</span>
                            ) : (
                                <span className={`text-lg font-semibold font-mono ${format === 'currency' ? valueColor(value) : 'text-fg'}`}>
                                    {format === 'currency' ? formatCurrency(value) : value.toLocaleString()}
                                </span>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* YTD P&L by Symbol (AC-154.5) */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden">
                <div className="px-4 py-3 border-b border-bg-subtle">
                    <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                        YTD P&L by Symbol
                    </h3>
                </div>
                <div data-testid={TAX_TEST_IDS.YTD_TABLE} className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-bg-subtle">
                                <th className="text-left px-4 py-2 text-fg-muted font-medium">Symbol</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">ST P&L</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">LT P&L</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {symbols.length === 0 && !isLoading ? (
                                <tr>
                                    <td colSpan={4} className="px-4 py-8 text-center text-fg-muted">
                                        No data for {taxYear}
                                    </td>
                                </tr>
                            ) : (
                                symbols.map((row) => (
                                    <tr key={row.ticker} className="border-b border-bg-subtle/50 hover:bg-bg-subtle/30">
                                        <td className="px-4 py-2 font-mono text-fg">{row.ticker}</td>
                                        <td className={`px-4 py-2 text-right font-mono ${valueColor(row.short_term_pnl)}`}>
                                            {formatCurrency(row.short_term_pnl)}
                                        </td>
                                        <td className={`px-4 py-2 text-right font-mono ${valueColor(row.long_term_pnl)}`}>
                                            {formatCurrency(row.long_term_pnl)}
                                        </td>
                                        <td className={`px-4 py-2 text-right font-mono font-semibold ${valueColor(row.total_pnl)}`}>
                                            {formatCurrency(row.total_pnl)}
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
