# Critical Review Handoff: Phase 10 Service Daemon Integration

## Task

- **Date:** 2026-02-21
- **Task slug:** docs-build-plan-service-daemon-integration-critical-review
- **Owner role:** orchestrator
- **Scope:** Critically review `docs/build-plan/` with focus on whether `10-service-daemon.md` is correctly integrated across plan docs and whether platform behavior claims are valid.

## Inputs

- User request:
  - Critically review `docs/build-plan/` files.
  - Verify newly added `10-service-daemon.md` integration quality.
  - Produce a feedback document in `.agent/context/handoffs/`.
  - Use web research to validate feature behavior.
- Docs reviewed:
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/07-distribution.md`
  - `docs/build-plan/10-service-daemon.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/output-index.md`
  - `docs/build-plan/gui-actions-index.md`
  - `docs/build-plan/testing-strategy.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/build-priority-matrix.md`
- External validation sources:
  - Apple launchd docs
  - systemd/loginctl docs
  - WinSW docs
  - Microsoft `sc create` docs
  - Electron docs (`process.resourcesPath`) and electron-builder docs (`extraResources`)

## Role Plan

1. orchestrator
2. researcher
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-21-docs-build-plan-service-daemon-integration-critical-review.md`
- Design notes:
  - Defect-focused review (integration correctness, behavior correctness, execution risk).
  - Prioritized findings by release risk and plan coherence impact.
- Commands run:
  - `rg --files docs/build-plan`
  - `rg -n` scans for phase/service references and section coverage
  - `Get-Content` deep reads of key plan files
  - Web lookups for platform behavior validation
- Results:
  - Found multiple cross-file integration gaps and several platform-specific behavior mismatches in Phase 10 architecture claims.

## Tester Output

- Commands run:
  - Cross-reference checks:
    - `rg -n "Phase 10|10-service-daemon|service|daemon" docs/build-plan`
    - `rg -n "^## " docs/build-plan/input-index.md docs/build-plan/gui-actions-index.md docs/build-plan/06f-gui-settings.md`
  - Targeted line extraction for evidence:
    - `Get-Content` ranges for all impacted files
  - External validation:
    - Apple launchd behavior
    - systemd lingering behavior
    - WinSW admin/elevation behavior
    - Windows service default account behavior
    - Electron packaged resource path behavior
- Pass/fail matrix:
  - Phase 10 indexed in plan tables and indexes: **partial**
  - Service behavior claims aligned to OS reality: **fail**
  - Internal code-contract consistency in `10-service-daemon.md`: **fail**
  - Packaging/runtime path consistency: **fail**
  - Test-plan integration for Phase 10: **partial**
- Coverage/test gaps:
  - No dedicated Phase 10 section in `testing-strategy.md`.
  - Snippet-level tests in `10-service-daemon.md` are not runnable as written.

## Reviewer Output

### Findings by severity

#### Critical 1: Phase 10 is not integrated across core planning surfaces

- Evidence:
  - `docs/build-plan/10-service-daemon.md:884` says Service Manager is added as `§6f.10`.
  - `docs/build-plan/06f-gui-settings.md:685` ends at `6f.9`; no `6f.10` section.
  - `docs/build-plan/06-gui.md:20` and `docs/build-plan/06-gui.md:221` list Settings scope without Service Manager.
  - `docs/build-plan/input-index.md:556` to `docs/build-plan/input-index.md:568` has no service-daemon input group.
  - `docs/build-plan/gui-actions-index.md:266` to `docs/build-plan/gui-actions-index.md:275` has no service-manager action group.
  - `docs/build-plan/00-overview.md:62` to `docs/build-plan/00-overview.md:75` phase summary stops at Phase 9.
  - `docs/build-plan/04-rest-api.md:846` to `docs/build-plan/04-rest-api.md:857` outputs omit service routes.
  - `docs/build-plan/05-mcp-server.md:1590` to `docs/build-plan/05-mcp-server.md:1596` outputs omit service tools.
- Risk:
  - Feature is planned in isolation; traceability gates and implementation sequence can drift.
- Constructive fix:
  - Add explicit Phase 10 entries to:
    - `00-overview.md` phase summary
    - `06f-gui-settings.md` as `6f.10`
    - `06-gui.md` Settings scope/exit criteria
    - `input-index.md` (service controls + programmatic triggers)
    - `gui-actions-index.md` (start/stop/restart/toggle/open logs)
    - `04-rest-api.md` outputs/exit criteria for service endpoints
    - `05-mcp-server.md` outputs/exit criteria for `zorivest_service_*`
    - `testing-strategy.md` dedicated Phase 10 coverage section

