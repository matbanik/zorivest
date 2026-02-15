# Pomera Notes

## 2026-02-14 — Role-based subagent workflow setup

### Completed
- Added canonical role specs:
  - `.agent/roles/orchestrator.md`
  - `.agent/roles/coder.md`
  - `.agent/roles/tester.md`
  - `.agent/roles/reviewer.md`
  - `.agent/roles/researcher.md`
  - `.agent/roles/guardrail.md`
- Added canonical workflow: `.agent/workflows/orchestrated-delivery.md`
- Added task handoff artifacts:
  - `.agent/context/handoffs/TEMPLATE.md`
  - `.agent/context/handoffs/README.md`
- Updated references and awareness in:
  - `AGENTS.md`
  - `GEMINI.md`
  - `.agent/docs/architecture.md`
  - `.agent/context/current-focus.md`
  - `.agent/workflows/pre-build-research.md`

### Next Steps
1. Use handoff template on the first Phase 1 implementation task.
2. Validate role workflow in one full coder -> tester -> reviewer execution.

## 2026-02-14 — BUILD_PLAN critical review

### Completed
- Performed line-by-line review of `docs/BUILD_PLAN.md`.
- Created actionable feedback doc: `docs/BUILD_PLAN_GPT53CODEX_FEEDBACK.md`.
- Included recommended design selections for:
  - Canonical image API contract (multipart REST, MCP adapts base64 to multipart).
  - API port strategy (default `8765`, env-configurable).
  - Test structure standardization (`tests/...`).

### Key Risks Identified
- Conflicting image contracts/routes across API, MCP, and UI.
- Contradictory phase order (MCP before API vs API-before-MCP narrative).
- Inconsistent model field naming (`account` vs `account_id`, image ownership fields).
- Non-runnable snippets in sections presented as implementation guides.

### Next Steps
1. Apply the feedback to `docs/BUILD_PLAN.md` in one consistency pass.
2. Update `.agent/docs/architecture.md` port references to align on default `8765`.
3. Re-validate all examples for runnable accuracy and consistent route contracts.
