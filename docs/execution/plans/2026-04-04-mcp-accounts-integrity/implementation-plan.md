# MEU-37: Account CRUD MCP Tools + Account-Trade Integrity

> **Project slug:** `2026-04-04-mcp-accounts-integrity`
> **MEU:** MEU-37 (`mcp-accounts`)
> **Build-plan ref:** [05f-mcp-accounts.md](../../../build-plan/05f-mcp-accounts.md) + [BUILD_PLAN.md L190](../../../BUILD_PLAN.md)
> **Phase:** 5 (MCP Server) — all prerequisites satisfied
> **Corrections applied:** 2026-04-04 — resolved 5 review findings + 3 user directives

---

## Problem Statement

MEU-37 is the last remaining Phase 5 MEU and is currently marked 🔴 `changes_required`. The MCP server's `accounts-tools.ts` has 8 thin-proxy tools implemented (broker sync, imports), but the **core Account CRUD MCP tools** are not yet implemented. Additionally, BUILD_PLAN.md L190 requires account-trade integrity features that don't exist in the domain, service, or API layers:

- **Missing entity fields:** `is_archived`, `is_system` on Account
- **Missing business logic:** System Reassignment Account, account deletion/archival/reassignment, system account guard
- **Missing computed metrics:** Per-account `trade_count`, `round_trip_count`, `win_rate`, `total_realized_pnl`
- **Missing MCP tools:** `list_accounts`, `get_account`, `create_account`, `update_account`, `delete_account`, `record_balance`, `archive_account`, `reassign_trades`
- **Missing MCP parity:** DELETE `/api/v1/accounts/{id}` has no corresponding `delete_account` MCP tool (M2 violation)

## Resolved Decisions

> [!NOTE]
> **Scope Reduction:** The 8 existing P2.75-dependent tools (`sync_broker`, `list_brokers`, `resolve_identifiers`, 3 import tools, `list_bank_accounts`, `get_account_review_checklist`) are OUT-OF-SCOPE. They remain as-is — they'll become functional when P2.75 MEUs (96–103) build the corresponding REST routes.

> [!NOTE]
> **System Reassignment Account (Human-approved):** `account_id = "SYSTEM_DEFAULT"`, `name = "System Reassignment Account"`, `account_type = broker`. Hidden from all default list/selector endpoints via `is_system` exclusion.

> [!NOTE]
> **Separate action endpoints (Human-approved, RFC 9110-aligned):**
> - `DELETE /accounts/{id}` → block-only: 409 if trades exist, 204 if no trades, 403 if system
> - `POST /accounts/{id}:archive` → soft-delete (set `is_archived=True`); 403 if system
> - `POST /accounts/{id}:reassign-trades` → move all trades to SYSTEM_DEFAULT, then hard delete; 403 if system
>
> Rationale: plain DELETE = safe default. Archive and reassign are materially different business actions exposed as explicit endpoints per RFC 9110 §9.3.5 guidance against overloading DELETE semantics.

> [!NOTE]
> **Confirmation on `delete_account` only (Human-approved):** `create_account` does not use `withConfirmation()`. Only `delete_account` and `reassign_trades` are destructive and require confirmation tokens. This aligns with M3 which governs destructive tools only.

---

