/**
 * SchedulingLayout — main list+detail split layout for scheduling.
 *
 * Left pane (~30%): PolicyList sidebar
 * Right pane (~70%): PolicyDetail + RunHistory
 *
 * Source: 06e-gui-scheduling.md §GUI Layout
 * MEU: MEU-72 (gui-scheduling)
 */

import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { SCHEDULING_TEST_IDS } from './test-ids'
import PolicyList from './PolicyList'
import PolicyDetail from './PolicyDetail'
import RunHistory from './RunHistory'
import {
    useSchedulingPolicies,
    useCreatePolicy,
    useUpdatePolicy,
    useDeletePolicy,
    useApprovePolicy,
    useTriggerRun,
    usePatchSchedule,
    usePolicyRuns,
    useSchedulerStatus,
} from './hooks'
import type { Policy } from './api'

export default function SchedulingLayout() {
    const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
    const { policies, isLoading, error } = useSchedulingPolicies()

    // Fetch default timezone from settings for new policies
    const { data: tzSetting } = useQuery<{ value: string | null }>({
        queryKey: ['settings', 'scheduling.default_timezone'],
        queryFn: async () => {
            try {
                return await apiFetch('/api/v1/settings/scheduling.default_timezone')
            } catch {
                return { value: null }
            }
        },
        staleTime: 5 * 60 * 1000,
    })

    // Mutations
    const createMutation = useCreatePolicy()
    const updateMutation = useUpdatePolicy()
    const deleteMutation = useDeletePolicy()
    const approveMutation = useApprovePolicy()
    const triggerMutation = useTriggerRun()
    const patchMutation = usePatchSchedule()

    // Run history for selected policy
    const { data: runs = [], isLoading: runsLoading } = usePolicyRuns(
        selectedPolicy?.id ?? null,
    )

    // Scheduler status
    const { data: schedulerStatus } = useSchedulerStatus()

    // Keep selected policy in sync when policies refresh
    const currentPolicy = selectedPolicy
        ? policies.find((p) => p.id === selectedPolicy.id) ?? selectedPolicy
        : null

    const handleSelect = useCallback((policy: Policy) => {
        setSelectedPolicy(policy)
    }, [])

    const handleCreate = useCallback(() => {
        const defaultPolicy = {
            schema_version: 1,
            name: `new-policy-${Date.now()}`,
            trigger: {
                cron_expression: '0 8 * * 1-5',
                timezone: tzSetting?.value || 'UTC',
                enabled: false,
            },
            steps: [
                {
                    id: 'fetch_data',
                    type: 'fetch',
                    params: {
                        provider: 'yahoo',
                        data_type: 'ohlcv',
                    },
                },
            ],
        }
        createMutation.mutate(
            { policy_json: defaultPolicy },
            {
                onSuccess: (created) => {
                    setSelectedPolicy(created)
                },
            },
        )
    }, [createMutation, tzSetting])

    const handleSave = useCallback(
        (policyJson: Record<string, unknown>) => {
            if (!currentPolicy) return
            updateMutation.mutate({
                policyId: currentPolicy.id,
                payload: { policy_json: policyJson },
            })
        },
        [currentPolicy, updateMutation],
    )

    const handleApprove = useCallback((opts?: { enableAfter?: boolean }) => {
        if (!currentPolicy) return
        const enableAfter = opts?.enableAfter ?? false
        approveMutation.mutate(currentPolicy.id, {
            onSuccess: () => {
                if (enableAfter) {
                    // Draft → Scheduled: also enable the schedule
                    patchMutation.mutate({
                        policyId: currentPolicy.id,
                        params: { enabled: true },
                    })
                }
            },
        })
    }, [currentPolicy, approveMutation, patchMutation])

    const handleDelete = useCallback(() => {
        if (!currentPolicy) return
        deleteMutation.mutate(currentPolicy.id, {
            onSuccess: () => {
                setSelectedPolicy(null)
            },
        })
    }, [currentPolicy, deleteMutation])

    const handleTriggerRun = useCallback(
        (dryRun: boolean) => {
            if (!currentPolicy) return
            triggerMutation.mutate({
                policyId: currentPolicy.id,
                payload: { dry_run: dryRun },
            })
        },
        [currentPolicy, triggerMutation],
    )

    const handlePatchSchedule = useCallback(
        (params: { cron_expression?: string; enabled?: boolean; timezone?: string }) => {
            if (!currentPolicy) return
            patchMutation.mutate({
                policyId: currentPolicy.id,
                params,
            })
        },
        [currentPolicy, patchMutation],
    )

    const handleRename = useCallback(
        (newName: string) => {
            if (!currentPolicy) return
            // Update the name inside policy_json and save via PUT
            const updatedJson = {
                ...(currentPolicy.policy_json as Record<string, unknown>),
                name: newName,
            }
            updateMutation.mutate({
                policyId: currentPolicy.id,
                payload: { policy_json: updatedJson },
            })
        },
        [currentPolicy, updateMutation],
    )

    return (
        <div data-testid={SCHEDULING_TEST_IDS.ROOT} className="flex h-full">
            {/* Left pane — Policy list */}
            <div className="w-[280px] min-w-[240px] border-r border-bg-subtle/30 flex-shrink-0">
                <PolicyList
                    policies={policies}
                    selectedPolicyId={currentPolicy?.id ?? null}
                    onSelect={handleSelect}
                    onCreate={handleCreate}
                    isLoading={isLoading}
                    error={error}
                />
            </div>

            {/* Right pane — Detail + Run History */}
            <div className="flex-1 min-w-0 flex flex-col">
                {currentPolicy ? (
                    <>
                        {/* Policy detail (scrollable) */}
                        <div className="flex-1 min-h-0 overflow-y-auto">
                            <PolicyDetail
                                policy={currentPolicy}
                                onSave={handleSave}
                                onApprove={handleApprove}
                                onDelete={handleDelete}
                                onTriggerRun={handleTriggerRun}
                                onPatchSchedule={handlePatchSchedule}
                                onRename={handleRename}
                                isSaving={updateMutation.isPending}
                            />
                        </div>

                        {/* Run History (bottom panel) */}
                        <div className="border-t border-bg-subtle/30 max-h-[35%] overflow-y-auto">
                            <div className="px-4 py-2 flex items-center justify-between border-b border-bg-subtle/20">
                                <h4 className="text-xs font-semibold text-fg-muted uppercase tracking-wider">
                                    Run history
                                </h4>
                                {schedulerStatus && (
                                    <div
                                        data-testid={SCHEDULING_TEST_IDS.SCHEDULER_STATUS}
                                        className="flex items-center gap-1.5 text-xs"
                                    >
                                        <span
                                            className={`w-2 h-2 rounded-full ${
                                                schedulerStatus.running
                                                    ? 'bg-accent-green'
                                                    : 'bg-accent-red'
                                            }`}
                                        />
                                        <span className="text-fg-muted">
                                            {schedulerStatus.running ? 'Scheduler running' : 'Scheduler stopped'}
                                            {' · '}
                                            {schedulerStatus.job_count} jobs
                                        </span>
                                    </div>
                                )}
                            </div>
                            <RunHistory
                                runs={runs}
                                isLoading={runsLoading}
                                timezone={
                                    ((currentPolicy?.policy_json as Record<string, unknown>)?.trigger as Record<string, unknown>)?.timezone as string | undefined
                                }
                            />
                        </div>
                    </>
                ) : (
                    /* Empty state when no policy selected */
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center text-fg-muted">
                            <div className="text-4xl mb-3">📋</div>
                            <h3 className="text-lg font-medium text-fg mb-1">
                                Scheduling & Pipelines
                            </h3>
                            <p className="text-sm max-w-[300px]">
                                Select a policy from the list or create a new one to configure
                                automated pipeline schedules.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
