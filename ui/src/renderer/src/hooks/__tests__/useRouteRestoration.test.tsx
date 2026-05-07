import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ─── Mocks ────────────────────────────────────────────────────────────────────

const { mockApiFetch } = vi.hoisted(() => ({
    mockApiFetch: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => mockApiFetch(...args),
}))

import { useRouteRestoration } from '../useRouteRestoration'

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

describe('useRouteRestoration', () => {
    let navigateSpy: ReturnType<typeof vi.fn>

    beforeEach(() => {
        vi.clearAllMocks()
        navigateSpy = vi.fn()
    })

    it('should navigate to saved page when async value arrives', async () => {
        // Server returns a saved page that differs from current
        mockApiFetch.mockResolvedValue({ value: '/settings' })

        renderHook(() => useRouteRestoration('/', navigateSpy), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(navigateSpy).toHaveBeenCalledWith('/settings')
        })
        // Should only navigate once
        expect(navigateSpy).toHaveBeenCalledTimes(1)
    })

    it('should NOT navigate when saved page is root (/)', async () => {
        // Server returns '/' — no navigation needed
        mockApiFetch.mockResolvedValue({ value: '/' })

        renderHook(() => useRouteRestoration('/', navigateSpy), {
            wrapper: createWrapper(),
        })

        // Give the async fetch time to resolve
        await waitFor(() => {
            // apiFetch was called for the settings read
            expect(mockApiFetch).toHaveBeenCalled()
        })

        // Should NOT navigate since saved page is root
        expect(navigateSpy).not.toHaveBeenCalled()
    })

    it('should NOT navigate when already on saved page', async () => {
        mockApiFetch.mockResolvedValue({ value: '/trades' })

        renderHook(() => useRouteRestoration('/trades', navigateSpy), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalled()
        })

        // Already on /trades — no navigation needed
        expect(navigateSpy).not.toHaveBeenCalled()
    })

    it('should save route changes after initial restore completes (fresh install)', async () => {
        // Fresh install: server returns '/' (default)
        const putCalls: string[] = []
        mockApiFetch.mockImplementation(async (path: string, opts?: any) => {
            if (opts?.method === 'PUT') {
                putCalls.push(path)
                return {}
            }
            return { value: '/' }
        })

        const { rerender } = renderHook(
            ({ path }) => useRouteRestoration(path, navigateSpy),
            {
                wrapper: createWrapper(),
                initialProps: { path: '/' },
            },
        )

        // Wait for the restore phase to settle (savedPage='/' arrives)
        await waitFor(() => {
            expect(mockApiFetch).toHaveBeenCalled()
        })

        // Simulate route change after restore phase
        rerender({ path: '/settings' })

        // The save effect should fire and persist the new route
        await waitFor(() => {
            const settingsPuts = putCalls.filter((p) =>
                p.includes('ui.activePage'),
            )
            expect(settingsPuts.length).toBeGreaterThan(0)
        })
    })

    it('should save route changes after navigating to a saved page', async () => {
        const putCalls: string[] = []
        mockApiFetch.mockImplementation(async (path: string, opts?: any) => {
            if (opts?.method === 'PUT') {
                putCalls.push(path)
                return {}
            }
            return { value: '/settings' }
        })

        const { rerender } = renderHook(
            ({ path }) => useRouteRestoration(path, navigateSpy),
            {
                wrapper: createWrapper(),
                initialProps: { path: '/' },
            },
        )

        // Wait for restore navigation
        await waitFor(() => {
            expect(navigateSpy).toHaveBeenCalledWith('/settings')
        })

        // Simulate user navigating to /trades after restore
        rerender({ path: '/trades' })

        await waitFor(() => {
            const settingsPuts = putCalls.filter((p) =>
                p.includes('ui.activePage'),
            )
            expect(settingsPuts.length).toBeGreaterThan(0)
        })
    })
})
