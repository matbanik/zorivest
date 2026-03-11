# MEU-42: ToolsetRegistry + Adaptive Client Detection

> **Project slug:** `2026-03-10-toolset-registry`
> **MEU:** 42 (`toolset-registry`)
> **Build Plan sections:** §5.11, §5.12, §5.13, §5.14
> **Dependencies:** MEU-31–41 (all ✅ approved)
> **Phase-exit significance:** Last MEU in Phase 5 — completes MCP Server phase

---

## Goal

Wire the `ToolsetRegistry` (skeleton from MEU-41) into a full startup orchestration flow: parse `--toolsets` CLI, detect client mode, selectively register tools, and apply two adaptive patterns (D: server instructions, E: safety confirmation). Patterns A (response compression) and B (tiered descriptions) deferred to MEU-42b.

---

## Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| `--toolsets` CLI flag parsing | Spec | §5.11 L754-769 | ✅ |
| `toolset-config.json` reading | Spec | §5.11 L771-783 | ✅ |
| `detectClientMode()` | Spec | §5.12 L787-835 | ✅ |
| `ZORIVEST_CLIENT_MODE` env override | Spec | §5.12 L825, L835 | ✅ |
| `registerToolsForClient()` | Spec | §5.14 L893-933 | ✅ |
| Pattern A: response format | Spec | §5.13 L846-856 | Deferred to MEU-42b |
| Pattern B: tiered descriptions | Spec | §5.13 L858-865 | Deferred to MEU-42b |
| Pattern D: server instructions | Spec | §5.13 L867-875 | ✅ |
| Pattern E: confirmation adaptation | Spec | §5.13 L877-889 | ✅ |
| `withConfirmation()` middleware | Spec | §5.14 L958-964 | ✅ |
| Middleware composition order | Spec | §5.14 L958-960 | ✅ |
| Annotation-based registration | Spec | §5.14 L936-953 | ✅ (existing) |

One SDK-sourced research gate resolved inline (static-mode notification ordering — see Design Notes).

---

## Feature Intent Contract (FIC)

### Acceptance Criteria

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `parseToolsets()` returns tagged union `ToolsetSelection` (`all` / `explicit` / `defaults`); `core` and `discovery` always loaded regardless of selection | Spec §5.11 L754-769 |
| AC-2 | `toolset-config.json` read from `ZORIVEST_TOOLSET_CONFIG` env var path; `defaultToolsets` parsed; file is optional (graceful fallback to defaults if missing). **`clientOverrides` declared in interface but deferred to MEU-42b** — not parsed or consumed. | Spec §5.11 L771-783 |
| AC-3 | `detectClientMode(server)` uses clientInfo-name detection: `ZORIVEST_CLIENT_MODE` env var (priority 1); `clientInfo.name` pattern matching — `claude-*` → `anthropic`, `antigravity`/`cline`/`roo-code`/`gemini-cli` → `dynamic` (priority 2); all others including `cursor`/`windsurf`/unknown → `static` (priority 3, safe default per §5.12 L833). Capability-first detection deferred — SDK `ClientCapabilities` has no `tools` property (`spec.types.d.ts:283-356`) | Spec §5.12 L787-838 + SDK constraint |
| AC-4 | Pre-connect-all + post-connect-filter: `registerAllToolsets()` registers ALL toolsets pre-connect (triggers `registerCapabilities` once); `applyModeFilter()` disables unwanted toolsets post-connect in `oninitialized` callback; sets `dynamicLoadingEnabled` based on mode | Spec §5.14 L893-933 + SDK constraint |
| AC-5 | Session-level `responseFormat` flag (`'detailed' \| 'concise'`) set by detected mode; anthropic/dynamic → `'detailed'`, static → `'concise'` | Spec §5.13 L846-856 |
| AC-6 | `getResponseFormat()` exported for tool handlers to check | Spec §5.13 L856 |
| AC-7 | Server `instructions` set at McpServer construction with comprehensive mode-aware text covering all client types; per-mode specialization deferred (SDK has no post-connect setter — `server/index.js:279`) | Spec §5.13 L867-875 + SDK constraint |
| AC-8 | `withConfirmation()` middleware wraps destructive tools on annotation-unaware (static) clients; on annotation-aware (anthropic/dynamic) clients, skips confirmation | Spec §5.13 L877-889, §5.14 L964 |
| AC-9 | `index.ts` startup: seed registry → parse CLI → build McpServer with instructions → register ALL toolsets (pre-connect) → set `oninitialized` callback → connect transport → (in callback) detect mode + disable non-selected toolsets + set behavioral flags → bootstrap auth | Spec §5.14 + SDK constraint |
| AC-10 | `ToolsetRegistry.getDefaults()` filters on `isDefault === true` AND `loaded === false` | Spec §5.11 L747 |
| AC-11 | `BUILD_PLAN.md` Phase 5 completed count updated from `1` to `12` after MEU-42 completes; MEU-42 status → ✅ | Workflow (create-plan.md L128, L162) |

