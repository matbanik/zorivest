---
project: "2026-04-25-pipeline-security-hardening"
date: "2026-04-25"
source: "docs/build-plan/09c-pipeline-security-hardening.md"
meus: ["MEU-PH1", "MEU-PH2", "MEU-PH3"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: P2.5c Pipeline Security Hardening

> **Project**: `2026-04-25-pipeline-security-hardening`
> **Build Plan Section(s)**: §9C.1–§9C.6
> **Status**: `draft`

---

## Goal

Harden the agentic pipeline against mutable state contamination, unauthorized SQL execution, and unsanctioned email delivery. Implements StepContext deep-copy isolation, a 6-layer SQL sandbox with SQLCipher support, secrets scanning, content-addressable policy IDs, and SendStep/FetchStep confirmation & content guards.

---

## User Review Required

> [!IMPORTANT]
> **SQLCipher scope (Human-approved):** PH2 implements SQLCipher-aware `open_sandbox_connection()` in `connection.py`, following the existing `create_encrypted_connection()` fallback pattern (`_SQLCIPHER_AVAILABLE` → SQLCipher, else plain sqlite3). The `SqlSandbox` constructor accepts a `sqlite3.Connection`-compatible object.

> [!IMPORTANT]
> **Approval provenance (Human-approved):** PH3 reuses existing `PolicyModel` approval state (`content_hash`, `approved_hash`, `approved_at` — see `models.py:444-448`) via a runtime `ApprovalSnapshot` dataclass injected into `StepContext`. No second persistent approval store is created.

> [!IMPORTANT]
> **Fan-out caps (Human-approved):** PH3 owns both caps: 5 URLs/step in `FetchStep` and 10 URLs/policy via `PipelineRunner` state tracking. Not deferred.

> [!IMPORTANT]
> **Body size cap:** 5 MB per spec §9C.4b (L393). Not 10 MB.

---

## Proposed Changes

### MEU-PH1: StepContext Deep-Copy Boundary

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1.1 | `StepContext.get_output()` returns a deep copy, not a reference | Spec §9C.1b | Mutation after get doesn't affect stored value |
| AC-1.2 | `StepContext.put_output()` stores a deep copy | Spec §9C.1b | Mutation after put doesn't affect stored value |
| AC-1.3 | `Secret` blocks `str()`, `format()`, `deepcopy()` | Spec §9C.1b | RuntimeError on stringify, RuntimeError on deepcopy |
| AC-1.4 | `Secret.reveal()` returns the original value | Spec §9C.1b | — |
| AC-1.5 | `safe_deepcopy` rejects objects exceeding 10 MB | Spec §9C.1c | MemoryError or ValueError on oversized object |
| AC-1.6 | `safe_deepcopy` rejects nesting > 64 levels | Spec §9C.1c | RecursionError or ValueError on deep nesting |
| AC-1.7 | `safe_deepcopy` handles circular references | Spec §9C.1c | No infinite loop; raises or returns safely |
| AC-1.8 | Nested objects containing `Secret` raise on deepcopy | Spec §9C.1c | RuntimeError when Secret is nested inside dict |
| AC-1.9 | `PipelineRunner` uses `put_output()` for all step results | Spec §9C.1b | Runner L201, L240 migrated; integration test proves isolation |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Deep-copy on get/put | Spec | §9C.1b explicit |
| Secret opaque wrapper | Spec | §9C.1b explicit |
| Depth/byte limits | Spec | §9C.1c explicit |
| Runner callsite migration | Spec | §9C.1b "steps no longer access raw references" |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/safe_copy.py` | new | `Secret` class + `safe_deepcopy()` with depth/byte limits |
| `packages/core/src/zorivest_core/domain/pipeline.py` | modify | Add `get_output()` → `safe_deepcopy`, add `put_output()` |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modify | Replace `context.outputs[step_def.id] = ...` with `context.put_output()` at L201, L240 |
| `tests/unit/test_stepcontext_isolation.py` | new | 9 tests (AC-1.1 through AC-1.9) |

---

### MEU-PH2: SQL Sandbox + Secrets Scanning + Content IDs

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-2.1 | SELECT on non-denied tables succeeds | Spec §9C.2d | — |
| AC-2.2 | INSERT/UPDATE/DELETE/DROP raise `SecurityError` | Spec §9C.2d | DML/DDL blocked |
| AC-2.3 | ATTACH DATABASE raises `SecurityError` | Spec §9C.2d | Attach blocked |
| AC-2.4 | PRAGMA with value raises `SecurityError` | Spec §9C.2d | Write-PRAGMA blocked |
| AC-2.5 | SELECT from each DENY_TABLE raises `SecurityError` | Spec §9C.2d | 6 tables tested |
| AC-2.6 | `sqlite_master` read blocked | Spec §9C.2d | — |
| AC-2.7 | CTE with SELECT allowed; CTE with DML blocked | Spec §9C.2d | — |
| AC-2.8 | Runaway query aborts after 2s | Spec §9C.2b L5 | Recursive CTE timeout |
| AC-2.9 | `load_extension()` blocked | Spec §9C.2d | — |
| AC-2.10 | Parameterized binds work | Spec §9C.2d | — |
| AC-2.11 | `open_sandbox_connection()` uses SQLCipher when available, plain sqlite3 fallback | Spec §9C.2b, Human-approved | — |
| AC-2.12 | `scan_for_secrets()` detects API keys, AWS keys, GH tokens, Bearer tokens, PEM keys | Spec §9C.5 (L429-449) | Returns match list |
| AC-2.13 | `scan_for_secrets()` returns empty list for clean policy JSON | Spec §9C.5 | — |
| AC-2.14 | `policy_content_id()` returns SHA-256 of canonical JSON | Spec §9C.6 (L456-466) | Deterministic hash |
| AC-2.15 | `policy_content_id()` is order-independent (sorted keys) | Spec §9C.6 | Same hash for reordered keys |
| AC-2.16 | `policy_validator.py` uses `SqlSandbox.validate_sql()` instead of `SQL_BLOCKLIST` | Spec §9C.2b L221 | AST validation replaces string matching |
| AC-2.17 | All callsites migrated: no direct `db_connection` SQL in steps | Spec §9C.2c | — |
| AC-2.18 | `DENY_TABLES` contract is importable from `sql_sandbox.py` for downstream PH9 use | Spec §9C.2e, Local Canon | Schema-discovery tests (PH9) import from here |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 6-layer security stack | Spec | §9C.2b explicit |
| SQLCipher-aware connection | Spec + Human-approved | §9C.2b L149,166-168; user directed: implement now with fallback |
| DENY_TABLES set | Spec | §9C.2b L154-164 |
| Secrets scanning | Spec | §9C.5 "Co-delivered with MEU-PH2" |
| Content-addressable IDs | Spec | §9C.6 "Co-delivered with MEU-PH2" |
| Schema-discovery tests | Spec | §9C.2d L267-270 "Owner: MEU-PH9" — deferred, PH2 owns DENY_TABLES contract only |
| `connection.py` factory | Spec | §9C.2b L220 explicit |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/sql_sandbox.py` | new | 6-layer sandbox + `SecurityError` + `validate_sql()` + `execute()` |
| `packages/infrastructure/src/zorivest_infra/database/connection.py` | modify | Add `open_sandbox_connection(db_path, passphrase, read_only=True)` with SQLCipher/sqlite3 fallback |
| `packages/core/src/zorivest_core/domain/policy_validator.py` | modify | Replace `SQL_BLOCKLIST` with `SqlSandbox.validate_sql()` + add `scan_for_secrets()` |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modify | Replace `db_connection` with `sql_sandbox` in context; compute+log `policy_content_id()` at run start |
| `packages/core/src/zorivest_core/pipeline_steps/store_report_step.py` | modify | Use `sql_sandbox.execute()` instead of raw `db_conn.execute()` |
| `packages/core/src/zorivest_core/services/criteria_resolver.py` | modify | Accept `sql_sandbox` instead of `db_connection` |
| `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py` | modify | Pass `sql_sandbox` to CriteriaResolver |
| `packages/core/pyproject.toml` | modify | Add `sqlglot` dependency |
| `tests/unit/test_sql_sandbox.py` | new | 22 tests (AC-2.1 through AC-2.18) |

#### Out of Scope (PH9-owned)

- `GET /scheduling/db-schema` route implementation
- MCP `list_db_tables` / `get_db_row_samples` tools
- MCP `pipeline://db-schema` resource
- 4 schema-discovery security tests

> PH2 delivers `SqlSandbox.DENY_TABLES` as the shared contract. PH9 consumes it for backend filtering.

---

### MEU-PH3: Confirmation & Content Guards

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-3.1 | SendStep raises when `requires_confirmation=True` and no UI confirmation | Spec §9C.3b | PolicyExecutionError |
| AC-3.2 | SendStep proceeds when `has_user_confirmation=True` | Spec §9C.3b | — |
| AC-3.3 | SendStep proceeds when `requires_confirmation=False` + valid approval snapshot | Spec §9C.3c | — |
| AC-3.4 | SendStep rejects opt-out without approval record | Spec §9C.3c | PolicyExecutionError |
| AC-3.5 | SendStep rejects opt-out when content_hash doesn't match approved_hash | Spec §9C.3c | PolicyExecutionError |
| AC-3.6 | FetchStep rejects MIME mismatch | Spec §9C.4c (L415) | SecurityError |
| AC-3.7 | FetchStep rejects body > 5 MB | Spec §9C.4b (L393) | SecurityError |
| AC-3.8 | FetchStep rejects > 5 URLs per step | Spec §9C.4c (L417), L404 | Validation error |
| AC-3.9 | PipelineRunner enforces 10 URLs per policy execution | Spec §9C.4d (L424), Human-approved | Validation error after 10 cumulative fetches |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Confirmation gate | Spec | §9C.3b explicit |
| Approval provenance | Spec + Human-approved | §9C.3c; user directed: reuse PolicyModel fields via ApprovalSnapshot |
| MIME validation | Spec | §9C.4b explicit |
| Body size cap (5 MB) | Spec | §9C.4b L393 explicit |
| Fan-out step cap (5) | Spec | §9C.4b L404 explicit |
| Fan-out policy cap (10) | Spec + Human-approved | §9C.4d L424; user directed: implement in PH3, not deferred |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/pipeline.py` | modify | Add `has_user_confirmation`, `approval_snapshot`, `policy_hash`, `fetch_url_count` to StepContext |
| `packages/core/src/zorivest_core/domain/approval_snapshot.py` | new | `ApprovalSnapshot` frozen dataclass from PolicyModel fields |
| `packages/core/src/zorivest_core/pipeline_steps/send_step.py` | modify | Add `requires_confirmation` + gate + approval provenance check |
| `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py` | modify | MIME validation, 5 MB cap, 5-URL/step cap, increment `context.fetch_url_count` |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modify | Initialize `fetch_url_count=0`; populate `approval_snapshot` from PolicyModel; enforce 10-URL policy cap |
| `tests/unit/test_confirmation_gates.py` | new | 9 tests (AC-3.1 through AC-3.9) |

---

## Out of Scope

- MEU-PH4 through PH10 (later phases)
- Schema-discovery API route and tests (PH9)
- Policy emulator / dry-run mode (PH10)
- `StoreReportStep` write path through sandbox (it writes reports, needs write access — separate design)

---

## BUILD_PLAN.md Audit

This project modifies §9C.1–§9C.6 status. Validation:

```powershell
rg "MEU-PH[123]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt
```

---

## Verification Plan

### 1. MEU-PH1 Tests (9 tests)
```powershell
uv run pytest tests/unit/test_stepcontext_isolation.py -x --tb=short -v *> C:\Temp\zorivest\ph1-tests.txt; Get-Content C:\Temp\zorivest\ph1-tests.txt | Select-Object -Last 40
```

### 2. MEU-PH2 Tests (22 tests)
```powershell
uv run pytest tests/unit/test_sql_sandbox.py -x --tb=short -v *> C:\Temp\zorivest\ph2-tests.txt; Get-Content C:\Temp\zorivest\ph2-tests.txt | Select-Object -Last 40
```

### 3. MEU-PH3 Tests (9 tests)
```powershell
uv run pytest tests/unit/test_confirmation_gates.py -x --tb=short -v *> C:\Temp\zorivest\ph3-tests.txt; Get-Content C:\Temp\zorivest\ph3-tests.txt | Select-Object -Last 40
```

### 4. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40
```

### 5. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 6. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Research References

- [09c-pipeline-security-hardening.md](file:///p:/zorivest/docs/build-plan/09c-pipeline-security-hardening.md) — authoritative spec
- [connection.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/connection.py) — existing SQLCipher fallback pattern
- [models.py:435-448](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L435-L448) — PolicyModel approval fields

---

## Addendum: Ad-Hoc Pipeline Scheduling UX (Session 2026-04-25)

> Unplanned work completed during the PH3 implementation session to resolve user-reported scheduling GUI issues. These are **not MEU-PH1–PH3 scope** — they are GUI-layer fixes.

### B1: Fix 422 on `+ New Policy` Creation
- **Root cause**: Default policy template had `params: {}` for `fetch` step, but `FetchStep.Params` requires `provider` and `data_type`.
- **File**: [SchedulingLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx)
- **Fix**: Added `provider: 'yahoo'` and `data_type: 'ohlcv'` to default step params.

### B2: Segmented State Selector (Draft/Ready/Scheduled)
- **Root cause**: Single cycling pill was confusing — user couldn't directly select the desired state.
- **Files**: [PolicyDetail.tsx](file:///p:/zorivest/ui/src/renderer/src/features/scheduling/PolicyDetail.tsx), [SchedulingLayout.tsx](file:///p:/zorivest/ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx)
- **Fix**: Replaced cycling pill with 3-button segmented selector. Each button directly sets its state on click.

### B3: Rename `+ New` → `+ New Policy`
- **File**: [PolicyList.tsx](file:///p:/zorivest/ui/src/renderer/src/features/scheduling/PolicyList.tsx)

### B4: Themed Delete Modal via Portal
- **Root cause**: Native `window.confirm()` doesn't respect dark theme.
- **File**: [PolicyDetail.tsx](file:///p:/zorivest/ui/src/renderer/src/features/scheduling/PolicyDetail.tsx)
- **Fix**: `createPortal(modal, document.body)` with CSS variable–based inline styles.

### B5: Approval/Scheduling Lifecycle Normalization
- **Root cause**: `approve_policy` auto-enabled scheduling; `patch_schedule` reset approval when `enabled` changed.
- **File**: `packages/core/src/zorivest_core/services/scheduling_service.py`
- **Fix**: Decoupled `enabled` from content hash; treated as operational metadata.

### Standards Added
- **G20**: Themed portaled modals, not native dialogs
- **G21**: Direct selection, not cycling, for segmented state controls
- **G22**: Default templates must satisfy backend validation schemas
