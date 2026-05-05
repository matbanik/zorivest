/**
 * ConfirmDeleteModal — Portal-based confirmation dialog for destructive operations.
 *
 * Features:
 * - Single-item mode: "Delete {type} '{name}'?" / "Archive {type} '{name}'?"
 * - Bulk mode: "Delete {count} {type}?" / "Archive {count} {type}?"
 * - Action modes: 'delete' (red, trash icon) | 'archive' (amber, archive icon)
 * - WCAG 2.1 AA: role="alertdialog", aria-modal, aria-labelledby
 * - Manual focus trap (Tab/Shift+Tab wraps within modal buttons)
 * - Escape key dismisses
 * - Auto-focus "Cancel" button on mount (safe default)
 * - Loading state for async operations
 *
 * Source: docs/build-plan/06-gui.md §Table UX Standardization
 * MEU: MEU-199 (gui-table-list-primitives)
 */

import { useEffect, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'

export interface DeleteTarget {
    /** Item type label (e.g., "account", "trade plans") */
    type: string
    /** For single-item delete: the item's display name */
    name?: string
    /** For bulk delete: how many items */
    count?: number
}

export interface ConfirmDeleteModalProps {
    open: boolean
    target: DeleteTarget
    onCancel: () => void
    onConfirm: () => void
    /** Show loading spinner and disable confirm button while processing */
    isDeleting?: boolean
    /** Action mode — controls icon, colors, heading, and button text.
     *  'delete' = red destructive (default), 'archive' = amber archival, 'unarchive' = teal restore */
    action?: 'delete' | 'archive' | 'unarchive'
}

const HEADING_ID = 'confirm-delete-heading'

export default function ConfirmDeleteModal({
    open,
    target,
    onCancel,
    onConfirm,
    isDeleting = false,
    action = 'delete',
}: ConfirmDeleteModalProps) {
    const firstButtonRef = useRef<HTMLButtonElement>(null)
    const lastButtonRef = useRef<HTMLButtonElement>(null)
    const dialogRef = useRef<HTMLDivElement>(null)

    // Auto-focus "Cancel" on open
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
                if (document.activeElement === firstEl) {
                    e.preventDefault()
                    lastEl.focus()
                }
            } else {
                if (document.activeElement === lastEl) {
                    e.preventDefault()
                    firstEl.focus()
                }
            }
        },
        [],
    )

    if (!open) return null

    // Action-specific theming
    const isArchive = action === 'archive'
    const isUnarchive = action === 'unarchive'
    const verb = isUnarchive ? 'unarchive' : isArchive ? 'archive' : 'delete'
    const verbCap = isUnarchive ? 'Unarchive' : isArchive ? 'Archive' : 'Delete'
    const verbGerund = isUnarchive ? 'Unarchiving' : isArchive ? 'Archiving' : 'Deleting'
    const subtitle = isUnarchive
        ? 'Items will be restored to your active accounts.'
        : isArchive
            ? 'Archived items can be restored later.'
            : 'This action cannot be undone.'
    const icon = isUnarchive ? '📤' : isArchive ? '📦' : '🗑'
    const accentColor = isUnarchive ? 'rgb(20,184,166)' : isArchive ? 'rgb(217,119,6)' : 'var(--color-accent-red, #ef4444)'
    const accentBg = isUnarchive ? 'rgba(20,184,166,0.15)' : isArchive ? 'rgba(217,119,6,0.15)' : 'rgba(239,68,68,0.15)'
    const accentBorder = isUnarchive ? 'rgba(20,184,166,0.5)' : isArchive ? 'rgba(217,119,6,0.5)' : 'rgba(239,68,68,0.5)'

    // Build the message based on single vs bulk mode
    const isBulk = target.count != null && target.count > 0
    const message = isBulk
        ? `Are you sure you want to ${verb} ${target.count} ${target.type}? ${subtitle}`
        : `Are you sure you want to ${verb} ${target.type} "${target.name}"? ${subtitle}`

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
                data-testid="confirm-delete-backdrop"
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
                data-testid="confirm-delete-modal"
                onKeyDown={handleKeyDown}
                style={{
                    position: 'relative',
                    backgroundColor: 'var(--color-bg-elevated, #1e2030)',
                    border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                    borderRadius: '12px',
                    padding: '24px',
                    maxWidth: '420px',
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
                            backgroundColor: accentBg,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                        }}
                    >
                        <span
                            style={{
                                color: accentColor,
                                fontSize: '18px',
                            }}
                        >
                            {icon}
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
                            {verbCap} {isBulk ? `${target.count} ${target.type}` : target.type}
                        </h4>
                        <p
                            style={{
                                fontSize: '12px',
                                color: 'var(--color-fg-muted, #8b8fa3)',
                                margin: '2px 0 0 0',
                            }}
                        >
                            {subtitle}
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
                    {message}
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
                        data-testid="confirm-delete-cancel-btn"
                        aria-label={`Cancel ${verb}`}
                        disabled={isDeleting}
                        style={{
                            padding: '8px 16px',
                            borderRadius: '6px',
                            fontSize: '13px',
                            fontWeight: 500,
                            border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                            backgroundColor: 'transparent',
                            color: 'var(--color-fg, #e0e0e0)',
                            cursor: isDeleting ? 'not-allowed' : 'pointer',
                            opacity: isDeleting ? 0.5 : 1,
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        ref={lastButtonRef}
                        onClick={onConfirm}
                        data-testid="confirm-delete-confirm-btn"
                        aria-label={`Confirm ${verb} of ${isBulk ? `${target.count} ${target.type}` : target.name || target.type}`}
                        disabled={isDeleting}
                        style={{
                            padding: '8px 16px',
                            borderRadius: '6px',
                            fontSize: '13px',
                            fontWeight: 500,
                            border: `1px solid ${accentBorder}`,
                            backgroundColor: accentBg,
                            color: accentColor,
                            cursor: isDeleting ? 'not-allowed' : 'pointer',
                            opacity: isDeleting ? 0.7 : 1,
                        }}
                    >
                        {isDeleting ? `${verbGerund}…` : verbCap}
                    </button>
                </div>
            </div>
        </div>
    )

    return createPortal(modal, document.body)
}
