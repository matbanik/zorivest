# Task Handoff Template

## Task

- **Date:** 2026-02-28
- **Task slug:** docs-build-plan-foundation-coding-readiness-critical-review
- **Owner role:** orchestrator
- **Scope:** Critical review of coding readiness for `docs/build-plan/00-overview.md`, `01-domain-layer.md`, `01a-logging.md`, `02-infrastructure.md`, `02a-backup-restore.md`, and dependency strategy validation.

## Inputs

- User request:
  - Run critical review with coding-readiness focus.
  - Validate planned approach with web research.
  - Identify testing/implementation/dependency-management issues.
- Specs/docs referenced:
  - `.agent/workflows/critical-review-feedback.md`
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/01a-logging.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/02a-backup-restore.md`
  - `docs/build-plan/dependency-manifest.md`
- Constraints:
  - Review-only; do not patch product docs.
  - Findings-first output with file/line evidence.
  - Include external validation sources.

## Role Plan

1. orchestrator
2. tester
3. reviewer
4. coder (not used; no fix request)
- Optional roles: researcher (used for web validation), guardrail (not required)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-28-docs-build-plan-foundation-coding-readiness-critical-review.md` (new review handoff)
- Design notes:
  - No product changes; review-only session.
- Commands run:
  - file-state and grep sweeps
  - line-numbered evidence extraction
  - web research queries (Python/SQLAlchemy/SQLite/uv/PyPA/SQLCipher/PyPI)
- Results:
  - Review artifacts compiled with severity-ranked findings and web-backed recommendations.

## Tester Output

- Commands run:
  - `git status --short -- docs/build-plan`
  - `rg -n "Goal|Implementation Tasks|Testing|Validation|Dependencies|dependency|uv |pip |pydantic|sqlalchemy|sqlcipher|WAL|journal_mode|Float|Decimal|Numeric|backup|restore|SettingsValidator|QueueHandler|os\\.uname|passphrase|TODO|TBD|placeholder" docs/build-plan/00-overview.md docs/build-plan/01-domain-layer.md docs/build-plan/01a-logging.md docs/build-plan/02-infrastructure.md docs/build-plan/02a-backup-restore.md docs/build-plan/dependency-manifest.md`
  - line-number dumps for each target file using `Get-Content` with explicit numbering
  - web queries against primary sources (`python.org`, `sqlalchemy.org`, `sqlite.org`, `docs.astral.sh`, `packaging.python.org`, `zetetic.net`)
- Pass/fail matrix:
  - DR-1 Claim-to-state match: **fail** (multiple cross-doc contract drifts)
  - DR-2 Residual old/contradictory terms: **fail**
  - DR-3 Downstream references updated: **partial fail** (settings/repo contracts drift across phases)
  - DR-4 Verification robustness: **fail** (tests don’t exercise WAL/concurrency assumptions)
  - DR-5 Evidence auditability: **pass** (all findings line-referenced)
- Repro failures:
  - `SettingsValidator.validate()` logic appears unreachable due indentation after `_resolve_spec` return block.
  - Method signature mismatch between `BackupRecoveryManager` API and integration tests.
- Coverage/test gaps:
  - No explicit concurrency test proving WAL + per-thread session behavior.
  - Backup/restore test snippets include placeholder assertions, not concrete corruption/recovery checks.
- Evidence bundle location:
  - This handoff plus cited source links in Reviewer Output.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable (docs review only).
- Mutation score:
  - Not applicable.
- Contract verification status:
  - **Failed** for several cross-phase interfaces and setting key contracts.

## Reviewer Output