#### Critical 2: Platform persistence claims are inconsistent with documented OS behavior

- Evidence in plan:
  - Global goal says "starts at boot and survives user logout": `docs/build-plan/10-service-daemon.md:9`.
  - macOS row claims LaunchAgent "Survives logout": `docs/build-plan/10-service-daemon.md:70`.
  - Linux row says no admin needed, but caveat requires `enable-linger`: `docs/build-plan/10-service-daemon.md:71`, `docs/build-plan/10-service-daemon.md:268`.
- External validation:
  - Apple launchd docs say per-user agents start at user login and receive `SIGTERM` on logout.
  - systemd/loginctl docs state lingering is required for user managers after logout and for boot-time user service start.
- Risk:
  - The current design cannot satisfy the stated always-on behavior on macOS/Linux without changing service level or privileges.
- Constructive fix:
  - Either:
    - revise requirement to "runs while user session is active", or
    - move to privileged system-level daemon model on macOS/Linux with explicit install-time elevation and security design.
  - Document platform-specific guarantees explicitly (boot, login, logout, reboot).

#### High 3: Windows service account strategy is undefined and likely incompatible with user-scoped data assumptions

- Evidence in plan:
  - Windows is "System-level service": `docs/build-plan/10-service-daemon.md:69`.
  - WinSW XML has no service account settings: `docs/build-plan/10-service-daemon.md:88` to `docs/build-plan/10-service-daemon.md:119`.
  - Logs assume `%LOCALAPPDATA%`: `docs/build-plan/10-service-daemon.md:100`, `docs/build-plan/10-service-daemon.md:118`.
- External validation:
  - Microsoft `sc create` docs: default `obj=` is `LocalSystem`.
  - WinSW docs: most lifecycle commands require admin privileges/UAC.
- Risk:
  - Service identity/data-path mismatch can break DB access, log visibility, and encryption/session assumptions.
- Constructive fix:
  - Pick one explicit model:
    - per-user service model (user context, user data paths), or
    - system service model with dedicated service account + service-owned data directory.
  - Add data-location/account model section to Phase 10 with migration and security implications.

#### High 4: Runtime pathing is inconsistent and brittle across platforms

- Evidence in plan:
  - Systemd template uses `%h/.local/share/...`: `docs/build-plan/10-service-daemon.md:224`.
  - Linux first-launch setup writes `ExecStart=${backendPath}` from app bundle path: `docs/build-plan/10-service-daemon.md:1238` to `docs/build-plan/10-service-daemon.md:1251`.
  - First-launch script uses hardcoded `Resources` path on Linux/macOS: `docs/build-plan/10-service-daemon.md:1181` to `docs/build-plan/10-service-daemon.md:1183`, `docs/build-plan/10-service-daemon.md:1238` to `docs/build-plan/10-service-daemon.md:1240`.
  - Phase 7 currently shows only backend resource copy; no service resources: `docs/build-plan/07-distribution.md:125` to `docs/build-plan/07-distribution.md:127`.
- External validation:
  - Electron docs: use `process.resourcesPath`.
  - electron-builder docs: `extraResources` lands in `Contents/Resources` on macOS and `resources` on Linux/Windows.
- Risk:
  - Service unit points to paths that differ between docs and runtime, increasing install/start failures.
- Constructive fix:
  - Normalize all runtime paths through a single resolver using `process.resourcesPath`.
  - Make `10.1` template and `10.6` setup generate identical final paths.
  - Update `07-distribution.md` baseline `extraResources` to include service assets.

#### High 5: Service Manager UI contract is internally inconsistent

- Evidence in plan:
  - `BackendHealth` interface has no `pid`, but render uses `health.pid`: `docs/build-plan/10-service-daemon.md:947` to `docs/build-plan/10-service-daemon.md:953`, `docs/build-plan/10-service-daemon.md:1031`.
  - Poll code fetches only `/service/status`: `docs/build-plan/10-service-daemon.md:977`.
  - UI reads `scheduler` + `database` fields that are provided by `/health`, not `/service/status`: `docs/build-plan/10-service-daemon.md:1034` to `docs/build-plan/10-service-daemon.md:1035`.
  - Endpoint table says scheduler comes from `/health`: `docs/build-plan/10-service-daemon.md:1106`.
  - `logDir` is displayed but never set: `docs/build-plan/10-service-daemon.md:965`, `docs/build-plan/10-service-daemon.md:1089`.
- Risk:
  - If implemented as written, this will type-fail and/or silently show incomplete status.
- Constructive fix:
  - Split UI state into `serviceStatusResponse` and `healthResponse`.
  - Poll both `/service/status` and `/health` when running.
  - Add IPC method for log directory discovery and initialize `logDir`.
  - Ensure TS interfaces exactly match REST response contracts.

