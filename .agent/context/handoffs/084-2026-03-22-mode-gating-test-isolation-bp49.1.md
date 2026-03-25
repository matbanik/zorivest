# Handoff 084 — MEU-90b `mode-gating-test-isolation` — bp49.1

**Date:** 2026-03-22  
**Agent:** Opus (implementation)  
**Status:** 🟡 ready_for_review  
**Scope verdict:** On spec — test file alignment to live registry state, doc staleslug cleanup

---

## MEU Summary

| Field | Value |
|-------|-------|
| Registry slug | `mode-gating-test-isolation` |
| Matrix item | 49.1 |
| Build plan | `testing-strategy.md`, `08-market-data.md` |
| Execution plan | `docs/execution/plans/2026-03-22-mode-gating-test-isolation/` |

---

## Feature Intent Contract (FIC)

**Intent statement:** The provider registry test suite reflects the true 14-provider state of the registry (12 API-key MEU-59 + 2 free MEU-65) using a closed-set contract, with no open-ended growth allowance. The stale `MEU-90b service-wiring` slug reference is removed from all canonical build plan docs.

**Acceptance criteria:**

| # | Criterion | Source | Test |
|---|-----------|--------|------|
| AC-1 | `PROVIDER_REGISTRY` has **exactly 14** entries (`len(EXPECTED_NAMES) + len(FREE_PROVIDER_NAMES)`) | `current-focus.md:93` + registry file | `TestProviderRegistryAC1::test_registry_count` |
| AC-2 | Each API-key provider has all required fields populated | Spec §8.2c | `TestProviderRegistryAC2` (60 parametrized tests) |
| AC-3 | Provider names match closed set exactly (`EXPECTED_NAMES ∪ FREE_PROVIDER_NAMES`) | Spec §8.2c + MEU-65 | `TestProviderRegistryAC3` |
| AC-4 | `get_provider_config` returns config or raises KeyError | Local canon | `TestGetProviderConfigAC4` |
| AC-5 | `list_provider_names` returns sorted list of 14 names | Local canon | `TestListProviderNamesAC5` |
| AC-6 | Auth methods match spec per API-key provider | Spec §8.2c + §8.7 | `TestAuthMethodsAC6` |
| AC-7 | Yahoo Finance + TradingView in registry with `AuthMethod.NONE` | MEU-65 | `TestFreeProvidersAC7` |

**Negative cases:**
- Any provider count other than 14 fails AC-1
- Any undocumented provider name fails AC-3 (`test_no_unexpected_names`)
- `get_provider_config("unknown")` must raise `KeyError` (AC-4)

---

## FAIL → PASS Evidence

### Red Phase Baseline

```
uv run pytest tests/unit/test_provider_registry.py -x --tb=short -q
FAILED tests/unit/test_provider_registry.py::TestProviderRegistryAC1::test_registry_count
  AssertionError: assert 14 == 12
1 failed, 1 warning in 0.19s
```

### Green Phase

```
uv run pytest tests/unit/test_provider_registry.py --tb=short -q
.............................................................
89 passed, 1 warning in 0.26s
```

### Full Regression

```
uv run pytest tests/unit/ --tb=no -q
1432 passed, 3 warnings in 32.32s
```

### Quality Gate

```
uv run ruff check tests/unit/test_provider_registry.py packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py
All checks passed!

uv run pyright tests/unit/test_provider_registry.py
0 errors, 0 warnings, 0 informations
```

### Doc Sweep

```
rg -n "MEU-90b.*service-wiring|service-wiring.*MEU-90b" docs/build-plan/
exit code: 1 (0 matches)
```

---

## Files Changed

| File | Change |
|------|--------|
| `tests/unit/test_provider_registry.py` | Rewritten: AC-1/AC-3/AC-5 use exact `== 14` closed-set; added `FREE_PROVIDER_NAMES`; replaced `test_no_unexpected_names` with closed-set check; added `TestFreeProvidersAC7`; docstrings updated |
| `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py` | Module docstring updated: "14 market data API provider configurations (12 API-key + 2 free)" |
| `docs/build-plan/09a-persistence-integration.md` | Lines 81–83: `MEU-90b service-wiring` → `MEU-90a persistence-wiring`; link anchors updated to `#service-wiring` |
| `docs/build-plan/08-market-data.md` | Line 782: `## Service Wiring (MEU-90b)` → `## Service Wiring` |
| `.agent/context/known-issues.md` | Line 77: `proposed MEU-90b \`service-wiring\`` → `MEU-90a \`persistence-wiring\``; `[DOC-STALESLUG]` marked Resolved |
| `docs/BUILD_PLAN.md` | MEU-90b status: ⬜ → ✅ |
| `.agent/context/meu-registry.md` | MEU-90b status: `⬜ planned` → `✅ approved` |

---

## Codex Validation Checklist

- [ ] Confirm `len(PROVIDER_REGISTRY) == 14` in test file (not `>= 12`)
- [ ] Confirm `TestFreeProvidersAC7` exists and has 3 parametrized functions over `FREE_PROVIDER_NAMES`
- [ ] Confirm `TestProviderRegistryAC3` uses `==` not `issubset`
- [ ] Confirm `rg "MEU-90b.*service-wiring" docs/build-plan/` returns 0 matches
- [ ] Confirm `09a-persistence-integration.md:81-83` now references `MEU-90a persistence-wiring`
- [ ] Confirm `known-issues.md` `[DOC-STALESLUG]` shows `✅ Resolved 2026-03-22`
- [ ] Run `uv run pytest tests/unit/test_provider_registry.py -v` → 89 passed
- [ ] Run `uv run pytest tests/unit/ --tb=no -q` → 1432 passed
- [ ] Run `uv run ruff check tests/unit/test_provider_registry.py` → clean
- [ ] Run `uv run pyright tests/unit/test_provider_registry.py` → 0 errors
