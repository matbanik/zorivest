# packages/core/src/zorivest_core/domain/analytics/results.py
"""Analytics result types — frozen dataclasses matching 03-service-layer.md."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExpectancyResult:
    """Result of trade expectancy analysis."""

    expectancy: Decimal
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    kelly_fraction: Decimal
    trade_count: int


@dataclass(frozen=True)
class DrawdownResult:
    """Result of Monte Carlo drawdown simulation."""

    probability_table: dict[str, Decimal]
    max_drawdown_median: Decimal
    recommended_risk_pct: Decimal
    simulations_run: int


@dataclass(frozen=True)
class SQNResult:
    """System Quality Number result."""

    sqn: Decimal
    grade: str
    trade_count: int
    mean_r: Decimal
    std_r: Decimal


@dataclass(frozen=True)
class ExcursionResult:
    """Maximum Favorable/Adverse Excursion result."""

    mfe: Decimal
    mae: Decimal
    bso: Decimal
    holding_bars: int


@dataclass(frozen=True)
class QualityResult:
    """Execution quality score result."""

    score: Decimal
    grade: str
    slippage_estimate: Decimal


@dataclass(frozen=True)
class PFOFResult:
    """Payment for Order Flow analysis result."""

    estimated_cost: Decimal
    routing_type: str
    confidence: str
    period: str


@dataclass(frozen=True)
class CostResult:
    """Hidden cost analysis result."""

    total_hidden_cost: Decimal
    pfof_component: Decimal
    fee_component: Decimal
    period: str


@dataclass(frozen=True)
class StrategyResult:
    """Per-strategy P&L breakdown result."""

    strategy_name: str
    total_pnl: Decimal
    trade_count: int
    win_rate: Decimal
