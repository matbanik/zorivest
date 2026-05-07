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
import AccountTypeBadge from '../AccountTypeBadge'

// ─── Test Data ────────────────────────────────────────────────────────────────

const MOCK_TRADES: Trade[] = [
    {
        exec_id: 'T001',
        instrument: 'SPY STK',
        action: 'BOT',
        quantity: 100,
        price: 619.61,
        account_id: 'DU123456',
        account_type: 'broker',
        commission: 1.02,
        realized_pnl: null,
        notes: 'Test note',
        image_count: 2,
        time: '2026-03-18T14:32:00Z',
    },
    {
        exec_id: 'T002',
        instrument: 'AAPL STK',
        action: 'SLD',
        quantity: 50,
        price: 198.30,
        account_id: 'DU789012',
        account_type: 'ira',
        commission: 0.52,
        realized_pnl: 220,
        notes: null,
        image_count: 0,
        time: '2026-03-18T14:35:00Z',
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

    // ── Dirty-state guard tests (G22/G23) ─────────────────────────────────

    // G22-1: Save button text is "Save" when form is clean
    it('G22-1: save button shows "Save" when form is clean', () => {
        render(<TradeDetailPanel trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        const saveBtn = screen.getByTestId('trade-submit-btn')
        expect(saveBtn.textContent).not.toContain('•')
    })

    // G22-2: Save button shows amber-pulse and bullet when form is dirty
    it('G22-2: save button shows dirty indicators after field change', () => {
        render(<TradeDetailPanel trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })

        // Modify symbol to make form dirty
        fireEvent.change(screen.getByTestId('trade-symbol-input'), { target: { value: 'TSLA STK' } })

        const saveBtn = screen.getByTestId('trade-submit-btn')
        expect(saveBtn.className).toContain('btn-save-dirty')
        expect(saveBtn.textContent).toContain('•')
    })

    // G22-3: onDirtyChange fires when form becomes dirty
    it('G22-3: onDirtyChange fires true when form becomes dirty', async () => {
        const onDirtyChange = vi.fn()
        render(<TradeDetailPanel trade={MOCK_TRADES[0]} onDirtyChange={onDirtyChange} />, { wrapper: createWrapper() })

        fireEvent.change(screen.getByTestId('trade-symbol-input'), { target: { value: 'TSLA STK' } })

        await waitFor(() => {
            expect(onDirtyChange).toHaveBeenCalledWith(true)
        })
    })

    // R1: Child validity reporting for form guard
    describe('isInvalid() imperative handle', () => {
        it('returns true when instrument is empty (required field missing)', () => {
            const ref = React.createRef<{ save: () => Promise<void>; isInvalid: () => boolean }>()
            // Render with empty instrument (new trade defaults)
            const emptyTrade: Trade = {
                ...MOCK_TRADES[0],
                instrument: '',
            }
            render(<TradeDetailPanel ref={ref} trade={emptyTrade} />, { wrapper: createWrapper() })

            expect(ref.current?.isInvalid()).toBe(true)
        })

        it('returns false when all required fields are populated', () => {
            const ref = React.createRef<{ save: () => Promise<void>; isInvalid: () => boolean }>()
            render(<TradeDetailPanel ref={ref} trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })

            expect(ref.current?.isInvalid()).toBe(false)
        })
    })
})

// ─── ScreenshotPanel Tests ───────────────────────────────────────────────────

describe('ScreenshotPanel', () => {
    const MOCK_IMAGES = [
        { id: 1, caption: 'Entry', mime_type: 'image/webp', file_size: 5000 },
        { id: 2, caption: 'Exit', mime_type: 'image/webp', file_size: 3000 },
    ]

    beforeEach(() => {
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/trades/T001/images')) return Promise.resolve(MOCK_IMAGES)
            return Promise.resolve([])
        })
    })

    it('should render upload button', async () => {
        render(<ScreenshotPanel tradeId="T001" />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('screenshot-upload-btn')).toBeInTheDocument()
        })
    })

    it('should render thumbnails for existing screenshots', async () => {
        render(<ScreenshotPanel tradeId="T001" />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getAllByTestId('screenshot-thumbnail')).toHaveLength(2)
        })
        // Verify alt text uses the caption from API response
        expect(screen.getByAltText('Entry')).toBeInTheDocument()
        expect(screen.getByAltText('Exit')).toBeInTheDocument()
    })

    it('should have hidden file input', async () => {
        render(<ScreenshotPanel tradeId="T001" />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('screenshot-file-input')).toBeInTheDocument()
        })
    })
})

// ─── TradeReportForm Tests ───────────────────────────────────────────────────

