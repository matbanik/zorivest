import React, { useCallback, useMemo, useRef, useState } from 'react'
import { useAccounts, useArchivedAccounts, useDeleteAccount, useForceDeleteAccount, useArchiveAccount, useUnarchiveAccount, fetchTradeCounts } from '@/hooks/useAccounts'
import type { Account, TradeCountInfo } from '@/hooks/useAccounts'
import { useAccountContext } from '@/context/AccountContext'
import { useFormGuard } from '@/hooks/useFormGuard'
import UnsavedChangesModal from '@/components/UnsavedChangesModal'
import SelectionCheckbox from '@/components/SelectionCheckbox'
import BulkActionBar from '@/components/BulkActionBar'
import TableFilterBar from '@/components/TableFilterBar'
import ConfirmDeleteModal from '@/components/ConfirmDeleteModal'
import TradeWarningModal from '@/components/TradeWarningModal'
import AccountDetailPanel from './AccountDetailPanel'
import type { AccountDetailPanelHandle } from './AccountDetailPanel'

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
    isSelected: boolean
    onToggleSelect: (id: string) => void
}

function AccountRow({ account, onSelect, portfolioPercent, isSelected, onToggleSelect }: AccountRowProps) {
    return (
        <tr
            className={`cursor-pointer border-b border-border transition-colors hover:bg-bg-elevated${isSelected ? ' bg-bg-subtle' : ''}`}
            onClick={() => onSelect(account.account_id)}
        >
            <td className="px-3 py-2 text-sm w-8" onClick={(e) => e.stopPropagation()}>
                <SelectionCheckbox
                    checked={isSelected}
                    onChange={() => onToggleSelect(account.account_id)}
                    ariaLabel={`Select ${account.name}`}
                    data-testid={`account-row-checkbox-${account.account_id}`}
                />
            </td>
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
    const deleteAccount = useDeleteAccount()
    const forceDeleteAccount = useForceDeleteAccount()
    const archiveAccount = useArchiveAccount()
    const unarchiveAccount = useUnarchiveAccount()
    const [showCreateForm, setShowCreateForm] = useState(false)
    const [typeFilter, setTypeFilter] = useState<string>('ALL')
    const [sortBy, setSortBy] = useState<'last_used' | 'name' | 'balance' | 'type' | 'institution' | 'portfolio'>('last_used')
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
    const [childDirty, setChildDirty] = useState(false)
    const [searchText, setSearchText] = useState('')
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
    const [showBulkConfirm, setShowBulkConfirm] = useState(false)
    const [showBulkArchive, setShowBulkArchive] = useState(false)
    const [showBulkUnarchive, setShowBulkUnarchive] = useState(false)

    // Trade warning queue for second confirmation on accounts with linked trades
    const [tradeWarningQueue, setTradeWarningQueue] = useState<Array<{
        accountId: string
        accountName: string
        tradeCount: number
        planCount: number
    }>>([])
    const [isCheckingTrades, setIsCheckingTrades] = useState(false)

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

    // ── Unsaved changes guard (3-button: Save & Continue via child ref) ────
    const panelRef = useRef<AccountDetailPanelHandle>(null)

    const doNavigate = useCallback((target: string | null) => {
        setChildDirty(false)
        if (target === '__new__') {
            handleAddNew()
        } else if (target) {
            handleSelectAccount(target)
        }
    }, [handleSelectAccount, handleAddNew])

    const handleSaveViaRef = useCallback(async () => {
        await panelRef.current?.save()
    }, [])

    const { showModal, guardedSelect, handleCancel, handleDiscard, handleSaveAndContinue, isSaveDisabled } =
        useFormGuard<string | null>({
            isDirty: childDirty,
            onNavigate: doNavigate,
            onSave: handleSaveViaRef,
            isFormInvalid: () => panelRef.current?.isInvalid() ?? false,
        })

    const guardedSelectAccount = useCallback((id: string) => {
        guardedSelect(id)
    }, [guardedSelect])

    const guardedAddNew = useCallback(() => {
        guardedSelect('__new__')
    }, [guardedSelect])

    const handleStartReview = useCallback(() => {
        window.dispatchEvent(new CustomEvent('zorivest:start-review'))
    }, [])

    const isArchivedMode = typeFilter === 'ARCHIVED'
    const { accounts: archivedAccounts, isFetching: isFetchingArchived } = useArchivedAccounts(isArchivedMode)

    // ── Selection helpers ──────────────────────────────────────────────────
    const toggleSelect = useCallback((id: string) => {
        setSelectedIds((prev) => {
            const next = new Set(prev)
            if (next.has(id)) {
                next.delete(id)
            } else {
                next.add(id)
            }
            return next
        })
    }, [])

    const clearSelection = useCallback(() => {
        setSelectedIds(new Set())
    }, [])

    // ── Bulk delete handler (two-stage: check trades, then confirm individually) ──
    const executeBulkDelete = useCallback(async () => {
        const ids = Array.from(selectedIds)
        setIsCheckingTrades(true)
        setShowBulkConfirm(false)

        try {
            // Fetch trade counts for all selected accounts
            const counts = await fetchTradeCounts(ids)

            // Separate accounts into no-trades (immediate delete) and has-trades (needs warning)
            const noTradeIds: string[] = []
            const withTrades: Array<{ accountId: string; accountName: string; tradeCount: number; planCount: number }> = []

            // Resolve account names from both active and archived lists
            const allAccounts = [...accounts, ...archivedAccounts]

            for (const id of ids) {
                const info: TradeCountInfo = counts[id] || { trade_count: 0, plan_count: 0 }
                if (info.trade_count === 0 && info.plan_count === 0) {
                    noTradeIds.push(id)
                } else {
                    const acct = allAccounts.find(a => a.account_id === id)
                    withTrades.push({
                        accountId: id,
                        accountName: acct?.name || id,
                        tradeCount: info.trade_count,
                        planCount: info.plan_count,
                    })
                }
            }

            // Immediately delete accounts with no trades
            for (const id of noTradeIds) {
                deleteAccount.mutate(id)
            }

            // Queue trade-warning modals for accounts with trades
            if (withTrades.length > 0) {
                setTradeWarningQueue(withTrades)
            } else {
                // All deleted, clean up
                clearSelection()
            }
        } catch {
            // If trade count check fails, fall back to regular delete
            for (const id of ids) {
                deleteAccount.mutate(id)
            }
            clearSelection()
        } finally {
            setIsCheckingTrades(false)
        }
    }, [selectedIds, accounts, archivedAccounts, deleteAccount, clearSelection])

    // Handle confirming a single trade-warning item (force-delete)
    const handleTradeWarningConfirm = useCallback(() => {
        const current = tradeWarningQueue[0]
        if (!current) return

        forceDeleteAccount.mutate(current.accountId, {
            onSettled: () => {
                setTradeWarningQueue(prev => {
                    const next = prev.slice(1)
                    if (next.length === 0) {
                        clearSelection()
                        refetch()
                    }
                    return next
                })
            },
        })
    }, [tradeWarningQueue, forceDeleteAccount, clearSelection, refetch])

    // Handle cancelling a trade-warning item (skip this account)
    const handleTradeWarningCancel = useCallback(() => {
        setTradeWarningQueue(prev => {
            const next = prev.slice(1)
            if (next.length === 0) {
                clearSelection()
                refetch()
            }
            return next
        })
    }, [clearSelection, refetch])

    // ── Bulk archive handler ─────────────────────────────────────────────
    const executeBulkArchive = useCallback(() => {
        const ids = Array.from(selectedIds)
        let completed = 0
        ids.forEach((id) => {
            archiveAccount.mutate(id, {
                onSettled: () => {
                    completed++
                    if (completed === ids.length) {
                        clearSelection()
                        setShowBulkArchive(false)
                        refetch()
                    }
                },
            })
        })
    }, [selectedIds, archiveAccount, clearSelection, refetch])

    // ── Bulk unarchive handler ────────────────────────────────────────────
    const executeBulkUnarchive = useCallback(() => {
        const ids = Array.from(selectedIds)
        let completed = 0
        ids.forEach((id) => {
            unarchiveAccount.mutate(id, {
                onSettled: () => {
                    completed++
                    if (completed === ids.length) {
                        clearSelection()
                        setShowBulkUnarchive(false)
                        refetch()
                    }
                },
            })
        })
    }, [selectedIds, unarchiveAccount, clearSelection, refetch])

    // Filter + sort accounts
    const filteredAccounts = useMemo(() => {
        const source = isArchivedMode ? archivedAccounts : (
            typeFilter === 'ALL' ? accounts : accounts.filter((a) => a.account_type === typeFilter)
        )

        // Apply text search filter
        const searched = searchText
            ? source.filter((a) => {
                const q = searchText.toLowerCase()
                return a.name.toLowerCase().includes(q) || (a.institution ?? '').toLowerCase().includes(q)
            })
            : source

        const sorted = [...searched].sort((a, b) => {
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
    }, [accounts, archivedAccounts, typeFilter, sortBy, sortDir, isArchivedMode, portfolioTotal, searchText])

    // ── Select-all toggle ────────────────────────────────────────────────
    const allSelected = filteredAccounts.length > 0 && filteredAccounts.every((a) => selectedIds.has(a.account_id))
    const someSelected = filteredAccounts.some((a) => selectedIds.has(a.account_id))

    const toggleSelectAll = useCallback(() => {
        if (allSelected) {
            clearSelection()
        } else {
            setSelectedIds(new Set(filteredAccounts.map((a) => a.account_id)))
        }
    }, [allSelected, filteredAccounts, clearSelection])

    return (
        <>
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
                            onSelect={guardedSelectAccount}
                        />
                    ))}
                    <AddNewCard onAdd={guardedAddNew} />
                </div>

                {/* Text Search + Type Filter */}
                <TableFilterBar
                    searchPlaceholder="Search by name or institution…"
                    searchValue={searchText}
                    onSearchChange={setSearchText}
                    debounceMs={0}
                    filterOptions={[
                        ...ACCOUNT_TYPES.map((t) => ({
                            label: ACCOUNT_TYPE_LABELS[t] ?? t,
                            value: t,
                        })),
                        { label: '📦 Archived', value: 'ARCHIVED' },
                    ]}
                    filterValue={typeFilter === 'ALL' ? '' : typeFilter}
                    onFilterChange={(v) => setTypeFilter(v || 'ALL')}
                    filterLabel="Type"
                />

                {/* Bulk Action Bar */}
                <BulkActionBar
                    selectedCount={selectedIds.size}
                    itemType="accounts"
                    onDelete={() => setShowBulkConfirm(true)}
                    onClearSelection={clearSelection}
                    actions={isArchivedMode
                        ? [{ label: '📤 Unarchive', onClick: () => setShowBulkUnarchive(true) }]
                        : [{ label: '📦 Archive', onClick: () => setShowBulkArchive(true) }]
                    }
                />

                {/* Portfolio summary */}
                <div data-testid="filter-sort-controls" className="flex items-center gap-3 mb-2">
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
                                <th className="px-3 py-2 w-8">
                                    <SelectionCheckbox
                                        checked={allSelected}
                                        indeterminate={!allSelected && someSelected}
                                        onChange={toggleSelectAll}
                                        ariaLabel="Select all accounts"
                                        data-testid="select-all-checkbox"
                                    />
                                </th>
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
                                        onSelect={guardedSelectAccount}
                                        portfolioPercent={pct}
                                        isSelected={selectedIds.has(account.account_id)}
                                        onToggleSelect={toggleSelect}
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
                        ref={panelRef}
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
                        onCreated={() => {
                            setChildDirty(false)
                            setShowCreateForm(false)
                        }}
                        onDirtyChange={setChildDirty}
                    />
                ) : activeAccount ? (
                    <AccountDetailPanel ref={panelRef} key={activeAccount.account_id} account={activeAccount} onDirtyChange={setChildDirty} />
                ) : (
                    <div className="flex h-full items-center justify-center text-fg-muted text-sm">
                        Select an account to view details
                    </div>
                )}
            </div>
        </div>

            <UnsavedChangesModal
                open={showModal}
                onCancel={handleCancel}
                onDiscard={handleDiscard}
                onSave={handleSaveAndContinue}
                isSaveDisabled={isSaveDisabled}
            />

            {/* Bulk Delete Confirmation Modal (first stage) */}
            {showBulkConfirm && (
                <ConfirmDeleteModal
                    open={showBulkConfirm}
                    target={{
                        type: 'accounts',
                        count: selectedIds.size,
                    }}
                    onCancel={() => setShowBulkConfirm(false)}
                    onConfirm={executeBulkDelete}
                    isDeleting={isCheckingTrades}
                />
            )}

            {/* Trade Warning Modal (second stage — sequential per account) */}
            {tradeWarningQueue.length > 0 && (
                <TradeWarningModal
                    open={true}
                    target={{
                        accountName: tradeWarningQueue[0].accountName,
                        tradeCount: tradeWarningQueue[0].tradeCount,
                        planCount: tradeWarningQueue[0].planCount,
                    }}
                    onCancel={handleTradeWarningCancel}
                    onConfirm={handleTradeWarningConfirm}
                    isDeleting={forceDeleteAccount.isPending}
                />
            )}

            {/* Bulk Archive Confirmation Modal */}
            {showBulkArchive && (
                <ConfirmDeleteModal
                    open={showBulkArchive}
                    target={{
                        type: 'accounts',
                        count: selectedIds.size,
                    }}
                    action="archive"
                    onCancel={() => setShowBulkArchive(false)}
                    onConfirm={executeBulkArchive}
                    isDeleting={archiveAccount.isPending}
                />
            )}

            {/* Bulk Unarchive Confirmation Modal */}
            {showBulkUnarchive && (
                <ConfirmDeleteModal
                    open={showBulkUnarchive}
                    target={{
                        type: 'accounts',
                        count: selectedIds.size,
                    }}
                    action="unarchive"
                    onCancel={() => setShowBulkUnarchive(false)}
                    onConfirm={executeBulkUnarchive}
                    isDeleting={unarchiveAccount.isPending}
                />
            )}
        </>
    )
}
