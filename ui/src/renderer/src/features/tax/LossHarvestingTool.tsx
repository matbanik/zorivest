/**
 * LossHarvestingTool — harvestable positions table ranked by loss amount.
 *
 * Fetches GET /api/v1/tax/harvest and renders table.
 * API returns { opportunities: [{ticker, disallowed_amount, status}], total_harvestable }
 *
 * Source: 06g-gui-tax.md L345–354
 * MEU: MEU-154 (AC-154.12)
 */

import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { TAX_TEST_IDS } from './test-ids'
import TaxHelpCard from './TaxHelpCard'
import { TAX_HELP } from './tax-help-content'

/** Matches actual API response shape from GET /api/v1/tax/harvest */
interface HarvestOpportunity {
    ticker: string
    disallowed_amount: string   // API returns as string (Decimal serialized)
    status: string              // e.g. "WashSaleStatus.ABSORBED"
}

interface HarvestResponse {
    opportunities: HarvestOpportunity[]
    total_harvestable: string   // API returns as string
}

/** Friendly status label */
function statusLabel(raw: string): { label: string; color: string } {
    const s = raw.replace('WashSaleStatus.', '')
    switch (s) {
        case 'ABSORBED': return { label: 'Absorbed', color: 'text-amber-400 bg-amber-500/10' }
        case 'RELEASED': return { label: 'Released', color: 'text-green-400 bg-green-500/10' }
        case 'DESTROYED': return { label: 'Destroyed', color: 'text-red-400 bg-red-500/10' }
        default: return { label: s, color: 'text-fg-muted bg-bg-subtle' }
    }
}

export default function LossHarvestingTool() {
    const { data, isLoading, error } = useQuery<HarvestResponse>({
        queryKey: ['tax-harvest'],
        queryFn: async () => {
            try {
                const res = await apiFetch('/api/v1/tax/harvest')
                // Normalize: API returns { opportunities[], total_harvestable }
                if (res && Array.isArray(res.opportunities)) return res as HarvestResponse
                if (Array.isArray(res)) return { opportunities: res, total_harvestable: '0.00' }
                return { opportunities: [], total_harvestable: '0.00' }
            } catch {
                return { opportunities: [], total_harvestable: '0.00' }
            }
        },
    })

    const opportunities = data?.opportunities ?? []
    const totalHarvestable = parseFloat(data?.total_harvestable ?? '0')

    if (error) {
        return (
            <div className="flex items-center justify-center h-32 text-red-400 text-sm">
                Failed to load harvest opportunities: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
        )
    }

    return (
        <div data-testid={TAX_TEST_IDS.LOSS_HARVESTING_TOOL} className="space-y-4">
            <TaxHelpCard content={TAX_HELP.harvesting} />
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wide">
                    Tax Loss Harvesting Opportunities
                </h3>
                <span className="text-xs text-fg-muted">
                    {opportunities.length} chain{opportunities.length !== 1 ? 's' : ''} ·{' '}
                    <span className="font-mono text-red-400">
                        ${totalHarvestable.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>{' '}
                    total deferred
                </span>
            </div>

            <div className="bg-bg-elevated rounded-lg border border-bg-subtle overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm" aria-label="Loss harvesting opportunities">
                        <thead>
                            <tr className="border-b border-bg-subtle">
                                <th className="text-left px-4 py-2 text-fg-muted font-medium">Ticker</th>
                                <th className="text-right px-4 py-2 text-fg-muted font-medium">Disallowed Amount</th>
                                <th className="text-center px-4 py-2 text-fg-muted font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading ? (
                                <tr>
                                    <td colSpan={3} className="px-4 py-8 text-center text-fg-muted">
                                        Loading…
                                    </td>
                                </tr>
                            ) : opportunities.length === 0 ? (
                                <tr>
                                    <td colSpan={3} className="px-4 py-8 text-center text-fg-muted">
                                        <span aria-hidden="true">🎉</span> No harvesting opportunities — no deferred wash sale losses
                                    </td>
                                </tr>
                            ) : (
                                opportunities.map((opp, idx) => {
                                    const amount = parseFloat(opp.disallowed_amount ?? '0')
                                    const st = statusLabel(opp.status ?? '')
                                    return (
                                        <tr
                                            key={`${opp.ticker}-${idx}`}
                                            data-testid={TAX_TEST_IDS.HARVEST_OPPORTUNITY_ROW}
                                            className="border-b border-bg-subtle/50 hover:bg-bg-subtle/30"
                                        >
                                            <td className="px-4 py-2 font-mono text-fg font-medium">{opp.ticker}</td>
                                            <td className="px-4 py-2 text-right font-mono text-red-400 font-semibold">
                                                ${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </td>
                                            <td className="px-4 py-2 text-center">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${st.color}`}>
                                                    {st.label}
                                                </span>
                                            </td>
                                        </tr>
                                    )
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
