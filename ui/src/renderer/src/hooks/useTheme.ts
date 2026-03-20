import { useEffect } from 'react'
import { usePersistedState } from './usePersistedState'

type Theme = 'dark' | 'light'

/**
 * useTheme — persists theme preference via usePersistedState (server-side).
 *
 * Applies the theme by toggling the `dark` class on `<html>`.
 * Default: 'dark' (matches CSS design system).
 *
 * Source: MEU-51 (gui-state-persistence), T6.5
 */
export function useTheme(): [Theme, (t: Theme) => void] {
    const [theme, setTheme] = usePersistedState<Theme>('ui.theme', 'dark')

    useEffect(() => {
        const root = document.documentElement
        if (theme === 'dark') {
            root.classList.add('dark')
        } else {
            root.classList.remove('dark')
        }
    }, [theme])

    return [theme, setTheme]
}
