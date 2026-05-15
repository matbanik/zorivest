# tests/unit/domain/tax/test_wash_sale_detector.py
"""Tests for wash sale detection algorithm (MEU-130 AC-130.5, AC-130.6, AC-130.7)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from zorivest_core.domain.entities import TaxLot
from zorivest_core.domain.tax.wash_sale_detector import WashSaleMatch, detect_wash_sales


def _make_lot(
    lot_id: str,
    ticker: str,
    open_date: datetime,
    close_date: Optional[datetime],
    quantity: float,
    cost_basis: Decimal,
    proceeds: Decimal = Decimal("0.00"),
    account_id: str = "acc-1",
) -> TaxLot:
    """Helper to build TaxLot with sensible defaults."""
    return TaxLot(
        lot_id=lot_id,
        account_id=account_id,
        ticker=ticker,
        open_date=open_date,
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=proceeds,
        wash_sale_adjustment=Decimal("0.00"),
        is_closed=close_date is not None,
    )


LOSS_DATE = datetime(2026, 3, 15, tzinfo=timezone.utc)


# ── AC-130.5: 61-day window detection ───────────────────────────────────


class TestDetectWashSalesWindow:
    """AC-130.5: detect securities purchased within ±30 calendar days."""

    def test_repurchase_within_30_days_after_triggers_match(self) -> None:
        """Buy same ticker 10 days after loss → wash sale."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=10),
            None,
            100,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1
        assert matches[0].replacement_lot_id == "lot-repl"

    def test_repurchase_within_30_days_before_triggers_match(self) -> None:
        """Buy same ticker 10 days before loss → wash sale."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=120),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE - timedelta(days=10),
            None,
            100,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1

    def test_repurchase_exactly_30_days_after_triggers_match(self) -> None:
        """Buy same ticker exactly 30 days after loss → still within window."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=30),
            None,
            100,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1

    def test_repurchase_31_days_after_no_match(self) -> None:
        """Buy same ticker 31 days after loss → outside window, no wash sale."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=31),
            None,
            100,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 0

    def test_no_repurchase_empty_candidates(self) -> None:
        """No candidates → empty match list (negative test)."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        matches = detect_wash_sales(loss_lot, [])
        assert matches == []


# ── AC-130.6: Ticker matching ───────────────────────────────────────────


class TestDetectWashSalesTickerMatch:
    """AC-130.6: same ticker = substantially identical; different → no match."""

    def test_different_ticker_no_match(self) -> None:
        """Buy different ticker within window → NOT a wash sale."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "MSFT",
            LOSS_DATE + timedelta(days=5),
            None,
            100,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 0

    def test_same_ticker_matches(self) -> None:
        """Buy same ticker within window → wash sale detected."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
            None,
            100,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1


# ── AC-130.7: Partial wash sale ─────────────────────────────────────────


class TestDetectWashSalesPartial:
    """AC-130.7: partial quantity → proportional disallowance."""

    def test_partial_repurchase_proportional(self) -> None:
        """Sell 100 at loss, buy 50 back → 50 shares disallowed."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
            None,
            50,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1
        assert matches[0].matched_quantity == 50.0

    def test_full_repurchase_full_disallowance(self) -> None:
        """Sell 100 at loss, buy 100 back → all 100 shares disallowed."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
            None,
            100,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1
        assert matches[0].matched_quantity == 100.0

    def test_excess_repurchase_capped_at_loss_quantity(self) -> None:
        """Sell 100 at loss, buy 200 back → capped at 100 shares disallowed."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
            None,
            200,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1
        assert matches[0].matched_quantity == 100.0

    def test_multiple_replacements_split(self) -> None:
        """Sell 100 at loss, buy 30 then 50 → two matches totaling 80."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        repl1 = _make_lot(
            "lot-r1",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
            None,
            30,
            Decimal("142.00"),
        )
        repl2 = _make_lot(
            "lot-r2",
            "AAPL",
            LOSS_DATE + timedelta(days=10),
            None,
            50,
            Decimal("143.00"),
        )
        matches = detect_wash_sales(loss_lot, [repl1, repl2])
        assert len(matches) == 2
        total_matched = sum(m.matched_quantity for m in matches)
        assert total_matched == 80.0


# ── WashSaleMatch result type ───────────────────────────────────────────


class TestWashSaleMatch:
    """WashSaleMatch holds detection output fields."""

    def test_match_fields(self) -> None:
        match = WashSaleMatch(
            loss_lot_id="lot-loss",
            replacement_lot_id="lot-repl",
            matched_quantity=50.0,
            disallowed_loss=Decimal("500.00"),
        )
        assert match.loss_lot_id == "lot-loss"
        assert match.replacement_lot_id == "lot-repl"
        assert match.matched_quantity == 50.0
        assert match.disallowed_loss == Decimal("500.00")


