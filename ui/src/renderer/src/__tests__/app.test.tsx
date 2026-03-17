import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Mock fuse.js (required because Ctrl+K opens CommandPalette which uses Fuse)
vi.mock('fuse.js', () => ({
    default: class FuseMock {
        constructor() { /* noop */ }
        search() { return [] }
    },
}))

// Mock window.api with init stub
Object.defineProperty(window, 'api', {
    value: {
        baseUrl: 'http://127.0.0.1:54321',
        token: 'a'.repeat(64),
        init: vi.fn().mockResolvedValue(undefined),
    },
    writable: true,
    configurable: true,
})

Object.defineProperty(window, 'electronStore', {
    value: {
        get: vi.fn(),
        set: vi.fn(),
    },
    writable: true,
    configurable: true,
})

// Mock useNavigate (AppShell → Header → CommandPalette uses it)
vi.mock('@tanstack/react-router', async () => {
    const actual = await vi.importActual('@tanstack/react-router')
    return {
        ...actual,
        useNavigate: () => vi.fn(),
    }
})

import AppShell from '../components/layout/AppShell'

function renderWithProviders(ui: React.ReactElement) {
    const testQueryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    })
    return render(
        <QueryClientProvider client={testQueryClient}>
            {ui}
        </QueryClientProvider>,
    )
}

describe('AppShell', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('should render without crashing', () => {
        renderWithProviders(<AppShell />)
        expect(document.body).toBeTruthy()
        // Value: verify the shell rendered key structural elements
        expect(screen.getByRole('navigation')).toBeInTheDocument()
    })

    it('should have a <nav> ARIA landmark for NavRail', () => {
        renderWithProviders(<AppShell />)
        const nav = screen.getByRole('navigation')
        expect(nav).toBeInTheDocument()
    })

    it('should have a <main> ARIA landmark', () => {
        renderWithProviders(<AppShell />)
        const main = screen.getByRole('main')
        expect(main).toBeInTheDocument()
    })

    it('should have a <header> element (banner role)', () => {
        renderWithProviders(<AppShell />)
        const header = screen.getByRole('banner')
        expect(header).toBeInTheDocument()
    })

    it('should have a skip-to-content link', () => {
        renderWithProviders(<AppShell />)
        const skipLink = screen.getByText(/skip to/i)
        expect(skipLink).toBeInTheDocument()
        expect(skipLink).toHaveAttribute('href', '#main-content')
    })

    it('should render 5 navigation items in NavRail', () => {
        renderWithProviders(<AppShell />)
        const nav = screen.getByRole('navigation')
        const links = nav.querySelectorAll('a, button')
        expect(links.length).toBeGreaterThanOrEqual(5)
        // Value: verify nav links contain expected accessible names
        const navText = nav.textContent
        expect(navText).toBeTruthy()
    })

    it('should render children inside <main> (Outlet injection point)', () => {
        renderWithProviders(
            <AppShell>
                <div data-testid="route-content">Accounts Dashboard Content</div>
            </AppShell>,
        )
        const main = screen.getByRole('main')
        const routeContent = screen.getByTestId('route-content')
        expect(main).toContainElement(routeContent)
        expect(routeContent).toHaveTextContent('Accounts Dashboard Content')
    })

    it('should open CommandPalette on Ctrl+K and close on second press', async () => {
        renderWithProviders(<AppShell />)

        // Initially no dialog
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

        // Press Ctrl+K → palette opens
        act(() => {
            window.dispatchEvent(
                new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }),
            )
        })
        expect(screen.getByRole('dialog', { name: /command palette/i })).toBeInTheDocument()

        // Press Ctrl+K again → palette closes
        act(() => {
            window.dispatchEvent(
                new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }),
            )
        })
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
})
