# Scheduling Domain Foundation — MEU-77 + MEU-78 + MEU-79 + MEU-80

> **Project slug:** `2026-03-13-scheduling-domain-foundation`
> **Build plan:** [09-scheduling.md](../../build-plan/09-scheduling.md) §9.1a–9.1g
> **Priority:** P2.5 — Phase 9: Scheduling & Pipeline Engine
> **MEUs:** 77 → 78 → 79 → 80 (dependency order)

## Overview

Build the pure-domain foundation for the scheduling & pipeline engine. These 4 MEUs create the enums, Pydantic models, step type registry, and policy validation module that all later Phase 9 MEUs depend on. No infrastructure, API, or MCP changes — all code lives in `packages/core/`.

---

## User Review Required

> [!IMPORTANT]
> **New dependencies:** `apscheduler` and `structlog` must be added to `zorivest-core`. Both are Phase 9 core deps per the [dependency manifest](../../build-plan/dependency-manifest.md) line 61.

> [!WARNING]
> **BUILD_PLAN.md stale count.** P2 row shows `Completed: 2` but MEU-66, 67, 68, 69 are all ✅ approved. Will fix to `4` as part of this project's BUILD_PLAN.md maintenance task.

---

## Spec Sufficiency Gate

### MEU-77: pipeline-enums

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| PipelineStatus enum (6 members) | Spec | [09-scheduling §9.1a](../../build-plan/09-scheduling.md) | ✅ |
| StepErrorMode enum (3 members) | Spec | [09-scheduling §9.1b](../../build-plan/09-scheduling.md) | ✅ |
| DataType enum (4 members) | Spec | [09-scheduling §9.4a](../../build-plan/09-scheduling.md) FetchStep.Params.data_type (line 1384) | ✅ |
| Use StrEnum (not str, Enum) | Local Canon | [enums.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py) pattern | ✅ |

### MEU-78: policy-models

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| RefValue Pydantic model | Spec | [09-scheduling §9.1c](../../build-plan/09-scheduling.md) | ✅ |
| RetryConfig model | Spec | §9.1c | ✅ |
| SkipConditionOperator enum (10 operators) | Spec | §9.1c | ✅ |
| SkipCondition model | Spec | §9.1c | ✅ |
| PolicyStep model (id, type, params, timeout, retry, on_error, skip_if, required) | Spec | §9.1c | ✅ |
| TriggerConfig model (cron, tz, enabled, misfire, coalesce, max_instances) | Spec | §9.1c | ✅ |
| PolicyMetadata model | Spec | §9.1c | ✅ |
| PolicyDocument model (schema_version, name, metadata, trigger, steps) | Spec | §9.1c | ✅ |
| unique_step_ids validator | Spec | §9.1c | ✅ |
| StepContext dataclass (run_id, policy_id, outputs, dry_run, logger) | Spec | §9.1d | ✅ |
| StepResult dataclass (status, output, error, timestamps, duration) | Spec | §9.1d | ✅ |
| StepContext.logger uses structlog.BoundLogger | Spec | §9.1d + dependency-manifest.md line 61 | ✅ |

### MEU-79: step-registry

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| StepBase Protocol (runtime_checkable, type_name, side_effects, execute, params_schema, compensate) | Spec | [09-scheduling §9.1e](../../build-plan/09-scheduling.md) | ✅ |
| RegisteredStep base class with __init_subclass__ auto-registration | Spec | §9.1f | ✅ |
| STEP_REGISTRY module-level dict | Spec | §9.1f | ✅ |
| get_step, has_step, list_steps, get_all_steps helper functions | Spec | §9.1f + §9.5 line 2598 | ✅ |
| Duplicate type_name raises ValueError | Spec | §9.1f | ✅ |

### MEU-80: policy-validator