---

## Proposed Changes

### Client Detection Module

#### [NEW] [client-detection.ts](file:///p:/zorivest/mcp-server/src/client-detection.ts)

- Export `type ClientMode = 'anthropic' | 'dynamic' | 'static'`
- Export `detectClientMode(server: McpServer): ClientMode` — clientInfo-name detection (post-connect):
  1. Check `ZORIVEST_CLIENT_MODE` env var (priority 1 override); if set, return immediately
  2. Read `server.server.getClientVersion()?.name` (populated after MCP initialize handshake)
  3. Name matches `claude-*` → `'anthropic'`
  4. Name matches `antigravity`, `cline`, `roo-code`, or `gemini-cli` → `'dynamic'`
  5. All others including `cursor`, `windsurf`, unknown → `'static'` (safe default per §5.12 L833)
- Export `getResponseFormat(): 'detailed' | 'concise'` — returns format based on detected mode
- Export `getServerInstructions(): string` — returns comprehensive instructions covering all modes (constructor-time; not mode-specific due to SDK constraint — see Design Notes)
- `getClientCapabilities()` is NOT used for mode detection (SDK `ClientCapabilities` has no `tools` property — see Design Notes)

---

### Registration Orchestrator

#### [NEW] [registration.ts](file:///p:/zorivest/mcp-server/src/registration.ts)

- Export `registerAllToolsets(server: McpServer, registry: ToolsetRegistry): void` — pre-connect phase: iterates `registry.getAll()`, calls each toolset's `register(server)` callback, stores returned `RegisteredTool[]` handles in `registry.storeHandles(name, handles)`. Triggers SDK `registerCapabilities({tools:{listChanged:true}})` exactly once on first tool registration.
- Export `applyModeFilter(registry: ToolsetRegistry, mode: ClientMode, selection: ToolsetSelection): void` — post-connect phase (called inside `oninitialized` callback): for each non-selected toolset, calls `handle.disable()` on all stored handles; calls `registry.markLoaded(name)` for active toolsets only
- Branch on `selection.kind`: `'all'` → enable all; `'explicit'` → enable named + alwaysLoaded; `'defaults'` → enable defaults + alwaysLoaded; all others disabled
- Set `toolsetRegistry.dynamicLoadingEnabled` based on mode (`static` → false)
- MCP protocol guarantee: `initialized` notification fires before any `tools/list` request, so filtering completes before the client sees the tool list

---

### Confirmation Middleware

#### [NEW] [confirmation.ts](file:///p:/zorivest/mcp-server/src/middleware/confirmation.ts)

- Export `withConfirmation<T>(toolName, handler): handler` — wraps destructive tools with `confirmation_token` parameter check
- On static clients: requires valid `confirmation_token` from `get_confirmation_token` tool
- On dynamic/anthropic clients: passes through (IDE handles confirmation)
- Destructive tools list: `zorivest_emergency_stop`, `create_trade`, `sync_broker`, `disconnect_market_provider`, `zorivest_service_restart`

---

### CLI Parsing

#### [NEW] [cli.ts](file:///p:/zorivest/mcp-server/src/cli.ts)

- Export tagged union type:
  ```typescript
  type ToolsetSelection =
    | { kind: 'all' }                        // --toolsets all
    | { kind: 'explicit'; names: string[] }  // --toolsets trade-analytics,tax
    | { kind: 'defaults' };                  // no flag / no config
  ```
- Export `parseToolsets(): ToolsetSelection` — parse `--toolsets` from `process.argv`
- If `--toolsets all` → `{ kind: 'all' }`
- If `--toolsets trade-analytics,tax` → `{ kind: 'explicit', names: ['trade-analytics', 'tax'] }`
- If no `--toolsets`, check `ZORIVEST_TOOLSET_CONFIG` for config file; if no config → `{ kind: 'defaults' }`

---

### Registry Enhancement

#### [MODIFY] [registry.ts](file:///p:/zorivest/mcp-server/src/toolsets/registry.ts)

