import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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
 * Global UI state for layout — persisted via Zustand persist middleware.
 *
 * Storage: localStorage (default Zustand storage).
 * Design decision: canon specifies Zustand + electron-store (06a §92).
 * electron-store v9+ is ESM-only (see [UI-ESMSTORE]); pinned to v8 (CJS).
 * The preload IPC bridge exists but has untested integration — localStorage
 * works in both Electron renderer and browser dev as interim storage.
 * Will migrate to electron-store bridge when integration is validated.
 *
 * Persisted: sidebarWidth, isRailCollapsed
 * NOT persisted: commandPaletteOpen (ephemeral UI state)
 *
 * Source: MEU-51 (gui-state-persistence), 06a §92
 */
export const useLayoutStore = create<LayoutState>()(
    persist(
        (set) => ({
            sidebarWidth: 240,
            isRailCollapsed: false,
            commandPaletteOpen: false,
            setSidebarWidth: (width) => set({ sidebarWidth: width }),
            toggleRail: () => set((s) => ({ isRailCollapsed: !s.isRailCollapsed })),
            toggleCommandPalette: () =>
                set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
            setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
        }),
        {
            name: 'zorivest-layout',
            partialize: (state) => ({
                sidebarWidth: state.sidebarWidth,
                isRailCollapsed: state.isRailCollapsed,
                // commandPaletteOpen intentionally excluded — ephemeral
            }),
        },
    ),
)
