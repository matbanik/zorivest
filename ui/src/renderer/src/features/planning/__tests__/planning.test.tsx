import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

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
import WatchlistPage from '../WatchlistPage'
import PositionCalculatorModal from '../PositionCalculatorModal'
import PlanningLayout from '../PlanningLayout'

// ─── Test Helpers ─────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    return function Wrapper({ children }: { children: ReactNode }) {
        return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    }
}

// ─── Test Data ────────────────────────────────────────────────────────────

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
]

const MOCK_WATCHLISTS = [
    {
        id: 1,
        name: 'Tech Stocks',
        description: 'Large-cap tech',
        created_at: '2026-03-20T10:00:00Z',
        updated_at: '2026-03-20T10:00:00Z',
        items: [
            { id: 1, watchlist_id: 1, ticker: 'AAPL', added_at: '2026-03-20T10:00:00Z', notes: 'Watch for earnings' },
            { id: 2, watchlist_id: 1, ticker: 'MSFT', added_at: '2026-03-20T10:00:00Z', notes: '' },
        ],
    },
]

// ─── TradePlanPage Tests ──────────────────────────────────────────────────

describe('MEU-48: TradePlanPage', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans') && !url.includes('/status')) {
                return Promise.resolve(MOCK_PLANS)
            }
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
    })

    it('should render page with testid', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-plan-page')).toBeInTheDocument()
        })
    })

    it('should render plan cards with conviction indicators (AC-2)', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
            expect(screen.getByText('NVDA')).toBeInTheDocument()
        })
        const indicators = screen.getAllByTestId('conviction-indicator')
        expect(indicators.length).toBe(2)
        expect(indicators[0].textContent).toBe('🟢') // high
        expect(indicators[1].textContent).toBe('🔴') // low
    })

    it('should show status badges on plan cards', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('active')).toBeInTheDocument()
            expect(screen.getByText('draft')).toBeInTheDocument()
        })
    })

    it('should filter plans by status (AC-6)', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.change(screen.getByTestId('plan-status-filter'), { target: { value: 'draft' } })
        await waitFor(() => {
            expect(screen.queryByText('AAPL')).not.toBeInTheDocument()
            expect(screen.getByText('NVDA')).toBeInTheDocument()
        })
    })

    it('should filter plans by conviction (AC-6)', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.change(screen.getByTestId('plan-conviction-filter'), { target: { value: 'high' } })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
            expect(screen.queryByText('NVDA')).not.toBeInTheDocument()
        })
    })

    it('should open detail panel with all fields on card click (AC-3)', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-detail-panel')).toBeInTheDocument()
            expect(screen.getByTestId('plan-ticker-input')).toHaveValue('AAPL')
            expect(screen.getByTestId('plan-entry-price')).toHaveValue(190)
            expect(screen.getByTestId('plan-stop-loss')).toHaveValue(188)
            expect(screen.getByTestId('plan-target-price')).toHaveValue(196)
        })
    })

    it('should compute R:R ratio live (AC-4)', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            const rrDisplay = screen.getByTestId('plan-rr-display')
            expect(rrDisplay).toBeInTheDocument()
            // entry=190, stop=188, target=196 → risk=2, reward=6, R:R=3.00
            expect(rrDisplay.textContent).toContain('3.00')
        })
    })

    it('should create a new plan via POST (AC-5)', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'POST') return Promise.resolve({ id: 3 })
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
        render(<TradePlanPage />, { wrapper: createWrapper() })
        fireEvent.click(screen.getByTestId('new-plan-btn'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-detail-panel')).toBeInTheDocument()
        })
        fireEvent.change(screen.getByTestId('plan-ticker-input'), { target: { value: 'TSLA' } })
        fireEvent.change(screen.getByTestId('plan-strategy-name'), { target: { value: 'Breakout' } })
        fireEvent.click(screen.getByTestId('plan-save-btn'))
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/trade-plans',
                expect.objectContaining({ method: 'POST' }),
            )
        })
    })

    it('should delete a plan (AC-5)', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'DELETE') return Promise.resolve(undefined)
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-delete-btn')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-delete-btn'))
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/trade-plans/1',
                expect.objectContaining({ method: 'DELETE' }),
            )
        })
    })

    it('should change status via PATCH (AC-5a)', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PATCH') return Promise.resolve({ ...MOCK_PLANS[0], status: 'executed' })
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-status-buttons')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-status-executed'))
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/trade-plans/1/status',
                expect.objectContaining({ method: 'PATCH' }),
            )
        })
    })

    it('should show linked_trade_id as readonly (AC-7)', async () => {
        const linkedPlan = { ...MOCK_PLANS[0], linked_trade_id: 'T001' }
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([linkedPlan])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId(`plan-card-${linkedPlan.id}`))
        await waitFor(() => {
            const linkedField = screen.getByTestId('plan-linked-trade')
            expect(linkedField).toHaveAttribute('readonly')
            expect(linkedField).toHaveValue('T001')
        })
    })
})

// ─── WatchlistPage Tests ──────────────────────────────────────────────────

describe('MEU-48: WatchlistPage', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
            if (url === '/api/v1/watchlists/1') return Promise.resolve(MOCK_WATCHLISTS[0])
            if (url.includes('/api/v1/settings/')) return Promise.resolve({ value: false })
            return Promise.resolve({})
        })
    })

    it('should render watchlist page', async () => {
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('watchlist-page')).toBeInTheDocument()
        })
    })

    it('should render watchlist cards with item counts (AC-8)', async () => {
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
            // W3: now shows ticker list instead of item count
            expect(screen.getByText('AAPL, MSFT')).toBeInTheDocument()
        })
    })

    it('should show items on card click (AC-8)', async () => {
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('watchlist-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('watchlist-detail-panel')).toBeInTheDocument()
            expect(screen.getByTestId('watchlist-row-AAPL')).toBeInTheDocument()
            expect(screen.getByTestId('watchlist-row-MSFT')).toBeInTheDocument()
        })
    })

    it('should add ticker inline (AC-9)', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'POST' && url.includes('/items')) {
                return Promise.resolve({ id: 3, watchlist_id: 1, ticker: 'GOOG', added_at: '', notes: '' })
            }
            if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
            if (url === '/api/v1/watchlists/1') return Promise.resolve(MOCK_WATCHLISTS[0])
            if (url.includes('/api/v1/settings/')) return Promise.resolve({ value: false })
            return Promise.resolve({})
        })
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('watchlist-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('watchlist-ticker-input')).toBeInTheDocument()
        })
        fireEvent.change(screen.getByTestId('watchlist-ticker-input-input'), { target: { value: 'GOOG' } })
        fireEvent.click(screen.getByTestId('watchlist-add-ticker-btn'))
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/watchlists/1/items',
                expect.objectContaining({ method: 'POST' }),
            )
        })
    })

    it('should remove ticker (AC-9)', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'DELETE') return Promise.resolve(undefined)
            if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
            if (url === '/api/v1/watchlists/1') return Promise.resolve(MOCK_WATCHLISTS[0])
            if (url.includes('/api/v1/settings/')) return Promise.resolve({ value: false })
            return Promise.resolve({})
        })
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('watchlist-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('remove-ticker-AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('remove-ticker-AAPL'))
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/watchlists/1/items/AAPL',
                expect.objectContaining({ method: 'DELETE' }),
            )
        })
    })

    it('should create a new watchlist (AC-10)', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'POST' && url === '/api/v1/watchlists/') {
                return Promise.resolve({ id: 2, name: 'New List', description: '', items: [] })
            }
            if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
            if (url.includes('/api/v1/settings/')) return Promise.resolve({ value: false })
            return Promise.resolve({})
        })
        render(<WatchlistPage />, { wrapper: createWrapper() })
        fireEvent.click(screen.getByTestId('new-watchlist-btn'))
        await waitFor(() => {
            expect(screen.getByTestId('watchlist-name')).toBeInTheDocument()
        })
        fireEvent.change(screen.getByTestId('watchlist-name'), { target: { value: 'New List' } })
        fireEvent.click(screen.getByTestId('watchlist-save-btn'))
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/watchlists/',
                expect.objectContaining({ method: 'POST' }),
            )
        })
    })
})

