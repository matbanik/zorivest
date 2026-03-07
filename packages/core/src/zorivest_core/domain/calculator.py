"""Position size calculator — pure math, zero dependencies.

Accepts account balance, risk percentage, entry/stop/target prices and
returns a frozen result dataclass with seven computed fields.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSizeResult:
    """Immutable result of a position size calculation."""

    account_risk_1r: float
    risk_per_share: float
    share_size: int
    position_size: int
    position_to_account_pct: float
    reward_risk_ratio: float
    potential_profit: float


def calculate_position_size(
    balance: float,
    risk_pct: float,
    entry: float,
    stop: float,
    target: float,
) -> PositionSizeResult:
    """Pure function — no side effects, no I/O, no dependencies.

    Args:
        balance: Account balance in dollars.
        risk_pct: Risk percentage (e.g. 1.0 for 1%). Clamped to 1% if out of
            the valid range (0, 100].
        entry: Entry price per share.
        stop: Stop-loss price per share.
        target: Target (take-profit) price per share.

    Returns:
        A frozen ``PositionSizeResult`` with all computed fields.
    """
    risk_decimal = risk_pct / 100.0
    if not (0.0001 <= risk_decimal <= 1.0):
        risk_decimal = 0.01

    acc_1r = balance * risk_decimal
    risk_per_share = abs(entry - stop) if entry > 0 and stop > 0 else 0.0

    share_size = math.floor(acc_1r / risk_per_share) if risk_per_share > 0 else 0
    position_size = math.ceil(entry * share_size)

    potential_per_share = abs(target - entry) if target > 0 else 0.0
    reward_risk = (potential_per_share / risk_per_share) if risk_per_share > 0 else 0.0
    reward_risk = math.floor(reward_risk * 100) / 100

    potential_profit = potential_per_share * share_size

    pos_to_acct = (position_size / balance * 100) if balance > 0 else 0.0
    pos_to_acct = math.floor(pos_to_acct * 100) / 100

    return PositionSizeResult(
        account_risk_1r=acc_1r,
        risk_per_share=risk_per_share,
        share_size=share_size,
        position_size=position_size,
        position_to_account_pct=pos_to_acct,
        reward_risk_ratio=reward_risk,
        potential_profit=potential_profit,
    )
