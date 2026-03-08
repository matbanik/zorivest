# Task Handoff

## Task

- **Date:** 2026-03-08
- **Task slug:** backup-recovery-config-image-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of the correlated `2026-03-08-backup-recovery-config-image` implementation (`021` through `023` handoffs, shared project artifacts, and claimed source/test files)

## Inputs

- User request: Run `.agent/workflows/critical-review-feedback.md` against implementation handoffs `021`, `022`, and `023`.
- Specs/docs referenced:
  - `SOUL.md`
  - `GEMINI.md`
  - `AGENTS.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `.agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md`
  - `.agent/context/handoffs/022-2026-03-08-config-export-bp02as2A.5.md`
  - `.agent/context/handoffs/023-2026-03-08-image-processing-bp03sIMG.md`
  - `docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md`
  - `docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/image-architecture.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/meu-registry.md`
  - `docs/execution/metrics.md`
- Constraints:
  - Review-only workflow. No fixes.
  - Findings first, severity-ranked, with repo-state evidence.
  - Scope expanded to the full correlated project because the three provided handoffs map to the same execution plan folder and the plan’s `Handoff Paths` section enumerates all three outputs.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-03-08-backup-recovery-config-image-implementation-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - `Get-Content` across the three MEU handoffs, correlated plan/task, claimed source files, tests, and shared artifacts
  - `git status --short`
  - `rg -n ...` sweeps for contract drift, missing shared artifacts, and stale status hubs
- Results:
  - Confirmed implementation-review mode for the explicit `021`/`022`/`023` handoff set correlated to `docs/execution/plans/2026-03-08-backup-recovery-config-image/`.
  - Confirmed no prior canonical implementation review file existed, so this file was created as the rolling review thread for the project.

## Tester Output

- Commands run:
  - `git status --short`
  - `Get-Content .agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md`
  - `Get-Content .agent/context/handoffs/022-2026-03-08-config-export-bp02as2A.5.md`
  - `Get-Content .agent/context/handoffs/023-2026-03-08-image-processing-bp03sIMG.md`
  - `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md`
  - `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md`
  - `Get-Content packages/infrastructure/src/zorivest_infra/backup/backup_recovery_manager.py`
  - `Get-Content packages/infrastructure/src/zorivest_infra/backup/backup_recovery_types.py`
  - `Get-Content packages/core/src/zorivest_core/domain/config_export.py`
  - `Get-Content packages/infrastructure/src/zorivest_infra/image_processing.py`
  - `Get-Content packages/core/src/zorivest_core/domain/exceptions.py`
  - `Get-Content packages/infrastructure/pyproject.toml`
  - `Get-Content tests/unit/test_backup_recovery.py`
  - `Get-Content tests/integration/test_backup_recovery_integration.py`
  - `Get-Content tests/unit/test_config_export.py`
  - `Get-Content tests/unit/test_image_processing.py`
  - `Get-Content .agent/context/meu-registry.md`
  - `Get-Content docs/execution/metrics.md`
  - `Test-Path docs/execution/reflections/2026-03-08-backup-recovery-config-image-reflection.md; Test-Path docs/execution/plans/2026-03-08-backup-recovery-config-image/commit-messages.md; Test-Path docs/execution/plans/2026-03-08-backup-recovery-config-image/session-state.md; Test-Path docs/execution/metrics.md`
  - `uv run pytest tests/unit/test_backup_recovery.py -q`
  - `uv run pytest tests/integration/test_backup_recovery_integration.py -q`
  - `uv run pytest tests/unit/test_config_export.py -q`
  - `uv run pytest tests/unit/test_image_processing.py -q`
  - `uv run pyright packages/`
  - `uv run ruff check packages/`
  - `rg "TODO|FIXME|NotImplementedError" packages/`
  - `uv run python tools/validate_codebase.py --scope meu`
  - `uv run pytest tests/ -q`
  - `@' ... '@ | uv run python -` probe calling `ConfigExportService.build_export(...)` followed by `validate_import(...)`
  - `rg -n "build_export|validate_import|portable|SECRET|SENSITIVE|ImportValidation" docs/build-plan/02a-backup-restore.md`
  - `Get-Content docs/build-plan/02a-backup-restore.md | Select-Object -Skip 700 -First 60`
  - `Get-Content docs/build-plan/02a-backup-restore.md | Select-Object -Skip 884 -First 40`
  - `rg -n "test_repair_corrupted_db|test_repair_healthy_database|test_repair_nonexistent_database|test_create_and_restore|test_verify_then_restore_roundtrip" tests/unit/test_backup_recovery.py tests/integration/test_backup_recovery_integration.py .agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md`
  - `rg -n "Post-Project|MEU gate|Full regression|Anti-placeholder|Reflection|Metrics|Session state|Commit messages" docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md`
  - `rg -n "MEU-20|MEU-21|MEU-22|✅ Completed|🔵 In Progress|P0 — Phase 2/2A|P0 — Phase 3/4" docs/BUILD_PLAN.md`
  - `rg -n "Phase 2A|MEU-20|MEU-21|MEU-22|Phase 3|Execution Order|Phase-Exit Criteria" .agent/context/meu-registry.md`
  - `rg -n "Date \\| MEU\\(s\\)|backup-recovery-config-image" docs/execution/metrics.md`
- Pass/fail matrix:
  - MEU-20 unit tests: pass (`12 passed`)
  - MEU-20 integration tests: pass (`5 passed`)
  - MEU-21 unit tests: pass (`16 passed`)
  - MEU-22 unit tests: pass (`16 passed`)
  - Full regression: pass (`499 passed, 1 skipped`)
  - `pyright packages/`: pass (`0 errors, 0 warnings, 0 informations`)
  - `ruff check packages/`: pass
  - Anti-placeholder scan: pass (clean; `rg` returned exit code `1`)
  - MEU gate: pass, with advisory only: `023-2026-03-08-image-processing-bp03sIMG.md missing: Evidence/FAIL_TO_PASS`
  - Config export round-trip probe: fail — `validate_import(build_export(...))` produced `accepted=[]`, `rejected=[]`, `unknown=['config_version', 'app_version', 'created_at', 'settings']`
  - Shared closeout artifacts: fail — reflection, commit messages, and session-state files are absent; `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, and `docs/execution/metrics.md` are not updated for MEU-20/21/22