const MOCK_REPORT_RESPONSE = {
    id: 1,
    trade_id: 'T001',
    setup_quality: 'A',
    execution_quality: 'B',
    followed_plan: true,
    emotional_state: 'Confident',
    lessons_learned: 'Good entry, held position',
    tags: ['momentum', 'breakout'],
    created_at: '2026-03-18T15:00:00Z',
}

describe('TradeReportForm', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Default: no existing report (404)
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/report')) {
                return Promise.reject(new Error('API 404: Not Found'))
            }
            return Promise.reject(new Error('Unknown URL'))
        })
    })

    it('should render star ratings', async () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Setup Quality')).toBeInTheDocument()
            expect(screen.getByText('Execution Quality')).toBeInTheDocument()
        })
    })

    it('should render emotional state dropdown', async () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-emotional-state')).toBeInTheDocument()
        })
    })

    it('should render followed-plan toggle as Yes/No buttons', async () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-followed-plan')).toBeInTheDocument()
            expect(screen.getByText('Yes')).toBeInTheDocument()
            expect(screen.getByText('No')).toBeInTheDocument()
        })
    })

    it('should render lessons textarea', async () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-lessons')).toBeInTheDocument()
        })
    })

    it('should render tag input', async () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-tag-input')).toBeInTheDocument()
        })
    })

    it('should render save journal button', async () => {
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-report-save')).toBeInTheDocument()
        })
    })
})

// ─── MEU-55: Trade Report API Wiring ─────────────────────────────────────────

