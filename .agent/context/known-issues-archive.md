# Known Issues — Archive

> Resolved issues moved from `known-issues.md`. Full detail preserved for historical reference.
> These entries are NOT loaded on session start — use `grep` or `pomera_notes` search if needed.

---

### [BOUNDARY-GAP] — Systemic input validation gaps across API/MCP write paths ✅ RESOLVED
- **Severity:** ~~High~~ → Resolved (2026-04-11)
- **Component:** api, core (services), mcp-server (planned)
- **Discovered:** 2026-04-05 (handoff 096 review)
- **Status:** ✅ **Fully resolved — 7 of 7 findings closed**
- **Details:** Originally 7 write boundaries lacked strict schema enforcement. All resolved:
  - ✅ F1 Accounts — resolved by MEU-BV1 (handoff 098)
  - ✅ F2 Trades — resolved by MEU-BV2 (handoff 099)
  - ✅ F3 Plans — resolved by MEU-BV3 (handoff 100)
  - ✅ F5 Market Data — resolved by MEU-BV4 (handoff 101)
  - ✅ F6 Email Settings — resolved by MEU-BV5 (handoff 102)
  - ✅ F4 Scheduling — resolved by MEU-BV6 (2026-04-11)
  - ✅ F7 Watchlists — resolved by MEU-BV7 (2026-04-11)
  - ✅ Settings — resolved by MEU-BV8 (2026-04-11)

---

### [PYRIGHT-PREEXIST] — ~300+ pre-existing pyright errors across test suite and services ✅ RESOLVED
- **Severity:** Low–Medium (all test-only or annotation-only; zero runtime impact)
- **Component:** tests (unit, integration, property), core (services)
- **Discovered:** 2026-04-05 (boundary validation review)
- **Status:** ✅ Fully resolved — 13 Tier 1 errors fixed 2026-04-06 (MEU-TS1 ✅), 36 Tier 2 errors fixed 2026-04-11 (MEU-TS2 ✅), 205 Tier 3 errors fixed 2026-04-11 (MEU-TS3 ✅). Only 7 excluded `test_encryption_integrity.py` errors remain (external `sqlcipher3` dep).
- **MEU linkage:** `BUILD_PLAN.md` → CI / Quality Gate Research Items → MEU-TS1 (✅), MEU-TS2 (✅), MEU-TS3 (✅)

#### Tier 1: Safe Test-Only Fixes — ✅ RESOLVED (2026-04-06)

13 errors fixed with zero production code changes:

| Category | Files | Errors | Fix Applied |
|----------|-------|--------|-------------|
| Generator fixture typing | `test_market_data_api.py`, `test_provider_service_wiring.py`, `test_api_email_settings.py` | ~8 | `-> TestClient` → `-> Generator[TestClient, None, None]` |
| Optional narrowing guards | `test_backup_manager.py`, `test_backup_integration.py`, `test_backup_roundtrip.py` | 3 | Added `assert obj is not None` before accessing `.kdf` / `backup_path` |
| Mock protocol compliance | `test_provider_connection_service.py` | 1 | Added `post()` to `MockHttpClient` (satisfies `HttpClient` protocol) |
| Protocol `__mro__` access | `test_ports.py` | 1 | Changed `UnitOfWork.__mro__` → `inspect.getmro(UnitOfWork)` |

**Evidence:** 134/134 tests pass, ruff clean. No production files touched.

#### Tier 2: String Literal → Enum Refactoring (~50 errors) — ✅ RESOLVED (2026-04-11)

- **Fix:** Resolved during MEU-BV1–BV8 boundary validation work which systematically introduced enum usage. 36 string→enum refactors applied during quality pipeline hardening (2026-04-11). Verification via `pyright tests/` shows 0 enum-literal errors.
- **MEU linkage:** MEU-TS2 ✅ 2026-04-11

#### Tier 3: Entity Factory Typing (~205 errors) — ✅ RESOLVED (2026-04-11)

- **Fix:** Applied three techniques across 14+ test files: (1) typed entity factory return annotations with `TYPE_CHECKING` imports, (2) `assert is not None` narrowing guards for Optional member access, (3) targeted `# type: ignore` suppressions for SQLAlchemy ColumnElement descriptor mismatches and Pydantic constructor patterns.
- **Evidence:** `pyright tests/` → 7 errors (all in excluded `test_encryption_integrity.py`), `pytest tests/unit/` → 1575 passed, `pyright packages/` → 0 errors.
- **MEU linkage:** MEU-TS3 ✅ 2026-04-11

#### Tier 4: Core Service Errors — ✅ RESOLVED (2026-04-06)

- `account_service.py:131` — `count_for_account` method not on `TradePlanRepository` port ABC → ✅ Fixed 2026-04-06
- `trade_service.py:175` — `float(filtered["quantity"])` fails type narrowing → ✅ Fixed 2026-04-06

#### Recommended Fix Schedule (Historical)

| Priority | Tier | Error Count | When Fixed | Approach |
|----------|------|-------------|------------|----------|
| P1 | Tier 1 | 13 | 2026-04-06 | Annotation + mock fixes |
| P2 | Tier 2 | ~50 | 2026-04-11 | Enum values from BV work |
| P3 | Tier 3 | ~205 | 2026-04-11 | Factory typing + suppressions |
| P4 | Tier 4 | 2 | 2026-04-06 | Port ABC + type narrowing |

