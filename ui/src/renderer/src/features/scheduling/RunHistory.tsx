/**
 * RunHistory — pipeline run history table.
 *
 * Displays a table of past pipeline runs with:
 * - Timestamp, Status (✅/❌), Duration, Error details
 * - Click to expand run detail with step statuses
 * - Search/filter input for filtering entries
 * - Pagination (25 per page) to prevent UI freeze with large datasets
 *
 * Source: 06e-gui-scheduling.md §Pipeline Run History
 * MEU: MEU-72 (gui-scheduling)
 */

import { useState, useCallback, useMemo, Fragment } from 'react'
import { SCHEDULING_TEST_IDS } from './test-ids'
import { formatTimestamp } from '@/lib/formatDate'
import type { PipelineRun } from './api'
import { useRunDetail } from './hooks'

// ── Constants ──────────────────────────────────────────────────────────

const PAGE_SIZE = 25

// ── Helpers ────────────────────────────────────────────────────────────

interface RunHistoryProps {
    runs: PipelineRun[]
    isLoading: boolean
    /** IANA timezone for timestamp display (e.g., 'America/New_York'). */
    timezone?: string
}

function formatDuration(ms: number | null): string {
    if (ms === null) return '—'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
}

// formatTimestamp is imported from '@/lib/formatDate' (timezone-aware)

function statusIcon(status: string): string {
    switch (status) {
        case 'completed':
            return '✅'
        case 'failed':
            return '❌'
        case 'running':
            return '🔄'
        case 'pending':
            return '⏳'
        default:
            return '⚪'
    }
}

function statusClass(status: string): string {
    switch (status) {
        case 'completed':
            return 'text-accent-green'
        case 'failed':
            return 'text-accent-red'
        case 'running':
            return 'text-accent-cyan'
        case 'pending':
            return 'text-accent-orange'
        default:
            return 'text-fg-muted'
    }
}

// ── RunDetailExpanded ──────────────────────────────────────────────────

function RunDetailExpanded({ runId }: { runId: string }) {
    const { data: detail, isLoading: detailLoading } = useRunDetail(runId)

    if (detailLoading) {
        return (
            <tr>
                <td colSpan={4} className="px-3 py-2 text-xs text-fg-muted">
                    Loading steps…
                </td>
            </tr>
        )
    }

    if (!detail?.steps?.length) {
        return (
            <tr>
                <td colSpan={4} className="px-3 py-2 text-xs text-fg-muted">
                    No step data available.
                </td>
            </tr>
        )
    }

    return (
        <tr data-testid={SCHEDULING_TEST_IDS.RUN_DETAIL_PANEL}>
            <td colSpan={4} className="px-3 py-2 bg-bg/50">
                <div className="space-y-1">
                    {detail.steps.map((step) => (
                        <div
                            key={step.step_id}
                            data-testid={SCHEDULING_TEST_IDS.STEP_STATUS}
                            className="flex items-center gap-3 text-xs"
                        >
                            <span className={statusClass(step.status)}>
                                {statusIcon(step.status)}
                            </span>
                            <span className="font-mono text-fg min-w-[120px]">
                                {step.step_type}
                            </span>
                            <span className="text-fg-muted">
                                {formatDuration(step.duration_ms)}
                            </span>
                            {step.error && (
                                <span className="text-accent-red break-words" title={step.error}>
                                    {step.error}
                                </span>
                            )}
                            {step.attempt > 1 && (
                                <span className="text-accent-orange text-[10px]">
                                    (attempt {step.attempt})
                                </span>
                            )}
                        </div>
                    ))}
                </div>
            </td>
        </tr>
    )
}

// ── RunHistory ─────────────────────────────────────────────────────────

