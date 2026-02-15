# BUILD_PLAN.md Critical Feedback and Recommendations

Reviewed file: `docs/BUILD_PLAN.md`  
Review style: defect-focused (bugs, contradictions, implementation risk)  
Date: 2026-02-14

## Recommended Design Selections (for your open items)

1. Image contract (`API` canonical choice)
- Use `multipart/form-data` as the canonical upload API.
- Canonical endpoint: `POST /api/v1/trades/{trade_id}/images` with fields:
  - `file` (binary, required)
  - `caption` (string, optional)
- Keep image retrieval as:
  - `GET /api/v1/trades/{trade_id}/images` (metadata list)
  - `GET /api/v1/images/{image_id}` (full image bytes)
  - `GET /api/v1/images/{image_id}/thumbnail?max_size=200`
  - `DELETE /api/v1/images/{image_id}`
- MCP tool should accept base64 input from clients, decode it in the MCP server, and forward as multipart to the REST API.  
Rationale: best fit for GUI/Electron uploads and clipboard blobs, avoids base64 overhead in API/storage path, and keeps FastAPI `UploadFile` usage simple.

2. API port
- Default port: `8765`.
- Make configurable via env:
  - `ZORIVEST_API_HOST` (default `127.0.0.1`)
  - `ZORIVEST_API_PORT` (default `8765`)
  - `ZORIVEST_API_BASE_URL` (derived if not set)
- Ensure UI, MCP, tests, and Electron launcher all read the same source of truth.

3. Test layout
- Standardize on `tests/...` (not `tests/python/...`), per your decision:
  - `tests/unit/`
  - `tests/integration/`
  - `tests/e2e/`
  - `tests/typescript/mcp/`
  - `tests/typescript/ui/`

## Findings (Severity-Ordered)

### Critical

1. Image API/tool/UI contracts conflict and will break integration.
- Evidence:
  - MCP sends JSON base64: `docs/BUILD_PLAN.md:1338`, `docs/BUILD_PLAN.md:1344`
  - API expects multipart `UploadFile`: `docs/BUILD_PLAN.md:1748`, `docs/BUILD_PLAN.md:1749`
  - GUI sends `FormData` field `image` (not `file`): `docs/BUILD_PLAN.md:2124`
  - Route usage mismatch: `docs/BUILD_PLAN.md:2148`, `docs/BUILD_PLAN.md:1779`
- Recommendation:
  - Adopt the canonical contract above and rewrite all examples to match exactly.

2. SQLAlchemy schema snippet is not runnable as written.
- Evidence:
  - Missing `Boolean` import while used: `docs/BUILD_PLAN.md:915`, `docs/BUILD_PLAN.md:961`
  - `back_populates` references missing counterpart relationships:
    - `ImageModel.trade`: `docs/BUILD_PLAN.md:934`
    - `TradeModel.account_rel`: `docs/BUILD_PLAN.md:965`
    - `TradeModel.report`: `docs/BUILD_PLAN.md:982`
- Recommendation:
  - Either provide complete paired relationships for every `back_populates`, or remove `back_populates` until fully modeled.
  - Keep snippets executable if they are presented as implementation templates.

3. Phase/build order contradicts itself.
- Evidence:
  - States REST (Phase 5) must be before MCP (Phase 4): `docs/BUILD_PLAN.md:40`
  - Actual section order is MCP then REST: `docs/BUILD_PLAN.md:1222`, `docs/BUILD_PLAN.md:1719`
  - Summary table lists MCP before API: `docs/BUILD_PLAN.md:2330`, `docs/BUILD_PLAN.md:2331`
- Recommendation:
  - Pick one ordering and make all sections/tables align.
  - Best fit for current architecture: implement API first, then MCP wrappers.

### High

4. Test structure is inconsistent in one document.
- Evidence:
  - Scaffold uses `tests/python/...`: `docs/BUILD_PLAN.md:145`
  - Execution commands and examples use `tests/unit`, `tests/integration`, `tests/e2e`: `docs/BUILD_PLAN.md:727`, `docs/BUILD_PLAN.md:902`
- Recommendation:
  - Replace all `tests/python/...` references with `tests/...`.

