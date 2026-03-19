import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useDynamicEntries } from '../useDynamicEntries'

// Mock useNavigate since useDynamicEntries may be used in navigation contexts
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
    it('should return empty array when cache has no data', () => {
        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const { result } = renderHook(() => useDynamicEntries(), {
            wrapper: createWrapper(queryClient),
        })
        expect(result.current).toEqual([])
    })

    it('should return empty array even when trades are in cache (trade search moved to Trades tab)', () => {
        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })

        // Pre-populate cache with trade data
        queryClient.setQueryData(['trades'], [
            { exec_id: 'E001', instrument: 'AAPL' },
            { exec_id: 'E002', instrument: 'TSLA' },
        ])

        const { result } = renderHook(() => useDynamicEntries(), {
            wrapper: createWrapper(queryClient),
        })

        // Trade entries no longer appear in command palette
        expect(result.current).toEqual([])
    })
})
