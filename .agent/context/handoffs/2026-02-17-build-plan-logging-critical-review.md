# Task Handoff

## Task

- **Date:** 2026-02-17
- **Task slug:** build-plan-logging-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of all `docs/build-plan/*.md` files, with deep focus on `docs/build-plan/01a-logging.md`, including web validation of logging approach.

## Inputs

- User request:
  - Critically review `docs/build-plan/` with emphasis on logging design in `01a-logging.md`.
  - Create a feedback handoff document under `.agent/context/handoffs`.
  - Perform web search to validate logging implementation approach.
- Specs/docs referenced:
  - `docs/build-plan/*.md` (all 24 files)
  - `.agent/context/handoffs/TEMPLATE.md`
  - `SOUL.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
- External sources used:
  - Python `logging.handlers` (`QueueHandler` / `QueueListener`): https://docs.python.org/3/library/logging.handlers.html
  - Python logging cookbook (`__name__`, `contextvars`, multiprocess caveats): https://docs.python.org/3/howto/logging-cookbook.html
  - Python logging docs (thread safety): https://docs.python.org/3/library/logging.html
  - FastAPI middleware docs: https://fastapi.tiangolo.com/tutorial/middleware/
  - Uvicorn settings (`--log-config`) docs: https://www.uvicorn.org/settings/
  - Uvicorn default loggers (`uvicorn`, `uvicorn.error`, `uvicorn.access`): https://raw.githubusercontent.com/encode/uvicorn/master/uvicorn/config.py
  - python-json-logger docs and latest release metadata: https://pypi.org/project/python-json-logger/ and https://nhairs.github.io/python-json-logger/latest/quickstart/
  - OWASP logging cheat sheet (sensitive-data exclusions): https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- Constraints:
  - Findings-first, severity-ranked.
  - Concrete file/line evidence.
  - Emphasize behavior/regression risk and integration safety.

## Role Plan

1. orchestrator
2. reviewer
3. coder (doc output only)
4. tester (verification via doc consistency checks and source validation)
- Optional roles: researcher (used), guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-17-build-plan-logging-critical-review.md` (new)
- Design notes:
  - Documentation-only review output; no product code changes.
  - Included cross-file contract checks and external standards validation.
- Commands run:
  - `rg --files docs/build-plan`
  - `rg -n` for logging/settings/logger contract tracing
  - `Get-Content` with line numbers for cited files
  - Markdown link integrity check script (PowerShell)
  - Web source retrieval for official logging guidance
- Results:
  - Critical design and integration issues identified, especially in logger namespace routing and settings key contracts.

## Tester Output

- Commands run:
  - Structural review commands only (doc review task).
- Pass/fail matrix:
  - Not applicable (no runnable code changed).
- Repro failures:
  - Not applicable.
- Coverage/test gaps:
  - Logging-route and logging-config integration tests are underspecified for cross-phase behavior (`01a` + `04` + `06`).

## Reviewer Output

