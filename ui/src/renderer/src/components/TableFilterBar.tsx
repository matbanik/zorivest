/**
 * TableFilterBar — Reusable search + category filter bar for tables/lists.
 *
 * Provides a debounced search input and optional category dropdown filter.
 * Matches the TradesLayout filter bar pattern for visual consistency.
 *
 * Source: docs/build-plan/06-gui.md §Table UX Standardization
 * MEU: MEU-199 (gui-table-list-primitives)
 */

import { useState, useEffect, useRef, useCallback } from 'react'

export interface FilterOption {
    label: string
    value: string
}

export interface TableFilterBarProps {
    /** Placeholder text for search input */
    searchPlaceholder?: string
    /** Current search value (controlled) */
    searchValue: string
    /** Called when search value changes (debounced) */
    onSearchChange: (value: string) => void
    /** Debounce delay in ms (default: 300) */
    debounceMs?: number
    /** Optional category filter options */
    filterOptions?: FilterOption[]
    /** Current filter value */
    filterValue?: string
    /** Called when filter changes */
    onFilterChange?: (value: string) => void
    /** Filter label (e.g., "Type", "Status") */
    filterLabel?: string
}

export default function TableFilterBar({
    searchPlaceholder = 'Search…',
    searchValue,
    onSearchChange,
    debounceMs = 300,
    filterOptions,
    filterValue = '',
    onFilterChange,
    filterLabel = 'Filter',
}: TableFilterBarProps) {
    const [localSearch, setLocalSearch] = useState(searchValue)
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    // Sync external changes
    useEffect(() => {
        setLocalSearch(searchValue)
    }, [searchValue])

    const handleSearchInput = useCallback(
        (value: string) => {
            setLocalSearch(value)
            if (debounceMs === 0) {
                onSearchChange(value)
                return
            }
            if (timeoutRef.current) clearTimeout(timeoutRef.current)
            timeoutRef.current = setTimeout(() => {
                onSearchChange(value)
            }, debounceMs)
        },
        [onSearchChange, debounceMs],
    )

    // Cleanup timeout on unmount
    useEffect(() => {
        return () => {
            if (timeoutRef.current) clearTimeout(timeoutRef.current)
        }
    }, [])

    return (
        <div
            data-testid="table-filter-bar"
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 0',
            }}
        >
            {/* Search input */}
            <div style={{ position: 'relative', flex: 1 }}>
                <input
                    type="text"
                    value={localSearch}
                    onChange={(e) => handleSearchInput(e.target.value)}
                    placeholder={searchPlaceholder}
                    data-testid="table-search-input"
                    aria-label={searchPlaceholder}
                    style={{
                        width: '100%',
                        padding: '6px 12px 6px 32px',
                        borderRadius: '6px',
                        border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                        backgroundColor: 'var(--color-bg, #171923)',
                        color: 'var(--color-fg, #e0e0e0)',
                        fontSize: '13px',
                        outline: 'none',
                    }}
                />
                {/* Search icon */}
                <span
                    style={{
                        position: 'absolute',
                        left: '10px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: 'var(--color-fg-muted, #8b8fa3)',
                        fontSize: '14px',
                        pointerEvents: 'none',
                    }}
                >
                    🔍
                </span>
            </div>

            {/* Category filter dropdown */}
            {filterOptions && filterOptions.length > 0 && onFilterChange && (
                <select
                    value={filterValue}
                    onChange={(e) => onFilterChange(e.target.value)}
                    data-testid="table-filter-select"
                    aria-label={filterLabel}
                    style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                        backgroundColor: 'var(--color-bg, #171923)',
                        color: 'var(--color-fg, #e0e0e0)',
                        fontSize: '13px',
                        outline: 'none',
                        cursor: 'pointer',
                    }}
                >
                    <option value="">All {filterLabel}s</option>
                    {filterOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
            )}
        </div>
    )
}
