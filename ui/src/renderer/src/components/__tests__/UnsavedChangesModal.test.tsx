/**
 * UnsavedChangesModal component tests — MEU-196 (AC-6 through AC-9).
 *
 * RED phase: component does not exist yet; all tests should FAIL.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'

import UnsavedChangesModal from '../UnsavedChangesModal'

// ── Tests ──────────────────────────────────────────────────────────────────

describe('MEU-196: UnsavedChangesModal', () => {
    let onCancel: ReturnType<typeof vi.fn>
    let onDiscard: ReturnType<typeof vi.fn>

    beforeEach(() => {
        onCancel = vi.fn()
        onDiscard = vi.fn()
    })

    // ── AC-6: 2-button vs 3-button layout ───────────────────────────────
    it('AC-6: renders 2 buttons when onSave is undefined', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        const buttons = screen.getAllByRole('button')
        expect(buttons).toHaveLength(2)
        expect(screen.getByText('Keep Editing')).toBeInTheDocument()
        expect(screen.getByText('Discard Changes')).toBeInTheDocument()
    })

    it('AC-6: renders 3 buttons when onSave is provided', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
                onSave={vi.fn()}
            />,
        )

        const buttons = screen.getAllByRole('button')
        expect(buttons).toHaveLength(3)
        expect(screen.getByText('Keep Editing')).toBeInTheDocument()
        expect(screen.getByText('Discard Changes')).toBeInTheDocument()
        expect(screen.getByText('Save & Continue')).toBeInTheDocument()
    })

    // ── AC-7: ARIA attributes ───────────────────────────────────────────
    it('AC-7: has role="alertdialog", aria-modal="true", and aria-labelledby', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        const dialog = screen.getByRole('alertdialog')
        expect(dialog).toHaveAttribute('aria-modal', 'true')
        expect(dialog).toHaveAttribute('aria-labelledby')

        // The aria-labelledby should point to a real heading element
        const labelledById = dialog.getAttribute('aria-labelledby')!
        const heading = document.getElementById(labelledById)
        expect(heading).toBeInTheDocument()
        expect(heading!.textContent).toContain('Unsaved Changes')
    })

    it('AC-7b: all buttons have aria-label attributes (2-button mode)', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        const buttons = screen.getAllByRole('button')
        for (const btn of buttons) {
            expect(btn).toHaveAttribute('aria-label')
            expect(btn.getAttribute('aria-label')!.length).toBeGreaterThan(0)
        }
    })

    it('AC-7c: all buttons have aria-label attributes (3-button mode)', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
                onSave={vi.fn()}
            />,
        )

        const buttons = screen.getAllByRole('button')
        expect(buttons).toHaveLength(3)
        for (const btn of buttons) {
            expect(btn).toHaveAttribute('aria-label')
            expect(btn.getAttribute('aria-label')!.length).toBeGreaterThan(0)
        }
    })

    // ── AC-8: Escape key dismisses modal ────────────────────────────────
    it('AC-8: pressing Escape calls onCancel', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        fireEvent.keyDown(document, { key: 'Escape' })
        expect(onCancel).toHaveBeenCalledTimes(1)
    })

    // ── AC-9: Focus trap — Tab wraps within modal ───────────────────────
    it('AC-9: Tab on last button wraps focus to first button', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        const buttons = screen.getAllByRole('button')
        const lastButton = buttons[buttons.length - 1]
        const firstButton = buttons[0]

        // Focus the last button
        lastButton.focus()
        expect(document.activeElement).toBe(lastButton)

        // Tab from last button should wrap to first
        fireEvent.keyDown(lastButton, { key: 'Tab' })
        expect(document.activeElement).toBe(firstButton)
    })

    it('AC-9: Shift+Tab on first button wraps focus to last button', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        const buttons = screen.getAllByRole('button')
        const firstButton = buttons[0]
        const lastButton = buttons[buttons.length - 1]

        // Focus the first button
        firstButton.focus()
        expect(document.activeElement).toBe(firstButton)

        // Shift+Tab from first should wrap to last
        fireEvent.keyDown(firstButton, { key: 'Tab', shiftKey: true })
        expect(document.activeElement).toBe(lastButton)
    })

    // ── Button click handlers ───────────────────────────────────────────
    it('Keep Editing button calls onCancel', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        fireEvent.click(screen.getByText('Keep Editing'))
        expect(onCancel).toHaveBeenCalledTimes(1)
    })

    it('Discard Changes button calls onDiscard', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        fireEvent.click(screen.getByText('Discard Changes'))
        expect(onDiscard).toHaveBeenCalledTimes(1)
    })

    it('Save & Continue button calls onSave', () => {
        const onSave = vi.fn()
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
                onSave={onSave}
            />,
        )

        fireEvent.click(screen.getByText('Save & Continue'))
        expect(onSave).toHaveBeenCalledTimes(1)
    })

    // ── open=false → no rendering ───────────────────────────────────────
    it('renders nothing when open=false', () => {
        render(
            <UnsavedChangesModal
                open={false}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    })

    // ── Auto-focus first button on open ─────────────────────────────────
    it('auto-focuses the first button (Keep Editing) on mount', () => {
        render(
            <UnsavedChangesModal
                open={true}
                onCancel={onCancel}
                onDiscard={onDiscard}
            />,
        )

        const keepEditing = screen.getByText('Keep Editing')
        expect(document.activeElement).toBe(keepEditing)
    })
})
