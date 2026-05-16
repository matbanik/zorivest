/**
 * WashSaleMonitor — chain list + detail split pane.
 *
 * Fetches POST /api/v1/tax/wash-sales and renders list/detail.
 *
 * Source: 06g-gui-tax.md L160–186
 * MEU: MEU-154 (AC-154.9)
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

interface WashSaleEntry {
    entry_id: string
    chain_id: string
    event_type: string // LOSS_DISALLOWED | BASIS_ADJUSTED | RELEASED | DESTROYED
    lot_id: string
    amount: number
    event_date: string
    account_id: string
}

interface WashSaleChain {
    chain_id: string
    ticker: string
    loss_lot_id: string
    loss_date: string
    loss_amount: number
    disallowed_amount: number
    status: string // ABSORBED | DISALLOWED | RELEASED | DESTROYED
    loss_open_date: string
    entries: WashSaleEntry[]
}

/** Badge color by chain status. */
function statusBadge(status: string): { bg: string; text: string } {
    switch (status) {
        case 'ABSORBED':
            return { bg: 'bg-amber-500/10', text: 'text-amber-400' }
        case 'RELEASED':
            return { bg: 'bg-green-500/10', text: 'text-green-400' }
        case 'DESTROYED':
            return { bg: 'bg-red-500/10', text: 'text-red-400' }
        default:
            return { bg: 'bg-blue-500/10', text: 'text-blue-400' }
    }
}

/** Entry event type display name + color. */
function eventDisplay(eventType: string): { label: string; color: string } {
    switch (eventType) {
        case 'LOSS_DISALLOWED':
            return { label: 'Loss Disallowed', color: 'text-red-400' }
        case 'BASIS_ADJUSTED':
            return { label: 'Basis Adjusted', color: 'text-amber-400' }
        case 'RELEASED':
            return { label: 'Released', color: 'text-green-400' }
        case 'DESTROYED':
            return { label: 'Destroyed', color: 'text-red-400' }
        default:
            return { label: eventType, color: 'text-fg-muted' }
    }
}

function formatDate(iso: string): string {
    try {
        return new Date(iso).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        })
    } catch {
        return iso
    }
}

export default function WashSaleMonitor() {
    const [selectedChain, setSelectedChain] = useState<WashSaleChain | null>(null)

    const { data: chains = [], isLoading, error } = useQuery<WashSaleChain[]>({
        queryKey: ['tax-wash-sales'],
        queryFn: async () => {
            try {
                // API is POST /wash-sales, returns { chains: [...], disallowed_total, affected_tickers }
                const res = await apiFetch('/api/v1/tax/wash-sales', {
                    method: 'POST',
                    body: JSON.stringify({}),
                })
                if (Array.isArray(res)) return res
                if (res && Array.isArray(res.chains)) return res.chains
                return []
            } catch {
                return []
            }
        },
    })

    if (error) {
        return (
            <div className="flex items-center justify-center h-32 text-red-400 text-sm">
                Failed to load wash sales: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
        )
    }

    return (
        <div data-testid={TAX_TEST_IDS.WASH_SALE_MONITOR} className="flex flex-col h-full gap-4">
            <TaxHelpCard content={TAX_HELP['wash-sales']} />
            <div className="flex flex-1 min-h-0 gap-4">
            {/* Left — Chain List */}
            <div className="w-[320px] shrink-0 space-y-2 overflow-y-auto" aria-label="Wash sale chains">
                <h3 className="text-xs text-fg-muted uppercase tracking-wider mb-2">
                    Wash Sale Chains ({chains.length})
                </h3>
                {isLoading ? (
                    <div className="text-sm text-fg-muted">Loading…</div>
                ) : chains.length === 0 ? (
                    <div className="text-sm text-fg-muted">No wash sales detected</div>
                ) : (
                    chains.map((chain) => {
                        const badge = statusBadge(chain.status)
                        return (
                            <button
                                key={chain.chain_id}
                                data-testid={TAX_TEST_IDS.WASH_SALE_CHAIN}
                                onClick={() => setSelectedChain(chain)}
                                aria-current={selectedChain?.chain_id === chain.chain_id ? 'true' : undefined}
                                aria-label={`${chain.ticker} wash sale chain, ${chain.status}, $${Math.abs(chain.disallowed_amount ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })} disallowed`}
                                className={`w-full text-left p-3 rounded-lg border transition-colors cursor-pointer ${
                                    selectedChain?.chain_id === chain.chain_id
                                        ? 'bg-bg-elevated border-accent/30'
                                        : 'bg-bg border-bg-subtle hover:bg-bg-elevated'
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="font-mono text-fg font-medium">{chain.ticker}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${badge.bg} ${badge.text}`}>
                                        {chain.status}
                                    </span>
                                </div>
                                <div className="text-xs text-fg-muted mt-1">
                                    {(chain.entries ?? []).length} entries · ${Math.abs(chain.disallowed_amount ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })} disallowed
                                </div>
                            </button>
                        )
                    })
                )}
            </div>

            {/* Right — Chain Detail */}
            <div className="flex-1 min-w-0" aria-live="polite">
                {selectedChain ? (
                    <div data-testid={TAX_TEST_IDS.WASH_SALE_CHAIN_DETAIL} className="bg-bg-elevated rounded-lg border border-bg-subtle p-4 space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-fg font-mono">
                                {selectedChain.ticker}
                            </h3>
                            {(() => {
                                const badge = statusBadge(selectedChain.status)
                                return (
                                    <span className={`text-sm px-3 py-1 rounded-full ${badge.bg} ${badge.text}`}>
                                        {selectedChain.status}
                                    </span>
                                )
                            })()}
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                                <span className="block text-xs text-fg-muted">Disallowed</span>
                                <span className="font-mono text-red-400">
                                    ${Math.abs(selectedChain.disallowed_amount ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">Loss Date</span>
                                <span className="text-fg">
                                    {formatDate(selectedChain.loss_date)}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">Loss Lot</span>
                                <span className="text-fg font-mono text-xs">{selectedChain.loss_lot_id}</span>
                            </div>
                        </div>

                        {/* Entry list */}
                        <table className="w-full text-sm" aria-label="Wash sale chain entries">
                            <thead>
                                <tr className="border-b border-bg-subtle">
                                    <th className="text-left px-3 py-2 text-fg-muted font-medium">Date</th>
                                    <th className="text-left px-3 py-2 text-fg-muted font-medium">Event</th>
                                    <th className="text-left px-3 py-2 text-fg-muted font-medium">Lot</th>
                                    <th className="text-right px-3 py-2 text-fg-muted font-medium">Amount</th>
                                </tr>
                            </thead>
                            <tbody>
                                {(selectedChain.entries ?? []).map((entry) => {
                                    const ev = eventDisplay(entry.event_type)
                                    return (
                                        <tr key={entry.entry_id} className="border-b border-bg-subtle/50">
                                            <td className="px-3 py-2 text-fg">{formatDate(entry.event_date)}</td>
                                            <td className="px-3 py-2">
                                                <span className={ev.color}>{ev.label}</span>
                                            </td>
                                            <td className="px-3 py-2 font-mono text-xs text-fg-muted">{entry.lot_id}</td>
                                            <td className="px-3 py-2 text-right font-mono text-red-400">
                                                ${(entry.amount ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="flex items-center justify-center h-full text-fg-muted text-sm">
                        Select a wash sale chain to view details
                    </div>
                )}
            </div>
            </div>
        </div>
    )
}
