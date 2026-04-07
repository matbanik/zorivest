---
meu: MEU-47a
slug: screenshot-wiring
matrix_item: "16.1"
build_plan_section: "06b §Screenshot"
status: complete
date: 2026-04-07
template_version: "2.0"
---

# Handoff — MEU-47a: Screenshot Panel API Wiring + Image Pipeline Fix

> **Project:** `2026-04-06-screenshot-wiring`
> **Section:** [06b §Screenshot](../../../docs/build-plan/06b-gui-trades.md)
> **Matrix Item:** 16.1

## Summary

Wired the `ScreenshotPanel` component from a presentational shell to a fully functional, React Query-driven interface supporting fetch, upload, delete, drag-and-drop, clipboard paste, and lightbox preview. Subsequently resolved a **silent image loading failure** caused by a missing CSP `img-src` directive and missing server-side thumbnail generation. Validated the full stack end-to-end with Playwright E2E tests.

## Changed Files

| File | Change |
|------|--------|
| `packages/core/src/zorivest_core/application/commands.py` | Added optional `thumbnail: bytes \| None` field to `AttachImage` command |
| `packages/core/src/zorivest_core/services/image_service.py` | Added `delete_image()` method; pass thumbnail from command to entity |
| `packages/api/src/zorivest_api/routes/images.py` | Added `DELETE /api/v1/images/{image_id}` route (204/404) |
| `packages/api/src/zorivest_api/routes/trades.py` | Upload route: validate image, convert to WebP, generate 200×200 thumbnail |
| `ui/src/renderer/index.html` | **CSP fix:** Added `img-src 'self' http://localhost:* http://127.0.0.1:* data:` |
| `ui/src/renderer/src/lib/api.ts` | `apiFetch`: detect `FormData` and omit `Content-Type` header |
| `ui/src/renderer/src/features/trades/ScreenshotPanel.tsx` | Full rewrite: useQuery + useMutation, drag-and-drop, clipboard paste, lightbox, loading/error states |
| `ui/src/renderer/src/features/trades/__tests__/ScreenshotPanel.test.tsx` | New: 16 unit tests covering AC-4 through AC-13 |
| `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx` | Updated 3 existing tests (added apiFetch mock + async waitFor) |
| `ui/tests/e2e/test-ids.ts` | Added `SCREENSHOTS` test ID constants (PANEL, THUMBNAIL, LIGHTBOX, etc.) |
| `ui/tests/e2e/screenshot-panel.test.ts` | **New:** 2 Playwright E2E tests for CSP verification + lightbox |
| `docs/BUILD_PLAN.md` | MEU-47a → ✅ |
| `.agent/context/meu-registry.md` | MEU-47a → ✅ 2026-04-07 |

## Root Cause Analysis: Silent Image Loading Failure

Three cascading issues prevented images from rendering in the Electron GUI:

| # | Issue | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | Images blocked by CSP | `default-src 'self'` blocked `<img src="http://127.0.0.1:...">` — no `img-src` directive | Added `img-src 'self' http://localhost:* http://127.0.0.1:* data:` to CSP |
| 2 | No thumbnails stored | Upload route missing `generate_thumbnail()` — raw bytes stored as thumbnail | Added Pillow-based WebP conversion + 200×200 thumbnail generation |
| 3 | FormData rejected | `apiFetch` always set `Content-Type: application/json`, corrupting multipart boundary | `FormData` instance detection to omit header |

## Evidence Bundle

### Backend Tests (Python)
```
uv run pytest tests/unit/test_image_service.py tests/unit/test_api_trades.py -x --tb=short -v
→ 36 passed, 1 warning
```

### Frontend Tests (TypeScript)
```
npx vitest run src/renderer/src/features/trades/__tests__/ScreenshotPanel.test.tsx
→ 16 passed (AC-4 through AC-13)

npx vitest run src/renderer/src/features/trades/__tests__/trades.test.tsx
→ 53 passed (regression GREEN)
```

### E2E Tests (Playwright + Electron)
```
npx playwright test tests/e2e/screenshot-panel.test.ts --reporter=line
→ 2 passed (4.7s)
  ✅ thumbnail image loads in ScreenshotPanel (CSP img-src)
  ✅ lightbox loads full image on thumbnail click
```

### MCP Image Retrieval
```
zorivest.get_screenshot(image_id=3)
→ success: true
→ 2974×1936, 144KB, image/webp — rendered inline in agent chat
```

### MEU Gate
```
uv run python tools/validate_codebase.py --scope meu
→ [1/8] Python Type Check (pyright): PASS
→ [2/8] Python Lint (ruff): PASS
→ [3/8] Python Unit Tests (pytest): PASS
→ [4/8] TypeScript Type Check (tsc): PASS
→ [5/8] TypeScript Lint (eslint): PASS
→ All blocking checks passed!
```

### Anti-Placeholder Scan
```
rg "TODO|FIXME|NotImplementedError" <changed files>
→ Zero matches
```

## Codex Review Metrics

| Metric | Value |
|--------|-------|
| **Total changed files** | 12 |
| **Lines added (approx)** | ~380 |
| **Unit tests written** | 16 new + 3 updated |
| **E2E tests written** | 2 |
| **Root causes fixed** | 3 (CSP, thumbnail, FormData) |
| **Review passes** | 1 (plan review) + 1 (corrections review) |
| **Blocking findings resolved** | 5/5 from plan critical review |
| **Regressions** | 0 |
| **Placeholders remaining** | 0 |

## Known Limitations

### jsdom DragEvent (AC-13)

jsdom `DragEvent` does not support `dataTransfer` in the constructor init ([jsdom/jsdom#2913](https://github.com/jsdom/jsdom/issues/2913)). AC-13 drag-and-drop tests verify handler attachment structurally. The upload function path is covered end-to-end by:
- **AC-6**: File input upload via `fireEvent.change`
- **AC-12**: Clipboard paste upload via `fireEvent.paste`

### E2E `seedTrade` requires `time` field

Boundary validation hardening (MEU-BV2) made the `time` field mandatory. E2E seeders must include `time: new Date().toISOString()`.

## Design Decisions

1. **CSP least-privilege**: Only the local API origin gets `img-src` access — no blanket `*` or `unsafe-inline`.
2. **WebP normalization**: All image storage standardized to `image/webp` at the API boundary for consistency.
3. **E2E via Node fetch**: Test data is seeded via Node's native `fetch()` rather than Playwright's `page.request`, which routes through Electron's own network stack and can hit CSP constraints.
4. **Content-Type override for FormData**: Set undefined to let browser set `multipart/form-data` boundary automatically.
5. **Cache invalidation**: Both upload and delete mutations invalidate `['trade-images', tradeId]` query key.