// ─── PositionCalculatorModal Tests ────────────────────────────────────────

describe('MEU-48: PositionCalculatorModal', () => {
    it('should not render when closed', () => {
        render(<PositionCalculatorModal isOpen={false} onClose={vi.fn()} />, { wrapper: createWrapper() })
        expect(screen.queryByTestId('calculator-modal')).not.toBeInTheDocument()
    })

    it('should render with all input fields (AC-14)', () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('calculator-modal')).toBeInTheDocument()
        expect(screen.getByTestId('calc-account-size')).toBeInTheDocument()
        expect(screen.getByTestId('calc-risk-percent')).toBeInTheDocument()
        expect(screen.getByTestId('calc-entry-price')).toBeInTheDocument()
        expect(screen.getByTestId('calc-stop-price')).toBeInTheDocument()
        expect(screen.getByTestId('calc-target-price')).toBeInTheDocument()
    })

    it('should compute shares correctly (AC-15)', () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        // Explicitly set account size (no longer relies on hardcoded default)
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: '' } })  // Manual
        fireEvent.change(screen.getByTestId('calc-account-size'), { target: { value: '100000' } })
        // $100k, 1% risk = $1000 risk
        // Entry 100, Stop 98 → risk/share = $2 → shares = floor(1000/2) = 500
        fireEvent.change(screen.getByTestId('calc-entry-price'), { target: { value: '100' } })
        fireEvent.change(screen.getByTestId('calc-stop-price'), { target: { value: '98' } })
        fireEvent.change(screen.getByTestId('calc-target-price'), { target: { value: '106' } })
        expect(screen.getByTestId('calc-shares-output').textContent).toBe('500')
    })

    it('should compute R:R ratio correctly (AC-15)', () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        fireEvent.change(screen.getByTestId('calc-entry-price'), { target: { value: '100' } })
        fireEvent.change(screen.getByTestId('calc-stop-price'), { target: { value: '98' } })
        fireEvent.change(screen.getByTestId('calc-target-price'), { target: { value: '106' } })
        // risk=2, reward=6 → R:R = 3.00
        expect(screen.getByTestId('calc-rr-output').textContent).toBe('3.00')
    })

    it('should show oversize warning when position > 100% (AC-15)', () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        // Explicitly set account size
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: '' } })  // Manual
        fireEvent.change(screen.getByTestId('calc-account-size'), { target: { value: '100000' } })
        // $100k account, 1% risk, entry=1000, stop=999 → risk/share=$1 → shares=1000 → position=$1M (1000%)
        fireEvent.change(screen.getByTestId('calc-entry-price'), { target: { value: '1000' } })
        fireEvent.change(screen.getByTestId('calc-stop-price'), { target: { value: '999' } })
        fireEvent.change(screen.getByTestId('calc-target-price'), { target: { value: '1003' } })
        expect(screen.getByTestId('calc-oversize-warning')).toBeInTheDocument()
    })

    it('should close on Escape key', () => {
        const onClose = vi.fn()
        render(<PositionCalculatorModal isOpen={true} onClose={onClose} />, { wrapper: createWrapper() })
        fireEvent.keyDown(window, { key: 'Escape' })
        expect(onClose).toHaveBeenCalled()
    })
})

// ─── PlanningLayout Tests ─────────────────────────────────────────────────

describe('MEU-48: PlanningLayout', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([])
            if (url.includes('/api/v1/watchlists')) return Promise.resolve([])
            if (url.includes('/api/v1/mcp-guard/status')) return Promise.resolve({ is_locked: false })
            return Promise.resolve({})
        })
    })

    it('should render tabs (AC-1)', async () => {
        render(<PlanningLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('planning-layout')).toBeInTheDocument()
            expect(screen.getByTestId('planning-tab-trade-plans')).toBeInTheDocument()
            expect(screen.getByTestId('planning-tab-watchlists')).toBeInTheDocument()
        })
    })

    it('should switch tabs', async () => {
        render(<PlanningLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('trade-plan-page')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('planning-tab-watchlists'))
        await waitFor(() => {
            expect(screen.getByTestId('watchlist-page')).toBeInTheDocument()
        })
    })

    it('should dispatch open-calculator event via button', async () => {
        const spy = vi.fn()
        window.addEventListener('zorivest:open-calculator', spy)
        render(<PlanningLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('open-calculator-btn')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('open-calculator-btn'))
        expect(spy).toHaveBeenCalledTimes(1)
        window.removeEventListener('zorivest:open-calculator', spy)
    })

    it('should render without calculator modal (modal is in AppShell) (AC-13)', async () => {
        render(<PlanningLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('planning-layout')).toBeInTheDocument()
        })
        // Calculator modal is rendered in AppShell, not PlanningLayout
        expect(screen.queryByTestId('calculator-modal')).not.toBeInTheDocument()
    })
})

// ─── MEU-70 TIER 1: C2 — Copy-to-clipboard ───────────────────────────────

