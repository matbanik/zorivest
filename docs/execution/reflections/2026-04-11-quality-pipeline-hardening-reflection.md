# Reflection: Quality Pipeline Hardening

**Project**: `2026-04-11-quality-pipeline-hardening`
**MEU**: CI-FIX-1, CI-FIX-2, MEU-TS2, MEU-TS4
**Date**: 2026-04-11
**Agent**: gemini-2.5-pro

---

## What Went Well

1. **Zero production code changes** — The entire project was scoped to test files, CI artifacts, and test assertions. No domain, infra, API, or MCP code was touched, eliminating regression risk.
2. **Efficient enum refactoring** — The Tier 2 `reportArgumentType` fix was systematic: identify enum type from entity signature → import enum → replace string literal. 36 errors across 3 files were fixed in a single pass.
3. **Correct root-cause diagnosis** — MEU-TS4's market data service failures were correctly traced to premature Yahoo Finance network calls, not mock configuration issues. The `@patch.object` on the private `_yahoo_quote` method was the precise fix.
4. **Clean MEU gate** — All 8 blocking checks passed on first attempt after implementation.

## What Could Improve

1. **Post-execution deliverables deferred** — Rows 17–21 (handoff, reflection, metrics, session note, BUILD_PLAN audit) were left incomplete at the end of the implementation session. The Codex critical review correctly flagged this as a High-severity audit gap. Lesson: treat post-execution deliverables as part of the same execution pass, not a separate session.
2. **Validation cell quality** — Three validation cells used shorthand ("same vitest command", "File comparison", "same pytest command") instead of exact commands. Three more used per-file pyright exits as Tier 2 proof when those files still contain Tier 3 errors, making exit codes meaningless. One used forbidden `| findstr` pipe. Lesson: every validation cell must be self-contained, P0-compliant, and prove exactly what it claims.
3. **Plan accuracy** — The initial plan anticipated Tier 2 errors in factory files and fixture files based on `known-issues.md`, but the actual errors were in integration test files and a service test file. Lesson: run the actual pyright command and count errors by file before finalizing the plan's file list.

## Lessons Learned

- **Per-file pyright exit codes are useless for error-category proof.** Pyright exits non-zero for ANY error — you can't distinguish Tier 2 from Tier 3 via exit code. The correct proof is `Select-String -Pattern "reportArgumentType"` on the full-suite output.
- **String-to-enum refactoring is mechanical once you know the signature.** The pattern is always: (1) read entity constructor → (2) import the enum → (3) replace `"literal"` with `EnumName.MEMBER`. This should be toolable in future.
- **`@patch.object` on private methods is fragile but justified.** The `_yahoo_quote` method is an implementation detail that could be renamed. But without it, provider-fallback tests make real HTTP calls, which is worse. The tradeoff was documented.

## Metrics

| Metric | Value |
|--------|-------|
| Planning passes | 2 (initial + 1 correction pass) |
| Execution passes | 1 |
| Codex review rounds | 1 (2 findings, both resolved) |
| Files changed | 8 (all test/CI artifacts) |
| ACs met | 7/7 |
| Pyright errors eliminated | 36 Tier 2 (241 → 205) |
| Tests confirmed passing | 1623 unit/integration |
