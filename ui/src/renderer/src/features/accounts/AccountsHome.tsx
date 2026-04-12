import React, { useCallback, useMemo, useState } from 'react'
import { useAccounts, useCreateAccount, useArchivedAccounts } from '@/hooks/useAccounts'
import { useAccountContext } from '@/context/AccountContext'
import type { Account } from '@/hooks/useAccounts'
import AccountDetailPanel from './AccountDetailPanel'

// ── Currency formatter ──────────────────────────────────────────────────────

const currencyFmt = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
})

// ── MRU Card ────────────────────────────────────────────────────────────────

interface MruCardProps {
    account: Account
    onSelect: (id: string) => void
}

function MruCard({ account, onSelect }: MruCardProps) {
    return (
        <button
            data-testid={`mru-card-${account.account_id}`}
            className="flex flex-col gap-1 rounded-lg border border-border bg-bg-subtle p-3 text-left transition-colors hover:bg-bg-hover min-w-[180px]"
            onClick={() => onSelect(account.account_id)}
        >
            <span className="text-xs font-medium text-fg-muted uppercase tracking-wide">
                {ACCOUNT_TYPE_LABELS[account.account_type] ?? account.account_type}
            </span>
            <span className="text-sm font-semibold text-fg truncate">
                {account.name}
            </span>
            <span className="text-xs text-fg-muted">
                {account.institution}
            </span>
            <span className="text-sm font-medium text-fg mt-1">
                {account.latest_balance !== null
                    ? currencyFmt.format(account.latest_balance)
                    : '—'}
            </span>
        </button>
    )
}

// ── Add New Card ────────────────────────────────────────────────────────────

interface AddNewCardProps {
    onAdd: () => void
}

function AddNewCard({ onAdd }: AddNewCardProps) {
    return (
        <button
            data-testid="add-account-btn"
            className="flex flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-border p-3 text-fg-muted transition-colors hover:bg-bg-hover hover:text-fg min-w-[180px] min-h-[100px]"
            onClick={onAdd}
        >
            <span className="text-2xl">+</span>
            <span className="text-xs font-medium">Add New</span>
        </button>
    )
}

// ── Account Types for filter (must match backend AccountType StrEnum) ───────

const ACCOUNT_TYPES = ['broker', 'bank', 'revolving', 'installment', 'ira', '401k'] as const
const ACCOUNT_TYPE_LABELS: Record<string, string> = {
    broker: 'Broker',
    bank: 'Bank',
    revolving: 'Revolving',
    installment: 'Installment',
    ira: 'IRA',
    '401k': '401(k)',
}

// ── Relative date helper ────────────────────────────────────────────────────

