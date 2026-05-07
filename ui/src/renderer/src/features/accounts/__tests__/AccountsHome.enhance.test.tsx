/**
 * MEU-200: Accounts Table Enhancements — Red-Phase Tests
 *
 * FIC: docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-200.md
 * These tests MUST fail in Red phase and pass after implementation (Green phase).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
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
        notes: 'Tax free growth',
        latest_balance: 25000,
        latest_balance_date: '2026-03-01',
    },
    {
        account_id: 'acct-3',
        name: 'Savings Account',
        account_type: 'bank',
        institution: 'Chase',
        currency: 'USD',
        is_tax_advantaged: false,
        notes: '',
        latest_balance: 10000,
        latest_balance_date: '2026-02-15',
    },
]

const mockDeleteMutate = vi.fn()
const mockRefetch = vi.fn()

vi.mock('@/hooks/useAccounts', () => ({
    useAccounts: () => ({
        accounts: mockAccounts,
        portfolioTotal: 85000,
        isLoading: false,
        error: null,
        isFetching: false,
        refetch: mockRefetch,
    }),
    useCreateAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useUpdateAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useDeleteAccount: () => ({ mutate: mockDeleteMutate, isPending: false }),
    useForceDeleteAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useBalanceHistory: () => ({ data: [], isLoading: false }),
    useAddBalance: () => ({ mutate: vi.fn(), isPending: false }),
    useArchiveAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useUnarchiveAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useArchivedAccounts: () => ({ accounts: [], isLoading: false, isFetching: false, error: null, refetch: vi.fn() }),
    fetchTradeCounts: vi.fn().mockResolvedValue({}),
}))

const mockSelectAccount = vi.fn()
vi.mock('@/context/AccountContext', () => ({
    AccountProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAccountContext: () => ({
        activeAccountId: null,
        selectAccount: mockSelectAccount,
        mruAccountIds: ['acct-1', 'acct-2', 'acct-3'],
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

// ── MEU-200 Red-Phase Tests ─────────────────────────────────────────────────

describe('MEU-200: Accounts Table Enhancements', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    // ── AC-1: Multi-select row checkboxes ────────────────────────────────

    describe('AC-1: Multi-select row checkboxes', () => {
        it('renders a SelectionCheckbox in each account row', async () => {
            renderWithProviders(<AccountsHome />)
            // Each row should have a checkbox with data-testid
            expect(screen.getByTestId('account-row-checkbox-acct-1')).toBeInTheDocument()
            expect(screen.getByTestId('account-row-checkbox-acct-2')).toBeInTheDocument()
            expect(screen.getByTestId('account-row-checkbox-acct-3')).toBeInTheDocument()
        })

        it('renders a header SelectionCheckbox that toggles all rows', async () => {
            const user = userEvent.setup()
            renderWithProviders(<AccountsHome />)
            const selectAll = screen.getByTestId('select-all-checkbox')
            expect(selectAll).toBeInTheDocument()

            // Click select-all
            await user.click(selectAll)

            // All row checkboxes should now be checked
            const cb1 = screen.getByTestId('account-row-checkbox-acct-1') as HTMLInputElement
            const cb2 = screen.getByTestId('account-row-checkbox-acct-2') as HTMLInputElement
            const cb3 = screen.getByTestId('account-row-checkbox-acct-3') as HTMLInputElement
            expect(cb1.checked).toBe(true)
            expect(cb2.checked).toBe(true)
            expect(cb3.checked).toBe(true)
        })
    })

    // ── AC-2: Bulk action bar ────────────────────────────────────────────

    describe('AC-2: Bulk action bar', () => {
        it('shows BulkActionBar when ≥1 row is selected', async () => {
            const user = userEvent.setup()
            renderWithProviders(<AccountsHome />)

            // Select first row
            await user.click(screen.getByTestId('account-row-checkbox-acct-1'))

            // Bulk action bar should appear
            const bar = screen.getByTestId('bulk-action-bar')
            expect(bar).toBeInTheDocument()
            expect(within(bar).getByText(/1 selected/i)).toBeInTheDocument()
        })

        it('shows bulk delete button that opens confirm modal', async () => {
            const user = userEvent.setup()
            renderWithProviders(<AccountsHome />)

            // Select two rows
            await user.click(screen.getByTestId('account-row-checkbox-acct-1'))
            await user.click(screen.getByTestId('account-row-checkbox-acct-2'))

            // Click bulk delete
            const deleteBtn = screen.getByTestId('bulk-delete-btn')
            expect(deleteBtn).toBeInTheDocument()
            await user.click(deleteBtn)

            // Confirm modal should appear with count
            await waitFor(() => {
                const modal = screen.getByTestId('confirm-delete-modal')
                expect(modal).toBeInTheDocument()
                expect(within(modal).getByRole('heading', { name: /delete 2 accounts/i })).toBeInTheDocument()
            })
        })
    })

    // ── AC-3: Text search filter ─────────────────────────────────────────

    describe('AC-3: Text search filter', () => {
        it('renders a search input for filtering', async () => {
            renderWithProviders(<AccountsHome />)
            expect(screen.getByTestId('table-search-input')).toBeInTheDocument()
        })

        it('filters accounts by name when typing', async () => {
            const user = userEvent.setup()
            renderWithProviders(<AccountsHome />)

            const searchInput = screen.getByTestId('table-search-input')
            await user.type(searchInput, 'Roth')

            await waitFor(() => {
                const table = screen.getByTestId('account-list')
                // Only Roth IRA should be visible
                expect(within(table).getByText('Roth IRA')).toBeInTheDocument()
                expect(within(table).queryByText('Interactive Brokers')).not.toBeInTheDocument()
                expect(within(table).queryByText('Savings Account')).not.toBeInTheDocument()
            })
        })

        it('filters accounts by institution when typing', async () => {
            const user = userEvent.setup()
            renderWithProviders(<AccountsHome />)

            const searchInput = screen.getByTestId('table-search-input')
            await user.type(searchInput, 'Chase')

            await waitFor(() => {
                const table = screen.getByTestId('account-list')
                expect(within(table).getByText('Savings Account')).toBeInTheDocument()
                expect(within(table).queryByText('Interactive Brokers')).not.toBeInTheDocument()
            })
        })
    })

    // ── AC-4: Column sorting with sort indicators ────────────────────────

    describe('AC-4: SortableColumnHeader indicators', () => {
        it('renders sort indicators on column headers', async () => {
            renderWithProviders(<AccountsHome />)
            // Look for the sort indicator characters (▲ or ▼) in headers
            const table = screen.getByTestId('account-list')
            const headers = within(table).getAllByRole('columnheader')
            // At least one header should show a sort indicator
            const hasIndicator = headers.some(
                (h) => h.textContent?.includes('↑') || h.textContent?.includes('↓')
            )
            expect(hasIndicator).toBe(true)
        })
    })

    // ── AC-6: data-testid attributes ─────────────────────────────────────

    describe('AC-6: data-testid attributes', () => {
        it('has select-all-checkbox testid', async () => {
            renderWithProviders(<AccountsHome />)
            expect(screen.getByTestId('select-all-checkbox')).toBeInTheDocument()
        })

        it('has bulk-action-bar testid when selection exists', async () => {
            const user = userEvent.setup()
            renderWithProviders(<AccountsHome />)
            await user.click(screen.getByTestId('account-row-checkbox-acct-1'))
            expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
        })

        it('has table-search-input testid', async () => {
            renderWithProviders(<AccountsHome />)
            expect(screen.getByTestId('table-search-input')).toBeInTheDocument()
        })
    })
})
