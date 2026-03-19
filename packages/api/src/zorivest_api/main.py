"""FastAPI application factory and middleware.

Source: 04-rest-api.md §App Factory, Lifespan, Middleware
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from zorivest_api.routes.health import health_router
from zorivest_api.routes.version import version_router
from zorivest_api.routes.trades import trade_router
from zorivest_api.routes.images import image_router
from zorivest_api.routes.round_trips import round_trip_router
from zorivest_api.routes.accounts import account_router
from zorivest_api.routes.auth import auth_router
from zorivest_api.routes.confirmation import confirm_router
from zorivest_api.routes.settings import settings_router
from zorivest_api.routes.logs import log_router
from zorivest_api.routes.mcp_guard import guard_router
from zorivest_api.routes.service import service_router
from zorivest_api.routes.analytics import analytics_router
from zorivest_api.routes.mistakes import mistakes_router
from zorivest_api.routes.fees import fees_router
from zorivest_api.routes.calculator import calculator_router
from zorivest_api.routes.tax import tax_router
from zorivest_api.routes.market_data import market_data_router
from zorivest_api.routes.reports import report_router
from zorivest_api.routes.plans import plan_router
from zorivest_api.routes.watchlists import watchlist_router
from zorivest_api.routes.scheduling import scheduling_router
from zorivest_api.routes.scheduler import scheduler_router
from zorivest_api.schemas.common import ErrorEnvelope
from zorivest_api.auth.auth_service import AuthService
from zorivest_api.stubs import McpGuardService, StubAnalyticsService, StubMarketDataService, StubProviderConnectionService, StubReviewService, StubTaxService
from zorivest_core.services.trade_service import TradeService
from zorivest_core.services.account_service import AccountService
from zorivest_core.services.image_service import ImageService
from zorivest_core.services.settings_service import SettingsService
from zorivest_core.services.report_service import ReportService
from zorivest_core.services.watchlist_service import WatchlistService
from zorivest_core.services.scheduling_service import SchedulingService
from zorivest_core.services.scheduler_service import SchedulerService
from zorivest_core.services.pipeline_guardrails import PipelineGuardrails
from zorivest_core.services.pipeline_runner import PipelineRunner
from zorivest_core.services.ref_resolver import RefResolver
from zorivest_core.services.condition_evaluator import ConditionEvaluator
from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork, create_engine_with_wal
from zorivest_infra.database.models import Base
from sqlalchemy import text
from zorivest_api.scheduling_adapters import (
    PolicyStoreAdapter,
    RunStoreAdapter,
    StepStoreAdapter,
    AuditCounterAdapter,
)

# ── Tag metadata ────────────────────────────────────────────────────────

TAGS_METADATA = [
    {"name": "trades", "description": "Trade lifecycle: CRUD, reports, plans, images, journal"},
    {"name": "accounts", "description": "Brokers, banking, import, identifiers, positions"},
    {"name": "auth", "description": "Unlock/lock, API keys, session management, confirmation tokens"},
    {"name": "settings", "description": "Configuration CRUD, validation, resolved settings"},
    {"name": "analytics", "description": "Quantitative analysis: expectancy, drawdown, SQN, fees, mistakes"},
    {"name": "tax", "description": "Simulate, estimate, wash sales, lots, quarterly, harvest"},
    {"name": "system", "description": "Health, version, logging, MCP guard, service lifecycle"},
    {"name": "market-data", "description": "Quotes, news, search, SEC filings, provider management"},
    {"name": "scheduling", "description": "Pipeline policies, execution, run history, scheduler status"},
    {"name": "scheduler", "description": "Power events, scheduler lifecycle"},
]


# ── Lifespan ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize state on startup, cleanup on shutdown.

    MEU-90a: Uses real SqlAlchemyUnitOfWork with persistent SQLite storage.
    UoW is pre-entered once at startup (reentrant depth counting) — each
    service method re-enters via 'with self.uow:' per call.  Rollback
    isolation under nested failure is proven by test_nested_failure_does_not_leak.
    """
    app.state.start_time = time.time()
    app.state.db_unlocked = bool(os.environ.get("ZORIVEST_DEV_UNLOCK", ""))
    app.state.db = None  # Placeholder for SQLCipherDB; initialized on unlock

    # ── Engine & schema ──────────────────────────────────────────────────
    db_url = os.environ.get("ZORIVEST_DB_URL", "sqlite:///zorivest.db")
    engine = create_engine_with_wal(db_url)
    Base.metadata.create_all(engine)

    # ── Schema migrations (no Alembic) ────────────────────────────────
    # Add missing columns to existing databases created before the column was added.
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE trades ADD COLUMN notes TEXT DEFAULT ''"))
            conn.commit()
        except Exception:
            # Column already exists (fresh DB or already migrated) — ignore
            conn.rollback()

    # ── Unit of Work (reentrant — pre-entered once, services re-enter per call) ──
    uow: Any = SqlAlchemyUnitOfWork(engine)
    uow.__enter__()  # Pre-enter: session stays alive until shutdown; services re-enter safely

    # ── Core services ────────────────────────────────────────────────────
    app.state.auth_service = AuthService()
    app.state.trade_service = TradeService(uow)
    app.state.account_service = AccountService(uow)
    app.state.image_service = ImageService(uow)
    app.state.settings_service = SettingsService(uow)
    app.state.guard_service = McpGuardService()
    app.state.analytics_service = StubAnalyticsService()
    app.state.review_service = StubReviewService()
    app.state.tax_service = StubTaxService()
    app.state.market_data_service = StubMarketDataService()
    app.state.provider_connection_service = StubProviderConnectionService()
    app.state.report_service = ReportService(uow)  # MEU-53
    app.state.watchlist_service = WatchlistService(uow)  # MEU-68

    # ── Scheduling adapters (bridge async dict protocols → sync ORM repos) ──
    audit_adapter = AuditCounterAdapter(uow)
    policy_adapter = PolicyStoreAdapter(uow)
    run_adapter = RunStoreAdapter(uow)
    step_adapter = StepStoreAdapter(uow)
    guardrails = PipelineGuardrails(audit_adapter, policy_adapter)
    pipeline_runner = PipelineRunner(uow, RefResolver(), ConditionEvaluator())
    scheduler_svc = SchedulerService(
        pipeline_runner=pipeline_runner,
        policy_repo=policy_adapter,
        db_url=db_url,  # MEU-90a: persistent APScheduler job store
    )
    app.state.scheduler_service = scheduler_svc
    app.state.scheduling_service = SchedulingService(
        policy_store=policy_adapter,
        run_store=run_adapter,
        step_store=step_adapter,
        pipeline_runner=pipeline_runner,
        scheduler_service=scheduler_svc,
        guardrails=guardrails,
        audit_logger=audit_adapter,
    )

    await scheduler_svc.start()
    try:
        yield
    finally:
        await scheduler_svc.shutdown()
        uow.__exit__(None, None, None)  # Close session
        engine.dispose()  # MEU-90a: cleanup engine on shutdown


