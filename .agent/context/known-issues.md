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

#### Phase 1 — Wireable now (MEU-90a `persistence-wiring`)

| Stub | Real impl MEU | Blocker |
|------|---------------|---------|
| `StubUnitOfWork` + 7 `_InMemory*` repos | MEU-90a ✅ | Only `test_watchlist_service.py` uses it — convert to real in-memory SQLAlchemy UoW |
| `McpGuardService` | MEU-90a ✅ | Moved to `services/mcp_guard.py`; no longer in stubs |
| `StubMarketDataService` | MEU-61 ✅ | Lifespan wiring (needs provider config) |
| `StubProviderConnectionService` | MEU-60 ✅ | Lifespan wiring |

#### Phase 2 — Blocked on future MEUs (remove per-service)

| Stub | Blocked on | Notes |
|------|-----------|-------|
| `StubAnalyticsService` (9 methods) | MEU-104 through MEU-116 (⬜) | Expectancy, SQN, drawdown, execution quality, etc. |
| `StubReviewService` (3 methods) | MEU-110 `ai-review-persona` (⬜) | AI review + mistake tracking |
| `StubTaxService` (12 methods) | MEU-123–126 (core engine), retire at MEU-148 `tax-api` | [04f §Service Wiring](../docs/build-plan/04f-api-tax.md) |

- **Fix:** Phase 1 via MEU-90a (`persistence-wiring`); Phase 2 naturally retires each stub when its real service is implemented.
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
### [PLAN-NOSIZE] — TradePlan entity missing `position_size` / `shares` field
- **Severity:** Medium
- **Component:** core / api / mcp-server / ui
- **Discovered:** 2026-03-20
- **Status:** Open — deferred to future run
- **Details:** The `TradePlan` entity (`entities.py` L113-151) has no `position_size` or `shares` field. The Position Calculator computes shares on-the-fly but the result is never persisted on the plan. Users expect to see share count in the Trade Plan detail view. Adding this requires full-stack propagation: domain entity → SQLAlchemy model → Alembic migration → API schemas (`CreatePlanRequest`, `UpdatePlanRequest`, `PlanResponse`) → MCP trade-planning toolset → GUI form display. The calculator already has the formula (`calculate_position_size` in `zorivest_core.domain.calculator`).
- **Workaround:** Use the standalone Position Calculator modal (C2 copy-to-clipboard) to compute shares separately.

### [E2E-AXEELECTRON] — `@axe-core/playwright` AxeBuilder incompatible with Electron sandbox
- **Severity:** High
- **Component:** ui (E2E tests)
- **Discovered:** 2026-03-22 (MEU-65 Wave 6 E2E)
- **Status:** Workaround Applied
- **Details:** `AxeBuilder.analyze()` internally calls `browserContext.newPage()`, which Electron rejects with `Protocol error (Target.createTarget): Not supported`. Additionally, Electron's `sandbox: true` + `contextIsolation: true` blocks `page.addScriptTag({ content: inlineString })` (inline script injection). This means the standard `@axe-core/playwright` API is completely unusable in Electron E2E tests without a workaround.
- **Workaround:** Load axe-core via a `file://` URL — Electron's sandboxed renderer allows loading local filesystem assets. Use `pathToFileURL()` from Node.js `url` module (handles Windows paths correctly), then call `window.axe.run()` via `page.evaluate()`:
  ```typescript
  const axeUrl = pathToFileURL(resolve(__dirname, '../../node_modules/axe-core/axe.min.js')).href
  await page.addScriptTag({ url: axeUrl })
  const violations = await page.evaluate(async () => {
      const r = await (window as any).axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } })
      return r.violations.map((v: any) => ({ id: v.id, impact: v.impact }))
  })
  expect(violations).toEqual([])
  ```
- **Note:** `disableIsolation()` is documented in newer axe-core/playwright but was not available in the installed version — always verify method availability before using.

### [E2E-AXESILENT] — Accessibility scan failures are silent if the scanner itself crashes
- **Severity:** Medium (testing process risk)
- **Component:** ui (E2E tests)
- **Discovered:** 2026-03-22 (MEU-65 Wave 6 E2E)
- **Status:** Active — process awareness
- **Details:** When `AxeBuilder.analyze()` throws (e.g., Electron protocol error), the test fails at the scan call — not at `expect(violations).toEqual([])`. If violation logging logic is guarded by `if (violations.length > 0)`, it is never reached, making it appear as if no violations were found (the log file is not written). This caused several debugging sessions chasing heading-order and label violations when the real issue was the scanner never running.
- **Workaround:** When debugging axe failures in E2E, always check the error at the scan call itself (not just the assertion). Wrap the scan in a try/catch during debugging to distinguish "scanner failed" from "violations found". Prefer writing violation details via `test.info().attach()` rather than filesystem writes, as attach() works regardless of where in the test the failure occurs.

### [E2E-ELECTRONLAUNCH] — Playwright `Process failed to launch!` in headless/sandboxed environments
- **Severity:** High (verification blocker)
- **Component:** ui (E2E tests)
- **Discovered:** 2026-03-18 (first observed in Codex critical review)
- **Status:** Active — environment-specific
- **Details:** `npx playwright test` fails with `Process failed to launch!` before any test assertions execute. Electron requires a display server (X11/Wayland on Linux, native desktop on Windows/macOS). The Codex reviewer runs in a sandboxed cloud environment without a display server, causing 100% E2E failure rate across all test suites (launch, persistence, accounts, market-data, trade-entry, position-size). The same tests pass on the developer's local Windows desktop.
- **Affected suites:** `launch.test.ts`, `persistence.test.ts`, `account-crud.test.ts`, `trade-entry.test.ts`, `mode-gating.test.ts`, `settings-market-data.test.ts`, `position-size.test.ts`
- **Workaround:** E2E tests are verified locally by the implementation agent (Opus). The Codex reviewer validates unit/integration tests and code review only. CI pipeline will need `xvfb-run` or equivalent virtual framebuffer when E2E tests are added to GitHub Actions.
- **Resolution path:** Configure `xvfb-run npx playwright test` in CI, or use Electron's `--headless` flag once Playwright's Electron integration supports it.

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

---

### [DOC-STALESLUG] — `09a-persistence-integration.md` references stale MEU-90b slug
- **Severity:** Low
- **Component:** docs
- **Discovered:** 2026-03-22
- **Status:** ✅ **Resolved 2026-03-22 (MEU-90b `mode-gating-test-isolation`)**
- **Details:** `docs/build-plan/09a-persistence-integration.md` lines 81–82 referenced `MEU-90b service-wiring`. Fixed to `MEU-90a persistence-wiring` and updated `08-market-data.md` section heading.
