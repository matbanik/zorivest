---
project: "2026-05-14-tax-engine-wiring"
source: "docs/execution/plans/2026-05-14-tax-engine-wiring/implementation-plan.md"
meus: ["MEU-148", "MEU-149", "MEU-150", "MEU-151", "MEU-152", "MEU-153"]
status: "in_progress"
template_version: "2.0"
ad_hoc: ["TAX-DBMIGRATION"]
---

# Task — Phase 3E Tax Engine Wiring (Session 5a)

> **Project:** `2026-05-14-tax-engine-wiring`
> **Type:** Service + API + MCP
> **Estimate:** ~12 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| | **MEU-150: YTD Tax Summary** | | | | |
| 1 | Write FIC + tests for `ytd_summary()` — AC-150.1→150.6 | coder | `tests/unit/test_tax_ytd_summary.py` | `uv run pytest tests/unit/test_tax_ytd_summary.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ytd-fic.txt; Get-Content C:\Temp\zorivest\pytest-ytd-fic.txt \| Select-Object -Last 30` | `[x]` |
| 2 | Implement `YtdTaxSummary` dataclass + `ytd_summary()` method | coder | `tax_service.py` additions | `uv run pytest tests/unit/test_tax_ytd_summary.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ytd.txt; Get-Content C:\Temp\zorivest\pytest-ytd.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-151: Deferred Loss Report** | | | | |
| 3 | Write FIC + tests for `deferred_loss_report()` — AC-151.1→151.5 | coder | `tests/unit/test_tax_deferred_loss.py` | `uv run pytest tests/unit/test_tax_deferred_loss.py -x --tb=short -v *> C:\Temp\zorivest\pytest-deferred-fic.txt; Get-Content C:\Temp\zorivest\pytest-deferred-fic.txt \| Select-Object -Last 30` | `[x]` |
| 4 | Implement `DeferredLossReport` dataclass + `deferred_loss_report()` method | coder | `tax_service.py` additions | `uv run pytest tests/unit/test_tax_deferred_loss.py -x --tb=short -v *> C:\Temp\zorivest\pytest-deferred.txt; Get-Content C:\Temp\zorivest\pytest-deferred.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-152: Tax Alpha Report** | | | | |
| 5 | Write FIC + tests for `tax_alpha_report()` — AC-152.1→152.5 | coder | `tests/unit/test_tax_alpha.py` | `uv run pytest tests/unit/test_tax_alpha.py -x --tb=short -v *> C:\Temp\zorivest\pytest-alpha-fic.txt; Get-Content C:\Temp\zorivest\pytest-alpha-fic.txt \| Select-Object -Last 30` | `[x]` |
| 6 | Implement `TaxAlphaReport` dataclass + `tax_alpha_report()` method | coder | `tax_service.py` additions | `uv run pytest tests/unit/test_tax_alpha.py -x --tb=short -v *> C:\Temp\zorivest\pytest-alpha.txt; Get-Content C:\Temp\zorivest\pytest-alpha.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-153: Transaction Audit** | | | | |
| 7 | Write FIC + tests for `run_audit()` — AC-153.1→153.7 | coder | `tests/unit/test_tax_audit.py` | `uv run pytest tests/unit/test_tax_audit.py -x --tb=short -v *> C:\Temp\zorivest\pytest-audit-fic.txt; Get-Content C:\Temp\zorivest\pytest-audit-fic.txt \| Select-Object -Last 30` | `[x]` |
| 8 | Implement `AuditFinding`, `AuditReport` dataclasses + `run_audit()` method | coder | `tax_service.py` additions | `uv run pytest tests/unit/test_tax_audit.py -x --tb=short -v *> C:\Temp\zorivest\pytest-audit.txt; Get-Content C:\Temp\zorivest\pytest-audit.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-148: Tax REST API Wiring** | | | | |
| 9 | Wire real TaxService into main.py lifespan — AC-148.1 | coder | `main.py` updated | `rg "TaxService" packages/api/src/zorivest_api/main.py *> C:\Temp\zorivest\import-check.txt; Get-Content C:\Temp\zorivest\import-check.txt` | `[x]` |
| 10 | Remove StubTaxService from stubs.py — AC-148.2 | coder | `stubs.py` cleaned | `rg StubTaxService packages/ *> C:\Temp\zorivest\stub-removal.txt; Get-Content C:\Temp\zorivest\stub-removal.txt` (expect 0 matches) | `[x]` |
| 11 | Refactor route handlers to unpack bodies for real TaxService — AC-148.3, AC-148.9 | coder | `routes/tax.py` updated | `uv run pytest tests/integration/test_tax_routes.py -x --tb=short -v *> C:\Temp\zorivest\pytest-routes.txt; Get-Content C:\Temp\zorivest\pytest-routes.txt \| Select-Object -Last 30` | `[x]` |
| 12 | Add 2 new routes (deferred-losses, alpha) — AC-148.5 | coder | `routes/tax.py` new endpoints | `rg "deferred.losses\|/alpha" packages/api/src/zorivest_api/routes/tax.py *> C:\Temp\zorivest\route-check.txt; Get-Content C:\Temp\zorivest\route-check.txt` | `[x]` |
| 13 | Implement record_payment persistence — AC-148.6 | coder | `tax_service.py` record_payment body | `rg "NotImplementedError" packages/core/src/zorivest_core/services/tax_service.py *> C:\Temp\zorivest\notimp-check.txt; Get-Content C:\Temp\zorivest\notimp-check.txt` (expect 0 matches) | `[x]` |
| 13b | Implement QuarterlyEstimate infra (model, repo, UoW, DB init) — AC-148.6 | coder | `models.py`, `tax_repository.py`, `unit_of_work.py`, `database_init.py` | `uv run pytest tests/unit/ -k "quarterly" -x --tb=short -v *> C:\Temp\zorivest\pytest-quarterly.txt; Get-Content C:\Temp\zorivest\pytest-quarterly.txt \| Select-Object -Last 30` | `[x]` |
| 14 | Write integration tests for all tax routes — AC-148.7 | coder | `tests/integration/test_tax_routes.py` | `uv run pytest tests/integration/test_tax_routes.py -x --tb=short -v *> C:\Temp\zorivest\pytest-integration.txt; Get-Content C:\Temp\zorivest\pytest-integration.txt \| Select-Object -Last 30` | `[x]` |
| | **MEU-149: Tax MCP Tool Wiring** | | | | |
| 15 | Rewrite `tax-tool.ts` with 8 real actions — AC-149.1→149.7 | coder | `mcp-server/src/compound/tax-tool.ts` | `cd mcp-server && npx tsc --noEmit *> C:\Temp\zorivest\tsc-check.txt; Get-Content C:\Temp\zorivest\tsc-check.txt \| Select-Object -Last 20` | `[x]` |
| 16 | Update `seed.ts` and `client-detection.ts` descriptions — AC-149.8, AC-149.9 | coder | Metadata files updated | `rg -i "stub" mcp-server/src/compound/tax-tool.ts mcp-server/src/toolsets/seed.ts *> C:\Temp\zorivest\stub-check.txt; Get-Content C:\Temp\zorivest\stub-check.txt` (expect 0 matches) | `[x]` |
| 17 | Write Vitest tests for MCP tax actions — AC-149.10 | coder | `mcp-server/tests/tax-tool.test.ts` | `cd mcp-server && npx vitest run tests/tax-tool.test.ts *> C:\Temp\zorivest\vitest-tax.txt; Get-Content C:\Temp\zorivest\vitest-tax.txt \| Select-Object -Last 30` | `[x]` |
| | **Verification** | | | | |
| 18 | Run full regression suite | tester | All tests green | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt \| Select-Object -Last 40` | `[x]` |
| 19 | Run pyright type check | tester | 0 errors | `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30` | `[x]` |
| 20 | Run ruff lint | tester | 0 errors | `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` | `[x]` |
| 21 | Anti-placeholder scan | tester | 0 matches in touched files | `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/services/tax_service.py packages/api/src/zorivest_api/routes/tax.py *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt` (expect 0 matches) | `[x]` |
| | **🔄 Re-Anchor Gate** | | | | |
| 22 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\[ \]' docs/execution/plans/2026-05-14-tax-engine-wiring/task.md *> C:\Temp\zorivest\reanchor-1.txt; Get-Content C:\Temp\zorivest\reanchor-1.txt` | `[x]` |
| | **📋 Closeout Phase** | | | | |
| | ⚠️ *Closeout artifacts are institutional memory. Apply the same rigor as production code. Context fatigue at session end is the primary risk — these steps are the countermeasure.* | | | | |
| | **🔄 Re-Anchor Gate** | | | | |
| 23 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation/verification rows above are still `[ ]`, go back and complete them before proceeding to closeout. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\[ \]' docs/execution/plans/2026-05-14-tax-engine-wiring/task.md *> C:\Temp\zorivest\reanchor-2.txt; Get-Content C:\Temp\zorivest\reanchor-2.txt` | `[x]` |
| 24 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | Phase 3E status updated | `rg "tax-engine-wiring" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` | `[x]` |
| 25 | Run verification plan | tester | All checks pass | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-verify.txt; Get-Content C:\Temp\zorivest\pytest-verify.txt \| Select-Object -Last 40` then `uv run pyright packages/ *> C:\Temp\zorivest\pyright-verify.txt; Get-Content C:\Temp\zorivest\pyright-verify.txt \| Select-Object -Last 30` then `uv run ruff check packages/ *> C:\Temp\zorivest\ruff-verify.txt; Get-Content C:\Temp\zorivest\ruff-verify.txt \| Select-Object -Last 20` | `[x]` |
| 26 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-tax-engine-wiring-2026-05-14` | MCP: `pomera_notes(action="search", search_term="Zorivest-tax-engine*")` returns ≥1 result | `[x]` |
| | **Template + Exemplar Loading** (mandatory before writing closeout artifacts) | | | | |
| 27 | Load templates and exemplars: `view_file` BOTH the template AND the most recent peer exemplar for each artifact. Do NOT write from memory. | orchestrator | Console evidence of template + exemplar reads | `Test-Path docs/execution/reflections/TEMPLATE.md *> C:\Temp\zorivest\template-check.txt; Get-ChildItem .agent/context/handoffs/*-handoff.md \| Sort-Object LastWriteTime -Descending \| Select-Object -First 1 -ExpandProperty Name *>> C:\Temp\zorivest\template-check.txt; Get-ChildItem docs/execution/reflections/*-reflection.md \| Sort-Object LastWriteTime -Descending \| Select-Object -First 1 -ExpandProperty Name *>> C:\Temp\zorivest\template-check.txt; Get-Content C:\Temp\zorivest\template-check.txt` | `[x]` |
| 28 | Create handoff following template structure and exemplar quality | reviewer | `.agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md` | `rg "Acceptance Criteria\|AC-" .agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md *> C:\Temp\zorivest\handoff-markers.txt; rg "CACHE BOUNDARY" .agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md *>> C:\Temp\zorivest\handoff-markers.txt; rg "Evidence\|FAIL_TO_PASS" .agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md *>> C:\Temp\zorivest\handoff-markers.txt; rg "Changed Files" .agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md *>> C:\Temp\zorivest\handoff-markers.txt; Get-Content C:\Temp\zorivest\handoff-markers.txt` | `[x]` |
| 29 | Create reflection following template structure and exemplar quality | orchestrator | `docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md` | `rg "Friction Log\|Execution Trace" docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md *> C:\Temp\zorivest\reflection-markers.txt; rg "Pattern Extraction\|Patterns to KEEP" docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md *>> C:\Temp\zorivest\reflection-markers.txt; rg "Efficiency Metrics" docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md *>> C:\Temp\zorivest\reflection-markers.txt; rg "Instruction Coverage\|schema: v1" docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md *>> C:\Temp\zorivest\reflection-markers.txt; rg "sections:" docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md *>> C:\Temp\zorivest\reflection-markers.txt; Get-Content C:\Temp\zorivest\reflection-markers.txt` | `[x]` |
| 30 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md -Tail 3 *> C:\Temp\zorivest\metrics-tail.txt; Get-Content C:\Temp\zorivest\metrics-tail.txt` | `[x]` |
| | **Closeout Quality Gate** | | | | |
| 31 | Run closeout structural checks | tester | All structural markers present (0 missing) | `rg "Acceptance Criteria\|AC-" .agent/context/handoffs/2026-05-14-tax-engine-wiring-handoff.md *> C:\Temp\zorivest\closeout-gate.txt; rg "Friction Log\|Execution Trace" docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md *>> C:\Temp\zorivest\closeout-gate.txt; rg "sections:" docs/execution/reflections/2026-05-14-tax-engine-wiring-reflection.md *>> C:\Temp\zorivest\closeout-gate.txt; Get-Content C:\Temp\zorivest\closeout-gate.txt` (expect ≥3 marker hits) | `[x]` |

| | **Ad-Hoc: TAX-DBMIGRATION (Inline Schema Migration)** | | | | |
| 32 | Write failing migration regression test — creates old-shape `tax_lots` table, runs inline migrations, asserts 3 columns exist + idempotency + fresh-DB path (AC-MIG.6) | coder | `tests/integration/test_inline_migrations.py` | `uv run pytest tests/integration/test_inline_migrations.py -x --tb=short -v *> C:\Temp\zorivest\pytest-migration-red.txt; Get-Content C:\Temp\zorivest\pytest-migration-red.txt \| Select-Object -Last 30` (expect FAIL — Red phase) | `[x]` |
| 33 | Add 3 ALTER TABLE statements to `_inline_migrations` in main.py for `cost_basis_method`, `realized_gain_loss`, `acquisition_source` — AC-MIG.1 | coder | `main.py` updated | `rg "tax_lots ADD COLUMN" packages/api/src/zorivest_api/main.py *> C:\Temp\zorivest\migration-check.txt; Get-Content C:\Temp\zorivest\migration-check.txt` (expect 3 lines) | `[x]` |
| 34 | Re-run migration regression test — AC-MIG.1 Green phase | tester | All migration tests pass | `uv run pytest tests/integration/test_inline_migrations.py -x --tb=short -v *> C:\Temp\zorivest\pytest-migration-green.txt; Get-Content C:\Temp\zorivest\pytest-migration-green.txt \| Select-Object -Last 30` (expect PASS) | `[x]` |
| 35 | Restart backend, verify `lots` endpoint returns 200 — AC-MIG.2 | tester | REST 200 | `Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/lots?account_id=99bb9b00-fc7a-44cf-b816-a6bb4dabfaca" -Method GET *> C:\Temp\zorivest\mig-lots.txt; Get-Content C:\Temp\zorivest\mig-lots.txt \| Select-Object -Last 20` | `[x]` |
| 36 | Verify `estimate` endpoint returns 200 — AC-MIG.3 | tester | REST 200 | `Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/estimate" -Method POST -ContentType "application/json" -Body '{"tax_year":2026,"account_id":"99bb9b00-fc7a-44cf-b816-a6bb4dabfaca"}' *> C:\Temp\zorivest\mig-estimate.txt; Get-Content C:\Temp\zorivest\mig-estimate.txt \| Select-Object -Last 20` | `[x]` |
| 37 | Verify `simulate` endpoint returns 200 — AC-MIG.4 | tester | REST 200 | `Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/simulate" -Method POST -ContentType "application/json" -Body '{"ticker":"MSFT","action":"sell","quantity":50,"price":420,"account_id":"99bb9b00-fc7a-44cf-b816-a6bb4dabfaca"}' *> C:\Temp\zorivest\mig-simulate.txt; Get-Content C:\Temp\zorivest\mig-simulate.txt \| Select-Object -Last 20` | `[x]` |
| 38 | Verify `ytd_summary` endpoint returns 200 — AC-MIG.5 | tester | REST 200 | `Invoke-RestMethod -Uri "http://127.0.0.1:17787/api/v1/tax/ytd-summary?tax_year=2026" -Method GET *> C:\Temp\zorivest\mig-ytd.txt; Get-Content C:\Temp\zorivest\mig-ytd.txt \| Select-Object -Last 20` | `[x]` |
| 39 | Verify fresh-DB creates all columns via `create_all` — AC-MIG.6 | tester | Migration test assertion passes | `uv run pytest tests/integration/test_inline_migrations.py -k "fresh" -x --tb=short -v *> C:\Temp\zorivest\pytest-migration-fresh.txt; Get-Content C:\Temp\zorivest\pytest-migration-fresh.txt \| Select-Object -Last 20` | `[x]` |
| 40 | Verify idempotent startup (columns already exist) — AC-MIG.7 | tester | Migration test assertion passes | `uv run pytest tests/integration/test_inline_migrations.py -k "idempotent" -x --tb=short -v *> C:\Temp\zorivest\pytest-migration-idemp.txt; Get-Content C:\Temp\zorivest\pytest-migration-idemp.txt \| Select-Object -Last 20` | `[x]` |
| 41 | Run full pytest regression | tester | All tests green | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-migration.txt; Get-Content C:\Temp\zorivest\pytest-migration.txt \| Select-Object -Last 40` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
