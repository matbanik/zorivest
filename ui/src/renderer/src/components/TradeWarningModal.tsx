/**
 * TradeWarningModal — Second-confirmation dialog for deleting accounts with trades.
 *
 * Shown after the initial "Are you sure?" confirmation when an account has
 * linked trades. Displays the account name and trade count in BIG prominent
 * font, warning that trades will be reassigned to the System Default account.
 *
 * Features:
 * - Large trade count display for visibility
 * - Clear warning about trade reassignment
 * - WCAG 2.1 AA: role="alertdialog", aria-modal, focus trap
 * - Orange/amber destructive theme
 */

import { useEffect, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'

export interface TradeWarningTarget {
    /** Account display name */
    accountName: string
    /** Number of trades linked to this account */
    tradeCount: number
    /** Number of trade plans linked (optional) */
    planCount?: number
}

export interface TradeWarningModalProps {
    open: boolean
    target: TradeWarningTarget
    onCancel: () => void
    onConfirm: () => void
    /** Show loading spinner while processing */
    isDeleting?: boolean
}

const HEADING_ID = 'trade-warning-heading'

export default function TradeWarningModal({
    open,
    target,
    onCancel,
    onConfirm,
    isDeleting = false,
}: TradeWarningModalProps) {
    const cancelRef = useRef<HTMLButtonElement>(null)
    const confirmRef = useRef<HTMLButtonElement>(null)
    const dialogRef = useRef<HTMLDivElement>(null)

    // Auto-focus Cancel on open
    useEffect(() => {
        if (open && cancelRef.current) {
            cancelRef.current.focus()
        }
    }, [open])

    // Escape key handler
    useEffect(() => {
        if (!open) return
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onCancel()
        }
        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [open, onCancel])

    // Focus trap
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key !== 'Tab') return
        const firstEl = cancelRef.current
        const lastEl = confirmRef.current
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
    }, [])

    if (!open) return null

    const totalLinked = target.tradeCount + (target.planCount || 0)

    const modal = (
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 10000, // Above the first confirmation modal
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }}
        >
            {/* Backdrop */}
            <div
                data-testid="trade-warning-backdrop"
                style={{
                    position: 'absolute',
                    inset: 0,
                    backgroundColor: 'rgba(0,0,0,0.75)',
                    backdropFilter: 'blur(6px)',
                }}
                onClick={onCancel}
            />
            {/* Dialog */}
            <div
                ref={dialogRef}
                role="alertdialog"
                aria-modal="true"
                aria-labelledby={HEADING_ID}
                data-testid="trade-warning-modal"
                onKeyDown={handleKeyDown}
                style={{
                    position: 'relative',
                    backgroundColor: 'var(--color-bg-elevated, #1e2030)',
                    border: '1px solid rgba(239,68,68,0.4)',
                    borderRadius: '12px',
                    padding: '28px',
                    maxWidth: '480px',
                    width: '90%',
                    boxShadow: '0 25px 50px -12px rgba(0,0,0,0.6), 0 0 40px rgba(239,68,68,0.15)',
                    color: 'var(--color-fg, #e0e0e0)',
                }}
            >
                {/* Warning Icon */}
                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'center',
                        marginBottom: '16px',
                    }}
                >
                    <div
                        style={{
                            width: '56px',
                            height: '56px',
                            borderRadius: '50%',
                            backgroundColor: 'rgba(239,68,68,0.15)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '28px',
                        }}
                    >
                        ⚠️
                    </div>
                </div>

                {/* Heading */}
                <h3
                    id={HEADING_ID}
                    style={{
                        margin: '0 0 8px 0',
                        fontSize: '18px',
                        fontWeight: 700,
                        textAlign: 'center',
                        color: 'var(--color-fg, #e0e0e0)',
                    }}
                >
                    Warning: Account Has Linked Trades
                </h3>

                {/* Account Name */}
                <p
                    style={{
                        margin: '0 0 20px 0',
                        fontSize: '14px',
                        textAlign: 'center',
                        color: 'var(--color-fg-muted, #999)',
                    }}
                >
                    <strong style={{ color: 'var(--color-fg, #e0e0e0)' }}>
                        {target.accountName}
                    </strong>
                </p>

                {/* BIG Trade Count */}
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '20px',
                        margin: '0 0 20px 0',
                        borderRadius: '10px',
                        backgroundColor: 'rgba(239,68,68,0.08)',
                        border: '1px solid rgba(239,68,68,0.25)',
                    }}
                >
                    <span
                        data-testid="trade-warning-count"
                        style={{
                            fontSize: '48px',
                            fontWeight: 800,
                            lineHeight: 1,
                            color: '#ef4444',
                            fontVariantNumeric: 'tabular-nums',
                        }}
                    >
                        {totalLinked}
                    </span>
                    <span
                        style={{
                            fontSize: '14px',
                            fontWeight: 600,
                            color: '#ef4444',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                        }}
                    >
                        {target.tradeCount > 0 && `${target.tradeCount} trade${target.tradeCount !== 1 ? 's' : ''}`}
                        {target.tradeCount > 0 && (target.planCount || 0) > 0 && ' + '}
                        {(target.planCount || 0) > 0 && `${target.planCount} plan${target.planCount !== 1 ? 's' : ''}`}
                        {' '}linked
                    </span>
                </div>

                {/* Explanation */}
                <p
                    style={{
                        margin: '0 0 24px 0',
                        fontSize: '13px',
                        lineHeight: 1.5,
                        textAlign: 'center',
                        color: 'var(--color-fg-muted, #999)',
                    }}
                >
                    Deleting this account will{' '}
                    <strong style={{ color: '#f59e0b' }}>
                        reassign all trades to the System Default account
                    </strong>
                    . This action cannot be undone.
                </p>

                {/* Buttons */}
                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                    <button
                        ref={cancelRef}
                        type="button"
                        data-testid="trade-warning-cancel"
                        onClick={onCancel}
                        disabled={isDeleting}
                        style={{
                            padding: '8px 20px',
                            borderRadius: '8px',
                            border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                            backgroundColor: 'transparent',
                            color: 'var(--color-fg, #e0e0e0)',
                            fontSize: '14px',
                            fontWeight: 500,
                            cursor: isDeleting ? 'not-allowed' : 'pointer',
                            opacity: isDeleting ? 0.5 : 1,
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        ref={confirmRef}
                        type="button"
                        data-testid="trade-warning-confirm"
                        onClick={onConfirm}
                        disabled={isDeleting}
                        style={{
                            padding: '8px 20px',
                            borderRadius: '8px',
                            border: '1px solid rgba(239,68,68,0.5)',
                            backgroundColor: 'rgba(239,68,68,0.15)',
                            color: '#ef4444',
                            fontSize: '14px',
                            fontWeight: 600,
                            cursor: isDeleting ? 'not-allowed' : 'pointer',
                            opacity: isDeleting ? 0.7 : 1,
                        }}
                    >
                        {isDeleting ? 'Deleting...' : 'Delete & Reassign Trades'}
                    </button>
                </div>
            </div>
        </div>
    )

    return createPortal(modal, document.body)
}