## Spec Sufficiency Table

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Account CRUD MCP tools (list/get/create/update/record_balance) | `Spec` | 05f-mcp-accounts.md L7-178 | ✅ |
| `delete_account` MCP tool (API↔MCP parity) | `Local Canon` | M2 standard + accounts.py L157 | ✅ |
| `archive_account` MCP tool | `Human-approved` | User directive: separate action endpoints | ✅ |
| `reassign_trades` MCP tool | `Human-approved` | User directive: separate action endpoints | ✅ |
| `is_archived` soft-delete field | `Spec` + `Research-backed` | BUILD_PLAN.md L190 + standard soft-delete pattern | ✅ |
| `is_system` guard field | `Spec` + `Research-backed` | BUILD_PLAN.md L190 + standard system-entity pattern | ✅ |
| System Reassignment Account (seeded, undeletable) | `Spec` + `Human-approved` | BUILD_PLAN.md L190 + user naming/hiding decision | ✅ |
| Deletion = block-only; archive/reassign via action endpoints | `Spec` + `Human-approved` | BUILD_PLAN.md L190 + user API design decision (RFC 9110) | ✅ |
| Computed metrics (trade_count, round_trip_count, win_rate, total_realized_pnl) | `Spec` | BUILD_PLAN.md L190 | ✅ |
| MCP `account_id` validation | `Spec` | BUILD_PLAN.md L190 | ✅ (API-layer enforced, no MCP-side duplicate) |
| `create_account` auto-assigns UUID | `Spec` | 05f-mcp-accounts.md L98 ("assigned account_id") | ✅ |
| System accounts hidden from default lists | `Human-approved` | User directive: exclude `is_system=True` from selectors | ✅ |
| GUI trade form `<select>` dropdown | `Local Canon` | 06b L179 — already built in MEU-47/71b | ✅ (verification only) |
| Destructive tool gate (M3) — delete + reassign only | `Local Canon` + `Human-approved` | emerging-standards.md M3 + user ruling: delete-only confirmation | ✅ |
| Schema field parity (M1) | `Local Canon` | emerging-standards.md M1 | ✅ |
| OpenAPI spec regen (G8) | `Local Canon` | emerging-standards.md G8 | ✅ |
| Inline migration pattern (no Alembic) | `Local Canon` | main.py L154-168 `_inline_migrations` + seed_defaults.py | ✅ |

---

## Proposed Changes

### WP-1: Domain Entity Changes

#### [MODIFY] [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py)

Add two fields to the `Account` dataclass:

```python
@dataclass
class Account:
    # ... existing fields ...
    is_archived: bool = False   # Soft-delete flag
    is_system: bool = False     # System-seeded, immutable/undeletable
```

#### [MODIFY] [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md)

Update Account entity section to document `is_archived` and `is_system` fields.

---

### WP-2: Infrastructure (SQLAlchemy + Inline Migration + Seed)

#### [MODIFY] [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py)

Add `is_archived` and `is_system` Boolean columns to `AccountModel`.

#### [MODIFY] [main.py](file:///p:/zorivest/packages/api/src/zorivest_api/main.py)

Add two inline migrations to the `_inline_migrations` list (L156-160):

```python
"ALTER TABLE accounts ADD COLUMN is_archived BOOLEAN DEFAULT 0",
"ALTER TABLE accounts ADD COLUMN is_system BOOLEAN DEFAULT 0",
```

These follow the existing pattern: `Base.metadata.create_all()` handles fresh databases; `ALTER TABLE` handles existing databases created before these columns existed.

#### [NEW] [seed_system_account.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/seed_system_account.py)

Idempotent seeding function following `seed_defaults.py` pattern:

```python
def seed_system_account(session: Session) -> None:
    """Ensure the System Reassignment Account exists.

    Idempotent: safe to call multiple times.
    """
    existing = session.get(AccountModel, "SYSTEM_DEFAULT")
    if existing is None:
        session.add(AccountModel(
            account_id="SYSTEM_DEFAULT",
            name="System Reassignment Account",
            account_type="broker",
            institution="System",
            is_system=True,
            is_archived=False,
            is_tax_advantaged=False,
        ))
```

Call in `main.py` lifespan after `seed_defaults()`.

#### System Reassignment Account seed values:

| Field | Value |
|---|---|
| `account_id` | `SYSTEM_DEFAULT` |
| `name` | `System Reassignment Account` |
| `account_type` | `broker` |
| `institution` | `System` |
| `is_system` | `True` |
| `is_archived` | `False` |
| `is_tax_advantaged` | `False` |

---

### WP-3: Repository Changes

#### [MODIFY] [repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py)

Update `AccountRepository.list_all()` to filter out archived and system accounts by default. Add parameters:
- `include_archived: bool = False` — include soft-deleted accounts
- `include_system: bool = False` — include system accounts (hidden from normal UX)

Add `count_all()` method for pagination (P1 standard).

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Update `AccountRepository` protocol to include `include_archived` and `include_system` parameters on `list_all` and add `count_all` method signature.

---

### WP-4: Service Layer — Integrity + Metrics

#### [MODIFY] [account_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/account_service.py)

**Block-only deletion:**

