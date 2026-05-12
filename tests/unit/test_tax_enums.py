# tests/unit/test_tax_enums.py
"""Unit tests for tax-related enums (MEU-123 + MEU-124).

FIC Reference: implementation-plan.md §MEU-123 AC-1, §MEU-124 AC-1/AC-2.
"""

from __future__ import annotations

import pytest


class TestCostBasisMethod:
    """MEU-123 AC-1: CostBasisMethod has exactly 8 values."""

    def test_member_count(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert len(CostBasisMethod) == 8

    def test_fifo_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.FIFO == "FIFO"

    def test_lifo_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.LIFO == "LIFO"

    def test_hifo_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.HIFO == "HIFO"

    def test_spec_id_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.SPEC_ID == "SPEC_ID"

    def test_max_lt_gain_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.MAX_LT_GAIN == "MAX_LT_GAIN"

    def test_max_lt_loss_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.MAX_LT_LOSS == "MAX_LT_LOSS"

    def test_max_st_gain_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.MAX_ST_GAIN == "MAX_ST_GAIN"

    def test_max_st_loss_member(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert CostBasisMethod.MAX_ST_LOSS == "MAX_ST_LOSS"

    def test_str_coercion(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        assert str(CostBasisMethod.FIFO) == "FIFO"

    def test_invalid_value_raises(self) -> None:
        from zorivest_core.domain.enums import CostBasisMethod

        with pytest.raises(ValueError):
            CostBasisMethod("invalid_method")

    def test_is_strenum(self) -> None:
        from enum import StrEnum

        from zorivest_core.domain.enums import CostBasisMethod

        assert issubclass(CostBasisMethod, StrEnum)


class TestFilingStatus:
    """MEU-124 AC-1: FilingStatus has exactly 4 values."""

    def test_member_count(self) -> None:
        from zorivest_core.domain.enums import FilingStatus

        assert len(FilingStatus) == 4

    def test_single_member(self) -> None:
        from zorivest_core.domain.enums import FilingStatus

        assert FilingStatus.SINGLE == "SINGLE"

    def test_married_joint_member(self) -> None:
        from zorivest_core.domain.enums import FilingStatus

        assert FilingStatus.MARRIED_JOINT == "MARRIED_JOINT"

    def test_married_separate_member(self) -> None:
        from zorivest_core.domain.enums import FilingStatus

        assert FilingStatus.MARRIED_SEPARATE == "MARRIED_SEPARATE"

    def test_head_of_household_member(self) -> None:
        from zorivest_core.domain.enums import FilingStatus

        assert FilingStatus.HEAD_OF_HOUSEHOLD == "HEAD_OF_HOUSEHOLD"

    def test_str_coercion(self) -> None:
        from zorivest_core.domain.enums import FilingStatus

        assert str(FilingStatus.SINGLE) == "SINGLE"

    def test_invalid_value_raises(self) -> None:
        from zorivest_core.domain.enums import FilingStatus

        with pytest.raises(ValueError):
            FilingStatus("invalid_status")

    def test_is_strenum(self) -> None:
        from enum import StrEnum

        from zorivest_core.domain.enums import FilingStatus

        assert issubclass(FilingStatus, StrEnum)


class TestWashSaleMatchingMethod:
    """MEU-124 AC-2: WashSaleMatchingMethod has exactly 2 values."""

    def test_member_count(self) -> None:
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        assert len(WashSaleMatchingMethod) == 2

    def test_conservative_member(self) -> None:
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        assert WashSaleMatchingMethod.CONSERVATIVE == "CONSERVATIVE"

    def test_aggressive_member(self) -> None:
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        assert WashSaleMatchingMethod.AGGRESSIVE == "AGGRESSIVE"

    def test_str_coercion(self) -> None:
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        assert str(WashSaleMatchingMethod.CONSERVATIVE) == "CONSERVATIVE"

    def test_invalid_value_raises(self) -> None:
        from zorivest_core.domain.enums import WashSaleMatchingMethod

        with pytest.raises(ValueError):
            WashSaleMatchingMethod("invalid_method")

    def test_is_strenum(self) -> None:
        from enum import StrEnum

        from zorivest_core.domain.enums import WashSaleMatchingMethod

        assert issubclass(WashSaleMatchingMethod, StrEnum)
