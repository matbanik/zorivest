import { useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'
import { useTheme } from '@/hooks/useTheme'
import McpServerStatusPanel from './McpServerStatusPanel'

interface GuardStatusResponse {
    is_locked: boolean
    calls_per_hour?: number
}

/**
 * Settings Layout — full settings page with MCP Status panel and MCP Guard controls.
 *
 * Required data-testids (from test-ids.ts):
 *   - settings-page: root element
 *   - mcp-guard-lock-toggle: lock/unlock toggle button
 *   - mcp-guard-status: guard status indicator
 */
export default function SettingsLayout() {
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()
    const [theme, setTheme] = useTheme()

    const { data: guardStatus } = useQuery<GuardStatusResponse>({
        queryKey: ['mcp-guard-status'],
        queryFn: () => apiFetch('/api/v1/mcp-guard/status'),
    })

    const lockMutation = useMutation({
        mutationFn: async () => {
            const action = guardStatus?.is_locked ? 'unlock' : 'lock'
            setStatus(`${action === 'lock' ? 'Locking' : 'Unlocking'} MCP Guard...`)
            const endpoint = `/api/v1/mcp-guard/${action}`
            await apiFetch(endpoint, { method: 'POST' })
        },
        onSuccess: () => {
            const wasLocked = guardStatus?.is_locked
            setStatus(`MCP Guard ${wasLocked ? 'unlocked' : 'locked'} successfully`, 3000)
            queryClient.invalidateQueries({ queryKey: ['mcp-guard-status'] })
        },
        onError: (err: Error) => {
            setStatus(`Guard toggle failed: ${err.message}`, 5000)
        },
    })

    const handleToggle = useCallback(() => {
        lockMutation.mutate()
    }, [lockMutation])

    const isLocked = guardStatus?.is_locked ?? false

    return (
        <div data-testid="settings-page" className="space-y-8 max-w-3xl">
            <div>
                <h2 className="text-lg font-semibold text-fg mb-6">Settings</h2>
            </div>

            {/* Theme Toggle */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4">
                <h3 className="text-base font-semibold text-fg mb-3">Appearance</h3>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-fg-muted">Theme</span>
                    <div className="flex gap-2">
                        <button
                            data-testid="theme-dark-btn"
                            onClick={() => setTheme('dark')}
                            className={`px-4 py-1.5 text-sm font-medium rounded-md border transition-colors cursor-pointer ${theme === 'dark'
                                    ? 'bg-accent-purple text-fg border-accent-purple'
                                    : 'bg-bg border-bg-subtle text-fg-muted hover:bg-bg-elevated hover:text-fg'
                                }`}
                        >
                            🌙 Dark
                        </button>
                        <button
                            data-testid="theme-light-btn"
                            onClick={() => setTheme('light')}
                            className={`px-4 py-1.5 text-sm font-medium rounded-md border transition-colors cursor-pointer ${theme === 'light'
                                    ? 'bg-accent-purple text-fg border-accent-purple'
                                    : 'bg-bg border-bg-subtle text-fg-muted hover:bg-bg-elevated hover:text-fg'
                                }`}
                        >
                            ☀️ Light
                        </button>
                    </div>
                </div>
            </div>

            {/* MCP Guard Controls */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4">
                <h3 className="text-base font-semibold text-fg mb-3">MCP Guard</h3>
                <div className="flex items-center gap-4">
                    <span
                        data-testid="mcp-guard-status"
                        className={`text-sm font-medium ${isLocked ? 'text-red-400' : 'text-green-400'}`}
                    >
                        {isLocked ? '🔒 Locked' : '🟢 Unlocked'}
                    </span>
                    <button
                        data-testid="mcp-guard-lock-toggle"
                        onClick={handleToggle}
                        disabled={lockMutation.isPending}
                        className="px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors disabled:opacity-50 cursor-pointer"
                    >
                        {lockMutation.isPending ? '⏳ Working...' : isLocked ? '🔓 Unlock' : '🔒 Lock'}
                    </button>
                </div>
            </div>

            {/* MCP Server Status Panel */}
            <McpServerStatusPanel />
        </div>
    )
}