- Repro failures:
  - `ConfigExportService.validate_import()` iterates top-level keys from the exported payload instead of `config_data["settings"]`, so the service cannot validate its own export shape.
  - Handoff `021` claims a passing `test_repair_corrupted_db`, but no such test exists in the repo.
  - Project-level closeout remains incomplete despite the three MEU handoffs being presented for validation.
- Coverage/test gaps:
  - MEU-20 does not test the corrupted-database repair branch of AC-20.6; only healthy and nonexistent DB paths are covered.
  - MEU-21 tests encode the same flat-dict contract drift as the implementation and therefore would not catch import/export shape mismatches against the build-plan contract.
- Evidence bundle location:
  - This handoff file.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - PASS_TO_PASS for the shipped unit/integration suites and full regression.
  - FAIL evidence captured for the config export round-trip probe and the missing corrupted-repair test evidence.
- Mutation score:
  - Not applicable.
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  - **High:** MEU-21 ships the wrong config export/import contract relative to `02a §2A.5`, and the implementation cannot validate the service’s own export payload. The build-plan contract expects `build_export(user_settings, defaults)` to produce a dict with nested `settings`, and `validate_import(config_data)` to iterate `config_data.get("settings", {})` (`docs/build-plan/02a-backup-restore.md:711-747`). The shipped implementation instead defines `build_export(resolved_values)` and loops over `for key in import_data:` in `validate_import()` (`packages/core/src/zorivest_core/domain/config_export.py:55-97`), while the tests codify the same flat-dict interface (`tests/unit/test_config_export.py:86-207`). A direct probe confirmed the break: `validate_import(build_export(...))` returns no accepted keys and marks `config_version`, `app_version`, `created_at`, and `settings` as unknown. This is a contract-level incompatibility that would break any caller using the documented export shape.
  - **High:** Handoff `021` materially overstates AC-20.6 evidence by claiming a corrupted-database repair test that does not exist, leaving the repair branch unverified. The tester matrix in the handoff reports `test_repair_corrupted_db` as passing (`.agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md:61-62`), but the actual unit file contains only `test_repair_healthy_database` and `test_repair_nonexistent_database` (`tests/unit/test_backup_recovery.py:295-314`), and the integration suite exercises verify/restore roundtrips but not a repair-on-integrity-failure scenario (`tests/integration/test_backup_recovery_integration.py:115-194`). Because AC-20.6 is specifically about integrity failure and attempted recovery (`docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md:99`), the current evidence bundle claims more than the repo proves.
  - **Medium:** The shared project closeout is incomplete, so the correlated handoff set is not yet consistent with the execution plan’s required outputs. The task file still leaves every post-project item unchecked (`docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md:36-46`); `docs/BUILD_PLAN.md` still shows Phase 2A as in progress, Phase 3 as not started, and MEU-20/21/22 as pending (`docs/BUILD_PLAN.md:61-62`, `docs/BUILD_PLAN.md:151-152`, `docs/BUILD_PLAN.md:160`, `docs/BUILD_PLAN.md:463-464`); `.agent/context/meu-registry.md` still stops at MEU-19 and has no Phase 3 section (`.agent/context/meu-registry.md:39-59`); the reflection, commit-messages, and session-state files are absent; and `docs/execution/metrics.md` has no `backup-recovery-config-image` row. The code may be mostly green, but the project-level evidence bundle is not complete enough to approve the implementation set.
