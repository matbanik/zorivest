# Known Issues — Zorivest

> Track bugs, limitations, and workarounds here.

## Active Issues

### [MCP-TOOLCAP] — IDE tool limits render 68-tool flat registration non-viable
- **Severity:** Critical
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Mitigated by Design
- **Details:** Cursor enforces 40-tool hard cap (silently drops 28 tools). ChatGPT has 5,000-token definition cap (~10 tools). LLM accuracy degrades above ~20 tools. See `friction-inventory.md` FR-3.x, FR-10.x.
- **Workaround:** Three-tier strategy: static ≤40 for Cursor, dynamic toolsets for VS Code, full for CLI/API. Client detection via `clientInfo.name` (§5.11).

### [MCP-ZODSTRIP] — `server.tool()` silently strips arguments with z.object()
- **Severity:** Critical
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Open — upstream SDK bug
- **Details:** Passing `z.object({...})` instead of raw Zod shape causes tool to register with empty parameters. No error, no warning. TS-SDK #1291, #1380, PR #1603. See `friction-inventory.md` FR-1.1.
- **Workaround:** Enforce raw shape convention. Add startup assertion that every tool has non-empty `inputSchema.properties`.

### [MCP-AUTHRACE] — Token refresh race condition under concurrent tool execution
- **Severity:** Critical
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Open — needs architectural mitigation
- **Details:** Concurrent 401s trigger overlapping refresh requests. No MCP client reliably handles token lifecycle. See `friction-inventory.md` FR-4.1, FR-4.7.
- **Workaround:** In-memory mutex for refresh; proactive JWT expiry check before each REST call.

### [MCP-WINDETACH] — Node.js `detached: true` broken on Windows since 2016
- **Severity:** Critical
- **Component:** infrastructure
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Open — upstream Node.js bug
- **Details:** `child_process.fork()` with `detached: true` does not work on Windows. Node #5146, #36808. Orphaned processes leave SQLCipher locks. See `friction-inventory.md` FR-9.1.
- **Workaround:** Windows Job Objects for process group management. Platform-specific spawn logic.