#### Medium 6: REST auth and test contracts conflict inside Phase 10

- Evidence in plan:
  - Summary marks `/service/*` as auth required: `docs/build-plan/10-service-daemon.md:712`, `docs/build-plan/10-service-daemon.md:713`.
  - Route snippets do not show auth dependency for `/service/status` or `/graceful-shutdown`: `docs/build-plan/10-service-daemon.md:667` to `docs/build-plan/10-service-daemon.md:704`.
  - Test name says "returns_202" but assertion expects `200`: `docs/build-plan/10-service-daemon.md:1423`, `docs/build-plan/10-service-daemon.md:1427`.
- Risk:
  - Security posture and expected status codes are ambiguous.
- Constructive fix:
  - Add explicit auth dependency in route signatures or change summary to match.
  - Choose one status code contract (200 or 202) and align route + tests + MCP polling behavior.

#### Medium 7: Uninstall cleanup strategy is likely not executable on macOS/Linux

- Evidence in plan:
  - "Only runs during app uninstall" claim via `will-quit` handler: `docs/build-plan/10-service-daemon.md:1271` to `docs/build-plan/10-service-daemon.md:1278`.
- Risk:
  - Uninstall often occurs when app is not running; service artifacts may be left behind.
- Constructive fix:
  - Move cleanup to actual uninstall scripts/packager hooks per platform.
  - Keep `will-quit` path as best-effort only, not authoritative cleanup mechanism.

#### Medium 8: Phase 10 test snippets are not runnable as written

- Evidence in plan:
  - `await` used in non-async `it(...)` blocks: `docs/build-plan/10-service-daemon.md:1336` to `docs/build-plan/10-service-daemon.md:1342`.
  - `cp` is referenced without import in test snippet: `docs/build-plan/10-service-daemon.md:1337`.
  - `testing-strategy.md` has no explicit Phase 10 test section: `docs/build-plan/testing-strategy.md:114` to `docs/build-plan/testing-strategy.md:120`.
- Risk:
  - TDD path for this phase is underspecified and examples may fail copy/paste.
- Constructive fix:
  - Correct snippets and add dedicated "Phase 10 Service Daemon" test matrix in `testing-strategy.md`.

#### Low 9: Cross-doc metadata drift remains

- Evidence:
  - `00-overview.md` still says build matrix has 131 items: `docs/build-plan/00-overview.md:92`.
  - `build-priority-matrix.md` states 136 items: `docs/build-plan/build-priority-matrix.md:3`.
- Risk:
  - Signals stale editing and lowers trust in plan metadata.
- Constructive fix:
  - Run one consistency pass for counts and cross-references after each major plan addition.

### Open questions

1. Should Phase 10 guarantee true "always-on after boot" on macOS/Linux, or only "while user session is active"?
2. For Windows, should backend service run under user identity or dedicated service identity?
3. Is service status intended to be auth-protected for GUI local calls, or only for MCP/remote-like consumers?

### Verdict

- **approved_with_blockers**
- Phase 10 concept is strong, but integration and platform-behavior contracts need correction before implementation to prevent rework and false confidence.

### Residual risk

- Without the corrections above, implementation will likely diverge by platform and fail acceptance criteria despite passing isolated unit tests.

## Guardrail Output (If Required)

- Safety checks:
  - No destructive operations performed.
  - Review is doc-only and evidence-backed.
- Blocking risks:
  - Platform behavior mismatch (logout/boot persistence) is release-blocking if not resolved.
- Verdict:
  - Block Phase 10 implementation until architecture contract is clarified and docs are synchronized.

## External Validation Sources

- Apple launchd lifecycle (LaunchAgents started at login; terminated at logout):
  - https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
- systemd/loginctl lingering behavior:
  - https://www.freedesktop.org/software/systemd/man/latest/loginctl.html
- WinSW usage and admin/UAC behavior:
  - https://github.com/winsw/winsw
- Microsoft `sc create` (default account behavior):
  - https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-create
- Electron runtime resource path:
  - https://www.electronjs.org/docs/latest/api/process
- electron-builder `extraResources` platform paths:
  - https://www.electron.build/configuration.html
- psutil process CPU semantics:
  - https://psutil.readthedocs.io/en/latest/#psutil.Process.cpu_percent

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Completed critical review with cross-file integration findings and web-validated platform corrections.
- Next steps:
  1. Decide platform persistence/account model for Phase 10.
  2. Apply a doc synchronization patch across overview/index/API/MCP/GUI/testing files.
  3. Re-run one consistency review pass before coding.

