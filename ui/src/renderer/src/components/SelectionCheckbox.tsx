/**
 * SelectionCheckbox — Row/header selection checkbox with indeterminate support.
 *
 * Used in TanStack Table row selection. Supports three states:
 * - unchecked (no rows selected)
 * - checked (all rows selected)
 * - indeterminate (some rows selected — header only)
 *
 * Source: docs/build-plan/06-gui.md §Table UX Standardization
 * MEU: MEU-199 (gui-table-list-primitives)
 */

import { useRef, useEffect } from 'react'
import type { CSSProperties } from 'react'

export interface SelectionCheckboxProps {
    /** Whether the checkbox is checked */
    checked: boolean
    /** Whether to show indeterminate state (some selected) */
    indeterminate?: boolean
    /** Change handler */
    onChange: (checked: boolean) => void
    /** Accessible label */
    ariaLabel?: string
    /** Optional inline style */
    style?: CSSProperties
    /** Optional custom data-testid (defaults to 'selection-checkbox') */
    'data-testid'?: string
}

export default function SelectionCheckbox({
    checked,
    indeterminate = false,
    onChange,
    ariaLabel = 'Select row',
    style,
    'data-testid': testId = 'selection-checkbox',
}: SelectionCheckboxProps) {
    const ref = useRef<HTMLInputElement>(null)

    useEffect(() => {
        if (ref.current) {
            ref.current.indeterminate = indeterminate
        }
    }, [indeterminate])

    return (
        <input
            ref={ref}
            type="checkbox"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            aria-label={ariaLabel}
            data-testid={testId}
            style={{
                width: '16px',
                height: '16px',
                cursor: 'pointer',
                accentColor: 'var(--color-accent, #6366f1)',
                ...style,
            }}
            onClick={(e) => e.stopPropagation()}
        />
    )
}
