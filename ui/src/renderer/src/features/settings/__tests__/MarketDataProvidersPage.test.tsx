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
        display_name: null,
        is_enabled: true,
        has_api_key: true,
        rate_limit: 5,
        timeout: 30,
        last_test_status: 'success',
        signup_url: null,
    },
    {
        provider_name: 'Polygon.io',
        display_name: 'Massive',
        is_enabled: false,
        has_api_key: false,
        rate_limit: 10,
        timeout: 30,
        last_test_status: null,
        signup_url: 'https://massive.com/pricing',
    },
    {
        provider_name: 'Alpaca',
        display_name: null,
        is_enabled: false,
        has_api_key: false,
        rate_limit: 200,
        timeout: 30,
        last_test_status: null,
        signup_url: null,
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
            expect(screen.getByText('Massive')).toBeInTheDocument()
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
        await waitFor(() => expect(screen.getByText('Massive')).toBeInTheDocument())

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

    // ── Dirty-state guard tests (G22/G23) ─────────────────────────────────

    // G22-1: Save button shows "Save Changes" (no bullet) when form is clean
    it('G22-1: save button shows "Save Changes" when form is clean', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])

        await waitFor(() => {
            const saveBtn = screen.getByTestId('provider-save-btn')
            expect(saveBtn).toHaveTextContent('Save Changes')
            expect(saveBtn.textContent).not.toContain('•')
        })
    })

    // G22-2: Save button shows "Save Changes •" and btn-save-dirty class when form is dirty
    it('G22-2: save button shows dirty indicators when form value changed', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-save-btn')).toBeInTheDocument())

        // Change rate limit to make form dirty
        const rateLimitInput = screen.getByTestId('provider-rate-limit-input')
        fireEvent.change(rateLimitInput, { target: { value: '99' } })

        await waitFor(() => {
            const saveBtn = screen.getByTestId('provider-save-btn')
            expect(saveBtn.textContent).toContain('•')
            expect(saveBtn.className).toContain('btn-save-dirty')
        })
    })

    // G22-3: Entering an API key makes form dirty
    it('G22-3: typing API key makes save button dirty', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-api-key-input')).toBeInTheDocument())

        const apiKeyInput = screen.getByTestId('provider-api-key-input')
        fireEvent.change(apiKeyInput, { target: { value: 'new-key-123' } })

        await waitFor(() => {
            const saveBtn = screen.getByTestId('provider-save-btn')
            expect(saveBtn.className).toContain('btn-save-dirty')
            expect(saveBtn.textContent).toContain('•')
        })
    })

    // G22-4: Guard modal appears when switching providers with dirty form
    it('G22-4: guard modal appears on dirty provider switch', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        // Select Alpha Vantage
        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-save-btn')).toBeInTheDocument())

        // Make form dirty
        const rateLimitInput = screen.getByTestId('provider-rate-limit-input')
        fireEvent.change(rateLimitInput, { target: { value: '99' } })

        // Try to switch to Polygon.io
        fireEvent.click(screen.getAllByTestId('provider-item')[1])

        // Guard modal should appear (portaled to body)
        await waitFor(() => {
            expect(screen.getByRole('alertdialog')).toBeInTheDocument()
        })
    })

    // G22-5: Discard in guard modal navigates to new provider
    it('G22-5: discard button in modal navigates to new provider', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        // Select Alpha Vantage and make dirty
        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-rate-limit-input')).toBeInTheDocument())
        fireEvent.change(screen.getByTestId('provider-rate-limit-input'), { target: { value: '99' } })

        // Switch provider
        fireEvent.click(screen.getAllByTestId('provider-item')[1])
        await waitFor(() => expect(screen.getByRole('alertdialog')).toBeInTheDocument())

        // Click discard
        const discardBtn = screen.getByRole('button', { name: /discard/i })
        fireEvent.click(discardBtn)

        // Modal closes and Polygon.io detail should load (form resets)
        await waitFor(() => {
            expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
        })
    })

    // G22-6: Keep Editing in guard modal dismisses and stays on current provider
    it('G22-6: keep editing button dismisses modal', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        // Select Alpha Vantage and make dirty
        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-rate-limit-input')).toBeInTheDocument())
        fireEvent.change(screen.getByTestId('provider-rate-limit-input'), { target: { value: '99' } })

        // Switch provider
        fireEvent.click(screen.getAllByTestId('provider-item')[1])
        await waitFor(() => expect(screen.getByRole('alertdialog')).toBeInTheDocument())

        // Click Keep Editing
        const keepBtn = screen.getByRole('button', { name: /keep editing/i })
        fireEvent.click(keepBtn)

        // Modal closes, dirty value still present
        await waitFor(() => {
            expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
            // Rate limit should still be the dirty value
            const input = screen.getByTestId('provider-rate-limit-input') as HTMLInputElement
            expect(input.value).toBe('99')
        })
    })

    // G22-7: "Disabled" label shown for disabled providers
    it('G22-7: disabled providers show "Disabled" label', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        // Polygon.io and Alpaca are is_enabled=false
        expect(screen.getAllByText('Disabled')).toHaveLength(2)
    })

    // G22-8: Clean provider switch does not trigger modal
    it('G22-8: clean provider switch does not show guard modal', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        // Select Alpha Vantage (clean)
        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-save-btn')).toBeInTheDocument())

        // Switch to Polygon.io without making changes
        fireEvent.click(screen.getAllByTestId('provider-item')[1])

        // No modal should appear
        await waitFor(() => {
            expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
        })
    })

    // G22-9: Save clears api_key field → isDirty returns to false
    it('G22-9: save resets dirty state by clearing api_key', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PUT') return Promise.resolve({})
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })

        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpha Vantage')).toBeInTheDocument())

        // Select provider and enter an API key (makes form dirty)
        fireEvent.click(screen.getAllByTestId('provider-item')[0])
        await waitFor(() => expect(screen.getByTestId('provider-api-key-input')).toBeInTheDocument())

        const apiKeyInput = screen.getByTestId('provider-api-key-input')
        fireEvent.change(apiKeyInput, { target: { value: 'test-key-123' } })

        // Verify form is dirty
        await waitFor(() => {
            const saveBtn = screen.getByTestId('provider-save-btn')
            expect(saveBtn.textContent).toContain('•')
            expect(saveBtn.className).toContain('btn-save-dirty')
        })

        // Click save
        fireEvent.click(screen.getByTestId('provider-save-btn'))

        // After save, form should no longer be dirty
        await waitFor(() => {
            const saveBtn = screen.getByTestId('provider-save-btn')
            expect(saveBtn.textContent).not.toContain('•')
            expect(saveBtn.className).not.toContain('btn-save-dirty')
        })

        // API key input should be cleared
        await waitFor(() => {
            const input = screen.getByTestId('provider-api-key-input') as HTMLInputElement
            expect(input.value).toBe('')
        })
    })

    // G22-10: Save also clears api_secret for dual-auth (Alpaca)
    it('G22-10: save clears api_secret for dual-auth providers', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PUT') return Promise.resolve({})
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })

        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByText('Alpaca')).toBeInTheDocument())

        // Select Alpaca (dual-auth) and enter credentials
        fireEvent.click(screen.getAllByTestId('provider-item')[2])
        await waitFor(() => expect(screen.getByTestId('provider-api-key-input')).toBeInTheDocument())

        fireEvent.change(screen.getByTestId('provider-api-key-input'), {
            target: { value: 'alpaca-key' },
        })
        fireEvent.change(screen.getByTestId('provider-api-secret-input'), {
            target: { value: 'alpaca-secret' },
        })

        // Verify form is dirty
        await waitFor(() => {
            const saveBtn = screen.getByTestId('provider-save-btn')
            expect(saveBtn.className).toContain('btn-save-dirty')
        })

        // Save
        fireEvent.click(screen.getByTestId('provider-save-btn'))

        // Both fields should be cleared, form should be clean
        await waitFor(() => {
            const saveBtn = screen.getByTestId('provider-save-btn')
            expect(saveBtn.className).not.toContain('btn-save-dirty')
        })

        await waitFor(() => {
            const keyInput = screen.getByTestId('provider-api-key-input') as HTMLInputElement
            const secretInput = screen.getByTestId('provider-api-secret-input') as HTMLInputElement
            expect(keyInput.value).toBe('')
            expect(secretInput.value).toBe('')
        })
    })
})

