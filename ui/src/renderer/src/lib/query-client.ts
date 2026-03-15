import { QueryClient } from '@tanstack/react-query'

/**
 * TanStack Query client with trading-specific defaults.
 *
 * - staleTime: 0 — Financial data is ALWAYS stale, always background-refetch
 * - gcTime: 5min — Prevent cache bloat in 8-16hr trading sessions
 * - refetchOnWindowFocus: true — Re-validate when trader returns
 * - retry: 2 — Retry failed reads twice
 * - mutations.retry: false — NEVER auto-retry financial transactions
 */
export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 0,
            gcTime: 5 * 60 * 1000,
            refetchOnWindowFocus: true,
            retry: 2,
        },
        mutations: {
            retry: false,
        },
    },
})
