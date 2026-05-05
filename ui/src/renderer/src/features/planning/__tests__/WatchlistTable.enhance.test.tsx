/**
 * MEU-202: Watchlist Tickers Table Enhancements — Red-Phase Tests
 *
 * FIC: docs/execution/plans/2026-05-03-gui-table-list-enhancements/fic-meu-202.md
 * These tests MUST fail in Red phase and pass after implementation (Green phase).
 *
 * Tests WatchlistTable directly since it's the component receiving enhancements.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import React from 'react'

import WatchlistTable, { type WatchlistItem, type MarketQuote } from '../WatchlistTable'

// ── Test Data ───────────────────────────────────────────────────────────────

const MOCK_ITEMS: WatchlistItem[] = [
    { id: 1, watchlist_id: 1, ticker: 'AAPL', added_at: '2026-03-01', notes: 'Tech leader' },
    { id: 2, watchlist_id: 1, ticker: 'NVDA', added_at: '2026-03-02', notes: '' },
    { id: 3, watchlist_id: 1, ticker: 'TSLA', added_at: '2026-03-03', notes: 'EV play momentum' },
]

const MOCK_QUOTES: Record<string, MarketQuote | null> = {
    AAPL: { last_price: 195.50, change: 2.30, change_pct: 1.19, volume: 45000000, symbol: 'AAPL' },
    NVDA: { last_price: 880.00, change: -5.20, change_pct: -0.59, volume: 32000000, symbol: 'NVDA' },
    TSLA: { last_price: 260.00, change: 8.40, change_pct: 3.34, volume: 55000000, symbol: 'TSLA' },
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const mockRemoveTicker = vi.fn()

function renderTable(props: Partial<Parameters<typeof WatchlistTable>[0]> = {}) {
    return render(
        <WatchlistTable
            items={MOCK_ITEMS}
            quotes={MOCK_QUOTES}
            colorblind={false}
            onRemoveTicker={mockRemoveTicker}
            {...props}
        />,
    )
}

// ── MEU-202 Red-Phase Tests ─────────────────────────────────────────────────

describe('MEU-202: Watchlist Tickers Table Enhancements', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    // ── AC-1: Multi-select row checkboxes ────────────────────────────────

    describe('AC-1: Multi-select row checkboxes', () => {
        it('renders a SelectionCheckbox in each ticker row', () => {
            renderTable()
            expect(screen.getByTestId('ticker-row-checkbox-AAPL')).toBeInTheDocument()
            expect(screen.getByTestId('ticker-row-checkbox-NVDA')).toBeInTheDocument()
            expect(screen.getByTestId('ticker-row-checkbox-TSLA')).toBeInTheDocument()
        })

        it('renders a header SelectionCheckbox that toggles all rows', async () => {
            const user = userEvent.setup()
            renderTable()
            const selectAll = screen.getByTestId('select-all-ticker-checkbox')
            expect(selectAll).toBeInTheDocument()

            await user.click(selectAll)

            const cb1 = screen.getByTestId('ticker-row-checkbox-AAPL') as HTMLInputElement
            const cb2 = screen.getByTestId('ticker-row-checkbox-NVDA') as HTMLInputElement
            const cb3 = screen.getByTestId('ticker-row-checkbox-TSLA') as HTMLInputElement
            expect(cb1.checked).toBe(true)
            expect(cb2.checked).toBe(true)
            expect(cb3.checked).toBe(true)
        })
    })

    // ── AC-2: Bulk action bar ────────────────────────────────────────────

    describe('AC-2: Bulk action bar', () => {
        it('shows BulkActionBar when ≥1 ticker is selected', async () => {
            const user = userEvent.setup()
            renderTable()

            await user.click(screen.getByTestId('ticker-row-checkbox-AAPL'))

            expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
        })

        it('shows bulk remove button that opens confirm modal', async () => {
            const user = userEvent.setup()
            renderTable()

            // Select two tickers
            await user.click(screen.getByTestId('ticker-row-checkbox-AAPL'))
            await user.click(screen.getByTestId('ticker-row-checkbox-NVDA'))

            const deleteBtn = screen.getByTestId('bulk-delete-btn')
            expect(deleteBtn).toBeInTheDocument()
            await user.click(deleteBtn)

            // Confirm modal should appear
            await waitFor(() => {
                const modal = screen.getByTestId('confirm-delete-modal')
                expect(modal).toBeInTheDocument()
                expect(within(modal).getByRole('heading', { name: /delete 2 tickers/i })).toBeInTheDocument()
            })
        })
    })

    // ── AC-3: Text search filter ─────────────────────────────────────────

    describe('AC-3: Text search filter', () => {
        it('renders a search input for filtering', () => {
            renderTable()
            expect(screen.getByTestId('ticker-search-input')).toBeInTheDocument()
        })

        it('filters tickers by symbol when typing', async () => {
            const user = userEvent.setup()
            renderTable()

            const search = screen.getByTestId('ticker-search-input')
            await user.type(search, 'AAPL')

            await waitFor(() => {
                expect(screen.getByTestId('watchlist-row-AAPL')).toBeInTheDocument()
                expect(screen.queryByTestId('watchlist-row-NVDA')).not.toBeInTheDocument()
                expect(screen.queryByTestId('watchlist-row-TSLA')).not.toBeInTheDocument()
            })
        })

        it('filters tickers by notes when typing', async () => {
            const user = userEvent.setup()
            renderTable()

            const search = screen.getByTestId('ticker-search-input')
            await user.type(search, 'momentum')

            await waitFor(() => {
                expect(screen.queryByTestId('watchlist-row-AAPL')).not.toBeInTheDocument()
                expect(screen.queryByTestId('watchlist-row-NVDA')).not.toBeInTheDocument()
                expect(screen.getByTestId('watchlist-row-TSLA')).toBeInTheDocument()
            })
        })
    })

    // ── AC-5: data-testid attributes ─────────────────────────────────────

    describe('AC-5: data-testid attributes', () => {
        it('has select-all-ticker-checkbox testid', () => {
            renderTable()
            expect(screen.getByTestId('select-all-ticker-checkbox')).toBeInTheDocument()
        })

        it('has ticker-search-input testid', () => {
            renderTable()
            expect(screen.getByTestId('ticker-search-input')).toBeInTheDocument()
        })

        it('has bulk-action-bar testid when selection exists', async () => {
            const user = userEvent.setup()
            renderTable()
            await user.click(screen.getByTestId('ticker-row-checkbox-AAPL'))
            expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
        })
    })
})
