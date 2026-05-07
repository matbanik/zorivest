/**
 * BulkActionBar — Contextual toolbar for multi-select bulk actions.
 *
 * Appears when 1+ rows are selected, showing the count and action buttons.
 * Renders nothing when selectedCount is 0.
 *
 * Source: docs/build-plan/06-gui.md §Table UX Standardization
 * MEU: MEU-199 (gui-table-list-primitives)
 */

import type { ReactNode } from 'react'

export interface BulkActionBarProps {
    /** Number of currently selected items */
    selectedCount: number
    /** Plural label for the item type (e.g., "accounts", "trade plans") */
    itemType: string
    /** Called when "Delete Selected" is clicked */
    onDelete: () => void
    /** Called when "Clear" is clicked to deselect all */
    onClearSelection?: () => void
    /** Optional additional action buttons */
    actions?: { label: string; onClick: () => void; icon?: ReactNode }[]
}

export default function BulkActionBar({
    selectedCount,
    _itemType,
    onDelete,
    onClearSelection,
    actions,
}: BulkActionBarProps) {
    if (selectedCount === 0) return null

    return (
        <div
            data-testid="bulk-action-bar"
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '8px 16px',
                backgroundColor: 'var(--color-bg-elevated, #1e2030)',
                borderRadius: '8px',
                border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                marginBottom: '8px',
                fontSize: '13px',
            }}
        >
            {/* Selection count */}
            <span
                style={{
                    color: 'var(--color-accent, #6366f1)',
                    fontWeight: 600,
                }}
            >
                {selectedCount} selected
            </span>

            {/* Divider */}
            <div
                style={{
                    width: '1px',
                    height: '20px',
                    backgroundColor: 'var(--color-bg-subtle, #2a2e3f)',
                }}
            />

            {/* Delete Selected button */}
            <button
                onClick={onDelete}
                data-testid="bulk-delete-btn"
                style={{
                    padding: '4px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: 500,
                    border: '1px solid rgba(239,68,68,0.4)',
                    backgroundColor: 'rgba(239,68,68,0.1)',
                    color: 'var(--color-accent-red, #ef4444)',
                    cursor: 'pointer',
                    transition: 'background-color 0.15s',
                }}
            >
                Delete Selected
            </button>

            {/* Additional actions */}
            {actions?.map((action, i) => (
                <button
                    key={i}
                    onClick={action.onClick}
                    style={{
                        padding: '4px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 500,
                        border: '1px solid var(--color-bg-subtle, #2a2e3f)',
                        backgroundColor: 'transparent',
                        color: 'var(--color-fg, #e0e0e0)',
                        cursor: 'pointer',
                    }}
                >
                    {action.icon}
                    {action.label}
                </button>
            ))}

            {/* Spacer */}
            <div style={{ flex: 1 }} />

            {/* Clear Selection */}
            {onClearSelection && (
                <button
                    onClick={onClearSelection}
                    data-testid="bulk-clear-btn"
                    style={{
                        padding: '4px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 500,
                        border: 'none',
                        backgroundColor: 'transparent',
                        color: 'var(--color-fg-muted, #8b8fa3)',
                        cursor: 'pointer',
                    }}
                >
                    Clear
                </button>
            )}
        </div>
    )
}