| Behavior | Source Type | Source | Resolved? |
|---|---|---|---|
| ValidationError dataclass (field, message, severity) | Spec | [09-scheduling §9.1g](../../build-plan/09-scheduling.md) | ✅ |
| validate_policy() → list[ValidationError] | Spec | §9.1g | ✅ |
| Rule 1: schema_version check | Spec | §9.1g | ✅ |
| Rule 2: step count limit (≤10) | Spec | §9.1g | ✅ |
| Rule 3: step types exist in registry | Spec | §9.1g | ✅ |
| Rule 4: referential integrity (refs → prior steps) | Spec | §9.1g | ✅ |
| Rule 5: cron expression validation (APScheduler) | Spec | §9.1g | ✅ |
| Rule 6: SQL blocklist check | Spec | §9.1g | ✅ |
| Rule 7: unique step IDs (Pydantic validator) | Spec | §9.1c | ✅ |
| Rule 8: content hash computation (SHA-256) | Spec | §9.1g | ✅ |
| compute_content_hash() | Spec | §9.1g | ✅ |
| _check_refs() recursive walker | Spec | §9.1g | ✅ |
| _check_sql_blocklist() recursive scanner | Spec | §9.1g | ✅ |
| SQL_BLOCKLIST constant | Spec | §9.1g | ✅ |

---

## Proposed Changes

### MEU-77: Pipeline Enums

#### [MODIFY] [enums.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py)

Append 3 new StrEnum classes after the existing enums:

- **PipelineStatus** — `pending`, `running`, `success`, `failed`, `skipped`, `cancelled`
- **StepErrorMode** — `fail_pipeline`, `log_and_continue`, `retry_then_fail`
- **DataType** — `quote`, `ohlcv`, `news`, `fundamentals`

#### [NEW] [test_pipeline_enums.py](file:///p:/zorivest/tests/unit/test_pipeline_enums.py)

Test enum membership, string values, StrEnum subclassing.

---

### MEU-78: Policy Pydantic Models

#### [NEW] [pipeline.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py)

Create the pipeline domain module with:
- `RefValue` — pattern-validated ref string
- `RetryConfig` — max_attempts, backoff, jitter
- `SkipConditionOperator` — 10-member StrEnum
- `SkipCondition` — field + operator + value
- `PolicyStep` — step definition with id constraints, timeout, retry, skip_if
- `TriggerConfig` — cron + scheduling params
- `PolicyMetadata` — author, timestamps, description
- `PolicyDocument` — root model with unique_step_ids validator
- `StepContext` — mutable execution context (dataclass, uses `structlog.BoundLogger`)
- `StepResult` — step output (dataclass)

#### [NEW] [test_pipeline_models.py](file:///p:/zorivest/tests/unit/test_pipeline_models.py)

Tests for every model's construction, validation, edge cases.

---

### MEU-79: Step Type Registry

#### [NEW] [step_registry.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/step_registry.py)

- `STEP_REGISTRY` dict
- `RegisteredStep` base class with `__init_subclass__` auto-registration
- `get_step()`, `has_step()`, `list_steps()`, `get_all_steps()` helpers
- `get_all_steps()` returns registered step classes (for REST API §9.5 line 2598 attribute access); `list_steps()` returns serialized dicts for MCP
- Duplicate name detection with `ValueError`

#### [NEW] [test_step_registry.py](file:///p:/zorivest/tests/unit/test_step_registry.py)

Auto-registration, duplicate detection, helpers, base class contracts.

---

### MEU-80: Policy Validator

#### [NEW] [policy_validator.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/policy_validator.py)

- `ValidationError` dataclass
- `SQL_BLOCKLIST` constant
- `validate_policy()` — 6 explicit rules
- `compute_content_hash()` — SHA-256
- `_validate_cron()` — APScheduler parser
- `_check_refs()` — recursive ref walker
- `_check_sql_blocklist()` — recursive scanner

#### [NEW] [test_policy_validator.py](file:///p:/zorivest/tests/unit/test_policy_validator.py)

All 8 validation rules, hash determinism, recursive scanning.

---