### [MCP-HTTPBROKEN] — Streamable HTTP transport has 5 failure modes
- **Severity:** High
- **Component:** mcp-server
- **Discovered:** 2026-03-04 (pre-mortem research)
- **Status:** Mitigated by Design (stdio primary)
- **Details:** Stateless mode broken (#340), async timeouts (#1106), cross-client data leak (GHSA-345p), SSE disconnects (#1211), EPIPE crash (#1564). See `friction-inventory.md` FR-6.x.
- **Workaround:** Use stdio as primary transport. Pin SDK version. Never use stateless mode.

### [UI-ESMSTORE] — electron-store v9+ (ESM-only) crashes electron-vite main process
- **Severity:** Medium
- **Component:** ui
- **Discovered:** 2026-03-14
- **Status:** Workaround Applied (pinned to v8)
- **Details:** `electron-store` v9+ is `"type": "module"` (ESM-only). electron-vite compiles the main process as CJS, so `import Store from 'electron-store'` resolves to `{ default: [class] }` instead of the class — `new Store()` throws `"Store is not a constructor"`. The app crashes before the window opens.
- **Workaround:** Pinned to `electron-store@8` (last CJS version). Same API (`new Store()`, `.get()`, `.set()`), zero code changes. Upgrade back to v10 when electron-vite adds native ESM output for the main process.

### [SCHED-WALPICKLE] — APScheduler cannot pickle WAL pragma listeners *(Resolved)*
- **Severity:** Medium → **Fixed**
- **Component:** api (scheduling)
- **Discovered:** 2026-03-19 (MEU-90a persistence wiring)
- **Status:** Fixed (module-level callback + WAL listener extraction)
- **Details:** SQLAlchemy 2.x `Engine` is fundamentally unpicklable (internal closures in `create_engine`). APScheduler pickles job callbacks — bound methods like `self._execute_policy` pickle `self`, which transitively holds the engine.
- **Fix applied:** (a) Extracted `_set_sqlite_pragmas` from closure to module-level in `unit_of_work.py`. (b) Added module-level `_execute_policy_callback` in `scheduler_service.py` with singleton registry. (c) APScheduler job func changed from bound method to `f"{__name__}:_execute_policy_callback"` string reference.
- **Residual:** Test still xfailed due to `PipelineRunRepository.create()` contract mismatch — separate issue tracked below.

### [SCHED-RUNREPO] — PipelineRunRepository.create() contract mismatch ✅ RESOLVED
- **Severity:** ~~Medium~~ → Resolved (2026-03-19)
- **Component:** api (`scheduling_adapters.py`), core (`scheduling_service.py`)
- **Discovered:** 2026-03-19 (MEU-90a xfail investigation)
- **Root cause:** Three contract mismatches: (1) `run_id` vs `id` key — service sends `run_id`, repo expects `id`; (2) missing `content_hash` in `trigger_run()` run_data; (3) response dicts returned ORM `id` but route schema expects `run_id`.
- **Fix:** Added key translation in `RunStoreAdapter.create()`, added `content_hash` to `SchedulingService.trigger_run()`, created `_run_model_to_dict()` to remap `id` → `run_id` in all adapter outputs. xfail removed.

### [STUB-RETIRE] — stubs.py contains legacy stubs that should be retired progressively
- **Severity:** Low (technical debt, no production impact)
- **Component:** api (`stubs.py`), tests
- **Discovered:** 2026-03-19 (MEU-90a stub cleanup pass)
- **Status:** Partially cleaned (4 dead scheduling stubs deleted); remainder tracked below

#### Phase 1 — Wireable now (proposed MEU-90b `service-wiring`)

| Stub | Real impl MEU | Blocker |
|------|---------------|---------|
| `StubUnitOfWork` + 7 `_InMemory*` repos | MEU-90a ✅ | Only `test_watchlist_service.py` uses it — convert to real in-memory SQLAlchemy UoW |
| `McpGuardService` | MEU-38 ✅ | Lifespan wiring (stateless, no DB) |
| `StubMarketDataService` | MEU-61 ✅ | Lifespan wiring (needs provider config) |
| `StubProviderConnectionService` | MEU-60 ✅ | Lifespan wiring |

#### Phase 2 — Blocked on future MEUs (remove per-service)

| Stub | Blocked on | Notes |
|------|-----------|-------|
| `StubAnalyticsService` (9 methods) | MEU-104 through MEU-116 (⬜) | Expectancy, SQN, drawdown, execution quality, etc. |
| `StubReviewService` (3 methods) | MEU-110 `ai-review-persona` (⬜) | AI review + mistake tracking |
| `StubTaxService` (12 methods) | MEU-123–126 (core engine), retire at MEU-148 `tax-api` | [04f §Service Wiring](../docs/build-plan/04f-api-tax.md) |

- **Fix:** Phase 1 via MEU-90b; Phase 2 naturally retires each stub when its real service is implemented.
- **Roadmap:** Full stub retirement roadmap with MEU assignments in [09a §Stub Retirement Roadmap](../docs/build-plan/09a-persistence-integration.md).

### [MCP-CONFIRM] — `create_trade` inputSchema missing `confirmation_token` field
- **Severity:** High
- **Component:** mcp-server
- **Discovered:** 2026-03-19 (live smoke test)
- **Status:** Fixed
- **Details:** The `create_trade` tool's Zod inputSchema in `trade-tools.ts` did not include `confirmation_token`. On static/annotation-unaware clients, the MCP SDK's Zod validation stripped the field before it reached `withConfirmation()` middleware, making trade creation impossible.
- **Fix:** Added `confirmation_token: z.string().optional()` to the inputSchema. Verified with 4 new TDD tests (AC-1 through AC-4) covering schema acceptance, body exclusion, static-mode round-trip, and dynamic-mode backward compatibility.

### [MCP-DIST-REBUILD] — MCP server runs from compiled `dist/`, not source `src/`
- **Severity:** High
- **Component:** mcp-server
- **Discovered:** 2026-03-19 (live smoke test)
- **Status:** Active — by design
- **Details:** The MCP server's `start` script runs `node dist/index.js`. After editing files in `mcp-server/src/`, the changes are invisible to the running MCP process until `dist/` is rebuilt and the IDE is restarted. This caused 2 unnecessary IDE restarts during the 2026-03-19 session when the `confirmation_token` schema fix was applied to source but `dist/` still had old code.
- **Workaround:** After any `mcp-server/src/` change: `cd mcp-server && npm run build` then restart the IDE to reload the MCP server process.

## Template

When adding issues, use this format:

```markdown
### [SHORT-TITLE] — Brief description
- **Severity:** Critical / High / Medium / Low
- **Component:** core / infrastructure / api / ui / mcp-server
- **Discovered:** YYYY-MM-DD
- **Status:** Open / In Progress / Workaround Applied
- **Details:** What happens, how to reproduce
- **Workaround:** (if any)
```
