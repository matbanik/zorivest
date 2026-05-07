import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Mock window.api
Object.defineProperty(window, 'api', {
    value: {
        baseUrl: 'http://127.0.0.1:54321',
        token: 'a'.repeat(64),
        init: vi.fn().mockResolvedValue(undefined),
    },
    writable: true,
    configurable: true,
})

// Mock apiFetch for settings persistence — stateful: remembers PUT values
const settingsStore: Record<string, unknown> = {}
const apiFetchMock = vi.fn().mockImplementation(async (path: string, opts?: { method?: string; body?: string }) => {
    if (path.includes('/settings/')) {
        const key = path.replace(/.*\/settings\//, '')
        if (opts?.method === 'PUT') {
            const { value } = JSON.parse(opts.body ?? '{}')
            settingsStore[key] = value
            return {}
        }
        // GET — return stored value or null
        return { value: key in settingsStore ? settingsStore[key] : null }
    }
    return {}
})
vi.mock('@/lib/api', () => ({
    apiFetch: (...args: unknown[]) => apiFetchMock(...args),
}))

// Import after mocks
import {
    AccountProvider,
    useAccountContext,
} from '../../context/AccountContext'

// ── Test helper ─────────────────────────────────────────────────────────────

function TestQueryWrapper({ children }: { children: React.ReactNode }) {
    const client = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    })
    return (
        <QueryClientProvider client={client}>
            {children}
        </QueryClientProvider>
    )
}

/** Renders a component that consumes AccountContext and exposes its state */
function AccountContextConsumer() {
    const { activeAccountId, selectAccount, mruAccountIds } = useAccountContext()
    return (
        <div>
            <span data-testid="active-id">{activeAccountId ?? 'none'}</span>
            <span data-testid="mru-ids">{JSON.stringify(mruAccountIds)}</span>
            <button onClick={() => selectAccount('acct-1')}>Select 1</button>
            <button onClick={() => selectAccount('acct-2')}>Select 2</button>
            <button onClick={() => selectAccount('acct-3')}>Select 3</button>
            <button onClick={() => selectAccount('acct-4')}>Select 4</button>
            <button onClick={() => selectAccount(null)}>Clear</button>
        </div>
    )
}

function renderWithContext() {
    return render(
        <TestQueryWrapper>
            <AccountProvider>
                <AccountContextConsumer />
            </AccountProvider>
        </TestQueryWrapper>,
    )
}

// ── AC-14: AccountContext provider ──────────────────────────────────────────

describe('AccountContext', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Clear persisted settings store between tests
        Object.keys(settingsStore).forEach((k) => delete settingsStore[k])
    })

    it('AC-14: should provide null activeAccountId by default', () => {
        renderWithContext()
        expect(screen.getByTestId('active-id')).toHaveTextContent('none')
    })

    it('AC-14: should provide empty MRU list by default', () => {
        renderWithContext()
        expect(screen.getByTestId('mru-ids')).toHaveTextContent('[]')
    })

    it('AC-14: selectAccount sets activeAccountId', async () => {
        const user = userEvent.setup()
        renderWithContext()

        await user.click(screen.getByText('Select 1'))

        await waitFor(() => {
            expect(screen.getByTestId('active-id')).toHaveTextContent('acct-1')
        })
    })

    it('AC-14: selectAccount(null) clears activeAccountId', async () => {
        const user = userEvent.setup()
        renderWithContext()

        await user.click(screen.getByText('Select 1'))
        await waitFor(() => {
            expect(screen.getByTestId('active-id')).toHaveTextContent('acct-1')
        })

        await user.click(screen.getByText('Clear'))
        await waitFor(() => {
            expect(screen.getByTestId('active-id')).toHaveTextContent('none')
        })
    })

    it('AC-14: selectAccount adds to MRU list', async () => {
        const user = userEvent.setup()
        renderWithContext()

        await user.click(screen.getByText('Select 1'))
        await waitFor(() => {
            const mruIds = JSON.parse(screen.getByTestId('mru-ids').textContent!)
            expect(mruIds).toContain('acct-1')
        })
    })

    it('AC-14: MRU list maintains max 3 entries', async () => {
        const user = userEvent.setup()
        renderWithContext()

        await user.click(screen.getByText('Select 1'))
        await user.click(screen.getByText('Select 2'))
        await user.click(screen.getByText('Select 3'))
        await user.click(screen.getByText('Select 4'))

        await waitFor(() => {
            const mruIds = JSON.parse(screen.getByTestId('mru-ids').textContent!)
            expect(mruIds).toHaveLength(3)
            // Most recent should be first
            expect(mruIds[0]).toBe('acct-4')
            // Oldest (acct-1) should be evicted
            expect(mruIds).not.toContain('acct-1')
        })
    })

    it('AC-14: selecting an existing MRU account moves it to front', async () => {
        const user = userEvent.setup()
        renderWithContext()

        await user.click(screen.getByText('Select 1'))
        await user.click(screen.getByText('Select 2'))
        await user.click(screen.getByText('Select 3'))

        // Re-select acct-1 — should move to front
        await user.click(screen.getByText('Select 1'))

        await waitFor(() => {
            const mruIds = JSON.parse(screen.getByTestId('mru-ids').textContent!)
            expect(mruIds[0]).toBe('acct-1')
            expect(mruIds).toHaveLength(3)
        })
    })

    it('AC-14: persists activeAccountId via usePersistedState', async () => {
        const user = userEvent.setup()
        renderWithContext()

        await user.click(screen.getByText('Select 1'))

        // Should have called PUT to persist active account
        const putCalls = apiFetchMock.mock.calls.filter(
            (c: unknown[]) => typeof c[0] === 'string' && c[0].includes('ui.accounts.active') && c[1] && (c[1] as Record<string, string>).method === 'PUT',
        )
        expect(putCalls.length).toBeGreaterThan(0)
    })

    it('AC-14: persists MRU list via usePersistedState', async () => {
        const user = userEvent.setup()
        renderWithContext()

        await user.click(screen.getByText('Select 1'))

        // Should have called PUT to persist MRU
        const putCalls = apiFetchMock.mock.calls.filter(
            (c: unknown[]) => typeof c[0] === 'string' && c[0].includes('ui.accounts.mru') && c[1] && (c[1] as Record<string, string>).method === 'PUT',
        )
        expect(putCalls.length).toBeGreaterThan(0)
    })

    it('AC-14: useAccountContext throws outside provider', () => {
        function BadConsumer() {
            useAccountContext()
            return null
        }

        expect(() => {
            render(
                <TestQueryWrapper>
                    <BadConsumer />
                </TestQueryWrapper>,
            )
        }).toThrow()
    })
})