# ── App factory ─────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Zorivest API",
        description="Trading journal REST API",
        version="0.1.0",
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
    )

    # ── CORS middleware ─────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^http://localhost(:\d+)?$",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request-ID middleware ───────────────────────────────────────
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):  # noqa: ANN001
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Global exception handler → ErrorEnvelope ────────────────────
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):  # noqa: ANN001
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=404,
            content=ErrorEnvelope(
                error="not_found",
                detail=str(exc.detail) if hasattr(exc, "detail") else "Not found",
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):  # noqa: ANN001
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=500,
            content=ErrorEnvelope(
                error="internal_error",
                detail="An unexpected error occurred",
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc):  # noqa: ANN001
        """Catch-all: wrap unhandled exceptions in ErrorEnvelope."""
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=500,
            content=ErrorEnvelope(
                error="internal_error",
                detail="An unexpected error occurred",
                request_id=request_id,
            ).model_dump(),
        )

    # ── Register routers ────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(version_router)
    app.include_router(trade_router)
    app.include_router(image_router)
    app.include_router(round_trip_router)
    app.include_router(account_router)
    app.include_router(auth_router)
    app.include_router(confirm_router)
    app.include_router(settings_router)
    app.include_router(log_router)
    app.include_router(guard_router)
    app.include_router(service_router)
    app.include_router(analytics_router)
    app.include_router(mistakes_router)
    app.include_router(fees_router)
    app.include_router(calculator_router)
    app.include_router(tax_router)
    app.include_router(market_data_router)
    app.include_router(report_router)  # MEU-53
    app.include_router(plan_router)    # MEU-66
    app.include_router(watchlist_router)  # MEU-68
    app.include_router(scheduling_router)  # MEU-89
    app.include_router(scheduler_router)  # MEU-89

    return app


# Module-level app instance for uvicorn CLI: `uvicorn zorivest_api.main:app`
# Required by ui/tests/e2e/global-setup.ts for E2E test backend bootstrap.
app = create_app()
