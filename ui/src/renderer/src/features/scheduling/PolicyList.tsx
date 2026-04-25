/**
 * PolicyList — left pane showing scheduling policies.
 *
 * Displays a scrollable list of policies with:
 * - Enabled/paused icon (✅ or ⏸️)
 * - Policy name
 * - Cron expression (human-readable)
 * - Next run time (or "paused")
 *
 * Source: 06e-gui-scheduling.md §Schedule List Card Fields
 * MEU: MEU-72 (gui-scheduling)
 */

import { useMemo } from 'react'
import cronstrue from 'cronstrue'
import { formatTimestamp } from '@/lib/formatDate'
import { SCHEDULING_TEST_IDS } from './test-ids'
import type { Policy } from './api'

interface PolicyListProps {
    policies: Policy[]
    selectedPolicyId: string | null
    onSelect: (policy: Policy) => void
    onCreate: () => void
    isLoading: boolean
    error: string | null
}

function formatCronShort(cron: string): string {
    try {
        return cronstrue.toString(cron, { use24HourTimeFormat: false })
    } catch {
        return cron
    }
}

function formatNextRun(nextRun: string | null, enabled: boolean, timezone?: string): string {
    if (!enabled) return '(paused)'
    if (!nextRun) return 'Not scheduled'
    return formatTimestamp(nextRun, timezone) || nextRun
}

export default function PolicyList({
    policies,
    selectedPolicyId,
    onSelect,
    onCreate,
    isLoading,
    error,
}: PolicyListProps) {
    const sortedPolicies = useMemo(
        () => [...policies].sort((a, b) => a.name.localeCompare(b.name)),
        [policies],
    )

    return (
        <div data-testid={SCHEDULING_TEST_IDS.POLICY_LIST} className="flex flex-col h-full">
            {/* Header */}
            <div className="px-3 py-2 border-b border-bg-subtle/30 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-fg">Policies</h3>
                <button
                    data-testid={SCHEDULING_TEST_IDS.POLICY_CREATE_BTN}
                    onClick={onCreate}
                    className="px-2 py-1 text-xs font-medium rounded-md bg-accent-purple/20 text-accent-purple hover:bg-accent-purple/30 transition-colors"
                    title="Create new policy"
                >
                    + New Policy
                </button>
            </div>

            {/* Loading */}
            {isLoading && (
                <div data-testid={SCHEDULING_TEST_IDS.LOADING_STATE} className="p-4 text-sm text-fg-muted text-center">
                    Loading policies…
                </div>
            )}

            {/* Error */}
            {error && !isLoading && (
                <div data-testid={SCHEDULING_TEST_IDS.ERROR_STATE} className="p-4 text-sm text-accent-red text-center">
                    {error}
                </div>
            )}

            {/* Empty state */}
            {!isLoading && !error && policies.length === 0 && (
                <div data-testid={SCHEDULING_TEST_IDS.EMPTY_STATE} className="p-4 text-sm text-fg-muted text-center">
                    No policies yet. Click "+ New Policy" to create one.
                </div>
            )}

            {/* Policy items */}
            <div className="flex-1 overflow-y-auto">
                {sortedPolicies.map((policy) => {
                    const isSelected = policy.id === selectedPolicyId
                    const trigger = (policy.policy_json as Record<string, Record<string, string>>)?.trigger
                    const cron = trigger?.cron_expression || ''
                    const timezone = trigger?.timezone || 'UTC'
                    // 3-state: draft (not approved), ready (approved, paused), scheduled (approved + enabled)
                    const policyState = !policy.approved ? 'draft' : !policy.enabled ? 'ready' : 'scheduled'
                    const stateIcon = policyState === 'draft' ? '📝' : policyState === 'ready' ? '⏸️' : '✅'
                    const stateLabel = policyState === 'draft' ? 'Draft' : policyState === 'ready' ? 'Ready (paused)' : 'Scheduled'

                    return (
                        <button
                            key={policy.id}
                            data-testid={SCHEDULING_TEST_IDS.POLICY_ITEM}
                            onClick={() => onSelect(policy)}
                            className={`w-full text-left px-3 py-2.5 border-b border-bg-subtle/20 transition-colors cursor-pointer ${
                                isSelected
                                    ? 'bg-accent-purple/15 border-l-2 border-l-accent-purple'
                                    : 'hover:bg-bg-elevated/50'
                            }`}
                        >
                            <div className="flex items-center gap-2">
                                <span
                                    data-testid={SCHEDULING_TEST_IDS.POLICY_STATUS}
                                    className="text-sm"
                                    title={stateLabel}
                                >
                                    {stateIcon}
                                </span>
                                <span
                                    data-testid={SCHEDULING_TEST_IDS.POLICY_NAME}
                                    className="text-sm font-medium text-fg truncate"
                                >
                                    {policy.name}
                                </span>
                            </div>
                            {cron && (
                                <div className="text-xs text-fg-muted mt-0.5 ml-6 truncate">
                                    {formatCronShort(cron)}
                                </div>
                            )}
                            <div
                                data-testid={SCHEDULING_TEST_IDS.POLICY_NEXT_RUN_TIME}
                                className="text-xs text-fg-muted/70 mt-0.5 ml-6"
                            >
                                Next: {formatNextRun(policy.next_run, policy.enabled, timezone)}
                            </div>
                        </button>
                    )
                })}
            </div>
        </div>
    )
}