- Open questions:
  - For MEU-21, do you want to align the implementation back to the documented `build_export(user_settings, defaults)` / `validate_import({"settings": ...})` contract, or revise the build-plan and downstream callers to a resolved-values API? Right now the implementation and local canon disagree.
  - For MEU-20, what is the intended corrupted-database fixture strategy for AC-20.6? The current handoff claims that path was tested, but the repository does not contain that test.
- Verdict:
  - `changes_required`
- Residual risk:
  - The backup recovery and image-processing code paths are broadly green, but the config export/import contract is currently incompatible with the documented payload shape, the repair branch in backup recovery is still not actually evidenced, and the project cannot be treated as complete while the status hubs and closeout artifacts remain stale.
- Anti-deferral scan result:
  - Failed at project level: the three MEU handoffs exist, but the plan-required post-project deliverables and shared hub updates have not been completed.

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this review-only task.
- Blocking risks:
  - Import/export contract drift could propagate into future REST/GUI work if approved as-is.
- Verdict:
  - Not applicable.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Implementation reviewed; corrections required before approval.
- Next steps:
  - Align MEU-21’s `ConfigExportService` with the `02a §2A.5` contract and add a round-trip test that validates the exported payload shape.
  - Replace the false `test_repair_corrupted_db` claim in handoff `021` with a real corrupted-database repair test or lower the claim explicitly.
  - Complete the post-project closeout in `task.md`, `docs/BUILD_PLAN.md`, `.agent/context/meu-registry.md`, `docs/execution/metrics.md`, the reflection file, `session-state.md`, and `commit-messages.md` before requesting another implementation recheck.

---

## Recheck Update — 2026-03-08

### Scope

- Rechecked the previously reported blockers against the current repo state after updates to `config_export.py`, `test_config_export.py`, `test_backup_recovery.py`, and the correlated project artifacts.

### Commands Executed

