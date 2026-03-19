import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'

// ── Types ────────────────────────────────────────────────────────────────

interface DatabaseStatus {
    unlocked: boolean
}

interface HealthResponse {
    status: string
    version: string
    uptime_seconds: number
    database: DatabaseStatus
}

interface VersionResponse {
    version: string
    environment?: string
}

interface GuardStatusResponse {
    is_locked: boolean
    calls_per_hour?: number
}

type IdeTarget = 'cursor' | 'claude-desktop' | 'windsurf'

// ── IDE Config Templates ─────────────────────────────────────────────────

function generateIdeConfig(target: IdeTarget, baseUrl: string): string {
    const serverConfig = {
        url: `${baseUrl}/mcp`,
        headers: {
            Authorization: 'Bearer <your-api-token>',
        },
    }

    const configs: Record<IdeTarget, object> = {
        cursor: {
            mcpServers: {
                zorivest: serverConfig,
            },
        },
        'claude-desktop': {
            mcpServers: {
                zorivest: {
                    ...serverConfig,
                    transport: 'sse',
                },
            },
        },
        windsurf: {
            mcpServers: {
                zorivest: serverConfig,
            },
        },
    }

    return JSON.stringify(configs[target], null, 2)
}

// ── Status Indicators ────────────────────────────────────────────────────

function StatusDot({ ok }: { ok: boolean }) {
    return (
        <span
            className={`inline-block w-2 h-2 rounded-full mr-2 ${ok ? 'bg-green-400' : 'bg-red-400'}`}
            aria-label={ok ? 'OK' : 'Error'}
        />
    )
}

function formatUptime(seconds: number): string {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)
    if (h > 0) return `${h}h ${m}m`
    if (m > 0) return `${m}m ${s}s`
    return `${s}s`
}

// ── Component ────────────────────────────────────────────────────────────

/**
 * MCP Server Status Panel — read-only status display with IDE config generation.
 *
 * REST-only data sources:
 *   - Backend status: GET /api/v1/health
 *   - Version: GET /api/v1/version/
 *   - Database: derived from /api/v1/health (database.unlocked)
 *   - Guard state: GET /api/v1/mcp-guard/status
 *
 * Tool count/uptime: N/A (requires MCP proxy — deferred to MEU-46a)
 */
