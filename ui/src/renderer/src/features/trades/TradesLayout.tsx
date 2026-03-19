import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import TradesTable, { type Trade } from './TradesTable'
import TradeDetailPanel from './TradeDetailPanel'

// Empty trade template for "New Trade" creation
const NEW_TRADE: Trade = {
    exec_id: '(new)',
    instrument: '',
    action: 'BOT',
    quantity: 0,
    price: 0,
    account_id: '',
    commission: 0,
    realized_pnl: null,
    notes: null,
    image_count: 0,
    time: new Date().toISOString(),
}

interface GuardStatusResponse {
    is_locked: boolean
}

/**
 * TradesLayout — list+detail split layout per 06b-gui-trades.md.
 *
 * Left pane (~60%): TradesTable
 * Right pane (~40%): TradeDetailPanel (slides in on row select or + New Trade)
 *
 * MCP Guard integration: when guard is locked, trade creation is disabled.
 */
export default function TradesLayout() {
    const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null)
    const [filterQuery, setFilterQuery] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    // Debounce the search input (300ms)
    const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined)
    useEffect(() => {
        debounceRef.current = setTimeout(() => {
            setDebouncedSearch(filterQuery.trim())
        }, 300)
        return () => clearTimeout(debounceRef.current)
    }, [filterQuery])

    const { data: trades = [], refetch, isFetching } = useQuery<Trade[]>({
        queryKey: ['trades', { search: debouncedSearch }],
        queryFn: async () => {
            try {
                const params = new URLSearchParams({ limit: '200', offset: '0' })
                if (debouncedSearch) params.set('search', debouncedSearch)
                const result = await apiFetch<{ items: Trade[] }>(`/api/v1/trades?${params}`)
                return result.items
            } catch {
                return []
            }
        },
        refetchInterval: 5_000,
    })

    const { data: guardStatus } = useQuery<GuardStatusResponse>({
        queryKey: ['mcp-guard-status'],
        queryFn: () => apiFetch('/api/v1/mcp-guard/status'),
    })

    const isGuardLocked = guardStatus?.is_locked ?? false

    // Listen for command-palette trade selection
    useEffect(() => {
        const handler = (e: Event) => {
            const { exec_id } = (e as CustomEvent<{ exec_id: string }>).detail
            const match = trades.find((t) => t.exec_id === exec_id)
            if (match) {
                setSelectedTrade(match)
            }
        }
        window.addEventListener('zorivest:select-trade', handler)
        return () => window.removeEventListener('zorivest:select-trade', handler)
    }, [trades])

    const handleRefresh = useCallback(() => {
        setStatus('Refreshing trades...')
        refetch().then(() => setStatus('Trades refreshed'))
    }, [refetch, setStatus])

    const handleSelectTrade = useCallback((trade: Trade) => {
        setSelectedTrade(trade)
    }, [])

    const handleNewTrade = useCallback(() => {
        setSelectedTrade({ ...NEW_TRADE, time: new Date().toISOString() })
    }, [])

    const handleClose = useCallback(() => {
        setSelectedTrade(null)
    }, [])

    const handleSaveTrade = useCallback(
        async (data: Record<string, unknown>) => {
            const isCreate = selectedTrade?.exec_id === '(new)'
            try {
                if (isCreate) {
                    setStatus('Creating trade...')
                    await apiFetch('/api/v1/trades', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            exec_id: `${Date.now()}`,
                            time: new Date().toISOString(),
                            ...data,
                        }),
                    })
                    setStatus('Trade created')
                } else {
                    setStatus('Saving trade...')
                    await apiFetch(`/api/v1/trades/${selectedTrade!.exec_id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data),
                    })
                    setStatus('Trade saved')
                }
                await queryClient.invalidateQueries({ queryKey: ['trades'] })
                setSelectedTrade(null)
            } catch (err) {
                setStatus(`Error: ${err instanceof Error ? err.message : 'Failed to save trade'}`)
            }
        },
        [selectedTrade, queryClient, setStatus],
    )

    const handleDeleteTrade = useCallback(
        async (execId: string) => {
            try {
                setStatus('Deleting trade...')
                await apiFetch(`/api/v1/trades/${execId}`, {
                    method: 'DELETE',
                })
                setStatus('Trade deleted')
                await queryClient.invalidateQueries({ queryKey: ['trades'] })
                setSelectedTrade(null)
            } catch (err) {
                setStatus(`Error: ${err instanceof Error ? err.message : 'Failed to delete trade'}`)
            }
        },
        [queryClient, setStatus],
    )

    return (
        <div data-testid="trades-page" className="flex h-full">
            {/* Left: Table */}
            <div className={`flex-1 min-w-0 transition-all ${selectedTrade ? 'w-[60%]' : 'w-full'}`}>
                <div className="p-4">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-fg">Trades</h2>
                        <div className="flex items-center gap-2">
                            <button
                                data-testid="refresh-trades-btn"
                                onClick={handleRefresh}
                                disabled={isFetching}
                                title="Refresh trades list"
                                className="px-3 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isFetching ? '⟳' : '↻'} Refresh
                            </button>
                            <button
                                data-testid="add-trade-btn"
                                onClick={handleNewTrade}
                                disabled={isGuardLocked}
                                aria-disabled={isGuardLocked}
                                title={isGuardLocked ? 'Trade creation disabled — MCP Guard is locked' : 'Create a new trade'}
                                className="px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                + New Trade
                            </button>
                        </div>
                    </div>
                </div>

                {/* Search/Filter bar */}
                <div className="px-4 pb-3">
                    <input
                        type="search"
                        placeholder="Filter by instrument, exec ID, account, or action…"
                        value={filterQuery}
                        onChange={(e) => setFilterQuery(e.target.value)}
                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg placeholder:text-fg-muted/50 focus:outline-none focus:border-accent"
                        data-testid="trades-filter-input"
                    />
                </div>
                <TradesTable
                    data={trades}
                    selectedId={selectedTrade?.exec_id}
                    onSelectTrade={handleSelectTrade}
                />
            </div>

            {/* Right: Detail Panel — key forces remount on trade switch */}
            {selectedTrade && (
                <div className="w-[40%] min-w-[320px] max-w-[500px]">
                    <TradeDetailPanel
                        key={selectedTrade.exec_id}
                        trade={selectedTrade}
                        onSave={handleSaveTrade}
                        onDelete={handleDeleteTrade}
                        onClose={handleClose}
                    />
                </div>
            )}
        </div>
    )
}
