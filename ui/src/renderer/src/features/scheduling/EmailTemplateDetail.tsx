/**
 * EmailTemplateDetail — editor for a single email template.
 *
 * Shows all fields from §6K.3, default protection (§6K.4),
 * and action buttons (§6K.5).
 *
 * Source: 06k-gui-email-templates.md §6K.3, §6K.4, §6K.5
 * MEU: MEU-72b (gui-email-templates)
 */

import { useState, useEffect, useCallback, useMemo, useRef, type KeyboardEvent } from 'react'
import { createPortal } from 'react-dom'
import { SCHEDULING_TEST_IDS } from './test-ids'
import type { EmailTemplate } from './template-api'

// Well-known pipeline variables that the pipeline runner always injects
// or that are commonly produced by step output_keys.
const KNOWN_PIPELINE_VARIABLES = [
    'date',
    'policy_id',
    'run_id',
    'accounts',
    'recent_trades',
    'trade_plans',
    'watchlist_items',
    'open_positions',
    'total_pnl',
    'day_change',
    'watchlist_alerts',
    'quotes',
    'news',
    'report_name',
    'summary',
    'portfolio_value',
    'results',
    'composed',
    'ticker',
    'strategy_name',
] as const

interface EmailTemplateDetailProps {
    template: EmailTemplate
    onSave: (data: Partial<EmailTemplate>) => void
    onDuplicate: () => void
    onDelete: () => void
    onPreview: () => void
    onRename: (newName: string, currentPayload?: Partial<EmailTemplate>) => void
    onDirtyChange?: (isDirty: boolean) => void
    isSaving: boolean
    deleteError?: string | null
}

