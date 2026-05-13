# packages/core/src/zorivest_core/domain/tax/ytd_pnl.py
"""Pure domain function for YTD P&L by symbol.

MEU-129: Computes year-to-date profit/loss breakdown by ticker symbol,
aggregating closed tax lots into per-symbol ST/LT gains.

Source: domain-model-reference.md A5
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.tax.gains_calculator import calculate_realized_gain


@dataclass(frozen=True)
class SymbolPnl:
    """Per-symbol P&L aggregation.

    AC-129.2: Contains ticker, st_gains, lt_gains, total_gains, lot_count.
    """

    ticker: str
    st_gains: Decimal
    lt_gains: Decimal
    total_gains: Decimal
    lot_count: int


@dataclass(frozen=True)
class YtdPnlResult:
    """Year-to-date P&L result with per-symbol breakdown and totals.

    AC-129.1: Contains by_symbol list, total_st_gains, total_lt_gains, total_gains.
    """

    by_symbol: list[SymbolPnl]
    total_st_gains: Decimal
    total_lt_gains: Decimal
    total_gains: Decimal


def compute_ytd_pnl(
    lots: list[TaxLot],
    tax_year: int,
) -> YtdPnlResult:
    """Compute YTD P&L by symbol for a given tax year.

    AC-129.3: Only lots with close_date in the specified tax_year are included.
    AC-129.5: Multiple lots for the same ticker are aggregated into one SymbolPnl.

    Args:
        lots: All closed tax lots (pre-filtered or not).
        tax_year: The year to compute P&L for.

    Returns:
        YtdPnlResult with per-symbol breakdown and totals.
    """
    # AC-129.3: Filter to lots closed in the target year
    year_lots = [
        lot
        for lot in lots
        if lot.close_date is not None and lot.close_date.year == tax_year
    ]

    # AC-129.5: Aggregate by ticker
    st_by_ticker: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    lt_by_ticker: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    count_by_ticker: dict[str, int] = defaultdict(int)

    for lot in year_lots:
        gain_result = calculate_realized_gain(lot, lot.proceeds)
        if gain_result.is_long_term:
            lt_by_ticker[lot.ticker] += gain_result.gain_amount
        else:
            st_by_ticker[lot.ticker] += gain_result.gain_amount
        count_by_ticker[lot.ticker] += 1

    # Build per-symbol entries
    all_tickers = sorted(
        set(st_by_ticker.keys())
        | set(lt_by_ticker.keys())
        | set(count_by_ticker.keys())
    )

    by_symbol: list[SymbolPnl] = []
    total_st = Decimal("0")
    total_lt = Decimal("0")

    for ticker in all_tickers:
        st_g = st_by_ticker.get(ticker, Decimal("0"))
        lt_g = lt_by_ticker.get(ticker, Decimal("0"))
        total_g = st_g + lt_g
        by_symbol.append(
            SymbolPnl(
                ticker=ticker,
                st_gains=st_g,
                lt_gains=lt_g,
                total_gains=total_g,
                lot_count=count_by_ticker.get(ticker, 0),
            )
        )
        total_st += st_g
        total_lt += lt_g

    return YtdPnlResult(
        by_symbol=by_symbol,
        total_st_gains=total_st,
        total_lt_gains=total_lt,
        total_gains=total_st + total_lt,
    )
