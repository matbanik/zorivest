/**
 * Tests for MEU-156: Tax Section Toggles / Tax Profile Settings.
 *
 * Tests the inline tax profile section in SettingsLayout:
 * - Tax profile section renders with correct data-testid
 * - Filing status, cost basis, and tax year selects present
 * - All controls are disabled (read-only until backend API)
 * - Disabled controls show "Coming soon" tooltip
 * - Read-only notice text present
 *
 * Test pattern follows McpServerStatusPanel.test.tsx (vi.hoisted mock, QueryClient wrapper).
 * MEU: MEU-156 (tax-section-toggles)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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

// Mock clipboard
const mockClipboardWriteText = vi.fn().mockResolvedValue(undefined)
Object.assign(navigator, {
    clipboard: { writeText: mockClipboardWriteText },
})

// Mock window.api
Object.defineProperty(window, 'api', {
    value: { baseUrl: 'http://localhost:8766', token: 'test-token' },
    writable: true,
})

// Import after mocks
import SettingsLayout from '../SettingsLayout'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )
    }
}

function setupDefaultMocks() {
    mockApiFetch.mockImplementation(async (path: string) => {
        if (path === '/api/v1/health') return { status: 'ok', version: 'v1.0.0', uptime_seconds: 60, database: { unlocked: true } }
        if (path === '/api/v1/version/') return { version: 'v1.0.0', environment: 'test' }
        if (path.includes('mcp-guard/status')) return { is_locked: false, calls_per_hour: 10 }
        if (path === '/api/v1/mcp/toolsets') return { total_tools: 13, toolset_count: 4, toolsets: [] }
        if (path === '/api/v1/mcp/diagnostics') return { api_uptime_seconds: 30, api_version: '0.1.0' }
        if (path.startsWith('/api/v1/settings/')) return { value: 'dark' }
        if (path.includes('market-data/providers')) return []
        return {}
    })
}

// ─── MEU-156: Tax Profile Section Tests ──────────────────────────────────────

describe('MEU-156: Tax Profile Settings (read-only)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        setupDefaultMocks()
    })

    // AC-156.1: Section renders with correct data-testid
    it('AC-156.1: renders tax-profile-settings section', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('tax-profile-settings')).toBeInTheDocument()
        })
    })

    // AC-156.2: Section has "Tax Profile" heading
    it('AC-156.2: renders Tax Profile heading', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const section = screen.getByTestId('tax-profile-settings')
            expect(section).toHaveTextContent('Tax Profile')
        })
    })

    // AC-156.3: Filing status select is present and disabled
    it('AC-156.3: filing status select is present and disabled', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-filing-status') as HTMLSelectElement
            expect(select).toBeInTheDocument()
            expect(select).toBeDisabled()
        })
    })

    // AC-156.4: Filing status has all 4 IRS filing statuses
    it('AC-156.4: filing status contains all 4 IRS filing options', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-filing-status') as HTMLSelectElement
            const options = Array.from(select.options).map(o => o.value)
            expect(options).toContain('single')
            expect(options).toContain('married_joint')
            expect(options).toContain('married_separate')
            expect(options).toContain('head_of_household')
        })
    })

    // AC-156.5: Cost basis method select is present and disabled
    it('AC-156.5: cost basis method select is present and disabled', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-cost-basis-method') as HTMLSelectElement
            expect(select).toBeInTheDocument()
            expect(select).toBeDisabled()
        })
    })

    // AC-156.6: Cost basis has FIFO, LIFO, Specific ID, Average Cost
    it('AC-156.6: cost basis method contains 4 method options', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-cost-basis-method') as HTMLSelectElement
            const options = Array.from(select.options).map(o => o.value)
            expect(options).toContain('fifo')
            expect(options).toContain('lifo')
            expect(options).toContain('specific_id')
            expect(options).toContain('avg_cost')
        })
    })

    // AC-156.7: Tax year select is present and disabled
    it('AC-156.7: tax year select is present and disabled', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-year-setting') as HTMLSelectElement
            expect(select).toBeInTheDocument()
            expect(select).toBeDisabled()
        })
    })

    // AC-156.8: Tax year has 2026, 2025, 2024 options
    it('AC-156.8: tax year contains 2026, 2025, 2024 options', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-year-setting') as HTMLSelectElement
            const options = Array.from(select.options).map(o => o.value)
            expect(options).toContain('2026')
            expect(options).toContain('2025')
            expect(options).toContain('2024')
        })
    })

    // AC-156.9: All disabled controls have "Coming soon" tooltip
    it('AC-156.9: all selects have "Coming soon" title tooltip', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const filingStatus = screen.getByTestId('tax-filing-status')
            const costBasis = screen.getByTestId('tax-cost-basis-method')
            const taxYear = screen.getByTestId('tax-year-setting')

            expect(filingStatus).toHaveAttribute('title', expect.stringContaining('Coming soon'))
            expect(costBasis).toHaveAttribute('title', expect.stringContaining('Coming soon'))
            expect(taxYear).toHaveAttribute('title', expect.stringContaining('Coming soon'))
        })
    })

    // AC-156.10: Read-only notice is displayed
    it('AC-156.10: shows read-only notice text', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const section = screen.getByTestId('tax-profile-settings')
            expect(section).toHaveTextContent(/Read-only/)
        })
    })

    // AC-156.11: Default values are correct
    it('AC-156.11: filing status defaults to "single"', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-filing-status') as HTMLSelectElement
            expect(select.value).toBe('single')
        })
    })

    it('AC-156.11: cost basis defaults to "fifo"', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-cost-basis-method') as HTMLSelectElement
            expect(select.value).toBe('fifo')
        })
    })

    it('AC-156.11: tax year defaults to "2026"', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            const select = screen.getByTestId('tax-year-setting') as HTMLSelectElement
            expect(select.value).toBe('2026')
        })
    })
})