```python
def delete_account(self, account_id: str) -> None:
    """Delete account if it has no trades.

    Raises:
        ForbiddenError: If account is a system account (is_system=True)
        ConflictError: If account has associated trades
        NotFoundError: If account does not exist
    """
```

**Archive account:**

```python
def archive_account(self, account_id: str) -> None:
    """Soft-delete: set is_archived=True. Trades remain unchanged.

    Raises:
        ForbiddenError: If account is a system account (is_system=True)
        NotFoundError: If account does not exist
    """
```

**Reassign trades and delete:**

```python
def reassign_trades_and_delete(self, account_id: str) -> int:
    """Move all trades to SYSTEM_DEFAULT, then hard-delete the account.

    Returns:
        Number of trades reassigned.

    Raises:
        ForbiddenError: If account is a system account (is_system=True)
        NotFoundError: If account does not exist
    """
```

**System account guard:**
- `update_account()` → raise `ForbiddenError` if `is_system=True`
- `delete_account()` → raise `ForbiddenError` if `is_system=True`
- `archive_account()` → raise `ForbiddenError` if `is_system=True`
- `reassign_trades_and_delete()` → raise `ForbiddenError` if `is_system=True`

**Computed metrics:**

```python
def get_account_metrics(self, account_id: str) -> dict:
    """Compute trade-based metrics for an account.

    Returns:
        dict with trade_count, round_trip_count, win_rate, total_realized_pnl
    """
```

Uses existing analytics functions from `zorivest_core.domain.analytics` to compute per-account aggregates.

#### [MODIFY] [exceptions.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/exceptions.py)

Add `ForbiddenError` and `ConflictError` domain exceptions (if not already present).

---

### WP-5: API Updates

#### [MODIFY] [accounts.py (routes)](file:///p:/zorivest/packages/api/src/zorivest_api/routes/accounts.py)

1. **`CreateAccountRequest`:** Make `account_id` optional (default to `str(uuid.uuid4())`). This aligns the API with 05f spec L98 ("assigned account_id"). Existing callers that supply `account_id` continue to work.

2. **Delete route:** Block-only (no strategy param). Map `ForbiddenError` → 403, `ConflictError` → 409.

3. **[NEW] Archive endpoint:** `POST /accounts/{id}:archive` → calls `service.archive_account()`. Map `ForbiddenError` → 403.

4. **[NEW] Reassign-trades endpoint:** `POST /accounts/{id}:reassign-trades` → calls `service.reassign_trades_and_delete()`. Map `ForbiddenError` → 403. Returns `{"trades_reassigned": N}`.

5. **AccountResponse enrichment:** Add optional fields for computed metrics on `GET /accounts/{id}`:
   ```python
   trade_count: Optional[int] = None
   round_trip_count: Optional[int] = None
   win_rate: Optional[float] = None
   total_realized_pnl: Optional[float] = None
   is_archived: bool = False
   is_system: bool = False
   ```

6. **List endpoint:** Add `include_archived: bool = Query(default=False)` and `include_system: bool = Query(default=False)` parameters. Default queries exclude both archived and system accounts.

---

### WP-6: MCP Tools (8 New Tools)

#### [MODIFY] [accounts-tools.ts](file:///p:/zorivest/mcp-server/src/tools/accounts-tools.ts)

Add 8 new tool registrations to `registerAccountTools()`:

| Tool | Method | Endpoint | Annotations |
|---|---|---|---|
| `list_accounts` | GET | `/api/v1/accounts` | readOnly, idempotent |
| `get_account` | GET | `/api/v1/accounts/{id}` | readOnly, idempotent |
| `create_account` | POST | `/api/v1/accounts` | guarded (no confirmation) |
| `update_account` | PUT | `/api/v1/accounts/{id}` | guarded |
| `delete_account` | DELETE | `/api/v1/accounts/{id}` | **destructive** + confirmation (M3) |
| `record_balance` | POST | `/api/v1/accounts/{id}/balances` | guarded |
| `archive_account` | POST | `/api/v1/accounts/{id}:archive` | guarded (non-destructive) |
| `reassign_trades` | POST | `/api/v1/accounts/{id}:reassign-trades` | **destructive** + confirmation (M3) |

