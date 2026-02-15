# Flows and Guidance Critical Feedback (GPT-5 Codex)

Reviewed files:
- `AGENTS.md`
- `.agent/workflows/pre-build-research.md`
- `.agent/docs/architecture.md`
- `.agent/docs/domain-model.md`
- `.agent/docs/testing-strategy.md`

Date: 2026-02-14

## Critical Findings

1. TypeScript logging guidance is technically invalid in the main agent rules.
Evidence: `AGENTS.md:76`, `AGENTS.md:85`.
Impact: The "Maximum" tier includes `mcp-server` (TypeScript) but requires `structlog` (Python), which is not usable in TS and creates impossible compliance.
Recommendation: Split logging rules by language. Keep `structlog` for Python layers and define a TypeScript structured logger standard for `ui/` and `mcp-server/`.

2. The domain model is internally inconsistent on image ownership and repository contracts.
Evidence: `.agent/docs/domain-model.md:36`, `.agent/docs/domain-model.md:42`, `.agent/docs/domain-model.md:85`, `.agent/docs/domain-model.md:87`, `.agent/docs/domain-model.md:121`.
Impact: `ImageAttachment` is defined as polymorphic (`owner_type`, `owner_id`) but `ImageRepository` is trade-only (`trade_id`), which will force schema/API drift and rework.
Recommendation: Choose one canonical model:
either trade-only images everywhere, or polymorphic ownership everywhere including repository interfaces and relationship docs.

3. Trade side/action semantics conflict across docs.
Evidence: `.agent/docs/domain-model.md:68`, `.agent/docs/domain-model.md:69`, `.agent/docs/domain-model.md:70`, `.agent/workflows/pre-build-research.md:129`, `.agent/workflows/pre-build-research.md:139`, `.agent/workflows/pre-build-research.md:153`.
Impact: One part of the system defines `BOT`/`SLD` while another teaches the AI to emit `BUY`/`SELL`; this creates avoidable normalization bugs at import/API boundaries.
Recommendation: Define a single canonical enum and an explicit mapping table for external formats. Reference it in both docs.

4. The pre-build workflow is enforced as absolute and can block urgent or low-risk work.
Evidence: `.agent/workflows/pre-build-research.md:7`, `.agent/workflows/pre-build-research.md:209`, `AGENTS.md:39`, `AGENTS.md:40`.
Impact: "No implementation until workflow complete" conflicts with single-session constraints and can delay bug fixes, refactors, and small operational changes.
Recommendation: Add exemptions for small bug fixes, security patches, and internal refactors; require abbreviated research only when introducing new feature classes or external integrations.

## High Findings

1. Research workflow commands reference a missing local tool.
Evidence: `.agent/workflows/pre-build-research.md:34`, `.agent/workflows/pre-build-research.md:41`.
Observed repo state: `tools/web_search.py` is absent in this workspace.
Impact: The prescribed workflow cannot be executed as written.
Recommendation: Replace with an available supported tool path (or add `tools/web_search.py` with documented setup and arguments).

2. Notes persistence steps use a CLI that is not available in this environment.
Evidence: `.agent/workflows/pre-build-research.md:86`, `.agent/workflows/pre-build-research.md:179`, `AGENTS.md:42`, `AGENTS.md:43`.
Observed repo state: `pomera_notes` command is not present.
Impact: Session discipline and research archival steps are not reproducible for contributors.
Recommendation: Document one canonical notes path per environment:
MCP tool usage in agent sessions and CLI fallback only if installed.

3. Lint command targets contradict the documented package structure.
Evidence: `AGENTS.md:15`, `.agent/docs/testing-strategy.md:28`, `.agent/docs/architecture.md:33`, `.agent/docs/architecture.md:34`.
Impact: `npx eslint src/` is misaligned with documented `ui/` and `mcp-server/` packages, risking false confidence or command failures.
Recommendation: Replace with explicit targets (for example `npx eslint ui/src mcp-server/src --max-warnings 0`) or document the actual monorepo lint entrypoint.

4. Integration-test strategy bypasses stated encryption architecture.
Evidence: `.agent/docs/testing-strategy.md:9`, `.agent/docs/testing-strategy.md:20`, `.agent/docs/testing-strategy.md:67`, `.agent/docs/architecture.md:50`, `.agent/docs/architecture.md:51`.
Impact: In-memory SQLite tests do not exercise SQLCipher behavior or key derivation assumptions, leaving core data-at-rest risks untested.
Recommendation: Keep in-memory tests for speed, but add a required SQLCipher-backed integration suite for repository/UoW paths.

## Medium Findings

1. `Trade` is frozen but contains a mutable `list` field.
Evidence: `.agent/docs/domain-model.md:9`, `.agent/docs/domain-model.md:20`.
Impact: "Frozen" semantics are partially undermined because list contents can still mutate.
Recommendation: Use an immutable collection type (tuple) or remove `frozen=True` and document mutability rules explicitly.

2. `owner_type` is an unconstrained string in a critical polymorphic relation.
Evidence: `.agent/docs/domain-model.md:42`.
Impact: Free-form values increase invalid data risk and branch complexity.
Recommendation: Replace with an enum/value object and validate at entity construction boundaries.

3. Testing doc mixes API and UI terminology in a way that can confuse responsibility boundaries.
Evidence: `.agent/docs/architecture.md:57`, `.agent/docs/testing-strategy.md:7`.
Impact: "E2E" labeling around `TestClient` can blur integration vs true end-to-end coverage.
Recommendation: Rename API `TestClient` tests to integration/system tests and reserve E2E for full-process browser/UI runs.

## Suggested Remediation Order

1. Resolve model-contract contradictions first (`domain-model` + pre-build schema examples).
2. Fix execution blockers (`tools/web_search.py`, notes workflow command path, eslint targets).
3. Patch policy realism in `pre-build-research` (exemptions and scoped checklist).
4. Tighten test strategy to cover SQLCipher-specific behavior.
