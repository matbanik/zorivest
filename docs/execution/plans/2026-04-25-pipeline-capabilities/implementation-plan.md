---
project: "2026-04-25-pipeline-capabilities"
date: "2026-04-25"
source: "docs/build-plan/09d-pipeline-step-extensions.md, docs/build-plan/09e-template-database.md"
meus: ["MEU-PH4", "MEU-PH5", "MEU-PH6", "MEU-PH7"]
status: "reviewed"
template_version: "2.0"
---

# Implementation Plan: P2.5c Pipeline Capabilities (PH4–PH7)

> **Project**: `2026-04-25-pipeline-capabilities`
> **Build Plan Section(s)**: §9D.1–§9D.6 (09d), §9E.1–§9E.5 (09e)
> **Status**: `reviewed`

---

## Goal

Extend the pipeline engine with two new step types (QueryStep, ComposeStep), a database-backed email template system with Jinja2 security hardening and Markdown sanitization, and schema v2 migration with variable injection, assertion gates, and a 20-step cap. These capabilities unblock the Policy Emulator (PH8) and MCP template CRUD tools (PH9).

---

## User Review Required

> [!IMPORTANT]
> **Dependency chain (Spec):** PH4 depends on PH2 (SqlSandbox ✅). PH5 has no internal deps. PH6 is independent but logically ordered after PH5. PH7 depends on PH4/PH5 being registered so the `model_validator` can correctly gate `query`/`compose` types. Execution order: PH4 → PH5 → PH6 → PH7.

> [!IMPORTANT]
> **New dependencies (Spec §9E.4a):** PH6 requires `nh3` (~0.5 MB, Rust-based HTML sanitizer) and `markdown-it-py` (~0.3 MB). Both will be added to `packages/core/pyproject.toml`.

> [!IMPORTANT]
> **Step-count cap change (Spec §9D.5b):** `PolicyDocument.steps` max_length changes from 10 → 20. No existing policies should be affected (development stage), but this is a schema-level change.

> [!IMPORTANT]
> **Ports directory creation (Spec §9E.1e):** PH6 creates `packages/core/src/zorivest_core/ports/` — a new architectural boundary. Core port → infra implementation follows the existing domain → infra dependency rule.

---

## Proposed Changes

### MEU-PH4: QueryStep Implementation

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| PolicyDocument JSON → PolicyStep.params | `QueryStep.Params` (Pydantic) | `queries`: list[QueryDef] max 5; `row_limit`: int le=5000; `output_key`: str | `extra="forbid"` |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-4.1 | Simple SELECT returns rows as list of dicts | Spec §9D.1b | — |
| AC-4.2 | Row limit enforced: >row_limit rows truncated | Spec §9D.1b | Excess rows silently capped |
| AC-4.3 | Named `:param` binds resolve correctly | Spec §9D.1b | — |
| AC-4.4 | `{"ref": "ctx.step_id.field"}` in binds resolves via RefResolver | Spec §9D.1b | Invalid ref raises KeyError |
| AC-4.5 | Multiple queries return merged dict keyed by query name | Spec §9D.1c | — |
| AC-4.6 | Output shape compatible with TransformStep auto-discovery | Spec §9D.1d | — |
| AC-4.7 | >5 queries per step raises Pydantic validation error | Spec §9D.1b | Fan-out cap exceeded |
| AC-4.8 | All SQL routed through SqlSandbox (not raw connection) | Spec §9D.1b | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| RegisteredStep pattern | Spec | §9D.1b "Follows RegisteredStep pattern" |
| SqlSandbox integration | Spec | §9D.1b "sandbox = context.outputs['sql_sandbox']" |
| QueryDef model shape | Spec | §9D.1b code example: `{name, sql, binds}` |
| Fan-out cap (5/step) | Spec | §9D.1b constraints table |
| Row limit default/max | Spec | §9D.1b `row_limit: int = Field(default=1000, le=5000)` |
| Ref support in binds | Spec | §9D.1b constraints "binds values can be {ref}" |
| SqlSandbox injection | Local Canon | PH2 delivers sandbox via `context.outputs["sql_sandbox"]` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/pipeline_steps/query_step.py` | new | QueryStep + QueryDef + Params models |
| `packages/core/src/zorivest_core/pipeline_steps/__init__.py` | modify | Import QueryStep for auto-registration |
| `tests/unit/test_query_step.py` | new | 8 tests (AC-4.1 through AC-4.8) |

---

### MEU-PH5: ComposeStep Implementation

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| PolicyDocument JSON → PolicyStep.params | `ComposeStep.Params` (Pydantic) | `sources`: list[SourceDef]; `merge_strategy`: Literal["dict_merge","array_concat"]; `output_key`: str | `extra="forbid"` |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-5.1 | Multiple sources merged into single dict via `dict_merge` | Spec §9D.2b | — |
| AC-5.2 | Lists from multiple sources concatenated via `array_concat` | Spec §9D.2b | — |
| AC-5.3 | Source renamed via `rename` field | Spec §9D.2c | — |
| AC-5.4 | Non-existent `step_id` raises `KeyError` | Spec §9D.2c | Missing step_id |
| AC-5.5 | Composed output is deep-copy isolated from source | Spec §9D.2c, Local Canon §9C.1b | Mutation after compose doesn't affect source |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| RegisteredStep pattern | Spec | §9D.2b "Follows RegisteredStep pattern" |
| SourceDef model shape | Spec | §9D.2b code example: `{step_id, key, rename?}` |
| dict_merge strategy | Spec | §9D.2b code: `merged[target_key] = data` |
| array_concat strategy | Spec | §9D.2b code: `merged.setdefault("items", []).extend(...)` |
| Deep-copy isolation | Local Canon | §9C.1b via `context.get_output()` returns deep copies |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/pipeline_steps/compose_step.py` | new | ComposeStep + SourceDef + Params models |
| `packages/core/src/zorivest_core/pipeline_steps/__init__.py` | modify | Import ComposeStep for auto-registration |
| `tests/unit/test_compose_step.py` | new | 5 tests (AC-5.1 through AC-5.5) |

