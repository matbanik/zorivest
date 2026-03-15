# Phase 9 Scheduling Infrastructure Core

Build the scheduling infrastructure layer: SQLAlchemy models, repository implementations, PipelineRunner execution engine, and RefResolver/ConditionEvaluator for parameter resolution. This project continues the Phase 9 domain foundation (MEU-77–80 ✅) and builds the persistence + execution layers that all pipeline steps depend on.

## Project Scope

- **Slug**: `2026-03-15-scheduling-infrastructure`
- **MEUs**: MEU-81, MEU-82, MEU-83, MEU-84 (in execution order: 81 → 84 → 82 → 83)
- **Build plan sections**: [09-scheduling.md](../../build-plan/09-scheduling.md) §9.2a–9.2j (models, triggers, repos), §9.3a–9.3e (PipelineRunner, zombie detection), §9.3b–9.3c (RefResolver, ConditionEvaluator)
- **In scope**: Models, repos, UoW extension, PipelineRunner, RefResolver, ConditionEvaluator, SQL triggers (report versioning + audit append-only)
- **Out of scope**: SchedulerService/APScheduler integration (§9.3d), FetchStep (§9.4), TransformStep (§9.5), StoreReportStep/RenderStep (§9.6), SendStep (§9.7), REST API (§9.8), MCP tools, GUI, sleep/wake handler (§9.3f)

---

## MEU-81: Scheduling Models (`scheduling-models`)

### Build Plan Ref
[09-scheduling.md §9.2a–9.2i](../../build-plan/09-scheduling.md)

### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| 9 model classes (PolicyModel, PipelineRunModel, PipelineStepModel, PipelineStateModel, ReportModel, ReportVersionModel, ReportDeliveryModel, FetchCacheModel, AuditLogModel) | Spec | §9.2a–9.2i | ✅ |
| UUID primary keys (String(36)) | Spec | §9.2a | ✅ |
| PolicyModel.policy_json stores full PolicyDocument JSON | Spec | §9.2c | ✅ |
| PolicyModel.approved_hash for change-detection re-approval | Spec | §9.2c | ✅ |
| PipelineStateModel has 4-column UniqueConstraint | Spec | §9.2d | ✅ |
| FetchCacheModel has 3-column UniqueConstraint | Spec | §9.2g | ✅ |
| AuditLogModel.id uses Integer autoincrement (not UUID) | Spec | §9.2i | ✅ |
| Report versioning trigger (BEFORE UPDATE on reports) | Spec | §9.2h | ✅ |
| Audit append-only triggers (BEFORE UPDATE/DELETE on audit_log) | Spec | §9.2i | ✅ |
| All models inherit from existing `Base` in models.py | Local Canon | `models.py` L26 | ✅ |
| Relationship back_populates for PipelineRunModel ↔ PolicyModel, PipelineStepModel ↔ PipelineRunModel, ReportModel ↔ ReportVersionModel, ReportModel ↔ ReportDeliveryModel | Spec | §9.2a–9.2f | ✅ |

### Feature Intent Contract (FIC)

- **AC-1** (Spec): 9 new model classes exist in `models.py` and inherit from `Base`
- **AC-2** (Spec): All 9 models create valid tables via `Base.metadata.create_all()` on in-memory SQLite
- **AC-3** (Spec): PolicyModel has `policy_json`, `content_hash`, `approved`, `approved_hash`, `approved_at` columns
- **AC-4** (Spec): PipelineRunModel has FK to `policies.id` and bidirectional relationship
- **AC-5** (Spec): PipelineStepModel has FK to `pipeline_runs.id` and bidirectional relationship
- **AC-6** (Spec): PipelineStateModel has UniqueConstraint on (`policy_id`, `provider_id`, `data_type`, `entity_key`)
- **AC-7** (Spec): FetchCacheModel has UniqueConstraint on (`provider`, `data_type`, `entity_key`)
- **AC-8** (Spec): AuditLogModel uses `Integer` PK with `autoincrement=True` (not UUID)
- **AC-9** (Spec): ReportModel has cascade relationships to versions and deliveries
- **AC-10** (Spec): ReportDeliveryModel.dedup_key is `unique=True`

