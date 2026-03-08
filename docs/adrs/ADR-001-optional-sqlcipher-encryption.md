# ADR-001: Optional SQLCipher Encryption Contract

- **Status:** Accepted
- **Date:** 2026-03-08
- **Decision maker:** Human (Mat) — approved via implementation plan review
- **Approval provenance:** Antigravity conversation `a15b51f8-3605-408b-8b19-a66a6345d553`, corrections plan approved at 2026-03-08T11:35:57-04:00

## Context

The build plan (`02-infrastructure.md` §2.3) originally specified that `create_encrypted_connection()` must produce databases unreadable by plain `sqlite3`. This requires `sqlcipher3`, a native C library wrapper that is not available in all environments (CI, Windows dev without prebuilt binaries).

MEU-16 was implemented with a graceful fallback: when `sqlcipher3` is absent, the factory uses standard `sqlite3` and logs a `WARNING`. The critical review flagged this as a contract violation.

## Decision

**Option A — Optional encryption — was chosen.**

- Real SQLCipher encryption is available via `pip install zorivest-infra[crypto]`
- Optional dependencies: `sqlcipher3-binary>=0.5.4`, `argon2-cffi>=23.1.0`
- When absent, the factory falls back to plain `sqlite3` with a WARNING-level log
- The plaintext probe test (`test_encrypted_db_unreadable_by_plain_sqlite`) is `skipif` when `sqlcipher3` is not installed
- A fallback warning test validates the WARNING is emitted

## Alternatives Considered

**Option B — Require encryption in CI:** Install `sqlcipher3-binary` in all environments. Rejected because native C library builds are fragile cross-platform and would block CI on Windows without prebuilt wheels.

## Consequences

- Downstream phases MUST NOT assume encrypted-at-rest without checking `is_sqlcipher_available()`
- Production deployment documentation must include `pip install zorivest-infra[crypto]`
- The `[crypto]` extra is documented in `02-infrastructure.md` §2.3
