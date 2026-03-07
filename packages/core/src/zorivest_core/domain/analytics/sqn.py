# packages/core/src/zorivest_core/domain/analytics/sqn.py
"""Calculate System Quality Number (SQN) and grade."""

from __future__ import annotations

import math
from decimal import Decimal

from zorivest_core.domain.analytics.results import SQNResult
from zorivest_core.domain.entities import Trade


def _grade_sqn(sqn_value: float) -> str:
    """Van Tharp SQN grading scale.

    Source: https://www.vantharp.com/sqn
    """
    if sqn_value < 1.6:
        return "Poor"
    if sqn_value < 2.0:
        return "Average"
    if sqn_value < 2.5:
        return "Good"
    if sqn_value < 3.0:
        return "Excellent"
    if sqn_value < 5.0:
        return "Superb"
    if sqn_value < 7.0:
        return "Holy Grail"
    return "Unicorn"


def calculate_sqn(trades: list[Trade]) -> SQNResult:
    """Compute System Quality Number for a list of trades.

    Formula: SQN = (mean_R / std_R) × √n
    Source: Van Tharp, Trade Your Way to Financial Freedom, ch. 15

    R-multiples are derived from realized_pnl on each trade.
    """
    if len(trades) < 2:
        return SQNResult(
            sqn=Decimal("0"),
            grade="Poor",
            trade_count=len(trades),
            mean_r=Decimal("0"),
            std_r=Decimal("0"),
        )

    r_values = [t.realized_pnl for t in trades]
    n = len(r_values)

    mean_r = sum(r_values) / n

    variance = sum((r - mean_r) ** 2 for r in r_values) / (n - 1)
    std_r = math.sqrt(variance)

    if std_r == 0:
        return SQNResult(
            sqn=Decimal("0"),
            grade="Poor",
            trade_count=n,
            mean_r=Decimal(str(mean_r)),
            std_r=Decimal("0"),
        )

    sqn_value = (mean_r / std_r) * math.sqrt(n)
    grade = _grade_sqn(sqn_value)

    return SQNResult(
        sqn=Decimal(str(round(sqn_value, 6))),
        grade=grade,
        trade_count=n,
        mean_r=Decimal(str(round(mean_r, 6))),
        std_r=Decimal(str(round(std_r, 6))),
    )
