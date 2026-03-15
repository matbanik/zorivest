import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useDynamicEntries } from '../useDynamicEntries'

// Mock useNavigate since useDynamicEntries indirectly used in components that may need it
vi.mock('@tanstack/react-router', async () => {
    const actual = await vi.importActual('@tanstack/react-router')
    return {
        ...actual,
        useNavigate: () => vi.fn(),
    }
})

function createWrapper(queryClient: QueryClient) {
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )
    }
}

describe('useDynamicEntries', () => {
    it('should return empty array when cache has no trade data', () => {
        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const { result } = renderHook(() => useDynamicEntries(), {
            wrapper: createWrapper(queryClient),
        })
        expect(result.current).toEqual([])
    })

    it('should return search entries when trades are in the query cache', () => {
        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })

        // Pre-populate cache with trade data
        queryClient.setQueryData(['trades'], [
            { id: 1, symbol: 'AAPL' },
            { id: 2, symbol: 'TSLA' },
        ])

        const { result } = renderHook(() => useDynamicEntries(), {
            wrapper: createWrapper(queryClient),
        })

        expect(result.current.length).toBe(2)
        expect(result.current[0].id).toBe('search:trade:1')
        expect(result.current[0].label).toBe('Go to Trade #1 (AAPL)')
        expect(result.current[0].category).toBe('search')
        expect(result.current[1].id).toBe('search:trade:2')
        expect(result.current[1].label).toBe('Go to Trade #2 (TSLA)')
    })

    it('should reactively update when cache changes', () => {
        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })

        const { result } = renderHook(() => useDynamicEntries(), {
            wrapper: createWrapper(queryClient),
        })

        // Initially empty
        expect(result.current).toEqual([])

        // Mutate cache → entries should update via subscription
        act(() => {
            queryClient.setQueryData(['trades'], [
                { id: 42, symbol: 'GOOG' },
            ])
        })

        expect(result.current.length).toBe(1)
        expect(result.current[0].id).toBe('search:trade:42')
        expect(result.current[0].category).toBe('search')
    })

    it('should cap entries at 10 trades', () => {
        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })

        // Create 15 trades
        const trades = Array.from({ length: 15 }, (_, i) => ({
            id: i + 1,
            symbol: `SYM${i + 1}`,
        }))
        queryClient.setQueryData(['trades'], trades)

        const { result } = renderHook(() => useDynamicEntries(), {
            wrapper: createWrapper(queryClient),
        })

        expect(result.current.length).toBe(10)
    })
})
