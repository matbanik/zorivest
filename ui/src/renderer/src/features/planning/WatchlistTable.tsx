/**
 * WatchlistTable — Professional trading data table component.
 *
 * MEU-70a Sub-MEU B — renders watchlist items with market data columns.
 *
 * Sources:
 * - 06i §1: column hierarchy (Ticker, Last Price, Chg $, Chg %, Volume)
 * - 06i §4: layout (32px rows, sticky header, zebra striping)
 * - 06i §5: coloring (gain/loss/muted with ▲/▼ arrows)
 * - 06i §6: freshness indicator
 *
 * Sorting: click headers to toggle asc/desc, matching Trades table convention.
 *
 * CSS: imports watchlist-tokens.css for design token custom properties.
 */

import { useState, useMemo, useCallback } from 'react'
import '../../styles/watchlist-tokens.css'
import { formatVolume, formatPrice, getChangeColor, formatFreshness } from './watchlist-utils'
import SelectionCheckbox from '@/components/SelectionCheckbox'
import BulkActionBar from '@/components/BulkActionBar'
import ConfirmDeleteModal from '@/components/ConfirmDeleteModal'

// ── Types ────────────────────────────────────────────────────────────────

export interface WatchlistItem {
    id: number
    watchlist_id: number
    ticker: string
    added_at: string
    notes: string
}

export interface MarketQuote {
    last_price: number
    change?: number         // Dollar change
    change_pct: number      // Percent change
    volume?: number
    symbol: string
    timestamp?: string      // ISO 8601 quote timestamp
}

export interface WatchlistTableProps {
    items: WatchlistItem[]
    quotes: Record<string, MarketQuote | null>
    colorblind: boolean
    onRemoveTicker?: (ticker: string) => void
    onUpdateNotes?: (ticker: string, notes: string) => void
    lastQuoteTime?: string | null  // Most recent quote timestamp for freshness
}

// ── Sort types ──────────────────────────────────────────────────────────

type SortField = 'ticker' | 'last_price' | 'change' | 'change_pct' | 'volume' | 'notes'
type SortDir = 'asc' | 'desc'

// ── Formatting helpers ──────────────────────────────────────────────────

function formatChange(value: number | null | undefined, prefix: boolean = true): string {
    if (value === null || value === undefined) return '—'
    const arrow = prefix ? (value > 0 ? '▲ ' : value < 0 ? '▼ ' : '') : ''
    const sign = value > 0 ? '+' : ''
    return `${arrow}${sign}${value.toFixed(2)}`
}

function formatChangePct(value: number | null | undefined): string {
    if (value === null || value === undefined) return '—'
    const arrow = value > 0 ? '▲ ' : value < 0 ? '▼ ' : ''
    const sign = value > 0 ? '+' : ''
    return `${arrow}${sign}${value.toFixed(2)}%`
}

// ── Sort indicator (matches Trades table convention) ─────────────────────

function SortIndicator({ field, sortField, sortDir }: {
    field: SortField
    sortField: SortField | null
    sortDir: SortDir
}) {
    if (field !== sortField) return null
    return <span data-testid={`sort-indicator-${field}`}>{sortDir === 'asc' ? ' ↑' : ' ↓'}</span>
}

// ── Component ────────────────────────────────────────────────────────────

