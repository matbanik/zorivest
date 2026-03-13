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

from zorivest_core.domain.entities import TradePlan, TradeReport

if TYPE_CHECKING:
    from zorivest_core.application.ports import UnitOfWork


class ReportService:
    """Trade documentation: post-trade reports and pre-trade plans.

    Canon: 03-service-layer.md L387-409 (absorbs TradeReportService + TradePlanService).
    Method names follow 04a-api-trades.md L126-151 (authoritative, newer):
      create(), get_for_trade(), update(), delete()
    Plan methods added in MEU-66: create_plan(), get_plan(), list_plans(), update_plan()
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    # ── Report methods ──────────────────────────────────────────────────

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

    # ── Plan methods (MEU-66) ───────────────────────────────────────────

    def create_plan(self, plan_data: dict[str, Any]) -> TradePlan:
        """Create a new TradePlan.

        Computes risk_reward_ratio from entry/stop/target prices.
        Rejects duplicate active plans for same ticker+direction.
        """
        entry = plan_data.get("entry_price", 0.0) or 0.0
        stop = plan_data.get("stop_loss", 0.0) or 0.0
        target = plan_data.get("target_price", 0.0) or 0.0
        rr = TradePlan.compute_risk_reward(entry, stop, target)

        ticker = plan_data.get("ticker", "")
        direction = plan_data.get("direction", "BOT")

        now = datetime.now()
        plan = TradePlan(
            id=0,  # auto-assigned by DB
            ticker=ticker,
            direction=direction,
            conviction=plan_data.get("conviction", "medium"),
            strategy_name=plan_data.get("strategy_name", ""),
            strategy_description=plan_data.get("strategy_description", ""),
            entry_price=entry,
            stop_loss=stop,
            target_price=target,
            entry_conditions=plan_data.get("entry_conditions", ""),
            exit_conditions=plan_data.get("exit_conditions", ""),
            timeframe=plan_data.get("timeframe", ""),
            risk_reward_ratio=rr,
            status=plan_data.get("status", "draft"),
            linked_trade_id=plan_data.get("linked_trade_id"),
            account_id=plan_data.get("account_id"),
            created_at=now,
            updated_at=now,
        )
        with self.uow:
            # F3: Duplicate active-plan rejection
            existing = self.uow.trade_plans.list_all(limit=1000, offset=0)
            for p in existing:
                if (
                    p.ticker == ticker
                    and str(p.direction) == str(direction)
                    and str(p.status) in ("draft", "active")
                ):
                    msg = f"Duplicate active plan for {ticker}/{direction}"
                    raise ValueError(msg)

            self.uow.trade_plans.save(plan)
            self.uow.commit()

            # Re-fetch by scanning for the last saved plan
            hydrated = self.uow.trade_plans.get(plan.id)
            return hydrated if hydrated is not None else plan

    def get_plan(self, plan_id: int) -> TradePlan | None:
        """Fetch a TradePlan by ID."""
        with self.uow:
            return self.uow.trade_plans.get(plan_id)

    def list_plans(
        self, limit: int = 100, offset: int = 0,
    ) -> list[TradePlan]:
        """List TradePlans with pagination."""
        with self.uow:
            return self.uow.trade_plans.list_all(limit=limit, offset=offset)

    def update_plan(self, plan_id: int, updates: dict[str, Any]) -> TradePlan:
        """Update an existing plan.

        Raises:
            ValueError: If no plan exists with the given ID.
        """
        with self.uow:
            existing = self.uow.trade_plans.get(plan_id)
            if existing is None:
                msg = f"Plan {plan_id} not found"
                raise ValueError(msg)

            updated = replace(existing, **updates, updated_at=datetime.now())
            self.uow.trade_plans.update(updated)
            self.uow.commit()
            return updated

    # ── Linking methods (MEU-67) ────────────────────────────────────────

    def link_plan_to_trade(
        self, plan_id: int, trade_id: str,
    ) -> TradePlan:
        """Link a TradePlan to an executed Trade.

        Sets linked_trade_id and transitions status to 'executed'.

        Raises:
            ValueError: If plan or trade not found.
        """
        with self.uow:
            plan = self.uow.trade_plans.get(plan_id)
            if plan is None:
                msg = f"Plan {plan_id} not found"
                raise ValueError(msg)

            trade = self.uow.trades.get(trade_id)
            if trade is None:
                msg = f"Trade '{trade_id}' not found"
                raise ValueError(msg)

            updated = replace(
                plan,
                linked_trade_id=trade_id,
                status="executed",
                updated_at=datetime.now(),
            )
            self.uow.trade_plans.update(updated)
            self.uow.commit()
            return updated

    def delete_plan(self, plan_id: int) -> None:
        """Delete a TradePlan by ID.

        Raises:
            ValueError: If no plan exists with the given ID.
        """
        with self.uow:
            existing = self.uow.trade_plans.get(plan_id)
            if existing is None:
                msg = f"Plan {plan_id} not found"
                raise ValueError(msg)
            self.uow.trade_plans.delete(plan_id)
            self.uow.commit()
