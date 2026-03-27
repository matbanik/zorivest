import { useState, useEffect, useMemo } from 'react'
import { apiFetch } from '@/lib/api'

// ── Account types matching backend AccountResponse ────────────────────────

export interface Account {
    account_id: string
    name: string
    account_type: string
    latest_balance: number | null
    latest_balance_date: string | null
}

export interface UseAccountsResult {
    accounts: Account[]
    portfolioTotal: number
    isLoading: boolean
    error: string | null
}

/**
 * useAccounts — fetches account list from GET /api/v1/accounts
 * and computes portfolio total from latest_balance fields.
 *
 * AC-6: Fetches from GET /api/v1/accounts and computes portfolio total.
 */
export function useAccounts(): UseAccountsResult {
    const [accounts, setAccounts] = useState<Account[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let cancelled = false
        setIsLoading(true)
        setError(null)

        apiFetch<Account[]>('/api/v1/accounts')
            .then((data) => {
                if (!cancelled) {
                    setAccounts(Array.isArray(data) ? data : [])
                    setIsLoading(false)
                }
            })
            .catch((err: unknown) => {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : 'Failed to fetch accounts')
                    setIsLoading(false)
                }
            })

        return () => { cancelled = true }
    }, [])

    // AC-3, AC-6: Compute portfolio total client-side from latest_balance fields
    const portfolioTotal = useMemo(() => {
        return accounts.reduce((sum, acct) => {
            return sum + (acct.latest_balance ?? 0)
        }, 0)
    }, [accounts])

    return { accounts, portfolioTotal, isLoading, error }
}