export default function McpServerStatusPanel() {
    const [ideTarget, setIdeTarget] = useState<IdeTarget>('cursor')
    const [copyFeedback, setCopyFeedback] = useState(false)
    const [refreshing, setRefreshing] = useState(false)
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    // ── Data fetching ────────────────────────────────────────────────
    const { data: health } = useQuery<HealthResponse>({
        queryKey: ['mcp-health'],
        queryFn: () => apiFetch('/api/v1/health'),
        refetchOnWindowFocus: false,
    })

    const { data: version } = useQuery<VersionResponse>({
        queryKey: ['mcp-version'],
        queryFn: () => apiFetch('/api/v1/version/'),
        refetchOnWindowFocus: false,
    })

    const { data: guard } = useQuery<GuardStatusResponse>({
        queryKey: ['mcp-guard-status'],
        queryFn: () => apiFetch('/api/v1/mcp-guard/status'),
        refetchOnWindowFocus: false,
    })

    const handleRefresh = useCallback(async () => {
        setRefreshing(true)
        setStatus('Refreshing MCP status...')
        try {
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ['mcp-health'] }),
                queryClient.invalidateQueries({ queryKey: ['mcp-version'] }),
                queryClient.invalidateQueries({ queryKey: ['mcp-guard-status'] }),
            ])
            setStatus('Status refreshed', 3000)
        } catch {
            setStatus('Refresh failed — backend unreachable', 5000)
        } finally {
            setRefreshing(false)
        }
    }, [queryClient, setStatus])

    const handleCopy = useCallback(async () => {
        const config = generateIdeConfig(ideTarget, window.api?.baseUrl ?? 'http://localhost:8766')
        await navigator.clipboard.writeText(config)
        setCopyFeedback(true)
        setStatus('IDE config copied to clipboard', 2000)
        setTimeout(() => setCopyFeedback(false), 2000)
    }, [ideTarget, setStatus])

    // ── Derived state ────────────────────────────────────────────────
    const backendOk = health?.status === 'ok'
    const dbReachable = health != null
    const dbUnlocked = health?.database?.unlocked === true
    const guardLocked = guard?.is_locked ?? false
    const callsPerHour = guard?.calls_per_hour ?? 0

    const baseUrl = typeof window !== 'undefined' && window.api?.baseUrl
        ? window.api.baseUrl
        : 'http://localhost:8766'
    const ideJson = generateIdeConfig(ideTarget, baseUrl)

    return (
        <div className="space-y-6">
            {/* Status Section */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4" data-testid="mcp-status-panel">
                <h3 className="text-base font-semibold text-fg mb-3">MCP Server Status</h3>

                <div className="grid grid-cols-2 gap-y-2 text-sm">
                    <div><StatusDot ok={backendOk} />Backend</div>
                    <div className="text-fg-muted">{backendOk ? 'OK' : 'Unreachable'}</div>

                    <div><StatusDot ok={!!version} />Version</div>
                    <div className="text-fg-muted">{version?.version ?? '—'}</div>

                    <div><StatusDot ok={dbUnlocked} />Database</div>
                    <div className="text-fg-muted">{!dbReachable ? 'Unreachable' : dbUnlocked ? 'Unlocked' : 'Locked'}</div>

                    <div><StatusDot ok={!guardLocked} />Guard</div>
                    <div className="text-fg-muted">
                        {guardLocked ? '🔒 Locked' : `🟢 Active (${callsPerHour} calls/hr)`}
                    </div>

                    <div className="text-fg-muted">Registered tools</div>
                    <div className="text-fg-muted">{health ? '—' : 'N/A'}</div>

                    <div className="text-fg-muted">Uptime</div>
                    <div className="text-fg-muted">{health?.uptime_seconds != null ? formatUptime(health.uptime_seconds) : 'N/A'}</div>
                </div>

                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    data-testid="mcp-refresh-btn"
                    className="mt-4 px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors disabled:opacity-50 cursor-pointer"
                >
                    {refreshing ? '⏳ Refreshing...' : '🔄 Refresh Status'}
                </button>
            </div>

            {/* IDE Configuration Section */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4" data-testid="mcp-ide-config">
                <h3 className="text-base font-semibold text-fg mb-3">IDE Configuration</h3>
                <p className="text-sm text-fg-muted mb-3">
                    Generate configuration for your AI IDE:
                </p>

                <div className="flex gap-2 mb-3">
                    {(['cursor', 'claude-desktop', 'windsurf'] as const).map((target) => (
                        <button
                            key={target}
                            onClick={() => setIdeTarget(target)}
                            data-testid={`ide-tab-${target}`}
                            className={`px-3 py-1 text-sm font-medium rounded-md border transition-colors cursor-pointer ${ideTarget === target
                                ? 'border-accent bg-accent/10 text-fg'
                                : 'border-bg-subtle bg-bg text-fg-muted hover:bg-bg-elevated hover:text-fg'
                                }`}
                        >
                            {target === 'claude-desktop' ? 'Claude Desktop' : target.charAt(0).toUpperCase() + target.slice(1)}
                        </button>
                    ))}
                </div>

                <pre className="bg-bg rounded-md p-3 text-xs text-fg-muted overflow-x-auto border border-bg-subtle">
                    <code>{ideJson}</code>
                </pre>

                <button
                    onClick={handleCopy}
                    data-testid="ide-copy-btn"
                    className="mt-3 px-4 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                >
                    {copyFeedback ? '✓ Copied!' : '📋 Copy to Clipboard'}
                </button>
            </div>
        </div>
    )
}
