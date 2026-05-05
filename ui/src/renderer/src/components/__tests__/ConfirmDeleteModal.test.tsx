/**
 * ConfirmDeleteModal component tests — MEU-199 (gui-table-list-primitives).
 *
 * RED phase: component does not exist yet; all tests should FAIL.
 * Modeled after UnsavedChangesModal.test.tsx pattern.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'

import ConfirmDeleteModal from '../ConfirmDeleteModal'

describe('MEU-199: ConfirmDeleteModal', () => {
    let onCancel: ReturnType<typeof vi.fn>
    let onConfirm: ReturnType<typeof vi.fn>

    beforeEach(() => {
        onCancel = vi.fn()
        onConfirm = vi.fn()
    })

    // ── Single-item mode ────────────────────────────────────────────────
    it('renders single-item delete message with item name', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Schwab IRA' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByText(/Schwab IRA/)).toBeInTheDocument()
        // 'account' appears in heading + message — use getAllByText
        expect(screen.getAllByText(/account/i).length).toBeGreaterThanOrEqual(1)
    })

    // ── Bulk mode ───────────────────────────────────────────────────────
    it('renders bulk delete message with item count', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'trade plans', count: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        // '5' and 'trade plans' appear in heading + message — use getAllByText
        expect(screen.getAllByText(/5/).length).toBeGreaterThanOrEqual(1)
        expect(screen.getAllByText(/trade plans/i).length).toBeGreaterThanOrEqual(1)
    })

    // ── 2-button layout ─────────────────────────────────────────────────
    it('renders Cancel and Delete buttons', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const buttons = screen.getAllByRole('button')
        expect(buttons).toHaveLength(2)
        expect(screen.getByText('Cancel')).toBeInTheDocument()
        expect(screen.getByText('Delete')).toBeInTheDocument()
    })

    // ── ARIA attributes ─────────────────────────────────────────────────
    it('has role="alertdialog", aria-modal="true", and aria-labelledby', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const dialog = screen.getByRole('alertdialog')
        expect(dialog).toHaveAttribute('aria-modal', 'true')
        expect(dialog).toHaveAttribute('aria-labelledby')

        const labelledById = dialog.getAttribute('aria-labelledby')!
        const heading = document.getElementById(labelledById)
        expect(heading).toBeInTheDocument()
        expect(heading!.textContent).toContain('Delete')
    })

    it('all buttons have aria-label attributes', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const buttons = screen.getAllByRole('button')
        for (const btn of buttons) {
            expect(btn).toHaveAttribute('aria-label')
            expect(btn.getAttribute('aria-label')!.length).toBeGreaterThan(0)
        }
    })

    // ── Escape key ──────────────────────────────────────────────────────
    it('pressing Escape calls onCancel', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        fireEvent.keyDown(document, { key: 'Escape' })
        expect(onCancel).toHaveBeenCalledTimes(1)
    })

    // ── Focus trap ──────────────────────────────────────────────────────
    it('Tab on last button wraps focus to first button', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const buttons = screen.getAllByRole('button')
        const lastButton = buttons[buttons.length - 1]
        const firstButton = buttons[0]

        lastButton.focus()
        expect(document.activeElement).toBe(lastButton)

        fireEvent.keyDown(lastButton, { key: 'Tab' })
        expect(document.activeElement).toBe(firstButton)
    })

    it('Shift+Tab on first button wraps focus to last button', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const buttons = screen.getAllByRole('button')
        const firstButton = buttons[0]
        const lastButton = buttons[buttons.length - 1]

        firstButton.focus()
        expect(document.activeElement).toBe(firstButton)

        fireEvent.keyDown(firstButton, { key: 'Tab', shiftKey: true })
        expect(document.activeElement).toBe(lastButton)
    })

    // ── Button handlers ─────────────────────────────────────────────────
    it('Cancel button calls onCancel', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        fireEvent.click(screen.getByText('Cancel'))
        expect(onCancel).toHaveBeenCalledTimes(1)
    })

    it('Delete button calls onConfirm', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        fireEvent.click(screen.getByText('Delete'))
        expect(onConfirm).toHaveBeenCalledTimes(1)
    })

    // ── open=false → no rendering ───────────────────────────────────────
    it('renders nothing when open=false', () => {
        render(
            <ConfirmDeleteModal
                open={false}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    })

    // ── Auto-focus Cancel on open ───────────────────────────────────────
    it('auto-focuses the Cancel button on mount', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const cancel = screen.getByText('Cancel')
        expect(document.activeElement).toBe(cancel)
    })

    // ── data-testid ─────────────────────────────────────────────────────
    it('has data-testid="confirm-delete-modal"', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument()
    })

    // ── isDeleting state ────────────────────────────────────────────────
    it('disables Delete button when isDeleting=true', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
                isDeleting={true}
            />,
        )

        const deleteBtn = screen.getByText('Deleting…')
        expect(deleteBtn).toBeDisabled()
    })

    // ── Backdrop click ──────────────────────────────────────────────────
    it('clicking backdrop calls onCancel', () => {
        render(
            <ConfirmDeleteModal
                open={true}
                target={{ type: 'account', name: 'Test' }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const backdrop = screen.getByTestId('confirm-delete-backdrop')
        fireEvent.click(backdrop)
        expect(onCancel).toHaveBeenCalledTimes(1)
    })
})
