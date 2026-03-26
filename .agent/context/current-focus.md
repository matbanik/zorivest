# Current Focus — Zorivest

> Last updated: 2026-03-23

## Active Phase

**Phase 8 — Market Data Aggregation Layer (in progress)**

## Current Priority

Complete post-MEU-65 closeout deliverables (reflection, metrics, commit messages). MEU-90a/b
persistence wiring cluster is done; real `ProviderConnectionService` is now wired in `main.py`.

### Dependency Chain

```
MEU-90a/b/c/d  ← service-wiring ✅ DONE (keys → encrypted DB, real providers)
  └── MEU-65   ← market-data-gui  ✅ DONE (14 providers, E2E Wave 6 complete)
        └── MEU-48 calculator ticker auto-fill  🔵 next
```

## Agent Configuration

| Agent | Role | Config File | Workflow |
|-------|------|------------|----------|
| Opus 4.6 (Antigravity) | Implementation (orchestrator, coder, tester) | `AGENTS.md` (via `GEMINI.md` shim) | `.agent/workflows/tdd-implementation.md` |
| GPT-5.4 Codex | Validation (reviewer, guardrail) | `AGENTS.md` | `.agent/workflows/validation-review.md` |
| Handoff Protocol | — | — | `.agent/workflows/meu-handoff.md` |

## Next Steps

1. ✅ **MEU-65 `market-data-gui`** — fully closed (2026-03-23): Wave 6 E2E 7/7 pass, real `ProviderConnectionService` wired, all trackers updated.
2. ✅ **MEU-90a** — `SqlAlchemyUnitOfWork` wired into FastAPI lifespan
3. ✅ **MEU-90b** — real `ProviderConnectionService` wired (API key encryption + DB persistence)
4. ✅ **agents-terminal-optimization-infra** — P0 block in AGENTS.md, terminal-preflight SKILL.md, workflow amendments (2026-03-25)
5. **Next:** MEU-48 calculator ticker auto-fill (unblocked) or next P2 item per build plan

## Archived Files (pomera_notes)

The following files were archived to pomera_notes and deleted from the repo on 2026-03-07:

| Former Path | pomera Note ID | Reason |
|-------------|---------------|--------|
| `docs/execution/prompts/TEMPLATE.md` | 290 | Replaced by `.agent/workflows/create-plan.md` |
| `docs/execution/prompts/2026-03-06-meu-1-calculator-pilot.md` | 291 | Historical prompt archived |
| `docs/execution/prompts/2026-03-07-meu-2-enums.md` | 292 | Historical prompt archived |
| `docs/execution/prompts/2026-03-07-meu-3-entities.md` | 293 | Historical prompt archived |

## Recently Completed