export default function EmailTemplateDetail({
    template,
    onSave,
    onDuplicate,
    onDelete,
    onPreview,
    onRename,
    onDirtyChange,
    isSaving,
    deleteError,
}: EmailTemplateDetailProps) {
    const isDefault = template.is_default
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

    // ── Inline editable name ───────────────────────────────────────────
    const [isEditingName, setIsEditingName] = useState(false)
    const [editName, setEditName] = useState(template.name)
    const nameInputRef = useRef<HTMLInputElement>(null)

    // Local form state
    const [description, setDescription] = useState(template.description)
    const [bodyFormat, setBodyFormat] = useState(template.body_format)
    const [subjectTemplate, setSubjectTemplate] = useState(template.subject_template)
    const [bodyHtml, setBodyHtml] = useState(template.body_html)
    const [requiredVariables, setRequiredVariables] = useState(template.required_variables)
    const [newVariable, setNewVariable] = useState('')
    const [showVarDropdown, setShowVarDropdown] = useState(false)
    const [highlightedIdx, setHighlightedIdx] = useState(-1)
    const varInputRef = useRef<HTMLInputElement>(null)
    const dropdownRef = useRef<HTMLDivElement>(null)

    // Dirty state tracking
    const isDirty = useMemo(() => {
        return (
            description !== template.description ||
            bodyFormat !== template.body_format ||
            subjectTemplate !== template.subject_template ||
            bodyHtml !== template.body_html ||
            JSON.stringify(requiredVariables) !== JSON.stringify(template.required_variables)
        )
    }, [description, bodyFormat, subjectTemplate, bodyHtml, requiredVariables, template])

    useEffect(() => {
        onDirtyChange?.(isDirty)
    }, [isDirty, onDirtyChange])

    // Reset form when template changes
    useEffect(() => {
        setEditName(template.name)
        setIsEditingName(false)
        setDescription(template.description)
        setBodyFormat(template.body_format)
        setSubjectTemplate(template.subject_template)
        setBodyHtml(template.body_html)
        setRequiredVariables(template.required_variables)
        setNewVariable('')
    }, [template])

    useEffect(() => {
        if (isEditingName && nameInputRef.current) {
            nameInputRef.current.focus()
            nameInputRef.current.select()
        }
    }, [isEditingName])

    const handleNameSubmit = useCallback(() => {
        setIsEditingName(false)
        const trimmed = editName.trim()
        if (trimmed && trimmed !== template.name) {
            // F3: Pass current form payload to preserve dirty edits
            onRename(trimmed, {
                body_html: bodyHtml,
                description,
                body_format: bodyFormat,
                subject_template: subjectTemplate,
                required_variables: requiredVariables,
            })
        } else {
            setEditName(template.name)
        }
    }, [editName, template.name, onRename])

    const handleSave = () => {
        onSave({
            body_html: bodyHtml,
            description,
            body_format: bodyFormat,
            subject_template: subjectTemplate,
            required_variables: requiredVariables,
        })
    }

    const handleDelete = useCallback(() => {
        setShowDeleteConfirm(true)
    }, [])

    const handleConfirmDelete = useCallback(() => {
        setShowDeleteConfirm(false)
        onDelete()
    }, [onDelete])

    // ── Variable suggestion engine ─────────────────────────────────────
    // Extract {{ variable }} references from template body + subject
    const detectedVars = useMemo(() => {
        // F4: Extended regex to capture dotted references like {{ quote.symbol }}
        // Uses optional group so single-char vars ({{ x }}) still match
        const regex = /\{\{\s*([a-zA-Z_](?:[a-zA-Z0-9_.]*[a-zA-Z0-9_])?)\s*\}\}/g
        const found = new Set<string>()
        for (const source of [bodyHtml, subjectTemplate]) {
            let match: RegExpExecArray | null
            while ((match = regex.exec(source)) !== null) {
                found.add(match[1])
            }
        }
        return Array.from(found)
    }, [bodyHtml, subjectTemplate])

    // Combine detected + known, filter out already-added
    const allSuggestions = useMemo(() => {
        const merged = new Set<string>([
            ...detectedVars,
            ...KNOWN_PIPELINE_VARIABLES,
        ])
        // Remove already-added variables
        requiredVariables.forEach((v) => merged.delete(v))
        return Array.from(merged).sort()
    }, [detectedVars, requiredVariables])

    const filteredSuggestions = useMemo(() => {
        const q = newVariable.trim().toLowerCase()
        if (!q) return allSuggestions
        return allSuggestions.filter((v) => v.toLowerCase().includes(q))
    }, [newVariable, allSuggestions])

    const handleAddVariable = useCallback((value?: string) => {
        const trimmed = (value ?? newVariable).trim()
        if (trimmed && !requiredVariables.includes(trimmed)) {
            setRequiredVariables([...requiredVariables, trimmed])
            setNewVariable('')
            setShowVarDropdown(false)
            setHighlightedIdx(-1)
        }
    }, [newVariable, requiredVariables])

    const handleVarKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Escape') {
            setShowVarDropdown(false)
            setHighlightedIdx(-1)
            return
        }
        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setHighlightedIdx((prev) =>
                prev < filteredSuggestions.length - 1 ? prev + 1 : 0,
            )
            return
        }
        if (e.key === 'ArrowUp') {
            e.preventDefault()
            setHighlightedIdx((prev) =>
                prev > 0 ? prev - 1 : filteredSuggestions.length - 1,
            )
            return
        }
        if (e.key === 'Enter') {
            e.preventDefault()
            if (highlightedIdx >= 0 && highlightedIdx < filteredSuggestions.length) {
                handleAddVariable(filteredSuggestions[highlightedIdx])
            } else {
                handleAddVariable()
            }
            return
        }
    }, [filteredSuggestions, highlightedIdx, handleAddVariable])

    // Close dropdown when clicking outside
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(e.target as Node) &&
                varInputRef.current &&
                !varInputRef.current.contains(e.target as Node)
            ) {
                setShowVarDropdown(false)
                setHighlightedIdx(-1)
            }
        }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    const handleRemoveVariable = (variable: string) => {
        setRequiredVariables(requiredVariables.filter((v) => v !== variable))
    }

    return (
    <>
        <div
            data-testid={SCHEDULING_TEST_IDS.TEMPLATE_DETAIL}
            className="p-4 space-y-4 overflow-y-auto"
        >
            {/* Default protection banner (§6K.4) */}
            {isDefault && (
                <div className="px-3 py-2 rounded bg-accent-amber/10 border border-accent-amber/30 text-sm text-accent-amber">
                    ⚠️ Default templates cannot be modified. Duplicate to create a custom version.
                </div>
            )}

            {/* Header: Editable Name (matches PolicyDetail pencil-edit pattern) */}
            <div className="flex items-center gap-2">
                {isEditingName && !isDefault ? (
                    <input
                        ref={nameInputRef}
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onBlur={handleNameSubmit}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleNameSubmit()
                            if (e.key === 'Escape') {
                                setEditName(template.name)
                                setIsEditingName(false)
                            }
                        }}
                        className="text-lg font-semibold text-fg bg-transparent border-b-2 border-accent-cyan outline-none px-0 py-0 flex-1 min-w-0"
                    />
                ) : (
                    <h3
                        className={`text-lg font-semibold text-fg truncate ${!isDefault ? 'cursor-pointer hover:text-accent-cyan transition-colors' : ''}`}
                        onClick={() => !isDefault && setIsEditingName(true)}
                        title={isDefault ? 'Default template names cannot be changed' : 'Click to rename'}
                    >
                        {template.name}
                        {!isDefault && <span className="text-fg-muted/40 text-sm ml-2">✏️</span>}
                    </h3>
                )}
            </div>

            {/* Action buttons (§6K.5) */}
            <div className="flex items-center gap-2">
                <button
                    data-testid={SCHEDULING_TEST_IDS.TEMPLATE_SAVE_BTN}
                    onClick={handleSave}
                    disabled={isDefault || isSaving || !isDirty}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors cursor-pointer ${
                        isDefault || isSaving || !isDirty
                            ? 'bg-bg-subtle/30 text-fg-muted cursor-not-allowed'
                            : 'border border-accent-green/30 bg-accent-green/20 text-accent-green hover:bg-accent-green/30'
                    }`}
                >
                    {isSaving ? 'Saving…' : 'Save'}
                </button>
                <button
                    data-testid={SCHEDULING_TEST_IDS.TEMPLATE_DUPLICATE_BTN}
                    onClick={onDuplicate}
                    className="px-3 py-1.5 rounded text-sm font-medium border border-bg-subtle/50 text-fg hover:bg-bg-subtle/30 transition-colors cursor-pointer"
                >
                    Duplicate
                </button>
                <button
                    data-testid={SCHEDULING_TEST_IDS.TEMPLATE_DELETE_BTN}
                    onClick={handleDelete}
                    disabled={isDefault}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors cursor-pointer ${
                        isDefault
                            ? 'bg-bg-subtle/30 text-fg-muted cursor-not-allowed'
                            : 'border border-accent-red/50 text-accent-red hover:bg-accent-red/10'
                    }`}
                >
                    Delete
                </button>
                <div className="flex-1" />
                <button
                    data-testid={SCHEDULING_TEST_IDS.TEMPLATE_PREVIEW_BTN}
                    onClick={onPreview}
                    disabled={!bodyHtml.trim()}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors cursor-pointer ${
                        !bodyHtml.trim()
                            ? 'bg-bg-subtle/30 text-fg-muted cursor-not-allowed'
                            : 'border border-accent-cyan/50 text-accent-cyan hover:bg-accent-cyan/10'
                    }`}
                >
                    Preview
                </button>
            </div>

            {/* Description */}
            <div>
                <label className="block text-xs font-medium text-fg-muted mb-1">Description</label>
                <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    readOnly={isDefault}
                    rows={2}
                    className="w-full px-2 py-1.5 rounded border border-bg-subtle/50 bg-bg text-sm text-fg resize-none focus:border-accent focus:outline-none"
                />
            </div>

            {/* Format */}
            <div>
                <label className="block text-xs font-medium text-fg-muted mb-1">Format</label>
                <select
                    value={bodyFormat}
                    onChange={(e) => setBodyFormat(e.target.value as 'html' | 'markdown')}
                    disabled={isDefault}
                    className="w-full px-2 py-1.5 rounded border border-bg-subtle/50 bg-bg text-sm text-fg focus:border-accent focus:outline-none"
                >
                    <option value="html">HTML</option>
                    <option value="markdown">Markdown</option>
                </select>
            </div>

            {/* Subject Template */}
            <div>
                <label className="block text-xs font-medium text-fg-muted mb-1">Subject Template</label>
                <input
                    type="text"
                    value={subjectTemplate}
                    onChange={(e) => setSubjectTemplate(e.target.value)}
                    readOnly={isDefault}
                    placeholder="Jinja2 subject line template"
                    className="w-full px-2 py-1.5 rounded border border-bg-subtle/50 bg-bg text-sm text-fg focus:border-accent focus:outline-none"
                />
            </div>

            {/* Required Variables (chip list + autocomplete dropdown) */}
            <div>
                <label className="block text-xs font-medium text-fg-muted mb-1">Required Variables</label>
                <div className="flex flex-wrap gap-1.5 mb-1.5">
                    {requiredVariables.map((variable) => (
                        <span
                            key={variable}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-accent-purple/15 text-accent-purple text-xs font-medium"
                        >
                            {variable}
                            {!isDefault && (
                                <button
                                    onClick={() => handleRemoveVariable(variable)}
                                    className="text-accent-purple/60 hover:text-accent-purple cursor-pointer"
                                >
                                    ×
                                </button>
                            )}
                        </span>
                    ))}
                </div>
                {!isDefault && (
                    <div className="relative">
                        <div className="flex gap-1.5">
                            <input
                                ref={varInputRef}
                                type="text"
                                value={newVariable}
                                onChange={(e) => {
                                    setNewVariable(e.target.value)
                                    setShowVarDropdown(true)
                                    setHighlightedIdx(-1)
                                }}
                                onFocus={() => setShowVarDropdown(true)}
                                onKeyDown={handleVarKeyDown}
                                placeholder="Search or add variable…"
                                className="flex-1 px-2 py-1 rounded border border-bg-subtle/50 bg-bg text-xs text-fg focus:border-accent focus:outline-none"
                                autoComplete="off"
                            />
                            <button
                                onClick={() => handleAddVariable()}
                                disabled={!newVariable.trim()}
                                className={`px-2 py-1 rounded text-xs cursor-pointer transition-colors ${
                                    !newVariable.trim()
                                        ? 'bg-bg-subtle/20 text-fg-muted/40 cursor-not-allowed'
                                        : 'bg-accent-purple/15 text-accent-purple hover:bg-accent-purple/25'
                                }`}
                            >
                                Add
                            </button>
                        </div>
                        {/* Autocomplete dropdown */}
                        {showVarDropdown && filteredSuggestions.length > 0 && (
                            <div
                                ref={dropdownRef}
                                className="absolute left-0 right-0 mt-1 z-50 rounded-md border border-bg-subtle/50 bg-bg-elevated shadow-lg max-h-[200px] overflow-y-auto"
                            >
                                {filteredSuggestions.map((suggestion, idx) => {
                                    const isDetected = detectedVars.includes(suggestion)
                                    return (
                                        <button
                                            key={suggestion}
                                            type="button"
                                            onClick={() => handleAddVariable(suggestion)}
                                            className={`w-full text-left px-3 py-1.5 text-xs transition-colors cursor-pointer flex items-center justify-between gap-2 ${
                                                idx === highlightedIdx
                                                    ? 'bg-accent-purple/15 text-accent-purple'
                                                    : 'text-fg hover:bg-bg-subtle/30'
                                            }`}
                                        >
                                            <span className="font-mono">{suggestion}</span>
                                            {isDetected && (
                                                <span className="text-[10px] text-accent-cyan/70 font-medium shrink-0">in template</span>
                                            )}
                                        </button>
                                    )
                                })}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Body (code editor area) */}
            <div>
                <label className="block text-xs font-medium text-fg-muted mb-1">Body</label>
                <textarea
                    value={bodyHtml}
                    onChange={(e) => setBodyHtml(e.target.value)}
                    readOnly={isDefault}
                    rows={12}
                    spellCheck={false}
                    className="w-full px-3 py-2 rounded border border-bg-subtle/50 bg-bg text-sm text-fg font-mono resize-y focus:border-accent focus:outline-none"
                />
            </div>
            {/* Delete error message (F1: 403 surfacing) */}
            {deleteError && (
                <div className="px-3 py-2 rounded bg-accent-red/10 border border-accent-red/30 text-sm text-accent-red">
                    ⚠️ {deleteError}
                </div>
            )}
        </div>

        {/* ── Delete Confirmation Modal (portaled to body) ── */}
        {showDeleteConfirm && createPortal(
            <div className="fixed inset-0 z-[9999] flex items-center justify-center" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}>
                {/* Backdrop */}
                <div
                    className="absolute inset-0"
                    style={{ backgroundColor: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }}
                    onClick={() => setShowDeleteConfirm(false)}
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
                            backgroundColor: 'rgba(239,68,68,0.15)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                        }}>
                            <span style={{ color: 'var(--color-accent-red, #ef4444)', fontSize: '18px' }}>⚠</span>
                        </div>
                        <div>
                            <h4 style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: 'var(--color-fg, #e0e0e0)' }}>Delete Template</h4>
                            <p style={{ fontSize: '12px', color: 'var(--color-fg-muted, #8b8fa3)', margin: '2px 0 0 0' }}>This action cannot be undone.</p>
                        </div>
                    </div>
                    <p style={{ fontSize: '14px', color: 'var(--color-fg-muted, #8b8fa3)', marginBottom: '20px' }}>
                        Are you sure you want to delete <strong style={{ color: 'var(--color-fg, #e0e0e0)' }}>{template.name}</strong>?
                    </p>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button
                            type="button"
                            onClick={() => setShowDeleteConfirm(false)}
                            style={{
                                padding: '6px 16px', fontSize: '13px', fontWeight: 500, borderRadius: '6px',
                                border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                                backgroundColor: 'transparent',
                                color: 'var(--color-fg-muted, #8b8fa3)',
                                cursor: 'pointer',
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-fg, #e0e0e0)' }}
                            onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-fg-muted, #8b8fa3)' }}
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            onClick={handleConfirmDelete}
                            style={{
                                padding: '6px 16px', fontSize: '13px', fontWeight: 500, borderRadius: '6px',
                                border: 'none',
                                backgroundColor: 'var(--color-accent-red, #ef4444)',
                                color: '#fff',
                                cursor: 'pointer',
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.85' }}
                            onMouseLeave={(e) => { e.currentTarget.style.opacity = '1' }}
                        >
                            Delete Template
                        </button>
                    </div>
                </div>
            </div>,
            document.body,
        )}
    </>
    )
}
