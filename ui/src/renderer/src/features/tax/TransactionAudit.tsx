/**
 * TransactionAudit — audit findings table with severity badges.
 *
 * Posts to POST /api/v1/tax/audit and renders findings.
 *
 * Source: 06g-gui-tax.md L449–458
 * MEU: MEU-154 (AC-154.15)
 */

import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'

interface AuditFinding {
    id: string
    severity: 'high' | 'medium' | 'low' | 'info'
    category: string
    description: string
    affected_trades: number
    recommendation: string
}

interface AuditResult {
    findings: AuditFinding[]
    total_trades_audited: number
    audit_timestamp: string
}

const SEVERITY_COLORS: Record<string, string> = {
    high: 'bg-red-500/10 text-red-400 border-red-500/20',
    medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    info: 'bg-bg-subtle text-fg-muted border-bg-subtle',
}

export default function TransactionAudit() {
    const auditMutation = useMutation<AuditResult, Error>({
        mutationFn: () =>
            apiFetch('/api/v1/tax/audit', {
                method: 'POST',
                body: JSON.stringify({}),
            }),
    })

    return (
        <div data-testid={TAX_TEST_IDS.TX_AUDIT_PANEL} className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    Transaction Audit
                </h3>
                <button
                    data-testid={TAX_TEST_IDS.TX_AUDIT_RUN_BTN}
                    onClick={() => auditMutation.mutate()}
                    disabled={auditMutation.isPending}
                    className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {auditMutation.isPending ? 'Running…' : '🔍 Run Audit'}
                </button>
            </div>

            {auditMutation.error && (
                <div className="text-sm text-red-400">
                    Audit failed: {auditMutation.error.message}
                </div>
            )}

            {auditMutation.data && (
                <>
                    <div className="text-xs text-fg-muted">
                        Audited {auditMutation.data.total_trades_audited} trades ·{' '}
                        {auditMutation.data.findings.length} finding{auditMutation.data.findings.length !== 1 ? 's' : ''}
                    </div>

                    {auditMutation.data.findings.length === 0 ? (
                        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-6 text-center text-green-400">
                            ✅ No issues found — all transactions look clean
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {auditMutation.data.findings.map((finding) => (
                                <div
                                    key={finding.id}
                                    data-testid={TAX_TEST_IDS.TX_AUDIT_FINDING_ROW}
                                    className={`rounded-lg border p-4 ${SEVERITY_COLORS[finding.severity] || SEVERITY_COLORS.info}`}
                                >
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded-full border border-current">
                                            {finding.severity}
                                        </span>
                                        <span className="text-sm font-medium">{finding.category}</span>
                                        <span className="text-xs text-fg-muted ml-auto">
                                            {finding.affected_trades} trade{finding.affected_trades !== 1 ? 's' : ''} affected
                                        </span>
                                    </div>
                                    <p className="text-sm mb-2">{finding.description}</p>
                                    <p className="text-xs text-fg-muted">
                                        💡 {finding.recommendation}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}

            {!auditMutation.data && !auditMutation.isPending && (
                <div className="flex items-center justify-center h-32 text-fg-muted text-sm">
                    Click "Run Audit" to analyze your transactions for tax issues
                </div>
            )}
        </div>
    )
}