describe('MEU-55: TradeReportForm API wiring', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('AC-1: should fetch existing report on mount via GET', async () => {
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/report')) {
                return Promise.resolve(MOCK_REPORT_RESPONSE)
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/trades/T001/report')
            )
        })
    })

    it('AC-2: should initialize with empty defaults on 404', async () => {
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/report')) {
                // R4: apiFetch throws Error('API 404: ...') for 404 responses (api.ts:23)
                return Promise.reject(new Error('API 404: Not Found'))
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            // Lessons textarea should be empty
            const lessons = screen.getByTestId('trade-lessons') as HTMLTextAreaElement
            expect(lessons.value).toBe('')
        })
    })

    it('AC-3: save button should call POST for new report', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: any) => {
            if (url.includes('/report') && !opts) {
                return Promise.reject(new Error('API 404: Not Found'))  // GET → no existing
            }
            if (url.includes('/report') && opts?.method === 'POST') {
                return Promise.resolve({ ...MOCK_REPORT_RESPONSE, id: 2 })
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-report-save')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('trade-report-save'))
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                `/api/v1/trades/T001/report`,
                expect.objectContaining({ method: 'POST' })
            )
        })
    })

    it('AC-4a: should convert star ratings to letter grades in payload', async () => {
        let capturedBody: any = null
        mockApiFetch.mockImplementation((url: string, opts?: any) => {
            if (url.includes('/report') && !opts) {
                return Promise.reject(new Error('API 404: Not Found'))
            }
            if (url.includes('/report') && opts?.method === 'POST') {
                capturedBody = JSON.parse(opts.body)
                return Promise.resolve({ ...MOCK_REPORT_RESPONSE, id: 2 })
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-report-save')).toBeInTheDocument()
        })
        // Click 5 stars on setup quality (default 0 → will send 'F' for 0, but let's set to 5)
        const stars = screen.getByTestId('star-rating-setup-quality').querySelectorAll('button')
        fireEvent.click(stars[4])  // 5th star = 5 → grade A
        fireEvent.click(screen.getByTestId('trade-report-save'))
        await waitFor(() => {
            expect(capturedBody).not.toBeNull()
            expect(capturedBody.setup_quality).toBe('A')
        })
    })

    it('AC-4b: should send followed_plan as boolean', async () => {
        let capturedBody: any = null
        mockApiFetch.mockImplementation((url: string, opts?: any) => {
            if (url.includes('/report') && !opts) {
                return Promise.reject(new Error('API 404: Not Found'))
            }
            if (url.includes('/report') && opts?.method === 'POST') {
                capturedBody = JSON.parse(opts.body)
                return Promise.resolve({ ...MOCK_REPORT_RESPONSE, id: 2 })
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-report-save')).toBeInTheDocument()
        })
        // Click No toggle
        fireEvent.click(screen.getByText('No'))
        fireEvent.click(screen.getByTestId('trade-report-save'))
        await waitFor(() => {
            expect(capturedBody).not.toBeNull()
            expect(capturedBody.followed_plan).toBe(false)
        })
    })

    it('AC-4c: should send emotional_state as string', async () => {
        let capturedBody: any = null
        mockApiFetch.mockImplementation((url: string, opts?: any) => {
            if (url.includes('/report') && !opts) {
                return Promise.reject(new Error('API 404: Not Found'))
            }
            if (url.includes('/report') && opts?.method === 'POST') {
                capturedBody = JSON.parse(opts.body)
                return Promise.resolve({ ...MOCK_REPORT_RESPONSE, id: 2 })
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-report-save')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('trade-report-save'))
        await waitFor(() => {
            expect(capturedBody).not.toBeNull()
            expect(typeof capturedBody.emotional_state).toBe('string')
        })
    })

    it('AC-6: should populate form with existing report data', async () => {
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/report')) {
                return Promise.resolve(MOCK_REPORT_RESPONSE)
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            const lessons = screen.getByTestId('trade-lessons') as HTMLTextAreaElement
            expect(lessons.value).toBe('Good entry, held position')
        })
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
            if (url.includes('/api/v1/accounts')) {
                return Promise.resolve([])
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
            if (url.includes('/api/v1/accounts')) {
                return Promise.resolve([])
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

    // ── R5: Parent-level invalid Save & Continue workflow ─────────────────
    describe('R5: invalid Save & Continue disabled at parent workflow level', () => {
        it('disables Save & Continue when instrument is cleared and user navigates', async () => {
            render(<TradesLayout />, { wrapper: createWrapper() })

            // Wait for trades to load
            await waitFor(() => {
                expect(screen.getAllByTestId('trade-row').length).toBeGreaterThan(0)
            })

            // Click first trade → detail panel renders
            fireEvent.click(screen.getAllByTestId('trade-row')[0])
            const symbolInput = await waitFor(() => {
                const input = screen.getByTestId('trade-symbol-input') as HTMLInputElement
                expect(input).toBeInTheDocument()
                return input
            })

            // Clear instrument field → form dirty + invalid
            fireEvent.change(symbolInput, { target: { value: '' } })

            // Click second trade → should trigger guard
            fireEvent.click(screen.getAllByTestId('trade-row')[1])

            // Modal should appear with Save & Continue disabled
            await waitFor(() => {
                expect(screen.getByTestId('unsaved-changes-modal')).toBeInTheDocument()
            })
            const saveBtn = screen.getByTestId('unsaved-save-continue-btn')
            expect(saveBtn).toBeDisabled()
        })

        it('does not navigate when clicking disabled Save & Continue on invalid trade form', async () => {
            render(<TradesLayout />, { wrapper: createWrapper() })

            // Wait for trades to load
            await waitFor(() => {
                expect(screen.getAllByTestId('trade-row').length).toBeGreaterThan(0)
            })

            // Click first trade → detail panel renders
            fireEvent.click(screen.getAllByTestId('trade-row')[0])
            await waitFor(() => {
                expect(screen.getByTestId('trade-symbol-input')).toBeInTheDocument()
            })

            // Clear instrument → dirty + invalid
            const symbolInput = screen.getByTestId('trade-symbol-input') as HTMLInputElement
            fireEvent.change(symbolInput, { target: { value: '' } })

            // Click second trade → guard triggers
            fireEvent.click(screen.getAllByTestId('trade-row')[1])

            // Modal appears
            await waitFor(() => {
                expect(screen.getByTestId('unsaved-changes-modal')).toBeInTheDocument()
            })

            // Click the disabled Save & Continue button
            const saveBtn = screen.getByTestId('unsaved-save-continue-btn')
            fireEvent.click(saveBtn)

            // First trade detail should still be visible (no navigation occurred)
            expect(screen.getByTestId('trade-symbol-input')).toBeInTheDocument()
            expect((screen.getByTestId('trade-symbol-input') as HTMLInputElement).value).toBe('')
        })
    })
})

// ─── MEU-54: Multi-Account UI Tests ──────────────────────────────────────────

describe('AccountTypeBadge', () => {
    it('should render badge with correct data-testid', () => {
        render(<AccountTypeBadge accountType="broker" />)
        expect(screen.getByTestId('account-type-badge')).toBeInTheDocument()
    })

    it('should render correct label for broker', () => {
        render(<AccountTypeBadge accountType="broker" />)
        expect(screen.getByText('Broker')).toBeInTheDocument()
    })

    it('should render correct label for ira', () => {
        render(<AccountTypeBadge accountType="ira" />)
        expect(screen.getByText('IRA')).toBeInTheDocument()
    })

    it('should render correct label for 401k', () => {
        render(<AccountTypeBadge accountType="401k" />)
        expect(screen.getByText('401k')).toBeInTheDocument()
    })

    it('should handle unknown account type gracefully', () => {
        render(<AccountTypeBadge accountType="custom" />)
        expect(screen.getByText('custom')).toBeInTheDocument()
    })

    it('should be case-insensitive', () => {
        render(<AccountTypeBadge accountType="BROKER" />)
        expect(screen.getByText('Broker')).toBeInTheDocument()
    })
})

describe('MEU-54: TradesTable account column', () => {
    it('should render account type badges when account_type is present', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        const badges = screen.getAllByTestId('account-type-badge')
        expect(badges.length).toBeGreaterThanOrEqual(2)
    })

    it('should render account ID alongside badge', () => {
        render(<TradesTable data={MOCK_TRADES} />, { wrapper: createWrapper() })
        expect(screen.getByText('DU123456')).toBeInTheDocument()
    })

    it('should truncate account IDs longer than 15 characters per G7', () => {
        const longIdTrades: Trade[] = [{
            ...MOCK_TRADES[0],
            account_id: 'VERY_LONG_ACCOUNT_ID_12345',
        }]
        render(<TradesTable data={longIdTrades} />, { wrapper: createWrapper() })
        expect(screen.getByText('VERY_LONG_ACCOU…')).toBeInTheDocument()
    })
})

describe('MEU-54: TradesLayout account filter', () => {
    const MOCK_FILTER_ACCOUNTS = [
        { account_id: 'DU123456', account_type: 'broker' },
        { account_id: 'DU789012', account_type: 'ira' },
    ]

    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/accounts')) {
                // AC-3: return account list from dedicated endpoint
                return Promise.resolve(MOCK_FILTER_ACCOUNTS)
            }
            if (url.includes('/api/v1/trades')) {
                return Promise.resolve({ items: MOCK_TRADES })
            }
            if (url.includes('/api/v1/mcp-guard/status')) {
                return Promise.resolve({ is_locked: false })
            }
            return Promise.reject(new Error('Unknown URL'))
        })
    })

    it('should render account filter dropdown', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('account-filter-dropdown')).toBeInTheDocument()
        })
    })

    it('should have All Accounts as default option', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('All Accounts')).toBeInTheDocument()
        })
    })

    it('AC-3: should query GET /api/v1/accounts for dropdown options', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            // Verify the accounts endpoint was called (AC-3 contract)
            const accountsCalls = mockApiFetch.mock.calls.filter(
                (c: unknown[]) => (c[0] as string).includes('/api/v1/accounts'),
            )
            expect(accountsCalls.length).toBeGreaterThanOrEqual(1)
        })
    })

    it('AC-3: should populate dropdown from /api/v1/accounts response', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const options = screen.getByTestId('account-filter-dropdown').querySelectorAll('option')
            // All Accounts + 2 accounts from MOCK_FILTER_ACCOUNTS = 3 options
            expect(options.length).toBeGreaterThanOrEqual(3)
        })
    })

    it('AC-4: should re-query trades with account_id when filter changes', async () => {
        render(<TradesLayout />, { wrapper: createWrapper() })
        // Wait for dropdown to populate from accounts query
        await waitFor(() => {
            const options = screen.getByTestId('account-filter-dropdown').querySelectorAll('option')
            expect(options.length).toBeGreaterThanOrEqual(3)
        })
        // Change filter selection
        fireEvent.change(screen.getByTestId('account-filter-dropdown'), {
            target: { value: 'DU123456' },
        })
        await waitFor(() => {
            // Verify a trades query was made with account_id param
            const tradesCalls = mockApiFetch.mock.calls.filter(
                (c: unknown[]) => (c[0] as string).includes('/api/v1/trades') &&
                    (c[0] as string).includes('account_id=DU123456'),
            )
            expect(tradesCalls.length).toBeGreaterThanOrEqual(1)
        })
    })
})

