# Phase 4: REST API (FastAPI)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 3](03-service-layer.md) | Outputs: [Phase 5](05-mcp-server.md), [Phase 6](06-gui.md)
>
> **Phase 2A routes**: Backup, config export/import, and settings resolver endpoints are defined in [Phase 2A](02a-backup-restore.md) and implemented in [04d-api-settings.md](04d-api-settings.md).

---

## Goal

Thin REST layer that delegates to the same service layer. Test with FastAPI's `TestClient`. Each domain's routes, schemas, and tests are specified in the corresponding sub-file.

## App Factory

```python
# packages/api/src/zorivest_api/main.py

from fastapi import FastAPI

tags_metadata = [
    {"name": "trades",    "description": "Trade lifecycle: CRUD, reports, plans, images, journal"},
    {"name": "accounts",  "description": "Brokers, banking, import, identifiers, positions"},
    {"name": "auth",      "description": "Unlock/lock, API keys, session management, confirmation tokens"},
    {"name": "settings",  "description": "Configuration CRUD, validation, resolved settings"},
    {"name": "analytics", "description": "Quantitative analysis: expectancy, drawdown, SQN, fees, mistakes"},
    {"name": "tax",       "description": "Simulate, estimate, wash sales, lots, quarterly, harvest"},
    {"name": "system",    "description": "Health, version, logging, MCP guard, service lifecycle"},
]

app = FastAPI(
    title="Zorivest API",
    version="1.0.0",
    openapi_tags=tags_metadata,
)
```

## Lifespan

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init SQLCipher connection pool (locked state)
    app.state.db = SQLCipherDB()
    yield
    # Shutdown: close all connections, flush logs
    app.state.db.close()
```

## Middleware

```python
# CORS — localhost only (Electron renderer)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:*"], ...)

# Request ID — inject X-Request-ID header for tracing
@app.middleware("http")
async def add_request_id(request, call_next): ...

# Global error handler — wrap exceptions in ErrorEnvelope
@app.exception_handler(Exception)
async def error_handler(request, exc): ...
```

### Mode-Gating Pattern

```python
# Dependencies that gate route availability
def require_unlocked_db(db: SQLCipherDB = Depends(get_db)):
    """All domain routes require an unlocked database.
    Only system routes (health, version, MCP guard status)
    are available before unlock."""
    if not db.is_unlocked:
        raise HTTPException(403, "Database is locked")
```

**Routes available before unlock:** health, version, unlock endpoint itself, MCP guard status
**Routes requiring unlock:** everything else (trades, accounts, settings, analytics, tax)

## Router Manifest

```python
from zorivest_api.routes.trades import trade_router
from zorivest_api.routes.trade_plans import plan_router
from zorivest_api.routes.round_trips import round_trip_router
from zorivest_api.routes.images import image_router
from zorivest_api.routes.accounts import account_router
from zorivest_api.routes.auth import auth_router
from zorivest_api.routes.confirmation import confirm_router
from zorivest_api.routes.settings import settings_router
from zorivest_api.routes.analytics import analytics_router
from zorivest_api.routes.tax import tax_router
from zorivest_api.routes.mcp_guard import guard_router
from zorivest_api.routes.logs import log_router
from zorivest_api.routes.version import version_router
from zorivest_api.routes.health import health_router
from zorivest_api.routes.service import service_router

from zorivest_api.routes.brokers import broker_router
from zorivest_api.routes.banking import banking_router
from zorivest_api.routes.import_ import import_router
from zorivest_api.routes.identifiers import identifiers_router
from zorivest_api.routes.mistakes import mistakes_router
from zorivest_api.routes.fees import fees_router
from zorivest_api.routes.calculator import calculator_router

