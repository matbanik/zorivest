import type { LucideIcon } from 'lucide-react'

/**
 * CommandRegistryEntry — the shape of every command in the palette.
 * Per 06a-gui-shell.md §CommandRegistryEntry Type.
 */
export interface CommandRegistryEntry {
    /** Unique identifier (e.g. 'nav:accounts', 'action:refresh') */
    id: string
    /** Display label */
    label: string
    /** Category for grouping per 06a-gui-shell.md §CommandRegistryEntry Type */
    category: 'navigation' | 'action' | 'settings' | 'search'
    /** Search keywords (matched by Fuse.js alongside label) */
    keywords: string[]
    /** Optional Lucide icon component */
    icon?: LucideIcon
    /** The function executed when this entry is selected */
    action: () => void
    /** Optional keyboard shortcut display hint (e.g. 'Ctrl+1') */
    shortcut?: string
}
