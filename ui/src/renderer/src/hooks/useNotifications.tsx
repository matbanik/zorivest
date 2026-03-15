import React, { createContext, useContext, useCallback, useRef } from 'react'
import { toast, Toaster } from 'sonner'

/**
 * Notification categories per 06a-gui-shell.md §Notification System.
 */
export type NotificationCategory = 'trade' | 'system' | 'data' | 'schedule' | 'error'

interface NotificationOptions {
    category: NotificationCategory
    message: string
    description?: string
    duration?: number
}

interface NotificationContextValue {
    notify: (options: NotificationOptions) => void
    dismiss: (id?: string | number) => void
}

const NotificationContext = createContext<NotificationContextValue | null>(null)

/**
 * Notification system with 5 categories.
 * Error notifications always show (cannot be suppressed).
 */
export function NotificationProvider({ children }: { children: React.ReactNode }) {
    const suppressedRef = useRef<Set<NotificationCategory>>(new Set())

    const notify = useCallback(({ category, message, description, duration }: NotificationOptions) => {
        // Error notifications cannot be suppressed
        if (category !== 'error' && suppressedRef.current.has(category)) {
            return
        }

        const toastFn = category === 'error' ? toast.error : toast.info
        toastFn(message, {
            description,
            duration: category === 'error' ? Infinity : (duration ?? 4000),
        })
    }, [])

    const dismiss = useCallback((id?: string | number) => {
        if (id) {
            toast.dismiss(id)
        } else {
            toast.dismiss()
        }
    }, [])

    return (
        <NotificationContext.Provider value={{ notify, dismiss }}>
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

export function useNotifications() {
    const context = useContext(NotificationContext)
    if (!context) {
        throw new Error('useNotifications must be used within NotificationProvider')
    }
    return context
}
