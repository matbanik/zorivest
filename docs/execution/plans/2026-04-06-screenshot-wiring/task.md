---
project: "2026-04-06-screenshot-wiring"
source: "docs/execution/plans/2026-04-06-screenshot-wiring/implementation-plan.md"
meus: ["MEU-47a"]
status: "complete"
template_version: "2.0"
---

# Task — Screenshot Panel API Wiring

> **Project:** `2026-04-06-screenshot-wiring`
> **Type:** GUI + API
> **Estimate:** 4 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write FIC (Feature Intent Contract) with source-backed ACs | orchestrator | FIC doc with AC-1 through AC-13 | Plan approval from user | `[x]` |
| 2 | *(pre-existing)* RED+GREEN: `ImageService.delete_image()` + 2 unit tests | coder | `tests/unit/test_image_service.py` — `TestDeleteImage` (2 tests) + `image_service.py:96-107` | `uv run pytest tests/unit/test_image_service.py -x --tb=short -v *> C:\Temp\zorivest\pytest-img-svc.txt` — expect PASS (regression) | `[x]` |
| 3 | Write RED tests: `TestDeleteImage` route in `test_api_trades.py` (Python) | coder | `tests/unit/test_api_trades.py` — 2 new tests (204 success + 404 not found) in existing `TestGlobalImages` class | `uv run pytest tests/unit/test_api_trades.py -x --tb=short -v *> C:\Temp\zorivest\pytest-img-route.txt` — expect FAIL | `[x]` |
| 4 | Write RED tests: `ScreenshotPanel.test.tsx` (TypeScript) | coder | `ui/src/renderer/src/features/trades/__tests__/ScreenshotPanel.test.tsx` — tests for fetch, upload, delete, drag-and-drop, lightbox, loading/error states | `cd ui && npx vitest run src/renderer/src/features/trades/__tests__/ScreenshotPanel.test.tsx *> C:\Temp\zorivest\vitest-ss.txt` — expect FAIL | `[x]` |
| 5 | GREEN: Add `DELETE /api/v1/images/{image_id}` route | coder | `packages/api/src/zorivest_api/routes/images.py` | `uv run pytest tests/unit/test_api_trades.py::TestGlobalImages -x --tb=short -v *> C:\Temp\zorivest\pytest-img-route.txt` — expect PASS | `[x]` |
| 6 | GREEN: Wire ScreenshotPanel to REST API with React Query | coder | `ui/src/renderer/src/features/trades/ScreenshotPanel.tsx` — useQuery + useMutation for fetch/upload/delete, drag-and-drop, loading/error states | `cd ui && npx vitest run src/renderer/src/features/trades/__tests__/ScreenshotPanel.test.tsx *> C:\Temp\zorivest\vitest-ss.txt` — expect PASS | `[x]` |
| 7 | PASS_TO_PASS regression: backend image API suite | tester | All existing image tests still pass | `uv run pytest tests/unit/test_image_service.py tests/unit/test_api_trades.py -x --tb=short -v *> C:\Temp\zorivest\pytest-meu47a-regress.txt` — expect PASS | `[x]` |
| 8 | PASS_TO_PASS regression: frontend trades integration test | tester | Existing `trades.test.tsx` still passes | `cd ui && npx vitest run src/renderer/src/features/trades/__tests__/trades.test.tsx *> C:\Temp\zorivest\vitest-regress.txt` — expect PASS | `[x]` |
| 9 | Run MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-meu47a.txt; Get-Content C:\Temp\zorivest\validate-meu47a.txt \| Select-Object -Last 50` | `[x]` |
| 10 | Anti-placeholder scan | tester | Zero matches | `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/services/image_service.py packages/api/src/zorivest_api/routes/images.py ui/src/renderer/src/features/trades/ScreenshotPanel.tsx *> C:\Temp\zorivest\placeholder-meu47a.txt` | `[x]` |
| 11 | Update MEU-47a status → ✅ in BUILD_PLAN.md + meu-registry.md | orchestrator | Status updated to ✅ | `rg "MEU-47a" docs/BUILD_PLAN.md .agent/context/meu-registry.md *> C:\Temp\zorivest\meu47a-status.txt` | `[x]` |
| 12 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-screenshot-wiring-2026-04-06` | MCP: `pomera_notes(action="search", search_term="Zorivest-screenshot*")` returns ≥1 result | `[x]` |
| 13 | Create handoff | reviewer | `.agent/context/handoffs/104-2026-04-06-screenshot-wiring-bp06bs16.1.md` | `Test-Path .agent/context/handoffs/104-2026-04-06-screenshot-wiring-bp06bs16.1.md` | `[x]` |
| 14 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-06-screenshot-wiring-reflection.md` | `Test-Path docs/execution/reflections/2026-04-06-screenshot-wiring-reflection.md` | `[x]` |
| 15 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
