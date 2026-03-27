import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'

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
        account_type: 'broker',
        latest_balance: 50000.0,
        latest_balance_date: '2025-03-15T00:00:00',
    },
    {
        account_id: 'ACC002',
        name: 'IRA',
        account_type: 'retirement',
        latest_balance: 25000.0,
        latest_balance_date: '2025-03-10T00:00:00',
    },
    {
        account_id: 'ACC003',
        name: 'Paper',
        account_type: 'paper',
        latest_balance: null,
        latest_balance_date: null,
    },
]

// ── Tests ──────────────────────────────────────────────────────────────────

describe('MEU-71b: useAccounts', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('AC-6: fetches accounts from GET /api/v1/accounts', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_ACCOUNTS)

        const { result } = renderHook(() => useAccounts())

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(mockApiFetch).toHaveBeenCalledWith('/api/v1/accounts')
        expect(result.current.accounts).toHaveLength(3)
        expect(result.current.accounts[0].account_id).toBe('ACC001')
    })

    it('AC-6: computes portfolioTotal from latest_balance fields', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_ACCOUNTS)

        const { result } = renderHook(() => useAccounts())

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        // 50000 + 25000 + 0 (null treated as 0) = 75000
        expect(result.current.portfolioTotal).toBe(75000)
    })

    it('AC-6: returns zero portfolioTotal for empty accounts list', async () => {
        mockApiFetch.mockResolvedValueOnce([])

        const { result } = renderHook(() => useAccounts())

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(result.current.portfolioTotal).toBe(0)
        expect(result.current.accounts).toHaveLength(0)
    })

    it('AC-6: handles fetch error gracefully', async () => {
        mockApiFetch.mockRejectedValueOnce(new Error('API 500: Internal error'))

        const { result } = renderHook(() => useAccounts())

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(result.current.error).toBe('API 500: Internal error')
        expect(result.current.accounts).toHaveLength(0)
        expect(result.current.portfolioTotal).toBe(0)
    })

    it('AC-6: starts in loading state', () => {
        mockApiFetch.mockReturnValue(new Promise(() => {})) // never resolves

        const { result } = renderHook(() => useAccounts())

        expect(result.current.isLoading).toBe(true)
        expect(result.current.accounts).toHaveLength(0)
    })
})
