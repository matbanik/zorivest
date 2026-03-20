import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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
import McpServerStatusPanel from '../McpServerStatusPanel'
import SettingsLayout from '../SettingsLayout'

// ─── Helpers ──────────────────────────────────────────────────────────────────

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

function setupDefaultMocks() {
    mockApiFetch.mockImplementation(async (path: string) => {
        if (path === '/api/v1/health') return { status: 'ok', version: 'v1.2.3', uptime_seconds: 60, database: { unlocked: true } }
        if (path === '/api/v1/version/') return { version: 'v1.2.3', environment: 'test' }
        if (path.includes('mcp-guard/status')) return { is_locked: false, calls_per_hour: 42 }
        if (path === '/api/v1/mcp/toolsets') return { total_tools: 51, toolset_count: 9, toolsets: [{ name: 'core', tool_count: 4, always_loaded: true }] }
        if (path === '/api/v1/mcp/diagnostics') return { api_uptime_seconds: 120.5, api_version: '0.1.0' }
        // Default for settings paths (useTheme, useRouteRestoration, etc.)
        if (path.startsWith('/api/v1/settings/')) return { value: 'dark' }
        return {}
    })
}

// ─── McpServerStatusPanel Tests ──────────────────────────────────────────────

describe('McpServerStatusPanel', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        setupDefaultMocks()
    })

    it('should render the status panel with data-testid', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-status-panel')).toBeInTheDocument()
        })
    })

    it('should show backend status from /health', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('OK')).toBeInTheDocument()
        })
    })

    it('should show version from /version', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('v1.2.3')).toBeInTheDocument()
        })
    })

    it('should show database status as Unlocked', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText('Unlocked')).toBeInTheDocument()
        })
    })

    it('should show guard state with calls/hr', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByText(/Active.*42 calls\/hr/)).toBeInTheDocument()
        })
    })

    it('should show live tool count and uptime from MCP endpoints', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            // MEU-46a: tool count from /mcp/toolsets
            expect(screen.getByTestId('mcp-tool-count')).toHaveTextContent('51 (9 toolsets)')
            // MEU-46a: uptime from /mcp/diagnostics
            expect(screen.getByTestId('mcp-uptime')).toHaveTextContent('2m 0s')
        })
    })

    it('should render Refresh Status button', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-refresh-btn')).toBeInTheDocument()
        })
    })

    // ── IDE Configuration ────────────────────────────────────────────

    it('should render IDE config section', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-ide-config')).toBeInTheDocument()
        })
    })

    it('should render tabs for 3 IDE targets', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('ide-tab-cursor')).toBeInTheDocument()
            expect(screen.getByTestId('ide-tab-claude-desktop')).toBeInTheDocument()
            expect(screen.getByTestId('ide-tab-windsurf')).toBeInTheDocument()
        })
    })

    it('should generate correct JSON for Cursor (default)', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            const codeBlock = screen.getByRole('code', { hidden: true }) ??
                screen.getByText(/mcpServers/)
            const text = codeBlock.textContent ?? ''
            expect(text).toContain('"mcpServers"')
            expect(text).toContain('"zorivest"')
            expect(text).toContain('/mcp')
        })
    })

    it('should switch IDE config when clicking Claude Desktop tab', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('ide-tab-claude-desktop')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('ide-tab-claude-desktop'))
        await waitFor(() => {
            const configText = document.querySelector('code')?.textContent ?? ''
            expect(configText).toContain('"transport"')
            expect(configText).toContain('"sse"')
        })
    })

    it('should copy JSON to clipboard when clicking copy button', async () => {
        render(<McpServerStatusPanel />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('ide-copy-btn')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId('ide-copy-btn'))
        await waitFor(() => {
            expect(mockClipboardWriteText).toHaveBeenCalled()
            const copiedText = mockClipboardWriteText.mock.calls[0][0]
            expect(copiedText).toContain('"mcpServers"')
        })
    })
})

// ─── SettingsLayout Tests ────────────────────────────────────────────────────

describe('SettingsLayout', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        setupDefaultMocks()
    })

    it('should render with data-testid="settings-page"', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        expect(screen.getByTestId('settings-page')).toBeInTheDocument()
    })

    it('should render MCP Guard status indicator', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-guard-status')).toBeInTheDocument()
        })
    })

    it('should show Unlocked when guard is not locked', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-guard-status')).toHaveTextContent(/Unlocked/)
        })
    })

    it('should show Locked when guard is locked', async () => {
        mockApiFetch.mockImplementation(async (path: string) => {
            if (path.includes('mcp-guard/status')) return { is_locked: true }
            if (path === '/api/v1/health') return { status: 'ok', version: 'v1.0.0', uptime_seconds: 0, database: { unlocked: true } }
            if (path === '/api/v1/version/') return { version: 'v1.0.0' }
            if (path.startsWith('/api/v1/settings/')) return { value: 'dark' }
            return {}
        })
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-guard-status')).toHaveTextContent(/Locked/)
        })
    })

    it('should render MCP Guard lock toggle', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-guard-lock-toggle')).toBeInTheDocument()
        })
    })

    it('should toggle guard when clicking lock toggle', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-guard-lock-toggle')).toBeInTheDocument()
        })

        fireEvent.click(screen.getByTestId('mcp-guard-lock-toggle'))

        await waitFor(() => {
            // Should have called lock endpoint (guard was unlocked)
            const lockCalls = mockApiFetch.mock.calls.filter(
                (c: any[]) => c[0].includes('mcp-guard/lock') && c[1]?.method === 'POST',
            )
            expect(lockCalls.length).toBeGreaterThanOrEqual(1)
        })
    })

    it('should render MCP Server Status panel within settings', async () => {
        render(<SettingsLayout />, { wrapper: createWrapper() })
        await waitFor(() => {
            expect(screen.getByTestId('mcp-status-panel')).toBeInTheDocument()
        })
    })
})
