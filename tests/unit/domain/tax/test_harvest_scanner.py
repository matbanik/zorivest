# tests/unit/domain/tax/test_harvest_scanner.py
"""FIC tests for harvest_scanner — MEU-138 ACs 138.1–138.9.

Feature Intent Contract:
  HarvestCandidate / HarvestScanResult frozen dataclasses.
  scan_harvest_candidates(open_lots, current_prices, tax_profile, all_lots) —
    scans for tax-loss harvesting opportunities, filters wash-sale-blocked,
    ranks by harvestable loss.

All tests are pure domain — no mocks, no I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal


from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.enums import (
    CostBasisMethod,
    FilingStatus,
    WashSaleMatchingMethod,
)

from zorivest_core.domain.tax.harvest_scanner import (
    HarvestScanResult,
    scan_harvest_candidates,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _lot(
    lot_id: str = "L1",
    ticker: str = "AAPL",
    open_date: datetime | None = None,
    quantity: float = 100.0,
    cost_basis: Decimal = Decimal("100.00"),
    wash_sale_adjustment: Decimal = Decimal("0.00"),
    is_closed: bool = False,
    close_date: datetime | None = None,
) -> TaxLot:
    return TaxLot(
        lot_id=lot_id,
        account_id="ACC-1",
        ticker=ticker,
        open_date=open_date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        close_date=close_date,
        quantity=quantity,
        cost_basis=cost_basis,
        proceeds=Decimal("0.00"),
        wash_sale_adjustment=wash_sale_adjustment,
        is_closed=is_closed,
        linked_trade_ids=[],
    )


def _profile(
    wash_sale_method: WashSaleMatchingMethod = WashSaleMatchingMethod.CONSERVATIVE,
) -> TaxProfile:
    return TaxProfile(
        id=1,
        filing_status=FilingStatus.SINGLE,
        tax_year=2026,
        federal_bracket=0.22,
        state_tax_rate=0.0,
        state="TX",
        prior_year_tax=Decimal("0"),
        agi_estimate=Decimal("100000"),
        capital_loss_carryforward=Decimal("0"),
        wash_sale_method=wash_sale_method,
        default_cost_basis=CostBasisMethod.FIFO,
    )


# ── AC-138.1: scan_harvest_candidates basic ──────────────────────────


class TestScanHarvestCandidates:
    """AC-138.1: scan_harvest_candidates returns HarvestScanResult."""

    def test_basic_scan(self) -> None:
        """Open lot with unrealized loss → appears as candidate."""
        lots = [
            _lot("L1", ticker="AAPL", cost_basis=Decimal("150.00"), quantity=100.0),
        ]
        prices = {"AAPL": Decimal("100.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        assert isinstance(result, HarvestScanResult)
        assert len(result.candidates) == 1
        assert result.candidates[0].ticker == "AAPL"
        # loss = (100 - 150) * 100 = -5000 → harvestable = 5000
        assert result.candidates[0].total_harvestable_loss == Decimal("5000.00")

    def test_no_open_lots_empty(self) -> None:
        """AC-138.1 negative: no open lots → empty result."""
        result = scan_harvest_candidates(
            open_lots=[],
            current_prices={},
            tax_profile=_profile(),
            all_lots=[],
        )
        assert result.candidates == []
        assert result.total_harvestable == Decimal("0")


# ── AC-138.4: Only unrealized losses ─────────────────────────────────


class TestOnlyLosses:
    """AC-138.4: Only lots with unrealized loss are included."""

    def test_all_gains_empty(self) -> None:
        """All lots in gain → empty candidates."""
        lots = [
            _lot("L1", ticker="AAPL", cost_basis=Decimal("50.00"), quantity=100.0),
        ]
        prices = {"AAPL": Decimal("100.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        assert result.candidates == []

    def test_mixed_gain_loss(self) -> None:
        """Only loss lots included, gain lots excluded."""
        lots = [
            _lot(
                "L1", ticker="AAPL", cost_basis=Decimal("50.00"), quantity=100.0
            ),  # gain
            _lot(
                "L2", ticker="MSFT", cost_basis=Decimal("200.00"), quantity=50.0
            ),  # loss
        ]
        prices = {"AAPL": Decimal("100.00"), "MSFT": Decimal("150.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        assert len(result.candidates) == 1
        assert result.candidates[0].ticker == "MSFT"


# ── AC-138.6: Ranked by total_harvestable_loss descending ────────────


class TestRanking:
    """AC-138.6: Results ranked by total_harvestable_loss descending."""

    def test_ranking_order(self) -> None:
        lots = [
            _lot(
                "L1", ticker="AAPL", cost_basis=Decimal("120.00"), quantity=100.0
            ),  # loss=2000
            _lot(
                "L2", ticker="MSFT", cost_basis=Decimal("200.00"), quantity=100.0
            ),  # loss=5000
        ]
        prices = {"AAPL": Decimal("100.00"), "MSFT": Decimal("150.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        assert len(result.candidates) == 2
        # MSFT (5000) should come before AAPL (2000)
        assert result.candidates[0].ticker == "MSFT"
        assert result.candidates[1].ticker == "AAPL"


# ── AC-138.9: Missing ticker price → skipped ────────────────────────


class TestMissingPrice:
    """AC-138.9: Missing price → excluded from scan, added to skipped_tickers."""

    def test_missing_price_excluded(self) -> None:
        lots = [
            _lot("L1", ticker="AAPL", cost_basis=Decimal("150.00"), quantity=100.0),
            _lot("L2", ticker="XYZ", cost_basis=Decimal("100.00"), quantity=50.0),
        ]
        prices = {"AAPL": Decimal("100.00")}  # XYZ missing
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        assert "XYZ" in result.skipped_tickers
        # Only AAPL should be in candidates
        tickers = [c.ticker for c in result.candidates]
        assert "AAPL" in tickers
        assert "XYZ" not in tickers


# ── AC-138.3: HarvestScanResult aggregation ──────────────────────────


class TestScanResultAggregation:
    """AC-138.3: HarvestScanResult has total_harvestable, total_blocked."""

    def test_total_harvestable(self) -> None:
        lots = [
            _lot(
                "L1", ticker="AAPL", cost_basis=Decimal("150.00"), quantity=100.0
            ),  # loss=5000
            _lot(
                "L2", ticker="MSFT", cost_basis=Decimal("120.00"), quantity=50.0
            ),  # loss=1000
        ]
        prices = {"AAPL": Decimal("100.00"), "MSFT": Decimal("100.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        # Total: 5000 + 1000 = 6000
        assert result.total_harvestable == Decimal("6000.00")


# ── AC-138.5: Wash sale blocked positions ────────────────────────────


class TestWashSaleBlocked:
    """AC-138.5: Positions that would trigger wash sales are flagged blocked."""

    def test_recent_purchase_blocks(self) -> None:
        """Recent repurchase within 30 days → blocked=True."""
        now = datetime(2026, 5, 14, tzinfo=timezone.utc)
        lots = [
            # Original lot with loss
            _lot(
                "L1",
                ticker="AAPL",
                cost_basis=Decimal("150.00"),
                quantity=100.0,
                open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            # Recent repurchase within 30 days
            _lot(
                "L2",
                ticker="AAPL",
                cost_basis=Decimal("95.00"),
                quantity=50.0,
                open_date=now - timedelta(days=10),
            ),
        ]
        prices = {"AAPL": Decimal("100.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        # AAPL should have wash_sale_blocked=True
        aapl = [c for c in result.candidates if c.ticker == "AAPL"]
        assert len(aapl) == 1
        assert aapl[0].wash_sale_blocked is True
        assert aapl[0].wash_sale_reason != ""


# ── AC-138.7: days_to_clear ─────────────────────────────────────────


class TestDaysToClear:
    """AC-138.7: days_to_clear = days until 30-day window expires."""

    def test_no_conflict_zero_days(self) -> None:
        """No recent sale/purchase → days_to_clear == 0."""
        lots = [
            _lot(
                "L1",
                ticker="AAPL",
                cost_basis=Decimal("150.00"),
                quantity=100.0,
                open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
        ]
        prices = {"AAPL": Decimal("100.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        assert len(result.candidates) == 1
        assert result.candidates[0].days_to_clear == 0


# ── AC-138.8: Respects wash_sale_method ──────────────────────────────


class TestWashSaleMethod:
    """AC-138.8: Scanner respects tax_profile.wash_sale_method."""

    def test_conservative_option_blocks_harvest(self) -> None:
        """CONSERVATIVE: option on same underlying bought recently → blocked."""
        now = datetime.now(tz=timezone.utc)
        loss_lot = _lot(
            "L1",
            ticker="AAPL",
            cost_basis=Decimal("150.00"),
            quantity=100.0,
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        # Option on AAPL underlying, purchased 10 days ago
        option_lot = _lot(
            "L2",
            ticker="AAPL 260620 C 200",
            cost_basis=Decimal("5.00"),
            quantity=10.0,
            open_date=now - timedelta(days=10),
        )
        prices = {"AAPL": Decimal("100.00")}
        profile = _profile(wash_sale_method=WashSaleMatchingMethod.CONSERVATIVE)
        result = scan_harvest_candidates(
            open_lots=[loss_lot],  # only the loss lot is open for harvest
            current_prices=prices,
            tax_profile=profile,
            all_lots=[loss_lot, option_lot],  # option lot in full history
        )
        aapl = [c for c in result.candidates if c.ticker == "AAPL"]
        assert len(aapl) == 1
        assert aapl[0].wash_sale_blocked is True

    def test_aggressive_option_does_not_block(self) -> None:
        """AGGRESSIVE: same option on underlying → NOT blocked (different CUSIP)."""
        now = datetime.now(tz=timezone.utc)
        loss_lot = _lot(
            "L1",
            ticker="AAPL",
            cost_basis=Decimal("150.00"),
            quantity=100.0,
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        option_lot = _lot(
            "L2",
            ticker="AAPL 260620 C 200",
            cost_basis=Decimal("5.00"),
            quantity=10.0,
            open_date=now - timedelta(days=10),
        )
        prices = {"AAPL": Decimal("100.00")}
        profile = _profile(wash_sale_method=WashSaleMatchingMethod.AGGRESSIVE)
        result = scan_harvest_candidates(
            open_lots=[loss_lot],
            current_prices=prices,
            tax_profile=profile,
            all_lots=[loss_lot, option_lot],
        )
        aapl = [c for c in result.candidates if c.ticker == "AAPL"]
        assert len(aapl) == 1
        assert aapl[0].wash_sale_blocked is False


# ── AC-138.2: HarvestCandidate fields ───────────────────────────────


class TestHarvestCandidateFields:
    """AC-138.2: HarvestCandidate has all required fields."""

    def test_all_fields_present(self) -> None:
        lots = [
            _lot("L1", ticker="AAPL", cost_basis=Decimal("150.00"), quantity=100.0),
        ]
        prices = {"AAPL": Decimal("100.00")}
        result = scan_harvest_candidates(
            open_lots=lots,
            current_prices=prices,
            tax_profile=_profile(),
            all_lots=lots,
        )
        c = result.candidates[0]
        assert isinstance(c.ticker, str)
        assert isinstance(c.lots, list)
        assert isinstance(c.total_harvestable_loss, Decimal)
        assert isinstance(c.wash_sale_blocked, bool)
        assert isinstance(c.wash_sale_reason, str)
        assert isinstance(c.days_to_clear, int)