---

### [TEST-ISOLATION] — test_api_foundation.py::test_unlock_propagates_db_unlocked flaky in suite ✅ RESOLVED
- **Severity:** ~~Low~~ → Resolved (2026-04-06)
- **Component:** tests (unit, integration)
- **Discovered:** 2026-04-05 (BV4/BV5 validation)
- **Status:** ✅ **Resolved 2026-04-06**
- **Root cause:** `test_api_roundtrip.py` and `test_gui_api_seams.py` set `os.environ["ZORIVEST_DEV_UNLOCK"] = "1"` at module import time but never cleaned up. When `test_api_foundation.py::TestAppStateWiring` later called `create_app()`, the lifespan read the leaked env var and started with `db_unlocked=True`.
- **Fix:** Added module-scoped `autouse` cleanup fixtures + defensive `autouse` clear.

---

### [TEST-ISOLATION-2] — test_api_roundtrip.py::test_dev_unlock_sets_db_unlocked fails in full suite ✅ RESOLVED
- **Severity:** ~~Low~~ → Resolved (2026-04-11)
- **Component:** tests (integration)
- **Discovered:** 2026-04-11 (Codex review of MEU-TS2/TS3)
- **Status:** ✅ **Resolved 2026-04-11 (MEU-TI2)**
- **Root cause:** Shared module-level `app` singleton between integration test modules caused env var leakage.
- **Fix:** Refactored all 3 integration test modules to use `create_app()` factory in module-scoped fixtures.

---

### [SCHED-WALPICKLE] — APScheduler cannot pickle WAL pragma listeners ✅ RESOLVED
- **Severity:** Medium → Fixed
- **Component:** api (scheduling)
- **Discovered:** 2026-03-19 (MEU-90a persistence wiring)
- **Fix:** Extracted `_set_sqlite_pragmas` to module-level. Added `_execute_policy_callback` with singleton registry.

---

### [SCHED-RUNREPO] — PipelineRunRepository.create() contract mismatch ✅ RESOLVED
- **Severity:** ~~Medium~~ → Resolved (2026-03-19)
- **Component:** api (`scheduling_adapters.py`), core (`scheduling_service.py`)
- **Fix:** Key translation in adapter, added `content_hash`, `_run_model_to_dict()` remapping.

---

### [MCP-CONFIRM] — `create_trade` inputSchema missing `confirmation_token` field ✅ RESOLVED
- **Severity:** High → Fixed
- **Component:** mcp-server
- **Fix:** Added `confirmation_token: z.string().optional()` to inputSchema. Verified with 4 TDD tests.

---

### [DOC-STALESLUG] — `09a-persistence-integration.md` references stale MEU-90b slug ✅ RESOLVED
- **Severity:** Low → Resolved (2026-03-22)
- **Fix:** Updated slug references in `09a-persistence-integration.md` and `08-market-data.md`.

---

### [PREMATURE-STOP] — Context truncation caused 16 task items to be silently dropped ✅ RESOLVED
- **Severity:** ~~High~~ → Resolved (2026-04-25)
- **Component:** Agent workflow (AGENTS.md, skills)
- **Discovered:** 2026-04-25 (pipeline-capabilities session, conversation `9986e441`)
- **Status:** ✅ **Resolved — completion-preflight skill created + AGENTS.md amended**
- **Root cause:** After context truncation, "all tests green" was treated as completion. 16 unchecked task items (rows 19–34) were dropped because: (1) no re-read of project task.md occurred post-truncation, (2) agent workspace copy was updated instead of project copy, (3) no programmatic completion gate existed.
- **Fix:** Created `.agent/skills/completion-preflight/SKILL.md` — a deterministic re-read gate modeled on `terminal-preflight`. Added AGENTS.md cross-reference (line ~273) and Knowledge Item (pomera note #937).
- **RCA:** [premature_stop_analysis.md](file:///p:/zorivest/_inspiration/agents_md_research/premature_stop_analysis.md)
- **Defense layers:** (1) AGENTS.md prose, (2) completion-preflight skill, (3) KI `Zorivest/Completion-Gate-Protocol`, (4) pomera session saves

---

### [TEST-DRIFT-MDS] — 5 tests in test_market_data_service.py fail due to wiring changes ✅ RESOLVED
- **Severity:** ~~Medium~~ → Resolved (2026-04-12)
- **Component:** tests (unit)
- **Discovered:** 2026-04-05
- **Status:** ✅ **Resolved — silently fixed during MEU-65a market data service wiring**
- **Verification:** `pytest tests/unit/test_market_data_service.py` → 13 passed in 0.30s (2026-04-12)

---

### [PIPE-NOLOCALQUERY] — No pipeline step type for querying local DB tables ✅ RESOLVED
- **Severity:** ~~Medium~~ → Resolved (2026-04-25)
- **Component:** core (`pipeline_steps/`)
- **Discovered:** 2026-04-21
- **Status:** ✅ **Resolved by MEU-PH4 (QueryStep) — 2026-04-25**
- **Details:** `FetchStep` was hard-wired to `MarketDataProviderAdapter` (external HTTP only). Could not query local DB tables.
- **Fix:** MEU-PH4 implemented `QueryStep` (`type_name="query"`) — read-only SQL via `SqlSandbox`, parameterized binds, row limit, ref support. 8 unit tests.
