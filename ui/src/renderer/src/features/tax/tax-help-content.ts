/**
 * Structured content definitions for TaxHelpCard — one entry per tab.
 *
 * Content is plain text (no JSX) so it can be maintained, localized,
 * or loaded from a CMS in the future without component changes.
 *
 * MEU: MEU-218i (Tax Help Cards)
 */

export interface TaxHelpContent {
    /** Unique key — matches TAX_TABS slug and localStorage key */
    tabKey: string
    /** "What this shows" — 1-sentence orientation */
    what: string
    /** "Where data comes from" — data source provenance */
    source: string
    /** "How values are calculated" — plain-language formula/logic */
    calculation: string
    /** External learn-more link (IRS pub, etc.) */
    learnMoreUrl: string
    /** Label for the learn-more link */
    learnMoreLabel: string
}

export const TAX_HELP: Record<string, TaxHelpContent> = {
    dashboard: {
        tabKey: 'dashboard',
        what: 'Overview of your tax position — realized gains/losses, estimated liability, and portfolio health at a glance.',
        source: 'Aggregated from Process Tax Lots (trade executions → tax lots), the liability estimator, and your year-to-date summary.',
        calculation: 'Each card pulls from a single API query. Realized P&L = sum of (proceeds − cost basis) across all closed lots. Unrealized gains use current market prices against your open lot cost basis.',
        learnMoreUrl: 'https://www.irs.gov/publications/p550',
        learnMoreLabel: 'IRS Publication 550 — Investment Income and Expenses',
    },
    profiles: {
        tabKey: 'profiles',
        what: 'Your tax configuration per year — filing status, federal/state rates, and cost basis preferences that drive all calculations.',
        source: 'Stored locally in your Zorivest database. You create and maintain these manually.',
        calculation: 'No calculations here — this is your input data. Your federal bracket and state rate flow into the Simulator, Quarterly Tracker, and Loss Harvester automatically.',
        learnMoreUrl: 'https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2026',
        learnMoreLabel: 'IRS Tax Rate Schedules',
    },
    lots: {
        tabKey: 'lots',
        what: 'Individual tax lots generated from your imported trade executions. Each buy creates a lot; each sell closes one or more lots using your cost basis method.',
        source: 'Created by "Process Tax Lots" from your trade execution history. The sync engine matches buys and sells using your configured cost basis method (FIFO, LIFO, HIFO, etc.).',
        calculation: 'Gain/Loss = Proceeds − Cost Basis. Classification: Short-term if held ≤ 365 days, Long-term if held > 365 days. The countdown timer shows days remaining until a short-term lot reclassifies to long-term.',
        learnMoreUrl: 'https://www.irs.gov/publications/p550#en_US_2024_publink100010310',
        learnMoreLabel: 'IRS Publication 550 §4 — Basis of Investment Property',
    },
    'wash-sales': {
        tabKey: 'wash-sales',
        what: 'Detects wash sale violations — when you sell at a loss and repurchase the same or substantially identical security within 30 days (before or after).',
        source: 'Analyzed by the wash sale scanner from your closed tax lots. Chains group related buy/sell events that form a wash sale sequence.',
        calculation: 'Disallowed amount = the loss that cannot be deducted this tax year. It gets added to the cost basis of the replacement shares, deferring (not eliminating) the loss.',
        learnMoreUrl: 'https://www.irs.gov/publications/p550#en_US_2024_publink100010601',
        learnMoreLabel: 'IRS Publication 550 §4 — Wash Sales',
    },
    simulator: {
        tabKey: 'simulator',
        what: '"What-if" tool — preview the tax impact of selling a position before you execute the trade. No actual trades are placed.',
        source: 'Uses your open lots and Tax Profile rates to simulate the sale. The simulation engine runs server-side against your actual lot data.',
        calculation: 'Simulates closing lots using your cost basis method. Applies your federal bracket + state rate to estimate tax owed. Flags wash sale risk if a related purchase occurred within the 30-day window.',
        learnMoreUrl: 'https://www.irs.gov/taxtopics/tc409',
        learnMoreLabel: 'IRS Topic No. 409 — Capital Gains and Losses',
    },
    harvesting: {
        tabKey: 'harvesting',
        what: 'Identifies positions with unrealized losses that could be sold to offset gains — a strategy called "tax-loss harvesting."',
        source: 'Scanned from your open lots where current market value is below cost basis. Positions with wash sale risk are flagged or excluded.',
        calculation: 'Harvestable loss = cost basis − current market value. Only surfaces positions where the potential loss exceeds your configured minimum threshold.',
        learnMoreUrl: 'https://www.irs.gov/taxtopics/tc409',
        learnMoreLabel: 'IRS Topic No. 409 — Capital Gains and Losses',
    },
    quarterly: {
        tabKey: 'quarterly',
        what: 'Tracks quarterly estimated tax payments — what you owe, what you\'ve paid, and when the next payment is due.',
        source: 'Estimated amounts calculated from your Tax Profile (AGI, prior year tax) using IRS safe harbor rules. Paid amounts are recorded manually by you.',
        calculation: 'Uses either the annualized income method or prior-year safe harbor (110% of last year\'s tax ÷ 4). Due dates follow the IRS schedule: Apr 15, Jun 15, Sep 15, Jan 15.',
        learnMoreUrl: 'https://www.irs.gov/forms-pubs/about-form-1040-es',
        learnMoreLabel: 'IRS Form 1040-ES — Estimated Tax for Individuals',
    },
    audit: {
        tabKey: 'audit',
        what: 'Scans your trade and lot data for inconsistencies — missing cost basis, orphaned lots, date mismatches, and other data quality issues.',
        source: 'Analyzes your lot and execution data for structural integrity. Rule-based checks, not AI.',
        calculation: 'Each finding has a severity level (info/warning/error) and a recommendation for how to resolve it. Fix issues to ensure accurate tax calculations.',
        learnMoreUrl: 'https://www.irs.gov/publications/p551',
        learnMoreLabel: 'IRS Publication 551 — Basis of Assets',
    },
}
