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

const mockUpdateMutate = vi.fn()
const mockDeleteMutate = vi.fn()
const mockAddBalanceMutate = vi.fn()

vi.mock('@/hooks/useAccounts', () => ({
    useAccounts: () => ({
        accounts: [],
        portfolioTotal: 0,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
    }),
    useCreateAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useUpdateAccount: () => ({ mutate: mockUpdateMutate, isPending: false }),
    useDeleteAccount: () => ({ mutate: mockDeleteMutate, isPending: false }),
    useForceDeleteAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useBalanceHistory: () => ({ data: [], isLoading: false }),
    useAddBalance: () => ({ mutate: mockAddBalanceMutate, isPending: false }),
    useArchiveAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useArchivedAccounts: () => ({ accounts: [], isLoading: false, isFetching: false, error: null, refetch: vi.fn() }),
    fetchTradeCounts: vi.fn().mockResolvedValue({}),
}))

import AccountDetailPanel from '../AccountDetailPanel'

// ── Helpers ─────────────────────────────────────────────────────────────────

const mockAccount = {
    account_id: 'acct-1',
    name: 'Interactive Brokers',
    account_type: 'broker',
    institution: 'IB LLC',
    currency: 'USD',
    is_tax_advantaged: false,
    notes: 'Main trading account',
    latest_balance: 50000,
    latest_balance_date: '2026-03-01',
}

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

describe('AccountDetailPanel', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    // AC-5: Form fields rendered
    it('AC-5: renders form with name, type, institution, tax-advantaged, notes fields', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)

        expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/type/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/institution/i)).toBeInTheDocument()
        // Currency dropdown deferred — see AccountDetailPanel.tsx DEFERRED comment
        expect(screen.getByLabelText(/tax.?advantaged/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/notes/i)).toBeInTheDocument()
    })

    // AC-5: Form pre-populated with account data
    it('AC-5: pre-populates form fields with account data', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)

        expect(screen.getByLabelText(/name/i)).toHaveValue('Interactive Brokers')
        expect(screen.getByLabelText(/institution/i)).toHaveValue('IB LLC')
        expect(screen.getByLabelText(/notes/i)).toHaveValue('Main trading account')
    })

    // AC-6: Latest balance displayed
    it('AC-6: displays latest balance', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)
        expect(screen.getByText(/50,000/)).toBeInTheDocument()
    })

    // AC-7: Save button present
    it('AC-7: renders a Save button', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)
        expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
    })

    // AC-7: Save triggers update mutation
    it('AC-7: clicking Save calls useUpdateAccount mutation', async () => {
        const user = userEvent.setup()
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)

        await user.click(screen.getByRole('button', { name: /save/i }))

        await waitFor(() => {
            expect(mockUpdateMutate).toHaveBeenCalled()
        })
    })

    // AC-8: Delete button present
    it('AC-8: renders a Delete button', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)
        expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    // AC-8: Delete requires confirmation
    it('AC-8: clicking Delete shows confirmation before calling mutation', async () => {
        const user = userEvent.setup()
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)

        await user.click(screen.getByRole('button', { name: /delete/i }))

        // Confirmation dialog should appear
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument()
    })

    // AC-6: Update Balance button present
    it('AC-6: renders an "Update Balance" button', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)
        expect(screen.getByRole('button', { name: /update balance/i })).toBeInTheDocument()
    })

    // data-testid for detail panel
    it('has data-testid="account-detail-panel"', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)
        expect(screen.getByTestId('account-detail-panel')).toBeInTheDocument()
    })

    // F6: Create mode hides edit-only UI
    it('isNew mode hides balance section, delete button, and balance history', () => {
        const newAccount = { ...mockAccount, account_id: '', name: '', latest_balance: null, latest_balance_date: null }
        renderWithProviders(<AccountDetailPanel account={newAccount} isNew onCreated={vi.fn()} />)

        // Balance section and Update Balance button should be absent
        expect(screen.queryByText(/Latest Balance/)).not.toBeInTheDocument()
        expect(screen.queryByRole('button', { name: /update balance/i })).not.toBeInTheDocument()
        // Delete button should be absent
        expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
        // Balance history component should be absent
        expect(screen.queryByTestId('balance-history')).not.toBeInTheDocument()
    })

    // F6: Create mode shows "Create" button label
    it('isNew mode shows "Create" button instead of "Save"', () => {
        const newAccount = { ...mockAccount, account_id: '', name: '', latest_balance: null, latest_balance_date: null }
        renderWithProviders(<AccountDetailPanel account={newAccount} isNew onCreated={vi.fn()} />)

        expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
        expect(screen.queryByRole('button', { name: /^save$/i })).not.toBeInTheDocument()
    })

    // ── Dirty-state guard tests (G22/G23) ─────────────────────────────────

    // G22-1: Save button text is "Save" when form is clean (no bullet)
    it('G22-1: save button shows "Save" when form is clean', () => {
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)
        const saveBtn = screen.getByRole('button', { name: /save/i })
        expect(saveBtn.textContent).not.toContain('•')
    })

    // G22-2: Save button shows amber-pulse and bullet when form is dirty
    it('G22-2: save button shows dirty indicators after field change', async () => {
        const user = userEvent.setup()
        renderWithProviders(<AccountDetailPanel account={mockAccount} />)

        // Modify the name field to make form dirty
        const nameInput = screen.getByLabelText(/name/i)
        await user.clear(nameInput)
        await user.type(nameInput, 'Changed Name')

        await waitFor(() => {
            const saveBtn = screen.getByRole('button', { name: /save/i })
            expect(saveBtn.className).toContain('btn-save-dirty')
            expect(saveBtn.textContent).toContain('•')
        })
    })

    // G22-3: onDirtyChange fires when form becomes dirty
    it('G22-3: onDirtyChange fires true when form becomes dirty', async () => {
        const onDirtyChange = vi.fn()
        const user = userEvent.setup()
        renderWithProviders(<AccountDetailPanel account={mockAccount} onDirtyChange={onDirtyChange} />)

        const nameInput = screen.getByLabelText(/name/i)
        await user.clear(nameInput)
        await user.type(nameInput, 'Changed')

        await waitFor(() => {
            expect(onDirtyChange).toHaveBeenCalledWith(true)
        })
    })
})
