import React, { useState, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import type { Account } from '@/hooks/useAccounts'
import { useUpdateAccount, useDeleteAccount, useAddBalance, useCreateAccount } from '@/hooks/useAccounts'
import BalanceHistory from './BalanceHistory'
import { formatTimestamp } from '@/lib/formatDate'

// ── Schema ──────────────────────────────────────────────────────────────────

// Must match backend AccountType StrEnum (lowercase values)
const ACCOUNT_TYPES = ['broker', 'bank', 'revolving', 'installment', 'ira', '401k'] as const
const ACCOUNT_TYPE_LABELS: Record<string, string> = {
    broker: 'Broker',
    bank: 'Bank',
    revolving: 'Revolving',
    installment: 'Installment',
    ira: 'IRA',
    '401k': '401(k)',
}
const CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'JPY', 'CHF'] as const

const accountSchema = z.object({
    name: z.string().min(1, 'Name is required').max(100),
    account_type: z.string().min(1, 'Account type is required'),
    institution: z.string().max(100).optional().default(''),
    currency: z.string().min(1).default('USD'),
    is_tax_advantaged: z.boolean().default(false),
    notes: z.string().max(1000).optional().default(''),
})

type AccountFormData = z.infer<typeof accountSchema>

// ── Currency formatter ──────────────────────────────────────────────────────

const currencyFmt = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
})

// ── Component ───────────────────────────────────────────────────────────────

interface AccountDetailPanelProps {
    account: Account
    /** When true, form creates a new account instead of updating */
    isNew?: boolean
    /** Callback fired after successful create */
    onCreated?: () => void
}

/**
 * AccountDetailPanel — CRUD form for account editing.
 *
 * AC-5: Form fields (name, type, institution, currency, tax-advantaged, notes)
 * AC-6: Latest balance display + "Update Balance" dialog
 * AC-7: Save → PUT /accounts/{id}
 * AC-8: Delete with confirmation → DELETE /accounts/{id}
 */
