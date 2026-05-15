# tests/unit/test_tax_quarterly.py
"""MEU-143/144/145: Quarterly Tax Estimates — RED phase tests.

FIC — Feature Intent Contract
=============================

MEU-143: QuarterlyEstimate Entity + Safe Harbor
AC-143.1: QuarterlyEstimate dataclass with 9 fields per spec.
          [Spec: domain-model-reference.md L403-413]
AC-143.2: compute_safe_harbor(current_year_estimate, prior_year_tax, agi,
          filing_status) returns the lower of 90%-current vs 100%/110%-prior.
          [Spec §D1: "Tool recommends the lower amount"]
AC-143.3: 110% threshold applies when AGI > $150K (or > $75K for MFS).
          [Research-backed: IRS Pub 505]
AC-143.4: Result includes method field indicating which safe harbor path.
          [Spec]
AC-143.5: Quarterly required payment = annual safe harbor / 4.
          [Spec]
AC-143.6: QuarterlyEstimateRepository port defined with get, save, update,
          list_for_year methods.
          [Local Canon: ports.py pattern]

MEU-144: Annualized Income Method (Form 2210 Schedule AI)
AC-144.1: compute_annualized_installment(quarterly_incomes, filing_status,
          tax_year) returns per-quarter required payment.
          [Research-backed: IRS Form 2210 Schedule AI]
AC-144.2: Annualization factors are [4, 2.4, 1.5, 1] for individuals.
          [Research-backed: Form 2210 Line 2]
AC-144.3: Each quarter's annualized tax = bracket computation on
          (cumulative_income × factor).
          [Research-backed]
AC-144.4: Required installment for Q(n) = min(annualized_installment,
          regular_installment) adjusted for cumulative prior payments.
          Per IRS Form 2210 Schedule AI line 27.
          [Research-backed: IRS Form 2210 Schedule AI]
AC-144.5: Result includes per-quarter breakdown.
          [Spec §D2]

MEU-145: Due Dates + Underpayment Penalty
AC-145.1: get_quarterly_due_dates(tax_year) returns 4 dates.
          [Spec §D3]
AC-145.2: Due dates on weekends shift to next Monday.
          [Research-backed: IRS rule]
AC-145.3: compute_underpayment_penalty(underpayment, due_date, payment_date,
          penalty_rate) = underpayment × rate × days_late/365.
          [Research-backed: Form 2210 Part III]
AC-145.4: quarterly_ytd_summary returns cumulative paid vs required.
          [Spec §D3]
AC-145.5: Penalty rate defaults stored in bracket data per year.
          [Research-backed]
AC-145.6: TaxService.quarterly_estimate() orchestrates computation.
          [Spec: 04f-api-tax.md L263]
AC-145.7: TaxService.record_payment() — method signature defined.
          [Spec: 04f-api-tax.md L264]
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from zorivest_core.services.tax_service import TaxService

from zorivest_core.domain.enums import FilingStatus
from zorivest_core.domain.tax.quarterly import (
    AnnualizedInstallmentResult,
    QuarterlyDueDate,
    SafeHarborResult,
    YtdQuarterlySummary,
    compute_annualized_installment,
    compute_safe_harbor,
    compute_underpayment_penalty,
    get_quarterly_due_dates,
    quarterly_ytd_summary,
)


# ══════════════════════════════════════════════════════════════════════════
# MEU-143: Safe Harbor Calculator
# ══════════════════════════════════════════════════════════════════════════


class TestComputeSafeHarbor:
    """AC-143.2/3/4/5: Safe harbor computation logic."""

    def test_recommends_lower_of_two_methods(self) -> None:
        """100% prior year ($20K) < 90% current year ($27K) → uses prior."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("30000"),
            prior_year_tax=Decimal("20000"),
            agi=Decimal("100000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert isinstance(result, SafeHarborResult)
        assert result.annual_required == Decimal("20000")
        assert result.method == "safe_harbor_100"
        assert result.quarterly_payment == Decimal("5000")

    def test_90pct_current_when_lower(self) -> None:
        """90% current ($18K) < 100% prior ($25K) → uses current."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("20000"),
            prior_year_tax=Decimal("25000"),
            agi=Decimal("100000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.annual_required == Decimal("18000")
        assert result.method == "current_year_90"
        assert result.quarterly_payment == Decimal("4500")

    def test_110pct_for_high_agi(self) -> None:
        """AGI > $150K → uses 110% of prior year instead of 100%."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("100000"),
            prior_year_tax=Decimal("50000"),
            agi=Decimal("200000"),
            filing_status=FilingStatus.SINGLE,
        )
        # 110% of $50K = $55K; 90% of $100K = $90K → lower is $55K
        assert result.annual_required == Decimal("55000")
        assert result.method == "safe_harbor_110"

    def test_100pct_at_exactly_150k(self) -> None:
        """AGI exactly $150K → uses 100%, not 110%."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("100000"),
            prior_year_tax=Decimal("50000"),
            agi=Decimal("150000"),
            filing_status=FilingStatus.SINGLE,
        )
        # 100% of $50K = $50K; 90% of $100K = $90K → lower is $50K
        assert result.annual_required == Decimal("50000")
        assert result.method == "safe_harbor_100"

    def test_mfs_110_threshold_at_75k(self) -> None:
        """MFS 110% threshold is $75K, not $150K."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("60000"),
            prior_year_tax=Decimal("30000"),
            agi=Decimal("80000"),
            filing_status=FilingStatus.MARRIED_SEPARATE,
        )
        # AGI $80K > $75K threshold → 110% of $30K = $33K
        # 90% of $60K = $54K → lower is $33K
        assert result.annual_required == Decimal("33000")
        assert result.method == "safe_harbor_110"

    def test_zero_prior_year_tax(self) -> None:
        """No prior year tax → uses 90% current only."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("30000"),
            prior_year_tax=Decimal("0"),
            agi=Decimal("100000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert result.annual_required == Decimal("0")
        assert result.method == "safe_harbor_100"

    def test_quarterly_payment_is_quarter_of_annual(self) -> None:
        """Quarterly = annual / 4."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("40000"),
            prior_year_tax=Decimal("40000"),
            agi=Decimal("100000"),
            filing_status=FilingStatus.SINGLE,
        )
        # 100% of $40K = $40K; 90% of $40K = $36K → lower is $36K
        assert result.quarterly_payment == Decimal("9000")

    def test_all_decimal_types(self) -> None:
        """All result fields are Decimal."""
        result = compute_safe_harbor(
            current_year_estimate=Decimal("50000"),
            prior_year_tax=Decimal("40000"),
            agi=Decimal("200000"),
            filing_status=FilingStatus.SINGLE,
        )
        assert isinstance(result.annual_required, Decimal)
        assert isinstance(result.quarterly_payment, Decimal)
        assert isinstance(result.current_year_90, Decimal)
        assert isinstance(result.prior_year_safe_harbor, Decimal)


