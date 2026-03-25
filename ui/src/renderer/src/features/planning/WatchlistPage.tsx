import { useState, useCallback, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import TickerAutocomplete from '@/components/TickerAutocomplete'

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
    change_pct: number
    symbol: string
}

// W2: Per-ticker quote fetcher — returns map of ticker → quote (or null)
function useWatchlistQuotes(tickers: string[]): Record<string, MarketQuote | null> {
    const [quotes, setQuotes] = useState<Record<string, MarketQuote | null>>({})

    useEffect(() => {
        if (tickers.length === 0) return
        let cancelled = false

        // Initialise with null (loading/placeholder)
        setQuotes((prev) => {
            const next = { ...prev }
            tickers.forEach((t) => { if (!(t in next)) next[t] = null })
            return next
        })

        tickers.forEach((ticker) => {
            apiFetch<MarketQuote>(`/api/v1/market-data/quote?ticker=${encodeURIComponent(ticker)}`)
                .then((q) => {
                    if (!cancelled) setQuotes((prev) => ({ ...prev, [ticker]: q }))
                })
                .catch(() => {
                    // AC-W2-4: graceful degradation — keep null (shows '—')
                })
        })
        return () => { cancelled = true }
    }, [tickers.join(',')]) // eslint-disable-line react-hooks/exhaustive-deps

    return quotes
}

// ── Component ────────────────────────────────────────────────────────────

export default function WatchlistPage() {
    const [selectedList, setSelectedList] = useState<Watchlist | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [nameInput, setNameInput] = useState('')
    const [descInput, setDescInput] = useState('')
    const [tickerInput, setTickerInput] = useState('')
    const [notesInput, setNotesInput] = useState('')
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    // W2: Fetch quotes for visible tickers when a watchlist is selected
    const visibleTickers = selectedList?.items.map((i) => i.ticker) ?? []
    const quotes = useWatchlistQuotes(visibleTickers)

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
    }, [])

    const handleNew = useCallback(() => {
        setSelectedList(null)
        setIsCreating(true)
        setNameInput('')
        setDescInput('')
    }, [])

    const handleClose = useCallback(() => {
        setSelectedList(null)
        setIsCreating(false)
    }, [])

    // Create / Update watchlist
    const handleSave = useCallback(async () => {
        try {
            if (isCreating) {
                setStatus('Creating watchlist...')
                await apiFetch('/api/v1/watchlists/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: nameInput, description: descInput }),
                })
                setStatus('Watchlist created')
            } else if (selectedList) {
                setStatus('Updating watchlist...')
                await apiFetch(`/api/v1/watchlists/${selectedList.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: nameInput, description: descInput }),
                })
                setStatus('Watchlist updated')
            }
            await queryClient.invalidateQueries({ queryKey: ['watchlists'] })
            handleClose()
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
        }
    }, [isCreating, selectedList, nameInput, descInput, queryClient, setStatus, handleClose])

    // Delete watchlist (G2: only shown for existing)
    const handleDelete = useCallback(async () => {
        if (!selectedList) return
        try {
            setStatus('Deleting watchlist...')
            await apiFetch(`/api/v1/watchlists/${selectedList.id}`, { method: 'DELETE' })
            setStatus('Watchlist deleted')
            await queryClient.invalidateQueries({ queryKey: ['watchlists'] })
            handleClose()
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
        }
    }, [selectedList, queryClient, setStatus, handleClose])

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

    const isDetailOpen = isCreating || selectedList !== null

    return (
        <div data-testid="watchlist-page" className="flex h-full">
            {/* Left: Watchlist List */}
            <div className={`flex-1 min-w-0 transition-all ${isDetailOpen ? 'w-[40%]' : 'w-full'}`}>
                <div className="p-4">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-fg">Watchlists</h2>
                        <button
                            data-testid="new-watchlist-btn"
                            onClick={handleNew}
                            className="px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                        >
                            + New Watchlist
                        </button>
                    </div>

                    <div className="space-y-2" data-testid="watchlist-list">
                        {watchlists.length === 0 && (
                            <p className="text-sm text-fg-muted py-4 text-center">No watchlists yet</p>
                        )}
                        {watchlists.map((wl) => (
                            <button
                                key={wl.id}
                                data-testid={`watchlist-card-${wl.id}`}
                                onClick={() => handleSelect(wl)}
                                className={`w-full text-left px-4 py-3 rounded-md border cursor-pointer transition-colors ${selectedList?.id === wl.id
                                    ? 'border-accent bg-accent/10'
                                    : 'border-bg-subtle bg-bg hover:bg-bg-elevated'
                                    }`}
                            >
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
                                    onChange={(e) => setNameInput(e.target.value)}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    placeholder="My Watchlist"
                                />
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
                                    onClick={handleSave}
                                    className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer"
                                >
                                    {isCreating ? 'Create' : 'Save'}
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

                        {/* Items Table (AC-8, AC-9) */}
                        {selectedList && !isCreating && (
                            <div className="border-t border-bg-subtle pt-4">
                                <h4 className="text-sm font-semibold text-fg mb-3">Tickers</h4>

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

                                {/* Items list */}
                                <div className="space-y-1" data-testid="watchlist-items">
                                    {selectedList.items.length === 0 && (
                                        <p className="text-xs text-fg-muted py-2 text-center">No tickers yet</p>
                                    )}
                                    {selectedList.items.map((item) => {
                                        const q = quotes[item.ticker]
                                        const hasPrice = q?.last_price != null
                                        const priceText = hasPrice ? (q!.last_price as number).toFixed(2) : '—'
                                        const changePct = (hasPrice && q?.change_pct != null) ? q.change_pct : null
                                        const changeText = changePct !== null
                                            ? `${changePct >= 0 ? '▲' : '▼'} ${Math.abs(changePct).toFixed(2)}%`
                                            : '—'
                                        const changeClass = changePct === null
                                            ? 'text-fg-muted'
                                            : changePct >= 0 ? 'text-gain' : 'text-loss'
                                        return (
                                            <div
                                                key={item.id}
                                                data-testid={`watchlist-item-${item.ticker}`}
                                                className="flex items-center justify-between px-3 py-2 rounded-md border border-bg-subtle bg-bg"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <span className="font-medium text-fg text-sm">{item.ticker}</span>
                                                    {item.notes && (
                                                        <span className="text-xs text-fg-muted">{item.notes}</span>
                                                    )}
                                                </div>
                                                {/* W2: Price + Change columns */}
                                                <div className="flex items-center gap-3">
                                                    <span
                                                        data-testid={`watchlist-price-${item.ticker}`}
                                                        className="text-sm font-mono text-fg"
                                                    >
                                                        {priceText}
                                                    </span>
                                                    <span
                                                        data-testid={`watchlist-change-${item.ticker}`}
                                                        className={`text-xs font-mono ${changeClass}`}
                                                    >
                                                        {changeText}
                                                    </span>
                                                    <button
                                                        data-testid={`remove-ticker-${item.ticker}`}
                                                        onClick={() => handleRemoveTicker(item.ticker)}
                                                        className="text-xs text-red-400 hover:text-red-300 cursor-pointer"
                                                        title="Remove"
                                                    >
                                                        ✕
                                                    </button>
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
