/**
 * useFormGuard hook unit tests — MEU-196 (AC-1 through AC-5).
 *
 * RED phase: these tests define the expected behavior of useFormGuard<T>.
 * The hook does not exist yet; these should all FAIL.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

import { useFormGuard } from '../useFormGuard'

// ── Tests ──────────────────────────────────────────────────────────────────

describe('MEU-196: useFormGuard<T>', () => {
    let onNavigate: ReturnType<typeof vi.fn>

    beforeEach(() => {
        onNavigate = vi.fn()
    })

    // ── AC-1: Clean state → immediate navigation ────────────────────────
    it('AC-1: guardedSelect fires onNavigate immediately when isDirty=false', () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: false, onNavigate }),
        )

        act(() => {
            result.current.guardedSelect('item-2')
        })

        expect(onNavigate).toHaveBeenCalledWith('item-2')
        expect(result.current.showModal).toBe(false)
    })

    // ── AC-1 negative: dirty → onNavigate must NOT fire ─────────────────
    it('AC-1 neg: guardedSelect does NOT fire onNavigate when isDirty=true', () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate }),
        )

        act(() => {
            result.current.guardedSelect('item-2')
        })

        expect(onNavigate).not.toHaveBeenCalled()
    })

    // ── AC-2: Dirty state → show modal ──────────────────────────────────
    it('AC-2: guardedSelect sets showModal=true when isDirty=true', () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate }),
        )

        act(() => {
            result.current.guardedSelect('item-2')
        })

        expect(result.current.showModal).toBe(true)
    })

    // ── AC-3: Cancel → dismiss modal, no navigation ─────────────────────
    it('AC-3: handleCancel sets showModal=false without calling onNavigate', () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate }),
        )

        // Trigger modal
        act(() => {
            result.current.guardedSelect('item-2')
        })
        expect(result.current.showModal).toBe(true)

        // Cancel
        act(() => {
            result.current.handleCancel()
        })

        expect(result.current.showModal).toBe(false)
        expect(onNavigate).not.toHaveBeenCalled()
    })

    // ── AC-4: Discard → dismiss modal + navigate ────────────────────────
    it('AC-4: handleDiscard sets showModal=false and calls onNavigate(pendingTarget)', () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate }),
        )

        act(() => {
            result.current.guardedSelect('item-2')
        })

        act(() => {
            result.current.handleDiscard()
        })

        expect(result.current.showModal).toBe(false)
        expect(onNavigate).toHaveBeenCalledWith('item-2')
    })

    // ── AC-5: Save & Continue → onSave() then onNavigate() ──────────────
    it('AC-5: handleSaveAndContinue calls onSave, then onNavigate on success', async () => {
        const onSave = vi.fn().mockResolvedValue(undefined)

        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate, onSave }),
        )

        act(() => {
            result.current.guardedSelect('item-2')
        })

        await act(async () => {
            await result.current.handleSaveAndContinue()
        })

        expect(onSave).toHaveBeenCalled()
        expect(onNavigate).toHaveBeenCalledWith('item-2')
        expect(result.current.showModal).toBe(false)
    })

    // ── AC-5 negative: onSave rejects → no navigation ──────────────────
    it('AC-5 neg: handleSaveAndContinue does NOT navigate when onSave rejects', async () => {
        const onSave = vi.fn().mockRejectedValue(new Error('save failed'))

        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate, onSave }),
        )

        act(() => {
            result.current.guardedSelect('item-2')
        })

        await act(async () => {
            await result.current.handleSaveAndContinue()
        })

        expect(onSave).toHaveBeenCalled()
        expect(onNavigate).not.toHaveBeenCalled()
        // Modal stays open so user can retry or cancel
        expect(result.current.showModal).toBe(true)
    })

    // ── Edge: handleDiscard without prior guardedSelect → no-op ─────────
    it('handleDiscard without prior guardedSelect does not call onNavigate', () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate }),
        )

        act(() => {
            result.current.handleDiscard()
        })

        expect(onNavigate).not.toHaveBeenCalled()
        expect(result.current.showModal).toBe(false)
    })

    // ── Edge: handleSaveAndContinue without onSave → no-op ──────────────
    it('handleSaveAndContinue without onSave does not call onNavigate', async () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate }),
        )

        act(() => {
            result.current.guardedSelect('item-2')
        })

        await act(async () => {
            await result.current.handleSaveAndContinue()
        })

        // No onSave provided → should not navigate
        expect(onNavigate).not.toHaveBeenCalled()
        expect(result.current.showModal).toBe(true)
    })

    // ── Edge: Multiple guardedSelect calls update pendingTarget ──────────
    it('multiple guardedSelect calls update pendingTarget to latest', () => {
        const { result } = renderHook(() =>
            useFormGuard<string>({ isDirty: true, onNavigate }),
        )

        act(() => {
            result.current.guardedSelect('item-A')
        })
        act(() => {
            result.current.guardedSelect('item-B')
        })

        act(() => {
            result.current.handleDiscard()
        })

        expect(onNavigate).toHaveBeenCalledWith('item-B')
    })
})
