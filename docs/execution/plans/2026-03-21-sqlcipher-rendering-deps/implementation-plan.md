# Implementation Plan — MEU-90c + MEU-90d
# Native Dependency Installation: SQLCipher + Rendering

> **Project slug:** `sqlcipher-rendering-deps`
> **Date:** 2026-03-21
> **MEUs:** MEU-90c (`sqlcipher-native-deps`), MEU-90d (`rendering-deps`)
> **Session folder:** `docs/execution/plans/2026-03-21-sqlcipher-rendering-deps/`
> **Handoff sequence:** 082 (MEU-90c), 083 (MEU-90d)

---

## Context

Both MEUs clear skipped tests by installing native / optional extras that were deferred
during earlier phases due to platform fragility. Neither MEU modifies application logic.

**MEU-90c** installs `sqlcipher3-binary` (the `[crypto]` extra already defined in
`packages/infrastructure/pyproject.toml`) and validates it clears 15 skipped encryption tests.

**MEU-90d** installs `playwright` + downloads the Chromium browser binary (the `[rendering]`
extra already defined in `packages/infrastructure/pyproject.toml`) and validates it clears
1 skipped PDF-render test (AC-SR12).

### Why these two MEUs are a natural pair
- Both are pure dependency installation tasks — zero application code changes
- Both are fully independent of MEU-90a and MEU-90b
- Both validate by running existing tests; no new test code needed
- Both clear "skipped" red flags so the full test suite is pristine before MEU-90b/90a

### Skipped Test Inventory

**MEU-90c — 15 tests gated on `HAS_SQLCIPHER`:**

| File | Tests | Gate |
|------|-------|------|
| `tests/security/test_encryption_integrity.py` | 14 tests (entire module, `pytestmark`) | `not HAS_SQLCIPHER` |
| `tests/integration/test_database_connection.py` | 1 test (`test_encrypted_db_unreadable_by_plain_sqlite`) | `not is_sqlcipher_available()` |

**MEU-90d — 1 test gated on `playwright` importability:**

| File | Test | Gate |
|------|------|------|
| `tests/unit/test_store_render_step.py` | `test_AC_SR12_render_pdf_creates_directory` | `pytest.importorskip("playwright")` |

> [!NOTE]
> `test_AC_SR11_render_candlestick_keys` (kaleido) is **not** a skip — it just has a
> `if result["png_data_uri"]:` conditional branch. Installing kaleido makes the PNG assertion
> active. This is also addressed in MEU-90d as a quality gate.

---

## Task Table

| Task | Owner Role | Deliverable | Validation | Status |
|------|-----------|-------------|------------|--------|
| Install `[crypto]` extra (`sqlcipher3-binary`) | Coder | `sqlcipher3` importable in venv | `uv run python -c "import sqlcipher3"` exits 0 | ⬜ |
| Validate MEU-90c: 14 encryption tests pass | Tester | `tests/security/test_encryption_integrity.py` 14 PASSED | `uv run pytest tests/security/test_encryption_integrity.py -v` | ⬜ |
| Validate MEU-90c: 1 skipif test now passes | Tester | `test_encrypted_db_unreadable_by_plain_sqlite` PASSED | `uv run pytest tests/integration/test_database_connection.py -v` | ⬜ |
| MEU-90c full regression | Tester | 0 FAILED, 0 ERROR | `uv run pytest tests/ -q --tb=short` | ⬜ |
| MEU-90c MEU gate | Tester | Gate passes | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| Write MEU-90c handoff `082-…` | Orchestrator | `082-2026-03-22-sqlcipher-native-deps-bp02s2.3.md` | File exists in `.agent/context/handoffs/` | ⬜ |
| Update MEU registry + BUILD_PLAN for MEU-90c | Orchestrator | Status → `🟡 ready_for_review` | `rg "MEU-90c" docs/BUILD_PLAN.md` shows 🟡 | ⬜ |
| Install `[rendering]` extra (playwright + kaleido) | Coder | Both packages importable; Chromium downloaded | `uv run python -c "import playwright; import kaleido"` exits 0 | ⬜ |
| Validate MEU-90d: AC-SR12 passes | Tester | `test_AC_SR12_render_pdf_creates_directory` PASSED | `uv run pytest tests/unit/test_store_render_step.py::test_AC_SR12_render_pdf_creates_directory -v` | ⬜ |
| Validate MEU-90d: AC-SR11 PNG branch exercised | Tester | `png_data_uri` non-empty, starts with `data:image/png;base64,` | `uv run pytest tests/unit/test_store_render_step.py::test_AC_SR11_render_candlestick_keys -v -s` | ⬜ |
| MEU-90d full regression | Tester | 0 new FAILED introduced by this MEU (pre-existing failures documented) | `uv run pytest tests/ -q --tb=short` — confirm count vs pre-install baseline | ⬜ |
| MEU-90d MEU gate | Tester | Gate passes | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| Write MEU-90d handoff `083-…` | Orchestrator | `083-2026-03-22-rendering-deps-bp09s9.7d.md` | File exists in `.agent/context/handoffs/` | ⬜ |
| Update MEU registry + BUILD_PLAN for MEU-90d | Orchestrator | Status → `🟡 ready_for_review` | `rg "MEU-90d" docs/BUILD_PLAN.md` shows 🟡 | ⬜ |
| Update `docs/BUILD_PLAN.md` hub task | Orchestrator | No stale refs; both MEUs show 🟡 | `rg "MEU-90c\|MEU-90d" docs/BUILD_PLAN.md` | ⬜ |

