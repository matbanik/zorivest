import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ─── Mocks ────────────────────────────────────────────────────────────────────

// Use vi.hoisted() so mock fns are declared at the same hoisting level as vi.mock
const {
    mockToastSuccess,
    mockToastError,
    mockToastWarning,
    mockToastMessage,
    mockToastDismiss,
    mockApiFetch,
} = vi.hoisted(() => ({
    mockToastSuccess: vi.fn(),
    mockToastError: vi.fn(),
    mockToastWarning: vi.fn(),
    mockToastMessage: vi.fn(),
    mockToastDismiss: vi.fn(),
    mockApiFetch: vi.fn(),
}))

// Mock sonner — capture all toast calls
vi.mock('sonner', () => ({
    toast: Object.assign(
        (msg: string, opts?: any) => mockToastMessage(msg, opts),
        {
            success: mockToastSuccess,
            error: mockToastError,
            warning: mockToastWarning,
            message: mockToastMessage,
            dismiss: mockToastDismiss,
        },
    ),
    Toaster: (props: any) => React.createElement('div', { 'data-testid': 'toaster' }),
}))

// Mock apiFetch for settings endpoint
vi.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => mockApiFetch(...args),
}))

// Import AFTER mocks are set up
import {
    NotificationProvider,
    useNotifications,
    type NotificationCategory,
} from '../useNotifications'

// ─── Test Helpers ─────────────────────────────────────────────────────────────

function createWrapper(prefsOverrides?: Record<string, boolean>) {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false, staleTime: 0, gcTime: 0 },
        },
    })

    return function Wrapper({ children }: { children: React.ReactNode }) {
        return React.createElement(
            QueryClientProvider,
            { client: queryClient },
            React.createElement(NotificationProvider, null, children),
        )
    }
}

function renderNotifications() {
    return renderHook(() => useNotifications(), { wrapper: createWrapper() })
}

