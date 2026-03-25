# Task Handoff — MEU-90d `rendering-deps`

## Task

- **Date:** 2026-03-22
- **Task slug:** `rendering-deps`
- **MEU:** MEU-90d (matrix 49.3)
- **Build plan ref:** `docs/build-plan/09-scheduling.md §9.7d`
- **Owner role:** Coder / Tester
- **Handoff SEQ:** 083

## Inputs

- Plan: `docs/execution/plans/2026-03-21-sqlcipher-rendering-deps/implementation-plan.md`
- Task: `docs/execution/plans/2026-03-21-sqlcipher-rendering-deps/task.md`
- Specs: `packages/infrastructure/pyproject.toml` [rendering] extra, `tests/unit/test_store_render_step.py`

## Scope

Install `zorivest-infra[rendering]` (`playwright>=1.50`, `kaleido>=1.0`) and download
Chromium browser binary. Clear 1 previously-skipped RenderStep test (AC-SR12) and prove
kaleido PNG branch in AC-SR11 is now exercised. **Zero application code changes.**

## Coder Output

### Changed Files

- None (install-only MEU)

### Packages Installed

| Package | Version | Mechanism |
|---------|---------|-----------|
| `playwright` | 1.58.0 | `uv pip install "packages/infrastructure[rendering]"` |
| `kaleido` | 1.2.0 | `uv pip install "packages/infrastructure[rendering]"` |
| Chromium browser | (current) | `uv run playwright install chromium` |

### Commands run

```powershell
# Pre-install (Red phase confirmation)
uv run pytest tests/unit/test_store_render_step.py::test_AC_SR12_render_pdf_creates_directory --tb=no -q
# → 1 skipped, 1 warning in 0.13s  ✅ confirmed skip

# Repair corrupt orjson dist-info first
uv pip install orjson --reinstall
# → orjson==3.11.7 reinstalled

# Install rendering extra
uv pip install "packages/infrastructure[rendering]"
# → playwright==1.58.0, kaleido==1.2.0 + deps installed

# Download Chromium
uv run playwright install chromium
# → exit 0 (binary cached in AppData)

# Verify imports (AC-90d.2)
uv run python -c "import playwright; import kaleido; print('playwright OK'); print('kaleido OK')"
# → playwright OK / kaleido OK

# Green phase — AC-SR12
uv run pytest tests/unit/test_store_render_step.py::test_AC_SR12_render_pdf_creates_directory --tb=short -q
# → 1 passed, 1 warning in 1.25s  ✅

# Green phase — AC-SR11 kaleido PNG branch
uv run pytest tests/unit/test_store_render_step.py::test_AC_SR11_render_candlestick_keys --tb=short -q
# → 1 passed, 1 warning in 1.23s  ✅

# Full store/render suite (24 tests)
uv run pytest tests/unit/test_store_render_step.py --tb=short -q
# → 24 passed, 1 warning in 2.58s  ✅

# Full regression
uv run pytest tests/ --tb=short -q
# → 6 failed, 1591 passed, 15 skipped, 3 warnings in 39.54s

# MEU gate
uv run python tools/validate_codebase.py --scope meu
# → All blocking checks passed! (21.55s)  ✅
```

## Tester Output

### FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_AC_SR12_render_pdf_creates_directory` | 1 skipped | 1 PASSED ✅ |
| `test_AC_SR11_render_candlestick_keys` (kaleido PNG branch) | conditional branch inactive (empty `png_data_uri`) | branch exercised, `png_data_uri` non-empty ✅ |

### Pass/fail matrix

| Suite | Count |
|-------|-------|
| `tests/unit/test_store_render_step.py` | 24 passed |
| Full suite | 1591 passed |

### Pre-existing Failures (not caused by this MEU)

Full regression result: **6 failed, 1591 passed, 15 skipped** — 0 new failures introduced by the rendering install. The 6 failures are pre-existing, splitting across two unrelated areas:

| Failures | Count | Root Cause | Scope |
|----------|-------|------------|-------|
| `tests/unit/test_provider_registry.py` | 5 | Provider count mismatch: registry has 14 providers (incl. `Yahoo Finance`, `TradingView`); tests assert 12 names. Providers added after tests were written. | MEU-65 or a future provider-registry MEU |
| `tests/unit/test_api_foundation.py::test_unlock_propagates_db_unlocked` | 1 | `app.state.db_unlocked` mode-gating assertion — lock/unlock state leaks between tests. | MEU-90b (`mode-gating-test-isolation`) |

Neither failure category is related to playwright or kaleido installation.

### Evidence

- **AC-90d.1**: `uv pip install "packages/infrastructure[rendering]"` → exit 0 ✅
- **AC-90d.2**: `import playwright; import kaleido` both print OK ✅
- **AC-90d.3**: `uv run playwright install chromium` → exit 0 ✅
- **AC-90d.4**: `test_AC_SR12_render_pdf_creates_directory` → 1 passed ✅
- **AC-90d.5**: `test_AC_SR11_render_candlestick_keys` → 1 passed, PNG branch active ✅
- **AC-90d.6**: Full suite: 6 failed (pre-existing, two unrelated causes — see table above), 1591 passed, 15 skipped; **0 new failures introduced by this MEU** ✅

### MEU Gate

```
All blocking checks passed! (21.55s)
Exit code: 0
```

## Reviewer Output

- Findings: None
- Verdict: `ready_for_review`

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:** —
- **Timestamp:** —

## Final Summary

- Status: `ready_for_review`
- Next steps: Codex validates this handoff. MEU-90c is **closed** (human decision 2026-03-22, Option A+B): local skip accepted, CI coverage added via `crypto-tests` job. No further MEU-90c work required.

## Sibling MEU Note — MEU-90c CLOSED

MEU-90c (`sqlcipher-native-deps`) was attempted in the same session and hit a hard
platform blocker: `sqlcipher3-binary` (≤ 0.6.0) ships only Linux wheels. The human
decision (2026-03-22) was Option A + B: accept local skip, add Linux CI stage.
The `crypto-tests` job in `.github/workflows/ci.yml` now runs the 15 encryption tests
on `ubuntu-latest`. ADR-001 §Addendum documents the decision. MEU-90c is **closed**.
