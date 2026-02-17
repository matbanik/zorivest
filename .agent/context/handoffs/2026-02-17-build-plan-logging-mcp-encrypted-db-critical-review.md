# Task Handoff

## Task

- **Date:** 2026-02-17
- **Task slug:** build-plan-logging-mcp-encrypted-db-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of build-plan docs with focus on (1) logging redaction updates and (2) MCP access to encrypted database.

## Inputs

- User request:
  - Review build-plan documentation after updates to sensitive-data redaction and MCP encrypted-DB access.
  - Produce a critical-review handoff in `.agent/context/handoffs`.
- Specs/docs referenced:
  - `docs/build-plan/01a-logging.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/07-distribution.md`
  - `docs/build-plan/08-market-data.md`
  - `docs/build-plan/input-index.md`
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/handoffs/TEMPLATE.md`
- Constraints:
  - Findings-first, severity-ranked, with concrete file/line evidence.
  - Focus on behavioral and security risk, not style.

## Role Plan

1. orchestrator
2. reviewer
3. coder (doc output only)
4. tester (doc consistency verification)
- Optional roles: researcher, guardrail (not used)

## Coder Output

- Changed files:
  - `.agent/context/handoffs/2026-02-17-build-plan-logging-mcp-encrypted-db-critical-review.md` (new)
- Design notes:
  - Documentation-only review artifact; no product/runtime code changes.
- Commands run:
  - `rg --files docs/build-plan docs`
  - `rg -n` cross-file contract tracing for logging/redaction/MCP/security topics
  - `Get-Content` with line numbers for cited evidence
  - `git diff -- docs/build-plan/01a-logging.md` (to validate latest redaction delta)
- Results:
  - Critical contract and security gaps identified in current build-plan docs.

## Tester Output

- Commands run:
  - Structural and consistency review commands only (doc review task).
- Pass/fail matrix:
  - Not applicable (no executable code changed).
- Repro failures:
  - Not applicable.
- Coverage/test gaps:
  - Missing tests for redaction of `extra={}` payloads and absent auth/unlock integration tests for standalone MCP + encrypted DB flow.

## Reviewer Output

- Findings by severity:

  - **Critical:** Redaction contract says `extra` fields are sanitized, but implementation does not sanitize `extra` at all.
    - Evidence:
      - Contract claims Layer 2 applies to `record.args` and `extra`: `docs/build-plan/01a-logging.md:229`.
      - Filter mutates only `record.msg` and `record.args`: `docs/build-plan/01a-logging.md:572`, `docs/build-plan/01a-logging.md:575`.
      - Formatter emits all non-reserved extras verbatim: `docs/build-plan/01a-logging.md:486`, `docs/build-plan/01a-logging.md:489`.
      - REST log ingestion writes structured payload into `extra={"data": ...}`: `docs/build-plan/04-rest-api.md:282`.
    - Risk:
      - Sensitive values can leak to JSONL via `extra` fields despite documented redaction guarantees.
    - Recommendation:
      - Add recursive redaction of non-reserved `record.__dict__` extras before formatting.
      - Add unit tests for nested `extra` payloads (dict/list/tuple) containing keys like `api_key`, `authorization`, `passphrase`.

  - **Critical:** Logging design reintroduces multi-writer risk for `app.jsonl` via two `RotatingFileHandler` instances.
    - Evidence:
      - Rationale explicitly requires single writer per file: `docs/build-plan/01a-logging.md:56`.
      - Feature loop creates handler for `app` feature to `app.jsonl`: `docs/build-plan/01a-logging.md:276`, `docs/build-plan/01a-logging.md:350`.
      - Separate catchall handler also targets `app.jsonl`: `docs/build-plan/01a-logging.md:364`.
    - Risk:
      - Rotation anomalies and unpredictable file rollover behavior for `app.jsonl`.
    - Recommendation:
      - Use one handler for `app.jsonl` with combined routing logic, or move catchall to a distinct file (for example `misc.jsonl`).

  - **Critical:** Build-plan does not define a complete encrypted-DB unlock/auth flow for standalone MCP access.
    - Evidence:
      - DB passphrase is GUI-only with no MCP/API surface: `docs/build-plan/input-index.md:344`.
      - MCP server is documented as thin REST wrapper only: `docs/build-plan/05-mcp-server.md:9`.
      - MCP examples provide API base URL but no auth/unlock handshake: `docs/build-plan/05-mcp-server.md:21`, `docs/build-plan/05-mcp-server.md:220`.
      - Standalone MCP distribution usage includes only `--api-url`: `docs/build-plan/07-distribution.md:60`.
      - REST routes shown are trades/images/settings/logs; no auth/unlock route contract is defined: `docs/build-plan/04-rest-api.md:24`, `docs/build-plan/04-rest-api.md:188`, `docs/build-plan/04-rest-api.md:258`.
    - Risk:
      - Standalone MCP cannot reliably access encrypted DB under current documented contracts, or teams may implement ad hoc bypasses.
    - Recommendation:
      - Add explicit Phase 4 auth/unlock contract (route, request/response schema, session lifetime, revocation).
      - Add corresponding Phase 5 MCP bootstrap/auth behavior and Phase 7 runtime invocation contract.
      - Update Input Index security rows to reflect canonical MCP unlock path (or explicitly prohibit standalone encrypted-DB MCP mode).

  - **High:** Redaction policy is inconsistent between global logging and market-data-specific redaction module.
    - Evidence:
      - Global logging policy redacts sensitive values to fixed placeholders: `docs/build-plan/01a-logging.md:215`, `docs/build-plan/01a-logging.md:231`.
      - Market-data helper retains partial secret fragments (`first4...last4`): `docs/build-plan/08-market-data.md:323`, `docs/build-plan/08-market-data.md:325`.
    - Risk:
      - Inconsistent redaction standard and potential secret fragment exposure.
    - Recommendation:
      - Consolidate to one redaction policy and one utility path for all logs.
      - If partial masking is intentionally allowed, document explicit rationale and where it is permitted.

  - **Medium:** Query-parameter regex is too broad and can over-redact non-secret fields.
    - Evidence:
      - Pattern includes bare `key` token without boundary constraints: `docs/build-plan/01a-logging.md:521`.
    - Risk:
      - False positives (for example, `monkey=`/`donkey=` substrings) reduce observability quality and can hide relevant diagnostics.
    - Recommendation:
      - Anchor key matching to query boundaries (`?`/`&`) and restrict to explicit sensitive parameter names.
      - Add targeted tests for false-positive avoidance.

  - **Low:** One overview line still implies Phase 1A has an extra package dependency.
    - Evidence:
      - `stdlib+1 pkg`: `docs/build-plan/00-overview.md:20`.
      - Logging doc and dependency manifest now define zero external dependencies: `docs/build-plan/01a-logging.md:82`, `docs/build-plan/dependency-manifest.md:27`.
    - Risk:
      - Minor planning confusion.
    - Recommendation:
      - Update overview dependency annotation to match current Phase 1A policy.

- Open questions:
  - Should standalone MCP be a first-class encrypted-DB access mode, or should encrypted DB remain GUI-unlock-only?
  - For `app.jsonl`, should catchall records stay in the same file as lifecycle events, or be split into a separate sink?
  - Is partial key masking (`abcd...wxyz`) acceptable anywhere, or should redaction be full replacement everywhere?

- Verdict:
  - Current build-plan is directionally improved on logging, but **not implementation-safe yet** for secure redaction guarantees and standalone MCP encrypted-DB access.

- Residual risk:
  - Without resolving critical findings, implementation is likely to ship with either secret leakage in logs or an undefined/fragile MCP unlock path for encrypted storage.

## Guardrail Output (If Required)

- Safety checks:
  - Documentation-only review output.
- Blocking risks:
  - No direct runtime changes; blockers are design-contract level only.
- Verdict:
  - Safe to proceed with a targeted docs correction pass before implementation.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Critical review completed and documented.
- Next steps:
  1. Resolve the three critical contract gaps (extra-field redaction, single-writer handler design, encrypted-DB MCP unlock contract).
  2. Apply a consistency patch across `01a-logging.md`, `04-rest-api.md`, `05-mcp-server.md`, `07-distribution.md`, `08-market-data.md`, and `input-index.md`.
  3. Run a focused reviewer pass on the corrected docs before implementation begins.
