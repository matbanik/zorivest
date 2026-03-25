import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate, useLocation } from '@tanstack/react-router'
import SkipLink from '../SkipLink'
import NavRail from './NavRail'
import Header from './Header'
import StatusFooter from './StatusFooter'
import CommandPalette from '../CommandPalette'
import PositionCalculatorModal from '../../features/planning/PositionCalculatorModal'
import { StatusBarProvider } from '../../hooks/useStatusBar'
import { useRouteRestoration } from '../../hooks/useRouteRestoration'
import { useTheme } from '../../hooks/useTheme'

interface AppShellProps {
    children?: React.ReactNode
}

/**
 * AppShell — root layout with ARIA landmarks + Ctrl+K command palette.
 *
 * Structure: SkipLink + NavRail (nav) + Header (banner) + main content + StatusFooter + CommandPalette
 * Per 06-gui.md §App Shell Architecture.
 *
 * MEU-51: Persistence wiring — route restoration + theme persistence.
 * MEU-48: Global Position Calculator (Ctrl+Shift+C / command palette).
 */
export default function AppShell({ children }: AppShellProps) {
    const [paletteOpen, setPaletteOpen] = useState(false)
    const [calculatorOpen, setCalculatorOpen] = useState(false)
    const navigate = useNavigate()
    const location = useLocation()

    // MEU-51: Persist and restore active page
    useRouteRestoration(location.pathname, (path) => navigate({ to: path }))

    // MEU-51: Persist theme preference
    useTheme()

    // Global Ctrl+K shortcut
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault()
                setPaletteOpen((prev) => !prev)
            }
        }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [])

    // Global Ctrl+Shift+C shortcut — opens Position Calculator from any page (AC-13)
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                e.preventDefault()
                setCalculatorOpen((prev) => !prev)
            }
        }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [])

    // Listen for command palette / custom event trigger
    useEffect(() => {
        const handler = () => setCalculatorOpen(true)
        window.addEventListener('zorivest:open-calculator', handler)
        return () => window.removeEventListener('zorivest:open-calculator', handler)
    }, [])

    const handleOpenCalculator = useCallback(() => {
        setCalculatorOpen(true)
    }, [])

    return (
        <StatusBarProvider>
            <div className="flex h-screen bg-bg text-fg">
                <SkipLink />
                <NavRail />
                <div className="flex flex-col flex-1 min-w-0">
                    <Header onCommandPaletteToggle={() => setPaletteOpen(true)} />
                    <main id="main-content" className="flex-1 overflow-auto p-4">
                        {children}
                    </main>
                    <StatusFooter />
                </div>
                <CommandPalette
                    open={paletteOpen}
                    onClose={() => setPaletteOpen(false)}
                />
                <PositionCalculatorModal
                    isOpen={calculatorOpen}
                    onClose={() => setCalculatorOpen(false)}
                />
            </div>
        </StatusBarProvider>
    )
}