- `Get-Content packages/core/src/zorivest_core/domain/config_export.py`
- `Get-Content tests/unit/test_config_export.py`
- `Get-Content tests/unit/test_backup_recovery.py`
- `Get-Content .agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md`
- `Get-Content .agent/context/handoffs/022-2026-03-08-config-export-bp02as2A.5.md`
- `Get-Content .agent/context/handoffs/023-2026-03-08-image-processing-bp03sIMG.md`
- `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md`
- `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md`
- `Get-Content docs/BUILD_PLAN.md`
- `Get-Content .agent/context/meu-registry.md`
- `Get-Content docs/execution/metrics.md`
- `uv run pytest tests/unit/test_backup_recovery.py -q`
- `uv run pytest tests/unit/test_config_export.py -q`
- `uv run pytest tests/unit/test_image_processing.py -q`
- `uv run pytest tests/ -q`
- `uv run pyright packages/`
- `uv run ruff check packages/`
- `uv run python tools/validate_codebase.py --scope meu`
- `rg -n ...` sweeps across the config export contract, repair test evidence, task checklist, BUILD_PLAN, and MEU registry

### Results

- The prior `validate_import(build_export(...))` bug is fixed: `validate_import()` now reads `import_data.get("settings", {})` and the new round-trip test passes.
- The prior AC-20.6 evidence gap is materially reduced: `test_repair_corrupted_database` now exists in `tests/unit/test_backup_recovery.py`.
- Current verification is green:
  - `tests/unit/test_backup_recovery.py` → `13 passed`
  - `tests/unit/test_config_export.py` → `17 passed`
  - `tests/unit/test_image_processing.py` → `16 passed`
  - full regression → `501 passed, 1 skipped`
  - `pyright packages/` → clean
  - `ruff check packages/` → clean
  - MEU gate → pass, with advisory only: `021-2026-03-08-backup-recovery-bp02as2A.4.md missing: Evidence/FAIL_TO_PASS`

### Findings By Severity

- **Medium:** `ConfigExportService` still does not match the documented/local-canon build contract even though the nested import bug is fixed. The spec still defines `build_export(self, user_settings, defaults)` and resolves values through the resolver (`docs/build-plan/02a-backup-restore.md:711-718`), and the execution plan still marks the `SettingsResolver` dependency as resolved (`docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md:99-111`). The shipped implementation instead exposes `build_export(self, resolved_values)` and contains no resolver dependency at all (`packages/core/src/zorivest_core/domain/config_export.py:55-70`, `packages/core/src/zorivest_core/domain/config_export.py:81-105`). The tests now correctly exercise nested import payloads, but they still codify the same `resolved_values=` API (`tests/unit/test_config_export.py:86`, `tests/unit/test_config_export.py:101`, `tests/unit/test_config_export.py:149`, `tests/unit/test_config_export.py:157`, `tests/unit/test_config_export.py:222`). This is now a contract-drift problem rather than a broken round-trip, but it still leaves the implementation out of alignment with the project canon that future callers are expected to follow.
- **Medium:** Project closeout and shared-review state are still incomplete, so the correlated implementation set cannot be approved. `task.md` still leaves all three `Codex validation` items unchecked plus every post-project item unchecked (`docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md:18`, `docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md:26`, `docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md:34`, `docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md:38-46`). `docs/BUILD_PLAN.md` still shows Phase 2A in progress, Phase 3 not started, and MEU-20/21/22 pending (`docs/BUILD_PLAN.md:61-62`, `docs/BUILD_PLAN.md:151-152`, `docs/BUILD_PLAN.md:160`, `docs/BUILD_PLAN.md:463-464`). `.agent/context/meu-registry.md` still stops at MEU-19 and has no Phase 3 section (`.agent/context/meu-registry.md:39-59`). The three MEU handoffs still show reviewer output as awaiting Codex validation (`.agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md:87-88`, `.agent/context/handoffs/022-2026-03-08-config-export-bp02as2A.5.md:70-71`, `.agent/context/handoffs/023-2026-03-08-image-processing-bp03sIMG.md:71-72`), and handoff `022` still reports `16 unit tests` even though the current suite is `17 passed` (`.agent/context/handoffs/022-2026-03-08-config-export-bp02as2A.5.md:75`). The reflection file, `commit-messages.md`, and `session-state.md` are still absent, and `docs/execution/metrics.md` still has no `backup-recovery-config-image` row.

