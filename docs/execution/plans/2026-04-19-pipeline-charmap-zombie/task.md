---
project: "2026-04-19-pipeline-charmap-zombie"
source: "docs/execution/plans/2026-04-19-pipeline-charmap-zombie/implementation-plan.md"
meus: ["MEU-PW4", "MEU-PW5"]
status: "complete"
template_version: "2.0"
---

# Task — Pipeline Charmap Fix + Zombie Run Elimination

> **Project:** `2026-04-19-pipeline-charmap-zombie`
> **Type:** Infrastructure/Domain
> **Estimate:** ~8 files changed (3 new, 5 modified)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | **MEU-PW4 Red:** Write tests for `configure_structlog_utf8()` (AC-1, AC-2, AC-6) | coder | `tests/unit/test_structlog_utf8.py` | `uv run pytest tests/unit/test_structlog_utf8.py -v` → all FAIL | `[x]` |
| 2 | **MEU-PW4 Red:** Write tests for `_safe_json_output()` (AC-4, AC-5) | coder | Tests in `tests/unit/test_structlog_utf8.py` | `uv run pytest -k "safe_json" -v` → all FAIL | `[x]` |
| 3 | **MEU-PW4 Green:** Create `logging_config.py` with `configure_structlog_utf8()` | coder | `packages/api/src/zorivest_api/logging_config.py` | `uv run pytest tests/unit/test_structlog_utf8.py -v` → all PASS | `[x]` |
| 4 | **MEU-PW4 Green:** Add `_safe_json_output()` to `pipeline_runner.py`, replace `json.dumps` in `_persist_step()` | coder | Modified `pipeline_runner.py` | `uv run pytest -k "safe_json" -v` → all PASS | `[x]` |
| 5 | **MEU-PW4 Green:** Call `configure_structlog_utf8()` in `main.py` lifespan | coder | Modified `main.py` | Import test → OK | `[x]` |
| 6 | **MEU-PW4 Quality:** Run pyright + ruff on touched packages | tester | Clean output | pyright + ruff clean | `[x]` |
| 7 | **MEU-PW5 Red:** Write tests for `run_id` param in `PipelineRunner.run()` (AC-1, AC-2, AC-6, AC-7) | coder | Tests in `tests/unit/test_pipeline_runner.py` | 5 FAIL confirmed (Red phase) | `[x]` |
| 8 | **MEU-PW5 Red:** Write tests for `SchedulingService.trigger_run()` single-record (AC-3, AC-4) | coder | Tests in `tests/unit/test_scheduling_service.py` | 2 FAIL confirmed (Red phase) | `[x]` |
| 9 | **MEU-PW5 Green:** Modify `pipeline_runner.py` — add `run_id` param, `_update_run_status()`, conditional create | coder | Modified `pipeline_runner.py` | 6 PASS (Green phase) | `[x]` |
| 10 | **MEU-PW5 Green:** Modify `scheduling_service.py` — pass `run_id`, set `pending`, remove duplicate finalization | coder | Modified `scheduling_service.py` | 3 PASS (Green phase) | `[x]` |
| 11 | **MEU-PW5 Green:** Add `recover_zombies()` call to `main.py` lifespan startup | coder | Modified `main.py` | Wired with try/except + structlog | `[x]` |
| 12 | **MEU-PW5 Green:** Replace single-value timeout with `httpx.Timeout(connect=10, read=30, write=10, pool=10)` in `market_data_adapter.py` | coder | Modified `market_data_adapter.py` | 9 passed, pyright clean | `[x]` |
| 13 | **MEU-PW5 Quality:** Run pyright + ruff on touched packages | tester | Clean output | 0 errors, All checks passed | `[x]` |
| 14 | Full pipeline regression | tester | All pipeline tests pass | 2026 passed, 15 skipped, 0 failures | `[x]` |
| 15 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | Update PW4/PW5 status to ✅ | Both rows updated ⬜→✅ | `[x]` |
| 16 | Run MEU gate | tester | All checks pass | 8/8 blocking passed (23.3s) | `[x]` |
| 17 | Update `meu-registry.md` with PW4/PW5 completion | orchestrator | Status → `✅ 2026-04-19` | PW4-PW8 added, PW4+PW5 marked ✅ | `[x]` |
| 18 | Regenerate OpenAPI spec (if api/ modified) | tester | No drift | `[OK] OpenAPI spec matches committed snapshot` | `[x]` |
| 19 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-charmap-zombie-2026-04-19` | Note ID 834 | `[x]` |
| 20 | Create handoff (PW4) | reviewer | `.agent/context/handoffs/116-2026-04-19-charmap-fix-bp09bs9B.2.md` | Created | `[x]` |
| 21 | Create handoff (PW5) | reviewer | `.agent/context/handoffs/117-2026-04-19-zombie-fix-bp09bs9B.3.md` | Created | `[x]` |
| 22 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-19-charmap-zombie-reflection.md` | Created | `[x]` |
| 23 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | Row added (2026-04-19 MEU-PW4/PW5) | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
