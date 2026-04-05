import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// ── Mocks ───────────────────────────────────────────────────────────────────

// Mock window.api
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

// Mock fuse.js (via CommandPalette dependency chain)
vi.mock('fuse.js', () => ({
    default: class FuseMock {
        constructor() { /* noop */ }
        search() { return [] }
    },
}))

// Mock router
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

// Mock useAccounts hook
vi.mock('@/hooks/useAccounts', () => ({
    useAccounts: () => ({
        accounts: mockAccounts,
        portfolioTotal: 85000,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
    }),
    useCreateAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useUpdateAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useDeleteAccount: () => ({ mutate: vi.fn(), isPending: false }),
    useBalanceHistory: () => ({ data: [], isLoading: false }),
    useAddBalance: () => ({ mutate: vi.fn(), isPending: false }),
}))

// Mock AccountContext
const mockSelectAccount = vi.fn()
vi.mock('@/context/AccountContext', () => ({
    AccountProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAccountContext: () => ({
        activeAccountId: null,
        selectAccount: mockSelectAccount,
        mruAccountIds: ['acct-1', 'acct-2', 'acct-3'],
    }),
}))

// Import after mocks
import AccountsHome from '../AccountsHome'

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

describe('AccountsHome', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    // AC-1: MRU card strip showing top-3 recent accounts
    it('AC-1: renders MRU card strip with up to 3 account cards', () => {
        renderWithProviders(<AccountsHome />)
        // Verify MRU cards exist by data-testid
        expect(screen.getByTestId('mru-card-acct-1')).toBeInTheDocument()
        expect(screen.getByTestId('mru-card-acct-2')).toBeInTheDocument()
        expect(screen.getByTestId('mru-card-acct-3')).toBeInTheDocument()
        // Verify card content
        expect(within(screen.getByTestId('mru-card-acct-1')).getByText('Interactive Brokers')).toBeInTheDocument()
    })

    // AC-2: "Add New Account" card in MRU strip
    it('AC-2: renders an "Add New" card in the MRU area', () => {
        renderWithProviders(<AccountsHome />)
        expect(screen.getByTestId('add-account-btn')).toBeInTheDocument()
    })

    // AC-3: Portfolio total displayed
    it('AC-3: displays portfolio total from useAccounts', () => {
        renderWithProviders(<AccountsHome />)
        // $85,000 formatted
        expect(screen.getByText(/85,000/)).toBeInTheDocument()
    })

    // AC-4: All Accounts table with name, type, institution, balance columns
    it('AC-4: renders All Accounts table with account data', () => {
        renderWithProviders(<AccountsHome />)
        const table = screen.getByTestId('account-list')
        expect(table).toBeInTheDocument()
        // All 3 accounts should appear in the table
        expect(within(table).getByText('Interactive Brokers')).toBeInTheDocument()
        expect(within(table).getByText('Roth IRA')).toBeInTheDocument()
        expect(within(table).getByText('Savings Account')).toBeInTheDocument()
    })

    // AC-15: data-testid="accounts-page" for E2E Wave 2
    it('AC-15: has data-testid="accounts-page" for E2E Wave 2', () => {
        renderWithProviders(<AccountsHome />)
        expect(screen.getByTestId('accounts-page')).toBeInTheDocument()
    })

    // AC-15: data-testid="account-list" for E2E Wave 2
    it('AC-15: has data-testid="account-list" for E2E Wave 2', () => {
        renderWithProviders(<AccountsHome />)
        expect(screen.getByTestId('account-list')).toBeInTheDocument()
    })

    // AC-4: clicking an account row calls selectAccount
    it('AC-4: clicking an account row calls selectAccount', async () => {
        const user = userEvent.setup()
        renderWithProviders(<AccountsHome />)
        const table = screen.getByTestId('account-list')
        const ibRow = within(table).getByText('Interactive Brokers').closest('tr')!
        await user.click(ibRow)
        expect(mockSelectAccount).toHaveBeenCalledWith('acct-1')
    })

    // AC-1: MRU card click selects account
    it('AC-1: clicking an MRU card selects that account', async () => {
        const user = userEvent.setup()
        renderWithProviders(<AccountsHome />)
        // Click the MRU card by its data-testid
        await user.click(screen.getByTestId('mru-card-acct-1'))
        expect(mockSelectAccount).toHaveBeenCalledWith('acct-1')
    })

    // Structure: split layout has left pane
    it('renders a split layout with left pane and right pane', () => {
        renderWithProviders(<AccountsHome />)
        expect(screen.getByTestId('accounts-left-pane')).toBeInTheDocument()
        expect(screen.getByTestId('accounts-right-pane')).toBeInTheDocument()
    })

    // Start Review button present
    it('renders a "Start Review" button', () => {
        renderWithProviders(<AccountsHome />)
        expect(screen.getByRole('button', { name: /start review/i })).toBeInTheDocument()
    })
})
