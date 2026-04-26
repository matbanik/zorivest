---
project: "2026-04-25-pipeline-capabilities"
source: "docs/execution/plans/2026-04-25-pipeline-capabilities/implementation-plan.md"
meus: ["MEU-PH4", "MEU-PH5", "MEU-PH6", "MEU-PH7"]
status: "reviewed"
template_version: "2.0"
---

# Task — P2.5c Pipeline Capabilities (PH4–PH7)

> **Project:** `2026-04-25-pipeline-capabilities`
> **Type:** Domain | Infrastructure
> **Estimate:** ~25 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write FIC: `test_query_step.py` (8 tests, AC-4.1–AC-4.8) | coder | `tests/unit/test_query_step.py` | `uv run pytest tests/unit/test_query_step.py -x --tb=short -v *> C:\Temp\zorivest\ph4-red.txt` → 8 FAILED | `[x]` |
| 2 | Implement `query_step.py` (QueryDef, Params, execute) | coder | `packages/core/src/zorivest_core/pipeline_steps/query_step.py` | `uv run pytest tests/unit/test_query_step.py -x --tb=short -v *> C:\Temp\zorivest\ph4-green.txt` → 8 PASSED | `[x]` |
| 3 | Register QueryStep in `__init__.py` | coder | `packages/core/src/zorivest_core/pipeline_steps/__init__.py` | `uv run python -c "from zorivest_core.domain.step_registry import has_step; assert has_step('query')" *> C:\Temp\zorivest\ph4-reg.txt; Get-Content C:\Temp\zorivest\ph4-reg.txt` | `[x]` |
| 4 | PH4 quality gate | tester | Clean pyright + ruff | `uv run pyright packages/core/ *> C:\Temp\zorivest\ph4-pyright.txt; uv run ruff check packages/core/ *> C:\Temp\zorivest\ph4-ruff.txt` | `[x]` |
| 5 | Write FIC: `test_compose_step.py` (5 tests, AC-5.1–AC-5.5) | coder | `tests/unit/test_compose_step.py` | `uv run pytest tests/unit/test_compose_step.py -x --tb=short -v *> C:\Temp\zorivest\ph5-red.txt` → 5 FAILED | `[x]` |
| 6 | Implement `compose_step.py` (SourceDef, Params, execute) | coder | `packages/core/src/zorivest_core/pipeline_steps/compose_step.py` | `uv run pytest tests/unit/test_compose_step.py -x --tb=short -v *> C:\Temp\zorivest\ph5-green.txt` → 5 PASSED | `[x]` |
| 7 | Register ComposeStep in `__init__.py` | coder | `packages/core/src/zorivest_core/pipeline_steps/__init__.py` | `uv run python -c "from zorivest_core.domain.step_registry import has_step; assert has_step('compose')" *> C:\Temp\zorivest\ph5-reg.txt; Get-Content C:\Temp\zorivest\ph5-reg.txt` | `[x]` |
| 8 | PH5 quality gate | tester | Clean pyright + ruff | `uv run pyright packages/core/ *> C:\Temp\zorivest\ph5-pyright.txt; uv run ruff check packages/core/ *> C:\Temp\zorivest\ph5-ruff.txt` | `[x]` |
| 9 | Write FICs: `test_secure_jinja.py` (8), `test_safe_markdown.py` (3), `test_email_template_repository.py` (8), `test_send_step_db_lookup.py` (5) | coder | 4 test files, 24 tests total | `uv run pytest tests/unit/test_secure_jinja.py tests/unit/test_safe_markdown.py tests/unit/test_email_template_repository.py tests/unit/test_send_step_db_lookup.py -x --tb=short -v *> C:\Temp\zorivest\ph6-red.txt` → 24 FAILED | `[x]` |
| 10 | Create core port layer: `ports/__init__.py`, `email_template_port.py` | coder | `EmailTemplatePort` ABC + `EmailTemplateDTO` dataclass | `uv run python -c "from zorivest_core.ports.email_template_port import EmailTemplatePort, EmailTemplateDTO" *> C:\Temp\zorivest\ph6-port.txt; Get-Content C:\Temp\zorivest\ph6-port.txt` | `[x]` |
| 11 | Implement `secure_jinja.py` (HardenedSandbox) | coder | `packages/core/src/zorivest_core/services/secure_jinja.py` | `uv run pytest tests/unit/test_secure_jinja.py -x --tb=short -v *> C:\Temp\zorivest\ph6-jinja.txt` → 8 PASSED | `[x]` |
| 12 | Implement `safe_markdown.py` (nh3 + markdown-it-py) | coder | `packages/core/src/zorivest_core/services/safe_markdown.py` | `uv run pytest tests/unit/test_safe_markdown.py -x --tb=short -v *> C:\Temp\zorivest\ph6-md.txt` → 3 PASSED | `[x]` |
| 13 | Add `EmailTemplateModel` to `models.py` | coder | 12-column SQLAlchemy model | `uv run python -c "from zorivest_infra.database.models import EmailTemplateModel" *> C:\Temp\zorivest\ph6-model.txt; Get-Content C:\Temp\zorivest\ph6-model.txt` | `[x]` |
| 14 | Implement `email_template_repository.py` + UoW property | coder | `EmailTemplateRepository` CRUD + `uow.email_templates` | `uv run pytest tests/unit/test_email_template_repository.py -x --tb=short -v *> C:\Temp\zorivest\ph6-repo.txt` → 8 PASSED | `[x]` |
| 15 | Create Alembic migration for `email_templates` table + seed 2 defaults | coder | `alembic/versions/xxxx_add_email_templates_table.py` | `Test-Path alembic/versions/*email_templates* *> C:\Temp\zorivest\ph6-migration.txt; Get-Content C:\Temp\zorivest\ph6-migration.txt` → True | `[B]` Alembic not scaffolded |
| 16 | Update `send_step.py` `_resolve_body()` with DB tier + template_port injection | coder | DB lookup tier via `context.outputs["template_port"]` | `uv run pytest tests/unit/test_send_step_db_lookup.py -x --tb=short -v *> C:\Temp\zorivest\ph6-send.txt` → 5 PASSED | `[x]` |
| 17 | Add `nh3`, `markdown-it-py` to `packages/core/pyproject.toml` | coder | Dependencies added | `rg "nh3\|markdown-it-py" packages/core/pyproject.toml *> C:\Temp\zorivest\ph6-deps.txt; Get-Content C:\Temp\zorivest\ph6-deps.txt` → 2 matches | `[x]` |
| 18 | PH6 quality gate | tester | 24 tests pass + clean pyright + ruff | `uv run pytest tests/unit/test_secure_jinja.py tests/unit/test_safe_markdown.py tests/unit/test_send_step_db_lookup.py tests/unit/test_email_template_repository.py -x --tb=short -v *> C:\Temp\zorivest\ph6-green.txt` → 24 PASSED | `[x]` |
| 19 | Write FICs: `test_variable_injection.py` (3), `test_assertion_gates.py` (4), `test_schema_v2_migration.py` (11) | coder | 3 test files, 18 tests total | `uv run pytest tests/unit/test_variable_injection.py tests/unit/test_assertion_gates.py tests/unit/test_schema_v2_migration.py -x --tb=short -v *> C:\Temp\zorivest\ph7-red.txt` → 18 FAILED | `[x]` |
| 20 | Modify `pipeline.py`: `variables` field, max_length 10→20, `model_validator`, `extra="forbid"` | coder | PolicyDocument schema v2 | `uv run pytest tests/unit/test_schema_v2_migration.py -x --tb=short -v *> C:\Temp\zorivest\ph7-schema.txt` → partial pass | `[x]` |
| 21 | Modify `ref_resolver.py`: add `{"var": "name"}` resolution | coder | Variable refs resolve to `variables[name]` | `uv run pytest tests/unit/test_variable_injection.py -x --tb=short -v *> C:\Temp\zorivest\ph7-vars.txt` → 3 PASSED | `[x]` |
| 22 | Modify `transform_step.py`: `kind` discriminator + assertions + `_run_assertions()` | coder | Assertion gates in TransformStep | `uv run pytest tests/unit/test_assertion_gates.py -x --tb=short -v *> C:\Temp\zorivest\ph7-assert.txt` → 4 PASSED | `[x]` |
| 23 | Modify `condition_evaluator.py`: add `evaluate_assertion()` static method | coder | Arithmetic + abs() in assertion evaluation | Tests covered by task 22 | `[x]` |
| 24 | Modify `policy_validator.py`: v2 gating, var ref gating, step cap 10→20, unused var warnings | coder | PolicyValidator schema-aware validation | `uv run pytest tests/unit/test_schema_v2_migration.py -x --tb=short -v *> C:\Temp\zorivest\ph7-pv.txt` → 11 PASSED | `[x]` |
| 25 | PH7 quality gate | tester | 19 tests pass + clean pyright + ruff | 19 passed (18 planned + 1 extra), 0 failed | `[x]` |
| 26 | Run MEU gate | tester | All checks pass | 8/8 blocking checks passed (24.45s) | `[x]` |
| 27 | Run full regression | tester | No regressions | 2299 passed, 23 skipped, 0 failed (164.34s) | `[x]` |
| 28 | Update `build-priority-matrix.md` status for PH4–PH7 | orchestrator | Status cells updated | PH4-PH7 not in build-priority-matrix.md; tracked in BUILD_PLAN.md (updated ⬜→✅) | `[x]` |
| 29 | Update `.agent/context/meu-registry.md` for PH4–PH7 | orchestrator | Registry entries updated | PH4-PH7 → ✅ 2026-04-25 | `[x]` |
| 30 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; clean grep | `rg "2026-04-25-pipeline-capabilities"` → 0 matches | `[x]` |
| 31 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-pipeline-capabilities-2026-04-25` | `[B]` pomera MCP server unavailable | `[B]` |
| 32 | Create handoffs (combined PH4–PH7) | reviewer | `.agent/context/handoffs/2026-04-25-pipeline-capabilities-ph4-ph7-handoff.md` | Combined handoff created (1 file covering all 4 MEUs) | `[x]` |
| 33 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-25-pipeline-capabilities-reflection.md` | File created | `[x]` |
| 34 | Append metrics row | orchestrator | Row in `docs/execution/metrics.md` | Row appended for MEU-PH4/PH5/PH6/PH7 | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
