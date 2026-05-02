/**
 * Tests for Scheduling & Pipeline feature.
 *
 * Sub-MEU A: Hook tests (useSchedulingPolicies, mutations, cache invalidation)
 * Sub-MEU B: Component tests (SchedulingLayout, PolicyList, PolicyDetail, CronPreview)
 * Sub-MEU C: RunHistory tests
 *
 * Test pattern follows trades.test.tsx (vi.hoisted mock, QueryClient wrapper).
 * MEU: MEU-72 (gui-scheduling)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, act } from '@testing-library/react'

// ─── Mocks ────────────────────────────────────────────────────────────────────

const { mockApiFetch } = vi.hoisted(() => ({
    mockApiFetch: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => mockApiFetch(...args),
}))

vi.mock('@/hooks/useStatusBar', () => ({
    useStatusBar: () => ({ message: 'Ready', setStatus: vi.fn() }),
    StatusBarProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Import after mocks
import {
    useSchedulingPolicies,
    useCreatePolicy,
    useDeletePolicy,
    useApprovePolicy,
    useTriggerRun,
    usePatchSchedule,
    schedulingKeys,
} from '../hooks'
import type { Policy, PolicyListResponse } from '../api'

// ─── Test Data ────────────────────────────────────────────────────────────────

const MOCK_POLICY: Policy = {
    id: 'pol-001',
    name: 'daily-import',
    schema_version: 1,
    enabled: true,
    approved: true,
    approved_at: '2026-03-18T12:00:00Z',
    content_hash: 'abc123',
    policy_json: {
        name: 'daily-import',
        trigger: { cron_expression: '0 6 * * 1-5', timezone: 'America/New_York' },
        steps: [{ id: 'step_1', type: 'fetch', params: {} }],
    },
    created_at: '2026-03-17T12:00:00Z',
    updated_at: '2026-03-18T12:00:00Z',
    next_run: '2026-03-19T06:00:00Z',
}

const MOCK_POLICY_2: Policy = {
    id: 'pol-002',
    name: 'weekly-report',
    schema_version: 1,
    enabled: false,
    approved: false,
    approved_at: null,
    content_hash: 'def456',
    policy_json: {
        name: 'weekly-report',
        trigger: { cron_expression: '0 8 * * 1', timezone: 'UTC' },
        steps: [{ id: 'step_1', type: 'fetch', params: {} }],
    },
    created_at: '2026-03-17T12:00:00Z',
    updated_at: null,
    next_run: null,
}

const MOCK_POLICIES_RESPONSE: PolicyListResponse = {
    policies: [MOCK_POLICY, MOCK_POLICY_2],
    total: 2,
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    })
    return function Wrapper({ children }: { children: React.ReactNode }) {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-MEU A: Hook Tests
// ═══════════════════════════════════════════════════════════════════════════════

describe('useSchedulingPolicies', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-A4: fetches typed policy list', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_POLICIES_RESPONSE)

        const { result } = renderHook(() => useSchedulingPolicies(), {
            wrapper: createWrapper(),
        })

        expect(result.current.isLoading).toBe(true)

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(result.current.policies).toHaveLength(2)
        expect(result.current.total).toBe(2)
        expect(result.current.policies[0].name).toBe('daily-import')
        expect(result.current.policies[1].name).toBe('weekly-report')
        expect(result.current.error).toBeNull()
    })

    it('returns empty array on error', async () => {
        mockApiFetch.mockRejectedValueOnce(new Error('Network error'))

        const { result } = renderHook(() => useSchedulingPolicies(), {
            wrapper: createWrapper(),
        })

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false)
        })

        expect(result.current.policies).toEqual([])
        expect(result.current.error).toBe('Network error')
    })
})

describe('useCreatePolicy', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-A5: invalidates cache on success', async () => {
        mockApiFetch.mockResolvedValueOnce(MOCK_POLICY)

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => useCreatePolicy(), { wrapper })

        await act(async () => {
            result.current.mutate({ policy_json: { name: 'new-policy' } })
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: schedulingKeys.all }),
        )
    })
})

describe('useDeletePolicy', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-A5: invalidates cache on delete', async () => {
        mockApiFetch.mockResolvedValueOnce(undefined)

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => useDeletePolicy(), { wrapper })

        await act(async () => {
            result.current.mutate('pol-001')
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: schedulingKeys.all }),
        )
    })
})

describe('useApprovePolicy', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
        // PH11: approvePolicy() now calls window.electronAPI.generateApprovalToken()
        // via IPC before making the API call. Must mock this in jsdom.
        ;(window as any).electronAPI = {
            generateApprovalToken: vi.fn().mockResolvedValue({
                token: 'a'.repeat(64),
                expiresAt: Date.now() + 300_000,
            }),
        }
    })

    afterEach(() => {
        delete (window as any).electronAPI
    })

    it('AC-A5: invalidates list + detail on approve', async () => {
        mockApiFetch.mockResolvedValueOnce({ ...MOCK_POLICY, approved: true })

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => useApprovePolicy(), { wrapper })

        await act(async () => {
            result.current.mutate('pol-001')
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: schedulingKeys.all }),
        )
        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: schedulingKeys.detail('pol-001') }),
        )
    })
})

describe('useTriggerRun', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
        // triggerRun() now calls window.electronAPI.generateApprovalToken()
        // via IPC before making the API call (same as approvePolicy).
        ;(window as any).electronAPI = {
            generateApprovalToken: vi.fn().mockResolvedValue({
                token: 'b'.repeat(64),
                expiresAt: Date.now() + 300_000,
            }),
        }
    })

    afterEach(() => {
        delete (window as any).electronAPI
    })

    it('AC-A5: invalidates run list on trigger', async () => {
        mockApiFetch.mockResolvedValueOnce({
            run_id: 'run-001',
            policy_id: 'pol-001',
            status: 'pending',
            trigger_type: 'manual',
            started_at: null,
            completed_at: null,
            duration_ms: null,
            error: null,
            dry_run: false,
        })

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => useTriggerRun(), { wrapper })

        await act(async () => {
            result.current.mutate({ policyId: 'pol-001', payload: { dry_run: false } })
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: schedulingKeys.runs('pol-001') }),
        )
    })
})

describe('usePatchSchedule', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-A5: invalidates list + detail on patch', async () => {
        mockApiFetch.mockResolvedValueOnce({ ...MOCK_POLICY, enabled: false })

        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        })
        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        )

        const { result } = renderHook(() => usePatchSchedule(), { wrapper })

        await act(async () => {
            result.current.mutate({
                policyId: 'pol-001',
                params: { enabled: false },
            })
        })

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true)
        })

        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: schedulingKeys.all }),
        )
        expect(invalidateSpy).toHaveBeenCalledWith(
            expect.objectContaining({ queryKey: schedulingKeys.detail('pol-001') }),
        )
    })
})

describe('schedulingKeys', () => {
    it('AC-A3: key factory produces consistent keys', () => {
        expect(schedulingKeys.all).toEqual(['scheduling-policies'])
        expect(schedulingKeys.detail('pol-001')).toEqual(['scheduling-policies', 'pol-001'])
        expect(schedulingKeys.runs('pol-001')).toEqual(['scheduling-runs', 'pol-001'])
        expect(schedulingKeys.runDetail('run-001')).toEqual(['scheduling-run-detail', 'run-001'])
        expect(schedulingKeys.schedulerStatus).toEqual(['scheduler-status'])
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-MEU B: Component Tests
// ═══════════════════════════════════════════════════════════════════════════════

import PolicyList from '../PolicyList'
import PolicyDetail from '../PolicyDetail'
import CronPreview from '../CronPreview'
import RunHistory from '../RunHistory'
import type { PipelineRun } from '../api'
import { SCHEDULING_TEST_IDS } from '../test-ids'

describe('PolicyList', () => {
    const defaultProps = {
        policies: [MOCK_POLICY, MOCK_POLICY_2],
        selectedPolicyId: null,
        onSelect: vi.fn(),
        onCreate: vi.fn(),
        isLoading: false,
        error: null,
    }

    it('AC-B1: renders policy list with data-testid', () => {
        render(<PolicyList {...defaultProps} />, { wrapper: createWrapper() })

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_LIST)).toBeInTheDocument()
        expect(screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_ITEM)).toHaveLength(2)
    })

    it('AC-B1: renders policy names', () => {
        render(<PolicyList {...defaultProps} />, { wrapper: createWrapper() })

        const names = screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_NAME)
        expect(names[0]).toHaveTextContent('daily-import')
        expect(names[1]).toHaveTextContent('weekly-report')
    })

    it('AC-B1: renders 3-state status icons (Scheduled / Draft)', () => {
        render(<PolicyList {...defaultProps} />, { wrapper: createWrapper() })

        const statuses = screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_STATUS)
        // MOCK_POLICY: approved=true, enabled=true → Scheduled (✅)
        expect(statuses[0]).toHaveTextContent('✅')
        // MOCK_POLICY_2: approved=false, enabled=false → Draft (📝)
        expect(statuses[1]).toHaveTextContent('📝')
    })

    it('shows empty state when no policies', () => {
        render(
            <PolicyList {...defaultProps} policies={[]} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.EMPTY_STATE)).toBeInTheDocument()
    })

    it('shows loading state', () => {
        render(
            <PolicyList {...defaultProps} isLoading={true} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.LOADING_STATE)).toBeInTheDocument()
    })

    it('shows error state', () => {
        render(
            <PolicyList {...defaultProps} error="Failed to fetch" />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.ERROR_STATE)).toHaveTextContent('Failed to fetch')
    })

    it('calls onSelect when policy clicked', () => {
        const onSelect = vi.fn()
        render(
            <PolicyList {...defaultProps} onSelect={onSelect} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_ITEM)[0])
        expect(onSelect).toHaveBeenCalledWith(MOCK_POLICY)
    })

    it('calls onCreate when + New clicked', () => {
        const onCreate = vi.fn()
        render(
            <PolicyList {...defaultProps} onCreate={onCreate} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_CREATE_BTN))
        expect(onCreate).toHaveBeenCalled()
    })

    it('highlights selected policy', () => {
        render(
            <PolicyList {...defaultProps} selectedPolicyId="pol-001" />,
            { wrapper: createWrapper() },
        )

        const items = screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_ITEM)
        expect(items[0].className).toContain('bg-accent-purple')
    })

    it('AC-72a: next-run uses formatTimestamp with policy timezone', () => {
        render(<PolicyList {...defaultProps} />, { wrapper: createWrapper() })

        const nextRunEls = screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_NEXT_RUN_TIME)
        // MOCK_POLICY: next_run = '2026-03-19T06:00:00Z', timezone = 'America/New_York'
        // 06:00 UTC → 02:00 AM ET (during EDT)
        // DT1 format: MM-DD-YYYY h:mmAM/PM
        expect(nextRunEls[0].textContent).toContain('03-19-2026')
        expect(nextRunEls[0].textContent).toContain('AM')
        // Ensure it does NOT use old locale format (e.g. "Mar 19" short-month)
        expect(nextRunEls[0].textContent).not.toMatch(/Mar\s+19/)
    })

    it('AC-72a: paused policy shows "(paused)" instead of timestamp', () => {
        render(<PolicyList {...defaultProps} />, { wrapper: createWrapper() })

        const nextRunEls = screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_NEXT_RUN_TIME)
        // MOCK_POLICY_2: enabled=false → should show '(paused)'
        expect(nextRunEls[1]).toHaveTextContent('(paused)')
    })

    it('AC-72a: renders POLICY_NEXT_RUN_TIME test ID', () => {
        render(<PolicyList {...defaultProps} />, { wrapper: createWrapper() })

        const nextRunEls = screen.getAllByTestId(SCHEDULING_TEST_IDS.POLICY_NEXT_RUN_TIME)
        expect(nextRunEls).toHaveLength(2)
    })
})

describe('CronPreview', () => {
    it('AC-B2: shows human-readable cron', () => {
        render(<CronPreview expression="0 8 * * 1-5" />)

        const preview = screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_CRON_PREVIEW)
        expect(preview).toBeInTheDocument()
        // cronstrue converts to something like "At 08:00 AM, Monday through Friday"
        expect(preview.textContent).toContain('8')
    })

    it('AC-B2: shows error for invalid cron', () => {
        render(<CronPreview expression="invalid-cron" />)

        const preview = screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_CRON_PREVIEW)
        expect(preview).toHaveTextContent('Invalid cron expression')
    })

    it('does not render for empty expression', () => {
        const { container } = render(<CronPreview expression="" />)
        expect(container.firstChild).toBeNull()
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-MEU B.2: PolicyDetail Action Tests
// ═══════════════════════════════════════════════════════════════════════════════

// Mock CodeMirror — PolicyDetail uses @codemirror/* which doesn't work in jsdom
// Must use vi.hoisted since vi.mock factories are hoisted above variable declarations
const { MockEditorView } = vi.hoisted(() => {
    const ctor = vi.fn().mockImplementation(() => ({
        state: { doc: { toString: () => '{"name":"test","trigger":{"cron_expression":"0 8 * * *","timezone":"UTC"},"steps":[{"id":"s1","type":"fetch","params":{}}]}' } },
        destroy: vi.fn(),
    }))
    // Static method used in EditorView.theme(...)
    ;(ctor as any).theme = vi.fn().mockReturnValue([])
    // Static field used in EditorView.updateListener.of(...)
    ;(ctor as any).updateListener = { of: vi.fn().mockReturnValue([]) }
    return { MockEditorView: ctor }
})

vi.mock('@codemirror/view', () => ({
    EditorView: MockEditorView,
    keymap: { of: vi.fn().mockReturnValue([]) },
}))
vi.mock('@codemirror/state', () => ({
    EditorState: { create: vi.fn().mockReturnValue({}) },
}))
vi.mock('@codemirror/lang-json', () => ({ json: vi.fn().mockReturnValue([]) }))
vi.mock('@codemirror/theme-one-dark', () => ({ oneDark: [] }))
vi.mock('codemirror', () => ({ basicSetup: [] }))

describe('PolicyDetail', () => {
    const defaultHandlers = {
        onSave: vi.fn(),
        onApprove: vi.fn(),
        onDelete: vi.fn(),
        onTriggerRun: vi.fn(),
        onPatchSchedule: vi.fn(),
        onRename: vi.fn(),
        isSaving: false,
    }

    beforeEach(() => {
        vi.clearAllMocks()
    })

    // Approved + enabled = scheduled state
    const APPROVED_POLICY = { ...MOCK_POLICY, approved: true, enabled: true }
    // Draft = not approved
    const DRAFT_POLICY = { ...MOCK_POLICY_2, approved: false, enabled: false }

    it('AC-C1: Test Run calls onTriggerRun(true) — always dry-run', () => {
        render(
            <PolicyDetail policy={APPROVED_POLICY} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEST_RUN_BTN))
        expect(defaultHandlers.onTriggerRun).toHaveBeenCalledWith(true)
    })

    it('AC-C2: Run Now requires two clicks (confirmation pattern)', () => {
        render(
            <PolicyDetail policy={APPROVED_POLICY} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        const btn = screen.getByTestId(SCHEDULING_TEST_IDS.RUN_NOW_BTN)

        // First click — shows confirmation
        fireEvent.click(btn)
        expect(defaultHandlers.onTriggerRun).not.toHaveBeenCalled()
        expect(btn.textContent).toBe('Confirm Run')

        // Second click — executes
        fireEvent.click(btn)
        expect(defaultHandlers.onTriggerRun).toHaveBeenCalledWith(false)
    })

    it('AC-C2: Test Run and Run Now disabled for draft policies', () => {
        render(
            <PolicyDetail policy={DRAFT_POLICY} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEST_RUN_BTN)).toBeDisabled()
        expect(screen.getByTestId(SCHEDULING_TEST_IDS.RUN_NOW_BTN)).toBeDisabled()
    })

    it('AC-B6: Delete opens themed confirmation modal and confirms', () => {
        render(
            <PolicyDetail policy={APPROVED_POLICY} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        // Click delete — should open themed modal, NOT window.confirm
        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_DELETE_BTN))

        // Modal should be visible in the DOM (portaled to body)
        // 'Delete Policy' appears in heading + confirm button, so use getAllByText
        expect(screen.getAllByText('Delete Policy').length).toBeGreaterThanOrEqual(1)
        expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument()

        // Click the confirm button in the modal
        const confirmBtn = screen.getByRole('button', { name: 'Delete Policy' })
        fireEvent.click(confirmBtn)

        expect(defaultHandlers.onDelete).toHaveBeenCalled()
    })

    it('AC-B6: Delete cancelled when user clicks Cancel in modal', () => {
        render(
            <PolicyDetail policy={APPROVED_POLICY} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        // Open the delete modal
        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_DELETE_BTN))
        expect(screen.getAllByText('Delete Policy').length).toBeGreaterThanOrEqual(1)

        // Click Cancel — modal should close, onDelete NOT called
        const cancelBtn = screen.getByRole('button', { name: 'Cancel' })
        fireEvent.click(cancelBtn)

        expect(defaultHandlers.onDelete).not.toHaveBeenCalled()
    })

    it('AC-B8: Clicking Ready button calls onApprove for draft policies', () => {
        render(
            <PolicyDetail policy={DRAFT_POLICY} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        // Click the "Ready" segment in the segmented selector
        fireEvent.click(screen.getAllByTestId('policy-state-ready')[0])
        expect(defaultHandlers.onApprove).toHaveBeenCalledWith({ enableAfter: false })
    })

    it('AC-B8: Clicking Scheduled button calls onPatchSchedule for ready policies', () => {
        const readyPolicy = { ...MOCK_POLICY, approved: true, enabled: false }

        render(
            <PolicyDetail policy={readyPolicy} {...defaultHandlers} />,
            { wrapper: createWrapper() },
        )

        // Click the "Scheduled" segment in the segmented selector
        fireEvent.click(screen.getAllByTestId('policy-state-scheduled')[0])
        expect(defaultHandlers.onPatchSchedule).toHaveBeenCalledWith({ enabled: true })
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-MEU C: RunHistory Tests
// ═══════════════════════════════════════════════════════════════════════════════

const MOCK_RUNS: PipelineRun[] = [
    {
        run_id: 'run-001',
        policy_id: 'pol-001',
        status: 'completed',
        trigger_type: 'scheduled',
        started_at: '2026-03-18T08:00:00Z',
        completed_at: '2026-03-18T08:00:12Z',
        duration_ms: 12300,
        error: null,
        dry_run: false,
    },
    {
        run_id: 'run-002',
        policy_id: 'pol-001',
        status: 'failed',
        trigger_type: 'manual',
        started_at: '2026-03-17T08:00:00Z',
        completed_at: '2026-03-17T08:00:04Z',
        duration_ms: 4100,
        error: 'API rate limit exceeded',
        dry_run: false,
    },
]

describe('RunHistory', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-C1: renders run history table with data-testid', () => {
        render(
            <RunHistory runs={MOCK_RUNS} isLoading={false} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.RUN_HISTORY_TABLE)).toBeInTheDocument()
        expect(screen.getAllByTestId(SCHEDULING_TEST_IDS.RUN_HISTORY_ROW)).toHaveLength(2)
    })

    it('AC-C1: shows status icons', () => {
        render(
            <RunHistory runs={MOCK_RUNS} isLoading={false} />,
            { wrapper: createWrapper() },
        )

        const rows = screen.getAllByTestId(SCHEDULING_TEST_IDS.RUN_HISTORY_ROW)
        expect(rows[0]).toHaveTextContent('✅')
        expect(rows[1]).toHaveTextContent('❌')
    })

    it('AC-C1: shows duration', () => {
        render(
            <RunHistory runs={MOCK_RUNS} isLoading={false} />,
            { wrapper: createWrapper() },
        )

        const rows = screen.getAllByTestId(SCHEDULING_TEST_IDS.RUN_HISTORY_ROW)
        expect(rows[0]).toHaveTextContent('12.3s')
        expect(rows[1]).toHaveTextContent('4.1s')
    })

    it('AC-C1: shows error details for failed runs', () => {
        render(
            <RunHistory runs={MOCK_RUNS} isLoading={false} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText('API rate limit exceeded')).toBeInTheDocument()
    })

    it('shows empty state when no runs', () => {
        render(
            <RunHistory runs={[]} isLoading={false} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText(/No runs yet/i)).toBeInTheDocument()
    })

    it('shows loading state', () => {
        render(
            <RunHistory runs={[]} isLoading={true} />,
            { wrapper: createWrapper() },
        )

        expect(screen.getByText(/Loading run history/i)).toBeInTheDocument()
    })

    // F1: Defensive array guard — RunHistory handles non-array props gracefully
    it('F1: renders empty state when runs prop is a non-array object', () => {
        // Simulates the case where API returns {} instead of [] and useQuery
        // doesn't apply the default fallback (data is {} not undefined)
        render(
            <RunHistory runs={{} as any} isLoading={false} />,
            { wrapper: createWrapper() },
        )

        // Should gracefully show empty state, not crash with TypeError
        expect(screen.getByText(/No runs yet/i)).toBeInTheDocument()
    })
})

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-MEU B: SchedulingLayout Integration Test
// ═══════════════════════════════════════════════════════════════════════════════

/** Standard mock that returns [] for /runs URLs to prevent unhandled runtime errors */
function layoutMock(url: string, init?: Record<string, unknown>) {
    if (url.includes('/runs')) return Promise.resolve([])
    if (url.includes('/policies')) return Promise.resolve(MOCK_POLICIES_RESPONSE)
    if (url.includes('/scheduler/status')) return Promise.resolve({ running: true, job_count: 2, jobs: [] })
    if (url.includes('/templates')) return Promise.resolve([])
    if (url.includes('/settings')) return Promise.resolve({ value: 'UTC' })
    return Promise.resolve([])
}