- `delete_account` and `reassign_trades` registered in `DESTRUCTIVE_TOOLS` set
- Both wrapped with `withConfirmation()` (M3)
- Both include `confirmation_token` in Zod schema (M1)
- `create_account` does NOT get confirmation (Human-approved: non-destructive write)

#### [MODIFY] toolsets registration

Update accounts toolset tool count from 8 → 16.

#### [MODIFY] MCP test file

Add vitest tests for all 8 new tools in `mcp-server/tests/accounts-tools.test.ts`.

---

### WP-7: Documentation & Tracker Updates

#### [MODIFY] [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md)

Add `is_archived`, `is_system` fields to Account entity section. Document System Reassignment Account. Document deletion/archival/reassignment semantics.

#### [MODIFY] [05f-mcp-accounts.md](file:///p:/zorivest/docs/build-plan/05f-mcp-accounts.md)

Canon alignment (resolves P2-F2 canon drift):
- Update `create_account` Side Effects (L99): change "guarded + confirmation required" → "guarded" (confirmation removed per Human-approved decision, pomera note 732)
- Add `archive_account` tool spec (new tool, mirrors `POST /accounts/{id}:archive`)
- Add `reassign_trades` tool spec (new tool, mirrors `POST /accounts/{id}:reassign-trades`)
- Update total tool count in header

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

1. Update MEU-37 status from 🔴 → ✅
2. Update MEU-37 description (L190): replace "three-path deletion (block/archive/reassign-to-default)" with "separate action endpoints (DELETE block, POST :archive, POST :reassign-trades)". Update tool count from 5 to 8. Add `archive_account`, `reassign_trades` to tool list.

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

Update MEU-37 status to ✅ approved with date.

#### [MODIFY] Schema contract tests

If `AccountResponse` fields are added, update `KNOWN_EXCEPTIONS` in `test_schema_contracts.py` (RULE-2).

---

## Feature Intent Contract (FIC)

### AC-1: `is_archived` field exists on Account entity [Spec]
Account dataclass has `is_archived: bool = False`. SQLAlchemy model has corresponding Boolean column. Inline migration adds column to existing databases.

### AC-2: `is_system` field exists on Account entity [Spec]
Account dataclass has `is_system: bool = False`. SQLAlchemy model has corresponding Boolean column. Inline migration adds column to existing databases.

### AC-3: System Reassignment Account is seeded on startup [Spec + Human-approved]
After startup, querying for `account_id = "SYSTEM_DEFAULT"` returns an account with `is_system=True`, `name="System Reassignment Account"`, `account_type="broker"`. Seeding is idempotent.

### AC-4: Archived accounts are hidden from list by default [Research-backed]
`list_accounts()` without `include_archived` parameter returns only accounts where `is_archived=False`. Passing `include_archived=True` returns all.

### AC-5: System accounts are hidden from list by default [Human-approved]
`list_accounts()` without `include_system` parameter returns only accounts where `is_system=False`. Passing `include_system=True` returns system accounts. This prevents the System Reassignment Account from appearing in trade form dropdowns.

### AC-6: System accounts cannot be updated [Spec]
`update_account("SYSTEM_DEFAULT", name="Foo")` raises `ForbiddenError`.

### AC-7: System accounts cannot be deleted/archived/reassigned [Spec]
`delete_account("SYSTEM_DEFAULT")`, `archive_account("SYSTEM_DEFAULT")`, and `reassign_trades_and_delete("SYSTEM_DEFAULT")` all raise `ForbiddenError`.

### AC-8: Delete rejects when trades exist [Spec]
Given an account with 1+ trades, `delete_account(account_id)` raises `ConflictError`. Account and trades are unchanged.

### AC-9: Delete succeeds when no trades [Spec]
Given an account with 0 trades, `delete_account(account_id)` succeeds. Account is removed.

### AC-10: Archive soft-deletes the account [Spec + Human-approved]
`archive_account(account_id)` sets `is_archived=True`. Trades are unchanged. Account no longer appears in default list. Endpoint: `POST /accounts/{id}:archive`.

### AC-11: Reassign moves trades to System Default then deletes [Spec + Human-approved]
`reassign_trades_and_delete(account_id)` moves all trades to SYSTEM_DEFAULT, hard-deletes the original account, and returns the count of reassigned trades. Endpoint: `POST /accounts/{id}:reassign-trades`.

