# tests/unit/test_tax_brackets.py
"""MEU-146: Marginal Tax Rate Calculator — RED phase tests.

FIC — Feature Intent Contract
=============================
AC-146.1: compute_marginal_rate(taxable_income, filing_status, tax_year)
          returns correct marginal bracket rate for all 7 brackets.
          [Research-backed: IRS Rev. Proc. 2024-40 (TY2025)]
AC-146.2: compute_effective_rate(taxable_income, filing_status, tax_year)
          returns total_tax / taxable_income as effective rate.
          [Spec §E1: "compute effective + marginal federal rate"]
AC-146.3: compute_tax_liability(taxable_income, filing_status, tax_year)
          returns total federal income tax in dollars using progressive brackets.
          [Research-backed: IRS progressive bracket math]
AC-146.4: compute_capital_gains_tax(lt_gains, taxable_income, filing_status, tax_year)
          returns LT capital gains tax at 0%/15%/20% rates.
          [Research-backed: IRS LT capital gains rate thresholds]
AC-146.5: Bracket data includes 2025 and 2026 tax years, with 4 filing statuses.
          [Research-backed: IRS inflation adjustments]
AC-146.6: compute_combined_rate(federal_effective, state_tax_rate) returns
          federal + state combined rate. state_tax_rate < 0 raises ValueError.
          [Spec: domain-model-reference.md L387, L557]
"""

from decimal import Decimal

import pytest

from zorivest_core.domain.enums import FilingStatus
from zorivest_core.domain.tax.brackets import (
    compute_capital_gains_tax,
    compute_combined_rate,
    compute_effective_rate,
    compute_marginal_rate,
    compute_tax_liability,
)


# ── AC-146.1: Marginal Rate ──────────────────────────────────────────────


