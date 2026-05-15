/**
 * LossHarvestingTool — harvestable positions table ranked by loss amount.
 *
 * Fetches GET /api/v1/tax/harvest and renders table.
 *
 * Source: 06g-gui-tax.md L345–354
 * MEU: MEU-154 (AC-154.12)
 */

import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'

interface HarvestOpportunity {
    ticker: string
    unrealized_loss: number
    current_price: number
    cost_basis: number
    quantity: number
    holding_days: number
    classification: 'ST' | 'LT'
    wash_sale_risk: boolean
}

export default function LossHarvestingTool() {
    const { data: opportunities = [], isLoading, error } = useQuery<HarvestOpportunity[]>({
        queryKey: ['tax-harvest'],
        queryFn: async () => {
            try {
                const res = await apiFetch('/api/v1/tax/harvest')
                // API returns { opportunities: [...], total_harvestable: "..." }
                if (Array.isArray(res)) return res
                if (res && Array.isArray(res.opportunities)) return res.opportunities
                return []
            } catch {
                return []
            }
        },
    })

    if (error) {
        return (
            <div className="flex items-center justify-center h-32 text-red-400 text-sm">
                Failed to load harvest opportunities: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
        )
    }

    return (
        <div data-testid={TAX_TEST_IDS.LOSS_HARVESTING_TOOL} className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    Tax Loss Harvesting Opportunities
                </h3>
                <span className="text-xs text-fg-muted">
                    {opportunities.length} position{opportunities.length !== 1 ? 's' : ''} with harvestable losses
                </span>
            </div>

            <div className="bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-bg-subtle">
                                <th className="text-left px-4 py-2 text-fg-muted font-medium">Ticker</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Qty</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Cost Basis</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Current</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Unrealized Loss</th>
                                <th className="text-center px-4 py-2 text-fg-muted font-medium">Type</th>
                                <th className="text-center px-4 py-2 text-fg-muted font-medium">Wash Risk</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading ? (
                                <tr>
                                    <td colSpan={7} className="px-4 py-8 text-center text-fg-muted">
                                        Loading…
                                    </td>
                                </tr>
                            ) : opportunities.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-4 py-8 text-center text-fg-muted">
                                        🎉 No harvesting opportunities — all positions are in the green
                                    </td>
                                </tr>
                            ) : (
                                opportunities.map((opp) => (
                                    <tr
                                        key={opp.ticker}
                                        data-testid={TAX_TEST_IDS.HARVEST_OPPORTUNITY_ROW}
                                        className="border-b border-bg-subtle/50 hover:bg-bg-subtle/30"
                                    >
                                        <td className="px-4 py-2 font-mono text-fg font-medium">{opp.ticker}</td>
                                        <td className="px-4 py-2 text-right font-mono text-fg">
                                            {opp.quantity.toLocaleString()}
                                        </td>
                                        <td className="px-4 py-2 text-right font-mono text-fg">
                                            ${opp.cost_basis.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                        </td>
                                        <td className="px-4 py-2 text-right font-mono text-fg">
                                            ${opp.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                        </td>
                                        <td className="px-4 py-2 text-right font-mono text-red-400 font-semibold">
                                            -${Math.abs(opp.unrealized_loss).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                        </td>
                                        <td className="px-4 py-2 text-center">
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                                opp.classification === 'LT'
                                                    ? 'bg-blue-500/10 text-blue-400'
                                                    : 'bg-amber-500/10 text-amber-400'
                                            }`}>
                                                {opp.classification}
                                            </span>
                                        </td>
                                        <td className="px-4 py-2 text-center">
                                            {opp.wash_sale_risk ? (
                                                <span className="text-red-400 text-xs" title="Wash sale risk within 30-day window">
                                                    ⚠️
                                                </span>
                                            ) : (
                                                <span className="text-green-400 text-xs">✓</span>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
