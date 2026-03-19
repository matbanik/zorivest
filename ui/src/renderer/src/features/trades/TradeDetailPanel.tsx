import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import type { Trade } from './TradesTable'
import ScreenshotPanel from './ScreenshotPanel'
import TradeReportForm from './TradeReportForm'

// ── Schema ───────────────────────────────────────────────────────────────

const tradeSchema = z.object({
    instrument: z.string().min(1, 'Instrument is required'),
    action: z.enum(['BOT', 'SLD']),
    quantity: z.number().positive('Quantity must be positive'),
    price: z.number().positive('Price must be positive'),
    account_id: z.string().min(1, 'Account is required'),
    commission: z.number().min(0).default(0),
    realized_pnl: z.number().nullable().default(null),
    notes: z.string().nullable().default(null),
})

type TradeFormData = z.infer<typeof tradeSchema>

// ── Tabs ─────────────────────────────────────────────────────────────────

type DetailTab = 'info' | 'journal' | 'screenshots'

// ── Component ────────────────────────────────────────────────────────────

interface TradeDetailPanelProps {
    trade?: Trade | null
    onSave?: (data: TradeFormData) => void
    onDelete?: (execId: string) => void
    onClose?: () => void
}

/**
 * TradeDetailPanel — slide-out right panel with 3 tabs: Info, Journal, Screenshots.
 * Info tab has 9 trade form fields with Zod validation.
 */
export default function TradeDetailPanel({
    trade,
    onSave,
    onDelete,
    onClose,
}: TradeDetailPanelProps) {
    const [activeTab, setActiveTab] = useState<DetailTab>('info')

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<TradeFormData>({
        resolver: zodResolver(tradeSchema),
        defaultValues: trade
            ? {
                instrument: trade.instrument,
                action: trade.action,
                quantity: trade.quantity,
                price: trade.price,
                account_id: trade.account_id,
                commission: trade.commission,
                realized_pnl: trade.realized_pnl,
                notes: trade.notes,
            }
            : {
                instrument: '',
                action: 'BOT',
                quantity: 0,
                price: 0,
                account_id: '',
                commission: 0,
                realized_pnl: null,
                notes: null,
            },
    })

    const onSubmit = (data: TradeFormData) => {
        onSave?.(data)
    }

    if (!trade) {
        return (
            <div className="flex items-center justify-center h-full text-fg-muted text-sm">
                Select a trade to view details
            </div>
        )
    }

    const tabs: { key: DetailTab; label: string }[] = [
        { key: 'info', label: 'Info' },
        { key: 'journal', label: 'Journal' },
        { key: 'screenshots', label: 'Screenshots' },
    ]

    return (
        <div className="flex flex-col h-full bg-bg-elevated border-l border-bg-subtle">
            {/* Header */}
            <div className="px-4 py-3 border-b border-bg-subtle">
                <div className="flex items-center justify-between">
                    <span className="text-sm text-fg-muted font-mono">{trade.exec_id}</span>
                    <button
                        onClick={onClose}
                        className="text-fg-muted hover:text-fg text-sm"
                        aria-label="Close detail panel"
                    >
                        ✕
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-bg-subtle">
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`px-4 py-2 text-sm transition-colors ${activeTab === tab.key
                            ? 'border-b-2 border-accent text-fg font-medium'
                            : 'text-fg-muted hover:text-fg'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-auto p-4">
                {activeTab === 'info' && (
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        {/* Instrument */}
                        <div>
                            <label className="block text-xs text-fg-muted mb-1">Instrument</label>
                            <input
                                data-testid="trade-symbol-input"
                                {...register('instrument')}
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                            {errors.instrument && (
                                <span className="text-xs text-red-400">{errors.instrument.message}</span>
                            )}
                        </div>

                        {/* Action + Qty row */}
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Action</label>
                                <select
                                    data-testid="trade-side-select"
                                    {...register('action')}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                >
                                    <option value="BOT">BOT</option>
                                    <option value="SLD">SLD</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Qty</label>
                                <input
                                    data-testid="trade-quantity-input"
                                    type="number"
                                    {...register('quantity', { valueAsNumber: true })}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                />
                                {errors.quantity && (
                                    <span className="text-xs text-red-400">{errors.quantity.message}</span>
                                )}
                            </div>
                        </div>

                        {/* Price */}
                        <div>
                            <label className="block text-xs text-fg-muted mb-1">Price</label>
                            <input
                                data-testid="trade-price-input"
                                type="number"
                                step="0.01"
                                {...register('price', { valueAsNumber: true })}
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                            {errors.price && (
                                <span className="text-xs text-red-400">{errors.price.message}</span>
                            )}
                        </div>

                        {/* Account */}
                        <div>
                            <label className="block text-xs text-fg-muted mb-1">Account</label>
                            <input
                                {...register('account_id')}
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                            />
                            {errors.account_id && (
                                <span className="text-xs text-red-400">{errors.account_id.message}</span>
                            )}
                        </div>

                        {/* Commission + P&L row */}
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Commission</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    {...register('commission', { valueAsNumber: true })}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-fg-muted mb-1">Realized P&L</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    {...register('realized_pnl', { valueAsNumber: true })}
                                    className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg"
                                />
                            </div>
                        </div>

                        {/* Notes */}
                        <div>
                            <label className="block text-xs text-fg-muted mb-1">Notes</label>
                            <textarea
                                {...register('notes')}
                                rows={3}
                                className="w-full px-3 py-1.5 text-sm rounded-md bg-bg border border-bg-subtle text-fg resize-y"
                            />
                        </div>

                        {/* Buttons */}
                        <div className="flex gap-2 pt-2">
                            <button
                                type="submit"
                                data-testid="trade-submit-btn"
                                className="px-4 py-1.5 text-sm rounded-md bg-accent text-accent-fg hover:bg-accent/90 border border-accent"
                            >
                                Save
                            </button>
                            {trade.exec_id !== '(new)' && (
                                <button
                                    type="button"
                                    onClick={() => trade && onDelete?.(trade.exec_id)}
                                    className="px-4 py-1.5 text-sm rounded-md bg-red-900/30 text-red-400 hover:bg-red-900/50 border border-red-900/50"
                                >
                                    Delete
                                </button>
                            )}
                            <button
                                type="button"
                                data-testid="trade-cancel-btn"
                                onClick={onClose}
                                className="px-4 py-1.5 text-sm rounded-md bg-bg text-fg-muted hover:text-fg border border-bg-subtle"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                )}

                {activeTab === 'journal' && <TradeReportForm trade={trade} onClose={onClose} />}

                {activeTab === 'screenshots' && (
                    <div>
                        <ScreenshotPanel tradeId={trade.exec_id} />
                        <div className="flex gap-2 pt-4">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-1.5 text-sm rounded-md bg-bg text-fg-muted hover:text-fg border border-bg-subtle"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
