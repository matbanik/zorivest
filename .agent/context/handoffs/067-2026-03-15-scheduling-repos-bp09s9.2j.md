---
meu: 82
slug: scheduling-repos
phase: 9
priority: P1
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 3
tests_added: 18
tests_passing: 18
---

# MEU-82: Scheduling Repositories + UoW Extension

## Scope

Implements 5 repository classes for scheduling infrastructure and extends `SqlAlchemyUnitOfWork` with 5 new attributes (10→15 total repos).

Build plan reference: [09-scheduling.md §9.2j](file:///p:/zorivest/docs/build-plan/09-scheduling.md)

## Feature Intent Contract

### Intent Statement
Data access layer for scheduling entities — CRUD repositories for policies, pipeline runs, reports, fetch cache, and audit logs, integrated into the existing Unit of Work pattern.

### Acceptance Criteria
- AC-1: PolicyRepository with create, get_by_id, get_by_name, list_all (enabled_only filter), update, delete
- AC-2: PipelineRunRepository with create, get_by_id, list_by_policy, list_recent, update_status
- AC-3: PipelineRunRepository.find_zombies returns runs stuck in "running" status
- AC-4: ReportRepository with create, get_by_id, get_versions
- AC-5: FetchCacheRepository with upsert (insert + update), get_cached
- AC-6: FetchCacheRepository.invalidate removes cached entries by provider/data_type
- AC-7: AuditLogRepository with append (insert-only) and list_recent
- AC-8: All repos follow `__init__(self, session: Session)` pattern
- AC-9: UoW creates scheduling repo attributes (policies, pipeline_runs, reports, fetch_cache, audit_log)

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | `tests/unit/test_scheduling_repos.py` | `TestPolicyRepository` (5 tests) |
| AC-2, AC-3 | `tests/unit/test_scheduling_repos.py` | `TestPipelineRunRepository` (5 tests) |
| AC-4 | `tests/unit/test_scheduling_repos.py` | `TestReportRepository` (2 tests) |
| AC-5, AC-6 | `tests/unit/test_scheduling_repos.py` | `TestFetchCacheRepository` (3 tests) |
| AC-7 | `tests/unit/test_scheduling_repos.py` | `TestAuditLogRepository` (1 test) |
| AC-8 | `tests/unit/test_scheduling_repos.py` | `TestSessionPattern` (1 test) |
| AC-9 | `tests/unit/test_scheduling_repos.py` | `TestUnitOfWorkExtension` (1 test, uses real UoW) |

## Design Decisions & Known Risks

- **Decision**: Separate `scheduling_repositories.py` file — **Reasoning**: Existing `repositories.py` has 10 repos (657 lines). Adding 5 more would make it unwieldy; separate file follows single-responsibility principle.
- **Decision**: FetchCacheRepository.upsert uses query-then-update — **Reasoning**: SQLite doesn't support `INSERT ... ON CONFLICT UPDATE` across all column combinations. Query+update is clearer and compatible.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | Created | 5 repository classes |
| `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | Modified | Added 5 scheduling repo imports, attrs, and __enter__ initialization |
| `tests/unit/test_scheduling_repos.py` | Created | 18 tests covering all repos + UoW extension |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest tests/unit/test_scheduling_repos.py -v` | PASS (18/18) | All green |
| `uv run ruff check scheduling_repositories.py` | PASS | 0 errors after removing 3 unused imports |
| `uv run pytest tests/ --tb=no -q` | PASS (1309/1309) | Full regression |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_scheduling_repos.py` (18 tests) | FAIL (module not found) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
