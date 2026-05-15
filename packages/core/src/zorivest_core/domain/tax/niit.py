# packages/core/src/zorivest_core/domain/tax/niit.py
"""MEU-147: Net Investment Income Tax (NIIT) — 3.8% surtax calculator.

The NIIT (IRC §1411) imposes a 3.8% tax on the lesser of:
  - Net investment income, OR
  - The amount by which MAGI exceeds the filing-status threshold.

Thresholds are NOT inflation-adjusted (fixed since 2013):
  - Single:            $200,000
  - Married Joint:     $250,000
  - Married Separate:  $125,000
  - Head of Household: $200,000

Disclaimer: This module provides tax estimation only and does not constitute
tax advice. Consult a qualified tax professional for actual filing.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from zorivest_core.domain.enums import FilingStatus

# ── Constants ────────────────────────────────────────────────────────────

NIIT_RATE = Decimal("0.038")

# IRC §1411(b) — static thresholds, no inflation adjustment
NIIT_THRESHOLDS: dict[FilingStatus, Decimal] = {
    FilingStatus.SINGLE: Decimal("200000"),
    FilingStatus.MARRIED_JOINT: Decimal("250000"),
    FilingStatus.MARRIED_SEPARATE: Decimal("125000"),
    FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("200000"),
}

# Proximity alert triggers when MAGI >= (1 - PROXIMITY_PCT) × threshold
_PROXIMITY_ALERT_PCT = Decimal("0.10")  # 10%


# ── Result types ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NiitResult:
    """Result of NIIT computation."""

    niit_amount: Decimal
    rate: Decimal
    threshold: Decimal
    magi_excess: Decimal
    taxable_base: Decimal  # min(NII, excess)


@dataclass(frozen=True)
class NiitProximityResult:
    """Result of NIIT proximity check."""

    alert: bool
    proximity_pct: Decimal  # MAGI / threshold (0.0 – 1.0+)
    threshold: Decimal
    distance_to_threshold: Decimal  # threshold - MAGI (can be negative)


# ── Public API ───────────────────────────────────────────────────────────


def compute_niit(
    magi: Decimal,
    net_investment_income: Decimal,
    filing_status: FilingStatus,
) -> NiitResult:
    """Compute Net Investment Income Tax (3.8% surtax).

    NIIT = 3.8% × min(NII, MAGI - threshold).

    Args:
        magi: Modified Adjusted Gross Income.
        net_investment_income: Net investment income (interest, dividends,
            capital gains, rental income, etc.).
        filing_status: IRS filing status for threshold lookup.

    Returns:
        NiitResult with computed NIIT amount and components.
    """
    threshold = NIIT_THRESHOLDS[filing_status]
    magi_excess = max(magi - threshold, Decimal("0"))

    if magi_excess == 0 or net_investment_income <= 0:
        return NiitResult(
            niit_amount=Decimal("0"),
            rate=NIIT_RATE,
            threshold=threshold,
            magi_excess=Decimal("0"),
            taxable_base=Decimal("0"),
        )

    taxable_base = min(net_investment_income, magi_excess)
    niit_amount = (taxable_base * NIIT_RATE).quantize(Decimal("0.01"))

    return NiitResult(
        niit_amount=niit_amount,
        rate=NIIT_RATE,
        threshold=threshold,
        magi_excess=magi_excess,
        taxable_base=taxable_base,
    )


def check_niit_proximity(
    magi: Decimal,
    filing_status: FilingStatus,
) -> NiitProximityResult:
    """Check how close MAGI is to the NIIT threshold.

    Alerts when MAGI is within 10% of the threshold (or already above).

    Args:
        magi: Modified Adjusted Gross Income.
        filing_status: IRS filing status for threshold lookup.

    Returns:
        NiitProximityResult with alert flag and proximity percentage.
    """
    threshold = NIIT_THRESHOLDS[filing_status]
    distance = threshold - magi

    if threshold > 0:
        proximity_pct = (magi / threshold).quantize(Decimal("0.01"))
    else:
        proximity_pct = Decimal("1.00")

    # Alert if within 10% of threshold or already above
    alert_threshold = threshold * (Decimal("1") - _PROXIMITY_ALERT_PCT)
    alert = magi >= alert_threshold

    return NiitProximityResult(
        alert=alert,
        proximity_pct=proximity_pct,
        threshold=threshold,
        distance_to_threshold=distance,
    )
