/**
 * TaxDashboard — summary cards + YTD P&L by Symbol table.
 *
 * Fetches GET /api/v1/tax/ytd-summary?tax_year={Y} and renders:
 * - Summary cards from actual YtdTaxSummary dataclass fields:
 *   realized_st_gain, realized_lt_gain, wash_sale_adjustments,
 *   estimated_federal_tax, estimated_state_tax, trades_count,
 *   quarterly_payments[]
 * - Derived: estimated_tax = estimated_federal_tax + estimated_state_tax
 *
 * Source: 06g-gui-tax.md L44–75, L82
 * MEU: MEU-154 (AC-154.4, AC-154.5, AC-154.6)
 */

import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

/** Matches SyncReport dataclass from tax_service.sync_lots() */
interface SyncReport {
    created: number
    updated: number
    skipped: number
    conflicts: number
    orphaned: number
    closed?: number
    account_id?: string | null
}

/** Matches actual YtdTaxSummary dataclass + API fallback shape */
interface YtdSummary {
    realized_st_gain: number
    realized_lt_gain: number
    total_realized: number
    wash_sale_adjustments: number
    trades_count: number
    estimated_federal_tax: number
    estimated_state_tax: number
    /** Computed: federal + state; present in API fallback path */
    estimated_tax?: number
    /** Q1-Q4 payment status from QuarterlyEstimate records */
    quarterly_payments?: { quarter: number; required: number; paid: number; due: number }[]
}

/** Safe number extraction — handles Decimal strings, null, undefined */
function n(v: unknown): number {
    if (v === null || v === undefined) return 0
    const num = Number(v)
    return isNaN(num) ? 0 : num
}

/** Normalize API response to our display model */
function normalizeSummary(raw: Record<string, unknown>): YtdSummary {
    const federal = n(raw.estimated_federal_tax)
    const state = n(raw.estimated_state_tax)
    return {
        realized_st_gain: n(raw.realized_st_gain),
        realized_lt_gain: n(raw.realized_lt_gain),
        total_realized: n(raw.total_realized),
        wash_sale_adjustments: n(raw.wash_sale_adjustments),
        trades_count: n(raw.trades_count),
        estimated_federal_tax: federal,
        estimated_state_tax: state,
        estimated_tax: n(raw.estimated_tax) || (federal + state),
        quarterly_payments: Array.isArray(raw.quarterly_payments) ? raw.quarterly_payments : [],
    }
}

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

    // Fetch YTD summary — normalize defensively
    const { data: summary, isLoading, error } = useQuery<YtdSummary>({
        queryKey: ['tax-ytd-summary', taxYear],
        queryFn: async () => {
            const raw = await apiFetch(`/api/v1/tax/ytd-summary?tax_year=${taxYear}`)
            return normalizeSummary(raw ?? {})
        },
    })

    // Year options: current year ± 5
    const yearOptions = useMemo(() => {
        const years: number[] = []
        for (let y = currentYear - 5; y <= currentYear; y++) years.push(y)
        return years
    }, [currentYear])

    // Sync lots mutation (Phase 3F, MEU-218)
    const queryClient = useQueryClient()
    const syncMutation = useMutation<SyncReport>({
        mutationFn: () => apiFetch('/api/v1/tax/sync-lots', { method: 'POST' }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tax-ytd-summary'] })
        },
    })

    if (error) {
        return (
            <div className="flex items-center justify-center h-32 text-red-400 text-sm">
                Failed to load tax summary: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
        )
    }

    // Build card definitions from actual data
    const cards = [
        { label: 'ST Gains', value: summary?.realized_st_gain ?? 0 },
        { label: 'LT Gains', value: summary?.realized_lt_gain ?? 0 },
        { label: 'Total Realized', value: summary?.total_realized ?? 0 },
        { label: 'Wash Sale Adj', value: summary?.wash_sale_adjustments ?? 0 },
        { label: 'Federal Tax', value: summary?.estimated_federal_tax ?? 0 },
        { label: 'State Tax', value: summary?.estimated_state_tax ?? 0 },
        { label: 'Total Est. Tax', value: summary?.estimated_tax ?? 0 },
        { label: 'Trades', value: summary?.trades_count ?? 0, isCurrency: false },
    ]

    return (
        <div data-testid={TAX_TEST_IDS.DASHBOARD} className="space-y-6">
            <TaxHelpCard content={TAX_HELP.dashboard} />
            {/* Year Selector + Sync button (AC-154.6) */}
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
                <button
                    data-testid={TAX_TEST_IDS.SYNC_BUTTON}
                    onClick={() => syncMutation.mutate()}
                    disabled={syncMutation.isPending}
                    aria-label="Process tax lots"
                    className="ml-auto px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {syncMutation.isPending ? 'Processing…' : <><span aria-hidden="true">🔄</span> Process Tax Lots</>}
                </button>
            </div>

            {/* Sync status message */}
            {syncMutation.isSuccess && (
                <div role="status" className="text-xs text-green-400 bg-green-400/10 rounded px-3 py-1.5">
                    Sync complete — {syncMutation.data?.created ?? 0} created,{' '}
                    {syncMutation.data?.updated ?? 0} updated,{' '}
                    {syncMutation.data?.conflicts ?? 0} conflicts
                </div>
            )}
            {syncMutation.isError && (
                <div role="alert" className="text-xs text-red-400 bg-red-400/10 rounded px-3 py-1.5">
                    Sync failed: {syncMutation.error instanceof Error ? syncMutation.error.message : 'Unknown error'}
                </div>
            )}

            {/* Summary Cards (AC-154.4) */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" aria-label="Tax summary cards">
                {cards.map(({ label, value, isCurrency }) => (
                    <div
                        key={label}
                        data-testid={TAX_TEST_IDS.SUMMARY_CARD}
                        className="bg-bg-elevated rounded-lg border border-bg-subtle p-4"
                    >
                        <span className="block text-xs text-fg-muted uppercase tracking-wider mb-1">
                            {label}
                        </span>
                        {isLoading ? (
                            <span className="text-lg font-semibold text-fg-muted font-mono">—</span>
                        ) : (
                            <span className={`text-lg font-semibold font-mono ${isCurrency === false ? 'text-fg' : valueColor(value)}`}>
                                {isCurrency === false ? value.toLocaleString() : formatCurrency(value)}
                            </span>
                        )}
                    </div>
                ))}
            </div>

            {/* Quarterly Payments Summary (from ytd_summary data) */}
            {(summary?.quarterly_payments ?? []).length > 0 && (
                <div className="bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden">
                    <div className="px-4 py-3 border-b border-bg-subtle">
                        <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                            Quarterly Payment Status
                        </h3>
                    </div>
                    <div className="grid grid-cols-4 gap-px bg-bg-subtle">
                        {(summary?.quarterly_payments ?? []).map((qp) => (
                            <div key={qp.quarter} className="bg-bg-elevated p-3 text-center">
                                <div className="text-xs text-fg-muted mb-1">Q{qp.quarter}</div>
                                <div className="text-sm font-mono">
                                    <span className="text-fg-muted">Req: </span>
                                    <span className={valueColor(n(qp.required))}>{formatCurrency(n(qp.required))}</span>
                                </div>
                                <div className="text-sm font-mono">
                                    <span className="text-fg-muted">Paid: </span>
                                    <span className="text-green-400">{formatCurrency(n(qp.paid))}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