5. Core entity field names drift across sections.
- Evidence:
  - `Trade.account_id`: `docs/BUILD_PLAN.md:204`
  - `Trade.account`: `docs/BUILD_PLAN.md:851`, `docs/BUILD_PLAN.md:930`
  - Image ownership model is polymorphic (`owner_type`, `owner_id`): `docs/BUILD_PLAN.md:262`
  - Pipeline still refers to `trade_id`-style storage: `docs/BUILD_PLAN.md:2017`
- Recommendation:
  - Define canonical names once (domain + ORM + DTO + API schema) and enforce in all examples.
  - Suggested: keep `account_id` consistently and keep polymorphic image ownership everywhere.

6. MCP language approach is inconsistent in the same plan.
- Evidence:
  - Phase says TS MCP server: `docs/BUILD_PLAN.md:1222`
  - Later uses Python `@mcp.tool()` sample as if MCP is Python-native: `docs/BUILD_PLAN.md:2073`
- Recommendation:
  - Keep MCP examples in TypeScript only, or clearly label Python snippet as conceptual/non-target.

7. Several snippets are placeholders despite “exact build order” framing.
- Evidence:
  - Placeholder entity creation: `docs/BUILD_PLAN.md:858`
  - Placeholder test steps: `docs/BUILD_PLAN.md:1103`, `docs/BUILD_PLAN.md:1616`
- Recommendation:
  - Mark these as pseudocode explicitly, or replace with runnable examples.

### Medium

8. Numbering and TOC anchors are inconsistent.
- Evidence:
  - Duplicate heading number `## 8` for two different sections: `docs/BUILD_PLAN.md:1824`, `docs/BUILD_PLAN.md:1885`
  - TOC references section 12 for dependency order, but heading is 11: `docs/BUILD_PLAN.md:20`, `docs/BUILD_PLAN.md:2261`
- Recommendation:
  - Re-number headings and regenerate TOC links.

9. Image validation code does not enforce its own documented constraints.
- Evidence:
  - Pipeline states `<10MB` check: `docs/BUILD_PLAN.md:1995`
  - `validate_image` has no file-size check: `docs/BUILD_PLAN.md:2047`
  - WebP detection via `RIFF` only is ambiguous: `docs/BUILD_PLAN.md:2057`
- Recommendation:
  - Add explicit max-bytes validation and robust format verification (e.g., Pillow decode + strict MIME mapping).

10. Integration test startup strategy is flaky.
- Evidence:
  - Fixed `setTimeout(3000)` to wait for API: `docs/BUILD_PLAN.md:1676`
- Recommendation:
  - Poll a health endpoint with timeout/retry instead of static sleep.

11. API port is inconsistent with architecture doc.
- Evidence:
  - Build plan examples use `8765`: `docs/BUILD_PLAN.md:1244`, `docs/BUILD_PLAN.md:2100`
  - Architecture doc states `8000`: `.agent/docs/architecture.md:57`
- Recommendation:
  - Standardize on `8765` default and update architecture docs to match.

12. “Zero external dependencies” conflicts with Phase-1 DTO guidance.
- Evidence:
  - Phase goal says zero deps: `docs/BUILD_PLAN.md:50`
  - Summary says Commands/DTOs rely on Pydantic: `docs/BUILD_PLAN.md:2323`
- Recommendation:
  - Either defer Pydantic to API layer/Phase 5, or revise Phase-1 statement to “no runtime infra dependencies.”

## Recommended Rewrite Plan (Minimal, High-Impact)

1. Normalize contracts
- Finalize image API shapes and route set.
- Align MCP and GUI examples to the same routes and payloads.

2. Normalize model vocabulary
- Pick one naming set (`account_id`, polymorphic image ownership) and apply globally.

3. Fix structural inconsistencies
- Correct phase order narrative vs section order.
- Fix heading numbering and TOC anchors.
- Standardize test paths to `tests/...`.

4. Make snippets executable
- Remove placeholder ellipses in “implementation” snippets.
- Ensure imports/relationships compile as shown.

5. Add reliability guards
- Health-check startup in integration tests.
- Explicit image size/type validation behavior and error contracts.

## Acceptance Criteria for This Document’s Recommendations

- A new engineer can follow `BUILD_PLAN.md` without guessing payload formats, routes, or folder paths.
- All example code in “implementation” sections runs with only context-local imports.
- There is one canonical contract for image upload/display used by API, MCP, and UI.
- Phase order statements, section ordering, and summary tables all agree.
