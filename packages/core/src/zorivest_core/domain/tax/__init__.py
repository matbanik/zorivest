# packages/core/src/zorivest_core/domain/tax/__init__.py
"""Tax domain module — lot selection, gains calculation, loss carryforward, option pairing, YTD P&L, wash sales, brackets, NIIT, quarterly, optimization tools."""

from zorivest_core.domain.tax.brackets import (
    PENALTY_RATES,
    SUPPORTED_YEARS,
    compute_capital_gains_tax,
    compute_combined_rate,
    compute_effective_rate,
    compute_marginal_rate,
    compute_tax_liability,
)
from zorivest_core.domain.tax.niit import (
    NIIT_RATE,
    NIIT_THRESHOLDS,
    NiitProximityResult,
    NiitResult,
    check_niit_proximity,
    compute_niit,
)
from zorivest_core.domain.tax.gains_calculator import (
    RealizedGainResult,
    calculate_realized_gain,
)
from zorivest_core.domain.tax.loss_carryforward import (
    CapitalLossResult,
    apply_capital_loss_rules,
)
from zorivest_core.domain.tax.lot_selector import select_lots_for_closing
from zorivest_core.domain.tax.option_pairing import (
    AdjustedBasisResult,
    AssignmentType,
    OptionDetails,
    adjust_basis_for_assignment,
    parse_option_symbol,
)
from zorivest_core.domain.tax.wash_sale import (
    WashSaleChain,
    WashSaleEntry,
)
from zorivest_core.domain.tax.wash_sale_chain_manager import WashSaleChainManager
from zorivest_core.domain.tax.wash_sale_detector import (
    WashSaleMatch,
    detect_wash_sales,
)
from zorivest_core.domain.tax.ytd_pnl import (
    SymbolPnl,
    YtdPnlResult,
    compute_ytd_pnl,
)
from zorivest_core.domain.tax.quarterly import (
    ANNUALIZATION_FACTORS,
    AnnualizedInstallmentResult,
    QuarterlyDueDate,
    SafeHarborResult,
    YtdQuarterlySummary,
    compute_annualized_installment,
    compute_safe_harbor,
    compute_underpayment_penalty,
    get_quarterly_due_dates,
    quarterly_ytd_summary,
)

# Phase 3C: Tax Optimization Tools (MEU-137–142)
from zorivest_core.domain.tax.harvest_scanner import (
    HarvestCandidate,
    HarvestScanResult,
    scan_harvest_candidates,
)
from zorivest_core.domain.tax.lot_matcher import (
    LotDetail,
    get_lot_details,
    preview_lot_selection,
)
from zorivest_core.domain.tax.lot_reassignment import (
    SETTLEMENT_DAYS,
    ReassignmentEligibility,
    can_reassign_lots,
    reassign_lots,
)
from zorivest_core.domain.tax.rate_comparison import (
    StLtComparison,
    compare_st_lt_tax,
)
from zorivest_core.domain.tax.replacement_suggestions import (
    REPLACEMENT_TABLE,
    ReplacementSuggestion,
    suggest_replacements,
    suggest_replacements_for_harvest,
)
from zorivest_core.domain.tax.tax_simulator import (
    TaxImpactResult,
    simulate_tax_impact,
)

__all__ = [
    "ANNUALIZATION_FACTORS",
    "AdjustedBasisResult",
    "AnnualizedInstallmentResult",
    "AssignmentType",
    "CapitalLossResult",
    "HarvestCandidate",
    "HarvestScanResult",
    "LotDetail",
    "NIIT_RATE",
    "NIIT_THRESHOLDS",
    "NiitProximityResult",
    "NiitResult",
    "OptionDetails",
    "PENALTY_RATES",
    "QuarterlyDueDate",
    "REPLACEMENT_TABLE",
    "RealizedGainResult",
    "ReassignmentEligibility",
    "ReplacementSuggestion",
    "SETTLEMENT_DAYS",
    "SUPPORTED_YEARS",
    "SafeHarborResult",
    "StLtComparison",
    "SymbolPnl",
    "TaxImpactResult",
    "WashSaleChain",
    "WashSaleChainManager",
    "WashSaleEntry",
    "WashSaleMatch",
    "YtdPnlResult",
    "YtdQuarterlySummary",
    "adjust_basis_for_assignment",
    "apply_capital_loss_rules",
    "calculate_realized_gain",
    "can_reassign_lots",
    "check_niit_proximity",
    "compare_st_lt_tax",
    "compute_annualized_installment",
    "compute_capital_gains_tax",
    "compute_combined_rate",
    "compute_effective_rate",
    "compute_marginal_rate",
    "compute_niit",
    "compute_safe_harbor",
    "compute_tax_liability",
    "compute_underpayment_penalty",
    "compute_ytd_pnl",
    "detect_wash_sales",
    "get_lot_details",
    "get_quarterly_due_dates",
    "parse_option_symbol",
    "preview_lot_selection",
    "quarterly_ytd_summary",
    "reassign_lots",
    "scan_harvest_candidates",
    "select_lots_for_closing",
    "simulate_tax_impact",
    "suggest_replacements",
    "suggest_replacements_for_harvest",
]