class TestComputeMarginalRate:
    """AC-146.1: Correct marginal bracket for all 7 brackets."""

    # 2025 Single brackets: 10%, 12%, 22%, 24%, 32%, 35%, 37%
    # Thresholds: $0, $11,925, $48,475, $103,350, $197,300, $250,525, $626,350
    # (Source: IRS Rev. Proc. 2024-40 as amended by OBBB)

    def test_10pct_bracket_single(self) -> None:
        rate = compute_marginal_rate(Decimal("10000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.10")

    def test_12pct_bracket_single(self) -> None:
        rate = compute_marginal_rate(Decimal("30000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.12")

    def test_22pct_bracket_single(self) -> None:
        rate = compute_marginal_rate(Decimal("80000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.22")

    def test_24pct_bracket_single(self) -> None:
        rate = compute_marginal_rate(Decimal("150000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.24")

    def test_32pct_bracket_single(self) -> None:
        rate = compute_marginal_rate(Decimal("200000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.32")

    def test_35pct_bracket_single(self) -> None:
        rate = compute_marginal_rate(Decimal("400000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.35")

    def test_37pct_bracket_single(self) -> None:
        rate = compute_marginal_rate(Decimal("700000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.37")

    def test_married_joint_12pct(self) -> None:
        """MFJ 12% bracket threshold is double Single."""
        rate = compute_marginal_rate(Decimal("50000"), FilingStatus.MARRIED_JOINT, 2025)
        assert rate == Decimal("0.12")

    def test_head_of_household_22pct(self) -> None:
        rate = compute_marginal_rate(
            Decimal("80000"), FilingStatus.HEAD_OF_HOUSEHOLD, 2025
        )
        assert rate == Decimal("0.22")

    def test_married_separate_24pct(self) -> None:
        rate = compute_marginal_rate(
            Decimal("110000"), FilingStatus.MARRIED_SEPARATE, 2025
        )
        assert rate == Decimal("0.24")

    def test_2026_brackets_single_37pct(self) -> None:
        """2026 has inflation-adjusted thresholds."""
        rate = compute_marginal_rate(Decimal("700000"), FilingStatus.SINGLE, 2026)
        assert rate == Decimal("0.37")

    def test_2026_brackets_single_10pct(self) -> None:
        rate = compute_marginal_rate(Decimal("5000"), FilingStatus.SINGLE, 2026)
        assert rate == Decimal("0.10")

    # ── C1: 2026 threshold boundary tests (Rev. Proc. 2025-32) ──────────

    # Single 2026: 12400, 50400, 105700, 201775, 256225, 640600
    def test_2026_single_at_12pct_boundary(self) -> None:
        """$12,400 is top of 10% bracket for 2026 Single."""
        assert compute_marginal_rate(
            Decimal("12400"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.10")

    def test_2026_single_over_12pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("12401"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.12")

    def test_2026_single_at_22pct_boundary(self) -> None:
        """$50,400 is top of 12% bracket for 2026 Single."""
        assert compute_marginal_rate(
            Decimal("50400"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.12")

    def test_2026_single_over_22pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("50401"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.22")

    def test_2026_single_at_24pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("105700"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.22")

    def test_2026_single_over_24pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("105701"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.24")

    def test_2026_single_at_32pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("201775"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.24")

    def test_2026_single_over_32pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("201776"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.32")

    def test_2026_single_at_35pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("256225"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.32")

    def test_2026_single_over_35pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("256226"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.35")

    def test_2026_single_at_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("640600"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.35")

    def test_2026_single_over_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("640601"), FilingStatus.SINGLE, 2026
        ) == Decimal("0.37")

    # MFJ 2026: 24800, 100800, 211400, 403550, 512450, 768700
    def test_2026_mfj_at_12pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("24800"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.10")

    def test_2026_mfj_over_12pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("24801"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.12")

    def test_2026_mfj_at_22pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("100800"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.12")

    def test_2026_mfj_over_22pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("100801"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.22")

    def test_2026_mfj_at_24pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("211400"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.22")

    def test_2026_mfj_over_24pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("211401"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.24")

    def test_2026_mfj_at_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("768700"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.35")

    def test_2026_mfj_over_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("768701"), FilingStatus.MARRIED_JOINT, 2026
        ) == Decimal("0.37")

    # MFS 2026: 12400, 50400, 105700, 201775, 256225, 384350
    def test_2026_mfs_at_12pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("12400"), FilingStatus.MARRIED_SEPARATE, 2026
        ) == Decimal("0.10")

    def test_2026_mfs_over_12pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("12401"), FilingStatus.MARRIED_SEPARATE, 2026
        ) == Decimal("0.12")

    def test_2026_mfs_at_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("384350"), FilingStatus.MARRIED_SEPARATE, 2026
        ) == Decimal("0.35")

    def test_2026_mfs_over_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("384351"), FilingStatus.MARRIED_SEPARATE, 2026
        ) == Decimal("0.37")

    # HoH 2026: 17700, 67450, 105700, 201775, 256200, 640600
    def test_2026_hoh_at_12pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("17700"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.10")

    def test_2026_hoh_over_12pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("17701"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.12")

    def test_2026_hoh_at_22pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("67450"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.12")

    def test_2026_hoh_over_22pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("67451"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.22")

    def test_2026_hoh_at_35pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("256200"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.32")

    def test_2026_hoh_over_35pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("256201"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.35")

    def test_2026_hoh_at_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("640600"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.35")

    def test_2026_hoh_over_37pct_boundary(self) -> None:
        assert compute_marginal_rate(
            Decimal("640601"), FilingStatus.HEAD_OF_HOUSEHOLD, 2026
        ) == Decimal("0.37")

    # 2026 liability cross-check — verifies progressive bracket math
    def test_2026_single_two_brackets_liability(self) -> None:
        """$30,000 single 2026: 10% on $12,400 + 12% on $17,600."""
        tax = compute_tax_liability(Decimal("30000"), FilingStatus.SINGLE, 2026)
        # 10%: 12400 * 0.10 = 1240.00
        # 12%: 17600 * 0.12 = 2112.00
        # Total = 3352.00
        assert tax == Decimal("3352.00")

    def test_2026_mfj_two_brackets_liability(self) -> None:
        """$80,000 MFJ 2026: 10% on $24,800 + 12% on $55,200."""
        tax = compute_tax_liability(Decimal("80000"), FilingStatus.MARRIED_JOINT, 2026)
        # 10%: 24800 * 0.10 = 2480.00
        # 12%: 55200 * 0.12 = 6624.00
        # Total = 9104.00
        assert tax == Decimal("9104.00")

    def test_negative_income_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            compute_marginal_rate(Decimal("-1"), FilingStatus.SINGLE, 2025)

    def test_zero_income(self) -> None:
        rate = compute_marginal_rate(Decimal("0"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.10")  # Lowest bracket

    def test_unsupported_year_raises(self) -> None:
        with pytest.raises(ValueError, match="year"):
            compute_marginal_rate(Decimal("50000"), FilingStatus.SINGLE, 2020)

    def test_boundary_exact_threshold(self) -> None:
        """Income exactly at bracket boundary falls into the lower bracket."""
        # $11,925 is the top of the 10% bracket for Single 2025
        rate = compute_marginal_rate(Decimal("11925"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.10")


# ── AC-146.2: Effective Rate ─────────────────────────────────────────────


class TestComputeEffectiveRate:
    """AC-146.2: Effective rate = total_tax / taxable_income."""

    def test_effective_rate_below_marginal(self) -> None:
        """Effective rate is always below marginal for multi-bracket income."""
        effective = compute_effective_rate(Decimal("100000"), FilingStatus.SINGLE, 2025)
        marginal = compute_marginal_rate(Decimal("100000"), FilingStatus.SINGLE, 2025)
        assert effective < marginal

    def test_effective_rate_positive(self) -> None:
        rate = compute_effective_rate(Decimal("50000"), FilingStatus.SINGLE, 2025)
        assert rate > Decimal("0")
        assert rate < Decimal("1")

    def test_zero_income_returns_zero(self) -> None:
        rate = compute_effective_rate(Decimal("0"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0")

    def test_low_income_effective_near_10pct(self) -> None:
        """$1,000 income should have ~10% effective rate."""
        rate = compute_effective_rate(Decimal("1000"), FilingStatus.SINGLE, 2025)
        assert rate == Decimal("0.10")


# ── AC-146.3: Tax Liability ──────────────────────────────────────────────


class TestComputeTaxLiability:
    """AC-146.3: Total federal income tax via progressive brackets."""

    def test_single_bracket_only(self) -> None:
        """$10,000 income — entirely in 10% bracket."""
        tax = compute_tax_liability(Decimal("10000"), FilingStatus.SINGLE, 2025)
        assert tax == Decimal("1000.00")

    def test_two_brackets(self) -> None:
        """$30,000 income spans 10% and 12% brackets (2025 Single)."""
        # 10% on first $11,925 = $1,192.50
        # 12% on remaining $18,075 = $2,169.00
        # Total = $3,361.50
        tax = compute_tax_liability(Decimal("30000"), FilingStatus.SINGLE, 2025)
        assert tax == Decimal("3361.50")

    def test_top_bracket_liability(self) -> None:
        """$1,000,000 income — verify total with all 7 brackets."""
        tax = compute_tax_liability(Decimal("1000000"), FilingStatus.SINGLE, 2025)
        # Should be > $300K but this is a sanity check
        assert tax > Decimal("300000")
        assert tax < Decimal("370000")

    def test_married_joint_brackets(self) -> None:
        """MFJ $80,000 — spans 10% + 12% brackets."""
        tax = compute_tax_liability(Decimal("80000"), FilingStatus.MARRIED_JOINT, 2025)
        # 10% on $23,850 = $2,385
        # 12% on $56,150 = $6,738
        # Total = $9,123
        assert tax == Decimal("9123.00")

    def test_unsupported_year_raises(self) -> None:
        with pytest.raises(ValueError, match="year"):
            compute_tax_liability(Decimal("50000"), FilingStatus.SINGLE, 2020)

    def test_zero_income_zero_tax(self) -> None:
        tax = compute_tax_liability(Decimal("0"), FilingStatus.SINGLE, 2025)
        assert tax == Decimal("0")


# ── AC-146.4: Capital Gains Tax ──────────────────────────────────────────


class TestComputeCapitalGainsTax:
    """AC-146.4: LT capital gains at 0%/15%/20% rates."""

    def test_zero_pct_bracket(self) -> None:
        """Low-income taxpayer with LT gains pays 0%."""
        tax = compute_capital_gains_tax(
            lt_gains=Decimal("10000"),
            taxable_income=Decimal("30000"),
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert tax == Decimal("0")

    def test_15pct_bracket(self) -> None:
        """Middle-income taxpayer with LT gains pays 15%."""
        tax = compute_capital_gains_tax(
            lt_gains=Decimal("10000"),
            taxable_income=Decimal("100000"),
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert tax == Decimal("1500.00")

    def test_20pct_bracket(self) -> None:
        """High-income taxpayer with LT gains pays 20%."""
        tax = compute_capital_gains_tax(
            lt_gains=Decimal("50000"),
            taxable_income=Decimal("600000"),
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert tax == Decimal("10000.00")

    def test_negative_gains_returns_zero(self) -> None:
        tax = compute_capital_gains_tax(
            lt_gains=Decimal("-5000"),
            taxable_income=Decimal("100000"),
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert tax == Decimal("0")

    def test_married_joint_higher_threshold(self) -> None:
        """MFJ 0% threshold is higher ($96,700 for 2025)."""
        tax = compute_capital_gains_tax(
            lt_gains=Decimal("10000"),
            taxable_income=Decimal("80000"),
            filing_status=FilingStatus.MARRIED_JOINT,
            tax_year=2025,
        )
        assert tax == Decimal("0")

    # ── C4: LTCG straddle documentation tests (Finding #4) ──────────

    def test_straddle_simplified_model_applies_single_rate(self) -> None:
        """Document: simplified model applies 15% to full gain even when
        part should be at 0%.

        Scenario: $40K ordinary + $10K LT gain = $50K total.
        0% threshold for Single 2025 is $48,350.
        Stacked model: $8,350 at 0%, $1,650 at 15% = $247.50.
        Simplified model: all $10K at 15% = $1,500.

        This test documents the current simplified behavior. When the
        stacked model is implemented, this test should be UPDATED to
        assert $247.50 instead.
        """
        tax = compute_capital_gains_tax(
            lt_gains=Decimal("10000"),
            taxable_income=Decimal("50000"),
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        # Simplified model: applies 15% to full gain
        assert tax == Decimal("1500.00")

    def test_straddle_at_zero_pct_boundary(self) -> None:
        """Document: income exactly at 0% threshold gets 0% on all gains.

        $48,350 single 2025 is exactly at 0% threshold boundary.
        Simplified model: entire gain at 0%.
        """
        tax = compute_capital_gains_tax(
            lt_gains=Decimal("5000"),
            taxable_income=Decimal("48350"),
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert tax == Decimal("0")


# ── AC-146.5: Year Coverage ──────────────────────────────────────────────


class TestYearCoverage:
    """AC-146.5: Bracket data for 2025 and 2026, 4 filing statuses."""

    @pytest.mark.parametrize("year", [2025, 2026])
    @pytest.mark.parametrize(
        "status",
        [
            FilingStatus.SINGLE,
            FilingStatus.MARRIED_JOINT,
            FilingStatus.MARRIED_SEPARATE,
            FilingStatus.HEAD_OF_HOUSEHOLD,
        ],
    )
    def test_all_combinations(self, year: int, status: FilingStatus) -> None:
        """Every year × filing status combination must compute without error."""
        rate = compute_marginal_rate(Decimal("50000"), status, year)
        assert Decimal("0") < rate <= Decimal("0.37")
        tax = compute_tax_liability(Decimal("50000"), status, year)
        assert tax > Decimal("0")


# ── AC-146.6: Combined Rate ──────────────────────────────────────────────


class TestComputeCombinedRate:
    """AC-146.6: federal + state combined rate."""

    def test_combined_rate_basic(self) -> None:
        """Federal 22% + state 5% = 27%."""
        result = compute_combined_rate(Decimal("0.22"), Decimal("0.05"))
        assert result == Decimal("0.27")

    def test_zero_state_rate_returns_federal_only(self) -> None:
        result = compute_combined_rate(Decimal("0.24"), Decimal("0"))
        assert result == Decimal("0.24")

    def test_both_zero(self) -> None:
        result = compute_combined_rate(Decimal("0"), Decimal("0"))
        assert result == Decimal("0")

    def test_negative_state_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="state_tax_rate"):
            compute_combined_rate(Decimal("0.22"), Decimal("-0.01"))

    def test_high_combined_rate(self) -> None:
        """37% federal + 13.3% CA = 50.3%."""
        result = compute_combined_rate(Decimal("0.37"), Decimal("0.133"))
        assert result == Decimal("0.503")
