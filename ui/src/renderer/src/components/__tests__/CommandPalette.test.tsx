import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock fuse.js with simple string matching
vi.mock('fuse.js', () => ({
    default: class FuseMock {
        private items: any[]
        constructor(items: any[]) {
            this.items = items
        }
        search(query: string) {
            return this.items
                .filter(
                    (item) =>
                        item.label.toLowerCase().includes(query.toLowerCase()) ||
                        item.keywords?.some((k: string) =>
                            k.toLowerCase().includes(query.toLowerCase()),
                        ),
                )
                .map((item) => ({ item }))
        }
    },
}))

// Mock TanStack Router useNavigate
const mockNavigate = vi.fn()
vi.mock('@tanstack/react-router', () => ({
    useNavigate: () => mockNavigate,
}))

import CommandPalette from '../CommandPalette'

beforeEach(() => {
    mockNavigate.mockClear()
})

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

function renderPalette(props: { open: boolean; onClose: () => void }) {
    return render(<CommandPalette {...props} />, { wrapper: createWrapper() })
}

describe('CommandPalette', () => {
    it('should render when open=true', () => {
        renderPalette({ open: true, onClose: vi.fn() })
        expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should NOT render when open=false', () => {
        renderPalette({ open: false, onClose: vi.fn() })
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should have a search input', () => {
        renderPalette({ open: true, onClose: vi.fn() })
        expect(screen.getByRole('searchbox')).toBeInTheDocument()
    })

    it('should call onClose when Escape is pressed', () => {
        const onClose = vi.fn()
        renderPalette({ open: true, onClose })
        const input = screen.getByRole('searchbox')
        fireEvent.keyDown(input, { key: 'Escape' })
        expect(onClose).toHaveBeenCalled()
    })

    it('should group results by category when query is empty', () => {
        renderPalette({ open: true, onClose: vi.fn() })
        // Category headers exist in the DOM (CSS uppercase is visual only)
        expect(screen.getByText('Navigation')).toBeInTheDocument()
        expect(screen.getByText('Actions')).toBeInTheDocument()
        // 'Settings' appears as both a category header and a nav entry label
        const settingsMatches = screen.getAllByText('Settings')
        expect(settingsMatches.length).toBeGreaterThanOrEqual(2)
    })

    it('should filter results when typing', () => {
        renderPalette({ open: true, onClose: vi.fn() })
        const input = screen.getByRole('searchbox')
        fireEvent.change(input, { target: { value: 'trades' } })
        expect(screen.getByText('Trades')).toBeInTheDocument()
    })

    it('should highlight selected item with aria-selected', async () => {
        renderPalette({ open: true, onClose: vi.fn() })
        const input = screen.getByRole('searchbox')
        fireEvent.keyDown(input, { key: 'ArrowDown' })
        await waitFor(() => {
            const options = screen.getAllByRole('option')
            expect(options[0]).toHaveAttribute('aria-selected', 'true')
        })
    })

    it('should execute action on Enter and close palette', () => {
        const onClose = vi.fn()
        renderPalette({ open: true, onClose })
        const input = screen.getByRole('searchbox')
        act(() => {
            fireEvent.keyDown(input, { key: 'ArrowDown' })
        })
        act(() => {
            fireEvent.keyDown(input, { key: 'Enter' })
        })
        expect(onClose).toHaveBeenCalled()
    })

    it('should call navigate when selecting a navigation entry', () => {
        const onClose = vi.fn()
        renderPalette({ open: true, onClose })
        const input = screen.getByRole('searchbox')
        // First entry is 'Accounts' nav entry -> navigate('/')
        act(() => {
            fireEvent.keyDown(input, { key: 'ArrowDown' })
        })
        act(() => {
            fireEvent.keyDown(input, { key: 'Enter' })
        })
        // mockNavigate is called via createStaticEntries((path) => navigate({ to: path }))
        // The navigate mock receives the { to: path } object
        expect(mockNavigate).toHaveBeenCalledWith({ to: '/' })
    })
})
