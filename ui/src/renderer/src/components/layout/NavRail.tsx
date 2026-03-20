import {
    LayoutDashboard,
    ArrowLeftRight,
    CalendarClock,
    Calendar,
    Settings,
    PanelLeftClose,
    PanelLeftOpen,
    type LucideIcon,
} from 'lucide-react'
import { useNavigate, useLocation } from '@tanstack/react-router'
import { useLayoutStore } from '../../stores/layout'

interface NavItem {
    label: string
    path: string
    icon: LucideIcon
}

const navItems: NavItem[] = [
    { label: 'Accounts', path: '/', icon: LayoutDashboard },
    { label: 'Trades', path: '/trades', icon: ArrowLeftRight },
    { label: 'Planning', path: '/planning', icon: CalendarClock },
    { label: 'Scheduling', path: '/scheduling', icon: Calendar },
    { label: 'Settings', path: '/settings', icon: Settings },
]

const navTestIds: Record<string, string> = {
    '/': 'nav-accounts',
    '/trades': 'nav-trades',
    '/planning': 'nav-planning',
    '/scheduling': 'nav-scheduling',
    '/settings': 'nav-settings',
}

interface NavRailProps {
    currentPath?: string
    onNavigate?: (path: string) => void
}

/**
 * Navigation Rail — vertical left sidebar with 5 icon+label items.
 * Matches 06-gui.md §Navigation Rail canonical routes.
 *
 * Supports collapsed state (icons only, 56px) via useLayoutStore.
 * Uses TanStack Router by default. Props override for testing.
 */
export default function NavRail({ currentPath, onNavigate }: NavRailProps) {
    const navigate = useNavigate()
    const location = useLocation()
    const activePath = currentPath ?? location.pathname
    const isCollapsed = useLayoutStore((s) => s.isRailCollapsed)
    const toggleRail = useLayoutStore((s) => s.toggleRail)

    const handleNavigate = (path: string) => {
        if (onNavigate) {
            onNavigate(path)
        } else {
            navigate({ to: path })
        }
    }

    return (
        <nav
            aria-label="Main navigation"
            className={`nav-rail ${isCollapsed ? 'nav-rail--collapsed' : ''}`}
        >
            <div className="flex flex-col gap-1 p-2 flex-1">
                {navItems.map((item) => {
                    const isActive = activePath === item.path
                    const Icon = item.icon
                    return (
                        <a
                            key={item.path}
                            href={`#${item.path}`}
                            data-testid={navTestIds[item.path]}
                            aria-current={isActive ? 'page' : undefined}
                            title={isCollapsed ? item.label : undefined}
                            onClick={(e) => {
                                e.preventDefault()
                                handleNavigate(item.path)
                            }}
                            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors
                ${isActive ? 'bg-bg-elevated text-fg' : 'text-fg-muted hover:bg-bg-elevated hover:text-fg'}
                ${isCollapsed ? 'justify-center' : ''}`}
                        >
                            <Icon size={18} aria-hidden="true" />
                            {!isCollapsed && <span>{item.label}</span>}
                        </a>
                    )
                })}
            </div>

            {/* Collapse toggle at bottom */}
            <div className="p-2 border-t border-bg-elevated">
                <button
                    data-testid="nav-collapse-toggle"
                    onClick={toggleRail}
                    title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    className="flex items-center justify-center w-full px-3 py-2 rounded-md text-sm text-fg-muted hover:bg-bg-elevated hover:text-fg transition-colors cursor-pointer"
                >
                    {isCollapsed ? (
                        <PanelLeftOpen size={18} aria-hidden="true" />
                    ) : (
                        <>
                            <PanelLeftClose size={18} aria-hidden="true" />
                            <span className="ml-3">Collapse</span>
                        </>
                    )}
                </button>
            </div>
        </nav>
    )
}
