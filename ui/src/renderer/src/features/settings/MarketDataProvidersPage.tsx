/**
 * MarketDataProvidersPage — MEU-65.
 *
 * List+detail split layout for configuring all 12 market data providers.
 * Source: docs/build-plan/06f-gui-settings.md §Market Data Settings Page.
 */

import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'

// Electron preload bridge type
declare global {
    interface Window {
        electron: { openExternal: (url: string) => void }
    }
}

// ── Types (G6: exact API field names from ProviderStatus) ────────────────────

export interface ProviderStatus {
    provider_name: string
    is_enabled: boolean
    has_api_key: boolean
    rate_limit: number
    timeout: number
    last_test_status: string | null
    signup_url: string | null
}

interface ProviderForm {
    api_key: string
    api_secret: string
    rate_limit: number
    timeout: number
    is_enabled: boolean
}

// Providers that require dual credentials (api_key + api_secret)
const DUAL_AUTH_PROVIDERS = new Set(['Alpaca'])

// Providers that need no API key at all
const FREE_PROVIDERS = new Set(['Yahoo Finance', 'TradingView'])

// ── Status icon helper ────────────────────────────────────────────────────────

function statusIcon(status: string | null): string {
    if (status === 'success') return '✅'
    if (status === 'failed') return '❌'
    return '⚪'
}

function buildForm(p: ProviderStatus): ProviderForm {
    return {
        api_key: '',
        api_secret: '',
        rate_limit: p.rate_limit,
        timeout: p.timeout,
        is_enabled: p.is_enabled,
    }
}

// ── Component ─────────────────────────────────────────────────────────────────

