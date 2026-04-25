---
seq: "125"
date: "2026-04-24"
project: "build-plan-incomplete-meus-critical-review"
meu: "multiple-incomplete"
status: "resolved"
action_required: "NONE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/BUILD_PLAN.md"
build_plan_section: "incomplete MEUs"
agent: "Codex"
reviewer: "none"
predecessor: "124-2026-04-21-pipeline-adhoc-fixes-docs.md"
---

# Handoff: Build Plan Incomplete MEUs Critical Review

> Status: resolved
> Action Required: NONE — all 16 findings corrected via plan-corrections workflow

## Scope

Critical review of `docs/BUILD_PLAN.md` and referenced files for MEUs not yet complete as of 2026-04-24.

Primary focus:

- Inaccuracies and cross-document inconsistencies.
- Contract violations against local architecture, boundary validation, and MCP/API standards.
- Architectural blunders that could derail implementation, especially missed wiring between layers or services.

Reviewed incomplete areas:

- P2 settings/home/dashboard leftovers: MEU-74 through MEU-76, MEU-171 through MEU-172.
- P2.5 WebSocket and pipeline hardening: MEU-174, MEU-PW8, MEU-TD1, MEU-PH1 through MEU-PH10.
- Phase 10 service daemon: MEU-91 through MEU-95b.
- P2.75 import/analytics expansion: MEU-97 through MEU-122.
- P3 tax: MEU-123 through MEU-156.
- Phase 7 distribution: MEU-157.
- P4 monetization: MEU-175 through MEU-181.

<!-- CACHE BOUNDARY -->

## Findings

### Critical

| # | Finding | Evidence | Recommendation |
|---|---------|----------|----------------|
| C1 | Phase 7 and Phase 10 form a dependency cycle. `BUILD_PLAN.md` says Distribution depends on "All", while Service Daemon depends on Phase 7; the daemon spec also says Phase 10 needs Phase 7, and distribution bundles Phase 10 service resources. This can deadlock planning and validation. | `docs/BUILD_PLAN.md:35`, `docs/BUILD_PLAN.md:44`, `docs/build-plan/10-service-daemon.md:3`, `docs/build-plan/07-distribution.md:3`, `docs/build-plan/07-distribution.md:125-127` | Split Phase 10 into a runtime/control-plane portion before distribution and installer packaging hooks consumed by Phase 7, or make the graph one-way with Phase 7 depending on completed daemon artifacts. |
| C2 | The Service Daemon has no SQLCipher unlock/key provisioning contract. It is supposed to run APScheduler/SQLCipher independently of the GUI, but auth/unlock requires API key to unwrap DEK and open SQLCipher. No OS credential store, locked-state behavior, GUI unlock handshake, or scheduler-disabled-until-unlocked rule is specified. | `docs/build-plan/10-service-daemon.md:9`, `docs/build-plan/04c-api-auth.md:51-59`, `packages/infrastructure/src/zorivest_infra/database/connection.py:90-124` | Define daemon unlock states before MEU-91: credential source, DEK lifetime, restart behavior, locked health status, and whether scheduled jobs queue/fail/skip while locked. |
| C3 | P2.5c SQL sandbox does not close all existing raw SQL surfaces. The spec identifies `db_connection` and `StoreReportStep`, but its file-change list only injects a new `sql_sandbox`; current code still has `StoreReportStep._execute_sandboxed_sql()` and `CriteriaResolver._resolve_db_query()` executing policy-authored SQL on the trusted connection. The deny list also omits actual sensitive tables like market provider and email provider settings. | `docs/build-plan/09c-pipeline-security-hardening.md:98`, `docs/build-plan/09c-pipeline-security-hardening.md:121-185`, `packages/core/src/zorivest_core/pipeline_steps/store_report_step.py:98-127`, `packages/core/src/zorivest_core/services/criteria_resolver.py:112-125`, `packages/infrastructure/src/zorivest_infra/database/models.py:197-260` | Route every policy-authored SQL path through one SQLCipher-aware sandbox port. Remove or hard-fail direct `db_connection` SQL in StoreReportStep/CriteriaResolver. Use allowlisted read models or an explicit deny/allow policy covering sensitive tables. |
| C4 | Template DB and Policy Emulator are planned as core features but reference infrastructure repositories directly. `PolicyEmulator` takes `EmailTemplateRepository`; SendStep DB lookup is described inside core behavior. That violates the architecture rule that core never imports infrastructure. | `.agent/docs/architecture.md:54-60`, `docs/build-plan/09e-template-database.md:126-169`, `docs/build-plan/09e-template-database.md:283-304`, `docs/build-plan/09f-policy-emulator.md:26-30` | Add a core `EmailTemplatePort`/`TemplateResolver` protocol and inject it at API composition. Keep SQLAlchemy repositories in infrastructure only. |
| C5 | WebSocket MEU-174 describes classes but misses essential server wiring. There is no concrete FastAPI `@router.websocket` endpoint registration, no auth/session/origin contract, no producer integration from scheduler/trade/notification services, a hardcoded `ws://8765`, and the Electron bridge calls `.emit()` without extending/importing an event emitter. | `docs/build-plan/04-rest-api.md:331-413`, `.agent/skills/backend-startup/SKILL.md`, `.agent/docs/architecture.md:64-72` | Specify route registration, auth token/origin policy, event producers, backpressure/reconnect behavior, and dynamic backend URL discovery before implementation. |
| C6 | Tax API MEU-148 is not implementable from its stated prerequisites without stubs. It depends only on MEU-123 through MEU-126, but its route surface calls quarterly estimates, payment recording, harvesting, YTD summary, audit, and wash-sale scanning. Its boundary models also lack `extra="forbid"` and one write endpoint accepts `body: dict`. | `docs/build-plan/04f-api-tax.md:20-45`, `docs/build-plan/04f-api-tax.md:97-172`, `docs/build-plan/04f-api-tax.md:215-236`, AGENTS Boundary Input Contract | Re-slice tax API MEUs by capability, or defer routes until matching core services exist. Add strict Pydantic models for every body/query/path write surface and map invalid input to 422. |