### Files

#### [MODIFY] [models.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py)
- Append 9 model classes after existing models (PolicyModel, PipelineRunModel, PipelineStepModel, PipelineStateModel, ReportModel, ReportVersionModel, ReportDeliveryModel, FetchCacheModel, AuditLogModel)
- Add `UniqueConstraint` and `Index` imports as needed

#### [NEW] [test_scheduling_models.py](file:///p:/zorivest/tests/unit/test_scheduling_models.py)
- In-memory SQLite tests for all 9 models: table creation, CRUD, FK constraints, unique constraints

---

## MEU-84: RefResolver + ConditionEvaluator (`ref-resolver`)

### Build Plan Ref
[09-scheduling.md §9.3b–9.3c](../../build-plan/09-scheduling.md)

### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| RefResolver.resolve() recursively walks params dict | Spec | §9.3b | ✅ |
| `{"ref": "ctx.<step_id>.output.<path>"}` format with single-key dict detection | Spec | §9.3b | ✅ |
| Nested path traversal (dict keys + list indices) | Spec | §9.3b | ✅ |
| KeyError on missing step or missing nested key | Spec | §9.3b | ✅ |
| ValueError for invalid ref format (no "ctx." prefix) | Spec | §9.3b | ✅ |
| ConditionEvaluator supports all 10 SkipConditionOperator values | Spec | §9.3c | ✅ |
| `_resolve_field` traverses `ctx.<step_id>.<path>` with graceful None on missing keys | Spec | §9.3c | ✅ |
| is_null/is_not_null don't require `value` parameter | Spec | §9.3c | ✅ |

### Feature Intent Contract (FIC)

- **AC-1** (Spec): `RefResolver.resolve()` returns new dict with all `{"ref": "ctx.x.y"}` replaced with actual values
- **AC-2** (Spec): Nested dict traversal: `ctx.step_id.output.nested.key` resolves correctly
- **AC-3** (Spec): List index traversal: `ctx.step_id.output.0` resolves via `int()` conversion
- **AC-4** (Spec): Non-ref dicts (keys ≠ `{"ref":...}`) are traversed recursively without substitution
- **AC-5** (Spec): Missing step in context raises `KeyError`
- **AC-6** (Spec): Invalid ref format (no `ctx.` prefix) raises `ValueError`
- **AC-7** (Spec): ConditionEvaluator implements all 10 operators: eq, ne, gt, lt, ge, le, in, not_in, is_null, is_not_null
- **AC-8** (Spec): ConditionEvaluator returns `True` when condition is met (step should be skipped)
- **AC-9** (Spec): Missing field path resolves to `None` (graceful, doesn't raise)
- **AC-10** (Spec): Unknown operator raises `ValueError`

### Files

#### [NEW] [ref_resolver.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/ref_resolver.py)
- `RefResolver` class with `resolve()` and `_walk()` methods

#### [NEW] [condition_evaluator.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/condition_evaluator.py)
- `ConditionEvaluator` class with `evaluate()`, `_resolve_field()`, `_compare()` methods

#### [NEW] [test_ref_resolver.py](file:///p:/zorivest/tests/unit/test_ref_resolver.py)
- Test class per component: `TestRefResolver`, `TestConditionEvaluator`

---

## MEU-82: Scheduling Repos (`scheduling-repos`)

### Build Plan Ref
[09-scheduling.md §9.2j](../../build-plan/09-scheduling.md)

### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| 5 repository classes: PolicyRepository, PipelineRunRepository, ReportRepository, FetchCacheRepository, AuditLogRepository | Spec | §9.2j | ✅ |
| PolicyRepository: create, get_by_id, get_by_name, list_all, update, delete | Spec | §9.2j | ✅ |
| PipelineRunRepository: create, get_by_id, list_by_policy, list_recent, update_status, find_zombies | Spec | §9.2j | ✅ |
| ReportRepository: create, get_by_id, get_versions | Spec | §9.2j | ✅ |
| FetchCacheRepository: get_cached, upsert, invalidate | Spec | §9.2j | ✅ |
| AuditLogRepository: append, list_recent | Spec | §9.2j | ✅ |
| Repos follow existing `__init__(self, session)` pattern | Local Canon | `repositories.py` | ✅ |
| UoW needs scheduling repo attributes | Local Canon | `unit_of_work.py` | ✅ |

### Feature Intent Contract (FIC)

- **AC-1** (Spec): `PolicyRepository` CRUD: create, get_by_id, get_by_name, list_all (with `enabled_only` filter), update, delete
- **AC-2** (Spec): `PipelineRunRepository` with `find_zombies()` returning runs where `status='running'`
- **AC-3** (Spec): `PipelineRunRepository.list_by_policy()` with limit parameter, ordered by `created_at DESC`
- **AC-4** (Spec): `ReportRepository` CRUD with `get_versions()` returning historical versions
- **AC-5** (Spec): `FetchCacheRepository.upsert()` handles insert-or-update for cache entries
- **AC-6** (Spec): `FetchCacheRepository.invalidate()` returns count of deleted entries
- **AC-7** (Spec): `AuditLogRepository.append()` creates append-only audit entries
- **AC-8** (Local Canon): All repos use `Session.__init__` pattern matching existing repos
- **AC-9** (Local Canon): `SqlAlchemyUnitOfWork.__enter__` creates scheduling repo attributes

### Files

#### [NEW] [scheduling_repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py)
- 5 repository classes following established Session-based pattern

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)
- Add scheduling repo imports + 5 new attributes in `__enter__`

