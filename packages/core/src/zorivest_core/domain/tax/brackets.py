# packages/core/src/zorivest_core/domain/tax/brackets.py
"""MEU-146: Federal income tax bracket tables and rate calculators.

Pure computation — no I/O, no dependencies beyond enums.

Data sources:
  - 2025: IRS Rev. Proc. 2024-40 (as amended by OBBB Act, July 2025)
  - 2026: IRS inflation adjustments (Rev. Proc. 2025-32)

Disclaimer: This module provides tax estimation only and does not constitute
tax advice. Consult a qualified tax professional for actual filing.
"""

from __future__ import annotations

from decimal import Decimal

from zorivest_core.domain.enums import FilingStatus

# ── Type aliases ─────────────────────────────────────────────────────────

# Each bracket list is ordered low-to-high: [(threshold, rate), ...]
# threshold = minimum taxable income for this bracket
BracketTable = list[tuple[Decimal, Decimal]]

# ── Federal Income Tax Brackets ──────────────────────────────────────────
# Structure: {tax_year: {filing_status: [(threshold, rate), ...]}}

_FEDERAL_BRACKETS: dict[int, dict[FilingStatus, BracketTable]] = {
    2025: {
        FilingStatus.SINGLE: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("11925"), Decimal("0.12")),
            (Decimal("48475"), Decimal("0.22")),
            (Decimal("103350"), Decimal("0.24")),
            (Decimal("197300"), Decimal("0.32")),
            (Decimal("250525"), Decimal("0.35")),
            (Decimal("626350"), Decimal("0.37")),
        ],
        FilingStatus.MARRIED_JOINT: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("23850"), Decimal("0.12")),
            (Decimal("96950"), Decimal("0.22")),
            (Decimal("206700"), Decimal("0.24")),
            (Decimal("394600"), Decimal("0.32")),
            (Decimal("501050"), Decimal("0.35")),
            (Decimal("751600"), Decimal("0.37")),
        ],
        FilingStatus.MARRIED_SEPARATE: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("11925"), Decimal("0.12")),
            (Decimal("48475"), Decimal("0.22")),
            (Decimal("103350"), Decimal("0.24")),
            (Decimal("197300"), Decimal("0.32")),
            (Decimal("250525"), Decimal("0.35")),
            (Decimal("375800"), Decimal("0.37")),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("17000"), Decimal("0.12")),
            (Decimal("64850"), Decimal("0.22")),
            (Decimal("103350"), Decimal("0.24")),
            (Decimal("197300"), Decimal("0.32")),
            (Decimal("250500"), Decimal("0.35")),
            (Decimal("626350"), Decimal("0.37")),
        ],
    },
    2026: {
        # IRS Rev. Proc. 2025-32 / IR-2025-103 (OBBB Act amendments)
        FilingStatus.SINGLE: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("12400"), Decimal("0.12")),
            (Decimal("50400"), Decimal("0.22")),
            (Decimal("105700"), Decimal("0.24")),
            (Decimal("201775"), Decimal("0.32")),
            (Decimal("256225"), Decimal("0.35")),
            (Decimal("640600"), Decimal("0.37")),
        ],
        FilingStatus.MARRIED_JOINT: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("24800"), Decimal("0.12")),
            (Decimal("100800"), Decimal("0.22")),
            (Decimal("211400"), Decimal("0.24")),
            (Decimal("403550"), Decimal("0.32")),
            (Decimal("512450"), Decimal("0.35")),
            (Decimal("768700"), Decimal("0.37")),
        ],
        FilingStatus.MARRIED_SEPARATE: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("12400"), Decimal("0.12")),
            (Decimal("50400"), Decimal("0.22")),
            (Decimal("105700"), Decimal("0.24")),
            (Decimal("201775"), Decimal("0.32")),
            (Decimal("256225"), Decimal("0.35")),
            (Decimal("384350"), Decimal("0.37")),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            (Decimal("0"), Decimal("0.10")),
            (Decimal("17700"), Decimal("0.12")),
            (Decimal("67450"), Decimal("0.22")),
            (Decimal("105700"), Decimal("0.24")),
            (Decimal("201775"), Decimal("0.32")),
            (Decimal("256200"), Decimal("0.35")),
            (Decimal("640600"), Decimal("0.37")),
        ],
    },
}

# ── Long-Term Capital Gains Rate Thresholds ──────────────────────────────
# Structure: {tax_year: {filing_status: [(threshold, rate), ...]}}
# Rates: 0%, 15%, 20%

