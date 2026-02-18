# Task Handoff

## Task

- **Date:** 2026-02-18
- **Task slug:** build-plan-release-versioning-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of release/versioning architecture updates in `00-overview.md`, `07-distribution.md`, and `dependency-manifest.md`.

## Inputs

- User request:
  - Review recent build-plan updates for Release & Versioning Architecture.
  - Produce a critical-review handoff in `.agent/context/handoffs`.
- Specs/docs referenced:
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/07-distribution.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first, severity-ranked, with concrete file/line evidence.
  - Focus on behavioral/regression/release risk, not style.

## Role Plan

1. orchestrator
2. reviewer
3. coder (doc output only)
4. tester (doc consistency verification)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-18-build-plan-release-versioning-critical-review.md` (new)
- Design notes:
  - Documentation-only review artifact; no runtime code changes.
- Commands run:
  - `git diff -- docs/build-plan/00-overview.md docs/build-plan/07-distribution.md docs/build-plan/dependency-manifest.md`
  - `Get-Content` with line numbering for evidence capture
  - `rg -n` for cross-file contract tracing
- Results:
  - Multiple release-pipeline and version-contract defects identified, including release-blocking verification drift.

## Tester Output

- Commands run:
  - Documentation consistency inspection only.
- Pass/fail matrix:
  - Not applicable (no executable code changed).
- Repro failures:
  - Not applicable.
- Coverage/test gaps:
  - New release/versioning docs do not specify tests for SemVer-to-PEP440 conversion correctness in publish verification.

## Reviewer Output

- Findings by severity:

  - **Critical:** Post-publish verification uses raw tag name, but version architecture requires transformed versions (`v` stripping + SemVer→PEP440).
    - Evidence:
      - Pre-release translation is explicitly required: `docs/build-plan/07-distribution.md:34`, `docs/build-plan/07-distribution.md:37`.
      - Version bump flow tags releases as `vX.Y.Z`: `docs/build-plan/07-distribution.md:84`.
      - Release trigger is tag-based (`v*.*.*`): `docs/build-plan/07-distribution.md:271`.
      - Verification installs/checks registries using `${{ github.ref_name }}` directly: `docs/build-plan/07-distribution.md:388`, `docs/build-plan/07-distribution.md:389`.
    - Risk:
      - Verification fails for stable tags (`v1.0.0`) and pre-releases (`v1.0.0-beta.1`), causing false-negative release failures.
    - Recommendation:
      - Normalize tag once (`v` removal + PEP440 conversion for PyPI) and pass normalized outputs through workflow job outputs/artifacts.

  - **Critical:** Dev-mode version resolution path is incorrect for documented package layout, so `.version` lookup can fail at runtime.
    - Evidence:
      - Dev fallback uses `Path(__file__).resolve().parents[3] / ".version"`: `docs/build-plan/07-distribution.md:57`.
      - Documented backend entrypoint location is `packages/api/src/zorivest_api/__main__.py`: `docs/build-plan/07-distribution.md:106`.
      - Single source of truth is root `.version`: `docs/build-plan/07-distribution.md:17`.
    - Risk:
      - `GET /version` in development can raise file-not-found errors and break diagnostics.
    - Recommendation:
      - Resolve repo root robustly (for example: ascend until `.version` exists) and raise explicit errors if missing.

  - **High:** TypeScript CI job uses root `npm ci`, but dependency/install contracts describe package-local installs (`mcp-server/`, `ui/`).
    - Evidence:
      - Install flow runs `npm init/install` inside `mcp-server` and `ui` directories: `docs/build-plan/dependency-manifest.md:35`, `docs/build-plan/dependency-manifest.md:48`.
      - CI runs `npm ci` from repo root in both TS jobs: `docs/build-plan/07-distribution.md:240`, `docs/build-plan/07-distribution.md:262`.
      - Monorepo structure documents `package.json` in each TS package directory: `docs/build-plan/01-domain-layer.md:86`, `docs/build-plan/01-domain-layer.md:97`.
    - Risk:
      - CI can fail or run against wrong dependency graph unless a root workspace contract is added.
    - Recommendation:
      - Use per-package working directories in CI or formally define npm workspaces at repo root and update docs consistently.

  - **High:** Backend release build depends on `pyinstaller` through `uv run`, but dependency manifest installs it outside the locked `uv` environment.
    - Evidence:
      - Manifest installs with `pip install pyinstaller`: `docs/build-plan/dependency-manifest.md:51`.
      - Release pipeline executes `uv sync --frozen` then `uv run pyinstaller`: `docs/build-plan/07-distribution.md:294`, `docs/build-plan/07-distribution.md:295`.
      - Phase goal claims secure, reproducible pipelines: `docs/build-plan/07-distribution.md:9`.
    - Risk:
      - Reproducibility is weakened and CI may fail if `pyinstaller` is absent from the uv environment.
    - Recommendation:
      - Move `pyinstaller` into uv-managed dependencies (pinned + lockfile) or install an explicitly pinned version in workflow before use.

  - **High:** `GET /version` is introduced in distribution docs but has no explicit Phase 4 REST contract section.
    - Evidence:
      - Distribution phase states REST exposes `GET /version`: `docs/build-plan/07-distribution.md:61`.
      - Phase 4 route docs enumerate `/api/v1/*` route groups (trades/settings/guard/auth) but no version section: `docs/build-plan/04-rest-api.md:13`, `docs/build-plan/04-rest-api.md:178`, `docs/build-plan/04-rest-api.md:459`.
    - Risk:
      - Endpoint path/auth/response semantics may drift between teams or be omitted in implementation.
    - Recommendation:
      - Add an explicit Phase 4 contract for version endpoint (path, schema, auth requirement, and tests).

  - **Medium:** Build-priority item count references were updated to 74, but current matrix still terminates at item 68.
    - Evidence:
      - Overview cross-reference says matrix has 74 items: `docs/build-plan/00-overview.md:77`.
      - Matrix header also claims 74 items: `docs/build-plan/build-priority-matrix.md:3`.
      - Final numbered row is 68 (`67a` exists, but no 69–74 rows): `docs/build-plan/build-priority-matrix.md:161`.
    - Risk:
      - Planning/tracking confusion and unreliable progress accounting.
    - Recommendation:
      - Reconcile numbering/count claims and ensure matrix row count matches overview references.

  - **Medium:** Python type-check command in CI is undocumented in dependency manifest mapping.
    - Evidence:
      - CI uses `uv run mypy packages/core/src`: `docs/build-plan/07-distribution.md:232`.
      - Cross-cutting manifest mapping omits `mypy`: `docs/build-plan/dependency-manifest.md:76`.
    - Risk:
      - CI dependency drift and unclear canonical type-check toolchain.
    - Recommendation:
      - Add `mypy` to manifest (if intended) or replace CI command with the documented checker.

- Open questions:
  - Should version endpoint be `/version` or `/api/v1/version` for consistency with other REST routes?
  - Is the intended TS dependency model root workspaces or per-package installs only?
  - Should publish verification consume normalized version outputs from `verify-version` rather than recomputing from `github.ref_name`?

- Verdict:
  - Release/versioning architecture is much stronger, but **not implementation-safe yet** due two critical release-path defects and unresolved CI contract inconsistencies.

- Residual risk:
  - If implemented as written, likely outcomes are broken release verification, fragile version diagnostics in dev mode, and intermittent CI failures in TS/backend build jobs.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review output.
- Blocking risks:
  - No runtime changes in this task; blockers are design-contract level only.
- Verdict:
  - Safe to proceed with targeted docs correction before implementation.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed and documented.
- Next steps:
  1. Fix version normalization pipeline first (`tag -> semver -> pep440`) and wire it into verification jobs.
  2. Correct dev version path resolution and formalize `GET /version` in Phase 4 with tests.
  3. Align CI dependency/install model (TS package directories, pyinstaller source, type-check tool declaration).
