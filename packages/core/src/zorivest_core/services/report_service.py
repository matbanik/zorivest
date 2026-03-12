# packages/core/src/zorivest_core/services/report_service.py
"""Trade report lifecycle management.

Canon: 03-service-layer.md L387-409 (absorbs TradeReportService + TradePlanService).
Method names follow 04a-api-trades.md L126-151 (authoritative, newer):
  create(), get_for_trade(), update(), delete()
Note: 03-service-layer.md L399-400 uses older create_report()/get_report()
which is stale on this point — 04a is the downstream consumer and takes precedence.

This MEU implements report-only methods; plan/journal methods deferred to MEU-66/117.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING, Any

from zorivest_core.domain.entities import TradeReport

if TYPE_CHECKING:
    from zorivest_core.application.ports import UnitOfWork


class ReportService:
    """Trade documentation: post-trade reports.

    Canon: 03-service-layer.md L387-409 (absorbs TradeReportService + TradePlanService).
    This MEU implements report-only methods; plan/journal methods deferred to MEU-66/117.

    Method names follow 04a-api-trades.md L126-151 (authoritative, newer):
      create(), get_for_trade(), update(), delete()
    Note: 03-service-layer.md L399-400 uses older create_report()/get_report()
    which is stale on this point — 04a is the downstream consumer and takes precedence.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def create(self, trade_id: str, report_data: dict[str, Any]) -> TradeReport:
        """Create a post-trade report for the given trade.

        Raises:
            ValueError: If trade not found or report already exists.
        """
        with self.uow:
            trade = self.uow.trades.get(trade_id)
            if trade is None:
                msg = f"Trade '{trade_id}' not found"
                raise ValueError(msg)

            existing = self.uow.trade_reports.get_for_trade(trade_id)
            if existing is not None:
                msg = f"Report for trade '{trade_id}' already exists"
                raise ValueError(msg)

            report = TradeReport(
                id=0,  # auto-assigned by DB
                trade_id=trade_id,
                setup_quality=report_data.get("setup_quality", 0),
                execution_quality=report_data.get("execution_quality", 0),
                followed_plan=report_data.get("followed_plan", False),
                emotional_state=report_data.get("emotional_state", "neutral"),
                created_at=datetime.now(),
                lessons_learned=report_data.get("lessons_learned", ""),
                tags=report_data.get("tags", []),
            )
            self.uow.trade_reports.save(report)
            self.uow.commit()

            # Re-fetch to hydrate the DB-assigned ID
            hydrated = self.uow.trade_reports.get_for_trade(trade_id)
            return hydrated if hydrated is not None else report

    def get_for_trade(self, trade_id: str) -> TradeReport | None:
        """Fetch TradeReport linked to a specific trade."""
        with self.uow:
            return self.uow.trade_reports.get_for_trade(trade_id)

    def update(self, trade_id: str, updates: dict[str, Any]) -> TradeReport:
        """Update an existing report.

        Raises:
            ValueError: If no report exists for the trade.
        """
        with self.uow:
            existing = self.uow.trade_reports.get_for_trade(trade_id)
            if existing is None:
                msg = f"Report for trade '{trade_id}' not found"
                raise ValueError(msg)

            updated = replace(existing, **updates)
            self.uow.trade_reports.update(updated)
            self.uow.commit()
            return updated

    def delete(self, trade_id: str) -> None:
        """Delete the report for a trade.

        Raises:
            ValueError: If no report exists for the trade.
        """
        with self.uow:
            existing = self.uow.trade_reports.get_for_trade(trade_id)
            if existing is None:
                msg = f"Report for trade '{trade_id}' not found"
                raise ValueError(msg)

            self.uow.trade_reports.delete(existing.id)
            self.uow.commit()