### BUILD_PLAN.md Maintenance

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Fix P2 completed count: `2` → `4` (MEU-66, 67, 68, 69 all ✅)
- Update Phase 9 status: `⚪ Not Started` → `🟡 In Progress`
- Update MEU-77–80 status in the P2.5 table as they complete
- Update P2.5 completed count

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Install `apscheduler` + `structlog` for core | coder | `pyproject.toml` updated | `uv sync` succeeds + `rg "apscheduler|structlog" packages/core/pyproject.toml` shows both | ⬜ |
| 2 | MEU-77: Pipeline enums | coder | `enums.py` + test | `uv run pytest tests/unit/test_pipeline_enums.py -v` | ⬜ |
| 3 | MEU-78: Policy models | coder | `pipeline.py` + test | `uv run pytest tests/unit/test_pipeline_models.py -v` | ⬜ |
| 4 | MEU-79: Step registry | coder | `step_registry.py` + test | `uv run pytest tests/unit/test_step_registry.py -v` | ⬜ |
| 5 | MEU-80: Policy validator | coder | `policy_validator.py` + test | `uv run pytest tests/unit/test_policy_validator.py -v` | ⬜ |
| 6 | BUILD_PLAN.md maintenance | coder | P2 count fix, Phase 9 status | Visual inspection | ⬜ |
| 7 | Consolidated handoff | coder | 1 handoff file (060) | Template completeness | ⬜ |
| 8 | MEU gate | tester | `uv run python tools/validate_codebase.py --scope meu` | Exit code 0 | ⬜ |
| 9 | Registry update | coder | `meu-registry.md` 4 new rows | Cross-check with BUILD_PLAN | ⬜ |
| 10 | Reflection | coder | `docs/execution/reflections/` | Complete | ⬜ |
| 11 | Metrics | coder | `docs/execution/metrics.md` row | Complete | ⬜ |
| 12 | Pomera session save | coder | pomera_notes entry | Note ID returned | ⬜ |
| 13 | Commit messages | coder | Proposed commit list | Presented to human | ⬜ |

---

## Feature Intent Contracts

### FIC: MEU-77 — Pipeline Enums

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `PipelineStatus` is a `StrEnum` with 6 members: `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `SKIPPED`, `CANCELLED` | Spec §9.1a |
| AC-2 | `StepErrorMode` is a `StrEnum` with 3 members: `FAIL_PIPELINE`, `LOG_AND_CONTINUE`, `RETRY_THEN_FAIL` | Spec §9.1b |
| AC-3 | `DataType` is a `StrEnum` with 4 members: `QUOTE`, `OHLCV`, `NEWS`, `FUNDAMENTALS` | Spec §9.4a line 1384 |
| AC-4 | All 3 enums live in `enums.py` consistent with existing enum patterns | Local Canon |
| AC-5 | String values use snake_case lowercase | Spec §9.1a–b |

### FIC: MEU-78 — Policy Models

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `RefValue.ref` validates pattern `^ctx\.\w+(\.\w+)*$` | Spec §9.1c |
| AC-2 | `RetryConfig.max_attempts` constrained `ge=1, le=10`, default 3 | Spec §9.1c |
| AC-3 | `SkipConditionOperator` has 10 members (`eq` through `is_not_null`) | Spec §9.1c |
| AC-4 | `PolicyStep.id` validates pattern `^[a-z][a-z0-9_]*$`, length 1–64 | Spec §9.1c |
| AC-5 | `PolicyStep.timeout` constrained `ge=10, le=3600`, default 300 | Spec §9.1c |
| AC-6 | `TriggerConfig.misfire_grace_time` constrained `ge=60, le=86400` | Spec §9.1c |
| AC-7 | `PolicyDocument.steps` must have 1–10 items | Spec §9.1c |
| AC-8 | `PolicyDocument.unique_step_ids` validator rejects duplicate IDs | Spec §9.1c |
| AC-9 | `StepContext.get_output()` raises `KeyError` for missing step_id | Spec §9.1d |
| AC-10 | `StepResult` defaults: empty output dict, None error, 0 duration | Spec §9.1d |
| AC-11 | `StepContext.logger` uses `structlog.BoundLogger` (per spec §9.1d) | Spec |

### FIC: MEU-79 — Step Registry

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `RegisteredStep` subclasses auto-register via `__init_subclass__` | Spec §9.1f |
| AC-2 | Duplicate `type_name` raises `ValueError` | Spec §9.1f |
| AC-3 | `get_step()` returns class or None | Spec §9.1f |
| AC-4 | `has_step()` returns bool | Spec §9.1f |
| AC-5 | `list_steps()` returns list of dicts with `type_name`, `side_effects`, `params_schema` | Spec §9.1f |
| AC-6 | Base `execute()` raises `NotImplementedError` | Spec §9.1f |
| AC-6b | `NotImplementedError` line tagged with `# noqa: placeholder` to pass anti-placeholder gate | Local Canon (`validate_codebase.py` `_scan_check.exclude_comment`) |
| AC-7 | Default `compensate()` is a no-op (no exception) | Spec §9.1f |
| AC-8 | `params_schema()` returns JSON schema if `Params` class exists, else empty dict | Spec §9.1f |
| AC-9 | `StepBase` Protocol is `@runtime_checkable` | Spec §9.1e |
| AC-10 | `get_all_steps()` returns step classes (not `list_steps()` dicts) for §9.5 attribute access | Spec §9.5 line 2598 |

