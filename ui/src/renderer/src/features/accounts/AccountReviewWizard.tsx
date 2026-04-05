import React, { useState, useMemo, useCallback } from 'react'
import { useAccounts, useAddBalance } from '@/hooks/useAccounts'
import { useAccountContext } from '@/context/AccountContext'
import type { Account } from '@/hooks/useAccounts'

// ── Currency formatter ──────────────────────────────────────────────────────

const currencyFmt = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
})

const percentFmt = new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
})

// Account type labels (must match backend AccountType StrEnum)
const ACCOUNT_TYPE_LABELS: Record<string, string> = {
    broker: 'Broker',
    bank: 'Bank',
    revolving: 'Revolving',
    installment: 'Installment',
    ira: 'IRA',
    '401k': '401(k)',
}

// ── Types ───────────────────────────────────────────────────────────────────

interface ReviewResult {
    account: Account
    previousBalance: number | null
    updatedBalance: number | null
    skipped: boolean
}

interface AccountReviewWizardProps {
    isOpen: boolean
    onClose: () => void
}

// ── Component ───────────────────────────────────────────────────────────────

/**
 * AccountReviewWizard — multi-step balance review dialog.
 *
 * Per 06d L83-162:
 * AC-10: Wizard opens/closes via isOpen prop
 * AC-11: Step view shows account info + current balance + new balance input
 * AC-12: Skip/Update & Next navigation
 * AC-13: Completion view with summary table
 * AC-16: Done button closes wizard
 *
 * Dedup rule: Balance only saved if value changed from last snapshot.
 */
