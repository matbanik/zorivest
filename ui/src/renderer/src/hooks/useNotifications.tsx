import React, { createContext, useContext, useCallback, useRef } from 'react'
import { toast, Toaster } from 'sonner'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'

/**
 * Notification categories per 06a-gui-shell.md §Notification System.
 *
 * Categories (spec-aligned):
 *   success       — suppressible, toast.success
 *   info          — suppressible, toast.message
 *   warning       — suppressible, toast.warning
 *   error         — NEVER suppressed, toast.error
 *   confirmation  — suppressible, if suppressed → defaultAction() executes
 */
export type NotificationCategory =
    | 'success'
    | 'info'
    | 'warning'
    | 'error'
    | 'confirmation'

interface NotificationOptions {
    category: NotificationCategory
    message: string
    description?: string
    duration?: number
    /** For confirmation category: action to execute if suppressed (default: cancel) */
    defaultAction?: () => void
}

interface NotificationContextValue {
    notify: (options: NotificationOptions) => void
    dismiss: (id?: string | number) => void
    /** True once notification preferences have loaded from the server */
    preferencesLoaded: boolean
}

const NotificationContext = createContext<NotificationContextValue | null>(null)

// ── Constants ────────────────────────────────────────────────────────────

const SUPPRESSIBLE_CATEGORIES: NotificationCategory[] = [
    'success',
    'info',
    'warning',
    'confirmation',
]

type Preferences = Record<string, boolean>

// ── Provider ─────────────────────────────────────────────────────────────

async function fetchAllPreferences(): Promise<Preferences> {
    const entries = await Promise.all(
        SUPPRESSIBLE_CATEGORIES.map(async (cat) => {
            const key = `notification.${cat}.enabled`
            try {
                const result = await apiFetch<{ value: boolean }>(
                    `/api/v1/settings/${key}`,
                )
                return [cat, result.value] as const
            } catch {
                return [cat, true] as const // default: enabled
            }
        }),
    )
    return Object.fromEntries(entries)
}

/**
 * Notification system with 5 spec-aligned categories.
 * Error notifications always show (cannot be suppressed).
 * Suppressed notifications are logged to console.
 * Confirmation suppression triggers defaultAction().
 */
export function NotificationProvider({ children }: { children: React.ReactNode }) {
    const { data: preferences, isFetched } = useQuery({
        queryKey: ['notification-preferences'],
        queryFn: fetchAllPreferences,
    })

    // Use ref so notify callback always reads latest preferences
    const prefsRef = useRef<Preferences>({})
    prefsRef.current = preferences ?? {}

    const notify = useCallback(
        ({ category, message, description, duration, defaultAction }: NotificationOptions) => {
            // Error notifications NEVER suppressed (AC-2)
            if (category === 'error') {
                toast.error(message, {
                    description,
                    duration: duration ?? Infinity,
                })
                return
            }

            // Check suppression preference (read latest via ref)
            const currentPrefs = prefsRef.current
            const isEnabled = currentPrefs[category] ?? true
            if (!isEnabled) {
                // Log suppressed notification (AC-4)
                console.log(`[suppressed:${category}]`, message)

                // Confirmation suppression → execute defaultAction (AC-3)
                if (category === 'confirmation' && defaultAction) {
                    defaultAction()
                }
                return
            }

            // Show the toast with the correct method per category
            const toastOpts = {
                description,
                duration: duration ?? 4000,
            }

            switch (category) {
                case 'success':
                    toast.success(message, toastOpts)
                    break
                case 'warning':
                    toast.warning(message, toastOpts)
                    break
                case 'info':
                case 'confirmation':
                    toast.message(message, toastOpts)
                    break
            }
        },
        [], // stable — reads prefs via ref
    )

    const dismiss = useCallback((id?: string | number) => {
        if (id) {
            toast.dismiss(id)
        } else {
            toast.dismiss()
        }
    }, [])

    return (
        <NotificationContext.Provider value={{ notify, dismiss, preferencesLoaded: isFetched }}>
            {children}
            <Toaster
                position="bottom-right"
                toastOptions={{
                    className: 'bg-bg-elevated text-fg border-bg-subtle',
                }}
            />
        </NotificationContext.Provider>
    )
}

// ── Hook ─────────────────────────────────────────────────────────────────

export function useNotifications() {
    const context = useContext(NotificationContext)
    if (!context) {
        throw new Error('useNotifications must be used within NotificationProvider')
    }
    return context
}
