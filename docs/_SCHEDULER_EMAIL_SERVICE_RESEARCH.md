# Scheduler & Email Reporting Service — Research & Design Specification

> **Status**: Research Complete — Pending Integration into BUILD_PLAN.md  
> **Date**: 2026-02-12  
> **Related**: [DESIGN_PROPOSAL.md](file:///p:/zorivest/DESIGN_PROPOSAL.md) · [APPLICATION_PURPOSE.md](file:///p:/zorivest/APPLICATION_PURPOSE.md) · [BUILD_PLAN.md](file:///p:/zorivest/BUILD_PLAN.md)

---

## Table of Contents

1. [Module Overview](#1-module-overview)
2. [Scheduler Selection: APScheduler](#2-scheduler-selection-apscheduler)
3. [FastAPI Lifecycle Integration](#3-fastapi-lifecycle-integration)
4. [Hexagonal Architecture: Ports & Adapters](#4-hexagonal-architecture-ports--adapters)
5. [Pipeline Pattern: Fetch → Process → Email](#5-pipeline-pattern-fetch--process--email)
6. [SMTP Provider Reference](#6-smtp-provider-reference)
7. [Email Template Engine (Jinja2)](#7-email-template-engine-jinja2)
8. [Credential Security](#8-credential-security)
9. [Failure Handling & Retry Strategy](#9-failure-handling--retry-strategy)
10. [Proposed Module Structure](#10-proposed-module-structure)
11. [Python Dependencies](#11-python-dependencies)
12. [REST API Endpoints](#12-rest-api-endpoints)
13. [GUI Control Surface (Electron + React)](#13-gui-control-surface-electron--react)
14. [MCP Tool Surface (AI Agent Access)](#14-mcp-tool-surface-ai-agent-access)
15. [Research Sources](#15-research-sources)

---

## 1. Module Overview

This module adds three scheduled capabilities to the Zorivest Python backend:

| Capability | Description | Schedule |
|---|---|---|
| **Data Fetch** | Pull data from external API endpoints into the SQLCipher database | Configurable (cron/interval) |
| **Report Processing** | Transform/aggregate raw data into report tables | After fetch completes |
| **Email Sending** | Render Jinja2 HTML templates with report data and send via SMTP | After processing completes |

### Design Constraints (from DESIGN_PROPOSAL.md)

- **Local-first**: No cloud infrastructure (Redis, RabbitMQ, etc.)
- **Single-process**: Must embed within the FastAPI app lifecycle
- **Hexagonal architecture**: Ports (Protocol ABCs) → Adapters (concrete implementations)
- **Encrypted storage**: SQLCipher database with Argon2id key derivation
- **Shared service layer**: Same services used by GUI, API, and MCP entry points

---

## 2. Scheduler Selection: APScheduler

### Why APScheduler

**APScheduler (Advanced Python Scheduler)** is the clear choice for this architecture. Both OpenAI and Anthropic research independently reached the same conclusion.

| Criterion | APScheduler | Celery/RQ | `schedule` lib |
|---|---|---|---|
| External broker required | ❌ None | ✅ Redis/RabbitMQ | ❌ None |
| AsyncIO support | ✅ `AsyncIOScheduler` | ⚠️ Workarounds | ❌ No |
| Cron/interval/date triggers | ✅ Full support | ✅ Celery Beat | ⚠️ Interval only |
| Job persistence | ✅ SQLAlchemy store | ✅ Via broker | ❌ No |
| In-process operation | ✅ Embeds in app | ❌ Separate workers | ✅ In-process |
| Complexity | Low | High | Very low |

### Key APScheduler Features for Zorivest

- **`AsyncIOScheduler`**: Shares FastAPI's event loop — no threading issues
- **`SQLAlchemyJobStore`**: Jobs survive app restarts and run missed jobs on startup
- **Cron triggers**: `CronTrigger(hour=8, minute=0)` for daily reports
- **Interval triggers**: `IntervalTrigger(minutes=30)` for periodic data refresh
- **Overlap protection**: `max_instances=1`, `coalesce=True`
- **Misfire handling**: `misfire_grace_time=3600` (1 hour grace window)

### Version Recommendation

```
apscheduler>=3.10,<4.0
```

> APScheduler v4 is a significant rewrite with a different API. v3.10+ is the stable, well-documented version with FastAPI community examples.

---

## 3. FastAPI Lifecycle Integration

The `on_event("startup")` / `on_event("shutdown")` pattern is **deprecated**. The modern approach uses the `lifespan` async context manager.

### Canonical Pattern

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    scheduler = AsyncIOScheduler(
        jobstores={'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')},
        timezone='UTC',
    )
    
    # Register jobs from service layer
    pipeline = app.state.pipeline_service
    scheduler.add_job(
        pipeline.run,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    
    scheduler.start()
    app.state.scheduler = scheduler
    
    yield  # --- App is running ---
    
    # --- Shutdown ---
    scheduler.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)
```

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Scheduler variant | `AsyncIOScheduler` | Shares FastAPI's event loop |
| Lifecycle hook | `lifespan` context manager | Modern pattern; `on_event` deprecated |
| Job persistence | `SQLAlchemyJobStore` | Survives restarts; runs missed jobs |
| Timezone | Explicit UTC | Avoids local timezone ambiguity |
| Shutdown mode | `shutdown(wait=True)` | Allow running jobs to complete |

---

## 4. Hexagonal Architecture: Ports & Adapters

### Driven Ports (Interfaces)

Following the existing DESIGN_PROPOSAL.md pattern using `typing.Protocol`:

```python
# application/ports.py — What the scheduler module NEEDS

from typing import Protocol

class ExternalApiPort(Protocol):
    """Fetch data from external APIs into the database."""
    async def fetch_into_db(self) -> int: ...

class ReportProcessorPort(Protocol):
    """Transform raw data into report tables."""
    async def process_reports(self) -> int: ...

class TemplateRendererPort(Protocol):
    """Render templates with data context."""
    def render(self, template_name: str, context: dict) -> tuple[str, str]: ...

class EmailSenderPort(Protocol):
    """Send composed email messages via SMTP."""
    async def send(self, subject: str, to: list[str], html: str, text: str) -> bool: ...
    async def test_connection(self) -> bool: ...

class CredentialStorePort(Protocol):
    """CRUD on encrypted SMTP credentials."""
    def store(self, provider: str, config: dict) -> None: ...
    def get(self, provider: str) -> dict | None: ...
    def list_providers(self) -> list[str]: ...
    def delete(self, provider: str) -> None: ...
```

### Adapters (Infrastructure Layer)

| Port | Adapter | Tech |
|---|---|---|
| `ExternalApiPort` | `HttpxApiAdapter` | httpx (already in DESIGN_PROPOSAL) |
| `ReportProcessorPort` | `SqlAlchemyReportProcessor` | SQLAlchemy queries/aggregations |
| `TemplateRendererPort` | `Jinja2TemplateAdapter` | Jinja2 `Environment` + `FileSystemLoader` |
| `EmailSenderPort` | `SmtpEmailAdapter` | `aiosmtplib` (async) or `smtplib` (sync via `to_thread`) |
| `CredentialStorePort` | `SqlCipherCredentialAdapter` | SQLCipher + Fernet field-level encryption |

### Scheduler Adapter

```python
class ApSchedulerAdapter:
    """Wraps APScheduler as an infrastructure adapter."""
    
    def __init__(self, scheduler: AsyncIOScheduler):
        self._scheduler = scheduler
    
    def add_pipeline_job(self, pipeline_fn, cron_expr: str, job_id: str):
        self._scheduler.add_job(
            pipeline_fn,
            trigger=CronTrigger.from_crontab(cron_expr),
            id=job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
    
    def remove_job(self, job_id: str):
        self._scheduler.remove_job(job_id)
    
    def get_jobs(self) -> list:
        return self._scheduler.get_jobs()
```

---

## 5. Pipeline Pattern: Fetch → Process → Email

### Four-Stage Pipeline

| Stage | Class | Network-Bound? | Retry? |
|---|---|---|---|
| 1. **Fetch** | `FetchDataStep` | ✅ Yes (API call) | ✅ 3 attempts, exponential backoff |
| 2. **Transform** | `TransformDataStep` | ❌ No (CPU/DB) | ❌ Fail fast on logic errors |
| 3. **Render** | `RenderTemplateStep` | ❌ No (local I/O) | ❌ Fail fast on template errors |
| 4. **Send** | `SendEmailStep` | ✅ Yes (SMTP) | ✅ 3 attempts, exponential backoff |

### Pipeline Orchestrator (Application Service)

```python
class PipelineService:
    """Orchestrates the fetch → process → render → email pipeline."""
    
    def __init__(
        self,
        api: ExternalApiPort,
        processor: ReportProcessorPort,
        renderer: TemplateRendererPort,
        emailer: EmailSenderPort,
        uow: AbstractUnitOfWork,
    ):
        self.api = api
        self.processor = processor
        self.renderer = renderer
        self.emailer = emailer
        self.uow = uow
        self._lock = asyncio.Lock()
    
    async def run(self) -> None:
        if self._lock.locked():
            logger.warning("Pipeline already running, skipping")
            return
        
        async with self._lock:
            run_id = uuid.uuid4()
            started = datetime.now(timezone.utc)
            
            # Stage 1: Fetch
            fetched = await self.api.fetch_into_db()
            
            # Stage 2: Process
            processed = await self.processor.process_reports()
            
            # Stage 3: Render
            context = {
                "run_id": str(run_id),
                "started_utc": started.isoformat(),
                "fetched": fetched,
                "processed": processed,
                "report_data": await self._get_report_data(),
            }
            html, text = self.renderer.render("daily_report.html", context)
            
            # Stage 4: Send
            await self.emailer.send(
                subject="Daily Report",
                to=["user@example.com"],
                html=html,
                text=text,
            )
```

### Pipeline State Persistence

For auditability and restart safety, persist pipeline runs:

```sql
CREATE TABLE pipeline_run (
    run_id      TEXT PRIMARY KEY,
    scheduled   TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT,
    status      TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING | RUNNING | SUCCESS | FAILED
    error       TEXT
);

CREATE TABLE pipeline_step (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES pipeline_run(run_id),
    step_name     TEXT NOT NULL,  -- 'fetch' | 'process' | 'render' | 'send'
    attempt       INTEGER NOT NULL DEFAULT 1,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    started_at    TEXT,
    finished_at   TEXT,
    error         TEXT,
    next_retry_at TEXT
);
```

---

## 6. SMTP Provider Reference

### Consolidated Configuration Table

All seven providers support STARTTLS on port 587 — enabling a **single generic SMTP adapter**.

| Provider | SMTP Host | STARTTLS Port | SSL Port | Username | Password/Key | Free Tier |
|---|---|---|---|---|---|---|
| **Gmail** | `smtp.gmail.com` | 587 | 465 | Full email address | App Password (2FA required) | 500/day (personal) |
| **Resend** | `smtp.resend.com` | 587, 25, 2587 | 465, 2465 | Literal `resend` | API Key | 100/day, 3000/month |
| **SendGrid** | `smtp.sendgrid.net` | 587, 25, 2525 | 465 | Literal `apikey` | API Key | 100/day for 60 days* |
| **Mailgun** | `smtp.mailgun.org` | 587, 25, 2525 | 465 | `postmaster@domain` | Domain password | 100/day forever |
| **Brevo** | `smtp-relay.brevo.com` | 587, 2525 | 465 | Account email | **SMTP Key** (not API key!) | 300/day forever |
| **Amazon SES** | `email-smtp.{region}.amazonaws.com` | 587, 25, 2587 | 465, 2465 | IAM SMTP username | IAM SMTP password | 3000/month (12 months) |
| **Mailtrap** | `live.smtp.mailtrap.io` | 587 | 465 | Literal `api` | API Token | 1000/month |

> \* SendGrid's free tier may have been modified in mid-2025 — verify current pricing.

### Critical Provider Nuances

| Provider | ⚠️ Watch out for |
|---|---|
| **Gmail** | App Passwords REQUIRED (2FA must be enabled). Regular passwords rejected. Limit: 500/day personal, 2000/day Workspace |
| **SendGrid** | Username is the literal string `"apikey"` — NOT your actual API key. API key goes in password field |
| **Brevo** | Uses a **SMTP Key** (generated in SMTP settings), NOT the main API key |
| **Amazon SES** | SMTP credentials are region-specific and derived from (but NOT identical to) IAM access keys. Must verify sender email/domain |
| **Resend** | Alternative ports 2465/2587 available when ISPs block standard SMTP ports |
| **Mailgun** | Requires custom domain verification for production sending |

### Recommended Default: Brevo

For developers wanting the best free tier with no expiration:
- **300 emails/day** (9,000/month) — free forever
- Easy SMTP key setup
- No domain verification required for testing
- Python-friendly documentation

### Why SMTP Over Provider SDKs

Both AI research models recommend **raw SMTP as the primary transport** for this architecture:

1. **Architectural consistency**: Single `SmtpEmailAdapter` serves ALL providers
2. **Hexagonal alignment**: SMTP is a universal protocol, not vendor-specific
3. **Desktop context**: SMTP port availability is not restricted on end-user machines
4. **Template independence**: Jinja2 renders locally regardless of transport

---

## 7. Email Template Engine (Jinja2)

### Template Architecture

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

class Jinja2TemplateAdapter:
    def __init__(self, templates_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
    
    def render(self, template_name: str, context: dict) -> tuple[str, str]:
        html_template = self.env.get_template(template_name)
        html = html_template.render(**context)
        
        # Plain text fallback
        text_name = template_name.replace(".html", ".txt")
        try:
            text_template = self.env.get_template(text_name)
            text = text_template.render(**context)
        except TemplateNotFoundError:
            text = self._strip_html(html)
        
        return html, text
```

### Email-Specific HTML Rules

All styling **MUST** be inline. External stylesheets and `<style>` blocks are stripped by most email clients (Gmail, Outlook, etc.).

### Data Table Template Pattern

```html
<!-- templates/daily_report.html -->
<!doctype html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 24px;">
    
    <h2 style="color: #2c3e50; margin-top: 0;">📊 Daily Report</h2>
    <p style="color: #666;">Generated: {{ started_utc }}</p>
    
    <!-- Summary stats -->
    <table style="width: 100%; margin-bottom: 20px;">
      <tr>
        <td style="padding: 12px; background: #3498db; color: #fff; border-radius: 4px; text-align: center;">
          <strong>{{ fetched }}</strong><br/>Records Fetched
        </td>
        <td style="width: 10px;"></td>
        <td style="padding: 12px; background: #2ecc71; color: #fff; border-radius: 4px; text-align: center;">
          <strong>{{ processed }}</strong><br/>Reports Generated
        </td>
      </tr>
    </table>
    
    <!-- Data table -->
    <table style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="background-color: #2c3e50; color: #ffffff;">
          {% for header in headers %}
          <th style="border: 1px solid #ddd; padding: 10px 14px; text-align: left;">
            {{ header }}
          </th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for row in data %}
        <tr style="background-color: {{ '#f9f9f9' if loop.index is odd else '#ffffff' }};">
          {% for header in headers %}
          <td style="border: 1px solid #ddd; padding: 8px 14px;">
            {% if row[header] is number %}
              {{ "{:,.2f}".format(row[header]) }}
            {% else %}
              {{ row[header] }}
            {% endif %}
          </td>
          {% endfor %}
        </tr>
        {% endfor %}
      </tbody>
    </table>
    
    <p style="color: #999; font-size: 12px; margin-top: 20px;">
      Run ID: {{ run_id }} · Zorivest Automated Report
    </p>
  </div>
</body>
</html>
```

### Chart Embedding Strategy

Since email clients cannot execute JavaScript:

1. **Generate charts server-side** using `matplotlib` or `plotly` static export
2. **Encode as base64 inline images**: `<img src="data:image/png;base64,{{ chart_b64 }}" />`
3. **Alternative**: CID-attached images (Content-ID references in multipart MIME) — broader email client support

---

## 8. Credential Security

### Defense-in-Depth Strategy (Aligned with DESIGN_PROPOSAL.md)

The DESIGN_PROPOSAL already uses SQLCipher with Argon2id key derivation. SMTP credentials get an additional layer:

| Layer | Protection | Mechanism |
|---|---|---|
| **Layer 1** | Database-level encryption | SQLCipher AES-256 (already in DESIGN_PROPOSAL) |
| **Layer 2** | Field-level encryption | Fernet on SMTP password column |
| **Layer 3** | Key derivation | Fernet key derived from user's master password |

### SMTP Credentials Table

```sql
CREATE TABLE smtp_credentials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name       TEXT NOT NULL UNIQUE,
    host                TEXT NOT NULL,
    port                INTEGER NOT NULL DEFAULT 587,
    use_tls             BOOLEAN NOT NULL DEFAULT 1,
    use_ssl             BOOLEAN NOT NULL DEFAULT 0,
    username            TEXT NOT NULL,
    password_encrypted  BLOB NOT NULL,    -- Fernet-encrypted
    from_email          TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT 1,
    created_at          TEXT DEFAULT (datetime('now')),
    updated_at          TEXT DEFAULT (datetime('now'))
);
```

### Why Not OS Keychain?

The OpenAI research recommends OS keychain/credential vault. However, for **Zorivest specifically**:

- The DESIGN_PROPOSAL already stores all settings inside the encrypted database
- Adding OS keychain dependency (`keyring` library) introduces platform-specific complexity
- SQLCipher + Fernet double-encryption provides equivalent security
- Keeps all data portable in a single encrypted file (important for the desktop app's portability goals)

**Recommendation**: Store in encrypted database with Fernet field-level encryption, consistent with the existing key-value settings pattern from DESIGN_PROPOSAL.md.

---

## 9. Failure Handling & Retry Strategy

### Stage-Specific Strategies

| Stage | Failure Type | Retry? | Idempotency Key |
|---|---|---|---|
| **Fetch** | API timeout, 5xx, network | ✅ 3 attempts, exponential backoff | `source + window + etag/hash` |
| **Process** | Logic error, bad data | ❌ Fail fast with diagnostics | Safe recomputation (idempotent) |
| **Render** | Template error | ❌ Fail fast | N/A |
| **Send** | SMTP timeout, 5xx | ✅ 3 attempts, exponential backoff | `message_id` in email_outbox |

### Retry Implementation (tenacity)

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, SMTPException)),
    before_sleep=lambda rs: logger.warning(f"Retry attempt {rs.attempt_number}")
)
async def send_with_retry(emailer, subject, to, html, text):
    return await emailer.send(subject, to, html, text)
```

### Email Outbox Pattern

Prevents duplicate sends and enables safe retry:

```sql
CREATE TABLE email_outbox (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id  TEXT NOT NULL UNIQUE,  -- UUID for idempotency
    run_id      TEXT REFERENCES pipeline_run(run_id),
    to_email    TEXT NOT NULL,
    subject     TEXT NOT NULL,
    html_body   TEXT NOT NULL,
    text_body   TEXT,
    status      TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING | SENT | FAILED | DEAD_LETTER
    attempts    INTEGER NOT NULL DEFAULT 0,
    last_error  TEXT,
    sent_at     TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
```

### Dead-Letter Handling

After 3 failed attempts, mark as `DEAD_LETTER` and surface in the Electron UI for manual action. User can:
- Retry manually
- View error details
- Change SMTP provider and retry

---

## 10. Proposed Module Structure

Fits within the existing monorepo structure from DESIGN_PROPOSAL.md:

```
packages/
├── core/
│   └── src/zorivest_core/
│       ├── domain/
│       │   └── scheduler/
│       │       ├── models.py           # EmailMessage, SmtpConfig, SmtpProvider enum
│       │       └── events.py           # PipelineCompleted, PipelineFailedEvent
│       ├── application/
│       │   └── scheduler/
│       │       ├── ports.py            # Protocol interfaces (all 5 ports)
│       │       ├── pipeline.py         # PipelineService orchestrator
│       │       └── use_cases.py        # SendReport, ScheduleTask, TestConnection
│       └── services/
│           └── scheduler_service.py    # Service layer entry point
│
├── infrastructure/
│   └── src/zorivest_infra/
│       └── scheduler/
│           ├── smtp_adapter.py         # Generic aiosmtplib adapter (all providers)
│           ├── smtp_factory.py         # Provider defaults + config builder
│           ├── failover_adapter.py     # Composite: tries providers in sequence
│           ├── jinja_adapter.py        # Jinja2 template rendering
│           ├── credential_adapter.py   # SQLCipher + Fernet storage
│           └── apscheduler_adapter.py  # APScheduler wrapper
│
├── api/
│   └── src/zorivest_api/
│       └── routes/
│           └── scheduler.py            # REST endpoints: schedules, email config, manual trigger
│
└── templates/
    └── email/
        ├── base_report.html            # Base layout with inline CSS
        ├── daily_summary.html          # Extends base; data table + stats
        └── alert_notification.html     # Extends base; alert formatting
```

---

## 11. Python Dependencies

### New Dependencies for this Module

| Package | Version | Purpose |
|---|---|---|
| `apscheduler` | `>=3.10,<4.0` | In-process task scheduling |
| `aiosmtplib` | `>=3.0` | Async SMTP client |
| `jinja2` | `>=3.1` | Email template engine |
| `cryptography` | `>=42.0` | Fernet field-level encryption for credentials |
| `tenacity` | `>=8.2` | Retry with exponential backoff |

### Already in DESIGN_PROPOSAL Stack

| Package | Used For |
|---|---|
| `httpx` | External API fetching (ExternalApiPort adapter) |
| `sqlalchemy` | Database access, repositories, UoW |
| `sqlcipher3` | Encrypted SQLite |
| `structlog` | Structured logging with correlation IDs |
| `pydantic` | Settings validation, DTOs |

---

## 12. REST API Endpoints

All GUI and MCP interactions route through these FastAPI endpoints. This ensures **one set of business rules** regardless of whether the user clicks a button or an AI agent calls a tool.

### Schedule Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/schedules` | List all scheduled jobs (id, trigger, next_run, status) |
| `POST` | `/api/v1/schedules` | Create a new scheduled job (cron expression, pipeline type) |
| `GET` | `/api/v1/schedules/{job_id}` | Get details of a specific job |
| `PATCH` | `/api/v1/schedules/{job_id}` | Update trigger, enable/disable |
| `DELETE` | `/api/v1/schedules/{job_id}` | Remove a scheduled job |
| `POST` | `/api/v1/schedules/{job_id}/run-now` | Trigger immediate execution |

### Pipeline Runs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/pipeline/runs` | List recent pipeline runs with status/timing |
| `GET` | `/api/v1/pipeline/runs/{run_id}` | Get run details including per-step status |
| `GET` | `/api/v1/pipeline/runs/{run_id}/steps` | Get step-level breakdown (fetch/process/render/send) |
| `POST` | `/api/v1/pipeline/runs/{run_id}/retry` | Retry a failed run from last failed step |

### SMTP Provider Configuration

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/email/providers` | List configured SMTP providers (passwords redacted) |
| `POST` | `/api/v1/email/providers` | Add/update an SMTP provider configuration |
| `DELETE` | `/api/v1/email/providers/{provider_name}` | Remove a provider |
| `POST` | `/api/v1/email/providers/{provider_name}/test` | Send a test email to verify connectivity |
| `PATCH` | `/api/v1/email/providers/{provider_name}/activate` | Set as active provider |

### Email Outbox

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/email/outbox` | List sent/pending/failed emails |
| `GET` | `/api/v1/email/outbox/{message_id}` | Get email details including rendered HTML |
| `POST` | `/api/v1/email/outbox/{message_id}/retry` | Retry a failed/dead-letter email |

### Email Templates

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/email/templates` | List available templates |
| `POST` | `/api/v1/email/templates/preview` | Render a template with sample data (returns HTML) |

### Pydantic Request/Response Schemas

```python
# api/schemas/scheduler.py

class ScheduleCreate(BaseModel):
    cron_expression: str          # "0 8 * * *" (daily 8am UTC)
    pipeline_type: str            # "daily_report" | "data_refresh" | custom
    enabled: bool = True
    description: str | None = None

class ScheduleResponse(BaseModel):
    job_id: str
    cron_expression: str
    pipeline_type: str
    enabled: bool
    next_run_utc: datetime | None
    last_run_utc: datetime | None
    description: str | None

class SmtpProviderCreate(BaseModel):
    provider_name: str            # "gmail" | "brevo" | "sendgrid" | custom
    host: str
    port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    username: str
    password: str                 # Plaintext here; encrypted at rest by adapter
    from_email: str

class SmtpProviderResponse(BaseModel):
    provider_name: str
    host: str
    port: int
    use_tls: bool
    use_ssl: bool
    username: str
    password: str = "********"    # Always redacted in responses
    from_email: str
    is_active: bool

class PipelineRunResponse(BaseModel):
    run_id: str
    status: str                   # PENDING | RUNNING | SUCCESS | FAILED
    started_at: datetime | None
    finished_at: datetime | None
    duration_seconds: float | None
    error: str | None
    steps: list[PipelineStepResponse]

class PipelineStepResponse(BaseModel):
    step_name: str                # fetch | process | render | send
    status: str
    attempt: int
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
```

---

## 13. GUI Control Surface (Electron + React)

The scheduler/email module adds **three new pages** to the Electron + React UI, plus a **dashboard widget** for at-a-glance status. All pages communicate with the Python backend via the REST endpoints defined in Section 12.

### 13.1 Dashboard Widget: Scheduler Status Card

Added to the existing Dashboard page as a card component:

```
┌─────────────────────────────────────────────────────────┐
│  📅 Scheduled Tasks                          ⚙️ Manage  │
│  ─────────────────────────────────────────────────────  │
│  ● Daily Report    08:00 UTC   Next: 6h 23m   ✅ Active │
│  ● Data Refresh    */30 * * *  Next: 12m       ✅ Active │
│  ● Weekly Summary  Sun 18:00   Next: 3d 4h     ⏸ Paused │
│  ─────────────────────────────────────────────────────  │
│  Last pipeline: ✅ Success (2m 14s ago)                  │
│  Emails sent today: 3/300 (Brevo)                       │
└─────────────────────────────────────────────────────────┘
```

**Data source**: `GET /api/v1/schedules` + `GET /api/v1/pipeline/runs?limit=1`  
**Refresh**: TanStack Query with 30-second polling interval  
**Interactions**: "Manage" navigates to Schedule Management page

### 13.2 Page: Schedule Management (`/schedules`)

CRUD interface for scheduled jobs.

```
┌──────────────────────────────────────────────────────────────────┐
│  Schedule Management                              [+ New Schedule]│
├──────────────────────────────────────────────────────────────────┤
│  ┌─ Filters ─────────────────────────────────────────────────┐  │
│  │ Status: [All ▾]  Type: [All ▾]  Search: [____________]    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Schedule List (TanStack Table) ─────────────────────────┐   │
│  │ ☐  Name           Cron           Next Run    Status  ⋮   │   │
│  │ ☐  Daily Report   0 8 * * *      6h 23m      ✅      ⋮   │   │
│  │ ☐  Data Refresh   */30 * * * *   12m          ✅      ⋮   │   │
│  │ ☐  Weekly Digest  0 18 * * 0     3d 4h        ⏸      ⋮   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ⋮ menu: [▶ Run Now] [✏ Edit] [⏸ Pause] [🗑 Delete]             │
└──────────────────────────────────────────────────────────────────┘
```

**Create/Edit Dialog** (Shadcn/Radix modal):

```
┌────────────────────── New Schedule ──────────────────────┐
│                                                          │
│  Name:        [Daily Performance Report        ]         │
│  Pipeline:    [daily_report              ▾]              │
│                                                          │
│  ── Schedule ──────────────────────────────────────────  │
│  Mode:  (●) Cron   ( ) Interval                          │
│                                                          │
│  Cron:        [0 8 * * *                       ]         │
│  Timezone:    [UTC                         ▾]            │
│  Preview:     "Every day at 08:00 UTC"                   │
│               Next 3 runs: Feb 13 08:00, Feb 14 08:00... │
│                                                          │
│  ── Recipients ────────────────────────────────────────  │
│  To:          [user@example.com                ]  [+ Add]│
│                                                          │
│  ── Options ───────────────────────────────────────────  │
│  ☑ Enabled      ☑ Skip if previous run still active      │
│  Misfire grace: [3600] seconds                           │
│                                                          │
│                            [Cancel]  [Save Schedule]     │
└──────────────────────────────────────────────────────────┘
```

**Key UI features**:
- **Cron expression preview**: Human-readable translation + next 3 run times (computed client-side with `cronstrue` or server-side)
- **Run Now**: `POST /api/v1/schedules/{job_id}/run-now` — triggers immediate pipeline execution
- **Bulk actions**: Select multiple → pause/resume/delete
- **Status toggle**: Inline enable/disable with `PATCH /api/v1/schedules/{job_id}`

### 13.3 Page: Pipeline Runs (`/pipelines`)

Execution history with drill-down into individual runs.

```
┌──────────────────────────────────────────────────────────────────┐
│  Pipeline Runs                                                   │
├──────────────────────────────────────────────────────────────────┤
│  ┌─ Filters ─────────────────────────────────────────────────┐  │
│  │ Status: [All ▾]  Date: [Last 7 days ▾]  Pipeline: [All ▾]│  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Run History (TanStack Table) ───────────────────────────┐   │
│  │ Run ID     Pipeline       Started          Duration Status│   │
│  │ a3b8d1..   Daily Report   Feb 12 08:00:03  2m 14s   ✅   │   │
│  │ f81d4f..   Data Refresh   Feb 12 07:30:01  45s      ✅   │   │
│  │ c5dae3..   Daily Report   Feb 11 08:00:02  —        ❌   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Run Detail (expandable row / side panel) ───────────────┐   │
│  │ Run a3b8d1.. — Daily Report — Feb 12 08:00:03            │   │
│  │                                                          │   │
│  │  Step        Status   Duration   Attempt   Error         │   │
│  │  1. Fetch    ✅        32s        1/3       —             │   │
│  │  2. Process  ✅        48s        1/1       —             │   │
│  │  3. Render   ✅        0.3s       1/1       —             │   │
│  │  4. Send     ✅        1.2s       1/3       —             │   │
│  │                                                          │   │
│  │                                         [🔄 Retry Run]   │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

**Key UI features**:
- **Expandable rows**: Click a run to see step-level breakdown with timings
- **Failed run indicator**: Red badge + error message + retry button
- **Dead-letter badge**: Orange "Needs Attention" indicator for runs that exhausted retries
- **Retry from failure point**: `POST /api/v1/pipeline/runs/{run_id}/retry`
- **Auto-refresh**: TanStack Query polling every 10s while a run is `RUNNING`

### 13.4 Page: Email Settings (`/settings/email`)

SMTP provider configuration and email outbox.

```
┌──────────────────────────────────────────────────────────────────┐
│  Email Configuration                                             │
├────────────────────┬─────────────────────────────────────────────┤
│                    │                                             │
│  Providers         │   ┌─ Gmail (Active) ✅ ───────────────────┐ │
│  ─────────────     │   │                                       │ │
│  ● Gmail    ✅     │   │  Host:     smtp.gmail.com              │ │
│  ○ Brevo    ⏸     │   │  Port:     587 (STARTTLS)              │ │
│  ○ SendGrid ⏸     │   │  Username: user@gmail.com              │ │
│                    │   │  Password: ••••••••  [👁 Show]          │ │
│  [+ Add Provider]  │   │  From:     user@gmail.com              │ │
│                    │   │                                       │ │
│                    │   │  [📧 Send Test Email]  [✏ Edit]  [🗑]  │ │
│                    │   └───────────────────────────────────────┘ │
│                    │                                             │
├────────────────────┴─────────────────────────────────────────────┤
│                                                                  │
│  Recent Emails (Outbox)                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Date            To               Subject       Status   │   │
│  │ Feb 12 08:02    user@email.com   Daily Report   ✅ Sent  │   │
│  │ Feb 11 08:02    user@email.com   Daily Report   ✅ Sent  │   │
│  │ Feb 10 08:03    user@email.com   Daily Report   ❌ Failed│   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Failed email detail: Click row → view error + [🔄 Retry]        │
└──────────────────────────────────────────────────────────────────┘
```

**Add Provider Dialog**:

```
┌────────────────── Add SMTP Provider ──────────────────────┐
│                                                           │
│  Provider: [Gmail               ▾]                        │
│            (auto-fills host/port/TLS defaults)             │
│                                                           │
│  Host:     [smtp.gmail.com                      ]         │
│  Port:     [587          ]  ☑ STARTTLS  ☐ SSL             │
│  Username: [user@gmail.com                      ]         │
│  Password: [••••••••••••••••                    ] [👁]     │
│  From:     [user@gmail.com                      ]         │
│                                                           │
│  ⚠️ Gmail requires an App Password (2FA must be enabled). │
│     Regular passwords will be rejected.                    │
│     → How to create an App Password                        │
│                                                           │
│                 [Cancel]  [Test & Save]                    │
└───────────────────────────────────────────────────────────┘
```

**Key UI features**:
- **Provider presets**: Dropdown auto-fills host, port, TLS/SSL based on provider (Gmail, Brevo, SendGrid, etc.)
- **Context-sensitive help**: Provider-specific warnings (Gmail App Password, SendGrid `apikey` username, Brevo SMTP key)
- **Test & Save**: Performs `POST /api/v1/email/providers/{name}/test` before saving — validates connectivity
- **Password masking**: Shown as dots; reveal toggle; password is Fernet-encrypted at rest
- **Active provider indicator**: Only one provider active at a time; switch with one click

### 13.5 Template Preview

Accessible from Email Settings or Pipeline page:

```
┌──────────────────── Template Preview ─────────────────────┐
│                                                           │
│  Template: [daily_summary.html        ▾]                  │
│                                                           │
│  ┌─ Preview (rendered HTML iframe) ──────────────────┐    │
│  │                                                   │    │
│  │  📊 Daily Report                                   │    │
│  │  Generated: 2026-02-12T08:00:03Z                  │    │
│  │                                                   │    │
│  │  ┌──────────┐  ┌──────────┐                       │    │
│  │  │ 47       │  │ 3        │                       │    │
│  │  │ Fetched  │  │ Reports  │                       │    │
│  │  └──────────┘  └──────────┘                       │    │
│  │                                                   │    │
│  │  Ticker  | Open   | Close  | Change               │    │
│  │  AAPL    | 189.50 | 191.20 | +0.90%               │    │
│  │  MSFT    | 420.10 | 418.80 | -0.31%               │    │
│  │  ...                                              │    │
│  └───────────────────────────────────────────────────┘    │
│                                                           │
│  [📧 Send Test Email]  [📋 Copy HTML]  [Close]            │
└───────────────────────────────────────────────────────────┘
```

**Data source**: `POST /api/v1/email/templates/preview` with sample data  
**Key feature**: Live preview with real template rendering before scheduling

### React Component Architecture

```
ui/src/
├── pages/
│   ├── SchedulesPage.tsx          # Schedule CRUD (TanStack Table)
│   ├── PipelineRunsPage.tsx       # Run history with drill-down
│   └── EmailSettingsPage.tsx      # SMTP config + outbox
├── components/scheduler/
│   ├── SchedulerStatusCard.tsx    # Dashboard widget
│   ├── ScheduleTable.tsx          # Sortable/filterable schedule list
│   ├── ScheduleDialog.tsx         # Create/edit modal with cron preview
│   ├── CronExpressionInput.tsx    # Cron builder with human-readable preview
│   ├── PipelineRunTable.tsx       # Run history with expandable rows
│   ├── PipelineStepTimeline.tsx   # Step-level visual timeline
│   ├── SmtpProviderCard.tsx       # Provider config card
│   ├── SmtpProviderDialog.tsx     # Add/edit provider with presets
│   ├── EmailOutboxTable.tsx       # Sent/failed email list
│   └── TemplatePreviewModal.tsx   # Rendered HTML preview
└── hooks/
    ├── useSchedules.ts            # TanStack Query: CRUD on schedules
    ├── usePipelineRuns.ts         # TanStack Query: run history + polling
    ├── useEmailProviders.ts       # TanStack Query: SMTP provider CRUD
    └── useEmailOutbox.ts          # TanStack Query: outbox list
```

### State Management

| Concern | Solution | Rationale |
|---|---|---|
| Server state (schedules, runs, providers, outbox) | **TanStack Query** | Automatic caching, refetching, loading/error states |
| Form state (schedule dialog, provider dialog) | **React Hook Form** + **Zod** | Validation with type inference |
| UI state (selected provider, expanded row) | **Zustand** or local `useState` | Minimal global state needed |
| Real-time polling | TanStack Query `refetchInterval` | 30s for schedules, 10s for active runs |

---

## 14. MCP Tool Surface (AI Agent Access)

Following the DESIGN_PROPOSAL.md pattern, MCP tools are **thin TypeScript wrappers** that call the same REST endpoints as the GUI. Each tool has a clear, specific description that helps LLMs decide when and how to use it.

### 14.1 MCP Tool Definitions

```typescript
// mcp-server/src/tools/scheduler-tools.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

const API_BASE = 'http://localhost:8765/api/v1';

export function registerSchedulerTools(server: McpServer) {

  // ── Schedule Management ──────────────────────────────────────

  server.tool(
    'list_schedules',
    'List all scheduled pipeline jobs with their cron expressions, next run times, and enabled/disabled status.',
    {},
    async () => {
      const res = await fetch(`${API_BASE}/schedules`);
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'create_schedule',
    'Create a new scheduled pipeline job. Accepts a cron expression (e.g., "0 8 * * *" for daily at 8am UTC) and a pipeline type.',
    {
      cron_expression: { type: 'string', description: 'Cron expression (5-field: minute hour day month weekday)' },
      pipeline_type: { type: 'string', description: 'Pipeline to run: "daily_report", "data_refresh", or custom' },
      description: { type: 'string', description: 'Human-readable description of this schedule' },
      enabled: { type: 'boolean', description: 'Whether the schedule is active (default: true)' },
    },
    async ({ cron_expression, pipeline_type, description, enabled = true }) => {
      const res = await fetch(`${API_BASE}/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cron_expression, pipeline_type, description, enabled }),
      });
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'update_schedule',
    'Update an existing schedule. Can change the cron expression, enable/disable it, or update the description.',
    {
      job_id: { type: 'string', description: 'Schedule job ID to update' },
      cron_expression: { type: 'string', description: 'New cron expression (optional)' },
      enabled: { type: 'boolean', description: 'Enable or disable (optional)' },
      description: { type: 'string', description: 'Updated description (optional)' },
    },
    async ({ job_id, ...updates }) => {
      const res = await fetch(`${API_BASE}/schedules/${job_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'run_pipeline_now',
    'Immediately trigger a pipeline run. Skips waiting for the next scheduled time. Returns the new run ID for tracking.',
    {
      job_id: { type: 'string', description: 'Schedule job ID to trigger immediately' },
    },
    async ({ job_id }) => {
      const res = await fetch(`${API_BASE}/schedules/${job_id}/run-now`, { method: 'POST' });
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  // ── Pipeline Run Monitoring ──────────────────────────────────

  server.tool(
    'list_pipeline_runs',
    'List recent pipeline execution history with status, timing, and error details. Use status filter to find failed runs.',
    {
      limit: { type: 'number', description: 'Max results (default: 20)' },
      status: { type: 'string', description: 'Filter by status: PENDING, RUNNING, SUCCESS, FAILED (optional)' },
    },
    async ({ limit = 20, status }) => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (status) params.set('status', status);
      const res = await fetch(`${API_BASE}/pipeline/runs?${params}`);
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'get_pipeline_run',
    'Get detailed status of a specific pipeline run, including per-step breakdown (fetch, process, render, send) with individual timings and error messages.',
    {
      run_id: { type: 'string', description: 'Pipeline run ID' },
    },
    async ({ run_id }) => {
      const res = await fetch(`${API_BASE}/pipeline/runs/${run_id}`);
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'retry_pipeline_run',
    'Retry a failed pipeline run starting from the last failed step. Will not re-run already-successful steps.',
    {
      run_id: { type: 'string', description: 'Failed pipeline run ID to retry' },
    },
    async ({ run_id }) => {
      const res = await fetch(`${API_BASE}/pipeline/runs/${run_id}/retry`, { method: 'POST' });
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  // ── Email Provider Management ────────────────────────────────

  server.tool(
    'list_email_providers',
    'List configured SMTP email providers with connection details (passwords are redacted). Shows which provider is currently active.',
    {},
    async () => {
      const res = await fetch(`${API_BASE}/email/providers`);
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'configure_email_provider',
    'Add or update an SMTP email provider configuration. Supported providers: gmail (requires App Password), brevo (300/day free), sendgrid, mailgun, resend, ses, mailtrap. The password is encrypted at rest.',
    {
      provider_name: { type: 'string', description: 'Provider identifier: gmail, brevo, sendgrid, mailgun, resend, ses, mailtrap, or custom' },
      host: { type: 'string', description: 'SMTP host (e.g., smtp.gmail.com)' },
      port: { type: 'number', description: 'SMTP port (default: 587)' },
      use_tls: { type: 'boolean', description: 'Use STARTTLS (default: true)' },
      username: { type: 'string', description: 'SMTP username' },
      password: { type: 'string', description: 'SMTP password or API key (will be encrypted at rest)' },
      from_email: { type: 'string', description: 'Sender email address' },
    },
    async (params) => {
      const res = await fetch(`${API_BASE}/email/providers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'test_email_provider',
    'Send a test email through a configured SMTP provider to verify connectivity. Returns success/failure with error details.',
    {
      provider_name: { type: 'string', description: 'Provider to test (must be already configured)' },
      to_email: { type: 'string', description: 'Recipient email for the test message (optional, defaults to from_email)' },
    },
    async ({ provider_name, to_email }) => {
      const res = await fetch(`${API_BASE}/email/providers/${provider_name}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_email }),
      });
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );

  server.tool(
    'list_email_outbox',
    'List emails in the outbox with their send status. Use to check if emails were sent successfully or to find failed/dead-letter messages that need attention.',
    {
      limit: { type: 'number', description: 'Max results (default: 20)' },
      status: { type: 'string', description: 'Filter: PENDING, SENT, FAILED, DEAD_LETTER (optional)' },
    },
    async ({ limit = 20, status }) => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (status) params.set('status', status);
      const res = await fetch(`${API_BASE}/email/outbox?${params}`);
      return { content: [{ type: 'text', text: JSON.stringify(await res.json(), null, 2) }] };
    }
  );
}
```

### 14.2 MCP Tool Summary

| Tool Name | Description | REST Endpoint |
|---|---|---|
| `list_schedules` | List all scheduled jobs | `GET /schedules` |
| `create_schedule` | Create new scheduled pipeline | `POST /schedules` |
| `update_schedule` | Update cron/enable/disable | `PATCH /schedules/{id}` |
| `run_pipeline_now` | Trigger immediate execution | `POST /schedules/{id}/run-now` |
| `list_pipeline_runs` | List execution history | `GET /pipeline/runs` |
| `get_pipeline_run` | Get run + step details | `GET /pipeline/runs/{id}` |
| `retry_pipeline_run` | Retry from failed step | `POST /pipeline/runs/{id}/retry` |
| `list_email_providers` | List SMTP configurations | `GET /email/providers` |
| `configure_email_provider` | Add/update SMTP provider | `POST /email/providers` |
| `test_email_provider` | Send test email | `POST /email/providers/{name}/test` |
| `list_email_outbox` | Check email send status | `GET /email/outbox` |

### 14.3 Example AI Agent Workflows

**Scenario 1**: AI sets up daily reporting
```
User: "Set up a daily report at 8am and send it to my email"

Agent:
  1. configure_email_provider(provider_name="gmail", host="smtp.gmail.com", ...)
  2. test_email_provider(provider_name="gmail")
  3. create_schedule(cron_expression="0 8 * * *", pipeline_type="daily_report")
  4. run_pipeline_now(job_id="...")  # Test run
  5. get_pipeline_run(run_id="...")  # Verify success
```

**Scenario 2**: AI diagnoses failed pipeline
```
User: "My daily report didn't arrive this morning"

Agent:
  1. list_pipeline_runs(status="FAILED", limit=5)
  2. get_pipeline_run(run_id="...")  # Inspect step-level failure
  3. > "The send step failed with: SMTPAuthenticationError. Your Gmail App Password may have expired."
  4. test_email_provider(provider_name="gmail")  # Confirm
  5. > "SMTP connection failed. Please update your Gmail App Password."
```

**Scenario 3**: AI changes schedule frequency
```
User: "Change my reports to weekly on Sunday evenings"

Agent:
  1. list_schedules()  # Find the daily_report job_id
  2. update_schedule(job_id="...", cron_expression="0 18 * * 0", description="Weekly Sunday report")
  3. > "Updated. Next run: Sunday Feb 16 at 18:00 UTC."
```

### 14.4 Access Path Consistency

Following the DESIGN_PROPOSAL principle: **both MCP tools and the Electron UI call the same REST API**, ensuring:

```mermaid
graph LR
  A[Electron UI] -->|fetch()| C[FastAPI REST API]
  B[MCP Server] -->|fetch()| C
  C --> D[Service Layer]
  D --> E[Ports/Adapters]
  E --> F[APScheduler]
  E --> G[SMTP/aiosmtplib]
  E --> H[SQLCipher DB]
  E --> I[Jinja2 Templates]
```

- **Same validation**: Pydantic schemas validate input from both GUI and MCP
- **Same authorization**: If API key auth is added later, both paths use the same mechanism
- **Same business logic**: Schedule overlap protection, credential encryption, retry limits
- **Same audit trail**: Every action — whether from a button click or an AI command — is logged in `pipeline_run` / `pipeline_step` tables with the same schema

---

## 15. Research Sources

### Web Search (Tavily — Advanced)

1. **Scheduling**: APScheduler vs Celery comparison, APScheduler persistence with SQLAlchemy, FastAPI integration patterns
2. **Email Services**: Free SMTP server comparison (Mailtrap), SMTP provider pricing (Mailgun, SendGrid, Brevo), Gmail SMTP configuration
3. **Templates**: Jinja2 email templates (GeeksforGeeks), FastAPI email service patterns, scheduled report automation

### AI Research (OpenAI GPT-5.2)

- Comprehensive report on APScheduler lifecycle integration, hexagonal pipeline architecture, Gmail SMTP adapter, retry patterns
- Key finding: APScheduler `AsyncIOScheduler` with `lifespan` context manager is the canonical pattern
- Complete working example: APScheduler + FastAPI + Jinja2 + Gmail SMTP

### AI Research (Anthropic Claude Opus 4.6)

- Detailed SMTP provider configuration table with nuances (SendGrid `apikey` username, Brevo SMTP key distinction, SES region-specific endpoints)
- Hexagonal module structure with 4 driven ports
- Defense-in-depth credential security (SQLCipher + Fernet)
- SMTP recommended over provider SDKs for hexagonal alignment
- `aiosmtplib` recommended for async SMTP operations
- `tenacity` recommended for retry with exponential backoff