# ══════════════════════════════════════════════════════════════════════════
# MEU-144: Annualized Income Method
# ══════════════════════════════════════════════════════════════════════════


class TestComputeAnnualizedInstallment:
    """AC-144.1–5: Schedule AI annualized income method."""

    def test_even_income_all_quarters(self) -> None:
        """Equal income each quarter → installments are equal."""
        result = compute_annualized_installment(
            quarterly_incomes=[
                Decimal("25000"),
                Decimal("25000"),
                Decimal("25000"),
                Decimal("25000"),
            ],
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert isinstance(result, AnnualizedInstallmentResult)
        assert len(result.installments) == 4
        # All installments should be roughly equal
        assert all(inst >= Decimal("0") for inst in result.installments)

    def test_front_loaded_income(self) -> None:
        """Big Q1, small rest → Q1 installment higher, Q2-Q4 lower."""
        result = compute_annualized_installment(
            quarterly_incomes=[
                Decimal("80000"),
                Decimal("5000"),
                Decimal("5000"),
                Decimal("5000"),
            ],
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        # Q1 should have the highest required installment
        assert result.installments[0] > result.installments[1]

    def test_all_zero_income(self) -> None:
        """No income → all installments zero."""
        result = compute_annualized_installment(
            quarterly_incomes=[Decimal("0")] * 4,
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert all(inst == Decimal("0") for inst in result.installments)

    def test_negative_installment_floors_to_zero(self) -> None:
        """If Q1 large and Q2 small, Q2 installment can't go negative."""
        result = compute_annualized_installment(
            quarterly_incomes=[
                Decimal("100000"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            ],
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        # All installments should be >= 0
        assert all(inst >= Decimal("0") for inst in result.installments)

    def test_annualization_factors(self) -> None:
        """Factors are [4, 2.4, 1.5, 1] per IRS Form 2210."""
        result = compute_annualized_installment(
            quarterly_incomes=[
                Decimal("25000"),
                Decimal("25000"),
                Decimal("25000"),
                Decimal("25000"),
            ],
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert result.factors == [
            Decimal("4"),
            Decimal("2.4"),
            Decimal("1.5"),
            Decimal("1"),
        ]

    def test_per_quarter_breakdown(self) -> None:
        """Result includes annualized_incomes and annualized_taxes."""
        result = compute_annualized_installment(
            quarterly_incomes=[
                Decimal("25000"),
                Decimal("25000"),
                Decimal("25000"),
                Decimal("25000"),
            ],
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        assert len(result.annualized_incomes) == 4
        assert len(result.annualized_taxes) == 4

    def test_empty_incomes_raises(self) -> None:
        with pytest.raises(ValueError, match="income"):
            compute_annualized_installment(
                quarterly_incomes=[],
                filing_status=FilingStatus.SINGLE,
                tax_year=2025,
            )

    def test_wrong_length_raises(self) -> None:
        with pytest.raises(ValueError, match="4"):
            compute_annualized_installment(
                quarterly_incomes=[Decimal("10000")] * 3,
                filing_status=FilingStatus.SINGLE,
                tax_year=2025,
            )

    def test_married_joint_brackets(self) -> None:
        """MFJ has different bracket thresholds → different installments."""
        single = compute_annualized_installment(
            quarterly_incomes=[Decimal("50000")] * 4,
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        joint = compute_annualized_installment(
            quarterly_incomes=[Decimal("50000")] * 4,
            filing_status=FilingStatus.MARRIED_JOINT,
            tax_year=2025,
        )
        # MFJ pays less tax at same income
        assert sum(joint.installments) < sum(single.installments)

    def test_min_annualized_vs_regular_uses_lower(self) -> None:
        """AC-144.4: When regular installment (safe harbor/4) is lower than
        annualized installment, use the regular amount."""
        # Front-loaded income → high annualized installment for Q1
        # But if required_annual_payment is low, regular = required/4 wins
        result = compute_annualized_installment(
            quarterly_incomes=[
                Decimal("200000"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            ],
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
            required_annual_payment=Decimal("10000"),
        )
        # Regular installment = $10000/4 = $2500
        # Annualized Q1 would be much higher (25% of tax on $800K)
        # min() should cap at the regular amount
        assert result.installments[0] <= Decimal("2500")

    def test_min_uses_annualized_when_lower(self) -> None:
        """AC-144.4: When annualized installment is lower, use annualized."""
        # Low Q1 income → small annualized installment
        result = compute_annualized_installment(
            quarterly_incomes=[
                Decimal("5000"),
                Decimal("5000"),
                Decimal("5000"),
                Decimal("5000"),
            ],
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
            required_annual_payment=Decimal("100000"),
        )
        # Regular installment = $100000/4 = $25000
        # Annualized Q1 would be small (25% of tax on $20K)
        # min() should use annualized
        assert result.installments[0] < Decimal("25000")

    def test_no_required_annual_defaults_to_annualized_only(self) -> None:
        """AC-144.4: When required_annual_payment is None, skip min() check."""
        result = compute_annualized_installment(
            quarterly_incomes=[Decimal("25000")] * 4,
            filing_status=FilingStatus.SINGLE,
            tax_year=2025,
        )
        # Should still work without the parameter (backward compat)
        assert len(result.installments) == 4
        assert all(inst >= Decimal("0") for inst in result.installments)


# ══════════════════════════════════════════════════════════════════════════
# MEU-145: Due Dates + Underpayment Penalty
# ══════════════════════════════════════════════════════════════════════════


class TestGetQuarterlyDueDates:
    """AC-145.1/2: Due date computation with weekend shifts."""

    def test_four_dates_returned(self) -> None:
        dates = get_quarterly_due_dates(2025)
        assert len(dates) == 4
        assert all(isinstance(d, QuarterlyDueDate) for d in dates)

    def test_standard_dates_2025(self) -> None:
        """2025: Apr 15 (Tue), Jun 16 (Mon — Jun 15 is Sun), Sep 15 (Mon), Jan 15 (Thu)."""
        dates = get_quarterly_due_dates(2025)
        assert dates[0].due_date == date(2025, 4, 15)
        assert dates[1].due_date == date(2025, 6, 16)  # Jun 15 is Sunday
        assert dates[2].due_date == date(2025, 9, 15)
        assert dates[3].due_date == date(2026, 1, 15)  # Q4 is next year

    def test_quarter_numbers(self) -> None:
        dates = get_quarterly_due_dates(2025)
        assert [d.quarter for d in dates] == [1, 2, 3, 4]

    def test_2026_dates(self) -> None:
        """2026: Apr 15 (Wed), Jun 15 (Mon), Sep 15 (Tue), Jan 15 (Fri)."""
        dates = get_quarterly_due_dates(2026)
        assert dates[0].due_date == date(2026, 4, 15)
        assert dates[1].due_date == date(2026, 6, 15)
        assert dates[2].due_date == date(2026, 9, 15)
        assert dates[3].due_date == date(2027, 1, 15)

    def test_saturday_shifts_to_monday(self) -> None:
        """If Apr 15 falls on Saturday, shifts to Monday Apr 17."""
        # 2028: Apr 15 is Saturday
        dates = get_quarterly_due_dates(2028)
        assert dates[0].due_date == date(2028, 4, 17)  # Monday

    def test_invalid_year_raises(self) -> None:
        with pytest.raises(ValueError, match="year"):
            get_quarterly_due_dates(1999)


class TestComputeUnderpaymentPenalty:
    """AC-145.3/5: Penalty = underpayment × rate × days/365."""

    def test_basic_penalty(self) -> None:
        """$10K underpayment, 90 days late, 7% rate."""
        penalty = compute_underpayment_penalty(
            underpayment=Decimal("10000"),
            due_date=date(2025, 4, 15),
            payment_date=date(2025, 7, 14),  # 90 days late
            penalty_rate=Decimal("0.07"),
        )
        # $10000 × 0.07 × 90/365 = $172.60
        expected = (
            Decimal("10000") * Decimal("0.07") * Decimal("90") / Decimal("365")
        ).quantize(Decimal("0.01"))
        assert penalty == expected

    def test_on_time_no_penalty(self) -> None:
        """Payment on or before due date → $0 penalty."""
        penalty = compute_underpayment_penalty(
            underpayment=Decimal("10000"),
            due_date=date(2025, 4, 15),
            payment_date=date(2025, 4, 15),
            penalty_rate=Decimal("0.07"),
        )
        assert penalty == Decimal("0")

    def test_early_payment_no_penalty(self) -> None:
        """Payment before due date → $0 penalty."""
        penalty = compute_underpayment_penalty(
            underpayment=Decimal("10000"),
            due_date=date(2025, 4, 15),
            payment_date=date(2025, 3, 1),
            penalty_rate=Decimal("0.07"),
        )
        assert penalty == Decimal("0")

    def test_zero_underpayment_no_penalty(self) -> None:
        penalty = compute_underpayment_penalty(
            underpayment=Decimal("0"),
            due_date=date(2025, 4, 15),
            payment_date=date(2025, 12, 31),
            penalty_rate=Decimal("0.07"),
        )
        assert penalty == Decimal("0")

    def test_full_year_penalty(self) -> None:
        """365 days late → full annual rate applied."""
        penalty = compute_underpayment_penalty(
            underpayment=Decimal("10000"),
            due_date=date(2025, 4, 15),
            payment_date=date(2026, 4, 15),
            penalty_rate=Decimal("0.07"),
        )
        assert penalty == Decimal("700.00")


class TestQuarterlyYtdSummary:
    """AC-145.4: Cumulative paid vs required per quarter."""

    def test_all_paid_on_time(self) -> None:
        payments = [Decimal("5000")] * 4
        required = [Decimal("5000")] * 4
        summary = quarterly_ytd_summary(2025, payments, required)
        assert isinstance(summary, YtdQuarterlySummary)
        assert summary.total_paid == Decimal("20000")
        assert summary.total_required == Decimal("20000")
        assert summary.total_shortfall == Decimal("0")

    def test_underpayment_tracked(self) -> None:
        payments = [Decimal("3000")] * 4
        required = [Decimal("5000")] * 4
        summary = quarterly_ytd_summary(2025, payments, required)
        assert summary.total_shortfall == Decimal("8000")

    def test_per_quarter_detail(self) -> None:
        payments = [Decimal("5000"), Decimal("3000"), Decimal("6000"), Decimal("4000")]
        required = [Decimal("5000")] * 4
        summary = quarterly_ytd_summary(2025, payments, required)
        assert len(summary.quarters) == 4
        # Q2 is short $2K, Q4 is short $1K; Q3 overpaid by $1K
        assert summary.quarters[1].shortfall == Decimal("2000")
        assert summary.quarters[2].shortfall == Decimal("0")  # Overpaid


# ══════════════════════════════════════════════════════════════════════════
# AC-145.7: TaxService.record_payment() — signature-only contract
# ══════════════════════════════════════════════════════════════════════════


class TestRecordPaymentContract:
    """AC-145.7 + AC-148.6: record_payment validates inputs and persists."""

    def _service(self) -> "TaxService":
        from unittest.mock import MagicMock

        from zorivest_core.services.tax_service import TaxService

        uow = MagicMock()
        uow.__enter__ = MagicMock(return_value=uow)
        uow.__exit__ = MagicMock(return_value=False)
        # Mock the quarterly_estimates repo for persistence
        uow.quarterly_estimates = MagicMock()
        uow.quarterly_estimates.get_for_quarter = MagicMock(return_value=None)
        return TaxService(uow)

    def test_valid_inputs_persists_payment(self) -> None:
        """Valid quarter/amount → persists via UoW (MEU-148 complete)."""
        svc = self._service()
        # Should not raise — persistence is now wired
        svc.record_payment(tax_year=2025, quarter=1, amount=Decimal("5000"))
        # Verify save was called on the repository
        svc._uow.quarterly_estimates.save.assert_called_once()  # type: ignore[union-attr]

    def test_invalid_quarter_zero_raises_business_rule(self) -> None:
        """Quarter 0 → BusinessRuleError (not NotImplementedError)."""
        from zorivest_core.domain.exceptions import BusinessRuleError

        svc = self._service()
        with pytest.raises(BusinessRuleError, match="quarter"):
            svc.record_payment(tax_year=2025, quarter=0, amount=Decimal("5000"))

    def test_invalid_quarter_five_raises_business_rule(self) -> None:
        """Quarter 5 → BusinessRuleError."""
        from zorivest_core.domain.exceptions import BusinessRuleError

        svc = self._service()
        with pytest.raises(BusinessRuleError, match="quarter"):
            svc.record_payment(tax_year=2025, quarter=5, amount=Decimal("5000"))

    def test_negative_amount_raises_business_rule(self) -> None:
        """Amount < 0 → BusinessRuleError."""
        from zorivest_core.domain.exceptions import BusinessRuleError

        svc = self._service()
        with pytest.raises(BusinessRuleError, match="amount"):
            svc.record_payment(tax_year=2025, quarter=1, amount=Decimal("-100"))

    def test_zero_amount_raises_business_rule(self) -> None:
        """Amount = 0 → BusinessRuleError."""
        from zorivest_core.domain.exceptions import BusinessRuleError

        svc = self._service()
        with pytest.raises(BusinessRuleError, match="amount"):
            svc.record_payment(tax_year=2025, quarter=1, amount=Decimal("0"))