---

### MEU-PH6: EmailTemplateModel + HardenedSandbox + Markdown Sanitization

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Internal: `EmailTemplateRepository.create()` | `EmailTemplateModel` (SQLAlchemy) | `name`: unique, max 128; `body_html`: not null; `body_format`: "html"\|"markdown" | Model-level constraints |
| Internal: `EmailTemplatePort.get_by_name()` | `EmailTemplateDTO` (frozen dataclass) | Read-only projection | No external write surface |
| Future (PH9): REST POST/PATCH | `EmailTemplateCreateRequest`/`UpdateRequest` | Documented in §9E.0 | `extra="forbid"` — deferred to PH9 |

> [!NOTE]
> PH6 creates the domain port, infra repository, and security services. External-facing REST/MCP surfaces are PH9 scope. The boundary inventory above documents the internal API contracts that PH9 will consume.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-6.1 | `EmailTemplateModel` has 12 columns per §9E.1c schema | Spec §9E.1c | — |
| AC-6.2 | `EmailTemplateRepository` CRUD: create, get_by_name, list_all, update, delete | Spec §9E.2a | — |
| AC-6.3 | `EmailTemplateRepository.delete()` rejects default templates (`is_default=True`) | Spec §9E.2a | ValueError on delete default |
| AC-6.4 | `EmailTemplatePort` ABC with `get_by_name()` and `list_all()` in core | Spec §9E.1e | — |
| AC-6.5 | `EmailTemplateDTO` frozen dataclass matches port contract | Spec §9E.1e | — |
| AC-6.6 | `SqlAlchemyUnitOfWork` has `email_templates` property | Spec §9E.2b | — |
| AC-6.7 | `HardenedSandbox` basic template renders correctly | Spec §9E.3b | — |
| AC-6.8 | `HardenedSandbox` allowed filter works (e.g., `upper`) | Spec §9E.3b | — |
| AC-6.9 | `HardenedSandbox` blocked filter raises `SecurityException` | Spec §9E.3c | Disallowed filter |
| AC-6.10 | `HardenedSandbox` blocks `__class__.__mro__` traversal | Spec §9E.3c | SSTI via MRO |
| AC-6.11 | `HardenedSandbox` blocks `__init__.__globals__` access | Spec §9E.3c | SSTI via globals |
| AC-6.12 | `HardenedSandbox` rejects >64 KiB source | Spec §9E.3b | SecurityError |
| AC-6.13 | `HardenedSandbox` rejects >256 KiB rendered output | Spec §9E.3b | SecurityError |
| AC-6.14 | `HardenedSandbox` strips callable values from context | Spec §9E.3b | Callable not passed through |
| AC-6.15 | `safe_render_markdown()` converts Markdown → HTML | Spec §9E.4a | — |
| AC-6.16 | `safe_render_markdown()` strips `<script>` tags | Spec §9E.4b | XSS injection removed |
| AC-6.17 | `safe_render_markdown()` preserves safe tags (`<strong>`, `<em>`, `<a>`) | Spec §9E.4b | — |
| AC-6.18 | `SendStep._resolve_body()` checks DB before hardcoded registry | Spec §9E.5a | — |
| AC-6.19 | `SendStep._resolve_body()` falls through to registry on DB miss | Spec §9E.5b | — |
| AC-6.20 | `SendStep._resolve_body()` renders inline templates via HardenedSandbox | Spec §9E.5b | — |
| AC-6.21 | Alembic migration creates `email_templates` table with 12 columns | Spec §9E.1d | — |
| AC-6.22 | Migration seeds 2 default templates from `EMAIL_TEMPLATES` dict | Spec §9E.1d | — |
| AC-6.23 | `SendStep` resolves template from `context.outputs["template_port"]` when available | Spec §9E.5a, Local Canon | — |
| AC-6.24 | `SendStep` falls through gracefully when `template_port` is `None` | Local Canon | Port unavailable → skip DB tier |
| AC-6.25 | No core→infra import in `send_step.py`; port injected via `StepContext` | Local Canon (dependency rule) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| EmailTemplateModel schema | Spec | §9E.1c explicit 12-column definition |
| Repository CRUD pattern | Spec | §9E.2a code example |
| Delete-default guard | Spec | §9E.2a `if template.is_default: raise ValueError` |
| Core port + DTO | Spec | §9E.1e explicit code example |
| UoW integration | Spec | §9E.2b "Add email_templates to SqlAlchemyUnitOfWork" |
| HardenedSandbox design | Spec | §9E.3b complete code example |
| Filter allowlist | Spec | §9E.3b `ALLOWED_FILTERS` frozenset |
| Attribute deny-list | Spec | §9E.3b `_DENY_ATTRS` frozenset |
| Size caps (64 KiB / 256 KiB) | Spec | §9E.3b MAX_TEMPLATE_BYTES / MAX_OUTPUT_BYTES |
| Markdown sanitization | Spec | §9E.4a `nh3.clean()` + `markdown_it` |
| SendStep resolution chain | Spec | §9E.5a 5-tier priority chain |
| Alembic migration for table | Spec | §9E.1d "New migration: alembic/versions/xxxx_add_email_templates_table.py" |
| Default template seeding | Spec | §9E.1d "Seeds 2 default templates migrated from EMAIL_TEMPLATES dict" |
| Template port injection | Local Canon | Core→infra dependency rule; port injected via `context.outputs` |
| nh3 + markdown-it-py deps | Spec | §9E.4a "New dependencies" |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/ports/__init__.py` | new | Empty init for ports package |
| `packages/core/src/zorivest_core/ports/email_template_port.py` | new | `EmailTemplatePort` ABC + `EmailTemplateDTO` frozen dataclass |
| `packages/core/src/zorivest_core/services/secure_jinja.py` | new | `HardenedSandbox` extending `ImmutableSandboxedEnvironment` |
| `packages/core/src/zorivest_core/services/safe_markdown.py` | new | `safe_render_markdown()` via `nh3` + `markdown-it-py` |
| `packages/infrastructure/src/zorivest_infra/database/models.py` | modify | Add `EmailTemplateModel` class |
| `packages/infrastructure/src/zorivest_infra/persistence/email_template_repository.py` | new | `EmailTemplateRepository` with CRUD |
| `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | modify | Add `email_templates` property |
| `packages/core/src/zorivest_core/pipeline_steps/send_step.py` | modify | Update `_resolve_body()` to add DB lookup tier (Tier 2); inject port via `context.outputs["template_port"]` |
| `packages/core/pyproject.toml` | modify | Add `nh3`, `markdown-it-py` dependencies |
| `alembic/versions/xxxx_add_email_templates_table.py` | new | Creates `email_templates` table + seeds 2 defaults from `EMAIL_TEMPLATES` |
| `tests/unit/test_secure_jinja.py` | new | 8 tests (AC-6.7 through AC-6.14) |
| `tests/unit/test_safe_markdown.py` | new | 3 tests (AC-6.15 through AC-6.17) |
| `tests/unit/test_send_step_db_lookup.py` | new | 5 tests (AC-6.18 through AC-6.20, AC-6.23 through AC-6.25) |
| `tests/unit/test_email_template_repository.py` | new | 8 tests (AC-6.1 through AC-6.6, AC-6.21 through AC-6.22) |

