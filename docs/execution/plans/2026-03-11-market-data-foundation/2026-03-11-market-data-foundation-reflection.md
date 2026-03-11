# Reflection — Market Data Foundation

> Project: `2026-03-11-market-data-foundation`
> MEUs: MEU-56, MEU-57, MEU-58
> Date: 2026-03-11

## What Went Well

- **TDD discipline held** — All tests written before implementation. Red→Green transitions clean for all 3 MEUs (20 + 16 + 10 = 46 tests).
- **Spec alignment** — After critical review corrections, `MarketDataPort` correctly uses DTO return types matching §8.1d exactly.
- **Dual review cycles** — Two rounds of critical review caught real issues: wrong return annotations (`Any` instead of DTO types), incomplete serialization coverage, and stale evidence counts.
- **Infrastructure fix** — Diagnosed and fixed `validate_codebase.py` TypeScript crash (wrong cwd + missing `shell=True` on Windows).

## What Could Improve

- **Initial return types** — `MarketDataPort` was initially implemented with `Any` returns instead of DTO types. Should have caught this during Green phase before handoff.
- **Serialization coverage** — Only `MarketQuote` had a JSON round-trip test initially. Should have written round-trip tests for all DTOs from the start.
- **Evidence freshness** — Regression counts went stale between MEU completion and handoff creation. Should refresh counts at handoff time, not at implementation time.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Separate `market_dtos.py` from `dtos.py` | Avoids mixing Pydantic models with frozen dataclass DTOs from Phase 1 |
| PBKDF2 480K iterations | OWASP recommendation for password-derived keys [Research-backed] |
| `encrypted_api_secret` nullable column | Supports dual-key providers (Alpaca) without breaking single-key providers |
| `shell=True` on Windows in validator | `npx.cmd` requires shell resolution on Windows |

## Test Summary

| MEU | Tests | Coverage |
|-----|:-----:|----------|
| MEU-56 | 20/20 | AuthMethod enum, ProviderConfig VO, MarketDataPort Protocol + return annotations |
| MEU-57 | 16/16 | 4 Pydantic DTOs, all with JSON round-trip |
| MEU-58 | 10/10 | encrypt/decrypt, idempotent, pass-through, derive_fernet_key, wrong-key |
| **Total** | **46/46** | + 2 model tests (encrypted_api_secret column) |
| Full regression | 696 passed, 1 skipped | |
