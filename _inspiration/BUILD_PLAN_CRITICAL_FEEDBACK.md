# docs/build-plan Critical Feedback

Date: 2026-02-15
Scope: `docs/build-plan/*.md` (14 files)
Review style: defect-focused (contract conflicts, build-order breaks, implementation blockers)

## Critical Findings

1. Missing `POST /api/v1/trades` contract while downstream phases depend on it
Evidence:
- `docs/build-plan/04-rest-api.md:21` defines `/api/v1/trades` router, but only `GET /` and image routes are shown (`docs/build-plan/04-rest-api.md:23`, `docs/build-plan/04-rest-api.md:33`).
- MCP `create_trade` calls `POST /trades` (`docs/build-plan/05-mcp-server.md:37`).
- Integration example also calls `POST /trades` (`docs/build-plan/testing-strategy.md:75`).
Impact:
- Phase 5 and testing docs depend on an endpoint that is not defined in the Phase 4 spec; this blocks a clean implementation path.
Recommended fix:
- Add explicit trade create/update/delete route contracts in `04-rest-api.md` with request/response schemas and status codes.

2. Image ownership model is polymorphic, but `ImageRepository` is trade-only
Evidence:
- Domain reference defines polymorphic ownership (`trade`, `report`, `plan`) via `owner_type`/`owner_id` (`docs/build-plan/domain-model-reference.md:98`, `docs/build-plan/domain-model-reference.md:101`).
- Infrastructure schema uses polymorphic columns (`docs/build-plan/02-infrastructure.md:44`, `docs/build-plan/02-infrastructure.md:45`).
- Core port only supports `trade_id` methods (`docs/build-plan/01-domain-layer.md:362`, `docs/build-plan/01-domain-layer.md:364`).
Impact:
- P1/P2 report and plan image features cannot be expressed through current core port contract without breaking changes later.
Recommended fix:
- Change image port to owner-based APIs (e.g., `save(owner_type, owner_id, image)`, `get_for_owner(owner_type, owner_id)`) and keep a trade-specific convenience method only as adapter sugar.

## High Findings

1. Phase 8 is not integrated into the overview and install manifest
Evidence:
- Overview phase table ends at Phase 7 (`docs/build-plan/00-overview.md:38`).
- Overview still claims matrix has 58 items (`docs/build-plan/00-overview.md:54`) while matrix says 68 (`docs/build-plan/build-priority-matrix.md:3`).
- Dependency manifest has no Phase 8 section (`docs/build-plan/dependency-manifest.md:54`) despite Phase 8 requiring `cryptography` (`docs/build-plan/08-market-data.md:184`).
Impact:
- New market-data phase appears optional/undocumented in top-level flow; install steps are incomplete.
Recommended fix:
- Update `00-overview.md` and `dependency-manifest.md` to include Phase 8 and its dependencies explicitly.

2. Dependency inversion inside matrix (MCP before REST for tax module)
Evidence:
- Matrix schedules tax MCP registration at item 61 (`docs/build-plan/build-priority-matrix.md:129`) before tax REST endpoints at item 62 (`docs/build-plan/build-priority-matrix.md:130`).
- Elsewhere the rule is REST before MCP (`docs/build-plan/00-overview.md:23`, `docs/build-plan/05-mcp-server.md:11`).
Impact:
- Violates documented architecture dependency rule and causes plan sequencing confusion.
Recommended fix:
- Swap items 61 and 62 or explicitly document why tax MCP is exempt (if intentional).

3. Port location is contradictory (`application/ports.py` vs `domain/ports.py`)
Evidence:
- Phase 1 defines ports in application layer (`docs/build-plan/01-domain-layer.md:348`).
- Phase 8 appends market port to domain path (`docs/build-plan/08-market-data.md:142`).
Impact:
- Conflicting module targets create import churn and architecture drift.
Recommended fix:
- Pick one canonical ports module location and align all phases.

4. Request schema drift: `account` vs `account_id`
Evidence:
- MCP tool sends `account_id` (`docs/build-plan/05-mcp-server.md:34`).
- Testing example sends `account` (`docs/build-plan/testing-strategy.md:80`).
Impact:
- Copy-pasted examples will fail validation or silently drop account linkage.
Recommended fix:
- Standardize to `account_id` everywhere; add a compatibility note only if legacy payloads are supported.

5. Mutable default in Pydantic DTO (`tickers: list[str] = []`)
Evidence:
- `docs/build-plan/08-market-data.md:117`.
Impact:
- Shared mutable defaults can leak state across model instances.
Recommended fix:
- Use `Field(default_factory=list)`.

6. Distribution commands are inconsistent with artifact paths
Evidence:
- PyInstaller command in Phase 7 does not set `--distpath` (`docs/build-plan/07-distribution.md:17`).
- Electron config expects binary in `dist-python/...` (`docs/build-plan/07-distribution.md:30`).
Impact:
- Packaging flow fails unless undocumented manual path changes are applied.
Recommended fix:
- Align build command and `extraResources` path (or define explicit copy step in release pipeline).

## Medium Findings

1. `caption` is defined like a query param, but examples send it in multipart form
Evidence:
- Route signature uses `caption: str = ""` with `UploadFile` (`docs/build-plan/04-rest-api.md:34`, `docs/build-plan/04-rest-api.md:35`).
- E2E example sends caption via form `data` (`docs/build-plan/04-rest-api.md:94`).
Impact:
- Caption handling is ambiguous and can be dropped unintentionally.
Recommended fix:
- Specify `caption: str = Form("")` and include `File(...)`/`Form(...)` imports in the canonical route example.

2. GUI API base URL is hardcoded
Evidence:
- `const API = 'http://localhost:8765/api/v1';` (`docs/build-plan/06-gui.md:52`).
Impact:
- Breaks non-default ports and packaged runtime configuration.
Recommended fix:
- Route through Electron-configured environment value or preload-configured API base.

3. UI assumes image response fields not guaranteed by REST contract
Evidence:
- GUI expects `thumbnail_url`, `file_size`, etc. (`docs/build-plan/06-gui.md:54`, `docs/build-plan/06-gui.md:59`).
- REST image list route returns `service.get_trade_images(exec_id)` with no documented schema (`docs/build-plan/04-rest-api.md:31`).
Impact:
- Frontend-backend integration risk due undocumented response shape.
Recommended fix:
- Define a canonical `TradeImageResponse` schema in Phase 4 and reuse it in GUI/MCP examples.

## Suggested Remediation Order

1. Fix hard contract blockers (Critical findings 1-2).
2. Reconcile plan consistency (High findings 1-4).
3. Address implementation safety issues (High findings 5-6, Medium findings).
4. Re-run a full docs consistency pass after edits (endpoints, DTOs, module paths, and phase numbering).
