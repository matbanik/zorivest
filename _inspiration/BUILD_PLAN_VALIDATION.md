# BUILD_PLAN Split Validation

Date: 2026-02-14  
Scope: `docs/build-plan/*.md` validated against `docs/BUILD_PLAN.md` (hub) and cross-file contracts.

## Verdict

- **Structural split integrity:** PASS
- **"Nothing lost" semantic integrity:** FAIL (critical contract drift remains)

The split is structurally complete, but there are cross-file behavioral mismatches that make the split set non-equivalent as an implementation guide.

## Validation Method

1. Ran structural validator: `python tools/validate_build_plan.py` (with `PYTHONUTF8=1` in this environment).
2. Verified hub-to-split coverage (13 links in hub, 13 files on disk, no missing/orphan files).
3. Performed manual semantic review across phase docs and reference docs for API/MCP/GUI contract consistency, naming consistency, and build-order consistency.
4. Compared against prior monolithic-review concerns (where source history was available via notes).

## What Was Preserved

- All expected split files exist and are linked from hub:
  - `docs/BUILD_PLAN.md`
  - `docs/build-plan/00-overview.md`
  - `docs/build-plan/01-domain-layer.md`
  - `docs/build-plan/02-infrastructure.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/05-mcp-server.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/07-distribution.md`
  - `docs/build-plan/domain-model-reference.md`
  - `docs/build-plan/testing-strategy.md`
  - `docs/build-plan/image-architecture.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/build-priority-matrix.md`
- Dependency narrative is preserved in hub + overview:
  - `docs/BUILD_PLAN.md:26`
  - `docs/BUILD_PLAN.md:27`
  - `docs/build-plan/00-overview.md:24`
- Rich domain/tax reference content is present in `docs/build-plan/domain-model-reference.md`.

## Findings

### Critical

1. Image API contract is inconsistent across REST, MCP, and GUI docs.
- Evidence:
  - REST router is namespaced under trades: `docs/build-plan/04-rest-api.md:19`
  - Thumbnail route declared under trade router: `docs/build-plan/04-rest-api.md:31`
  - E2E test calls global image route: `docs/build-plan/04-rest-api.md:71`
  - MCP expects global image metadata/full routes: `docs/build-plan/05-mcp-server.md:156`, `docs/build-plan/05-mcp-server.md:163`
  - GUI expects global image thumbnail/full routes: `docs/build-plan/06-gui.md:100`, `docs/build-plan/06-gui.md:114`
- Impact: Following docs as written yields non-matching endpoints and integration breakage.

2. Request schema drift: `account` vs `account_id`.
- Evidence:
  - MCP tool schema/payload uses `account`: `docs/build-plan/05-mcp-server.md:34`, `docs/build-plan/05-mcp-server.md:40`
  - Domain/service/test docs use `account_id`: `docs/build-plan/01-domain-layer.md:319`, `docs/build-plan/03-service-layer.md:31`, `docs/build-plan/testing-strategy.md:132`, `docs/build-plan/domain-model-reference.md:42`
- Impact: Tool payloads and backend contracts diverge.

### High

3. Build-order contradiction remains in priority matrix.
- Evidence:
  - Build-order rule says REST before MCP: `docs/build-plan/00-overview.md:24`, `docs/BUILD_PLAN.md:26`, `docs/BUILD_PLAN.md:27`
  - Priority matrix places MCP before FastAPI routes: `docs/build-plan/build-priority-matrix.md:25`, `docs/build-plan/build-priority-matrix.md:26`
- Impact: Sequence ambiguity for implementation planning.

4. Some split snippets are no longer runnable as written (possible truncation/degradation during split).
- Evidence:
  - Undefined variables in infra test snippet (`image_id`, `original_data` context missing): `docs/build-plan/02-infrastructure.md:222`, `docs/build-plan/02-infrastructure.md:224`
  - `TestImageService` uses `self.uow`/`self.service` but no setup in class block: `docs/build-plan/03-service-layer.md:49`, `docs/build-plan/03-service-layer.md:51`
  - REST snippet uses `UploadFile` and `AttachImageCommand` but imports don't include them: `docs/build-plan/04-rest-api.md:16`, `docs/build-plan/04-rest-api.md:39`, `docs/build-plan/04-rest-api.md:43`
- Impact: Docs cannot be followed verbatim without guesswork.

### Medium

5. Validation command in hub is brittle on default Windows code page.
- Evidence:
  - Hub instructs direct run: `docs/BUILD_PLAN.md:82`
  - Validator prints emoji characters that trigger cp1252 encode failure in this environment: `tools/validate_build_plan.py:378`, `tools/validate_build_plan.py:443`
- Impact: "Run validator" may fail for Windows users unless UTF-8 mode is enabled.

## Conclusion

The split is complete at a file/link structure level, but it is **not accurate to claim "nothing was lost"** yet. Critical contract mismatches and snippet degradation indicate semantic drift from a single-source implementation spec.

## Recommended Next Fixes

1. Normalize image endpoints and payload contracts across `04-rest-api.md`, `05-mcp-server.md`, and `06-gui.md`.
2. Standardize on `account_id` across MCP/tool payloads and examples.
3. Reorder or renumber matrix items 12/13 to align with REST-before-MCP dependency rule.
4. Repair non-runnable snippets (missing setup/imports/variables).
5. Make validator output ASCII-only (or explicitly require UTF-8 mode in docs).

## Limitation

A byte-for-byte comparison to the pre-split monolithic `docs/BUILD_PLAN.md` could not be executed in this workspace because that historical file version is not present and git history is unavailable here. This validation is therefore structural + semantic, not literal text diff.
