import { useEffect, useRef } from 'react'
import { usePersistedState } from './usePersistedState'

/**
 * useRouteRestoration — persists active page and restores on mount.
 *
 * Reads `ui.activePage` from server-side settings via usePersistedState.
 * Waits until isLoading is false (server value arrived or fetch failed),
 * then navigates once if needed. Saves current route on subsequent changes.
 *
 * Source: MEU-51 (gui-state-persistence), 06a §90
 */
export function useRouteRestoration(
    currentPath: string,
    navigate: (path: string) => void,
): void {
    const [savedPage, setSavedPage, isFetching] = usePersistedState('ui.activePage', '/')
    const hasRestored = useRef(false)

    // Restore once server fetch completes (isFetching flips to false)
    useEffect(() => {
        if (!hasRestored.current && !isFetching) {
            hasRestored.current = true
            if (savedPage && savedPage !== '/' && savedPage !== currentPath) {
                navigate(savedPage)
            }
        }
    }, [savedPage, isFetching]) // eslint-disable-line react-hooks/exhaustive-deps -- re-run when server value arrives

    // Save on route change — skip until restore is complete
    useEffect(() => {
        if (hasRestored.current && currentPath !== savedPage) {
            setSavedPage(currentPath)
        }
    }, [currentPath]) // eslint-disable-line react-hooks/exhaustive-deps -- minimal deps
}
