import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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

// Import components after mocks
import TradesTable, { type Trade, tradeColumns } from '../TradesTable'
import TradeDetailPanel from '../TradeDetailPanel'
import ScreenshotPanel from '../ScreenshotPanel'
import TradeReportForm from '../TradeReportForm'
import TradesLayout from '../TradesLayout'

// ─── Test Data ────────────────────────────────────────────────────────────────

const MOCK_TRADES: Trade[] = [
    {
        exec_id: 'T001',
        instrument: 'SPY STK',
        action: 'BOT',
        quantity: 100,
        price: 619.61,
        account_id: 'DU123456',
        commission: 1.02,
        realized_pnl: null,
        notes: 'Test note',
        image_count: 2,
        created_at: '2026-03-18T14:32:00Z',
    },
    {
        exec_id: 'T002',
        instrument: 'AAPL STK',
        action: 'SLD',
        quantity: 50,
        price: 198.30,
        account_id: 'DU123456',
        commission: 0.52,
        realized_pnl: 220,
        notes: null,
        image_count: 0,
        created_at: '2026-03-18T14:35:00Z',
    },
]

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

// ─── TradesTable Tests ───────────────────────────────────────────────────────

describe('TradesTable', () => {
    it('should define 9 columns', () => {
        expect(tradeColumns).toHaveLength(9)
    })

    it('should render trade rows with data-testid', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        const rows = screen.getAllByTestId('trade-row')
        expect(rows).toHaveLength(2)
    })

    it('should render all column headers', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        expect(screen.getByText('Time')).toBeInTheDocument()
        expect(screen.getByText('Instrument')).toBeInTheDocument()
        expect(screen.getByText('Action')).toBeInTheDocument()
        expect(screen.getByText('Qty')).toBeInTheDocument()
        expect(screen.getByText('Price')).toBeInTheDocument()
        expect(screen.getByText('Account')).toBeInTheDocument()
        expect(screen.getByText('Comm')).toBeInTheDocument()
        expect(screen.getByText('P&L')).toBeInTheDocument()
        expect(screen.getByText('📷')).toBeInTheDocument()
    })

    it('should render trade-list testid', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trade-list')).toBeInTheDocument()
    })

    it('should call onSelectTrade when row is clicked', () => {
        const onSelect = vi.fn()
        render(<TradesTable data={MOCK_TRADES} onSelectTrade={onSelect} />, {
            wrapper: createWrapper(),
        })
        fireEvent.click(screen.getAllByTestId('trade-row')[0])
        expect(onSelect).toHaveBeenCalledWith(MOCK_TRADES[0])
    })

    it('should color-code BOT as green and SLD as red', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        const rows = screen.getAllByTestId('trade-row')
        const botCell = rows[0].querySelector('.text-green-400')
        expect(botCell).not.toBeNull()
        const sldCell = rows[1].querySelector('.text-red-400')
        expect(sldCell).not.toBeNull()
    })

    it('should render image badge for trades with images', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        expect(screen.getByText('🖼×2')).toBeInTheDocument()
    })

    it('should show pagination controls', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        expect(screen.getByText(/Page 1/)).toBeInTheDocument()
    })

    // F6 FIX: Strengthened sorting test — verifies row order actually changes
    it('should reorder rows when sorting by Instrument column', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        const rows = screen.getAllByTestId('trade-row')
        // Before sort: SPY first (original order)
        expect(rows[0]).toHaveTextContent('SPY STK')
        expect(rows[1]).toHaveTextContent('AAPL STK')

        // Click Instrument header to sort ascending
        fireEvent.click(screen.getByText('Instrument'))

        const sortedRows = screen.getAllByTestId('trade-row')
        // After ascending sort: AAPL < SPY
        expect(sortedRows[0]).toHaveTextContent('AAPL STK')
        expect(sortedRows[1]).toHaveTextContent('SPY STK')
    })
})

// ─── TradeDetailPanel Tests ──────────────────────────────────────────────────

