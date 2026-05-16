/**
 * TransactionAudit — audit findings table with severity badges.
 *
 * Posts to POST /api/v1/tax/audit and renders findings.
 * API returns: { findings: [{finding_type, severity, message, lot_id, details}], severity_summary }
 *
 * Source: 06g-gui-tax.md L449–458
 * MEU: MEU-154 (AC-154.15)
 */

import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

/** Matches actual AuditFinding dataclass from API */
interface AuditFinding {
    finding_type: string     // e.g. "missing_basis", "duplicate_lot", "orphaned_lot"
    severity: string         // "error" | "warning" | "info"
    message: string
    lot_id: string
    details: Record<string, unknown>
}

/** Matches actual AuditReport dataclass from API */
interface AuditResult {
    findings: AuditFinding[]
    severity_summary: Record<string, number>  // {"error": N, "warning": N, "info": N}
}

/** Map API severity to display color */
const SEVERITY_COLORS: Record<string, string> = {
    error: 'bg-red-500/10 text-red-400 border-red-500/20',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
}

/** Friendly labels for finding_type */
const FINDING_LABELS: Record<string, string> = {
    missing_basis: 'Missing Cost Basis',
    duplicate_lot: 'Duplicate Lot',
    orphaned_lot: 'Orphaned Lot',
    invalid_proceeds: 'Invalid Proceeds',
}

/** Generate recommendation from finding_type */
function getRecommendation(findingType: string): string {
    switch (findingType) {
        case 'missing_basis': return 'Review and update cost basis for this lot from your broker statement'
        case 'duplicate_lot': return 'Check for duplicate trade imports and remove the extra entry'
        case 'orphaned_lot': return 'Link this closed lot to its originating trade execution'
        case 'invalid_proceeds': return 'Verify sale proceeds — a closed lot should have positive proceeds'
        default: return 'Review this lot for potential data entry issues'
    }
}

export default function TransactionAudit() {
    const auditMutation = useMutation<AuditResult, Error>({
        mutationFn: () =>
            apiFetch('/api/v1/tax/audit', {
                method: 'POST',
                body: JSON.stringify({}),
            }),
    })

    const data = auditMutation.data
    const totalFindings = data?.findings?.length ?? 0
    const summary = data?.severity_summary ?? {}

    return (
        <div data-testid={TAX_TEST_IDS.TX_AUDIT_PANEL} className="space-y-4">
            <TaxHelpCard content={TAX_HELP.audit} />
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    Transaction Audit
                </h3>
                <button
                    data-testid={TAX_TEST_IDS.TX_AUDIT_RUN_BTN}
                    onClick={() => auditMutation.mutate()}
                    disabled={auditMutation.isPending}
                    aria-label="Run audit"
                    className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {auditMutation.isPending ? 'Running…' : <><span aria-hidden="true">🔍</span> Run Audit</>}
                </button>
            </div>

            {auditMutation.error && (
                <div className="text-sm text-red-400">
                    Audit failed: {auditMutation.error.message}
                </div>
            )}

            <div aria-live="polite">
            {data && (
                <>
                    {/* Severity summary bar */}
                    <div className="flex items-center gap-4 text-xs text-fg-muted">
                        <span>{totalFindings} finding{totalFindings !== 1 ? 's' : ''}</span>
                        {(summary.error ?? 0) > 0 && (
                            <span className="text-red-400">⊘ {summary.error} error{(summary.error ?? 0) !== 1 ? 's' : ''}</span>
                        )}
                        {(summary.warning ?? 0) > 0 && (
                            <span className="text-yellow-400">⚠ {summary.warning} warning{(summary.warning ?? 0) !== 1 ? 's' : ''}</span>
                        )}
                        {(summary.info ?? 0) > 0 && (
                            <span className="text-blue-400">ℹ {summary.info} info</span>
                        )}
                    </div>

                    {totalFindings === 0 ? (
                        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-6 text-center text-green-400">
                            <span aria-hidden="true">✅</span> No issues found — all transactions look clean
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {data.findings.map((finding, idx) => (
                                <div
                                    key={finding.lot_id || idx}
                                    data-testid={TAX_TEST_IDS.TX_AUDIT_FINDING_ROW}
                                    className={`rounded-lg border p-4 ${SEVERITY_COLORS[finding.severity] || SEVERITY_COLORS.info}`}
                                >
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded-full border border-current">
                                            {finding.severity}
                                        </span>
                                        <span className="text-sm font-medium">
                                            {FINDING_LABELS[finding.finding_type] || finding.finding_type}
                                        </span>
                                        {finding.lot_id && (
                                            <span className="text-xs text-fg-muted ml-auto font-mono" title={finding.lot_id}>
                                                Lot {finding.lot_id.slice(0, 8)}…
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-sm mb-2">{finding.message}</p>
                                    <p className="text-xs text-fg-muted">
                                        <span aria-hidden="true">💡</span> {getRecommendation(finding.finding_type)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
            </div>

            {!data && !auditMutation.isPending && (
                <div className="flex items-center justify-center h-32 text-fg-muted text-sm">
                    Click "Run Audit" to analyze your transactions for tax issues
                </div>
            )}
        </div>
    )
}
