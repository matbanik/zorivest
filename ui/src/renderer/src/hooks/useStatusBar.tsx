import React, { createContext, useContext, useState, useCallback, useRef } from 'react'

interface StatusBarContextValue {
    message: string
    setStatus: (msg: string, durationMs?: number) => void
}

const StatusBarContext = createContext<StatusBarContextValue>({
    message: 'Ready',
    setStatus: () => { },
})

/**
 * StatusBarProvider — provides a global status message that auto-resets.
 *
 * Components call `setStatus('Refreshing...', 3000)` to temporarily
 * update the footer. After `durationMs` it reverts to "Ready".
 */
export function StatusBarProvider({ children }: { children: React.ReactNode }) {
    const [message, setMessage] = useState('Ready')
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const setStatus = useCallback((msg: string, durationMs = 3000) => {
        if (timerRef.current) clearTimeout(timerRef.current)
        setMessage(msg)
        timerRef.current = setTimeout(() => {
            setMessage('Ready')
            timerRef.current = null
        }, durationMs)
    }, [])

    return (
        <StatusBarContext.Provider value={{ message, setStatus }}>
            {children}
        </StatusBarContext.Provider>
    )
}

export function useStatusBar() {
    return useContext(StatusBarContext)
}