export function MarketDataProvidersPage() {
    const [selectedName, setSelectedName] = useState<string | null>(null)
    const [form, setForm] = useState<ProviderForm>({
        api_key: '',
        api_secret: '',
        rate_limit: 5,
        timeout: 30,
        is_enabled: false,
    })
    const [testResult, setTestResult] = useState<string | null>(null)
    const [testingAll, setTestingAll] = useState(false)
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    // Fetch providers (G5: 5s auto-refresh)
    const { data: providers = [] } = useQuery<ProviderStatus[]>({
        queryKey: ['market-providers'],
        queryFn: async () => {
            try {
                return await apiFetch<ProviderStatus[]>('/api/v1/market-data/providers')
            } catch {
                return []
            }
        },
        refetchInterval: 5_000,
    })

    const selectedProvider = providers.find((p) => p.provider_name === selectedName) ?? null

    const handleSelect = useCallback((provider: ProviderStatus) => {
        setSelectedName(provider.provider_name)
        setForm(buildForm(provider))
        setTestResult(null)
    }, [])

    const updateField = useCallback(<K extends keyof ProviderForm>(key: K, value: ProviderForm[K]) => {
        setForm((prev) => ({ ...prev, [key]: value }))
    }, [])

    // Save Changes (AC-3, AC-7, AC-8, AC-13)
    const handleSave = useCallback(async () => {
        if (!selectedName) return
        const payload: Record<string, unknown> = {
            rate_limit: form.rate_limit,
            timeout: form.timeout,
            is_enabled: form.is_enabled,
        }
        if (form.api_key) payload.api_key = form.api_key
        if (form.api_secret && DUAL_AUTH_PROVIDERS.has(selectedName)) {
            payload.api_secret = form.api_secret
        }
        try {
            setStatus('Saving...')
            await apiFetch(`/api/v1/market-data/providers/${selectedName}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            })
            await queryClient.invalidateQueries({ queryKey: ['market-providers'] })
            setStatus('Saved')
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed to save'}`)
        }
    }, [selectedName, form, queryClient, setStatus])

    // Test Connection (AC-4)
    const handleTest = useCallback(async () => {
        if (!selectedName) return
        try {
            setStatus('Testing connection...')
            setTestResult(null)
            const result = await apiFetch<{ success: boolean; message: string }>(
                `/api/v1/market-data/providers/${selectedName}/test`,
                { method: 'POST' }
            )
            await queryClient.invalidateQueries({ queryKey: ['market-providers'] })
            setTestResult(result.message)
            setStatus(result.success ? 'Connection successful' : `Test failed: ${result.message}`)
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Test failed'
            setTestResult(msg)
            setStatus(`Error: ${msg}`)
        }
    }, [selectedName, queryClient, setStatus])

    // Test All Connections (AC-5)
    const handleTestAll = useCallback(async () => {
        const targets = providers.filter((p) => p.has_api_key)
        if (targets.length === 0) {
            setStatus('No providers with API keys to test')
            return
        }
        setTestingAll(true)
        setStatus(`Testing ${targets.length} providers...`)
        let passed = 0
        for (const p of targets) {
            try {
                const result = await apiFetch<{ success: boolean; message: string }>(
                    `/api/v1/market-data/providers/${p.provider_name}/test`,
                    { method: 'POST' }
                )
                if (result.success) passed++
            } catch {
                // continue testing others
            }
        }
        await queryClient.invalidateQueries({ queryKey: ['market-providers'] })
        setTestingAll(false)
        setStatus(`Test all complete: ${passed}/${targets.length} passed`)
    }, [providers, queryClient, setStatus])

    // Remove Key (AC-9, G2: disabled when no key)
    const handleRemoveKey = useCallback(async () => {
        if (!selectedName || !selectedProvider?.has_api_key) return
        try {
            setStatus('Removing API key...')
            await apiFetch(`/api/v1/market-data/providers/${selectedName}/key`, {
                method: 'DELETE',
            })
            await queryClient.invalidateQueries({ queryKey: ['market-providers'] })
            setForm((prev) => ({ ...prev, api_key: '', api_secret: '' }))
            setStatus('API key removed')
        } catch (err) {
            setStatus(`Error: ${err instanceof Error ? err.message : 'Failed to remove key'}`)
        }
    }, [selectedName, selectedProvider, queryClient, setStatus])

    const isDualAuth = selectedName !== null && DUAL_AUTH_PROVIDERS.has(selectedName)
    const isFree = selectedName !== null && FREE_PROVIDERS.has(selectedName)

    return (
        <div data-testid="market-data-providers" className="flex h-full">
            {/* Left panel: provider list (AC-1, AC-6) */}
            <div className="w-64 shrink-0 border-r border-bg-subtle overflow-y-auto">
                <div className="p-3 border-b border-bg-subtle">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-semibold text-fg">Market Data Providers</h2>
                        <button
                            data-testid="provider-test-all-btn"
                            onClick={handleTestAll}
                            disabled={testingAll}
                            className="px-2 py-1 text-xs rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {testingAll ? 'Testing…' : 'Test All'}
                        </button>
                    </div>
                    <div className="mt-1 text-xs text-fg-muted" aria-label="Legend: connected, failed, not tested">
                        <span aria-hidden="true">✅</span> connected
                        {' '}<span aria-hidden="true">❌</span> failed
                        {' '}<span aria-hidden="true">⚪</span> not tested
                    </div>
                </div>

                <ul data-testid="provider-list" className="py-1">
                    {providers.map((provider) => (
                        <li key={provider.provider_name}>
                            <button
                                data-testid="provider-item"
                                aria-label={`${provider.provider_name} — ${provider.last_test_status ?? 'not tested'}${!provider.is_enabled ? ', disabled' : ''}`}
                                onClick={() => handleSelect(provider)}
                                className={`w-full text-left px-3 py-2 text-sm transition-colors cursor-pointer flex items-center gap-2 ${selectedName === provider.provider_name
                                    ? 'bg-accent/10 text-accent'
                                    : 'text-fg hover:bg-bg-elevated'
                                    }`}
                            >
                                <span aria-hidden="true">{statusIcon(provider.last_test_status)}</span>
                                <span className="flex-1 truncate">{provider.provider_name}</span>
                                {!provider.is_enabled && (
                                    <span className="text-xs text-fg-muted" aria-hidden="true">off</span>
                                )}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Right panel: provider detail (AC-2) */}
            {selectedProvider ? (
                <div
                    data-testid="provider-detail"
                    className="flex-1 overflow-y-auto p-4 space-y-4"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <h2 className="text-base font-semibold text-fg">
                            {selectedProvider.provider_name}
                        </h2>
                        <span className="text-sm" aria-hidden="true">
                            {statusIcon(selectedProvider.last_test_status)}
                        </span>
                    </div>

                    {/* API Configuration — hidden for free providers */}
                    {isFree ? (
                        <div className="flex items-center gap-2 p-3 rounded-md border border-green-500/30 bg-green-500/10">
                            <span className="text-green-400 text-sm" aria-hidden="true">✅</span>
                            <div>
                                <div className="text-sm font-medium text-green-400">Free — no API key required</div>
                                <div className="text-xs text-fg-muted">This provider works without authentication</div>
                            </div>
                        </div>
                    ) : (
                        <section className="space-y-3 p-3 rounded-md border border-bg-subtle bg-bg-elevated">
                            <h3 className="text-xs font-semibold text-fg-muted uppercase tracking-wide">
                                API Configuration <span aria-hidden="true">🔒</span>
                            </h3>

                            {/* API Key (AC-3) */}
                            <div>
                                <label htmlFor="provider-api-key" className="block text-xs text-fg-muted mb-1">
                                    API Key
                                </label>
                                <input
                                    id="provider-api-key"
                                    data-testid="provider-api-key-input"
                                    type="password"
                                    value={form.api_key}
                                    onChange={(e) => updateField('api_key', e.target.value)}
                                    placeholder={selectedProvider.has_api_key ? '••••••••' : 'Enter API key'}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                />
                            </div>

                            {/* API Secret — Alpaca only (AC-13) */}
                            {isDualAuth && (
                                <div>
                                    <label htmlFor="provider-api-secret" className="block text-xs text-fg-muted mb-1">
                                        API Secret
                                    </label>
                                    <input
                                        id="provider-api-secret"
                                        data-testid="provider-api-secret-input"
                                        type="password"
                                        value={form.api_secret}
                                        onChange={(e) => updateField('api_secret', e.target.value)}
                                        placeholder={selectedProvider.has_api_key ? '••••••••' : 'Enter API secret'}
                                        className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                    />
                                </div>
                            )}
                        </section>
                    )}

                    {/* Rate Limiting (AC-7) */}
                    <section className="space-y-3 p-3 rounded-md border border-bg-subtle bg-bg-elevated">
                        <h3 className="text-xs font-semibold text-fg-muted uppercase tracking-wide">
                            Rate Limiting
                        </h3>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label htmlFor="provider-rate-limit" className="block text-xs text-fg-muted mb-1">
                                    Requests / min
                                </label>
                                <input
                                    id="provider-rate-limit"
                                    data-testid="provider-rate-limit-input"
                                    type="number"
                                    min={1}
                                    value={form.rate_limit}
                                    onChange={(e) =>
                                        updateField('rate_limit', parseInt(e.target.value, 10) || 1)
                                    }
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                />
                            </div>
                            <div>
                                <label htmlFor="provider-timeout" className="block text-xs text-fg-muted mb-1">
                                    Timeout (s)
                                </label>
                                <input
                                    id="provider-timeout"
                                    data-testid="provider-timeout-input"
                                    type="number"
                                    min={1}
                                    value={form.timeout}
                                    onChange={(e) =>
                                        updateField('timeout', parseInt(e.target.value, 10) || 1)
                                    }
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                />
                            </div>
                        </div>
                    </section>

                    {/* Enable toggle + Connection Status */}
                    <section className="space-y-3 p-3 rounded-md border border-bg-subtle bg-bg-elevated">
                        <h3 className="text-xs font-semibold text-fg-muted uppercase tracking-wide">
                            Connection Status
                        </h3>
                        <div className="flex items-center gap-2">
                            <input
                                data-testid="provider-enable-toggle"
                                type="checkbox"
                                id="provider-enable"
                                checked={form.is_enabled}
                                onChange={(e) => updateField('is_enabled', e.target.checked)}
                                className="w-4 h-4 accent-accent cursor-pointer"
                            />
                            <label htmlFor="provider-enable" className="text-sm text-fg cursor-pointer">
                                Enabled
                            </label>
                        </div>

                        <div className="text-sm text-fg">
                            <span aria-hidden="true">{statusIcon(selectedProvider.last_test_status)}</span>{' '}
                            {testResult ?? (
                                selectedProvider.last_test_status === 'success'
                                    ? 'Connection successful'
                                    : selectedProvider.last_test_status === 'failed'
                                        ? 'Last test failed'
                                        : 'Not yet tested'
                            )}
                        </div>

                        <button
                            data-testid="provider-test-btn"
                            onClick={handleTest}
                            className="px-3 py-1.5 text-sm rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                        >
                            Test Connection
                        </button>
                    </section>

                    {/* Provider Info (AC-14) */}
                    <section className="space-y-2 p-3 rounded-md border border-bg-subtle bg-bg-elevated">
                        <h3 className="text-xs font-semibold text-fg-muted uppercase tracking-wide">
                            Provider Info
                        </h3>
                        <div className="text-xs text-fg-muted space-y-1">
                            <div>
                                Default rate limit: {selectedProvider.rate_limit} req/min
                            </div>
                            <div>Default timeout: {selectedProvider.timeout}s</div>
                        </div>
                    </section>

                    {/* Action Buttons (G1: borders, G2) */}
                    <div className="flex gap-2 pt-2 border-t border-bg-subtle">
                        <button
                            data-testid="provider-save-btn"
                            onClick={handleSave}
                            className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer"
                        >
                            Save Changes
                        </button>
                        <button
                            data-testid="provider-remove-key-btn"
                            onClick={handleRemoveKey}
                            disabled={!selectedProvider.has_api_key}
                            className="px-4 py-1.5 text-sm rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            Remove Key
                        </button>
                    </div>

                    {/* Get API Key deep-link */}
                    {selectedProvider.signup_url && (
                        <button
                            data-testid="provider-get-api-key-btn"
                            onClick={() => window.electron.openExternal(selectedProvider.signup_url!)}
                            className="w-full px-4 py-2 text-sm rounded-md border border-accent/40 text-accent hover:bg-accent/10 transition-colors cursor-pointer flex items-center justify-center gap-2"
                        >
                            {isFree ? '📖 View Documentation' : '🔑 Get API Key'}
                        </button>
                    )}
                </div>
            ) : (
                <div className="flex-1 flex items-center justify-center text-fg-muted text-sm">
                    Select a provider to configure
                </div>
            )}
        </div>
    )
}
