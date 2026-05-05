/**
 * MEU-201: Trade Plans Table Enhancements — Red-Phase Tests
 *
 * FIC: docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-201.md
 * These tests MUST fail in Red phase and pass after implementation (Green phase).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ── Mocks ───────────────────────────────────────────────────────────────────

// Mock api module
const mockApiFetch = vi.fn()
vi.mock('@/lib/api', () => ({
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

// Mock status bar
const mockSetStatus = vi.fn()
vi.mock('@/hooks/useStatusBar', () => ({
    useStatusBar: () => ({ setStatus: mockSetStatus }),
}))

import TradePlanPage, { type TradePlan } from '../TradePlanPage'

// ── Test Data ───────────────────────────────────────────────────────────────

const MOCK_PLANS: TradePlan[] = [
    {
        id: 1,
        ticker: 'AAPL',
        direction: 'BOT',
        conviction: 'high',
        strategy_name: 'Gap Fill',
        strategy_description: 'Morning gap fill play',
        entry_price: 190,
        stop_loss: 188,
        target_price: 196,
        entry_conditions: 'Gap down > 2%',
        exit_conditions: 'Gap fill complete',
        timeframe: 'intraday',
        risk_reward_ratio: 3.0,
        status: 'active',
        linked_trade_id: null,
        account_id: 'DU123456',
        created_at: '2026-03-20T10:00:00Z',
        updated_at: '2026-03-20T10:00:00Z',
    },
    {
        id: 2,
        ticker: 'NVDA',
        direction: 'SLD',
        conviction: 'low',
        strategy_name: 'Breakdown',
        strategy_description: '',
        entry_price: 800,
        stop_loss: 810,
        target_price: 770,
        entry_conditions: '',
        exit_conditions: '',
        timeframe: 'swing',
        risk_reward_ratio: 3.0,
        status: 'draft',
        linked_trade_id: null,
        account_id: null,
        created_at: '2026-03-19T09:00:00Z',
        updated_at: '2026-03-19T09:00:00Z',
    },
    {
        id: 3,
        ticker: 'TSLA',
        direction: 'BOT',
        conviction: 'medium',
        strategy_name: 'Momentum',
        strategy_description: 'Breakout entry',
        entry_price: 250,
        stop_loss: 245,
        target_price: 265,
        entry_conditions: 'Above 20SMA',
        exit_conditions: 'Below 20SMA',
        timeframe: 'swing',
        risk_reward_ratio: 3.0,
        status: 'active',
        linked_trade_id: null,
        account_id: null,
        created_at: '2026-03-18T09:00:00Z',
        updated_at: '2026-03-18T09:00:00Z',
    },
]

// ── Helpers ──────────────────────────────────────────────────────────────────

function setupApiMocks() {
    mockApiFetch.mockImplementation((url: string) => {
        if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
        if (url.includes('/api/v1/accounts')) return Promise.resolve([])
        if (url.includes('/api/v1/trades')) return Promise.resolve({ items: [] })
        return Promise.resolve([])
    })
}

function renderWithProviders(ui: React.ReactElement) {
    const client = new QueryClient({
        defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    return render(
        <QueryClientProvider client={client}>
            {ui}
        </QueryClientProvider>,
    )
}

// ── MEU-201 Red-Phase Tests ─────────────────────────────────────────────────

describe('MEU-201: Trade Plans Table Enhancements', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        setupApiMocks()
    })

    // ── AC-1: Multi-select row checkboxes ────────────────────────────────

    describe('AC-1: Multi-select row checkboxes', () => {
        it('renders a SelectionCheckbox in each plan card', async () => {
            renderWithProviders(<TradePlanPage />)

            // Wait for plans to load
            await waitFor(() => {
                expect(screen.getByTestId('plan-row-checkbox-1')).toBeInTheDocument()
            })
            expect(screen.getByTestId('plan-row-checkbox-2')).toBeInTheDocument()
            expect(screen.getByTestId('plan-row-checkbox-3')).toBeInTheDocument()
        })

        it('renders a header SelectionCheckbox that toggles all plans', async () => {
            const user = userEvent.setup()
            renderWithProviders(<TradePlanPage />)

            await waitFor(() => {
                expect(screen.getByTestId('select-all-plan-checkbox')).toBeInTheDocument()
            })

            const selectAll = screen.getByTestId('select-all-plan-checkbox')
            await user.click(selectAll)

            // All plan checkboxes should now be checked
            const cb1 = screen.getByTestId('plan-row-checkbox-1') as HTMLInputElement
            const cb2 = screen.getByTestId('plan-row-checkbox-2') as HTMLInputElement
            const cb3 = screen.getByTestId('plan-row-checkbox-3') as HTMLInputElement
            expect(cb1.checked).toBe(true)
            expect(cb2.checked).toBe(true)
            expect(cb3.checked).toBe(true)
        })
    })

    // ── AC-2: Bulk action bar ────────────────────────────────────────────

    describe('AC-2: Bulk action bar', () => {
        it('shows BulkActionBar when ≥1 plan is selected', async () => {
            const user = userEvent.setup()
            renderWithProviders(<TradePlanPage />)

            await waitFor(() => {
                expect(screen.getByTestId('plan-row-checkbox-1')).toBeInTheDocument()
            })

            // Select one plan
            await user.click(screen.getByTestId('plan-row-checkbox-1'))

            await waitFor(() => {
                expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
            })
        })

        it('shows bulk delete button that opens confirm modal', async () => {
            const user = userEvent.setup()
            renderWithProviders(<TradePlanPage />)

            await waitFor(() => {
                expect(screen.getByTestId('plan-row-checkbox-1')).toBeInTheDocument()
            })

            // Select two plans
            await user.click(screen.getByTestId('plan-row-checkbox-1'))
            await user.click(screen.getByTestId('plan-row-checkbox-2'))

            await waitFor(() => {
                expect(screen.getByTestId('bulk-delete-btn')).toBeInTheDocument()
            })

            // Click bulk delete button
            await user.click(screen.getByTestId('bulk-delete-btn'))

            // Confirm modal should appear with count
            await waitFor(() => {
                const modal = screen.getByTestId('confirm-delete-modal')
                expect(modal).toBeInTheDocument()
                expect(within(modal).getByRole('heading', { name: /delete 2 trade plans/i })).toBeInTheDocument()
            })
        })
    })

    // ── AC-3: Text search filter ─────────────────────────────────────────

    describe('AC-3: Text search filter', () => {
        it('renders a search input for filtering', async () => {
            renderWithProviders(<TradePlanPage />)

            await waitFor(() => {
                expect(screen.getByTestId('table-search-input')).toBeInTheDocument()
            })
        })

        it('filters plans by ticker when typing', async () => {
            const user = userEvent.setup()
            renderWithProviders(<TradePlanPage />)

            await waitFor(() => {
                expect(screen.getByTestId('plan-card-1')).toBeInTheDocument()
            })

            const search = screen.getByTestId('table-search-input')
            await user.type(search, 'AAPL')

            await waitFor(() => {
                expect(screen.getByTestId('plan-card-1')).toBeInTheDocument()
                expect(screen.queryByTestId('plan-card-2')).not.toBeInTheDocument()
                expect(screen.queryByTestId('plan-card-3')).not.toBeInTheDocument()
            })
        })

        it('filters plans by strategy name when typing', async () => {
            const user = userEvent.setup()
            renderWithProviders(<TradePlanPage />)

            await waitFor(() => {
                expect(screen.getByTestId('plan-card-1')).toBeInTheDocument()
            })

            const search = screen.getByTestId('table-search-input')
            await user.type(search, 'Breakdown')

            await waitFor(() => {
                expect(screen.queryByTestId('plan-card-1')).not.toBeInTheDocument()
                expect(screen.getByTestId('plan-card-2')).toBeInTheDocument()
                expect(screen.queryByTestId('plan-card-3')).not.toBeInTheDocument()
            })
        })
    })

    // ── AC-5: data-testid attributes ─────────────────────────────────────

    describe('AC-5: data-testid attributes', () => {
        it('has select-all-plan-checkbox testid', async () => {
            renderWithProviders(<TradePlanPage />)
            await waitFor(() => {
                expect(screen.getByTestId('select-all-plan-checkbox')).toBeInTheDocument()
            })
        })

        it('has bulk-action-bar testid when selection exists', async () => {
            const user = userEvent.setup()
            renderWithProviders(<TradePlanPage />)

            await waitFor(() => {
                expect(screen.getByTestId('plan-row-checkbox-1')).toBeInTheDocument()
            })

            await user.click(screen.getByTestId('plan-row-checkbox-1'))

            await waitFor(() => {
                expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
            })
        })

        it('has table-search-input testid', async () => {
            renderWithProviders(<TradePlanPage />)
            await waitFor(() => {
                expect(screen.getByTestId('table-search-input')).toBeInTheDocument()
            })
        })
    })
})
