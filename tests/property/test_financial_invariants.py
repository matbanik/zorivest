"""Property-based tests for financial calculation invariants.

Tests calculate_expectancy() and calculate_sqn() hold domain-level
invariants for ALL valid inputs, not just example-based cases.

Source: testing-strategy.md §Hypothesis Property-Based Tests
Phase:  3.1 of Test Rigor Audit
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from zorivest_core.domain.analytics.expectancy import calculate_expectancy
from zorivest_core.domain.analytics.sqn import calculate_sqn
from zorivest_core.domain.entities import Trade
from zorivest_core.domain.enums import TradeAction


# ── Strategies ──────────────────────────────────────────────────────────

# Finite floats suitable for realized_pnl (no NaN, no ±inf)
finite_pnl = st.floats(
    min_value=-1e8, max_value=1e8, allow_nan=False, allow_infinity=False
)

# Non-zero PnL for skip-zero scenarios
nonzero_pnl = finite_pnl.filter(lambda x: x != 0.0)


def make_trade(pnl: float) -> Trade:
    """Build a minimal Trade with the given realized_pnl."""
    return Trade(
        exec_id=f"PROP-{id(pnl)}",
        time=datetime(2025, 7, 1),
        instrument="SPY",
        action=TradeAction.BOT,
        quantity=100.0,
        price=100.0,
        account_id="TEST",
        realized_pnl=pnl,
    )


# ── Expectancy Invariants ───────────────────────────────────────────────


class TestExpectancyInvariants:
    """Invariants for calculate_expectancy()."""

    @given(pnls=st.lists(finite_pnl, min_size=1, max_size=200))
    @settings(max_examples=200)
    def test_expectancy_is_finite(self, pnls: list[float]) -> None:
        """Expectancy must be a finite Decimal for any trade list."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_expectancy(trades)
        assert result.expectancy.is_finite()

    @given(pnls=st.lists(finite_pnl, min_size=1, max_size=200))
    @settings(max_examples=200)
    def test_win_rate_bounded_zero_one(self, pnls: list[float]) -> None:
        """win_rate ∈ [0, 1] for any non-empty trade list."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_expectancy(trades)
        assert Decimal("0") <= result.win_rate <= Decimal("1")

    @given(pnls=st.lists(finite_pnl, min_size=1, max_size=200))
    @settings(max_examples=200)
    def test_kelly_fraction_at_most_one(self, pnls: list[float]) -> None:
        """Kelly fraction ≤ 1.0 for any trade list."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_expectancy(trades)
        assert result.kelly_fraction <= Decimal("1")

    @given(pnls=st.lists(finite_pnl, min_size=1, max_size=200))
    @settings(max_examples=200)
    def test_trade_count_equals_input_length(self, pnls: list[float]) -> None:
        """trade_count must equal the number of input trades."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_expectancy(trades)
        assert result.trade_count == len(pnls)

    @given(
        pnls=st.lists(
            st.floats(min_value=0.01, max_value=1e6, allow_nan=False),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_all_wins_positive_expectancy(self, pnls: list[float]) -> None:
        """When every trade is a winner, expectancy > 0."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_expectancy(trades)
        assert result.expectancy > 0

    @given(
        pnls=st.lists(
            st.floats(min_value=-1e6, max_value=-0.01, allow_nan=False),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_all_losses_nonpositive_expectancy(self, pnls: list[float]) -> None:
        """When every trade is a loser, expectancy ≤ 0."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_expectancy(trades)
        assert result.expectancy <= 0

    @given(pnls=st.lists(finite_pnl, min_size=1, max_size=200))
    @settings(max_examples=200)
    def test_profit_factor_nonnegative(self, pnls: list[float]) -> None:
        """profit_factor ≥ 0 for any trade list."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_expectancy(trades)
        assert result.profit_factor >= 0

    def test_empty_list_returns_zero(self) -> None:
        """Empty input → all-zero result."""
        result = calculate_expectancy([])
        assert result.trade_count == 0
        assert result.expectancy == Decimal("0")
        assert result.win_rate == Decimal("0")


# ── SQN Invariants ──────────────────────────────────────────────────────


class TestSQNInvariants:
    """Invariants for calculate_sqn()."""

    @given(pnls=st.lists(finite_pnl, min_size=2, max_size=200))
    @settings(max_examples=200)
    def test_sqn_is_finite(self, pnls: list[float]) -> None:
        """SQN must be a finite Decimal."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_sqn(trades)
        assert result.sqn.is_finite()

    @given(pnls=st.lists(nonzero_pnl, min_size=3, max_size=200))
    @settings(max_examples=200)
    def test_sqn_sign_matches_mean_sign(self, pnls: list[float]) -> None:
        """SQN sign matches mean_r sign when σ > 0.

        Note: When std_r >> mean_r (e.g., std=99M, mean=22), SQN ≈ 0.0000004
        which rounds to 0.0 at 6 decimal places.  We accept 0 as consistent
        with both positive and negative mean in that edge case.
        """
        trades = [make_trade(p) for p in pnls]
        result = calculate_sqn(trades)
        if result.std_r > 0:
            # sign(SQN) == sign(mean_r), or zero due to precision rounding
            if result.mean_r > 0:
                assert result.sqn >= 0
            elif result.mean_r < 0:
                assert result.sqn <= 0

    def test_fewer_than_two_trades_returns_zero(self) -> None:
        """< 2 trades → SQN = 0 (Poor)."""
        result_empty = calculate_sqn([])
        assert result_empty.sqn == Decimal("0")
        assert result_empty.grade == "Poor"

        result_one = calculate_sqn([make_trade(100.0)])
        assert result_one.sqn == Decimal("0")

    @given(pnls=st.lists(finite_pnl, min_size=2, max_size=200))
    @settings(max_examples=200)
    def test_grade_is_valid_van_tharp(self, pnls: list[float]) -> None:
        """Grade is always one of the Van Tharp categories."""
        valid_grades = {
            "Poor",
            "Average",
            "Good",
            "Excellent",
            "Superb",
            "Holy Grail",
            "Unicorn",
        }
        trades = [make_trade(p) for p in pnls]
        result = calculate_sqn(trades)
        assert result.grade in valid_grades

    @given(pnls=st.lists(finite_pnl, min_size=2, max_size=200))
    @settings(max_examples=200)
    def test_trade_count_matches(self, pnls: list[float]) -> None:
        """trade_count reflects input length."""
        trades = [make_trade(p) for p in pnls]
        result = calculate_sqn(trades)
        assert result.trade_count == len(pnls)

    @given(
        pnl=st.integers(min_value=-10000, max_value=10000),
        n=st.integers(min_value=2, max_value=50),
    )
    @settings(max_examples=100)
    def test_identical_trades_zero_std(self, pnl: int, n: int) -> None:
        """All identical PnL → std_r=0 → SQN=0."""
        trades = [make_trade(float(pnl)) for _ in range(n)]
        result = calculate_sqn(trades)
        assert result.std_r == Decimal("0")
        assert result.sqn == Decimal("0")