app.include_router(trade_router)       # /api/v1/trades
app.include_router(plan_router)        # /api/v1/trade-plans
app.include_router(round_trip_router)  # /api/v1/round-trips
app.include_router(image_router)       # /api/v1/images
app.include_router(account_router)     # /api/v1/accounts
app.include_router(broker_router)      # /api/v1/brokers
app.include_router(banking_router)     # /api/v1/banking
app.include_router(import_router)      # /api/v1/import
app.include_router(identifiers_router) # /api/v1/identifiers
app.include_router(auth_router)        # /api/v1/auth
app.include_router(confirm_router)     # /api/v1/confirmation-tokens
app.include_router(settings_router)    # /api/v1/settings
app.include_router(analytics_router)   # /api/v1/analytics
app.include_router(mistakes_router)    # /api/v1/mistakes
app.include_router(fees_router)        # /api/v1/fees
app.include_router(calculator_router)  # /api/v1/calculator
app.include_router(tax_router)         # /api/v1/tax
app.include_router(guard_router)       # /api/v1/mcp-guard
app.include_router(log_router)         # /api/v1/logs
app.include_router(version_router)     # /api/v1/version
app.include_router(health_router)      # /api/v1/health       (no auth)
app.include_router(service_router)     # /api/v1/service
```

## Route Contract Registry

> Canonical cross-reference: every REST endpoint, its owner sub-file, and downstream consumers. Sub-files contain schemas and tests; this table is the single source of truth for route ownership.

| Route ID | Method | Path | Owner | MCP Consumers (05) | GUI Consumers (06) |
|----------|--------|------|-------|--------------------|--------------------| 

**Trades (04a)**

| trades.list | `GET` | `/api/v1/trades` | [04a](04a-api-trades.md) | `list_trades` (05c) | 06b |
| trades.create | `POST` | `/api/v1/trades` | [04a](04a-api-trades.md) | `create_trade` (05c) | 06b |
| trades.get | `GET` | `/api/v1/trades/{exec_id}` | [04a](04a-api-trades.md) | — (GUI-only) | 06b |
| trades.update | `PUT` | `/api/v1/trades/{exec_id}` | [04a](04a-api-trades.md) | — (GUI-only) | 06b |
| trades.delete | `DELETE` | `/api/v1/trades/{exec_id}` | [04a](04a-api-trades.md) | — (GUI-only) | 06b |
| trades.images.list | `GET` | `/api/v1/trades/{exec_id}/images` | [04a](04a-api-trades.md) | — | 06b |
| trades.images.upload | `POST` | `/api/v1/trades/{exec_id}/images` | [04a](04a-api-trades.md) | `attach_screenshot` (05c) | 06b |
| trades.report.create | `POST` | `/api/v1/trades/{exec_id}/report` | [04a](04a-api-trades.md) | — | 06b |
| trades.report.get | `GET` | `/api/v1/trades/{exec_id}/report` | [04a](04a-api-trades.md) | — | 06b |
| trades.report.update | `PUT` | `/api/v1/trades/{exec_id}/report` | [04a](04a-api-trades.md) | — | 06b |
| trades.report.delete | `DELETE` | `/api/v1/trades/{exec_id}/report` | [04a](04a-api-trades.md) | — | 06b |
| trades.journal | `POST` | `/api/v1/trades/{exec_id}/journal-link` | [04a](04a-api-trades.md) | — | 06b |
| plans.create | `POST` | `/api/v1/trade-plans` | [04a](04a-api-trades.md) | `create_trade_plan` (05d) | 06c |
| roundtrips.list | `GET` | `/api/v1/round-trips` | [04a](04a-api-trades.md) | `get_round_trips` (05c) | 06b |
| images.get | `GET` | `/api/v1/images/{image_id}` | [04a](04a-api-trades.md) | — | 06b |
| images.thumb | `GET` | `/api/v1/images/{image_id}/thumbnail` | [04a](04a-api-trades.md) | `get_screenshot` (05c) | 06b |
| images.full | `GET` | `/api/v1/images/{image_id}/full` | [04a](04a-api-trades.md) | — | 06b |

**Accounts & Ingest (04b)**

| accounts.list | `GET` | `/api/v1/accounts` | [04b](04b-api-accounts.md) | — | 06d |
| accounts.create | `POST` | `/api/v1/accounts` | [04b](04b-api-accounts.md) | — | 06d |
| accounts.get | `GET` | `/api/v1/accounts/{account_id}` | [04b](04b-api-accounts.md) | — | 06d |
| accounts.update | `PUT` | `/api/v1/accounts/{account_id}` | [04b](04b-api-accounts.md) | — | 06d |
| accounts.delete | `DELETE` | `/api/v1/accounts/{account_id}` | [04b](04b-api-accounts.md) | — | 06d |
| accounts.balance | `POST` | `/api/v1/accounts/{account_id}/balances` | [04b](04b-api-accounts.md) | — | 06d |
| brokers.list | `GET` | `/api/v1/brokers` | [04b](04b-api-accounts.md) | `list_brokers` (05f) | 06d |
| brokers.sync | `POST` | `/api/v1/brokers/{broker_id}/sync` | [04b](04b-api-accounts.md) | `sync_broker` (05f) | 06d |
| brokers.positions | `GET` | `/api/v1/brokers/{broker_id}/positions` | [04b](04b-api-accounts.md) | — | 06d |
| banking.import | `POST` | `/api/v1/banking/import` | [04b](04b-api-accounts.md) | `import_bank_statement` (05f) | 06d |
| banking.accounts | `GET` | `/api/v1/banking/accounts` | [04b](04b-api-accounts.md) | — | 06d |
| banking.transactions | `POST` | `/api/v1/banking/transactions` | [04b](04b-api-accounts.md) | — | 06d |
| banking.balance | `PUT` | `/api/v1/banking/accounts/{account_id}/balance` | [04b](04b-api-accounts.md) | — | 06d |
| import.csv | `POST` | `/api/v1/import/csv` | [04b](04b-api-accounts.md) | `import_broker_csv` (05f) | 06d |
| import.pdf | `POST` | `/api/v1/import/pdf` | [04b](04b-api-accounts.md) | `import_broker_pdf` (05f) | 06d |
| identifiers.resolve | `POST` | `/api/v1/identifiers/resolve` | [04b](04b-api-accounts.md) | `resolve_identifiers` (05f) | — |

**Auth & Security (04c)**

| auth.unlock | `POST` | `/api/v1/auth/unlock` | [04c](04c-api-auth.md) | — | 06a |
| auth.lock | `POST` | `/api/v1/auth/lock` | [04c](04c-api-auth.md) | — | 06a |
| auth.status | `GET` | `/api/v1/auth/status` | [04c](04c-api-auth.md) | — | 06a |
| auth.keys.create | `POST` | `/api/v1/auth/keys` | [04c](04c-api-auth.md) | — | 06f |
| auth.keys.list | `GET` | `/api/v1/auth/keys` | [04c](04c-api-auth.md) | — | 06f |
| auth.keys.delete | `DELETE` | `/api/v1/auth/keys/{key_id}` | [04c](04c-api-auth.md) | — | 06f |
| confirm.create | `POST` | `/api/v1/confirmation-tokens` | [04c](04c-api-auth.md) | `get_confirmation_token` (05j) | — |

**Settings (04d) — includes Phase 2A delegated routes**

| settings.list | `GET` | `/api/v1/settings` | [04d](04d-api-settings.md) | `get_settings` (05a) | 06f |
| settings.get | `GET` | `/api/v1/settings/{key}` | [04d](04d-api-settings.md) | — | 06f |
| settings.put | `PUT` | `/api/v1/settings` | [04d](04d-api-settings.md) | `update_settings` (05a) | 06f |
| settings.resolved | `GET` | `/api/v1/settings/resolved` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| settings.reset | `POST` | `/api/v1/settings/reset` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| settings.delete | `DELETE` | `/api/v1/settings/{key}` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| config.export | `GET` | `/api/v1/config/export` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| config.import | `POST` | `/api/v1/config/import` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| backups.create | `POST` | `/api/v1/backups` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| backups.list | `GET` | `/api/v1/backups` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| backups.verify | `POST` | `/api/v1/backups/verify` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |
| backups.restore | `POST` | `/api/v1/backups/restore` | [04d](04d-api-settings.md) / [02a](02a-backup-restore.md) | — | 06f |

**Analytics (04e)**

| analytics.expect | `GET` | `/api/v1/analytics/expectancy` | [04e](04e-api-analytics.md) | `get_expectancy_metrics` (05c) | 06b |
| analytics.drawdown | `GET` | `/api/v1/analytics/drawdown` | [04e](04e-api-analytics.md) | `simulate_drawdown` (05c) | 06b |
| analytics.eq | `GET` | `/api/v1/analytics/execution-quality` | [04e](04e-api-analytics.md) | `get_execution_quality` (05c) | 06b |
| analytics.pfof | `GET` | `/api/v1/analytics/pfof-report` | [04e](04e-api-analytics.md) | `estimate_pfof_impact` (05c) | 06b |
| analytics.strategy | `GET` | `/api/v1/analytics/strategy-breakdown` | [04e](04e-api-analytics.md) | `get_strategy_breakdown` (05c) | 06b |
| analytics.sqn | `GET` | `/api/v1/analytics/sqn` | [04e](04e-api-analytics.md) | `get_sqn` (05c) | 06b |
| analytics.cost | `GET` | `/api/v1/analytics/cost-of-free` | [04e](04e-api-analytics.md) | `get_cost_of_free` (05c) | 06b |
| analytics.ai | `POST` | `/api/v1/analytics/ai-review` | [04e](04e-api-analytics.md) | `ai_review_trade` (05i) | 06b |
| analytics.excursion | `POST` | `/api/v1/analytics/excursion/{trade_exec_id}` | [04e](04e-api-analytics.md) | `get_trade_excursion` (05c) | 06b |
| analytics.options | `POST` | `/api/v1/analytics/options-strategy` | [04e](04e-api-analytics.md) | `detect_options_strategy` (05c) | 06b |
| mistakes.create | `POST` | `/api/v1/mistakes` | [04e](04e-api-analytics.md) | `track_mistake` (05i) | 06b |
| mistakes.summary | `GET` | `/api/v1/mistakes/summary` | [04e](04e-api-analytics.md) | `get_mistake_summary` (05i) | 06b |
| fees.summary | `GET` | `/api/v1/fees/summary` | [04e](04e-api-analytics.md) | `get_fee_summary` (05c) | 06b |
| calculator.size | `POST` | `/api/v1/calculator/position-size` | [04e](04e-api-analytics.md) | `calculate_position_size` (05c) | 06h |

**Tax (04f)**

| tax.simulate | `POST` | `/api/v1/tax/simulate` | [04f](04f-api-tax.md) | `simulate_tax_impact` (05h) | 06g |
| tax.estimate | `POST` | `/api/v1/tax/estimate` | [04f](04f-api-tax.md) | `estimate_tax` (05h) | 06g |
| tax.wash_sales | `POST` | `/api/v1/tax/wash-sales` | [04f](04f-api-tax.md) | `get_wash_sales` (05h) | 06g |
| tax.lots | `GET` | `/api/v1/tax/lots` | [04f](04f-api-tax.md) | `get_tax_lots` (05h) | 06g |
| tax.quarterly | `GET` | `/api/v1/tax/quarterly` | [04f](04f-api-tax.md) | `get_quarterly_estimate` (05h) | 06g |
| tax.payment | `POST` | `/api/v1/tax/quarterly/payment` | [04f](04f-api-tax.md) | `record_quarterly_tax_payment` (05h) | 06g |
| tax.harvest | `GET` | `/api/v1/tax/harvest` | [04f](04f-api-tax.md) | `harvest_losses` (05h) | 06g |
| tax.ytd | `GET` | `/api/v1/tax/ytd-summary` | [04f](04f-api-tax.md) | `get_ytd_summary` (05h) | 06g |
| tax.lot_close | `POST` | `/api/v1/tax/lots/{lot_id}/close` | [04f](04f-api-tax.md) | — | 06g |
| tax.lot_reassign | `PUT` | `/api/v1/tax/lots/{lot_id}/reassign` | [04f](04f-api-tax.md) | — | 06g |
| tax.wash_scan | `POST` | `/api/v1/tax/wash-sales/scan` | [04f](04f-api-tax.md) | — | 06g |
| tax.audit | `POST` | `/api/v1/tax/audit` | [04f](04f-api-tax.md) | `run_tax_audit` (05h) | 06g |

**System (04g)**

| guard.status | `GET` | `/api/v1/mcp-guard/status` | [04g](04g-api-system.md) | `zorivest_diagnose` (05b) | 06f |
| guard.config | `PUT` | `/api/v1/mcp-guard/config` | [04g](04g-api-system.md) | — | 06f |
| guard.lock | `POST` | `/api/v1/mcp-guard/lock` | [04g](04g-api-system.md) | `zorivest_emergency_stop` (05a) | 06f |
| guard.unlock | `POST` | `/api/v1/mcp-guard/unlock` | [04g](04g-api-system.md) | `zorivest_emergency_unlock` (05a) | 06f |
| guard.check | `POST` | `/api/v1/mcp-guard/check` | [04g](04g-api-system.md) | — | — |
| log.ingest | `POST` | `/api/v1/logs` | [04g](04g-api-system.md) | — | 06a (renderer) |
| health.check | `GET` | `/api/v1/health` | [04g](04g-api-system.md) | `zorivest_service_status` (05b) | 06f |
| version.get | `GET` | `/api/v1/version` | [04g](04g-api-system.md) | `zorivest_diagnose` (05b) | 06f |
| service.status | `GET` | `/api/v1/service/status` | [04g](04g-api-system.md) | `zorivest_service_status` (05b) | 06f |
| service.shutdown | `POST` | `/api/v1/service/graceful-shutdown` | [04g](04g-api-system.md) | `zorivest_service_restart` (05b) | 06f |

## Shared Schemas

```python
# packages/api/src/zorivest_api/schemas/common.py

