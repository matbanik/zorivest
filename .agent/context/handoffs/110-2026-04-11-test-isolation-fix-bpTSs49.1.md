---
meu: TI2
slug: test-isolation-fix
build_plan_ref: testing-strategy §49.1
verbosity: standard
---

# Handoff: MEU-TI2 — Integration Test Isolation Fix

## Summary

Resolved `[TEST-ISOLATION-2]`: `test_dev_unlock_sets_db_unlocked` failing in full suite context due to cross-module env var leakage from shared `app` singleton.

## Changed Files

```diff
# tests/integration/test_api_roundtrip.py
- os.environ["ZORIVEST_DEV_UNLOCK"] = "1"
- from zorivest_api.main import app  # noqa: E402
+ from zorivest_api.main import create_app
  # + module-scoped app() fixture with env lifecycle
  # + client(app: FastAPI) fixture

# tests/integration/test_api_accounts_integration.py
- os.environ["ZORIVEST_DEV_UNLOCK"] = "1"
- from zorivest_api.main import app  # noqa: E402
+ from zorivest_api.main import create_app
  # + module-scoped app() fixture with env lifecycle
  # + client(app: FastAPI) fixture

# tests/integration/test_gui_api_seams.py
- os.environ["ZORIVEST_DEV_UNLOCK"] = "1"
- from zorivest_api.main import app  # noqa: E402
+ from zorivest_api.main import create_app
  # + module-scoped app() fixture with env lifecycle
  # + client(app: FastAPI) fixture
```

**Zero production code changes.**

## Evidence

<!-- CACHE BOUNDARY -->

### AC Verification

| AC | Description | Result | Evidence |
|----|-------------|--------|----------|
| AC-1 | `test_dev_unlock_sets_db_unlocked` passes in full suite | ✅ PASS | `pytest tests/integration/ -x` → PASSED |
| AC-2 | No singleton app imports | ✅ PASS | `rg "from zorivest_api.main import app$" tests/integration/` → 0 matches |
| AC-3 | No module-level env var | ✅ PASS | `rg "^os.environ" tests/integration/test_api_` → 0 matches |
| AC-4 | 3 per-module app fixtures | ✅ PASS | `rg "def app()" tests/integration/` → 3 matches |
| AC-5 | Full integration suite passes | ✅ PASS | 165 passed, 1 skipped, 0 failed (9.94s) |
| AC-6 | Full unit suite unaffected | ✅ PASS | 1575 passed, 0 failed (59.93s) |
| AC-7 | CI Quality Gate passes | ⏳ | Pending push + CI run |

### Commands Executed

```
uv run pytest tests/integration/ -x --tb=short -v  → 165 passed, 0 failed
uv run pytest tests/unit/ -x --tb=short -q          → 1575 passed, 0 failed
uv run python tools/validate_codebase.py --scope meu → All 8 blocking checks passed
```

### MEU Gate

```
[1/8] Python Type Check (pyright): PASS
[2/8] Python Lint (ruff): PASS
[3/8] Python Unit Tests (pytest): PASS
[4/8] TypeScript Type Check (tsc): PASS
[5/8] TypeScript Lint (eslint): PASS
[6/8] TypeScript Unit Tests (vitest): PASS
[7/8] Anti-Placeholder Scan: PASS
[8/8] Anti-Deferral Scan: PASS
```

## Residual Risk

None. This was a pure test-infrastructure fix. No production code was modified. The pattern is the same one used by MEU-90b for the original TEST-ISOLATION-1 fix.
