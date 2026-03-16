# Pipeline Steps — Session Reflection

**Date**: 2026-03-15/16
**MEUs**: MEU-85 (FetchStep), MEU-86 (TransformStep), MEU-87 (StoreReportStep + RenderStep)
**Review Rounds**: 7

## What Went Well

1. **TDD pattern held** — all 4 pipeline steps were implemented test-first with AC-mapped tests
2. **Hook-based architecture** — delegation to injected collaborators via `context.outputs` cleanly separates core from infra
3. **CriteriaResolver per-field design** — static passthrough with typed dispatch matches the build-plan spec and is extensible

## What Cost Time

1. **Missing-collaborator false success** — hooks silently returning defaults instead of failing caused 3 correction passes
2. **Pyright narrowing** — compound assert expressions don't narrow; restructuring to early-return + simple guard was the fix
3. **Test-codify-degradation trap** — writing tests that assert degraded behavior (success with None pdf_path) delayed catching the real contract violations

## Rules Checked (10/10)

| Rule | Followed? |
|------|-----------|
| TDD red-green-refactor | ✅ |
| Hook methods delegate to infra | ✅ |
| ValueError for missing collaborators | ✅ (after Pass 4) |
| Build-plan contract adherence | ✅ (per-field criteria, spec_json, pdf failure) |
| Anti-placeholder scan | ✅ |
| No stale evidence | ✅ (after Pass 6) |
| Pyright clean | ✅ |
| Ruff clean | ✅ |
| Regression green | ✅ |
| Closeout artifacts complete | ✅ |

## Key Lesson

**Don't codify degraded behavior in tests.** When a hook returns a default/fallback, the test should assert failure — not validate the fallback as acceptable. This was the root cause of the store/render multi-pass loop.
