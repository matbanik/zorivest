# Task: MEU-90c + MEU-90d — Native Dependency Installation
# Project: sqlcipher-rendering-deps
# Date: 2026-03-21

## Pre-Execution Checklist
- [x] Read SOUL.md, AGENTS.md, current-focus.md, known-issues.md, emerging-standards.md
- [x] Surveyed MEU registry (both ⬜ planned)
- [x] Read ADR-001 (optional crypto contract)
- [x] Audited test files — confirmed 15 + 1 skipped tests
- [x] Confirmed pyproject.toml extras already defined correctly
- [x] No emerging standards apply (infra install; no API/GUI/MCP changes)
- [x] Found next handoff SEQ: 082, 083
- [x] Created project folder: `docs/execution/plans/2026-03-21-sqlcipher-rendering-deps/`
- [x] Wrote `implementation-plan.md`
- [x] Wrote `task.md` (this file)

---

## MEU-90c — `sqlcipher-native-deps`

> ✅ **CLOSED** — Option A + B (human decision 2026-03-22).
> - **Option A:** Accept local Windows skip (ADR-001 already endorses this).
> - **Option B:** `crypto-tests` CI job added to `.github/workflows/ci.yml` — runs 15 encryption tests on `ubuntu-latest`.
> - See handoff `082-2026-03-22-sqlcipher-native-deps-bp02s2.3.md` and ADR-001 §Addendum.

### Install
- [x] Run: `uv pip install "packages/infrastructure[crypto]"` — ❌ FAILED (no Windows wheels; CI covered)
- [ ] ~~Verify: `uv run python -c "import sqlcipher3; print('ok')"`~~ — not reachable locally

### Validate
- [ ] ~~Run: `uv run pytest tests/security/test_encryption_integrity.py -v` → 14 PASSED~~ — local Windows skip; ✅ CI job covers this
- [ ] ~~Run: `uv run pytest tests/integration/test_database_connection.py -v`~~ — local Windows skip; ✅ CI job covers this
- [ ] ~~Confirm `test_fallback_produces_plaintext_warning` now SKIPPED~~ — intentional (no sqlcipher locally)
- [x] Run: `uv run pytest tests/ -q --tb=short` → 0 FAILED attributable to this MEU ✅

### Handoff
- [ ] ~~Run MEU gate~~ — skipped (install failed, no deliverable to gate)
- [x] Write `082-2026-03-22-sqlcipher-native-deps-bp02s2.3.md` (closed — human decision)
- [x] Update MEU registry: MEU-90c → 🚫 closed
- [x] Update `docs/BUILD_PLAN.md`: MEU-90c status → 🚫 closed

---

## MEU-90d — `rendering-deps`

> ✅ **COMPLETE** — playwright 1.58.0 + kaleido 1.2.0 installed. AC-SR12 PASSED (was skipped).
> MEU gate: all blocking checks passed.

### Install
- [x] Run: `uv pip install "packages/infrastructure[rendering]"` → playwright 1.58.0 + kaleido 1.2.0 ✅
- [x] Run: `uv run playwright install chromium` → Chromium downloaded ✅
- [x] Verify: `uv run python -c "import playwright; import kaleido; print('ok')"` → OK ✅

### Validate
- [x] Run: `uv run pytest tests/unit/test_store_render_step.py::test_AC_SR12_render_pdf_creates_directory -v` → **1 PASSED** (was skipped) ✅
- [x] Run: `uv run pytest tests/unit/test_store_render_step.py::test_AC_SR11_render_candlestick_keys -v -s` → PNG branch exercised ✅
- [x] Run: `uv run pytest tests/unit/test_store_render_step.py -v` → **24 passed** ✅
- [x] Run: `uv run pytest tests/ -q --tb=short` → 1591 passed, 15 skipped, 6 pre-existing failures (MEU-90a scope) ✅

### Handoff
- [x] Run MEU gate: `uv run python tools/validate_codebase.py --scope meu` → **All blocking checks passed** ✅
- [x] Write `083-2026-03-22-rendering-deps-bp09s9.7d.md`
- [x] Update MEU registry: MEU-90d → 🟡 ready_for_review
- [x] Update `docs/BUILD_PLAN.md`: MEU-90d status → 🟡

---

## Post-Project
- [x] **Hub drift check** — `rg "MEU-90c|MEU-90d" docs/BUILD_PLAN.md` → MEU-90c 🚫 closed, MEU-90d 🟡 ✅
- [x] Create reflection file: `docs/execution/reflections/2026-03-22-sqlcipher-rendering-deps-reflection.md`
- [x] Update `docs/execution/metrics.md`
- [x] Save session state to pomera_notes (note ID: 657)
- [x] Prepare proposed commit messages (see below)
- [x] Note pre-existing doc bug: `09a-persistence-integration.md` lines 81-82 stale slug — logged to `.agent/context/known-issues.md` as [DOC-STALESLUG]

### Proposed Commit Messages

```
feat(ci): add crypto-tests job for SQLCipher encryption tests on Linux

Installs [crypto] extra (sqlcipher3-binary) on ubuntu-latest and runs
14 security + 1 integration encryption tests. Resolves MEU-90c blocker:
no Windows wheels exist for sqlcipher3-binary; local skip retained per
ADR-001 Option A+B (human decision 2026-03-22).

Refs: ADR-001 §Addendum, handoff 082, BUILD_PLAN MEU-90c
```

```
docs(adr): append Option A+B decision addendum to ADR-001

Documents the 2026-03-22 human decision to accept local skip (Option A)
and add Linux CI coverage (Option B) for sqlcipher3-binary Windows
incompatibility.
```

```
feat(infra): install rendering deps (playwright 1.58.0 + kaleido 1.2.0)

Installs zorivest-infra[rendering] extra and downloads Chromium binary.
Clears 1 previously-skipped RenderStep test (test_AC_SR12) and activates
the kaleido PNG branch in test_AC_SR11. All 24 store/render tests pass.

Refs: BUILD_PLAN MEU-90d (09 §9.7d), handoff 083
```

---

## Stop Conditions
- ~~STOP and notify if `sqlcipher3-binary` has no Windows wheel~~ ← **triggered** → handoff 082 written
- STOP and notify if `playwright install chromium` fails (network/proxy issue)
- STOP and notify if any previously-PASSING test begins FAILING after installs
