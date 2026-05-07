import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import { usePersistedState } from '@/hooks/usePersistedState'
import { useFormGuard } from '@/hooks/useFormGuard'
import UnsavedChangesModal from '@/components/UnsavedChangesModal'
import ConfirmDeleteModal from '@/components/ConfirmDeleteModal'
import { useConfirmDelete } from '@/hooks/useConfirmDelete'
import SelectionCheckbox from '@/components/SelectionCheckbox'
import BulkActionBar from '@/components/BulkActionBar'
import TickerAutocomplete from '@/components/TickerAutocomplete'
import WatchlistTable from './WatchlistTable'

// ── Types (G6: exact API field names) ────────────────────────────────────

interface WatchlistItem {
    id: number
    watchlist_id: number
    ticker: string
    added_at: string
    notes: string
}

interface Watchlist {
    id: number
    name: string
    description: string
    created_at: string
    updated_at: string
    items: WatchlistItem[]
}

interface MarketQuote {
    last_price: number
    change?: number         // Dollar change
    change_pct: number      // Percent change
    volume?: number
    symbol: string
    timestamp?: string      // ISO 8601 quote timestamp
}

// API response shape — matches backend MarketQuote DTO (market_dtos.py)
interface ApiMarketQuote {
    ticker: string
    price: number
    change: number | null
    change_pct: number | null
    volume: number | null
    provider: string
    timestamp?: string
}

/** Map backend DTO → UI MarketQuote (field name bridge). */
function mapApiQuote(api: ApiMarketQuote): MarketQuote {
    return {
        last_price: api.price,
        change: api.change ?? undefined,
        change_pct: api.change_pct ?? 0,
        volume: api.volume ?? undefined,
        symbol: api.ticker,
        timestamp: api.timestamp,
    }
}


// W2: Per-ticker quote fetcher — returns map of ticker → quote (or null)
// W2: Stagger-polled quote fetcher — fetches each ticker with 200ms delay
// to avoid API rate-limiting, tracks most recent timestamp for freshness.
function useWatchlistQuotes(tickers: string[]): {
    quotes: Record<string, MarketQuote | null>
    lastQuoteTime: string | null
} {
    const [quotes, setQuotes] = useState<Record<string, MarketQuote | null>>({})
    const [lastQuoteTime, setLastQuoteTime] = useState<string | null>(null)
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

    useEffect(() => {
        if (tickers.length === 0) return
        let cancelled = false

        // Initialise with null (loading/placeholder)
        setQuotes((prev) => {
            const next = { ...prev }
            tickers.forEach((t) => { if (!(t in next)) next[t] = null })
            return next
        })

        // Stagger-fetch: 4000 + Math.random() * 1000 per ticker (06i §6 — thundering herd prevention)
        const REFRESH_BASE_MS = 4000
        const REFRESH_JITTER_MS = 1000

        const fetchAll = () => {
            tickers.forEach((ticker) => {
                const delay = REFRESH_BASE_MS + Math.random() * REFRESH_JITTER_MS
                setTimeout(() => {
                    if (cancelled) return
                    apiFetch<ApiMarketQuote>(`/api/v1/market-data/quote?ticker=${encodeURIComponent(ticker)}`)
                        .then((raw) => {
                            if (!cancelled) {
                                const q = mapApiQuote(raw)
                                setQuotes((prev) => ({ ...prev, [ticker]: q }))
                                setLastQuoteTime(q.timestamp ?? new Date().toISOString())
                            }
                        })
                        .catch(() => {
                            // AC-W2-4: graceful degradation — keep null (shows '—')
                        })
                }, delay)
            })
        }

        fetchAll()

        // Auto-refresh every 5s (06i §6 — refetchInterval: 5000)
        intervalRef.current = setInterval(fetchAll, 5000)

        return () => {
            cancelled = true
            if (intervalRef.current) clearInterval(intervalRef.current)
        }
    }, [tickers.join(',')]) // eslint-disable-line react-hooks/exhaustive-deps

    return { quotes, lastQuoteTime }
}

// ── Component ────────────────────────────────────────────────────────────

