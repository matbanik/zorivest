/**
 * QuarterlyTracker — 4-quarter timeline cards + payment entry form.
 *
 * Fetches GET /api/v1/tax/quarterly?quarter={Q}&tax_year={Y} for each quarter.
 * Payment form posts to POST /api/v1/tax/quarterly/payment with body
 * { quarter, tax_year, payment_amount, confirm: true }.
 *
 * Source: 06g-gui-tax.md L416–433
 * MEU: MEU-154 (AC-154.13, AC-154.14)
 */

import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

interface QuarterData {
    quarter: string
    tax_year: number
    estimated_amount: number
    paid_amount: number
    due_date: string
    status: 'paid' | 'partial' | 'due' | 'overdue' | 'upcoming'
}

/** Map API response fields to our UI model */
function normalizeQuarterData(q: string, year: number, raw: Record<string, unknown>): QuarterData {
    const required = Number(raw.required_amount ?? raw.required ?? raw.estimated_amount ?? 0)
    const paid = Number(raw.paid ?? raw.paid_amount ?? 0)
    const dueDate = String(raw.due_date ?? '')
    let status: QuarterData['status'] = 'upcoming'
    if (required > 0 && paid >= required) status = 'paid'
    else if (required > 0 && paid > 0) status = 'partial'
    else if (required > 0) status = 'due'
    return { quarter: q, tax_year: year, estimated_amount: required, paid_amount: paid, due_date: dueDate, status }
}

const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4'] as const

const STATUS_COLORS: Record<string, string> = {
    paid: 'bg-green-500/10 text-green-400 border-green-500/20',
    partial: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    due: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    overdue: 'bg-red-500/10 text-red-400 border-red-500/20',
    upcoming: 'bg-bg-subtle text-fg-muted border-bg-subtle',
}

interface QuarterlyTrackerProps {
    /** Callback to report dirty form state to parent (G23 form guard) */
    onDirtyChange?: (dirty: boolean) => void
}

