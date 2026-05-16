# tests/unit/test_tax_entities.py
"""Unit tests for TaxLot and TaxProfile entities (MEU-123 + MEU-124).

FIC Reference: implementation-plan.md §MEU-123 AC-2/AC-3/AC-4, §MEU-124 AC-3.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from zorivest_core.domain.entities import TaxLot, TaxProfile


class TestTaxLot:
    """MEU-123 AC-2/AC-3/AC-4: TaxLot entity with 18 stored fields + 2 computed."""

    def _make_lot(self, **overrides: object) -> TaxLot:
        """Factory for TaxLot with valid defaults."""
        from zorivest_core.domain.entities import TaxLot

        defaults: dict[str, object] = {
            "lot_id": "lot-001",
            "account_id": "acct-001",
            "ticker": "AAPL",
            "open_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "close_date": None,
            "quantity": 100.0,
            "cost_basis": Decimal("150.00"),
            "proceeds": Decimal("0.00"),
            "wash_sale_adjustment": Decimal("0.00"),
            "is_closed": False,
            "linked_trade_ids": ["exec-001", "exec-002"],
        }
        defaults.update(overrides)
        return TaxLot(**defaults)  # type: ignore[arg-type]

    def test_construction_all_fields(self) -> None:
        """AC-2: TaxLot can be constructed with all 11 stored fields."""
        lot = self._make_lot()
        assert lot.lot_id == "lot-001"
        assert lot.account_id == "acct-001"
        assert lot.ticker == "AAPL"
        assert lot.quantity == 100.0
        assert lot.cost_basis == Decimal("150.00")
        assert lot.is_closed is False
        assert lot.linked_trade_ids == ["exec-001", "exec-002"]

    def test_stored_field_count(self) -> None:
        """AC-2: TaxLot has exactly 18 stored fields (14 base + 4 provenance)."""
        from zorivest_core.domain.entities import TaxLot
        import dataclasses

        init_fields = [f for f in dataclasses.fields(TaxLot)]
        assert len(init_fields) == 18

    def test_missing_required_field_raises_type_error(self) -> None:
        """AC-2 negative: Missing required field raises TypeError."""
        from zorivest_core.domain.entities import TaxLot

        with pytest.raises(TypeError):
            TaxLot(lot_id="lot-001")  # type: ignore[call-arg]

    def test_holding_period_open_lot(self) -> None:
        """AC-3: Open lot computes holding_period_days from open_date to today."""
        lot = self._make_lot(
            open_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_date=None,
            is_closed=False,
        )
        # Should be a positive integer
        assert lot.holding_period_days > 0

    def test_holding_period_closed_lot(self) -> None:
        """AC-3: Closed lot computes holding_period_days from open to close."""
        lot = self._make_lot(
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2025, 7, 1, tzinfo=timezone.utc),
            is_closed=True,
        )
        # Jan 1 to Jul 1 = 181 days
        assert lot.holding_period_days == 181

    def test_holding_period_future_open_date_returns_zero(self) -> None:
        """AC-3 negative: Open lot with future open_date returns 0."""
        lot = self._make_lot(
            open_date=datetime(2099, 1, 1, tzinfo=timezone.utc),
            close_date=None,
            is_closed=False,
        )
        assert lot.holding_period_days == 0

    def test_is_long_term_365_days_is_false(self) -> None:
        """AC-4: 365 days → is_long_term is False."""
        lot = self._make_lot(
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 1, 1, tzinfo=timezone.utc),  # 365 days
            is_closed=True,
        )
        assert lot.holding_period_days == 365
        assert lot.is_long_term is False

    def test_is_long_term_366_days_is_true(self) -> None:
        """AC-4: 366 days → is_long_term is True."""
        lot = self._make_lot(
            open_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            close_date=datetime(2026, 1, 2, tzinfo=timezone.utc),  # 366 days
            is_closed=True,
        )
        assert lot.holding_period_days == 366
        assert lot.is_long_term is True

    def test_is_mutable_dataclass(self) -> None:
        """TaxLot should be a mutable dataclass (not frozen)."""
        lot = self._make_lot()
        lot.quantity = 200.0  # type: ignore[attr-defined]
        assert lot.quantity == 200.0  # type: ignore[attr-defined]


class TestTaxProfile:
    """MEU-124 AC-3: TaxProfile entity with 14 fields."""

    def _make_profile(self, **overrides: object) -> TaxProfile:
        """Factory for TaxProfile with valid defaults."""
        from zorivest_core.domain.entities import TaxProfile
        from zorivest_core.domain.enums import (
            CostBasisMethod,
            FilingStatus,
            WashSaleMatchingMethod,
        )

        defaults: dict[str, object] = {
            "id": 1,
            "filing_status": FilingStatus.SINGLE,
            "tax_year": 2026,
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

    def test_construction_all_fields(self) -> None:
        """AC-3: TaxProfile can be constructed with all fields."""
        profile = self._make_profile()
        assert profile.tax_year == 2026
        assert profile.state == "NY"
        assert profile.federal_bracket == 0.37

    def test_field_count(self) -> None:
        """AC-3: TaxProfile has exactly 14+1 fields (14 spec + id PK)."""
        from zorivest_core.domain.entities import TaxProfile
        import dataclasses

        # 14 spec fields + 1 PK (id) = 15 total dataclass fields
        all_fields = dataclasses.fields(TaxProfile)
        assert len(all_fields) == 15

    def test_missing_required_field_raises_type_error(self) -> None:
        """AC-3 negative: Missing required field raises TypeError."""
        from zorivest_core.domain.entities import TaxProfile

        with pytest.raises(TypeError):
            TaxProfile(id=1)  # type: ignore[call-arg]

    def test_boolean_defaults(self) -> None:
        """Spec: boolean flags have correct defaults."""
        profile = self._make_profile()
        assert profile.include_drip_wash_detection is True
        assert profile.include_spousal_accounts is False
        assert profile.section_475_elected is False
        assert profile.section_1256_eligible is False

    def test_filing_status_type(self) -> None:
        """Filing status is a FilingStatus enum value."""
        from zorivest_core.domain.enums import FilingStatus

        profile = self._make_profile()
        assert profile.filing_status == FilingStatus.SINGLE

    def test_wash_sale_method_type(self) -> None:
        """Wash sale method is a WashSaleMatchingMethod enum value."""
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        profile = self._make_profile()
        assert profile.wash_sale_method == WashSaleMatchingMethod.CONSERVATIVE

    def test_default_cost_basis_type(self) -> None:
        """Default cost basis is a CostBasisMethod enum value."""
        from zorivest_core.domain.enums import CostBasisMethod

        profile = self._make_profile()
        assert profile.default_cost_basis == CostBasisMethod.FIFO

    def test_is_mutable_dataclass(self) -> None:
        """TaxProfile should be a mutable dataclass (not frozen)."""
        profile = self._make_profile()
        profile.tax_year = 2027  # type: ignore[attr-defined]
        assert profile.tax_year == 2027  # type: ignore[attr-defined]