---

## Spec Sufficiency Gate

### MEU-90c

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Install mechanism: `[crypto]` extra | `Spec` | `packages/infrastructure/pyproject.toml` L23-26 | ✅ |
| Packages: `sqlcipher3-binary>=0.5.4`, `argon2-cffi>=23.1.0` | `Spec` | `packages/infrastructure/pyproject.toml` L24-25 | ✅ |
| Plain SQLite fallback when absent | `Spec` | `docs/adrs/ADR-001-optional-sqlcipher-encryption.md` | ✅ |
| Test gate function `is_sqlcipher_available()` declared + imported | `Local Canon` | `packages/infrastructure/src/zorivest_infra/database/connection.py`; exercised in `tests/integration/test_database_connection.py` L10-13, L93-98 | ✅ |
| `HAS_SQLCIPHER` module-level skip in security test | `Local Canon` | `tests/security/test_encryption_integrity.py` L32-42 (`pytestmark`) | ✅ |
| 15 tests to clear | `Spec` | `docs/BUILD_PLAN.md` MEU-90c description + test collection audit | ✅ |
| `test_fallback_produces_plaintext_warning` becomes skip after install | `Local Canon` | `tests/integration/test_database_connection.py` L119-136 (skipif `is_sqlcipher_available()`) | ✅ |

### MEU-90d

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| Install mechanism: `[rendering]` extra | `Spec` | `packages/infrastructure/pyproject.toml` L27-30 | ✅ |
| Packages: `playwright>=1.50`, `kaleido>=1.0` | `Spec` | `packages/infrastructure/pyproject.toml` L28-29 | ✅ |
| Chromium browser download required separately | `Spec` | `packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py` L41-42 (ImportError message) + AC-SR12 skip reason `tests/unit/test_store_render_step.py` L239 | ✅ |
| Test gate: `pytest.importorskip("playwright")` | `Local Canon` | `tests/unit/test_store_render_step.py` L239 | ✅ |
| 1 test to clear (AC-SR12) | `Spec` | `docs/BUILD_PLAN.md` MEU-90d description | ✅ |
| kaleido activates AC-SR11 PNG branch | `Local Canon` | `tests/unit/test_store_render_step.py` L222-227 | ✅ |

---

## Proposed Changes

> [!IMPORTANT]
> **Zero application code changes.** Both MEUs are install-and-validate only.
> The `pyproject.toml` extras are already correctly defined. Only dependency
> installation commands are needed.

### MEU-90c — SQLCipher Native Deps

**Steps:**
1. Install `zorivest-infra[crypto]` into the project venv using `uv`
2. Verify `sqlcipher3` is importable in the venv
3. Run the 15 previously-skipped encryption tests and confirm they pass
4. Confirm `test_fallback_produces_plaintext_warning` is now skipped (correct — inverse gate)
5. Run full regression to confirm no regressions

**Install command:**
```bash
uv pip install "packages/infrastructure[crypto]"
```

> [!NOTE]
> `sqlcipher3-binary` provides prebuilt Windows wheels since 0.5.4.
> `argon2-cffi` is already in core deps (≥25.1.0 > 23.1.0) so the crypto extra
> version pin is a no-op for argon2. The key package is `sqlcipher3-binary`.

### MEU-90d — Rendering Deps (Playwright + kaleido)

**Steps:**
1. Install `zorivest-infra[rendering]` into the project venv using `uv`
2. Download Chromium browser binary via `playwright install chromium`
3. Verify `playwright` and `kaleido` are importable in the venv
4. Run AC-SR12 (the 1 previously-skipped PDF test) and confirm it passes
5. Run AC-SR11 again and confirm PNG branch is now exercised (non-empty `png_data_uri`)
6. Run full regression to confirm no regressions