describe('MEU-55: TradeReportForm R4 error handling', () => {
    it('R4: non-404 GET error shows error state, not empty create form', async () => {
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/report')) {
                return Promise.reject(new Error('API 500: Internal Server Error'))
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            // Error state must be shown — form should NOT render the create/edit UI
            expect(screen.getByTestId('trade-report-error')).toBeInTheDocument()
            expect(screen.queryByTestId('trade-report-form')).not.toBeInTheDocument()
        })
    })

    it('AC-8: existing report uses PUT not POST', async () => {
        const MOCK_EXISTING: typeof MOCK_REPORT_RESPONSE = { ...MOCK_REPORT_RESPONSE }
        mockApiFetch.mockImplementation((url: string, opts?: RequestInit) => {
            if (url.includes('/report') && !opts) {
                return Promise.resolve(MOCK_EXISTING)
            }
            if (url.includes('/report') && opts?.method === 'PUT') {
                return Promise.resolve(MOCK_EXISTING)
            }
            return Promise.reject(new Error('Unknown'))
        })
        render(<TradeReportForm trade={MOCK_TRADES[0]} />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-report-save')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('trade-report-save'))
        await waitFor(() => {
            const putCalls = mockApiFetch.mock.calls.filter(
                (c: unknown[]) => (c[0] as string).includes('/report') && (c[1] as RequestInit)?.method === 'PUT',
            )
            expect(putCalls.length).toBeGreaterThanOrEqual(1)
        })
    })
})
