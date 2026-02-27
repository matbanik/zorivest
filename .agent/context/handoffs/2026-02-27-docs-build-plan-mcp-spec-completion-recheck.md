# Re-check Handoff

## Scope

Re-check of prior findings from:

- `.agent/context/handoffs/2026-02-27-docs-build-plan-mcp-spec-completion-critical-review.md`

Against current `docs/build-plan/*` file state.

## Commands Run

- `git status --short -- docs/build-plan`
- `rg -n -i "all 8 tools are \*\*planned\*\*|## Planned Tools|DRAFT — Planned tool|not yet specified" docs/build-plan/05h-mcp-tax.md docs/build-plan/05c-mcp-trade-analytics.md docs/build-plan/05d-mcp-trade-planning.md docs/build-plan/05f-mcp-accounts.md`
- `rg -n "REST Dependency:.*(GET|POST) /api/v1/tax/lots|/api/v1/tax/lots|@tax_router.get" docs/build-plan/05h-mcp-tax.md docs/build-plan/04-rest-api.md docs/build-plan/mcp-tool-index.md docs/build-plan/mcp-planned-readiness.md`
- `rg -n "\| 18\.8 \| Agent Tax Simulation|\| 18\.9 \| Agent Loss Harvesting|\| 18\.10 \| Agent Trade Plan|\| 4\.6 \| Harvestable Losses|\| 5\.1 \| Create plan|\| 18\.1 \| Simulate|\| 19\.1 \| Scan portfolio" docs/build-plan/input-index.md docs/build-plan/output-index.md docs/build-plan/gui-actions-index.md`
- `rg -n "/api/v1/plans|/api/v1/trade-plans" docs/build-plan`
- `rg -n "quarterly_estimate|get_quarterly_estimate|record_quarterly_tax_payment" docs/build-plan/build-priority-matrix.md docs/build-plan/05h-mcp-tax.md docs/build-plan/mcp-tool-index.md`
- `rg -n "DRAFT — Not yet registered|not yet registered" docs/build-plan/05a-mcp-zorivest-settings.md`
- `rg -n "#### Annotations" docs/build-plan -g "05?-mcp-*.md" | Measure-Object`
- `rg -n "Total annotation blocks|All 68 tools now have" docs/build-plan/mcp-planned-readiness.md`

## Closed Findings

1. Residual planned wording in MCP tax/report/plan/accounts category files: **closed**
   - No matches for old phrases in `05c/05d/05f/05h`.
2. `get_tax_lots` method mismatch (`POST` vs `GET`): **closed**
   - `05h`: `GET /api/v1/tax/lots` now matches `04-rest-api`.
3. Previously cited index rows still pending (`📋`/`🔶`): **closed**
   - `input-index` rows 18.8/18.9/18.10 now ✅
   - `output-index` row 4.6 now ✅
   - `gui-actions-index` rows 5.1, 18.1, 19.1 now ✅
4. `/api/v1/plans` drift in `06c-gui-planning.md` and gui action 5.1: **closed**
   - Both now use `/api/v1/trade-plans`.

## Remaining Findings

1. **Medium** — Residual `/api/v1/plans` references still exist (partial route drift)
   - `docs/build-plan/06b-gui-trades.md:331` (`linked_plan_id` source still `/api/v1/plans`)
   - `docs/build-plan/gui-actions-index.md:75` (`PATCH /api/v1/plans/{id}/status`)
   - `docs/build-plan/gui-actions-index.md:76` (`PUT /api/v1/plans/{id}` set trade_id)

2. **Low** — Alias drift remains in priority matrix
   - `docs/build-plan/build-priority-matrix.md:237` still uses `quarterly_estimate` alias instead of canonical `get_quarterly_estimate`.

3. **Low** — Stale metrics in readiness summary
   - `docs/build-plan/mcp-planned-readiness.md:163` says `Total annotation blocks | 65`
   - Current measured category-file count is `69`.

4. **Low** — Residual draft wording in logging MCP category file
   - `docs/build-plan/05a-mcp-zorivest-settings.md:193`
   - `docs/build-plan/05a-mcp-zorivest-settings.md:237`
   - Both still say `DRAFT — Not yet registered in build plan` while headings are `[Specified]`.

## Verdict

`partial_fixes_applied` — prior high-severity issues are resolved; a few medium/low consistency items remain.
