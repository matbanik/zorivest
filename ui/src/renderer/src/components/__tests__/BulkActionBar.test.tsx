/**
 * BulkActionBar component tests — MEU-199 (gui-table-list-primitives).
 *
 * RED phase: component does not exist yet; all tests should FAIL.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'

import BulkActionBar from '../BulkActionBar'

describe('MEU-199: BulkActionBar', () => {
    it('renders nothing when selectedCount is 0', () => {
        const { container } = render(
            <BulkActionBar
                selectedCount={0}
                itemType="accounts"
                onDelete={vi.fn()}
            />,
        )

        expect(container.innerHTML).toBe('')
    })

    it('renders selection count when selectedCount > 0', () => {
        render(
            <BulkActionBar
                selectedCount={3}
                itemType="accounts"
                onDelete={vi.fn()}
            />,
        )

        expect(screen.getByText(/3 selected/)).toBeInTheDocument()
    })

    it('renders Delete Selected button', () => {
        render(
            <BulkActionBar
                selectedCount={2}
                itemType="trade plans"
                onDelete={vi.fn()}
            />,
        )

        expect(screen.getByText(/Delete Selected/i)).toBeInTheDocument()
    })

    it('calls onDelete when Delete Selected is clicked', () => {
        const onDelete = vi.fn()
        render(
            <BulkActionBar
                selectedCount={2}
                itemType="accounts"
                onDelete={onDelete}
            />,
        )

        fireEvent.click(screen.getByText(/Delete Selected/i))
        expect(onDelete).toHaveBeenCalledTimes(1)
    })

    it('has data-testid="bulk-action-bar"', () => {
        render(
            <BulkActionBar
                selectedCount={1}
                itemType="accounts"
                onDelete={vi.fn()}
            />,
        )

        expect(screen.getByTestId('bulk-action-bar')).toBeInTheDocument()
    })

    it('renders Clear Selection button and calls onClearSelection', () => {
        const onClear = vi.fn()
        render(
            <BulkActionBar
                selectedCount={3}
                itemType="accounts"
                onDelete={vi.fn()}
                onClearSelection={onClear}
            />,
        )

        const clearBtn = screen.getByText(/Clear/i)
        fireEvent.click(clearBtn)
        expect(onClear).toHaveBeenCalledTimes(1)
    })
})
