import Store from 'electron-store'

/** Window bounds shape */
export interface WindowBounds {
    x?: number
    y?: number
    width: number
    height: number
}

/** Schema for electron-store typed config */
interface StoreSchema {
    windowBounds: WindowBounds
}

/** Default fallback bounds when no stored value exists */
export const DEFAULT_BOUNDS: WindowBounds = {
    width: 1280,
    height: 800,
}

/** Lazy-initialized store instance (avoids ESM issues in tests) */
let _store: Store<StoreSchema> | null = null

function getStore(): Store<StoreSchema> {
    if (!_store) {
        _store = new Store<StoreSchema>({
            name: 'zorivest-window-state',
            defaults: {
                windowBounds: DEFAULT_BOUNDS,
            },
        })
    }
    return _store
}

/** Retrieve stored window bounds, falling back to defaults */
export function getStoredBounds(): WindowBounds {
    return getStore().get('windowBounds') ?? DEFAULT_BOUNDS
}

/** Persist window bounds to disk */
export function saveWindowBounds(bounds: WindowBounds): void {
    getStore().set('windowBounds', bounds)
}