describe('MEU-70 T1: C2 — Copy-to-clipboard on shares', () => {
    it('should render copy button next to shares output', () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        fireEvent.change(screen.getByTestId('calc-entry-price'), { target: { value: '100' } })
        fireEvent.change(screen.getByTestId('calc-stop-price'), { target: { value: '98' } })
        expect(screen.getByTestId('calc-copy-shares-btn')).toBeInTheDocument()
    })

    it('should copy shares to clipboard on click', async () => {
        const writeText = vi.fn().mockResolvedValue(undefined)
        Object.assign(navigator, { clipboard: { writeText } })

        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        // Explicitly set account size
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: '' } })  // Manual
        fireEvent.change(screen.getByTestId('calc-account-size'), { target: { value: '100000' } })
        fireEvent.change(screen.getByTestId('calc-entry-price'), { target: { value: '100' } })
        fireEvent.change(screen.getByTestId('calc-stop-price'), { target: { value: '98' } })
        fireEvent.change(screen.getByTestId('calc-target-price'), { target: { value: '106' } })

        fireEvent.click(screen.getByTestId('calc-copy-shares-btn'))
        await waitFor(() => {
            expect(writeText).toHaveBeenCalledWith('500')
        })
    })
})

// ─── MEU-70 TIER 1: T3 — Account dropdown on Trade Plan ──────────────────

describe('MEU-70 T1: T3 — Account dropdown', () => {
    const MOCK_ACCOUNTS = [
        { account_id: 'acc-1', name: 'Main Trading', account_type: 'margin' },
        { account_id: 'acc-2', name: 'IRA', account_type: 'retirement' },
    ]

    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve(MOCK_ACCOUNTS)
            return Promise.resolve({})
        })
    })

    it('should render account select dropdown in plan form', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        fireEvent.click(screen.getByTestId('new-plan-btn'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-account-select')).toBeInTheDocument()
        })
    })

    it('should populate account dropdown with fetched accounts', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        fireEvent.click(screen.getByTestId('new-plan-btn'))
        await waitFor(() => {
            const select = screen.getByTestId('plan-account-select') as HTMLSelectElement
            // Should have default 'None' + 2 accounts
            expect(select.options.length).toBeGreaterThanOrEqual(3)
        })
    })

    it('should set account_id when account is selected', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'POST') return Promise.resolve({ id: 3 })
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve(MOCK_ACCOUNTS)
            return Promise.resolve({})
        })
        render(<TradePlanPage />, { wrapper: createWrapper() })
        fireEvent.click(screen.getByTestId('new-plan-btn'))
        // Wait for accounts to load into dropdown
        await waitFor(() => {
            const select = screen.getByTestId('plan-account-select') as HTMLSelectElement
            expect(select.options.length).toBeGreaterThanOrEqual(3)
        })
        fireEvent.change(screen.getByTestId('plan-account-select'), { target: { value: 'acc-1' } })
        fireEvent.change(screen.getByTestId('plan-ticker-input'), { target: { value: 'TSLA' } })
        fireEvent.click(screen.getByTestId('plan-save-btn'))
        await waitFor(() => {
            const call = mockApiFetch.mock.calls.find(
                (c: unknown[]) => (c[1] as Record<string, unknown>)?.method === 'POST',
            )
            expect(call).toBeDefined()
            const body = JSON.parse((call![1] as Record<string, string>).body)
            expect(body.account_id).toBe('acc-1')
        })
    })
})

// ─── MEU-70 TIER 1: T6 — Strategy name combobox ──────────────────────────

describe('MEU-70 T1: T6 — Strategy name combobox', () => {
    const PLANS_WITH_STRATEGIES: TradePlan[] = [
        { ...MOCK_PLANS[0], strategy_name: 'Gap Fill' },
        { ...MOCK_PLANS[1], strategy_name: 'Breakout' },
    ]

    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(PLANS_WITH_STRATEGIES)
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
    })

    it('should render strategy name as datalist-backed input', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('new-plan-btn'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-strategy-name')).toHaveAttribute('list')
        })
    })

    it('should include existing strategy names as datalist options', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('new-plan-btn'))
        await waitFor(() => {
            const datalist = document.getElementById('strategy-suggestions')
            expect(datalist).toBeInTheDocument()
            const options = datalist!.querySelectorAll('option')
            const values = Array.from(options).map((o) => o.value)
            expect(values).toContain('Gap Fill')
            expect(values).toContain('Breakout')
        })
    })

    it('should allow free-text entry of new strategy names', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        fireEvent.click(screen.getByTestId('new-plan-btn'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-strategy-name')).toBeInTheDocument()
        })
        fireEvent.change(screen.getByTestId('plan-strategy-name'), { target: { value: 'New Custom Strategy' } })
        expect(screen.getByTestId('plan-strategy-name')).toHaveValue('New Custom Strategy')
    })
})

// ─── MEU-70 TIER 1: T2 — Calculator ↔ Trade Plan integration ─────────────

describe('MEU-70 T1: T2 — Calculator ↔ Trade Plan', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
    })

    it('should show Calculate Position button in plan detail', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-calculate-position-btn')).toBeInTheDocument()
        })
    })

    it('should dispatch open-calculator event with plan prices on click', async () => {
        const spy = vi.fn()
        window.addEventListener('zorivest:open-calculator', spy)

        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-calculate-position-btn')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-calculate-position-btn'))
        expect(spy).toHaveBeenCalledTimes(1)

        const event = spy.mock.calls[0][0] as CustomEvent
        expect(event.detail).toEqual(
            expect.objectContaining({
                entry_price: 190,
                stop_loss: 188,
                target_price: 196,
            }),
        )
        window.removeEventListener('zorivest:open-calculator', spy)
    })
})

// ─── MEU-70 TIER 1: W3 — Better watchlist item display ───────────────────

describe('MEU-70 T1: W3 — Better watchlist display', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
            if (url === '/api/v1/watchlists/1') return Promise.resolve(MOCK_WATCHLISTS[0])
            if (url.includes('/api/v1/settings/')) return Promise.resolve({ value: false })
            return Promise.resolve({})
        })
    })

    it('should show ticker symbols in sidebar card instead of just count', async () => {
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
        })
        const card = screen.getByTestId('watchlist-card-1')
        expect(card).toHaveTextContent('AAPL')
        expect(card).toHaveTextContent('MSFT')
    })
})

// ─── MEU-70 TIER 1: T5 — Status timestamps display ──────────────────────

describe('MEU-70 T1: T5 — Status timestamps display', () => {
    const EXECUTED_PLAN = {
        ...MOCK_PLANS[0],
        status: 'executed',
        executed_at: '2026-03-20T15:45:00Z',
    }

    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([EXECUTED_PLAN])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
    })

    it('should show executed_at timestamp for executed plans', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('AAPL')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('plan-executed-at')).toBeInTheDocument()
        })
    })
})

