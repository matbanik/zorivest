import { useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'

// ── Account types matching backend AccountResponse ────────────────────────

export interface Account {
    account_id: string
    name: string
    account_type: string
    institution: string
    currency: string
    is_tax_advantaged: boolean
    notes: string
    latest_balance: number | null
    latest_balance_date: string | null
}

/** Payload for creating/updating an account */
export interface AccountPayload {
    name: string
    account_type: string
    institution?: string
    currency?: string
    is_tax_advantaged?: boolean
    notes?: string
}

/** Balance history entry — matches Python BalanceSnapshotResponse */
export interface BalanceEntry {
    id: number
    account_id: string
    balance: number
    datetime: string | null
}

/** Paginated balance response — matches Python PaginatedBalanceResponse */
export interface PaginatedBalanceResponse {
    items: BalanceEntry[]
    total: number
}

/** Payload for posting a new balance — matches Python BalanceRequest */
export interface BalancePayload {
    balance: number
    snapshot_datetime?: string
}

export interface UseAccountsResult {
    accounts: Account[]
    portfolioTotal: number
    isLoading: boolean
    error: string | null
    refetch: () => void
}

// ── Query keys ──────────────────────────────────────────────────────────────

const accountKeys = {
    all: ['accounts'] as const,
    detail: (id: string) => ['accounts', id] as const,
    balances: (id: string) => ['accounts', id, 'balances'] as const,
}

// ── useAccounts — fetches account list ──────────────────────────────────────

/**
 * useAccounts — fetches account list from GET /api/v1/accounts
 * and computes portfolio total from latest_balance fields.
 *
 * AC-6: Fetches from GET /api/v1/accounts and computes portfolio total.
 */
export function useAccounts(): UseAccountsResult {
    const { data, isLoading, error, refetch } = useQuery({
        queryKey: accountKeys.all,
        queryFn: () => apiFetch<Account[]>('/api/v1/accounts'),
        staleTime: 30_000,
    })

    const accounts = Array.isArray(data) ? data : []

    // AC-3, AC-6: Compute portfolio total client-side from latest_balance fields
    const portfolioTotal = useMemo(() => {
        return accounts.reduce((sum, acct) => {
            return sum + (acct.latest_balance ?? 0)
        }, 0)
    }, [accounts])

    return {
        accounts,
        portfolioTotal,
        isLoading,
        error: error ? (error instanceof Error ? error.message : 'Failed to fetch accounts') : null,
        refetch,
    }
}

// ── CRUD mutation hooks ─────────────────────────────────────────────────────

/**
 * useCreateAccount — POST /api/v1/accounts
 *
 * AC-7: Save → POST /accounts for new accounts.
 */
export function useCreateAccount() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (payload: AccountPayload) =>
            apiFetch<Account>('/api/v1/accounts', {
                method: 'POST',
                body: JSON.stringify({
                    account_id: crypto.randomUUID(),
                    ...payload,
                }),
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
        },
    })
}

/**
 * useUpdateAccount — PUT /api/v1/accounts/{id}
 *
 * AC-7: Save → PUT /accounts/{id} for existing accounts.
 */
export function useUpdateAccount() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ id, payload }: { id: string; payload: AccountPayload }) =>
            apiFetch<Account>(`/api/v1/accounts/${id}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
        },
    })
}

/**
 * useDeleteAccount — DELETE /api/v1/accounts/{id}
 *
 * AC-8: Delete with confirmation → DELETE /accounts/{id}.
 */
export function useDeleteAccount() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id: string) =>
            apiFetch<void>(`/api/v1/accounts/${id}`, {
                method: 'DELETE',
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
        },
    })
}

// ── Balance hooks ───────────────────────────────────────────────────────────

/**
 * useBalanceHistory — GET /api/v1/accounts/{id}/balances
 *
 * AC-9: Balance history sparkline + table data.
 */
export function useBalanceHistory(accountId: string | null) {
    return useQuery({
        queryKey: accountId ? accountKeys.balances(accountId) : ['accounts', 'no-id', 'balances'],
        queryFn: async (): Promise<BalanceEntry[]> => {
            if (!accountId) return []
            const res = await apiFetch<PaginatedBalanceResponse>(
                `/api/v1/accounts/${accountId}/balances`,
            )
            return res.items
        },
        enabled: !!accountId,
    })
}

/**
 * useAddBalance — POST /api/v1/accounts/{id}/balances
 *
 * AC-9: Add new balance entry.
 */
export function useAddBalance() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ accountId, payload }: { accountId: string; payload: BalancePayload }) =>
            apiFetch<BalanceEntry>(`/api/v1/accounts/${accountId}/balances`, {
                method: 'POST',
                body: JSON.stringify(payload),
            }),
        onSuccess: (_data, variables) => {
            queryClient.invalidateQueries({ queryKey: accountKeys.balances(variables.accountId) })
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
        },
    })
}
