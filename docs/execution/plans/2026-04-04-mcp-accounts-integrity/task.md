# MEU-37 Task List — Account CRUD MCP Tools + Integrity

> **Project slug**: `2026-04-04-mcp-accounts-integrity`
> **MEU**: MEU-37 (`mcp-accounts`)
> **Plan**: [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-04-04-mcp-accounts-integrity/implementation-plan.md)
> **Corrections**: Pass 1 (2026-04-04) + Pass 2 (2026-04-04)
> **User decisions**: pomera note 732

---

## WP-1: Domain Entity Changes

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | AC-1: Add `is_archived: bool = False` to Account dataclass | coder | `entities.py` | `pytest tests/unit/test_entities.py` | `[x]` |
| 2 | AC-2: Add `is_system: bool = False` to Account dataclass | coder | `entities.py` | `pytest tests/unit/test_entities.py` | `[x]` |
| 3 | Write tests for new entity fields | coder | `test_entities.py` | Tests exist + RED | `[x]` |

---

## WP-2: Infrastructure

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 4 | Add `is_archived`, `is_system` columns to `AccountModel` | coder | `models.py` | `pytest tests/unit/test_models.py` | `[x]` |
| 5 | Add inline ALTER TABLE migrations to `main.py` `_inline_migrations` | coder | `main.py` L156-160 | Startup: columns exist in DB | `[x]` |
| 6 | AC-3: Create idempotent `seed_system_account()` (name: "System Reassignment Account") | coder | `seed_system_account.py` | Startup: SYSTEM_DEFAULT row present | `[x]` |
| 7 | Call `seed_system_account()` in `main.py` lifespan after `seed_defaults()` | coder | `main.py` lifespan | Startup: seed is called | `[x]` |
| 8 | Write model tests | coder | `test_models.py` | Tests exist + RED | `[x]` |

---

## WP-3: Repository Changes

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 9 | Update `AccountRepository` port with `include_archived`, `include_system`, `count_all` | coder | `ports.py` | `pyright` clean | `[x]` |
| 10 | AC-4: Update `list_all()` to filter archived by default | coder | `repositories.py` | `pytest tests/integration/test_repositories.py` | `[x]` |
| 11 | AC-5: Update `list_all()` to filter system accounts by default | coder | `repositories.py` | `pytest tests/integration/test_repositories.py` | `[x]` |
| 12 | Add `count_all()` to repository | coder | `repositories.py` | `pytest tests/integration/test_repositories.py` | `[x]` |
| 13 | Write repository tests | coder | `tests/integration/test_repositories.py` | Tests exist + RED | `[x]` |

---

## WP-4: Service Layer

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 14 | Add `ForbiddenError` and `ConflictError` to domain exceptions | coder | `exceptions.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 15 | AC-6: System account guard on `update_account()` | coder | `account_service.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 16 | AC-7: System account guard on `delete_account()`, `archive_account()`, `reassign_trades_and_delete()` | coder | `account_service.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 17 | AC-8: Block-only `delete_account()` — reject if trades exist (ConflictError) | coder | `account_service.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 18 | AC-9: Block-only `delete_account()` — allow if no trades (hard delete) | coder | `account_service.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 19 | AC-10: `archive_account()` — set `is_archived=True` | coder | `account_service.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 20 | AC-11: `reassign_trades_and_delete()` — move trades to SYSTEM_DEFAULT, hard delete | coder | `account_service.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 21 | AC-12: Computed metrics (`get_account_metrics`) | coder | `account_service.py` | `pytest tests/unit/test_account_service.py` | `[x]` |
| 22 | Write service tests | coder | `test_account_service.py` | Tests exist + RED | `[x]` |

---

## WP-5: API Updates

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 23 | AC-13: Make `account_id` optional in `CreateAccountRequest` (default UUID) | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` | `[x]` |
| 24 | Extend `AccountResponse` with `is_archived`, `is_system`, metrics fields | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` | `[x]` |
| 25 | Update `DELETE /accounts/{id}` — block-only (ForbiddenError/ConflictError) | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` | `[x]` |
| 26 | Add `POST /accounts/{id}:archive` route | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` (AC-10) | `[x]` |
| 27 | Add `POST /accounts/{id}:reassign-trades` route | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` (AC-11) | `[x]` |
| 28 | Add `include_archived`/`include_system` to list route | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` (AC-4, AC-5) | `[x]` |
| 29 | Enrich `GET /accounts/{id}` with computed metrics | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` (AC-12) | `[x]` |
| 30 | Map `ForbiddenError` → 403, `ConflictError` → 409 | coder | `accounts.py` (routes) | `pytest tests/unit/test_api_accounts.py` | `[x]` |
| 31 | Update KNOWN_EXCEPTIONS in `test_schema_contracts.py` (RULE-2) | coder | `test_schema_contracts.py` | `pytest tests/unit/test_schema_contracts.py` | `[x]` |
| 32 | Regenerate OpenAPI spec (G8) | coder | `openapi.committed.json` | `uv run python tools/export_openapi.py --check` | `[x]` |
| 33 | Write route tests | coder | `tests/unit/test_api_accounts.py` | Tests exist + RED | `[x]` |