_LTCG_BRACKETS: dict[int, dict[FilingStatus, BracketTable]] = {
    2025: {
        FilingStatus.SINGLE: [
            (Decimal("0"), Decimal("0")),
            (Decimal("48350"), Decimal("0.15")),
            (Decimal("533400"), Decimal("0.20")),
        ],
        FilingStatus.MARRIED_JOINT: [
            (Decimal("0"), Decimal("0")),
            (Decimal("96700"), Decimal("0.15")),
            (Decimal("600050"), Decimal("0.20")),
        ],
        FilingStatus.MARRIED_SEPARATE: [
            (Decimal("0"), Decimal("0")),
            (Decimal("48350"), Decimal("0.15")),
            (Decimal("300025"), Decimal("0.20")),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            (Decimal("0"), Decimal("0")),
            (Decimal("64750"), Decimal("0.15")),
            (Decimal("566700"), Decimal("0.20")),
        ],
    },
    2026: {
        FilingStatus.SINGLE: [
            (Decimal("0"), Decimal("0")),
            (Decimal("49475"), Decimal("0.15")),
            (Decimal("545925"), Decimal("0.20")),
        ],
        FilingStatus.MARRIED_JOINT: [
            (Decimal("0"), Decimal("0")),
            (Decimal("98950"), Decimal("0.15")),
            (Decimal("614100"), Decimal("0.20")),
        ],
        FilingStatus.MARRIED_SEPARATE: [
            (Decimal("0"), Decimal("0")),
            (Decimal("49475"), Decimal("0.15")),
            (Decimal("307050"), Decimal("0.20")),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            (Decimal("0"), Decimal("0")),
            (Decimal("66250"), Decimal("0.15")),
            (Decimal("579900"), Decimal("0.20")),
        ],
    },
}

# ── IRS Underpayment Penalty Rates ───────────────────────────────────────
# Federal short-term rate + 3%, announced quarterly by IRS.
# Source: IRS Rev. Rul. quarterly announcements.

PENALTY_RATES: dict[int, Decimal] = {
    2025: Decimal("0.07"),  # ~7% (fed short-term ~4% + 3%)
    2026: Decimal("0.07"),  # ~7% (estimated, same ballpark)
}

# ── Supported years ──────────────────────────────────────────────────────

SUPPORTED_YEARS: frozenset[int] = frozenset(_FEDERAL_BRACKETS.keys())


# ── Private helpers ──────────────────────────────────────────────────────


def _validate_inputs(
    taxable_income: Decimal,
    filing_status: FilingStatus,
    tax_year: int,
    *,
    allow_zero: bool = True,
) -> None:
    """Common validation for all bracket functions."""
    if tax_year not in SUPPORTED_YEARS:
        msg = f"Unsupported tax year {tax_year}. Supported: {sorted(SUPPORTED_YEARS)}"
        raise ValueError(msg)
    if taxable_income < 0:
        msg = f"Taxable income cannot be negative: {taxable_income}"
        raise ValueError(msg)


def _get_brackets(
    tax_year: int,
    filing_status: FilingStatus,
    table: dict[int, dict[FilingStatus, BracketTable]],
) -> BracketTable:
    """Retrieve bracket table for given year and filing status."""
    return table[tax_year][filing_status]


# ── Public API ───────────────────────────────────────────────────────────


def compute_marginal_rate(
    taxable_income: Decimal,
    filing_status: FilingStatus,
    tax_year: int,
) -> Decimal:
    """Return the marginal federal income tax rate for the given income.

    The marginal rate is the rate applied to the last dollar of income.
    Income exactly at a bracket threshold stays in the lower bracket.

    Args:
        taxable_income: Total taxable income (non-negative).
        filing_status: IRS filing status enum.
        tax_year: Calendar year (must be in SUPPORTED_YEARS).

    Returns:
        Marginal rate as a Decimal (e.g. Decimal("0.22") for 22%).

    Raises:
        ValueError: If income is negative or year is unsupported.
    """
    _validate_inputs(taxable_income, filing_status, tax_year)
    brackets = _get_brackets(tax_year, filing_status, _FEDERAL_BRACKETS)

    marginal = brackets[0][1]  # Default to lowest bracket
    for threshold, rate in brackets:
        if taxable_income > threshold:
            marginal = rate
        else:
            break
    return marginal


