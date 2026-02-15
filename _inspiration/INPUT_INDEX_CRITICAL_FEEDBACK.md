# input-index.md Critical Feedback

Date: 2026-02-15
Scope: `docs/build-plan/input-index.md`
Review style: defect-focused (contract fidelity, cross-doc consistency, implementability)

## Critical Findings

1. Canonical claim is invalidated by unsupported input contracts
Evidence:
- File claims this is a canonical registry of "every input the system accepts" (`docs/build-plan/input-index.md:5`).
- OAuth/email/scheduling inputs are listed as active contracts (`docs/build-plan/input-index.md:326`, `docs/build-plan/input-index.md:390`, `docs/build-plan/input-index.md:413`) but referenced build-plan contracts do not define those routes/tools:
  - REST phase currently specifies trade/image endpoints only (`docs/build-plan/04-rest-api.md:24`, `docs/build-plan/04-rest-api.md:137`).
  - MCP phase currently specifies trade/image/calculator tools only (`docs/build-plan/05-mcp-server.md:25`, `docs/build-plan/05-mcp-server.md:117`).
  - Priority matrix has no email/scheduler work items (`docs/build-plan/build-priority-matrix.md:11`, `docs/build-plan/build-priority-matrix.md:136`).
Impact:
- Teams/agents will implement against contracts that do not exist in the active build plan.
Recommended fix:
- Add a `status` column (`implemented` / `planned` / `research-only`) and move non-build-plan items to a separate roadmap/research appendix.

2. Source-of-truth reference is broken
Evidence:
- Header links `../../user-input-features.md` as source (`docs/build-plan/input-index.md:3`), but that file is missing in repository.
Impact:
- Provenance and traceability for this "canonical" index are broken.
Recommended fix:
- Restore the source file or replace with existing source docs (e.g., build-plan files + explicitly named research docs).

## High Findings

1. Position calculator contract drift (`account_id` + long/short validation)
Evidence:
- Index includes calculator `account_id` and account auto-resolution (`docs/build-plan/input-index.md:22`, `docs/build-plan/input-index.md:27`).
- MCP calculator schema only accepts `balance`, `risk_pct`, `entry`, `stop`, `target` (`docs/build-plan/05-mcp-server.md:101`, `docs/build-plan/05-mcp-server.md:106`).
- Domain calculator function also has no `account_id`/direction parameter (`docs/build-plan/01-domain-layer.md:267`, `docs/build-plan/01-domain-layer.md:273`).
- Index test expects direction-aware validation (`stop must be below entry for BOT`) (`docs/build-plan/input-index.md:35`) without any `action` input in calculator contract.
Impact:
- Inconsistent calculator behavior expectations across UI/MCP/domain.
Recommended fix:
- Either remove `account_id` and direction-specific validation from index, or add explicit calculator contract extension everywhere.

2. Tax profile field names do not match canonical domain model
Evidence:
- Index uses `default_cost_basis_method`, `include_drip_wash`, `include_spousal` (`docs/build-plan/input-index.md:236`, `docs/build-plan/input-index.md:237`, `docs/build-plan/input-index.md:238`).
- Domain model names are `default_cost_basis`, `include_drip_wash_detection`, `include_spousal_accounts` (`docs/build-plan/domain-model-reference.md:264`, `docs/build-plan/domain-model-reference.md:267`, `docs/build-plan/domain-model-reference.md:268`).
Impact:
- API/MCP/GUI payloads generated from this index will mismatch core model fields.
Recommended fix:
- Align names to domain model (or add explicit alias mapping rules).

3. Duplicate-trade behavior conflicts with REST create contract
Evidence:
- Index test says duplicate create returns `None` (`docs/build-plan/input-index.md:60`).
- Service-layer test also expects `None` for dedupe (`docs/build-plan/03-service-layer.md:33`).
- REST create route assumes a non-null result and returns 201 with `result.exec_id` (`docs/build-plan/04-rest-api.md:61`, `docs/build-plan/04-rest-api.md:65`).
Impact:
- Duplicate `exec_id` path is under-specified and can produce runtime/API inconsistency.
Recommended fix:
- Define canonical duplicate behavior (idempotent 200, 409 conflict, or 202 skipped) and align service + REST + index tests.

4. `provider_preference` is documented as input but not exposed by market-data routes/tools
Evidence:
- Index includes `provider_preference` (`docs/build-plan/input-index.md:373`).
- REST quote endpoint only exposes `ticker` (`docs/build-plan/08-market-data.md:469`, `docs/build-plan/08-market-data.md:471`).
- MCP `get_stock_quote` tool only takes `ticker` (`docs/build-plan/08-market-data.md:520`, `docs/build-plan/08-market-data.md:523`).
Impact:
- User/agent cannot provide an input that the index advertises.
Recommended fix:
- Either add provider selection params to REST/MCP contracts or remove this input from index.

## Medium Findings

1. Trade plan input naming/status drift
Evidence:
- Index defines `thesis` as input (`docs/build-plan/input-index.md:123`).
- Domain model field is `strategy_description` (thesis is descriptive text, not field name) (`docs/build-plan/domain-model-reference.md:82`).
- Index test expects creation with `ACTIVE` status (`docs/build-plan/input-index.md:137`), while infra model default is `draft` (`docs/build-plan/02-infrastructure.md:104`).
Impact:
- Generated forms and tests will not match plan contracts.
Recommended fix:
- Use canonical field names and default status from domain/infra contracts.

2. Image owner inputs are over-generalized for current REST routes
Evidence:
- Index lists API inputs `owner_type`/`owner_id` (`docs/build-plan/input-index.md:75`, `docs/build-plan/input-index.md:76`).
- Current REST upload endpoint is trade-scoped path (`/trades/{exec_id}/images`) and not a generic owner endpoint (`docs/build-plan/04-rest-api.md:94`, `docs/build-plan/04-rest-api.md:100`).
Impact:
- API consumers may attempt unsupported payload fields.
Recommended fix:
- Mark owner polymorphism as internal/service-level for now, or define explicit generic owner routes.

3. Summary statistics are internally inconsistent
Evidence:
- Claims `feature groups = 17` and `MCP-only inputs = 0` (`docs/build-plan/input-index.md:480`, `docs/build-plan/input-index.md:483`).
- File includes 18 numbered top-level sections (plus `15d`), and includes MCP-only `image_base64` (`docs/build-plan/input-index.md:73`).
Impact:
- Reduces trust in the index as an operational control document.
Recommended fix:
- Auto-generate summary stats from the tables or remove approximate stats.

## Suggested Next Step

Normalize this file into two explicit scopes:
1. `implemented_contracts` (strictly what current build-plan phases define)
2. `planned_or_research_contracts` (future and research-backed features)

That change removes ambiguity and prevents implementation against non-existent endpoints/tools.
