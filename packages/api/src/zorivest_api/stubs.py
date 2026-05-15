"""Stub service implementations for runtime wiring.

Phase 1 stubs (InMemoryRepo, StubUnitOfWork) have been retired — MEU-90a.
McpGuardService moved to zorivest_api.services.mcp_guard — MEU-90a.
StubMarketDataService retired — MEU-91 (replaced by real MarketDataService).
StubProviderConnectionService retired — MEU-65 (replaced by real ProviderConnectionService).
StubTaxService retired — MEU-148 (replaced by real TaxService).

Retained stubs (blocked on future MEUs):
- StubAnalyticsService          — MEU-118 expansion-api
- StubReviewService             — MEU-118 expansion-api
"""

from __future__ import annotations

from typing import Any


class StubAnalyticsService:
    """Stub analytics service — returns properly shaped defaults.

    Source: 04e — all analytics methods return empty/default dicts.
    No __getattr__ — explicit methods only.
    """

    def get_expectancy(
        self, account_id: Any = None, period: str = "all"
    ) -> dict[str, Any]:
        return {
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "expectancy": 0.0,
            "kelly_pct": 0.0,
        }

    def get_drawdown(
        self, account_id: Any = None, simulations: int = 10000
    ) -> dict[str, Any]:
        return {
            "max_drawdown_pct": 0.0,
            "simulations": simulations,
            "probability_table": [],
        }

    def get_execution_quality(self, trade_id: Any = None) -> dict[str, Any]:
        return {"score": 0.0, "nbbo_available": False}

    def get_pfof_report(self, account_id: str, period: str = "ytd") -> dict[str, Any]:
        return {
            "estimate_label": "ESTIMATE",
            "total_pfof_impact": 0.0,
            "trades_analyzed": 0,
        }

    def get_strategy_breakdown(self, account_id: Any = None) -> dict[str, Any]:
        return {"strategies": []}

    def get_sqn(self, account_id: Any = None, period: str = "all") -> dict[str, Any]:
        return {"sqn": 0.0, "grade": "N/A", "trade_count": 0}

    def get_cost_of_free(
        self, account_id: Any = None, period: str = "ytd"
    ) -> dict[str, Any]:
        return {"total_hidden_cost": 0.0, "breakdown": []}

    def enrich_trade(self, trade_exec_id: str) -> dict[str, Any]:
        return {"trade_exec_id": trade_exec_id, "mfe": 0.0, "mae": 0.0, "bso": 0.0}

    def detect_strategy(self, leg_exec_ids: list[str]) -> dict[str, Any]:
        return {"strategy_type": "unknown", "legs": leg_exec_ids}

    def fee_summary(
        self, account_id: Any = None, period: str = "ytd"
    ) -> dict[str, Any]:
        return {"total_fees": 0.0, "by_type": [], "pnl_pct": 0.0}


class StubReviewService:
    """Stub review service — returns properly shaped defaults.

    Source: 04e — review/mistake methods return empty results.
    No __getattr__ — explicit methods only.
    """

    def ai_review(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"review_id": "stub", "personas": [], "status": "stub_response"}

    def track_mistake(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"mistake_id": "stub", "status": "tracked"}

    def mistake_summary(
        self, account_id: Any = None, period: str = "ytd"
    ) -> dict[str, Any]:
        return {"total_cost": 0.0, "by_category": [], "trend": []}