// ═══════════════════════════════════════════════════════════════════════════
// Corrections: Finding 4 — display_name Rendering Regression
// ═══════════════════════════════════════════════════════════════════════════

describe('display_name rendering', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url.includes('/market-data/providers')) return Promise.resolve(MOCK_PROVIDERS)
            return Promise.resolve({})
        })
    })

    it('renders display_name (Massive) in sidebar instead of internal key (Polygon.io)', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })

        await waitFor(() => {
            const items = screen.getAllByTestId('provider-item')
            expect(items.length).toBeGreaterThanOrEqual(3)
        })

        // The sidebar should show "Massive", not "Polygon.io"
        const providerItems = screen.getAllByTestId('provider-item')
        const polygonItem = providerItems.find((el) => el.textContent?.includes('Massive'))
        expect(polygonItem).toBeDefined()

        // "Polygon.io" should NOT appear as visible text in sidebar items
        const polygonRawItem = providerItems.find((el) =>
            el.querySelector('.truncate')?.textContent === 'Polygon.io'
        )
        expect(polygonRawItem).toBeUndefined()
    })

    it('renders provider_name when display_name is null', async () => {
        render(<MarketDataProvidersPage />, { wrapper: createWrapper() })

        await waitFor(() => {
            const items = screen.getAllByTestId('provider-item')
            expect(items.length).toBeGreaterThanOrEqual(3)
        })

        // Alpha Vantage has display_name=null → should show "Alpha Vantage"
        const providerItems = screen.getAllByTestId('provider-item')
        const avItem = providerItems.find((el) => el.textContent?.includes('Alpha Vantage'))
        expect(avItem).toBeDefined()
    })
})
