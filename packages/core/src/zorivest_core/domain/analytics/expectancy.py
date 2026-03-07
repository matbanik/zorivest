# packages/core/src/zorivest_core/domain/analytics/expectancy.py
"""Calculate trade expectancy, profit factor, and Kelly fraction."""

from __future__ import annotations

from decimal import Decimal

from zorivest_core.domain.analytics.results import ExpectancyResult
from zorivest_core.domain.entities import Trade


def calculate_expectancy(trades: list[Trade]) -> ExpectancyResult:
    """Compute expectancy metrics for a list of trades.

    Formula: expectancy = (win_rate × avg_win) - (loss_rate × avg_loss)
    Source: Van Tharp, Trade Your Way to Financial Freedom, 3rd ed., ch. 7
    """
    if not trades:
        return ExpectancyResult(
            expectancy=Decimal("0"),
            win_rate=Decimal("0"),
            avg_win=Decimal("0"),
            avg_loss=Decimal("0"),
            profit_factor=Decimal("0"),
            kelly_fraction=Decimal("0"),
            trade_count=0,
        )

    total = len(trades)
    wins = [t for t in trades if t.realized_pnl > 0]
    losses = [t for t in trades if t.realized_pnl < 0]

    win_count = len(wins)
    loss_count = len(losses)

    win_rate = Decimal(str(win_count)) / Decimal(str(total))
    loss_rate = Decimal("1") - win_rate

    gross_wins = sum(Decimal(str(t.realized_pnl)) for t in wins)
    gross_losses = sum(Decimal(str(t.realized_pnl)) for t in losses)

    avg_win = gross_wins / Decimal(str(win_count)) if win_count > 0 else Decimal("0")
    avg_loss = (
        abs(gross_losses) / Decimal(str(loss_count)) if loss_count > 0 else Decimal("0")
    )

    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

    # Profit factor = gross_wins / abs(gross_losses)
    profit_factor = (
        gross_wins / abs(gross_losses) if gross_losses != 0 else Decimal("0")
    )

    # Kelly fraction = win_rate - (loss_rate / payoff_ratio)
    payoff_ratio = avg_win / avg_loss if avg_loss != 0 else Decimal("0")
    kelly_fraction = (
        win_rate - (loss_rate / payoff_ratio) if payoff_ratio != 0 else Decimal("0")
    )

    return ExpectancyResult(
        expectancy=expectancy,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        kelly_fraction=kelly_fraction,
        trade_count=total,
    )
