/**
 * Scheduling API types and client functions.
 *
 * Types mirror Python Pydantic response models in scheduling.py.
 * API functions use the canonical apiFetch wrapper from @/lib/api.
 *
 * Source: 09-scheduling.md §9.10, scheduling.py response models
 * MEU: MEU-72 (gui-scheduling)
 */

import { apiFetch } from '@/lib/api'

// ── Response Types (match Python models exactly) ───────────────────────

/** Matches scheduling.py PolicyResponse */
export interface Policy {
    id: string
    name: string
    schema_version: number
    enabled: boolean
    approved: boolean
    approved_at: string | null
    content_hash: string
    policy_json: Record<string, unknown>
    created_at: string
    updated_at: string | null
    next_run: string | null
}

/** Matches scheduling.py PolicyListResponse */
export interface PolicyListResponse {
    policies: Policy[]
    total: number
}

/** Matches scheduling.py RunResponse */
export interface PipelineRun {
    run_id: string
    policy_id: string
    status: string
    trigger_type: string
    started_at: string | null
    completed_at: string | null
    duration_ms: number | null
    error: string | null
    dry_run: boolean
}

/** Matches scheduling.py StepResponse */
export interface PipelineStep {
    step_id: string
    step_type: string
    status: string
    started_at: string | null
    completed_at: string | null
    duration_ms: number | null
    error: string | null
    attempt: number
}

/** Matches scheduling.py RunDetailResponse */
export interface RunDetail extends PipelineRun {
    steps: PipelineStep[]
}

/** Matches scheduling.py SchedulerStatusResponse */
export interface SchedulerStatus {
    running: boolean
    job_count: number
    jobs: Record<string, unknown>[]
}

// ── Request Types ──────────────────────────────────────────────────────

export interface PolicyCreatePayload {
    policy_json: Record<string, unknown>
}

export interface RunTriggerPayload {
    dry_run: boolean
}

export interface PatchScheduleParams {
    cron_expression?: string
    enabled?: boolean
    timezone?: string
}

// ── API Client Functions ───────────────────────────────────────────────

const BASE = '/api/v1/scheduling'

export function fetchPolicies(enabledOnly = false): Promise<PolicyListResponse> {
    const qs = enabledOnly ? '?enabled_only=true' : ''
    return apiFetch<PolicyListResponse>(`${BASE}/policies${qs}`)
}

export function fetchPolicy(policyId: string): Promise<Policy> {
    return apiFetch<Policy>(`${BASE}/policies/${policyId}`)
}

export function createPolicy(payload: PolicyCreatePayload): Promise<Policy> {
    return apiFetch<Policy>(`${BASE}/policies`, {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function updatePolicy(policyId: string, payload: PolicyCreatePayload): Promise<Policy> {
    return apiFetch<Policy>(`${BASE}/policies/${policyId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
    })
}

export function deletePolicy(policyId: string): Promise<void> {
    return apiFetch<void>(`${BASE}/policies/${policyId}`, {
        method: 'DELETE',
    })
}

export async function approvePolicy(policyId: string): Promise<Policy> {
    // PH11: Get CSRF approval token from Electron main process via IPC
    const tokenResult = await (window as any).electronAPI?.generateApprovalToken(policyId)
    if (!tokenResult?.token) {
        throw new Error('Failed to obtain approval token from Electron main process')
    }

    return apiFetch<Policy>(`${BASE}/policies/${policyId}/approve`, {
        method: 'POST',
        headers: {
            'X-Approval-Token': tokenResult.token,
        },
    })
}

export function triggerRun(policyId: string, payload: RunTriggerPayload): Promise<PipelineRun> {
    return apiFetch<PipelineRun>(`${BASE}/policies/${policyId}/run`, {
        method: 'POST',
        body: JSON.stringify(payload),
    })
}

export function fetchPolicyRuns(policyId: string, limit = 20): Promise<PipelineRun[]> {
    return apiFetch<PipelineRun[]>(`${BASE}/policies/${policyId}/runs?limit=${limit}`)
}

export function fetchRunDetail(runId: string): Promise<RunDetail> {
    return apiFetch<RunDetail>(`${BASE}/runs/${runId}`)
}

export function fetchSchedulerStatus(): Promise<SchedulerStatus> {
    return apiFetch<SchedulerStatus>(`${BASE}/scheduler/status`)
}

export function patchSchedule(policyId: string, params: PatchScheduleParams): Promise<Policy> {
    const qs = new URLSearchParams()
    if (params.cron_expression !== undefined) qs.set('cron_expression', params.cron_expression)
    if (params.enabled !== undefined) qs.set('enabled', String(params.enabled))
    if (params.timezone !== undefined) qs.set('timezone', params.timezone)
    return apiFetch<Policy>(`${BASE}/policies/${policyId}/schedule?${qs.toString()}`, {
        method: 'PATCH',
    })
}