#### [NEW] [test_scheduling_repos.py](file:///p:/zorivest/tests/unit/test_scheduling_repos.py)
- In-memory SQLite tests for all 5 repos: CRUD operations, filter/sort, zombies, upsert, invalidate

---

## MEU-83: PipelineRunner (`pipeline-runner`)

### Build Plan Ref
[09-scheduling.md §9.3a, §9.3e](../../build-plan/09-scheduling.md)

### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Sequential async step execution | Spec | §9.3a | ✅ |
| Skip condition evaluation via ConditionEvaluator | Spec | §9.3a | ✅ |
| Dry-run mode: skip steps with `side_effects=True` | Spec | §9.3a | ✅ |
| Retry with backoff + jitter for RETRY_THEN_FAIL error mode | Spec | §9.3a | ✅ |
| Resume from failure via `resume_from` parameter | Spec | §9.3a | ✅ |
| Per-step timeout via `asyncio.timeout()` | Spec | §9.3a | ✅ |
| Final status: SUCCESS, FAILED, CANCELLED | Spec | §9.3a | ✅ |
| Zombie recovery: find_zombies + mark FAILED | Spec | §9.3e | ✅ |
| StepErrorMode.FAIL_PIPELINE aborts pipeline | Spec | §9.3a | ✅ |
| StepErrorMode.LOG_AND_CONTINUE continues after failure | Spec | §9.3a | ✅ |
| PipelineRunner.__init__ takes uow, ref_resolver, condition_evaluator | Spec | §9.3a | ✅ |

> [!NOTE]
> The PipelineRunner spec references `_create_run_record`, `_persist_step`, `_finalize_run`, `_load_prior_output` as stub methods. These will be implemented using the scheduling repos from MEU-82. For unit tests, we mock the UoW to isolate the runner logic.

### Feature Intent Contract (FIC)

