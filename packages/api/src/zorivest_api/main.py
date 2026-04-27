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
from zorivest_api.routes.mcp_toolsets import mcp_toolsets_router  # MEU-46a
from zorivest_api.routes.email_settings import email_settings_router  # MEU-73
from zorivest_api.routes.config import config_router  # MEU-75
from zorivest_api.routes.backups import backup_router  # MEU-74
from zorivest_api.schemas.common import ErrorEnvelope
from zorivest_api.auth.auth_service import AuthService
from zorivest_api.services.mcp_guard import McpGuardService
from zorivest_api.stubs import (
    StubAnalyticsService,
    StubReviewService,
    StubTaxService,
)
from zorivest_core.services.trade_service import TradeService
from zorivest_core.services.account_service import AccountService
from zorivest_core.services.image_service import ImageService
from zorivest_core.services.settings_service import SettingsService
from zorivest_core.services.report_service import ReportService
from zorivest_core.services.provider_connection_service import ProviderConnectionService
from zorivest_core.services.watchlist_service import WatchlistService
from zorivest_core.services.email_provider_service import EmailProviderService  # MEU-73
from zorivest_core.services.scheduling_service import SchedulingService
from zorivest_core.services.scheduler_service import SchedulerService
from zorivest_core.services.pipeline_guardrails import PipelineGuardrails
from zorivest_core.services.pipeline_runner import PipelineRunner
from zorivest_core.services.ref_resolver import RefResolver
from zorivest_core.services.condition_evaluator import ConditionEvaluator
from zorivest_infra.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
    create_engine_with_wal,
)
from zorivest_infra.database.models import Base
from zorivest_infra.market_data.provider_registry import PROVIDER_REGISTRY
from zorivest_infra.market_data.rate_limiter import RateLimiter
from zorivest_infra.market_data.service_factory import (
    FernetEncryptionAdapter,
    HttpxClient,
)
from zorivest_infra.market_data.normalizers import (
    QUOTE_NORMALIZERS,
    NEWS_NORMALIZERS,
    SEARCH_NORMALIZERS,
)
from zorivest_core.services.market_data_service import MarketDataService  # MEU-91
from sqlalchemy import text
from zorivest_api.scheduling_adapters import (
    PolicyStoreAdapter,
    RunStoreAdapter,
    StepStoreAdapter,
    AuditCounterAdapter,
)
from zorivest_infra.adapters.db_write_adapter import DbWriteAdapter
from zorivest_infra.database.connection import open_sandbox_connection
from zorivest_core.services.sql_sandbox import SqlSandbox
from zorivest_infra.rendering.template_engine import create_template_engine
from zorivest_infra.market_data.market_data_adapter import MarketDataProviderAdapter
from zorivest_infra.market_data.pipeline_rate_limiter import PipelineRateLimiter
from zorivest_api.middleware.approval_token import ApprovalTokenValidator

# ── Tag metadata ────────────────────────────────────────────────────────

TAGS_METADATA = [
    {
        "name": "trades",
        "description": "Trade lifecycle: CRUD, reports, plans, images, journal",
    },
    {
        "name": "accounts",
        "description": "Brokers, banking, import, identifiers, positions",
    },
    {
        "name": "auth",
        "description": "Unlock/lock, API keys, session management, confirmation tokens",
    },
    {
        "name": "settings",
        "description": "Configuration CRUD, validation, resolved settings",
    },
    {
        "name": "analytics",
        "description": "Quantitative analysis: expectancy, drawdown, SQN, fees, mistakes",
    },
    {
        "name": "tax",
        "description": "Simulate, estimate, wash sales, lots, quarterly, harvest",
    },
    {
        "name": "system",
        "description": "Health, version, logging, MCP guard, service lifecycle",
    },
    {
        "name": "market-data",
        "description": "Quotes, news, search, SEC filings, provider management",
    },
    {
        "name": "scheduling",
        "description": "Pipeline policies, execution, run history, scheduler status",
    },
    {"name": "scheduler", "description": "Power events, scheduler lifecycle"},
    {"name": "backups", "description": "Database backup, restore, verify, history"},
    {"name": "config", "description": "Config export/import with security filtering"},
]


