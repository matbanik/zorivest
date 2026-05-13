# packages/core/src/zorivest_core/domain/tax/option_pairing.py
"""Pure domain functions for options assignment/exercise cost basis pairing.

MEU-128: Parses normalized option symbols and adjusts stock cost basis
for four IRS paths (short put/call assignment, long call/put exercise).

Source: IRS Publication 550 §Puts and Calls; domain-model-reference.md A4
Local Canon: Side derived from option_trade.action (BOT=holder, SLD=writer)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from zorivest_core.domain.entities import TaxLot, Trade
from zorivest_core.domain.enums import TradeAction
from zorivest_core.domain.exceptions import BusinessRuleError


# ── AssignmentType enum ──────────────────────────────────────────────────


class AssignmentType(StrEnum):
    """Assignment/exercise type for option-to-stock pairing.

    Local Canon: Consistency with TradeAction enforced in adjust_basis_for_assignment.
    """

    WRITTEN_PUT_ASSIGNMENT = "WRITTEN_PUT_ASSIGNMENT"  # SLD put → assigned
    WRITTEN_CALL_ASSIGNMENT = "WRITTEN_CALL_ASSIGNMENT"  # SLD call → assigned
    LONG_CALL_EXERCISE = "LONG_CALL_EXERCISE"  # BOT call → exercised
    LONG_PUT_EXERCISE = "LONG_PUT_EXERCISE"  # BOT put → exercised


# ── Required action for each assignment type ─────────────────────────────


_REQUIRED_ACTION: dict[AssignmentType, TradeAction] = {
    AssignmentType.WRITTEN_PUT_ASSIGNMENT: TradeAction.SLD,
    AssignmentType.WRITTEN_CALL_ASSIGNMENT: TradeAction.SLD,
    AssignmentType.LONG_CALL_EXERCISE: TradeAction.BOT,
    AssignmentType.LONG_PUT_EXERCISE: TradeAction.BOT,
}

# Required option put/call kind for each assignment type
_REQUIRED_PUT_CALL: dict[AssignmentType, str] = {
    AssignmentType.WRITTEN_PUT_ASSIGNMENT: "P",
    AssignmentType.WRITTEN_CALL_ASSIGNMENT: "C",
    AssignmentType.LONG_CALL_EXERCISE: "C",
    AssignmentType.LONG_PUT_EXERCISE: "P",
}


# ── AC-128.7: OptionDetails frozen dataclass ─────────────────────────────


@dataclass(frozen=True)
class OptionDetails:
    """Parsed option symbol details.

    AC-128.7: Frozen dataclass with underlying, expiry, put_call, strike.
    """

    underlying: str
    expiry: date
    put_call: str  # "C" | "P"
    strike: Decimal


# ── Result type for adjust_basis_for_assignment ──────────────────────────


@dataclass(frozen=True)
class AdjustedBasisResult:
    """Result of cost basis adjustment for option assignment/exercise."""

    adjusted_cost_basis: Decimal
    adjusted_proceeds: Decimal
    premium_total: Decimal
    assignment_type: AssignmentType


# ── AC-128.1: parse_option_symbol ────────────────────────────────────────


def parse_option_symbol(instrument: str) -> OptionDetails | None:
    """Parse a normalized option symbol into its components.

    AC-128.1: Targets the normalized format produced by IBKR/TOS adapters:
    'UNDERLYING YYMMDD C/P STRIKE' (space-separated).

    Returns None for non-option strings, malformed dates, or raw OCC symbols.

    Args:
        instrument: Instrument string (e.g., 'AAPL 260320 C 200').

    Returns:
        OptionDetails if valid normalized option, None otherwise.
    """
    if not instrument:
        return None

    parts = instrument.split()
    if len(parts) != 4:
        return None

    underlying, date_str, put_call, strike_str = parts

    # Validate put/call
    if put_call not in ("C", "P"):
        return None

    # Parse date: YYMMDD
    if len(date_str) != 6:
        return None
    try:
        year = 2000 + int(date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        expiry = date(year, month, day)
    except (ValueError, OverflowError):
        return None

    # Parse strike
    try:
        strike = Decimal(strike_str)
    except Exception:
        return None

    return OptionDetails(
        underlying=underlying,
        expiry=expiry,
        put_call=put_call,
        strike=strike,
    )


# ── AC-128.2–128.5, AC-128.9: adjust_basis_for_assignment ───────────────


def adjust_basis_for_assignment(
    stock_lot: TaxLot,
    option_trade: Trade,
    assignment_type: AssignmentType,
) -> AdjustedBasisResult:
    """Adjust stock lot cost basis or proceeds for option assignment/exercise.

    Four IRS paths (IRS Pub 550 §Puts and Calls):
    1. WRITTEN_PUT_ASSIGNMENT: premium reduces stock cost basis
    2. WRITTEN_CALL_ASSIGNMENT: premium increases amount realized
    3. LONG_CALL_EXERCISE: premium added to stock cost basis
    4. LONG_PUT_EXERCISE: premium reduces amount realized

    Side derived from option_trade.action (Local Canon):
    - SLD (writer) → WRITTEN_PUT/CALL
    - BOT (holder) → LONG_CALL/PUT

    Args:
        stock_lot: The stock TaxLot being adjusted.
        option_trade: The option Trade providing premium information.
        assignment_type: Which IRS adjustment path to apply.

    Returns:
        AdjustedBasisResult with adjusted cost basis and/or proceeds.

    Raises:
        BusinessRuleError: If assignment_type inconsistent with trade action,
            or ticker mismatch between option underlying and stock lot.
    """
    # AC-128.9: Validate action consistency
    required_action = _REQUIRED_ACTION[assignment_type]
    if option_trade.action != required_action:
        raise BusinessRuleError(
            f"Option trade action '{option_trade.action}' is inconsistent with "
            f"assignment type '{assignment_type}' — expected '{required_action}'"
        )

    # Validate ticker match — parse option to get underlying
    option_details = parse_option_symbol(option_trade.instrument)
    if option_details is not None:
        underlying = option_details.underlying
    else:
        # If unparseable, use the raw instrument for comparison
        underlying = option_trade.instrument

    if underlying != stock_lot.ticker:
        raise BusinessRuleError(
            f"Option underlying ticker '{underlying}' does not match "
            f"stock lot ticker '{stock_lot.ticker}'"
        )

    # F2 Fix: Validate put_call matches assignment type
    if option_details is not None:
        required_pc = _REQUIRED_PUT_CALL[assignment_type]
        if option_details.put_call != required_pc:
            raise BusinessRuleError(
                f"Option put_call '{option_details.put_call}' is incompatible with "
                f"assignment type '{assignment_type}' — expected '{required_pc}'"
            )

    # Calculate total premium (option price × 100 shares per contract × quantity)
    shares_per_contract = 100
    premium_total = (
        Decimal(str(option_trade.price))
        * Decimal(str(shares_per_contract))
        * Decimal(str(option_trade.quantity))
    )

    # Per-share premium adjustment
    per_share_premium = premium_total / Decimal(str(stock_lot.quantity))

    adjusted_basis = stock_lot.cost_basis
    adjusted_proceeds = stock_lot.proceeds

    if assignment_type == AssignmentType.WRITTEN_PUT_ASSIGNMENT:
        # AC-128.2: Premium received reduces cost basis
        adjusted_basis = stock_lot.cost_basis - per_share_premium
    elif assignment_type == AssignmentType.WRITTEN_CALL_ASSIGNMENT:
        # AC-128.3: Premium received increases amount realized
        adjusted_proceeds = stock_lot.proceeds + per_share_premium
    elif assignment_type == AssignmentType.LONG_CALL_EXERCISE:
        # AC-128.4: Premium paid added to cost basis
        adjusted_basis = stock_lot.cost_basis + per_share_premium
    elif assignment_type == AssignmentType.LONG_PUT_EXERCISE:
        # AC-128.5: Premium paid reduces amount realized
        adjusted_proceeds = stock_lot.proceeds - per_share_premium

    return AdjustedBasisResult(
        adjusted_cost_basis=adjusted_basis,
        adjusted_proceeds=adjusted_proceeds,
        premium_total=premium_total,
        assignment_type=assignment_type,
    )
