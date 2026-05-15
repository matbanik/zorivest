/**
 * WashSaleMonitor — chain list + detail split pane.
 *
 * Fetches GET /api/v1/tax/wash-sales and renders list/detail.
 *
 * Source: 06g-gui-tax.md L160–186
 * MEU: MEU-154 (AC-154.9)
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'

interface WashSaleChain {
    chain_id: string
    ticker: string
    adjustment_amount: number
    trade_count: number
    first_trade_date: string
    last_trade_date: string
    status: 'active' | 'resolved'
    trades: WashSaleTrade[]
}

interface WashSaleTrade {
    exec_id: string
    date: string
    action: string
    quantity: number
    price: number
    wash_amount: number
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
        <div data-testid={TAX_TEST_IDS.WASH_SALE_MONITOR} className="flex h-full gap-4">
            {/* Left — Chain List */}
            <div className="w-[320px] shrink-0 space-y-2 overflow-y-auto">
                <h3 className="text-xs text-fg-muted uppercase tracking-wider mb-2">
                    Wash Sale Chains ({chains.length})
                </h3>
                {isLoading ? (
                    <div className="text-sm text-fg-muted">Loading…</div>
                ) : chains.length === 0 ? (
                    <div className="text-sm text-fg-muted">No wash sales detected</div>
                ) : (
                    chains.map((chain) => (
                        <button
                            key={chain.chain_id}
                            data-testid={TAX_TEST_IDS.WASH_SALE_CHAIN}
                            onClick={() => setSelectedChain(chain)}
                            className={`w-full text-left p-3 rounded-lg border transition-colors cursor-pointer ${
                                selectedChain?.chain_id === chain.chain_id
                                    ? 'bg-bg-elevated border-accent/30'
                                    : 'bg-bg border-bg-subtle hover:bg-bg-elevated'
                            }`}
                        >
                            <div className="flex items-center justify-between">
                                <span className="font-mono text-fg font-medium">{chain.ticker}</span>
                                <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    chain.status === 'active'
                                        ? 'bg-red-500/10 text-red-400'
                                        : 'bg-green-500/10 text-green-400'
                                }`}>
                                    {chain.status}
                                </span>
                            </div>
                            <div className="text-xs text-fg-muted mt-1">
                                {chain.trade_count} trades · ${Math.abs(chain.adjustment_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })} adj
                            </div>
                        </button>
                    ))
                )}
            </div>

            {/* Right — Chain Detail */}
            <div className="flex-1 min-w-0">
                {selectedChain ? (
                    <div data-testid={TAX_TEST_IDS.WASH_SALE_CHAIN_DETAIL} className="bg-bg-elevated rounded-lg border border-bg-subtle p-4 space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-fg font-mono">
                                {selectedChain.ticker}
                            </h3>
                            <span className={`text-sm px-3 py-1 rounded-full ${
                                selectedChain.status === 'active'
                                    ? 'bg-red-500/10 text-red-400'
                                    : 'bg-green-500/10 text-green-400'
                            }`}>
                                {selectedChain.status}
                            </span>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                                <span className="block text-xs text-fg-muted">Adjustment</span>
                                <span className="font-mono text-red-400">
                                    ${Math.abs(selectedChain.adjustment_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">Period</span>
                                <span className="text-fg">
                                    {selectedChain.first_trade_date} → {selectedChain.last_trade_date}
                                </span>
                            </div>
                            <div>
                                <span className="block text-xs text-fg-muted">Trades</span>
                                <span className="text-fg">{selectedChain.trade_count}</span>
                            </div>
                        </div>

                        {/* Trade list */}
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-bg-subtle">
                                    <th className="text-left px-3 py-2 text-fg-muted font-medium">Date</th>
                                    <th className="text-left px-3 py-2 text-fg-muted font-medium">Action</th>
                                    <th className="text-right px-3 py-2 text-fg-muted font-medium">Qty</th>
                                    <th className="text-right px-3 py-2 text-fg-muted font-medium">Price</th>
                                    <th className="text-right px-3 py-2 text-fg-muted font-medium">Wash Adj</th>
                                </tr>
                            </thead>
                            <tbody>
                                {selectedChain.trades.map((trade) => (
                                    <tr key={trade.exec_id} className="border-b border-bg-subtle/50">
                                        <td className="px-3 py-2 text-fg">{trade.date}</td>
                                        <td className="px-3 py-2">
                                            <span className={trade.action === 'BOT' ? 'text-green-400' : 'text-red-400'}>
                                                {trade.action}
                                            </span>
                                        </td>
                                        <td className="px-3 py-2 text-right font-mono text-fg">{trade.quantity}</td>
                                        <td className="px-3 py-2 text-right font-mono text-fg">
                                            ${trade.price.toFixed(2)}
                                        </td>
                                        <td className="px-3 py-2 text-right font-mono text-red-400">
                                            ${trade.wash_amount.toFixed(2)}
                                        </td>
                                    </tr>
                                ))}
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
    )
}