def compute_tax_liability(
    taxable_income: Decimal,
    filing_status: FilingStatus,
    tax_year: int,
) -> Decimal:
    """Compute total federal income tax using progressive bracket math.

    Each bracket's tax is computed on only the income within that bracket's range.

    Args:
        taxable_income: Total taxable income (non-negative).
        filing_status: IRS filing status enum.
        tax_year: Calendar year (must be in SUPPORTED_YEARS).

    Returns:
        Total federal income tax as a Decimal (2 decimal places).

    Raises:
        ValueError: If income is negative or year is unsupported.
    """
    _validate_inputs(taxable_income, filing_status, tax_year)

    if taxable_income == 0:
        return Decimal("0")

    brackets = _get_brackets(tax_year, filing_status, _FEDERAL_BRACKETS)
    total_tax = Decimal("0")

    for i, (threshold, rate) in enumerate(brackets):
        # Determine the ceiling for this bracket
        if i + 1 < len(brackets):
            ceiling = brackets[i + 1][0]
        else:
            ceiling = taxable_income  # No cap on top bracket

        # Income taxed in this bracket
        taxable_in_bracket = min(taxable_income, ceiling) - threshold
        if taxable_in_bracket <= 0:
            break

        total_tax += taxable_in_bracket * rate

    return total_tax.quantize(Decimal("0.01"))


def compute_effective_rate(
    taxable_income: Decimal,
    filing_status: FilingStatus,
    tax_year: int,
) -> Decimal:
    """Compute effective federal income tax rate.

    Effective rate = total_tax / taxable_income.

    Args:
        taxable_income: Total taxable income (non-negative).
        filing_status: IRS filing status enum.
        tax_year: Calendar year (must be in SUPPORTED_YEARS).

    Returns:
        Effective rate as a Decimal. Returns Decimal("0") for zero income.

    Raises:
        ValueError: If income is negative or year is unsupported.
    """
    _validate_inputs(taxable_income, filing_status, tax_year)

    if taxable_income == 0:
        return Decimal("0")

    total_tax = compute_tax_liability(taxable_income, filing_status, tax_year)
    return (total_tax / taxable_income).quantize(Decimal("0.0001"))


def compute_capital_gains_tax(
    lt_gains: Decimal,
    taxable_income: Decimal,
    filing_status: FilingStatus,
    tax_year: int,
) -> Decimal:
    """Compute long-term capital gains tax at preferential rates (0/15/20%).

    **Simplified Model (current implementation)**:
    The applicable rate is determined by the taxpayer's *total* taxable
    income (including gains) and applied uniformly to the full gain amount.
    This is an approximation suitable for quarterly estimation but NOT
    equivalent to the IRS Qualified Dividends and Capital Gain Tax
    Worksheet, which stacks ordinary income first and then layers gains
    on top, potentially splitting gains across two LTCG brackets.

    **Approximation boundary**: When ordinary income places the taxpayer
    near a LTCG threshold, the simplified model can over-tax (e.g.,
    taxing the full gain at 15% when part of it should be at 0%).
    The maximum per-estimate error is bounded by the gain amount × the
    rate differential (typically 15% of gains).

    **Future generalization** (deferred to a dedicated MEU): Accept
    ordinary_income as a separate parameter and implement stacked
    bracket logic per the IRS worksheet.

    Args:
        lt_gains: Long-term capital gains amount. Negative → returns 0.
        taxable_income: Total taxable income (including gains).
        filing_status: IRS filing status enum.
        tax_year: Calendar year (must be in SUPPORTED_YEARS).

    Returns:
        Capital gains tax as a Decimal (2 decimal places).
        Returns Decimal("0") for negative or zero gains.

    Raises:
        ValueError: If taxable_income is negative or year is unsupported.
    """
    _validate_inputs(taxable_income, filing_status, tax_year)

    if lt_gains <= 0:
        return Decimal("0")

    brackets = _get_brackets(tax_year, filing_status, _LTCG_BRACKETS)

    # Find applicable rate based on total taxable income
    applicable_rate = brackets[0][1]
    for threshold, rate in brackets:
        if taxable_income > threshold:
            applicable_rate = rate
        else:
            break

    return (lt_gains * applicable_rate).quantize(Decimal("0.01"))


def compute_combined_rate(
    federal_effective: Decimal,
    state_tax_rate: Decimal,
) -> Decimal:
    """Compute combined federal + state tax rate.

    AC-146.6: State tax is a flat passthrough from TaxProfile.state_tax_rate.

    Args:
        federal_effective: Federal effective tax rate (e.g. Decimal("0.22")).
        state_tax_rate: State flat tax rate (e.g. Decimal("0.05")).

    Returns:
        Combined rate as Decimal (federal + state).

    Raises:
        ValueError: If state_tax_rate is negative.
    """
    if state_tax_rate < 0:
        msg = f"state_tax_rate cannot be negative: {state_tax_rate}"
        raise ValueError(msg)

    return federal_effective + state_tax_rate
