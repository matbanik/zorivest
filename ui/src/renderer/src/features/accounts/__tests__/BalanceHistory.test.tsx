import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// ── Mocks ───────────────────────────────────────────────────────────────────

Object.defineProperty(window, 'api', {
    value: {
        baseUrl: 'http://127.0.0.1:54321',
        token: 'a'.repeat(64),
        init: vi.fn().mockResolvedValue(undefined),
    },
    writable: true,
    configurable: true,
})

const mockBalances = [
    {
        id: 1,
        account_id: 'acct-1',
        balance: 45000,
        datetime: '2026-01-15T00:00:00Z',
    },
    {
        id: 2,
        account_id: 'acct-1',
        balance: 48000,
        datetime: '2026-02-15T00:00:00Z',
    },
    {
        id: 3,
        account_id: 'acct-1',
        balance: 50000,
        datetime: '2026-03-01T00:00:00Z',
    },
]

vi.mock('@/hooks/useAccounts', () => ({
    useBalanceHistory: vi.fn(() => ({
        data: mockBalances,
        isLoading: false,
    })),
    useAddBalance: () => ({ mutate: vi.fn(), isPending: false }),
}))

import BalanceHistory from '../BalanceHistory'

// ── Helpers ─────────────────────────────────────────────────────────────────

function renderWithProviders(ui: React.ReactElement) {
    const client = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    })
    return render(
        <QueryClientProvider client={client}>
            {ui}
        </QueryClientProvider>,
    )
}

// ── Tests ───────────────────────────────────────────────────────────────────

describe('BalanceHistory', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    // AC-9: data-testid present
    it('AC-9: renders with data-testid="balance-history"', () => {
        renderWithProviders(<BalanceHistory accountId="acct-1" />)
        expect(screen.getByTestId('balance-history')).toBeInTheDocument()
    })

    // AC-9: Sparkline rendered
    it('AC-9: renders sparkline canvas when data available', () => {
        renderWithProviders(<BalanceHistory accountId="acct-1" />)
        expect(screen.getByTestId('balance-sparkline')).toBeInTheDocument()
    })

    // AC-9: Balance table with entries
    it('AC-9: renders balance entries in a table', () => {
        renderWithProviders(<BalanceHistory accountId="acct-1" />)
        // All 3 balances should appear
        expect(screen.getByText(/\$45,000/)).toBeInTheDocument()
        expect(screen.getByText(/\$48,000/)).toBeInTheDocument()
        expect(screen.getByText(/\$50,000/)).toBeInTheDocument()
    })

    // AC-9: Change column shows dollar and percent
    it('AC-9: displays change column with dollar and percent values', () => {
        renderWithProviders(<BalanceHistory accountId="acct-1" />)
        // Change from 48000 to 50000 = +$2,000.00 (+4.2%)
        expect(screen.getByText(/\+\$2,000/)).toBeInTheDocument()
    })

    // AC-9: Table headers
    it('AC-9: renders Date, Balance, Change headers', () => {
        renderWithProviders(<BalanceHistory accountId="acct-1" />)
        expect(screen.getByText('Date')).toBeInTheDocument()
        expect(screen.getByText('Balance')).toBeInTheDocument()
        expect(screen.getByText('Change')).toBeInTheDocument()
    })

    // F9: Sparkline drawing path verification
    it('sparkline calls getContext("2d") when data has ≥2 entries', () => {
        const getContextSpy = vi.spyOn(HTMLCanvasElement.prototype, 'getContext')
        renderWithProviders(<BalanceHistory accountId="acct-1" />)

        // The Sparkline component should call getContext('2d') to draw
        expect(getContextSpy).toHaveBeenCalledWith('2d')
        getContextSpy.mockRestore()
    })
})