export default function RunHistory({ runs: rawRuns, isLoading, timezone }: RunHistoryProps) {
    // F1: Defensive normalization — API may return {} instead of [] when
    // useQuery data is not undefined (so the `= []` default doesn't apply)
    const runs = Array.isArray(rawRuns) ? rawRuns : []
    const [expandedRunId, setExpandedRunId] = useState<string | null>(null)
    const [searchQuery, setSearchQuery] = useState('')
    const [currentPage, setCurrentPage] = useState(0)

    const toggleExpand = useCallback((runId: string) => {
        setExpandedRunId((prev) => (prev === runId ? null : runId))
    }, [])

    // Filter runs based on search query
    const filteredRuns = useMemo(() => {
        if (!searchQuery.trim()) return runs
        const q = searchQuery.toLowerCase()
        return runs.filter((run) => {
            const timestamp = formatTimestamp(run.started_at, timezone).toLowerCase()
            const status = run.status.toLowerCase()
            const error = (run.error || '').toLowerCase()
            const trigger = (run.trigger_type || '').toLowerCase()
            const dryLabel = run.dry_run ? 'dry run' : ''
            return (
                timestamp.includes(q) ||
                status.includes(q) ||
                error.includes(q) ||
                trigger.includes(q) ||
                dryLabel.includes(q)
            )
        })
    }, [runs, searchQuery, timezone])

    // Reset page when search changes
    const handleSearchChange = useCallback((value: string) => {
        setSearchQuery(value)
        setCurrentPage(0)
    }, [])

    // Pagination
    const totalPages = Math.max(1, Math.ceil(filteredRuns.length / PAGE_SIZE))
    const pagedRuns = useMemo(
        () => filteredRuns.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE),
        [filteredRuns, currentPage],
    )

    if (isLoading && runs.length === 0) {
        return (
            <div className="p-3 text-xs text-fg-muted text-center">
                Loading run history…
            </div>
        )
    }

    if (runs.length === 0) {
        return (
            <div className="p-3 text-xs text-fg-muted text-center">
                No runs yet for this policy.
            </div>
        )
    }

    return (
        <div data-testid={SCHEDULING_TEST_IDS.RUN_HISTORY_TABLE}>
            {/* Search input */}
            <div className="px-3 py-1.5">
                <input
                    data-testid="run-history-search"
                    type="text"
                    placeholder="Filter runs…"
                    value={searchQuery}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    className="w-full px-2 py-1 text-xs rounded-md bg-bg border border-bg-subtle text-fg placeholder:text-fg-muted/50 focus:outline-none focus:border-accent-cyan"
                />
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-xs text-fg-muted uppercase tracking-wider">
                            <th className="text-left px-3 py-1.5">Timestamp</th>
                            <th className="text-left px-3 py-1.5">Status</th>
                            <th className="text-left px-3 py-1.5">Duration</th>
                            <th className="text-left px-3 py-1.5">Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {pagedRuns.map((run) => (
                            <Fragment key={run.run_id}>
                                <tr
                                    data-testid={SCHEDULING_TEST_IDS.RUN_HISTORY_ROW}
                                    onClick={() => toggleExpand(run.run_id)}
                                    className="border-t border-bg-subtle/20 hover:bg-bg-elevated/30 cursor-pointer transition-colors"
                                >
                                    <td className="px-3 py-1.5 text-fg tabular-nums">
                                        {formatTimestamp(run.started_at, timezone)}
                                    </td>
                                    <td className={`px-3 py-1.5 ${statusClass(run.status)}`}>
                                        {statusIcon(run.status)} {run.status}
                                    </td>
                                    <td className="px-3 py-1.5 text-fg-muted tabular-nums">
                                        {formatDuration(run.duration_ms)}
                                    </td>
                                    <td className="px-3 py-1.5 text-fg-muted text-xs break-words max-w-[400px]">
                                        {run.error || (run.dry_run ? '🧪 dry run' : '—')}
                                    </td>
                                </tr>
                                {expandedRunId === run.run_id && (
                                    <RunDetailExpanded key={`detail-${run.run_id}`} runId={run.run_id} />
                                )}
                            </Fragment>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination footer */}
            {filteredRuns.length > PAGE_SIZE && (
                <div className="flex items-center justify-between px-3 py-1.5 border-t border-bg-subtle/20 text-xs text-fg-muted">
                    <span>
                        Page {currentPage + 1} of {totalPages} ({filteredRuns.length} runs)
                    </span>
                    <div className="flex items-center gap-1">
                        <button
                            type="button"
                            disabled={currentPage === 0}
                            onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                            className="px-2 py-0.5 rounded border border-bg-subtle text-fg-muted hover:bg-bg-elevated/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        >
                            ← Prev
                        </button>
                        <button
                            type="button"
                            disabled={currentPage >= totalPages - 1}
                            onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                            className="px-2 py-0.5 rounded border border-bg-subtle text-fg-muted hover:bg-bg-elevated/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        >
                            Next →
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
