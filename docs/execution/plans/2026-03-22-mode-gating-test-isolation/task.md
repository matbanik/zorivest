# MEU-90b: mode-gating-test-isolation — Task Checklist

## Research (complete)
- [x] Read meu-registry.md — confirmed slug = `mode-gating-test-isolation`, matrix 49.1
- [x] Read main.py — lifespan line 133 sets `db_unlocked` from `ZORIVEST_DEV_UNLOCK`
- [x] Read 4 test files with `locked_client` fixtures (analytics, tax, system, market_data)
- [x] Read 09a-persistence-integration.md — stale slug bug at lines 81–83
- [x] Ran mode-gating tests in isolation — 9/9 PASS
- [x] Ran full unit test suite — 5 FAIL in `test_provider_registry.py` (count drift)
- [x] Identified root cause: MEU-65 added Yahoo Finance + TradingView (GUI layer); tests not updated
- [x] Confirmed canon: Yahoo Finance + TradingView are MEU-65 additions, not MEU-59 spec (`current-focus.md:93`)
- [x] Confirmed DOC-STALESLUG correct target: `MEU-90a persistence-wiring` (`known-issues.md:142`)
- [x] Plan critical review completed — `changes_required` → corrections applied

## Implementation

### Fix 1: test_provider_registry.py — exact closed-set contract (12 API-key + 2 free = 14)
- [x] Keep `EXPECTED_NAMES` at 12 (used for AC-2 parametrized field-presence tests)
- [x] Add `FREE_PROVIDER_NAMES = ["TradingView", "Yahoo Finance"]` constant
- [x] AC-1: `assert len(PROVIDER_REGISTRY) == len(EXPECTED_NAMES) + len(FREE_PROVIDER_NAMES)` (== 14 exact)
- [x] AC-1: update class + module docstrings — "exactly 14 entries (12 API-key + 2 free)"
- [x] AC-3: exact closed-set `assert actual_set == set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)`
- [x] AC-5: `assert len(names) == 14`; `assert set(names) == set(EXPECTED_NAMES) | set(FREE_PROVIDER_NAMES)`
- [x] AC-5: update docstrings — "exactly 14 names"
- [x] Add `TestFreeProvidersAC7` — verifies Yahoo Finance + TradingView exist with `AuthMethod.NONE`
- [x] Fix module docstring — "12" → "14"

### Fix 2: provider_registry.py module docstring
- [x] Line 3: "Static registry of all 12 market data" → "Static registry of market data" (remove hard count)

### Fix 3: Stale doc [DOC-STALESLUG] — all 3 files
- [x] `09a-persistence-integration.md` lines 81–83: `MEU-90b \`service-wiring\`` → `MEU-90a \`persistence-wiring\``
- [x] `09a-persistence-integration.md` lines 81–82: link anchor `#service-wiring-meu-90b` → `#service-wiring-meu-90a`
- [x] `08-market-data.md` line 782: `## Service Wiring (MEU-90b)` → `## Service Wiring` (remove MEU attribution)
- [x] `08-market-data.md` line 785: `MEU-90b (\`service-wiring\`)` → `The service-wiring MEU`
- [x] `known-issues.md` line 77: `proposed MEU-90b \`service-wiring\`` → `MEU-90a \`persistence-wiring\``

### Fix 4: known-issues.md [DOC-STALESLUG] closure
- [x] Mark `[DOC-STALESLUG]` as **Resolved** — 2026-03-22

## Verification
- [x] `uv run pytest tests/unit/test_provider_registry.py -v` — 89 passed
- [x] `uv run pytest tests/unit/ --tb=no -q` — 1432 passed
- [x] Mode-gating tests still 9 passed
- [x] `uv run ruff check tests/unit/test_provider_registry.py` — clean
- [x] `uv run pyright tests/unit/test_provider_registry.py` — clean
- [x] `uv run python tools/validate_codebase.py --scope meu` — clean (advisory: handoff bundle format, addressed in 084)
- [x] `rg "MEU-90b.*service-wiring" docs/build-plan/` — 0 matches

## Handoff & Documentation
- [x] Update MEU-90b status in BUILD_PLAN.md (⬜ → ✅, reverted → 🔴 pending impl review clean pass)
- [x] Update meu-registry.md — MEU-90b status = 🔴 changes_required
- [x] Create handoff 084
