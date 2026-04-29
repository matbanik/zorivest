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
import { createPortal } from 'react-dom'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { SCHEDULING_TEST_IDS } from './test-ids'
import PolicyList from './PolicyList'
import PolicyDetail from './PolicyDetail'
import RunHistory from './RunHistory'
import EmailTemplateList from './EmailTemplateList'
import EmailTemplateDetail from './EmailTemplateDetail'
import EmailTemplatePreview from './EmailTemplatePreview'
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
import {
    useEmailTemplates,
    useCreateTemplate,
    useUpdateTemplate,
    useDeleteTemplate,
    useDuplicateTemplate,
    usePreviewTemplate,
} from './template-hooks'
import type { Policy } from './api'
import type { EmailTemplate } from './template-api'

const SCHEDULING_TABS = ['Report Policies', 'Email Templates'] as const
type SchedulingTab = typeof SCHEDULING_TABS[number]

export default function SchedulingLayout() {
    const [activeTab, setActiveTab] = useState<SchedulingTab>('Report Policies')
    const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
    const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(false)
    const { policies, isLoading, error } = useSchedulingPolicies()

    // ── Email Templates state ──
    const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null)
    const { templates, isLoading: templatesLoading, error: templatesError } = useEmailTemplates()
    const createTemplateMutation = useCreateTemplate()
    const updateTemplateMutation = useUpdateTemplate()
    const deleteTemplateMutation = useDeleteTemplate()
    const duplicateTemplateMutation = useDuplicateTemplate()
    const previewTemplateMutation = usePreviewTemplate()

    // ── Dirty state + unsaved changes guard ──
    const [policyDirty, setPolicyDirty] = useState(false)
    const [templateDirty, setTemplateDirty] = useState(false)
    const [pendingNav, setPendingNav] = useState<
        | { type: 'policy'; item: Policy }
        | { type: 'template'; item: EmailTemplate }
        | { type: 'tab'; tab: SchedulingTab }
        | { type: 'create-policy' }
        | { type: 'create-template' }
        | null
    >(null)

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
        if (policyDirty) {
            setPendingNav({ type: 'policy', item: policy })
            return
        }
        setSelectedPolicy(policy)
    }, [policyDirty])

    // Extracted unguarded create helper — used by both direct handler and discard branch
    const doCreatePolicy = useCallback(() => {
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

    const handleCreate = useCallback(() => {
        // F2: Guard create action when editor is dirty
        if (policyDirty) {
            setPendingNav({ type: 'create-policy' })
            return
        }
        doCreatePolicy()
    }, [policyDirty, doCreatePolicy])

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

    // ── Email Template Handlers ──

    const handleSelectTemplate = useCallback((template: EmailTemplate) => {
        if (templateDirty) {
            setPendingNav({ type: 'template', item: template })
            return
        }
        setSelectedTemplate(template)
        previewTemplateMutation.reset()
    }, [templateDirty, previewTemplateMutation])

    // Extracted unguarded create-template helper — used by both direct handler and discard branch
    const doCreateTemplate = useCallback(() => {
        const newTemplate = {
            name: `custom-template-${Date.now()}`,
            body_html: '<h1>{{ report_name }}</h1>\n<p>Your report content here.</p>',
        }
        createTemplateMutation.mutate(newTemplate, {
            onSuccess: (created) => {
                setSelectedTemplate(created)
            },
        })
    }, [createTemplateMutation])

    const handleCreateTemplate = useCallback(() => {
        // F2: Guard create action when template editor is dirty
        if (templateDirty) {
            setPendingNav({ type: 'create-template' })
            return
        }
        doCreateTemplate()
    }, [templateDirty, doCreateTemplate])

    const handleSaveTemplate = useCallback(
        (data: Partial<EmailTemplate>) => {
            if (!selectedTemplate) return
            updateTemplateMutation.mutate({
                name: selectedTemplate.name,
                payload: data,
            })
        },
        [selectedTemplate, updateTemplateMutation],
    )

    const handleDuplicateTemplate = useCallback(() => {
        if (!selectedTemplate) return
        duplicateTemplateMutation.mutate(
            {
                name: `${selectedTemplate.name}-custom`,
                body_html: selectedTemplate.body_html,
                description: selectedTemplate.description,
                body_format: selectedTemplate.body_format,
                subject_template: selectedTemplate.subject_template,
                required_variables: selectedTemplate.required_variables,
            },
            {
                onSuccess: (created) => {
                    setSelectedTemplate(created)
                },
            },
        )
    }, [selectedTemplate, duplicateTemplateMutation])

    const handleDeleteTemplate = useCallback(() => {
        if (!selectedTemplate) return
        deleteTemplateMutation.mutate(selectedTemplate.name, {
            onSuccess: () => {
                setSelectedTemplate(null)
            },
        })
    }, [selectedTemplate, deleteTemplateMutation])

    const handlePreviewTemplate = useCallback(() => {
        if (!selectedTemplate) return
        previewTemplateMutation.mutate({ name: selectedTemplate.name })
    }, [selectedTemplate, previewTemplateMutation])

    const handleRenameTemplate = useCallback((newName: string, currentPayload?: Partial<EmailTemplate>) => {
        if (!selectedTemplate) return
        // F3: Use current form payload if provided to preserve dirty edits;
        // fall back to selectedTemplate.* fields for backward compatibility
        createTemplateMutation.mutate(
            {
                name: newName,
                body_html: currentPayload?.body_html ?? selectedTemplate.body_html,
                description: currentPayload?.description ?? selectedTemplate.description,
                body_format: currentPayload?.body_format ?? selectedTemplate.body_format,
                subject_template: currentPayload?.subject_template ?? selectedTemplate.subject_template,
                required_variables: currentPayload?.required_variables ?? selectedTemplate.required_variables,
            },
            {
                onSuccess: (created) => {
                    deleteTemplateMutation.mutate(selectedTemplate.name)
                    setSelectedTemplate(created)
                    setTemplateDirty(false)
                },
            },
        )
    }, [selectedTemplate, createTemplateMutation, deleteTemplateMutation])

    const handleDiscardNav = useCallback(() => {
        if (!pendingNav) return
        switch (pendingNav.type) {
            case 'policy':
                setPolicyDirty(false)
                setSelectedPolicy(pendingNav.item)
                break
            case 'template':
                setTemplateDirty(false)
                setSelectedTemplate(pendingNav.item)
                previewTemplateMutation.reset()
                break
            case 'tab':
                setPolicyDirty(false)
                setTemplateDirty(false)
                setActiveTab(pendingNav.tab)
                break
            case 'create-policy':
                setPolicyDirty(false)
                doCreatePolicy()
                break
            case 'create-template':
                setTemplateDirty(false)
                doCreateTemplate()
                break
        }
        setPendingNav(null)
    }, [pendingNav, previewTemplateMutation, doCreatePolicy, doCreateTemplate])

    // Keep selected template in sync when templates refresh
    const currentTemplate = selectedTemplate
        ? templates.find((t) => t.name === selectedTemplate.name) ?? selectedTemplate
        : null

    return (
        <>
        <div data-testid={SCHEDULING_TEST_IDS.ROOT} className="flex flex-col h-full">
            {/* Tab Bar (§6K.1) */}
            <div className="flex border-b border-bg-subtle px-4">
                {SCHEDULING_TABS.map((tab) => (
                    <button
                        key={tab}
                        data-testid={
                            tab === 'Report Policies'
                                ? SCHEDULING_TEST_IDS.TAB_REPORT_POLICIES
                                : SCHEDULING_TEST_IDS.TAB_EMAIL_TEMPLATES
                        }
                        onClick={() => {
                            // F2: Guard tab switch when editor is dirty
                            if ((policyDirty || templateDirty) && tab !== activeTab) {
                                setPendingNav({ type: 'tab', tab })
                                return
                            }
                            setActiveTab(tab)
                        }}
                        className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                            activeTab === tab
                                ? 'text-accent border-accent'
                                : 'text-fg-muted border-transparent hover:text-fg'
                        }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
                {activeTab === 'Report Policies' && (
                    <div className="flex h-full">
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
                                    {/* Policy detail (scrollable area takes up remaining space) */}
                                    <div className={`min-h-0 overflow-y-auto ${isHistoryCollapsed ? 'flex-1' : 'flex-[2_2_0%]'}`}>
                                        <PolicyDetail
                                            policy={currentPolicy}
                                            onSave={handleSave}
                                            onApprove={handleApprove}
                                            onDelete={handleDelete}
                                            onTriggerRun={handleTriggerRun}
                                            onPatchSchedule={handlePatchSchedule}
                                            onRename={handleRename}
                                            onDirtyChange={setPolicyDirty}
                                            isSaving={updateMutation.isPending}
                                        />
                                    </div>

                                    {/* Run History — collapsible bottom panel */}
                                    <div className={`border-t border-bg-subtle/30 flex flex-col shrink-0 ${isHistoryCollapsed ? '' : 'flex-[1_1_0%] min-h-[120px] max-h-[40%]'}`}>
                                        {/* Collapsible header with +/- toggle */}
                                        <button
                                            type="button"
                                            onClick={() => setIsHistoryCollapsed((prev) => !prev)}
                                            className="w-full px-4 py-2 flex items-center justify-between border-b border-bg-subtle/20 cursor-pointer hover:bg-bg-subtle/10 transition-colors shrink-0"
                                        >
                                            <div className="flex items-center gap-2">
                                                <span className="text-fg-muted/70 text-sm font-mono w-4 text-center">
                                                    {isHistoryCollapsed ? '+' : '−'}
                                                </span>
                                                <h4 className="text-xs font-semibold text-fg-muted uppercase tracking-wider">
                                                    Run history
                                                </h4>
                                            </div>
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
                                        </button>
                                        {/* Collapsible content */}
                                        {!isHistoryCollapsed && (
                                            <div className="flex-1 min-h-0 overflow-y-auto">
                                                <RunHistory
                                                    runs={runs}
                                                    isLoading={runsLoading}
                                                    timezone={
                                                        ((currentPolicy?.policy_json as Record<string, unknown>)?.trigger as Record<string, unknown>)?.timezone as string | undefined
                                                    }
                                                />
                                            </div>
                                        )}
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
                )}

                {activeTab === 'Email Templates' && (
                    <div className="flex h-full">
                        {/* Left pane — Template list */}
                        <div className="w-[280px] min-w-[240px] border-r border-bg-subtle/30 flex-shrink-0">
                            <EmailTemplateList
                                templates={templates}
                                selectedTemplateName={currentTemplate?.name ?? null}
                                onSelect={handleSelectTemplate}
                                onCreate={handleCreateTemplate}
                                isLoading={templatesLoading}
                                error={templatesError}
                            />
                        </div>

                        {/* Right pane — Template detail + Preview */}
                        <div className="flex-1 min-w-0 flex flex-col">
                            {currentTemplate ? (
                                <>
                                    <div className="flex-1 min-h-0 overflow-y-auto">
                                        <EmailTemplateDetail
                                            template={currentTemplate}
                                            onSave={handleSaveTemplate}
                                            onDuplicate={handleDuplicateTemplate}
                                            onDelete={handleDeleteTemplate}
                                            onPreview={handlePreviewTemplate}
                                            onRename={handleRenameTemplate}
                                            onDirtyChange={setTemplateDirty}
                                            isSaving={updateTemplateMutation.isPending}
                                            deleteError={deleteTemplateMutation.error instanceof Error ? deleteTemplateMutation.error.message : deleteTemplateMutation.error ? String(deleteTemplateMutation.error) : null}
                                        />
                                    </div>
                                    {/* Preview (always visible below editor — UX2) */}
                                    <div className="border-t border-bg-subtle/30 max-h-[35%] overflow-y-auto p-4">
                                        <EmailTemplatePreview
                                            renderedHtml={previewTemplateMutation.data?.body_rendered ?? null}
                                            isLoading={previewTemplateMutation.isPending}
                                            error={previewTemplateMutation.error instanceof Error ? previewTemplateMutation.error.message : previewTemplateMutation.error ? String(previewTemplateMutation.error) : null}
                                        />
                                    </div>
                                </>
                            ) : (
                                <div className="flex-1 flex items-center justify-center">
                                    <div className="text-center text-fg-muted">
                                        <div className="text-4xl mb-3">📧</div>
                                        <h3 className="text-lg font-medium text-fg mb-1">
                                            Email Templates
                                        </h3>
                                        <p className="text-sm max-w-[300px]">
                                            Select a template from the list to edit, or create a new one
                                            for your pipeline reports.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>

            {/* Unsaved changes confirmation modal */}
            {pendingNav && createPortal(
                <div className="fixed inset-0 z-[9999] flex items-center justify-center" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}>
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0"
                        style={{ backgroundColor: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }}
                        onClick={() => setPendingNav(null)}
                    />
                    {/* Dialog */}
                    <div
                        style={{
                            position: 'relative',
                            backgroundColor: 'var(--color-bg-elevated, #1e2030)',
                            border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                            borderRadius: '12px',
                            padding: '24px',
                            maxWidth: '400px',
                            width: '90%',
                            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
                            color: 'var(--color-fg, #e0e0e0)',
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                            <div style={{
                                width: '40px', height: '40px', borderRadius: '50%',
                                backgroundColor: 'rgba(255,184,108,0.15)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                            }}>
                                <span style={{ color: 'var(--color-accent-amber, #ffb86c)', fontSize: '18px' }}>⚠</span>
                            </div>
                            <div>
                                <h4 style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: 'var(--color-fg, #e0e0e0)' }}>Unsaved Changes</h4>
                                <p style={{ fontSize: '12px', color: 'var(--color-fg-muted, #8b8fa3)', margin: '2px 0 0 0' }}>Your edits have not been saved.</p>
                            </div>
                        </div>
                        <p style={{ fontSize: '14px', color: 'var(--color-fg-muted, #8b8fa3)', marginBottom: '20px' }}>
                            You have unsaved changes that will be lost if you navigate away.
                        </p>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                            <button
                                onClick={() => setPendingNav(null)}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '6px',
                                    fontSize: '13px',
                                    fontWeight: 500,
                                    border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                                    backgroundColor: 'transparent',
                                    color: 'var(--color-fg, #e0e0e0)',
                                    cursor: 'pointer',
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDiscardNav}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '6px',
                                    fontSize: '13px',
                                    fontWeight: 500,
                                    border: '1px solid rgba(239,68,68,0.5)',
                                    backgroundColor: 'rgba(239,68,68,0.1)',
                                    color: 'var(--color-accent-red, #ef4444)',
                                    cursor: 'pointer',
                                }}
                            >
                                Discard Changes
                            </button>
                        </div>
                    </div>
                </div>,
                document.body,
            )}
        </>
    )
}
