/**
 * useFormGuard<T> — Generic unsaved-changes guard hook.
 *
 * Extracts the dirty-check + modal pattern from SchedulingLayout into a
 * reusable hook. T is the type of the navigation target (e.g., string ID,
 * Policy object, etc.).
 *
 * Usage:
 *   const { showModal, guardedSelect, handleCancel, handleDiscard, handleSaveAndContinue, isSaveDisabled }
 *     = useFormGuard<string>({ isDirty, onNavigate, onSave, isFormInvalid })
 *
 * Source: docs/build-plan/06-gui.md §UX Hardening
 * MEU: MEU-196 (gui-form-guard-infra), MEU-204 (calculator-validation-ux)
 */

import { useState, useCallback, useRef, useMemo } from 'react'

export interface UseFormGuardOptions<T> {
    /** Whether the form has unsaved changes. */
    isDirty: boolean
    /** Called with the pending target when navigation is confirmed. */
    onNavigate: (target: T) => void
    /** Optional async save handler. When provided, modal shows "Save & Continue". */
    onSave?: () => Promise<void>
    /** Optional predicate — returns true when the form has validation errors.
     *  When true, the "Save & Continue" button is disabled in the modal. */
    isFormInvalid?: () => boolean
}

export interface UseFormGuardReturn<T> {
    /** Whether the unsaved changes modal is visible. */
    showModal: boolean
    /** Call when user selects a new item. Guards if dirty, else navigates immediately. */
    guardedSelect: (target: T) => void
    /** "Keep Editing" — dismiss modal, stay on current item. */
    handleCancel: () => void
    /** "Discard Changes" — dismiss modal, navigate to pending target. */
    handleDiscard: () => void
    /** "Save & Continue" — save, then navigate. No-op if onSave not provided. */
    handleSaveAndContinue: () => Promise<void>
    /** Whether the Save & Continue button should be disabled (form has validation errors). */
    isSaveDisabled: boolean
}

export function useFormGuard<T>(options: UseFormGuardOptions<T>): UseFormGuardReturn<T> {
    const { isDirty, onNavigate, onSave, isFormInvalid } = options

    const [showModal, setShowModal] = useState(false)
    const pendingTargetRef = useRef<T | null>(null)

    const guardedSelect = useCallback(
        (target: T) => {
            if (!isDirty) {
                onNavigate(target)
                return
            }
            pendingTargetRef.current = target
            setShowModal(true)
        },
        [isDirty, onNavigate],
    )

    const handleCancel = useCallback(() => {
        setShowModal(false)
        pendingTargetRef.current = null
    }, [])

    const handleDiscard = useCallback(() => {
        const target = pendingTargetRef.current
        setShowModal(false)
        pendingTargetRef.current = null
        if (target !== null) {
            onNavigate(target)
        }
    }, [onNavigate])

    const handleSaveAndContinue = useCallback(async () => {
        if (!onSave) return

        try {
            await onSave()
            const target = pendingTargetRef.current
            setShowModal(false)
            pendingTargetRef.current = null
            if (target !== null) {
                onNavigate(target)
            }
        } catch {
            // Save failed (validation) — dismiss modal so user sees inline errors.
            // Form remains dirty, so guard will re-trigger on next navigation.
            setShowModal(false)
            pendingTargetRef.current = null
        }
    }, [onSave, onNavigate])

    const isSaveDisabled = useMemo(
        () => isFormInvalid ? isFormInvalid() : false,
        // eslint-disable-next-line react-hooks/exhaustive-deps -- isFormInvalid is a predicate; re-evaluate when modal visibility changes
        [isFormInvalid, showModal],
    )

    return {
        showModal,
        guardedSelect,
        handleCancel,
        handleDiscard,
        handleSaveAndContinue,
        isSaveDisabled,
    }
}