- [x] APPLICATION_PURPOSE.md — vision and requirements
- [x] DESIGN_PROPOSAL.md — hybrid architecture
- [x] BUILD_PLAN.md — phased implementation plan
- [x] Agentic coding research + questionnaire (22/22 answered)
- [x] AGENTS.md + .agent/ structure generated
- [x] Role-based subagent workflow + role specs added
- [x] `docs/build-plan/*.md` critical review completed; feedback saved in `BUILD_PLAN_CRITICAL_FEEDBACK.md`
- [x] `docs/build-plan/input-index.md` critical review completed; feedback saved in `INPUT_INDEX_CRITICAL_FEEDBACK.md`
- [x] `docs/build-plan/` market-data GUI/API update review completed; handoff saved in `.agent/context/handoffs/2026-02-15-build-plan-market-data-gui-input-index-review.md`
- [x] `docs/build-plan/06-gui.md` critical review completed; handoff saved in `.agent/context/handoffs/2026-02-16-06-gui-critical-review.md`
- [x] `docs/build-plan/` critical review completed with logging deep-dive (`01a-logging.md`); handoff saved in `.agent/context/handoffs/2026-02-17-build-plan-logging-critical-review.md`
- [x] `docs/build-plan/` critical review completed for logging redaction + MCP encrypted-DB access contracts; handoff saved in `.agent/context/handoffs/2026-02-17-build-plan-logging-mcp-encrypted-db-critical-review.md`
- [x] `docs/build-plan/` critical review completed for backup/restore + settings defaults/export-import updates; handoff saved in `.agent/context/handoffs/2026-02-18-build-plan-backup-restore-defaults-critical-review.md`
- [x] `docs/build-plan/` critical review completed for settings validation/cache/422 GUI error-contract updates; handoff saved in `.agent/context/handoffs/2026-02-18-build-plan-settings-validation-critical-review.md`
- [x] `docs/build-plan/` critical review completed for MCP guard circuit-breaker + emergency-stop updates; handoff saved in `.agent/context/handoffs/2026-02-18-build-plan-mcp-guard-emergency-stop-critical-review.md`
- [x] `docs/build-plan/` critical review completed for release/versioning architecture updates (`00-overview.md`, `07-distribution.md`, `dependency-manifest.md`); handoff saved in `.agent/context/handoffs/2026-02-18-build-plan-release-versioning-critical-review.md`
- [x] `docs/build-plan/` critical review completed for index updates (`gui-actions-index.md`, `output-index.md`, `input-index.md`); handoff saved in `.agent/context/handoffs/2026-02-18-build-plan-indexes-critical-review.md`
- [x] `docs/build-plan/` critical review completed for MCP enhancements (`zorivest_diagnose`, metrics middleware, `zorivest_launch_gui`, MCP Server Status panel + related indexes/testing); handoff saved in `.agent/context/handoffs/2026-02-18-build-plan-mcp-enhancements-critical-review.md`
- [x] `_inspiration/scheduling_research/` three-model synthesis completed (`chatgpt-prompt-1`, `claude-prompt-1`, `gemini-prompt-1`) with Opus comparison; deliverable saved in `_inspiration/scheduling_research/codex-composite-policy-engine-synthesis.md`, handoff in `.agent/context/handoffs/2026-02-19-scheduling-research-composite.md`
- [x] `_inspiration/scheduling_research/2/` three-model synthesis completed (`chatgpt-prompt-2`, `claude-prompt-2`, `gemini-prompt-2`) with Opus comparison; deliverable saved in `_inspiration/scheduling_research/2/codex-composite-pipeline-step-chain-synthesis.md`, handoff in `.agent/context/handoffs/2026-02-19-scheduling-research-2-composite.md`
- [x] `2026-02-19-phase9-build-plan.md` critically reviewed against `_inspiration/scheduling_research/`; findings saved in `.agent/context/handoffs/2026-02-20-phase9-plan-vs-scheduling-research-critical-review.md`
- [x] `docs/build-plan/` detailed planning critically reviewed; findings saved in `.agent/context/handoffs/2026-02-20-docs-build-plan-detailed-critical-review.md`
- [x] `docs/build-plan/image-architecture.md` WebP-standardization updates critically reviewed for cross-plan alignment; findings saved in `.agent/context/handoffs/2026-02-20-image-architecture-webp-critical-review.md`
- [x] `_inspiration/import_research/Build Plan Expansion Ideas.md` critically reviewed with independent web validation and Zorivest-fit scoring; findings saved in `.agent/context/handoffs/2026-02-20-build-plan-expansion-ideas-critical-review.md`
- [x] `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md` critically reviewed for derivation quality vs source ideas; findings saved in `.agent/context/handoffs/2026-02-21-build-plan-expansion-implementation-plan-derivation-critical-review.md`
- [x] `docs/build-plan/` critically reviewed for alignment with `_inspiration/import_research/Build Plan Expansion - Implementation Plan.md`; findings saved in `.agent/context/handoffs/2026-02-21-docs-build-plan-vs-expansion-implementation-plan-critical-review.md`
- [x] `docs/build-plan/` critically reviewed for implementation execution risks after latest updates; findings saved in `.agent/context/handoffs/2026-02-21-docs-build-plan-critical-review-execution-risks.md`
- [x] Web research completed for feature-validation rigor + anti-drift/anti-fake-completion planning controls; findings saved in `.agent/context/handoffs/2026-02-21-docs-build-plan-feature-validation-and-agentic-integrity-research.md`
- [x] `docs/build-plan/` critically reviewed for `10-service-daemon.md` integration + platform behavior validity; findings saved in `.agent/context/handoffs/2026-02-21-docs-build-plan-service-daemon-integration-critical-review.md`
- [x] `docs/build-plan/` critically reviewed for GUI↔MCP feature parity and contract drift; findings saved in `.agent/context/handoffs/2026-02-21-docs-build-plan-gui-mcp-parity-critical-review.md`
- [x] `.agent/context/handoffs/2026-02-26-mcp-session3-plan.md` critically reviewed against `docs/build-plan/` cross-cutting index/strategy files; findings saved in `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-session3-plan-critical-review.md`
- [x] `.agent/context/handoffs/2026-02-26-mcp-session4-plan.md` + `.agent/context/handoffs/2026-02-26-mcp-session4-walkthrough.md` critically reviewed against `docs/build-plan/`; findings saved in `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-session4-plan-critical-review.md`
- [x] `.agent/context/handoffs/2026-02-26-mcp-session6-plan.md` + `.agent/context/handoffs/2026-02-26-mcp-session6-walkthrough.md` critically reviewed against `docs/build-plan/`; findings saved in `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-session6-plan-critical-review.md`
- [x] MCP Session 2/3/4/6 open issues re-check completed; closure matrix and remaining open items saved in `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-open-issues-recheck.md`
- [x] Remaining open MCP docs issues patched (Session 3 baseline note + Session 6 semantic verification guards); patch handoff saved in `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-open-issues-patch.md`
- [x] `docs/build-plan/03-service-layer.md` + cross-plan wholeness critically reviewed via workflow; findings saved in `.agent/context/handoffs/2026-02-27-build-plan-03-service-layer-wholeness-critical-review.md`
- [x] `docs/build-plan/04-rest-api.md` + Phase 03/05 contract wholeness critically reviewed via workflow; findings saved in `.agent/context/handoffs/2026-02-27-build-plan-04-rest-api-wholeness-critical-review.md`
- [x] Re-check completed for `docs/build-plan/04-rest-api.md` wholeness fixes; results saved in `.agent/context/handoffs/2026-02-27-build-plan-04-rest-api-wholeness-recheck.md`
- [x] Final re-check completed for `docs/build-plan/04-rest-api.md` wholeness fixes; results saved in `.agent/context/handoffs/2026-02-27-build-plan-04-rest-api-wholeness-final-recheck.md`
- [x] `docs/build-plan/` critically reviewed from the `friction-inventory.md` perspective with official MCP/Anthropic/OpenAI research and dual-agent implementation guidance; handoff saved in `.agent/context/handoffs/2026-03-06-docs-build-plan-friction-agentic-senior-review.md`
- [x] 16 reference docs relocated from `docs/` to `_inspiration/`; `docs/build-plan/` links and remaining `_inspiration/` stale references normalized, handoff saved in `.agent/context/handoffs/2026-03-06-docs-inspiration-relocation.md`
- [x] **MEU-65 `market-data-gui`** — Market Data Providers GUI page complete (2026-03-23): 14 providers (12 registry + Yahoo Finance + TradingView free), `/settings/market` route, Settings nav card, Get API Key via `shell.openExternal` IPC, free-provider badge, real `ProviderConnectionService` wired, Wave 6 E2E 7/7 pass. Plan: `docs/execution/plans/2026-03-21-market-data-gui/task.md`
