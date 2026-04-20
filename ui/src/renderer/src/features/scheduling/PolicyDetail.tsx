/**
 * PolicyDetail — right pane showing policy detail with JSON editor.
 *
 * Redesigned with:
 * - 3-state lifecycle pill (Draft → Ready → Scheduled)
 * - Inline-editable policy name
 * - CronPicker (frequency-based visual builder)
 * - Cleaned up Run Now section
 *
 * Source: 06e-gui-scheduling.md §Schedule Detail Fields
 * MEU: MEU-72 (gui-scheduling)
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { EditorView, keymap } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { json } from '@codemirror/lang-json'
import { oneDark } from '@codemirror/theme-one-dark'
import { basicSetup } from 'codemirror'
import { SCHEDULING_TEST_IDS } from './test-ids'
import { formatTimestamp } from '@/lib/formatDate'
import type { Policy } from './api'
import CronPicker from './CronPicker'

// ── Policy State helpers ───────────────────────────────────────────────

type PolicyState = 'draft' | 'ready' | 'scheduled'

function getPolicyState(policy: Policy): PolicyState {
    if (!policy.approved) return 'draft'
    if (!policy.enabled) return 'ready'
    return 'scheduled'
}

const STATE_CONFIG: Record<PolicyState, { label: string; color: string; bgClass: string; dotClass: string }> = {
    draft: {
        label: 'Draft',
        color: 'text-accent-orange',
        bgClass: 'bg-accent-orange/15 hover:bg-accent-orange/25',
        dotClass: 'bg-accent-orange',
    },
    ready: {
        label: 'Ready',
        color: 'text-accent-yellow',
        bgClass: 'bg-accent-yellow/15 hover:bg-accent-yellow/25',
        dotClass: 'bg-accent-yellow',
    },
    scheduled: {
        label: 'Scheduled',
        color: 'text-accent-green',
        bgClass: 'bg-accent-green/15 hover:bg-accent-green/25',
        dotClass: 'bg-accent-green',
    },
}

// ── Props ──────────────────────────────────────────────────────────────

interface PolicyDetailProps {
    policy: Policy
    onSave: (policyJson: Record<string, unknown>) => void
    onApprove: () => void
    onDelete: () => void
    onTriggerRun: (dryRun: boolean) => void
    onPatchSchedule: (params: { cron_expression?: string; enabled?: boolean; timezone?: string }) => void
    onRename: (newName: string) => void
    isSaving: boolean
}

export default function PolicyDetail({
    policy,
    onSave,
    onApprove,
    onDelete,
    onTriggerRun,
    onPatchSchedule,
    onRename,
    isSaving,
}: PolicyDetailProps) {
    const editorRef = useRef<HTMLDivElement>(null)
    const viewRef = useRef<EditorView | null>(null)
    const [jsonError, setJsonError] = useState<string | null>(null)
    const [confirmRun, setConfirmRun] = useState(false)
    const confirmRunTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    // ── Inline editable name ───────────────────────────────────────────
    const [isEditingName, setIsEditingName] = useState(false)
    const [editName, setEditName] = useState(policy.name)
    const nameInputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        setEditName(policy.name)
    }, [policy.name])

    useEffect(() => {
        if (isEditingName && nameInputRef.current) {
            nameInputRef.current.focus()
            nameInputRef.current.select()
        }
    }, [isEditingName])

    const handleNameSubmit = useCallback(() => {
        setIsEditingName(false)
        const trimmed = editName.trim()
        if (trimmed && trimmed !== policy.name) {
            onRename(trimmed)
        } else {
            setEditName(policy.name) // revert if empty or same
        }
    }, [editName, policy.name, onRename])

    // ── Extract trigger fields from policy_json (FIXED path) ───────────
    const trigger = (policy.policy_json as Record<string, unknown>)?.trigger as Record<string, unknown> | undefined
    const cronExpression = (trigger?.cron_expression as string) || ''
    const timezone = (trigger?.timezone as string) || 'UTC'

    // ── Policy state ───────────────────────────────────────────────────
    const policyState = getPolicyState(policy)
    const stateConfig = STATE_CONFIG[policyState]

    // ── State transitions ──────────────────────────────────────────────
    const handleStateAdvance = useCallback(() => {
        if (policyState === 'draft') {
            // Draft → Ready: approve the policy
            onApprove()
        } else if (policyState === 'ready') {
            // Ready → Scheduled: enable the schedule
            onPatchSchedule({ enabled: true })
        } else if (policyState === 'scheduled') {
            // Scheduled → Ready: pause the schedule
            onPatchSchedule({ enabled: false })
        }
    }, [policyState, onApprove, onPatchSchedule])

    const stateTooltip = useMemo(() => ({
        draft: 'Click to approve this policy',
        ready: 'Click to activate schedule',
        scheduled: 'Click to pause schedule',
    }[policyState]), [policyState])

    // ── Stable JSON string for CodeMirror ──────────────────────────────
    const policyJsonStr = useMemo(
        () => JSON.stringify(policy.policy_json, null, 2),
        [policy.policy_json],
    )

    // ── Initialize CodeMirror editor ───────────────────────────────────
    useEffect(() => {
        if (!editorRef.current) return

        const state = EditorState.create({
            doc: policyJsonStr,
            extensions: [
                basicSetup,
                json(),
                oneDark,
                EditorView.theme({
                    '&': { height: '300px', fontSize: '13px' },
                    '.cm-scroller': { overflow: 'auto' },
                    '.cm-content': { fontFamily: 'var(--font-mono)' },
                }),
                keymap.of([]),
            ],
        })

        const view = new EditorView({
            state,
            parent: editorRef.current,
        })

        viewRef.current = view

        return () => {
            view.destroy()
            viewRef.current = null
        }
    }, [policy.id, policyJsonStr])

    const handleSave = useCallback(() => {
        if (!viewRef.current) return
        const text = viewRef.current.state.doc.toString()
        try {
            const parsed = JSON.parse(text)
            setJsonError(null)
            onSave(parsed)
        } catch (e) {
            setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
        }
    }, [onSave])

    const handleDelete = useCallback(() => {
        if (window.confirm(`Delete policy "${policy.name}"? This cannot be undone.`)) {
            onDelete()
        }
    }, [onDelete, policy.name])

    // ── Cron change handler ────────────────────────────────────────────
    // Updates BOTH the schedule metadata via PATCH AND the policy_json
    // via PUT so the JSON editor stays in sync.
    const handleCronChange = useCallback(
        (newCron: string) => {
            onPatchSchedule({ cron_expression: newCron })
        },
        [onPatchSchedule],
    )

    // ── Test Run handler ───────────────────────────────────────────────
    const handleTestRun = useCallback(() => {
        onTriggerRun(true) // always dry-run
    }, [onTriggerRun])

    // ── Run Now handler (two-click confirmation) ───────────────────────
    const handleRunNow = useCallback(() => {
        if (confirmRun) {
            onTriggerRun(false) // real execution
            setConfirmRun(false)
            if (confirmRunTimerRef.current) clearTimeout(confirmRunTimerRef.current)
        } else {
            setConfirmRun(true)
            confirmRunTimerRef.current = setTimeout(() => setConfirmRun(false), 3000)
        }
    }, [confirmRun, onTriggerRun])

    return (
        <div data-testid={SCHEDULING_TEST_IDS.POLICY_DETAIL} className="h-full overflow-y-auto">
            <div className="p-4 space-y-4">
                {/* ── Header: Editable Name + State Pill ── */}
                <div className="flex items-center justify-between gap-3">
                    {/* Editable policy name */}
                    {isEditingName ? (
                        <input
                            ref={nameInputRef}
                            data-testid={SCHEDULING_TEST_IDS.POLICY_NAME_INPUT}
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            onBlur={handleNameSubmit}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') handleNameSubmit()
                                if (e.key === 'Escape') {
                                    setEditName(policy.name)
                                    setIsEditingName(false)
                                }
                            }}
                            className="text-lg font-semibold text-fg bg-transparent border-b-2 border-accent-cyan outline-none px-0 py-0 flex-1 min-w-0"
                        />
                    ) : (
                        <h3
                            data-testid={SCHEDULING_TEST_IDS.POLICY_NAME}
                            className="text-lg font-semibold text-fg cursor-pointer hover:text-accent-cyan transition-colors truncate"
                            onClick={() => setIsEditingName(true)}
                            title="Click to rename"
                        >
                            {policy.name}
                            <span className="text-fg-muted/40 text-sm ml-2">✏️</span>
                        </h3>
                    )}

                    {/* 3-state lifecycle pill */}
                    <button
                        data-testid={SCHEDULING_TEST_IDS.POLICY_STATE_PILL}
                        onClick={handleStateAdvance}
                        title={stateTooltip}
                        type="button"
                        className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0 cursor-pointer ${stateConfig.bgClass} ${stateConfig.color}`}
                    >
                        <span className={`w-2 h-2 rounded-full ${stateConfig.dotClass}`} />
                        {stateConfig.label}
                    </button>
                </div>

                {/* State context info */}
                {policyState === 'draft' && (
                    <div className="text-xs text-accent-orange/80 bg-accent-orange/10 px-3 py-1.5 rounded-md">
                        📝 This policy is a draft. Click the status pill to approve it for execution.
                    </div>
                )}

                {/* Approval-reset notice */}
                {policyState === 'draft' && policy.updated_at && (
                    <div className="text-xs text-fg-muted/60 bg-bg-elevated/30 px-3 py-1 rounded-md">
                        ℹ️ Changing the schedule or policy content resets approval. Re-approve after making changes.
                    </div>
                )}

                {/* ── Scheduling Trigger section ── */}
                <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-fg-muted uppercase tracking-wider">
                        Schedule
                    </h4>
                    <div className="grid grid-cols-[1fr_auto] gap-3 items-start">
                        <CronPicker
                            value={cronExpression}
                            onChange={handleCronChange}
                        />
                        <div>
                            <label className="block text-xs text-fg-muted mb-1">Timezone</label>
                            <select
                                value={timezone}
                                onChange={(e) =>
                                    onPatchSchedule({ timezone: e.target.value })
                                }
                                className="px-2 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg focus:outline-none focus:border-accent-cyan"
                            >
                                <option value="UTC">UTC</option>
                                <option value="America/New_York">America/New_York</option>
                                <option value="America/Chicago">America/Chicago</option>
                                <option value="America/Denver">America/Denver</option>
                                <option value="America/Los_Angeles">America/Los_Angeles</option>
                                <option value="Europe/London">Europe/London</option>
                                <option value="Europe/Berlin">Europe/Berlin</option>
                                <option value="Asia/Tokyo">Asia/Tokyo</option>
                            </select>
                        </div>
                    </div>
                    {policy.next_run && (
                        <div className="text-xs text-fg-muted">
                            Next run:{' '}
                            <span className="text-fg">
                                {formatTimestamp(policy.next_run, timezone)}
                            </span>
                        </div>
                    )}
                </div>

                {/* ── Policy document (JSON editor) ── */}
                <div className="space-y-2">
                    <div className="flex items-baseline gap-3">
                        <h4 className="text-xs font-semibold text-fg-muted uppercase tracking-wider shrink-0">
                            Policy document
                        </h4>
                        <div className="text-[11px] text-fg-muted/50 flex items-baseline gap-2 flex-wrap">
                            <span>Schema v{policy.schema_version} · Hash: {policy.content_hash.slice(0, 8)}</span>
                            <span>Created: {formatTimestamp(policy.created_at, timezone)}</span>
                            {policy.updated_at && (
                                <span>Updated: {formatTimestamp(policy.updated_at, timezone)}</span>
                            )}
                        </div>
                    </div>
                    <div
                        data-testid={SCHEDULING_TEST_IDS.POLICY_JSON_EDITOR}
                        ref={editorRef}
                        className="rounded-md overflow-hidden border border-bg-subtle"
                    />
                    {jsonError && (
                        <div className="text-xs text-accent-red mt-1">
                            ⚠️ {jsonError}
                        </div>
                    )}
                </div>

                {/* ── Actions ── */}
                <div className="flex items-center gap-2 pt-2 border-t border-bg-subtle/30">
                    <button
                        data-testid={SCHEDULING_TEST_IDS.POLICY_SAVE_BTN}
                        onClick={handleSave}
                        disabled={isSaving}
                        type="button"
                        className="px-3 py-1.5 text-sm font-medium rounded-md border border-accent-green/30 bg-accent-green/20 text-accent-green hover:bg-accent-green/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSaving ? 'Saving…' : 'Save'}
                    </button>

                    <button
                        data-testid={SCHEDULING_TEST_IDS.TEST_RUN_BTN}
                        onClick={handleTestRun}
                        disabled={policyState === 'draft'}
                        type="button"
                        className="px-3 py-1.5 text-sm font-medium rounded-md border border-accent-cyan/30 bg-accent-cyan/20 text-accent-cyan hover:bg-accent-cyan/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title={
                            policyState === 'draft'
                                ? 'Approve the policy first to enable execution'
                                : 'Execute pipeline in dry-run mode (no side effects)'
                        }
                    >
                        Test Run
                    </button>

                    <button
                        data-testid={SCHEDULING_TEST_IDS.RUN_NOW_BTN}
                        onClick={handleRunNow}
                        disabled={policyState === 'draft'}
                        type="button"
                        className={`px-3 py-1.5 text-sm font-medium rounded-md border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                            confirmRun
                                ? 'bg-accent-orange text-fg border-accent-orange'
                                : 'border-accent-green/30 bg-accent-green/20 text-accent-green hover:bg-accent-green/30'
                        }`}
                        title={
                            policyState === 'draft'
                                ? 'Approve the policy first to enable execution'
                                : confirmRun
                                    ? 'Click again to confirm execution'
                                    : 'Trigger immediate pipeline execution'
                        }
                    >
                        {confirmRun ? 'Confirm Run' : 'Run Now'}
                    </button>

                    {/* Inline status pill — duplicate of header pill for quick access */}
                    <button
                        data-testid="policy-state-pill-inline"
                        onClick={handleStateAdvance}
                        title={stateTooltip}
                        type="button"
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors shrink-0 cursor-pointer border ${stateConfig.bgClass} ${stateConfig.color} border-current/20`}
                    >
                        <span className={`w-1.5 h-1.5 rounded-full ${stateConfig.dotClass}`} />
                        {stateConfig.label}
                    </button>

                    <div className="ml-auto">
                        <button
                            data-testid={SCHEDULING_TEST_IDS.POLICY_DELETE_BTN}
                            onClick={handleDelete}
                            type="button"
                            className="px-3 py-1.5 text-sm font-medium rounded-md border bg-accent-red/20 text-accent-red border-accent-red/30 hover:bg-accent-red/30 transition-colors"
                        >
                            Delete
                        </button>
                    </div>
                </div>


            </div>
        </div>
    )
}
