"""Stub service implementations for runtime wiring.

Phase 1 stubs (InMemoryRepo, StubUnitOfWork) have been retired — MEU-90a.
McpGuardService moved to zorivest_api.services.mcp_guard — MEU-90a.

Retained stubs (blocked on future MEUs):
- StubAnalyticsService          — MEU-118 expansion-api
- StubReviewService             — MEU-118 expansion-api
- StubTaxService                — MEU-148 tax-api
- StubMarketDataService         — Service-wiring MEU (post-MEU-61)
- StubProviderConnectionService — Service-wiring MEU (post-MEU-60)
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


class StubTaxService:
    """Stub tax service — returns properly shaped defaults.

    Source: 04f — all tax methods return empty/default dicts.
    No __getattr__ — explicit methods only.
    """

    def simulate_impact(self, body: Any) -> dict[str, Any]:
        return {
            "estimated_tax": 0.0,
            "lots": [],
            "st_lt_split": {"short_term": 0.0, "long_term": 0.0},
        }

    def estimate(self, body: Any) -> dict[str, Any]:
        return {"federal_estimate": 0.0, "state_estimate": 0.0, "bracket_breakdown": []}

    def find_wash_sales(self, body: Any) -> dict[str, Any]:
        return {"chains": [], "disallowed_total": 0.0, "affected_tickers": []}

    def get_lots(
        self,
        account_id: str,
        ticker: Any = None,
        status: str = "all",
        sort_by: str = "acquired_date",
    ) -> dict[str, Any]:
        return {"lots": [], "total_count": 0}

    def quarterly_estimate(
        self, quarter: str, tax_year: int, method: str = "annualized"
    ) -> dict[str, Any]:
        return {
            "required": 0.0,
            "paid": 0.0,
            "due": 0.0,
            "penalty": 0.0,
            "due_date": "",
        }

    def record_payment(self, body: Any) -> dict[str, Any]:
        return {
            "status": "recorded",
            "quarter": getattr(body, "quarter", ""),
            "amount": getattr(body, "payment_amount", 0.0),
        }

    def harvest_scan(
        self, account_id: Any = None, min_loss: float = 0.0, exclude_wash: bool = False
    ) -> dict[str, Any]:
        return {"opportunities": [], "total_harvestable": 0.0}

    def ytd_summary(self, tax_year: int, account_id: Any = None) -> dict[str, Any]:
        return {
            "short_term": 0.0,
            "long_term": 0.0,
            "wash_adjustments": 0.0,
            "estimated_tax": 0.0,
        }

    def close_lot(self, lot_id: str) -> dict[str, Any]:
        return {"lot_id": lot_id, "status": "closed", "realized_gain_loss": 0.0}

    def reassign_basis(self, lot_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {
            "lot_id": lot_id,
            "method": body.get("method", "fifo"),
            "status": "reassigned",
        }

    def scan_wash_sales(self, account_id: Any = None) -> dict[str, Any]:
        return {"active_chains": [], "trapped_amount": 0.0, "alerts": []}

    def run_audit(self, account_id: Any = None, tax_year: Any = None) -> dict[str, Any]:
        return {
            "findings": [],
            "severity_summary": {"error": 0, "warning": 0, "info": 0},
        }


class StubMarketDataService:
    """Stub market data service — returns empty defaults for all endpoints.

    Source: 08-market-data.md §8.3b
    Ships shaped responses so the API routes resolve without real providers.
    Replaced by real MarketDataService when Phase 8 providers are configured.
    No __getattr__ — explicit methods only.
    """

    async def get_quote(self, ticker: str) -> dict[str, Any]:
        return {"ticker": ticker, "price": 0.0, "provider": "stub"}

    async def get_news(self, ticker: Any = None, count: int = 5) -> list:
        return []

    async def search_ticker(self, query: str) -> list:
        return []

    async def get_sec_filings(self, ticker: str) -> list:
        return []


class StubProviderConnectionService:
    """Stub provider connection service — returns empty defaults.

    Source: 08-market-data.md §8.3a
    Ships shaped responses so provider management routes resolve.
    Replaced by real ProviderConnectionService when Phase 8 integrates.
    No __getattr__ — explicit methods only.
    """

    async def list_providers(self) -> list:
        return []

    async def configure_provider(self, name: str, **kwargs: Any) -> None:
        pass

    async def test_connection(self, name: str) -> tuple[bool, str]:
        return (True, "stub connection — no providers configured")

    async def remove_api_key(self, name: str) -> None:
        pass
