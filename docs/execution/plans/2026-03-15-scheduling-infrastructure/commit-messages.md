# Commit Messages — Phase 9 Scheduling Infrastructure

## Commit 1: feat(scheduling): add scheduling models, repos, runner, resolver (MEU-81..84)

```
feat(scheduling): add scheduling models, repos, runner, resolver (MEU-81..84)

Phase 9 Scheduling Infrastructure Core:

MEU-81: 9 SQLAlchemy scheduling models (pipeline_runs, pipeline_steps,
  policies, reports, report_versions, report_deliveries, fetch_cache,
  audit_log) with Alembic DDL trigger

MEU-82: 5 scheduling repositories (PolicyRepository,
  PipelineRunRepository, ReportRepository, FetchCacheRepository,
  AuditLogRepository) + UoW extension (10→15 repos)

MEU-83: PipelineRunner — async sequential executor with:
  - Ref resolution, skip conditions, error modes
  - Retry with backoff, dry-run, resume-from-failure
  - Persistence hooks (_create_run_record, _persist_step,
    _finalize_run, _load_prior_output)
  - Zombie recovery (recover_zombies)

MEU-84: RefResolver + ConditionEvaluator — param resolution via
  dot-path refs and skip-condition evaluation with 6 operators

77 new tests, 1309 total passing.
```

## Commit 2: docs(scheduling): update BUILD_PLAN, meu-registry, reflection

```
docs(scheduling): update BUILD_PLAN, meu-registry, reflection

- Mark MEU-81..84 as ✅ in BUILD_PLAN.md (P2.5: 4→8 completed)
- Add MEU-81..84 to meu-registry.md
- Add scheduling-infrastructure reflection
- Add metrics row
- Update task.md with all deliverables marked done
```