export default function QuarterlyTracker({ onDirtyChange }: QuarterlyTrackerProps) {
    const currentYear = new Date().getFullYear()
    const [taxYear, setTaxYear] = useState(currentYear)
    const [paymentQuarter, setPaymentQuarter] = useState<string>('Q1')
    const [paymentAmount, setPaymentAmount] = useState<number>(0)
    const queryClient = useQueryClient()

    // G23: report dirty state to parent
    const isDirty = paymentAmount > 0
    useEffect(() => {
        onDirtyChange?.(isDirty)
    }, [isDirty, onDirtyChange])

    // Fetch all 4 quarters (AC-154.13)
    const quarterQueries = QUARTERS.map((q) =>
        // eslint-disable-next-line react-hooks/rules-of-hooks
        useQuery<QuarterData>({
            queryKey: ['tax-quarterly', taxYear, q],
            queryFn: async () => {
                try {
                    const res = await apiFetch(`/api/v1/tax/quarterly?quarter=${q}&tax_year=${taxYear}`)
                    return normalizeQuarterData(q, taxYear, res ?? {})
                } catch {
                    return normalizeQuarterData(q, taxYear, {})
                }
            },
        })
    )

    // Payment mutation (AC-154.14)
    const paymentMutation = useMutation({
        mutationFn: async () => {
            await apiFetch('/api/v1/tax/quarterly/payment', {
                method: 'POST',
                body: JSON.stringify({
                    quarter: paymentQuarter,
                    tax_year: taxYear,
                    payment_amount: paymentAmount,
                    confirm: true,
                }),
            })
        },
        onSuccess: () => {
            // Refresh quarter data and dashboard
            queryClient.invalidateQueries({ queryKey: ['tax-quarterly'] })
            queryClient.invalidateQueries({ queryKey: ['tax-ytd-summary'] })
            setPaymentAmount(0)
        },
    })

    const handleRecordPayment = useCallback((e: React.FormEvent) => {
        e.preventDefault()
        paymentMutation.mutate()
    }, [paymentMutation])

    return (
        <div data-testid={TAX_TEST_IDS.QUARTERLY_TRACKER} className="space-y-6">
            <TaxHelpCard content={TAX_HELP.quarterly} />
            {/* Year Selector */}
            <div className="flex items-center gap-3">
                <label htmlFor="quarterly-year" className="text-sm text-fg-muted">Tax Year</label>
                <select
                    id="quarterly-year"
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    className="rounded border border-border bg-bg px-2 py-1.5 text-sm text-fg min-w-[100px]"
                >
                    {[currentYear - 1, currentYear, currentYear + 1].map((y) => (
                        <option key={y} value={y}>{y}</option>
                    ))}
                </select>
            </div>

            {/* Quarter Cards (AC-154.13) */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" aria-label="Quarterly payment timeline">
                {QUARTERS.map((q, i) => {
                    const query = quarterQueries[i]
                    const data = query.data
                    const statusClass = data ? STATUS_COLORS[data.status] || STATUS_COLORS.upcoming : STATUS_COLORS.upcoming

                    return (
                        <div
                            key={q}
                            data-testid={TAX_TEST_IDS.QUARTERLY_CARD}
                            className={`rounded-lg border p-4 space-y-2 ${statusClass}`}
                        >
                            <div className="flex items-center justify-between">
                                <span className="text-lg font-semibold">{q}</span>
                                {data && (
                                    <span className="text-xs uppercase font-medium">{data.status}</span>
                                )}
                            </div>
                            {query.isLoading ? (
                                <div className="text-sm">Loading…</div>
                            ) : data ? (
                                <>
                                    <div className="space-y-1">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-fg-muted">Estimated</span>
                                            <span className="font-mono">
                                                ${data.estimated_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-fg-muted">Paid</span>
                                            <span className="font-mono">
                                                ${data.paid_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="text-xs text-fg-muted">Due: {data.due_date}</div>
                                </>
                            ) : (
                                <div className="text-sm text-fg-muted">No data</div>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Record Payment Form (AC-154.14) */}
            <form
                onSubmit={handleRecordPayment}
                className="bg-bg-elevated rounded-lg border border-bg-subtle p-4 space-y-4"
            >
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    Record Payment
                </h3>
                <div className="flex items-end gap-4">
                    <div>
                        <label htmlFor="payment-quarter" className="block text-xs text-fg-muted mb-1">
                            Quarter
                        </label>
                        <select
                            id="payment-quarter"
                            value={paymentQuarter}
                            onChange={(e) => setPaymentQuarter(e.target.value)}
                            className="rounded border border-border bg-bg px-2 py-1.5 text-sm text-fg"
                        >
                            {QUARTERS.map((q) => (
                                <option key={q} value={q}>{q}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label htmlFor="payment-amount" className="block text-xs text-fg-muted mb-1">
                            Amount ($)
                        </label>
                        <input
                            id="payment-amount"
                            data-testid={TAX_TEST_IDS.QUARTERLY_PAYMENT_INPUT}
                            type="number"
                            step="0.01"
                            min={0.01}
                            value={paymentAmount || ''}
                            onChange={(e) => setPaymentAmount(parseFloat(e.target.value) || 0)}
                            placeholder="0.00"
                            required
                            className="w-36 px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                        />
                    </div>
                    <button
                        type="submit"
                        data-testid={TAX_TEST_IDS.QUARTERLY_PAYMENT_SUBMIT}
                        disabled={paymentAmount <= 0 || paymentMutation.isPending}
                        className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {paymentMutation.isPending ? 'Recording…' : 'Record Payment'}
                    </button>
                </div>
                {paymentMutation.error && (
                    <div role="alert" className="text-sm text-red-400">
                        Failed: {paymentMutation.error instanceof Error ? paymentMutation.error.message : 'Unknown error'}
                    </div>
                )}
                {paymentMutation.isSuccess && (
                    <div role="status" className="text-sm text-green-400">
                        ✓ Payment recorded successfully
                    </div>
                )}
            </form>
        </div>
    )
}