from pydantic import BaseModel
from typing import Any, Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int

class ErrorEnvelope(BaseModel):
    error: str
    detail: Any = None
    request_id: str | None = None
```

## Sub-File Index

| File | Domain | Routes | Spec |
|------|--------|--------|------|
| [04a-api-trades.md](04a-api-trades.md) | Trade lifecycle | CRUD, reports, plans, all images, journal, round-trips | Trades tag |
| [04b-api-accounts.md](04b-api-accounts.md) | Accounts & ingest | Brokers, banking, import, identifiers, positions | Accounts tag |
| [04c-api-auth.md](04c-api-auth.md) | Auth & security | Unlock/lock, API keys, session, confirmation tokens | Auth tag |
| [04d-api-settings.md](04d-api-settings.md) | Configuration | Settings CRUD, validation, resolved | Settings tag |
| [04e-api-analytics.md](04e-api-analytics.md) | Analysis | Expectancy, drawdown, SQN, PFOF, AI review, excursion, options-strategy, mistakes, fees, calculator | Analytics tag |
| [04f-api-tax.md](04f-api-tax.md) | Tax engine | Simulate, estimate, wash sales, lots, quarterly, harvest, YTD, audit | Tax tag |
| [04g-api-system.md](04g-api-system.md) | Infrastructure | Health, version, logging, MCP guard, service lifecycle | System tag |

Each sub-file contains a **Consumer Notes** section documenting which MCP tools and GUI components consume its endpoints.

## Exit Criteria

- All e2e tests pass with FastAPI `TestClient`
- Health endpoint returns 200
- Settings CRUD endpoints return correct values
- Log ingestion endpoint accepts and records frontend metrics
- Trade list supports `account_id` filter and `sort` parameter
- MCP guard lock/unlock cycle and threshold updates work end-to-end
- Version endpoint returns valid SemVer and resolution context
- Service status endpoint returns process metrics (PID, uptime, memory, CPU)
- Graceful shutdown endpoint triggers backend restart via OS service wrapper
- Confirmation token generation and validation work end-to-end
- Tax simulation, estimation, and lot management return correct results
- Analytics endpoints return computed metrics for all domains

## Outputs

- FastAPI app factory with OpenAPI tags and middleware — this file
- Trade routes (CRUD, reports, plans, images, journal) — [04a](04a-api-trades.md)
- Account & ingest routes (brokers, banking, import) — [04b](04b-api-accounts.md)
- Auth routes (unlock/lock, API keys, confirmation tokens) — [04c](04c-api-auth.md)
- Settings routes (CRUD, validation, resolved) — [04d](04d-api-settings.md)
- Analytics routes (expectancy, drawdown, SQN, fees, mistakes, calculator) — [04e](04e-api-analytics.md)
- Tax routes (simulate, estimate, wash sales, lots, quarterly, harvest) — [04f](04f-api-tax.md)
- System routes (logging, MCP guard, version, health, service lifecycle) — [04g](04g-api-system.md)
- E2E tests using `TestClient` — in each sub-file
