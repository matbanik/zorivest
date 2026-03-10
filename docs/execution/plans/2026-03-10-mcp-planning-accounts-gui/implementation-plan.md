# MCP Planning, Accounts & GUI Launch

> Project: `mcp-planning-accounts-gui` | MEU-36, MEU-37, MEU-40
> Date: 2026-03-10

## Goal

Implement the three remaining Phase 5 MCP tool modules:
1. **MEU-36** — Trade planning MCP tool (`create_trade_plan`)
2. **MEU-37** — Account MCP tools (8 tools including broker sync, CSV/PDF/bank import, identifier resolution, review checklist)
3. **MEU-40** — GUI launch MCP tool (`zorivest_launch_gui` with 4-method discovery + cross-platform process detachment)

These complete the MCP tool surface except for MEU-42 (ToolsetRegistry), which depends on this project.

---

## Spec Sufficiency

### MEU-36 — Trade Planning

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| `create_trade_plan` input schema | Spec | [05d L57-84](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) | ✅ | ticker, direction, conviction, strategy_name, entry, stop, target, conditions, timeframe, account_id |
| Annotations (readOnly=false, destructive=false, idempotent=false) | Spec | [05d L87-93](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) | ✅ | |
| REST endpoint `POST /api/v1/trade-plans` | Spec | [05d L99](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) | ✅ | Endpoint not yet implemented — thin proxy pattern, tested with mocked fetch |
| Toolset/meta: trade-planning, alwaysLoaded=false | Spec | [05d L41-42](file:///p:/zorivest/docs/build-plan/05d-mcp-trade-planning.md) | ✅ | |
| `calculate_position_size` already implemented | Local Canon | [calculator-tools.ts](file:///p:/zorivest/mcp-server/src/tools/calculator-tools.ts) | ✅ | Skip — already complete |

### MEU-37 — Accounts

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| 7 thin-proxy tools (sync_broker, list_brokers, resolve_identifiers, import_bank_statement, import_broker_csv, import_broker_pdf, list_bank_accounts) | Spec | [05f L7-213](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | ✅ | All use fetchApi/uploadFile pattern |
| `get_account_review_checklist` — client-side aggregation logic | Spec | [05f L216-306](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | ✅ | Fetches from 2 endpoints, filters by scope/staleness |
| `uploadFile` shared helper | Spec | [05f L310-329](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | ✅ | FormData + multipart for 3 import tools |
| All annotations per tool | Spec | [05f](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | ✅ | Each tool has explicit annotation block |
| Toolset/meta: accounts, alwaysLoaded=false | Spec | [05f](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md) | ✅ | All 8 tools |
| REST endpoints not yet implemented | Local Canon | grep: no `/brokers`, `/banking`, `/import`, `/identifiers` routes in API | ✅ | Thin proxy + mocked tests |
| `resolve_identifiers` request shape: 05f vs 04b bridging | Spec + Local Canon | [05f L61-76](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md), [04b L158-165](file:///p:/zorivest/docs/build-plan/04b-api-accounts.md) | ✅ | Spec: MCP tool follows 05f structured `{id_type, id_value}`. Local Canon: 04b expects wrapped `{"identifiers": [...]}` object via `body.get("identifiers", [])` — handler bridges with `JSON.stringify({ identifiers })`. |

### MEU-40 — GUI Launch

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| `zorivest_launch_gui` tool spec | Spec | [05b L109-144](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | ✅ | Canonical spec with input/output/annotations |
| Input: `wait_for_close` (bool, default false) | Spec | [05b L120-122](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | ✅ | |
| Output: `gui_found`, `method`, `message`, optional `setup_instructions` | Spec | [05b L142](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | ✅ | |
| Annotations: readOnlyHint=false, destructive=false, idempotent=false | Spec | [05b L135-139](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | ✅ | |
| 4 discovery methods (packaged, dev, PATH, env var) | Spec | [05 §5.8 L302-309](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | ✅ | |
| Cross-platform spawn (Windows `start`, macOS `open`, Linux `setsid`) | Spec | [05 §5.8 L316-321](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | ✅ | |
| Not-found behavior: opens releases page in browser | Spec | [05b L118-127](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | ✅ | Opens `https://github.com/zorivest/zorivest/releases` |
| Unguarded — always callable | Spec | [05 §5.8 L299-301](file:///p:/zorivest/docs/build-plan/05-mcp-server.md) | ✅ | Same pattern as zorivest_diagnose |
| Toolset/meta: core, alwaysLoaded=true | Spec | [05b L138-139](file:///p:/zorivest/docs/build-plan/05b-mcp-zorivest-diagnostics.md) | ✅ | |

---

## Proposed Changes

### MEU-36: Trade Planning Tool

#### [NEW] [planning-tools.ts](file:///p:/zorivest/mcp-server/src/tools/planning-tools.ts)

Register `create_trade_plan` MCP tool:
- Input schema from spec: ticker, direction, conviction, strategy_name, entry, stop, target, conditions, timeframe, account_id
- Annotations: readOnly=false, destructive=false, idempotent=false
- `_meta`: toolset=trade-planning, alwaysLoaded=false
- Handler: POST to `/trade-plans` via `fetchApi()`
- Middleware: `withMetrics` wrapping `withGuard`

#### [NEW] [planning-tools.test.ts](file:///p:/zorivest/mcp-server/tests/planning-tools.test.ts)

- `create_trade_plan` calls `POST /trade-plans` with correct payload
- Returns error envelope on API failure
- Validates required fields forwarding

---

### MEU-37: Account Tools

#### [NEW] [accounts-tools.ts](file:///p:/zorivest/mcp-server/src/tools/accounts-tools.ts)

Register 8 account MCP tools:
1. `sync_broker` — POST `/brokers/{broker_id}/sync`
2. `list_brokers` — GET `/brokers`
3. `resolve_identifiers` — POST `/identifiers/resolve`. MCP input is structured `{id_type, id_value}` objects per 05f. Handler sends `headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifiers })` to bridge 05f structured input to 04b’s `body.get("identifiers", [])` REST contract (see note below)
4. `import_bank_statement` — multipart POST `/banking/import` (via uploadFile helper)
5. `import_broker_csv` — multipart POST `/import/csv`
6. `import_broker_pdf` — multipart POST `/import/pdf`
7. `list_bank_accounts` — GET `/banking/accounts`
8. `get_account_review_checklist` — aggregation handler (fetches brokers + banks, filters by scope/staleness)

Includes `uploadFile` shared helper for multipart form uploads.

> **Spec + Local Canon decision — `resolve_identifiers` request shape:**
> 05f (MCP spec) defines structured `{id_type, id_value}` objects as input and shows handler calling `fetchApi('/identifiers/resolve', { method: 'POST', body: identifiers })` (L76).
> 04b (REST spec) defines the endpoint as `body.get("identifiers", [])` (L165), expecting a wrapped `{"identifiers": [...]}` JSON object.
> **Resolution:** The MCP handler sends `headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifiers })`, matching the existing JSON POST pattern used by `create_trade` (trade-tools.ts:103-106) and `update_setting` (settings-tools.ts:80-83). This bridges 05f input to 04b’s REST contract.

#### [NEW] [accounts-tools.test.ts](file:///p:/zorivest/mcp-server/tests/accounts-tools.test.ts)

- Tests for each of the 8 tools
- Upload helper tested with mock FormData
- `get_account_review_checklist` aggregation logic tested with scope variants

---

### MEU-40: GUI Launch Tool

#### [NEW] [gui-tools.ts](file:///p:/zorivest/mcp-server/src/tools/gui-tools.ts)

Register `zorivest_launch_gui` MCP tool:
- Input: `wait_for_close: z.boolean().default(false)`
- `discoverGui()` — tries 4 methods in order (packaged app, dev mode, PATH lookup, env var)
- Cross-platform spawn via `child_process.exec` with OS-specific commands
- Not-found behavior: opens releases page (`https://github.com/zorivest/zorivest/releases`) in default browser + returns `setup_instructions`
- Unguarded — no `withGuard` wrapper (like `zorivest_diagnose`)
- Wrapped with `withMetrics` only
- `_meta`: toolset=core, alwaysLoaded=true
- Returns: `{ gui_found: bool, method: string, message: string, setup_instructions?: string }`

#### [NEW] [gui-tools.test.ts](file:///p:/zorivest/mcp-server/tests/gui-tools.test.ts)

- Returns `gui_found: false` + setup_instructions + opens releases page when GUI not found
- Returns `gui_found: true` + method when found via installed path
- Returns `gui_found: true` + `dev-mode` method when dev repo detected
- Mock `fs.existsSync`, `child_process.exec`

---

### Integration Updates

#### [MODIFY] [index.ts](file:///p:/zorivest/mcp-server/src/index.ts)

- Import and call `registerPlanningTools` and `registerGuiTools`
- `registerGuiTools` goes with the unguarded group (like diagnostics)
- `registerPlanningTools` goes with guarded tools
- **Remove `registerCalculatorTools` from startup** — calculator tools migrate to `trade-planning` toolset
- **Do NOT register accounts tools at startup** — accounts is a deferred toolset, registered on-demand via `enable_toolset`

#### [MODIFY] [seed.ts](file:///p:/zorivest/mcp-server/src/toolsets/seed.ts)

- **Migrate `calculate_position_size` out of `core` toolset** — remove from `core.tools` list and `core.register()` callback. It belongs in `trade-planning` per §5.11 L740
- **Align `trade-planning` tool inventory** to canonical §5.11 L740 (3-tool set): `calculate_position_size`, `create_trade_plan`, `create_trade` (cross-tagged from 05c). Remove stale `list_trade_plans`, `get_trade_plan`
- **Align `accounts` tool inventory** to canonical 05f spec: `sync_broker`, `list_brokers`, `resolve_identifiers`, `import_bank_statement`, `import_broker_csv`, `import_broker_pdf`, `list_bank_accounts`, `get_account_review_checklist` (replace stale `list_accounts`, `create_account`, `import_csv`, `sync_broker`)
- Update `trade-planning` `register()` callback to call `registerPlanningTools` + `registerCalculatorTools` + `registerCreateTradeTool`
- **`registerCreateTradeTool(server)`**: new exported function extracted from trade-tools.ts that registers only `create_trade`. Uses a **server-scoped** idempotent guard via `WeakSet<McpServer>` at module scope. This is safe for multi-server test environments (each fresh `McpServer` instance gets its own registration state, and `WeakSet` allows GC of old instances). `registerTradeTools` also calls `registerCreateTradeTool` internally so the guard is always used regardless of which toolset loads first.
- Update `accounts` `register()` callback to call `registerAccountsTools`
- `accounts` stays `loaded: false` (deferred toolset — §5.11 marks it as "⬜ Deferred")
- Add `zorivest_launch_gui` to `core` toolset tool list
- `trade-planning` stays `loaded: true` (default-loaded — §5.11 L740 marks it as "✅ Default")

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Update MEU-36, MEU-37, MEU-40 status from ⬜ to ✅
- Fix Phase 5 summary completed count

---

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 1 | Write FIC for MEU-36 | coder | FIC in plan | `rg 'create_trade_plan' docs/execution/plans/2026-03-10-mcp-planning-accounts-gui/implementation-plan.md` | ⬜ |
| 2 | Write tests for planning-tools (RED) | coder | planning-tools.test.ts | `cd mcp-server && npx vitest run tests/planning-tools.test.ts` | ⬜ |
| 3 | Implement planning-tools.ts (GREEN) | coder | planning-tools.ts | `cd mcp-server && npx vitest run tests/planning-tools.test.ts` | ⬜ |
| 4 | Write FIC for MEU-37 | coder | FIC in plan | `rg 'sync_broker' docs/execution/plans/2026-03-10-mcp-planning-accounts-gui/implementation-plan.md` | ⬜ |
| 5 | Write tests for accounts-tools (RED) | coder | accounts-tools.test.ts | `cd mcp-server && npx vitest run tests/accounts-tools.test.ts` | ⬜ |
| 6 | Implement accounts-tools.ts (GREEN) | coder | accounts-tools.ts | `cd mcp-server && npx vitest run tests/accounts-tools.test.ts` | ⬜ |
| 7 | Write FIC for MEU-40 | coder | FIC in plan | `rg 'launch_gui' docs/execution/plans/2026-03-10-mcp-planning-accounts-gui/implementation-plan.md` | ⬜ |
| 8 | Write tests for gui-tools (RED) | coder | gui-tools.test.ts | `cd mcp-server && npx vitest run tests/gui-tools.test.ts` | ⬜ |
| 9 | Implement gui-tools.ts (GREEN) | coder | gui-tools.ts | `cd mcp-server && npx vitest run tests/gui-tools.test.ts` | ⬜ |
| 10 | Update index.ts + seed.ts (migrate calculator) | coder | Modified files | `cd mcp-server && npx tsc --noEmit && npx vitest run` | ⬜ |
| 11 | Update BUILD_PLAN.md | coder | Updated hub | `rg "MEU-36" docs/BUILD_PLAN.md && rg "MEU-37" docs/BUILD_PLAN.md && rg "MEU-40" docs/BUILD_PLAN.md` | ⬜ |
| 12 | Run MEU gate | tester | Gate results | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 12a | TypeScript blocking checks | tester | Gate results | `cd mcp-server && npx tsc --noEmit && npx eslint src/ tests/ && npx vitest run && npm run build` | ⬜ |
| 13 | Python regression | tester | No regressions | `uv run pytest tests/ -v` | ⬜ |
| 14 | Create handoffs (040, 041, 042) | coder | 3 handoff files | `if (!(Test-Path .agent/context/handoffs/040-2026-03-10-planning-tools-bp05ds5d.md)) { throw 'missing 040' }; if (!(Test-Path .agent/context/handoffs/041-2026-03-10-accounts-tools-bp05fs5f.md)) { throw 'missing 041' }; if (!(Test-Path .agent/context/handoffs/042-2026-03-10-gui-tools-bp05s5.10.md)) { throw 'missing 042' }` | ⬜ |
| 15 | Update MEU registry | coder | meu-registry.md | `rg "MEU-36" .agent/context/meu-registry.md && rg "MEU-37" .agent/context/meu-registry.md && rg "MEU-40" .agent/context/meu-registry.md` | ⬜ |
| 16 | Review + verify corrections | reviewer | Updated review handoff | `rg "verdict" .agent/context/handoffs/2026-03-10-mcp-planning-accounts-gui-plan-critical-review.md` | ⬜ |
| 17 | Create reflection (from TEMPLATE.md) | coder | `docs/execution/reflections/2026-03-10-mcp-planning-accounts-gui-reflection.md` | `if (!(Test-Path docs/execution/reflections/2026-03-10-mcp-planning-accounts-gui-reflection.md)) { throw 'missing reflection' }` | ⬜ |
| 18 | Update metrics.md | coder | metrics row | `cd mcp-server; npx vitest run 2>&1; cd ..; rg "test" docs/execution/metrics.md` | ⬜ |
| 19 | Prepare commit messages | coder | In handoff | `rg "commit" .agent/context/handoffs/040-2026-03-10-planning-tools-bp05ds5d.md` | ⬜ |

---

## Feature Intent Contracts

### MEU-36 FIC — `create_trade_plan`

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | Tool registers with name `create_trade_plan` and full input schema (ticker, direction, conviction, strategy_name, strategy_description, entry, stop, target, conditions, timeframe, account_id) | Spec: 05d L57-84 |
| AC-2 | Annotations: readOnlyHint=false, destructiveHint=false, idempotentHint=false, openWorldHint=false | Spec: 05d L87-93 |
| AC-3 | `_meta`: toolset=trade-planning, alwaysLoaded=false | Spec: 05d L41-42 |
| AC-4 | Handler POSTs to `/trade-plans` with full body and returns JSON text content | Spec: 05d L76-83 |
| AC-5 | Returns error envelope on API failure (non-2xx) | Local Canon: fetchApi pattern in api-client.ts |
| AC-6 | Wrapped with `withMetrics` + `withGuard` (guarded tool) | Spec: 05 §5.9 middleware composition |

### MEU-37 FIC — Account Tools

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `sync_broker` POSTs to `/brokers/{broker_id}/sync` with broker_id param | Spec: 05f L12-17 |
| AC-2 | `list_brokers` GETs `/brokers` with no params | Spec: 05f L39-44 |
| AC-3 | `resolve_identifiers` POSTs to `/identifiers/resolve` with `headers: { "Content-Type": "application/json" }, body: JSON.stringify({ identifiers })` wrapping 05f structured `{id_type, id_value}` objects to match 04b’s `body.get("identifiers", [])` contract. | Spec: 05f L61-76 + Local Canon: 04b L158-165 |
| AC-4 | `import_bank_statement` uploads multipart to `/banking/import` with file_path, account_id, format_hint | Spec: 05f L99-109 |
| AC-5 | `import_broker_csv` uploads multipart to `/import/csv` with file_path, account_id, broker_hint | Spec: 05f L131-141 |
| AC-6 | `import_broker_pdf` uploads multipart to `/import/pdf` with file_path, account_id | Spec: 05f L163-172 |
| AC-7 | `list_bank_accounts` GETs `/banking/accounts` with no params | Spec: 05f L194-199 |
| AC-8 | `get_account_review_checklist` aggregates brokers + banks data, filters by scope and stale_threshold_days, returns structured review | Spec: 05f L234-292 |
| AC-9 | All tools have correct annotations per spec | Spec: 05f |
| AC-10 | All tools have `_meta: { toolset: "accounts", alwaysLoaded: false }` | Spec: 05f |
| AC-11 | `uploadFile` helper constructs FormData with file blob and additional fields | Spec: 05f L312-329 |
| AC-12 | All guarded tools wrapped with `withMetrics` + `withGuard` | Spec: 05 §5.9 |

### MEU-40 FIC — GUI Launch

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `zorivest_launch_gui` registered with canonical name and description from spec | Spec: 05b L116-118 |
| AC-2 | Input: `wait_for_close: z.boolean().default(false)` | Spec: 05b L120-122 |
| AC-3 | Output: JSON with `gui_found` (bool), `method` (string), `message` (string), optional `setup_instructions` (string) | Spec: 05b L142 |
| AC-4 | `discoverGui()` tries 4 methods in order: packaged app, dev mode, PATH, env var | Spec: 05 §5.8 L302-309 |
| AC-5 | Windows uses `start ""` for detached spawn | Spec: 05 §5.8 L318 |
| AC-6 | macOS uses `open -a` or `nohup & ` | Spec: 05 §5.8 L319 |
| AC-7 | Linux uses `setsid` | Spec: 05 §5.8 L320 |
| AC-8 | When GUI not found: opens `https://github.com/zorivest/zorivest/releases` in default browser + returns `setup_instructions` | Spec: 05b L118-127, 05 §5.8 |
| AC-9 | Not guarded — always callable even when guard is locked | Spec: 05 §5.8 L299-301 |
| AC-10 | Annotations: readOnlyHint=false, destructiveHint=false, idempotentHint=false | Spec: 05b L135-137 |
| AC-11 | `_meta`: toolset=core, alwaysLoaded=true | Spec: 05b L138-139 |
| AC-12 | Wrapped with `withMetrics` only (no withGuard) | Spec: 05 §5.9 middleware composition |

---

## Verification Plan

### Automated Tests

```bash
# MEU gate (AGENTS.md L78)
uv run python tools/validate_codebase.py --scope meu

# TypeScript blocking checks (AGENTS.md L83)
cd mcp-server && npx tsc --noEmit && npx eslint src/ tests/ && npx vitest run && npm run build

# Python regression (from repo root)
uv run pytest tests/ -v
```

### Handoff Naming

| SEQ | File | Build-plan ref |
|-----|------|---------------|
| 040 | `040-2026-03-10-planning-tools-bp05ds5d.md` | 05d §trade-planning |
| 041 | `041-2026-03-10-accounts-tools-bp05fs5f.md` | 05f §accounts |
| 042 | `042-2026-03-10-gui-tools-bp05s5.10.md` | 05 §5.10 |
