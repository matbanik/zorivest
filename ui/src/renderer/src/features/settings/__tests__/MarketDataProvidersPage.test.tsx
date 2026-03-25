import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockApiFetch = vi.fn()
vi.mock('@/lib/api', () => ({
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

const mockSetStatus = vi.fn()
vi.mock('@/hooks/useStatusBar', () => ({
    useStatusBar: () => ({ setStatus: mockSetStatus }),
}))

import { MarketDataProvidersPage, type ProviderStatus } from '../MarketDataProvidersPage'

// ── Helpers ───────────────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    return function Wrapper({ children }: { children: ReactNode }) {
        return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    }
}

// ── Test Data ─────────────────────────────────────────────────────────────────

const MOCK_PROVIDERS: ProviderStatus[] = [
    {
        provider_name: 'Alpha Vantage',
        is_enabled: true,
        has_api_key: true,
        rate_limit: 5,
        timeout: 30,
        last_test_status: 'success',
    },
    {
        provider_name: 'Polygon.io',
        is_enabled: false,
        has_api_key: false,
        rate_limit: 10,
        timeout: 30,
        last_test_status: null,
    },
    {
        provider_name: 'Alpaca',
        is_enabled: false,
        has_api_key: false,
        rate_limit: 200,
        timeout: 30,
        last_test_status: null,
    },
]

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('MEU-65: MarketDataProvidersPage', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })
    })

    // AC-1: renders root testid
    it('AC-1: renders page with data-testid', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('market-data-providers')).toBeInTheDocument()
        })
    })

    // AC-1: renders provider list panel
    it('AC-1: renders provider list on load', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('provider-list')).toBeInTheDocument()
            expect(screen.getByText('Alpha Vantage')).toBeInTheDocument()
            expect(screen.getByText('Polygon.io')).toBeInTheDocument()
        })
    })

    // AC-2: shows detail panel after clicking provider
    it('AC-2: opens detail panel on provider click', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        const items = screen.getAllByTestId('provider-item')
        fireEvent.click(items[0])

        await waitFor(() => {
            expect(screen.getByTestId('provider-detail')).toBeInTheDocument()
        })
    })

    // AC-3: shows API key input in detail form
    it('AC-3: detail panel has API key input', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])

        await waitFor(() => {
            expect(screen.getByTestId('provider-api-key-input')).toBeInTheDocument()
        })
    })

    // AC-7: shows rate limit and timeout inputs
    it('AC-7: detail panel has rate limit and timeout inputs', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])

        await waitFor(() => {
            expect(screen.getByTestId('provider-rate-limit-input')).toBeInTheDocument()
            expect(screen.getByTestId('provider-timeout-input')).toBeInTheDocument()
        })
    })

    // AC-8: Save Changes calls PUT
    it('AC-8: Save Changes calls PUT /market-data/providers/{name}', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PUT') return Promise.resolve({})
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })

        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-save-btn')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('provider-save-btn'))

        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/market-data/providers/Alpha Vantage',
                expect.objectContaining({ method: 'PUT' }),
            )
        })
    })

    // AC-8: setStatus called with 'Saved' on success
    it('AC-8: setStatus called on save success', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PUT') return Promise.resolve({})
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })

        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-save-btn')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('provider-save-btn'))

        await waitFor(() => {
            expect(mockSetStatus).toHaveBeenCalledWith('Saved')
        })
    })

    // AC-12: setStatus called on save error
    it('AC-12: setStatus called on save error', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PUT') return Promise.reject(new Error('Network error'))
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })

        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-save-btn')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('provider-save-btn'))

        await waitFor(() => {
            expect(mockSetStatus).toHaveBeenCalledWith(
                expect.stringContaining('Error:'),
            )
        })
    })

    // AC-4: Test Connection calls POST
    it('AC-4: Test Connection calls POST /market-data/providers/{name}/test', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'POST' && url.includes('/test')) {
                return Promise.resolve({ success: true, message: 'OK' })
            }
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })

        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-test-btn')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('provider-test-btn'))

        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                expect.stringContaining('/test'),
                expect.objectContaining({ method: 'POST' }),
            )
        })
    })

    // AC-9: Remove Key disabled when has_api_key is false (G2 guard)
    it('AC-9: Remove Key button disabled when no API key (G2)', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Polygon.io')).toBeInTheDocument())

        // Click Polygon.io (has_api_key = false)
        const items = screen.getAllByTestId('provider-item')
        fireEvent.click(items[1])

        await waitFor(() => {
            const btn = screen.getByTestId('provider-remove-key-btn')
            expect(btn).toBeDisabled()
        })
    })

    // AC-9: Remove Key enabled when has_api_key is true
    it('AC-9: Remove Key enabled when API key exists', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        // Click Alpha Vantage (has_api_key = true)
        const items = screen.getAllByTestId('provider-item')
        fireEvent.click(items[0])

        await waitFor(() => {
            const btn = screen.getByTestId('provider-remove-key-btn')
            expect(btn).not.toBeDisabled()
        })
    })

    // AC-5: Test All Connections renders button
    it('AC-5: Test All Connections button present', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('provider-test-all-btn')).toBeInTheDocument()
        })
    })

    // AC-13: Alpaca shows API secret field (dual-auth)
    it('AC-13: Alpaca shows api_secret field for dual-auth', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpaca')).toBeInTheDocument())

        const items = screen.getAllByTestId('provider-item')
        // Alpaca is the 3rd provider (index 2)
        fireEvent.click(items[2])

        await waitFor(() => {
            expect(screen.getByTestId('provider-api-secret-input')).toBeInTheDocument()
        })
    })

    // AC-13: non-dual-auth provider does NOT show api_secret field
    it('AC-13: non-Alpaca provider hides api_secret field', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])

        await waitFor(() => {
            expect(screen.queryByTestId('provider-api-secret-input')).not.toBeInTheDocument()
        })
    })

    // AC-14: Provider info card present
    it('AC-14: provider info card shows defaults', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])

        await waitFor(() => {
            // Default rate_limit from mock = 5
            expect(screen.getByText(/Default rate limit: 5/)).toBeInTheDocument()
        })
    })
})