**Install commands:**
```bash
uv pip install "packages/infrastructure[rendering]"
uv run playwright install chromium
```

> [!NOTE]
> `playwright install chromium` downloads ~130MB Chromium binary.
> This only needs to run once per machine. The binary is cached in Playwright's
> `AppData` directory on Windows.

---

## BUILD_PLAN.md Review

**Required update:** After each MEU completes and its handoff is written, update the
status column for that MEU from `⬜` to `🟡 ready_for_review`. The `✅ approved` state
is set only after Codex validation passes — Opus cannot self-approve.

**Documentation bug (flagged in previous analysis):**
`09a-persistence-integration.md` lines 81-82 reference `MEU-90b service-wiring` for
`StubMarketDataService` and `StubProviderConnectionService`, but `BUILD_PLAN.md` registry
assigns MEU-90b slug as `mode-gating-test-isolation`. This doc bug is pre-existing —
fixing it is out of scope for this project, but it is noted in both handoffs for the
next session to resolve.

---

## Feature Intent Contracts (FICs)

### FIC: MEU-90c — `sqlcipher-native-deps`

| Acceptance Criterion | Source | Description |
|---|---|---|
| AC-90c.1 | `Spec` | `uv pip install packages/infrastructure[crypto]` exits 0 |
| AC-90c.2 | `Local Canon` | `python -c "import sqlcipher3; print('ok')"` prints `ok` |
| AC-90c.3 | `Spec` | All 15 previously-skipped tests in `test_encryption_integrity.py` + `test_database_connection.py` now **pass** |
| AC-90c.4 | `Spec` | `pytest tests/ -q` shows 0 FAILED, 0 ERROR (skips reduced by 15) |
| AC-90c.5 | `Spec` | `test_fallback_produces_plaintext_warning` transitions from PASS → SKIP (correct: gate is `is_sqlcipher_available()`) |

### FIC: MEU-90d — `rendering-deps`

| Acceptance Criterion | Source | Description |
|---|---|---|
| AC-90d.1 | `Spec` | `uv pip install packages/infrastructure[rendering]` exits 0 |
| AC-90d.2 | `Local Canon` | `python -c "import playwright; import kaleido; print('ok')"` prints `ok` |
| AC-90d.3 | `Spec` | `uv run playwright install chromium` completes (Chromium downloaded) |
| AC-90d.4 | `Spec` | `test_AC_SR12_render_pdf_creates_directory` now **passes** (was skipped) |
| AC-90d.5 | `Local Canon` | `test_AC_SR11_render_candlestick_keys` PNG branch is exercised: `png_data_uri` non-empty and starts with `data:image/png;base64,` |
| AC-90d.6 | `Spec` | `pytest tests/ -q` shows **0 new FAILED introduced by this MEU**; pre-existing failures documented in handoff |

---

## Handoff Files

```
082-2026-03-22-sqlcipher-native-deps-bp02s2.3.md
083-2026-03-22-rendering-deps-bp09s9.7d.md
```

---

## Verification Plan

### Automated Tests

**MEU-90c validation sequence:**
```powershell
# 1. Verify import
uv run python -c "import sqlcipher3; print('sqlcipher3 OK:', sqlcipher3.sqlite_version)"

# 2. Run encryption-specific tests
uv run pytest tests/security/test_encryption_integrity.py -v

# 3. Run database connection tests (includes the 1 skipif test)
uv run pytest tests/integration/test_database_connection.py -v

# 4. Full regression
uv run pytest tests/ -q --tb=short
```

**MEU-90d validation sequence:**
```powershell
# 1. Verify imports
uv run python -c "import playwright; import kaleido; print('rendering deps OK')"

# 2. Run the single previously-skipped test
uv run pytest tests/unit/test_store_render_step.py::test_AC_SR12_render_pdf_creates_directory -v

# 3. Run AC-SR11 to verify PNG branch is now exercised
uv run pytest tests/unit/test_store_render_step.py::test_AC_SR11_render_candlestick_keys -v -s

# 4. Full store/render step suite
uv run pytest tests/unit/test_store_render_step.py -v

# 5. Full regression
uv run pytest tests/ -q --tb=short
```

### No OpenAPI Changes
Neither MEU touches `packages/api/`. No `export_openapi.py` regeneration needed.

### No GUI Changes
Neither MEU touches `ui/`. No E2E tests affected.
