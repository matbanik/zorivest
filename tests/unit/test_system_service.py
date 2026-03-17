# tests/unit/test_system_service.py
"""Tests for SystemService (MEU-12, AC-12.9)."""

from __future__ import annotations

from zorivest_core.domain.calculator import PositionSizeResult
from zorivest_core.services.system_service import SystemService


class TestSystemServiceCalculate:
    """AC-12.9: SystemService.calculate() delegates to calculate_position_size()."""

    def test_calculate_delegates(self) -> None:
        """AC-12.9: delegates to calculate_position_size with correct args."""
        svc = SystemService()
        result = svc.calculate(
            balance=100_000.0,
            risk_pct=1.0,
            entry=150.0,
            stop=145.0,
            target=165.0,
        )

        assert isinstance(result, PositionSizeResult)
        assert result.share_size > 0
        assert result.position_size > 0
        assert result.reward_risk_ratio > 0

    def test_calculate_returns_frozen_dataclass(self) -> None:
        svc = SystemService()
        result = svc.calculate(
            balance=50_000.0,
            risk_pct=2.0,
            entry=100.0,
            stop=95.0,
            target=115.0,
        )
        assert isinstance(result, PositionSizeResult)
        # Value: verify concrete computed values
        assert result.account_risk_1r == 50_000.0 * 0.02  # $1000
        assert result.risk_per_share == 100.0 - 95.0  # $5
        assert result.share_size == 200  # $1000 / $5
        assert result.position_size == 200 * 100.0  # 200 * $100
        assert result.reward_risk_ratio == (115.0 - 100.0) / (100.0 - 95.0)  # 3.0
        assert result.potential_profit == 200 * (115.0 - 100.0)  # $3000