function formatRelativeDate(dateStr: string | null): string {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 30) return `${diffDays}d ago`
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`
    return `${Math.floor(diffDays / 365)}y ago`
}

// ── Account Row ─────────────────────────────────────────────────────────────

interface AccountRowProps {
    account: Account
    onSelect: (id: string) => void
    portfolioPercent: number | null
}

function AccountRow({ account, onSelect, portfolioPercent }: AccountRowProps) {
    return (
        <tr
            className="cursor-pointer border-b border-border transition-colors hover:bg-bg-hover"
            onClick={() => onSelect(account.account_id)}
        >
            <td className="px-3 py-2 text-sm">
                <span className="inline-block rounded bg-bg-subtle px-1.5 py-0.5 text-xs font-medium text-fg-muted">
                    {ACCOUNT_TYPE_LABELS[account.account_type] ?? account.account_type}
                </span>
            </td>
            <td className="px-3 py-2 text-sm font-medium text-fg">
                {account.name}
            </td>
            <td className="px-3 py-2 text-sm text-fg-muted">
                {account.institution}
            </td>
            <td className="px-3 py-2 text-sm text-right tabular-nums">
                {account.latest_balance !== null
                    ? currencyFmt.format(account.latest_balance)
                    : '—'}
            </td>
            <td className="px-3 py-2 text-xs text-fg-muted">
                {formatRelativeDate(account.latest_balance_date)}
            </td>
            <td className="px-3 py-2 text-sm text-right tabular-nums text-fg-muted">
                {portfolioPercent !== null
                    ? `${portfolioPercent.toFixed(1)}%`
                    : '—'}
            </td>
        </tr>
    )
}

// ── AccountsHome ────────────────────────────────────────────────────────────

/**
 * AccountsHome — Account Management dashboard.
 *
 * Per 06-gui.md L275-398 and 06d L13-49:
 * - Split layout: left pane (MRU cards + table) + right pane (detail form)
 * - MRU card strip with top 3 recently used + "Add New"
 * - All Accounts table with type, name, institution, balance
 * - Portfolio total in left pane footer
 * - "Start Review" button dispatches zorivest:start-review event
 *
 * AC-1: MRU card strip
 * AC-2: Add New card
 * AC-3: Portfolio total
 * AC-4: All Accounts table
 * AC-15: E2E data-testid attributes
 */
export default function AccountsHome() {
    const { accounts, portfolioTotal, isFetching, refetch } = useAccounts()
    const { activeAccountId, selectAccount, mruAccountIds } = useAccountContext()
    const createAccount = useCreateAccount()
    const [showCreateForm, setShowCreateForm] = useState(false)
    const [typeFilter, setTypeFilter] = useState<string>('ALL')
    const [sortBy, setSortBy] = useState<'last_used' | 'name' | 'balance' | 'type' | 'institution' | 'portfolio'>('last_used')
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

    // Column sort handler — toggles direction, or resets to default when clicking a new column
    const handleColumnSort = useCallback((col: typeof sortBy) => {
        if (sortBy === col) {
            setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
        } else {
            setSortBy(col)
            setSortDir(col === 'name' || col === 'type' || col === 'institution' ? 'asc' : 'desc')
        }
    }, [sortBy])

    // Resolve MRU account objects from IDs
    const mruAccounts = mruAccountIds
        .map((id) => accounts.find((a) => a.account_id === id))
        .filter((a): a is Account => a !== undefined)

    const activeAccount = activeAccountId
        ? accounts.find((a) => a.account_id === activeAccountId) ?? null
        : null

    const handleSelectAccount = useCallback(
        (id: string) => {
            setShowCreateForm(false)
            selectAccount(id)
        },
        [selectAccount],
    )

    const handleAddNew = useCallback(() => {
        selectAccount(null)
        setShowCreateForm(true)
    }, [selectAccount])

    const handleStartReview = useCallback(() => {
        window.dispatchEvent(new CustomEvent('zorivest:start-review'))
    }, [])

    const isArchivedMode = typeFilter === 'ARCHIVED'
    const { accounts: archivedAccounts, isFetching: isFetchingArchived } = useArchivedAccounts(isArchivedMode)

    // Filter + sort accounts
    const filteredAccounts = useMemo(() => {
        const source = isArchivedMode ? archivedAccounts : (
            typeFilter === 'ALL' ? accounts : accounts.filter((a) => a.account_type === typeFilter)
        )

        const sorted = [...source].sort((a, b) => {
            let cmp = 0
            switch (sortBy) {
                case 'name':
                    cmp = a.name.localeCompare(b.name)
                    break
                case 'type':
                    cmp = (a.account_type ?? '').localeCompare(b.account_type ?? '')
                    break
                case 'institution':
                    cmp = (a.institution ?? '').localeCompare(b.institution ?? '')
                    break
                case 'balance':
                    cmp = (a.latest_balance ?? 0) - (b.latest_balance ?? 0)
                    break
                case 'portfolio': {
                    const pctA = portfolioTotal > 0 && a.latest_balance !== null ? a.latest_balance / portfolioTotal : 0
                    const pctB = portfolioTotal > 0 && b.latest_balance !== null ? b.latest_balance / portfolioTotal : 0
                    cmp = pctA - pctB
                    break
                }
                case 'last_used':
                default:
                    cmp = (a.latest_balance_date ?? '').localeCompare(b.latest_balance_date ?? '')
                    break
            }
            return sortDir === 'desc' ? -cmp : cmp
        })

        return sorted
    }, [accounts, archivedAccounts, typeFilter, sortBy, sortDir, isArchivedMode, portfolioTotal])

    return (
        <div data-testid="accounts-page" className="flex h-full gap-4">
            {/* Left Pane — MRU cards + table */}
            <div
                data-testid="accounts-left-pane"
                className="flex flex-col flex-1 min-w-0"
            >
                {/* Header with Start Review */}
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-fg">Accounts</h2>
                    <div className="flex items-center gap-2">
                        <button
                            data-testid="refresh-accounts-btn"
                            onClick={() => refetch()}
                            disabled={isFetching}
                            title="Refresh accounts list"
                            className="px-3 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isFetching || isFetchingArchived ? '⟳' : '↻'} Refresh
                        </button>
                        <button
                            data-testid="start-review-btn"
                            className="px-3 py-1.5 text-sm font-medium rounded-md border border-bg-subtle bg-bg hover:bg-bg-elevated text-fg transition-colors cursor-pointer"
                            onClick={handleStartReview}
                        >
                            Start Review
                        </button>
                    </div>
                </div>

                {/* MRU Card Strip */}
                <div className="flex gap-3 overflow-x-auto pb-3 mb-4">
                    {mruAccounts.map((account) => (
                        <MruCard
                            key={account.account_id}
                            account={account}
                            onSelect={handleSelectAccount}
                        />
                    ))}
                    <AddNewCard onAdd={handleAddNew} />
                </div>

                {/* Filter / Sort Controls */}
                <div data-testid="filter-sort-controls" className="flex items-center gap-3 mb-2">
                    <label className="flex items-center gap-1 text-xs text-fg-muted">
                        Filter:
                        <select
                            data-testid="type-filter"
                            className="rounded border border-border bg-bg px-1.5 py-0.5 text-xs"
                            value={typeFilter}
                            onChange={(e) => setTypeFilter(e.target.value)}
                        >
                            <option value="ALL">All Types</option>
                            {ACCOUNT_TYPES.map((t) => (
                                <option key={t} value={t}>{ACCOUNT_TYPE_LABELS[t] ?? t}</option>
                            ))}
                            <option disabled>────────</option>
                            <option value="ARCHIVED">📦 Archived</option>
                        </select>
                    </label>

                    <div className="ml-auto flex items-baseline gap-2">
                        <span className="text-sm font-semibold text-fg tabular-nums">
                            Portfolio: {currencyFmt.format(portfolioTotal)}
                        </span>
                        <span className="text-xs text-fg-muted">
                            across {filteredAccounts.length} {filteredAccounts.length === 1 ? 'account' : 'accounts'}
                        </span>
                    </div>
                </div>

                {/* All Accounts Table */}
                <div className="flex-1 overflow-auto rounded-lg border border-border">
                    <table
                        data-testid="account-list"
                        className="w-full text-left"
                    >
                        <thead className="border-b border-border bg-bg-subtle">
                            <tr>
                                {[
                                    { key: 'type' as const, label: 'Type', align: '' },
                                    { key: 'name' as const, label: 'Name', align: '' },
                                    { key: 'institution' as const, label: 'Institution', align: '' },
                                    { key: 'balance' as const, label: 'Balance', align: 'text-right' },
                                    { key: 'last_used' as const, label: 'Last Used', align: '' },
                                    { key: 'portfolio' as const, label: 'Portfolio %', align: 'text-right' },
                                ].map((col) => (
                                    <th
                                        key={col.key}
                                        className={`px-3 py-2 text-xs font-medium text-fg-muted uppercase tracking-wide cursor-pointer select-none hover:text-fg transition-colors ${col.align}`}
                                        onClick={() => handleColumnSort(col.key)}
                                    >
                                        {col.label}
                                        {sortBy === col.key && (
                                            <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
                                        )}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAccounts.map((account) => {
                                const pct = portfolioTotal > 0 && account.latest_balance !== null
                                    ? (account.latest_balance / portfolioTotal) * 100
                                    : null
                                return (
                                    <AccountRow
                                        key={account.account_id}
                                        account={account}
                                        onSelect={handleSelectAccount}
                                        portfolioPercent={pct}
                                    />
                                )
                            })}
                        </tbody>
                    </table>
                </div>


            </div>

            {/* Right Pane — Detail/Create panel */}
            <div
                data-testid="accounts-right-pane"
                className="w-96 shrink-0 border-l border-border pl-4 overflow-y-auto"
            >
                {showCreateForm ? (
                    <AccountDetailPanel
                        key="create"
                        account={{
                            account_id: '',
                            name: '',
                            account_type: 'broker',
                            institution: '',
                            currency: 'USD',
                            is_tax_advantaged: false,
                            is_archived: false,
                            is_system: false,
                            notes: '',
                            latest_balance: null,
                            latest_balance_date: null,
                        }}
                        isNew
                        onCreated={() => setShowCreateForm(false)}
                    />
                ) : activeAccount ? (
                    <AccountDetailPanel key={activeAccount.account_id} account={activeAccount} />
                ) : (
                    <div className="flex h-full items-center justify-center text-fg-muted text-sm">
                        Select an account to view details
                    </div>
                )}
            </div>
        </div>
    )
}
