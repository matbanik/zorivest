# Opus vs Codex — Full Audit Synthesis

## Grand Total: 1,469 Tests

| Bucket | Tests | Opus 🟢 | Opus 🟡 | Opus 🔴 | Codex 🟢 | Codex 🟡 | Codex 🔴 |
|--------|------:|--------:|--------:|--------:|---------:|---------:|---------:|
| API Routes | 167 | 96 | 63 | 8 | 90 | 74 | 3 |
| Domain Models | 349 | 297 | 21 | 31 | 296 | 12 | 41 |
| Service Layer | 268 | 227 | 35 | 6 | 220 | 35 | 13 |
| Infra/Pipeline | 425 | 345 | 72 | 8 | 340 | 73 | 12 |
| Integration | 48 | 40 | 7 | 1 | 39 | 7 | 2 |
| MCP Server | 156 | 151 | 5 | 0 | 151 | 5 | 0 |
| UI | 56 | 48 | 8 | 0 | 48 | 8 | 0 |
| **Total** | **1,469** | **1,204** | **211** | **54** | **1,184** | **214** | **71** |

## Delta Summary

| Metric | Codex | Opus | Delta |
|--------|------:|-----:|------:|
| 🟢 | 1,184 | 1,204 | **+20** |
| 🟡 | 214 | 211 | **−3** |
| 🔴 | 71 | 54 | **−17** |

**Opus 🟢 rate: 82.0%** vs Codex 80.6% (+1.4pp)

## Systematic Disagreements

### 1. Exception/Event Inheritance Tests (14 tests upgraded 🔴→🟡)

**Pattern**: `issubclass(XError, BaseError)` or `isinstance(event, DomainEvent)`

**Codex view**: Pure structural type-check.

**Opus view**: Exception inheritance IS behavioral — it determines which `except` clauses catch them. Event inheritance carries `event_id`/`occurred_at` via base class. These have behavioral impact beyond mere type structure.

**Affected buckets**: Domain (10 tests), no other buckets.

### 2. Delete-Success Mock Verification (5 tests upgraded 🔴→🟡)

**Pattern**: `repo.delete(id).assert_called_once_with(correct_id)` + `commit.assert_called_once()`

**Codex view**: "Trivially weak / no assertions."

**Opus view**: Verifying the correct ID was dispatched to the correct repository method AND the transaction was committed is a meaningful service-layer contract — not tautological.

**Affected buckets**: Service (4 tests), Report service (1 test).

### 3. Rate Limiter Behavioral Tests (2 tests upgraded 🔴→🟢)

**Pattern**: `asyncio.sleep` mock assert_called/assert_not_called after N calls.

**Codex view**: "Private patch / no assertions."

**Opus view**: `asyncio.sleep` is a public stdlib API, not a private attribute. The assertion "sleep was called" after N rate-limited calls IS the behavioral contract.

### 4. Status-Code-Only API Tests (39 tests: Opus 🟢, Codex 🟡)

**Pattern**: `assert response.status_code == 403/404/422/503`

**Codex view**: Status-code-only without body verification.

**Opus view**: Status codes ARE the behavioral contract for error-mapping tests — FastAPI maps specific exceptions to specific codes. The test target IS the mapping. Body is secondary.

### 5. Router Tag Tests (7 tests: Opus 🔴, Codex 🟢)

**Pattern**: `assert "tag" in router.tags`

**Codex view**: Behavioral — verifies tag presence.

**Opus view**: Structural — tag presence is an OpenAPI metadata concern, not a runtime behavioral property. Would pass with empty route implementations.

## 🔴 Tests — Full Inventory (54 Opus 🔴)

| Pattern | Count | Fix Effort |
|---------|------:|:----------:|
| `issubclass(X, Protocol)` | 14 | 🟢 Delete |
| Import surface / `hasattr(mod, "X")` | 18 | 🟢 Delete |
| `isinstance(result, TypeX)` without value check | 9 | 🟡 Add value assertions |
| Router tag presence | 7 | 🟡 Replace with route tests |
| `hasattr(uow, "repo")` attribute checks | 3 | 🟢 Delete |
| `is_str_enum` / base class isinstance | 3 | 🟡 Add member assertions |

**Estimated fix effort**: 32 trivial deletes, 22 test upgrades needed.

## Recommendations

1. **Safe to delete (32 tests)**: All `issubclass(X, Protocol)`, import surface, and `hasattr(mod, "X")` tests. These are subsumed by companion behavioral tests.
2. **Upgrade priority (22 tests)**: `isinstance` + value, router tags → route assertions, StrEnum member checks.
3. **No action needed**: MCP (0 🔴), UI (0 🔴), Integration (1 🔴) — these buckets are exemplary.