- Add `isDefault: boolean` to `ToolsetDefinition` interface
- **Change `register` return type:** `register: (server: McpServer) => RegisteredTool[]` (was `=> void`). Each concrete registration function must collect and return the `RegisteredTool` handles from its `server.registerTool()` calls.
- **Add `toolHandles` map:** `private toolHandles = new Map<string, RegisteredTool[]>()` — stores handles per toolset name
- **Add `storeHandles(name, handles)`:** stores returned handles from `register()` calls
- **Add `getHandles(name): RegisteredTool[]`:** retrieves stored handles for re-enable/disable operations
- Update `getDefaults()` to filter on `isDefault === true` AND `loaded === false` (only not-yet-active defaults)
- Add `getAllNames(): string[]` utility
- **Add `loaded` state semantics:** `loaded: false` = registered but disabled (or not yet filtered); `loaded: true` = registered AND enabled (active in session)

---

### Seed Data Update

#### [MODIFY] [seed.ts](file:///p:/zorivest/mcp-server/src/toolsets/seed.ts)

- **All toolsets start `loaded: false`** (runtime state, not metadata)
- **Add `discovery` toolset** to seeded definitions: `{ name: 'discovery', alwaysLoaded: true, isDefault: false, register: (server) => registerDiscoveryTools(server, toolsetRegistry) }` — resolves current exclusion (seed.ts L9-11 "Discovery is registered separately")
- Add `isDefault: true` to `trade-analytics` and `trade-planning` definitions
- Add `isDefault: false` to deferred toolsets (market-data, accounts, scheduling, tax, behavioral)
- Core: `alwaysLoaded: true, isDefault: false, loaded: false` → `loaded` flips to `true` only for active toolsets after `applyModeFilter()` runs
- **All `register` callbacks must return `RegisteredTool[]`** — each concrete `register*Tools()` function updated to collect and return the handles from its `server.registerTool()` calls

---

### Entry Point Refactor

#### [MODIFY] [index.ts](file:///p:/zorivest/mcp-server/src/index.ts)

- Import `parseToolsets` from cli.ts
- Import `detectClientMode`, `getServerInstructions` from client-detection.ts
- Import `registerAllToolsets`, `applyModeFilter` from registration.ts
- **Pre-connect-all + post-connect-filter** (SDK constraints: `registerCapabilities()` must precede `connect()`; `ClientCapabilities` has no tool detection fields):
  1. Seed registry: `seedRegistry(toolsetRegistry)` — populates all 9 toolset definitions (8 + discovery)
  2. Parse CLI: `const selection = parseToolsets()`
  3. Build McpServer with comprehensive instructions: `new McpServer(info, { instructions: getServerInstructions() })`
  4. **Pre-connect registration:** `registerAllToolsets(server, registry)` — registers ALL tools (all enabled), stores handles in `registry.toolHandles`, triggers `registerCapabilities` once
  5. Set `oninitialized` callback on `server.server`:
     ```typescript
     server.server.oninitialized = () => {
       const mode = detectClientMode(server);
       applyModeFilter(registry, mode, selection);
       setResponseFormat(mode);
       setConfirmationMode(mode);
     };
     ```
  6. Connect transport: `server.connect(transport)` — handshake begins
  7. (async, SDK-driven) Initialize handshake → `oninitialized` fires → mode detected, tools filtered
  8. Client calls `tools/list` → sees only enabled tools (MCP protocol guarantees ordering)
  9. Bootstrap auth
- Remove individual `register*Tools()` imports (handled by seed.ts `register` callbacks)

---

### BUILD_PLAN.md Update

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Fix Phase 5 completed count: `1` → `12` (line 465)
- Update MEU-42 status: `⬜` → `✅` (line 194)
- Update Phase 5 status: `🟡 In Progress` → `✅ Completed` with date (line 64)

---

