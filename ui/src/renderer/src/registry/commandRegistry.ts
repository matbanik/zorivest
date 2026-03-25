import {
    LayoutDashboard,
    ArrowLeftRight,
    CalendarClock,
    Calendar,
    Settings,
    Calculator,
    Upload,
    ClipboardCheck,
    Globe,
    Mail,
    Monitor,
    Bell,
    FileText,
} from 'lucide-react'
import type { CommandRegistryEntry } from './types'

/**
 * createStaticEntries — builds the 13 static command entries per 06a-gui-shell.md §Static Registry.
 *
 * Navigation entries use the provided navigate function.
 * Action entries log a stub message (backing features are in later MEUs).
 * Settings entries navigate to /settings sub-routes.
 *
 * @param navigate - callback to navigate: (path: string) => void
 */
export function createStaticEntries(
    navigate: (path: string) => void,
): CommandRegistryEntry[] {
    return [
        // ── Navigation (5) — routes match 06-gui.md nav rail ──
        {
            id: 'nav:accounts',
            label: 'Accounts',
            category: 'navigation',
            keywords: ['home', 'overview', 'dashboard', 'broker', 'bank', 'balance'],
            icon: LayoutDashboard,
            action: () => navigate('/'),
            shortcut: 'Ctrl+1',
        },
        {
            id: 'nav:trades',
            label: 'Trades',
            category: 'navigation',
            keywords: ['executions', 'positions', 'journal', 'review'],
            icon: ArrowLeftRight,
            action: () => navigate('/trades'),
            shortcut: 'Ctrl+2',
        },
        {
            id: 'nav:planning',
            label: 'Planning',
            category: 'navigation',
            keywords: ['plans', 'thesis', 'strategy', 'watchlists', 'tickers'],
            icon: CalendarClock,
            action: () => navigate('/planning'),
            shortcut: 'Ctrl+3',
        },
        {
            id: 'nav:scheduling',
            label: 'Scheduling',
            category: 'navigation',
            keywords: ['schedules', 'cron', 'pipeline', 'report', 'jobs'],
            icon: Calendar,
            action: () => navigate('/scheduling'),
            shortcut: 'Ctrl+4',
        },
        {
            id: 'nav:settings',
            label: 'Settings',
            category: 'navigation',
            keywords: ['config', 'preferences', 'theme', 'display'],
            icon: Settings,
            action: () => navigate('/settings'),
            shortcut: 'Ctrl+,',
        },

        // ── Actions (3) — per spec; stubs until backing features exist ──
        {
            id: 'action:calc',
            label: 'Position Calculator',
            category: 'action',
            keywords: ['size', 'risk', 'shares'],
            icon: Calculator,
            action: () => { window.dispatchEvent(new CustomEvent('zorivest:open-calculator')) },
            shortcut: 'Ctrl+Shift+C',
        },
        {
            id: 'action:import',
            label: 'Import Trades',
            category: 'action',
            keywords: ['upload', 'csv', 'ibkr'],
            icon: Upload,
            action: () => { console.info('[command] Import Trades — not yet implemented') },
        },
        {
            id: 'action:review',
            label: 'Account Review',
            category: 'action',
            keywords: ['balance', 'wizard', 'update'],
            icon: ClipboardCheck,
            action: () => { console.info('[command] Account Review — not yet implemented') },
        },

        // ── Settings (5) — navigate to /settings sub-routes per spec ──
        {
            id: 'settings:market',
            label: 'Market Data Providers',
            category: 'settings',
            keywords: ['api', 'keys', 'polygon'],
            icon: Globe,
            action: () => navigate('/settings/market'),
        },
        {
            id: 'settings:email',
            label: 'Email Provider',
            category: 'settings',
            keywords: ['smtp', 'gmail', 'brevo'],
            icon: Mail,
            action: () => navigate('/settings/email'),
        },
        {
            id: 'settings:display',
            label: 'Display Preferences',
            category: 'settings',
            keywords: ['privacy', 'dollar', 'percent'],
            icon: Monitor,
            action: () => navigate('/settings/display'),
        },
        {
            id: 'settings:notifications',
            label: 'Notification Preferences',
            category: 'settings',
            keywords: ['toasts', 'alerts', 'suppress'],
            icon: Bell,
            action: () => navigate('/settings/notifications'),
        },
        {
            id: 'settings:logging',
            label: 'Logging Settings',
            category: 'settings',
            keywords: ['logs', 'debug', 'level', 'jsonl'],
            icon: FileText,
            action: () => navigate('/settings/logging'),
        },
    ]
}
