# packages/core/src/zorivest_core/domain/tax/quarterly.py
"""MEU-143/144/145: Quarterly estimated tax payment engine.

Safe harbor calculations, annualized income method (Form 2210 Schedule AI),
due dates, and underpayment penalty estimation.

Sources:
  - Safe harbor: IRS Pub 505 §2
  - Annualized method: IRS Form 2210 Schedule AI
  - Due dates: IRS §6654(c)(2)
  - Penalty: underpayment × (fed-short-term-rate + 3%) × days/365

Disclaimer: This module provides tax estimation only and does not constitute
tax advice. Consult a qualified tax professional for actual filing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from zorivest_core.domain.enums import FilingStatus
from zorivest_core.domain.tax.brackets import compute_tax_liability

# ── Constants ────────────────────────────────────────────────────────────

# Form 2210 Schedule AI annualization factors (individuals)
ANNUALIZATION_FACTORS: list[Decimal] = [
    Decimal("4"),
    Decimal("2.4"),
    Decimal("1.5"),
    Decimal("1"),
]

# AGI threshold above which 110% prior-year safe harbor applies
_HIGH_AGI_THRESHOLD = Decimal("150000")
_HIGH_AGI_THRESHOLD_MFS = Decimal("75000")

# Minimum year for due date computation
_MIN_YEAR = 2020


# ── Result types ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SafeHarborResult:
    """Result of safe harbor calculation."""

    annual_required: Decimal
    quarterly_payment: Decimal
    method: str  # "safe_harbor_100" | "safe_harbor_110" | "current_year_90"
    current_year_90: Decimal
    prior_year_safe_harbor: Decimal  # 100% or 110% of prior year
    prior_year_pct: Decimal  # 1.00 or 1.10


@dataclass(frozen=True)
class QuarterlyDueDate:
    """A single quarterly payment due date."""

    quarter: int  # 1-4
    due_date: date  # Weekend-adjusted


@dataclass(frozen=True)
class AnnualizedInstallmentResult:
    """Result of annualized income method computation."""

    installments: list[Decimal]  # Per-quarter required payments
    factors: list[Decimal]  # The 4 annualization factors used
    annualized_incomes: list[Decimal]  # Cumulative × factor for each Q
    annualized_taxes: list[Decimal]  # Tax on each annualized income


@dataclass(frozen=True)
class QuarterDetail:
    """Per-quarter detail in YTD summary."""

    quarter: int
    paid: Decimal
    required: Decimal
    shortfall: Decimal  # max(0, required - paid)
    cumulative_paid: Decimal
    cumulative_required: Decimal


@dataclass(frozen=True)
class YtdQuarterlySummary:
    """Year-to-date quarterly payment summary."""

    tax_year: int
    total_paid: Decimal
    total_required: Decimal
    total_shortfall: Decimal
    quarters: list[QuarterDetail]


# ── Private helpers ──────────────────────────────────────────────────────


def _adjust_for_weekend(d: date) -> date:
    """Shift weekend dates to next Monday (IRS rule)."""
    weekday = d.weekday()  # Mon=0 ... Sun=6
    if weekday == 5:  # Saturday → Monday
        return d.replace(day=d.day + 2)
    if weekday == 6:  # Sunday → Monday
        return d.replace(day=d.day + 1)
    return d


# ── Public API: Safe Harbor (MEU-143) ────────────────────────────────────


def compute_safe_harbor(
    current_year_estimate: Decimal,
    prior_year_tax: Decimal,
    agi: Decimal,
    filing_status: FilingStatus,
) -> SafeHarborResult:
    """Compute the safe harbor minimum estimated tax payment.

    Safe harbor = min(90% current year, 100%/110% prior year).
    The 110% threshold applies when AGI > $150K ($75K for MFS).

    Args:
        current_year_estimate: Estimated total tax liability for current year.
        prior_year_tax: Total tax paid in the prior year.
        agi: Adjusted Gross Income estimate.
        filing_status: IRS filing status.

    Returns:
        SafeHarborResult with recommended annual and quarterly amounts.
    """
    current_year_90 = (current_year_estimate * Decimal("0.90")).quantize(
        Decimal("0.01")
    )

    # Determine prior year multiplier
    threshold = (
        _HIGH_AGI_THRESHOLD_MFS
        if filing_status == FilingStatus.MARRIED_SEPARATE
        else _HIGH_AGI_THRESHOLD
    )

    if agi > threshold:
        prior_pct = Decimal("1.10")
    else:
        prior_pct = Decimal("1.00")

    prior_year_safe_harbor = (prior_year_tax * prior_pct).quantize(Decimal("0.01"))

    # Choose the lower of the two methods
    if prior_year_safe_harbor <= current_year_90:
        annual_required = prior_year_safe_harbor
        if prior_pct == Decimal("1.10"):
            method = "safe_harbor_110"
        else:
            method = "safe_harbor_100"
    else:
        annual_required = current_year_90
        method = "current_year_90"

    quarterly_payment = (annual_required / Decimal("4")).quantize(Decimal("0.01"))

    return SafeHarborResult(
        annual_required=annual_required,
        quarterly_payment=quarterly_payment,
        method=method,
        current_year_90=current_year_90,
        prior_year_safe_harbor=prior_year_safe_harbor,
        prior_year_pct=prior_pct,
    )


# ── Public API: Due Dates (MEU-145) ─────────────────────────────────────


def get_quarterly_due_dates(tax_year: int) -> list[QuarterlyDueDate]:
    """Return the 4 quarterly estimated tax payment due dates for a year.

    Standard dates: Apr 15, Jun 15, Sep 15, Jan 15 (next year).
    Weekend dates shift to next Monday.

    Args:
        tax_year: Calendar year for the estimates.

    Returns:
        List of 4 QuarterlyDueDate objects.

    Raises:
        ValueError: If year is before 2020.
    """
    if tax_year < _MIN_YEAR:
        msg = f"Unsupported tax year {tax_year}. Must be >= {_MIN_YEAR}"
        raise ValueError(msg)

    raw_dates = [
        (1, date(tax_year, 4, 15)),
        (2, date(tax_year, 6, 15)),
        (3, date(tax_year, 9, 15)),
        (4, date(tax_year + 1, 1, 15)),
    ]

    return [
        QuarterlyDueDate(quarter=q, due_date=_adjust_for_weekend(d))
        for q, d in raw_dates
    ]


# ── Public API: Annualized Income Method (MEU-144) ───────────────────────


def compute_annualized_installment(
    quarterly_incomes: list[Decimal],
    filing_status: FilingStatus,
    tax_year: int,
    *,
    required_annual_payment: Decimal | None = None,
) -> AnnualizedInstallmentResult:
    """Compute per-quarter required installments using the annualized method.

    IRS Form 2210 Schedule AI: Annualize cumulative income for each quarter,
    compute tax on the annualized amount, then derive each quarter's
    installment as min(annualized_installment, regular_installment) minus
    cumulative prior installments (Schedule AI line 27).

    When required_annual_payment is provided, the regular installment is
    25% of that amount. The required installment for each quarter is the
    *lesser* of the annualized and regular installments, minus any cumulative
    excess from prior quarters, floored to 0.

    Args:
        quarterly_incomes: Exactly 4 values — income earned per quarter.
        filing_status: IRS filing status for bracket lookup.
        tax_year: Calendar year for bracket data.
        required_annual_payment: Optional safe harbor annual amount for
            min() comparison. If None, only annualized method is used.

    Returns:
        AnnualizedInstallmentResult with per-quarter breakdown.

    Raises:
        ValueError: If quarterly_incomes doesn't have exactly 4 elements.
    """
    if len(quarterly_incomes) != 4:
        msg = (
            f"Expected exactly 4 quarterly income values, got {len(quarterly_incomes)}"
        )
        raise ValueError(msg)

    # Regular installment = 25% of required annual payment (if provided)
    regular_installment: Decimal | None = None
    if required_annual_payment is not None:
        regular_installment = (required_annual_payment * Decimal("0.25")).quantize(
            Decimal("0.01")
        )

    factors = ANNUALIZATION_FACTORS
    annualized_incomes: list[Decimal] = []
    annualized_taxes: list[Decimal] = []
    installments: list[Decimal] = []
    cumulative_required = Decimal("0")

    for i in range(4):
        # Cumulative income through quarter i
        cumulative_income = sum(quarterly_incomes[: i + 1])

        # Annualize: cumulative × factor
        annualized = (cumulative_income * factors[i]).quantize(Decimal("0.01"))
        annualized_incomes.append(annualized)

        # Compute tax on annualized income
        if annualized > 0:
            tax_on_annualized = compute_tax_liability(
                annualized, filing_status, tax_year
            )
        else:
            tax_on_annualized = Decimal("0")
        annualized_taxes.append(tax_on_annualized)

        # Annualized installment = 25% of annualized tax
        annualized_inst = tax_on_annualized * Decimal("0.25")

        # AC-144.4: required = min(annualized, regular) if regular provided
        if regular_installment is not None:
            quarter_base = min(annualized_inst, regular_installment)
        else:
            quarter_base = annualized_inst

        # Subtract cumulative prior installments
        quarter_required = (quarter_base - cumulative_required).quantize(
            Decimal("0.01")
        )

        # Floor at 0 — can't have negative required payment
        quarter_required = max(quarter_required, Decimal("0"))
        installments.append(quarter_required)
        cumulative_required += quarter_required

    return AnnualizedInstallmentResult(
        installments=installments,
        factors=factors,
        annualized_incomes=annualized_incomes,
        annualized_taxes=annualized_taxes,
    )


# ── Public API: Underpayment Penalty (MEU-145) ──────────────────────────


def compute_underpayment_penalty(
    underpayment: Decimal,
    due_date: date,
    payment_date: date,
    penalty_rate: Decimal,
) -> Decimal:
    """Compute underpayment penalty for a single quarter.

    Penalty = underpayment × rate × days_late / 365.

    Args:
        underpayment: Dollar shortfall below required payment.
        due_date: Quarterly due date.
        payment_date: Date payment was actually made.
        penalty_rate: Annual penalty rate (fed-short-term + 3%).

    Returns:
        Penalty amount as Decimal (2 decimal places). $0 if not late.
    """
    if underpayment <= 0 or payment_date <= due_date:
        return Decimal("0")

    days_late = (payment_date - due_date).days
    penalty = (
        underpayment * penalty_rate * Decimal(days_late) / Decimal("365")
    ).quantize(Decimal("0.01"))
    return penalty


# ── Public API: YTD Summary (MEU-145) ────────────────────────────────────


def quarterly_ytd_summary(
    tax_year: int,
    payments: list[Decimal],
    required: list[Decimal],
) -> YtdQuarterlySummary:
    """Build year-to-date quarterly payment summary.

    Args:
        tax_year: Calendar year.
        payments: Actual payments for Q1-Q4 (0 if not yet paid).
        required: Required payments for Q1-Q4.

    Returns:
        YtdQuarterlySummary with per-quarter detail.
    """
    quarters: list[QuarterDetail] = []
    cumulative_paid = Decimal("0")
    cumulative_required = Decimal("0")

    for i in range(4):
        paid = payments[i] if i < len(payments) else Decimal("0")
        req = required[i] if i < len(required) else Decimal("0")
        shortfall = max(req - paid, Decimal("0"))

        cumulative_paid += paid
        cumulative_required += req

        quarters.append(
            QuarterDetail(
                quarter=i + 1,
                paid=paid,
                required=req,
                shortfall=shortfall,
                cumulative_paid=cumulative_paid,
                cumulative_required=cumulative_required,
            )
        )

    total_shortfall = max(cumulative_required - cumulative_paid, Decimal("0"))

    return YtdQuarterlySummary(
        tax_year=tax_year,
        total_paid=cumulative_paid,
        total_required=cumulative_required,
        total_shortfall=total_shortfall,
        quarters=quarters,
    )