### Open Questions

- Should MEU-21 be brought back to the `build_export(user_settings, defaults)` plus resolver-based contract, or do you want the build-plan and downstream integration points revised to accept the shipped `resolved_values` API?

### Verdict

- `changes_required`

### Residual Risk

- The code now looks functionally healthy under test, but approval would still lock in an unresolved contract drift for config export and leave the project’s shared evidence/state artifacts inconsistent with the implementation that was just validated.

---

## Recheck Update — 2026-03-08 (Pass 3)

### Scope

- Rechecked the post-correction state after updates to the build-plan spec, project closeout artifacts, shared status hubs, and the three MEU handoffs.

### Commands Executed

- `Get-Content docs/build-plan/02a-backup-restore.md | Select-Object -Skip 705 -First 40`
- `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md`
- `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/task.md`
- `Get-Content docs/BUILD_PLAN.md`
- `Get-Content .agent/context/meu-registry.md`
- `Get-Content docs/execution/metrics.md`
- `Get-Content docs/execution/reflections/2026-03-08-backup-recovery-config-image-reflection.md`
- `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/session-state.md`
- `Get-Content docs/execution/plans/2026-03-08-backup-recovery-config-image/commit-messages.md`
- `Get-Content .agent/context/handoffs/021-2026-03-08-backup-recovery-bp02as2A.4.md`
- `Get-Content .agent/context/handoffs/022-2026-03-08-config-export-bp02as2A.5.md`
- `Get-Content .agent/context/handoffs/023-2026-03-08-image-processing-bp03sIMG.md`
- `uv run python tools/validate_codebase.py --scope meu`
- `uv run pytest tests/ -q`
- `rg -n ...` sweeps for spec alignment, BUILD_PLAN counts, implementation-plan status rows, and handoff evidence markers

### Results

- The config-export contract drift is resolved at the spec level: `docs/build-plan/02a-backup-restore.md` now documents the shipped `resolved_values` API and upstream resolution model.
- The missing project closeout artifacts are now present: reflection, metrics row, session-state, commit-messages, BUILD_PLAN phase rows, MEU registry rows, and handoff reviewer statuses are all updated.
- Current verification is green:
  - full regression → `501 passed, 1 skipped`
  - MEU gate → pass, with advisory only: `023-2026-03-08-image-processing-bp03sIMG.md missing: Evidence/FAIL_TO_PASS`

### Findings By Severity

- **Medium:** `docs/BUILD_PLAN.md` is still internally inconsistent because the phase tracker and MEU rows were updated but the MEU summary counts were not. The same file now marks Phase 2A complete, Phase 3 complete, and MEU-20/21/22 approved (`docs/BUILD_PLAN.md:61-62`, `docs/BUILD_PLAN.md:151-152`, `docs/BUILD_PLAN.md:160`), but the summary table still reports only `5` completed for `P0 — Phase 2/2A`, `0` completed for `P0 — Phase 3/4`, and `19` total completed (`docs/BUILD_PLAN.md:463-476`). That leaves the canonical hub contradicting itself about project completion.
- **Low:** The execution-plan companion docs are still not fully reconciled with the final project state. `implementation-plan.md` still leaves the completion-oriented task rows unchecked (`docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md:30-55`), still advertises a `SettingsResolver dependency` for MEU-21 (`docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md:111`), and still describes the BUILD_PLAN change as `Phase 3 status ... → 🔵 In Progress` plus summary-count updates that do not match the actual final hub state (`docs/execution/plans/2026-03-08-backup-recovery-config-image/implementation-plan.md:215-219`). Separately, the MEU gate still emits an evidence-bundle advisory for handoff `023`, which means the handoff set is approved but not perfectly clean from the validator’s perspective.

### Verdict

- `changes_required`

### Residual Risk

- Product behavior appears sound and the prior code-level blockers are resolved. The remaining risk is auditability: the canonical status documents still disagree about how much of the project is complete, which will create avoidable confusion for the next planning or review pass.
