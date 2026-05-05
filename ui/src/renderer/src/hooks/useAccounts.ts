import { useEffect, useMemo } from 'react'
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
    is_archived: boolean
    is_system: boolean
    notes: string
    latest_balance: number | null
    latest_balance_date: string | null
    trade_count?: number | null
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
    isFetching: boolean
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
    const queryClient = useQueryClient()

    // Clear any stale cache on mount — prevents ghost flash when navigating back
    useEffect(() => {
        queryClient.removeQueries({ queryKey: accountKeys.all, exact: true })
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    const { data, isLoading, isFetching, error, refetch } = useQuery({
        queryKey: accountKeys.all,
        queryFn: () => apiFetch<Account[]>('/api/v1/accounts'),
        staleTime: 0,
        gcTime: 0,
        refetchInterval: 5_000,    // G5: auto-refresh for external mutations (MCP, API)
        refetchOnWindowFocus: true,
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
        isFetching,
        error: error ? (error instanceof Error ? error.message : 'Failed to fetch accounts') : null,
        refetch,
    }
}

// ── useArchivedAccounts ─ fetches archived accounts only when needed ────────

export function useArchivedAccounts(enabled: boolean) {
    const { data, isLoading, isFetching, error, refetch } = useQuery({
        queryKey: ['accounts', 'archived'],
        queryFn: () => apiFetch<Account[]>('/api/v1/accounts?include_archived=true'),
        staleTime: 0,
        enabled,
    })

    // Filter to only archived accounts (the API returns all when include_archived=true)
    const archivedAccounts = useMemo(() => {
        const all = Array.isArray(data) ? data : []
        return all.filter((a) => a.is_archived)
    }, [data])

    return {
        accounts: archivedAccounts,
        isLoading,
        isFetching,
        error: error ? (error instanceof Error ? error.message : 'Failed to fetch archived accounts') : null,
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
        onMutate: async (id: string) => {
            // Optimistic removal — prevent stale ghost flash
            await queryClient.cancelQueries({ queryKey: accountKeys.all })
            const previous = queryClient.getQueryData<Account[]>(accountKeys.all)
            queryClient.setQueryData<Account[]>(
                accountKeys.all,
                (old) => old?.filter((a) => a.account_id !== id) ?? [],
            )
            return { previous }
        },
        onError: (_err, _id, context) => {
            // Rollback on failure
            if (context?.previous) {
                queryClient.setQueryData(accountKeys.all, context.previous)
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
            queryClient.invalidateQueries({ queryKey: ['accounts', 'archived'] })
        },
    })
}

/**
 * useForceDeleteAccount — POST /api/v1/accounts/{id}:reassign-trades
 *
 * Moves all trades to SYSTEM_DEFAULT then hard-deletes the account.
 * Use this for archived accounts that have trades (where DELETE returns 409).
 */
export function useForceDeleteAccount() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id: string) =>
            apiFetch<{ trades_reassigned: number; account_id: string }>(`/api/v1/accounts/${id}:reassign-trades`, {
                method: 'POST',
            }),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
            queryClient.invalidateQueries({ queryKey: ['accounts', 'archived'] })
        },
    })
}

/**
 * useArchiveAccount — POST /api/v1/accounts/{id}:archive
 *
 * AC-10: Soft-delete (set is_archived=True). Trades remain unchanged.
 */
export function useArchiveAccount() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id: string) =>
            apiFetch<{ status: string; account_id: string }>(`/api/v1/accounts/${id}:archive`, {
                method: 'POST',
            }),
        onMutate: async (id: string) => {
            // Optimistic removal — archived accounts excluded from default list
            await queryClient.cancelQueries({ queryKey: accountKeys.all })
            const previous = queryClient.getQueryData<Account[]>(accountKeys.all)
            queryClient.setQueryData<Account[]>(
                accountKeys.all,
                (old) => old?.filter((a) => a.account_id !== id) ?? [],
            )
            return { previous }
        },
        onError: (_err, _id, context) => {
            if (context?.previous) {
                queryClient.setQueryData(accountKeys.all, context.previous)
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
            queryClient.invalidateQueries({ queryKey: ['accounts', 'archived'] })
        },
    })
}

/**
 * useUnarchiveAccount — POST /api/v1/accounts/{id}:unarchive
 *
 * Restore an archived account: set is_archived=False.
 */
export function useUnarchiveAccount() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id: string) =>
            apiFetch<{ status: string; account_id: string }>(`/api/v1/accounts/${id}:unarchive`, {
                method: 'POST',
            }),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: accountKeys.all })
            queryClient.invalidateQueries({ queryKey: ['accounts', 'archived'] })
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

// ── Trade count query ───────────────────────────────────────────────────

/** Result shape from POST /accounts:trade-counts */
export interface TradeCountInfo {
    trade_count: number
    plan_count: number
}

/**
 * Fetch trade + plan counts for a list of account IDs.
 * Used by the delete flow to determine which accounts need
 * a second confirmation (trade reassignment warning).
 */
export async function fetchTradeCounts(
    accountIds: string[],
): Promise<Record<string, TradeCountInfo>> {
    return apiFetch<Record<string, TradeCountInfo>>('/api/v1/accounts:trade-counts', {
        method: 'POST',
        body: JSON.stringify({ account_ids: accountIds }),
    })
}
