# GUI Planning + Email Settings — Implementation Plan (v4)

**Project slug:** `2026-03-24-gui-planning-email`
**MEUs:** MEU-70 (`gui-planning`) + MEU-73 (`gui-email-settings`)
**Build-plan refs:** `06c-gui-planning.md` | `06f-gui-settings.md` §Email Provider
**Date:** 2026-03-24 (v4 — third corrections pass)

---

## Background

### MEU-70 — Completing gui-planning

`TradePlanPage.tsx` and `WatchlistPage.tsx` were built in the prior `gui-plans` iteration. `planning.test.tsx` (950 lines, 25+ suites) already contains all test coverage for both pages and all MEU-70 T1 enhancements.

**MEU-70 actual scope:** Run the test suite, identify failures, fix only implementation code (never test assertions; fixture/setup fixes are the narrow exception). Only known missing component feature: C2 — `calc-copy-shares-btn` copy button in `PositionCalculatorModal.tsx`.

### MEU-73 — Greenfield Email Settings

The generic settings pipeline cannot serve email credentials (closed 24-entry registry, no encryption). **Pattern:** dedicated `EmailProviderModel` + repository + service + route, following the `MarketProviderSettings`/`ProviderConnectionService` pattern exactly.

**API contract (spec `06f-gui-settings.md:256-258`):**
- `GET /api/v1/settings/email` — returns config with `has_password: bool` (not raw password)
- `PUT /api/v1/settings/email` — saves 7 fields; empty password = keep existing
- `POST /api/v1/settings/email/test` — `aiosmtplib` SMTP test

**Route-shadowing fix:** register `email_settings_router` before `settings_router` in `main.py` (FastAPI static path beats dynamic `{key}` path in registration order).

**Full internal wiring (per live code audit):**

| Component | File | Change |
|---|---|---|
| ORM model | `models.py` | Add `EmailProviderModel` (single-row, `LargeBinary` for encrypted password) |
| Repository protocol | `ports.py` | Add `EmailProviderRepository` Protocol + add `email_provider` slot to `UnitOfWork` Protocol |
| Repository impl | `email_provider_repository.py` | `SqlAlchemyEmailProviderRepository` using `EmailProviderModel` imported from `models.py` |
| UoW impl | `unit_of_work.py` | Import + add `email_provider: SqlAlchemyEmailProviderRepository` to class body and `__enter__` |
| Service | `email_provider_service.py` | `EmailProviderService(uow, encryption)` — `get_config`, `save_config`, `test_connection` |
| Lifespan | `main.py` | `app.state.email_provider_service = EmailProviderService(uow=uow, encryption=_encryption)` — after existing services |
| Dependency | `dependencies.py` | `get_email_provider_service` — resolves from `app.state.email_provider_service` |
| Route | `email_settings.py` | Router prefix `/api/v1/settings/email`; registered **before** `settings_router` |

---

## Spec Sufficiency Gate

### MEU-70 — All ACs traceable

| AC | Component | Test Line |
|---|---|---|
| AC-1 Planning tabs | PlanningLayout | L461 |
| AC-2 Conviction indicators | TradePlanPage | L114 |
| AC-3 Detail panel | TradePlanPage | L158 |
| AC-4 Live R:R | TradePlanPage | L173 |
| AC-5 CRUD | TradePlanPage | L187, L210 |
| AC-5a Status PATCH buttons | TradePlanPage | L234 |
| AC-6 Filters | TradePlanPage | L134, L146 |
| AC-7 Linked trade readonly | TradePlanPage | L258 |
| AC-8 Watchlist list+detail | WatchlistPage | L297, L306 |
| AC-9 Add/remove ticker | WatchlistPage | L319, L346 |
| AC-10 Create watchlist | WatchlistPage | L370 |
| C2 Copy shares | PositionCalculatorModal | L505 — confirm `calc-copy-shares-btn` in component |
| T2 Calculator integration | TradePlanPage | L649 |
| T3 Account dropdown | TradePlanPage | L531 |
| T4-UX Trade picker | TradePlanPage | L766 |
| T5 Status timestamps | TradePlanPage | L720 |
| T6 Strategy combobox | TradePlanPage | L592 |
| W3 Ticker list preview | WatchlistPage | L697 |

### MEU-73 — Design contracts

| Contract | Source |
|---|---|
| `GET/PUT /api/v1/settings/email`, `POST /api/v1/settings/email/test` | Spec `06f-gui-settings.md:256-258` |
| Password Fernet-encrypted at rest | Spec `06f-gui-settings.md` §Credentials |
| Single-row table (id=1 always) | Local Canon (MarketProviderSettings analogy) |
| Route registered before `settings_router` | Local Canon (avoids `{key}` shadowing) |
| 6 preset auto-fill (client-side only) | Spec `06f-gui-settings.md` §Preset Auto-Fill |

---

## Proposed Changes

### MEU-70 — Run Tests, Fix Implementation Gaps

#### [MODIFY] [PositionCalculatorModal.tsx](file:///p:/zorivest/ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx)

Add `data-testid="calc-copy-shares-btn"` copy button. Additional fixes only if vitest reveals implementation gaps in other T1 suites; test assertions are never modified.

---

### MEU-73 — Email Provider (Full Internal Wiring)

#### [MODIFY] [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py)

Add `EmailProviderModel` in the `# ── Balance/Settings Models` section:

