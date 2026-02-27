# Critical Review: docs/build-plan Execution Risks

## Task

- **Date:** 2026-02-21
- **Task slug:** docs-build-plan-critical-review-execution-risks
- **Owner role:** orchestrator
- **Scope:** Deep critical review of `docs/build-plan/*.md` for issues that would complicate implementation execution.

## Inputs

- User request:
  - Critically review `docs/build-plan/` after recent updates.
  - Focus on potential execution blockers and coding complications.
  - Produce a feedback handoff document.
- Specs/docs referenced:
  - All files under `docs/build-plan/`
  - Recent handoffs under `.agent/context/handoffs/` (2026-02-20 to 2026-02-21)
  - Session context files (`SOUL.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`)
- Constraints:
  - High-accuracy, defect-focused analysis.
  - Severity-ordered findings with concrete references and practical fixes.

## Role Plan

1. orchestrator
2. reviewer
3. tester
4. coder

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-21-docs-build-plan-critical-review-execution-risks.md`
- Design notes:
  - Findings are ordered by implementation risk.
  - Each finding includes concrete references and remediation.
- Commands run:
  - `rg --files docs/build-plan`
  - targeted `rg -n` consistency scans
  - multiple full/partial `Get-Content` passes with line-numbered extraction
  - link/reference and endpoint parity sanity scripts
- Results:
  - Multiple critical/high contract drifts found.
  - Highest risks are API/MCP contract mismatches, scheduling split-brain docs, and provider credential model inconsistencies.

## Tester Output

- Commands run:
  - Contract sanity checks via regex scans and cross-file comparison scripts.
  - Endpoint presence checks between REST (`04-rest-api.md`) and MCP (`05-mcp-server.md`) contracts.
  - Index vs source parity checks (`output-index.md`, `gui-actions-index.md`, `input-index.md` vs phase docs).
- Pass/fail matrix:
  - Cross-file naming consistency: **fail**
  - Endpoint contract parity: **fail**
  - Tool-name parity (MCP vs indexes): **fail**
  - Scheduling contract parity (06e vs 09): **fail**
  - Provider-count parity (9 vs 12): **fail**
  - CI/release workflow internal consistency: **fail**
- Repro failures:
  - See Reviewer findings (Critical 1-4, High 5-9).
- Coverage/test gaps:
  - Several new contracts are documented but missing explicit route/tool/schema stubs or test commands tied to those routes/tools.

## Reviewer Output

### Findings by severity

#### Critical 1: MCP import tools and REST import routes use incompatible payload contracts

- Evidence:
  - REST expects multipart uploads:
    - `docs/build-plan/04-rest-api.md:761`
    - `docs/build-plan/04-rest-api.md:793`
    - `docs/build-plan/04-rest-api.md:801`
  - MCP tools send JSON with `file_path`:
    - `docs/build-plan/05-mcp-server.md:1481`
    - `docs/build-plan/05-mcp-server.md:1491`
    - `docs/build-plan/05-mcp-server.md:1502`
- Why this blocks execution:
  - If implemented as documented, MCP calls will not satisfy FastAPI `UploadFile` + `Form(...)` signatures.
- Remediation:
  - Canonicalize one contract:
    - Option A: MCP reads local file and forwards multipart/form-data.
    - Option B: Add explicit trusted-localhost JSON `file_path` endpoints and mark multipart/JSON split in docs.

#### Critical 2: `zorivest_diagnose` “always callable” contract still has failure paths

- Evidence:
  - Always-callable requirement:
    - `docs/build-plan/05-mcp-server.md:588`
  - `safeFetch` does not check `res.ok`:
    - `docs/build-plan/05-mcp-server.md:618`
  - Provider mapping assumes array and can throw on error payloads:
    - `docs/build-plan/05-mcp-server.md:642`
  - Guard routes may return 403 without active session:
    - `docs/build-plan/04-rest-api.md:490`
- Why this blocks execution:
  - Diagnostics can throw or misreport in locked/unauthenticated states, exactly when diagnostics are needed most.
- Remediation:
  - Make `safeFetch` return `{ok,status,data}`.
  - Guard/provider parsing must handle non-array/non-200 responses gracefully.
  - Add explicit tests for 401/403/404 responses in diagnostics test block.

#### Critical 3: Market provider credential model cannot satisfy Alpaca contract

- Evidence:
  - Alpaca requires key + secret headers:
    - `docs/build-plan/08-market-data.md:329`
    - `docs/build-plan/08-market-data.md:331`
  - Stored model only has one credential field:
    - `docs/build-plan/08-market-data.md:167`
  - API config DTO only accepts `api_key`:
    - `docs/build-plan/08-market-data.md:554`
  - GUI only edits `api_key`:
    - `docs/build-plan/06f-gui-settings.md:95`
- Why this blocks execution:
  - Alpaca provider cannot be configured/tested with current schema/UI.
- Remediation:
  - Add `encrypted_api_secret` end-to-end (DB, DTO, REST, GUI, redaction, tests), or remove Alpaca from Phase 8 provider registry and keep it only in broker-adapter scope.

#### Critical 4: Scheduling docs are split-brain between legacy and canonical contracts

- Evidence:
  - Legacy schedule endpoints + tools still documented in GUI spec:
    - `docs/build-plan/06e-gui-scheduling.md:193`
    - `docs/build-plan/06e-gui-scheduling.md:174`
  - Canonical policy-driven contracts in Phase 9:
    - `docs/build-plan/09-scheduling.md:2418`
    - `docs/build-plan/09-scheduling.md:2478`
    - `docs/build-plan/09-scheduling.md:2667`
  - Index already points to policy contracts:
    - `docs/build-plan/gui-actions-index.md:282`
- Why this blocks execution:
  - Frontend/API/MCP teams can implement different, incompatible scheduling surfaces.
- Remediation:
  - Rewrite `06e-gui-scheduling.md` to Phase 9 canonical contracts; keep legacy contract only in a clearly marked deprecated appendix.

#### High 5: Expansion REST contract remains incomplete for endpoints consumed by MCP and indexes

- Evidence:
  - MCP calls require these endpoints:
    - `docs/build-plan/05-mcp-server.md:1331` (`/round-trips`)
    - `docs/build-plan/05-mcp-server.md:1477` (`/identifiers/resolve`)
    - `docs/build-plan/05-mcp-server.md:1339` (`/analytics/excursion/{id}`)
    - `docs/build-plan/05-mcp-server.md:1528` (`/analytics/options-strategy`)
  - REST summary references some, but explicit route blocks are missing:
    - `docs/build-plan/04-rest-api.md:652`
    - `docs/build-plan/04-rest-api.md:653`
- Why this complicates coding:
  - Missing request/response contracts force implementers to guess payloads and error models.
- Remediation:
  - Add full route stubs + schemas + test entries for all endpoints called by MCP tools and listed in indexes.

#### High 6: Indexes contain non-canonical endpoint/tool names

- Evidence:
  - Market-data endpoints in output index do not match Phase 8 routes:
    - `docs/build-plan/output-index.md:239`
    - `docs/build-plan/output-index.md:240`
    - `docs/build-plan/output-index.md:241`
    - `docs/build-plan/output-index.md:242`
    - vs canonical:
      - `docs/build-plan/08-market-data.md:508`
      - `docs/build-plan/08-market-data.md:512`
      - `docs/build-plan/08-market-data.md:516`
      - `docs/build-plan/08-market-data.md:520`
  - MCP guard index endpoints/tool names drift:
    - `docs/build-plan/output-index.md:251`
    - `docs/build-plan/gui-actions-index.md:167`
    - `docs/build-plan/gui-actions-index.md:169`
    - vs canonical:
      - `docs/build-plan/04-rest-api.md:497`
      - `docs/build-plan/04-rest-api.md:502`
      - `docs/build-plan/05-mcp-server.md:435`
      - `docs/build-plan/05-mcp-server.md:455`
- Why this complicates coding:
  - Index-driven implementation/testing will target wrong routes and tool names.
- Remediation:
  - Regenerate indexes from source docs or enforce an automated parity check before merging doc updates.

#### High 7: Provider count drift (9 vs 12) remains unresolved across phase docs

- Evidence:
  - Phase 8 goal says 12 providers:
    - `docs/build-plan/08-market-data.md:11`
  - Multiple docs still encode 9-provider assumptions:
    - `docs/build-plan/08-market-data.md:750`
    - `docs/build-plan/08-market-data.md:763`
    - `docs/build-plan/06f-gui-settings.md:17`
    - `docs/build-plan/06-gui.md:362`
    - `docs/build-plan/build-priority-matrix.md:72`
    - `docs/build-plan/input-index.md:374`
- Why this complicates coding:
  - UI completeness checks, test counts, and delivery scope are inconsistent.
- Remediation:
  - Choose canonical provider set for Phase 8 and update all counts, checklists, and matrix notes.

#### High 8: CI/release pipeline plan in Phase 7 has blocking internal contradictions

- Evidence:
  - `publish.yml` verification depends on `verify-version` outputs without defining that job in the publish flow:
    - `docs/build-plan/07-distribution.md:375`
    - `docs/build-plan/07-distribution.md:425`
  - CI uses `mypy` despite cross-doc type-check standard being `pyright`:
    - `docs/build-plan/07-distribution.md:239`
    - `docs/build-plan/dependency-manifest.md:82`
  - Python test path differs from test strategy conventions:
    - `docs/build-plan/07-distribution.md:276`
    - `docs/build-plan/testing-strategy.md:220`
- Why this complicates coding:
  - Pipeline templates are likely to fail when implemented verbatim.
- Remediation:
  - Harmonize CI to documented local validation standards, and make workflow dependency graph self-contained per file.

#### High 9: Tax GUI prerequisites now reference wrong matrix item range

- Evidence:
  - Tax GUI prerequisite points to items 36–68:
    - `docs/build-plan/06g-gui-tax.md:3`
  - Tax GUI says tax endpoints are in item 61:
    - `docs/build-plan/06g-gui-tax.md:9`
  - Matrix now places scheduling in 36–49 and tax API at 75:
    - `docs/build-plan/build-priority-matrix.md:103`
    - `docs/build-plan/build-priority-matrix.md:229`
- Why this complicates coding:
  - Teams can gate tax GUI on unrelated scheduling/expansion tasks or implement against the wrong dependency milestones.
- Remediation:
  - Replace numeric item references with stable phase/section references.

#### Medium 10: Duplicate PDF parser tasks in the matrix create implementation ambiguity

- Evidence:
  - First mention:
    - `docs/build-plan/build-priority-matrix.md:138`
  - Duplicate mention:
    - `docs/build-plan/build-priority-matrix.md:159`
- Why this complicates coding:
  - Two roadmap entries can trigger duplicate implementation/testing work.
- Remediation:
  - Keep one parser task and make dependent tasks reference it explicitly.

#### Medium 11: Account-enhancement component scope is inconsistent

- Evidence:
  - 5 components listed:
    - `docs/build-plan/06d-gui-accounts.md:268`
    - `docs/build-plan/06d-gui-accounts.md:271`
    - `docs/build-plan/06d-gui-accounts.md:272`
  - Outputs list only 3 expansion components:
    - `docs/build-plan/06d-gui-accounts.md:294`
  - Matrix expects 5 components:
    - `docs/build-plan/build-priority-matrix.md:170`
- Why this complicates coding:
  - Acceptance criteria do not clearly state what “done” includes.
- Remediation:
  - Align `Outputs` with component table and matrix scope, or explicitly mark optional components.

#### Low 12: Overview metadata is stale

- Evidence:
  - Overview says matrix is 106 items:
    - `docs/build-plan/00-overview.md:92`
  - Matrix header says 131-item order:
    - `docs/build-plan/build-priority-matrix.md:3`
- Why this complicates coding:
  - Progress tracking and planning metrics become unreliable.
- Remediation:
  - Remove hardcoded counts from overview or auto-derive them from the matrix.

### Open questions

1. Should diagnostics/version/health contracts be root (`/health`, `/version`) or namespaced (`/api/v1/health`, `/api/v1/version`)?  
2. For agent-triggered imports, is canonical transport multipart file upload or trusted-localhost `file_path` JSON?  
3. Is Alpaca intentionally in Phase 8 market-data provider registry, or only in broker-adapter scope?

### Verdict

- **Verdict:** Not execution-ready in current state.
- **Reason:** Multiple critical contract mismatches can cause immediate implementation divergence or failing integrations.

### Residual risk

- Even after fixing critical items, index drift risk remains high unless endpoint/tool contracts are generated or parity-checked automatically.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:** (pending)
- **Timestamp:** (pending)

## Final Summary

- Status:
  - Critical review completed with severity-ranked findings and remediation order.
- Next steps:
  1. Resolve Critical 1-4 before starting code implementation for expansion/scheduling/diagnostics.
  2. Run a single “contract reconciliation pass” across `04`, `05`, `06e`, `08`, and all three indexes.
  3. Add a lightweight parity check script (routes/tools/indexes) to prevent future drift.

