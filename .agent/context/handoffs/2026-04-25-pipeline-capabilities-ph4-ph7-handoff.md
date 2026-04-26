---
project: "2026-04-25-pipeline-capabilities"
meus: ["MEU-PH4", "MEU-PH5", "MEU-PH6", "MEU-PH7"]
conversation: "9986e441-db91-4c7e-ba8f-8c6e0c54b1c2"
date: 2026-04-25
status: "complete_with_blocked_deps"
verbosity: "standard"
---

# Handoff: Pipeline Capabilities PH4–PH7

> **Project:** `2026-04-25-pipeline-capabilities`
> **Spec refs:** [09d §9D.1–9D.5](file:///p:/zorivest/docs/build-plan/09d-pipeline-step-extensions.md), [09e](file:///p:/zorivest/docs/build-plan/09e-template-database.md)
> **Test count:** 19 PH7 + 24 PH6 + 5 PH5 + 8 PH4 = 56 new tests
> **Regression:** 2299 passed, 23 skipped, 0 failed

<!-- CACHE BOUNDARY -->

## MEU-PH4: QueryStep

**Scope:** Read-only SQL execution via `SqlSandbox`.

### Changed Files

- [query_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/query_step.py) — New file
- [test_query_step.py](file:///p:/zorivest/tests/unit/test_query_step.py) — 8 tests
- [__init__.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/__init__.py) — Registration

### Acceptance Criteria

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-4.1 | QueryStep type registered as "query" | ✅ | Registration import in `__init__.py` |
| AC-4.2 | params require `sql` + optional `database` | ✅ | `QueryStepParams` Pydantic model |
| AC-4.3 | Executes via SqlSandbox read-only | ✅ | `sandbox.execute_readonly()` call |
| AC-4.4 | Returns list-of-dicts output | ✅ | `test_query_step_returns_list_of_dicts` |
| AC-4.5 | Empty result returns empty list | ✅ | `test_query_step_empty_result` |
| AC-4.6 | SQL errors propagated as StepExecutionError | ✅ | `test_query_step_sql_error` |
| AC-4.7 | Requires schema_version >= 2 | ✅ | Enforced by model_validator |
| AC-4.8 | Sandbox denies write operations | ✅ | `test_query_step_write_denied` |

---

## MEU-PH5: ComposeStep

**Scope:** Multi-source data merging from predecessor step outputs.

### Changed Files

- [compose_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/compose_step.py) — New file
- [test_compose_step.py](file:///p:/zorivest/tests/unit/test_compose_step.py) — 5 tests
- [__init__.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/__init__.py) — Registration

### Acceptance Criteria

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-5.1 | ComposeStep type registered as "compose" | ✅ | Registration import |
| AC-5.2 | `sources` param: list of SourceDef with step_id + key | ✅ | `ComposeStepParams` model |
| AC-5.3 | Merges multiple step outputs into single dict | ✅ | `test_compose_step_merges_sources` |
| AC-5.4 | Missing source step raises StepExecutionError | ✅ | `test_compose_step_missing_source` |
| AC-5.5 | Requires schema_version >= 2 | ✅ | Enforced by model_validator |

---

## MEU-PH6: EmailTemplateModel + HardenedSandbox + Markdown Sanitization

**Scope:** Template database, secure Jinja2, HTML sanitization.

### Changed Files

- [secure_jinja.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/secure_jinja.py) — New: HardenedSandbox
- [safe_markdown.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/safe_markdown.py) — New: nh3-based sanitization
- [email_template_port.py](file:///p:/zorivest/packages/core/src/zorivest_core/ports/email_template_port.py) — New: port + DTO
- [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py) — EmailTemplateModel added
- [email_template_repository.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/email_template_repository.py) — New: CRUD repo
- [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py) — DB lookup tier
- 4 test files (24 tests total)

### Blocked Item

- **Task 15** (`[B]`): Alembic migration for `email_templates` table. Blocked pending Alembic scaffolding in infrastructure layer. The SQLAlchemy model and in-memory tests are complete.

---

## MEU-PH7: Variables, Assertions, Step-Count Cap, Schema v2

**Scope:** PolicyDocument v2 features.

### Changed Files

- [pipeline.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py) — `variables` field, `enforce_version_features` validator
- [ref_resolver.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/ref_resolver.py) — `{var: name}` resolution
- [transform_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py) — `kind` discriminator + assertions
- [condition_evaluator.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/condition_evaluator.py) — `evaluate_assertion()` static method
- [policy_validator.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/policy_validator.py) — v2 gating, var refs, step cap 20, unused var warnings
- 3 test files (19 tests: 3 variable injection + 4 assertion gates + 12 schema v2)

### Post-Implementation Fixes

- **Pyright fix:** `pipeline.py:163` — replaced unhashable `PolicyStep` set comprehension with `any()` check
- **Ruff fix:** `policy_validator.py:422` — removed dead `_scan_for_var_refs()` reference (F841)

---

## Quality Gates

| Gate | Result |
|------|--------|
| MEU code gate (`validate_codebase.py --scope meu`) | ✅ All 8/8 blocking checks passed |
| Full regression (`pytest tests/`) | ✅ 2299 passed, 23 skipped, 0 failed |
| Pyright | ✅ 0 errors |
| Ruff | ✅ 0 errors |

## Residual Risk

1. **Alembic migration (Task 15):** `[B]` — EmailTemplateModel table creation deferred. In-memory tests pass. Real DB requires migration.
2. **PH8–PH10 remain:** Policy emulator, MCP tools, default template not yet implemented.
