import {
    createColumnHelper,
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    getPaginationRowModel,
    flexRender,
    type SortingState,
    type ColumnDef,
} from '@tanstack/react-table'
import { useState, useMemo } from 'react'

// ── Types ────────────────────────────────────────────────────────────────

/** Resolve text-alignment class from column meta. Used by BOTH <th> and <td>
 *  so header/cell alignment can never drift apart. */
const getAlignClass = (meta: unknown): string =>
    (meta as any)?.align === 'right' ? 'text-right' : 'text-left'

export interface Trade {
    exec_id: string
    instrument: string
    action: 'BOT' | 'SLD'
    quantity: number
    price: number
    account_id: string
    commission: number
    realized_pnl: number | null
    notes: string | null
    image_count: number
    time: string
}

// ── Column Definitions ───────────────────────────────────────────────────

const col = createColumnHelper<Trade>()

export const tradeColumns = [
    col.accessor('time', {
        header: 'Time',
        cell: (info) => {
            try {
                const d = new Date(info.getValue())
                const mm = String(d.getMonth() + 1).padStart(2, '0')
                const dd = String(d.getDate()).padStart(2, '0')
                const yyyy = d.getFullYear()
                const time = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
                return `${mm}/${dd}/${yyyy} ${time}`
            } catch {
                return '—'
            }
        },
        sortingFn: 'datetime',
    }),
    col.accessor('instrument', {
        header: 'Instrument',
        cell: (info) => info.getValue(),
    }),
    col.accessor('action', {
        header: 'Action',
        cell: (info) => {
            const val = info.getValue()
            return (
                <span className={val === 'BOT' ? 'text-green-400' : 'text-red-400'}>
                    {val}
                </span>
            )
        },
    }),
    col.accessor('quantity', {
        header: 'Qty',
        cell: (info) => {
            const val = info.getValue()
            return val != null ? Number(val).toLocaleString() : '—'
        },
        meta: { align: 'right' as const },
    }),
    col.accessor('price', {
        header: 'Price',
        cell: (info) => {
            const val = info.getValue()
            return val != null ? Number(val).toFixed(2) : '—'
        },
        meta: { align: 'right' as const },
    }),
    col.accessor('account_id', {
        header: 'Account',
        cell: (info) => {
            const val = info.getValue()
            return <span title={val}>{val.length > 5 ? `${val.slice(0, 5)}…` : val}</span>
        },
    }),
    col.accessor('commission', {
        header: 'Comm',
        cell: (info) => {
            const val = info.getValue()
            return val != null ? Number(val).toFixed(2) : '—'
        },
        meta: { align: 'right' as const },
    }),
    col.accessor('realized_pnl', {
        header: 'P&L',
        cell: (info) => {
            const val = info.getValue()
            if (val === null) return ''
            return (
                <span className={val >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {val >= 0 ? '+' : ''}
                    {val.toFixed(0)}
                </span>
            )
        },
        meta: { align: 'right' as const },
    }),
    col.accessor('image_count', {
        header: '📷',
        cell: (info) => (info.getValue() > 0 ? `🖼×${info.getValue()}` : ''),
        enableSorting: false,
        size: 60,
    }),
] satisfies ColumnDef<Trade, any>[]

// ── Component ────────────────────────────────────────────────────────────

interface TradesTableProps {
    data: Trade[]
    selectedId?: string
    onSelectTrade?: (trade: Trade) => void
    pageSize?: number
}

/**
 * TradesTable — TanStack Table with 9 columns per 06b-gui-trades.md.
 *
 * Features: sorting, pagination (50/page default), row selection.
 */
export default function TradesTable({
    data,
    selectedId,
    onSelectTrade,
    pageSize = 50,
}: TradesTableProps) {
    const [sorting, setSorting] = useState<SortingState>([])

    const table = useReactTable({
        data,
        columns: tradeColumns,
        state: { sorting },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        initialState: {
            pagination: { pageSize },
        },
    })

    return (
        <div data-testid="trade-list" className="flex flex-col h-full">
            {/* Table */}
            <div className="flex-1 overflow-auto">
                <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-bg border-b border-bg-subtle">
                        {table.getHeaderGroups().map((hg) => (
                            <tr key={hg.id}>
                                {hg.headers.map((header) => (
                                    <th
                                        key={header.id}
                                        className={`px-3 py-2 font-medium cursor-pointer select-none text-fg-muted ${getAlignClass(header.column.columnDef.meta)}`}
                                        onClick={header.column.getToggleSortingHandler()}
                                        style={{ width: header.getSize() }}
                                    >
                                        {flexRender(header.column.columnDef.header, header.getContext())}
                                        {{ asc: ' ↑', desc: ' ↓' }[header.column.getIsSorted() as string] ?? ''}
                                    </th>
                                ))}
                            </tr>
                        ))}
                    </thead>
                    <tbody>
                        {table.getRowModel().rows.map((row) => (
                            <tr
                                key={row.id}
                                data-testid="trade-row"
                                onClick={() => onSelectTrade?.(row.original)}
                                className={`cursor-pointer border-b border-bg-subtle transition-colors
                                    ${row.original.exec_id === selectedId
                                        ? 'bg-accent/10 text-fg'
                                        : 'hover:bg-bg-elevated text-fg'}`}
                            >
                                {row.getVisibleCells().map((cell) => (
                                    <td
                                        key={cell.id}
                                        className={`px-3 py-2 ${getAlignClass(cell.column.columnDef.meta)}`}
                                    >
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-3 py-2 border-t border-bg-subtle text-sm text-fg-muted">
                <span>
                    Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
                </span>
                <div className="flex gap-2">
                    <button
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                        className="px-2 py-1 rounded bg-bg-elevated disabled:opacity-30"
                    >
                        Prev
                    </button>
                    <button
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                        className="px-2 py-1 rounded bg-bg-elevated disabled:opacity-30"
                    >
                        Next
                    </button>
                </div>
            </div>
        </div>
    )
}
