# Re-check Handoff (Remaining Issues)

## Task

- **Date:** 2026-02-27
- **Task slug:** docs-build-plan-mcp-spec-completion-recheck-remaining-issues
- **Owner role:** reviewer
- **Scope:** Re-check the 4 previously remaining issues from `...mcp-spec-completion-recheck.md`

## Commands Run

- `git status --short -- docs/build-plan`
- `rg -n '/api/v1/plans|/api/v1/trade-plans' docs/build-plan/06b-gui-trades.md docs/build-plan/gui-actions-index.md`
- `rg -n 'quarterly_estimate|get_quarterly_estimate|record_quarterly_tax_payment' docs/build-plan/build-priority-matrix.md`
- `rg -n 'Total annotation blocks|All 68 tools now have' docs/build-plan/mcp-planned-readiness.md`
- `rg -n '#### Annotations' docs/build-plan -g '05?-mcp-*.md' | Measure-Object`
- `rg -n '^### \`get_log_settings\` \[Specified\]|^### \`update_log_level\` \[Specified\]' docs/build-plan/05a-mcp-zorivest-settings.md`
- `rg -n -i 'draft|not yet registered|not yet specified|planned tool' docs/build-plan/05a-mcp-zorivest-settings.md`
- direct line read around `05a` lines ~185–254

## Results

1. **Issue 1 (route drift `/api/v1/plans`)**: **Closed**
   - `docs/build-plan/06b-gui-trades.md:331` now uses `/api/v1/trade-plans`
   - `docs/build-plan/gui-actions-index.md:75` now uses `PATCH /api/v1/trade-plans/{id}/status`
   - `docs/build-plan/gui-actions-index.md:76` now uses `PUT /api/v1/trade-plans/{id}`

2. **Issue 2 (alias drift `quarterly_estimate`)**: **Closed**
   - `docs/build-plan/build-priority-matrix.md:237` now uses `get_quarterly_estimate`
   - Matrix item 76 includes canonical `get_quarterly_estimate` and `record_quarterly_tax_payment`

3. **Issue 3 (annotation count stale)**: **Closed**
   - `docs/build-plan/mcp-planned-readiness.md:163` now shows `Total annotation blocks | 69`
   - Measured category-file count: `69`

4. **Issue 4 (05a residual draft wording)**: **Closed**
   - `docs/build-plan/05a-mcp-zorivest-settings.md:193` now `// Specified — registered in build plan`
   - `docs/build-plan/05a-mcp-zorivest-settings.md:237` now `// Specified — registered in build plan`
   - No remaining matches for `draft/not yet registered/not yet specified/planned tool` in `05a`

## Verdict

`approved` — all four previously remaining issues are corrected in current file state.
