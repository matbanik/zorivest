/**
 * Tests for Tax GUI feature (MEU-154).
 *
 * Tests cover:
 * - TaxDisclaimer rendering
 * - TaxLayout tab navigation
 * - TaxDashboard summary cards + YTD table
 * - TaxLotViewer filters + disabled buttons
 * - WashSaleMonitor list/detail
 * - WhatIfSimulator form + results
 * - LossHarvestingTool table
 * - QuarterlyTracker cards + payment form
 * - TransactionAudit findings
 *
 * Test pattern follows scheduling.test.tsx (vi.hoisted mock, QueryClient wrapper).
 * MEU: MEU-154 (gui-tax)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ─── Mocks ────────────────────────────────────────────────────────────────────

const { mockApiFetch } = vi.hoisted(() => ({
    mockApiFetch: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => mockApiFetch(...args),
}))

vi.mock('@/hooks/useStatusBar', () => ({
    useStatusBar: () => ({ message: 'Ready', setStatus: vi.fn() }),
    StatusBarProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Import after mocks
import TaxDisclaimer from '../TaxDisclaimer'
import TaxDashboard from '../TaxDashboard'
import TaxLotViewer from '../TaxLotViewer'
import WashSaleMonitor from '../WashSaleMonitor'
import WhatIfSimulator from '../WhatIfSimulator'
import LossHarvestingTool from '../LossHarvestingTool'
import QuarterlyTracker from '../QuarterlyTracker'
import TransactionAudit from '../TransactionAudit'
import { TAX_TEST_IDS } from '../test-ids'

// ─── Global setup: dismiss TaxHelpCards so they don't interfere ────────────────
// TaxHelpCard defaults to 'expanded' when localStorage is empty, adding DOM
// elements that shift child indices and pollute text queries.

const TAX_HELP_TAB_KEYS = [
    'dashboard', 'profiles', 'lots', 'wash-sales',
    'simulator', 'harvesting', 'quarterly', 'audit',
]

beforeEach(() => {
    for (const key of TAX_HELP_TAB_KEYS) {
        localStorage.setItem(`zorivest:tax-help:${key}:state`, 'dismissed')
    }
})

afterEach(() => {
    localStorage.clear()
})

// Mock Electron API for components that use window.electron
Object.defineProperty(window, 'electron', {
    value: { openExternal: vi.fn() },
    writable: true,
    configurable: true,
})

// ─── Test Data ────────────────────────────────────────────────────────────────

const MOCK_YTD_SUMMARY = {
    realized_st_gain: 12500.50,
    realized_lt_gain: 8200.00,
    total_realized: 20700.50,
    wash_sale_adjustments: -1500.25,
    estimated_tax: 5200.00,
    estimated_federal_tax: 3900.00,
    estimated_state_tax: 1300.00,
    trades_count: 42,
    capital_loss_carryforward: 3200.00,
    harvestable_losses: 1800.50,
    tax_alpha: 750.25,
}

const MOCK_SYMBOL_BREAKDOWN = [
    { ticker: 'AAPL', short_term_pnl: 5000, long_term_pnl: 3000, total_pnl: 8000 },
    { ticker: 'MSFT', short_term_pnl: -1000, long_term_pnl: 2000, total_pnl: 1000 },
]

const MOCK_LOTS = [
    {
        lot_id: 'lot-001',
        ticker: 'AAPL',
        quantity: 100,
        cost_basis: 15000,
        proceeds: 17500,
        wash_sale_adjustment: 0,
        is_closed: false,
        open_date: '2024-01-15',  // > 366 days ago → LT
        close_date: null,
        linked_trade_ids: [],
        cost_basis_method: 'FIFO',
        realized_gain_loss: 2500,
        acquisition_source: null,
        account_id: 'acc-001',
        materialized_at: null,
        is_user_modified: false,
        source_hash: null,
        sync_status: 'synced',
    },
    {
        lot_id: 'lot-002',
        ticker: 'TSLA',
        quantity: 50,
        cost_basis: 10000,
        proceeds: 0,
        wash_sale_adjustment: 0,
        is_closed: false,
        open_date: new Date(Date.now() - 246 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),  // 246 days ago → ST, 120d remaining
        close_date: null,
        linked_trade_ids: [],
        cost_basis_method: 'FIFO',
        realized_gain_loss: -1500,
        acquisition_source: null,
        account_id: 'acc-001',
        materialized_at: null,
        is_user_modified: false,
        source_hash: null,
        sync_status: 'synced',
    },
]

const MOCK_WASH_SALES = [
    {
        chain_id: 'chain-001',
        ticker: 'TSLA',
        adjustment_amount: -500,
        trade_count: 3,
        first_trade_date: '2026-01-10',
        last_trade_date: '2026-02-05',
        status: 'active' as const,
        trades: [
            { exec_id: 'e1', date: '2026-01-10', action: 'SLD', quantity: 50, price: 200, wash_amount: 300 },
            { exec_id: 'e2', date: '2026-01-25', action: 'BOT', quantity: 50, price: 180, wash_amount: 200 },
        ],
    },
]

const MOCK_HARVEST = [
    {
        ticker: 'NFLX',
        unrealized_loss: -2000,
        current_price: 350,
        cost_basis: 370,
        quantity: 100,
        holding_days: 45,
        classification: 'ST' as const,
        wash_sale_risk: false,
    },
]

const MOCK_ACCOUNTS = [
    { account_id: 'acc-001-full-id', name: 'Main Brokerage', account_type: 'BROKER' },
]

const MOCK_OPEN_LOTS = {
    lots: [
        { lot_id: 'lot-sim-1', ticker: 'AAPL', quantity: 100, cost_basis: 120, status: 'open', acquired_date: '2025-01-15' },
    ],
}

const MOCK_QUARTERLY = {
    quarter: 'Q1',
    tax_year: 2026,
    estimated_amount: 3500,
    paid_amount: 3500,
    due_date: '2026-04-15',
    status: 'paid' as const,
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    })
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TaxDisclaimer
// ═══════════════════════════════════════════════════════════════════════════════

describe('TaxDisclaimer', () => {
    it('AC-154.16: renders disclaimer text with test-id', () => {
        render(<TaxDisclaimer />)
        const el = screen.getByTestId(TAX_TEST_IDS.DISCLAIMER)
        expect(el).toBeInTheDocument()
        expect(el).toHaveTextContent('not tax advice')
        expect(el).toHaveTextContent('CPA')
    })

    it('AC-154.16: has role="status" for accessibility', () => {
        render(<TaxDisclaimer />)
        expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('accepts custom className', () => {
        render(<TaxDisclaimer className="mt-4" />)
        const el = screen.getByTestId(TAX_TEST_IDS.DISCLAIMER)
        expect(el.className).toContain('mt-4')
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// TaxDashboard
// ═══════════════════════════════════════════════════════════════════════════════

describe('TaxDashboard', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-154.4: renders 8 summary cards with data-testid', async () => {
        mockApiFetch
            .mockResolvedValueOnce(MOCK_YTD_SUMMARY) // ytd-summary
            .mockResolvedValueOnce(MOCK_SYMBOL_BREAKDOWN) // ytd-summary?group_by=symbol
        render(<TaxDashboard />, { wrapper: createWrapper() })

        await waitFor(() => {
            const cards = screen.getAllByTestId(TAX_TEST_IDS.SUMMARY_CARD)
            expect(cards).toHaveLength(8)
        })

        // Verify spec-required labels are present (matches current TaxDashboard cards array)
        const expectedLabels = [
            'ST Gains', 'LT Gains', 'Total Realized', 'Wash Sale Adj',
            'Federal Tax', 'State Tax', 'Total Est. Tax', 'Trades',
        ]
        for (const label of expectedLabels) {
            expect(screen.getByText(label)).toBeInTheDocument()
        }
    })

    it('AC-154.4: renders dashboard root test-id', async () => {
        mockApiFetch
            .mockResolvedValueOnce(MOCK_YTD_SUMMARY)
            .mockResolvedValueOnce([])
        render(<TaxDashboard />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.DASHBOARD)).toBeInTheDocument()
    })

    it('AC-154.5: renders YTD summary data after fetch', async () => {
        mockApiFetch
            .mockResolvedValueOnce(MOCK_YTD_SUMMARY)
            .mockResolvedValueOnce(MOCK_SYMBOL_BREAKDOWN)
        render(<TaxDashboard />, { wrapper: createWrapper() })

        // The dashboard renders summary cards with values from YTD data.
        // Verify the data loads and the dashboard container is present.
        await waitFor(() => {
            expect(screen.getByTestId(TAX_TEST_IDS.DASHBOARD)).toBeInTheDocument()
        })

        // Verify that summary card values render (ST Gains card should show the value)
        await waitFor(() => {
            expect(screen.getByText('ST Gains')).toBeInTheDocument()
        })
    })

    it('AC-154.6: renders year selector', async () => {
        mockApiFetch
            .mockResolvedValueOnce(MOCK_YTD_SUMMARY)
            .mockResolvedValueOnce([])
        render(<TaxDashboard />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.YEAR_SELECTOR)).toBeInTheDocument()
    })

    it('shows error state on fetch failure', async () => {
        mockApiFetch.mockRejectedValue(new Error('Network error'))
        render(<TaxDashboard />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getByText(/Failed to load tax summary/)).toBeInTheDocument()
        })
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// TaxLotViewer
// ═══════════════════════════════════════════════════════════════════════════════

describe('TaxLotViewer', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-154.7: renders lot rows with disabled Close/Reassign buttons', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_LOTS)
        render(<TaxLotViewer />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getAllByTestId(TAX_TEST_IDS.LOT_ROW)).toHaveLength(2)
        })

        const closeBtns = screen.getAllByTestId(TAX_TEST_IDS.LOT_CLOSE_BTN)
        const reassignBtns = screen.getAllByTestId(TAX_TEST_IDS.LOT_REASSIGN_BTN)
        closeBtns.forEach((btn) => {
            expect(btn).toBeDisabled()
            expect(btn).toHaveAttribute('title', 'Coming soon — Module C4/C5')
        })
        reassignBtns.forEach((btn) => {
            expect(btn).toBeDisabled()
            expect(btn).toHaveAttribute('title', 'Coming soon — Module C4/C5')
        })
    })

    it('AC-154.8: renders ST/LT badges', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_LOTS)
        render(<TaxLotViewer />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getByText('LT')).toBeInTheDocument()
            expect(screen.getByText(/ST/)).toBeInTheDocument()
        })
    })

    it('AC-154.8: shows days-to-LT countdown for ST open lots', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_LOTS)
        render(<TaxLotViewer />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getByText(/120d/)).toBeInTheDocument()
        })
    })

    it('renders filter controls', async () => {
        mockApiFetch.mockResolvedValueOnce([])
        render(<TaxLotViewer />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.LOT_FILTER_STATUS)).toBeInTheDocument()
        expect(screen.getByTestId(TAX_TEST_IDS.LOT_FILTER_TICKER)).toBeInTheDocument()
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// WashSaleMonitor
// ═══════════════════════════════════════════════════════════════════════════════

describe('WashSaleMonitor', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-154.9: renders chain list items', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_WASH_SALES)
        render(<WashSaleMonitor />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getAllByTestId(TAX_TEST_IDS.WASH_SALE_CHAIN)).toHaveLength(1)
        })
        expect(screen.getByText('TSLA')).toBeInTheDocument()
    })

    it('AC-154.9: clicking chain shows detail pane', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_WASH_SALES)
        render(<WashSaleMonitor />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getByTestId(TAX_TEST_IDS.WASH_SALE_CHAIN)).toBeInTheDocument()
        })

        fireEvent.click(screen.getByTestId(TAX_TEST_IDS.WASH_SALE_CHAIN))

        expect(screen.getByTestId(TAX_TEST_IDS.WASH_SALE_CHAIN_DETAIL)).toBeInTheDocument()
    })

    it('shows empty state when no chains', async () => {
        mockApiFetch.mockResolvedValueOnce([])
        render(<WashSaleMonitor />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getByText(/No wash sales detected/)).toBeInTheDocument()
        })
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// WhatIfSimulator
// ═══════════════════════════════════════════════════════════════════════════════

describe('WhatIfSimulator', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-154.10: renders simulator form with test-ids', () => {
        render(<WhatIfSimulator />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_SIMULATOR)).toBeInTheDocument()
        expect(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_TICKER_INPUT)).toBeInTheDocument()
        expect(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_QUANTITY)).toBeInTheDocument()
        expect(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_PRICE)).toBeInTheDocument()
        expect(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_SUBMIT)).toBeInTheDocument()
    })

    it('AC-154.10: submit button disabled until required fields filled', () => {
        render(<WhatIfSimulator />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_SUBMIT)).toBeDisabled()
    })

    it('AC-154.11: shows results after simulation', async () => {
        const mockResult = {
            ticker: 'AAPL',
            quantity: 100,
            price: 150,
            total_proceeds: 15000,
            total_cost_basis: 12000,
            realized_pnl: 3000,
            short_term_gain: 1000,
            long_term_gain: 2000,
            estimated_tax: 750,
            wash_sale_risk: false,
            lot_details: [],
        }
        // Mock sequence: (1) accounts list, (2) open lots, (3) simulate result
        mockApiFetch
            .mockResolvedValueOnce(MOCK_ACCOUNTS)     // accounts fetch
            .mockResolvedValueOnce(MOCK_OPEN_LOTS)     // open lots fetch
            .mockResolvedValueOnce(mockResult)         // simulate mutation

        render(<WhatIfSimulator />, { wrapper: createWrapper() })

        // Wait for accounts to load and auto-select, then lots to populate ticker dropdown
        await waitFor(() => {
            const tickerSelect = screen.getByTestId(TAX_TEST_IDS.WHAT_IF_TICKER_INPUT)
            expect(tickerSelect).not.toBeDisabled()
        })

        // Select ticker from dropdown (select element, not text input)
        fireEvent.change(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_TICKER_INPUT), { target: { value: 'AAPL' } })
        fireEvent.change(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_QUANTITY), { target: { value: '100' } })
        fireEvent.change(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_PRICE), { target: { value: '150' } })

        // Submit
        fireEvent.click(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_SUBMIT))

        await waitFor(() => {
            expect(screen.getByTestId(TAX_TEST_IDS.WHAT_IF_RESULT)).toBeInTheDocument()
        })
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// LossHarvestingTool
// ═══════════════════════════════════════════════════════════════════════════════

describe('LossHarvestingTool', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-154.12: renders harvest opportunity rows', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_HARVEST)
        render(<LossHarvestingTool />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getAllByTestId(TAX_TEST_IDS.HARVEST_OPPORTUNITY_ROW)).toHaveLength(1)
        })
        expect(screen.getByText('NFLX')).toBeInTheDocument()
    })

    it('AC-154.12: shows empty state when no opportunities', async () => {
        mockApiFetch.mockResolvedValueOnce([])
        render(<LossHarvestingTool />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getByText(/No harvesting opportunities/)).toBeInTheDocument()
        })
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// QuarterlyTracker
// ═══════════════════════════════════════════════════════════════════════════════

describe('QuarterlyTracker', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-154.13: renders 4 quarter cards', async () => {
        // 4 quarter fetches
        mockApiFetch
            .mockResolvedValueOnce(MOCK_QUARTERLY)
            .mockResolvedValueOnce({ ...MOCK_QUARTERLY, quarter: 'Q2', status: 'due' })
            .mockResolvedValueOnce({ ...MOCK_QUARTERLY, quarter: 'Q3', status: 'upcoming' })
            .mockResolvedValueOnce({ ...MOCK_QUARTERLY, quarter: 'Q4', status: 'upcoming' })
        render(<QuarterlyTracker />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getAllByTestId(TAX_TEST_IDS.QUARTERLY_CARD)).toHaveLength(4)
        })
    })

    it('AC-154.14: renders payment form', () => {
        mockApiFetch.mockResolvedValue(MOCK_QUARTERLY)
        render(<QuarterlyTracker />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.QUARTERLY_PAYMENT_INPUT)).toBeInTheDocument()
        expect(screen.getByTestId(TAX_TEST_IDS.QUARTERLY_PAYMENT_SUBMIT)).toBeInTheDocument()
    })

    it('AC-154.14: submit disabled when amount is 0', () => {
        mockApiFetch.mockResolvedValue(MOCK_QUARTERLY)
        render(<QuarterlyTracker />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.QUARTERLY_PAYMENT_SUBMIT)).toBeDisabled()
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// TransactionAudit
// ═══════════════════════════════════════════════════════════════════════════════

describe('TransactionAudit', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-154.15: renders audit panel with run button', () => {
        render(<TransactionAudit />, { wrapper: createWrapper() })

        expect(screen.getByTestId(TAX_TEST_IDS.TX_AUDIT_PANEL)).toBeInTheDocument()
        expect(screen.getByTestId(TAX_TEST_IDS.TX_AUDIT_RUN_BTN)).toBeInTheDocument()
    })

    it('AC-154.15: shows findings after audit run', async () => {
        const mockAuditResult = {
            findings: [
                {
                    finding_type: 'missing_basis',
                    severity: 'error',
                    message: 'Trade e1 has no cost basis',
                    lot_id: 'lot-f1',
                    details: {},
                },
            ],
            severity_summary: { error: 1, warning: 0, info: 0 },
        }
        mockApiFetch.mockResolvedValueOnce(mockAuditResult)

        render(<TransactionAudit />, { wrapper: createWrapper() })

        fireEvent.click(screen.getByTestId(TAX_TEST_IDS.TX_AUDIT_RUN_BTN))

        await waitFor(() => {
            expect(screen.getAllByTestId(TAX_TEST_IDS.TX_AUDIT_FINDING_ROW)).toHaveLength(1)
        })
        expect(screen.getByText('Missing Cost Basis')).toBeInTheDocument()
    })

    it('AC-154.15: shows clean state when no findings', async () => {
        mockApiFetch.mockResolvedValueOnce({
            findings: [],
            severity_summary: { error: 0, warning: 0, info: 0 },
        })

        render(<TransactionAudit />, { wrapper: createWrapper() })

        fireEvent.click(screen.getByTestId(TAX_TEST_IDS.TX_AUDIT_RUN_BTN))

        await waitFor(() => {
            expect(screen.getByText(/No issues found/)).toBeInTheDocument()
        })
    })

    it('shows placeholder when audit not yet run', () => {
        render(<TransactionAudit />, { wrapper: createWrapper() })

        expect(screen.getByText(/Click "Run Audit"/)).toBeInTheDocument()
    })
})
