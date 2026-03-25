# MEU-90b: mode-gating-test-isolation

Fix the 5 failing `test_provider_registry.py` tests (registry count drift) and resolve the stale doc bug [DOC-STALESLUG] in `09a-persistence-integration.md`.

> [!NOTE]
> The original 8 flaky mode-gating tests were already fixed in session `a1f060ee` (2026-03-20). All 9 mode-gating tests pass. MEU-90b scope is narrowed to registry-test alignment and doc cleanup.

> [!IMPORTANT]
> **Provider count canon (H1):** Yahoo Finance + TradingView are a MEU-65 GUI-layer addition ("14 providers (12 registry + Yahoo Finance + TradingView free)" — `current-focus.md:93`), **not** part of the MEU-59 12-provider canonical spec. The fix preserves the 12-provider contract while allowing registry growth.
>
> **DOC-STALESLUG correct target (H2):** `known-issues.md:142` — correct fix is `MEU-90b service-wiring` → **`MEU-90a persistence-wiring`**, not `mode-gating-test-isolation`.

## Proposed Changes

---

### Provider Registry Tests

#### [MODIFY] [test_provider_registry.py](file:///p:/zorivest/tests/unit/test_provider_registry.py)

Source of truth: `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py` (not `packages/api/`).

Strategy — **preserve MEU-59 12-provider contract, closed set of 14 total**:

1. **Keep `EXPECTED_NAMES`** at 12 original API-key providers (used for AC-2 parametrized field-presence tests)
2. **Add `FREE_PROVIDER_NAMES`** constant — `["TradingView", "Yahoo Finance"]` (MEU-65 GUI additions)
3. **AC-1 (`test_registry_count`)** — `assert len(PROVIDER_REGISTRY) == len(EXPECTED_NAMES) + len(FREE_PROVIDER_NAMES)` (== 14, exact closed set)
4. **AC-1 docstring** — update: "exactly 14 entries (12 API-key + 2 free)"
5. **AC-3 name tests** — exact closed-set equality:
   - `test_all_expected_names_present` → `assert actual_set == set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)`
   - `test_no_unexpected_names` → `assert actual_set == set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)` (consolidate or keep two for clarity)
6. **AC-5** — `assert len(names) == len(EXPECTED_NAMES) + len(FREE_PROVIDER_NAMES)`; `assert set(names) == set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)`
7. **AC-5 docstring** — update: "exactly 14 names (12 API-key + 2 free)"
8. **Add `TestFreeProvidersAC7`** — new test class verifying Yahoo Finance + TradingView are in registry with `AuthMethod.NONE`
9. **Module docstring lines 4, 8** — update count references (`12` → `14`)

---

### Stale Documentation Fix

#### [MODIFY] [09a-persistence-integration.md](file:///p:/zorivest/docs/build-plan/09a-persistence-integration.md)

Lines 81–83: Change `MEU-90b \`service-wiring\`` → `MEU-90a \`persistence-wiring\`` in the stub retirement table (three rows: `StubMarketDataService`, `StubProviderConnectionService`, `McpGuardService`).

Update cross-reference link anchors `#service-wiring-meu-90b` → `#service-wiring-meu-90a`.

#### [MODIFY] [08-market-data.md](file:///p:/zorivest/docs/build-plan/08-market-data.md)

- Line 782: `## Service Wiring (MEU-90b)` → `## Service Wiring` (remove MEU attribution — no single registered MEU owns the full wiring scope)
- Line 785: Remove `MEU-90b (\`service-wiring\`)` → `The service-wiring MEU`

#### [MODIFY] [known-issues.md](file:///p:/zorivest/.agent/context/known-issues.md)

- Line 77: `#### Phase 1 — Wireable now (proposed MEU-90b \`service-wiring\`)` → `#### Phase 1 — Wireable now (MEU-90a \`persistence-wiring\`)`
- Mark `[DOC-STALESLUG]` as **Resolved** — 2026-03-22

---

### Build Plan + Registry Updates

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

Line 301: Update MEU-90b status `⬜` → `✅`

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

Update MEU-90b status to `✅ approved`.

---

## Verification Plan

### Automated Tests

```bash
# Primary fix: 5 failing tests all green
uv run pytest tests/unit/test_provider_registry.py -v

# Full regression: 0 failures remaining
uv run pytest tests/unit/ --tb=no -q

# Mode-gating confirmation (must still pass, 9 tests)
uv run pytest tests/unit/test_api_analytics.py::TestModeGating tests/unit/test_api_tax.py::TestTaxModeGating tests/unit/test_api_system.py::TestMcpGuardAuth tests/unit/test_market_data_api.py::TestGetQuote::test_locked_db_returns_403 tests/unit/test_api_foundation.py::TestModeGating tests/unit/test_api_settings.py::TestSettingsModeGating -v
```

### Quality Gate

```bash
# Lint + types on touched files
uv run ruff check tests/unit/test_provider_registry.py packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py
uv run pyright tests/unit/test_provider_registry.py
# MEU gate (required by AGENTS.md:209 before MEU completion)
uv run python tools/validate_codebase.py --scope meu
```

### Doc Cross-Reference Check

```bash
# Restrict to docs/build-plan/ only (excludes handoffs and known-issues history)
rg -n "MEU-90b.*service-wiring|service-wiring.*MEU-90b" docs/build-plan/
```

**Expected outcomes:**
- `test_provider_registry.py`: 83+ passed, 0 failed
- Full unit suite: 0 failed
- Mode-gating: 9 passed
- Ruff + pyright: clean
- Doc sweep: 0 matches for stale slug
