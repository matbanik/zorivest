# Handoff: Planning Corrections — Agentic Continuity Review

**Date**: 2026-03-06
**Source**: [2026-03-06-docs-build-plan-agentic-continuity-review.md](2026-03-06-docs-build-plan-agentic-continuity-review.md)
**Workflow**: `/planning-corrections`
**Status**: ✅ Complete

---

## Findings Disposition

| # | Severity | Disposition | Files Changed |
|---|----------|-------------|---------------|
| C-1 | Critical | ✅ Fixed | `tdd-implementation.md`, `GEMINI.md`, `prompt-templates.md` |
| C-2 | Critical | ✅ Residual fixed | `BUILD_PLAN.md` (9→12 providers) |
| H-1 | High | ✅ Fixed | `BUILD_PLAN.md` (+phases 1A/2A/9/10, status tracker) |
| H-2 | High | ✅ Fixed | `06-gui.md`, `06e-gui-scheduling.md`, `06f-gui-settings.md`, `00-overview.md` |
| H-3 | High | ✅ Fixed | `tdd-implementation.md`, `validation-review.md` |
| H-4 | High | ⏭️ Deferred | Advisory — no file fix; process rule for future phases |
| M-1 | Medium | ✅ Fixed | `build-priority-matrix.md` |
| M-2 | Medium | ⏭️ Deferred | Advisory — needs design decision on Phase 5/10 coupling |

## Changed Files

| File | Finding | Change |
|------|---------|--------|
| `.agent/workflows/tdd-implementation.md` | C-1, H-3 | `CLAUDE.md`→`GEMINI.md`; tiered validation paths |
| `GEMINI.md` | C-1 | +5 slash commands (`/tdd-implementation`, `/validation-review`, `/planning-corrections`, `/critical-review-feedback`, `/meu-handoff`) |
| `.agent/docs/prompt-templates.md` | C-1 | Planning gate added to "Start a New MEU" prompt |
| `docs/BUILD_PLAN.md` | H-1, C-2 | +phases 1A/2A/9/10; 9→12 providers; deps updated for Phase 5/6; status tracker expanded |
| `docs/build-plan/00-overview.md` | H-2 | Phase 10 dep: `4,7`→`4,7,9` |
| `docs/build-plan/06-gui.md` | H-2 | Prerequisites expanded (+Phase 9, +Phase 10) |
| `docs/build-plan/06e-gui-scheduling.md` | H-2 | +Phase 9 prerequisite |
| `docs/build-plan/06f-gui-settings.md` | H-2 | +Phase 8, +Phase 10 prerequisites |
| `.agent/workflows/validation-review.md` | H-3 | Self-contained phase-scoped matrix, tiered validation paths, tsc/vitest/eslint gate for Phase 5+ |
| `docs/build-plan/build-priority-matrix.md` | M-1 | "Pydantic validation" → "Dataclass validation (Pydantic deferred to Phase 4)" |

## Verification Evidence

| Check | Result |
|-------|--------|
| `python tools/validate_build_plan.py` | ✅ PASSED (0 errors, 3 pre-existing warnings) |
| `rg "CLAUDE.md" .agent/ GEMINI.md` | ⚠️ Matches in `deep-research-prompts-dual-agent.md:17,44` (research notes, not active workflows) — no startup-contract regression |
| GUI prerequisite headers | ✅ All three files list correct phases |
| Phase 10 dep consistency (`00-overview` vs `10-service-daemon`) | ✅ Both say `Phase 4, 7, 9` |
| Pydantic in build-priority-matrix L19 | ✅ Now says "Dataclass validation" |
| Tiered validation notes | ✅ Present in both `tdd-implementation.md` and `validation-review.md` |

## Open Items (Deferred)

1. **H-4 (Work-unit sizing)**: Add standing rule requiring MEU registry before phase implementation begins
2. **M-2 (Phase 5/10 coupling)**: Decide if service-control MCP tools belong in `core` toolset or a Phase 10-gated toolset
