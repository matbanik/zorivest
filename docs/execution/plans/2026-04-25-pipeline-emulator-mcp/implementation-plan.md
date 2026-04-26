---
project: "2026-04-25-pipeline-emulator-mcp"
date: "2026-04-25"
source: "docs/build-plan/09f-policy-emulator.md, docs/build-plan/05g-mcp-scheduling.md, docs/build-plan/09e-template-database.md"
meus: ["MEU-PH8", "MEU-PH9", "MEU-PH10"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Pipeline Emulator + MCP + Default Template

> **Project**: `2026-04-25-pipeline-emulator-mcp`
> **Build Plan Section(s)**: [09f](../../build-plan/09f-policy-emulator.md), [05g](../../build-plan/05g-mcp-scheduling.md), [09e §9E.6](../../build-plan/09e-template-database.md)
> **Status**: `draft`

---

## Goal

Complete P2.5c Pipeline Security Hardening (10/10 MEUs) by implementing the capstone trio:

1. **MEU-PH8** — 4-phase policy emulator (`PARSE→VALIDATE→SIMULATE→RENDER`) with output containment, session budget, and structured error schema
2. **MEU-PH9** — 11 new MCP tools + 4 new MCP resources (TypeScript) + backing REST API endpoints for emulator, schema discovery, template CRUD, and provider discovery
3. **MEU-PH10** — Morning Check-In default template seed (Alembic migration)

All dependencies satisfied: MEU-PH1–PH7 ✅.

---

## User Review Required

> [!IMPORTANT]
> 1. **PH9 crosses Python→TypeScript boundary.** MCP tools are REST proxies — complexity is in the Python backend routes.
> 2. **PH10 Alembic migration** creates a seed row in `email_templates`. This is a data migration — safe for existing DBs (additive only).
> 3. **No new Python dependencies** — `sqlglot`, `nh3`, `markdown-it-py` were added in PH2/PH6.

---

## Proposed Changes

### MEU-PH8: Policy Emulator

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 4-phase emulator (PARSE→VALIDATE→SIMULATE→RENDER) | Spec | [09f §9F.1b](../../build-plan/09f-policy-emulator.md) |
| Output containment: SHA-256 hash for RENDER | Spec | [09f §9F.2a](../../build-plan/09f-policy-emulator.md) |
| Per-call MCP response cap: 4 KiB | Spec | [09f §9F.2a](../../build-plan/09f-policy-emulator.md) |
| Cumulative session budget: 64 KiB per policy-hash | Spec | [09f §9F.2b](../../build-plan/09f-policy-emulator.md) |
| Rate limit: 10 calls/min per policy-hash | Spec | [09f §9F.2b](../../build-plan/09f-policy-emulator.md) |
| Structured error schema: `EmulatorError` + `EmulatorResult` | Spec | [09f §9F.3](../../build-plan/09f-policy-emulator.md) |
| Error type registry (9 error types) | Spec | [09f §9F.3b](../../build-plan/09f-policy-emulator.md) |
| `_source_type` metadata on step outputs | Spec | [09f §9F.4](../../build-plan/09f-policy-emulator.md) |
| Phase subset execution (run individual phases) | Spec | [09f §9F.1b](../../build-plan/09f-policy-emulator.md) |
| Early stop on parse error | Spec | [09f §9F.1b](../../build-plan/09f-policy-emulator.md) |
| VALIDATE: SQL AST allowlist via SqlSandbox | Local Canon | [09c §9C.2](../../build-plan/09c-pipeline-security-hardening.md) |
| VALIDATE: template existence via EmailTemplatePort | Local Canon | [09e §9E.1e](../../build-plan/09e-template-database.md) |
| VALIDATE: ref integrity check (step references) | Local Canon | [09f §9F.1b](../../build-plan/09f-policy-emulator.md) |
| SIMULATE: mock data injection per step type | Spec | [09f §9F.1b](../../build-plan/09f-policy-emulator.md) |
| RENDER: inline template compilation via HardenedSandbox | Local Canon | [09e §9E.3](../../build-plan/09e-template-database.md) |
| PolicyEmulator constructor takes SqlSandbox, HardenedSandbox, EmailTemplatePort | Spec | [09f §9F.1b](../../build-plan/09f-policy-emulator.md) |
| Mock output anonymization | Spec | [09f §9F.2a](../../build-plan/09f-policy-emulator.md) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | Valid policy JSON passes PARSE phase | Spec | N/A |
| AC-2 | Invalid policy JSON returns `EmulatorError(phase="PARSE", error_type="SCHEMA_INVALID")` | Spec | Malformed JSON, missing required fields |
| AC-3 | Broken step reference returns `REF_UNRESOLVED` error | Spec | `source_step_id` pointing to non-existent step |
| AC-4 | SQL with INSERT/UPDATE/DELETE returns `SQL_BLOCKED` | Local Canon | Write-SQL in query step params |
| AC-5 | Missing template returns `TEMPLATE_MISSING` | Spec | `body_template: "nonexistent"` |
| AC-6 | Existing template passes validation | Spec | N/A |
| AC-7 | SIMULATE populates mock outputs for all steps | Spec | N/A |
| AC-8 | RENDER returns SHA-256 hash, never raw content | Spec | Verify return type is hex digest, not HTML |
| AC-9 | Inline template compiles with simulated data | Spec | N/A |
| AC-10 | Phase subset execution works (e.g., PARSE only) | Spec | N/A |
| AC-11 | Parse failure prevents VALIDATE/SIMULATE/RENDER | Spec | Invalid schema → only PARSE error returned |
| AC-12 | SessionBudget tracks cumulative bytes per policy hash | Spec | N/A |
| AC-13 | >64 KiB cumulative raises `SecurityError` | Spec | Exceed byte budget |
| AC-14 | >10 calls/min per policy hash raises `SecurityError` | Spec | Rapid-fire calls |
| AC-15 | Different policy hashes have independent budgets | Spec | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/policy_emulator.py` | new | 4-phase emulator engine |
| `packages/core/src/zorivest_core/services/emulator_budget.py` | new | SessionBudget with rate limiting + byte budget |
| `packages/core/src/zorivest_core/domain/emulator_models.py` | new | `EmulatorError` + `EmulatorResult` Pydantic models |
| `tests/unit/test_policy_emulator.py` | new | 11 emulator tests |
| `tests/unit/test_emulator_budget.py` | new | 4 budget tests |

---

### MEU-PH9: Emulator MCP Tools + REST Endpoints

#### Boundary Inventory

**MCP Tool Inputs (12 tools):**

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `emulate_policy` | Zod: `policy_json: z.record(z.unknown())`, `phases: z.array(z.enum([...]))` | phases enum: PARSE, VALIDATE, SIMULATE, RENDER | `.strict()` on wrapper |
| `validate_sql` | Zod: `sql: z.string().min(1).max(10000)` | 1–10000 chars | `.strict()` |
| `create_email_template` | Zod schema mirroring Pydantic `EmailTemplateCreateRequest` | `name` regex `^[a-z0-9][a-z0-9_-]*$` 1–128, `body_html` 1–65536, `body_format` enum html/markdown | `.strict()` |
| `update_email_template` | Zod schema mirroring Pydantic `EmailTemplateUpdateRequest` | Same constraints as create, all optional except `name` (path key) | `.strict()` |
| `get_email_template` | Zod: `name: z.string().min(1).max(128)` | Template name | `.strict()` |
| `list_email_templates` | No input parameters | N/A | N/A (read-only, no schema) |
| `preview_email_template` | Zod: `name: z.string().min(1).max(128)`, optional `data: z.record(z.unknown())` | name required, data overrides sample_data_json | `.strict()` |
| `get_db_row_samples` | Zod: `table_name: z.string().min(1)`, `limit: z.number().min(1).max(20).default(5)` | Validated server-side against `DENY_TABLES` | `.strict()` |
| `list_step_types` | No input parameters | N/A | N/A (read-only, no schema) |
| `list_db_tables` | No input parameters | N/A | N/A (read-only, no schema) |
| `list_provider_capabilities` | No input parameters | N/A | N/A (read-only, no schema) |

**MCP Resources (6 resources — fetch-only, no input schema):**

| Resource URI | Backend Endpoint | Contract |
|-------------|-----------------|----------|
| `pipeline://templates` | `GET /scheduling/templates` | Returns JSON array of template summaries |
| `pipeline://db-schema` | `GET /scheduling/db-schema` | Returns table/column schemas, DENY_TABLES excluded server-side |
| `pipeline://emulator/mock-data` | `GET /scheduling/emulator/mock-data` | Returns sample mock data sets per `data_type` |
| `pipeline://providers` | `GET /market-data/providers` | Returns provider names, data_types, auth methods |
| `pipeline://deny-tables` | Static | Returns JSON array of DENY_TABLES entries |
| `pipeline://emulator-phases` | Static | Returns 4-phase pipeline documentation (PARSE, VALIDATE, SIMULATE, RENDER) |

**REST Endpoints (write surfaces):**

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| REST `POST /scheduling/emulator/run` | Pydantic `EmulateRequest(extra="forbid")` | `policy_json: dict`, `phases: list[str] or None` | `extra="forbid"` |
| REST `POST /scheduling/templates` | Pydantic `EmailTemplateCreateRequest(extra="forbid")` | [09e §9E.0](../../build-plan/09e-template-database.md) field constraints | `extra="forbid"` |
| REST `PATCH /scheduling/templates/{name}` | Pydantic `EmailTemplateUpdateRequest(extra="forbid")` | Same invariants as create for provided fields | `extra="forbid"` |
| REST `DELETE /scheduling/templates/{name}` | Path param `name: str` | Rejects `is_default=True` templates (403) | N/A |
| REST `GET /scheduling/templates/{name}` | Path param `name: str` | 404 if not found | N/A |
| REST `POST /scheduling/templates/{name}/preview` | Pydantic `PreviewRequest(extra="forbid")` | Optional `data: dict` override | `extra="forbid"` |
| REST `POST /scheduling/validate-sql` | Pydantic `ValidateSqlRequest(extra="forbid")` | `sql: str`, 1–10000 chars | `extra="forbid"` |
| REST `GET /scheduling/db-schema/samples/{table}` | Path param `table: str`, query `limit: int = 5` | `table` validated against `DENY_TABLES` (403) | N/A |

**Error mapping:**

| Condition | HTTP Status | MCP Error |
|-----------|:-----------:|-----------|
| Invalid emulator input | 422 | `INVALID_PARAMS` |
| Invalid policy JSON (PARSE) | 200 (structured error in body) | Structured `EmulatorResult.errors` |
| SQL validation failure | 200 (structured) | `{valid: false, errors: [...]}` |
| Template name conflict (create) | 409 | MCP error text |
| Template not found | 404 | MCP error text |
| `DENY_TABLES` violation | 403 | MCP error text |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 12 MCP tools (emulate_policy, list_step_types, list_db_tables, get_db_row_samples, validate_sql, list_provider_capabilities, create/get/list/update/delete/preview_email_template) | Spec | [05g §Pipeline Security Hardening Tools](../../build-plan/05g-mcp-scheduling.md) |
| 6 MCP resources (pipeline://templates, pipeline://db-schema, pipeline://emulator/mock-data, pipeline://providers, pipeline://deny-tables, pipeline://emulator-phases) | Spec | [05g §New Resources](../../build-plan/05g-mcp-scheduling.md) |
| REST endpoint: `POST /scheduling/emulator/run` | Spec | [09f §9F.1](../../build-plan/09f-policy-emulator.md) — emulator REST wrapper |
| REST endpoints: template CRUD (POST/GET/PATCH/DELETE + preview) | Spec | [09e §9E.2](../../build-plan/09e-template-database.md) — PH6 built core port + infra repo; REST routes are NEW in PH9 |
| REST endpoint: `GET /scheduling/db-schema` | Spec | [05g §pipeline://db-schema](../../build-plan/05g-mcp-scheduling.md) — filters `DENY_TABLES` |
| REST endpoint: `GET /scheduling/emulator/mock-data` | Spec | [05g §pipeline://emulator/mock-data](../../build-plan/05g-mcp-scheduling.md) |
| REST endpoint: `GET /scheduling/step-types` | Local Canon | Exists (MEU-89) — verified in `scheduling.py` |
| REST endpoint: `GET /market-data/providers` | Local Canon | Exists (MEU-63) — verified in `market_data.py` |
| REST endpoint: `POST /scheduling/validate-sql` | Spec | [05g §validate_sql](../../build-plan/05g-mcp-scheduling.md) |
| REST endpoint: `GET /scheduling/db-schema/samples/{table}` | Spec | [05g §get_db_row_samples](../../build-plan/05g-mcp-scheduling.md) |
| MCP response cap: 4 KiB for emulator tool | Spec | [09f §9F.2a](../../build-plan/09f-policy-emulator.md) |
| Zod/Pydantic schema parity for template CRUD | Local Canon | [09e §9E.0](../../build-plan/09e-template-database.md) |
| Tool descriptions include M7 workflow context | Local Canon | [emerging-standards.md §M7](../../../.agent/docs/emerging-standards.md) |
| Pipeline security tools registered in scheduling toolset | Spec | [05g §annotations](../../build-plan/05g-mcp-scheduling.md) |
| MCP protocol tests for all 12 tools + 6 resources | Local Canon | AGENTS.md §Testing + [09c §PH9 test matrix](../../build-plan/09c-pipeline-security-hardening.md) — PH9 ships tools, tests ship with them |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-16 | `emulate_policy` MCP tool calls `POST /scheduling/emulator/run` and returns structured result | Spec | Invalid policy JSON → structured errors |
| AC-17 | `validate_sql` MCP tool returns `{valid, errors}` | Spec | INSERT statement → `{valid: false}` |
| AC-18 | `list_step_types` returns all registered step types including `query`, `compose` | Spec | N/A |
| AC-19 | `list_db_tables` excludes tables in `DENY_TABLES` | Spec | Verify denied tables absent from result |
| AC-20 | `get_db_row_samples` rejects `DENY_TABLES` with 403 | Spec | Request `settings` table → 403 |
| AC-21 | `create_email_template` MCP tool proxies to `POST /scheduling/templates` | Spec | Duplicate name → 409 error |
| AC-22 | `get_email_template` returns template by name | Spec | Non-existent name → 404 |
| AC-23 | `list_email_templates` returns all templates | Spec | N/A |
| AC-24 | `update_email_template` proxies to PATCH | Spec | Invalid body_html → 422 |
| AC-25 | `preview_email_template` renders with sample data | Spec | N/A |
| AC-26 | `list_provider_capabilities` returns providers from market-data API | Spec | N/A |
| AC-27 | All 6 MCP resources return valid JSON | Spec | N/A |
| AC-28 | Emulator MCP response capped at 4 KiB | Spec | Large policy with many steps |
| AC-29 | All MCP tool descriptions include M7 workflow context | Local Canon | N/A |
| AC-30m | Template REST CRUD: create, get, list, update, delete work end-to-end | Spec | Delete default → 403 |
| AC-31m | Zod `.strict()` rejects unknown fields on write tools | Spec | Extra field → MCP `INVALID_PARAMS` |
| AC-32m | `list_db_tables` resource and tool both exclude DENY_TABLES | Spec | `settings` absent from result |
| AC-33m | MCP protocol tests pass for all 12 tools + 6 resources | Local Canon | Invalid input, denied tables, cap enforcement |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/routes/scheduling.py` | modify | Add emulator, db-schema, validate-sql, samples, **template CRUD** endpoints |
| `packages/api/src/zorivest_api/schemas/template_schemas.py` | new | `EmailTemplateCreateRequest`, `EmailTemplateUpdateRequest`, `PreviewRequest`, `ValidateSqlRequest`, `EmulateRequest` Pydantic models |
| `packages/api/src/zorivest_api/main.py` | modify | Wire `PolicyEmulator` + `SessionBudget` + `EmailTemplateRepository` into lifespan |
| `mcp-server/src/tools/pipeline-security-tools.ts` | new | 12 MCP tools + 6 resources |
| `mcp-server/src/index.ts` | modify | Import + register pipeline security tools |
| `tests/unit/test_emulator_api.py` | new | REST endpoint tests for emulator + template CRUD |
| `tests/unit/test_mcp_pipeline_security.py` | new | MCP protocol tests: Zod strict, DENY_TABLES enforcement, 4 KiB cap, resource JSON shape |

---

### MEU-PH10: Default Morning Check-In Template

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Template name: `morning-check-in` | Spec | [09e §9E.6b](../../build-plan/09e-template-database.md) |
| Subject: `Morning Market Check-In — {{ date }}` | Spec | [09e §9E.6b](../../build-plan/09e-template-database.md) |
| Sections: watchlist quotes, portfolio summary, market news | Spec | [09e §9E.6b](../../build-plan/09e-template-database.md) |
| Required variables: `["date", "watchlist_name"]` | Spec | [09e §9E.6b](../../build-plan/09e-template-database.md) |
| `is_default: True` | Spec | [09e §9E.1c](../../build-plan/09e-template-database.md) |
| Seeded via Alembic migration | Spec | [09e §9E.6](../../build-plan/09e-template-database.md) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-30 | `morning-check-in` template exists in DB after migration | Spec | N/A |
| AC-31 | Template has `is_default=True` and cannot be deleted | Spec | `DELETE /scheduling/templates/morning-check-in` → 403 |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `alembic/versions/xxxx_seed_morning_checkin.py` | new | Alembic data migration seeding the template |
| `tests/unit/test_default_template.py` | new | 2 tests: existence + delete protection |

---

## Out of Scope

- PH8 E2E integration tests (covered by existing MEU-PW8 harness)
- GUI template editor (future MEU under Phase 6)
- Alembic migration for `email_templates` table creation (already done in PH6)
- MCP tool description audit / workflow discovery enrichment (MEU-TD1 scope — independent of PH9 protocol correctness)

---

## BUILD_PLAN.md Audit

This project changes PH8/PH9/PH10 status from ⬜ to ✅ in `docs/BUILD_PLAN.md`. It also updates the Phase 9 status tracker row to reflect "P2.5c complete (10/10 MEUs)".

```powershell
rg "MEU-PH8|MEU-PH9|MEU-PH10" docs/BUILD_PLAN.md  # Expected: 3 matches in P2.5c table
```

The P2.5c summary count in `docs/BUILD_PLAN.md` line 627 currently says `7` completed — must update to `10`.

---

## Verification Plan

### 1. Unit Tests (Python)
```powershell
uv run pytest tests/unit/test_policy_emulator.py tests/unit/test_emulator_budget.py tests/unit/test_default_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ph8.txt; Get-Content C:\Temp\zorivest\pytest-ph8.txt | Select-Object -Last 40
```

### 2. Emulator API Tests
```powershell
uv run pytest tests/unit/test_emulator_api.py -x --tb=short -v *> C:\Temp\zorivest\pytest-emu-api.txt; Get-Content C:\Temp\zorivest\pytest-emu-api.txt | Select-Object -Last 30
```

### 3. Type Checking
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 4. Linting
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 5. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/ *> C:\Temp\zorivest\placeholders.txt; Get-Content C:\Temp\zorivest\placeholders.txt | Select-Object -Last 20
```

### 6. MCP Build (TypeScript)
```powershell
cd mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt | Select-Object -Last 20
```

### 7. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 8. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 9. OpenAPI Spec (if API routes modified)
```powershell
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi-check.txt; Get-Content C:\Temp\zorivest\openapi-check.txt
```

---

## Open Questions

> [!WARNING]
> None. All behaviors are fully specified in the build plan documents. No human decision gates required.

---

## Research References

- [09f — Policy Emulator](../../build-plan/09f-policy-emulator.md)
- [05g — MCP Scheduling Tools](../../build-plan/05g-mcp-scheduling.md)
- [09e — Template Database](../../build-plan/09e-template-database.md) §9E.6
- [09c — Pipeline Security Hardening](../../build-plan/09c-pipeline-security-hardening.md)
- [p2.5c Security Hardening Analysis](p2.5c_security_hardening_analysis.md) (Session 3 grouping)
