import React from 'react'
import { useBalanceHistory } from '@/hooks/useAccounts'
import { formatDate } from '@/lib/formatDate'
import type { BalanceEntry } from '@/hooks/useAccounts'

// ── Currency formatter ──────────────────────────────────────────────────────

const currencyFmt = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
})

const percentFmt = new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
})

// ── Sparkline (canvas-based) ────────────────────────────────────────────────

interface SparklineProps {
    data: number[]
    width?: number
    height?: number
}

function Sparkline({ data, width = 200, height = 40 }: SparklineProps) {
    const canvasRef = React.useRef<HTMLCanvasElement>(null)

    React.useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas || data.length < 2) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        const dpr = window.devicePixelRatio || 1
        canvas.width = width * dpr
        canvas.height = height * dpr
        ctx.scale(dpr, dpr)
        canvas.style.width = `${width}px`
        canvas.style.height = `${height}px`

        const min = Math.min(...data)
        const max = Math.max(...data)
        const range = max - min || 1
        const padding = 2

        ctx.clearRect(0, 0, width, height)
        ctx.beginPath()
        ctx.strokeStyle = data[data.length - 1] >= data[0] ? '#22c55e' : '#ef4444'
        ctx.lineWidth = 1.5
        ctx.lineJoin = 'round'

        data.forEach((val, i) => {
            const x = (i / (data.length - 1)) * (width - padding * 2) + padding
            const y = height - padding - ((val - min) / range) * (height - padding * 2)
            if (i === 0) ctx.moveTo(x, y)
            else ctx.lineTo(x, y)
        })

        ctx.stroke()
    }, [data, width, height])

    if (data.length < 2) {
        return (
            <div className="flex items-center justify-center text-xs text-fg-muted" style={{ width, height }}>
                Not enough data
            </div>
        )
    }

    return <canvas ref={canvasRef} data-testid="balance-sparkline" />
}

// ── BalanceHistory Component ────────────────────────────────────────────────

interface BalanceHistoryProps {
    accountId: string
}

/**
 * BalanceHistory — Sparkline chart + scrollable balance table.
 *
 * AC-9: Balance history sparkline + table with Date, Balance, Change ($ and %).
 * Uses canvas-based sparkline (no external charting library dependency).
 */
export default function BalanceHistory({ accountId }: BalanceHistoryProps) {
    const { data: balances, isLoading } = useBalanceHistory(accountId)
    const entries = Array.isArray(balances) ? balances : []

    // Sort by date ascending for sparkline
    const sorted = [...entries].sort(
        (a, b) => new Date(a.datetime ?? 0).getTime() - new Date(b.datetime ?? 0).getTime(),
    )

    // Compute change data for the table (show newest first)
    const tableRows = [...sorted].reverse().map((entry, idx, arr) => {
        const prevEntry = arr[idx + 1] // next in reversed = older entry
        const changeDollar = prevEntry ? entry.balance - prevEntry.balance : 0
        const changePercent = prevEntry && prevEntry.balance !== 0
            ? (entry.balance - prevEntry.balance) / prevEntry.balance
            : 0
        return { ...entry, changeDollar, changePercent }
    })

    if (isLoading) {
        return (
            <div data-testid="balance-history" className="animate-pulse text-xs text-fg-muted">
                Loading balance history...
            </div>
        )
    }

    return (
        <div data-testid="balance-history" className="flex flex-col gap-2">
            <h4 className="text-xs font-medium text-fg-muted uppercase tracking-wide">
                Balance History
            </h4>

            {/* Sparkline */}
            <Sparkline data={sorted.map((e) => e.balance)} />

            {/* Table */}
            {entries.length === 0 ? (
                <p className="text-xs text-fg-muted">No balance entries yet.</p>
            ) : (
                <div className="max-h-48 overflow-auto">
                    <table className="w-full text-left text-xs">
                        <thead className="sticky top-0 bg-bg-subtle">
                            <tr>
                                <th className="px-2 py-1 font-medium text-fg-muted">Date</th>
                                <th className="px-2 py-1 font-medium text-fg-muted text-right">Balance</th>
                                <th className="px-2 py-1 font-medium text-fg-muted text-right">Change</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tableRows.map((row) => (
                                <tr key={row.id} className="border-b border-border/50">
                                    <td className="px-2 py-1 tabular-nums">
                                        {formatDate(row.datetime)}
                                    </td>
                                    <td className="px-2 py-1 text-right tabular-nums">
                                        {currencyFmt.format(row.balance)}
                                    </td>
                                    <td className="px-2 py-1 text-right tabular-nums">
                                        {row.changeDollar !== 0 && (
                                            <span className={row.changeDollar > 0 ? 'text-green-500' : 'text-red-500'}>
                                                {row.changeDollar > 0 ? '+' : ''}
                                                {currencyFmt.format(row.changeDollar)}
                                                {' '}
                                                ({row.changePercent > 0 ? '+' : ''}
                                                {percentFmt.format(row.changePercent)})
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}
