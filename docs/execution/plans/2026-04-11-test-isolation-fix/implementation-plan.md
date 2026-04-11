# Integration Test Isolation Fix — MEU-TI2

> **Known Issue:** `[TEST-ISOLATION-2]` in `.agent/context/known-issues.md`
> **CI Impact:** Quality Gate `Integration tests` step fails on every push
> **Scope:** 3 integration test files, zero production code changes

## Problem

Three integration test modules share the module-level `app` singleton from `zorivest_api.main` (L362: `app = create_app()`):

| Module | Pattern | Issue |
|--------|---------|-------|
| `test_api_accounts_integration.py` | Sets env at L18, imports `app` at L20, cleanup fixture at L23 | Cleanup removes env var before other modules run |
| `test_api_roundtrip.py` | Sets env at L17, imports `app` at L19, cleanup fixture at L22 | Lifespan reads env var that accounts already removed |
| `test_gui_api_seams.py` | Sets env at L22, imports `app` at L24, re-set fixture at L33 | Defensive re-set works but shares same app singleton |

**Root cause:** All three modules import the same `app` object. Each `TestClient(app)` creates a **new lifespan context** that re-reads `os.environ["ZORIVEST_DEV_UNLOCK"]`. When accounts' cleanup fixture removes the env var after its tests but before roundtrip's tests run, the roundtrip lifespan sees `db_unlocked=False`.

**Proof:** The failing test passes in isolation (`pytest tests/integration/test_api_roundtrip.py` → 16/16) but fails in suite context.

## Proposed Changes

### Fix Strategy: Per-Module App Factory

Replace `from zorivest_api.main import app` (singleton) with `from zorivest_api.main import create_app` (factory). Each module creates its own isolated `app` instance through a module-scoped fixture that manages the env var lifecycle.

**Target pattern:**
```python
from zorivest_api.main import create_app  # factory, not singleton

@pytest.fixture(scope="module")
def app():
    """Create a fresh app with ZORIVEST_DEV_UNLOCK for this module only."""
    os.environ["ZORIVEST_DEV_UNLOCK"] = "1"
    _app = create_app()
    yield _app
    os.environ.pop("ZORIVEST_DEV_UNLOCK", None)

@pytest.fixture()
def client(app):
    """TestClient with per-test lifespan from module's app."""
    with TestClient(app) as c:
        yield c
```

---

### [MODIFY] [test_api_roundtrip.py](file:///p:/zorivest/tests/integration/test_api_roundtrip.py)

1. Remove module-level `os.environ["ZORIVEST_DEV_UNLOCK"] = "1"` (L17)
2. Replace `from zorivest_api.main import app` (L19) → `from zorivest_api.main import create_app`
3. Replace `_cleanup_dev_unlock` fixture (L22-32) with module-scoped `app` fixture that sets env, creates app, yields, cleans up
4. Update `client` fixture (L35-39) to accept `app` parameter instead of using module-level `app`

---

### [MODIFY] [test_api_accounts_integration.py](file:///p:/zorivest/tests/integration/test_api_accounts_integration.py)

1. Remove module-level `os.environ["ZORIVEST_DEV_UNLOCK"] = "1"` (L18)
2. Replace `from zorivest_api.main import app` (L20) → `from zorivest_api.main import create_app`
3. Replace `_cleanup_dev_unlock` fixture (L23-27) with module-scoped `app` fixture
4. Update `client` fixture (L30-34) to accept `app` parameter

---

### [MODIFY] [test_gui_api_seams.py](file:///p:/zorivest/tests/integration/test_gui_api_seams.py)

1. Remove module-level `os.environ["ZORIVEST_DEV_UNLOCK"] = "1"` (L22)
2. Replace `from zorivest_api.main import app` (L24) → `from zorivest_api.main import create_app`
3. Replace `_ensure_dev_unlock` fixture (L33-43) with module-scoped `app` fixture
4. Update `client` fixture (L46-49) to accept `app` parameter

---

## Acceptance Criteria

| AC | Description | Source | Verification |
|----|-------------|--------|-------------|
| AC-1 | `test_dev_unlock_sets_db_unlocked` passes in full suite | Known Issue | `pytest tests/ -x --tb=short` — 0 failures |
| AC-2 | All 3 modules use `create_app()` factory, not `from main import app` | Fix strategy | `rg "from zorivest_api.main import app" tests/integration/` — 0 matches |
| AC-3 | No module-level env var set at import time | Fix strategy | `rg "^os.environ" tests/integration/test_api_` — 0 matches |
| AC-4 | Each module has its own `app` fixture managing env lifecycle | Fix strategy | `rg "def app\(\)" tests/integration/` — 3 matches |
| AC-5 | Full integration suite passes | Regression | `pytest tests/integration/ -x` — 0 failures |
| AC-6 | Full unit suite unaffected | Regression | `pytest tests/unit/ -x` — 0 failures |
| AC-7 | CI Quality Gate passes | CI | Push and verify GitHub Actions green |

## Open Questions

None — this is a straightforward mechanical refactoring with a well-understood root cause and proven fix pattern (MEU-90b used similar isolation fixtures).

## Verification Plan

### Automated Tests
```powershell
# 1. Integration suite (in-scope)
uv run pytest tests/integration/ -x --tb=short -q *> C:\Temp\zorivest\pytest-integ.txt
# 2. Full suite including integration (proves AC-1)
uv run pytest tests/ -x --tb=short -q *> C:\Temp\zorivest\pytest-full.txt
# 3. Unit regression
uv run pytest tests/unit/ -x --tb=short -q *> C:\Temp\zorivest\pytest-unit.txt
# 4. Pyright (zero production changes, but verify test typing)
uv run pyright tests/integration/ *> C:\Temp\zorivest\pyright-integ.txt
# 5. MEU gate
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-ti2.txt
```

### Manual Verification
- Push to GitHub and verify CI Quality Gate integration tests step goes green
