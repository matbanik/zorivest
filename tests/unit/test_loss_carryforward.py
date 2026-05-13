# tests/unit/test_loss_carryforward.py
"""FIC tests for MEU-127: Capital Loss Carryforward Rules.

Feature Intent Contract:
  apply_capital_loss_rules(st_gains, lt_gains, st_carryforward, lt_carryforward, filing_status)
  → CapitalLossResult with deductible_loss, remaining_st_carryforward,
    remaining_lt_carryforward, net_st, net_lt

Acceptance Criteria:
  AC-127.1: Function signature and return type
  AC-127.2: $3,000 cap (SINGLE/MJ/HoH), $1,500 cap (MARRIED_SEPARATE)
  AC-127.3: Netting order per IRS Schedule D Part III + Human-approved ST/LT split

Source: IRS Publication 550, IRS Schedule D instructions
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from zorivest_core.domain.enums import FilingStatus
from zorivest_core.domain.tax.loss_carryforward import (
    CapitalLossResult,
    apply_capital_loss_rules,
)


# ── AC-127.1: Function signature and return type ────────────────────────


class TestApplyCapitalLossRulesSignature:
    """AC-127.1: Function returns CapitalLossResult with correct fields."""

    def test_returns_capital_loss_result(self) -> None:
        """Basic call returns CapitalLossResult dataclass."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("1000"),
            lt_gains=Decimal("2000"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert isinstance(result, CapitalLossResult)

    def test_result_has_all_fields(self) -> None:
        """CapitalLossResult has deductible_loss, remaining carryforwards, net ST/LT."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert hasattr(result, "deductible_loss")
        assert hasattr(result, "remaining_st_carryforward")
        assert hasattr(result, "remaining_lt_carryforward")
        assert hasattr(result, "net_st")
        assert hasattr(result, "net_lt")

    def test_negative_carryforward_rejected(self) -> None:
        """AC-127.1 negative: Negative carryforward raises ValueError."""
        with pytest.raises(ValueError, match="carryforward"):
            apply_capital_loss_rules(
                st_gains=Decimal("0"),
                lt_gains=Decimal("0"),
                st_carryforward=Decimal("-100"),
                lt_carryforward=Decimal("0"),
                filing_status=FilingStatus.SINGLE,
            )

    def test_negative_lt_carryforward_rejected(self) -> None:
        """AC-127.1 negative: Negative LT carryforward raises ValueError."""
        with pytest.raises(ValueError, match="carryforward"):
            apply_capital_loss_rules(
                st_gains=Decimal("0"),
                lt_gains=Decimal("0"),
                st_carryforward=Decimal("0"),
                lt_carryforward=Decimal("-50"),
                filing_status=FilingStatus.SINGLE,
            )


# ── AC-127.2: Annual deduction cap ─────────────────────────────────────


class TestAnnualDeductionCap:
    """AC-127.2: $3,000 cap for SINGLE/MJ/HoH, $1,500 for MARRIED_SEPARATE."""

    def test_cap_3000_single(self) -> None:
        """SINGLE: net loss of $10K → deductible_loss = $3,000."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("10000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.deductible_loss == Decimal("3000")

    def test_cap_3000_married_joint(self) -> None:
        """MARRIED_JOINT: net loss of $10K → deductible_loss = $3,000."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("10000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.MARRIED_JOINT,
        )
        assert result.deductible_loss == Decimal("3000")

    def test_cap_3000_head_of_household(self) -> None:
        """HEAD_OF_HOUSEHOLD: net loss of $10K → deductible_loss = $3,000."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("10000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.HEAD_OF_HOUSEHOLD,
        )
        assert result.deductible_loss == Decimal("3000")

    def test_cap_1500_married_separate(self) -> None:
        """MARRIED_SEPARATE: net loss of $10K → deductible_loss = $1,500."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("10000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.MARRIED_SEPARATE,
        )
        assert result.deductible_loss == Decimal("1500")

    def test_loss_under_cap_fully_deductible(self) -> None:
        """Loss of $2,000 (under $3K cap) → deductible_loss = $2,000."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("2000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.deductible_loss == Decimal("2000")
        assert result.remaining_st_carryforward == Decimal("0")
        assert result.remaining_lt_carryforward == Decimal("0")

    def test_excess_loss_goes_to_carryforward(self) -> None:
        """AC-127.2 negative: Loss beyond cap carried forward."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("5000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.deductible_loss == Decimal("3000")
        # Remaining: 5000 - 3000 = 2000 ST carryforward
        assert result.remaining_st_carryforward == Decimal("2000")


# ── AC-127.3: IRS Schedule D netting order ──────────────────────────────


class TestNettingOrder:
    """AC-127.3: Netting per IRS Schedule D Part III + Human-approved ST/LT split."""

    def test_st_losses_offset_st_gains_first(self) -> None:
        """ST carryforward offsets ST gains before cross-netting."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("5000"),
            lt_gains=Decimal("3000"),
            st_carryforward=Decimal("2000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        # ST: 5000 - 2000 = 3000 net ST gain
        assert result.net_st == Decimal("3000")
        # LT: unchanged
        assert result.net_lt == Decimal("3000")
        assert result.deductible_loss == Decimal("0")

    def test_lt_losses_offset_lt_gains_first(self) -> None:
        """LT carryforward offsets LT gains before cross-netting."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("2000"),
            lt_gains=Decimal("8000"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("5000"),
            filing_status=FilingStatus.SINGLE,
        )
        # LT: 8000 - 5000 = 3000 net LT gain
        assert result.net_lt == Decimal("3000")
        # ST: unchanged
        assert result.net_st == Decimal("2000")
        assert result.deductible_loss == Decimal("0")

    def test_cross_net_st_excess_loss_offsets_lt_gains(self) -> None:
        """Excess ST loss after netting ST gains offsets LT gains."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("2000"),
            lt_gains=Decimal("5000"),
            st_carryforward=Decimal("6000"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        # ST netting: 2000 - 6000 = -4000 (excess ST loss of 4000)
        # Cross-net: LT 5000 - 4000 = 1000
        assert result.net_lt == Decimal("1000")
        assert result.net_st == Decimal("0")
        assert result.deductible_loss == Decimal("0")

    def test_cross_net_lt_excess_loss_offsets_st_gains(self) -> None:
        """Excess LT loss after netting LT gains offsets ST gains."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("5000"),
            lt_gains=Decimal("2000"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("6000"),
            filing_status=FilingStatus.SINGLE,
        )
        # LT netting: 2000 - 6000 = -4000 (excess LT loss of 4000)
        # Cross-net: ST 5000 - 4000 = 1000
        assert result.net_st == Decimal("1000")
        assert result.net_lt == Decimal("0")
        assert result.deductible_loss == Decimal("0")

    def test_mixed_st_gain_lt_loss_scenario(self) -> None:
        """Mixed: ST gain $10K + LT carryforward $15K → net loss, cap at $3K."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("10000"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("15000"),
            filing_status=FilingStatus.SINGLE,
        )
        # LT netting: 0 - 15000 = -15000
        # Cross-net: ST 10000 - 15000 = net loss of 5000
        assert result.net_st == Decimal("0")
        assert result.net_lt == Decimal("0")
        assert result.deductible_loss == Decimal("3000")
        # Remaining: 5000 - 3000 = 2000 LT carryforward
        assert result.remaining_lt_carryforward == Decimal("2000")

    def test_all_gains_no_losses(self) -> None:
        """No carryforward → no deduction, net = gains."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("5000"),
            lt_gains=Decimal("3000"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.net_st == Decimal("5000")
        assert result.net_lt == Decimal("3000")
        assert result.deductible_loss == Decimal("0")
        assert result.remaining_st_carryforward == Decimal("0")
        assert result.remaining_lt_carryforward == Decimal("0")

    def test_zero_everything(self) -> None:
        """All zeros → all zeros result."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.net_st == Decimal("0")
        assert result.net_lt == Decimal("0")
        assert result.deductible_loss == Decimal("0")
        assert result.remaining_st_carryforward == Decimal("0")
        assert result.remaining_lt_carryforward == Decimal("0")

    def test_both_st_and_lt_carryforwards_applied(self) -> None:
        """Both ST and LT carryforwards applied to respective pools."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("4000"),
            lt_gains=Decimal("6000"),
            st_carryforward=Decimal("1000"),
            lt_carryforward=Decimal("2000"),
            filing_status=FilingStatus.SINGLE,
        )
        # ST: 4000 - 1000 = 3000
        assert result.net_st == Decimal("3000")
        # LT: 6000 - 2000 = 4000
        assert result.net_lt == Decimal("4000")
        assert result.deductible_loss == Decimal("0")

    def test_total_wipeout_both_pools(self) -> None:
        """Carryforwards exceed both gain pools — net loss capped."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("1000"),
            lt_gains=Decimal("2000"),
            st_carryforward=Decimal("5000"),
            lt_carryforward=Decimal("8000"),
            filing_status=FilingStatus.SINGLE,
        )
        # ST: 1000 - 5000 = -4000 excess
        # LT: 2000 - 8000 = -6000 excess
        # Total net loss: 10000
        assert result.net_st == Decimal("0")
        assert result.net_lt == Decimal("0")
        assert result.deductible_loss == Decimal("3000")
        # Remaining carryforward: 10000 - 3000 = 7000 total
        total_remaining = (
            result.remaining_st_carryforward + result.remaining_lt_carryforward
        )
        assert total_remaining == Decimal("7000")

    def test_negative_gains_treated_as_losses(self) -> None:
        """Negative gains (current year losses) contribute to netting."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("-2000"),
            lt_gains=Decimal("5000"),
            st_carryforward=Decimal("0"),
            lt_carryforward=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        # ST: -2000 (loss), cross-net against LT: 5000 - 2000 = 3000
        assert result.net_st == Decimal("0")
        assert result.net_lt == Decimal("3000")
        assert result.deductible_loss == Decimal("0")

    def test_carryforward_character_preserved(self) -> None:
        """Remaining carryforwards retain their ST/LT character.

        IRS Schedule D Capital Loss Carryover Worksheet requires
        character retention.
        """
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("3000"),
            lt_carryforward=Decimal("5000"),
            filing_status=FilingStatus.SINGLE,
        )
        # Total loss = 8000, deductible = 3000
        # Remaining = 5000 — character should be preserved
        # ST carryforward used first against deduction (ST-first per Human-approved)
        # Deduction eats 3000 from ST → ST remaining = 0, LT remaining = 5000
        assert result.remaining_st_carryforward == Decimal("0")
        assert result.remaining_lt_carryforward == Decimal("5000")

    def test_married_separate_excess_carryforward(self) -> None:
        """MARRIED_SEPARATE: $1,500 cap with excess going to carryforward."""
        result = apply_capital_loss_rules(
            st_gains=Decimal("0"),
            lt_gains=Decimal("0"),
            st_carryforward=Decimal("2000"),
            lt_carryforward=Decimal("1000"),
            filing_status=FilingStatus.MARRIED_SEPARATE,
        )
        assert result.deductible_loss == Decimal("1500")
        # Remaining: 3000 - 1500 = 1500
        total_remaining = (
            result.remaining_st_carryforward + result.remaining_lt_carryforward
        )
        assert total_remaining == Decimal("1500")
