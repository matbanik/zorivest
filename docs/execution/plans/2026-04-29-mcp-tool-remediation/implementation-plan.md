---
project: "2026-04-29-mcp-tool-remediation"
date: "2026-04-29"
source: "docs/build-plan/05c-mcp-trade-analytics.md, 05a-mcp-zorivest-settings.md, 05-mcp-server.md, 05d-mcp-trade-planning.md"
meus: ["MEU-TA1", "MEU-TA2", "MEU-TA3", "MEU-TA4"]
status: "executed"
template_version: "2.0"
---

# Implementation Plan: MCP Tool Remediation (P2.5e)

> **Project**: `2026-04-29-mcp-tool-remediation`
> **Build Plan Section(s)**: P2.5e (BUILD_PLAN.md L405-418), Matrix Items 5.J–5.M
> **Status**: `executed`

---

## Goal

Resolve the four remaining `[MCP-TOOLAUDIT]` findings from the 2026-04-27 MCP tool audit:

1. **TA1**: `delete_trade` returns 500 on valid exec_id — missing error handling in API route
2. **TA2**: `update_settings` returns 422 with `[object Object]` — error detail serialization bug
3. **TA3**: 7 MCP tools with no backend return 404/500 — need 501 "Not Implemented" guards
4. **TA4**: No `list_trade_plans` or `delete_trade_plan` MCP tools — plan lifecycle incomplete

**Execution order**: TA1 → TA2 → TA4 → TA3, followed by a full `/mcp-audit`.

---

## Resolved Design Decisions

> [!NOTE]
> **TA3 tool count (Human-approved)**: The BUILD_PLAN description says "6 unimplemented" but the parenthetical lists 7 (3 accounts + 4 tax). User confirmed during planning session that all 7 tools listed in the spec parenthetical should be guarded. The `behavioral` toolset (3 more ghost tools) is **out of scope** — it was not cited in the audit finding.

---

## Proposed Changes

### MEU-TA1: Fix `delete_trade` 500 Error

**Root cause**: The API route `DELETE /trades/{exec_id}` (line 175-177 of `trades.py`) calls `service.delete_trade(exec_id)` with **no try/except**. The service layer calls `uow.trades.delete(exec_id)`, which silently succeeds even when the exec_id doesn't exist (repo `delete` at line 263-267 does `if m: session.delete(m)` — no-op on miss). The 500 comes from downstream errors (e.g. 204 response body parsing, or unhandled exceptions from cascading deletes of linked reports/images).

