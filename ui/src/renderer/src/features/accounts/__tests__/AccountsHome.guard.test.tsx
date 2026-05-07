/**
 * R5: Parent-level AccountsHome invalid Save & Continue workflow tests.
 *
 * Proves the full chain: AccountDetailPanel.isInvalid() → useFormGuard(isFormInvalid)
 * → isSaveDisabled → UnsavedChangesModal Save & Continue button disabled.
 *
 * This test renders AccountsHome with an active account selected,
 * manipulates the child form to be dirty+invalid, triggers navigation,
 * and asserts the modal appears with Save & Continue disabled.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// ── Mocks ────────────────────────────────────────────────────────────────────

Object.defineProperty(window, 'api', {
    value: {
        baseUrl: 'http://127.0.0.1:54321',
        token: 'a'.repeat(64),
        init: vi.fn().mockResolvedValue(undefined),
    },
    writable: true,
    configurable: true,
})

Object.defineProperty(window, 'electronStore', {
    value: { get: vi.fn(), set: vi.fn() },
    writable: true,
    configurable: true,
})

vi.mock('fuse.js', () => ({
    default: class FuseMock {
        constructor() { /* noop */ }
        search() { return [] }
    },
}))

vi.mock('@tanstack/react-router', async () => {
    const actual = await vi.importActual('@tanstack/react-router')
    return {
        ...actual,
        useNavigate: () => vi.fn(),
        useLocation: () => ({ pathname: '/' }),
    }
})

const mockAccounts = [
    {
        account_id: 'acct-1',
        name: 'Interactive Brokers',
        account_type: 'broker',
        institution: 'IB LLC',
        currency: 'USD',
        is_tax_advantaged: false,
        is_archived: false,
        is_system: false,
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
        is_archived: false,
        is_system: false,
        notes: 'Tax free growth',
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
        isFetching: false,
        refetch: vi.fn(),
    }),
    useCreateAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useUpdateAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useDeleteAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useForceDeleteAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useBalanceHistory: () => ({ data: [], isLoading: false }),
    useAddBalance: () => ({ mutate: vi.fn(), isPending: false }),
    useArchiveAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useUnarchiveAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useArchivedAccounts: () => ({
        accounts: [], isLoading: false, isFetching: false, error: null, refetch: vi.fn(),
    }),
    fetchTradeCounts: vi.fn().mockResolvedValue({}),
}))

// CRITICAL: set activeAccountId to 'acct-1' so the detail panel renders
const mockSelectAccount = vi.fn()
vi.mock('@/context/AccountContext', () => ({
    AccountProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAccountContext: () => ({
        activeAccountId: 'acct-1',
        selectAccount: mockSelectAccount,
        mruAccountIds: ['acct-1', 'acct-2'],
    }),
}))

import AccountsHome from '../AccountsHome'

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

// ── R5: Parent-level guard integration tests ────────────────────────────────

describe('R5: AccountsHome invalid Save & Continue workflow', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('disables Save & Continue when account name is cleared and user navigates', async () => {
        renderWithProviders(<AccountsHome />)

        // Step 1: Detail panel should be visible for acct-1
        const nameInput = await waitFor(() => {
            const input = screen.getByTestId('account-name-input') as HTMLInputElement
            expect(input).toBeInTheDocument()
            return input
        })
        expect(nameInput.value).toBe('Interactive Brokers')

        // Step 2: Clear the name field — makes form dirty AND invalid
        fireEvent.change(nameInput, { target: { value: '' } })

        // Step 3: Navigate to acct-2 by clicking its row in the table
        const table = screen.getByTestId('account-list')
        const rothRow = Array.from(table.querySelectorAll('tr')).find(
            (row) => row.textContent?.includes('Roth IRA'),
        )
        expect(rothRow).toBeTruthy()
        fireEvent.click(rothRow!)

        // Step 4: Modal should appear
        await waitFor(() => {
            expect(screen.getByTestId('unsaved-changes-modal')).toBeInTheDocument()
        })

        // Step 5: Save & Continue button should be DISABLED because form is invalid
        const saveBtn = screen.getByTestId('unsaved-save-continue-btn')
        expect(saveBtn).toBeDisabled()
    })

    it('does not call save when clicking disabled Save & Continue on invalid form', async () => {
        renderWithProviders(<AccountsHome />)

        // Detail panel visible for acct-1
        const nameInput = await waitFor(() =>
            screen.getByTestId('account-name-input') as HTMLInputElement,
        )

        // Clear name → dirty + invalid
        fireEvent.change(nameInput, { target: { value: '' } })

        // Navigate to acct-2
        const table = screen.getByTestId('account-list')
        const rothRow = Array.from(table.querySelectorAll('tr')).find(
            (row) => row.textContent?.includes('Roth IRA'),
        )
        fireEvent.click(rothRow!)

        // Modal appears
        await waitFor(() => {
            expect(screen.getByTestId('unsaved-changes-modal')).toBeInTheDocument()
        })

        // Click the disabled Save & Continue
        const saveBtn = screen.getByTestId('unsaved-save-continue-btn')
        fireEvent.click(saveBtn)

        // Should NOT have navigated (selectAccount not called for acct-2)
        expect(mockSelectAccount).not.toHaveBeenCalledWith('acct-2')
    })
})
