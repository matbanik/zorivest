/**
 * SortableColumnHeader — Reusable TanStack-compatible sortable table header.
 *
 * Renders a clickable <th> with sort direction indicators (↑ ↓).
 * Matches the pattern used in TradesTable.tsx for visual consistency.
 *
 * Source: docs/build-plan/06-gui.md §Table UX Standardization
 * MEU: MEU-199 (gui-table-list-primitives)
 */

import type { Column } from '@tanstack/react-table'
import type { CSSProperties, ReactNode } from 'react'

export interface SortableColumnHeaderProps<TData> {
    /** TanStack column instance */
    column: Column<TData, unknown>
    /** Header label text or node */
    children: ReactNode
    /** Text alignment (default: 'left') */
    align?: 'left' | 'right' | 'center'
    /** Optional inline style override */
    style?: CSSProperties
    /** Optional className */
    className?: string
}

export default function SortableColumnHeader<TData>({
    column,
    children,
    align = 'left',
    style,
    className,
}: SortableColumnHeaderProps<TData>) {
    const sortDirection = column.getIsSorted()
    const indicator = sortDirection === 'asc' ? ' ↑' : sortDirection === 'desc' ? ' ↓' : ''

    return (
        <th
            onClick={column.getToggleSortingHandler()}
            className={className}
            style={{
                padding: '8px 12px',
                fontWeight: 500,
                cursor: 'pointer',
                userSelect: 'none',
                textAlign: align,
                color: 'var(--color-fg-muted, #8b8fa3)',
                fontSize: '12px',
                whiteSpace: 'nowrap',
                ...style,
            }}
        >
            {children}
            {indicator && (
                <span
                    style={{
                        color: 'var(--color-accent, #6366f1)',
                        fontWeight: 600,
                    }}
                >
                    {indicator}
                </span>
            )}
        </th>
    )
}
