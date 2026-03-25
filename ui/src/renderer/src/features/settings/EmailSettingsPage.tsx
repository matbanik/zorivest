import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { useStatusBar } from '@/hooks/useStatusBar'

interface EmailConfig {
    provider_preset: string | null
    smtp_host: string | null
    port: number | null
    security: string | null
    username: string | null
    has_password: boolean
    from_email: string | null
}

interface TestResult {
    success: boolean
    message: string
}

const PRESETS: Record<string, { smtp_host: string; port: number; security: string }> = {
    Gmail: { smtp_host: 'smtp.gmail.com', port: 587, security: 'STARTTLS' },
    Brevo: { smtp_host: 'smtp-relay.brevo.com', port: 587, security: 'STARTTLS' },
    SendGrid: { smtp_host: 'smtp.sendgrid.net', port: 587, security: 'STARTTLS' },
    Outlook: { smtp_host: 'smtp-mail.outlook.com', port: 587, security: 'STARTTLS' },
    Yahoo: { smtp_host: 'smtp.mail.yahoo.com', port: 465, security: 'SSL' },
    Custom: { smtp_host: '', port: 587, security: 'STARTTLS' },
}

export default function EmailSettingsPage() {
    const queryClient = useQueryClient()
    const { setStatus } = useStatusBar()

    const { data: config, isLoading } = useQuery<EmailConfig>({
        queryKey: ['email-config'],
        queryFn: () => apiFetch('/api/v1/settings/email'),
    })

    const [form, setForm] = useState({
        provider_preset: '',
        smtp_host: '',
        port: 587,
        security: 'STARTTLS',
        username: '',
        password: '',
        from_email: '',
    })
    const [testResult, setTestResult] = useState<TestResult | null>(null)
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

    useEffect(() => {
        if (config) {
            setForm(prev => ({
                ...prev,
                provider_preset: config.provider_preset ?? '',
                smtp_host: config.smtp_host ?? '',
                port: config.port ?? 587,
                security: config.security ?? 'STARTTLS',
                username: config.username ?? '',
                from_email: config.from_email ?? '',
            }))
        }
    }, [config])

    const handlePresetChange = (preset: string) => {
        setForm(prev => ({
            ...prev,
            provider_preset: preset,
            ...(PRESETS[preset] ?? {}),
        }))
    }

    const saveMutation = useMutation({
        mutationFn: () =>
            apiFetch('/api/v1/settings/email', {
                method: 'PUT',
                body: JSON.stringify(form),
            }),
        onSuccess: () => {
            setStatus('Email settings saved ✓', 3000)
            setFieldErrors({})
            queryClient.invalidateQueries({ queryKey: ['email-config'] })
        },
        onError: (err: Error & { detail?: string }) => {
            setStatus(`Save failed: ${err.message}`, 5000)
        },
    })

    const testMutation = useMutation<TestResult, Error>({
        mutationFn: () =>
            apiFetch('/api/v1/settings/email/test', { method: 'POST' }) as Promise<TestResult>,
        onSuccess: (data: TestResult) => {
            setTestResult(data)
        },
        onError: () => {
            setTestResult({ success: false, message: 'Connection test failed.' })
        },
    })

    if (isLoading) return <div className="text-fg-muted">Loading…</div>

    return (
        <div data-testid="email-settings-page" className="space-y-6 max-w-2xl">
            <div>
                <h2 className="text-lg font-semibold text-fg mb-1">Email Provider</h2>
                <p className="text-sm text-fg-muted">
                    Configure SMTP credentials for trade notifications and alerts.
                </p>
            </div>

            {/* Provider Preset */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4 space-y-4">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    Provider Preset
                </h3>
                <div className="flex flex-wrap gap-2">
                    {Object.keys(PRESETS).map((preset) => (
                        <button
                            key={preset}
                            data-testid={`preset-${preset.toLowerCase()}`}
                            onClick={() => handlePresetChange(preset)}
                            className={`px-3 py-1.5 text-sm rounded-md border transition-colors cursor-pointer ${form.provider_preset === preset
                                ? 'bg-accent-purple text-fg border-accent-purple'
                                : 'bg-bg border-bg-subtle text-fg-muted hover:bg-bg-elevated hover:text-fg'
                                }`}
                        >
                            {preset}
                        </button>
                    ))}
                </div>
            </div>

            {/* SMTP Fields */}
            <div className="bg-bg-elevated rounded-lg border border-bg-subtle p-4 space-y-4">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    SMTP Configuration
                </h3>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs text-fg-muted mb-1">SMTP Host</label>
                        <input
                            data-testid="smtp-host-input"
                            type="text"
                            value={form.smtp_host}
                            onChange={(e) => setForm(prev => ({ ...prev, smtp_host: e.target.value }))}
                            placeholder="smtp.example.com"
                            className="w-full bg-bg border border-bg-subtle rounded px-3 py-2 text-sm text-fg placeholder-fg-muted focus:outline-none focus:border-accent-purple"
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-fg-muted mb-1">Port</label>
                        <input
                            data-testid="smtp-port-input"
                            type="number"
                            value={form.port}
                            onChange={(e) => setForm(prev => ({ ...prev, port: Number(e.target.value) }))}
                            className="w-full bg-bg border border-bg-subtle rounded px-3 py-2 text-sm text-fg focus:outline-none focus:border-accent-purple"
                        />
                    </div>
                </div>

                {/* Security */}
                <div>
                    <label className="block text-xs text-fg-muted mb-2">Security</label>
                    <div className="flex gap-3">
                        {['STARTTLS', 'SSL'].map((sec) => (
                            <label
                                key={sec}
                                data-testid={`security-${sec.toLowerCase()}`}
                                className="flex items-center gap-2 cursor-pointer"
                            >
                                <input
                                    type="radio"
                                    name="security"
                                    value={sec}
                                    checked={form.security === sec}
                                    onChange={() => setForm(prev => ({ ...prev, security: sec }))}
                                    className="accent-accent-purple"
                                />
                                <span className="text-sm text-fg">{sec}</span>
                            </label>
                        ))}
                    </div>
                </div>

                {/* Credentials */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs text-fg-muted mb-1">Username</label>
                        <input
                            data-testid="smtp-username-input"
                            type="text"
                            value={form.username}
                            onChange={(e) => setForm(prev => ({ ...prev, username: e.target.value }))}
                            placeholder="user@example.com"
                            className="w-full bg-bg border border-bg-subtle rounded px-3 py-2 text-sm text-fg placeholder-fg-muted focus:outline-none focus:border-accent-purple"
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-fg-muted mb-1">
                            Password{' '}
                            {config?.has_password && (
                                <span data-testid="password-stored-indicator" className="text-fg-muted">
                                    (••••• stored)
                                </span>
                            )}
                        </label>
                        <input
                            data-testid="smtp-password-input"
                            type="password"
                            value={form.password}
                            onChange={(e) => setForm(prev => ({ ...prev, password: e.target.value }))}
                            placeholder={config?.has_password ? 'Leave blank to keep existing' : 'Enter password'}
                            className="w-full bg-bg border border-bg-subtle rounded px-3 py-2 text-sm text-fg placeholder-fg-muted focus:outline-none focus:border-accent-purple"
                        />
                    </div>
                </div>

                {/* From Email */}
                <div>
                    <label className="block text-xs text-fg-muted mb-1">From Email</label>
                    <input
                        data-testid="smtp-from-email-input"
                        type="email"
                        value={form.from_email}
                        onChange={(e) => setForm(prev => ({ ...prev, from_email: e.target.value }))}
                        placeholder="noreply@example.com"
                        className="w-full bg-bg border border-bg-subtle rounded px-3 py-2 text-sm text-fg placeholder-fg-muted focus:outline-none focus:border-accent-purple"
                    />
                </div>

                {/* Field errors */}
                {Object.keys(fieldErrors).length > 0 && (
                    <div className="space-y-1">
                        {Object.entries(fieldErrors).map(([field, msg]) => (
                            <p key={field} className="text-xs text-red-400">
                                {field}: {msg}
                            </p>
                        ))}
                    </div>
                )}
            </div>

            {/* Test Result */}
            {testResult && (
                <div
                    data-testid="test-connection-result"
                    className={`rounded-lg border p-3 text-sm ${testResult.success
                        ? 'border-green-500/30 bg-green-500/10 text-green-400'
                        : 'border-red-500/30 bg-red-500/10 text-red-400'
                        }`}
                >
                    {testResult.success ? '✅' : '❌'} {testResult.message}
                </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
                <button
                    data-testid="test-connection-btn"
                    onClick={() => testMutation.mutate()}
                    disabled={testMutation.isPending}
                    className="px-4 py-2 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors disabled:opacity-50 cursor-pointer"
                >
                    {testMutation.isPending ? '⏳ Testing…' : '⚡ Test Connection'}
                </button>
                <button
                    data-testid="save-email-settings-btn"
                    onClick={() => saveMutation.mutate()}
                    disabled={saveMutation.isPending}
                    className="px-4 py-2 text-sm font-medium rounded-md bg-accent-purple text-fg hover:bg-accent-purple/90 transition-colors disabled:opacity-50 cursor-pointer"
                >
                    {saveMutation.isPending ? '⏳ Saving…' : '💾 Save'}
                </button>
            </div>
        </div>
    )
}