#### Template Port Injection Design

> Source: Local Canon (core→infra dependency rule), Spec §9E.5a (resolution chain)

**Problem:** `SendStep` (core) needs `EmailTemplatePort` (core port) backed by `EmailTemplateRepository` (infra). Core must not import infra.

**Solution:** `PipelineRunner` injects the port into `StepContext` at pipeline start:

```python
# PipelineRunner (infra layer) — at pipeline start:
context.outputs["template_port"] = uow.email_templates  # EmailTemplateRepository implements EmailTemplatePort

# SendStep._resolve_body() (core layer):
template_port: EmailTemplatePort | None = context.outputs.get("template_port")
if template_port and p.body_template:
    dto = template_port.get_by_name(p.body_template)
    if dto:
        return sandbox.render_safe(dto.body_source, render_ctx)
# ... fall through to hardcoded registry ...
```

**Fallback:** When `template_port` is `None` (e.g., in unit tests or pre-migration environments), the DB tier is silently skipped and resolution falls through to the hardcoded registry (Tier 3). No error, no log spam.

---

### MEU-PH7: Variables, Assertions, Step-Count Cap, Schema v2 Migration

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| PolicyDocument JSON | `PolicyDocument` (Pydantic) | `schema_version`: 1\|2; `variables`: dict; `steps`: max_length=20 | `extra="forbid"` — Source: AGENTS.md boundary input contract |
| TransformStep params | `TransformStep.Params` (Pydantic) | `kind`: Literal["transform","assertion"]; `assertions`: list[AssertionDef]\|None | `extra="forbid"` (existing) |
| RefResolver params | `RefResolver._walk()` | `{"var": "name"}` pattern alongside `{"ref": ...}` | — |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-7.1 | `{"var": "threshold"}` resolves to `variables["threshold"]` | Spec §9D.3c | — |
| AC-7.2 | Undefined variable raises `ValueError` | Spec §9D.3c | Unknown var name |
| AC-7.3 | Variable reference in QueryStep binds resolves correctly | Spec §9D.3c | — |
| AC-7.4 | Assertion passes → `SUCCESS` status | Spec §9D.4c | — |
| AC-7.5 | Fatal assertion failure → `FAILED` status + halts pipeline | Spec §9D.4c | Fatal severity |
| AC-7.6 | Non-fatal assertion failure → `SUCCESS` with warnings | Spec §9D.4c | Warning severity |
| AC-7.7 | ConditionEvaluator supports `abs()` and arithmetic in assertions | Spec §9D.4c | — |
| AC-7.8 | Policy with 20 steps validates | Spec §9D.5c | — |
| AC-7.9 | Policy with 21 steps raises `ValidationError` | Spec §9D.5c | Exceeds 20-step cap |
| AC-7.10 | v1 policy with no v2 features still validates | Spec §9D.6c | — |
| AC-7.11 | `variables` or `query` step with `schema_version: 1` raises `ValidationError` | Spec §9D.6c | v2 feature on v1 schema |
| AC-7.12 | Same features with `schema_version: 2` pass validation | Spec §9D.6c | — |
| AC-7.13 | `PolicyValidator` allows `query`/`compose` step types on v2 policies | Spec §9D.6b | — |
| AC-7.14 | `PolicyValidator` rejects `query`/`compose` step types on v1 policies | Spec §9D.6b | v1 + query → error |
| AC-7.15 | `PolicyValidator` rejects `{"var": ...}` refs on v1 policies | Spec §9D.6b | v1 + var ref → error |
| AC-7.16 | `PolicyValidator` warns on unused variables in v2 policies | Spec §9D.6b | Warning, not error |
| AC-7.17 | `PolicyValidator` step-count cap updated from 10 → 20 | Spec §9D.5b | — |
| AC-7.18 | `PolicyDocument` rejects unknown top-level fields (`extra="forbid"`) | AGENTS.md boundary input contract | Unknown field → ValidationError |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Variable injection | Spec | §9D.3b code example |
| RefResolver var support | Spec | §9D.3b `_resolve_var()` method |
| Assertion discriminator | Spec | §9D.4b `kind: Literal["transform", "assertion"]` |
| AssertionDef model | Spec | §9D.4b code: `{field_ref, operator, expected, severity}` |
| Fatal vs warning severity | Spec | §9D.4b "fatals halt pipeline" |
| ConditionEvaluator arithmetic | Spec | §9D.4c "supports abs() and arithmetic" |
| 20-step cap | Spec | §9D.5b `max_length=20` |
| Schema v2 model_validator | Spec | §9D.6b complete code example |
| v2 step type gating | Spec | §9D.6b "query/compose rejected on v1" |
| v2 feature detection | Spec | §9D.6b `has_v2_features` logic |
| PolicyValidator v2 gating | Spec | §9D.6b "PolicyValidator uses schema_version to gate which step types and ref patterns are allowed" |
| PolicyValidator step cap update | Spec | §9D.5b step count cap 10→20 |
| PolicyDocument extra="forbid" | AGENTS.md | Boundary input contract: external-input models require `extra="forbid"` or source-backed exception |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/domain/pipeline.py` | modify | Add `variables` field, change max_length 10→20, add `model_validator` for v2 gating, add `model_config = ConfigDict(extra="forbid")` |
| `packages/core/src/zorivest_core/services/ref_resolver.py` | modify | Add `{"var": "name"}` resolution alongside `{"ref": ...}` |
| `packages/core/src/zorivest_core/pipeline_steps/transform_step.py` | modify | Add `kind` discriminator + `assertions` field + `_run_assertions()` method |
| `packages/core/src/zorivest_core/services/condition_evaluator.py` | modify | Add static `evaluate_assertion()` method for assertion field/operator/expected |
| `packages/core/src/zorivest_core/domain/policy_validator.py` | modify | Accept v2 schema_version, gate `query`/`compose` by version, gate var refs by version, warn unused vars, update step cap 10→20 |
| `tests/unit/test_variable_injection.py` | new | 3 tests (AC-7.1 through AC-7.3) |
| `tests/unit/test_assertion_gates.py` | new | 4 tests (AC-7.4 through AC-7.7) |
| `tests/unit/test_schema_v2_migration.py` | new | 11 tests (AC-7.8 through AC-7.18) |

---

## Out of Scope

- MEU-PH8 (Policy Emulator) — depends on PH4–PH7
- MEU-PH9 (MCP tools: template CRUD, emulator, schema discovery) — depends on PH6, PH8
- MEU-PH10 (Default Morning Check-In template seed) — depends on PH6
- REST routes for template CRUD (`POST/PATCH/DELETE /scheduling/templates`) — PH9
- MCP template tools (`create_email_template`, `update_email_template`) — PH9

---

## BUILD_PLAN.md Audit

This project does not modify `docs/BUILD_PLAN.md` hub content. Validation:

```powershell
rg "MEU-PH[4567]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt
```

Expected: 0 matches (MEU-PH4–PH7 are tracked in `build-priority-matrix.md`, not BUILD_PLAN.md hub).

---

## Verification Plan

### 1. MEU-PH4 Tests (8 tests)
```powershell
uv run pytest tests/unit/test_query_step.py -x --tb=short -v *> C:\Temp\zorivest\ph4-tests.txt; Get-Content C:\Temp\zorivest\ph4-tests.txt | Select-Object -Last 40
```

### 2. MEU-PH5 Tests (5 tests)
```powershell
uv run pytest tests/unit/test_compose_step.py -x --tb=short -v *> C:\Temp\zorivest\ph5-tests.txt; Get-Content C:\Temp\zorivest\ph5-tests.txt | Select-Object -Last 40
```

### 3. MEU-PH6 Tests (24 tests)
```powershell
uv run pytest tests/unit/test_secure_jinja.py tests/unit/test_safe_markdown.py tests/unit/test_send_step_db_lookup.py tests/unit/test_email_template_repository.py -x --tb=short -v *> C:\Temp\zorivest\ph6-tests.txt; Get-Content C:\Temp\zorivest\ph6-tests.txt | Select-Object -Last 40
```

### 4. MEU-PH7 Tests (18 tests)
```powershell
uv run pytest tests/unit/test_variable_injection.py tests/unit/test_assertion_gates.py tests/unit/test_schema_v2_migration.py -x --tb=short -v *> C:\Temp\zorivest\ph7-tests.txt; Get-Content C:\Temp\zorivest\ph7-tests.txt | Select-Object -Last 40
```

### 5. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40
```

### 6. Type Check
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 7. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 8. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

No open questions. All behaviors resolved from Spec or Local Canon sources.

---

## Research References

- [09d-pipeline-step-extensions.md](file:///p:/zorivest/docs/build-plan/09d-pipeline-step-extensions.md) — PH4, PH5, PH7 spec
- [09e-template-database.md](file:///p:/zorivest/docs/build-plan/09e-template-database.md) — PH6 spec
- [p2.5c_security_hardening_analysis.md](file:///p:/zorivest/docs/execution/plans/2026-04-25-pipeline-security-hardening/p2.5c_security_hardening_analysis.md) — MEU dependency graph
- [step_registry.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/step_registry.py) — RegisteredStep pattern
- [sql_sandbox.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/sql_sandbox.py) — SqlSandbox consumed by PH4
- [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py) — _resolve_body() chain modified by PH6
- [pipeline.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py) — PolicyDocument modified by PH7
- [ref_resolver.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/ref_resolver.py) — RefResolver modified by PH7
