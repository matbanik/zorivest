/**
 * useConfirmDelete hook tests — MEU-199 (gui-table-list-primitives).
 *
 * RED phase: hook does not exist yet; all tests should FAIL.
 */

import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'

import { useConfirmDelete } from '../useConfirmDelete'

describe('MEU-199: useConfirmDelete', () => {
    it('initially has showModal=false and target=null', () => {
        const { result } = renderHook(() => useConfirmDelete())

        expect(result.current.showModal).toBe(false)
        expect(result.current.target).toBeNull()
    })

    it('confirmSingle opens modal with name target', () => {
        const { result } = renderHook(() => useConfirmDelete())
        const onConfirm = vi.fn()

        act(() => {
            result.current.confirmSingle('account', 'Schwab IRA', onConfirm)
        })

        expect(result.current.showModal).toBe(true)
        expect(result.current.target).toEqual({ type: 'account', name: 'Schwab IRA' })
    })

    it('confirmBulk opens modal with count target', () => {
        const { result } = renderHook(() => useConfirmDelete())
        const onConfirm = vi.fn()

        act(() => {
            result.current.confirmBulk('trade plans', 5, onConfirm)
        })

        expect(result.current.showModal).toBe(true)
        expect(result.current.target).toEqual({ type: 'trade plans', count: 5 })
    })

    it('handleCancel closes modal and clears target', () => {
        const { result } = renderHook(() => useConfirmDelete())
        const onConfirm = vi.fn()

        act(() => {
            result.current.confirmSingle('account', 'Test', onConfirm)
        })
        expect(result.current.showModal).toBe(true)

        act(() => {
            result.current.handleCancel()
        })

        expect(result.current.showModal).toBe(false)
        expect(result.current.target).toBeNull()
    })

    it('handleConfirm executes pending callback and closes modal', () => {
        const { result } = renderHook(() => useConfirmDelete())
        const onConfirm = vi.fn()

        act(() => {
            result.current.confirmSingle('account', 'Test', onConfirm)
        })

        act(() => {
            result.current.handleConfirm()
        })

        expect(onConfirm).toHaveBeenCalledTimes(1)
        expect(result.current.showModal).toBe(false)
        expect(result.current.target).toBeNull()
    })

    it('handleConfirm does nothing if no pending callback', () => {
        const { result } = renderHook(() => useConfirmDelete())

        // Should not throw
        act(() => {
            result.current.handleConfirm()
        })

        expect(result.current.showModal).toBe(false)
    })

    it('subsequent confirmSingle replaces previous pending target', () => {
        const { result } = renderHook(() => useConfirmDelete())
        const first = vi.fn()
        const second = vi.fn()

        act(() => {
            result.current.confirmSingle('account', 'First', first)
        })
        act(() => {
            result.current.confirmSingle('account', 'Second', second)
        })

        expect(result.current.target).toEqual({ type: 'account', name: 'Second' })

        act(() => {
            result.current.handleConfirm()
        })

        expect(first).not.toHaveBeenCalled()
        expect(second).toHaveBeenCalledTimes(1)
    })
})
