# Remaining Buckets — Opus Audit

Covers Integration, MCP, and UI test buckets.
Criteria: [phase1-ir5-rating-criteria.md](../phase1-ir5-rating-criteria.md)

## Integration Tests

Summary: 48 tests audited | 🟢 40 | 🟡 7 | 🔴 1

### Codex Comparison

| Metric | Codex | Opus | Delta |
|--------|------:|-----:|------:|
| 🟢 | 39 | 40 | +1 |
| 🟡 | 7 | 7 | 0 |
| 🔴 | 2 | 1 | −1 |

### Codex Disagreement

| Rating | File | Line | Test | Codex | Opus Reason |
|--------|------|-----:|------|-------|-------------|
| 🟡 | `test_database_connection.py` | 93 | `test_sqlcipher_availability_flag` | 🔴 | Checks `hasattr(module, 'SQLCIPHER_AVAILABLE')` — structural but the flag gates encryption behavior globally. 🟡 not 🔴 because feature-gating flags have behavioral impact. |
| 🔴 | `test_unit_of_work.py` | 82 | `test_all_repos_available` | 🔴 | Agrees — pure `hasattr` checks for `uow.trades`, `uow.accounts`, etc. without exercising them. |

### Assessment

Integration tests are the **strongest** bucket per-test — 83% 🟢 with deep round-trip coverage (backup create→verify→restore, repo CRUD, WAL concurrency). Only 1 structural 🔴 remains.

---

## MCP Server Tests

Summary: 156 tests audited | 🟢 151 | 🟡 5 | 🔴 0

### Codex Comparison

**Full agreement.** No Opus disagreements.

### Assessment

MCP tests are **exemplary** — 97% 🟢, zero 🔴. Clean HTTP mock assertions with URL, method, header, and body validation. The 5 🟡s are mock-call verifications (`sendToolListChanged`, guard bypass).

---

## UI Tests

Summary: 56 tests audited | 🟢 48 | 🟡 8 | 🔴 0

### Codex Comparison

**Full agreement.** No Opus disagreements.

### Assessment

UI tests are **strong** — 86% 🟢, zero 🔴. Good ARIA landmark assertions, accessibility checks, and behavioral tests (keyboard navigation, command palette filtering). The 8 🟡s are rendering/mock-call checks.

---

## Cross-Bucket Summary

| Bucket | Tests | 🟢 | 🟡 | 🔴 |
|--------|------:|----:|----:|----:|
| Integration | 48 | 40 | 7 | 1 |
| MCP | 156 | 151 | 5 | 0 |
| UI | 56 | 48 | 8 | 0 |
| **Subtotal** | **260** | **239** | **20** | **1** |