- Findings by severity:

  - **Critical:** Logger namespace contract is internally inconsistent; most logs will not route to feature files as specified.
    - Evidence:
      - Routing expects `zorivest.*` prefixes (`docs/build-plan/01a-logging.md:90`, `docs/build-plan/01a-logging.md:216`, `docs/build-plan/01a-logging.md:349`).
      - Usage guidance says `logging.getLogger(__name__)` (`docs/build-plan/01a-logging.md:150`, `docs/build-plan/01a-logging.md:439`, `docs/build-plan/01a-logging.md:703`).
      - Package names are `zorivest_core`, `zorivest_infra`, `zorivest_api` (`docs/build-plan/01-domain-layer.md:56`, `docs/build-plan/01-domain-layer.md:76`), so `__name__` will not naturally match `zorivest.*`.
    - Risk:
      - Silent log loss due to `FeatureFilter` dropping unmatched logger names.
    - Recommendation:
      - Pick one canonical strategy and apply it across docs:
        - Option A: keep `__name__`, then route by actual package prefixes (`zorivest_core.*`, `zorivest_infra.*`, `zorivest_api.*`, `uvicorn.*`).
        - Option B: require explicit feature loggers (`logging.getLogger("zorivest.trades")`, etc.) and ban `__name__` for routed events.

  - **Critical:** Frontend log ingestion route cannot reach `app.jsonl` with current filter map.
    - Evidence:
      - API route uses `logging.getLogger("zorivest.frontend")` (`docs/build-plan/04-rest-api.md:259`).
      - `FEATURES` only defines `zorivest.app` / `zorivest.api` and no `zorivest.frontend` (`docs/build-plan/01a-logging.md:225`, `docs/build-plan/01a-logging.md:226`).
      - Phase 4 claims those frontend logs route to `app.jsonl` (`docs/build-plan/04-rest-api.md:248`).
    - Risk:
      - Startup metrics appear “sent” from GUI but are not persisted in the intended feature file.
    - Recommendation:
      - Either change logger to `zorivest.app` in Phase 4, or add `frontend` to `FEATURES` and map it explicitly.

  - **Critical:** Startup metric payload is discarded by formatter contract.
    - Evidence:
      - GUI sends structured metric object in `data` (`docs/build-plan/06-gui.md:94` to `docs/build-plan/06-gui.md:99`).
      - API forwards it in `extra={"data": entry.data}` (`docs/build-plan/04-rest-api.md:273`, `docs/build-plan/04-rest-api.md:274`).
      - `JsonFormatter` does not include `data` or arbitrary extra fields (`docs/build-plan/01a-logging.md:380` to `docs/build-plan/01a-logging.md:384`).
    - Risk:
      - Observability regression: emitted startup metrics are reduced to message text and cannot be queried structurally.
    - Recommendation:
      - Add `data` to allowed extras or include all safe non-reserved extras in formatter output.

  - **High:** Rotation settings key contract is conflicting across files (global vs per-feature).
    - Evidence:
      - `configure_from_settings` reads per-feature keys (`logging.{feature}.rotation_mb`, `logging.{feature}.backup_count`) (`docs/build-plan/01a-logging.md:282`, `docs/build-plan/01a-logging.md:285`).
      - Settings section and GUI define global keys (`logging.rotation_mb`, `logging.backup_count`) (`docs/build-plan/01a-logging.md:470`, `docs/build-plan/01a-logging.md:471`, `docs/build-plan/06f-gui-settings.md:370`, `docs/build-plan/06f-gui-settings.md:371`).
    - Risk:
      - GUI updates will not affect handler configuration as documented.
    - Recommendation:
      - Choose one contract:
        - Global only (apply fallback to all handlers), or
        - Per-feature plus optional global defaults.
      - Document exact precedence and update all phase docs consistently.

  - **High:** Severity-level contract drift (`CRITICAL` is defined in architecture but excluded in GUI controls).
    - Evidence:
      - Logging architecture says same five levels (`DEBUG`–`CRITICAL`) (`docs/build-plan/01a-logging.md:23`).
      - Logging settings GUI offers only four levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`) (`docs/build-plan/06f-gui-settings.md:366` to `docs/build-plan/06f-gui-settings.md:369`).
    - Risk:
      - Inability to configure full documented severity range.
    - Recommendation:
      - Add `CRITICAL` to GUI options or revise architecture docs to a four-level policy.

  - **Medium:** `POST /api/v1/logs` level input is underspecified and may fail at runtime for unexpected strings.
    - Evidence:
      - `level` is unconstrained `str` (`docs/build-plan/04-rest-api.md:263`).
      - Handler dispatch uses `getattr(logger, entry.level, logger.info)` (`docs/build-plan/04-rest-api.md:272`).
    - Risk:
      - Non-log-method values can produce non-callable attributes and 500s.
    - Recommendation:
      - Use `Literal["debug","info","warning","error","critical"]` and normalize case.

  - **Medium:** Dependency/implementation drift around `python-json-logger`.
    - Evidence:
      - Docs say use `python-json-logger` and add dependency (`docs/build-plan/01a-logging.md:82`, `docs/build-plan/01a-logging.md:661`, `docs/build-plan/dependency-manifest.md:27`).
      - Proposed implementation uses custom `JsonFormatter` and no `python-json-logger` API (`docs/build-plan/01a-logging.md:363`).
    - Risk:
      - Unnecessary dependency or unclear formatter ownership.
    - Recommendation:
      - Decide explicitly:
        - Keep custom formatter and drop dependency, or
        - Use `pythonjsonlogger` formatter directly.
      - If keeping dependency, pin with an explicit major range aligned to current release policy.

  - **Medium:** Build-order wording conflicts remain in shared docs.
    - Evidence:
      - Logging says “Build this first” (`docs/build-plan/01a-logging.md:5`) and matrix places `1A` before `1` (`docs/build-plan/build-priority-matrix.md:11`).
      - Same matrix still states first production code must be `calculator.py` (`docs/build-plan/build-priority-matrix.md:154`) and overview repeats first-line rule (`docs/build-plan/00-overview.md:60`).
    - Risk:
      - Team execution drift on day-zero implementation sequence.
    - Recommendation:
      - Resolve to one explicit rule: parallel start, or strict calculator-first, and update all references.

  - **Medium:** Workspace package install command for logging dependency is ambiguous.
    - Evidence:
      - Command uses `uv add python-json-logger` without package scoping (`docs/build-plan/dependency-manifest.md:27`).
      - Mapping table says Phase 1A dependency belongs to `zorivest-infra` (`docs/build-plan/dependency-manifest.md:69`).
    - Risk:
      - Dependency may land in the wrong package in a monorepo.
    - Recommendation:
      - Use `uv add --package zorivest-infra python-json-logger`.

- Web validation summary:
  - Core direction is sound:
    - `QueueHandler`/`QueueListener` for decoupled producer/consumer logging is aligned with Python docs.
    - `respect_handler_level=True` is the correct way to enforce per-handler levels in listener dispatch.
    - Thread safety claims are consistent with stdlib logging guarantees.
  - Gaps versus best practice:
    - Official Python guidance commonly uses module loggers (`__name__`), so custom prefix-routing requires explicit namespace policy and cannot be assumed.
    - Uvicorn has its own logger namespaces (`uvicorn`, `uvicorn.error`, `uvicorn.access`); if API/server logs are desired in feature files, mapping/config must account for these.
    - Sensitive-data handling should include structured payloads/extras, not only message strings (OWASP guidance).

- Open questions:
  - Should canonical logger names be feature-centric (`zorivest.<feature>`) or module-centric (`__name__`)? If module-centric, what is the exact routing map?
  - Do you want one global rotation policy or per-feature rotation policy with global fallback?
  - Should frontend telemetry stay in `app.jsonl` or move to dedicated `frontend.jsonl`?
  - Should API server logs include `uvicorn.*` by default in `api.jsonl`?

- Verdict:
  - Logging architecture choice is fundamentally solid, but current docs are **not integration-safe** due namespace, key, and formatter contract drift across Phases 1A/4/6.

- Residual risk:
  - If unresolved before implementation, expected observability will silently fail (dropped logs, missing structured metrics, non-functional runtime settings).

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only task; no runtime changes made.
- Blocking risks:
  - None for this handoff artifact itself.
- Verdict:
  - Safe to proceed with doc correction pass before coding Phase 1A.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Full build-plan review completed with deep logging validation and web-backed recommendations.
- Next steps:
  1. Resolve the four open contract decisions (logger namespace, frontend logger target file, rotation key scheme, and formatter extra-field policy).
  2. Patch `01a-logging.md`, `04-rest-api.md`, `06f-gui-settings.md`, `00-overview.md`, `build-priority-matrix.md`, and `dependency-manifest.md` in one consistency change set.
  3. Re-run a focused reviewer pass to verify zero cross-file contract drift before implementation starts.
