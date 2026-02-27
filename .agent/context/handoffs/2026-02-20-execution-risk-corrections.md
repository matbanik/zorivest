# Handoff: Execution Risk Corrections

**Date**: 2026-02-20
**Task**: Address 12 findings from `docs-build-plan-critical-review-execution-risks.md`
**Status**: ✅ Complete

## What Was Done

12 findings (4 Critical, 5 High, 2 Medium, 1 Low) corrected across 13 files:

### Critical
1. **MCP import tools** → multipart upload helper in `05-mcp-server.md`
2. **`zorivest_diagnose`** → `safeFetch` checks `res.ok`, provider mapping try/catch
3. **Alpaca credentials** → `encrypted_api_secret` column + `api_secret` field in `08-market-data.md`
4. **Scheduling split-brain** → canonical Phase 9 contracts in `06e-gui-scheduling.md`

### High
5. **Expansion REST routes** → already present (no action needed)
6. **Index endpoints** → query-param format + `/mcp-guard/status` in `output-index.md`
7. **Provider count** → 9→12 in 7 files
8. **CI pipeline** → `pyright` + `packages/core/tests` in `07-distribution.md` + `validate.ps1`
9. **Tax GUI refs** → items 50–82, item 75 in `06g-gui-tax.md`

### Medium/Low
10. **Duplicate PDF parser** → marked in `build-priority-matrix.md`
11. **Account components** → +2 in `06d-gui-accounts.md` outputs
12. **Item count** → 106→131 in `00-overview.md`

## Decisions Made
- Provider count: **12** (canonical per `08-market-data.md`)
- Type checker: **pyright** (matches `validate.ps1`)
- Test path: **`packages/core/tests`** (monorepo convention)

## Known Issues (Pre-Existing)
- Build plan validator shows 19 broken `_inspiration/` links (files moved/renamed)
- `07-distribution.md` uses `## 7.15 Exit Criteria` instead of `## Exit Criteria`

## Files Modified
`05-mcp-server.md`, `08-market-data.md`, `06e-gui-scheduling.md`, `output-index.md`, `06g-gui-tax.md`, `build-priority-matrix.md`, `00-overview.md`, `input-index.md`, `06f-gui-settings.md`, `06-gui.md`, `07-distribution.md`, `06d-gui-accounts.md`, `validate.ps1`