// --- T4-UX: TDD Red Phase ---
// AC-T4-UX-1: label shows date/time, not "T -"          [Human-approved]
// AC-T4-UX-2: picker has text search input               [Human-approved]
// AC-T4-UX-3: option data-testid uses exec_id            [Human-approved]
// AC-T4-UX-3b: filtering hides non-matching options      [Human-approved]

const REAL_API_TRADE = {
    exec_id: 'E-001',
    time: '2026-03-20T14:35:00Z',
    instrument: 'asd',
    action: 'BOT',
    quantity: 100,
    price: 50.25,
}
const EXECUTED_PLAN_UX = { ...MOCK_PLANS[0], ticker: 'asd', status: 'executed' }

describe('MEU-48 T4-UX: Searchable Trade Picker', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([EXECUTED_PLAN_UX])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            if (url.includes('/api/v1/trades')) return Promise.resolve({ items: [REAL_API_TRADE], total: 1 })
            return Promise.resolve({})
        })
    })

    async function openExecutedPlanDetail() {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('asd')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        // wait for picker + search input (sync) then options (async query)
        await waitFor(() => expect(screen.getByTestId('trade-picker-search')).toBeInTheDocument())
        await waitFor(() => expect(screen.getByTestId('trade-option-E-001')).toBeInTheDocument())
    }

    it('AC-T4-UX-1: option label shows date/time not "T -" prefix', async () => {
        await openExecutedPlanDetail()
        const option = screen.getByTestId('trade-option-E-001')
        expect(option.textContent).not.toMatch(/^T -/)
        expect(option.textContent).toMatch(/2026|BOT/i)
    })

    it('AC-T4-UX-2: trade picker section has a text search input', async () => {
        await openExecutedPlanDetail()
        expect(screen.getByTestId('trade-picker-search')).toBeInTheDocument()
    })

    it('AC-T4-UX-3: option data-testid uses exec_id (correct field mapping)', async () => {
        await openExecutedPlanDetail()
        expect(screen.getByTestId('trade-option-E-001')).toBeInTheDocument()
    })

    it('AC-T4-UX-3b: typing filter hides non-matching trade options', async () => {
        await openExecutedPlanDetail()
        fireEvent.change(screen.getByTestId('trade-picker-search'), { target: { value: 'ZZZNOMATCH' } })
        expect(screen.queryByTestId('trade-option-E-001')).not.toBeInTheDocument()
    })
})

// --- Date Format + Trade Selection TDD Red Phase ---
// AC-T4-DATE-1: date label uses MM-DD-YYYY h:mmAM/PM format  [Human-approved]
// AC-T4-SELECT-1: clicking a trade highlights it as selected  [Human-approved]

describe('MEU-48 T4-UX: Date Format + Trade Selection', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([EXECUTED_PLAN_UX])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            if (url.includes('/api/v1/trades')) return Promise.resolve({ items: [REAL_API_TRADE], total: 1 })
            return Promise.resolve({})
        })
    })

    async function openAndWaitForTrades() {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('asd')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('trade-picker-search')).toBeInTheDocument())
        await waitFor(() => expect(screen.getByTestId('trade-option-E-001')).toBeInTheDocument())
    }

    it('AC-T4-DATE-1: date label format is MM-DD-YYYY not "Mar X, YYYY"', async () => {
        await openAndWaitForTrades()
        const option = screen.getByTestId('trade-option-E-001')
        // Must match 03-20-2026 format
        expect(option.textContent).toMatch(/03-20-2026/)
        // Must NOT use locale "Mar 20, 2026" format
        expect(option.textContent).not.toMatch(/Mar 20, 2026/)
    })

    it('AC-T4-SELECT-1: clicking a trade option shows the selected label in the picker input (MEU-70b)', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('asd')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('trade-picker-search')).toBeInTheDocument())
        // Wait for trade options to load
        await waitFor(() => expect(screen.queryByTestId('trade-option-E-001')).toBeInTheDocument())
        // Click the trade option
        fireEvent.click(screen.getByTestId('trade-option-E-001'))
        // MEU-70b: after selection, the options list collapses and the input shows the selected label
        await waitFor(() => {
            const input = screen.getByTestId('trade-picker-search') as HTMLInputElement
            // Input value should now contain the trade label (date + action + qty@price)
            expect(input.value).toMatch(/03-20-2026/)
        })
        // The option list should be hidden (label is set, !tradePickerLabel = false → list hidden)
        expect(screen.queryByTestId('trade-option-E-001')).not.toBeInTheDocument()
    })
})

describe('Recheck R1-R5: persistence and contract regressions', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([EXECUTED_PLAN_UX])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            if (url.includes('/api/v1/trades')) return Promise.resolve({ items: [REAL_API_TRADE], total: 1 })
            return Promise.resolve({})
        })
    })

    it('R1: handleSave PUT payload includes linked_trade_id', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('asd')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('trade-option-E-001')).toBeInTheDocument())
        // Select a trade in the picker
        fireEvent.click(screen.getByTestId('trade-option-E-001'))
        // Click Save Changes
        fireEvent.click(screen.getByTestId('plan-save-btn'))
        await waitFor(() => {
            const putCalls = mockApiFetch.mock.calls.filter(
                (c: unknown[]) =>
                    (c[0] as string).includes('/api/v1/trade-plans/') &&
                    (c[1] as RequestInit)?.method === 'PUT',
            )
            expect(putCalls.length).toBeGreaterThanOrEqual(1)
            const body = JSON.parse((putCalls[0][1] as RequestInit).body as string)
            expect(body).toHaveProperty('linked_trade_id', 'E-001')
        })
    })

    it('R2: trade picker queries /api/v1/trades with search= not ticker=', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('asd')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            const tradeCalls = mockApiFetch.mock.calls.filter(
                (c: unknown[]) => (c[0] as string).includes('/api/v1/trades'),
            )
            expect(tradeCalls.length).toBeGreaterThanOrEqual(1)
            const url = tradeCalls[0][0] as string
            // R2: must use 'search=' not 'ticker='
            expect(url).toContain('search=')
            expect(url).not.toContain('ticker=')
        })
    })

    it('R3: status stays unchanged in local form on PATCH failure', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: RequestInit) => {
            if (url.includes('/status') && opts?.method === 'PATCH') {
                return Promise.reject(new Error('API 500: Server error'))
            }
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([EXECUTED_PLAN_UX])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            if (url.includes('/api/v1/trades')) return Promise.resolve({ items: [], total: 0 })
            return Promise.resolve({})
        })
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('asd')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('plan-status-active')).toBeInTheDocument())
        // Attempt to change to 'active' status (PATCH will fail)
        fireEvent.click(screen.getByTestId('plan-status-active'))
        // After failure, 'executed' button should still be aria-pressed=true (original status)
        await waitFor(() => {
            const executedBtn = screen.getByTestId('plan-status-executed') as HTMLButtonElement
            expect(executedBtn.getAttribute('aria-pressed')).toBe('true')
        })
    })

    it('R5: zorivest:open-calculator event detail includes ticker', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('asd')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('plan-calculate-position-btn')).toBeInTheDocument())

        let capturedDetail: Record<string, unknown> | null = null
        window.addEventListener('zorivest:open-calculator', (e) => {
            capturedDetail = (e as CustomEvent).detail
        }, { once: true })

        fireEvent.click(screen.getByTestId('plan-calculate-position-btn'))
        expect(capturedDetail).not.toBeNull()
        expect(capturedDetail).toHaveProperty('ticker')
        expect(typeof (capturedDetail as unknown as Record<string, unknown>).ticker).toBe('string')
    })
})

