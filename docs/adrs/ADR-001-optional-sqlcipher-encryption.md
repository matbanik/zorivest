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

## Addendum — 2026-03-22: Windows Dev Environment Decision

**Context:** MEU-90c (`sqlcipher-native-deps`) attempted to install `sqlcipher3-binary` on
Windows (Python 3.12.12 AMD64) and found that all published versions (≤0.6.0) ship only
`manylinux_2_17_x86_64` / `manylinux2014_x86_64` wheels — no `win_amd64` wheels exist.

**Decision (Human-approved 2026-03-22):** Option A + Option B.

- **Option A — Accept local skip:** The 15 encryption tests remain `skipif` gated by
  `is_sqlcipher_available()` / `HAS_SQLCIPHER` on Windows developer machines. This is
  consistent with the original ADR decision rationale: Option B ("require in CI") was
  rejected for fragility, and local Windows dev is even more constrained than CI.
- **Option B — Linux CI stage:** A dedicated `crypto-tests` job was added to
  `.github/workflows/ci.yml` running on `ubuntu-latest`. It installs `[crypto]` and runs
  all 15 encryption tests, providing full CI coverage without requiring Windows compilation.

**Effect on MEU-90c:** Closed as `won't fix locally`; CI coverage provided via Option B.
