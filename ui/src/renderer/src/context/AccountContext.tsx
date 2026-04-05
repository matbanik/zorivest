import React, { createContext, useContext, useCallback, useRef } from 'react'
import { usePersistedState } from '@/hooks/usePersistedState'

// ── Types ───────────────────────────────────────────────────────────────────

interface AccountContextValue {
    /** Currently selected account ID, or null if none selected */
    activeAccountId: string | null
    /** Select an account (or null to clear). Updates MRU list. */
    selectAccount: (id: string | null) => void
    /** Most Recently Used account IDs (max 3, newest first) */
    mruAccountIds: string[]
}

// ── Context ─────────────────────────────────────────────────────────────────

const AccountContext = createContext<AccountContextValue | null>(null)

const MRU_MAX = 3

// ── Provider ────────────────────────────────────────────────────────────────

interface AccountProviderProps {
    children: React.ReactNode
}

/**
 * AccountProvider — global account selection context.
 *
 * Per 06-gui.md L350-378:
 * - `activeAccountId` is consumed by Trades, Planning, Tax modules
 * - MRU list persisted via usePersistedState('ui.accounts.active') + ('ui.accounts.mru')
 * - Max 3 MRU entries, newest first, deduplicated
 *
 * AC-14: AccountContext provider sets global activeAccountId.
 */
export function AccountProvider({ children }: AccountProviderProps) {
    // Store as string — empty string means "no selection".
    // The settings API uses value_type="str", so null would become
    // the string "None". Empty string is the correct sentinel.
    const [activeRaw, setActiveRaw] = usePersistedState<string>(
        'ui.accounts.active',
        '',
    )
    const [mruAccountIds, setMruAccountIds] = usePersistedState<string[]>(
        'ui.accounts.mru',
        [],
    )

    // Convert "" → null for consumers (public API stays string | null)
    const activeAccountId = activeRaw || null

    // Refs to capture latest persisted values for the callback
    const mruRef = useRef(mruAccountIds)
    mruRef.current = mruAccountIds

    const selectAccount = useCallback(
        (id: string | null) => {
            // Convert null → "" for storage
            setActiveRaw(id ?? '')

            if (id !== null) {
                const prev = mruRef.current
                // Remove if already present (dedup)
                const filtered = prev.filter((existingId) => existingId !== id)
                // Prepend to front
                const updated = [id, ...filtered]
                // Cap at MRU_MAX
                setMruAccountIds(updated.slice(0, MRU_MAX))
            }
        },
        [setActiveRaw, setMruAccountIds],
    )

    const value: AccountContextValue = {
        activeAccountId,
        selectAccount,
        mruAccountIds,
    }

    return (
        <AccountContext.Provider value={value}>
            {children}
        </AccountContext.Provider>
    )
}

// ── Hook ────────────────────────────────────────────────────────────────────

/**
 * useAccountContext — access global account selection.
 *
 * Throws if used outside AccountProvider.
 */
export function useAccountContext(): AccountContextValue {
    const context = useContext(AccountContext)
    if (context === null) {
        throw new Error('useAccountContext must be used within an AccountProvider')
    }
    return context
}
