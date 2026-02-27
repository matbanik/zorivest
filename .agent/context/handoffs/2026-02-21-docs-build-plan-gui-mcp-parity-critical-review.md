# Critical Review Handoff: GUI vs MCP Parity (docs/build-plan)

## Task

- **Date:** 2026-02-21
- **Task slug:** docs-build-plan-gui-mcp-parity-critical-review
- **Owner role:** orchestrator
- **Scope:** Critically review `docs/build-plan/` for feature parity between GUI actions and MCP tool calls; provide issues + constructive architecture feedback; validate feature behavior with web research.

## Inputs

- User request:
  - Critically review `docs/build-plan/` files for GUI↔MCP parity.
  - Create feedback document in `.agent/context/handoffs/`.
  - Use web search to validate feature functions.
- Docs reviewed:
  - `docs/build-plan/gui-actions-index.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06e-gui-scheduling.md`
  - `docs/build-plan/09-scheduling.md`
  - `docs/build-plan/10-service-daemon.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/output-index.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/08-market-data.md`
- External validation targets:
  - MCP TypeScript SDK API shape/version stability
  - Service lifecycle control constraints across Windows/macOS/Linux
  - Process detachment behavior for GUI launch

## Role Plan

1. orchestrator
2. researcher
3. reviewer

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-21-docs-build-plan-gui-mcp-parity-critical-review.md`
- Commands run:
  - `rg --files docs/build-plan`
  - `rg -n ... docs/build-plan/...` (cross-reference + contract checks)
  - `Get-Content` (targeted deep reads)
  - web searches + source opens for platform/MCP validation
- Results:
  - Confirmed multiple concrete parity mismatches and cross-doc contract drift.
  - Identified architecture risks where parity is partial/implicit rather than explicit-by-design.

## Tester Output

- Commands run:
  - Tool-definition extraction by regex (`server.tool(...)`) and comparison against GUI/Input index MCP names.
  - Cross-file grep checks for scheduling, guard, tax, and service-tool names.
  - Web validation of MCP SDK, Windows service rights, launchd, systemd linger, Node child-process detach behavior, WinSW config/admin requirements.
- Pass/fail matrix:
  - GUI action MCP names match MCP registry: **fail**
  - Scheduling GUI doc aligned with scheduling MCP contracts: **fail**
  - Service lifecycle GUI/MCP parity and recoverability: **partial/fail**
  - Planned-vs-defined MCP signaling in indices: **partial/fail**
  - External behavior claims (OS service constraints): **mostly pass**, with design implications not fully codified in parity docs.

## Reviewer Output

### Findings by severity

#### Critical 1: Canonical GUI↔MCP tool naming drift on core actions

- Evidence:
  - GUI index maps trade create to `log_trade`: `docs/build-plan/gui-actions-index.md:39`.
  - MCP canonical tool is `create_trade`: `docs/build-plan/05-mcp-server.md:26`, `docs/build-plan/05-mcp-server.md:1593`.
  - GUI index maps guard lock/unlock to `lock_mcp`/`unlock_mcp`: `docs/build-plan/gui-actions-index.md:167`, `docs/build-plan/gui-actions-index.md:168`.
  - MCP canonical guard tools are `zorivest_emergency_stop`/`zorivest_emergency_unlock`: `docs/build-plan/05-mcp-server.md:435`, `docs/build-plan/05-mcp-server.md:455`, `docs/build-plan/05-mcp-server.md:1596`.
- Risk:
  - Agents and docs consumers will call non-existent tools; parity tables become untrustworthy for implementation/testing.
- Constructive fix:
  - Enforce one canonical MCP name set (prefer names in `05-mcp-server.md` outputs).
  - Update `gui-actions-index.md` and any index references to canonical names.
  - Add CI lint: every MCP name referenced in index files must resolve to an actual `server.tool(...)` definition.

#### Critical 2: Scheduling contracts are split between legacy GUI doc and canonical Phase 9 MCP

- Evidence:
  - GUI scheduling doc advertises MCP tools `get_policy`, `approve_policy`, `get_pipeline_runs`: `docs/build-plan/06e-gui-scheduling.md:176`, `docs/build-plan/06e-gui-scheduling.md:177`, `docs/build-plan/06e-gui-scheduling.md:179`.
  - Canonical Phase 9 MCP tools are `create_policy`, `list_policies`, `run_pipeline`, `preview_report`, `update_policy_schedule`, `get_pipeline_history`: `docs/build-plan/09-scheduling.md:2850`, `docs/build-plan/09-scheduling.md:2855`, `docs/build-plan/09-scheduling.md:2857`, `docs/build-plan/09-scheduling.md:2858`, `docs/build-plan/09-scheduling.md:2859`.
  - GUI scheduling doc uses dry-run endpoint `/policies/{id}/test`: `docs/build-plan/06e-gui-scheduling.md:203`, while canonical path is `/policies/{id}/run` with `dry_run=true`: `docs/build-plan/09-scheduling.md:2638`, `docs/build-plan/09-scheduling.md:2734`, `docs/build-plan/09-scheduling.md:2759`, `docs/build-plan/gui-actions-index.md:285`.
  - Phase 9 explicitly makes approval GUI-only in action mapping and guardrail flow: `docs/build-plan/09-scheduling.md:2388`, `docs/build-plan/09-scheduling.md:2922`, while 06e suggests agent approval flow: `docs/build-plan/06e-gui-scheduling.md:186`.
- Risk:
  - Implementation teams can build incompatible GUI and MCP behavior; approval security boundary becomes ambiguous.
- Constructive fix:
  - Treat `09-scheduling.md` as canonical and rewrite `06e-gui-scheduling.md` MCP/endpoint sections to mirror it exactly.
  - Explicitly mark any intentionally GUI-only operations (for approval governance).

#### High 3: `create_trade_plan` is marked as active MCP usage without a defined tool contract

- Evidence:
  - GUI index includes `create_trade_plan` for plan creation: `docs/build-plan/gui-actions-index.md:72`.
  - Input index marks `create_trade_plan via MCP` as ✅: `docs/build-plan/input-index.md:518`.
  - `05-mcp-server.md` outputs do not include `create_trade_plan`: `docs/build-plan/05-mcp-server.md:1593` to `docs/build-plan/05-mcp-server.md:1601`.
- Risk:
  - False-ready parity for planning workflows; test plans may assume non-existent MCP entry points.
- Constructive fix:
  - Either define `create_trade_plan` MCP contract in Phase 5+ (or referenced phase), or downgrade status to planned and remove parity claim until implemented.

#### High 4: Service lifecycle parity is incomplete; MCP cannot recover a fully stopped backend

- Evidence:
  - GUI has Start/Stop/Auto-start actions with no MCP equivalent: `docs/build-plan/gui-actions-index.md:300`, `docs/build-plan/gui-actions-index.md:301`, `docs/build-plan/gui-actions-index.md:303`.
  - MCP service tools are only status/restart/logs: `docs/build-plan/10-service-daemon.md:899`, `docs/build-plan/10-service-daemon.md:900`, `docs/build-plan/10-service-daemon.md:901`.
  - MCP restart uses `POST /service/graceful-shutdown`: `docs/build-plan/10-service-daemon.md:809`, which presumes a currently running backend.
- Risk:
  - If service is down, agent-side tooling can observe failure (`zorivest_service_status`) but cannot perform true recovery/start.
- Constructive fix:
  - Decide if this is an intentional security boundary:
    - If yes: explicitly document non-parity and reason ("start/stop restricted to trusted GUI + local elevation").
    - If no: add guarded MCP `zorivest_service_start`/`zorivest_service_stop` with explicit confirmation + OS privilege model.

#### High 5: MCP SDK version-drift risk is unmitigated in dependency plan

- Evidence:
  - Dependency manifest installs unpinned SDK: `docs/build-plan/dependency-manifest.md:38`.
  - Plan code uses older-style `McpServer` import + `server.tool(...)`: `docs/build-plan/05-mcp-server.md:18`, `docs/build-plan/05-mcp-server.md:26`.
- External validation:
  - MCP TypeScript SDK repo notes v2 pre-alpha/package split and a new API surface.
  - Current server docs show `registerTool(...)` under `@modelcontextprotocol/sdk/server/index.js`.
- Risk:
  - Future installs can silently pull API-breaking SDK versions and invalidate planned code snippets/contracts.
- Constructive fix:
  - Pin SDK major/minor version in manifest.
  - Add "MCP SDK compatibility" section defining supported API style + migration rule.
  - Add smoke test in CI that compiles MCP server bootstrap against locked SDK version.

#### Medium 6: Tax MCP parity is presented before canonical MCP contracts exist in Phase 5 docs

- Evidence:
  - GUI/input indices reference `simulate_tax_impact` and `harvest_losses`: `docs/build-plan/gui-actions-index.md:210`, `docs/build-plan/gui-actions-index.md:220`, `docs/build-plan/input-index.md:516`, `docs/build-plan/input-index.md:517`.
  - Tax MCP registration is deferred in matrix item 76: `docs/build-plan/build-priority-matrix.md:244`.
- Risk:
  - Readers may interpret parity as available now rather than phase-gated.
- Constructive fix:
  - Keep references, but add explicit phase gate labels in GUI/Input indices (e.g., "MCP parity planned in matrix item 76").

#### Medium 7: `Open log folder` is labeled as MCP-equivalent, but semantics differ

- Evidence:
  - GUI action opens native folder via Electron shell: `docs/build-plan/gui-actions-index.md:304`.
  - MCP tool returns log path + listing (does not open GUI file manager): `docs/build-plan/10-service-daemon.md:901`.
- Risk:
  - "Equivalent MCP tool" column overstates parity; behavior differs materially.
- Constructive fix:
  - Mark this as `partial` parity in index semantics (inspect vs open), or split columns into `MCP Equivalent` and `Parity Level`.

#### Medium 8: Scheduler status endpoint naming drift between docs

- Evidence:
  - 06e lists `GET /api/v1/scheduling/status`: `docs/build-plan/06e-gui-scheduling.md:205`.
  - 09 canonical endpoint is `GET /api/v1/scheduling/scheduler/status` (router-relative `/scheduler/status`): `docs/build-plan/09-scheduling.md:2581`, `docs/build-plan/09-scheduling.md:2643`.
- Risk:
  - Broken wiring if frontend follows outdated endpoint path.
- Constructive fix:
  - Normalize endpoint references to Phase 9 canonical path and add redirect/deprecation note only if both are intentionally supported.

#### Low 9: Index summary metadata drift reduces trust

- Evidence:
  - GUI actions table includes superseded entries (`⛔`) in section 15, but summary omits that status bucket and reports planned counts that no longer match visible statuses: `docs/build-plan/gui-actions-index.md:174`, `docs/build-plan/gui-actions-index.md:308`.
  - Input summary "MCP-only inputs" includes tool names (`zorivest_service_status`, `zorivest_service_logs`) rather than input fields: `docs/build-plan/input-index.md:674`.
- Risk:
  - Traceability indices become harder to use as implementation contracts.
- Constructive fix:
  - Auto-generate summary stats from row data.
  - Separate "MCP-only parameters" from "MCP-only tool calls" in input index summaries.

### Open questions

1. Is service start/stop intentionally GUI-only for security/elevation reasons, or should MCP parity be complete for service lifecycle?
2. Should scheduling approval remain strictly GUI-only (human gate), or is there a constrained MCP approval path planned?
3. Which document is canonical for tool naming: `05-mcp-server.md` only, or per-phase docs with generated index sync?

### Verdict

- **approved_with_blockers**
- The architecture direction is strong, but current parity artifacts are inconsistent enough to cause implementation/test drift unless corrected first.

### Residual risk

- Without parity contract normalization, team members/agents will implement against different tool and endpoint names and produce avoidable integration failures.

## Guardrail Output (If Required)

- Safety checks:
  - Doc-only review, no destructive operations.
  - Evidence tied to exact file locations + external primary docs.
- Blocking risks:
  - Canonical naming drift and scheduling contract split are immediate blockers for implementation reliability.
- Verdict:
  - Block parity-dependent implementation until index + phase docs are synchronized.

## External Validation Sources

- MCP TypeScript SDK repository (v2 pre-alpha notice / package split):
  - https://github.com/modelcontextprotocol/typescript-sdk
- MCP server API docs (`registerTool`, `@modelcontextprotocol/sdk/server/index.js`):
  - https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/src/server/README.md
- Node.js child process detachment semantics (`detached`, `unref`, stdio caveat):
  - https://nodejs.org/api/child_process.html
- Microsoft SQL Server docs (start/stop service requires admin privileges):
  - https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/start-stop-pause-resume-restart-sql-server-services?view=sql-server-ver16
- Windows service access rights (query/start rights model):
  - https://learn.microsoft.com/en-us/windows/win32/services/service-security-and-access-rights
- `sc config` command syntax details:
  - https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-config
- WinSW usage/admin requirements:
  - https://github.com/winsw/winsw
- WinSW XML config (`onfailure`, `startmode`) reference:
  - https://raw.githubusercontent.com/winsw/winsw/v3/docs/xml-config-file.md
- Apple launchd user-agent lifecycle (login start / logout termination):
  - https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
- `loginctl` linger semantics (`enable-linger`):
  - https://man7.org/linux/man-pages/man1/loginctl.1.html

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status: Completed focused parity review with severity-ranked findings and web-validated architecture constraints.
- Next steps:
  1. Resolve canonical naming/endpoint mismatches (`gui-actions-index.md`, `06e-gui-scheduling.md`, `input-index.md`).
  2. Declare explicit parity levels (exact/partial/by-design-none) for service and UX-bound actions.
  3. Pin MCP SDK version and add compatibility guardrails in dependency + CI docs.
