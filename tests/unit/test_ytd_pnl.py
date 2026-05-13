# tests/unit/test_ytd_pnl.py
"""FIC tests for MEU-129: YTD P&L by Symbol.

Feature Intent Contract:
  compute_ytd_pnl(lots, tax_year) → YtdPnlResult

Acceptance Criteria:
  AC-129.1: Returns YtdPnlResult with per-symbol breakdown and totals
  AC-129.2: SymbolPnl has ticker, st_gains, lt_gains, total_gains, lot_count
  AC-129.3: Only lots with close_date in specified tax_year
  AC-129.5: Multiple lots for same ticker aggregated

Source: domain-model-reference.md A5
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.tax.ytd_pnl import (
    YtdPnlResult,
    compute_ytd_pnl,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _closed_lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    cost_basis: Decimal = Decimal("100.00"),
    proceeds: Decimal = Decimal("150.00"),
    quantity: float = 100.0,
    open_date: datetime | None = None,
    close_date: datetime | None = None,
) -> TaxLot:
    od = open_date or datetime(2023, 1, 15, tzinfo=timezone.utc)
    cd = close_date or datetime(2026, 6, 1, tzinfo=timezone.utc)
    return TaxLot(
        lot_id=lot_id,
        account_id="ACC-1",
        ticker=ticker,
        open_date=od,
        close_date=cd,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=Decimal("0"),
        is_closed=True,
        linked_trade_ids=[],
        realized_gain_loss=(proceeds - cost_basis) * Decimal(str(quantity)),
    )


# ── AC-129.1: compute_ytd_pnl return type ──────────────────────────────


class TestComputeYtdPnlReturnType:
    """AC-129.1: Returns YtdPnlResult with per-symbol breakdown and totals."""

    def test_returns_ytd_pnl_result(self) -> None:
        lots = [_closed_lot()]
        result = compute_ytd_pnl(lots, 2026)
        assert isinstance(result, YtdPnlResult)

    def test_result_has_breakdown_and_totals(self) -> None:
        lots = [_closed_lot()]
        result = compute_ytd_pnl(lots, 2026)
        assert hasattr(result, "by_symbol")
        assert hasattr(result, "total_st_gains")
        assert hasattr(result, "total_lt_gains")
        assert hasattr(result, "total_gains")

    def test_empty_lot_list_returns_zero_totals(self) -> None:
        """AC-129.1 negative: Empty lot list returns zero totals."""
        result = compute_ytd_pnl([], 2026)
        assert result.total_st_gains == Decimal("0")
        assert result.total_lt_gains == Decimal("0")
        assert result.total_gains == Decimal("0")
        assert len(result.by_symbol) == 0


# ── AC-129.2: SymbolPnl fields ─────────────────────────────────────────


class TestSymbolPnlFields:
    """AC-129.2: SymbolPnl has ticker, st_gains, lt_gains, total_gains, lot_count."""

    def test_symbol_pnl_fields(self) -> None:
        lots = [
            _closed_lot(
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),  # LT
                close_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            )
        ]
        result = compute_ytd_pnl(lots, 2026)
        assert len(result.by_symbol) == 1
        entry = result.by_symbol[0]
        assert entry.ticker == "AAPL"
        assert entry.lt_gains == Decimal("5000.00")
        assert entry.st_gains == Decimal("0")
        assert entry.total_gains == Decimal("5000.00")
        assert entry.lot_count == 1


# ── AC-129.3: Year filtering ───────────────────────────────────────────


class TestYearFiltering:
    """AC-129.3: Only lots with close_date in specified tax_year included."""

    def test_lot_in_year_included(self) -> None:
        lot = _closed_lot(close_date=datetime(2026, 3, 15, tzinfo=timezone.utc))
        result = compute_ytd_pnl([lot], 2026)
        assert len(result.by_symbol) == 1

    def test_lot_in_different_year_excluded(self) -> None:
        lot = _closed_lot(close_date=datetime(2025, 12, 31, tzinfo=timezone.utc))
        result = compute_ytd_pnl([lot], 2026)
        assert len(result.by_symbol) == 0
        assert result.total_gains == Decimal("0")

    def test_mixed_years_filtered(self) -> None:
        """Only lots closed in target year contribute."""
        lots = [
            _closed_lot("L1", close_date=datetime(2026, 1, 10, tzinfo=timezone.utc)),
            _closed_lot("L2", close_date=datetime(2025, 11, 30, tzinfo=timezone.utc)),
            _closed_lot("L3", close_date=datetime(2026, 6, 15, tzinfo=timezone.utc)),
        ]
        result = compute_ytd_pnl(lots, 2026)
        # Only L1 and L3 count
        assert result.by_symbol[0].lot_count == 2  # Both AAPL


# ── AC-129.5: Ticker aggregation ───────────────────────────────────────


class TestTickerAggregation:
    """AC-129.5: Multiple lots for same ticker aggregated into single SymbolPnl."""

    def test_two_aapl_lots_produce_one_entry(self) -> None:
        lots = [
            _closed_lot(
                "L1",
                ticker="AAPL",
                cost_basis=Decimal("100.00"),
                proceeds=Decimal("150.00"),
                quantity=50.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
            _closed_lot(
                "L2",
                ticker="AAPL",
                cost_basis=Decimal("120.00"),
                proceeds=Decimal("160.00"),
                quantity=30.0,
                open_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
            ),
        ]
        result = compute_ytd_pnl(lots, 2026)
        assert len(result.by_symbol) == 1
        entry = result.by_symbol[0]
        assert entry.ticker == "AAPL"
        assert entry.lot_count == 2
        # L1: (150-100)*50 = 2500 LT, L2: (160-120)*30 = 1200 LT
        assert entry.lt_gains == Decimal("3700.00")

    def test_different_tickers_separate_entries(self) -> None:
        lots = [
            _closed_lot(
                "L1", ticker="AAPL", open_date=datetime(2023, 1, 1, tzinfo=timezone.utc)
            ),
            _closed_lot(
                "L2", ticker="MSFT", open_date=datetime(2023, 1, 1, tzinfo=timezone.utc)
            ),
        ]
        result = compute_ytd_pnl(lots, 2026)
        tickers = {e.ticker for e in result.by_symbol}
        assert tickers == {"AAPL", "MSFT"}

    def test_st_and_lt_lots_aggregated_separately(self) -> None:
        """Same ticker, mixed ST/LT holding periods."""
        lots = [
            _closed_lot(
                "L1",
                ticker="AAPL",
                cost_basis=Decimal("100.00"),
                proceeds=Decimal("150.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),  # LT
            _closed_lot(
                "L2",
                ticker="AAPL",
                cost_basis=Decimal("140.00"),
                proceeds=Decimal("150.00"),
                quantity=100.0,
                open_date=datetime(2025, 12, 1, tzinfo=timezone.utc),
            ),  # ST
        ]
        result = compute_ytd_pnl(lots, 2026)
        assert len(result.by_symbol) == 1
        entry = result.by_symbol[0]
        # L1 LT: (150-100)*100 = 5000, L2 ST: (150-140)*100 = 1000
        assert entry.lt_gains == Decimal("5000.00")
        assert entry.st_gains == Decimal("1000.00")
        assert entry.total_gains == Decimal("6000.00")

    def test_loss_aggregated_correctly(self) -> None:
        """Losses aggregate as negative values."""
        lots = [
            _closed_lot(
                "L1",
                ticker="AAPL",
                cost_basis=Decimal("200.00"),
                proceeds=Decimal("150.00"),
                quantity=100.0,
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),  # LT loss
        ]
        result = compute_ytd_pnl(lots, 2026)
        entry = result.by_symbol[0]
        # (150-200)*100 = -5000
        assert entry.lt_gains == Decimal("-5000.00")
        assert entry.total_gains == Decimal("-5000.00")