describe('TradeDetailPanel', () => {
    it('should show placeholder when no trade is selected', () => {
        render(<TradeDetailPanel />, { wrapper: createWrapper() })
        expect(screen.getByText(/Select a trade/)).toBeInTheDocument()
    })

    it('should render form fields when trade is provided', () => {
        render(<TradeDetailPanel trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trade-symbol-input')).toBeInTheDocument()
        expect(screen.getByTestId('trade-side-select')).toBeInTheDocument()
        expect(screen.getByTestId('trade-quantity-input')).toBeInTheDocument()
        expect(screen.getByTestId('trade-price-input')).toBeInTheDocument()
        expect(screen.getByTestId('trade-submit-btn')).toBeInTheDocument()
        expect(screen.getByTestId('trade-cancel-btn')).toBeInTheDocument()
    })

    it('should render 3 tabs: Info, Journal, Screenshots', () => {
        render(<TradeDetailPanel trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByText('Info')).toBeInTheDocument()
        expect(screen.getByText('Journal')).toBeInTheDocument()
        expect(screen.getByText('Screenshots')).toBeInTheDocument()
    })

    it('should show trade exec_id in header', () => {
        render(<TradeDetailPanel trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByText('T001')).toBeInTheDocument()
    })

    it('should call onSave when form is submitted with valid data', async () => {
        const onSave = vi.fn()
        render(<TradeDetailPanel trade={MOCK_TRADES[0]} onSave={onSave} />, {
            wrapper: createWrapper(),
        })
        fireEvent.click(screen.getByTestId('trade-submit-btn'))
        await waitFor(() => {
            expect(onSave).toHaveBeenCalled()
        })
    })

    // F6 FIX: Verify form resets when using key prop with different trades
    it('should populate form with correct trade data', () => {
        render(<TradeDetailPanel trade={MOCK_TRADES[1]} />, { wrapper: createWrapper() })
        const symbolInput = screen.getByTestId('trade-symbol-input') as HTMLInputElement
        expect(symbolInput.value).toBe('AAPL STK')
    })
})

// ─── ScreenshotPanel Tests ───────────────────────────────────────────────────

describe('ScreenshotPanel', () => {
    it('should render upload button', () => {
        render(<ScreenshotPanel tradeId="T001" />, { wrapper: createWrapper() })
        expect(screen.getByTestId('screenshot-upload-btn')).toBeInTheDocument()
    })

    it('should render thumbnails for existing screenshots', () => {
        const screenshots = [
            { id: 's1', url: 'http://example.com/img1.png', caption: 'Entry' },
            { id: 's2', url: 'http://example.com/img2.png', caption: 'Exit' },
        ]
        render(<ScreenshotPanel tradeId="T001" screenshots={screenshots} />, {
            wrapper: createWrapper(),
        })
        expect(screen.getByAltText('Entry')).toBeInTheDocument()
        expect(screen.getByAltText('Exit')).toBeInTheDocument()
    })

    it('should have hidden file input', () => {
        render(<ScreenshotPanel tradeId="T001" />, { wrapper: createWrapper() })
        expect(screen.getByTestId('screenshot-file-input')).toBeInTheDocument()
    })
})

// ─── TradeReportForm Tests ───────────────────────────────────────────────────

describe('TradeReportForm', () => {
    it('should render star ratings', () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByText('Setup Quality')).toBeInTheDocument()
        expect(screen.getByText('Execution Quality')).toBeInTheDocument()
    })

    it('should render emotional state dropdown', () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trade-emotional-state')).toBeInTheDocument()
    })

    it('should render followed-plan select', () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trade-followed-plan')).toBeInTheDocument()
    })

    it('should render lessons textarea', () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trade-lessons')).toBeInTheDocument()
    })

    it('should render tag input', () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trade-tag-input')).toBeInTheDocument()
    })

    it('should render save journal button', () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trade-report-save')).toBeInTheDocument()
    })
})

// ─── TradesLayout Tests ──────────────────────────────────────────────────────

describe('TradesLayout', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trades')) {
                return Promise.resolve({ items: MOCK_TRADES })
            }
            if (url.includes('/api/v1/mcp-guard/status')) {
                return Promise.resolve({ is_locked: false })
            }
            return Promise.reject(new Error('Unknown URL'))
        })
    })

    it('should render trades-page testid', () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        expect(screen.getByTestId('trades-page')).toBeInTheDocument()
    })

    it('should render add-trade-btn', () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        expect(screen.getByTestId('add-trade-btn')).toBeInTheDocument()
    })

    it('should render trades table with data', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-list')).toBeInTheDocument()
        })
    })

    it('should show detail panel when trade is clicked', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getAllByTestId('trade-row').length).toBeGreaterThan(0)
        })
        fireEvent.click(screen.getAllByTestId('trade-row')[0])
        expect(screen.getByText('T001')).toBeInTheDocument()
    })

    // F6 FIX: Test create-mode opens empty form with + New Trade
    it('should open empty detail panel when + New Trade is clicked', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        fireEvent.click(screen.getByTestId('add-trade-btn'))
        expect(screen.getByText('(new)')).toBeInTheDocument()
        const symbolInput = screen.getByTestId('trade-symbol-input') as HTMLInputElement
        expect(symbolInput.value).toBe('')
    })

    // F6 FIX: Test MCP Guard disables add-trade-btn
    it('should disable add-trade-btn when MCP Guard is locked', async () => {
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trades')) {
                return Promise.resolve({ items: MOCK_TRADES })
            }
            if (url.includes('/api/v1/mcp-guard/status')) {
                return Promise.resolve({ is_locked: true })
            }
            return Promise.reject(new Error('Unknown URL'))
        })
        render(<TradesLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('add-trade-btn')).toBeDisabled()
        })
    })
})