export default function AccountDetailPanel({ account, isNew, onCreated }: AccountDetailPanelProps) {
    const updateAccount = useUpdateAccount()
    const deleteAccount = useDeleteAccount()
    const addBalance = useAddBalance()
    const createAccountMutation = useCreateAccount()
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
    const [showBalanceInput, setShowBalanceInput] = useState(false)
    const [newBalance, setNewBalance] = useState('')

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<AccountFormData>({
        resolver: zodResolver(accountSchema),
        defaultValues: {
            name: account.name,
            account_type: account.account_type,
            institution: account.institution,
            currency: account.currency,
            is_tax_advantaged: account.is_tax_advantaged,
            notes: account.notes,
        },
    })

    // Reset form when switching to a DIFFERENT account.
    // Uses a ref to avoid re-resetting the same account (which would
    // clear user-typed values when the parent re-renders).
    const prevAccountId = useRef(account.account_id)
    useEffect(() => {
        if (prevAccountId.current !== account.account_id) {
            prevAccountId.current = account.account_id
            reset({
                name: account.name,
                account_type: account.account_type,
                institution: account.institution,
                currency: account.currency,
                is_tax_advantaged: account.is_tax_advantaged,
                notes: account.notes,
            })
        }
    }, [account.account_id, account.name, account.account_type, account.institution, account.currency, account.is_tax_advantaged, account.notes, reset])

    const onSave = (data: AccountFormData) => {
        if (isNew) {
            createAccountMutation.mutate(data, {
                onSuccess: () => onCreated?.(),
            })
        } else {
            updateAccount.mutate({
                id: account.account_id,
                payload: data,
            })
        }
    }

    const onDelete = () => {
        deleteAccount.mutate(account.account_id)
        setShowDeleteConfirm(false)
    }

    const onUpdateBalance = () => {
        const num = parseFloat(newBalance)
        if (!isNaN(num)) {
            addBalance.mutate({
                accountId: account.account_id,
                payload: { balance: num },
            })
            setShowBalanceInput(false)
            setNewBalance('')
        }
    }

    return (
        <div data-testid="account-detail-panel" className="flex flex-col gap-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-fg">{isNew ? 'New Account' : account.name}</h3>
            </div>

            {/* Balance Section — only for existing accounts */}
            {!isNew && (
            <div className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between">
                    <div>
                        <span className="text-xs text-fg-muted uppercase tracking-wide">
                            Latest Balance
                        </span>
                        <p data-testid="balance-latest-value" className="text-xl font-semibold text-fg tabular-nums">
                            {account.latest_balance !== null
                                ? currencyFmt.format(account.latest_balance)
                                : '—'}
                        </p>
                        {account.latest_balance_date && (
                            <span className="text-xs text-fg-muted">
                            as of {formatTimestamp(account.latest_balance_date)}
                            </span>
                        )}
                    </div>
                    {!showBalanceInput && (
                    <button
                        type="button"
                        data-testid="balance-update-btn"
                        className="rounded-md border border-border px-2 py-1 text-xs text-fg-muted hover:bg-bg-hover"
                        onClick={() => setShowBalanceInput(true)}
                    >
                        Update Balance
                    </button>
                    )}
                </div>

                {showBalanceInput && (
                    <div className="mt-3 flex gap-2">
                        <input
                            type="number"
                            step="0.01"
                            value={newBalance}
                            onChange={(e) => setNewBalance(e.target.value)}
                            className="flex-1 rounded-md border border-border bg-bg px-2 py-1 text-sm"
                            placeholder="New balance..."
                            aria-label="New balance amount"
                            data-testid="balance-input"
                        />
                        <button
                            type="button"
                            data-testid="balance-save-btn"
                            className="rounded-md bg-accent px-3 py-1.5 text-sm text-accent-fg hover:bg-accent/90 border border-accent"
                            onClick={onUpdateBalance}
                        >
                            Save
                        </button>
                        <button
                            type="button"
                            data-testid="balance-cancel-btn"
                            className="rounded-md bg-bg px-3 py-1.5 text-sm text-fg-muted hover:text-fg border border-bg-subtle"
                            onClick={() => setShowBalanceInput(false)}
                        >
                            Cancel
                        </button>
                    </div>
                )}
            </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit(onSave)} className="flex flex-col gap-3">
                {/* Name */}
                <div className="flex flex-col gap-1">
                    <label htmlFor="name" className="text-xs font-medium text-fg-muted">
                        Name
                    </label>
                    <input
                        id="name"
                        data-testid="account-name-input"
                        {...register('name')}
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm"
                    />
                    {errors.name && (
                        <span className="text-xs text-error">{errors.name.message}</span>
                    )}
                </div>

                {/* Account Type */}
                <div className="flex flex-col gap-1">
                    <label htmlFor="account_type" className="text-xs font-medium text-fg-muted">
                        Type
                    </label>
                    <select
                        id="account_type"
                        data-testid="account-type-select"
                        {...register('account_type')}
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm"
                    >
                        {ACCOUNT_TYPES.map((type) => (
                            <option key={type} value={type}>
                                {ACCOUNT_TYPE_LABELS[type] ?? type}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Institution */}
                <div className="flex flex-col gap-1">
                    <label htmlFor="institution" className="text-xs font-medium text-fg-muted">
                        Institution
                    </label>
                    <input
                        id="institution"
                        data-testid="account-institution-input"
                        {...register('institution')}
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm"
                    />
                </div>

                {/*
                 * DEFERRED: Multi-currency support.
                 * The Currency selector is hidden because the $ symbol and USD
                 * formatting are hardcoded throughout the GUI (Intl.NumberFormat,
                 * balance displays, portfolio totals, etc.). Enabling this dropdown
                 * without a coordinated currency-aware formatting pass would create
                 * data inconsistencies (e.g., GBP balance displayed with $ symbol).
                 *
                 * This requires a dedicated planning phase after the full GUI build
                 * is complete, covering: dynamic Intl.NumberFormat per account,
                 * multi-currency portfolio aggregation, and FX rate sourcing.
                 *
                 * The database column (AccountModel.currency) exists and defaults
                 * to USD. Re-enable this block once multi-currency planning is done.
                 */}
                {/* <div className="flex flex-col gap-1">
                    <label htmlFor="currency" className="text-xs font-medium text-fg-muted">
                        Currency
                    </label>
                    <select
                        id="currency"
                        data-testid="account-currency-select"
                        {...register('currency')}
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm"
                    >
                        {CURRENCIES.map((curr) => (
                            <option key={curr} value={curr}>
                                {curr}
                            </option>
                        ))}
                    </select>
                </div> */}

                {/* Tax Advantaged */}
                <div className="flex items-center gap-2">
                    <input
                        id="is_tax_advantaged"
                        type="checkbox"
                        data-testid="account-tax-advantaged-checkbox"
                        {...register('is_tax_advantaged')}
                        className="rounded border-border"
                    />
                    <label htmlFor="is_tax_advantaged" className="text-sm text-fg">
                        Tax Advantaged
                    </label>
                </div>

                {/* Notes */}
                <div className="flex flex-col gap-1">
                    <label htmlFor="notes" className="text-xs font-medium text-fg-muted">
                        Notes
                    </label>
                    <textarea
                        id="notes"
                        data-testid="account-notes-textarea"
                        {...register('notes')}
                        rows={3}
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm resize-none"
                    />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2 border-t border-border">
                    <button
                        type="submit"
                        data-testid="account-submit-btn"
                        className="flex-1 rounded-md bg-accent px-4 py-1.5 text-sm font-medium text-accent-fg hover:bg-accent/90 border border-accent"
                        disabled={isNew ? createAccountMutation.isPending : updateAccount.isPending}
                    >
                        {isNew
                            ? (createAccountMutation.isPending ? 'Creating...' : 'Create')
                            : (updateAccount.isPending ? 'Saving...' : 'Save')}
                    </button>
                    {!isNew && (
                    <button
                        type="button"
                        data-testid="account-delete-btn"
                        className="rounded-md bg-red-900/30 px-4 py-1.5 text-sm font-medium text-red-400 hover:bg-red-900/50 border border-red-900/50"
                        onClick={() => setShowDeleteConfirm(true)}
                    >
                        Delete
                    </button>
                    )}
                </div>
            </form>

            {/* Delete Confirmation */}
            {showDeleteConfirm && (
                <div className="rounded-lg border border-error bg-error/5 p-3">
                    <p className="text-sm text-fg mb-2">
                        Are you sure you want to delete <strong>{account.name}</strong>?
                        This action cannot be undone.
                    </p>
                    <div className="flex gap-2">
                        <button
                            className="rounded-md bg-error px-3 py-1 text-sm text-white hover:bg-error/80"
                            onClick={onDelete}
                        >
                            Confirm Delete
                        </button>
                        <button
                            className="rounded-md border border-border px-3 py-1 text-sm hover:bg-bg-hover"
                            onClick={() => setShowDeleteConfirm(false)}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {/* Balance History — only for existing accounts */}
            {!isNew && <BalanceHistory accountId={account.account_id} />}
        </div>
    )
}