describe('SchedulingLayout', () => {
    beforeEach(() => {
        mockApiFetch.mockReset()
    })

    it('AC-B3: renders root container with data-testid', async () => {
        mockApiFetch.mockImplementation(layoutMock)

        const { default: SchedulingLayout } = await import('../SchedulingLayout')

        render(<SchedulingLayout />, { wrapper: createWrapper() })

        expect(screen.getByTestId(SCHEDULING_TEST_IDS.ROOT)).toBeInTheDocument()
    })

    it('AC-B3: shows empty state when no policy selected', async () => {
        mockApiFetch.mockImplementation(layoutMock)

        const { default: SchedulingLayout } = await import('../SchedulingLayout')

        render(<SchedulingLayout />, { wrapper: createWrapper() })

        await waitFor(() => {
            expect(screen.getByText('Scheduling & Pipelines')).toBeInTheDocument()
        })
    })

    it('AC-B3: +New button sends valid PolicyDocument payload to API', async () => {
        // Track all API calls to capture the create POST
        const capturedCalls: Array<[string, Record<string, unknown>]> = []
        mockApiFetch.mockImplementation((url: string, init?: Record<string, unknown>) => {
            capturedCalls.push([url, init ?? {}])
            if (url.includes('/policies') && init?.method === 'POST') {
                // Simulate successful creation
                return Promise.resolve({
                    id: 'new-id',
                    name: 'new-policy',
                    schema_version: 1,
                    enabled: true,
                    approved: false,
                    approved_at: null,
                    content_hash: 'newhash',
                    policy_json: {},
                    created_at: '2026-03-18T00:00:00Z',
                    updated_at: null,
                    next_run: null,
                })
            }
            if (url.includes('/runs')) return Promise.resolve([])
            if (url.includes('/policies')) {
                return Promise.resolve({ policies: [], total: 0 })
            }
            if (url.includes('/scheduler/status')) {
                return Promise.resolve({ running: true, job_count: 0, jobs: [] })
            }
            if (url.includes('/templates')) return Promise.resolve([])
            if (url.includes('/settings')) return Promise.resolve({ value: 'UTC' })
            return Promise.resolve([])
        })

        const { default: SchedulingLayout } = await import('../SchedulingLayout')
        render(<SchedulingLayout />, { wrapper: createWrapper() })

        // Wait for initial load, then click +New
        await waitFor(() => {
            expect(screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_CREATE_BTN)).toBeInTheDocument()
        })
        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.POLICY_CREATE_BTN))

        // Wait for the mutation to fire
        await waitFor(() => {
            const postCall = capturedCalls.find(
                ([url, init]) => url.includes('/policies') && init?.method === 'POST',
            )
            expect(postCall).toBeDefined()
        })

        // Extract and validate the POST body
        const postCall = capturedCalls.find(
            ([url, init]) => url.includes('/policies') && init?.method === 'POST',
        )!
        const body = JSON.parse(postCall[1].body as string)

        // Contract: must wrap in { policy_json: {...} }
        expect(body).toHaveProperty('policy_json')
        const policyJson = body.policy_json

        // Contract: PolicyDocument requires these fields
        expect(policyJson).toHaveProperty('name')
        expect(policyJson).toHaveProperty('trigger')
        expect(policyJson).toHaveProperty('steps')

        // Contract: TriggerConfig requires cron_expression (not 'cron' or 'schedule')
        expect(policyJson.trigger).toHaveProperty('cron_expression')
        expect(policyJson.trigger.cron_expression).toBeTruthy()

        // Contract: steps must be non-empty array (min_length=1)
        expect(Array.isArray(policyJson.steps)).toBe(true)
        expect(policyJson.steps.length).toBeGreaterThanOrEqual(1)

        // Contract: each step needs id and type
        const step = policyJson.steps[0]
        expect(step).toHaveProperty('id')
        expect(step).toHaveProperty('type')
        // Step id must match pattern ^[a-z][a-z0-9_]*$
        expect(step.id).toMatch(/^[a-z][a-z0-9_]*$/)
    })

    // F2: Navigation guard — tab switching works when NOT dirty (smoke test)
    // The guard wiring is verified by confirming tabs still switch normally.
    // When dirty, the same pendingNav + modal pattern tested in list-selection
    // guard tests is used — no separate integration test needed for the modal
    // since the mechanism is shared (pendingNav → handleDiscardNav → modal portal).
    it('F2: tab switch works normally when no dirty state', async () => {
        // Mock with templates available so the template tab renders content
        const tabMock = (url: string, init?: Record<string, unknown>) => {
            if (url.includes('/runs')) return Promise.resolve([])
            if (url.includes('/templates') && !init?.method) {
                return Promise.resolve([{
                    name: 'test-template',
                    description: 'Test',
                    body_html: '<h1>Test</h1>',
                    body_format: 'html',
                    subject_template: 'Test Subject',
                    required_variables: [],
                    is_default: false,
                    sample_data_json: null,
                }])
            }
            if (url.includes('/policies')) return Promise.resolve(MOCK_POLICIES_RESPONSE)
            if (url.includes('/scheduler/status')) return Promise.resolve({ running: true, job_count: 2, jobs: [] })
            if (url.includes('/settings')) return Promise.resolve({ value: 'UTC' })
            return Promise.resolve([])
        }
        mockApiFetch.mockImplementation(tabMock)

        const { default: SchedulingLayout } = await import('../SchedulingLayout')
        render(<SchedulingLayout />, { wrapper: createWrapper() })

        // Verify we start on Report Policies tab (default)
        await waitFor(() => {
            expect(screen.getByText('Scheduling & Pipelines')).toBeInTheDocument()
        })

        // Switch to Email Templates tab — should work since nothing is dirty
        const emailTab = screen.getByTestId(SCHEDULING_TEST_IDS.TAB_EMAIL_TEMPLATES)
        fireEvent.click(emailTab)

        // Should show email templates empty state content
        await waitFor(() => {
            expect(screen.getByText(/Select a template from the list/i)).toBeInTheDocument()
        })

        // No modal should appear
        expect(screen.queryByText('Unsaved Changes')).not.toBeInTheDocument()
    })

    // F2: Dirty create guard — discard fires the deferred create mutation
    it('F2: dirty template → create → discard fires create mutation', async () => {
        const createCalls: unknown[] = []
        const tabMock = (url: string, init?: Record<string, unknown>) => {
            if (url.includes('/runs')) return Promise.resolve([])
            if (url.includes('/templates') && init?.method === 'POST') {
                createCalls.push(init)
                return Promise.resolve({
                    name: 'custom-template-new',
                    description: '',
                    body_html: '<h1>{{ report_name }}</h1>\n<p>Your report content here.</p>',
                    body_format: 'html',
                    subject_template: '',
                    required_variables: [],
                    is_default: false,
                    sample_data_json: null,
                })
            }
            if (url.includes('/templates') && !init?.method) {
                return Promise.resolve([{
                    name: 'existing-template',
                    description: 'Existing',
                    body_html: '<h1>Old</h1>',
                    body_format: 'html',
                    subject_template: 'Old Subject',
                    required_variables: [],
                    is_default: false,
                    sample_data_json: null,
                }])
            }
            if (url.includes('/policies')) return Promise.resolve({ policies: [], total: 0 })
            if (url.includes('/scheduler/status')) return Promise.resolve({ running: true, job_count: 0, jobs: [] })
            if (url.includes('/settings')) return Promise.resolve({ value: 'UTC' })
            return Promise.resolve([])
        }
        mockApiFetch.mockImplementation(tabMock)

        const { default: SchedulingLayout } = await import('../SchedulingLayout')
        render(<SchedulingLayout />, { wrapper: createWrapper() })

        // Switch to Email Templates tab
        const emailTab = screen.getByTestId(SCHEDULING_TEST_IDS.TAB_EMAIL_TEMPLATES)
        fireEvent.click(emailTab)

        // Wait for template list to render and select a template
        await waitFor(() => {
            expect(screen.getByText('existing-template')).toBeInTheDocument()
        })
        fireEvent.click(screen.getByText('existing-template'))

        // Wait for detail editor to render
        await waitFor(() => {
            expect(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_DETAIL)).toBeInTheDocument()
        })

        // Make the editor dirty by changing the subject input (has placeholder)
        const subjectInput = screen.getByPlaceholderText(/jinja2 subject/i)
        fireEvent.change(subjectInput, { target: { value: 'Modified subject' } })

        // Click +New — should show unsaved changes modal (NOT create immediately)
        fireEvent.click(screen.getByTestId(SCHEDULING_TEST_IDS.TEMPLATE_NEW_BTN))

        // Modal should appear
        await waitFor(() => {
            expect(screen.getByText('Unsaved Changes')).toBeInTheDocument()
        })

        // No create mutation should have fired yet
        expect(createCalls).toHaveLength(0)

        // Click "Discard Changes" to confirm discard
        fireEvent.click(screen.getByText('Discard Changes'))

        // Now the create mutation should fire
        await waitFor(() => {
            expect(createCalls.length).toBeGreaterThan(0)
        })
    })
})
