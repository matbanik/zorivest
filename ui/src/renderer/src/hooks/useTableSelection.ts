/**
 * useTableSelection — TanStack row selection state wrapper.
 *
 * Provides convenient helpers for managing row selection state with
 * TanStack React Table's built-in selection model.
 *
 * Usage:
 *   const { rowSelection, setRowSelection, selectedCount, clearSelection, getSelectedRows }
 *     = useTableSelection()
 *
 * Source: docs/build-plan/06-gui.md §Table UX Standardization
 * MEU: MEU-199 (gui-table-list-primitives)
 */

import { useState, useCallback, useMemo } from 'react'
import type { RowSelectionState, Table } from '@tanstack/react-table'

export interface UseTableSelectionReturn<TData> {
    /** TanStack row selection state object */
    rowSelection: RowSelectionState
    /** TanStack setter for row selection */
    setRowSelection: React.Dispatch<React.SetStateAction<RowSelectionState>>
    /** Number of currently selected rows */
    selectedCount: number
    /** Clear all selections */
    clearSelection: () => void
    /** Get the selected row data from a TanStack table instance */
    getSelectedRows: (table: Table<TData>) => TData[]
}

export function useTableSelection<TData>(): UseTableSelectionReturn<TData> {
    const [rowSelection, setRowSelection] = useState<RowSelectionState>({})

    const selectedCount = useMemo(
        () => Object.keys(rowSelection).filter((k) => rowSelection[k]).length,
        [rowSelection],
    )

    const clearSelection = useCallback(() => {
        setRowSelection({})
    }, [])

    const getSelectedRows = useCallback(
        (table: Table<TData>): TData[] => {
            return table
                .getSelectedRowModel()
                .rows.map((row) => row.original)
        },
        [],
    )

    return {
        rowSelection,
        setRowSelection,
        selectedCount,
        clearSelection,
        getSelectedRows,
    }
}
