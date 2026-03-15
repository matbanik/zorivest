import {
    LayoutDashboard,
    ArrowLeftRight,
    CalendarClock,
    Calendar,
    Settings,
    type LucideIcon,
} from 'lucide-react'

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

interface NavRailProps {
    currentPath?: string
    onNavigate?: (path: string) => void
}

/**
 * Navigation Rail — vertical left sidebar with 5 icon+label items.
 * Matches 06-gui.md §Navigation Rail canonical routes.
 */
export default function NavRail({ currentPath = '/', onNavigate }: NavRailProps) {
    return (
        <nav aria-label="Main navigation" className="nav-rail">
            <div className="flex flex-col gap-1 p-2">
                {navItems.map((item) => {
                    const isActive = currentPath === item.path
                    const Icon = item.icon
                    return (
                        <a
                            key={item.path}
                            href={`#${item.path}`}
                            aria-current={isActive ? 'page' : undefined}
                            onClick={(e) => {
                                e.preventDefault()
                                onNavigate?.(item.path)
                            }}
                            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors
                ${isActive ? 'bg-bg-elevated text-fg' : 'text-fg-muted hover:bg-bg-elevated hover:text-fg'}`}
                        >
                            <Icon size={18} aria-hidden="true" />
                            <span>{item.label}</span>
                        </a>
                    )
                })}
            </div>
        </nav>
    )
}
