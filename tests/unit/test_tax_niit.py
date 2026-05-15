# tests/unit/test_tax_niit.py
"""MEU-147: NIIT (Net Investment Income Tax) Threshold Alert — RED phase tests.

FIC — Feature Intent Contract
=============================
AC-147.1: compute_niit(magi, net_investment_income, filing_status)
          returns NIIT amount when MAGI exceeds threshold.
          [Research-backed: IRC §1411]
AC-147.2: NIIT = 3.8% × min(NII, MAGI - threshold).
          [Research-backed: IRS Form 8960 instructions]
AC-147.3: Correct thresholds for all 4 filing statuses:
          Single=$200K, MFJ=$250K, MFS=$125K, HoH=$200K.
          [Research-backed: IRC §1411(b)]
AC-147.4: check_niit_proximity(magi, filing_status) returns proximity
          percentage and alert flag when within 10% of threshold.
          [Spec §E2: "Flag when approaching threshold"]
AC-147.5: All monetary computations use Decimal for precision.
          [Local Canon: entities.py pattern]
"""

from decimal import Decimal

from zorivest_core.domain.enums import FilingStatus
from zorivest_core.domain.tax.niit import (
    NiitProximityResult,
    NiitResult,
    check_niit_proximity,
    compute_niit,
)


# ── AC-147.1 + AC-147.2: NIIT Computation ───────────────────────────────


class TestComputeNiit:
    """AC-147.1/2: NIIT = 3.8% × min(NII, MAGI - threshold)."""

    def test_single_above_threshold(self) -> None:
        """MAGI $250K, NII $30K → NIIT = 3.8% × min($30K, $50K) = $1,140."""
        result = compute_niit(
            magi=Decimal("250000"),
            net_investment_income=Decimal("30000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert isinstance(result, NiitResult)
        assert result.niit_amount == Decimal("1140.00")
        assert result.rate == Decimal("0.038")
        assert result.threshold == Decimal("200000")

    def test_single_nii_less_than_excess(self) -> None:
        """NII ($10K) < MAGI excess ($50K) → uses NII."""
        result = compute_niit(
            magi=Decimal("250000"),
            net_investment_income=Decimal("10000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.niit_amount == Decimal("380.00")

    def test_single_excess_less_than_nii(self) -> None:
        """MAGI excess ($5K) < NII ($50K) → uses excess."""
        result = compute_niit(
            magi=Decimal("205000"),
            net_investment_income=Decimal("50000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.niit_amount == Decimal("190.00")

    def test_below_threshold_returns_zero(self) -> None:
        """MAGI below threshold → NIIT = 0."""
        result = compute_niit(
            magi=Decimal("199000"),
            net_investment_income=Decimal("50000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.niit_amount == Decimal("0")

    def test_nii_zero_returns_zero(self) -> None:
        """NII = 0 → NIIT = 0 regardless of MAGI."""
        result = compute_niit(
            magi=Decimal("500000"),
            net_investment_income=Decimal("0"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.niit_amount == Decimal("0")


# ── AC-147.3: Filing Status Thresholds ───────────────────────────────────


class TestNiitThresholds:
    """AC-147.3: Correct thresholds per filing status."""

    def test_married_joint_threshold_250k(self) -> None:
        result = compute_niit(
            magi=Decimal("300000"),
            net_investment_income=Decimal("50000"),
            filing_status=FilingStatus.MARRIED_JOINT,
        )
        assert result.threshold == Decimal("250000")
        assert result.niit_amount == Decimal("1900.00")

    def test_married_separate_threshold_125k(self) -> None:
        result = compute_niit(
            magi=Decimal("175000"),
            net_investment_income=Decimal("50000"),
            filing_status=FilingStatus.MARRIED_SEPARATE,
        )
        assert result.threshold == Decimal("125000")
        assert result.niit_amount == Decimal("1900.00")

    def test_head_of_household_threshold_200k(self) -> None:
        result = compute_niit(
            magi=Decimal("250000"),
            net_investment_income=Decimal("30000"),
            filing_status=FilingStatus.HEAD_OF_HOUSEHOLD,
        )
        assert result.threshold == Decimal("200000")
        assert result.niit_amount == Decimal("1140.00")

    def test_exact_at_threshold_no_niit(self) -> None:
        """MAGI exactly at threshold → no excess → no NIIT."""
        result = compute_niit(
            magi=Decimal("200000"),
            net_investment_income=Decimal("50000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.niit_amount == Decimal("0")


# ── AC-147.4: Proximity Alert ────────────────────────────────────────────


class TestCheckNiitProximity:
    """AC-147.4: Alert when within 10% of threshold."""

    def test_within_10pct_alerts(self) -> None:
        """MAGI $190K → 5% below $200K threshold → alert."""
        result = check_niit_proximity(
            magi=Decimal("190000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert isinstance(result, NiitProximityResult)
        assert result.alert is True
        assert result.proximity_pct > Decimal("0.90")

    def test_far_below_no_alert(self) -> None:
        """MAGI $100K → 50% of $200K threshold → no alert."""
        result = check_niit_proximity(
            magi=Decimal("100000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.alert is False
        assert result.proximity_pct == Decimal("0.50")

    def test_above_threshold_alerts(self) -> None:
        """MAGI above threshold → always alert."""
        result = check_niit_proximity(
            magi=Decimal("300000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.alert is True

    def test_mfj_proximity(self) -> None:
        """MFJ $240K → 96% of $250K → within 10% → alert."""
        result = check_niit_proximity(
            magi=Decimal("240000"),
            filing_status=FilingStatus.MARRIED_JOINT,
        )
        assert result.alert is True
        assert result.proximity_pct == Decimal("0.96")


# ── AC-147.5: Decimal Precision ──────────────────────────────────────────


class TestDecimalPrecision:
    """AC-147.5: All computations use Decimal."""

    def test_result_types_are_decimal(self) -> None:
        result = compute_niit(
            magi=Decimal("250000"),
            net_investment_income=Decimal("30000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert isinstance(result.niit_amount, Decimal)
        assert isinstance(result.rate, Decimal)
        assert isinstance(result.threshold, Decimal)

    def test_proximity_result_decimal(self) -> None:
        result = check_niit_proximity(
            magi=Decimal("190000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert isinstance(result.proximity_pct, Decimal)
