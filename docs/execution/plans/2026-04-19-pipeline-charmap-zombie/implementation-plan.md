---
project: "2026-04-19-pipeline-charmap-zombie"
date: "2026-04-19"
source: "docs/build-plan/09b-pipeline-hardening.md §9B.2, §9B.3"
meus: ["MEU-PW4", "MEU-PW5"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Pipeline Charmap Fix + Zombie Run Elimination

> **Project**: `2026-04-19-pipeline-charmap-zombie`
> **Build Plan Section(s)**: 09b-pipeline-hardening.md §9B.2 (MEU-PW4), §9B.3 (MEU-PW5)
> **Status**: `draft`

---

## Goal

Fix two HIGH-severity pipeline runtime bugs that render the scheduling pipeline non-functional:

1. **[PIPE-CHARMAP] (MEU-PW4):** Windows `cp1252` encoding crashes structlog when exception messages contain non-ASCII characters. Secondary: `json.dumps()` fails on `bytes` objects in step output.
2. **[PIPE-ZOMBIE] (MEU-PW5):** Dual-write architecture creates orphaned "running" records that stay forever. `SchedulingService.trigger_run()` creates one run record, `PipelineRunner.run()` creates a second — only the inner one gets finalized.

These two MEUs form the foundation of the hardening chain — PW6, PW7, and PW8 all depend on PW4+PW5 being complete.

---

## User Review Required

> [!IMPORTANT]
> **Dual-write elimination changes the record-creation contract.** After PW5, `PipelineRunner.run()` no longer creates its own run record when `run_id` is provided. All callers that pass `run_id=""` (standalone mode) are unaffected — the runner auto-creates a record as before. Only `SchedulingService.trigger_run()` behavior changes: it creates the record and passes `run_id` into the runner.

> [!IMPORTANT]
> **Structlog configuration is global.** `configure_structlog_utf8()` reconfigures the global structlog pipeline once at startup. All existing `structlog.get_logger()` calls will inherit the new processor chain. This is intentional — we want UTF-8 safety everywhere.

---

## Proposed Changes

### MEU-PW4: Charmap Encoding Fix

#### Boundary Inventory

No external-input write surfaces. This MEU modifies internal logging and serialization — no REST, MCP, or UI boundaries affected.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `configure_structlog_utf8()` module exists and configures structlog with `UnicodeDecoder`, `TimeStamper`, and `PrintLoggerFactory` using UTF-8 `TextIOWrapper` on stderr | Spec (§9B.2b) | Calling without prior configuration produces unconfigured error |
| AC-2 | `sys.stderr` is reconfigured with `encoding="utf-8", errors="replace"` if `.reconfigure()` is available | Spec (§9B.2b) | Non-ASCII chars in log messages do NOT raise `UnicodeEncodeError` |
| AC-3 | `configure_structlog_utf8()` is called once during FastAPI lifespan startup, before any pipeline execution | Spec (§9B.2d) | — |
| AC-4 | `_safe_json_output()` helper serializes `bytes` values via `decode("utf-8", errors="replace")` and `datetime` values via `.isoformat()` | Spec (§9B.2c) | `bytes` object in step output raises `TypeError` |
| AC-5 | `_persist_step()` uses `_safe_json_output()` instead of raw `json.dumps(result.output)` | Spec (§9B.2c) | Step output containing `bytes` is persisted without crash |
| AC-6 | Structlog output is JSON when stderr is not a TTY, and `ConsoleRenderer` when it is | Spec (§9B.2b) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Structlog processor chain (exact order) | Spec | §9B.2b provides full `structlog.configure()` call |
| stderr reconfiguration via `.reconfigure()` | Spec | §9B.2b line 58-59 |
| `_safe_json_output()` signature and `default` handler | Spec | §9B.2c provides exact implementation |
| Call site in lifespan | Spec | §9B.2d table row 1 |
| Existing log format preservation | Research-backed | structlog docs: `ConsoleRenderer()` is the default dev format; `JSONRenderer()` is production. Both are standard. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/logging_config.py` | new | `configure_structlog_utf8()` function |
| `packages/api/src/zorivest_api/main.py` | modify | Call `configure_structlog_utf8()` at start of lifespan |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modify | Add `_safe_json_output()`, replace `json.dumps(result.output)` in `_persist_step()` |
| `tests/unit/test_logging_config.py` | new | Tests for AC-1, AC-2, AC-4, AC-5 |

---

### MEU-PW5: Zombie Run Elimination

#### Boundary Inventory

No new external-input write surfaces. The `run_id` parameter added to `PipelineRunner.run()` is an internal contract between `SchedulingService` and `PipelineRunner` — not exposed to REST/MCP callers.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `PipelineRunner.run()` accepts optional `run_id: str = ""` parameter. When provided (non-empty), skips `_create_run_record()` and updates the existing record to `RUNNING` status | Spec (§9B.3b) | Passing non-empty `run_id` must NOT create a second pipeline_runs row |
| AC-2 | `PipelineRunner.run()` with `run_id=""` (default) creates a new run record as before — backward compatible | Spec (§9B.3b) | Standalone mode still works identically to current behavior |
| AC-3 | `SchedulingService.trigger_run()` creates the run record, passes `run_id` into `self._runner.run()`, and does NOT perform a second update/finalization after the runner returns (the runner finalizes) | Spec (§9B.3b) | Only ONE `pipeline_runs` row exists per `trigger_run()` call |
| AC-4 | `SchedulingService.trigger_run()` initial run status is `"pending"` (not `"running"`) — the runner transitions it to `"running"` on start | Spec (§9B.3b) | Run record starts as `pending`, transitions to `running`, then to final status |
| AC-5 | `recover_zombies()` is called during FastAPI lifespan startup | Spec (§9B.3d, §9B.3e table row 4) | — |
| AC-6 | `PipelineRunner` has `_update_run_status()` private method that updates an existing run record's status field | Spec (§9B.3b) | — |
| AC-7 | When `run_id` is provided and runner finalizes, the final status/error/duration are persisted on that same run record | Spec (§9B.3b) | Run record shows final `status`, `error`, `duration_ms` after completion |
| AC-8 | `MarketDataProviderAdapter` uses `httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)` instead of default single-value timeout | Spec (§9B.3c) | TCP-hanging fetch completes or raises within read timeout |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `run_id` parameter signature and default | Spec | §9B.3b provides exact signature |
| Conditional `_create_run_record()` skip | Spec | §9B.3b code block lines 165-170 |
| `SchedulingService` creates sole record | Spec | §9B.3b code block lines 178-193 |
| Initial status `"pending"` | Spec | §9B.3b line 181 |
| Runner updates to `"running"` on start | Spec | §9B.3b line 170 |
| `recover_zombies()` in lifespan | Spec | §9B.3e table row 4 |
| Duplicate finalization removal from `SchedulingService` | Spec | §9B.3b lines 191-193 — the runner now owns finalization |
| `_update_run_status()` method | Spec | §9B.3b line 170 implies this helper |
| `httpx.Timeout` per-phase configuration | Spec | §9B.3c provides exact values; §9B.3e table row 3 |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modify | Add `run_id` param to `run()`, add `_update_run_status()`, conditional record creation |
| `packages/core/src/zorivest_core/services/scheduling_service.py` | modify | Pass `run_id` to runner, set initial status to `"pending"`, remove duplicate finalization |
| `packages/api/src/zorivest_api/main.py` | modify | Call `pipeline_runner.recover_zombies()` in lifespan startup |
| `packages/infrastructure/src/zorivest_infra/market_data/market_data_adapter.py` | modify | Replace single-value timeout with `httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)` |
| `tests/unit/test_pipeline_runner.py` | modify | Add tests for `run_id` param, backward compat, no-dual-write |
| `tests/unit/test_scheduling_service.py` | modify | Add PW5 tests for single-record creation, `run_id` passthrough to existing MEU-89 suite |

---

## Out of Scope

- **MEU-PW6 (URL Builders):** Provider-specific URL construction — depends on PW5
- **MEU-PW7 (Cancellation):** `CANCELLING` status, task registry, cancel endpoint — depends on PW5
- **MEU-PW8 (E2E Test Harness):** Integration test infrastructure — depends on PW4–PW7

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections structurally. MEU-PW4 and PW5 status columns will be updated from `⬜ planned` to `✅ {date}` upon completion.

Validation:

```powershell
rg "MEU-PW4|MEU-PW5" docs/BUILD_PLAN.md  # Expected: 2+ matches in P2.5b section
```

---

## Verification Plan

### 1. Unit Tests (PW4)
```powershell
uv run pytest tests/unit/test_logging_config.py -v *> C:\Temp\zorivest\pytest-pw4.txt; Get-Content C:\Temp\zorivest\pytest-pw4.txt | Select-Object -Last 30
```

### 2. Unit Tests (PW5)
```powershell
uv run pytest tests/unit/test_pipeline_runner.py tests/unit/test_scheduling_service.py -v *> C:\Temp\zorivest\pytest-pw5.txt; Get-Content C:\Temp\zorivest\pytest-pw5.txt | Select-Object -Last 30
```

### 3. Integration Test (dual-write elimination)
```powershell
uv run pytest tests/unit/test_pipeline_runner.py -k "run_id" -v *> C:\Temp\zorivest\pytest-dualwrite.txt; Get-Content C:\Temp\zorivest\pytest-dualwrite.txt | Select-Object -Last 20
```

### 4. Type Check
```powershell
uv run pyright packages/core packages/api *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 5. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 6. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 7. Regression (all pipeline tests)
```powershell
uv run pytest tests/ -k "pipeline" -v *> C:\Temp\zorivest\pytest-pipeline-all.txt; Get-Content C:\Temp\zorivest\pytest-pipeline-all.txt | Select-Object -Last 40
```

---

## Open Questions

No open questions. The spec (§9B.2 and §9B.3) is sufficiently detailed to implement both MEUs without ambiguity.

---

## Research References

- [docs/build-plan/09b-pipeline-hardening.md](file:///p:/zorivest/docs/build-plan/09b-pipeline-hardening.md) (§9B.2, §9B.3)
- [structlog docs: Configuration](https://www.structlog.org/en/stable/configuration.html) — processor chain ordering, `PrintLoggerFactory`
- [Python docs: sys.stderr.reconfigure()](https://docs.python.org/3/library/io.html#io.TextIOWrapper.reconfigure) — UTF-8 override on Windows
- [known-issues.md: PIPE-CHARMAP](file:///p:/zorivest/.agent/context/known-issues.md#L31) — original bug report
- [known-issues.md: PIPE-ZOMBIE](file:///p:/zorivest/.agent/context/known-issues.md#L39) — original bug report