## Task Table

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Scope project + write FIC | orchestrator | This plan document | `Select-String -Path docs/execution/plans/2026-03-10-toolset-registry/implementation-plan.md -Pattern "AC-"` returns 11 ACs | `[ ]` |
| 2 | Write TDD tests (Red phase) | coder | Test files: `cli.test.ts`, `client-detection.test.ts`, `registration.test.ts`, `confirmation.test.ts` | `cd mcp-server && npx vitest run --reporter=verbose` — all new tests FAIL | `[ ]` |
| 3 | Implement `cli.ts` | coder | `mcp-server/src/cli.ts` | `cd mcp-server && npx vitest run tests/cli.test.ts` | `[ ]` |
| 4 | Implement `client-detection.ts` | coder | `mcp-server/src/client-detection.ts` | `cd mcp-server && npx vitest run tests/client-detection.test.ts` | `[ ]` |
| 5 | Implement `confirmation.ts` | coder | `mcp-server/src/middleware/confirmation.ts` | `cd mcp-server && npx vitest run tests/confirmation.test.ts` | `[ ]` |
| 6 | Implement `registration.ts` | coder | `mcp-server/src/registration.ts` | `cd mcp-server && npx vitest run tests/registration.test.ts` | `[ ]` |
| 7 | Enhance `registry.ts` (handle map, `register` return type) + `seed.ts` (discovery + `isDefault`) | coder | Updated registry with `toolHandles`, `storeHandles`, `getHandles`; seed includes discovery; all `register` callbacks return `RegisteredTool[]` | `cd mcp-server && npx vitest run` (full suite green) | `[ ]` |
| 8 | Update `discovery-tools.ts` (`enable_toolset` re-enable path) | coder | `enable_toolset` uses `getHandles()` + `handle.enable()` instead of `ts.register(server)` | `cd mcp-server && npx vitest run tests/discovery-tools.test.ts` | `[ ]` |
| 9 | Refactor `index.ts` (pre-connect-all + oninitialized filter) | coder | Updated entry point | `cd mcp-server && npx vitest run && npx tsc --noEmit && npx eslint src/` | `[ ]` |
| 10 | Full quality gate | tester | Green build + lint + type check | `cd mcp-server && npm run build && npx tsc --noEmit && npx eslint src/ && npx vitest run` | `[ ]` |
| 11 | Validate + update `BUILD_PLAN.md` | coder | Phase 5 count + MEU-42 status | `Select-String -Path docs/BUILD_PLAN.md -Pattern "Phase 5\|MEU-42"` | `[ ]` |
| 12 | MEU gate | tester | Scoped validation | `uv run python tools/validate_codebase.py --scope meu` | `[ ]` |
| 13 | Create handoff + review | reviewer | Handoff file | `Test-Path .agent/context/handoffs/043-2026-03-10-toolset-registry-bp05s5.11+5.12+5.13+5.14.md` | `[ ]` |

---

## Verification Plan

### Automated Tests

All tests run from the MCP server directory:

```powershell
cd mcp-server
npx vitest run --reporter=verbose
```

Expected new test files:
- `tests/cli.test.ts` — CLI flag parsing (5+ tests)
- `tests/client-detection.test.ts` — mode detection (5+ tests)
- `tests/registration.test.ts` — orchestrated registration (5+ tests)
- `tests/confirmation.test.ts` — confirmation middleware (5+ tests)

Existing test suite must remain green (12 existing test files).

### Type Check

```powershell
cd mcp-server
npx tsc --noEmit
```

### MEU Gate

```powershell
uv run python tools/validate_codebase.py --scope meu
```

### BUILD_PLAN.md Validation

```powershell
# Verify Phase 5 count and status
Select-String -Path docs/BUILD_PLAN.md -Pattern "Phase 5"
Select-String -Path docs/BUILD_PLAN.md -Pattern "MEU-42"
```

---

## Handoff

- Path: `.agent/context/handoffs/043-2026-03-10-toolset-registry-bp05s5.11+5.12+5.13+5.14.md`
- Template: `.agent/context/handoffs/TEMPLATE.md`

---

## Design Notes

### Pre-Connect-All + Post-Connect-Filter (SDK Constraints)

SDK v1.26 has three hard constraints that shape startup:

1. **`Server.registerCapabilities()`** (`server/index.js:86-91`) throws `"Cannot register capabilities after connecting to transport"` if `this.transport` is set. The first `McpServer.tool()` / `registerTool()` call triggers `setToolRequestHandlers()` (`mcp.js:56-66`), which calls `registerCapabilities({tools:{listChanged:true}})`. The `_toolHandlersInitialized` flag ensures this only happens once.

2. **`Server._instructions`** (`server/index.js:50,279`) is set at constructor time and sent during `_oninitialize()`. No public setter exists.

3. **`ClientCapabilities`** (`spec.types.d.ts:283-356`) has NO `tools` property — only `experimental`, `roots`, `sampling`, `elicitation`, `tasks`. The build plan's `tools.deferLoading` and client-side `tools.listChanged` are **future spec features** not present in SDK v1.26. Zero matches for `deferLoading`/`defer_loading` across the entire installed SDK.