### AC-12: Computed metrics on get_account response [Spec]
GET `/api/v1/accounts/{id}` response includes `trade_count`, `round_trip_count`, `win_rate`, `total_realized_pnl` (all optional, populated from analytics).

### AC-13: `create_account` auto-assigns account_id [Spec]
`CreateAccountRequest.account_id` is optional (defaults to `str(uuid.uuid4())`). The MCP `create_account` tool omits `account_id` per 05f spec; the API auto-generates it. Response includes the assigned `account_id`.

### AC-14: `list_accounts` MCP tool returns account list [Spec]
MCP `list_accounts` tool calls GET `/api/v1/accounts` and returns JSON array of account objects.

### AC-15: `get_account` MCP tool returns single account [Spec]
MCP `get_account` tool calls GET `/api/v1/accounts/{id}` and returns JSON account object with metrics.

### AC-16: `create_account` MCP tool creates account (no confirmation) [Spec]
MCP `create_account` tool calls POST `/api/v1/accounts` with body. Guarded but no confirmation required (non-destructive write, per Human-approved ruling).

### AC-17: `delete_account` MCP tool is destructive with confirmation [Local Canon M2/M3]
MCP `delete_account` tool registered in DESTRUCTIVE_TOOLS, wrapped with `withConfirmation()`. Schema includes `confirmation_token` (M1). Block-only deletion semantics.

### AC-18: `archive_account` MCP tool archives account (non-destructive) [Human-approved]
MCP `archive_account` tool calls POST `/api/v1/accounts/{id}:archive`. Guarded, non-destructive (no confirmation required).

### AC-19: `reassign_trades` MCP tool is destructive with confirmation [Human-approved + M3]
MCP `reassign_trades` tool registered in DESTRUCTIVE_TOOLS, wrapped with `withConfirmation()`. Schema includes `confirmation_token` (M1). Calls POST `/api/v1/accounts/{id}:reassign-trades`.

