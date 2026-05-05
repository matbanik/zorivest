/**
 * useConfirmDelete — State management hook for delete confirmation flow.
 *
 * Manages the modal open/close state, the pending delete target, and the
 * deferred callback pattern. Supports both single-item and bulk delete flows.
 *
 * Usage:
 *   const { showModal, target, confirmSingle, confirmBulk, handleCancel, handleConfirm }
 *     = useConfirmDelete()
 *
 * Source: docs/build-plan/06-gui.md §Table UX Standardization
 * MEU: MEU-199 (gui-table-list-primitives)
 */

import { useState, useCallback, useRef } from 'react'
import type { DeleteTarget } from '../components/ConfirmDeleteModal'

export interface UseConfirmDeleteReturn {
    /** Whether the confirmation modal is visible. */
    showModal: boolean
    /** The current delete target (type + name or count). */
    target: DeleteTarget | null
    /** Initiate single-item delete confirmation. */
    confirmSingle: (type: string, name: string, onConfirm: () => void) => void
    /** Initiate bulk delete confirmation. */
    confirmBulk: (type: string, count: number, onConfirm: () => void) => void
    /** Cancel — dismiss modal without deleting. */
    handleCancel: () => void
    /** Confirm — execute the pending delete callback and dismiss. */
    handleConfirm: () => void
}

export function useConfirmDelete(): UseConfirmDeleteReturn {
    const [showModal, setShowModal] = useState(false)
    const [target, setTarget] = useState<DeleteTarget | null>(null)
    const pendingCallbackRef = useRef<(() => void) | null>(null)

    const confirmSingle = useCallback(
        (type: string, name: string, onConfirm: () => void) => {
            setTarget({ type, name })
            pendingCallbackRef.current = onConfirm
            setShowModal(true)
        },
        [],
    )

    const confirmBulk = useCallback(
        (type: string, count: number, onConfirm: () => void) => {
            setTarget({ type, count })
            pendingCallbackRef.current = onConfirm
            setShowModal(true)
        },
        [],
    )

    const handleCancel = useCallback(() => {
        setShowModal(false)
        setTarget(null)
        pendingCallbackRef.current = null
    }, [])

    const handleConfirm = useCallback(() => {
        const callback = pendingCallbackRef.current
        setShowModal(false)
        setTarget(null)
        pendingCallbackRef.current = null
        if (callback) {
            callback()
        }
    }, [])

    return {
        showModal,
        target,
        confirmSingle,
        confirmBulk,
        handleCancel,
        handleConfirm,
    }
}