### High

| # | Finding | Evidence | Recommendation |
|---|---------|----------|----------------|
| H1 | DashboardService is specified against non-existent ports, entity fields, and repository methods while claiming it only orchestrates existing services. It imports `zorivest_core.ports.unit_of_work`, uses `a.current_balance`, `list_by_status`, `list_recent`, `list_active`, and `list_next_runs`; current code uses `zorivest_core.application.ports`, `account_id`, and different repository/service APIs. The `/watchlists` endpoint is also placeholder-level. | `docs/build-plan/06j-gui-home.md:9`, `docs/build-plan/06j-gui-home.md:36-115`, `docs/build-plan/06j-gui-home.md:159`, `packages/core/src/zorivest_core/application/ports.py:31-245`, `packages/core/src/zorivest_core/domain/entities.py:98-101` | Rewrite 06j around current service ports or explicitly add new read ports first. Do not mark MEU-171 ready until the read model/wiring contract compiles. |
| H2 | MCP template/emulator tooling violates the boundary ownership standard. 09e says MCP create/update template boundaries are owned by Pydantic request models, but MCP boundaries are TypeScript/Zod; 05g lists many new tools without strict `server.tool` schemas or parity rules. | `docs/build-plan/09e-template-database.md:14-21`, `docs/build-plan/05g-mcp-scheduling.md:430-536`, `.agent/docs/emerging-standards.md:28-58` | Define strict Zod schemas for every MCP tool, plus matching REST Pydantic schemas and schema parity tests. |
| H3 | Port/base URL contracts conflict across planned layers. Backend startup canon uses port 17787 and `ZORIVEST_API_URL`; WebSocket and service daemon docs hardcode 8765; build-priority matrix also references 8766 for liveness. This will split GUI, MCP, WebSocket, and daemon controls across wrong endpoints. | `.agent/skills/backend-startup/SKILL.md`, `docs/build-plan/04-rest-api.md:340-404`, `docs/build-plan/10-service-daemon.md:43-49`, `docs/build-plan/10-service-daemon.md:754`, `docs/build-plan/build-priority-matrix.md:305-336` | Establish one canonical runtime discovery contract: env var, dev default, packaged default, and WebSocket derivation. Update all docs before MEU-174/91/95b. |
| H4 | Monetization defines license and usage services but not enforcement wiring. No API dependencies, MCP wrappers, service guards, or GUI downgrade behavior are tied to `LicenseService`/`UsageMeteringService`; `UsageMeteringService.increment()` references `meter.tier` even though `UsageMeter` has no tier. Google API services are specified as core services that POST to Google directly, violating port/adapter boundaries. | `docs/build-plan/11-monetization.md:64-70`, `docs/build-plan/11-monetization.md:123-151`, `docs/build-plan/11-monetization.md:177-199`, `docs/build-plan/11-monetization.md:262-276`, `docs/build-plan/11-monetization.md:376-379` | Add a feature-gate/enforcement matrix per API route, MCP tool, and service method. Move Google calls behind core ports with infrastructure adapters. Fix the usage entity/service contract before MEU-181. |
| H5 | `record_quarterly_tax_payment` is documented as a write but has MCP annotations `destructiveHint: false` and `idempotentHint: true`. There is no idempotency key or destructive-tool gate. Repeating the tool can double-record payments. | `docs/build-plan/05h-mcp-tax.md:258-289`, `.agent/docs/emerging-standards.md:38-45` | Mark as destructive/non-idempotent unless an idempotency key is designed. Use the M3 confirmation gate, not only an ad hoc `confirm` boolean. |
| H6 | Build status and known-issue state conflict. `BUILD_PLAN.md` marks MEU-PW6/PW7 complete and says P2.5c prerequisite is PW1 through PW13 complete, while PW8 is still partial, TD1 is open, and known issues still list PIPE-URLBUILD and PIPE-NOCANCEL as open. | `docs/BUILD_PLAN.md:335-344`, `docs/BUILD_PLAN.md:352`, `docs/BUILD_PLAN.md:614-615`, `.agent/context/known-issues.md:70-104`, `.agent/context/known-issues.md:165-190` | Reconcile status before starting P2.5c. Either archive fixed known issues with evidence or downgrade the build plan status/prerequisite. |

