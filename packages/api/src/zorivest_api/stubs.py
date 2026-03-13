"""Phase 4 in-memory stub implementations for runtime wiring.

Provides an in-memory StubUnitOfWork so that domain services can be
instantiated in lifespan() without a real database. _InMemoryRepo
persists data in dicts and implements filtering, dedup, and ownership
scoping so service-layer contracts hold.

Replaced by the real SqlAlchemyUnitOfWork when Phase 2 integrates.
"""

from __future__ import annotations

from typing import Any


class _InMemoryRepo:
    """In-memory repository — dict-backed persistence with query semantics.

    Supports the full read/write/dedup/filter surface used by services,
    plus a __getattr__ catch-all for any method not explicitly defined.
    """

    def __init__(self) -> None:
        self._store: dict[Any, Any] = {}
        self._auto_id: int = 0

    # ── Read ────────────────────────────────────────────────────────────

    def get(self, key: Any, *args: Any, **kwargs: Any) -> Any:
        return self._store.get(key)

    def exists(self, key: Any, *args: Any, **kwargs: Any) -> bool:
        return key in self._store

    def exists_by_fingerprint_since(self, fingerprint: Any, *args: Any, **kwargs: Any) -> bool:
        """Check for duplicate by fingerprint within lookback window.

        Computes the fingerprint for each stored trade on-the-fly
        using the canonical trade_fingerprint() function, then compares.
        """
        from zorivest_core.domain.trades.identity import trade_fingerprint
        from zorivest_core.domain.entities import Trade

        for entity in self._store.values():
            if isinstance(entity, Trade):
                if trade_fingerprint(entity) == fingerprint:
                    return True
        return False

    # ── Write ───────────────────────────────────────────────────────────

    def save(self, *args: Any, **kwargs: Any) -> int:
        self._auto_id += 1
        if len(args) >= 2:
            # Pattern: save(owner_type, owner_id, entity) for images
            entity = args[-1]
            if hasattr(entity, 'id') and entity.id == 0:
                # Assign auto-id to image attachments
                object.__setattr__(entity, 'id', self._auto_id) if hasattr(type(entity), '__dataclass_fields__') else setattr(entity, 'id', self._auto_id)
            self._store[self._auto_id] = entity
        elif len(args) == 1:
            entity = args[0]
            key = getattr(entity, 'exec_id', None) or getattr(entity, 'account_id', None) or getattr(entity, 'id', self._auto_id)
            self._store[key] = entity
        return self._auto_id

    def delete(self, key: Any, *args: Any, **kwargs: Any) -> None:
        self._store.pop(key, None)

    def update(self, entity: Any, *args: Any, **kwargs: Any) -> None:
        key = getattr(entity, 'exec_id', None) or getattr(entity, 'account_id', None) or getattr(entity, 'id', None)
        if key is not None:
            self._store[key] = entity

    # ── List/Filter ─────────────────────────────────────────────────────

    def list_for_account(self, account_id: Any, *args: Any, **kwargs: Any) -> list:
        """Return entities matching account_id."""
        return [
            e for e in self._store.values()
            if getattr(e, 'account_id', None) == account_id
        ]

    def list_filtered(
        self,
        limit: int = 100,
        offset: int = 0,
        account_id: Any = None,
        sort: str = "-time",
        **kwargs: Any,
    ) -> list:
        """Return entities with optional account filter and pagination."""
        items = list(self._store.values())
        if account_id is not None:
            items = [e for e in items if getattr(e, 'account_id', None) == account_id]
        return items[offset : offset + limit]

    def get_for_owner(self, owner_type: Any, owner_id: Any, *args: Any, **kwargs: Any) -> list:
        """Return entities matching owner_type + owner_id."""
        return [
            e for e in self._store.values()
            if getattr(e, 'owner_type', None) is not None
            and (
                getattr(e, 'owner_type', None) == owner_type
                or getattr(getattr(e, 'owner_type', None), 'value', None) == owner_type
            )
            and str(getattr(e, 'owner_id', None)) == str(owner_id)
        ]

    def get_full_data(self, key: Any, *args: Any, **kwargs: Any) -> Any:
        """Return raw bytes data for an entity (e.g., image data)."""
        entity = self._store.get(key)
        if entity is not None:
            return getattr(entity, 'data', None)
        return None

    def get_all(self, *args: Any, **kwargs: Any) -> list:
        """Return all stored items as a list."""
        return list(self._store.values())

    def bulk_upsert(self, settings: dict[str, Any], *args: Any, **kwargs: Any) -> None:
        """Store key-value pairs as Pydantic models (attribute-accessible + JSON-serializable)."""
        from pydantic import BaseModel as _BM

        class _Setting(_BM):
            key: str
            value: str
            value_type: str

        for key, value in settings.items():
            self._store[key] = _Setting(key=key, value=str(value), value_type=type(value).__name__)

    def list_all(self, *args: Any, **kwargs: Any) -> list:
        return list(self._store.values())

    def get_thumbnail(self, key: Any, *args: Any, **kwargs: Any) -> Any:
        """Return thumbnail data (stub: returns full image data)."""
        entity = self._store.get(key)
        if entity is not None:
            return getattr(entity, 'data', None)
        return None

    # ── Catch-all ───────────────────────────────────────────────────────

    def __getattr__(self, name: str) -> Any:
        """Catch-all: any unimplemented repo method returns a no-op callable."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


class _InMemoryTradeReportRepo(_InMemoryRepo):
    """Extends _InMemoryRepo with get_for_trade() and auto-ID assignment."""

    def save(self, entity: Any, *args: Any, **kwargs: Any) -> int:
        """Save report with auto-ID assignment (matches SqlAlchemy behavior)."""
        self._auto_id += 1
        if hasattr(entity, "id") and entity.id == 0:
            if hasattr(type(entity), "__dataclass_fields__"):
                object.__setattr__(entity, "id", self._auto_id)
            else:
                setattr(entity, "id", self._auto_id)
        self._store[self._auto_id] = entity
        return self._auto_id

    def get_for_trade(self, trade_id: Any, *args: Any, **kwargs: Any) -> Any:
        for entity in self._store.values():
            if getattr(entity, "trade_id", None) == trade_id:
                return entity
        return None


class _InMemoryTradePlanRepo(_InMemoryRepo):
    """Extends _InMemoryRepo with auto-ID assignment for TradePlan (MEU-66)."""

    def save(self, entity: Any, *args: Any, **kwargs: Any) -> int:
        """Save plan with auto-ID assignment (matches SqlAlchemy behavior)."""
        self._auto_id += 1
        if hasattr(entity, "id") and entity.id == 0:
            if hasattr(type(entity), "__dataclass_fields__"):
                object.__setattr__(entity, "id", self._auto_id)
            else:
                setattr(entity, "id", self._auto_id)
        self._store[self._auto_id] = entity
        return self._auto_id


class StubUnitOfWork:
    """Phase 4 in-memory UoW — satisfies the UnitOfWork protocol.

    Data persists within the lifespan of the app. Create→get→list
    contracts hold, with filtering, dedup, and ownership scoping.
    Replaced by real SqlAlchemyUnitOfWork when Phase 2 integrates.
    """

    def __init__(self) -> None:
        self.trades: Any = _InMemoryRepo()
        self.images: Any = _InMemoryRepo()
        self.accounts: Any = _InMemoryRepo()
        self.balance_snapshots: Any = _InMemoryRepo()
        self.round_trips: Any = _InMemoryRepo()
        self.settings: Any = _InMemoryRepo()
        self.app_defaults: Any = _InMemoryRepo()
        self.trade_reports: Any = _InMemoryTradeReportRepo()  # MEU-52
        self.trade_plans: Any = _InMemoryTradePlanRepo()      # MEU-66

    def __enter__(self) -> StubUnitOfWork:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


class McpGuardService:
    """In-memory MCP guard — circuit breaker for MCP tool access.

    Source: 04g-api-system.md §MCP Guard Routes
    No __getattr__ — explicit methods only.
    """

    def __init__(self) -> None:
        self._is_enabled: bool = False
        self._is_locked: bool = False
        self._locked_at: str | None = None
        self._lock_reason: str | None = None
        self._calls_per_minute_limit: int = 60
        self._calls_per_hour_limit: int = 1000
        self._recent_calls: list[float] = []

    def _state_dict(self) -> dict[str, Any]:
        """Build state dict for route responses."""
        import time as _time
        now = _time.time()
        calls_1min = sum(1 for t in self._recent_calls if now - t < 60)
        calls_1hr = sum(1 for t in self._recent_calls if now - t < 3600)
        return {
            "is_enabled": self._is_enabled,
            "is_locked": self._is_locked,
            "locked_at": self._locked_at,
            "lock_reason": self._lock_reason,
            "calls_per_minute_limit": self._calls_per_minute_limit,
            "calls_per_hour_limit": self._calls_per_hour_limit,
            "recent_calls_1min": calls_1min,
            "recent_calls_1hr": calls_1hr,
        }

    def get_status(self) -> dict[str, Any]:
        return self._state_dict()

    def update_config(self, config: dict[str, Any]) -> dict[str, Any]:
        if "is_enabled" in config:
            self._is_enabled = config["is_enabled"]
        if "calls_per_minute_limit" in config:
            self._calls_per_minute_limit = config["calls_per_minute_limit"]
        if "calls_per_hour_limit" in config:
            self._calls_per_hour_limit = config["calls_per_hour_limit"]
        return self._state_dict()

    def lock(self, reason: str = "manual") -> dict[str, Any]:
        from datetime import datetime, timezone
        self._is_locked = True
        self._locked_at = datetime.now(timezone.utc).isoformat()
        self._lock_reason = reason
        return self._state_dict()

    def unlock(self) -> dict[str, Any]:
        self._is_locked = False
        self._locked_at = None
        self._lock_reason = None
        return self._state_dict()

    def check(self) -> dict[str, Any]:
        import time as _time
        if not self._is_enabled:
            return {"allowed": True, "reason": "guard_disabled"}
        if self._is_locked:
            return {"allowed": False, "reason": self._lock_reason or "locked"}

        now = _time.time()
        self._recent_calls.append(now)
        # Prune old entries
        self._recent_calls = [t for t in self._recent_calls if now - t < 3600]

        calls_1min = sum(1 for t in self._recent_calls if now - t < 60)
        if calls_1min > self._calls_per_minute_limit:
            self.lock("rate_limit_exceeded")
            return {"allowed": False, "reason": "rate_limit_exceeded"}

        return {"allowed": True, "reason": "ok"}


class StubAnalyticsService:
    """Stub analytics service — returns properly shaped defaults.

    Source: 04e — all analytics methods return empty/default dicts.
    No __getattr__ — explicit methods only.
    """

    def get_expectancy(self, account_id: Any = None, period: str = "all") -> dict[str, Any]:
        return {"win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0, "expectancy": 0.0, "kelly_pct": 0.0}

    def get_drawdown(self, account_id: Any = None, simulations: int = 10000) -> dict[str, Any]:
        return {"max_drawdown_pct": 0.0, "simulations": simulations, "probability_table": []}

    def get_execution_quality(self, trade_id: Any = None) -> dict[str, Any]:
        return {"score": 0.0, "nbbo_available": False}

    def get_pfof_report(self, account_id: str, period: str = "ytd") -> dict[str, Any]:
        return {"estimate_label": "ESTIMATE", "total_pfof_impact": 0.0, "trades_analyzed": 0}

    def get_strategy_breakdown(self, account_id: Any = None) -> dict[str, Any]:
        return {"strategies": []}

    def get_sqn(self, account_id: Any = None, period: str = "all") -> dict[str, Any]:
        return {"sqn": 0.0, "grade": "N/A", "trade_count": 0}

    def get_cost_of_free(self, account_id: Any = None, period: str = "ytd") -> dict[str, Any]:
        return {"total_hidden_cost": 0.0, "breakdown": []}

    def enrich_trade(self, trade_exec_id: str) -> dict[str, Any]:
        return {"trade_exec_id": trade_exec_id, "mfe": 0.0, "mae": 0.0, "bso": 0.0}

    def detect_strategy(self, leg_exec_ids: list[str]) -> dict[str, Any]:
        return {"strategy_type": "unknown", "legs": leg_exec_ids}

    def fee_summary(self, account_id: Any = None, period: str = "ytd") -> dict[str, Any]:
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

    def mistake_summary(self, account_id: Any = None, period: str = "ytd") -> dict[str, Any]:
        return {"total_cost": 0.0, "by_category": [], "trend": []}


class StubTaxService:
    """Stub tax service — returns properly shaped defaults.

    Source: 04f — all tax methods return empty/default dicts.
    No __getattr__ — explicit methods only.
    """

    def simulate_impact(self, body: Any) -> dict[str, Any]:
        return {"estimated_tax": 0.0, "lots": [], "st_lt_split": {"short_term": 0.0, "long_term": 0.0}}

    def estimate(self, body: Any) -> dict[str, Any]:
        return {"federal_estimate": 0.0, "state_estimate": 0.0, "bracket_breakdown": []}

    def find_wash_sales(self, body: Any) -> dict[str, Any]:
        return {"chains": [], "disallowed_total": 0.0, "affected_tickers": []}

    def get_lots(self, account_id: str, ticker: Any = None, status: str = "all", sort_by: str = "acquired_date") -> dict[str, Any]:
        return {"lots": [], "total_count": 0}

    def quarterly_estimate(self, quarter: str, tax_year: int, method: str = "annualized") -> dict[str, Any]:
        return {"required": 0.0, "paid": 0.0, "due": 0.0, "penalty": 0.0, "due_date": ""}

    def record_payment(self, body: Any) -> dict[str, Any]:
        return {"status": "recorded", "quarter": getattr(body, "quarter", ""), "amount": getattr(body, "payment_amount", 0.0)}

    def harvest_scan(self, account_id: Any = None, min_loss: float = 0.0, exclude_wash: bool = False) -> dict[str, Any]:
        return {"opportunities": [], "total_harvestable": 0.0}

    def ytd_summary(self, tax_year: int, account_id: Any = None) -> dict[str, Any]:
        return {"short_term": 0.0, "long_term": 0.0, "wash_adjustments": 0.0, "estimated_tax": 0.0}

    def close_lot(self, lot_id: str) -> dict[str, Any]:
        return {"lot_id": lot_id, "status": "closed", "realized_gain_loss": 0.0}

    def reassign_basis(self, lot_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {"lot_id": lot_id, "method": body.get("method", "fifo"), "status": "reassigned"}

    def scan_wash_sales(self, account_id: Any = None) -> dict[str, Any]:
        return {"active_chains": [], "trapped_amount": 0.0, "alerts": []}

    def run_audit(self, account_id: Any = None, tax_year: Any = None) -> dict[str, Any]:
        return {"findings": [], "severity_summary": {"error": 0, "warning": 0, "info": 0}}


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
