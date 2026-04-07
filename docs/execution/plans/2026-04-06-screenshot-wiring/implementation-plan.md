---
project: "2026-04-06-screenshot-wiring"
date: "2026-04-06"
source: "docs/build-plan/06b-gui-trades.md §Screenshot Panel"
meus: ["MEU-47a"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Screenshot Panel API Wiring

> **Project**: `2026-04-06-screenshot-wiring`
> **Build Plan Section(s)**: [06b §Screenshot Panel](../../build-plan/06b-gui-trades.md)
> **Status**: `draft`

---

## Goal

Wire the existing presentational `ScreenshotPanel.tsx` component to the backend image REST API. The backend pipeline is complete (image processing, service, repository, REST routes for upload/list/get), and the MCP tools are functional. The GUI component currently renders UI elements (upload button, thumbnail grid, lightbox) but has zero API integration — it receives props but no real data flows through.

This MEU bridges the last gap: React Query hooks for CRUD operations, a `DELETE` API route, and full upload support (file picker, drag-and-drop, clipboard paste).

> [!NOTE]
> **Baseline note**: `ImageService.delete_image()` and its two unit tests (`test_image_service.py:96-123`) were implemented in an earlier session pass. This plan treats them as pre-existing and adds the remaining DELETE route + frontend wiring.

---

## User Review Required

> [!IMPORTANT]
> **New DELETE endpoint**: This adds `DELETE /api/v1/images/{image_id}` to the REST API — a new write path. The port protocol (`ImageRepository.delete`), repository implementation, and service method (`ImageService.delete_image()`) already exist; only the API route is missing.

> [!IMPORTANT]
> **`apiFetch` limitation**: The existing `apiFetch()` wrapper always sets `Content-Type: application/json`. For `FormData` uploads, the upload mutation must override this header to `undefined` so that `fetch()` auto-generates the multipart boundary. This is a per-call override, not a library change.

---

## Proposed Changes

### Backend: ImageService + DELETE Route

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `DELETE /api/v1/images/{image_id}` path param | FastAPI path typing (`int`) | `image_id > 0` (enforced by path type) | N/A (path param only) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `ImageService.delete_image(image_id)` deletes image via `uow.images.delete()` with commit | Spec: [image-architecture.md](../../build-plan/image-architecture.md) lifecycle | Non-existent ID raises `NotFoundError` | *(pre-existing — implemented in earlier session)* |
| AC-2 | `DELETE /api/v1/images/{image_id}` returns 204 on success | Local Canon: FastAPI delete convention (trades.py L118) | 404 for non-existent image |
| AC-3 | DELETE route requires `require_unlocked_db` dependency | Local Canon: all image routes pattern (images.py L32,42,58) | Locked DB returns 403 |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Delete cascading (foreign keys) | Local Canon | SQLAlchemy cascade on `ImageModel` handles child cleanup — no explicit cascade code needed |
| Delete auth (who can delete) | Spec | Per image-architecture.md, any unlocked user can delete any image (single-user app) |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/services/image_service.py` | *(pre-existing)* | `delete_image(image_id: int) -> None` already implemented |
| `packages/api/src/zorivest_api/routes/images.py` | modify | Add `DELETE /{image_id}` route returning 204 |

---

### Frontend: ScreenshotPanel API Wiring

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `POST /trades/{exec_id}/images` (upload) | `FormData` | `file`: image/*, max 10MB (enforced server-side) | N/A |
| `GET /trades/{exec_id}/images` (list) | API response JSON | `id: number`, `caption: string`, `mime_type: string` | N/A |
| `DELETE /images/{id}` | Path param | `id: number` | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-4 | `useQuery` fetches trade images via `GET /trades/{exec_id}/images` | Spec: 06b §Screenshot Panel L231-234 | Empty array when trade has no images |
| AC-5 | Thumbnails render via `GET /images/{id}/thumbnail` URL | Spec: 06b §Screenshot Panel L264 | Broken image placeholder on 404 |
| AC-6 | `useMutation` uploads via `POST /trades/{exec_id}/images` with `FormData` | Spec: 06b §Screenshot Panel L237-246 | 422 on invalid file type |
| AC-7 | Upload success invalidates `['trade-images', tradeId]` query cache | Spec: 06b L245 | N/A (always invalidate) |
| AC-8 | Delete button on each thumbnail calls `DELETE /images/{id}` and invalidates cache | Spec: 06b §Screenshot Panel (implied by thumbnail grid layout) | 404 on already-deleted image (handled gracefully) |
| AC-9 | Lightbox opens on thumbnail click via `GET /images/{id}/full` | Spec: 06b L276-280 | Click backdrop closes lightbox |
| AC-10 | Loading state shows skeleton/spinner during fetch | Local Canon: G15 pattern from TradeReportForm L280-286 | N/A |
| AC-11 | Error state shows error message with retry capability | Local Canon: G15 pattern from TradeReportForm L288-293 | API unreachable → error shown |
| AC-12 | Clipboard paste (Ctrl+V) triggers upload mutation via `ClipboardEvent.clipboardData.files` | Spec: 06b L248-256 | Non-image paste ignored |
| AC-13 | Drag-and-drop upload triggers upload mutation via `onDrop` handler | Spec: 06b L206,236 + gui-actions-index 3.3 | Non-image drop ignored |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Screenshot Panel uses `apiFetch` or raw `fetch` | Local Canon | Use `apiFetch` for JSON endpoints (list, delete); raw `fetch` with FormData for upload (Content-Type override) |
| Thumbnail size in grid | Spec | 06b shows `w-20 h-20` (80px × 80px) — matches existing shell |
| Image refetch interval | Research-backed | No auto-refetch needed — images change only on explicit user action (upload/delete) |
| Delete confirmation dialog | Local Canon | No confirmation — instant delete per project's minimal-friction pattern |
| Clipboard API choice | Research-backed | `ClipboardEvent.clipboardData.files` is the web-standard approach that works in Electron renderers without IPC; `clipboard.readImage()` requires Electron IPC channel not yet wired (deferred per MEU-47 scope) |
| Drag-and-drop upload | Spec | Required by 06b L206 and gui-actions-index 3.3 — `onDragOver` + `onDrop` handlers on the panel container |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/trades/ScreenshotPanel.tsx` | modify | Replace prop-based shell with self-contained React Query component (useQuery + useMutation for upload/delete/drag-and-drop) |

---

## Out of Scope

- **Electron `clipboard.readImage()` IPC** — Spec: 06b L207 calls for Electron clipboard API, but the IPC channel (`window.electronAPI.clipboard`) is not yet wired (MEU-47 did not scaffold it). AC-12 delivers equivalent functionality via the web-standard `ClipboardEvent.clipboardData.files` API, which works in Electron renderers without IPC. Source: [MDN ClipboardEvent](https://developer.mozilla.org/en-US/docs/Web/API/ClipboardEvent), Electron renderer process runs Chromium. Follow-up: IPC-based `readImage()` can be added when the Electron preload bridge is extended.
- **Image editing/cropping** — not in 06b spec
- **MCP screenshot tools** — already complete and tested (MEU-31)
- **Backend image processing changes** — pipeline is complete (MEU-22)

---

## BUILD_PLAN.md Audit

This project adds MEU-47a to the Phase 6 GUI section. Already applied:

```powershell
rg "MEU-47a" docs/BUILD_PLAN.md  # Expected: 1 match (the new row)
rg "MEU-47a" .agent/context/meu-registry.md  # Expected: 1 match
rg "16.1" docs/build-plan/build-priority-matrix.md  # Expected: 1 match
```

---

## Verification Plan

### 1. Python Unit Tests (Backend — new DELETE route + regression)
```powershell
uv run pytest tests/unit/test_image_service.py tests/unit/test_api_trades.py -x --tb=short -v *> C:\Temp\zorivest\pytest-meu47a.txt; Get-Content C:\Temp\zorivest\pytest-meu47a.txt | Select-Object -Last 40
```

### 2. TypeScript Component Tests (Frontend — new + regression)
```powershell
cd ui && npx vitest run src/renderer/src/features/trades/__tests__/ScreenshotPanel.test.tsx src/renderer/src/features/trades/__tests__/trades.test.tsx *> C:\Temp\zorivest\vitest-meu47a.txt; Get-Content C:\Temp\zorivest\vitest-meu47a.txt | Select-Object -Last 40
```

### 3. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-meu47a.txt; Get-Content C:\Temp\zorivest\validate-meu47a.txt | Select-Object -Last 50
```

### 4. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/services/image_service.py packages/api/src/zorivest_api/routes/images.py ui/src/renderer/src/features/trades/ScreenshotPanel.tsx *> C:\Temp\zorivest\placeholder-meu47a.txt; Get-Content C:\Temp\zorivest\placeholder-meu47a.txt
```

---

## Open Questions

> [!WARNING]
> **Delete confirmation UX**: The current design has no delete confirmation dialog — clicking the delete button immediately removes the image. This follows the project's minimal-friction pattern but could lead to accidental deletions. Should we add a confirmation modal?

---

## Research References

- [06b-gui-trades.md §Screenshot Panel](../../build-plan/06b-gui-trades.md) — reference implementation code
- [image-architecture.md](../../build-plan/image-architecture.md) — BLOB storage, processing pipeline
- [TradeReportForm.tsx](../../../../ui/src/renderer/src/features/trades/TradeReportForm.tsx) — React Query pattern reference
