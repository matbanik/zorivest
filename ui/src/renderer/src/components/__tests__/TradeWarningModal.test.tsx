/**
 * TradeWarningModal component tests — second-confirmation for account deletion.
 *
 * RED phase: tests written FIRST per TDD protocol.
 * Covers: rendering, trade count display, button handlers, accessibility,
 *         focus trap, escape key, backdrop click, loading state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import React from 'react'

import TradeWarningModal from '../TradeWarningModal'

describe('TradeWarningModal', () => {
    let onCancel: ReturnType<typeof vi.fn>
    let onConfirm: ReturnType<typeof vi.fn>

    beforeEach(() => {
        onCancel = vi.fn()
        onConfirm = vi.fn()
    })

    // ── Rendering ───────────────────────────────────────────────────────
    it('renders account name in the modal', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Schwab IRA', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByText('Schwab IRA')).toBeInTheDocument()
    })

    it('renders trade count prominently', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 12, planCount: 3 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        // Total linked = 12 + 3 = 15
        const countEl = screen.getByTestId('trade-warning-count')
        expect(countEl).toBeInTheDocument()
        expect(countEl.textContent).toBe('15')
    })

    it('renders trade-only count when no plans', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 7 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const countEl = screen.getByTestId('trade-warning-count')
        expect(countEl.textContent).toBe('7')
    })

    it('displays warning about trade reassignment', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 3 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByText(/reassign all trades/i)).toBeInTheDocument()
        expect(screen.getByText(/System Default/i)).toBeInTheDocument()
    })

    it('displays the warning heading', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 3 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByText(/Warning.*Linked Trades/i)).toBeInTheDocument()
    })

    // ── Buttons ─────────────────────────────────────────────────────────
    it('renders Cancel and Delete & Reassign buttons', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByText('Cancel')).toBeInTheDocument()
        expect(screen.getByText('Delete & Reassign Trades')).toBeInTheDocument()
    })

    it('Cancel button calls onCancel', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        fireEvent.click(screen.getByTestId('trade-warning-cancel'))
        expect(onCancel).toHaveBeenCalledTimes(1)
    })

    it('Confirm button calls onConfirm', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        fireEvent.click(screen.getByTestId('trade-warning-confirm'))
        expect(onConfirm).toHaveBeenCalledTimes(1)
    })

    // ── ARIA attributes ─────────────────────────────────────────────────
    it('has role="alertdialog" with aria-modal and aria-labelledby', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
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
    })

    // ── open=false → no rendering ───────────────────────────────────────
    it('renders nothing when open=false', () => {
        render(
            <TradeWarningModal
                open={false}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    })

    // ── Escape key ──────────────────────────────────────────────────────
    it('pressing Escape calls onCancel', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        fireEvent.keyDown(document, { key: 'Escape' })
        expect(onCancel).toHaveBeenCalledTimes(1)
    })

    // ── Focus trap ──────────────────────────────────────────────────────
    it('Tab on confirm wraps focus to cancel', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const cancelBtn = screen.getByTestId('trade-warning-cancel')
        const confirmBtn = screen.getByTestId('trade-warning-confirm')

        confirmBtn.focus()
        expect(document.activeElement).toBe(confirmBtn)

        fireEvent.keyDown(confirmBtn, { key: 'Tab' })
        expect(document.activeElement).toBe(cancelBtn)
    })

    it('Shift+Tab on cancel wraps focus to confirm', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const cancelBtn = screen.getByTestId('trade-warning-cancel')
        const confirmBtn = screen.getByTestId('trade-warning-confirm')

        cancelBtn.focus()
        expect(document.activeElement).toBe(cancelBtn)

        fireEvent.keyDown(cancelBtn, { key: 'Tab', shiftKey: true })
        expect(document.activeElement).toBe(confirmBtn)
    })

    // ── Auto-focus Cancel ───────────────────────────────────────────────
    it('auto-focuses the Cancel button on mount', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const cancelBtn = screen.getByTestId('trade-warning-cancel')
        expect(document.activeElement).toBe(cancelBtn)
    })

    // ── Backdrop click ──────────────────────────────────────────────────
    it('clicking backdrop calls onCancel', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        const backdrop = screen.getByTestId('trade-warning-backdrop')
        fireEvent.click(backdrop)
        expect(onCancel).toHaveBeenCalledTimes(1)
    })

    // ── Loading state ───────────────────────────────────────────────────
    it('disables both buttons and shows "Deleting..." when isDeleting=true', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
                isDeleting={true}
            />,
        )

        const confirmBtn = screen.getByTestId('trade-warning-confirm')
        const cancelBtn = screen.getByTestId('trade-warning-cancel')
        expect(confirmBtn).toBeDisabled()
        expect(cancelBtn).toBeDisabled()
        expect(confirmBtn.textContent).toContain('Deleting...')
    })

    // ── data-testid ─────────────────────────────────────────────────────
    it('has data-testid="trade-warning-modal"', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByTestId('trade-warning-modal')).toBeInTheDocument()
    })

    // ── Trade + plan breakdown display ──────────────────────────────────
    it('shows separate trade and plan counts in description', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 5, planCount: 2 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        // Should show "5 trades + 2 plans linked"
        expect(screen.getByText(/5 trades/i)).toBeInTheDocument()
        expect(screen.getByText(/2 plans/i)).toBeInTheDocument()
    })

    it('shows singular "trade" for count of 1', () => {
        render(
            <TradeWarningModal
                open={true}
                target={{ accountName: 'Test', tradeCount: 1 }}
                onCancel={onCancel}
                onConfirm={onConfirm}
            />,
        )

        expect(screen.getByText(/1 trade /i)).toBeInTheDocument()
    })
})
