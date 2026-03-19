import React, { useEffect, useState } from 'react'
import SkipLink from '../SkipLink'
import NavRail from './NavRail'
import Header from './Header'
import StatusFooter from './StatusFooter'
import CommandPalette from '../CommandPalette'
import { StatusBarProvider } from '../../hooks/useStatusBar'

interface AppShellProps {
    children?: React.ReactNode
}

/**
 * AppShell — root layout with ARIA landmarks + Ctrl+K command palette.
 *
 * Structure: SkipLink + NavRail (nav) + Header (banner) + main content + StatusFooter + CommandPalette
 * Per 06-gui.md §App Shell Architecture.
 */
export default function AppShell({ children }: AppShellProps) {
    const [paletteOpen, setPaletteOpen] = useState(false)

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
            </div>
        </StatusBarProvider>
    )
}
