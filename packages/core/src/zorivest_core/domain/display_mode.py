# packages/core/src/zorivest_core/domain/display_mode.py
"""MEU-10: Display mode formatting and privacy masking.

Provides formatting functions that respect GUI display privacy toggles
(hide dollars, hide percentages, percent mode).

Source: domain-model-reference.md lines 124–156 (truth table),
        enums.py DisplayModeFlag (built in MEU-2).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class DisplayMode:
    """GUI display privacy state.

    Attributes:
        hide_dollars: When True, all dollar amounts are masked as '••••••'.
        hide_percentages: When True, all percentage values are masked as '••%'.
        percent_mode: When True, dollar values also show % of TotalPortfolioBalance.
    """

    hide_dollars: bool = False
    hide_percentages: bool = False
    percent_mode: bool = False


_DOLLAR_MASK = "••••••"
_PERCENT_MASK = "••%"


def _format_raw_dollar(amount: Decimal) -> str:
    """Format a dollar amount with commas and $ prefix.

    Preserves decimal places if present, otherwise shows integer.
    """
    # Normalize to remove trailing zeros for display
    try:
        # Check if amount has fractional part
        if amount == amount.to_integral_value():
            return f"${amount:,.0f}"
        return f"${amount:,.2f}"
    except InvalidOperation:
        return f"${amount}"


def _compute_percentage(amount: Decimal, total: Decimal) -> str:
    """Compute percentage string or 'N/A%' if total is zero."""
    if total == 0:
        return "N/A%"
    pct = (amount / total) * 100
    return f"{pct:.2f}%"


def format_dollar(
    amount: Decimal,
    mode: DisplayMode,
    total_portfolio: Decimal | None = None,
) -> str:
    """Format a dollar amount respecting display mode privacy toggles.

    Truth table (from domain-model-reference.md lines 149–156):
        $ visible + % visible + % off  → $437,903
        $ visible + % visible + % on   → $437,903 (84.52%)
        $ hidden  + % visible + % on   → •••••• (84.52%)
        $ hidden  + % hidden  + % on   → •••••• (••%)
        $ hidden  + % visible + % off  → ••••••
        $ visible + % hidden  + % on   → $437,903 (••%)

    Args:
        amount: Dollar amount to format.
        mode: Current display mode state.
        total_portfolio: Total portfolio balance for percentage computation.
            Required when percent_mode is True. If None, percentage is omitted.

    Returns:
        Formatted string per the truth table.
    """
    # Dollar part
    dollar_part = _DOLLAR_MASK if mode.hide_dollars else _format_raw_dollar(amount)

    # Percentage part (only if percent_mode is on AND total_portfolio provided)
    if mode.percent_mode and total_portfolio is not None:
        if mode.hide_percentages:
            pct_part = _PERCENT_MASK
        else:
            pct_part = _compute_percentage(amount, total_portfolio)
        return f"{dollar_part} ({pct_part})"

    return dollar_part


def format_percentage(value: Decimal, mode: DisplayMode) -> str:
    """Format a percentage value respecting display mode privacy toggles.

    Args:
        value: Percentage value (e.g., Decimal("84.52") for 84.52%).
        mode: Current display mode state.

    Returns:
        'X.XX%' if visible, '••%' if hidden.
    """
    if mode.hide_percentages:
        return _PERCENT_MASK
    return f"{value:.2f}%"