**Workaround — pre-connect-all + post-connect-filter:**
- **Pre-connect:** Seed registry, then register ALL toolsets (all enabled by default). This triggers `registerCapabilities()` exactly once before transport connect.
- **Set `oninitialized` callback:** The MCP protocol guarantees: `initialize` → `initialized` notification → subsequent requests. The `Server.oninitialized` callback (`server/index.d.ts:84`) fires when the client sends `initialized`, which is BEFORE any `tools/list` request.
- **In callback:** Detect mode from `clientInfo.name`, disable unwanted toolsets via `RegisteredTool.disable()`, set behavioral flags. The client's first `tools/list` response includes only enabled tools (`mcp.js:68-69`).
- **Static mode guarantee (SDK-sourced):** The guarantee does NOT depend on client behavior regarding `tools/list_changed` notifications. It is a **server-side ordering guarantee** based on the SDK's message processing model:
  1. `Protocol._onnotification()` (`shared/protocol.js:269-278`) dispatches handlers via `Promise.resolve().then(() => handler(notification))`.
  2. The `oninitialized` callback (`server/index.js:53`) runs synchronously within that handler: `() => this.oninitialized?.()`.
  3. All `RegisteredTool.disable()` calls within `oninitialized` execute synchronously, mutating the tool registry state before the handler promise resolves.
  4. JavaScript's single-threaded event loop ensures the next `onmessage` event (e.g., a `tools/list` request) cannot fire until the current notification handler's microtask chain completes.
  5. Therefore, any `tools/list` request processed after the `initialized` notification ALWAYS sees post-filter state, regardless of whether the client reacts to `tools/list_changed` notifications.
  - **Source basis:** SDK `shared/protocol.js:231-244` (message dispatch), `shared/protocol.js:269-278` (notification handling), `server/index.js:53` (oninitialized binding). Classification: `Research-backed` (primary source: installed SDK v1.26).
  - **Note:** The SDK DOES send `notifications/tools/list_changed` during `disable()` calls (`server/index.js:433-434`). This notification is benign: if a client re-requests `tools/list` in response, they receive the same already-filtered list. No client behavior assumption is required.

### Client Detection Strategy (clientInfo-Name)

Since `ClientCapabilities` lacks tool-related fields, detection falls back to `clientInfo.name` pattern matching via `Server.getClientVersion()` (`server/index.js:291-293`), with env var override:

1. **Priority 1 (override):** `ZORIVEST_CLIENT_MODE` env var — explicit override for testing/production
2. **Priority 2 (clientInfo):** `server.server.getClientVersion()?.name` — pattern match: `claude-*` → `anthropic`; `antigravity`/`cline`/`roo-code`/`gemini-cli` → `dynamic`
3. **Priority 3 (safe default):** All others including `cursor`, `windsurf`, unknown → `static` (per §5.12 L833)

> **Forward-compatibility:** When MCP spec adds `tools.deferLoading` or client-side `tools.listChanged` to `ClientCapabilities`, the detection function can be extended to check capabilities first (priority 1.5) without changing the startup flow.

### Server Instructions (AC-7 Constraint)

Since `_instructions` cannot be updated post-connect, we set comprehensive instructions at constructor time that cover all three modes. These instructions describe: available toolsets, how to discover/enable deferred toolsets via meta-tools, and the confirmation workflow for destructive operations. Per-mode instruction specialization is a future enhancement if SDK adds a setter.

### Loaded State Semantics

The `loaded` flag has one definition used consistently across the plan:
- **`loaded: false`** = registered but not yet enabled (disabled, or not yet filtered by `applyModeFilter`)
- **`loaded: true`** = registered AND enabled (active in session — tools visible in `tools/list`)

Seed data always initializes `loaded: false`. Only `applyModeFilter()` and `enable_toolset` flip `loaded` to `true` via `registry.markLoaded()`. The flags `alwaysLoaded` and `isDefault` are **metadata** (what should be loaded at startup), not runtime state.

### Middleware Composition

Per §5.14 L958-960, the composition order is:
```
Tool call → withMetrics() → withGuard() → withConfirmation() → handler
```

`withConfirmation()` is only active on static clients. On dynamic/anthropic clients, it's a pass-through.

### Patterns C and F

Explicitly deferred per §5.13 L844:
- **Pattern C** (composite tools): Session 5
- **Pattern F** (PTC routing): Session 6

These are out-of-scope for MEU-42.