# ── MEU-134 AC-134.1: AcquisitionSource enum ───────────────────────────


class TestAcquisitionSourceEnum:
    """AC-134.1: AcquisitionSource enum with 7 members."""

    def test_enum_importable(self) -> None:
        """AcquisitionSource can be imported from enums module."""
        from zorivest_core.domain.enums import AcquisitionSource

        assert hasattr(AcquisitionSource, "DRIP")

    def test_enum_has_seven_members(self) -> None:
        """AcquisitionSource has exactly 7 members."""
        from zorivest_core.domain.enums import AcquisitionSource

        assert len(AcquisitionSource) == 7

    def test_enum_values(self) -> None:
        """All 7 members are present with correct string values."""
        from zorivest_core.domain.enums import AcquisitionSource

        expected = {
            "PURCHASE",
            "DRIP",
            "TRANSFER",
            "GIFT",
            "INHERITANCE",
            "EXERCISE",
            "ASSIGNMENT",
        }
        assert {m.name for m in AcquisitionSource} == expected


# ── MEU-134 AC-134.2: TaxLot.acquisition_source field ──────────────────


class TestTaxLotAcquisitionSource:
    """AC-134.2: TaxLot has optional acquisition_source field."""

    def test_taxlot_accepts_acquisition_source(self) -> None:
        """TaxLot can be created with acquisition_source field."""
        from zorivest_core.domain.enums import AcquisitionSource

        lot = _make_lot("lot-1", "AAPL", LOSS_DATE, None, 100, Decimal("150.00"))
        lot.acquisition_source = AcquisitionSource.DRIP
        assert lot.acquisition_source == AcquisitionSource.DRIP

    def test_taxlot_default_acquisition_source_is_none(self) -> None:
        """TaxLot without acquisition_source defaults to None."""
        lot = _make_lot("lot-1", "AAPL", LOSS_DATE, None, 100, Decimal("150.00"))
        assert getattr(lot, "acquisition_source", "MISSING") is None


# ── MEU-134 AC-134.3/134.4: DRIP detection in wash sale detector ───────


