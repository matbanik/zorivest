# Reflection — settings-backup-foundation

> Project: settings-backup-foundation | Phase 2A | 2026-03-08

## Scope

MEU-17 (app-defaults), MEU-18 (settings-resolver), MEU-19 (backup-manager).

## What Went Well

- **Three-tier settings resolution** (hardcoded → app_default → user override) implemented cleanly with proper separation of concerns.
- **TDD discipline** held: all acceptance criteria mapped to tests before implementation.
- **Backup pipeline** (snapshot → encrypt → manifest → GFS rotate → verify) delivered end-to-end.

## What Needed Correction

The implementation critical review identified 5 findings that required a corrections pass:

1. **SQLAlchemy settings repos missing** — ports existed but no concrete `SqlAlchemySettingsRepository`/`SqlAlchemyAppDefaultsRepository` were implemented. Service only worked against test doubles.
2. **KDF contract mismatch** — Code used PBKDF2 while `KDFParams` metadata claimed Argon2id. Resolved by installing `argon2-cffi` and implementing real Argon2id.
3. **Security test gaps** — Backup tests only covered happy paths. Added wrong-password, hash integrity, KDF domain separation, algorithm verification, GFS rotation, and file presence tests.
4. **Missing `get_all()` method** — Plan required 5 methods, only 4 were delivered.
5. **Incomplete shared artifacts** — BUILD_PLAN.md, meu-registry.md, task.md not updated.

## Lessons Learned

- **Don't defer infrastructure wiring** — if the plan says "add SqlAlchemy repos", ship them in the same MEU. Test doubles masking real integration gaps is a recurring anti-pattern.
- **KDF metadata must match implementation** — writing `algorithm: "argon2id"` when using PBKDF2 is misleading. Either use the spec-intended library or downgrade the spec honestly.
- **Security tests are non-optional** — backup/restore is safety-critical. Wrong-password, hash integrity, and KDF verification should be in the initial test suite, not added in corrections.
- **Track all plan methods** — diff the plan's method list against the implementation before handoff.

## Metrics

| Metric | Value |
|--------|-------|
| MEUs delivered | 3 (17, 18, 19) |
| Tests at handoff | 447 passed, 1 skipped |
| Tests added in corrections | 9 (7 backup + 2 settings) |
| Findings from review | 5 (3 High, 2 Medium) |
| Corrections pass count | 1 |
| Dependencies added | `argon2-cffi`, `pyzipper` |