export default function AccountReviewWizard({ isOpen, onClose }: AccountReviewWizardProps) {
    const { accounts } = useAccounts()
    const addBalance = useAddBalance()
    const { activeAccountId } = useAccountContext()

    const [currentIndex, setCurrentIndex] = useState(0)
    const [newBalance, setNewBalance] = useState<number>(0)
    const [results, setResults] = useState<ReviewResult[]>([])
    const [isComplete, setIsComplete] = useState(false)

    const totalAccounts = accounts.length
    const currentAccount = accounts[currentIndex] ?? null

    // Initialize balance when account changes
    React.useEffect(() => {
        if (currentAccount) {
            setNewBalance(currentAccount.latest_balance ?? 0)
        }
    }, [currentAccount])

    // Reset state when wizard opens — start from active account if set
    React.useEffect(() => {
        if (isOpen) {
            const startIdx = activeAccountId
                ? Math.max(0, accounts.findIndex((a) => a.account_id === activeAccountId))
                : 0
            setCurrentIndex(startIdx)
            setResults([])
            setIsComplete(false)
            if (accounts.length > 0) {
                const startAccount = accounts[startIdx] ?? accounts[0]
                setNewBalance(startAccount.latest_balance ?? 0)
            }
        }
    }, [isOpen, accounts, activeAccountId])

    const advance = useCallback(() => {
        if (currentIndex + 1 >= totalAccounts) {
            setIsComplete(true)
        } else {
            setCurrentIndex((prev) => prev + 1)
        }
    }, [currentIndex, totalAccounts])

    const handleSkip = useCallback(() => {
        if (currentAccount) {
            setResults((prev) => [
                ...prev,
                {
                    account: currentAccount,
                    previousBalance: currentAccount.latest_balance,
                    updatedBalance: null,
                    skipped: true,
                },
            ])
        }
        advance()
    }, [currentAccount, advance])

    const handleUpdate = useCallback(async () => {
        if (!currentAccount) return

        const changed = newBalance !== (currentAccount.latest_balance ?? 0)

        if (changed) {
            await addBalance.mutateAsync({
                accountId: currentAccount.account_id,
                payload: { balance: newBalance },
            })
        }

        setResults((prev) => [
            ...prev,
            {
                account: currentAccount,
                previousBalance: currentAccount.latest_balance,
                updatedBalance: changed ? newBalance : currentAccount.latest_balance,
                skipped: false,
            },
        ])

        advance()
    }, [currentAccount, newBalance, addBalance, advance])

    // Compute change display
    const changeDollar = currentAccount
        ? newBalance - (currentAccount.latest_balance ?? 0)
        : 0
    const changePercent = currentAccount && currentAccount.latest_balance
        ? changeDollar / currentAccount.latest_balance
        : 0

    // Running portfolio total
    const portfolioTotal = useMemo(() => {
        let total = 0
        accounts.forEach((acct, idx) => {
            const result = results.find((r) => r.account.account_id === acct.account_id)
            if (result && result.updatedBalance !== null) {
                total += result.updatedBalance
            } else if (idx === currentIndex && !isComplete) {
                total += newBalance
            } else {
                total += acct.latest_balance ?? 0
            }
        })
        return total
    }, [accounts, results, currentIndex, newBalance, isComplete])

    if (!isOpen) return null

    return (
        <div
            data-testid="account-review-wizard"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
            onClick={onClose}
        >
            <div
                className="mx-4 w-[480px] min-h-[250px] rounded-xl bg-bg border border-border shadow-2xl overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {isComplete ? (
                    /* ── Completion View ─────────────────────────────────────── */
                    <div className="p-6">
                        <h2 className="text-lg font-semibold text-fg mb-4">
                            Review Complete
                        </h2>

                        {/* Summary Table */}
                        <div className="max-h-64 overflow-auto mb-4">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-bg-subtle">
                                    <tr>
                                        <th className="px-3 py-2 text-xs font-medium text-fg-muted">Account</th>
                                        <th className="px-3 py-2 text-xs font-medium text-fg-muted text-right">Previous</th>
                                        <th className="px-3 py-2 text-xs font-medium text-fg-muted text-right">Updated</th>
                                        <th className="px-3 py-2 text-xs font-medium text-fg-muted text-right">Change</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {results.map((result) => {
                                        const prev = result.previousBalance ?? 0
                                        const updated = result.updatedBalance ?? prev
                                        const delta = updated - prev
                                        return (
                                            <tr key={result.account.account_id} className="border-b border-border/50">
                                                <td className="px-3 py-2">
                                                    {result.account.name}
                                                    {result.skipped && (
                                                        <span className="ml-1 text-xs text-fg-muted">(skipped)</span>
                                                    )}
                                                </td>
                                                <td className="px-3 py-2 text-right tabular-nums">
                                                    {currencyFmt.format(prev)}
                                                </td>
                                                <td className="px-3 py-2 text-right tabular-nums">
                                                    {result.skipped ? '—' : currencyFmt.format(updated)}
                                                </td>
                                                <td className="px-3 py-2 text-right tabular-nums">
                                                    {result.skipped ? '—' : (
                                                        <span className={delta > 0 ? 'text-green-500' : delta < 0 ? 'text-red-500' : ''}>
                                                            {delta > 0 ? '+' : ''}{currencyFmt.format(delta)}
                                                        </span>
                                                    )}
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>

                        {/* Portfolio Total */}
                        <div className="flex justify-between items-center py-3 border-t border-border">
                            <span className="text-sm text-fg-muted">Portfolio Total</span>
                            <span className="font-semibold text-fg tabular-nums">
                                {currencyFmt.format(portfolioTotal)}
                            </span>
                        </div>

                        {/* Done Button */}
                        <button
                            className="mt-4 w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-fg-on-accent hover:bg-accent-hover"
                            onClick={onClose}
                        >
                            Done
                        </button>
                    </div>
                ) : currentAccount ? (
                    /* ── Step View ───────────────────────────────────────────── */
                    <div className="p-6">
                        {/* Header with Cancel */}
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-xs text-fg-muted">Balance Review</span>
                            <button
                                className="rounded px-2 py-1 text-xs text-fg-muted hover:bg-bg-hover"
                                onClick={onClose}
                            >
                                ✕ Cancel
                            </button>
                        </div>

                        {/* Progress Bar */}
                        <div className="mb-4">
                            <div className="flex items-center justify-between text-xs text-fg-muted mb-1">
                                <span>Account {currentIndex + 1} of {totalAccounts}</span>
                                <span>{Math.round(((currentIndex) / totalAccounts) * 100)}%</span>
                            </div>
                            <div className="h-1.5 rounded-full bg-bg-subtle overflow-hidden">
                                <div
                                    className="h-full rounded-full bg-accent transition-all"
                                    style={{ width: `${((currentIndex) / totalAccounts) * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Account Info */}
                        <div className="mb-4">
                            <span className="inline-block rounded bg-bg-subtle px-1.5 py-0.5 text-xs font-medium text-fg-muted mb-1">
                                {ACCOUNT_TYPE_LABELS[currentAccount.account_type] ?? currentAccount.account_type}
                            </span>
                            <h3 className="text-lg font-semibold text-fg">
                                {currentAccount.name}
                            </h3>
                            <p className="text-sm text-fg-muted">{currentAccount.institution}</p>
                        </div>

                        {/* Current Balance */}
                        <div className="rounded-lg border border-border p-3 mb-4">
                            <span className="text-xs text-fg-muted uppercase tracking-wide">
                                Current Balance
                            </span>
                            <p className="text-xl font-semibold text-fg tabular-nums">
                                {currentAccount.latest_balance !== null
                                    ? currencyFmt.format(currentAccount.latest_balance)
                                    : '—'}
                            </p>
                            {currentAccount.latest_balance_date && (
                                <span className="text-xs text-fg-muted">
                                    as of {currentAccount.latest_balance_date}
                                </span>
                            )}
                        </div>

                        {/* New Balance Input */}
                        <div className="mb-4">
                            <label htmlFor="new-balance" className="text-xs font-medium text-fg-muted block mb-1">
                                New Balance
                            </label>
                            <input
                                id="new-balance"
                                type="number"
                                step="0.01"
                                value={newBalance}
                                onChange={(e) => setNewBalance(parseFloat(e.target.value) || 0)}
                                className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm tabular-nums"
                            />
                            {/* Live change calculation */}
                            {changeDollar !== 0 && (
                                <p className={`text-sm mt-1 ${changeDollar > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {changeDollar > 0 ? '+' : ''}{currencyFmt.format(changeDollar)}
                                    {' '}({changePercent > 0 ? '+' : ''}{percentFmt.format(changePercent)})
                                </p>
                            )}
                        </div>

                        {/* Fetch from API — BROKER accounts only (AC-13) */}
                        {currentAccount.account_type === 'broker' && (
                            <button
                                data-testid="fetch-from-api-btn"
                                className="mb-4 w-full rounded-md border border-border px-3 py-2 text-sm text-fg-muted opacity-60 cursor-not-allowed"
                                disabled
                                title="Not yet connected — configure in Settings"
                            >
                                Fetch from API
                            </button>
                        )}

                        {/* Running Portfolio Total */}
                        <div className="flex justify-between items-center py-2 text-sm border-t border-border mb-4">
                            <span className="text-fg-muted">Running Portfolio Total</span>
                            <span className="font-semibold text-fg tabular-nums">
                                {currencyFmt.format(portfolioTotal)}
                            </span>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2">
                            <button
                                className="flex-1 rounded-md border border-border px-4 py-2 text-sm text-fg-muted hover:bg-bg-hover"
                                onClick={handleSkip}
                            >
                                Skip
                            </button>
                            <button
                                className="flex-1 rounded-md bg-accent px-4 py-2 text-sm font-medium text-fg-on-accent hover:bg-accent-hover"
                                onClick={handleUpdate}
                                disabled={addBalance.isPending}
                            >
                                {addBalance.isPending ? 'Saving...' : 'Update & Next ▶'}
                            </button>
                        </div>
                    </div>
                ) : (
                    /* ── Empty State (no accounts) ──────────────────────────── */
                    <div className="p-6 text-center">
                        <p className="text-sm text-fg-muted mb-4">No accounts to review.</p>
                        <button
                            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-fg-on-accent hover:bg-accent-hover"
                            onClick={onClose}
                        >
                            Close
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