### Medium

| # | Finding | Evidence | Recommendation |
|---|---------|----------|----------------|
| M1 | PH1 `safe_deepcopy` claims depth/byte guards, but the sketched implementation only uses shallow `sys.getsizeof(obj)` and `copy.deepcopy(obj)`. It has no recursive depth walk, aggregate byte budget, cycle policy, or secret traversal tests. | `docs/build-plan/09c-pipeline-security-hardening.md:53-88` | Specify a recursive traversal algorithm and tests for nested, cyclic, over-depth, aggregate-size, and `Secret` values. |
| M2 | Tax outputs require a "not tax advice" disclaimer in the domain reference, but API/MCP tax response contracts do not include a uniform disclaimer field/envelope. GUI mentions tax pages, but agent/API consumers can miss the disclaimer. | `docs/build-plan/domain-model-reference.md:348-349`, `docs/build-plan/04f-api-tax.md:48-180`, `docs/build-plan/05h-mcp-tax.md:19-394` | Add a response envelope or required field for all tax API/MCP outputs carrying the disclaimer. |
| M3 | P2.75 and many P3 MEUs are too thin for FIC/TDD. Several rows point only to matrix bullets without boundary inventory, schemas, acceptance criteria, service wiring, or test contracts. | `docs/BUILD_PLAN.md:420-520`, `docs/build-plan/build-priority-matrix.md:170-282` | Expand detailed build-plan docs before execution. Do not create FICs from matrix rows alone. |
| M4 | SendStep confirmation opt-out says `requires_confirmation=False` is allowed for pre-approved templates, but no provenance contract ties a template/policy hash to that approval. A malicious policy can set the opt-out flag unless another gate is added. | `docs/build-plan/09c-pipeline-security-hardening.md:228-240`, `docs/build-plan/09c-pipeline-security-hardening.md:280-289` | Require stored policy/template approval records keyed by content hash and recipient scope before allowing confirmation bypass. |

## Commands Executed

All shell commands used redirected output to `C:\Temp\zorivest\` receipts per the Windows terminal preflight policy.

| Purpose | Receipt |
|---------|---------|
| Handoff inventory | `C:\Temp\zorivest\handoffs-list.txt` |
| Symbol/code contract checks | `C:\Temp\zorivest\symbol-checks.txt` |
| Sensitive model table scan | `C:\Temp\zorivest\model-sensitive-lines.txt` |
| Build-plan/doc reference scans | `C:\Temp\zorivest\docrefs-1.txt`, `C:\Temp\zorivest\docrefs-2.txt` |

## Verdict

`resolved` — All 16 findings (6 Critical, 6 High, 4 Medium) corrected via `/plan-corrections` workflow on 2026-04-24.

### Corrections Applied

| Batch | Findings | Files Modified |
|-------|----------|---------------|
| 1: Status Reconciliation | H6 | `known-issues.md`, `BUILD_PLAN.md` |
| 2: Dependency Cycle | C1 | `07-distribution.md`, `10-service-daemon.md` |
| 3: Security Boundaries | C2, C3, C4, M1, M4 | `10-service-daemon.md`, `09c-pipeline-security-hardening.md`, `09e-template-database.md`, `09f-policy-emulator.md` |
| 4: Wiring & Contracts | C5, C6, H1, H3, H4, H5, M2 | `04-rest-api.md`, `04f-api-tax.md`, `06j-gui-home.md`, `05h-mcp-tax.md`, `11-monetization.md`, `BUILD_PLAN.md` |
| 5: Spec Depth | H2 | `09e-template-database.md` |

No production code was modified. All changes limited to `docs/build-plan/`, `docs/BUILD_PLAN.md`, and `.agent/context/known-issues.md`.