- **AC-1** (Spec): `PipelineRunner.run()` executes steps sequentially and returns `{run_id, status, duration_ms, error, steps}`
- **AC-2** (Spec): Steps with `skip_if` condition met → `StepResult(status=SKIPPED)`
- **AC-3** (Spec): Dry-run mode → steps with `side_effects=True` are skipped with `{"dry_run": True}` output
- **AC-4** (Spec): `StepErrorMode.FAIL_PIPELINE` → pipeline stops, returns FAILED
- **AC-5** (Spec): `StepErrorMode.LOG_AND_CONTINUE` → step failure logged, pipeline continues
- **AC-6** (Spec): `StepErrorMode.RETRY_THEN_FAIL` → retry up to `max_attempts` with exponential backoff
- **AC-7** (Spec): `resume_from` → skips steps until reaching the specified step_id, loading prior outputs
- **AC-8** (Spec): Per-step `asyncio.timeout()` → TimeoutError caught and wrapped as FAILED StepResult
- **AC-9** (Spec): `asyncio.CancelledError` → pipeline status = CANCELLED
- **AC-10** (Spec): `recover_zombies()` marks orphaned RUNNING runs as FAILED with appropriate logging

### Files

#### [NEW] [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py)
- `PipelineRunner` class with `run()`, `_execute_step()`, `recover_zombies()`, persistence stubs

#### [NEW] [test_pipeline_runner.py](file:///p:/zorivest/tests/unit/test_pipeline_runner.py)
- Async tests with mocked UoW, mock step implementations, edge cases

---

## BUILD_PLAN.md Update Task

Review and update `docs/BUILD_PLAN.md` for:
- Phase 9 status: update from `⚪ Not Started` to `🟡 In Progress` (line 68)
- MEU-81, 82, 83, 84 status columns updated to ✅
- Phase 9 phase-exit criteria update (if MEU-81–84 completion warrants)
- MEU Summary table: P2.5 completed count (line 471): 4 → 8
- Total completed (line 477): 60 → 64
- No stale execution plan references need updating for this scope

### Validation
```bash
rg "⬜.*scheduling-models\|⬜.*scheduling-repos\|⬜.*pipeline-runner\|⬜.*ref-resolver" docs/BUILD_PLAN.md
# Should return 0 matches after update (all changed to ✅)
```

---

## Verification Plan

### Automated Tests

```bash
# MEU-81: Scheduling models (in-memory SQLite)
uv run pytest tests/unit/test_scheduling_models.py -v

# MEU-84: RefResolver + ConditionEvaluator (pure unit tests)
uv run pytest tests/unit/test_ref_resolver.py -v

# MEU-82: Scheduling repos (in-memory SQLite)
uv run pytest tests/unit/test_scheduling_repos.py -v

# MEU-83: PipelineRunner (async tests with mocks)
uv run pytest tests/unit/test_pipeline_runner.py -v

# Full regression — all existing tests still pass
uv run pytest tests/ -v

# MEU gate
uv run python tools/validate_codebase.py --scope meu

# Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/services/pipeline_runner.py packages/core/src/zorivest_core/services/ref_resolver.py packages/core/src/zorivest_core/services/condition_evaluator.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py
```

### Type Checking
```bash
uv run pyright packages/core/src/zorivest_core/services/pipeline_runner.py packages/core/src/zorivest_core/services/ref_resolver.py packages/core/src/zorivest_core/services/condition_evaluator.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py packages/infrastructure/src/zorivest_infra/database/models.py
```

---

## Handoff Files

| MEU | Handoff Path |
|-----|-------------|
| MEU-81 | `.agent/context/handoffs/061-2026-03-15-scheduling-models-bp09s9.2.md` |
| MEU-84 | `.agent/context/handoffs/062-2026-03-15-ref-resolver-bp09s9.3b+9.3c.md` |
| MEU-82 | `.agent/context/handoffs/063-2026-03-15-scheduling-repos-bp09s9.2j.md` |
| MEU-83 | `.agent/context/handoffs/064-2026-03-15-pipeline-runner-bp09s9.3a+9.3e.md` |

> Sequence numbers are estimates — will be finalized by checking `ls .agent/context/handoffs/ | Sort-Object` at execution time.