// Helper to set up preferences via apiFetch mock.
// Returns a resolved preferences map based on category overrides.
function setupPreferences(overrides: Partial<Record<NotificationCategory, boolean>> = {}) {
    mockApiFetch.mockImplementation(async (path: string) => {
        for (const [cat, enabled] of Object.entries(overrides)) {
            if (path.includes(`notification.${cat}.enabled`)) {
                return { value: enabled }
            }
        }
        return { value: true } // default: enabled
    })
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('useNotifications', () => {
    let consoleSpy: ReturnType<typeof vi.spyOn>

    beforeEach(() => {
        vi.clearAllMocks()
        consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => { })
        // Default: all preferences enabled (no suppression)
        setupPreferences()
    })

    afterEach(() => {
        consoleSpy.mockRestore()
    })

    // ── AC-1: 5 spec categories ──────────────────────────────────────────

    it('should expose notify() that accepts all 5 spec categories', () => {
        const { result } = renderNotifications()
        expect(result.current.notify).toBeDefined()
        expect(typeof result.current.notify).toBe('function')
    })

    it('should accept "success" category and call toast.success', async () => {
        const { result } = renderNotifications()
        act(() => {
            result.current.notify({ category: 'success', message: 'Trade saved' })
        })
        expect(mockToastSuccess).toHaveBeenCalledWith(
            'Trade saved',
            expect.any(Object),
        )
    })

    it('should accept "info" category and call toast.message', async () => {
        const { result } = renderNotifications()
        act(() => {
            result.current.notify({ category: 'info', message: 'Data refreshed' })
        })
        expect(mockToastMessage).toHaveBeenCalledWith(
            'Data refreshed',
            expect.any(Object),
        )
    })

    it('should accept "warning" category and call toast.warning', async () => {
        const { result } = renderNotifications()
        act(() => {
            result.current.notify({ category: 'warning', message: 'Rate limited' })
        })
        expect(mockToastWarning).toHaveBeenCalledWith(
            'Rate limited',
            expect.any(Object),
        )
    })

    it('should accept "error" category and call toast.error', async () => {
        const { result } = renderNotifications()
        act(() => {
            result.current.notify({ category: 'error', message: 'Connection lost' })
        })
        expect(mockToastError).toHaveBeenCalledWith(
            'Connection lost',
            expect.any(Object),
        )
    })

    it('should accept "confirmation" category and call toast.message', async () => {
        const { result } = renderNotifications()
        act(() => {
            result.current.notify({
                category: 'confirmation',
                message: 'Delete trade?',
            })
        })
        expect(mockToastMessage).toHaveBeenCalledWith(
            'Delete trade?',
            expect.any(Object),
        )
    })

    // ── AC-2: error always shows ─────────────────────────────────────────

    it('should always show error notifications even when suppressed', async () => {
        // Set all preferences to false (suppressed)
        setupPreferences({ success: false, info: false, warning: false, confirmation: false })

        const { result } = renderNotifications()
        // Wait for preferences to load from mock
        await waitFor(() => {
            expect(result.current.preferencesLoaded).toBe(true)
        })

        act(() => {
            result.current.notify({ category: 'error', message: 'Critical failure' })
        })
        expect(mockToastError).toHaveBeenCalledWith(
            'Critical failure',
            expect.any(Object),
        )
    })

    // ── AC-3: confirmation suppression → defaultAction ───────────────────

    it('should execute defaultAction (cancel) when confirmation is suppressed', async () => {
        setupPreferences({ confirmation: false })

        const { result } = renderNotifications()
        // Wait for preferences to load from mock
        await waitFor(() => {
            expect(result.current.preferencesLoaded).toBe(true)
        })

        const defaultAction = vi.fn()
        act(() => {
            result.current.notify({
                category: 'confirmation',
                message: 'Delete this trade?',
                defaultAction,
            })
        })

        // Toast should NOT have been called (suppressed)
        expect(mockToastMessage).not.toHaveBeenCalled()
        expect(mockToastSuccess).not.toHaveBeenCalled()
        // defaultAction should execute
        expect(defaultAction).toHaveBeenCalled()
    })

    // ── AC-4: console logging on suppression ─────────────────────────────

    it('should log suppressed notifications with [suppressed:{category}] prefix', async () => {
        setupPreferences({ info: false })

        const { result } = renderNotifications()
        await waitFor(() => {
            expect(result.current.preferencesLoaded).toBe(true)
        })

        act(() => {
            result.current.notify({
                category: 'info',
                message: 'Background sync complete',
            })
        })

        expect(consoleSpy).toHaveBeenCalledWith(
            '[suppressed:info]',
            'Background sync complete',
        )
    })

    it('should NOT log when notifications are shown (not suppressed)', async () => {
        const { result } = renderNotifications()
        act(() => {
            result.current.notify({ category: 'success', message: 'Saved' })
        })
        expect(consoleSpy).not.toHaveBeenCalled()
    })

    // ── AC-5: preferences via REST ───────────────────────────────────────

    it('should read notification preferences from /api/v1/settings', async () => {
        const { result } = renderNotifications()

        await waitFor(() => {
            expect(result.current.preferencesLoaded).toBe(true)
        })

        // Should use /api/v1/settings/ path (not /api/settings/)
        const calls = mockApiFetch.mock.calls.map((c: any[]) => c[0])
        const settingsCalls = calls.filter((path: string) =>
            path.startsWith('/api/v1/settings/'),
        )
        expect(settingsCalls.length).toBeGreaterThan(0)
    })

    it('should suppress info notifications when preference is false', async () => {
        setupPreferences({ info: false })

        const { result } = renderNotifications()
        await waitFor(() => {
            expect(result.current.preferencesLoaded).toBe(true)
        })

        act(() => {
            result.current.notify({ category: 'info', message: 'Suppressed msg' })
        })

        // info toast should NOT show
        expect(mockToastMessage).not.toHaveBeenCalled()
        // But should be logged
        expect(consoleSpy).toHaveBeenCalledWith(
            '[suppressed:info]',
            'Suppressed msg',
        )
    })

    // ── AC-7: Error behavior edge cases ──────────────────────────────────

    it('should NOT suppress error even when error preference is false', async () => {
        mockApiFetch.mockResolvedValue({ value: false })

        const { result } = renderNotifications()
        act(() => {
            result.current.notify({ category: 'error', message: 'Always shows' })
        })

        expect(mockToastError).toHaveBeenCalled()
        // Error should NOT be logged as suppressed
        expect(consoleSpy).not.toHaveBeenCalled()
    })

    it('should throw if useNotifications is used outside NotificationProvider', () => {
        expect(() => {
            renderHook(() => useNotifications())
        }).toThrow('useNotifications must be used within NotificationProvider')
    })

    // ── Category suppression combinations ────────────────────────────────

    it('should suppress success when preference is false', async () => {
        setupPreferences({ success: false })

        const { result } = renderNotifications()
        await waitFor(() => {
            expect(result.current.preferencesLoaded).toBe(true)
        })

        act(() => {
            result.current.notify({ category: 'success', message: 'Suppressed' })
        })

        expect(mockToastSuccess).not.toHaveBeenCalled()
        expect(consoleSpy).toHaveBeenCalledWith('[suppressed:success]', 'Suppressed')
    })

    it('should suppress warning when preference is false', async () => {
        setupPreferences({ warning: false })

        const { result } = renderNotifications()
        await waitFor(() => {
            expect(result.current.preferencesLoaded).toBe(true)
        })

        act(() => {
            result.current.notify({ category: 'warning', message: 'Suppressed' })
        })

        expect(mockToastWarning).not.toHaveBeenCalled()
        expect(consoleSpy).toHaveBeenCalledWith(
            '[suppressed:warning]',
            'Suppressed',
        )
    })

    // ── dismiss ──────────────────────────────────────────────────────────

    it('should expose dismiss function', () => {
        const { result } = renderNotifications()
        expect(result.current.dismiss).toBeDefined()
    })
})