### FIC: MEU-80 — Policy Validator

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `validate_policy()` returns empty list for valid policy | Spec §9.1g |
| AC-2 | Rejects unsupported schema_version (≠ 1) | Spec §9.1g |
| AC-3 | Rejects >10 steps | Spec §9.1g |
| AC-4 | Rejects unknown step types (not in STEP_REGISTRY) | Spec §9.1g |
| AC-5 | Rejects forward references (ref to step not yet seen) | Spec §9.1g |
| AC-6 | Rejects invalid cron expressions (validated via APScheduler) | Spec §9.1g |
| AC-7 | Detects SQL blocklist keywords in step params (recursive scan) | Spec §9.1g |
| AC-8 | `compute_content_hash()` returns deterministic SHA-256 | Spec §9.1g |
| AC-9 | `SQL_BLOCKLIST` contains: DROP, DELETE, UPDATE, INSERT, ALTER, ATTACH, PRAGMA, CREATE | Spec §9.1g |
| AC-10 | Nested dict/list values in params are recursively scanned for SQL | Spec §9.1g |

---

## Verification Plan

### Automated Tests

Each MEU's test file validates all acceptance criteria:

```bash
# Per-MEU tests
uv run pytest tests/unit/test_pipeline_enums.py -v
uv run pytest tests/unit/test_pipeline_models.py -v
uv run pytest tests/unit/test_step_registry.py -v
uv run pytest tests/unit/test_policy_validator.py -v

# Full regression (1020+ existing tests must pass)
uv run pytest tests/ -v

# Type checking
uv run pyright packages/core/src/zorivest_core/domain/pipeline.py packages/core/src/zorivest_core/domain/step_registry.py packages/core/src/zorivest_core/domain/policy_validator.py packages/core/src/zorivest_core/domain/enums.py

# Anti-placeholder scan (real gate with exclusion — raw rg is advisory only)
uv run python tools/validate_codebase.py --scope meu
# Advisory raw grep (will show the excluded base-class line, which is expected):
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/pipeline.py packages/core/src/zorivest_core/domain/step_registry.py packages/core/src/zorivest_core/domain/policy_validator.py
```

### MEU Gate

```bash
uv run python tools/validate_codebase.py --scope meu
```

### Handoff Naming

All 4 MEUs consolidated into a single handoff:

| MEUs | Handoff File |
|------|-------------|
| MEU-77–80 | `060-2026-03-13-scheduling-domain-foundation-bp09s9.1.md` |