### AC-20: `record_balance` MCP tool records balance snapshot [Spec]
MCP `record_balance` tool calls POST `/api/v1/accounts/{id}/balances`. Guarded.

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Add `is_archived`, `is_system` to Account entity | coder | entities.py updated | `pytest tests/unit/test_entities.py` | ⬜ |
| 2 | Add columns to SQLAlchemy AccountModel | coder | models.py updated | `pytest tests/unit/test_models.py` | ⬜ |
| 3 | Add inline ALTER TABLE migrations to main.py | coder | main.py updated | Startup: columns exist in DB | ⬜ |
| 4 | Create idempotent `seed_system_account()` + call in lifespan | coder | seed_system_account.py + main.py | Startup: SYSTEM_DEFAULT row present | ⬜ |
| 5 | Update repository — archive/system filter + count | coder | repositories.py, ports.py | `pytest tests/integration/test_repositories.py` | ⬜ |
| 6 | Add ForbiddenError, ConflictError exceptions | coder | exceptions.py | `pytest tests/unit/test_account_service.py` | ⬜ |
| 7 | Implement block-only `delete_account` in AccountService | coder | account_service.py | `pytest tests/unit/test_account_service.py` (AC-7, AC-8, AC-9) | ⬜ |
| 8 | Implement `archive_account` in AccountService | coder | account_service.py | `pytest tests/unit/test_account_service.py` (AC-10) | ⬜ |
| 9 | Implement `reassign_trades_and_delete` in AccountService | coder | account_service.py | `pytest tests/unit/test_account_service.py` (AC-11) | ⬜ |
| 10 | System account guards on all mutating methods | coder | account_service.py | `pytest tests/unit/test_account_service.py` (AC-6, AC-7) | ⬜ |
| 11 | Add computed metrics to AccountService | coder | account_service.py | `pytest tests/unit/test_account_service.py` (AC-12) | ⬜ |
| 12 | Make `account_id` optional in `CreateAccountRequest` | coder | accounts.py (routes) | `pytest tests/unit/test_api_accounts.py` (AC-13) | ⬜ |
| 13 | Update API DELETE route (block-only, ForbiddenError/ConflictError) | coder | accounts.py (routes) | `pytest tests/unit/test_api_accounts.py` | ⬜ |
| 14 | Add `POST /accounts/{id}:archive` route | coder | accounts.py (routes) | `pytest tests/unit/test_api_accounts.py` (AC-10) | ⬜ |
| 15 | Add `POST /accounts/{id}:reassign-trades` route | coder | accounts.py (routes) | `pytest tests/unit/test_api_accounts.py` (AC-11) | ⬜ |
| 16 | Extend AccountResponse with metrics + flags | coder | accounts.py (routes) | `pytest tests/unit/test_api_accounts.py` (AC-12) | ⬜ |
| 17 | Add `include_archived`/`include_system` to list route | coder | accounts.py (routes) | `pytest tests/unit/test_api_accounts.py` (AC-4, AC-5) | ⬜ |
| 18 | Implement 8 MCP CRUD tools | coder | accounts-tools.ts | `npx vitest run mcp-server/tests/accounts-tools.test.ts` (AC-14..AC-20) | ⬜ |
| 19 | Register delete + reassign as destructive (M3) | coder | accounts-tools.ts | `npx vitest run mcp-server/tests/accounts-tools.test.ts` (AC-17, AC-19) | ⬜ |
| 20 | Build MCP dist | coder | mcp-server/dist/ | `cd mcp-server && npm run build` succeeds | ⬜ |
| 21 | Update domain-model-reference.md | coder | docs updated | Manual review | ⬜ |
| 22 | Update 05f-mcp-accounts.md — canon alignment | coder | 05f updated (create_account confirmation removed, 2 new tool specs) | `rg 'confirmation required' docs/build-plan/05f-mcp-accounts.md` returns 0 | ⬜ |
| 23 | Update KNOWN_EXCEPTIONS if needed (RULE-2) | coder | test_schema_contracts.py | `pytest tests/unit/test_schema_contracts.py` | ⬜ |
| 24 | Regenerate OpenAPI spec (G8) | coder | openapi.committed.json | `uv run python tools/export_openapi.py --check` | ⬜ |
| 25 | Update BUILD_PLAN.md — status ✅ + description text | coder | BUILD_PLAN.md L190 updated | `rg 'three-path deletion' docs/BUILD_PLAN.md` returns 0 | ⬜ |
| 26 | Update meu-registry.md | coder | meu-registry.md updated | Manual verify | ⬜ |
| 27 | Anti-placeholder scan | guardrail | No TODO/FIXME | `rg "TODO\|FIXME\|NotImplementedError" packages/` | ⬜ |
| 28 | MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 29 | Pre-commit check (RULE-1) | tester | Hooks pass | `pre-commit run --all-files` | ⬜ |

---

## Verification Plan

### Automated Tests

```bash
# Python — unit tests (TDD: write first, implement second)
uv run pytest tests/unit/test_entities.py -x --tb=short -v
uv run pytest tests/unit/test_account_service.py -x --tb=short -v
uv run pytest tests/unit/test_api_accounts.py -x --tb=short -v

# Python — integration tests (repository layer)
uv run pytest tests/integration/test_repositories.py -x --tb=short -v

# TypeScript — MCP tool tests
cd mcp-server && npx vitest run tests/accounts-tools.test.ts

# Full regression
uv run pytest tests/ -x --tb=short -v

# MEU gate
uv run python tools/validate_codebase.py --scope meu

# OpenAPI drift check
uv run python tools/export_openapi.py --check openapi.committed.json

# Pre-commit
pre-commit run --all-files
```

### Manual Verification

- Verify System Reassignment Account appears in database after startup
- Verify `GET /api/v1/accounts` excludes archived and system accounts by default
- Verify `DELETE /api/v1/accounts/SYSTEM_DEFAULT` returns 403
- Verify `POST /api/v1/accounts/SYSTEM_DEFAULT:archive` returns 403
- Verify `POST /api/v1/accounts/SYSTEM_DEFAULT:reassign-trades` returns 403

---

## Handoff Naming

```
096-2026-04-0X-mcp-accounts-integrity-bp05fs5f.md
```

(Sequence 096, incrementing from last handoff in `.agent/context/handoffs/`)