class TestDripWashSaleDetection:
    """AC-134.3/134.4: DRIP lot detection in wash sale matching."""

    def _make_drip_lot(
        self,
        lot_id: str,
        ticker: str,
        open_date: datetime,
        quantity: float = 10.0,
        cost_basis: Decimal = Decimal("150.00"),
    ) -> TaxLot:
        """Create a lot with DRIP acquisition source."""
        from zorivest_core.domain.enums import AcquisitionSource

        lot = _make_lot(lot_id, ticker, open_date, None, quantity, cost_basis)
        lot.acquisition_source = AcquisitionSource.DRIP
        return lot

    def test_drip_lot_within_window_triggers_match(self) -> None:
        """AC-134.3: DRIP lot purchased within 61-day window → wash sale match."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        drip_lot = self._make_drip_lot(
            "lot-drip",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
        )
        matches = detect_wash_sales(loss_lot, [drip_lot], include_drip=True)
        assert len(matches) == 1
        assert matches[0].is_drip_triggered is True

    def test_include_drip_false_excludes_drip_lots(self) -> None:
        """AC-134.3 negative: include_drip=False → DRIP lots excluded."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        drip_lot = self._make_drip_lot(
            "lot-drip",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
        )
        matches = detect_wash_sales(loss_lot, [drip_lot], include_drip=False)
        assert len(matches) == 0

    def test_non_drip_purchase_not_drip_triggered(self) -> None:
        """AC-134.4: non-DRIP purchase match → is_drip_triggered=False."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        regular_lot = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
            None,
            50,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(loss_lot, [regular_lot], include_drip=True)
        assert len(matches) == 1
        assert matches[0].is_drip_triggered is False

    def test_mixed_drip_and_regular_lots(self) -> None:
        """DRIP and regular lots both match, with correct is_drip_triggered."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        drip_lot = self._make_drip_lot(
            "lot-drip",
            "AAPL",
            LOSS_DATE + timedelta(days=3),
        )
        regular_lot = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=10),
            None,
            50,
            Decimal("142.00"),
        )
        matches = detect_wash_sales(
            loss_lot, [drip_lot, regular_lot], include_drip=True
        )
        assert len(matches) == 2
        drip_match = next(m for m in matches if m.replacement_lot_id == "lot-drip")
        regular_match = next(m for m in matches if m.replacement_lot_id == "lot-repl")
        assert drip_match.is_drip_triggered is True
        assert regular_match.is_drip_triggered is False

    def test_existing_tests_backward_compatible(self) -> None:
        """Existing calls without include_drip param still work (default=True)."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        replacement = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=10),
            None,
            100,
            Decimal("142.00"),
        )
        # Call without include_drip → should default to True and still work
        matches = detect_wash_sales(loss_lot, [replacement])
        assert len(matches) == 1


# ── MEU-133 AC-133.1–133.4: Options-to-Stock Matching ──────────────────


class TestOptionsToStockWashSaleMatching:
    """AC-133.1–133.4: Options on same underlying match as substantially identical."""

    def _make_option_lot(
        self,
        lot_id: str,
        option_symbol: str,
        open_date: datetime,
        quantity: float = 1.0,
        cost_basis: Decimal = Decimal("5.00"),
    ) -> TaxLot:
        """Create a lot with an option ticker."""
        return _make_lot(
            lot_id,
            option_symbol,
            open_date,
            None,
            quantity,
            cost_basis,
        )

    def test_conservative_option_matches_stock_loss(self) -> None:
        """AC-133.2: CONSERVATIVE mode — AAPL call option matches AAPL stock loss."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        option_lot = self._make_option_lot(
            "lot-opt",
            "AAPL 260420 C 200",
            LOSS_DATE + timedelta(days=5),
        )
        matches = detect_wash_sales(
            loss_lot,
            [option_lot],
            wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
        )
        assert len(matches) == 1
        assert matches[0].replacement_lot_id == "lot-opt"

    def test_conservative_put_option_matches_stock_loss(self) -> None:
        """AC-133.2: CONSERVATIVE mode — AAPL put option also matches."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        option_lot = self._make_option_lot(
            "lot-put",
            "AAPL 260420 P 130",
            LOSS_DATE + timedelta(days=5),
        )
        matches = detect_wash_sales(
            loss_lot,
            [option_lot],
            wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
        )
        assert len(matches) == 1

    def test_aggressive_mode_skips_options(self) -> None:
        """AC-133.3: AGGRESSIVE mode — option on same underlying → no match."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        option_lot = self._make_option_lot(
            "lot-opt",
            "AAPL 260420 C 200",
            LOSS_DATE + timedelta(days=5),
        )
        matches = detect_wash_sales(
            loss_lot,
            [option_lot],
            wash_sale_method=WashSaleMatchingMethod.AGGRESSIVE,
        )
        assert len(matches) == 0

    def test_different_underlying_option_no_match(self) -> None:
        """AC-133.2 negative: option on different underlying → no match."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        option_lot = self._make_option_lot(
            "lot-opt",
            "MSFT 260420 C 200",
            LOSS_DATE + timedelta(days=5),
        )
        matches = detect_wash_sales(
            loss_lot,
            [option_lot],
            wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
        )
        assert len(matches) == 0

    def test_malformed_option_symbol_skipped(self) -> None:
        """AC-133.4: malformed option string → None → skip (no crash)."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        # Not a valid option symbol, and doesn't match "AAPL" exactly
        bad_option_lot = self._make_option_lot(
            "lot-bad",
            "AAPL-GARBLED",
            LOSS_DATE + timedelta(days=5),
        )
        matches = detect_wash_sales(
            loss_lot,
            [bad_option_lot],
            wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE,
        )
        assert len(matches) == 0

    def test_default_wash_sale_method_is_conservative(self) -> None:
        """AC-133.1: default wash_sale_method → CONSERVATIVE (backward compat)."""
        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        option_lot = self._make_option_lot(
            "lot-opt",
            "AAPL 260420 C 200",
            LOSS_DATE + timedelta(days=5),
        )
        # Call without wash_sale_method — default should be CONSERVATIVE
        matches = detect_wash_sales(loss_lot, [option_lot])
        assert len(matches) == 1

    def test_stock_to_stock_unaffected_by_method(self) -> None:
        """Stock-to-stock matching works in both CONSERVATIVE and AGGRESSIVE."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        loss_lot = _make_lot(
            "lot-loss",
            "AAPL",
            LOSS_DATE - timedelta(days=60),
            LOSS_DATE,
            100,
            Decimal("150.00"),
            Decimal("140.00"),
        )
        stock_lot = _make_lot(
            "lot-repl",
            "AAPL",
            LOSS_DATE + timedelta(days=5),
            None,
            100,
            Decimal("142.00"),
        )
        for method in WashSaleMatchingMethod:
            matches = detect_wash_sales(
                loss_lot,
                [stock_lot],
                wash_sale_method=method,
            )
            assert len(matches) == 1, f"Stock match should work for {method}"
