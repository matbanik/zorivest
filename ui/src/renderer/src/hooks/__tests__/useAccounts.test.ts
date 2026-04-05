import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ── Mocks ──────────────────────────────────────────────────────────────────

const mockApiFetch = vi.fn()
vi.mock('@/lib/api', () => ({
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

import { useAccounts, type Account } from '../useAccounts'

// ── Test Data ──────────────────────────────────────────────────────────────

const MOCK_ACCOUNTS: Account[] = [
    {
        account_id: 'ACC001',
        name: 'Main Trading',
        account_type: 'BROKER',
        institution: 'IB LLC',
        currency: 'USD',
        is_tax_advantaged: false,
        notes: '',
        latest_balance: 50000.0,
        latest_balance_date: '2025-03-15T00:00:00',
    },
    {
        account_id: 'ACC002',
        name: 'IRA',
        account_type: 'RETIREMENT',
        institution: 'Fidelity',
        currency: 'USD',
        is_tax_advantaged: true,
        notes: '',
        latest_balance: 25000.0,
        latest_balance_date: '2025-03-10T00:00:00',
    },
    {
        account_id: 'ACC003',
        name: 'Paper',
        account_type: 'BROKER',
        institution: '',
        currency: 'USD',
        is_tax_advantaged: false,
        notes: '',
        latest_balance: null,
        latest_balance_date: null,
    },
]

// ── Helper ─────────────────────────────────────────────────────────────────

function createWrapper() {
    const client = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    })
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return React.createElement(QueryClientProvider, { client }, children)
    }
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe('MEU-71b: useAccounts', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('AC-6: fetches accounts from GET /api/v1/accounts', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_ACCOUNTS)

        const { result } = renderHook(() => useAccounts(), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(mockApiFetch).toHaveBeenCalledWith('/api/v1/accounts')
        expect(result.current.accounts).toHaveLength(3)
        expect(result.current.accounts[0].account_id).toBe('ACC001')
    })

    it('AC-6: computes portfolioTotal from latest_balance fields', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_ACCOUNTS)

        const { result } = renderHook(() => useAccounts(), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        // 50000 + 25000 + 0 (null treated as 0) = 75000
        expect(result.current.portfolioTotal).toBe(75000)
    })

    it('AC-6: returns zero portfolioTotal for empty accounts list', async () => {
        mockApiFetch.mockResolvedValueOnce([])

        const { result } = renderHook(() => useAccounts(), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(result.current.portfolioTotal).toBe(0)
        expect(result.current.accounts).toHaveLength(0)
    })

    it('AC-6: handles fetch error gracefully', async () => {
        mockApiFetch.mockRejectedValueOnce(new Error('API 500: Internal error'))

        const { result } = renderHook(() => useAccounts(), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(result.current.error).toBeTruthy()
        })

        expect(result.current.error).toBe('API 500: Internal error')
        expect(result.current.accounts).toHaveLength(0)
        expect(result.current.portfolioTotal).toBe(0)
    })

    it('AC-6: starts with initial empty data', () => {
        mockApiFetch.mockReturnValue(new Promise(() => {})) // never resolves

        const { result } = renderHook(() => useAccounts(), {
            wrapper: createWrapper(),
        })

        // With TanStack Query + initialData: [], isLoading is false
        // but accounts starts as the initialData []
        expect(result.current.accounts).toHaveLength(0)
    })
})
