# tests/unit/test_lot_selector.py
"""FIC tests for lot_selector.py — MEU-125 AC-125.5 through AC-125.11.

Feature Intent Contract:
  select_lots_for_closing(lots, quantity, method, sale_price=None, lot_ids=None)
  - Pure domain function selecting which TaxLots to close for a given sale.
  - Implements all 8 CostBasisMethod algorithms.
  - MAX_* methods use IBKR Tax Optimizer 4-tier priority logic.
  - Returns list of (TaxLot, quantity_to_close) tuples.

Source: implementation-plan.md ACs 125.5–125.11
IBKR: ibkrguides.com/traderworkstation/lot-matching-methods.htm
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.enums import CostBasisMethod
from zorivest_core.domain.tax.lot_selector import select_lots_for_closing


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("100.00"),
    account_id: str = "ACC-1",
) -> TaxLot:
    """Factory for test TaxLot with sensible defaults."""
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=None,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=Decimal("0.00"),
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=False,
        linked_trade_ids=[],
    )


# ── AC-125.6: FIFO ──────────────────────────────────────────────────────


class TestFIFO:
    """FIFO selects oldest lots first."""

    def test_fifo_selects_oldest_first(self) -> None:
        lots = [
            _lot("L1", open_date=datetime(2024, 3, 1, tzinfo=timezone.utc)),
            _lot("L2", open_date=datetime(2024, 1, 1, tzinfo=timezone.utc)),
            _lot("L3", open_date=datetime(2024, 2, 1, tzinfo=timezone.utc)),
        ]
        result = select_lots_for_closing(lots, 100.0, CostBasisMethod.FIFO)
        assert result[0][0].lot_id == "L2"

    def test_fifo_partial_fill(self) -> None:
        lots = [
            _lot(
                "L1", open_date=datetime(2024, 1, 1, tzinfo=timezone.utc), quantity=50.0
            ),
            _lot(
                "L2",
                open_date=datetime(2024, 2, 1, tzinfo=timezone.utc),
                quantity=100.0,
            ),
        ]
        result = select_lots_for_closing(lots, 80.0, CostBasisMethod.FIFO)
        assert len(result) == 2
        assert result[0] == (lots[0], 50.0)  # Full fill of L1
        assert result[1] == (lots[1], 30.0)  # Partial fill of L2

    def test_fifo_exact_fill(self) -> None:
        lots = [_lot("L1", quantity=100.0)]
        result = select_lots_for_closing(lots, 100.0, CostBasisMethod.FIFO)
        assert len(result) == 1
        assert result[0] == (lots[0], 100.0)

    def test_fifo_deterministic_with_equal_dates(self) -> None:
        """When dates are equal, order should be deterministic (by lot_id)."""
        same_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        lots = [
            _lot("L3", open_date=same_date),
            _lot("L1", open_date=same_date),
            _lot("L2", open_date=same_date),
        ]
        result = select_lots_for_closing(lots, 100.0, CostBasisMethod.FIFO)
        # Should pick L1 first (lowest lot_id as tiebreaker)
        assert result[0][0].lot_id == "L1"


# ── AC-125.6: LIFO ──────────────────────────────────────────────────────


class TestLIFO:
    """LIFO selects newest lots first."""

    def test_lifo_selects_newest_first(self) -> None:
        lots = [
            _lot("L1", open_date=datetime(2024, 1, 1, tzinfo=timezone.utc)),
            _lot("L2", open_date=datetime(2024, 3, 1, tzinfo=timezone.utc)),
            _lot("L3", open_date=datetime(2024, 2, 1, tzinfo=timezone.utc)),
        ]
        result = select_lots_for_closing(lots, 100.0, CostBasisMethod.LIFO)
        assert result[0][0].lot_id == "L2"

    def test_lifo_partial_fill(self) -> None:
        lots = [
            _lot(
                "L1",
                open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
                quantity=100.0,
            ),
            _lot(
                "L2", open_date=datetime(2024, 3, 1, tzinfo=timezone.utc), quantity=50.0
            ),
        ]
        result = select_lots_for_closing(lots, 80.0, CostBasisMethod.LIFO)
        assert result[0] == (lots[1], 50.0)  # Full fill of L2 (newest)
        assert result[1] == (lots[0], 30.0)  # Partial fill of L1


# ── AC-125.6: HIFO ──────────────────────────────────────────────────────


class TestHIFO:
    """HIFO selects highest cost basis lots first."""

    def test_hifo_selects_highest_cost_first(self) -> None:
        lots = [
            _lot("L1", cost_basis=Decimal("100.00")),
            _lot("L2", cost_basis=Decimal("150.00")),
            _lot("L3", cost_basis=Decimal("120.00")),
        ]
        result = select_lots_for_closing(lots, 100.0, CostBasisMethod.HIFO)
        assert result[0][0].lot_id == "L2"

    def test_hifo_partial_fill(self) -> None:
        lots = [
            _lot("L1", cost_basis=Decimal("200.00"), quantity=30.0),
            _lot("L2", cost_basis=Decimal("100.00"), quantity=100.0),
        ]
        result = select_lots_for_closing(lots, 50.0, CostBasisMethod.HIFO)
        assert result[0] == (lots[0], 30.0)
        assert result[1] == (lots[1], 20.0)


# ── AC-125.5: Quantity exceeds total open ────────────────────────────────


class TestQuantityValidation:
    """ValueError when quantity exceeds total open lot quantity."""

    def test_quantity_exceeds_raises(self) -> None:
        lots = [_lot("L1", quantity=50.0)]
        with pytest.raises(ValueError, match="exceeds"):
            select_lots_for_closing(lots, 100.0, CostBasisMethod.FIFO)

    def test_empty_lots_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds"):
            select_lots_for_closing([], 1.0, CostBasisMethod.FIFO)


# ── AC-125.11: SPEC_ID ──────────────────────────────────────────────────


class TestSpecID:
    """SPEC_ID requires explicit lot_ids parameter."""

    def test_spec_id_without_lot_ids_raises(self) -> None:
        lots = [_lot("L1")]
        with pytest.raises(ValueError, match="lot_ids"):
            select_lots_for_closing(lots, 100.0, CostBasisMethod.SPEC_ID)

    def test_spec_id_with_empty_lot_ids_raises(self) -> None:
        lots = [_lot("L1")]
        with pytest.raises(ValueError, match="lot_ids"):
            select_lots_for_closing(lots, 100.0, CostBasisMethod.SPEC_ID, lot_ids=[])

    def test_spec_id_selects_specified_lots(self) -> None:
        lots = [
            _lot("L1", quantity=100.0),
            _lot("L2", quantity=100.0),
            _lot("L3", quantity=100.0),
        ]
        result = select_lots_for_closing(
            lots, 200.0, CostBasisMethod.SPEC_ID, lot_ids=["L1", "L3"]
        )
        selected_ids = [r[0].lot_id for r in result]
        assert "L1" in selected_ids
        assert "L3" in selected_ids
        assert "L2" not in selected_ids

    def test_spec_id_unknown_lot_id_raises(self) -> None:
        lots = [_lot("L1", quantity=100.0)]
        with pytest.raises(ValueError, match="not found"):
            select_lots_for_closing(
                lots, 100.0, CostBasisMethod.SPEC_ID, lot_ids=["L99"]
            )


# ── AC-125.7: MAX_LT_GAIN (MLG) 4-tier priority ────────────────────────
#
# IBKR MLG priority:
#   ① Maximize LT gain/share (sell LT lots with lowest cost basis first)
#   ② If no LT gain lots: maximize ST gain/share
#   ③ If no gain lots: minimize ST loss/share
#   ④ If no ST loss lots: minimize LT loss/share


class TestMaxLTGain:
    """MLG — 4-tier IBKR priority."""

    def test_tier1_selects_lt_gain_lots_lowest_basis(self) -> None:
        """Tier 1: LT lots with gain → pick lowest basis (max gain)."""
        sale_price = Decimal("150.00")
        lots = [
            # LT lot, basis 100 → gain 50/share
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # LT lot, basis 120 → gain 30/share
            _lot(
                "L2",
                open_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("120.00"),
            ),
            # ST lot, basis 80 → gain 70/share (bigger gain but ST)
            _lot(
                "L3",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("80.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_LT_GAIN, sale_price=sale_price
        )
        # Should prefer L1 (LT, highest gain = 50/share) over L2 (LT, 30/share)
        assert result[0][0].lot_id == "L1"

    def test_tier2_fallback_to_st_gain(self) -> None:
        """Tier 2: No LT gain lots → pick ST gain lots."""
        sale_price = Decimal("150.00")
        lots = [
            # LT lot with LOSS (basis 200 > sale 150) → no tier 1
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("200.00"),
            ),
            # ST lot with GAIN (basis 100 < sale 150)
            _lot(
                "L2",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_LT_GAIN, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L2"

    def test_tier3_fallback_to_min_st_loss(self) -> None:
        """Tier 3: No gain lots → pick ST loss lots (minimize loss)."""
        sale_price = Decimal("80.00")
        lots = [
            # LT lot, loss of 20/share
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # ST lot, loss of 10/share (smaller loss)
            _lot(
                "L2",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("90.00"),
            ),
            # ST lot, loss of 30/share (bigger loss)
            _lot(
                "L3",
                open_date=datetime(2025, 11, 15, tzinfo=timezone.utc),
                cost_basis=Decimal("110.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_LT_GAIN, sale_price=sale_price
        )
        # Tier 3: minimize ST loss → pick L2 (smallest ST loss: -10)
        assert result[0][0].lot_id == "L2"

    def test_tier4_fallback_to_min_lt_loss(self) -> None:
        """Tier 4: No ST loss lots → pick LT loss lots (minimize loss)."""
        sale_price = Decimal("80.00")
        lots = [
            # LT lot, loss of 20/share
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # LT lot, loss of 40/share
            _lot(
                "L2",
                open_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("120.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_LT_GAIN, sale_price=sale_price
        )
        # Tier 4: minimize LT loss → pick L1 (loss -20, smaller than -40)
        assert result[0][0].lot_id == "L1"

    def test_requires_sale_price(self) -> None:
        lots = [_lot("L1")]
        with pytest.raises(ValueError, match="sale_price"):
            select_lots_for_closing(lots, 100.0, CostBasisMethod.MAX_LT_GAIN)


# ── AC-125.8: MAX_LT_LOSS (MLL) 4-tier priority ────────────────────────
#
# ① Maximize LT loss/share → ② Max ST loss → ③ Min ST gain → ④ Min LT gain


class TestMaxLTLoss:
    """MLL — 4-tier IBKR priority."""

    def test_tier1_selects_lt_loss_lots_highest_basis(self) -> None:
        """Tier 1: LT lots with loss → pick highest basis (max loss)."""
        sale_price = Decimal("80.00")
        lots = [
            # LT, loss -20/share
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # LT, loss -40/share (bigger loss)
            _lot(
                "L2",
                open_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("120.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_LT_LOSS, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L2"

    def test_tier2_fallback_to_st_loss(self) -> None:
        """Tier 2: No LT loss → pick ST loss lots."""
        sale_price = Decimal("80.00")
        lots = [
            # LT with GAIN (basis 50 < sale 80) → no tier 1
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("50.00"),
            ),
            # ST with LOSS (basis 100 > sale 80)
            _lot(
                "L2",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_LT_LOSS, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L2"

    def test_tier3_fallback_to_min_st_gain(self) -> None:
        """Tier 3: No loss lots → pick ST gain (minimize gain)."""
        sale_price = Decimal("150.00")
        lots = [
            # LT with gain 50/share
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # ST with gain 30/share (smaller gain)
            _lot(
                "L2",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("120.00"),
            ),
            # ST with gain 10/share (smallest gain)
            _lot(
                "L3",
                open_date=datetime(2025, 12, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("140.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_LT_LOSS, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L3"

    def test_requires_sale_price(self) -> None:
        lots = [_lot("L1")]
        with pytest.raises(ValueError, match="sale_price"):
            select_lots_for_closing(lots, 100.0, CostBasisMethod.MAX_LT_LOSS)


# ── AC-125.9: MAX_ST_GAIN (MSG) 4-tier priority ────────────────────────
#
# ① Max ST gain → ② Max LT gain → ③ Min LT loss → ④ Min ST loss


class TestMaxSTGain:
    """MSG — 4-tier IBKR priority."""

    def test_tier1_selects_st_gain_lowest_basis(self) -> None:
        """Tier 1: ST lots with gain → pick lowest basis (max gain)."""
        sale_price = Decimal("150.00")
        lots = [
            # ST, gain 50/share
            _lot(
                "L1",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # ST, gain 30/share
            _lot(
                "L2",
                open_date=datetime(2025, 11, 15, tzinfo=timezone.utc),
                cost_basis=Decimal("120.00"),
            ),
            # LT, gain 70/share (bigger but LT → not tier 1)
            _lot(
                "L3",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("80.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_ST_GAIN, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L1"

    def test_tier2_fallback_to_lt_gain(self) -> None:
        """Tier 2: No ST gain → pick LT gain lots."""
        sale_price = Decimal("150.00")
        lots = [
            # ST with LOSS
            _lot(
                "L1",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("200.00"),
            ),
            # LT with GAIN
            _lot(
                "L2",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_ST_GAIN, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L2"

    def test_requires_sale_price(self) -> None:
        lots = [_lot("L1")]
        with pytest.raises(ValueError, match="sale_price"):
            select_lots_for_closing(lots, 100.0, CostBasisMethod.MAX_ST_GAIN)


# ── AC-125.10: MAX_ST_LOSS (MSL) 4-tier priority ───────────────────────
#
# ① Max ST loss → ② Max LT loss → ③ Min LT gain → ④ Min ST gain


class TestMaxSTLoss:
    """MSL — 4-tier IBKR priority."""

    def test_tier1_selects_st_loss_highest_basis(self) -> None:
        """Tier 1: ST lots with loss → pick highest basis (max loss)."""
        sale_price = Decimal("80.00")
        lots = [
            # ST, loss -20/share
            _lot(
                "L1",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # ST, loss -40/share (bigger loss)
            _lot(
                "L2",
                open_date=datetime(2025, 11, 15, tzinfo=timezone.utc),
                cost_basis=Decimal("120.00"),
            ),
            # LT, loss -50/share (bigger but LT → not tier 1)
            _lot(
                "L3",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("130.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_ST_LOSS, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L2"

    def test_tier2_fallback_to_lt_loss(self) -> None:
        """Tier 2: No ST loss → pick LT loss lots."""
        sale_price = Decimal("80.00")
        lots = [
            # ST with GAIN
            _lot(
                "L1",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("50.00"),
            ),
            # LT with LOSS
            _lot(
                "L2",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_ST_LOSS, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L2"

    def test_tier3_fallback_to_min_lt_gain(self) -> None:
        """Tier 3: No loss → pick LT gain (minimize gain)."""
        sale_price = Decimal("150.00")
        lots = [
            # LT gain 50/share
            _lot(
                "L1",
                open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("100.00"),
            ),
            # LT gain 10/share (smallest)
            _lot(
                "L2",
                open_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("140.00"),
            ),
            # ST gain 20/share
            _lot(
                "L3",
                open_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                cost_basis=Decimal("130.00"),
            ),
        ]
        result = select_lots_for_closing(
            lots, 100.0, CostBasisMethod.MAX_ST_LOSS, sale_price=sale_price
        )
        assert result[0][0].lot_id == "L2"

    def test_requires_sale_price(self) -> None:
        lots = [_lot("L1")]
        with pytest.raises(ValueError, match="sale_price"):
            select_lots_for_closing(lots, 100.0, CostBasisMethod.MAX_ST_LOSS)


# ── Cross-cutting: single lot ───────────────────────────────────────────


class TestSingleLot:
    """When only one lot exists, all methods should select it."""

    @pytest.mark.parametrize("method", list(CostBasisMethod))
    def test_single_lot_selected(self, method: CostBasisMethod) -> None:
        lot = _lot(
            "L1",
            quantity=100.0,
            cost_basis=Decimal("100.00"),
            open_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )
        kwargs: dict = {}
        if method in (
            CostBasisMethod.MAX_LT_GAIN,
            CostBasisMethod.MAX_LT_LOSS,
            CostBasisMethod.MAX_ST_GAIN,
            CostBasisMethod.MAX_ST_LOSS,
        ):
            kwargs["sale_price"] = Decimal("150.00")
        if method == CostBasisMethod.SPEC_ID:
            kwargs["lot_ids"] = ["L1"]
        result = select_lots_for_closing([lot], 100.0, method, **kwargs)
        assert len(result) == 1
        assert result[0] == (lot, 100.0)
