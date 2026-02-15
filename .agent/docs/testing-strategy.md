# Testing Strategy — Zorivest

## Test Pyramid

```
         ┌─────────┐
         │  E2E    │  Few — Playwright (UI), TestClient (API)
         ├─────────┤
         │ Integr. │  Medium — Real DB (in-memory SQLite)
         ├─────────┤
         │  Unit   │  Many — Pure logic, no I/O
         └─────────┘
```

## Tools

| Layer | Tool | Command |
|-------|------|---------|
| Python unit | pytest | `pytest tests/unit/` |
| Python integration | pytest + in-memory SQLite | `pytest tests/integration/` |
| Python E2E | pytest + TestClient | `pytest tests/e2e/` |
| TypeScript unit | vitest | `npx vitest run` |
| React components | React Testing Library | `npx vitest run` |
| UI E2E | Playwright | `npx playwright test` |
| Type check (Python) | pyright | `pyright packages/` |
| Type check (TS) | tsc | `npx tsc --noEmit` |
| Lint (Python) | ruff | `ruff check packages/` |
| Lint (TS) | eslint | `npx eslint src/ --max-warnings 0` |

## Coverage Targets (Advisory)

| Package | Target | Rationale |
|---------|--------|-----------|
| `packages/core` | 80–90% | Pure logic, easy to test, bugs are costly |
| `packages/infrastructure` | 70% | Integration tests cover critical paths |
| `packages/api` | 70% | Endpoint + error path tests |
| `ui/` | 50–60% | Focus on logic-heavy components |
| `mcp-server/` | 70% | Tool handlers must be robust |

```bash
# Check coverage (advisory — does not block)
pytest --cov=packages/core --cov-report=term
```

## TDD Workflow

1. **Human writes the test** — defines the specification
2. **AI implements the code** — makes the test pass
3. **Run tests** — verify green
4. **AI NEVER modifies tests** to make them pass
5. **Run full validation** — `.\validate.ps1`
6. **Repeat** for next feature

## Fixtures

### In-Memory SQLite (Integration Tests)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from zorivest_infra.database.models import Base

@pytest.fixture
def session():
    """In-memory SQLite for fast integration tests."""
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

### TestClient (API E2E)

```python
from fastapi.testclient import TestClient
from zorivest_api.main import app

@pytest.fixture
def client():
    return TestClient(app)
```

## Test File Organization

```
tests/
├── unit/
│   ├── test_calculator.py        # PositionSizeCalculator
│   ├── test_entities.py          # Domain entity validation
│   └── test_value_objects.py     # Enums, value types
├── integration/
│   ├── test_repositories.py      # SQLAlchemy repos + real DB
│   └── test_unit_of_work.py      # Transaction management
└── e2e/
    └── test_api_endpoints.py     # FastAPI TestClient
```

## What to Test (per entity)

| Entity | Unit Tests | Integration Tests |
|--------|-----------|-------------------|
| Trade | Validation, field defaults | Save, get, list, exists |
| Account | Validation, type check | Save, get, list |
| ImageAttachment | Mime type, owner fields | Save, get_for_trade, delete |
| Calculator | Basic calc, edge cases, zero inputs | N/A (pure function) |
| UnitOfWork | N/A | Commit, rollback, context manager |
