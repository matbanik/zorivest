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

---

### [MCP-APPROVBYPASS] — Policy approval endpoint has no source verification ✅ RESOLVED
- **Severity:** ~~Critical~~ → Resolved (2026-04-29)
- **Component:** api (`scheduling.py`), mcp-server, ui (Electron IPC)
- **Discovered:** 2026-04-26
- **Status:** ✅ **Resolved by MEU-PH11 (approval-csrf-token)**
- **Details:** Originally `POST /api/v1/scheduling/policies/{id}/approve` had no mechanism to verify the caller was the GUI, allowing AI agents to self-approve policies.
- **Fix:** `validate_approval_token` FastAPI dependency added to the approve endpoint (`scheduling.py:211`). Token generated by Electron main process IPC (`approval-token-manager.ts`), injected in renderer `scheduling/api.ts`. Single-use, 5-min TTL, policy-scoped.

---

### [MCP-POLICYGAP] — Missing MCP tools for delete_policy and update_policy ✅ RESOLVED
- **Severity:** ~~High~~ → Resolved (2026-04-29)
- **Component:** mcp-server (`scheduling` toolset)
- **Discovered:** 2026-04-26
- **Status:** ✅ **Resolved by MEU-PH12 (mcp-scheduling-gap-fill)**
- **Details:** No MCP tools existed for `delete_policy` or `update_policy`, forcing direct REST calls bypassing MCP guard/audit.
- **Fix:** 3 tools added in `scheduling-tools.ts`: `delete_policy` (L416-473, destructive + confirmation gate), `update_policy` (L475-540, in-place PATCH), `get_email_config` (L542-584, SMTP readiness without credentials).

---

### [EMULATOR-VALIDATE] — Emulator VALIDATE phase accepts invalid SQL and missing infrastructure ✅ RESOLVED
- **Severity:** ~~Medium~~ → Resolved (2026-04-29)
- **Component:** core (`policy_emulator.py`)
- **Discovered:** 2026-04-26
- **Status:** ✅ **Resolved by MEU-PH13 (emulator-validate-hardening)**
- **Details:** VALIDATE phase returned `valid: true` for policies with invalid SQL, unconfigured SMTP, and broken step wiring.
- **Fix:** Three hardening additions in `policy_emulator.py`: (1) `EXPLAIN SQL` schema validation (L244-259), (2) SMTP readiness check for email send steps (L261-276), (3) step output wiring validation — `body_from_step` must reference existing render/compose step (L278-305). 14 unit tests in `test_emulator_validate_hardening.py`.

---

### [MCP-TOOLAUDIT] — MCP tool CRUD audit (post-consolidation) ✅ RESOLVED
- **Severity:** ~~Low~~ → Resolved (2026-04-30)
- **Component:** mcp-server, api
- **Discovered:** 2026-04-27 (original), 2026-04-29 (post-consolidation re-audit)
- **Status:** ✅ **Audit PASS — 46 tested, 44 pass, 0 fail, 2 skip (provider-config-dependent)**
- **Consolidation Score:** 1.08 (13/12 ideal) — Excellent
- **Remediated (P2.5f):** All 4 critical review findings resolved:
  - ✅ F1: `zorivest_plan` relocated trade→ops
  - ✅ F2: 6 action names aligned to v3.1 contract
  - ✅ F3: 116 behavior tests covering all 13 compound tools
  - ✅ F4: `/mcp-audit` validation gate executed
- **Remaining (informational, not blocking):**
  - `get_market_news` 503 (Finnhub 422) — needs provider API key configuration
  - `get_sec_filings` 503 — SEC API not configured
  - No `delete_watchlist` action — low priority feature gap
- **Audit ref:** [MCP Tool Audit Report](MCP/mcp-tool-audit-report.md)

---

### [TRADE-CASCADE] — delete_trade 500 on trade with linked report/images ✅ RESOLVED
- **Severity:** ~~High~~ → Resolved (2026-04-29)
- **Component:** infrastructure (`models.py`), core (`trade_service.py`)
- **Discovered:** 2026-04-29 (live MCP audit)
- **Status:** ✅ **Resolved — 2026-04-29**
- **Fix:** Added `cascade="all, delete-orphan"` to `TradeModel.report`, `ondelete="CASCADE"` to `TradeReportModel.trade_id` FK, `ImageRepository.delete_for_owner()` port+impl, and explicit image+report cleanup in `TradeService.delete_trade()`.
- **Tests:** 2 integration tests (delete-with-report, delete-with-images) + 2 unit tests (service cleanup behavior). All GREEN (2396 passed).

---

### [MCP-TOOLDISCOVERY] — MCP tool descriptions lack workflow context and examples for AI discoverability ✅ RESOLVED
- **Severity:** ~~Medium~~ → Resolved (2026-04-30)
- **Component:** mcp-server
- **Discovered:** 2026-04-12
- **Status:** ✅ **Resolved by MEU-TD1 (`mcp-discoverability-audit`) — 2026-04-30**
- **Details:** Server instructions and tool descriptions were too terse for AI agents to discover and correctly use multi-step workflows. Confirmed gaps across scheduling, accounts, trade-analytics, trade-planning, market-data toolsets.
- **Fix:** MEU-TD1 audited all 13 compound tool descriptions and enriched them with M7 metadata: WORKFLOW context, Prerequisites, Return shapes, Error conditions. Server instructions expanded. M7 enforcement gate added to emerging-standards.md.
- **Sub-issue — Template registry:** Resolved by MEU-PH9 (template CRUD tools + `pipeline://templates` resource) + MEU-TD1 (description enrichment with step-wiring examples).
- **Verification:** All 13 compound tool files in `mcp-server/src/compound/` contain M7-pattern descriptions.

---

### [MCP-TOOLCAP] — IDE tool limits render 68-tool flat registration non-viable ✅ RESOLVED
- **Severity:** ~~Critical~~ → Resolved (2026-04-30)
- **Component:** mcp-server
- **Discovered:** 2026-03-19
- **Status:** ✅ **Resolved by compound-tool consolidation (P2.5f MC0–MC5) — 2026-04-29**
- **Details:** Original flat registration of 68+ tools exceeded IDE limits (Cursor ≤40, VS Code variable). Three-tier strategy was designed as mitigation.
- **Fix:** 85→13 compound-tool consolidation completed (P2.5f MC0–MC5). All 13 compound tools with action-based dispatch. Tool count well within ALL IDE limits. MCP audit passes (46/46 tools tested).
- **Supersedes:** Three-tier strategy is no longer needed — 13 tools fits all IDEs natively.