```python
class EmailProviderModel(Base):
    """Email SMTP provider configuration — singleton row."""
    __tablename__ = "email_provider"
    id = Column(Integer, primary_key=True, default=1)
    provider_preset = Column(String(50), nullable=True)
    smtp_host = Column(String(256), nullable=True)
    port = Column(Integer, nullable=True)
    security = Column(String(10), nullable=True)  # "STARTTLS" | "SSL"
    username = Column(String(256), nullable=True)
    password_encrypted = Column(LargeBinary, nullable=True)
    from_email = Column(String(256), nullable=True)
    updated_at = Column(DateTime, nullable=True)
```

Model lives in `models.py` so that `Base.metadata.create_all(engine)` (called at `main.py:147`) creates the table automatically.

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Add `EmailProviderRepository` Protocol and `email_provider` slot to `UnitOfWork`:

```python
class EmailProviderRepository(Protocol):
    """Repository for email provider configuration (single-row)."""
    def get(self) -> Optional[Any]: ...
    def save(self, config: Any) -> None: ...

class UnitOfWork(Protocol):
    ...
    email_provider: EmailProviderRepository  # MEU-73
```

#### [NEW] [email_provider_repository.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/email_provider_repository.py)

`SqlAlchemyEmailProviderRepository` using `EmailProviderModel` imported from `models.py`:

```python
from zorivest_infra.database.models import EmailProviderModel

class SqlAlchemyEmailProviderRepository:
    def __init__(self, session: Session) -> None: ...
    def get(self) -> Optional[EmailProviderModel]: ...  # id=1 always
    def save(self, config: EmailProviderModel) -> None: ...  # upsert id=1
```

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

Import `SqlAlchemyEmailProviderRepository` and add `email_provider` slot:

```python
from zorivest_infra.database.email_provider_repository import (
    SqlAlchemyEmailProviderRepository,
)

class SqlAlchemyUnitOfWork:
    ...
    email_provider: SqlAlchemyEmailProviderRepository  # MEU-73

    def __enter__(self):
        ...
        self.email_provider = SqlAlchemyEmailProviderRepository(self._session)  # MEU-73
```

#### [NEW] [email_provider_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/email_provider_service.py)

```python
class EmailProviderService:
    def __init__(self, uow, encryption) -> None: ...
    def get_config(self) -> dict: ...          # has_password bool, not raw bytes
    def save_config(self, data: dict) -> None: ...  # Fernet-encrypt password
    def test_connection(self) -> dict: ...    # aiosmtplib; decrypts password for send
```

#### [NEW] [email_settings.py](file:///p:/zorivest/packages/api/src/zorivest_api/routes/email_settings.py)

Router prefix `/api/v1/settings/email`. Three endpoints per spec.

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Two changes:
1. Import and register `email_settings_router` **before** `settings_router`
2. Add to lifespan after existing services: `app.state.email_provider_service = EmailProviderService(uow=uow, encryption=_encryption)`

#### [MODIFY] [dependencies.py](file:///p:/zorivest/packages/api/src/zorivest_api/dependencies.py)

```python
async def get_email_provider_service(request: Request):
    """Resolve EmailProviderService from app state (MEU-73)."""
    svc = getattr(request.app.state, "email_provider_service", None)
    if svc is None:
        raise HTTPException(500, "EmailProviderService not configured")
    return svc
```

#### [NEW] [EmailSettingsPage.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/EmailSettingsPage.tsx)

Consumes `GET/PUT /api/v1/settings/email` and `POST /api/v1/settings/email/test`. See v3 plan for full UI spec.

#### [MODIFY] [router.tsx](file:///p:/zorivest/ui/src/renderer/src/router.tsx)

Add `settingsEmailRoute` at `/settings/email`.

#### [MODIFY] [SettingsLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/SettingsLayout.tsx)

Add "Email Provider" nav item.

#### [NEW] [test_api_email_settings.py](file:///p:/zorivest/tests/unit/test_api_email_settings.py)

AC-E1 through AC-E5. Includes `app.dependency_overrides[get_email_provider_service]` pattern for test isolation (same as all other service tests).

#### [NEW] [EmailSettingsPage.test.tsx](file:///p:/zorivest/ui/src/renderer/src/features/settings/__tests__/EmailSettingsPage.test.tsx)

AC-E6 through AC-E10.

#### [MODIFY] [openapi.committed.json](file:///p:/zorivest/openapi.committed.json)

Regenerated after API changes.

---

## Verification Plan

### MEU-70

```powershell
# Cwd: p:\zorivest\ui
npx vitest run src/renderer/src/features/planning/__tests__/ --reporter=verbose
# Expected: all suites PASS

npm run build
npx playwright test tests/e2e/position-size.test.ts --reporter=list
# Expected: 2 tests PASS
```

### MEU-73

```powershell
# API unit tests (Cwd: p:\zorivest)
uv run pytest tests/unit/test_api_email_settings.py -v
# Expected: 5 tests PASS (AC-E1 through AC-E5)

# Frontend unit tests (Cwd: p:\zorivest\ui)
npx vitest run src/renderer/src/features/settings/__tests__/EmailSettingsPage.test.tsx --reporter=verbose
# Expected: 5 tests PASS (AC-E6 through AC-E10)
```

### Full Regression + Quality Gate

```powershell
# Python regression (Cwd: p:\zorivest)
uv run pytest tests/ --tb=short -q

# MEU gate (Cwd: p:\zorivest)
uv run python tools/validate_codebase.py --scope meu

# Type + lint — Python (Cwd: p:\zorivest)
uv run pyright packages/api packages/core packages/infrastructure
uv run ruff check packages/ tests/

# Type + lint — TypeScript (Cwd: p:\zorivest\ui)
npx tsc --noEmit
npx eslint src/ --max-warnings 0

# OpenAPI spec check (Cwd: p:\zorivest)
uv run python tools/export_openapi.py --check openapi.committed.json
```
