# Test Rigor Audit — Task List

**Project**: Full test suite IR-5 rigor audit
**Plan**: [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-03-16-test-rigor-audit/implementation-plan.md)
**Reviewer**: Codex validation agent
**Date**: 2026-03-16

---

## Tasks

- [ ] **Task 1**: Audit API route tests (16 files) — rate each test 🟢/🟡/🔴
  - Files: `tests/unit/test_api_*.py`, `test_api_key_encryption.py`
  - Deliverable: Per-test rating table
  - Owner: `reviewer`

- [ ] **Task 2**: Audit domain model tests (8+ files) — rate each test 🟢/🟡/🔴
  - Files: `test_entities.py`, `test_enums.py`, `test_events.py`, `test_exceptions.py`, `test_calculator.py`, `test_analytics.py`, `test_account_review.py`
  - Deliverable: Per-test rating table
  - Owner: `reviewer`

- [ ] **Task 3**: Audit service layer tests (10+ files) — rate each test 🟢/🟡/🔴
  - Files: `test_trade_service.py`, `test_account_service.py`, `test_image_service.py`, `test_system_service.py`, `test_settings_*.py`, `test_report_service.py`, `test_plan_service.py`, `test_watchlist_service.py`, `test_provider_connection_service.py`
  - Deliverable: Per-test rating table
  - Owner: `reviewer`

- [ ] **Task 4**: Audit infra & pipeline tests (15+ files) — rate each test 🟢/🟡/🔴
  - Files: `test_backup_manager.py`, `test_log_redaction.py`, `test_csv_import.py`, `test_ibkr_flexquery.py`, `test_pipeline_runner.py`, `test_policy_validator.py`, `test_step_registry.py`, `test_pydantic_models.py`, `test_ref_resolver.py`, `test_logging_service.py`, remaining unit files
  - Deliverable: Per-test rating table
  - Owner: `reviewer`

- [ ] **Task 5**: Audit integration tests (6 files) — rate each test 🟢/🟡/🔴
  - Files: `test_backup_integration.py`, `test_backup_recovery_integration.py`, `test_database_connection.py`, `test_repositories.py`, `test_unit_of_work.py`, `test_wal_concurrency.py`
  - Deliverable: Per-test rating table
  - Owner: `reviewer`

- [ ] **Task 6**: Synthesize findings into summary report
  - Aggregate all ratings, identify files with 🔴 ratings, recommend fixes
  - Write review handoff to `.agent/context/handoffs/2026-03-16-test-rigor-audit-critical-review.md`
  - Deliverable: Summary report with verdict
  - Owner: `reviewer`

---

## Handoff

- Create review handoff: `.agent/context/handoffs/2026-03-16-test-rigor-audit-critical-review.md`

## Baseline Commands (run first)

```powershell
# Confirm all tests pass
uv run pytest tests/ -x --tb=short -q

# Get test counts per file
uv run pytest tests/ --co -q

# Search for common weakness patterns
rg "hasattr\(" tests/ --count
rg "assert_called_once\(\)" tests/ --count
rg "assert.*> 0" tests/ --count
```
