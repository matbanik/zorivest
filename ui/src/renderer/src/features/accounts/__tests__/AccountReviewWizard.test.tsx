import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

const mockAddBalanceMutate = vi.fn()

const mockAccounts = [
    {
        account_id: 'acct-1',
        name: 'Interactive Brokers',
        account_type: 'broker',
        institution: 'IB LLC',
        currency: 'USD',
        is_tax_advantaged: false,
        notes: '',
        latest_balance: 50000,
        latest_balance_date: '2026-03-01',
    },
    {
        account_id: 'acct-2',
        name: 'Roth IRA',
        account_type: 'ira',
        institution: 'Fidelity',
        currency: 'USD',
        is_tax_advantaged: true,
        notes: '',
        latest_balance: 25000,
        latest_balance_date: '2026-03-01',
    },
]

vi.mock('@/hooks/useAccounts', () => ({
    useAccounts: () => ({
        accounts: mockAccounts,
        portfolioTotal: 75000,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
    }),
    useAddBalance: () => ({ mutateAsync: mockAddBalanceMutate, isPending: false }),
}))
// Mock useAccountContext
let mockActiveAccountId: string | null = null
vi.mock('@/context/AccountContext', () => ({
    useAccountContext: () => ({ activeAccountId: mockActiveAccountId, selectAccount: vi.fn(), mruAccountIds: [] }),
    AccountProvider: ({ children }: { children: React.ReactNode }) => children,
}))

import AccountReviewWizard from '../AccountReviewWizard'

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

describe('AccountReviewWizard', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockAddBalanceMutate.mockResolvedValue({})
        mockActiveAccountId = null
    })

    // AC-10: Wizard renders when open
    it('AC-10: renders wizard overlay when isOpen=true', () => {
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)
        expect(screen.getByTestId('account-review-wizard')).toBeInTheDocument()
    })

    // AC-10: Wizard does not render when closed
    it('AC-10: does not render when isOpen=false', () => {
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={false} onClose={onClose} />)
        expect(screen.queryByTestId('account-review-wizard')).not.toBeInTheDocument()
    })

    // AC-10: Shows progress "Account 1 of N"
    it('AC-10: shows progress indicator "Account 1 of 2"', () => {
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)
        expect(screen.getByText(/account 1 of 2/i)).toBeInTheDocument()
    })

    // AC-11: Shows account info
    it('AC-11: displays current account name and type', () => {
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)
        expect(screen.getByText('Interactive Brokers')).toBeInTheDocument()
        expect(screen.getByText('Broker')).toBeInTheDocument()
    })

    // AC-11: Shows current balance
    it('AC-11: displays current balance', () => {
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)
        expect(screen.getByText(/50,000/)).toBeInTheDocument()
    })

    // AC-11: Balance input pre-filled
    it('AC-11: has balance input pre-filled with latest balance', () => {
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)
        const input = screen.getByLabelText(/new balance/i)
        expect(input).toHaveValue(50000)
    })

    // AC-12: Skip button advances to next account
    it('AC-12: Skip button advances to next account', async () => {
        const user = userEvent.setup()
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)

        await user.click(screen.getByRole('button', { name: /skip/i }))

        expect(screen.getByText(/account 2 of 2/i)).toBeInTheDocument()
        expect(screen.getByText('Roth IRA')).toBeInTheDocument()
    })

    // AC-12: "Update & Next" advances to next account
    it('AC-12: "Update & Next" calls addBalance and advances', async () => {
        const user = userEvent.setup()
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)

        // Change balance to 51000
        const input = screen.getByLabelText(/new balance/i)
        await user.clear(input)
        await user.type(input, '51000')
        await user.click(screen.getByRole('button', { name: /update/i }))

        await waitFor(() => {
            expect(mockAddBalanceMutate).toHaveBeenCalledWith({
                accountId: 'acct-1',
                payload: { balance: 51000 },
            })
        })

        // Should advance to account 2
        expect(screen.getByText(/account 2 of 2/i)).toBeInTheDocument()
    })

    // AC-13: Completion view shows summary after last account
    it('AC-13: shows completion view after reviewing all accounts', async () => {
        const user = userEvent.setup()
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)

        // Skip both accounts
        await user.click(screen.getByRole('button', { name: /skip/i }))
        await user.click(screen.getByRole('button', { name: /skip/i }))

        // Should show completion view
        expect(screen.getByText(/review complete/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /done/i })).toBeInTheDocument()
    })

    // AC-16: Done button calls onClose
    it('AC-16: Done button calls onClose to dismiss wizard', async () => {
        const user = userEvent.setup()
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)

        // Skip all to reach completion
        await user.click(screen.getByRole('button', { name: /skip/i }))
        await user.click(screen.getByRole('button', { name: /skip/i }))

        await user.click(screen.getByRole('button', { name: /done/i }))
        expect(onClose).toHaveBeenCalled()
    })

    // AC-13: Fetch from API button shown for BROKER accounts
    it('AC-13: shows disabled Fetch from API button for BROKER accounts', () => {
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)
        // First account is BROKER
        const fetchBtn = screen.getByTestId('fetch-from-api-btn')
        expect(fetchBtn).toBeInTheDocument()
        expect(fetchBtn).toBeDisabled()
        expect(fetchBtn).toHaveAttribute('title', expect.stringContaining('Not yet connected'))
    })

    // AC-13: Fetch from API button NOT shown for non-BROKER accounts
    it('AC-13: does not show Fetch from API button for non-BROKER accounts', async () => {
        const user = userEvent.setup()
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)

        // Skip first (BROKER) account to reach RETIREMENT account
        await user.click(screen.getByRole('button', { name: /skip/i }))

        expect(screen.getByText('Roth IRA')).toBeInTheDocument()
        expect(screen.queryByTestId('fetch-from-api-btn')).not.toBeInTheDocument()
    })

    // AC-16: Wizard starts from selected account context
    it('AC-16: wizard starts from selected account when activeAccountId is set', () => {
        mockActiveAccountId = 'acct-2'
        const onClose = vi.fn()
        renderWithProviders(<AccountReviewWizard isOpen={true} onClose={onClose} />)

        // Should start on account 2 (Roth IRA), not account 1
        expect(screen.getByText('Roth IRA')).toBeInTheDocument()
        expect(screen.getByText(/account 2 of 2/i)).toBeInTheDocument()
    })
})
