# tests/integration/test_tax_repo_integration.py
"""Integration tests for TaxLot and TaxProfile repositories (MEU-123 + MEU-124).

RED phase: These tests import SqlAlchemy repository implementations that
don't exist yet. They should fail with ImportError until Task 7-10.

FIC Reference: implementation-plan.md §MEU-123 AC-5, §MEU-124 AC-4.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from zorivest_core.domain.entities import TaxLot, TaxProfile
from zorivest_core.domain.enums import (
    CostBasisMethod,
    FilingStatus,
    WashSaleMatchingMethod,
)


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def tax_lot_repo(db_session):
    """Create a TaxLot repository backed by the test session."""
    from zorivest_infra.database.tax_repository import SqlTaxLotRepository

    return SqlTaxLotRepository(db_session)


@pytest.fixture()
def tax_profile_repo(db_session):
    """Create a TaxProfile repository backed by the test session."""
    from zorivest_infra.database.tax_repository import SqlTaxProfileRepository

    return SqlTaxProfileRepository(db_session)


# ── Factories ───────────────────────────────────────────────────────────


def _make_lot(
    lot_id: str = "lot-001",
    account_id: str = "acct-001",
    ticker: str = "AAPL",
    **overrides: object,
) -> TaxLot:
    defaults: dict[str, object] = {
        "lot_id": lot_id,
        "account_id": account_id,
        "ticker": ticker,
        "open_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "close_date": None,
        "quantity": 100.0,
        "cost_basis": Decimal("150.00"),
        "proceeds": Decimal("0.00"),
        "wash_sale_adjustment": Decimal("0.00"),
        "is_closed": False,
        "linked_trade_ids": ["exec-001"],
    }
    defaults.update(overrides)
    return TaxLot(**defaults)  # type: ignore[arg-type]


def _make_profile(
    tax_year: int = 2026,
    **overrides: object,
) -> TaxProfile:
    defaults: dict[str, object] = {
        "id": 0,
        "filing_status": FilingStatus.SINGLE,
        "tax_year": tax_year,
        "federal_bracket": 0.37,
        "state_tax_rate": 0.05,
        "state": "NY",
        "prior_year_tax": Decimal("50000.00"),
        "agi_estimate": Decimal("500000.00"),
        "capital_loss_carryforward": Decimal("3000.00"),
        "wash_sale_method": WashSaleMatchingMethod.CONSERVATIVE,
        "default_cost_basis": CostBasisMethod.FIFO,
        "include_drip_wash_detection": True,
        "include_spousal_accounts": False,
        "section_475_elected": False,
        "section_1256_eligible": False,
    }
    defaults.update(overrides)
    return TaxProfile(**defaults)  # type: ignore[arg-type]


# ── TaxLot Repository Tests ────────────────────────────────────────────


class TestTaxLotCRUD:
    """MEU-123 AC-5: CRUD operations for TaxLotRepository."""

    def test_save_and_get(self, tax_lot_repo) -> None:
        lot = _make_lot()
        tax_lot_repo.save(lot)

        fetched = tax_lot_repo.get("lot-001")
        assert fetched is not None
        assert fetched.lot_id == "lot-001"
        assert fetched.ticker == "AAPL"
        assert fetched.cost_basis == Decimal("150.00")

    def test_update(self, tax_lot_repo) -> None:
        lot = _make_lot()
        tax_lot_repo.save(lot)

        lot.quantity = 200.0
        lot.is_closed = True
        lot.close_date = datetime(2025, 7, 1, tzinfo=timezone.utc)
        lot.proceeds = Decimal("175.00")
        tax_lot_repo.update(lot)

        fetched = tax_lot_repo.get("lot-001")
        assert fetched is not None
        assert fetched.quantity == 200.0
        assert fetched.is_closed is True
        assert fetched.proceeds == Decimal("175.00")

    def test_delete(self, tax_lot_repo) -> None:
        lot = _make_lot()
        tax_lot_repo.save(lot)

        tax_lot_repo.delete("lot-001")
        assert tax_lot_repo.get("lot-001") is None

    def test_get_nonexistent_returns_none(self, tax_lot_repo) -> None:
        assert tax_lot_repo.get("nonexistent") is None


class TestTaxLotFiltering:
    """MEU-123 AC-5: list_filtered and count_filtered."""

    def test_list_for_account(self, tax_lot_repo) -> None:
        tax_lot_repo.save(_make_lot(lot_id="lot-a1", account_id="acct-A"))
        tax_lot_repo.save(_make_lot(lot_id="lot-a2", account_id="acct-A"))
        tax_lot_repo.save(_make_lot(lot_id="lot-b1", account_id="acct-B"))

        result = tax_lot_repo.list_for_account("acct-A")
        assert len(result) == 2
        assert all(lot.account_id == "acct-A" for lot in result)

    def test_list_filtered_by_ticker(self, tax_lot_repo) -> None:
        tax_lot_repo.save(_make_lot(lot_id="lot-1", ticker="AAPL"))
        tax_lot_repo.save(_make_lot(lot_id="lot-2", ticker="MSFT"))
        tax_lot_repo.save(_make_lot(lot_id="lot-3", ticker="AAPL"))

        result = tax_lot_repo.list_filtered(ticker="AAPL")
        assert len(result) == 2

    def test_list_filtered_by_is_closed(self, tax_lot_repo) -> None:
        tax_lot_repo.save(_make_lot(lot_id="lot-open", is_closed=False))
        tax_lot_repo.save(
            _make_lot(
                lot_id="lot-closed",
                is_closed=True,
                close_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
            )
        )

        open_lots = tax_lot_repo.list_filtered(is_closed=False)
        assert len(open_lots) == 1
        assert open_lots[0].lot_id == "lot-open"

    def test_count_filtered(self, tax_lot_repo) -> None:
        tax_lot_repo.save(_make_lot(lot_id="lot-1", ticker="AAPL"))
        tax_lot_repo.save(_make_lot(lot_id="lot-2", ticker="MSFT"))

        assert tax_lot_repo.count_filtered(ticker="AAPL") == 1
        assert tax_lot_repo.count_filtered() == 2

    def test_list_filtered_limit_offset(self, tax_lot_repo) -> None:
        for i in range(5):
            tax_lot_repo.save(_make_lot(lot_id=f"lot-{i}"))

        page = tax_lot_repo.list_filtered(limit=2, offset=0)
        assert len(page) == 2


class TestTaxLotLinkedTradeIds:
    """Verify linked_trade_ids round-trip through persistence."""

    def test_linked_trade_ids_roundtrip(self, tax_lot_repo) -> None:
        lot = _make_lot(linked_trade_ids=["exec-001", "exec-002", "exec-003"])
        tax_lot_repo.save(lot)

        fetched = tax_lot_repo.get("lot-001")
        assert fetched is not None
        assert fetched.linked_trade_ids == ["exec-001", "exec-002", "exec-003"]


# ── TaxProfile Repository Tests ────────────────────────────────────────


class TestTaxProfileCRUD:
    """MEU-124 AC-4: CRUD for TaxProfileRepository."""

    def test_save_and_get(self, tax_profile_repo) -> None:
        profile = _make_profile()
        profile_id = tax_profile_repo.save(profile)
        assert profile_id > 0

        fetched = tax_profile_repo.get(profile_id)
        assert fetched is not None
        assert fetched.tax_year == 2026
        assert fetched.filing_status == FilingStatus.SINGLE
        assert fetched.federal_bracket == 0.37

    def test_update(self, tax_profile_repo) -> None:
        profile = _make_profile()
        profile_id = tax_profile_repo.save(profile)

        profile.id = profile_id
        profile.federal_bracket = 0.32
        profile.state = "TX"
        tax_profile_repo.update(profile)

        fetched = tax_profile_repo.get(profile_id)
        assert fetched is not None
        assert fetched.federal_bracket == 0.32
        assert fetched.state == "TX"

    def test_get_for_year(self, tax_profile_repo) -> None:
        tax_profile_repo.save(_make_profile(tax_year=2025))
        tax_profile_repo.save(_make_profile(tax_year=2026))

        result = tax_profile_repo.get_for_year(2025)
        assert result is not None
        assert result.tax_year == 2025

    def test_get_for_year_nonexistent(self, tax_profile_repo) -> None:
        assert tax_profile_repo.get_for_year(9999) is None

    def test_get_nonexistent_returns_none(self, tax_profile_repo) -> None:
        assert tax_profile_repo.get(99999) is None

    def test_decimal_precision(self, tax_profile_repo) -> None:
        """Decimal fields round-trip with precision."""
        profile = _make_profile(
            prior_year_tax=Decimal("123456.78"),
            agi_estimate=Decimal("999999.99"),
            capital_loss_carryforward=Decimal("3000.00"),
        )
        pid = tax_profile_repo.save(profile)

        fetched = tax_profile_repo.get(pid)
        assert fetched is not None
        assert fetched.prior_year_tax == Decimal("123456.78")
        assert fetched.agi_estimate == Decimal("999999.99")


# ── F1 Regression: Computed Properties After Persistence ───────────────


class TestTaxLotComputedAfterRoundTrip:
    """F1: Persisted lots must compute holding_period_days/is_long_term
    without raising TypeError from naive/aware datetime mixing."""

    def test_open_lot_holding_period_after_roundtrip(self, tax_lot_repo) -> None:
        """Save an open lot, fetch it, and call holding_period_days."""
        lot = _make_lot(
            lot_id="lot-f1-open",
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=None,
            is_closed=False,
        )
        tax_lot_repo.save(lot)

        fetched = tax_lot_repo.get("lot-f1-open")
        assert fetched is not None
        # This must not raise TypeError
        days = fetched.holding_period_days
        assert isinstance(days, int)
        assert days > 0

    def test_open_lot_is_long_term_after_roundtrip(self, tax_lot_repo) -> None:
        """Save an open lot opened >366 days ago, fetch, assert is_long_term."""
        lot = _make_lot(
            lot_id="lot-f1-lt",
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=None,
            is_closed=False,
        )
        tax_lot_repo.save(lot)

        fetched = tax_lot_repo.get("lot-f1-lt")
        assert fetched is not None
        assert fetched.is_long_term is True

    def test_closed_lot_holding_period_after_roundtrip(self, tax_lot_repo) -> None:
        """Save a closed lot, fetch it, verify exact holding_period_days."""
        lot = _make_lot(
            lot_id="lot-f1-closed",
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2025, 7, 1, tzinfo=timezone.utc),
            is_closed=True,
        )
        tax_lot_repo.save(lot)

        fetched = tax_lot_repo.get("lot-f1-closed")
        assert fetched is not None
        assert fetched.holding_period_days == 181
        assert fetched.is_long_term is False

    def test_fetched_open_date_is_utc_aware(self, tax_lot_repo) -> None:
        """After round-trip, open_date must have tzinfo=UTC."""
        lot = _make_lot(
            lot_id="lot-f1-tz",
            open_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        tax_lot_repo.save(lot)

        fetched = tax_lot_repo.get("lot-f1-tz")
        assert fetched is not None
        assert fetched.open_date.tzinfo is not None, (
            "open_date must be timezone-aware after persistence round-trip"
        )


# ── F5: UoW Wiring Integration Tests ──────────────────────────────────


class TestUoWTaxWiring:
    """F5: SqlAlchemyUnitOfWork must expose usable tax_lots and tax_profiles."""

    def test_uow_tax_lots_save_and_get(self, engine) -> None:
        """Enter UoW, save a TaxLot via uow.tax_lots, fetch it back."""
        from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

        uow = SqlAlchemyUnitOfWork(engine)
        with uow:
            lot = _make_lot(lot_id="uow-lot-1")
            uow.tax_lots.save(lot)
            uow.commit()

        uow2 = SqlAlchemyUnitOfWork(engine)
        with uow2:
            fetched = uow2.tax_lots.get("uow-lot-1")
            assert fetched is not None
            assert fetched.lot_id == "uow-lot-1"
            assert fetched.ticker == "AAPL"

    def test_uow_tax_profiles_save_and_get(self, engine) -> None:
        """Enter UoW, save a TaxProfile via uow.tax_profiles, fetch it back."""
        from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork

        uow = SqlAlchemyUnitOfWork(engine)
        with uow:
            profile = _make_profile(tax_year=2099)
            pid = uow.tax_profiles.save(profile)
            uow.commit()

        uow2 = SqlAlchemyUnitOfWork(engine)
        with uow2:
            fetched = uow2.tax_profiles.get(pid)
            assert fetched is not None
            assert fetched.tax_year == 2099