// ─── MEU-71b: Calculator Account Integration ──────────────────────────────

describe('MEU-71b: Calculator Account Dropdown', () => {
    const MOCK_ACCOUNTS_ENRICHED = [
        {
            account_id: 'ACC001',
            name: 'Main Trading',
            account_type: 'broker',
            latest_balance: 50000.0,
            latest_balance_date: '2025-03-15T00:00:00',
        },
        {
            account_id: 'ACC002',
            name: 'IRA',
            account_type: 'retirement',
            latest_balance: 25000.0,
            latest_balance_date: '2025-03-10T00:00:00',
        },
    ]

    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/accounts')) return Promise.resolve(MOCK_ACCOUNTS_ENRICHED)
            return Promise.resolve({})
        })
    })

    it('AC-1: renders account dropdown with Manual, All Accounts, and individual accounts; defaults to All Accounts', async () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })

        await waitFor(() => {
            const select = screen.getByTestId('calc-account-select') as HTMLSelectElement
            expect(select).toBeInTheDocument()
            // "Manual" + "All Accounts" + 2 individual accounts = 4 options
            expect(select.options.length).toBe(4)
            // Default should be "All Accounts" per 06h L80
            expect(select.value).toBe('__ALL__')
        })
    })

    it('AC-1b: calculator opens with portfolio total pre-filled in account size', async () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })

        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            // 50000 + 25000 = 75000 (portfolio total from default All Accounts)
            expect(parseFloat(sizeInput.value)).toBe(75000)
        })
    })

    it('AC-2: selecting account auto-fills balance from latest_balance', async () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })

        // Wait for accounts to load (default __ALL__ fills portfolio total)
        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            expect(parseFloat(sizeInput.value)).toBe(75000)
        })

        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: 'ACC001' } })

        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            expect(parseFloat(sizeInput.value)).toBe(50000)
        })
    })

    it('AC-3: switching from individual account to All Accounts fills portfolio total', async () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })

        // Wait for accounts to load (default __ALL__ fills portfolio total)
        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            expect(parseFloat(sizeInput.value)).toBe(75000)
        })

        // First select individual account → balance changes to 50000
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: 'ACC001' } })
        await waitFor(() => {
            expect((screen.getByTestId('calc-account-size') as HTMLInputElement).value).toBe('50000')
        })

        // Switch back to All Accounts → should restore portfolio total 75000
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: '__ALL__' } })
        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            expect(parseFloat(sizeInput.value)).toBe(75000)
        })
    })

    it('AC-3b: zero-total portfolio defaults to 0 account size', async () => {
        // Override mock to return accounts with zero balances
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/accounts')) {
                return Promise.resolve([
                    { account_id: 'ZERO1', name: 'Empty', account_type: 'broker', latest_balance: 0, latest_balance_date: null },
                ])
            }
            return Promise.resolve({})
        })

        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })

        // Default is __ALL__, portfolio total = 0, so account size should be 0
        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            expect(parseFloat(sizeInput.value)).toBe(0)
        })

        // Verify the selector shows All Accounts as default
        const select = screen.getByTestId('calc-account-select') as HTMLSelectElement
        expect(select.value).toBe('__ALL__')
    })

    it('AC-4: user can manually override balance after auto-fill', async () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })

        // Wait for accounts to load (default __ALL__ fills portfolio total)
        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            expect(parseFloat(sizeInput.value)).toBe(75000)
        })

        // Select account to auto-fill
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: 'ACC001' } })

        await waitFor(() => {
            expect((screen.getByTestId('calc-account-size') as HTMLInputElement).value).toBe('50000')
        })

        // Manual override
        fireEvent.change(screen.getByTestId('calc-account-size'), { target: { value: '60000' } })
        expect((screen.getByTestId('calc-account-size') as HTMLInputElement).value).toBe('60000')
    })

})

// ─── MEU-70a Sub-MEU C: Calculator Write-Back + Readonly position_size ────

describe('MEU-70a Sub-MEU C: AC-20 — Readonly position_size display', () => {
    const PLAN_WITH_POSITION = {
        ...MOCK_PLANS[0],
        shares_planned: 100,
        position_size: 19000.0, // 100 shares × $190 entry
    }

    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([PLAN_WITH_POSITION])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
    })

    it('should display position_size as readonly when plan has a value', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            const posField = screen.getByTestId('plan-position-size')
            expect(posField).toBeInTheDocument()
            expect(posField).toHaveAttribute('readonly')
            // Should show formatted value $19,000.00
            expect(posField).toHaveValue('$19,000.00')
        })
    })

    it('should show "—" when position_size is null', async () => {
        const planNoPosition = { ...MOCK_PLANS[0], shares_planned: null, position_size: null }
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve([planNoPosition])
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            const posField = screen.getByTestId('plan-position-size')
            expect(posField).toHaveValue('—')
        })
    })

    it('should keep shares_planned editable (no regression from MEU-70b)', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => {
            const sharesInput = screen.getByTestId('plan-shares-planned')
            expect(sharesInput).not.toHaveAttribute('readonly')
            expect(sharesInput).toHaveValue(100)
        })
    })
})

