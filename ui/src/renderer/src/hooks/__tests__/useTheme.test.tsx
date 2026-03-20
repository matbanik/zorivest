import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ─── Mocks ────────────────────────────────────────────────────────────────────

const { mockApiFetch } = vi.hoisted(() => ({
    mockApiFetch: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => mockApiFetch(...args),
}))

import { useTheme } from '../useTheme'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false, staleTime: 0, gcTime: 0 },
        },
    })
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return React.createElement(
            QueryClientProvider,
            { client: queryClient },
            children,
        )
    }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('useTheme', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Default: return 'dark' theme from server
        mockApiFetch.mockResolvedValue({ value: 'dark' })
        // Reset document state
        document.documentElement.classList.remove('dark')
    })

    afterEach(() => {
        document.documentElement.classList.remove('dark')
    })

    it('should default to dark theme', () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: createWrapper(),
        })

        const [theme] = result.current
        expect(theme).toBe('dark')
    })

    it('should apply dark class to documentElement for dark theme', async () => {
        mockApiFetch.mockResolvedValue({ value: 'dark' })

        renderHook(() => useTheme(), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(document.documentElement.classList.contains('dark')).toBe(
                true,
            )
        })
    })

    it('should remove dark class for light theme', async () => {
        // Server returns 'light'
        mockApiFetch.mockResolvedValue({ value: 'light' })

        renderHook(() => useTheme(), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(document.documentElement.classList.contains('dark')).toBe(
                false,
            )
        })
    })

    it('should persist theme changes via API', async () => {
        const putCalls: Array<{ path: string; body: string }> = []
        mockApiFetch.mockImplementation(async (path: string, opts?: any) => {
            if (opts?.method === 'PUT') {
                putCalls.push({ path, body: opts.body })
                return {}
            }
            return { value: 'dark' }
        })

        const { result } = renderHook(() => useTheme(), {
            wrapper: createWrapper(),
        })

        // Switch to light theme
        act(() => {
            const [, setTheme] = result.current
            setTheme('light')
        })

        await waitFor(() => {
            const themePuts = putCalls.filter((c) =>
                c.path.includes('ui.theme'),
            )
            expect(themePuts.length).toBeGreaterThan(0)
            expect(themePuts[0].body).toContain('light')
        })
    })

    it('should return setTheme function', () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: createWrapper(),
        })

        const [, setTheme] = result.current
        expect(typeof setTheme).toBe('function')
    })
})
