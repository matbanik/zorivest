# packages/core/src/zorivest_core/domain/tax/__init__.py
"""Tax domain module — lot selection, gains calculation, loss carryforward, option pairing, YTD P&L."""

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
from zorivest_core.domain.tax.ytd_pnl import (
    SymbolPnl,
    YtdPnlResult,
    compute_ytd_pnl,
)

__all__ = [
    "AdjustedBasisResult",
    "AssignmentType",
    "CapitalLossResult",
    "OptionDetails",
    "RealizedGainResult",
    "SymbolPnl",
    "YtdPnlResult",
    "adjust_basis_for_assignment",
    "apply_capital_loss_rules",
    "calculate_realized_gain",
    "compute_ytd_pnl",
    "parse_option_symbol",
    "select_lots_for_closing",
]
