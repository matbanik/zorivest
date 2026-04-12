/**
 * React Query hooks for the Scheduling & Pipeline feature.
 *
 * Follows the canonical hook pattern from useAccounts.ts:
 * - Query key factory for structured invalidation
 * - Mutations invalidate parent queries on success
 * - Typed return values matching api.ts types
 *
 * Source: 06e-gui-scheduling.md, useAccounts.ts pattern
 * MEU: MEU-72 (gui-scheduling)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Policy, PolicyCreatePayload, PipelineRun, RunDetail, SchedulerStatus, PatchScheduleParams, RunTriggerPayload } from './api'
import {
    fetchPolicies,
    fetchPolicy,
    createPolicy,
    updatePolicy,
    deletePolicy,
    approvePolicy,
    triggerRun,
    fetchPolicyRuns,
    fetchRunDetail,
    fetchSchedulerStatus,
    patchSchedule,
} from './api'

// ── Query Keys ─────────────────────────────────────────────────────────

export const schedulingKeys = {
    all: ['scheduling-policies'] as const,
    detail: (id: string) => ['scheduling-policies', id] as const,
    runs: (policyId: string) => ['scheduling-runs', policyId] as const,
    runDetail: (runId: string) => ['scheduling-run-detail', runId] as const,
    schedulerStatus: ['scheduler-status'] as const,
}

// ── Query Hooks ────────────────────────────────────────────────────────

/** Fetch all scheduling policies. Auto-refreshes every 10s. */
export function useSchedulingPolicies() {
    const { data, isLoading, isFetching, error, refetch } = useQuery({
        queryKey: schedulingKeys.all,
        queryFn: () => fetchPolicies(),
        staleTime: 0,
        refetchInterval: 10_000,
        refetchOnWindowFocus: true,
    })

    return {
        policies: data?.policies ?? [],
        total: data?.total ?? 0,
        isLoading,
        isFetching,
        error: error ? (error instanceof Error ? error.message : 'Failed to fetch policies') : null,
        refetch,
    }
}

/** Fetch a single policy by ID. */
export function useSchedulingPolicy(policyId: string | null) {
    return useQuery<Policy | null>({
        queryKey: policyId ? schedulingKeys.detail(policyId) : ['scheduling-policies', 'no-id'],
        queryFn: async () => {
            if (!policyId) return null
            return fetchPolicy(policyId)
        },
        enabled: !!policyId,
    })
}

/** Fetch run history for a specific policy. Auto-refreshes every 10s. */
export function usePolicyRuns(policyId: string | null) {
    return useQuery<PipelineRun[]>({
        queryKey: policyId ? schedulingKeys.runs(policyId) : ['scheduling-runs', 'no-id'],
        queryFn: async () => {
            if (!policyId) return []
            return fetchPolicyRuns(policyId)
        },
        enabled: !!policyId,
        refetchInterval: 10_000,
    })
}

/** Fetch detailed run info with step statuses. */
export function useRunDetail(runId: string | null) {
    return useQuery<RunDetail | null>({
        queryKey: runId ? schedulingKeys.runDetail(runId) : ['scheduling-run-detail', 'no-id'],
        queryFn: async () => {
            if (!runId) return null
            return fetchRunDetail(runId)
        },
        enabled: !!runId,
    })
}

/** Fetch scheduler health status. Auto-refreshes every 30s. */
export function useSchedulerStatus() {
    return useQuery<SchedulerStatus>({
        queryKey: schedulingKeys.schedulerStatus,
        queryFn: fetchSchedulerStatus,
        refetchInterval: 30_000,
    })
}

// ── Mutation Hooks ─────────────────────────────────────────────────────

/** Create a new policy. Invalidates policy list on success. */
export function useCreatePolicy() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (payload: PolicyCreatePayload) => createPolicy(payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: schedulingKeys.all })
        },
    })
}

/** Update an existing policy. Invalidates list + detail on success. */
export function useUpdatePolicy() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ policyId, payload }: { policyId: string; payload: PolicyCreatePayload }) =>
            updatePolicy(policyId, payload),
        onSuccess: (_data, variables) => {
            queryClient.invalidateQueries({ queryKey: schedulingKeys.all })
            queryClient.invalidateQueries({ queryKey: schedulingKeys.detail(variables.policyId) })
        },
    })
}

/** Delete a policy. Invalidates policy list on success. */
export function useDeletePolicy() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (policyId: string) => deletePolicy(policyId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: schedulingKeys.all })
        },
    })
}

/** Approve a policy (GUI-only gate). Invalidates list + detail. */
export function useApprovePolicy() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (policyId: string) => approvePolicy(policyId),
        onSuccess: (_data, policyId) => {
            queryClient.invalidateQueries({ queryKey: schedulingKeys.all })
            queryClient.invalidateQueries({ queryKey: schedulingKeys.detail(policyId) })
        },
    })
}

/** Trigger a pipeline run. Invalidates run list on success. */
export function useTriggerRun() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ policyId, payload }: { policyId: string; payload: RunTriggerPayload }) =>
            triggerRun(policyId, payload),
        onSuccess: (_data, variables) => {
            queryClient.invalidateQueries({ queryKey: schedulingKeys.runs(variables.policyId) })
        },
    })
}

/** Patch schedule fields (cron, timezone, enabled). */
export function usePatchSchedule() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ policyId, params }: { policyId: string; params: PatchScheduleParams }) =>
            patchSchedule(policyId, params),
        onSuccess: (_data, variables) => {
            queryClient.invalidateQueries({ queryKey: schedulingKeys.all })
            queryClient.invalidateQueries({ queryKey: schedulingKeys.detail(variables.policyId) })
        },
    })
}
