import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockApiFetch = vi.fn()
vi.mock('@/lib/api', () => ({
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

const mockSetStatus = vi.fn()
vi.mock('@/hooks/useStatusBar', () => ({
    useStatusBar: () => ({ setStatus: mockSetStatus }),
}))

import EmailSettingsPage from '../EmailSettingsPage'

// ── Helpers ───────────────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    return function Wrapper({ children }: { children: ReactNode }) {
        return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    }
}

const MOCK_CONFIG = {
    provider_preset: 'Gmail',
    smtp_host: 'smtp.gmail.com',
    port: 587,
    security: 'STARTTLS',
    username: 'user@gmail.com',
    has_password: true,
    from_email: 'user@gmail.com',
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('MEU-73: EmailSettingsPage', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        mockApiFetch.mockImplementation((url: string) => {
            if (url === '/api/v1/settings/email') return Promise.resolve(MOCK_CONFIG)
            return Promise.resolve({})
        })
    })

    // AC-E6: renders page with correct testid
    it('AC-E6: renders email-settings-page testid', async () => {
        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('email-settings-page')).toBeInTheDocument()
        })
    })

    // AC-E7: has_password true shows placeholder indicator
    it('AC-E7: shows password-stored-indicator when has_password=true', async () => {
        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('password-stored-indicator')).toBeInTheDocument()
        })
    })

    // AC-E7: has_password false does NOT show indicator
    it('AC-E7: hides password-stored-indicator when has_password=false', async () => {
        mockApiFetch.mockResolvedValue({ ...MOCK_CONFIG, has_password: false })
        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.queryByTestId('password-stored-indicator')).not.toBeInTheDocument()
        })
    })

    // AC-E8: preset auto-fill (client-side, no extra API call)
    it('AC-E8: clicking preset fills smtp_host without extra API call', async () => {
        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByTestId('preset-brevo')).toBeInTheDocument())

        const callCountBefore = mockApiFetch.mock.calls.length
        fireEvent.click(screen.getByTestId('preset-brevo'))

        await waitFor(() => {
            const hostInput = screen.getByTestId('smtp-host-input') as HTMLInputElement
            expect(hostInput.value).toBe('smtp-relay.brevo.com')
        })
        // No extra API call beyond initial GET
        expect(mockApiFetch.mock.calls.length).toBe(callCountBefore)
    })

    // AC-E9: Save calls PUT with form data
    it('AC-E9: save button calls PUT /api/v1/settings/email', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'PUT') return Promise.resolve(MOCK_CONFIG)
            if (url === '/api/v1/settings/email') return Promise.resolve(MOCK_CONFIG)
            return Promise.resolve({})
        })

        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByTestId('save-email-settings-btn')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('save-email-settings-btn'))

        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/settings/email',
                expect.objectContaining({ method: 'PUT' }),
            )
        })
    })

    // AC-E10: Test Connection calls POST
    it('AC-E10: test-connection button calls POST /api/v1/settings/email/test', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'POST') return Promise.resolve({ success: true, message: 'OK' })
            if (url === '/api/v1/settings/email') return Promise.resolve(MOCK_CONFIG)
            return Promise.resolve({})
        })

        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByTestId('test-connection-btn')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('test-connection-btn'))

        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalledWith(
                '/api/v1/settings/email/test',
                expect.objectContaining({ method: 'POST' }),
            )
        })
    })

    // AC-E10: test result banner shown after test call
    it('AC-E10: test result banner appears after test call', async () => {
        mockApiFetch.mockImplementation((url: string, opts?: Record<string, unknown>) => {
            if (opts?.method === 'POST')
                return Promise.resolve({ success: true, message: 'Test email sent successfully to user@gmail.com.' })
            return Promise.resolve(MOCK_CONFIG)
        })

        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByTestId('test-connection-btn')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('test-connection-btn'))

        await waitFor(() => {
            expect(screen.getByTestId('test-connection-result')).toBeInTheDocument()
        })
    })

    // AC-E8 (Outlook preset): host, port, security correct per spec
    it('AC-E8: Outlook preset fills smtp-mail.outlook.com:587 STARTTLS', async () => {
        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByTestId('preset-outlook')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('preset-outlook'))

        await waitFor(() => {
            const hostInput = screen.getByTestId('smtp-host-input') as HTMLInputElement
            const portInput = screen.getByTestId('smtp-port-input') as HTMLInputElement
            expect(hostInput.value).toBe('smtp-mail.outlook.com')
            expect(portInput.value).toBe('587')
            expect(screen.getByDisplayValue('STARTTLS')).toBeInTheDocument()
        })
    })

    // AC-E8 (Yahoo preset): host, port, security correct per spec
    it('AC-E8: Yahoo preset fills smtp.mail.yahoo.com:465 SSL', async () => {
        render(<EmailSettingsPage />, { wrapper: createWrapper() })
        await waitFor(() => expect(screen.getByTestId('preset-yahoo')).toBeInTheDocument())

        fireEvent.click(screen.getByTestId('preset-yahoo'))

        await waitFor(() => {
            const hostInput = screen.getByTestId('smtp-host-input') as HTMLInputElement
            const portInput = screen.getByTestId('smtp-port-input') as HTMLInputElement
            expect(hostInput.value).toBe('smtp.mail.yahoo.com')
            expect(portInput.value).toBe('465')
            expect(screen.getByDisplayValue('SSL')).toBeInTheDocument()
        })
    })
})