- Findings by severity:

  - **Critical**
    - `SettingsValidator` control flow is broken in sample implementation: stage-1/2/3 validation logic is indented under `_resolve_spec` after `return None`, so `validate()` returns early for unknown keys but does not execute validation pipeline for valid keys.  
      Evidence: `docs/build-plan/02a-backup-restore.md:262-299`

  - **High**
    - Settings key contract drift across Phase 1/2/2A:
      - Domain enums use positive visibility flags (`dollar_visible`, `percent_visible`).
      - Infrastructure notes also reference `display.dollar_visible` and `display.percent_visible`.
      - 2A defaults/tests use `display.hide_dollars` and `display.hide_percentages`.
      This creates serialization/API drift and migration ambiguity.  
      Evidence: `docs/build-plan/01-domain-layer.md:191-196`, `docs/build-plan/02-infrastructure.md:156-160`, `docs/build-plan/02a-backup-restore.md:52-54`, `docs/build-plan/02a-backup-restore.md:854-867`

    - Repository contract drift between Phase 1 ports and Phase 2 usage:
      - Port defines `ImageRepository.save(owner_type, owner_id, image)` and `get_for_owner(...)`.
      - Integration tests call `img_repo.save("TRADE1", image)` and `get_for_trade("TRADE1")`.
      Evidence: `docs/build-plan/01-domain-layer.md:468-474`, `docs/build-plan/02-infrastructure.md:420`, `docs/build-plan/02-infrastructure.md:437`

    - Backup manager API/test mismatch:
      - Class signatures show `restore_backup(self, backup_path)` / `verify_backup(self, backup_path)` with session-held passphrase.
      - Tests call both with explicit `passphrase` parameter.
      Evidence: `docs/build-plan/02a-backup-restore.md:600-614`, `docs/build-plan/02a-backup-restore.md:930-935`

    - `ConfigExportService.build_export()` references `self._app_version` without initialization in shown constructor, creating an immediate implementation error as written.
      Evidence: `docs/build-plan/02a-backup-restore.md:705-721`

    - Phase-1 dependency contradiction:
      - Domain plan says commands/DTOs use Pydantic in Phase 1.
      - Dependency manifest adds Pydantic in Phase 4 only.
      Evidence: `docs/build-plan/01-domain-layer.md:9`, `docs/build-plan/dependency-manifest.md:14-16`, `docs/build-plan/dependency-manifest.md:27`

  - **Medium**
    - Logging doc contradiction for `__name__` logger routing:
      - Policy table says `__name__` routes to `misc.jsonl`.
      - Example comment says it routes to `app.jsonl`.
      Evidence: `docs/build-plan/01a-logging.md:119`, `docs/build-plan/01a-logging.md:128`, `docs/build-plan/01a-logging.md:134`

    - Windows portability bug in logging snippet: `os.uname()` is used directly for Darwin detection. `os.uname` is Unix-only per Python docs.
      Evidence: `docs/build-plan/01a-logging.md:293-300`

    - Monetary fields use SQLAlchemy `Float` widely, increasing rounding risk for finance/tax values.
      Evidence: `docs/build-plan/02-infrastructure.md:29-33`, `98-100`, `142`, `231-235`, `279`, `293-295`, `341`

    - WAL requirement is declared critical, but integration fixture uses plain in-memory SQLite without WAL/thread config, so tests won’t validate intended concurrency behavior.
      Evidence: `docs/build-plan/02-infrastructure.md:365-377`, `docs/build-plan/02-infrastructure.md:389-393`

    - Backup settings terminology drift: setting says “gzip compression” while architecture is AES-encrypted ZIP (`.zvbak` via `pyzipper`), making operator expectations unclear.
      Evidence: `docs/build-plan/02a-backup-restore.md:57`, `docs/build-plan/02a-backup-restore.md:490-497`

  - **Low**
    - Dependency manifest cross-cutting table includes `pyright`, but installation commands never add `pyright` explicitly.
      Evidence: `docs/build-plan/dependency-manifest.md:31`, `docs/build-plan/dependency-manifest.md:91`
    - `pip-audit` appears duplicated in two phases.
      Evidence: `docs/build-plan/dependency-manifest.md:31`, `docs/build-plan/dependency-manifest.md:53`

- Open questions:
  - Canonical settings key naming: keep `display.hide_*` or `display.*_visible`?
  - Canonical image repository API: owner-typed generic or trade-specific convenience methods?
  - Should passphrase be session-held only, or method-parameterized for recovery flows/tests?

- Verdict:
  - **changes_required**

- Residual risk:
  - Implementers may build to conflicting contracts, causing Phase 3+ churn.
  - Financial precision and concurrency assumptions are under-specified relative to stated requirements.
  - Dependency process lacks explicit lock/sync guardrails for reproducible builds.

- Anti-deferral scan result:
  - Several issues are compile-time/interface blockers and should be corrected in docs before implementation starts.

### External Validation Notes (Primary Sources)

- Python logging queue architecture: stdlib `QueueHandler` / `QueueListener` are intended for decoupled async logging pipelines.  
  Source: https://docs.python.org/3/library/logging.handlers.html
- `os.uname` availability is Unix-only (not Windows).  
  Source: https://docs.python.org/3/library/os.html#os.uname
- SQLite thread/session constraints and SQLAlchemy guidance:
  - Session-per-thread model and no cross-thread Session sharing.  
    Source: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
  - SQLite in-memory multi-thread caveats (`StaticPool`, same connection).  
    Source: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads
- Financial precision: SQLAlchemy `Numeric` with Decimal semantics is the safer choice for exact numeric values than `Float`.  
  Source: https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Numeric
- WAL behavior/details:  
  Source: https://sqlite.org/wal.html
- SQLCipher recovery ops referenced in plan (`cipher_migrate`, `sqlcipher_export`) are valid mechanisms.  
  Source: https://www.zetetic.net/sqlcipher/sqlcipher-api/
- Dependency management:
  - `uv` supports dependency groups and lock/sync workflow for reproducibility.  
    Sources: https://docs.astral.sh/uv/concepts/projects/dependencies/ , https://docs.astral.sh/uv/concepts/projects/sync/
  - Packaging guidance on dependency specification (`install_requires` vs requirements files).  
    Source: https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/

## Guardrail Output (If Required)

- Safety checks:
  - Not required for docs-only review.
- Blocking risks:
  - N/A
- Verdict:
  - N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Review complete; multiple blocking readiness issues remain.
- Next steps:
  1. Resolve critical/high contract drifts (validator flow, settings keys, repository API, backup signatures).
  2. Align dependency timing and reproducibility policy (`uv lock` + `uv sync --frozen`, explicit package/version policy).
  3. Strengthen Phase 2 test plan to cover concurrency/WAL and finance precision invariants.
