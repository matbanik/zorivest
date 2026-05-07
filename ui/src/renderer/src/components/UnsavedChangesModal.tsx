/**
 * UnsavedChangesModal — Portal-based confirmation dialog for unsaved changes.
 *
 * Features:
 * - 2-button mode (Keep Editing, Discard) when onSave is undefined
 * - 3-button mode (Keep Editing, Discard, Save & Continue) when onSave is provided
 * - WCAG 2.1 AA: role="alertdialog", aria-modal, aria-labelledby
 * - Manual focus trap (Tab/Shift+Tab wraps within modal buttons)
 * - Escape key dismisses
 * - Auto-focus "Keep Editing" button on mount
 *
 * Source: docs/build-plan/06-gui.md §UX Hardening
 * MEU: MEU-196 (gui-form-guard-infra)
 */

import { useEffect, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'

export interface UnsavedChangesModalProps {
    open: boolean
    onCancel: () => void
    onDiscard: () => void
    onSave?: () => void
    /** When true, the "Save & Continue" button is visually disabled (form has validation errors). */
    isSaveDisabled?: boolean
}

const HEADING_ID = 'unsaved-changes-heading'

export default function UnsavedChangesModal({
    open,
    onCancel,
    onDiscard,
    onSave,
    isSaveDisabled = false,
}: UnsavedChangesModalProps) {
    const firstButtonRef = useRef<HTMLButtonElement>(null)
    const lastButtonRef = useRef<HTMLButtonElement>(null)
    const dialogRef = useRef<HTMLDivElement>(null)

    // Auto-focus "Keep Editing" on open
    useEffect(() => {
        if (open && firstButtonRef.current) {
            firstButtonRef.current.focus()
        }
    }, [open])

    // Escape key handler
    useEffect(() => {
        if (!open) return

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onCancel()
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [open, onCancel])

    // Focus trap: Tab wraps within modal
    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            if (e.key !== 'Tab') return

            const firstEl = firstButtonRef.current
            const lastEl = lastButtonRef.current
            if (!firstEl || !lastEl) return

            if (e.shiftKey) {
                // Shift+Tab on first element → wrap to last
                if (document.activeElement === firstEl) {
                    e.preventDefault()
                    lastEl.focus()
                }
            } else {
                // Tab on last element → wrap to first
                if (document.activeElement === lastEl) {
                    e.preventDefault()
                    firstEl.focus()
                }
            }
        },
        [],
    )

    if (!open) return null

    const modal = (
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 9999,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }}
        >
            {/* Backdrop */}
            <div
                style={{
                    position: 'absolute',
                    inset: 0,
                    backgroundColor: 'rgba(0,0,0,0.65)',
                    backdropFilter: 'blur(4px)',
                }}
                onClick={onCancel}
            />
            {/* Dialog */}
            <div
                ref={dialogRef}
                role="alertdialog"
                aria-modal="true"
                aria-labelledby={HEADING_ID}
                data-testid="unsaved-changes-modal"
                onKeyDown={handleKeyDown}
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
                {/* Header */}
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        marginBottom: '16px',
                    }}
                >
                    <div
                        style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '50%',
                            backgroundColor: 'rgba(255,184,108,0.15)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                        }}
                    >
                        <span
                            style={{
                                color: 'var(--color-accent-amber, #ffb86c)',
                                fontSize: '18px',
                            }}
                        >
                            ⚠
                        </span>
                    </div>
                    <div>
                        <h4
                            id={HEADING_ID}
                            style={{
                                fontSize: '14px',
                                fontWeight: 600,
                                margin: 0,
                                color: 'var(--color-fg, #e0e0e0)',
                            }}
                        >
                            Unsaved Changes
                        </h4>
                        <p
                            style={{
                                fontSize: '12px',
                                color: 'var(--color-fg-muted, #8b8fa3)',
                                margin: '2px 0 0 0',
                            }}
                        >
                            Your edits have not been saved.
                        </p>
                    </div>
                </div>

                <p
                    style={{
                        fontSize: '14px',
                        color: 'var(--color-fg-muted, #8b8fa3)',
                        marginBottom: '20px',
                    }}
                >
                    You have unsaved changes that will be lost if you navigate
                    away.
                </p>

                {/* Buttons */}
                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'flex-end',
                        gap: '8px',
                    }}
                >
                    <button
                        ref={firstButtonRef}
                        onClick={onCancel}
                        data-testid="unsaved-keep-editing-btn"
                        aria-label="Keep editing current form"
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
                        Keep Editing
                    </button>
                    <button
                        ref={onSave ? undefined : lastButtonRef}
                        onClick={onDiscard}
                        data-testid="unsaved-discard-btn"
                        aria-label="Discard unsaved changes"
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
                    {onSave && (
                        <button
                            ref={lastButtonRef}
                            onClick={isSaveDisabled ? undefined : onSave}
                            disabled={isSaveDisabled}
                            aria-disabled={isSaveDisabled ? 'true' : undefined}
                            data-testid="unsaved-save-continue-btn"
                            aria-label="Save changes and continue"
                            style={{
                                padding: '8px 16px',
                                borderRadius: '6px',
                                fontSize: '13px',
                                fontWeight: 500,
                                border: '1px solid rgba(80,250,123,0.5)',
                                backgroundColor: 'rgba(80,250,123,0.1)',
                                color: 'var(--color-accent-green, #50fa7b)',
                                cursor: isSaveDisabled ? 'not-allowed' : 'pointer',
                                opacity: isSaveDisabled ? 0.5 : 1,
                            }}
                        >
                            Save &amp; Continue
                        </button>
                    )}
                </div>
            </div>
        </div>
    )

    return createPortal(modal, document.body)
}
