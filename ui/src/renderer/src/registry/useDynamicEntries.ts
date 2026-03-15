import { useState, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { CommandRegistryEntry } from './types'

/**
 * useDynamicEntries — returns CommandRegistryEntry[] from TanStack Query cache.
 *
 * Per 06a-gui-shell.md §Dynamic Entry Composition:
 * - Returns entries derived from cached data (e.g. "Go to trade #123")
 * - Returns empty array until caches are populated by data pages
 * - Re-evaluates when query cache changes via subscription
 */
export function useDynamicEntries(): CommandRegistryEntry[] {
    const queryClient = useQueryClient()
    const [entries, setEntries] = useState<CommandRegistryEntry[]>([])

    const buildEntries = useCallback(() => {
        const result: CommandRegistryEntry[] = []

        // Pull trade entries from cache if available
        const tradesData = queryClient.getQueryData<{ id: number; symbol: string }[]>([
            'trades',
        ])
        if (tradesData) {
            for (const trade of tradesData.slice(0, 10)) {
                result.push({
                    id: `search:trade:${trade.id}`,
                    label: `Go to Trade #${trade.id} (${trade.symbol})`,
                    category: 'search',
                    keywords: [trade.symbol, String(trade.id), 'trade'],
                    action: () => {
                        console.info(`[command] Navigate to trade ${trade.id} — detail route not yet implemented`)
                    },
                })
            }
        }

        setEntries(result)
    }, [queryClient])

    useEffect(() => {
        // Build initial entries
        buildEntries()

        // Subscribe to cache changes
        const unsubscribe = queryClient.getQueryCache().subscribe(() => {
            buildEntries()
        })

        return unsubscribe
    }, [queryClient, buildEntries])

    return entries
}
