"""Position size calculator tests — MEU-1 acceptance criteria.

Tests written FIRST (Red phase) before any implementation exists.
All values from docs/build-plan/01-domain-layer.md §1.3.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestPositionSizeCalculator:
    """Test the pure calculation logic with known values from the spec."""

    # ── AC-1: Basic calculation matches spec values ──────────────────────

    def test_basic_calculation(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=437_903.03,
            risk_pct=1.0,
            entry=619.61,
            stop=618.61,
            target=620.61,
        )
        assert result.account_risk_1r == pytest.approx(4379.03, abs=0.01)
        assert result.risk_per_share == pytest.approx(1.00, abs=0.01)
        assert result.share_size == 4379
        assert result.position_size == 2713273
        assert result.position_to_account_pct == pytest.approx(619.6, abs=0.01)
        assert result.reward_risk_ratio == 1.00
        assert result.potential_profit == pytest.approx(4379.00, abs=0.01)

    # ── AC-2: Zero entry → zero shares, zero risk per share ─────────────

    def test_zero_entry_returns_zero_shares(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=100_000,
            risk_pct=1.0,
            entry=0.0,
            stop=0.0,
            target=0.0,
        )
        assert result.share_size == 0
        assert result.risk_per_share == 0

    # ── AC-3: Risk % out of range defaults to 1% ────────────────────────

    def test_risk_out_of_range_defaults_to_one_percent(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=100_000,
            risk_pct=200.0,  # > 100%
            entry=100.0,
            stop=99.0,
            target=101.0,
        )
        # Should default to 1%
        assert result.account_risk_1r == pytest.approx(1000.0, abs=0.01)

    def test_risk_zero_defaults_to_one_percent(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=100_000,
            risk_pct=0.0,  # == 0
            entry=100.0,
            stop=99.0,
            target=101.0,
        )
        assert result.account_risk_1r == pytest.approx(1000.0, abs=0.01)

    def test_risk_negative_defaults_to_one_percent(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=100_000,
            risk_pct=-5.0,  # negative
            entry=100.0,
            stop=99.0,
            target=101.0,
        )
        assert result.account_risk_1r == pytest.approx(1000.0, abs=0.01)

    # ── AC-4: entry == stop → zero shares, zero reward/risk ratio ───────

    def test_entry_equals_stop(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=100_000,
            risk_pct=1.0,
            entry=100.0,
            stop=100.0,
            target=105.0,  # entry == stop
        )
        assert result.share_size == 0
        assert result.reward_risk_ratio == 0

    # ── AC-5: Zero balance → 0.0 for position_to_account_pct ────────────

    def test_zero_balance(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=0.0,
            risk_pct=1.0,
            entry=100.0,
            stop=99.0,
            target=101.0,
        )
        assert result.position_to_account_pct == 0.0

    # ── AC-6: PositionSizeResult is a frozen dataclass ───────────────────

    def test_frozen_dataclass(self) -> None:
        from zorivest_core.domain.calculator import calculate_position_size

        result = calculate_position_size(
            balance=100_000,
            risk_pct=1.0,
            entry=100.0,
            stop=99.0,
            target=101.0,
        )
        with pytest.raises(AttributeError):
            result.share_size = 999  # type: ignore[misc]

    # ── AC-7: Implementation imports only __future__, math, dataclasses ──

    def test_import_surface(self) -> None:
        import zorivest_core.domain.calculator as mod
        import ast

        source_file = mod.__file__
        assert source_file is not None

        with open(source_file, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        allowed_modules = {"__future__", "math", "dataclasses"}
        import_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name in allowed_modules, (
                        f"Forbidden import: {alias.name}"
                    )
                    import_count += 1
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    top_module = node.module.split(".")[0]
                    assert top_module in allowed_modules, (
                        f"Forbidden import from: {node.module}"
                    )
                    import_count += 1
        # Value: verify at least 1 import was checked
        assert import_count >= 1, f"Only {import_count} imports found"