describe('MEU-70a Sub-MEU C: AC-21 — Apply to Plan button in Calculator', () => {
    it('should render "Apply to Plan" button in calculator results section', () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        expect(screen.getByTestId('calc-apply-to-plan-btn')).toBeInTheDocument()
    })

    it('should dispatch zorivest:calculator-apply event with shares and position_size on click', () => {
        const spy = vi.fn()
        window.addEventListener('zorivest:calculator-apply', spy)

        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })
        // Set up calculator inputs: $100k, 1% risk, entry=100, stop=98, target=106
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: '' } })
        fireEvent.change(screen.getByTestId('calc-account-size'), { target: { value: '100000' } })
        fireEvent.change(screen.getByTestId('calc-entry-price'), { target: { value: '100' } })
        fireEvent.change(screen.getByTestId('calc-stop-price'), { target: { value: '98' } })
        fireEvent.change(screen.getByTestId('calc-target-price'), { target: { value: '106' } })

        fireEvent.click(screen.getByTestId('calc-apply-to-plan-btn'))

        expect(spy).toHaveBeenCalledTimes(1)
        const event = spy.mock.calls[0][0] as CustomEvent
        // shares = floor(1000/2) = 500, positionValue = 500 * 100 = 50000
        expect(event.detail).toEqual({
            shares_planned: 500,
            position_size: 50000,
        })

        window.removeEventListener('zorivest:calculator-apply', spy)
    })
})

describe('MEU-70a Sub-MEU C: AC-22 — TradePlanPage calculator-apply listener', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
    })

    it('should populate shares_planned and position_size when calculator-apply fires', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument())
        // Open a plan to edit
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('plan-shares-planned')).toBeInTheDocument())

        // Simulate calculator-apply event
        act(() => {
            window.dispatchEvent(new CustomEvent('zorivest:calculator-apply', {
                detail: { shares_planned: 250, position_size: 47500 },
            }))
        })

        await waitFor(() => {
            // shares_planned should be populated (editable field)
            const sharesInput = screen.getByTestId('plan-shares-planned') as HTMLInputElement
            expect(parseInt(sharesInput.value)).toBe(250)
            // position_size should be populated (readonly field)
            const posField = screen.getByTestId('plan-position-size') as HTMLInputElement
            expect(posField.value).toBe('$47,500.00')
        })
    })

    it('should ignore calculator-apply event with no payload', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('plan-shares-planned')).toBeInTheDocument())

        const sharesBefore = (screen.getByTestId('plan-shares-planned') as HTMLInputElement).value

        // Fire event with no detail
        act(() => {
            window.dispatchEvent(new CustomEvent('zorivest:calculator-apply', { detail: null }))
        })

        // shares_planned should be unchanged
        const sharesAfter = (screen.getByTestId('plan-shares-planned') as HTMLInputElement).value
        expect(sharesAfter).toBe(sharesBefore)
    })

    it('should ignore calculator-apply when no plan is being edited', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument())
        // Do NOT click a plan card — no plan selected

        // This should not throw or crash
        act(() => {
            window.dispatchEvent(new CustomEvent('zorivest:calculator-apply', {
                detail: { shares_planned: 100, position_size: 19000 },
            }))
        })

        // Page should still be intact
        expect(screen.getByTestId('trade-plan-page')).toBeInTheDocument()
    })
})

describe('MEU-70a Sub-MEU C: AC-23 — Applied values in PUT save', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PUT') return Promise.resolve({ id: 1 })
            if (url.includes('/api/v1/trade-plans')) return Promise.resolve(MOCK_PLANS)
            if (url.includes('/api/v1/accounts')) return Promise.resolve([])
            return Promise.resolve({})
        })
    })

    it('should include position_size in PUT payload after calculator-apply', async () => {
        render(<TradePlanPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument())
        fireEvent.click(screen.getByTestId('plan-card-1'))
        await waitFor(() => expect(screen.getByTestId('plan-shares-planned')).toBeInTheDocument())

        // Apply calculator result
        act(() => {
            window.dispatchEvent(new CustomEvent('zorivest:calculator-apply', {
                detail: { shares_planned: 300, position_size: 57000 },
            }))
        })

        // Save
        fireEvent.click(screen.getByTestId('plan-save-btn'))
        await waitFor(() => {
            const putCalls = mockApiFetch.mock.calls.filter(
                (c: unknown[]) =>
                    (c[0] as string).includes('/api/v1/trade-plans/') &&
                    (c[1] as RequestInit)?.method === 'PUT',
            )
            expect(putCalls.length).toBeGreaterThanOrEqual(1)
            const body = JSON.parse((putCalls[0][1] as RequestInit).body as string)
            expect(body.shares_planned).toBe(300)
            expect(body.position_size).toBe(57000)
        })
    })
})

// ─── MEU-71b (continued): Calculator Account Integration ──────────────────

describe('MEU-71b (continued): Calculator Account Dropdown', () => {
    const MOCK_ACCOUNTS_ENRICHED = [
        {
            account_id: 'ACC001',
            name: 'Main Trading',
            account_type: 'broker',
            latest_balance: 50000.0,
            latest_balance_date: '2025-03-15T00:00:00',
        },
        {
            account_id: 'ACC002',
            name: 'IRA',
            account_type: 'retirement',
            latest_balance: 25000.0,
            latest_balance_date: '2025-03-10T00:00:00',
        },
    ]

    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/api/v1/accounts')) return Promise.resolve(MOCK_ACCOUNTS_ENRICHED)
            return Promise.resolve({})
        })
    })

    it('AC-5: changing account reverts balance to API value', async () => {
        render(<PositionCalculatorModal isOpen={true} onClose={vi.fn()} />, { wrapper: createWrapper() })

        // Wait for accounts to load (default __ALL__ fills portfolio total)
        await waitFor(() => {
            const sizeInput = screen.getByTestId('calc-account-size') as HTMLInputElement
            expect(parseFloat(sizeInput.value)).toBe(75000)
        })

        // Select ACC001 → 50000
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: 'ACC001' } })
        await waitFor(() => {
            expect((screen.getByTestId('calc-account-size') as HTMLInputElement).value).toBe('50000')
        })

        // Manual override to 60000
        fireEvent.change(screen.getByTestId('calc-account-size'), { target: { value: '60000' } })

        // Change to ACC002 → should revert to 25000 (not keep 60000)
        fireEvent.change(screen.getByTestId('calc-account-select'), { target: { value: 'ACC002' } })
        await waitFor(() => {
            expect((screen.getByTestId('calc-account-size') as HTMLInputElement).value).toBe('25000')
        })
    })
})

// ─── Bug-Fix: WatchlistTable renders market data from API quote shape ──────

import WatchlistTable, { type MarketQuote as WTMarketQuote } from '../WatchlistTable'

