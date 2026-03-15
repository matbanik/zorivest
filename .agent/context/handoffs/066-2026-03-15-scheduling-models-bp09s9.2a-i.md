---
meu: 81
slug: scheduling-models
phase: 9
priority: P1
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 2
tests_added: 18
tests_passing: 18
---

# MEU-81: Scheduling SQLAlchemy Models

## Scope

Implements 9 SQLAlchemy model classes for scheduling/pipeline infrastructure and 3 trigger DDL statements for report versioning and audit log append-only behavior.

Build plan reference: [09-scheduling.md §9.2a–9.2i](file:///p:/zorivest/docs/build-plan/09-scheduling.md)

## Feature Intent Contract

### Intent Statement
Persistent storage schema for pipeline policies, runs, steps, state, reports, fetch cache, and audit logs — the data layer for the scheduling engine.

### Acceptance Criteria
- AC-1: PolicyModel with all spec columns (id, name, schema_version, policy_json, content_hash, enabled, approved, etc.)
- AC-2: PipelineRunModel with FK to policies, status, trigger_type, duration_ms
- AC-3: PipelineStepModel with FK to pipeline_runs, step_id, attempt, output_json
- AC-4: PipelineStateModel with unique (policy_id, key) for persistent state
- AC-5: ReportModel with version, spec_json, format
- AC-6: ReportVersionModel with FK to reports, version trigger
- AC-7: ReportDeliveryModel with FK to reports
- AC-8: FetchCacheModel with unique (provider, data_type, entity_key), TTL
- AC-9: AuditLogModel append-only (no UPDATE/DELETE triggers)

### Negative Cases
- Must NOT: Allow UPDATE on audit_log rows (trigger raises ABORT)
- Must NOT: Allow DELETE on audit_log rows (trigger raises ABORT)

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | `tests/unit/test_scheduling_models.py` | `TestPolicyModel` (2 tests) |
| AC-2 | `tests/unit/test_scheduling_models.py` | `TestPipelineRunModel` (2 tests) |
| AC-3 | `tests/unit/test_scheduling_models.py` | `TestPipelineStepModel` (2 tests) |
| AC-4 | `tests/unit/test_scheduling_models.py` | `TestPipelineStateModel` (2 tests) |
| AC-5 | `tests/unit/test_scheduling_models.py` | `TestReportModel` (2 tests) |
| AC-6 | `tests/unit/test_scheduling_models.py` | `TestReportVersionModel` (1 test) |
| AC-7 | `tests/unit/test_scheduling_models.py` | `TestReportDeliveryModel` (1 test) |
| AC-8 | `tests/unit/test_scheduling_models.py` | `TestFetchCacheModel` (2 tests) |
| AC-9 | `tests/unit/test_scheduling_models.py` | `TestAuditAppendOnlyTriggers` (4 tests) |

## Design Decisions & Known Risks

- **Decision**: Triggers installed via `event.listen(Base.metadata, "after_create")` — **Reasoning**: Follows established precedent from Phase 2 models. Ensures triggers are created alongside tables.
- **Decision**: Raw SQL wrapped in `text()` — **Reasoning**: SQLAlchemy 2.x requires `text()` for `connection.execute()` with raw strings.
- **Decision**: FK enforcement via `PRAGMA foreign_keys=ON` in test fixture — **Reasoning**: SQLite does not enforce FKs by default; explicit per-connection pragma needed.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `packages/infrastructure/src/zorivest_infra/database/models.py` | Modified | Added 9 model classes + `install_scheduling_triggers()` DDL |
| `tests/unit/test_scheduling_models.py` | Created | 18 tests covering all models and triggers |
| `tests/unit/test_models.py` | Modified | Updated expected table count from 21 to 30 |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest tests/unit/test_scheduling_models.py -v` | PASS (18/18) | All green |
| `uv run pytest tests/ --tb=no -q` | PASS (1309/1309) | Full regression |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_scheduling_models.py` (18 tests) | FAIL (models not found) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
