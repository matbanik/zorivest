import { create } from 'zustand'

interface LayoutState {
    sidebarWidth: number
    isRailCollapsed: boolean
    commandPaletteOpen: boolean
    setSidebarWidth: (width: number) => void
    toggleRail: () => void
    toggleCommandPalette: () => void
    setCommandPaletteOpen: (open: boolean) => void
}

/**
 * Global UI state for layout — persisted via electron-store.
 * Uses Zustand v5 with selector-based updates to prevent re-render cascades.
 */
export const useLayoutStore = create<LayoutState>()((set) => ({
    sidebarWidth: 240,
    isRailCollapsed: false,
    commandPaletteOpen: false,
    setSidebarWidth: (width) => set({ sidebarWidth: width }),
    toggleRail: () => set((s) => ({ isRailCollapsed: !s.isRailCollapsed })),
    toggleCommandPalette: () =>
        set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
    setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
}))