# ── Default template seeding ────────────────────────────────────────────


def _seed_default_templates(repo: Any, session: Any) -> None:
    """Seed built-in default templates if they don't already exist.

    PH10: morning-check-in is the first default template.
    """
    import json
    from datetime import datetime as _dt, timezone as _tz
    from zorivest_infra.database.models import EmailTemplateModel

    _DEFAULTS = [
        {
            "name": "morning-check-in",
            "description": "Default morning portfolio check-in email template",
            "subject_template": "Zorivest — Morning Check-in {{ date }}",
            "body_html": (
                "<h1>Morning Check-in</h1>\n"
                "<p>Date: {{ date }}</p>\n"
                "<h2>Portfolio Summary</h2>\n"
                "<ul>\n"
                "  <li>Open positions: {{ open_positions }}</li>\n"
                "  <li>Total P&L: {{ total_pnl }}</li>\n"
                "  <li>Day change: {{ day_change }}</li>\n"
                "</ul>\n"
                "<h2>Watchlist Alerts</h2>\n"
                "{{ watchlist_alerts }}\n"
                "<p><em>Generated by Zorivest Pipeline Engine</em></p>"
            ),
            "body_format": "html",
            "required_variables": [
                "date",
                "open_positions",
                "total_pnl",
                "day_change",
                "watchlist_alerts",
            ],
            "sample_data_json": json.dumps(
                {
                    "date": "2026-04-26",
                    "open_positions": 5,
                    "total_pnl": "$1,234.56",
                    "day_change": "+0.42%",
                    "watchlist_alerts": "<p>AAPL: crossed 200 SMA</p>",
                }
            ),
            "is_default": True,
        },
    ]

    for tpl_data in _DEFAULTS:
        existing = repo.get_by_name(tpl_data["name"])
        if existing is not None:
            continue
        model = EmailTemplateModel(
            name=tpl_data["name"],
            description=tpl_data["description"],
            subject_template=tpl_data["subject_template"],
            body_html=tpl_data["body_html"],
            body_format=tpl_data["body_format"],
            required_variables=json.dumps(tpl_data["required_variables"]),
            sample_data_json=tpl_data["sample_data_json"],
            is_default=tpl_data["is_default"],
            created_at=_dt.now(_tz.utc),
        )
        repo.create(model)
    session.commit()


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

    # ── Logging (UTF-8 safe, idempotent) ─────────────────────────────────
    from zorivest_api.logging_config import configure_structlog_utf8

    configure_structlog_utf8()

    # ── Engine & schema ──────────────────────────────────────────────────
    db_url = os.environ.get("ZORIVEST_DB_URL", "sqlite:///zorivest.db")
    engine = create_engine_with_wal(db_url)
    Base.metadata.create_all(engine)

    # ── Schema migrations (no Alembic) ────────────────────────────────
    # Add missing columns to existing databases created before the column was added.
    _inline_migrations = [
        "ALTER TABLE trades ADD COLUMN notes TEXT DEFAULT ''",
        "ALTER TABLE trade_plans ADD COLUMN executed_at TEXT",  # T5: status timestamps
        "ALTER TABLE trade_plans ADD COLUMN cancelled_at TEXT",  # T5: status timestamps
        "ALTER TABLE accounts ADD COLUMN is_archived BOOLEAN DEFAULT 0",  # MEU-37 AC-1
        "ALTER TABLE accounts ADD COLUMN is_system BOOLEAN DEFAULT 0",  # MEU-37 AC-2
        "ALTER TABLE trade_plans ADD COLUMN shares_planned INTEGER",  # Position size
        "ALTER TABLE trade_plans ADD COLUMN position_size REAL",  # MEU-70a: dollar value
        "ALTER TABLE market_quotes ADD COLUMN change NUMERIC(15,6)",  # Yahoo v8 quote
        "ALTER TABLE market_quotes ADD COLUMN change_pct REAL",  # Yahoo v8 quote
    ]
    with engine.connect() as conn:
        for _stmt in _inline_migrations:
            try:
                conn.execute(text(_stmt))
                conn.commit()
            except Exception:
                # Column already exists (fresh DB or already migrated) — ignore
                conn.rollback()

    # ── Seed system account (MEU-37 AC-3) ─────────────────────────────
    from zorivest_infra.database.seed_system_account import seed_system_account
    from sqlalchemy.orm import Session as _SaSession

    with _SaSession(engine) as _seed_session:
        seed_system_account(_seed_session)
        _seed_session.commit()

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
    # MEU-91: shared HTTP client, encryption, rate limiters for all market data services
    _http_client = HttpxClient()
    _encryption = FernetEncryptionAdapter()
    _rate_limiters = {
        name: RateLimiter(cfg.default_rate_limit)
        for name, cfg in PROVIDER_REGISTRY.items()
    }
    # MEU-91: real MarketDataService — wires real provider fallback chain with Yahoo Finance fallback
    app.state.market_data_service = MarketDataService(
        uow=uow,
        encryption=_encryption,
        http_client=_http_client,
        rate_limiters=_rate_limiters,
        provider_registry=PROVIDER_REGISTRY,
        quote_normalizers=QUOTE_NORMALIZERS,
        news_normalizers=NEWS_NORMALIZERS,
        search_normalizers=SEARCH_NORMALIZERS,
    )
    # MEU-65: real ProviderConnectionService — shares same http/encryption/rate_limiters
    app.state.provider_connection_service = ProviderConnectionService(
        uow=uow,
        encryption=_encryption,
        http_client=_http_client,
        rate_limiters=_rate_limiters,
        provider_registry=PROVIDER_REGISTRY,
    )
    app.state.report_service = ReportService(uow)  # MEU-53
    app.state.watchlist_service = WatchlistService(uow)  # MEU-68
    app.state.email_provider_service = EmailProviderService(
        uow=uow, encryption=_encryption
    )  # MEU-73

    # ── Register pipeline step types (auto-registration via __init_subclass__) ──
    import zorivest_core.pipeline_steps  # noqa: F401 — triggers step registration

    # ── Scheduling adapters (bridge async dict protocols → sync ORM repos) ──
    audit_adapter = AuditCounterAdapter(uow)
    policy_adapter = PolicyStoreAdapter(uow)
    run_adapter = RunStoreAdapter(uow)
    step_adapter = StepStoreAdapter(uow)
    guardrails = PipelineGuardrails(audit_adapter, policy_adapter)
    # ── Pipeline runtime wiring (MEU-PW1) ──────────────────────────────
    # Extract db_path from URL for sandboxed read-only connection
    _db_path = db_url.replace("sqlite:///", "")
    _sandboxed_conn = open_sandbox_connection(_db_path, read_only=True)
    _sql_sandbox = SqlSandbox(_db_path, connection=_sandboxed_conn)
    _template_engine = create_template_engine()
    _db_write_adapter = DbWriteAdapter(session=uow._session)  # noqa: SLF001
    _smtp_runtime_config = app.state.email_provider_service.get_smtp_runtime_config()

    # ── Fetch step wiring (MEU-PW2) ──────────────────────────────────────
    _rate_limits: dict[str, tuple[float, float]] = {
        name: (float(cfg.default_rate_limit), 1.0)
        for name, cfg in PROVIDER_REGISTRY.items()
    }
    _pipeline_rate_limiter = PipelineRateLimiter(_rate_limits)
    _market_data_adapter = MarketDataProviderAdapter(
        http_client=_http_client,
        rate_limiter=_pipeline_rate_limiter,
    )

    # ── PH9: Template CRUD services (created early for runner injection) ──
    from zorivest_infra.database.email_template_repository import (
        EmailTemplateRepository,
    )

    _template_repo = EmailTemplateRepository(uow._session)  # noqa: SLF001

    pipeline_runner = PipelineRunner(
        uow,
        RefResolver(),
        ConditionEvaluator(),
        delivery_repository=uow.deliveries,
        smtp_config=_smtp_runtime_config,
        provider_adapter=_market_data_adapter,
        db_writer=_db_write_adapter,
        db_connection=_sandboxed_conn,
        sql_sandbox=_sql_sandbox,
        report_repository=uow.reports,
        template_engine=_template_engine,
        template_port=_template_repo,
        pipeline_state_repo=uow.pipeline_state,
        fetch_cache_repo=uow.fetch_cache,
    )

    # ── Zombie recovery (MEU-PW5 §9.3e) ─────────────────────────────────
    import structlog as _structlog

    _startup_log = _structlog.get_logger()
    try:
        recovered = await pipeline_runner.recover_zombies()
        if recovered:
            _startup_log.warning(
                "zombie_runs_recovered",
                count=len(recovered),
                runs=recovered,
            )
    except Exception as exc:
        _startup_log.error("zombie_recovery_failed", error=str(exc))

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

    # ── PH9: Emulator + budget services ──────────────────────────────────
    from zorivest_core.services.policy_emulator import PolicyEmulator
    from zorivest_core.services.emulator_budget import SessionBudget
    from zorivest_core.services.secure_jinja import HardenedSandbox

    _hardened_sandbox = HardenedSandbox()

    # PH13: SMTP readiness checker from wired EmailProviderService (Finding #1)
    # The checker returns True if SMTP host + password are configured.
    _email_svc = app.state.email_provider_service

    def _check_email_configured() -> bool:
        config = _email_svc.get_config()
        return bool(config.get("smtp_host")) and bool(config.get("has_password"))

    _policy_emulator = PolicyEmulator(
        sandbox=_sql_sandbox,
        template_engine=_hardened_sandbox,
        template_port=_template_repo,
        email_config_checker=_check_email_configured,
    )
    _session_budget = SessionBudget()

    app.state.template_repo = _template_repo
    app.state.policy_emulator = _policy_emulator
    app.state.session_budget = _session_budget
    app.state.sql_sandbox = _sql_sandbox

    # ── PH11: CSRF approval token validator ─────────────────────────────
    # Electron main process sets ZORIVEST_APPROVAL_CALLBACK_PORT when it
    # starts its internal validation HTTP server.  The API calls back to
    # that server to validate single-use approval tokens.
    _approval_port = os.environ.get("ZORIVEST_APPROVAL_CALLBACK_PORT")
    if _approval_port:
        _callback_url = f"http://127.0.0.1:{_approval_port}/internal/validate-token"
        app.state.approval_token_validator = ApprovalTokenValidator(_callback_url)
        import structlog as _atv_log

        _atv_log.get_logger().info(
            "approval_token_validator_configured",
            callback_url=_callback_url,
        )
    else:
        import structlog as _atv_log

        _atv_log.get_logger().warning(
            "approval_token_validator_not_configured",
            reason="ZORIVEST_APPROVAL_CALLBACK_PORT not set — "
            "approval endpoint will reject all requests",
        )

    # ── PH10: Seed default templates ────────────────────────────────────
    _seed_default_templates(_template_repo, uow._session)  # noqa: SLF001

    await scheduler_svc.start()
    try:
        yield
    finally:
        await scheduler_svc.shutdown()
        await _http_client.aclose()  # MEU-65: close httpx session
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
    app.include_router(
        email_settings_router
    )  # MEU-73 — before settings_router (static path wins)
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
    app.include_router(plan_router)  # MEU-66
    app.include_router(watchlist_router)  # MEU-68
    app.include_router(scheduling_router)  # MEU-89
    app.include_router(scheduler_router)  # MEU-89
    app.include_router(mcp_toolsets_router)  # MEU-46a
    app.include_router(config_router)  # MEU-75
    app.include_router(backup_router)  # MEU-74

    return app


# Module-level app instance for uvicorn CLI: `uvicorn zorivest_api.main:app`
# Required by ui/tests/e2e/global-setup.ts for E2E test backend bootstrap.
app = create_app()