export default function WatchlistTable({
    items,
    quotes,
    colorblind,
    onRemoveTicker,
    onUpdateNotes,
    lastQuoteTime,
}: WatchlistTableProps) {
    const [editingTicker, setEditingTicker] = useState<string | null>(null)
    const [editValue, setEditValue] = useState('')
    const [sortField, setSortField] = useState<SortField | null>(null)
    const [sortDir, setSortDir] = useState<SortDir>('asc')

    // MEU-202: Multi-select state
    const [selectedTickers, setSelectedTickers] = useState<Set<string>>(new Set())
    const [searchQuery, setSearchQuery] = useState('')
    const [showBulkConfirm, setShowBulkConfirm] = useState(false)

    const startEdit = (ticker: string, currentNotes: string) => {
        setEditingTicker(ticker)
        setEditValue(currentNotes)
    }

    const saveNotes = (ticker: string) => {
        onUpdateNotes?.(ticker, editValue)
        setEditingTicker(null)
        setEditValue('')
    }

    const cancelEdit = () => {
        setEditingTicker(null)
        setEditValue('')
    }

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            // Toggle direction on same field
            setSortDir(prev => prev === 'asc' ? 'desc' : 'asc')
        } else {
            // New field defaults to asc
            setSortField(field)
            setSortDir('asc')
        }
    }

    /** Get a numeric sort value for a given item+field, pushing nulls to the end. */
    const getNumericValue = useCallback((item: WatchlistItem, field: SortField): number => {
        const q = quotes[item.ticker]
        switch (field) {
            case 'last_price': return q?.last_price ?? -Infinity
            case 'change': return q?.change ?? -Infinity
            case 'change_pct': return q?.change_pct ?? -Infinity
            case 'volume': return q?.volume ?? -Infinity
            default: return 0
        }
    }, [quotes])

    // MEU-202: Text search filter
    const filteredItems = useMemo(() => {
        if (!searchQuery.trim()) return items
        const q = searchQuery.toLowerCase()
        return items.filter((item) =>
            item.ticker.toLowerCase().includes(q) ||
            item.notes.toLowerCase().includes(q)
        )
    }, [items, searchQuery])

    const sortedItems = useMemo(() => {
        if (!sortField) return filteredItems

        const sorted = [...filteredItems].sort((a, b) => {
            if (sortField === 'ticker') {
                return a.ticker.localeCompare(b.ticker)
            }
            if (sortField === 'notes') {
                return (a.notes || '').localeCompare(b.notes || '')
            }
            // Numeric fields
            const aVal = getNumericValue(a, sortField)
            const bVal = getNumericValue(b, sortField)
            return aVal - bVal
        })

        if (sortDir === 'desc') sorted.reverse()
        return sorted
    }, [filteredItems, sortField, sortDir, getNumericValue])

    // MEU-202: Selection handlers
    const toggleSelect = useCallback((ticker: string) => {
        setSelectedTickers(prev => {
            const next = new Set(prev)
            if (next.has(ticker)) next.delete(ticker)
            else next.add(ticker)
            return next
        })
    }, [])

    const toggleSelectAll = useCallback(() => {
        setSelectedTickers(prev => {
            if (prev.size === filteredItems.length && prev.size > 0) {
                return new Set()
            }
            return new Set(filteredItems.map(i => i.ticker))
        })
    }, [filteredItems])

    const handleBulkRemove = useCallback(async () => {
        const tickers = Array.from(selectedTickers)
        for (const ticker of tickers) {
            onRemoveTicker?.(ticker)
        }
        setSelectedTickers(new Set())
        setShowBulkConfirm(false)
    }, [selectedTickers, onRemoveTicker])

    if (items.length === 0) {
        return (
            <div className="wl-empty" data-testid="watchlist-table-empty">
                No tickers in this watchlist yet. Add one above.
            </div>
        )
    }

    const thClass = 'wl-th-sortable'

    return (
        <div className={colorblind ? 'wl-colorblind' : ''} data-testid="watchlist-table-wrapper">
            {/* MEU-202: Search input */}
            <div style={{ marginBottom: '8px' }}>
                <input
                    data-testid="ticker-search-input"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by ticker or notes…"
                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                />
            </div>

            {/* MEU-202: Bulk action bar */}
            {selectedTickers.size > 0 && (
                <BulkActionBar
                    selectedCount={selectedTickers.size}
                    entityLabel="ticker"
                    onDelete={() => setShowBulkConfirm(true)}
                    onClearSelection={() => setSelectedTickers(new Set())}
                />
            )}

            <table className="watchlist-table" data-testid="watchlist-table">
                <thead>
                    <tr>
                        {/* MEU-202: Select-all checkbox header */}
                        <th style={{ width: '32px', textAlign: 'center' }}>
                            <SelectionCheckbox
                                checked={selectedTickers.size === filteredItems.length && filteredItems.length > 0}
                                indeterminate={selectedTickers.size > 0 && selectedTickers.size < filteredItems.length}
                                onChange={toggleSelectAll}
                                ariaLabel="Select all tickers"
                                data-testid="select-all-ticker-checkbox"
                            />
                        </th>
                        <th
                            className={`wl-ticker ${thClass}`}
                            style={{ textAlign: 'left' }}
                            onClick={() => handleSort('ticker')}
                            data-testid="sort-header-ticker"
                        >
                            Ticker
                            <SortIndicator field="ticker" sortField={sortField} sortDir={sortDir} />
                        </th>
                        <th
                            className={`wl-num ${thClass}`}
                            style={{ textAlign: 'right' }}
                            onClick={() => handleSort('last_price')}
                            data-testid="sort-header-last_price"
                        >
                            Last Price
                            <SortIndicator field="last_price" sortField={sortField} sortDir={sortDir} />
                        </th>
                        <th
                            className={`wl-num ${thClass}`}
                            style={{ textAlign: 'right' }}
                            onClick={() => handleSort('change')}
                            data-testid="sort-header-change"
                        >
                            Chg $
                            <SortIndicator field="change" sortField={sortField} sortDir={sortDir} />
                        </th>
                        <th
                            className={`wl-num ${thClass}`}
                            style={{ textAlign: 'right' }}
                            onClick={() => handleSort('change_pct')}
                            data-testid="sort-header-change_pct"
                        >
                            Chg %
                            <SortIndicator field="change_pct" sortField={sortField} sortDir={sortDir} />
                        </th>
                        <th
                            className={`wl-num ${thClass}`}
                            style={{ textAlign: 'right' }}
                            onClick={() => handleSort('volume')}
                            data-testid="sort-header-volume"
                        >
                            Volume
                            <SortIndicator field="volume" sortField={sortField} sortDir={sortDir} />
                        </th>
                        <th
                            className={thClass}
                            style={{ textAlign: 'left', minWidth: '160px' }}
                            onClick={() => handleSort('notes')}
                            data-testid="sort-header-notes"
                        >
                            Notes
                            <SortIndicator field="notes" sortField={sortField} sortDir={sortDir} />
                        </th>
                        <th style={{ textAlign: 'center', width: '40px' }}></th>
                    </tr>
                </thead>
                <tbody>
                    {sortedItems.map((item) => {
                        const q = quotes[item.ticker]
                        const price = q?.last_price ?? null
                        const change = q?.change ?? null
                        const changePct = q?.change_pct ?? null
                        const volume = q?.volume ?? null
                        const changeColor = getChangeColor(changePct, colorblind)
                        const isEditing = editingTicker === item.ticker

                        return (
                            <tr key={item.id} data-testid={`watchlist-row-${item.ticker}`}>
                                {/* MEU-202: Row checkbox */}
                                <td style={{ textAlign: 'center', width: '32px' }}>
                                    <SelectionCheckbox
                                        checked={selectedTickers.has(item.ticker)}
                                        onChange={() => toggleSelect(item.ticker)}
                                        ariaLabel={`Select ${item.ticker}`}
                                        data-testid={`ticker-row-checkbox-${item.ticker}`}
                                    />
                                </td>
                                {/* Ticker */}
                                <td className="wl-ticker">{item.ticker}</td>

                                {/* Last Price */}
                                <td className="wl-num">{formatPrice(price)}</td>

                                {/* Change $ */}
                                <td className="wl-num" style={{ color: changeColor }}>
                                    {formatChange(change)}
                                </td>

                                {/* Change % */}
                                <td className="wl-num" style={{ color: changeColor }}>
                                    {formatChangePct(changePct)}
                                </td>

                                {/* Volume */}
                                <td className="wl-num" style={{ color: 'var(--wl-fg-muted)' }}>
                                    {formatVolume(volume)}
                                </td>

                                {/* Notes cell — inline editing */}
                                <td style={{ textAlign: 'left' }}>
                                    {isEditing ? (
                                        <span style={{ display: 'inline-flex', gap: '4px', alignItems: 'center' }}>
                                            <input
                                                data-testid={`notes-input-${item.ticker}`}
                                                type="text"
                                                value={editValue}
                                                onChange={(e) => setEditValue(e.target.value)}
                                                className="wl-notes-input"
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') saveNotes(item.ticker)
                                                    if (e.key === 'Escape') cancelEdit()
                                                }}
                                                autoFocus
                                            />
                                            <button
                                                data-testid={`save-notes-${item.ticker}`}
                                                onClick={() => saveNotes(item.ticker)}
                                                className="wl-notes-icon"
                                                title="Save notes"
                                                style={{ cursor: 'pointer', background: 'none', border: 'none' }}
                                            >
                                                ✓
                                            </button>
                                        </span>
                                    ) : (
                                        <span
                                            data-testid={`edit-notes-${item.ticker}`}
                                            onClick={() => startEdit(item.ticker, item.notes)}
                                            className={item.notes ? 'wl-notes-text' : 'wl-notes-placeholder'}
                                            title={item.notes || 'Click to add notes'}
                                            role="button"
                                            tabIndex={0}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' || e.key === ' ') startEdit(item.ticker, item.notes)
                                            }}
                                        >
                                            {item.notes || '—'}
                                        </span>
                                    )}
                                </td>

                                {/* Remove button */}
                                <td style={{ textAlign: 'center' }}>
                                    {onRemoveTicker && (
                                        <button
                                            data-testid={`remove-ticker-${item.ticker}`}
                                            onClick={() => onRemoveTicker(item.ticker)}
                                            className="wl-notes-icon"
                                            title="Remove"
                                            style={{ cursor: 'pointer', background: 'none', border: 'none' }}
                                        >
                                            ✕
                                        </button>
                                    )}
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>

            {/* Freshness indicator */}
            <div className="wl-freshness" data-testid="watchlist-freshness">
                {formatFreshness(lastQuoteTime)}
            </div>

            {/* MEU-202: Bulk remove confirmation */}
            <ConfirmDeleteModal
                open={showBulkConfirm}
                target={{ count: selectedTickers.size, type: selectedTickers.size === 1 ? 'ticker' : 'tickers' }}
                onCancel={() => setShowBulkConfirm(false)}
                onConfirm={handleBulkRemove}
            />
        </div>
    )
}