---

## WP-6: MCP Tools

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 34 | AC-14: Implement `list_accounts` MCP tool | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 35 | AC-15: Implement `get_account` MCP tool | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 36 | AC-16: Implement `create_account` MCP tool (guarded, no confirmation) | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 37 | Implement `update_account` MCP tool | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 38 | AC-17: Implement `delete_account` MCP tool (destructive + confirmation, M2/M3) | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 39 | AC-18: Implement `archive_account` MCP tool (guarded, non-destructive) | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 40 | AC-19: Implement `reassign_trades` MCP tool (destructive + confirmation, M3) | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 41 | AC-20: Implement `record_balance` MCP tool | coder | `accounts-tools.ts` | `npx vitest run mcp-server/tests/accounts-tools.test.ts` | `[x]` |
| 42 | Update toolset tool count (8 → 16) | coder | `seed.ts` | `rg 'accounts.*16' mcp-server/src/toolsets/seed.ts` | `[x]` |
| 43 | Build MCP dist | coder | `mcp-server/dist/` | `cd mcp-server && npm run build` succeeds | `[x]` |
| 44 | Write vitest tests for all 8 tools | coder | `mcp-server/tests/accounts-tools.test.ts` | Tests exist + RED | `[x]` |

---

## WP-7: Documentation & Trackers

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 45 | Update `domain-model-reference.md` (is_archived, is_system, System Reassignment Account) | coder | `domain-model-reference.md` | Manual review | `[x]` |
| 46 | Update `05f-mcp-accounts.md` — remove create_account confirmation, add archive/reassign specs | coder | `05f-mcp-accounts.md` | `rg 'confirmation required' docs/build-plan/05f-mcp-accounts.md` returns 0 | `[x]` |
| 47 | Update `BUILD_PLAN.md` — status ✅ + description text (separate endpoints, 8 tools) | coder | `BUILD_PLAN.md` L190 | `rg 'three-path deletion' docs/BUILD_PLAN.md` returns 0 | `[x]` |
| 48 | Update `meu-registry.md` status → ✅ | coder | `meu-registry.md` | Manual verify | `[x]` |

---

## Quality Gates

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 49 | Anti-placeholder scan | guardrail | No TODO/FIXME | `rg "TODO\|FIXME\|NotImplementedError" packages/` | `[x]` |
| 50 | MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu` | `[x]` |
| 51 | Pre-commit | tester | Hooks pass | `pre-commit run --all-files` | `[x]` |
| 52 | Full regression | tester | All tests GREEN | `uv run pytest tests/ -x --tb=short -v` | `[x]` |
| 53 | OpenAPI drift check | tester | No drift | `uv run python tools/export_openapi.py --check` | `[x]` |

---

## Post-MEU Deliverables

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 54 | Create handoff (097-2026-04-05-mcp-accounts-integrity-bp05fs5f.md) | coder | Handoff file | File exists with evidence | `[x]` |
| 55 | Create reflection | coder | Reflection file | File exists | `[x]` |
| 56 | Update metrics table | coder | Metrics updated | Manual review | `[x]` |
| 57 | Save session state to pomera_notes | coder | Note saved | Note ID returned | `[x]` |
| 58 | Prepare commit messages | coder | Commit messages | Ready for `git commit` | `[x]` |
