# Critical Review: `image-architecture.md` WebP Changes vs Build Plan

## Scope
- Reviewed updates in `docs/build-plan/image-architecture.md`.
- Checked alignment with impacted build-plan docs: `01-domain-layer.md`, `02-infrastructure.md`, `03-service-layer.md`, `04-rest-api.md`, `05-mcp-server.md`, `06b-gui-trades.md`, `input-index.md`, `testing-strategy.md`, `dependency-manifest.md`, `domain-model-reference.md`.

## Findings (Severity-Ordered)

### Critical
- Stored MIME contract is still ambiguous, which can produce content-type/data mismatch at runtime.
  Evidence:
  - Architecture now says DB stores standardized WebP bytes and `mime_type = image/webp` (`docs/build-plan/image-architecture.md:68`, `docs/build-plan/image-architecture.md:71`, `docs/build-plan/image-architecture.md:146`).
  - REST upload still forwards client MIME into command (`docs/build-plan/04-rest-api.md:113`).
  - MCP tool still accepts caller MIME and forwards it (`docs/build-plan/05-mcp-server.md:64`, `docs/build-plan/05-mcp-server.md:72`).
  - Full-image route responds using persisted `img.mime_type` (`docs/build-plan/04-rest-api.md:149`).
  Impact:
  - If conversion happens but persisted MIME is not forcibly normalized, clients may receive WebP bytes labeled `image/png`/other, breaking rendering and caching assumptions.
  Fix:
  - Make service-layer normalization explicit: after validation/conversion, persist `mime_type="image/webp"` unconditionally.
  - Treat incoming MIME as advisory only (`original_mime_type` for logs/audit), not storage metadata.

### High
- Test fixtures now encode an impossible state (PNG bytes labeled WebP), weakening the new invariant.
  Evidence:
  - `sample_image` returns PNG bytes with `mime_type="image/webp"` (`docs/build-plan/testing-strategy.md:150`, `docs/build-plan/testing-strategy.md:159`).
  - `make_image` default uses `b"\x89PNG_fake"` with `mime_type="image/webp"` (`docs/build-plan/testing-strategy.md:181`, `docs/build-plan/testing-strategy.md:182`).
  - Infrastructure test still asserts raw PNG round-trip (`docs/build-plan/02-infrastructure.md:257`, `docs/build-plan/02-infrastructure.md:262`).
  Impact:
  - Tests can pass while violating the stated storage contract ("all images standardized to WebP"), so regressions will slip through.
  Fix:
  - Split fixtures into `raw_input_image_*` (pre-standardization) and `stored_image_webp_*` (post-standardization).
  - Add explicit assertions for RIFF/WebP magic in stored `data` and thumbnail responses.

- New image-processing contract depends on Pillow features without a version floor in dependency docs.
  Evidence:
  - Architecture references Pillow AVIF capability and uses `has_transparency_data` (`docs/build-plan/image-architecture.md:90`, `docs/build-plan/image-architecture.md:117`).
  - Dependency manifest still uses unpinned `pillow` (`docs/build-plan/dependency-manifest.md:19`, `docs/build-plan/dependency-manifest.md:71`).
  Impact:
  - Older Pillow builds can silently diverge in format support/behavior across environments.
  Fix:
  - Add minimum version requirement in docs and lockfiles (example: `pillow>=11.2` if that is the intended floor).

### Medium
- Pipeline prose under-specifies accepted formats compared to validator logic.
  Evidence:
  - Pipeline text says magic-byte check for "PNG/JPG" (`docs/build-plan/image-architecture.md:40`), but validator allows PNG/JPEG/GIF/WebP (`docs/build-plan/image-architecture.md:153`, `docs/build-plan/image-architecture.md:171`).
  Impact:
  - Implementers may drop GIF/WebP support unintentionally when following the pipeline diagram.
  Fix:
  - Align diagram text with validator support list.

- Domain model reference does not reflect the new storage invariant.
  Evidence:
  - Model table still describes `data` as generic "raw image" (`docs/build-plan/domain-model-reference.md:103`), while architecture now mandates standardized WebP storage (`docs/build-plan/image-architecture.md:82`).
  Impact:
  - Cross-doc drift during implementation and review.
  Fix:
  - Update model reference to state that stored `ImageAttachment.data` is canonical WebP payload.

## Positive Alignment
- Thumbnail route now returns `image/webp` (`docs/build-plan/04-rest-api.md:141`, `docs/build-plan/04-rest-api.md:175`).
- MCP default MIME and input index were updated to WebP-oriented defaults (`docs/build-plan/05-mcp-server.md:64`, `docs/build-plan/input-index.md:78`, `docs/build-plan/input-index.md:89`).
- Domain/infrastructure examples now mostly trend toward WebP defaults (`docs/build-plan/01-domain-layer.md:341`, `docs/build-plan/02-infrastructure.md:48`).

## Recommended Remediation Order
1. Resolve the critical MIME source-of-truth contract in service/API/MCP docs.
2. Repair fixtures/tests to enforce pre-vs-post standardization states.
3. Pin/document Pillow minimum version.
4. Clean remaining prose/model-reference drift.

## Verdict
- Direction is correct, but the current docs are not yet fully self-consistent around ingestion invariants.
- Implementation should not proceed until the critical contract ambiguity is removed.
