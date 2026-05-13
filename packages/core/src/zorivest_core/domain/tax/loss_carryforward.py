# packages/core/src/zorivest_core/domain/tax/loss_carryforward.py
"""Pure domain function for IRS capital loss carryforward rules.

MEU-127: Applies capital loss netting per IRS Schedule D Part III,
enforces $3K/$1.5K annual deduction cap, and computes remaining
carryforward with character (ST/LT) preservation.

Source: IRS Publication 550, IRS Schedule D instructions
Human-approved: ST-first allocation for deduction (conversation 65dc5cb3, 2026-05-12)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from zorivest_core.domain.enums import FilingStatus

# IRS annual deduction caps
_CAP_DEFAULT = Decimal("3000")
_CAP_MARRIED_SEPARATE = Decimal("1500")


@dataclass(frozen=True)
class CapitalLossResult:
    """Result of capital loss carryforward computation.

    AC-127.1: Contains deductible_loss, remaining carryforwards, and net gains.
    """

    deductible_loss: Decimal
    remaining_st_carryforward: Decimal
    remaining_lt_carryforward: Decimal
    net_st: Decimal
    net_lt: Decimal


def apply_capital_loss_rules(
    st_gains: Decimal,
    lt_gains: Decimal,
    st_carryforward: Decimal,
    lt_carryforward: Decimal,
    filing_status: FilingStatus,
) -> CapitalLossResult:
    """Apply IRS capital loss netting and deduction cap rules.

    Netting order (IRS Schedule D Part III):
    1. ST losses + ST carryforward offset ST gains
    2. LT losses + LT carryforward offset LT gains
    3. Cross-net: excess ST loss offsets LT gains, and vice versa
    4. Apply annual deduction cap ($3K or $1.5K) against ordinary income
    5. Remaining loss carries forward, preserving ST/LT character

    Args:
        st_gains: Short-term gains (negative = current-year ST losses).
        lt_gains: Long-term gains (negative = current-year LT losses).
        st_carryforward: Short-term carryforward from prior year (>= 0).
        lt_carryforward: Long-term carryforward from prior year (>= 0).
        filing_status: IRS filing status for cap determination.

    Returns:
        CapitalLossResult with deductible_loss, remaining carryforwards,
        and net ST/LT amounts.

    Raises:
        ValueError: If carryforward amounts are negative.
    """
    if st_carryforward < 0:
        raise ValueError("ST carryforward must be non-negative")
    if lt_carryforward < 0:
        raise ValueError("LT carryforward must be non-negative")

    # Step 1: Net each pool against its own carryforward
    # Carryforward reduces gains (subtracts from pool)
    net_st = st_gains - st_carryforward
    net_lt = lt_gains - lt_carryforward

    # Step 2: Cross-net — excess losses from one pool offset the other
    if net_st < 0 and net_lt > 0:
        # Excess ST loss offsets LT gains
        combined = net_st + net_lt
        if combined >= 0:
            net_lt = combined
            net_st = Decimal("0")
        else:
            net_lt = Decimal("0")
            net_st = combined  # Still negative
    elif net_lt < 0 and net_st > 0:
        # Excess LT loss offsets ST gains
        combined = net_st + net_lt
        if combined >= 0:
            net_st = combined
            net_lt = Decimal("0")
        else:
            net_st = Decimal("0")
            net_lt = combined  # Still negative

    # Step 3: Determine total net loss (if any)
    total_net_loss = Decimal("0")
    if net_st < 0:
        total_net_loss += abs(net_st)
    if net_lt < 0:
        total_net_loss += abs(net_lt)

    # Step 4: Apply annual deduction cap
    cap = (
        _CAP_MARRIED_SEPARATE
        if filing_status == FilingStatus.MARRIED_SEPARATE
        else _CAP_DEFAULT
    )
    deductible_loss = min(total_net_loss, cap)

    # Step 5: Compute remaining carryforward with character preservation
    # ST-first allocation: deduction eats ST losses first, then LT
    # (Human-approved, conversation 65dc5cb3, 2026-05-12)

    st_loss_portion = abs(net_st) if net_st < 0 else Decimal("0")
    lt_loss_portion = abs(net_lt) if net_lt < 0 else Decimal("0")

    # Deduction consumes ST first
    st_deducted = min(deductible_loss, st_loss_portion)
    lt_deducted = deductible_loss - st_deducted

    remaining_st = st_loss_portion - st_deducted
    remaining_lt = lt_loss_portion - lt_deducted

    # Final net values: negative pools become 0 (loss is tracked in carryforward)
    final_net_st = max(net_st, Decimal("0"))
    final_net_lt = max(net_lt, Decimal("0"))

    return CapitalLossResult(
        deductible_loss=deductible_loss,
        remaining_st_carryforward=remaining_st,
        remaining_lt_carryforward=remaining_lt,
        net_st=final_net_st,
        net_lt=final_net_lt,
    )
