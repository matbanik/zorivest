---
project: "2026-04-11-boundary-validation-phase2"
source: "docs/execution/plans/2026-04-11-boundary-validation-phase2/implementation-plan.md"
meus: ["MEU-BV6", "MEU-BV7", "MEU-BV8"]
status: "complete"
template_version: "2.0"
---

# Task — Boundary Validation Phase 2

> **Project:** `2026-04-11-boundary-validation-phase2`
> **Type:** API
> **Estimate:** 6 files changed (3 route files + 3 test files)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write BV6 negative tests (scheduling) | coder | `tests/unit/test_api_scheduling.py` — 6 BV test methods | `uv run pytest tests/unit/test_api_scheduling.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv6-red.txt` — all FAIL | `[x]` |
| 2 | Harden scheduling schemas | coder | `scheduling.py` — `extra="forbid"`, `Query(min_length=1)` on PATCH params, `policy_json` non-empty validator | `uv run pytest tests/unit/test_api_scheduling.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv6-green.txt` — all PASS | `[x]` |
| 3 | Write BV7 negative tests (watchlists) | coder | `tests/unit/test_api_watchlists.py` — 7 BV test methods | `uv run pytest tests/unit/test_api_watchlists.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv7-red.txt` — all FAIL | `[x]` |
| 4 | Harden watchlist schemas | coder | `watchlists.py` — `StrippedStr`, `Field(min_length=1)`, `extra="forbid"` on 3 models | `uv run pytest tests/unit/test_api_watchlists.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv7-green.txt` — all PASS | `[x]` |
| 5 | Write BV8 negative tests (settings) | coder | `tests/unit/test_api_settings.py` — 3 BV test methods | `uv run pytest tests/unit/test_api_settings.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv8-red.txt` — all FAIL | `[x]` |
| 6 | Harden settings schemas | coder | `settings.py` — empty-body guard on bulk PUT, `UpdateSettingRequest` model with `extra="forbid"` for single-key PUT | `uv run pytest tests/unit/test_api_settings.py -k "Boundary" -x --tb=short -v *> C:\Temp\zorivest\bv8-green.txt` — all PASS | `[x]` |
| 7 | Full regression + lint | tester | All existing + new tests pass, ruff clean | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt` | `[x]` |
| 8 | Regenerate OpenAPI spec | coder | `openapi.committed.json` updated | `uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi.txt` | `[x]` |
| 9 | Update `known-issues.md` | orchestrator | F4, F7, Settings marked ✅ resolved | `rg "⬜" .agent/context/known-issues.md` (expect 0 BOUNDARY-GAP matches) | `[x]` |
| 10 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; evidence of clean grep | `rg "boundary-validation-phase2" docs/BUILD_PLAN.md` (expect 0 matches) | `[x]` |
| 11 | Run MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt` | `[x]` |
| 12 | Update MEU registry | orchestrator | MEU-BV6/BV7/BV8 rows added to `.agent/context/meu-registry.md` | `rg "MEU-BV[678]" .agent/context/meu-registry.md` returns 3 rows | `[x]` |
| 13 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-boundary-validation-phase2-2026-04-11` | MCP: `pomera_notes(action="search", search_term="Zorivest-boundary*")` returns ≥1 result | `[x]` |
| 14 | Create handoffs | reviewer | `.agent/context/handoffs/107-2026-04-11-boundary-validation-phase2.md` (consolidated) | `Test-Path .agent/context/handoffs/107-*` | `[x]` |
| 15 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-11-boundary-validation-phase2-reflection.md` | `Test-Path docs/execution/reflections/2026-04-11-boundary-validation-phase2-reflection.md` | `[x]` |
| 16 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