describe('Bug-Fix: WatchlistTable renders market data', () => {
    const items = [
        { id: 1, watchlist_id: 1, ticker: 'AAPL', added_at: '2026-03-20T10:00:00Z', notes: 'Watch for earnings' },
        { id: 2, watchlist_id: 1, ticker: 'MSFT', added_at: '2026-03-20T10:00:00Z', notes: '' },
    ]

    // This is what the API returns after the fix — price maps to last_price
    const quotes: Record<string, WTMarketQuote> = {
        AAPL: { last_price: 190.50, change: 2.50, change_pct: 1.33, volume: 45300000, symbol: 'AAPL' },
        MSFT: { last_price: 420.00, change: -3.20, change_pct: -0.76, volume: 22100000, symbol: 'MSFT' },
    }

    it('should display last_price when quote data is available', () => {
        render(
            <WatchlistTable items={items} quotes={quotes} colorblind={false} />,
            { wrapper: createWrapper() },
        )
        expect(screen.getByTestId('watchlist-row-AAPL')).toHaveTextContent('190.50')
        expect(screen.getByTestId('watchlist-row-MSFT')).toHaveTextContent('420.00')
    })

    it('should display change values with arrows', () => {
        render(
            <WatchlistTable items={items} quotes={quotes} colorblind={false} />,
            { wrapper: createWrapper() },
        )
        // AAPL has positive change → ▲
        const aaplRow = screen.getByTestId('watchlist-row-AAPL')
        expect(aaplRow).toHaveTextContent('▲')
        expect(aaplRow).toHaveTextContent('+2.50')
        // MSFT has negative change → ▼
        const msftRow = screen.getByTestId('watchlist-row-MSFT')
        expect(msftRow).toHaveTextContent('▼')
    })

    it('should display volume formatted', () => {
        render(
            <WatchlistTable items={items} quotes={quotes} colorblind={false} />,
            { wrapper: createWrapper() },
        )
        expect(screen.getByTestId('watchlist-row-AAPL')).toHaveTextContent('45.3M')
    })

    it('should show "—" when quote is null (fallback)', () => {
        render(
            <WatchlistTable items={items} quotes={{ AAPL: null, MSFT: null }} colorblind={false} />,
            { wrapper: createWrapper() },
        )
        // All data cells should show em-dash
        const aaplRow = screen.getByTestId('watchlist-row-AAPL')
        // Price, Chg $, Chg %, Volume should all show "—"
        const cells = aaplRow.querySelectorAll('td.wl-num')
        cells.forEach((cell) => {
            expect(cell.textContent).toBe('—')
        })
    })
})

// ─── Bug-Fix: Colorblind toggle applies to table data cells ─────────────────

describe('Bug-Fix: Colorblind toggle changes cell colors', () => {
    const items = [
        { id: 1, watchlist_id: 1, ticker: 'AAPL', added_at: '2026-03-20T10:00:00Z', notes: '' },
    ]

    const quotesUp: Record<string, WTMarketQuote> = {
        AAPL: { last_price: 190.50, change: 2.50, change_pct: 1.33, volume: 45300000, symbol: 'AAPL' },
    }

    it('should use green (#26A69A) for positive change in normal mode', () => {
        render(
            <WatchlistTable items={items} quotes={quotesUp} colorblind={false} />,
            { wrapper: createWrapper() },
        )
        const row = screen.getByTestId('watchlist-row-AAPL')
        const changeCells = row.querySelectorAll('td.wl-num')
        // Chg $ cell (index 1) should have green color
        expect((changeCells[1] as HTMLElement).style.color).toBe('rgb(38, 166, 154)')
    })

    it('should use blue (#2962FF) for positive change in colorblind mode', () => {
        render(
            <WatchlistTable items={items} quotes={quotesUp} colorblind={true} />,
            { wrapper: createWrapper() },
        )
        const row = screen.getByTestId('watchlist-row-AAPL')
        const changeCells = row.querySelectorAll('td.wl-num')
        // Chg $ cell (index 1) should have blue color
        expect((changeCells[1] as HTMLElement).style.color).toBe('rgb(41, 98, 255)')
    })
})

// ─── Bug-Fix: WatchlistTable inline notes editing ───────────────────────────

describe('Bug-Fix: WatchlistTable inline notes editing', () => {
    const items = [
        { id: 1, watchlist_id: 1, ticker: 'AAPL', added_at: '2026-03-20T10:00:00Z', notes: 'Watch for earnings' },
        { id: 2, watchlist_id: 1, ticker: 'MSFT', added_at: '2026-03-20T10:00:00Z', notes: '' },
    ]

    it('should display actual notes text (not icon) for items with notes', () => {
        const mockUpdateNotes = vi.fn()
        render(
            <WatchlistTable items={items} quotes={{}} colorblind={false} onUpdateNotes={mockUpdateNotes} />,
            { wrapper: createWrapper() },
        )
        const notesEl = screen.getByTestId('edit-notes-AAPL')
        expect(notesEl).toBeInTheDocument()
        expect(notesEl.textContent).toBe('Watch for earnings')
        expect(notesEl.className).toContain('wl-notes-text')
    })

    it('should display "—" placeholder for items without notes', () => {
        const mockUpdateNotes = vi.fn()
        render(
            <WatchlistTable items={items} quotes={{}} colorblind={false} onUpdateNotes={mockUpdateNotes} />,
            { wrapper: createWrapper() },
        )
        const placeholderEl = screen.getByTestId('edit-notes-MSFT')
        expect(placeholderEl.textContent).toBe('—')
        expect(placeholderEl.className).toContain('wl-notes-placeholder')
    })

    it('should open inline editor when clicking notes text', () => {
        const mockUpdateNotes = vi.fn()
        render(
            <WatchlistTable items={items} quotes={{}} colorblind={false} onUpdateNotes={mockUpdateNotes} />,
            { wrapper: createWrapper() },
        )
        fireEvent.click(screen.getByTestId('edit-notes-AAPL'))
        expect(screen.getByTestId('notes-input-AAPL')).toBeInTheDocument()
    })

    it('should show inline input pre-filled with existing notes', () => {
        const mockUpdateNotes = vi.fn()
        render(
            <WatchlistTable items={items} quotes={{}} colorblind={false} onUpdateNotes={mockUpdateNotes} />,
            { wrapper: createWrapper() },
        )
        fireEvent.click(screen.getByTestId('edit-notes-AAPL'))
        const input = screen.getByTestId('notes-input-AAPL') as HTMLInputElement
        expect(input.value).toBe('Watch for earnings')
    })

    it('should call onUpdateNotes when saving edited notes', async () => {
        const mockUpdateNotes = vi.fn()
        render(
            <WatchlistTable items={items} quotes={{}} colorblind={false} onUpdateNotes={mockUpdateNotes} />,
            { wrapper: createWrapper() },
        )
        fireEvent.click(screen.getByTestId('edit-notes-AAPL'))
        const input = screen.getByTestId('notes-input-AAPL')
        fireEvent.change(input, { target: { value: 'Updated earnings note' } })
        fireEvent.click(screen.getByTestId('save-notes-AAPL'))
        expect(mockUpdateNotes).toHaveBeenCalledWith('AAPL', 'Updated earnings note')
    })

    it('should allow clicking placeholder to add notes for items without notes', () => {
        const mockUpdateNotes = vi.fn()
        render(
            <WatchlistTable items={items} quotes={{}} colorblind={false} onUpdateNotes={mockUpdateNotes} />,
            { wrapper: createWrapper() },
        )
        // MSFT has no notes — click placeholder to start editing
        const placeholder = screen.getByTestId('edit-notes-MSFT')
        expect(placeholder).toBeInTheDocument()
        fireEvent.click(placeholder)
        expect(screen.getByTestId('notes-input-MSFT')).toBeInTheDocument()
    })
})

