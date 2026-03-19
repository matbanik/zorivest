import { useState, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { CommandRegistryEntry } from './types'

/**
 * useDynamicEntries — returns CommandRegistryEntry[] from TanStack Query cache.
 *
 * Per 06a-gui-shell.md §Dynamic Entry Composition:
 * - Returns entries derived from cached data
 * - Returns empty array until caches are populated by data pages
 * - Re-evaluates when query cache changes via subscription
 *
 * NOTE: Trade search was intentionally moved to the Trades tab filter bar.
 * The command palette is for navigation and actions, not data search.
 */
export function useDynamicEntries(
    _navigate?: (path: string) => void,
): CommandRegistryEntry[] {
    const queryClient = useQueryClient()
    const [entries, setEntries] = useState<CommandRegistryEntry[]>([])

    const buildEntries = useCallback(() => {
        const result: CommandRegistryEntry[] = []

        // Future: add account entries, watchlist entries, etc. here
        // Trade search is handled by the filter bar on the Trades page.

        setEntries(result)
    }, [queryClient])

    useEffect(() => {
        buildEntries()

        const unsubscribe = queryClient.getQueryCache().subscribe(() => {
            buildEntries()
        })

        return unsubscribe
    }, [queryClient, buildEntries])

    return entries
}