export default function WatchlistPage() {
    const [selectedList, setSelectedList] = useState<Watchlist | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [nameInput, setNameInput] = useState('')
    const [descInput, setDescInput] = useState('')
    const [nameError, setNameError] = useState<string | null>(null)
    const [tickerInput, setTickerInput] = useState('')
    const [notesInput, setNotesInput] = useState('')
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    // AH-7: Search + selection state for watchlist sidebar
    const [sidebarSearch, setSidebarSearch] = useState('')
    const [selectedWlIds, setSelectedWlIds] = useState<Set<number>>(new Set())
    const [showBulkWlConfirm, setShowBulkWlConfirm] = useState(false)

    // W2: Fetch quotes for visible tickers when a watchlist is selected
    const visibleTickers = selectedList?.items.map((i) => i.ticker) ?? []
    const { quotes, lastQuoteTime } = useWatchlistQuotes(visibleTickers)

    // Colorblind mode — persisted via Settings API
    const [colorblind, setColorblind] = usePersistedState<boolean>('ui.watchlist.colorblind_mode', false)

    // Fetch watchlists (G5: 5s auto-refresh)
    const { data: watchlists = [] } = useQuery<Watchlist[]>({
        queryKey: ['watchlists'],
        queryFn: async () => {
            try {
                return await apiFetch<Watchlist[]>('/api/v1/watchlists/')
            } catch {
                return []
            }
        },
        refetchInterval: 5_000,
    })

    const handleSelect = useCallback((wl: Watchlist) => {
        setSelectedList(wl)
        setIsCreating(false)
        setNameInput(wl.name)
        setDescInput(wl.description)
        setNameError(null)
    }, [])

    // AH-7: Filtered watchlists
    const filteredWatchlists = useMemo(() => {
        if (!sidebarSearch.trim()) return watchlists
        const q = sidebarSearch.toLowerCase()
        return watchlists.filter((wl) =>
            wl.name.toLowerCase().includes(q) || wl.description.toLowerCase().includes(q)
        )
    }, [watchlists, sidebarSearch])

    // AH-7: Selection handlers
    const toggleWlSelect = useCallback((id: number) => {
        setSelectedWlIds(prev => {
            const next = new Set(prev)
            if (next.has(id)) next.delete(id)
            else next.add(id)
            return next
        })
    }, [])

    const toggleWlSelectAll = useCallback(() => {
        setSelectedWlIds(prev => {
            if (prev.size === filteredWatchlists.length && prev.size > 0) return new Set()
            return new Set(filteredWatchlists.map(wl => wl.id))
        })
    }, [filteredWatchlists])

    const handleBulkWlDelete = useCallback(async () => {
        for (const id of selectedWlIds) {
            await apiFetch(`/api/v1/watchlists/${id}`, { method: 'DELETE' })
        }
        setSelectedWlIds(new Set())
        setShowBulkWlConfirm(false)
        await queryClient.invalidateQueries({ queryKey: ['watchlists'] })
        setSelectedList(null)
        setStatus(`${selectedWlIds.size} watchlist(s) deleted`)
    }, [selectedWlIds, queryClient, setStatus])

    const handleNew = useCallback(() => {
        setSelectedList(null)
        setIsCreating(true)
        setNameInput('')
        setDescInput('')
        setNameError(null)
    }, [])

    // ── Dirty state computation ───────────────────────────────────────────
    const isDirty = (() => {
        if (isCreating) {
            return !!nameInput || !!descInput
        }
        if (!selectedList) return false
        return nameInput !== selectedList.name || descInput !== selectedList.description
    })()

    // ── Unsaved changes guard (3-button: parent-owned form) ─────────────
    const doNavigate = useCallback((target: Watchlist | '__new__' | null) => {
        if (target === '__new__') {
            handleNew()
        } else if (target) {
            handleSelect(target)
        }
    }, [handleSelect, handleNew])

    const { showModal, guardedSelect, handleCancel, handleDiscard, handleSaveAndContinue, isSaveDisabled } =
        useFormGuard<Watchlist | '__new__' | null>({
            isDirty,
            onNavigate: doNavigate,
            onSave: async () => {
                await handleSave()
            },
            isFormInvalid: () => !nameInput.trim() || nameInput.trim().length < 2,
        })

    const handleClose = useCallback(() => {
        setSelectedList(null)
        setIsCreating(false)
        setNameError(null)
    }, [])

    // Create / Update watchlist
    const handleSave = useCallback(async () => {
        if (!nameInput.trim()) {
            setNameError('Name is required')
            setStatus('Error: Please fix the highlighted fields')
            throw new Error('Validation failed')
        }
        if (nameInput.trim().length < 2) {
            setNameError('Name must be at least 2 characters')
            setStatus('Error: Please fix the highlighted fields')
            throw new Error('Validation failed')
        }
        setNameError(null)
        try {
            if (isCreating) {
                setStatus('Creating watchlist...')
                await apiFetch('/api/v1/watchlists/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: nameInput.trim(), description: descInput }),
                })
                setStatus('Watchlist created')
            } else if (selectedList) {
                setStatus('Updating watchlist...')
                await apiFetch(`/api/v1/watchlists/${selectedList.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: nameInput.trim(), description: descInput }),
                })
                setStatus('Watchlist updated')
            }
            await queryClient.invalidateQueries({ queryKey: ['watchlists'] })
            handleClose()
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed'
            // Parse API 422 errors for field-level feedback
            if (msg.includes('422') && msg.toLowerCase().includes('name')) {
                setNameError('Name is too short or invalid')
            }
            setStatus(`Error: ${msg}`)
        }
    }, [isCreating, selectedList, nameInput, descInput, queryClient, setStatus, handleClose])

    // Delete watchlist (G2: only shown for existing)
    const deleteConfirm = useConfirmDelete()
    const handleDelete = useCallback(() => {
        if (!selectedList) return
        deleteConfirm.confirmSingle('watchlist', selectedList.name, async () => {
            try {
                setStatus('Deleting watchlist...')
                await apiFetch(`/api/v1/watchlists/${selectedList.id}`, { method: 'DELETE' })
                setStatus('Watchlist deleted')
                await queryClient.invalidateQueries({ queryKey: ['watchlists'] })
                handleClose()
            } catch (err) {
                setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
            }
        })
    }, [selectedList, deleteConfirm, queryClient, setStatus, handleClose])

    // Add ticker to watchlist (AC-9)
    const handleAddTicker = useCallback(async () => {
        if (!selectedList || !tickerInput.trim()) return
        try {
            setStatus('Adding ticker...')
            await apiFetch(`/api/v1/watchlists/${selectedList.id}/items`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: tickerInput.trim().toUpperCase(), notes: notesInput }),
            })
            setStatus('Ticker added')
            setTickerInput('')
            setNotesInput('')
            await queryClient.invalidateQueries({ queryKey: ['watchlists'] })
            // Refetch selected watchlist to update items
            const updated = await apiFetch<Watchlist>(`/api/v1/watchlists/${selectedList.id}`)
            setSelectedList(updated)
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
        }
    }, [selectedList, tickerInput, notesInput, queryClient, setStatus])

    // Remove ticker (AC-9)
    const handleRemoveTicker = useCallback(async (ticker: string) => {
        if (!selectedList) return
        try {
            setStatus('Removing ticker...')
            await apiFetch(`/api/v1/watchlists/${selectedList.id}/items/${ticker}`, { method: 'DELETE' })
            setStatus('Ticker removed')
            await queryClient.invalidateQueries({ queryKey: ['watchlists'] })
            const updated = await apiFetch<Watchlist>(`/api/v1/watchlists/${selectedList.id}`)
            setSelectedList(updated)
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
        }
    }, [selectedList, queryClient, setStatus])

    // Update item notes (Bug-Fix: inline editing)
    const handleUpdateNotes = useCallback(async (ticker: string, notes: string) => {
        if (!selectedList) return
        try {
            setStatus('Updating notes...')
            await apiFetch(`/api/v1/watchlists/${selectedList.id}/items/${ticker}`, {
                method: 'PATCH',
                body: JSON.stringify({ notes }),
            })
            setStatus('Notes updated')
            const updated = await apiFetch<Watchlist>(`/api/v1/watchlists/${selectedList.id}`)
            setSelectedList(updated)
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
        }
    }, [selectedList, setStatus])

    const isDetailOpen = isCreating || selectedList !== null

    return (
        <>
        <div data-testid="watchlist-page" className="flex h-full">
            {/* Left: Watchlist List */}
            <div className={`flex-1 min-w-0 transition-all ${isDetailOpen ? 'w-[40%]' : 'w-full'}`}>
                <div className="p-4">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-fg">Watchlists</h2>
                        <button
                            data-testid="new-watchlist-btn"
                            onClick={() => guardedSelect('__new__')}
                            className="px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                        >
                            + New Watchlist
                        </button>
                    </div>

                    {/* AH-7: Search input */}
                    <div className="mb-3">
                        <input
                            data-testid="watchlist-sidebar-search"
                            type="text"
                            value={sidebarSearch}
                            onChange={(e) => setSidebarSearch(e.target.value)}
                            placeholder="Search watchlists…"
                            className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg placeholder:text-fg-muted/50"
                        />
                    </div>

                    {/* AH-7: Select-all */}
                    {filteredWatchlists.length > 0 && (
                        <div className="flex items-center gap-2 mb-2">
                            <SelectionCheckbox
                                checked={selectedWlIds.size === filteredWatchlists.length && filteredWatchlists.length > 0}
                                indeterminate={selectedWlIds.size > 0 && selectedWlIds.size < filteredWatchlists.length}
                                onChange={toggleWlSelectAll}
                                ariaLabel="Select all watchlists"
                                data-testid="select-all-watchlist-checkbox"
                            />
                            <span className="text-xs text-fg-muted">Select all</span>
                        </div>
                    )}

                    {/* AH-7: Bulk action bar */}
                    {selectedWlIds.size > 0 && (
                        <BulkActionBar
                            selectedCount={selectedWlIds.size}
                            entityLabel="watchlist"
                            onDelete={() => setShowBulkWlConfirm(true)}
                            onClearSelection={() => setSelectedWlIds(new Set())}
                        />
                    )}

                    <div className="space-y-2" data-testid="watchlist-list">
                        {filteredWatchlists.length === 0 && (
                            <p className="text-sm text-fg-muted py-4 text-center">No watchlists yet</p>
                        )}
                        {filteredWatchlists.map((wl) => (
                            <button
                                key={wl.id}
                                data-testid={`watchlist-card-${wl.id}`}
                                onClick={() => guardedSelect(wl)}
                                className={`w-full text-left px-4 py-3 rounded-md border cursor-pointer transition-colors ${selectedList?.id === wl.id
                                    ? 'border-accent bg-accent/10'
                                    : 'border-bg-subtle bg-bg hover:bg-bg-elevated'
                                    }`}
                            >
                                <div className="flex items-center gap-2">
                                    {/* AH-7: Row checkbox */}
                                    <span onClick={(e) => e.stopPropagation()}>
                                        <SelectionCheckbox
                                            checked={selectedWlIds.has(wl.id)}
                                            onChange={() => toggleWlSelect(wl.id)}
                                            ariaLabel={`Select ${wl.name}`}
                                            data-testid={`watchlist-row-checkbox-${wl.id}`}
                                        />
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between">
                                            <span className="font-medium text-fg">{wl.name}</span>
                                            <span className="text-xs text-fg-muted">
                                                {wl.items.length === 0
                                                    ? '0 items'
                                                    : wl.items.length <= 5
                                                        ? wl.items.map((i) => i.ticker).join(', ')
                                                        : `${wl.items.slice(0, 5).map((i) => i.ticker).join(', ')} +${wl.items.length - 5}`
                                                }
                                            </span>
                                        </div>
                                        {wl.description && (
                                            <div className="text-xs text-fg-muted mt-1">{wl.description}</div>
                                        )}
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right: Detail Panel */}
            {isDetailOpen && (
                <div className="w-[60%] border-l border-bg-subtle overflow-y-auto" data-testid="watchlist-detail-panel">
                    <div className="p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-md font-semibold text-fg">
                                {isCreating ? 'New Watchlist' : selectedList?.name}
                            </h3>
                            <button
                                onClick={handleClose}
                                className="text-fg-muted hover:text-fg cursor-pointer"
                                data-testid="close-watchlist-detail"
                            >
                                ✕
                            </button>
                        </div>

                        {/* Name + Description */}
                        <div className="space-y-3 mb-4">
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Name</label>
                                <input
                                    data-testid="watchlist-name"
                                    value={nameInput}
                                    onChange={(e) => { setNameInput(e.target.value); setNameError(null) }}
                                    className={`w-full px-3 py-1.5 text-sm rounded-md bg-bg border text-fg ${nameError ? 'border-red-500' : 'border-bg-subtle'}`}
                                    placeholder="My Watchlist"
                                />
                                {nameError && (
                                    <span className="text-xs text-red-400">{nameError}</span>
                                )}
                            </div>
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Description</label>
                                <textarea
                                    data-testid="watchlist-description"
                                    value={descInput}
                                    onChange={(e) => setDescInput(e.target.value)}
                                    rows={2}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y"
                                />
                            </div>
                            <div className="flex gap-2">
                                <button
                                    data-testid="watchlist-save-btn"
                                    onClick={() => handleSave().catch(() => { /* validation errors already rendered inline */ })}
                                    className={`px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer${isDirty ? ' btn-save-dirty' : ''}`}
                                >
                                    {isCreating ? 'Create' : (isDirty ? 'Save Changes •' : 'Save')}
                                </button>
                                {selectedList && !isCreating && (
                                    <button
                                        data-testid="watchlist-delete-btn"
                                        onClick={handleDelete}
                                        className="px-4 py-1.5 text-sm rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 cursor-pointer"
                                    >
                                        Delete
                                    </button>
                                )}
                                <button
                                    onClick={handleClose}
                                    className="px-4 py-1.5 text-sm rounded-md bg-bg text-fg-muted hover:text-fg border border-bg-subtle cursor-pointer"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>

                        {/* Items Table (AC-8, AC-9) — WatchlistTable */}
                        {selectedList && !isCreating && (
                            <div className="border-t border-bg-subtle pt-4">
                                <div className="flex items-center justify-between mb-3">
                                    <h4 className="text-sm font-semibold text-fg">Tickers</h4>
                                    {/* Colorblind toggle (AC-18) */}
                                    <button
                                        data-testid="colorblind-toggle"
                                        onClick={() => setColorblind(!colorblind)}
                                        className={`wl-cb-toggle${colorblind ? ' wl-cb-toggle--active' : ''}`}
                                    >
                                        <span>🔵</span>
                                        <span>{colorblind ? 'Colorblind: On' : 'Colorblind: Off'}</span>
                                    </button>
                                </div>

                                {/* Add ticker inline (AC-9) */}
                                <div className="flex gap-2 mb-3">
                                    <div className="w-32">
                                        <TickerAutocomplete
                                            value={tickerInput}
                                            onChange={setTickerInput}
                                            placeholder="Ticker (e.g. AAPL)"
                                            data-testid="watchlist-ticker-input"
                                        />
                                    </div>
                                    <input
                                        data-testid="watchlist-notes-input"
                                        value={notesInput}
                                        onChange={(e) => setNotesInput(e.target.value)}
                                        onKeyDown={(e) => { if (e.key === 'Enter') handleAddTicker() }}
                                        placeholder="Notes (optional)"
                                        className="flex-1 px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    />
                                    <button
                                        data-testid="watchlist-add-ticker-btn"
                                        onClick={handleAddTicker}
                                        disabled={!tickerInput.trim()}
                                        className="px-3 py-1.5 text-sm rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        + Add
                                    </button>
                                </div>

                                {/* Professional data table */}
                                <div data-testid="watchlist-items">
                                    <WatchlistTable
                                        items={selectedList.items}
                                        quotes={quotes}
                                        colorblind={colorblind}
                                        onRemoveTicker={handleRemoveTicker}
                                        onUpdateNotes={handleUpdateNotes}
                                        lastQuoteTime={lastQuoteTime}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>

            <UnsavedChangesModal
                open={showModal}
                onCancel={handleCancel}
                onDiscard={handleDiscard}
                onSave={handleSaveAndContinue}
                isSaveDisabled={isSaveDisabled}
            />

            {deleteConfirm.target && (
                <ConfirmDeleteModal
                    open={deleteConfirm.showModal}
                    target={deleteConfirm.target}
                    onCancel={deleteConfirm.handleCancel}
                    onConfirm={deleteConfirm.handleConfirm}
                />
            )}

            {/* AH-7: Bulk delete confirmation for watchlist sidebar */}
            <ConfirmDeleteModal
                open={showBulkWlConfirm}
                target={{ count: selectedWlIds.size, type: selectedWlIds.size === 1 ? 'watchlist' : 'watchlists' }}
                onCancel={() => setShowBulkWlConfirm(false)}
                onConfirm={handleBulkWlDelete}
            />
        </>
    )
}