// ─── Redesign Coverage: Freshness rendering ─────────────────────────────────

describe('Redesign: WatchlistTable freshness rendering', () => {
    const items = [
        { id: 1, watchlist_id: 1, ticker: 'AAPL', added_at: '2026-03-20T10:00:00Z', notes: '' },
    ]
    const quotes: Record<string, WTMarketQuote> = {
        AAPL: { last_price: 190.50, change: 2.50, change_pct: 1.33, volume: 45300000, symbol: 'AAPL' },
    }

    it('should render freshness text from lastQuoteTime prop', () => {
        // Use a very recent timestamp so formatFreshness returns "Just now"
        const recentTime = new Date().toISOString()
        render(
            <WatchlistTable
                items={items}
                quotes={quotes}
                colorblind={false}
                lastQuoteTime={recentTime}
            />,
            { wrapper: createWrapper() },
        )
        const freshness = screen.getByTestId('watchlist-freshness')
        expect(freshness).toBeInTheDocument()
        expect(freshness.textContent).toBe('Just now')
    })

    it('should show "No data" when lastQuoteTime is null', () => {
        render(
            <WatchlistTable
                items={items}
                quotes={quotes}
                colorblind={false}
                lastQuoteTime={null}
            />,
            { wrapper: createWrapper() },
        )
        const freshness = screen.getByTestId('watchlist-freshness')
        expect(freshness).toBeInTheDocument()
        expect(freshness.textContent).toBe('No data')
    })
})

// ─── Redesign Coverage: Colorblind toggle persistence ───────────────────────

describe('Redesign: Colorblind toggle persistence via Settings API', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        let storedColorblind = false
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            // Watchlist data
            if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
            if (url === '/api/v1/watchlists/1') return Promise.resolve(MOCK_WATCHLISTS[0])
            // Settings: PUT colorblind mode — update stored value
            if (url === '/api/v1/settings/ui.watchlist.colorblind_mode' && opts?.method === 'PUT') {
                const body = JSON.parse(opts.body as string)
                storedColorblind = body.value === true || body.value === 'true'
                return Promise.resolve({ value: storedColorblind })
            }
            // Settings: GET colorblind mode — return stored value
            if (url === '/api/v1/settings/ui.watchlist.colorblind_mode') {
                return Promise.resolve({ value: storedColorblind })
            }
            // Market data quotes
            if (url.includes('/api/v1/market-data/quote')) {
                return Promise.resolve({ ticker: 'AAPL', price: 190.50, change: 2.50, change_pct: 1.33, volume: 45300000, provider: 'yahoo', timestamp: new Date().toISOString() })
            }
            return Promise.resolve({})
        })
    })

    it('should render toggle showing "Colorblind: Off" initially', async () => {
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('watchlist-card-1'))
        await waitFor(() => {
            const toggle = screen.getByTestId('colorblind-toggle')
            expect(toggle).toBeInTheDocument()
            expect(toggle.textContent).toContain('Colorblind: Off')
        })
    })

    it('should call Settings API PUT when toggle is clicked', async () => {
        render(<WatchlistPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('watchlist-card-1'))
        await waitFor(() => {
            expect(screen.getByTestId('colorblind-toggle')).toBeInTheDocument()
        })

        // Click toggle to enable colorblind mode
        fireEvent.click(screen.getByTestId('colorblind-toggle'))

        // Verify PUT was called with the new value
        await waitFor(() => {
            const putCalls = mockApiFetch.mock.calls.filter(
                (call: unknown[]) =>
                    call[0] === '/api/v1/settings/ui.watchlist.colorblind_mode' &&
                    (call[1] as Record<string, unknown>)?.method === 'PUT',
            )
            expect(putCalls.length).toBeGreaterThanOrEqual(1)
        })

        // Verify toggle text changed
        await waitFor(() => {
            const toggle = screen.getByTestId('colorblind-toggle')
            expect(toggle.textContent).toContain('Colorblind: On')
        })
    })
})

// ─── Redesign Coverage: Quote polling cadence ───────────────────────────────

describe('Redesign: Quote polling cadence (5s interval)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('should fire additional quote fetches after 5s polling interval', async () => {
        vi.useFakeTimers({ shouldAdvanceTime: true })

        let quoteFetchCount = 0
        mockApiFetch.mockImplementation((url: string) => {
            if (url === '/api/v1/watchlists/') return Promise.resolve(MOCK_WATCHLISTS)
            if (url === '/api/v1/watchlists/1') return Promise.resolve(MOCK_WATCHLISTS[0])
            if (url.includes('/api/v1/settings/')) return Promise.resolve({ value: false })
            if (url.includes('/api/v1/market-data/quote')) {
                quoteFetchCount++
                return Promise.resolve({
                    ticker: 'AAPL', price: 190.50, change: 2.50,
                    change_pct: 1.33, volume: 45300000, provider: 'yahoo',
                    timestamp: new Date().toISOString(),
                })
            }
            return Promise.resolve({})
        })

        render(<WatchlistPage />, { wrapper: createWrapper() })

        // Select the watchlist to trigger quote fetching
        await act(async () => {
            await vi.advanceTimersByTimeAsync(100)
        })
        await waitFor(() => {
            expect(screen.getByText('Tech Stocks')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('watchlist-card-1'))

        // Wait for initial staggered fetches (4000 + jitter ms)
        await act(async () => {
            await vi.advanceTimersByTimeAsync(5500)
        })

        const initialCount = quoteFetchCount
        expect(initialCount).toBeGreaterThan(0) // Initial fetch completed

        // Advance by 6s to trigger at least one polling cycle (5s interval + jitter)
        await act(async () => {
            await vi.advanceTimersByTimeAsync(6000)
        })

        // Verify additional fetches were fired by the polling interval
        expect(quoteFetchCount).toBeGreaterThan(initialCount)

        vi.useRealTimers()
    })
})