**Fix**: Add `NotFoundError` handling to the route (consistent with `update_trade` pattern at line 166-167), and raise `NotFoundError` from the service when exec_id doesn't exist (fail-fast instead of silent no-op).

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP `delete_trade` input | Zod `z.string()` | Non-empty exec_id | N/A (string param) |
| REST `DELETE /trades/{exec_id}` | FastAPI path param | str, URL-decoded | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-0 | `DELETE /trades/{exec_id}` succeeds for a valid trade with linked report/images (reproduces audit failure) | Spec (.agent/context/MCP/mcp-tool-audit-report.md §Issues #3) | — |
| AC-1 | `DELETE /trades/{exec_id}` returns 204 on valid exec_id | Spec (05c) | — |
| AC-2 | `DELETE /trades/{exec_id}` returns 404 on nonexistent exec_id | Local Canon (G15 error handling) | exec_id = "NONEXISTENT" |
| AC-3 | Service `delete_trade` raises `NotFoundError` when exec_id not found | Local Canon (trade_service pattern) | — |
| AC-4 | MCP `delete_trade` returns `{success: false, error: "404: ..."}` on nonexistent exec_id | Spec (M2 parity) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 204 on success | Spec | Already implemented (status_code=204) |
| 404 on not-found | Local Canon | Matches `update_trade` pattern |
| Service raises NotFoundError | Local Canon | Consistent with `get_trade` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/trade_service.py` | modify | Add not-found check before `delete`, raise `NotFoundError` |
| `packages/api/src/zorivest_api/routes/trades.py` | modify | Add `try/except NotFoundError → 404` to `delete_trade` route |
| `tests/unit/test_api_trades.py` | modify | Regression tests for AC-0 through AC-4 (added to existing trade API test file) |

---

### MEU-TA2: Fix `update_settings` Serialization Bug

**Root cause**: The MCP tool at `settings-tools.ts:85` correctly sends `JSON.stringify(params.settings)` to `PUT /settings`. The API route at `settings.py:119-137` accepts `body: dict[str, Any]` and calls `service.bulk_upsert(body)`. When validation fails, `SettingsValidationError` is raised and the route returns `HTTPException(422, detail={"errors": e.per_key_errors})`.

The bug is in how `fetchApi` handles the 422 response: at `api-client.ts:107-108`, `detail = parsed.detail ?? body` — but `parsed.detail` here is an **object** (`{"errors": {...}}`), not a string. When this object gets inserted into the error string at line 112 (`${res.status}: ${detail}`), JavaScript coerces it to `[object Object]`.

**Fix**: Stringify the error detail when it's not a string in `fetchApi`.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP `update_settings` input | Zod `z.record(z.string())` | Values must be strings | Zod validates |
| REST `PUT /settings` body | FastAPI `dict[str, Any]` | Validated by SettingsValidator | extra not applicable (dict) |
| Error response | HTTPException detail | `{"errors": {key: [messages]}}` | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-5 | `fetchApi` returns human-readable error string when API returns structured error detail | Local Canon (G15) | — |
| AC-6 | `fetchApi` correctly serializes structured 422 body (mocked response with object `detail`) | Spec (.agent/context/MCP/mcp-tool-audit-report.md §Issues #8) | Mock fetch → `{detail: {errors: {...}}}` |
| AC-7 | `fetchApi` still handles string error details correctly | Local Canon (regression safety) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Error serialization format | Local Canon | fetchApi must stringify non-string details |
| Settings validation returns structured errors | Spec (04d) | Already works — only MCP rendering broken |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/utils/api-client.ts` | modify | Stringify non-string `detail` values in error path |
| `mcp-server/tests/settings-tools.test.ts` | modify | Regression test for structured error detail serialization (added to existing settings test file) |

---

### MEU-TA4: Trade Plan Lifecycle MCP Tools

**Prerequisite context**: Backend REST endpoints already exist:
- `GET /api/v1/trade-plans` → `list_plans` (plans.py:160-171)
- `DELETE /api/v1/trade-plans/{plan_id}` → `delete_plan` (plans.py:254-267)

These are fully implemented in the API layer. The MCP server simply needs thin wiring tools.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP `list_trade_plans` input | Zod | limit (1-1000, default 100), offset (≥0, default 0), status filter (optional) | Zod validates |
| MCP `delete_trade_plan` input | Zod | plan_id: number (int), confirmation_token: optional in Zod schema but enforced by `withConfirmation()` middleware per M3 | Zod validates; destructive gate via `DESTRUCTIVE_TOOLS` registry |
| REST `GET /trade-plans` | FastAPI Query params | limit 1-1000, offset ≥0 | extra="forbid" on body |
| REST `DELETE /trade-plans/{plan_id}` | FastAPI path param | int | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-8 | `list_trade_plans` returns array of plans from `GET /trade-plans` | Spec (05d §plan-lifecycle) | — |
| AC-9 | `list_trade_plans` supports `limit` and `offset` pagination params | Spec (M2 parity) | — |
| AC-10 | `delete_trade_plan` sends `DELETE /trade-plans/{plan_id}` and returns 204 | Spec (05d) | — |
| AC-11 | `delete_trade_plan` requires confirmation gate (M3 destructive tool) | Local Canon (M3) | — |
| AC-12 | `delete_trade_plan` returns 404-class error on nonexistent plan_id | Local Canon (G15) | plan_id = 999999 |
| AC-13 | After `delete_trade_plan`, `create_trade_plan` for same ticker succeeds (409 unblocked) | Spec (.agent/context/MCP/mcp-tool-audit-report.md §Issues #9) | — |
| AC-14 | Both tools registered in `trade-planning` toolset seed | Spec (05d) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| list_trade_plans pagination | Spec | Mirrors REST endpoint query params |
| delete requires confirmation | Local Canon (M3) | Destructive tool pattern established |
| 404 on not-found | Local Canon (G15) | Consistent error handling |
| Toolset registration | Spec | trade-planning seed.ts |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/tools/planning-tools.ts` | modify | Add `list_trade_plans` and `delete_trade_plan` tool registrations |
| `mcp-server/src/toolsets/seed.ts` | modify | Add tools to `trade-planning` toolset definition |

---

### MEU-TA3: Unimplemented Tool Guards (501)

Guard 7 MCP tools whose backend endpoints don't exist with "501 Not Implemented" responses. These tools are defined in toolset seeds and have handlers registered, but their API calls fail because no backend route serves them.

**Accounts toolset** (3 tools — currently return 404 from missing API routes):
1. `list_bank_accounts` → `GET /banking/accounts` (no route)
2. `list_brokers` → `GET /brokers` (no route)
3. `resolve_identifiers` → `POST /identifiers/resolve` (no route)

**Tax toolset** (4 tools — currently have `register: () => []` so they appear in `describe_toolset` but aren't callable):
4. `estimate_tax`
5. `find_wash_sales`
6. `manage_lots`
7. `harvest_losses`

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| MCP 501 stub handlers (7 tools) | `Human-approved` exception: 501 stubs are exempt from MCP schema ownership because they return immediately without reading, validating, or processing any input parameters. No Zod schema is defined; no field constraints apply. | No validation (immediate 501 return) | Not applicable — input is neither read nor forwarded; extra fields have no effect |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-15 | `list_bank_accounts` returns `{success: false, error: "501: Not Implemented ..."}` | Spec (.agent/context/MCP/mcp-tool-audit-report.md §Issues #1) | — |
| AC-16 | `list_brokers` returns `{success: false, error: "501: Not Implemented ..."}` | Spec (.agent/context/MCP/mcp-tool-audit-report.md §Issues #2) | — |
| AC-17 | `resolve_identifiers` returns `{success: false, error: "501: Not Implemented ..."}` | Spec (.agent/context/MCP/mcp-tool-audit-report.md §Issues #11) | — |
| AC-18 | Tax toolset 4 tools (`estimate_tax`, `find_wash_sales`, `manage_lots`, `harvest_losses`) return 501 when called | Spec (.agent/context/MCP/mcp-tool-audit-report.md §Issues #12) | — |
| AC-19 | 501 responses include informative message: "This tool is planned but not yet implemented" | Local Canon | — |
| AC-20 | No behavioral toolset changes (out of scope per Issue #12 scope) | Spec | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 501 status pattern | Research-backed | HTTP 501 is the standard "Not Implemented" status |
| Guard wrapping pattern | Local Canon | Replaces existing live handlers with stub responses |
| Tax tool registration | Local Canon | Must add real handlers (stubs) since `register: () => []` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/tools/accounts-tools.ts` | modify | Replace 3 tool handlers with 501 stub responses |
| `mcp-server/src/toolsets/seed.ts` | modify | Wire tax toolset register function to actual stub handler |
| `mcp-server/src/tools/tax-tools.ts` | new | 501 stub handlers for 4 tax tools |

---

## Out of Scope

- **Behavioral toolset** (3 ghost tools) — not cited in audit finding
- **Tool consolidation** (74→12) — separate future project
- **get_market_news / get_sec_filings** — provider issues, not MCP bugs
- **list_provider_capabilities redundancy** — cosmetic, not functional
- **Backend implementation** of banking, broker, identifier, or tax endpoints — 501 stubs only

---

## BUILD_PLAN.md Audit

This project updates 4 MEU statuses in BUILD_PLAN.md (TA1-TA4 from ⬜ to ✅).

```powershell
rg "MEU-TA[1-4]" docs/BUILD_PLAN.md  # Expected: 4 matches (status rows)
```

---

## Verification Plan

### 1. Python Unit Tests (TA1)
```powershell
uv run pytest tests/unit/test_api_trades.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ta1.txt; Get-Content C:\Temp\zorivest\pytest-ta1.txt | Select-Object -Last 40
```

### 2. OpenAPI Drift Check (TA1 — route change)
```powershell
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt | Select-Object -Last 10
```

### 3. TypeScript Build (TA2, TA3, TA4)
```powershell
cd mcp-server && npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 20
```

### 4. Targeted Vitest (TA2, TA3, TA4)
```powershell
cd mcp-server && npx vitest run tests/settings-tools.test.ts *> C:\Temp\zorivest\vitest-ta2.txt; Get-Content C:\Temp\zorivest\vitest-ta2.txt | Select-Object -Last 20
cd mcp-server && npx vitest run tests/planning-tools.test.ts *> C:\Temp\zorivest\vitest-ta4.txt; Get-Content C:\Temp\zorivest\vitest-ta4.txt | Select-Object -Last 20
cd mcp-server && npx vitest run tests/accounts-tools.test.ts *> C:\Temp\zorivest\vitest-ta3.txt; Get-Content C:\Temp\zorivest\vitest-ta3.txt | Select-Object -Last 20
```

### 5. Full MCP Test Suite
```powershell
cd mcp-server && npx vitest run *> C:\Temp\zorivest\vitest-full.txt; Get-Content C:\Temp\zorivest\vitest-full.txt | Select-Object -Last 30
```

### 6. MCP Audit (post-implementation)
```
Invoke /mcp-audit workflow per .agent/skills/mcp-audit/SKILL.md
```

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Resolved Questions

> [!NOTE]
> **TA3 count discrepancy (Human-approved)**: BUILD_PLAN says "6" but lists 7 tools (3 accounts + 4 tax). User confirmed all 7 are in scope during planning session. The BUILD_PLAN description text is imprecise but the parenthetical enumeration (the normative list) is correct.

---

## Research References

- [MCP Tool Audit Report](../../.agent/context/MCP/mcp-tool-audit-report.md) — source of all findings
- [Emerging Standards](../../.agent/docs/emerging-standards.md) — M2, M3, G15 patterns
- [HTTP 501](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/501) — standard "Not Implemented" response
