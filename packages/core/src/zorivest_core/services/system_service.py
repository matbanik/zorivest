"""SystemService — calculator wrapper per matrix item 6.

Source: 03-service-layer.md §SystemService + build-priority-matrix item 6
Delegates to: domain.calculator.calculate_position_size()
"""

from __future__ import annotations

from zorivest_core.domain.calculator import PositionSizeResult, calculate_position_size


class SystemService:
    """System utilities: calculator wrapper.

    Per matrix item 6, this MEU delivers the calculator wrapper only.
    Backup/config logic belongs to Phase 2A BackupService.
    """

    def calculate(
        self,
        balance: float,
        risk_pct: float,
        entry: float,
        stop: float,
        target: float,
    ) -> PositionSizeResult:
        """Delegate to the pure domain calculator function.

        Args:
            balance: Account balance in dollars.
            risk_pct: Risk percentage (e.g. 1.0 for 1%).
            entry: Entry price per share.
            stop: Stop-loss price per share.
            target: Target (take-profit) price per share.

        Returns:
            PositionSizeResult with computed fields.
        """
        return calculate_position_size(
            balance=balance,
            risk_pct=risk_pct,
            entry=entry,
            stop=stop,
            target=target,
        )
