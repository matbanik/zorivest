# tests/unit/test_analytics.py
"""MEU-8: Analytics — tests for AC-1 through AC-19."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import inspect

import pytest

from zorivest_core.domain.analytics.expectancy import calculate_expectancy
from zorivest_core.domain.analytics.results import (
    CostResult,
    DrawdownResult,
    ExcursionResult,
    ExpectancyResult,
    PFOFResult,
    QualityResult,
    SQNResult,
    StrategyResult,
)
from zorivest_core.domain.analytics.sqn import calculate_sqn
from zorivest_core.domain.entities import Trade
from zorivest_core.domain.enums import TradeAction

pytestmark = pytest.mark.unit


def _make_trade(pnl: float, exec_id: str = "T") -> Trade:
    """Helper to create a Trade with a given realized_pnl."""
    return Trade(
        exec_id=exec_id,
        time=datetime(2025, 1, 1),
        instrument="AAPL",
        action=TradeAction.BOT,
        quantity=100.0,
        price=150.0,
        account_id="ACC-1",
        realized_pnl=pnl,
    )


# ── AC-1: ExpectancyResult ──────────────────────────────────────────────


class TestExpectancyResult:
    """AC-1: ExpectancyResult frozen dataclass."""

    def test_expectancy_result_fields(self) -> None:
        """AC-1: ExpectancyResult has all specified fields."""
        r = ExpectancyResult(
            expectancy=Decimal("1.5"),
            win_rate=Decimal("0.6"),
            avg_win=Decimal("500"),
            avg_loss=Decimal("200"),
            profit_factor=Decimal("2.5"),
            kelly_fraction=Decimal("0.2"),
            trade_count=100,
        )
        assert r.expectancy == Decimal("1.5")
        assert r.trade_count == 100

    def test_expectancy_result_is_frozen(self) -> None:
        """AC-9: ExpectancyResult is frozen."""
        r = ExpectancyResult(
            expectancy=Decimal("0"),
            win_rate=Decimal("0"),
            avg_win=Decimal("0"),
            avg_loss=Decimal("0"),
            profit_factor=Decimal("0"),
            kelly_fraction=Decimal("0"),
            trade_count=0,
        )
        with pytest.raises(AttributeError):
            r.expectancy = Decimal("999")  # type: ignore[misc]


# ── AC-2: SQNResult ─────────────────────────────────────────────────────


class TestSQNResult:
    """AC-2: SQNResult frozen dataclass."""

    def test_sqn_result_fields(self) -> None:
        """AC-2: SQNResult has all specified fields."""
        r = SQNResult(
            sqn=Decimal("2.5"),
            grade="Excellent",
            trade_count=50,
            mean_r=Decimal("0.5"),
            std_r=Decimal("0.2"),
        )
        assert r.sqn == Decimal("2.5")
        assert r.grade == "Excellent"

    def test_sqn_result_is_frozen(self) -> None:
        """AC-9: SQNResult is frozen."""
        r = SQNResult(
            sqn=Decimal("0"),
            grade="Poor",
            trade_count=0,
            mean_r=Decimal("0"),
            std_r=Decimal("0"),
        )
        with pytest.raises(AttributeError):
            r.grade = "changed"  # type: ignore[misc]


# ── AC-3: StrategyResult ────────────────────────────────────────────────


class TestStrategyResult:
    """AC-3: StrategyResult frozen dataclass."""

    def test_strategy_result_fields(self) -> None:
        """AC-3: StrategyResult has all specified fields."""
        r = StrategyResult(
            strategy_name="Momentum",
            total_pnl=Decimal("5000"),
            trade_count=25,
            win_rate=Decimal("0.64"),
        )
        assert r.strategy_name == "Momentum"
        assert r.total_pnl == Decimal("5000")

    def test_strategy_result_is_frozen(self) -> None:
        """AC-9: StrategyResult is frozen."""
        r = StrategyResult(
            strategy_name="X",
            total_pnl=Decimal("0"),
            trade_count=0,
            win_rate=Decimal("0"),
        )
        with pytest.raises(AttributeError):
            r.strategy_name = "Y"  # type: ignore[misc]


# ── AC-4 through AC-8: Out-of-scope result types ────────────────────────


class TestOutOfScopeResultTypes:
    """AC-4 through AC-8: Verify pure type definitions exist and are frozen."""

    def test_drawdown_result(self) -> None:
        """AC-4: DrawdownResult can be instantiated."""
        r = DrawdownResult(
            probability_table={"5%": Decimal("0.10")},
            max_drawdown_median=Decimal("0.15"),
            recommended_risk_pct=Decimal("0.02"),
            simulations_run=10000,
        )
        assert r.simulations_run == 10000

    def test_excursion_result(self) -> None:
        """AC-5: ExcursionResult can be instantiated."""
        r = ExcursionResult(
            mfe=Decimal("500"),
            mae=Decimal("200"),
            bso=Decimal("0.7"),
            holding_bars=15,
        )
        assert r.holding_bars == 15

    def test_quality_result(self) -> None:
        """AC-6: QualityResult can be instantiated."""
        r = QualityResult(
            score=Decimal("85"),
            grade="A",
            slippage_estimate=Decimal("0.05"),
        )
        assert r.grade == "A"

    def test_pfof_result(self) -> None:
        """AC-7: PFOFResult can be instantiated."""
        r = PFOFResult(
            estimated_cost=Decimal("2.50"),
            routing_type="pfof",
            confidence="high",
            period="2025-Q1",
        )
        assert r.routing_type == "pfof"

    def test_cost_result(self) -> None:
        """AC-8: CostResult can be instantiated."""
        r = CostResult(
            total_hidden_cost=Decimal("10.00"),
            pfof_component=Decimal("2.50"),
            fee_component=Decimal("7.50"),
            period="2025-Q1",
        )
        assert r.total_hidden_cost == Decimal("10.00")

    def test_all_out_of_scope_frozen(self) -> None:
        """AC-9: All out-of-scope types are frozen."""
        dr = DrawdownResult(
            probability_table={},
            max_drawdown_median=Decimal("0"),
            recommended_risk_pct=Decimal("0"),
            simulations_run=0,
        )
        with pytest.raises(AttributeError):
            dr.simulations_run = 1  # type: ignore[misc]


# ── AC-10 through AC-12: calculate_expectancy ────────────────────────────


class TestCalculateExpectancy:
    """AC-10-13: Expectancy function tests."""

    def test_empty_trades_returns_zero(self) -> None:
        """AC-13: Empty trades list returns zero-value result."""
        result = calculate_expectancy([])
        assert result.trade_count == 0
        assert result.expectancy == Decimal("0")
        assert result.win_rate == Decimal("0")
        assert result.profit_factor == Decimal("0")
        assert result.kelly_fraction == Decimal("0")

    def test_all_winning_trades(self) -> None:
        """AC-10, AC-11: Expectancy with all winning trades."""
        trades = [
            _make_trade(100.0, "T1"),
            _make_trade(200.0, "T2"),
            _make_trade(150.0, "T3"),
        ]
        result = calculate_expectancy(trades)
        assert result.trade_count == 3
        assert result.win_rate == Decimal("1")
        assert result.avg_win == Decimal("150")
        assert result.avg_loss == Decimal("0")
        # profit_factor = 0 when no losses (gross_losses = 0)
        assert result.profit_factor == Decimal("0")

    def test_all_losing_trades(self) -> None:
        """AC-10: Expectancy with all losing trades."""
        trades = [
            _make_trade(-100.0, "T1"),
            _make_trade(-200.0, "T2"),
        ]
        result = calculate_expectancy(trades)
        assert result.trade_count == 2
        assert result.win_rate == Decimal("0")
        assert result.avg_loss == Decimal("150")

    def test_mixed_trades_expectancy(self) -> None:
        """AC-10, AC-11, AC-12: Mixed trades produce correct metrics."""
        trades = [
            _make_trade(200.0, "T1"),  # win
            _make_trade(300.0, "T2"),  # win
            _make_trade(-100.0, "T3"),  # loss
            _make_trade(-50.0, "T4"),  # loss
        ]
        result = calculate_expectancy(trades)
        assert result.trade_count == 4
        assert result.win_rate == Decimal("0.5")
        assert result.avg_win == Decimal("250")
        assert result.avg_loss == Decimal("75")

        # profit_factor = 500 / 150 ≈ 3.333...
        assert result.profit_factor > Decimal("3")

        # kelly_fraction should be positive for this profitable system
        assert result.kelly_fraction > Decimal("0")

    def test_breakeven_trade_excluded_from_wins_and_losses(self) -> None:
        """AC-10: Trades with realized_pnl=0 are neither wins nor losses."""
        trades = [
            _make_trade(100.0, "T1"),
            _make_trade(0.0, "T2"),  # breakeven
            _make_trade(-50.0, "T3"),
        ]
        result = calculate_expectancy(trades)
        assert result.trade_count == 3
        # win_rate = 1/3 (only T1 is a win)
        expected_win_rate = Decimal("1") / Decimal("3")
        assert abs(result.win_rate - expected_win_rate) < Decimal("0.001")


# ── AC-14 through AC-17: calculate_sqn ───────────────────────────────────


class TestCalculateSQN:
    """AC-14-17: SQN function tests."""

    def test_empty_trades_returns_zero(self) -> None:
        """AC-17: Fewer than 2 trades returns zero result."""
        result = calculate_sqn([])
        assert result.trade_count == 0
        assert result.sqn == Decimal("0")
        assert result.grade == "Poor"

    def test_single_trade_returns_zero(self) -> None:
        """AC-17: Single trade returns zero (need ≥2 for std)."""
        result = calculate_sqn([_make_trade(100.0, "T1")])
        assert result.trade_count == 1
        assert result.sqn == Decimal("0")

    def test_identical_trades_zero_std(self) -> None:
        """AC-17: All identical R-multiples → std=0 → SQN=0."""
        trades = [_make_trade(100.0, f"T{i}") for i in range(5)]
        result = calculate_sqn(trades)
        assert result.std_r == Decimal("0")
        assert result.sqn == Decimal("0")

    def test_positive_sqn(self) -> None:
        """AC-14, AC-15: SQN with varied profitable trades."""
        trades = [
            _make_trade(100.0, "T1"),
            _make_trade(150.0, "T2"),
            _make_trade(50.0, "T3"),
            _make_trade(200.0, "T4"),
        ]
        result = calculate_sqn(trades)
        assert result.trade_count == 4
        assert result.sqn > Decimal("0")
        assert result.mean_r > Decimal("0")
        assert result.std_r > Decimal("0")

    def test_sqn_grade_poor(self) -> None:
        """AC-16: SQN < 1.6 grades as Poor."""
        # Trades with high variance relative to mean
        trades = [
            _make_trade(10.0, "T1"),
            _make_trade(-8.0, "T2"),
            _make_trade(5.0, "T3"),
            _make_trade(-7.0, "T4"),
        ]
        result = calculate_sqn(trades)
        # With low mean and high std, SQN should be low
        assert result.grade == "Poor"

    def test_sqn_grade_table(self) -> None:
        """AC-16: Verify all grade boundaries exist in the grading function."""
        from zorivest_core.domain.analytics.sqn import _grade_sqn

        assert _grade_sqn(0.5) == "Poor"
        assert _grade_sqn(1.6) == "Average"
        assert _grade_sqn(2.0) == "Good"
        assert _grade_sqn(2.5) == "Excellent"
        assert _grade_sqn(3.0) == "Superb"
        assert _grade_sqn(5.0) == "Holy Grail"
        assert _grade_sqn(7.0) == "Unicorn"
        assert _grade_sqn(10.0) == "Unicorn"


# ── AC-18, AC-19: Module imports ─────────────────────────────────────────


class TestAnalyticsModuleImports:
    """AC-18, AC-19: Import constraints."""

    def test_results_module_exports(self) -> None:
        """AC-18: results module has all 8 result types."""
        import zorivest_core.domain.analytics.results as mod

        expected_names = [
            "ExpectancyResult",
            "SQNResult",
            "StrategyResult",
            "DrawdownResult",
            "ExcursionResult",
            "QualityResult",
            "PFOFResult",
            "CostResult",
        ]
        for name in expected_names:
            assert hasattr(mod, name), f"Missing: {name}"
            cls = getattr(mod, name)
            assert isinstance(cls, type), f"{name} is not a class"
            # Value: verify each is a dataclass with fields
            assert hasattr(cls, "__dataclass_fields__"), f"{name} is not a dataclass"
            assert len(cls.__dataclass_fields__) >= 2, (
                f"{name} has fewer than 2 fields: {list(cls.__dataclass_fields__)}"
            )

    def test_results_module_no_unexpected_exports(self) -> None:
        """AC-18: results module has no unexpected exports."""
        import zorivest_core.domain.analytics.results as mod

        public = {n for n in dir(mod) if not n.startswith("_")}
        expected = {
            "ExpectancyResult",
            "SQNResult",
            "StrategyResult",
            "DrawdownResult",
            "ExcursionResult",
            "QualityResult",
            "PFOFResult",
            "CostResult",
            "dataclass",
            "Decimal",
            "annotations",
        }
        unexpected = public - expected
        assert not unexpected, f"Unexpected exports: {unexpected}"

    def test_expectancy_module_exports(self) -> None:
        """AC-19: expectancy module has calculate_expectancy."""
        import zorivest_core.domain.analytics.expectancy as mod

        assert hasattr(mod, "calculate_expectancy")
        assert callable(mod.calculate_expectancy)
        # Value: verify function signature accepts trades parameter
        sig = inspect.signature(mod.calculate_expectancy)
        param_names = list(sig.parameters.keys())
        assert "trades" in param_names, f"Expected 'trades' param, got {param_names}"

    def test_sqn_module_exports(self) -> None:
        """AC-19: sqn module has calculate_sqn."""
        import zorivest_core.domain.analytics.sqn as mod

        assert hasattr(mod, "calculate_sqn")
        assert callable(mod.calculate_sqn)
        # Value: verify function signature accepts trades parameter
        sig = inspect.signature(mod.calculate_sqn)
        param_names = list(sig.parameters.keys())
        assert "trades" in param_names, f"Expected 'trades' param, got {param_names}"
